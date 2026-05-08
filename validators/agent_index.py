"""Validate agent-index folder schema.

Required README.md content:
- AGENT-INDEX HTML comment marker (<!-- AGENT-INDEX: ... -->)
- A scope-boundary callout (a heading like '## Scope boundary' or
  '## ⚠️ Scope boundary')
- A 'Lookup recipes' (or '## Lookup recipes') section
- A glossary section, OR a glossary pointer in another file referenced in the README
- (Optional) a Verification/Independent-audit section — if present, audit-trail
  notes must be well-formed

Required for each non-README synthesis *.md file in the folder:
- At least one entry block starting with '- **Source:**'
- Each entry's Source line contains at least one URL or bibkey-style token
- When canonical 5-bullet bullets (Source / Code / Mechanism / Result / Status) appear
  together in an entry, they must be in that order. Code is optional; entries can
  legitimately omit Code when no separate code repo exists.
- The number of '**Source:**' lines matches a footer count if the footer states one
  (footer pattern: '<N> entries' or 'Total entries: <N>')

The validator does NOT enforce that every entry has every canonical bullet — different
content types use different bullet schemas (papers use 5-bullet; vendor / lab / standards
profiles often use Status / Source / Scope or similar). This loose schema reflects prompt-injection's
heterogeneous content. The mini fixture (positive-case ideal) demonstrates the strict
5-bullet schema for paper synthesis.

Files with zero '**Source:**' lines (overview / index / TOC files like 00_overview.md)
are exempt — treated as navigational, not synthesis.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE, cli_main
from validators.audit_trail import validate_audit_trail

AGENT_INDEX_COMMENT_RE = re.compile(r"<!--\s*AGENT-INDEX:[^>]*-->", re.IGNORECASE)
SCOPE_BOUNDARY_RE = re.compile(r"^##.*scope boundary", re.MULTILINE | re.IGNORECASE)
LOOKUP_RECIPES_RE = re.compile(r"^##.*lookup recipes", re.MULTILINE | re.IGNORECASE)
GLOSSARY_RE = re.compile(r"glossary", re.IGNORECASE)

REQUIRED_BULLETS = ("Source", "Mechanism", "Result", "Status")
OPTIONAL_BULLETS = ("Code",)
ALL_BULLETS_ORDERED = ("Source", "Code", "Mechanism", "Result", "Status")
SOURCE_LINE_RE = re.compile(r"^\s*-\s*\*\*Source:\*\*", re.MULTILINE)
ENTRY_BLOCK_RE = re.compile(
    r"^\s*-\s*\*\*Source:\*\*.*?(?=^\s*-\s*\*\*Source:\*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)
URL_OR_BIBKEY_RE = re.compile(rf"({URL_RE}|[a-z][a-z0-9_]+\d{{4}}[a-z0-9_]+)")
ENTRY_COUNT_FOOTER_RE = re.compile(
    r"(?:total\s+entries|^\s*entries)\s*:?\s*(\d+)|^\s*(\d+)\s+entries\b",
    re.MULTILINE | re.IGNORECASE,
)


def _validate_readme(readme: Path) -> list[str]:
    errors: list[str] = []
    text = readme.read_text(encoding="utf-8")

    if not AGENT_INDEX_COMMENT_RE.search(text):
        errors.append("README.md: missing AGENT-INDEX HTML comment marker")
    if not SCOPE_BOUNDARY_RE.search(text):
        errors.append("README.md: missing '## Scope boundary' section")
    if not LOOKUP_RECIPES_RE.search(text):
        errors.append("README.md: missing '## Lookup recipes' section")
    if not GLOSSARY_RE.search(text):
        errors.append("README.md: no mention of 'glossary' (header or pointer)")

    errors.extend(f"README.md: {e}" for e in validate_audit_trail(text))
    return errors


def _validate_synthesis_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    source_count = len(SOURCE_LINE_RE.findall(text))

    if source_count == 0:
        # Overview / index / TOC file — exempt from entry-shape checks.
        return errors

    blocks = [m.group(0) for m in ENTRY_BLOCK_RE.finditer(text)]

    for block in blocks:
        # The regex may capture a leading newline; locate the actual Source line.
        source_line = next(
            (line for line in block.splitlines() if "**Source:**" in line),
            "",
        )
        block_excerpt = source_line.strip()[:80]
        if not URL_OR_BIBKEY_RE.search(source_line):
            errors.append(
                f"{path.name}: entry's Source line has no URL or bibkey "
                f"(near '{block_excerpt}...')"
            )

        # Soft check on canonical ordering: only enforce when an entry uses Result
        # (the strongest signal it's a paper-synthesis entry, not a vendor / standards
        # profile which uses Source / Status / Scope or similar). Otherwise the entry
        # is using a different schema that's content-type-appropriate.
        if "Result" in re.findall(r"\*\*(\w+):\*\*", block):
            canonical = re.findall(
                r"\*\*(Source|Code|Mechanism|Result|Status):\*\*", block
            )
            expected = [b for b in ALL_BULLETS_ORDERED if b in canonical]
            if canonical != expected:
                errors.append(
                    f"{path.name}: paper-synthesis entry has canonical bullets in "
                    f"order {canonical}, expected {expected} "
                    f"(Source / Code / Mechanism / Result / Status; Code optional) "
                    f"(near '{block_excerpt}...')"
                )

    footer_match = ENTRY_COUNT_FOOTER_RE.search(text)
    if footer_match:
        footer_n = int(next(g for g in footer_match.groups() if g is not None))
        if footer_n != source_count:
            errors.append(
                f"{path.name}: footer claims {footer_n} entries, "
                f"but found {source_count} '**Source:**' lines"
            )

    return errors


def validate(path: Path) -> list[str]:
    if not path.is_dir():
        return [f"expected a directory, got file: {path}"]

    errors: list[str] = []
    readme = path / "README.md"
    if not readme.exists():
        errors.append("missing README.md")
    else:
        errors.extend(_validate_readme(readme))

    synthesis_files = sorted(
        p for p in path.glob("*.md") if p.name.lower() != "readme.md"
    )
    if not synthesis_files:
        errors.append("no synthesis *.md files (only README.md present)")
    for synth in synthesis_files:
        errors.extend(_validate_synthesis_file(synth))

    return errors


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))
