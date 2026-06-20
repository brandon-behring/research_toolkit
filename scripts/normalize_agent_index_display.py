#!/usr/bin/env python3
"""Normalize agent_index Mechanism displays to their verified verbatim excerpt.

Root cause this fixes (corpus-wide, ~826/835 ``cross_stage --strict`` errors): a
``- **Mechanism:** ...`` display in a failing dossier is an *editorial wrapper* around the
verbatim span, e.g. ::

    - **Mechanism:** <Title> — <venue>. Headline contribution, stated verbatim from the
      abstract: "<excerpt>" [claim_X]

The whole display string is therefore NOT a normalized substring of the cached source (the
preamble + the ``[claim_X]`` atom are not in the source), so it violates the display-vs-evidence
contract enforced by ``validators/agent_index_display.py``. The *already-green* dossiers (e.g.
``research_content_review``) are the same ``extraction_method: verbatim_match`` — they simply
display the **bare excerpt** as the Mechanism (plus an inline ``- **Evidence:** ev_*`` bullet).

This script makes every Mechanism match that green-reference form, deterministically:

  1. Join the block to its evidence record — (i) an existing ``**Evidence:** ev_*`` bullet
     (authoritative), else (ii) the ``**Source:**`` URL → the ev with that ``source_url``.
  2. Rewrite the Mechanism display to that ev's ``excerpt`` (whitespace-collapsed to one line —
     the same normalized form the gate checks), and ensure the block carries its
     ``- **Evidence:** ev_*`` bullet (inserted after ``**Status:**``).

SCOPE (post Rule B): this normalizer only touches **0-atom** paraphrase-display blocks (a
displayed sentence that paraphrases a single source whose verbatim span is its ``excerpt``).
Atom-bearing Mechanisms (those citing inline ``[claim_X]``) are grounded by the validator's
Rule B — each atom resolves to its evidence record, the verbatim proof living in that record's
anchor — so they are LEFT UNTOUCHED here (rewriting them would strip authored synthesis).

It REUSES the validator's own internals (``validators.agent_index_display`` /
``validators.v2_common``) so the selection + substring semantics are byte-identical to the gate.
It NEVER edits ``evidence_ledger.yml`` — it never sets/flips ``extraction_method`` and never
touches ``link_confidence``. The display always becomes an exact ev ``excerpt``; never invented
text.

NEVER FAIL SILENTLY (core principle #1):
  - excerpt does not verify against the cache (bad/stale blob)  -> REPORT (RE-GATHER), block untouched.
  - block joins no existing evidence record                     -> REPORT, block untouched.
  - claim atoms / source URL resolve to >1 distinct ev          -> REPORT (manual pick), block untouched.
  - a joined ev has a multi-line / empty excerpt                 -> REPORT (manual), block untouched.

Transactional per dossier (mirrors ``reanchor_evidence_ledger.py``): apply all rewrites, then run
``cross_stage.validate(dossier, strict=True)`` in-process. Green -> keep the written files. Any
residual error -> RESTORE every touched file and report the dossier RED (a residual arXiv-orphan
``--strict`` warning, a bad-cache excerpt, or another defect class routes the dossier to Phase 4 —
the partial display fix is never half-committed).

Usage:
  normalize_agent_index_display.py <dossier_dir> [--dry-run]
Exit codes:
  0  dossier is green after normalization (kept), or nothing to do, or --dry-run (informational).
  1  residual errors remain (restored) or unresolved blocks could not be normalized.
  2  usage error / IO error.
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

from validators import agent_index_display as aid  # noqa: E402
from validators import cross_stage  # noqa: E402
from validators.v2_common import _normalize_ws  # noqa: E402

# Reused verbatim from the validator so segmentation/matching agrees with the gate.
ENTRY_BLOCK_RE = aid.ENTRY_BLOCK_RE
SOURCE_LINE_RE = aid.SOURCE_LINE_RE
MECHANISM_LINE_RE = aid.MECHANISM_LINE_RE
EVIDENCE_LINE_RE = aid.EVIDENCE_LINE_RE

CLAIM_ATOM_RE = re.compile(r"\[(claim_[A-Za-z0-9_]+)\]")
URL_RE = re.compile(r"https?://[^\s<>]+")
# Placement anchors for the Evidence bullet (locate-only; no capture).
_STATUS_LOC = re.compile(r"^\s*-\s*\*\*Status:\*\*")
_MECH_LOC = re.compile(r"^\s*-\s*\*\*Mechanism:\*\*")
_INDENT_RE = re.compile(r"^(\s*)")


class NormalizeError(RuntimeError):
    """A rewrite could not be applied safely — the dossier file(s) are restored."""


# ---------- evidence indices ----------

def _norm_url(value: str) -> str:
    """Normalize a Source value or an ev ``source_url`` to a comparable key.

    Prefers an embedded ``http(s)://`` URL (handles ``<url>`` Mode-2 sources and
    ``bibkey url`` mixed lines); falls back to the bare token. Trailing ``/`` and
    wrapping ``<>`` are stripped so both sides of the join normalize identically.
    """
    value = value.strip()
    m = URL_RE.search(value)
    token = m.group(0) if m else value.lstrip("<").rstrip(">")
    return token.rstrip("/")


def _source_url_index(evidence: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """normalized ``source_url`` -> [evidence records]."""
    idx: dict[str, list[dict[str, Any]]] = {}
    for e in evidence.get("entries", []):
        if not isinstance(e, dict):
            continue
        url = e.get("source_url")
        if isinstance(url, str) and url.strip():
            idx.setdefault(_norm_url(url), []).append(e)
    return idx


def _dedupe_by_evid(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for e in records:
        evid = e.get("evidence_id")
        if isinstance(evid, str) and evid not in seen:
            seen.add(evid)
            out.append(e)
    return out


def _join_block(
    block: str,
    *,
    evidence_by_id: dict[str, dict[str, Any]],
    source_url_index: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    """Resolve the evidence record a 0-atom block's Mechanism should display.

    Returns ``(evidence, route, reason)`` — exactly one of (evidence, reason) is non-None.
    Priority: (i) an existing Evidence bullet (authoritative), (ii) the Source URL. Ambiguous
    (>1 distinct ev) / unresolved -> reason, never a guess. (Atom-bearing blocks are filtered
    out before this is called — Rule B owns them.)
    """
    # (i) existing Evidence bullet — authoritative.
    em = EVIDENCE_LINE_RE.search(block)
    if em:
        ev_id = em.group(1).strip()
        ev = evidence_by_id.get(ev_id)
        if ev is None:
            return None, None, f"Evidence bullet {ev_id!r} not in evidence_ledger"
        return ev, "evidence-bullet", None

    # (ii) Source URL.
    sm = SOURCE_LINE_RE.search(block)
    if not sm:
        return None, None, "block has no Evidence bullet and no Source line"
    url = _norm_url(sm.group(1))
    evs = _dedupe_by_evid(source_url_index.get(url, []))
    if len(evs) == 1:
        return evs[0], "source-url", None
    if len(evs) > 1:
        return None, None, (
            f"ambiguous: {len(evs)} evidence records share source_url {url!r} — manual pick"
        )
    return None, None, f"no evidence joins this block (no bullet; source_url {url!r} unmatched)"


# ---------- block rewrite primitives ----------

def _rewrite_mechanism(block: str, new_display: str) -> str:
    """Replace only the Mechanism display text, preserving its indent + ``- **Mechanism:** ``
    prefix and any trailing whitespace. ``count=1`` — one Mechanism per block."""
    def repl(m: re.Match[str]) -> str:
        return block[m.start():m.start(1)] + new_display + block[m.end(1):m.end()]

    return MECHANISM_LINE_RE.sub(repl, block, count=1)


def _ensure_evidence_bullet(block: str, ev_id: str) -> str:
    """Insert ``- **Evidence:** ev_id`` after the Status line (else after Mechanism),
    matching that anchor line's indent. No-op if an Evidence bullet already exists."""
    if EVIDENCE_LINE_RE.search(block):
        return block
    lines = block.splitlines(keepends=True)
    anchor = next((i for i, ln in enumerate(lines) if _STATUS_LOC.match(ln)), None)
    if anchor is None:
        anchor = next((i for i, ln in enumerate(lines) if _MECH_LOC.match(ln)), None)
    if anchor is None:  # no Mechanism — caller never sends such a block; defensive.
        raise NormalizeError("block has no Status or Mechanism line to anchor the Evidence bullet")
    indent = _INDENT_RE.match(lines[anchor]).group(1)  # type: ignore[union-attr]
    if not lines[anchor].endswith("\n"):
        lines[anchor] = lines[anchor] + "\n"
    lines.insert(anchor + 1, f"{indent}- **Evidence:** {ev_id}\n")
    return "".join(lines)


def _transform_block(block: str, fix: dict[str, Any]) -> str:
    if fix["need_display_rewrite"]:
        block = _rewrite_mechanism(block, fix["new_display"])
    if fix["need_bullet"]:
        block = _ensure_evidence_bullet(block, fix["ev_id"])
    return block


# ---------- plan / apply ----------

def plan_normalize(dossier_dir: Path) -> dict[str, Any]:
    """Identify per-block display normalizations. Pure (no writes).

    Returns ``{"fixes": [...], "unresolved": [...]}``. Each fix carries
    file/block_index/ev_id/route/old_display/new_display/need_display_rewrite/need_bullet;
    each unresolved carries file/block_index/display/reason.
    """
    index_dir = dossier_dir / "agent_index"
    cache_path = dossier_dir / "cache_manifest.yml"
    evidence_path = dossier_dir / "evidence_ledger.yml"

    fixes: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    if not index_dir.is_dir():
        return {"fixes": fixes, "unresolved": unresolved}

    cache = yaml.safe_load(cache_path.read_text(encoding="utf-8")) or {}
    evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8")) or {}
    cache_entries = aid._cache_entries(cache)
    evidence_by_id = aid._evidence_by_id(evidence)
    source_url_index = _source_url_index(evidence)
    cache_root = cache.get("cache_root") if isinstance(cache.get("cache_root"), str) else None

    family_files = sorted(p for p in index_dir.glob("*.md") if p.name.lower() != "readme.md")
    for fpath in family_files:
        text = fpath.read_text(encoding="utf-8")
        for bidx, m in enumerate(ENTRY_BLOCK_RE.finditer(text)):
            block = m.group(0)
            mech = MECHANISM_LINE_RE.search(block)
            if not mech:
                continue
            display = mech.group(1).strip()
            # Atom-bearing Mechanisms are grounded by the validator's Rule B (each [claim_X]
            # resolves to its evidence record); rewriting them would strip authored synthesis.
            # The normalizer only fixes 0-atom paraphrase displays (Form C).
            if CLAIM_ATOM_RE.search(display):
                continue
            short = display[:60] + ("..." if len(display) > 60 else "")
            ev_rec, route, reason = _join_block(
                block, evidence_by_id=evidence_by_id, source_url_index=source_url_index,
            )
            if ev_rec is None:
                unresolved.append({"file": fpath.name, "block_index": bidx,
                                   "display": short, "reason": reason})
                continue
            excerpt = ev_rec.get("excerpt")
            if not isinstance(excerpt, str) or not excerpt.strip():
                unresolved.append({"file": fpath.name, "block_index": bidx, "display": short,
                                   "reason": f"joined ev {ev_rec.get('evidence_id')!r} has no usable excerpt"})
                continue
            new_display = " ".join(excerpt.split())  # collapse to one line; gate-normalized form
            if not new_display:
                unresolved.append({"file": fpath.name, "block_index": bidx, "display": short,
                                   "reason": f"joined ev {ev_rec.get('evidence_id')!r} excerpt is whitespace-only"})
                continue
            cached, err = aid._cache_text_for_evidence(ev_rec, cache_entries, cache_path, cache_root)
            if err is not None:
                unresolved.append({"file": fpath.name, "block_index": bidx, "display": short,
                                   "reason": f"ev {ev_rec.get('evidence_id')!r} cache unreadable: {err} (RE-GATHER)"})
                continue
            if _normalize_ws(new_display) not in _normalize_ws(cached):
                unresolved.append({"file": fpath.name, "block_index": bidx, "display": short,
                                   "reason": f"ev {ev_rec.get('evidence_id')!r} excerpt not a substring of its cache "
                                             f"(bad/stale blob — RE-GATHER)"})
                continue
            need_disp = display != new_display
            need_bullet = not bool(EVIDENCE_LINE_RE.search(block))
            if not need_disp and not need_bullet:
                continue  # idempotent: already the green-reference form
            fixes.append({"file": fpath.name, "block_index": bidx, "ev_id": ev_rec["evidence_id"],
                          "route": route, "old_display": short, "new_display": new_display,
                          "need_display_rewrite": need_disp, "need_bullet": need_bullet})
    return {"fixes": fixes, "unresolved": unresolved}


def apply_normalize(dossier_dir: Path, fixes: list[dict[str, Any]]) -> None:
    """Apply fixes in place, positionally by (file, block_index). Format-preserving:
    only the Mechanism line + an inserted Evidence bullet change."""
    index_dir = dossier_dir / "agent_index"
    by_file: dict[str, dict[int, dict[str, Any]]] = {}
    for fx in fixes:
        by_file.setdefault(fx["file"], {})[fx["block_index"]] = fx
    for fname, fmap in by_file.items():
        fpath = index_dir / fname
        text = fpath.read_text(encoding="utf-8")
        out: list[str] = []
        last = 0
        for bidx, m in enumerate(ENTRY_BLOCK_RE.finditer(text)):
            out.append(text[last:m.start()])
            block = m.group(0)
            fx = fmap.get(bidx)
            out.append(_transform_block(block, fx) if fx else block)
            last = m.end()
        out.append(text[last:])
        fpath.write_text("".join(out), encoding="utf-8")


def normalize_dossier(dossier_dir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Plan + (unless dry_run) apply transactionally.

    On apply: write all fixes, run ``cross_stage.validate(strict=True)``; keep iff green,
    else RESTORE every touched file. Returns the plan plus ``kept``/``wrote``/``residual``.
    """
    plan = plan_normalize(dossier_dir)
    result: dict[str, Any] = {"dossier": dossier_dir.name, **plan,
                              "kept": False, "wrote": False, "residual": []}
    if dry_run:
        result["residual"] = cross_stage.validate(dossier_dir, strict=True)  # current (unmodified) state
        return result
    if not plan["fixes"]:
        result["residual"] = cross_stage.validate(dossier_dir, strict=True)
        result["kept"] = not result["residual"]
        return result

    index_dir = dossier_dir / "agent_index"
    touched = sorted({fx["file"] for fx in plan["fixes"]})
    originals = {f: (index_dir / f).read_text(encoding="utf-8") for f in touched}

    def _restore() -> None:
        for f, txt in originals.items():
            (index_dir / f).write_text(txt, encoding="utf-8")

    try:
        apply_normalize(dossier_dir, plan["fixes"])
        errs = cross_stage.validate(dossier_dir, strict=True)
    except Exception:
        _restore()
        raise
    if errs:
        _restore()
        result["residual"] = errs
        result["kept"] = False
    else:
        result["wrote"] = True
        result["kept"] = True
    return result


def _print_report(result: dict[str, Any], *, dry_run: bool) -> None:
    head = "DRY-RUN " if dry_run else ""
    print(f"== {head}{result['dossier']}: {len(result['fixes'])} display-fix(es), "
          f"{len(result['unresolved'])} unresolved ==", file=sys.stderr)
    for fx in result["fixes"]:
        verb = "would normalize" if dry_run else ("normalized" if result["kept"] else "planned (restored)")
        bits = []
        if fx["need_display_rewrite"]:
            bits.append("display:=excerpt")
        if fx["need_bullet"]:
            bits.append("+Evidence bullet")
        print(f"  {verb} {fx['file']} [{fx['ev_id']} via {fx['route']}]: "
              f"{', '.join(bits)}  (was: '{fx['old_display']}')", file=sys.stderr)
    for ur in result["unresolved"]:
        print(f"  UNRESOLVED {ur['file']} block#{ur['block_index']} ('{ur['display']}'): {ur['reason']}",
              file=sys.stderr)
    if result["residual"]:
        print(f"  RESIDUAL cross_stage --strict ({len(result['residual'])} error(s)) -> Phase 4:",
              file=sys.stderr)
        for e in result["residual"][:12]:
            print(f"    - {e}", file=sys.stderr)
        if len(result["residual"]) > 12:
            print(f"    … +{len(result['residual']) - 12} more", file=sys.stderr)
    state = "GREEN (kept)" if result["kept"] else ("DRY-RUN" if dry_run else "RED (restored)")
    print(f"  cross_stage --strict: {state}", file=sys.stderr)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="normalize_agent_index_display")
    parser.add_argument("dossier_dir", help="dossier directory containing agent_index/")
    parser.add_argument("--dry-run", action="store_true", help="report planned changes; write nothing")
    args = parser.parse_args(argv)

    dossier = Path(args.dossier_dir).expanduser().resolve()
    if not (dossier / "agent_index").is_dir():
        print(f"error: no agent_index/ in {dossier}", file=sys.stderr)
        return 2
    for required in ("cache_manifest.yml", "evidence_ledger.yml"):
        if not (dossier / required).exists():
            print(f"error: no {required} in {dossier}", file=sys.stderr)
            return 2
    try:
        result = normalize_dossier(dossier, dry_run=args.dry_run)
    except NormalizeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    _print_report(result, dry_run=args.dry_run)
    if args.dry_run:
        return 0
    if result["kept"] and not result["unresolved"]:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
