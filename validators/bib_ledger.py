"""Validate bib_ledger.yml schema.

Required fields per entry:
    bibkey | primary_url | title | status | claim_family

Optional fields (v1.1):
    authors    — first-author display string (e.g., "Hu et al. (2021)").
    venue      — publication venue (e.g., "ICLR 2022", "arXiv preprint").
    code_url   — canonical code URL (GitHub/HF/etc.); if present, must be a valid http(s) URL.

When `authors`/`venue`/`code_url` are populated by `/research-gather`, downstream stages
(`/dossier-build`, `/agent-index`) render from data instead of guessing — eliminating
the "guessed `<author>/<paper-slug>` GitHub URL → 404" failure mode reproduced across
vol27 (7/117 hard 404s) and vol28 (3/137 hard 404s).

When primary_url points at arxiv.org, this validator additionally requires the canonical
`arxiv.org/abs/<id>` form. This catches transposition errors and `/pdf/` URLs that
break dossier rendering.

Asserts bibkey uniqueness across the ledger.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# Allow standalone invocation: `python validators/bib_ledger.py path` works
# without needing `pip install -e .` or `python -m validators.bib_ledger`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE, cli_main

ALLOWED_STATUS = {"unverified", "verified", "mismatched"}
REQUIRED_FIELDS = ("bibkey", "primary_url", "title", "status", "claim_family")
OPTIONAL_STRING_FIELDS = ("authors", "venue", "code_url")
URL_PATTERN = re.compile(rf"^{URL_RE}$")
ARXIV_ABS_PATTERN = re.compile(
    r"^https?://(?:www\.)?arxiv\.org/abs/\d{4}\.\d{4,5}(?:v\d+)?/?$"
)
ARXIV_HOST_PATTERN = re.compile(r"^https?://(?:www\.)?arxiv\.org/")


def _validate_arxiv_url(url: str) -> str | None:
    """If url is on arxiv.org, require the canonical /abs/ form. Else return None (no check)."""
    if not ARXIV_HOST_PATTERN.match(url):
        return None
    if ARXIV_ABS_PATTERN.match(url):
        return None
    return (
        f"arxiv URL must be canonical 'arxiv.org/abs/<id>' form (no /pdf/, no extra "
        f"path); got {url!r}"
    )


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(data, dict) or "entries" not in data:
        return ["top-level must be a mapping with key 'entries:'"]

    entries = data["entries"]
    if not isinstance(entries, list) or not entries:
        return ["'entries' must be a non-empty list"]

    seen_bibkeys: set[str] = set()
    for idx, entry in enumerate(entries):
        loc = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: must be a mapping")
            continue

        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"{loc}: missing required field '{field}'")
            elif not isinstance(entry[field], str):
                errors.append(f"{loc}.{field}: must be a string")
            elif not entry[field].strip():
                errors.append(f"{loc}.{field}: must be non-empty")

        for field in OPTIONAL_STRING_FIELDS:
            if field in entry:
                value = entry[field]
                if not isinstance(value, str):
                    errors.append(f"{loc}.{field}: must be a string when present")
                elif not value.strip():
                    errors.append(
                        f"{loc}.{field}: when present, must be non-empty "
                        f"(use a dash field omission rather than empty string)"
                    )

        bibkey = entry.get("bibkey")
        if isinstance(bibkey, str):
            if bibkey in seen_bibkeys:
                errors.append(f"{loc}: duplicate bibkey '{bibkey}'")
            seen_bibkeys.add(bibkey)

        url = entry.get("primary_url")
        if isinstance(url, str) and url.strip():
            stripped = url.strip()
            if not URL_PATTERN.match(stripped):
                errors.append(f"{loc}.primary_url: not a valid http(s) URL: {url!r}")
            else:
                arxiv_err = _validate_arxiv_url(stripped)
                if arxiv_err is not None:
                    errors.append(f"{loc}.primary_url: {arxiv_err}")

        code_url = entry.get("code_url")
        if isinstance(code_url, str) and code_url.strip():
            if not URL_PATTERN.match(code_url.strip()):
                errors.append(
                    f"{loc}.code_url: not a valid http(s) URL: {code_url!r}"
                )

        status = entry.get("status")
        if isinstance(status, str) and status not in ALLOWED_STATUS:
            errors.append(
                f"{loc}.status: {status!r} not in {sorted(ALLOWED_STATUS)}"
            )

    return errors


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))
