"""Validate research_plan.md schema.

Required structure:
- H1 heading starting with 'Research Plan:'
- '## Sub-areas' with 4-8 top-level list items
- '## Out-of-scope' with >=1 list item
- '## Claim family taxonomy' with >=3 list items
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from validators._common import cli_main

H1_RE = re.compile(r"^# Research Plan:\s*\S", re.MULTILINE)
H2_RE = re.compile(r"^## (?P<title>.+?)\s*$", re.MULTILINE)
TOP_LEVEL_BULLET_RE = re.compile(r"^[-*] ", re.MULTILINE)

REQUIRED_SECTIONS = {
    "Sub-areas": (4, 8),
    "Out-of-scope": (1, None),
    "Claim family taxonomy": (3, None),
}


def _section_body(text: str, h2_title: str) -> str | None:
    """Return the body of the first '## <h2_title>' section, up to the next H2 or EOF."""
    pattern = re.compile(
        rf"^## {re.escape(h2_title)}\s*$(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1) if match else None


def _count_top_level_bullets(body: str) -> int:
    return sum(1 for _ in TOP_LEVEL_BULLET_RE.finditer(body))


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if path.is_dir():
        return [f"expected a markdown file, got directory: {path}"]

    text = path.read_text(encoding="utf-8")

    if not H1_RE.search(text):
        errors.append("missing required H1: '# Research Plan: <topic>'")

    found_h2 = {m.group("title").strip() for m in H2_RE.finditer(text)}

    for required_h2, (min_count, max_count) in REQUIRED_SECTIONS.items():
        if required_h2 not in found_h2:
            errors.append(f"missing required H2 section: '## {required_h2}'")
            continue
        body = _section_body(text, required_h2)
        if body is None:
            errors.append(f"could not extract body of '## {required_h2}'")
            continue
        bullet_count = _count_top_level_bullets(body)
        if bullet_count < min_count:
            errors.append(
                f"'## {required_h2}': has {bullet_count} top-level bullets, "
                f"need at least {min_count}"
            )
        if max_count is not None and bullet_count > max_count:
            errors.append(
                f"'## {required_h2}': has {bullet_count} top-level bullets, "
                f"max allowed is {max_count}"
            )

    return errors


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))
