#!/usr/bin/env python3
"""Bulk re-anchor ``evidence_ledger.yml`` excerpt_anchors against the extracted cache text.

Root cause this fixes: many v3 ``supports[].excerpt_anchor`` carry ``text_path_offset``
values computed against the RAW HTML (or a since-rotated cache blob), so the offset
overflows the shorter *extracted* text, or the span's sha256/excerpt no longer matches.
For each anchor that currently FAILS ``verify_excerpt_anchor`` (the exact /citation-audit
check), this re-locates the entry's verbatim ``excerpt`` in the *current* extracted cache
text and recomputes ``text_path_offset`` + ``sha256_of_span`` — wrapping
``build_excerpt_anchor.build_anchor`` so producer and verifier never disagree.

NEVER FAIL SILENTLY (core principle #1):
  - excerpt not found in cache         -> RE-GATHER report, anchor left unchanged.
  - excerpt ambiguous (>1 match)       -> AMBIGUOUS report, anchor left unchanged.
  - cache_id/text_path/file missing    -> reported, anchor left unchanged.
Only anchors that currently fail verification are touched (idempotent — a second run is a
no-op). The in-place rewrite is format-preserving (keyed on the globally-unique old
sha256_of_span; handles both block- and flow-style ``text_path_offset``), so a clean diff
shows only the changed offsets/hashes. After writing, every rewritten anchor is re-verified;
if any fails the file is RESTORED and the run aborts (a rewrite bug must never ship).

Usage:
  reanchor_evidence_ledger.py <dossier_dir> [--dry-run]
Exit codes:
  0  dossier evidence_ledger is green (all failing anchors re-anchored; none unresolved),
     or --dry-run completed (informational).
  1  unresolved anchors remain (re-gather/ambiguous) -> dossier not yet green.
  2  usage error, IO error, or a rewrite bug (file restored).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_excerpt_anchor import build_anchor  # noqa: E402
from validators import evidence_ledger  # noqa: E402
from validators.v2_common import (  # noqa: E402
    load_yaml_mapping,
    resolve_cache_path,
    verify_excerpt_anchor,
)


class ReanchorError(RuntimeError):
    """A rewrite could not be located/applied safely — the dossier file is restored."""


def _classify_value_error(msg: str) -> str:
    """Turn a build_anchor ValueError message into a stable, human report reason."""
    if "not found" in msg or "not clean UTF-8" in msg:
        return "excerpt not found in extracted cache text (RE-GATHER)"
    if "matches" in msg and "span" in msg:
        return f"excerpt AMBIGUOUS — {msg}"
    return msg


def _compute_new_anchor(text_bytes: bytes, excerpt: str) -> tuple[dict[str, Any], str | None]:
    """Build a fresh anchor for ``excerpt``. Returns (anchor, note).

    A unique match returns (anchor, None). When the excerpt appears more than once,
    every occurrence is an equally-valid anchor (each span whitespace-normalizes to the
    excerpt and is independently sha-verified), so we deterministically pick the FIRST
    and return a loud note — never a silent guess, and never a human bottleneck for a
    choice that cannot be wrong. Genuine not-found/ambiguity-of-zero re-raises ValueError.
    """
    try:
        return build_anchor(text_bytes, excerpt), None
    except ValueError as exc:
        m = re.search(r"matches (\d+) span", str(exc))
        if not m:
            raise
        anchor = build_anchor(text_bytes, excerpt, occurrence=1)
        return anchor, f"ambiguous: auto-picked occurrence 1 of {m.group(1)} (all occurrences validate)"


def _rewrite_anchor_block(
    lines: list[str], old_sha: str, new_off: list[int], new_sha: str
) -> bool:
    """Rewrite, in ``lines``, the offset+sha of the anchor whose sha256_of_span == old_sha.

    Keyed on the globally-unique old sha, so the match is unambiguous. Handles both
    ``text_path_offset: [s, e]`` (flow) and the ``text_path_offset:\\n - s\\n - e`` (block)
    styles. Returns True on success, False if the block shape was not as expected (caller
    treats that as a hard ReanchorError).
    """
    sha_idx = next(
        (i for i, ln in enumerate(lines) if f"sha256_of_span: {old_sha}" in ln), None
    )
    if sha_idx is None:
        return False
    tpo_idx = next(
        (
            i
            for i in range(sha_idx - 1, max(-1, sha_idx - 6), -1)
            if "text_path_offset:" in lines[i]
        ),
        None,
    )
    if tpo_idx is None:
        return False
    lines[sha_idx] = lines[sha_idx].replace(old_sha, new_sha)
    tpo_line = lines[tpo_idx]
    if "[" in tpo_line:  # flow style
        lines[tpo_idx] = re.sub(
            r"\[[^\]]*\]", f"[{new_off[0]}, {new_off[1]}]", tpo_line, count=1
        )
        return True
    # block style: the next two "- <int>" lines are the start/end
    item_idxs = [
        j
        for j in range(tpo_idx + 1, min(len(lines), tpo_idx + 5))
        if re.match(r"\s*-\s*\d+\s*$", lines[j])
    ][:2]
    if len(item_idxs) != 2:
        return False
    lines[item_idxs[0]] = re.sub(r"-\s*\d+", f"- {new_off[0]}", lines[item_idxs[0]], count=1)
    lines[item_idxs[1]] = re.sub(r"-\s*\d+", f"- {new_off[1]}", lines[item_idxs[1]], count=1)
    return True


def _manifest_context(man_path: Path) -> tuple[str | None, dict[str, Any]]:
    """Return (cache_root, cache_entries_by_id) from a cache_manifest.yml."""
    mdata, merrs = load_yaml_mapping(man_path)
    if mdata is None:
        raise ReanchorError(f"cannot read cache_manifest: {'; '.join(merrs) or man_path}")
    cache_root = mdata.get("cache_root") if isinstance(mdata.get("cache_root"), str) else None
    by_id = {
        e["cache_id"]: e
        for e in (mdata.get("entries") or [])
        if isinstance(e, dict) and isinstance(e.get("cache_id"), str)
    }
    return cache_root, by_id


def plan_reanchor(dossier_dir: Path) -> dict[str, Any]:
    """Identify failing anchors and compute replacements. Pure (no writes).

    Returns {"fixes": [...], "unresolved": [...]} where each fix is a dict with
    evidence_id/cache_id/old_off/old_sha/new_off/new_sha and each unresolved is a dict
    with evidence_id/cache_id/reason.
    """
    led_path = dossier_dir / "evidence_ledger.yml"
    man_path = dossier_dir / "cache_manifest.yml"
    led = yaml.safe_load(led_path.read_text(encoding="utf-8"))
    cache_root, by_id = _manifest_context(man_path)

    fixes: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for entry in led.get("entries", []):
        if not isinstance(entry, dict):
            continue
        excerpt = entry.get("excerpt")
        evid = entry.get("evidence_id")
        for support in entry.get("supports", []) or []:
            if not isinstance(support, dict):
                continue
            anchor = support.get("excerpt_anchor")
            if not isinstance(anchor, dict):
                continue
            cid = anchor.get("cache_id")
            old_off = anchor.get("text_path_offset")
            old_sha = anchor.get("sha256_of_span")
            # Idempotency: only touch anchors that currently fail verification.
            if not verify_excerpt_anchor(
                excerpt=excerpt if isinstance(excerpt, str) else "",
                cache_id=cid,
                text_path_offset=old_off,
                sha256_of_span=old_sha,
                cache_entries_by_id=by_id,
                manifest_path=man_path,
                loc=str(evid),
                cache_root=cache_root,
            ):
                continue
            if not isinstance(excerpt, str) or not excerpt.strip():
                unresolved.append({"evidence_id": evid, "cache_id": cid,
                                   "reason": "entry has no usable 'excerpt' to re-anchor"})
                continue
            cache_entry = by_id.get(cid)
            if cache_entry is None:
                unresolved.append({"evidence_id": evid, "cache_id": cid,
                                   "reason": f"cache_id {cid!r} not in cache_manifest"})
                continue
            tp = cache_entry.get("text_path")
            if not isinstance(tp, str):
                unresolved.append({"evidence_id": evid, "cache_id": cid,
                                   "reason": "manifest entry has no text_path"})
                continue
            text_file = resolve_cache_path(tp, manifest_path=man_path, cache_root=cache_root)
            try:
                text_bytes = text_file.read_bytes()
            except FileNotFoundError:
                unresolved.append({"evidence_id": evid, "cache_id": cid,
                                   "reason": f"cache text file missing: {text_file}"})
                continue
            try:
                new_anchor, note = _compute_new_anchor(text_bytes, excerpt)
            except ValueError as exc:
                unresolved.append({"evidence_id": evid, "cache_id": cid,
                                   "reason": _classify_value_error(str(exc))})
                continue
            new_off = new_anchor["text_path_offset"]
            new_sha = new_anchor["sha256_of_span"]
            if not isinstance(old_sha, str):
                unresolved.append({"evidence_id": evid, "cache_id": cid,
                                   "reason": "anchor has no sha256_of_span to key the rewrite on"})
                continue
            fixes.append({"evidence_id": evid, "cache_id": cid, "old_off": old_off,
                          "old_sha": old_sha, "new_off": new_off, "new_sha": new_sha,
                          "note": note})
    return {"fixes": fixes, "unresolved": unresolved}


def apply_reanchor(dossier_dir: Path, fixes: list[dict[str, Any]]) -> None:
    """Apply fixes in place (format-preserving) and re-verify; restore + raise on any failure."""
    led_path = dossier_dir / "evidence_ledger.yml"
    man_path = dossier_dir / "cache_manifest.yml"
    if not fixes:
        return
    original = led_path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    for fx in fixes:
        if not _rewrite_anchor_block(lines, fx["old_sha"], fx["new_off"], fx["new_sha"]):
            raise ReanchorError(
                f"could not locate anchor block for {fx['evidence_id']} (sha {fx['old_sha'][:12]}…)"
            )
    led_path.write_text("".join(lines), encoding="utf-8")
    # Re-verify every rewritten anchor against the freshly written file.
    cache_root, by_id = _manifest_context(man_path)
    led2 = yaml.safe_load(led_path.read_text(encoding="utf-8"))
    excerpt_by_evid = {
        e.get("evidence_id"): e.get("excerpt")
        for e in led2.get("entries", [])
        if isinstance(e, dict)
    }
    anchors_by_evid: dict[Any, list[dict]] = {}
    for e in led2.get("entries", []):
        if isinstance(e, dict):
            anchors_by_evid.setdefault(e.get("evidence_id"), [])
            for s in e.get("supports", []) or []:
                if isinstance(s, dict) and isinstance(s.get("excerpt_anchor"), dict):
                    anchors_by_evid[e.get("evidence_id")].append(s["excerpt_anchor"])
    bad: list[str] = []
    for fx in fixes:
        match = next(
            (a for a in anchors_by_evid.get(fx["evidence_id"], [])
             if a.get("sha256_of_span") == fx["new_sha"]),
            None,
        )
        if match is None:
            bad.append(f"{fx['evidence_id']} (rewritten anchor not found post-write)")
            continue
        errs = verify_excerpt_anchor(
            excerpt=excerpt_by_evid.get(fx["evidence_id"]) or "",
            cache_id=match.get("cache_id"),
            text_path_offset=match.get("text_path_offset"),
            sha256_of_span=match.get("sha256_of_span"),
            cache_entries_by_id=by_id,
            manifest_path=man_path,
            loc=str(fx["evidence_id"]),
            cache_root=cache_root,
        )
        if errs:
            bad.append(f"{fx['evidence_id']}: {'; '.join(errs)}")
    if bad:
        led_path.write_text(original, encoding="utf-8")
        raise ReanchorError("post-write re-verify FAILED (file restored): " + " | ".join(bad))


def reanchor_dossier(dossier_dir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Plan + (unless dry_run) apply. Returns the plan plus 'wrote' and 'green' (evidence_ledger)."""
    plan = plan_reanchor(dossier_dir)
    if not dry_run:
        apply_reanchor(dossier_dir, plan["fixes"])
    led_errs = evidence_ledger.validate(dossier_dir / "evidence_ledger.yml")
    plan["wrote"] = bool(plan["fixes"]) and not dry_run
    plan["green"] = not led_errs
    plan["remaining_ledger_errors"] = led_errs
    return plan


def _print_report(name: str, result: dict[str, Any], *, dry_run: bool) -> None:
    head = "DRY-RUN " if dry_run else ""
    print(f"== {head}{name}: {len(result['fixes'])} re-anchor(s), "
          f"{len(result['unresolved'])} unresolved ==", file=sys.stderr)
    for fx in result["fixes"]:
        verb = "would re-anchor" if dry_run else "re-anchored"
        suffix = f"  [{fx['note']}]" if fx.get("note") else ""
        print(f"  {verb} {fx['evidence_id']} [{fx['cache_id']}]: "
              f"{fx['old_off']} -> {fx['new_off']}{suffix}", file=sys.stderr)
    for ur in result["unresolved"]:
        print(f"  UNRESOLVED {ur['evidence_id']} [{ur['cache_id']}]: {ur['reason']}",
              file=sys.stderr)
    state = "GREEN" if result["green"] else "RED"
    print(f"  evidence_ledger: {state}"
          + ("" if result["green"] else f" ({len(result['remaining_ledger_errors'])} error(s) remain)"),
          file=sys.stderr)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="reanchor_evidence_ledger")
    parser.add_argument("dossier_dir", help="dossier directory containing evidence_ledger.yml")
    parser.add_argument("--dry-run", action="store_true", help="report planned changes; write nothing")
    args = parser.parse_args(argv)

    dossier = Path(args.dossier_dir).expanduser().resolve()
    if not (dossier / "evidence_ledger.yml").exists():
        print(f"error: no evidence_ledger.yml in {dossier}", file=sys.stderr)
        return 2
    if not (dossier / "cache_manifest.yml").exists():
        print(f"error: no cache_manifest.yml in {dossier}", file=sys.stderr)
        return 2
    try:
        result = reanchor_dossier(dossier, dry_run=args.dry_run)
    except ReanchorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    _print_report(dossier.name, result, dry_run=args.dry_run)
    if args.dry_run:
        return 0
    return 0 if result["green"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
