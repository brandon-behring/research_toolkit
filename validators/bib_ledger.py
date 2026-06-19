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
PEFT (7/117 hard 404s) and calibration (3/137 hard 404s).

When primary_url points at arxiv.org, this validator additionally requires the canonical
`arxiv.org/abs/<id>` form. This catches transposition errors and `/pdf/` URLs that
break dossier rendering.

Asserts bibkey uniqueness across the ledger.

Memory-verification anti-cheat heuristic (v1.2):
    If a ledger has ≥50 entries AND every single entry has `status: verified`,
    that's the signature of a Stage 2 subagent that marked everything `verified`
    from memory under time pressure rather than per-entry WebFetch. calibration produced
    1 misattribution-out-of-88 this way that only Stage 5 audit caught.

    Default behavior: emit a warning to stderr (informational). The validator
    returns success. Use `--strict` to promote the warning to an error.

    Usage:
        python -m validators.bib_ledger ledger.yml             # warns
        python -m validators.bib_ledger ledger.yml --strict    # errors
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
from validators.v2_common import (
    is_v2_mapping,
    parse_iso_date,
    validate_strict_live_entry,
    validate_strict_live_top,
)

ALLOWED_STATUS = {"unverified", "verified", "mismatched"}
REQUIRED_FIELDS = ("bibkey", "primary_url", "title", "status", "claim_family")
OPTIONAL_STRING_FIELDS = ("authors", "venue", "code_url")
# Optional date fields validated as ISO YYYY-MM-DD when present (never required).
# These are date-checked rather than string-checked because PyYAML deserializes
# unquoted ``2017-06-12`` to a ``datetime.date`` — parse_iso_date accepts both
# str and date, mirroring how retrieved_at / verified_at are handled in v2_common.
#   published_online — date the content first appeared online (arXiv v1 /
#                      Crossref issued / page publish date). Display-only
#                      freshness anchor for judging content age vs cache age.
OPTIONAL_DATE_FIELDS = ("published_online",)
URL_PATTERN = re.compile(rf"^{URL_RE}$")
# Accept both arXiv identifier schemes in canonical /abs/ form:
#   - new style (post-2007): 1234.56789(vN)   e.g. arxiv.org/abs/2106.09685
#   - legacy  (pre-2007):    <archive>(.<subclass>)?/YYMMNNN(vN)
#     e.g. arxiv.org/abs/math/9404236, hep-th/9901001, math.GT/0309136
ARXIV_ABS_PATTERN = re.compile(
    r"^https?://(?:www\.)?arxiv\.org/abs/"
    r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2,})?/\d{7})"
    r"(?:v\d+)?/?$"
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


MEMORY_VERIFIED_THRESHOLD = 50  # ≥ this many entries triggers the anti-cheat check


def _memory_verified_warning(entries: list[dict]) -> str | None:
    """Detect Stage-2-marked-everything-verified-from-memory anti-pattern.

    Returns a warning string if the heuristic fires, else None. The heuristic:
    - At least MEMORY_VERIFIED_THRESHOLD (50) entries.
    - 100% of entries have status: verified (zero unverified, zero mismatched).

    This pattern is the signature of a subagent that skipped per-entry WebFetch
    and bulk-marked everything as verified — a v1.0/v1.1 dogfood failure mode
    (calibration §2.1 BURN_IN). With per-entry verification done correctly, expect at
    least a couple of mismatched/unverified entries on a 50+-entry run.
    """
    if len(entries) < MEMORY_VERIFIED_THRESHOLD:
        return None
    statuses = [e.get("status") for e in entries if isinstance(e, dict)]
    if not statuses:
        return None
    if all(s == "verified" for s in statuses):
        return (
            f"WARN memory-verification suspected: {len(statuses)} entries, "
            f"all marked 'verified' (no 'unverified' or 'mismatched'). Per-entry "
            f"WebFetch verification typically produces ≥2 mismatched/unverified "
            f"entries on a run this size. See BURN_IN_NOTES.md calibration §2.1; "
            f"--strict promotes to error"
        )
    return None


def validate(path: Path, *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(data, dict) or "entries" not in data:
        return ["top-level must be a mapping with key 'entries:'"]

    v2 = is_v2_mapping(data)
    if v2:
        errors.extend(validate_strict_live_top(data))

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

        for field in OPTIONAL_DATE_FIELDS:
            if field in entry and entry[field] is not None:
                _, err = parse_iso_date(entry[field], f"{loc}.{field}")
                if err:
                    errors.append(err)

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

        if v2:
            errors.extend(validate_strict_live_entry(entry, loc=loc))

    # Anti-cheat heuristic — memory-verified detection. Soft by default.
    only_dicts = [e for e in entries if isinstance(e, dict)]
    warning = _memory_verified_warning(only_dicts)
    if warning:
        if strict:
            errors.append(warning)
        else:
            warnings.append(warning)

    if warnings and not strict:
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)

    return errors


def _cli_with_strict(argv: list[str]) -> int:
    """CLI entrypoint that supports --strict for the anti-cheat heuristic."""
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
