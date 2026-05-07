"""Validate bib_ledger.yml schema.

Checks each entry has bibkey/primary_url/title/status/claim_family with valid types
and enum membership. Asserts bibkey uniqueness across the ledger.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from validators._common import URL_RE, cli_main

ALLOWED_STATUS = {"unverified", "verified", "mismatched"}
REQUIRED_FIELDS = ("bibkey", "primary_url", "title", "status", "claim_family")
URL_PATTERN = re.compile(rf"^{URL_RE}$")


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

        bibkey = entry.get("bibkey")
        if isinstance(bibkey, str):
            if bibkey in seen_bibkeys:
                errors.append(f"{loc}: duplicate bibkey '{bibkey}'")
            seen_bibkeys.add(bibkey)

        url = entry.get("primary_url")
        if isinstance(url, str) and url.strip() and not URL_PATTERN.match(url.strip()):
            errors.append(f"{loc}.primary_url: not a valid http(s) URL: {url!r}")

        status = entry.get("status")
        if isinstance(status, str) and status not in ALLOWED_STATUS:
            errors.append(
                f"{loc}.status: {status!r} not in {sorted(ALLOWED_STATUS)}"
            )

    return errors


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))
