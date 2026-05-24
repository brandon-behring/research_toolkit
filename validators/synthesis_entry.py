"""Validate synthesis_entry.yml schema.

A synthesis_entry consolidates ≥3 primary sources into a single citation-ready
note. Used by /agent-index Phase 4c (synthesis pass; v2.4+) via
scripts/scaffold_synthesis_entry.py, or hand-authored when a single claim
requires multi-source attribution that doesn't fit the per-source
bib_ledger model.

Required fields per entry:
    synthesis_id | source_urls (≥3) | title | claim_family | volatility |
    tier_summary | status

Optional fields:
    cert_task_areas (list[str]) — project-specific cert coverage hooks
    attribution_map (mapping str → list[str]) — claim → supporting source_urls
    contradictions (list[str]) — open contradictions across sources

Hard schema rules (validator FAILS):
1. ``source_urls`` must be a list with ≥3 entries (the definitional bar — fewer
   sources means use bib_ledger + evidence_ledger instead).
2. Each ``source_urls`` entry is a valid http(s) URL.
3. ``volatility`` ∈ {stable, evolving, fast-moving}.
4. ``status`` ∈ {unverified, verified, mismatched}.
5. ``tier_summary`` matches the pattern "T<n>: N(, T<n>: N)*" with at least
   one ``T1: <≥1>`` (synthesis claims require ≥1 T1 source).

See ``templates/synthesis_entry.template.yml`` for the canonical shape.

BURN_IN_NOTES.md external dogfood item #8 motivated this template + validator.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE, cli_main

ALLOWED_VOLATILITY = {"stable", "evolving", "fast-moving"}
ALLOWED_STATUS = {"unverified", "verified", "mismatched"}
REQUIRED_FIELDS = (
    "synthesis_id",
    "source_urls",
    "title",
    "claim_family",
    "volatility",
    "tier_summary",
    "status",
)
URL_PATTERN = re.compile(rf"^{URL_RE}$")
TIER_SUMMARY_PATTERN = re.compile(r"^T\d+:\s*\d+(\s*,\s*T\d+:\s*\d+)*$")
TIER_ENTRY_PATTERN = re.compile(r"T(\d+):\s*(\d+)")

MIN_SOURCE_URLS = 3


def _validate_tier_summary(value: str, loc: str) -> list[str]:
    """Return [] if the tier_summary is well-formed AND has ≥1 T1, else errors."""
    if not TIER_SUMMARY_PATTERN.match(value):
        return [
            f"{loc}.tier_summary: {value!r} does not match pattern "
            f"'T<n>: N(, T<n>: N)*' (e.g., 'T1: 2, T2: 1')"
        ]
    tiers = {int(m.group(1)): int(m.group(2)) for m in TIER_ENTRY_PATTERN.finditer(value)}
    if tiers.get(1, 0) < 1:
        return [
            f"{loc}.tier_summary: synthesis requires ≥1 T1 source; got {tiers!r}"
        ]
    return []


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

    seen_ids: set[str] = set()
    for idx, entry in enumerate(entries):
        loc = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: must be a mapping")
            continue

        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"{loc}: missing required field '{field}'")

        # synthesis_id uniqueness
        sid = entry.get("synthesis_id")
        if isinstance(sid, str) and sid.strip():
            if sid in seen_ids:
                errors.append(f"{loc}: duplicate synthesis_id '{sid}'")
            seen_ids.add(sid)
        elif "synthesis_id" in entry:
            errors.append(f"{loc}.synthesis_id: must be a non-empty string")

        # source_urls: list with ≥3 entries, each a valid URL
        urls = entry.get("source_urls")
        if urls is None:
            pass  # already flagged as missing required field above
        elif not isinstance(urls, list):
            errors.append(f"{loc}.source_urls: must be a list")
        elif len(urls) < MIN_SOURCE_URLS:
            errors.append(
                f"{loc}.source_urls: synthesis requires ≥{MIN_SOURCE_URLS} URLs; "
                f"got {len(urls)} ({'use bib_ledger + evidence_ledger for ≤2 sources' if len(urls) < MIN_SOURCE_URLS else ''})"
            )
        else:
            for i, url in enumerate(urls):
                if not isinstance(url, str) or not URL_PATTERN.match(url.strip()):
                    errors.append(
                        f"{loc}.source_urls[{i}]: not a valid http(s) URL: {url!r}"
                    )

        # title: non-empty string
        title = entry.get("title")
        if title is not None and (not isinstance(title, str) or not title.strip()):
            errors.append(f"{loc}.title: must be a non-empty string")

        # claim_family: non-empty string
        cf = entry.get("claim_family")
        if cf is not None and (not isinstance(cf, str) or not cf.strip()):
            errors.append(f"{loc}.claim_family: must be a non-empty string")

        # volatility enum
        vol = entry.get("volatility")
        if isinstance(vol, str) and vol not in ALLOWED_VOLATILITY:
            errors.append(
                f"{loc}.volatility: {vol!r} not in {sorted(ALLOWED_VOLATILITY)}"
            )

        # status enum
        status = entry.get("status")
        if isinstance(status, str) and status not in ALLOWED_STATUS:
            errors.append(
                f"{loc}.status: {status!r} not in {sorted(ALLOWED_STATUS)}"
            )

        # tier_summary pattern + ≥1 T1
        ts = entry.get("tier_summary")
        if isinstance(ts, str) and ts.strip():
            errors.extend(_validate_tier_summary(ts, loc))

        # cert_task_areas: must be a list when present
        cta = entry.get("cert_task_areas")
        if cta is not None and not isinstance(cta, list):
            errors.append(f"{loc}.cert_task_areas: must be a list when present")

        # contradictions: must be a list when present
        contr = entry.get("contradictions")
        if contr is not None and not isinstance(contr, list):
            errors.append(f"{loc}.contradictions: must be a list when present")

    return errors


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv, validate))
