"""Backfill `authors`/`venue`/`code_url` into a bib_ledger.yml from its dossier.

The v1.1 schema added optional `authors`/`venue`/`code_url` fields to bib_ledger
entries. The eval-methodology/27/28 ledgers were created before v1.1 and don't have them
populated — but the corresponding dossier files DO have venue + authors + GitHub
metadata in their table cells. This script promotes that metadata back into the
ledger so future re-runs of /dossier-build and /agent-index can render from data
instead of guessing.

Matching strategy: the join key is the arXiv ID. Both ledger entries (in
primary_url) and dossier rows (in the arXiv/DOI cell) carry it. Entries without
arXiv IDs (Platt 1999, Brier 1950, etc.) are skipped — the dossier may still
have venue info, but the matching becomes title-fuzzy and error-prone.

Usage:
    python scripts/backfill_ledger.py <project_dir>
    python scripts/backfill_ledger.py --dry-run <project_dir>

Idempotent: if an entry already has `authors`/`venue`/`code_url`, the script
does NOT overwrite — it only fills empty fields. Re-running is safe.

The script preserves the YAML file's comment header and entry order. It uses
ruamel.yaml-style round-trip if available, falling back to a hand-rolled
text-edit approach (since PyYAML strips comments and reorders keys).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml

ARXIV_ID_RE = re.compile(
    r"(?:arxiv\.org/abs/|arxiv:)(\d{4}\.\d{4,5})", re.IGNORECASE
)
DOSSIER_PAPER_HEADER_RE = re.compile(
    r"^\|\s*Title\s*\|\s*Authors\s*\(year\)\s*\|", re.MULTILINE
)


def _split_pipe_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in inner.split("|")]


def _extract_dossier_metadata(dossier_dir: Path) -> dict[str, dict[str, str]]:
    """Walk dossier/*.md, return {arxiv_id: {authors, venue, code_url}}.

    Pulls from the canonical 7-column paper-table schema:
      Title | Authors (year) | Venue | arXiv/DOI | GitHub | Desc | KC
    """
    out: dict[str, dict[str, str]] = {}
    for md in sorted(dossier_dir.glob("*.md")):
        name = md.name.lower()
        if name in {"readme.md", "_dossier_readme.md"}:
            continue
        text = md.read_text(encoding="utf-8")
        lines = text.splitlines()
        in_paper_table = False
        col_count = 0
        for line in lines:
            if DOSSIER_PAPER_HEADER_RE.match(line):
                cols = _split_pipe_row(line)
                col_count = len(cols)
                in_paper_table = True
                continue
            stripped = line.strip()
            if in_paper_table:
                if not stripped.startswith("|"):
                    in_paper_table = False
                    continue
                if re.match(r"^\|\s*:?-+", stripped):
                    continue  # separator
                cells = _split_pipe_row(line)
                if len(cells) != col_count:
                    continue  # malformed; skip
                # cells[0] = Title, cells[1] = Authors (year),
                # cells[2] = Venue, cells[3] = arXiv/DOI,
                # cells[4] = GitHub, cells[5...] = desc/contribution
                if col_count < 5:
                    continue
                arxiv_cell = cells[3]
                m = ARXIV_ID_RE.search(arxiv_cell)
                if not m:
                    continue  # no arxiv ID; skip (can't join)
                arxiv_id = m.group(1)
                authors = cells[1]
                venue = cells[2]
                github = cells[4]
                # Convert bare "org/repo" to full GitHub URL.
                if (
                    github
                    and github != "—"
                    and not github.startswith("http")
                    and "/" in github
                ):
                    code_url = f"https://github.com/{github}"
                elif github.startswith("http"):
                    code_url = github
                else:
                    code_url = ""  # "—" or empty → no code_url
                out[arxiv_id] = {
                    "authors": authors,
                    "venue": venue,
                    "code_url": code_url,
                }
    return out


def _ledger_entries(ledger_path: Path) -> list[dict]:
    data = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "entries" not in data:
        return []
    entries = data["entries"]
    return entries if isinstance(entries, list) else []


def _entry_arxiv_id(entry: dict) -> str | None:
    url = entry.get("primary_url", "")
    if not isinstance(url, str):
        return None
    m = ARXIV_ID_RE.search(url)
    return m.group(1) if m else None


def _backfill_entry_text(
    entry_text: str,
    authors: str,
    venue: str,
    code_url: str,
) -> str:
    """Append optional fields to an entry's YAML block (if not already present).

    `entry_text` is the raw text of one entry (starts with `- bibkey:` and
    runs until the next entry or EOF). Idempotent: skips fields that already
    exist. Fields are appended at the end of the block, before the trailing
    blank line if any.
    """
    additions: list[str] = []
    if authors and "  authors:" not in entry_text:
        # YAML-quote authors string if it contains special chars.
        additions.append(f"  authors: {_yaml_scalar(authors)}")
    if venue and "  venue:" not in entry_text:
        additions.append(f"  venue: {_yaml_scalar(venue)}")
    if code_url and "  code_url:" not in entry_text:
        additions.append(f"  code_url: {code_url}")
    if not additions:
        return entry_text
    # Strip trailing blank lines from the entry, append additions, re-add blank.
    body = entry_text.rstrip("\n")
    return body + "\n" + "\n".join(additions) + "\n"


def _yaml_scalar(s: str) -> str:
    """Render a string as a safe YAML scalar."""
    if any(c in s for c in [":", "#", "'", '"', "[", "]", "{", "}", ","]):
        # Quote with single quotes; escape internal singles by doubling.
        escaped = s.replace("'", "''")
        return f"'{escaped}'"
    return s


def _backfill_ledger_text(
    ledger_text: str,
    metadata_by_arxiv_id: dict[str, dict[str, str]],
) -> tuple[str, int]:
    """Walk the ledger text and inject optional fields per entry.

    Returns (new_text, count_of_entries_backfilled).
    """
    # Split into chunks: each chunk is `- bibkey: ...` through the next `- bibkey:` or EOF.
    pattern = re.compile(r"(^- bibkey:.*?)(?=^- bibkey:|\Z)", re.MULTILINE | re.DOTALL)
    last_end = 0
    out_parts: list[str] = []
    count = 0
    for m in pattern.finditer(ledger_text):
        # Append everything before the entry (header / comments / etc.).
        if m.start() > last_end:
            out_parts.append(ledger_text[last_end:m.start()])
        entry_text = m.group(1)
        url_m = ARXIV_ID_RE.search(entry_text)
        if url_m:
            arxiv_id = url_m.group(1)
            meta = metadata_by_arxiv_id.get(arxiv_id)
            if meta:
                new_entry = _backfill_entry_text(
                    entry_text,
                    authors=meta.get("authors", ""),
                    venue=meta.get("venue", ""),
                    code_url=meta.get("code_url", ""),
                )
                if new_entry != entry_text:
                    count += 1
                out_parts.append(new_entry)
                last_end = m.end()
                continue
        out_parts.append(entry_text)
        last_end = m.end()
    if last_end < len(ledger_text):
        out_parts.append(ledger_text[last_end:])
    return "".join(out_parts), count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill authors/venue/code_url into a bib_ledger.yml from its dossier."
    )
    parser.add_argument("project_dir", help="Project dir with bib_ledger.yml + dossier/")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()

    project = Path(args.project_dir).expanduser().resolve()
    ledger_path = project / "bib_ledger.yml"
    dossier_dir = project / "dossier"

    if not ledger_path.exists():
        print(f"FATAL: {ledger_path} not found", file=sys.stderr)
        return 2
    if not dossier_dir.is_dir():
        print(f"FATAL: {dossier_dir} not found", file=sys.stderr)
        return 2

    metadata = _extract_dossier_metadata(dossier_dir)
    print(f"Extracted metadata for {len(metadata)} arxiv IDs from dossier", file=sys.stderr)

    ledger_text = ledger_path.read_text(encoding="utf-8")
    ledger_entries = _ledger_entries(ledger_path)
    ledger_arxiv_ids = {_entry_arxiv_id(e) for e in ledger_entries}
    ledger_arxiv_ids.discard(None)
    overlap = len(ledger_arxiv_ids & set(metadata.keys()))
    print(
        f"Ledger has {len(ledger_entries)} entries; "
        f"{len(ledger_arxiv_ids)} have arxiv IDs; "
        f"{overlap} overlap with dossier metadata",
        file=sys.stderr,
    )

    new_text, count = _backfill_ledger_text(ledger_text, metadata)
    print(f"Backfilled {count} entries", file=sys.stderr)

    if args.dry_run:
        print("--dry-run: no changes written", file=sys.stderr)
        return 0

    if new_text != ledger_text:
        ledger_path.write_text(new_text, encoding="utf-8")
        print(f"Wrote {ledger_path}", file=sys.stderr)
    else:
        print("No changes to write", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
