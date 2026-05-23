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

from validators._common import cli_main, matches_canonical_fuzzy

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
WIKI_LINK_RE = re.compile(r"\[\[([\w\-]+)\]\]")


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


def _ledger_primary_urls(entries: list[dict]) -> set[str]:
    """Extract canonical primary_url strings from ledger entries (used by dataset_ledger flow)."""
    urls: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        url = entry.get("primary_url", "")
        if isinstance(url, str) and url.strip():
            urls.add(url.strip().rstrip("/"))  # canonicalize trailing slash
    return urls


def _agent_index_source_urls(agent_index_dir: Path) -> set[str]:
    """Extract `**Source:**` URLs from agent_index synthesis files (used by dataset_ledger flow).

    Returns canonicalized URLs (trailing slash stripped). Excludes README.md +
    00_overview.md per the same convention as _agent_index_source_arxiv_ids.
    """
    urls: set[str] = set()
    for md in agent_index_dir.glob("*.md"):
        name = md.name.lower()
        if name in {"readme.md", "00_overview.md"}:
            continue
        text = md.read_text(encoding="utf-8")
        for m in SOURCE_LINE_RE.finditer(text):
            url = m.group("url").rstrip(".,;:").rstrip("/")
            urls.add(url)
    return urls


def _check_bib_ledger_flow(
    path: Path, *, errors: list[str], warnings: list[str]
) -> None:
    """Original v1.2 paper-pipeline cross-stage flow. Mutates errors/warnings in-place.

    Triggered when `<path>/bib_ledger.yml` exists.
    """
    ledger = path / "bib_ledger.yml"
    entries = _ledger_entries(ledger)
    ledger_ids = _ledger_arxiv_ids(entries)
    ledger_families = _ledger_claim_families(entries)

    plan = path / "research_plan.md"
    if plan.exists():
        taxonomy = _research_plan_taxonomy(plan)
        if taxonomy is not None:
            # Two-tier check: strict equality stays an error; fuzzy match
            # downgrades to a warning ("paraphrased — accepted"). Avoids
            # false-positive errors when agents write near-canonical forms
            # (e.g., "Session state" vs canonical "Session state (--resume,
            # fork_session, scratchpads)"). See BURN_IN_NOTES.md dogfood #5.
            strict_unknown = ledger_families - taxonomy
            truly_unknown = {
                f for f in strict_unknown
                if not matches_canonical_fuzzy(f, taxonomy)
            }
            paraphrased = strict_unknown - truly_unknown
            if truly_unknown:
                errors.append(
                    f"bib_ledger uses {len(truly_unknown)} claim_family value(s) "
                    f"not in research_plan.md taxonomy (no fuzzy match either): "
                    f"{sorted(truly_unknown)}"
                )
            if paraphrased:
                warnings.append(
                    f"WARN bib_ledger paraphrases {len(paraphrased)} claim_family "
                    f"value(s) (fuzzy-matched the taxonomy; prefer canonical phrasing): "
                    f"{sorted(paraphrased)} (--strict promotes to error)"
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


def _check_dataset_ledger_flow(
    path: Path, *, errors: list[str], warnings: list[str]
) -> None:
    """v1.9 dataset-pipeline cross-stage flow. Parallel to bib_ledger flow but
    keys on `primary_url` (since datasets don't have arxiv IDs).

    Triggered when `<path>/dataset_ledger.yml` exists. Mutates errors/warnings.

    Soft warnings (default → stderr; --strict → errors):
    - Orphan ledger: dataset_ledger entry with no matching `**Source:**` URL in agent_index.
    - Orphan synthesis: agent_index `**Source:**` URL with no matching dataset_ledger primary_url.
    """
    ledger = path / "dataset_ledger.yml"
    entries = _ledger_entries(ledger)
    ledger_urls = _ledger_primary_urls(entries)

    agent_index = path / "agent_index"
    if not agent_index.is_dir():
        return  # ledger present but no synthesis yet — not a cross-stage issue

    synthesis_urls = _agent_index_source_urls(agent_index)

    # Orphan ledger: in dataset_ledger but not in any agent_index Source line.
    orphan_ledger = ledger_urls - synthesis_urls
    if orphan_ledger:
        sample = sorted(orphan_ledger)[:5]
        extra = (
            f" (and {len(orphan_ledger) - 5} more)" if len(orphan_ledger) > 5 else ""
        )
        warnings.append(
            f"WARN dataset_ledger has {len(orphan_ledger)} entry/entries with no "
            f"matching agent_index **Source:** URL: {sample}{extra} "
            f"(stale ledger entries — synthesis incomplete? --strict promotes to error)"
        )

    # Orphan synthesis: in agent_index Source line but not in dataset_ledger.
    orphan_synthesis = synthesis_urls - ledger_urls
    if orphan_synthesis:
        sample = sorted(orphan_synthesis)[:5]
        extra = (
            f" (and {len(orphan_synthesis) - 5} more)"
            if len(orphan_synthesis) > 5
            else ""
        )
        warnings.append(
            f"WARN agent_index **Source:** URLs reference {len(orphan_synthesis)} "
            f"URL(s) not in dataset_ledger: {sample}{extra} "
            f"(unattributed synthesis entries — likely a rendering bug; "
            f"--strict promotes to error)"
        )


def _check_wiki_link_resolution(
    path: Path, *, errors: list[str], warnings: list[str]
) -> None:
    """Check that ``[[slug]]`` cross-references in agent_index/ resolve.

    A ``[[slug]]`` resolves if it matches one of:
    - A filename stem in ``agent_index/`` (slug = filename without .md)
    - A bibkey in ``bib_ledger.yml`` (paper pipeline)
    - An entry ID in ``dataset_ledger.yml`` (dataset pipeline)

    Dangling references are flagged as warnings (soft by default; --strict
    promotes to errors). See BURN_IN_NOTES.md external dogfood item #6.
    """
    agent_index_dir = path / "agent_index"
    if not agent_index_dir.is_dir():
        return

    valid_slugs: set[str] = set()
    for md in agent_index_dir.glob("*.md"):
        valid_slugs.add(md.stem)

    bib_ledger_path = path / "bib_ledger.yml"
    if bib_ledger_path.exists():
        for entry in _ledger_entries(bib_ledger_path):
            if isinstance(entry, dict):
                bibkey = entry.get("bibkey", "")
                if isinstance(bibkey, str) and bibkey.strip():
                    valid_slugs.add(bibkey.strip())

    dataset_ledger_path = path / "dataset_ledger.yml"
    if dataset_ledger_path.exists():
        for entry in _ledger_entries(dataset_ledger_path):
            if isinstance(entry, dict):
                eid = entry.get("id") or entry.get("dataset_id") or entry.get("bibkey", "")
                if isinstance(eid, str) and eid.strip():
                    valid_slugs.add(eid.strip())

    dangling: list[tuple[str, str]] = []
    for md in sorted(agent_index_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for m in WIKI_LINK_RE.finditer(text):
            slug = m.group(1)
            if slug not in valid_slugs:
                dangling.append((md.name, slug))

    if dangling:
        sample = dangling[:5]
        extra = f" (and {len(dangling) - 5} more)" if len(dangling) > 5 else ""
        sample_str = ", ".join(f"{f}→[[{s}]]" for f, s in sample)
        warnings.append(
            f"WARN {len(dangling)} dangling [[slug]] reference(s) in agent_index: "
            f"{sample_str}{extra} (--strict promotes to error)"
        )


def validate(path: Path, *, strict: bool = False) -> list[str]:
    """Validate cross-stage consistency for a research-toolkit project directory.

    Handles both pipelines:
    - Paper pipeline: triggered when `<path>/bib_ledger.yml` exists.
    - Dataset pipeline: triggered when `<path>/dataset_ledger.yml` exists.
    - Both: when both ledgers present, both flows run independently.
    - Neither: returns [] (no project to validate).

    Hard errors are always returned. Soft warnings are returned only when
    `strict=True`; otherwise printed to stderr and not counted as failures.
    """
    if path.is_file():
        return [f"expected a project directory, got file: {path}"]

    errors: list[str] = []
    warnings: list[str] = []

    bib_ledger = path / "bib_ledger.yml"
    dataset_ledger = path / "dataset_ledger.yml"

    if not bib_ledger.exists() and not dataset_ledger.exists():
        return []

    if bib_ledger.exists():
        _check_bib_ledger_flow(path, errors=errors, warnings=warnings)

    if dataset_ledger.exists():
        _check_dataset_ledger_flow(path, errors=errors, warnings=warnings)

    # Dangling [[slug]] reference check — applies whenever agent_index/ exists.
    # Treats agent_index filenames + bib_ledger bibkeys + dataset_ledger
    # entry IDs as valid targets. See BURN_IN_NOTES.md dogfood item #6.
    _check_wiki_link_resolution(path, errors=errors, warnings=warnings)

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
