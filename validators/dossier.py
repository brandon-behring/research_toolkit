"""Validate dossier directory schema.

A dossier is a directory of topic-organized markdown files. The schema is loose enough
to handle heterogeneous content (paper tables, leaderboard lists, vendor profiles,
standards profiles). Hard requirements:

- The first 5 columns of any header row starting '| Title |' must be:
    Title | Authors (year) | Venue | arXiv/DOI | GitHub | ...
  (Additional columns are allowed with varying names — One-line description, Mechanism,
  Threat surface, Dataset, etc. — depending on the topic file's editorial schema.)
- For every data row: Title and Authors (year) must be non-empty.
- At least one of arXiv/DOI or GitHub must be non-empty (or marked '(no arXiv)' / '—').

Files with no '| Title |' tables are accepted (they use a different content format —
bullet lists, prose summaries — which is appropriate for some topic types like
leaderboards and standards profiles).

The validator accepts either a directory (validates every *.md file inside, excluding
README.md) or a single .md file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from validators._common import cli_main

REQUIRED_FIRST_4 = ("Title", "Authors (year)", "Venue", "arXiv/DOI")
COL_5_PREFIXES = ("GitHub", "HF", "Code", "Repo")
HEADER_LINE_RE = re.compile(r"^\|\s*Title\s*\|", re.MULTILINE)


def _split_row(line: str) -> list[str]:
    # Strip leading/trailing pipes, split on |, strip cells.
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [cell.strip() for cell in inner.split("|")]


def _is_separator(line: str) -> bool:
    cells = _split_row(line)
    return all(re.fullmatch(r":?-+:?", c) for c in cells if c)


def _validate_single_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    header_indices = [i for i, line in enumerate(lines) if HEADER_LINE_RE.match(line)]
    if not header_indices:
        # File uses a non-table format (bullet lists, prose). Accepted.
        return errors

    for hidx in header_indices:
        header_cells = _split_row(lines[hidx])
        col_count = len(header_cells)
        is_paper_table = col_count >= 2 and header_cells[1].strip() == "Authors (year)"

        if is_paper_table:
            first_4 = tuple(header_cells[:4])
            col_5 = header_cells[4] if col_count >= 5 else ""
            if first_4 != REQUIRED_FIRST_4:
                errors.append(
                    f"{path.name}:{hidx + 1}: first 4 header columns {list(first_4)} "
                    f"do not match required {list(REQUIRED_FIRST_4)}"
                )
                continue
            if not any(col_5.startswith(p) for p in COL_5_PREFIXES):
                errors.append(
                    f"{path.name}:{hidx + 1}: column 5 is {col_5!r}, "
                    f"expected to start with one of {list(COL_5_PREFIXES)}"
                )
                continue

        # Expect a separator line right below.
        if hidx + 1 >= len(lines) or not _is_separator(lines[hidx + 1]):
            errors.append(f"{path.name}:{hidx + 2}: expected separator line under header")
            continue

        # Walk data rows until we hit a non-pipe line.
        row_idx = hidx + 2
        while row_idx < len(lines) and lines[row_idx].lstrip().startswith("|"):
            row_cells = _split_row(lines[row_idx])
            line_no = row_idx + 1
            if len(row_cells) != col_count:
                errors.append(
                    f"{path.name}:{line_no}: row has {len(row_cells)} cells, "
                    f"expected {col_count} (matching header)"
                )
            elif is_paper_table:
                title, authors, _venue, arxiv_doi, github = row_cells[:5]
                if not title:
                    errors.append(f"{path.name}:{line_no}: Title cell is empty")
                if not authors:
                    errors.append(f"{path.name}:{line_no}: Authors cell is empty")
                if not arxiv_doi and not github:
                    errors.append(
                        f"{path.name}:{line_no}: both arXiv/DOI and GitHub cells empty"
                    )
            else:
                # Non-paper table (e.g., standards docs with Title/Date/URL/Description).
                # Some legitimate entries are PDF-only with no stable URL —
                # only Title is required.
                title = row_cells[0]
                if not title:
                    errors.append(f"{path.name}:{line_no}: Title cell is empty")
            row_idx += 1

    return errors


def validate(path: Path) -> list[str]:
    if path.is_file():
        return _validate_single_file(path)

    errors: list[str] = []
    md_files = sorted(p for p in path.glob("*.md") if p.name.lower() != "readme.md")
    if not md_files:
        return [f"no *.md files found in {path}"]
    for md in md_files:
        errors.extend(_validate_single_file(md))
    return errors


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))
