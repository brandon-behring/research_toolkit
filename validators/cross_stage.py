"""Validate cross-stage consistency for a research project.

This is a v1.2 defensive check that complements the per-artifact validators.
The per-artifact validators check schema correctness in isolation; this validator
checks that the artifacts agree on the canonical entry → URL → taxonomy
relationships.

Reproduced bugs this catches:
- claim_family drift: a bib_ledger entry uses claim_family `peft_serving` but
  research_plan.md's taxonomy only lists `lora_variant`. Pre-v1.2 the
  bib_ledger validator accepted this (string non-empty check only); the plan
  was never cross-checked. (PEFT dogfood: subagent flagged this manually.)
- Orphan arxiv IDs (soft warning by default, promotable to error with --strict):
  agent_index `**Source:**` URLs that don't have a matching bib_ledger entry.
  In prompt-injection/real this is intentional (cross-references to pre-LLM foundational
  papers) so it's a warning, not an error. With --strict it becomes hard.

Hard requirements (validator FAILS):
1. Every claim_family value in bib_ledger.yml MUST appear in the
   research_plan.md "## Claim family taxonomy" section.

Soft warnings (printed to stderr, don't fail by default; --strict promotes
to errors):
2. Orphan arxiv IDs in dossier paper-tables (referenced but not in ledger).
3. Orphan arxiv IDs in agent_index `**Source:**` lines (referenced but not
   in ledger; prompt-injection/real legitimately has these as foundational
   cross-references).
4. Stale ledger entries (in bib_ledger but no `**Source:**` line in any
   agent_index synthesis file references their arxiv ID; might be
   intentional if the synthesis hasn't been built yet).

Usage:
    python -m validators.cross_stage <project_dir>           # warnings only
    python -m validators.cross_stage <project_dir> --strict  # warnings → errors

Expected layout under <project_dir>:
    <project_dir>/research_plan.md
    <project_dir>/bib_ledger.yml
    <project_dir>/dossier/         (optional)
    <project_dir>/agent_index/     (optional)

The validator skips gracefully if any directory is absent (returns no errors).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import cli_main

ARXIV_ID_RE = re.compile(
    r"(?:arxiv\.org/abs/|arxiv:)(\d{4}\.\d{4,5})", re.IGNORECASE
)
SOURCE_LINE_RE = re.compile(
    r"^\s*-\s*\*\*Source:\*\*\s*(?P<url>https?://\S+)",
    re.MULTILINE,
)
DOSSIER_PAPER_HEADER_RE = re.compile(
    r"^\|\s*Title\s*\|\s*Authors\s*\(year\)\s*\|", re.MULTILINE
)
TAXONOMY_SECTION_RE = re.compile(
    r"^## Claim family taxonomy\s*$(?P<body>.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
TAXONOMY_ITEM_RE = re.compile(r"^[-*]\s+`?([a-zA-Z_][\w]*)`?", re.MULTILINE)


def _research_plan_taxonomy(plan_path: Path) -> set[str] | None:
    """Extract the set of claim_family values from research_plan.md.

    Returns None if the section is absent (skip the cross-check).
    """
    text = plan_path.read_text(encoding="utf-8")
    m = TAXONOMY_SECTION_RE.search(text)
    if m is None:
        return None
    body = m.group("body")
    return {match.group(1) for match in TAXONOMY_ITEM_RE.finditer(body)}


def _ledger_entries(ledger_path: Path) -> list[dict]:
    data = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "entries" not in data:
        return []
    entries = data["entries"]
    return entries if isinstance(entries, list) else []


def _ledger_arxiv_ids(entries: list[dict]) -> set[str]:
    ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        url = entry.get("primary_url", "")
        if isinstance(url, str):
            m = ARXIV_ID_RE.search(url)
            if m:
                ids.add(m.group(1))
    return ids


def _ledger_claim_families(entries: list[dict]) -> set[str]:
    families: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cf = entry.get("claim_family", "")
        if isinstance(cf, str) and cf.strip():
            families.add(cf.strip())
    return families


def _agent_index_source_arxiv_ids(agent_index_dir: Path) -> set[str]:
    ids: set[str] = set()
    for md in agent_index_dir.glob("*.md"):
        name = md.name.lower()
        if name in {"readme.md", "00_overview.md"}:
            continue
        text = md.read_text(encoding="utf-8")
        for m in SOURCE_LINE_RE.finditer(text):
            url = m.group("url").rstrip(".,;:")
            arxiv_match = ARXIV_ID_RE.search(url)
            if arxiv_match:
                ids.add(arxiv_match.group(1))
    return ids


def _dossier_arxiv_ids_in_paper_tables(dossier_dir: Path) -> set[str]:
    ids: set[str] = set()
    for md in sorted(dossier_dir.glob("*.md")):
        name = md.name.lower()
        if name in {"readme.md", "_dossier_readme.md"}:
            continue
        text = md.read_text(encoding="utf-8")
        in_paper_table = False
        for line in text.splitlines():
            if DOSSIER_PAPER_HEADER_RE.match(line):
                in_paper_table = True
                continue
            stripped = line.strip()
            if in_paper_table:
                if stripped.startswith("|") and not re.match(r"^\|\s*:?-+", stripped):
                    for m in ARXIV_ID_RE.finditer(stripped):
                        ids.add(m.group(1))
                elif stripped == "":
                    in_paper_table = False
    return ids


def validate(path: Path, *, strict: bool = False) -> list[str]:
    """Validate cross-stage consistency.

    Hard errors are always returned. Soft warnings are returned only when
    `strict=True`; otherwise they're printed to stderr and not counted as
    failures.
    """
    if path.is_file():
        return [f"expected a project directory, got file: {path}"]

    errors: list[str] = []
    warnings: list[str] = []

    ledger = path / "bib_ledger.yml"
    if not ledger.exists():
        return []

    entries = _ledger_entries(ledger)
    ledger_ids = _ledger_arxiv_ids(entries)
    ledger_families = _ledger_claim_families(entries)

    plan = path / "research_plan.md"
    if plan.exists():
        taxonomy = _research_plan_taxonomy(plan)
        if taxonomy is not None:
            unknown = ledger_families - taxonomy
            if unknown:
                errors.append(
                    f"bib_ledger uses {len(unknown)} claim_family value(s) "
                    f"not in research_plan.md taxonomy: {sorted(unknown)}"
                )

    dossier = path / "dossier"
    if dossier.is_dir():
        dossier_ids = _dossier_arxiv_ids_in_paper_tables(dossier)
        orphan = dossier_ids - ledger_ids
        if orphan:
            sample = sorted(orphan)[:5]
            extra = f" (and {len(orphan) - 5} more)" if len(orphan) > 5 else ""
            warnings.append(
                f"WARN dossier paper-tables reference {len(orphan)} arxiv ID(s) "
                f"not in bib_ledger: {sample}{extra}"
            )

    agent_index = path / "agent_index"
    if agent_index.is_dir():
        index_source_ids = _agent_index_source_arxiv_ids(agent_index)
        orphan = index_source_ids - ledger_ids
        if orphan:
            sample = sorted(orphan)[:5]
            extra = f" (and {len(orphan) - 5} more)" if len(orphan) > 5 else ""
            warnings.append(
                f"WARN agent_index **Source:** lines reference {len(orphan)} "
                f"arxiv ID(s) not in bib_ledger: {sample}{extra} "
                f"(may be foundational cross-references; --strict promotes to error)"
            )

        stale = ledger_ids - index_source_ids
        if stale:
            sample = sorted(stale)[:5]
            extra = f" (and {len(stale) - 5} more)" if len(stale) > 5 else ""
            warnings.append(
                f"WARN bib_ledger has {len(stale)} arxiv ID(s) with no "
                f"matching agent_index **Source:** line: {sample}{extra} "
                f"(stale entries — synthesis incomplete? --strict promotes to error)"
            )

    if strict:
        errors.extend(warnings)
    else:
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)

    return errors


def _cli_with_strict(argv: list[str]) -> int:
    """CLI entrypoint that supports --strict."""
    strict = False
    args = argv[1:]
    if "--strict" in args:
        strict = True
        args = [a for a in args if a != "--strict"]
    if len(args) != 1:
        print(f"usage: {Path(argv[0]).name} [--strict] <path>", file=sys.stderr)
        return 2
    target = Path(args[0]).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    errors = validate(target, strict=strict)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            f"VALIDATION FAILED: {len(errors)} error(s) in {target}",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(_cli_with_strict(sys.argv))
