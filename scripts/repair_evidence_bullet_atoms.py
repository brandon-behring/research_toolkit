#!/usr/bin/env python3
"""Repair malformed ``- **Evidence:**`` bullets into inline ``[claim_X]`` atoms (Rule B).

Some dossiers authored a block's evidence as ``- **Evidence:** claim_a, claim_b`` (claim_ids,
comma/space-separated) or ``- **Evidence:** ev_1 ev_2`` (several ev_ids) — but ``EVIDENCE_LINE_RE``
captures the whole value as ONE id, so it resolves to nothing and the block fails
``cross_stage`` ("Evidence id ... not found"). The authored INTENT is a synthesis Mechanism that
cites several claims; the green form for that is **inline ``[claim_X]`` atoms in the Mechanism**
(grounded by the validator's Rule B), not a multi-id Evidence bullet.

This script converts each such malformed bullet: it resolves every token (a ``claim_id`` directly,
or an ``ev_id`` → that record's first ``supports[].claim_id``), APPENDS the resulting atoms to the
Mechanism display (those not already inline), and REMOVES the malformed Evidence bullet. A bullet
that is already a single valid ``evidence_id`` is left untouched.

NEVER FAIL SILENTLY: a bullet with any token that resolves to neither a claim_id nor an ev_id is
REPORTED, the block untouched. Transactional per dossier (mirror Scripts 1/2): apply → run
``cross_stage.validate(strict=True)`` → keep iff green, else RESTORE the file(s) and report.

Usage:  repair_evidence_bullet_atoms.py <dossier_dir> [--dry-run]
Exit:   0 green (kept) / nothing to do / --dry-run; 1 residual; 2 usage.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators import agent_index_display as aid  # noqa: E402
from validators import cross_stage  # noqa: E402

ENTRY_BLOCK_RE = aid.ENTRY_BLOCK_RE
MECHANISM_LINE_RE = aid.MECHANISM_LINE_RE
EVIDENCE_LINE_RE = aid.EVIDENCE_LINE_RE
CLAIM_ATOM_RE = aid.CLAIM_ATOM_RE


def _ev_first_claim(evidence: dict[str, Any]) -> dict[str, str]:
    """evidence_id -> its FIRST supports[].claim_id (the record's primary claim)."""
    out: dict[str, str] = {}
    for e in evidence.get("entries", []):
        if not isinstance(e, dict) or not isinstance(e.get("evidence_id"), str):
            continue
        for s in e.get("supports", []) or []:
            if isinstance(s, dict) and isinstance(s.get("claim_id"), str) and s["claim_id"].strip():
                out[e["evidence_id"]] = s["claim_id"].strip()
                break
    return out


def _resolve_tokens(value: str, known_claims: set[str], ev_first_claim: dict[str, str]
                    ) -> tuple[list[str] | None, str | None]:
    """Resolve a malformed Evidence-bullet value to a list of claim atoms, or a reason."""
    tokens = [t for t in value.replace(",", " ").split() if t]
    atoms: list[str] = []
    for tk in tokens:
        if tk in known_claims:
            atoms.append(tk)
        elif tk in ev_first_claim:
            atoms.append(ev_first_claim[tk])
        else:
            return None, f"token {tk!r} resolves to neither a claim_id nor an ev_id"
    # de-dupe, preserve order
    seen: set[str] = set()
    out = [a for a in atoms if not (a in seen or seen.add(a))]
    return out, None


def _append_atoms_to_mechanism(line: str, atoms: list[str]) -> str:
    existing = set(CLAIM_ATOM_RE.findall(line))
    add = [a for a in atoms if a not in existing]
    if not add:
        return line
    stripped = line.rstrip("\n")
    nl = "\n" if line.endswith("\n") else ""
    return stripped + " " + " ".join(f"[{a}]" for a in add) + nl


def _transform_block(block: str, atoms: list[str]) -> str:
    """Append atoms to the Mechanism line and drop the (first) Evidence bullet line."""
    out: list[str] = []
    dropped = False
    for ln in block.splitlines(keepends=True):
        if not dropped and EVIDENCE_LINE_RE.search(ln):
            dropped = True
            continue
        if MECHANISM_LINE_RE.search(ln):
            ln = _append_atoms_to_mechanism(ln, atoms)
        out.append(ln)
    return "".join(out)


def plan_repair(dossier_dir: Path) -> dict[str, Any]:
    index_dir = dossier_dir / "agent_index"
    evidence = yaml.safe_load((dossier_dir / "evidence_ledger.yml").read_text(encoding="utf-8")) or {}
    evidence_by_id = aid._evidence_by_id(evidence)
    known_claims = aid._claim_ids(evidence)
    ev_first_claim = _ev_first_claim(evidence)

    fixes: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    if not index_dir.is_dir():
        return {"fixes": fixes, "unresolved": unresolved}
    for fpath in sorted(p for p in index_dir.glob("*.md") if p.name.lower() != "readme.md"):
        text = fpath.read_text(encoding="utf-8")
        for bidx, m in enumerate(ENTRY_BLOCK_RE.finditer(text)):
            block = m.group(0)
            if not MECHANISM_LINE_RE.search(block):
                continue
            em = EVIDENCE_LINE_RE.search(block)
            if not em:
                continue
            value = em.group(1).strip()
            if value in evidence_by_id:
                continue  # already a single valid ev_id — well-formed, leave it
            atoms, reason = _resolve_tokens(value, known_claims, ev_first_claim)
            if atoms is None:
                unresolved.append({"file": fpath.name, "block_index": bidx, "value": value, "reason": reason})
                continue
            fixes.append({"file": fpath.name, "block_index": bidx, "value": value, "atoms": atoms})
    return {"fixes": fixes, "unresolved": unresolved}


def apply_repair(dossier_dir: Path, fixes: list[dict[str, Any]]) -> None:
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
            out.append(_transform_block(block, fx["atoms"]) if fx else block)
            last = m.end()
        out.append(text[last:])
        fpath.write_text("".join(out), encoding="utf-8")


def repair_dossier(dossier_dir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    plan = plan_repair(dossier_dir)
    result: dict[str, Any] = {"dossier": dossier_dir.name, **plan, "kept": False, "wrote": False, "residual": []}
    if dry_run:
        result["residual"] = cross_stage.validate(dossier_dir, strict=True)
        return result
    if not plan["fixes"]:
        result["residual"] = cross_stage.validate(dossier_dir, strict=True)
        result["kept"] = not result["residual"]
        return result
    index_dir = dossier_dir / "agent_index"
    touched = sorted({fx["file"] for fx in plan["fixes"]})
    originals = {f: (index_dir / f).read_text(encoding="utf-8") for f in touched}
    try:
        apply_repair(dossier_dir, plan["fixes"])
        errs = cross_stage.validate(dossier_dir, strict=True)
    except Exception:
        for f, txt in originals.items():
            (index_dir / f).write_text(txt, encoding="utf-8")
        raise
    if errs:
        for f, txt in originals.items():
            (index_dir / f).write_text(txt, encoding="utf-8")
        result["residual"] = errs
    else:
        result["wrote"] = True
        result["kept"] = True
    return result


def _print_report(result: dict[str, Any], *, dry_run: bool) -> None:
    head = "DRY-RUN " if dry_run else ""
    print(f"== {head}{result['dossier']}: {len(result['fixes'])} bullet-repair(s), "
          f"{len(result['unresolved'])} unresolved ==", file=sys.stderr)
    for fx in result["fixes"]:
        verb = "would repair" if dry_run else ("repaired" if result["kept"] else "planned (restored)")
        print(f"  {verb} {fx['file']} block#{fx['block_index']}: "
              f"'{fx['value']}' -> atoms {fx['atoms']}", file=sys.stderr)
    for ur in result["unresolved"]:
        print(f"  UNRESOLVED {ur['file']} block#{ur['block_index']} ('{ur['value']}'): {ur['reason']}",
              file=sys.stderr)
    for e in result["residual"][:8]:
        print(f"  RESIDUAL: {e}", file=sys.stderr)
    state = "GREEN (kept)" if result["kept"] else ("DRY-RUN" if dry_run else "RED (restored)")
    print(f"  cross_stage --strict: {state}", file=sys.stderr)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="repair_evidence_bullet_atoms")
    parser.add_argument("dossier_dir")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    dossier = Path(args.dossier_dir).expanduser().resolve()
    if not (dossier / "agent_index").is_dir():
        print(f"error: no agent_index/ in {dossier}", file=sys.stderr)
        return 2
    if not (dossier / "evidence_ledger.yml").exists():
        print(f"error: no evidence_ledger.yml in {dossier}", file=sys.stderr)
        return 2
    result = repair_dossier(dossier, dry_run=args.dry_run)
    _print_report(result, dry_run=args.dry_run)
    if args.dry_run:
        return 0
    return 0 if (result["kept"] and not result["unresolved"]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
