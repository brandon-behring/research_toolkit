"""Validate topic_backlog.yml schema (v1).

A topic backlog is the output of /topic-discovery: a prioritized, deduplicated,
*living* list of research topics mined from a knowledge corpus (e.g., the
interview-prep LaTeX series). Each entry is a candidate topic that hands off to
/research-plan; the file is append-only across runs and tracks per-topic
lifecycle so re-runs can dedup already-researched topics.

Required fields per entry:
    topic_id | title | kind | track | priority | rationale |
    claim_family_seeds | status

`kind` is a fixed enum:
    deepen   — a frontier subtopic of a volume the corpus already covers.
    adjacent — uncovered white-space related to the corpus.

`priority` is a fixed enum: P0 | P1 | P2 (P0 = research first).
`status` is a fixed enum: proposed | planned | researched | dropped.

`claim_family_seeds` must list ≥3 seed taxonomy categories — these front-load
/research-plan's claim_family taxonomy step (which wants 3-8 families).

Conditional rule: a `deepen` entry must name its parent `source_volume`; an
`adjacent` entry omits it (there is no single parent volume).

Optional fields (omit rather than use empty string — do NOT fabricate):
    source_volume   (str)       — required when kind == deepen.
    source_los      (list[str]) — LOS IDs the topic clusters from.
    seed_sources    (list[str]) — landmark http(s) URLs (e.g., from a volume's
                                   reading_list.yml).
    notes           (str)       — free-form.

Lifecycle fields (absent or null = not yet set; written by scripts/backlog_stamp.py):
    dossier_path    (str|null)  — set when status -> researched.
    researched_at   (str|null)  — set when status -> researched.

Both-kinds anti-cheat heuristic (parallels dataset_ledger's memory-verification
check): a backlog with ≥8 entries that surfaces only ONE `kind` is the signature
of a one-axis mine — /topic-discovery is required to surface BOTH deepen and
adjacent. Default behavior: warn to stderr; --strict promotes to error. Two
companion shape warnings (all-identical priority, P0 inflation) ride the same
gate.

    Usage:
        python validators/topic_backlog.py backlog.yml            # warns
        python validators/topic_backlog.py backlog.yml --strict   # errors
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE

ALLOWED_KIND = {"deepen", "adjacent"}
ALLOWED_PRIORITY = {"P0", "P1", "P2"}
ALLOWED_STATUS = {"proposed", "planned", "researched", "dropped"}

REQUIRED_FIELDS = (
    "topic_id",
    "title",
    "kind",
    "track",
    "priority",
    "rationale",
    "claim_family_seeds",
    "status",
)
OPTIONAL_STRING_FIELDS = ("source_volume", "notes")
NULLABLE_STRING_FIELDS = ("dossier_path",)
TOP_LEVEL_REQUIRED = ("schema_version", "source_corpus", "generated_at")

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
URL_PATTERN = re.compile(rf"^{URL_RE}$")

MIN_CLAIM_FAMILY_SEEDS = 3
BOTH_KINDS_THRESHOLD = 8  # ≥ this many entries triggers the shape heuristics
P0_INFLATION_RATIO = 0.6


def _is_date_or_nonempty_str(value: object) -> bool:
    """True for a datetime.date (PyYAML auto-parses unquoted YYYY-MM-DD) or a
    non-empty string. Date fields tolerate both quoted and unquoted YAML."""
    if isinstance(value, datetime.date):
        return True
    return isinstance(value, str) and bool(value.strip())


def _shape_warnings(entries: list[dict]) -> list[str]:
    """Detect lazy one-axis mines + scoring that never ran.

    Only fires at ≥BOTH_KINDS_THRESHOLD entries — a small hand-curated backlog
    is legitimately allowed to be one-sided.
    """
    warnings: list[str] = []
    if len(entries) < BOTH_KINDS_THRESHOLD:
        return warnings

    kinds = {e.get("kind") for e in entries if isinstance(e.get("kind"), str)}
    if kinds and not ({"deepen", "adjacent"} <= kinds):
        warnings.append(
            f"WARN one-axis backlog: {len(entries)} entries but only kind(s) "
            f"{sorted(kinds)} present. /topic-discovery must surface BOTH "
            f"'deepen' and 'adjacent'. --strict promotes to error"
        )

    priorities = [e.get("priority") for e in entries if isinstance(e.get("priority"), str)]
    if priorities and len(set(priorities)) == 1:
        warnings.append(
            f"WARN flat priorities: all {len(priorities)} entries are "
            f"{priorities[0]!r}. Scoring should produce a spread (P0/P1/P2). "
            f"--strict promotes to error"
        )

    if priorities:
        p0_ratio = priorities.count("P0") / len(priorities)
        if p0_ratio > P0_INFLATION_RATIO:
            warnings.append(
                f"WARN P0 inflation: {p0_ratio:.0%} of entries are P0 "
                f"(> {P0_INFLATION_RATIO:.0%}). Reserve P0 for research-first "
                f"topics. --strict promotes to error"
            )

    return warnings


def _validate_entry(entry: dict, loc: str, seen: set[str]) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"{loc}: missing required field '{field}'")

    # topic_id: kebab + unique
    topic_id = entry.get("topic_id")
    if isinstance(topic_id, str):
        if not KEBAB_RE.match(topic_id):
            errors.append(f"{loc}.topic_id: {topic_id!r} is not kebab-case")
        if topic_id in seen:
            errors.append(f"{loc}: duplicate topic_id {topic_id!r}")
        seen.add(topic_id)
    elif "topic_id" in entry:
        errors.append(f"{loc}.topic_id: must be a string")

    # non-empty string fields
    for field in ("title", "rationale"):
        value = entry.get(field)
        if field in entry and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{loc}.{field}: must be a non-empty string")

    # track: required, int or non-empty string
    if "track" in entry:
        track = entry["track"]
        if isinstance(track, bool) or not isinstance(track, (int, str)):
            errors.append(f"{loc}.track: must be an int or string")
        elif isinstance(track, str) and not track.strip():
            errors.append(f"{loc}.track: empty string; omit or set a value")

    # enums
    kind = entry.get("kind")
    if isinstance(kind, str) and kind not in ALLOWED_KIND:
        errors.append(f"{loc}.kind: {kind!r} not in {sorted(ALLOWED_KIND)}")
    priority = entry.get("priority")
    if isinstance(priority, str) and priority not in ALLOWED_PRIORITY:
        errors.append(f"{loc}.priority: {priority!r} not in {sorted(ALLOWED_PRIORITY)}")
    status = entry.get("status")
    if isinstance(status, str) and status not in ALLOWED_STATUS:
        errors.append(f"{loc}.status: {status!r} not in {sorted(ALLOWED_STATUS)}")

    # claim_family_seeds: list of ≥3 non-empty strings
    seeds = entry.get("claim_family_seeds")
    if "claim_family_seeds" in entry:
        if not isinstance(seeds, list):
            errors.append(f"{loc}.claim_family_seeds: must be a list")
        elif len(seeds) < MIN_CLAIM_FAMILY_SEEDS:
            errors.append(
                f"{loc}.claim_family_seeds: has {len(seeds)}, need at least "
                f"{MIN_CLAIM_FAMILY_SEEDS} (seeds /research-plan's taxonomy)"
            )
        elif not all(isinstance(s, str) and s.strip() for s in seeds):
            errors.append(
                f"{loc}.claim_family_seeds: every seed must be a non-empty string"
            )

    # conditional: deepen requires source_volume
    if kind == "deepen":
        source_volume = entry.get("source_volume")
        if not isinstance(source_volume, str) or not source_volume.strip():
            errors.append(f"{loc}: deepen entry requires source_volume")

    # optional plain-string fields: non-empty when present
    for field in OPTIONAL_STRING_FIELDS:
        if field in entry:
            value = entry[field]
            if not isinstance(value, str):
                errors.append(f"{loc}.{field}: must be a string when present")
            elif not value.strip():
                errors.append(
                    f"{loc}.{field}: when present, must be non-empty "
                    f"(omit the field rather than use empty string)"
                )

    # lifecycle string fields: absent or null = not set; else non-empty string
    for field in NULLABLE_STRING_FIELDS:
        if field in entry and entry[field] is not None:
            value = entry[field]
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"{loc}.{field}: must be a non-empty string or null"
                )

    # researched_at: absent or null = not set; else a date or non-empty string
    if "researched_at" in entry and entry["researched_at"] is not None:
        if not _is_date_or_nonempty_str(entry["researched_at"]):
            errors.append(
                f"{loc}.researched_at: must be a date, non-empty string, or null"
            )

    # source_los: list of non-empty strings
    if "source_los" in entry:
        los = entry["source_los"]
        if not isinstance(los, list) or not all(
            isinstance(x, str) and x.strip() for x in los
        ):
            errors.append(f"{loc}.source_los: must be a list of non-empty strings")

    # seed_sources: list of valid http(s) URLs
    if "seed_sources" in entry:
        sources = entry["seed_sources"]
        if not isinstance(sources, list):
            errors.append(f"{loc}.seed_sources: must be a list")
        else:
            for k, url in enumerate(sources):
                if not isinstance(url, str) or not URL_PATTERN.match(url.strip()):
                    errors.append(
                        f"{loc}.seed_sources[{k}]: not a valid http(s) URL: {url!r}"
                    )

    return errors


def validate(path: Path, *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(data, dict) or "entries" not in data:
        return ["top-level must be a mapping with key 'entries:'"]

    for field in TOP_LEVEL_REQUIRED:
        value = data.get(field)
        if field not in data:
            errors.append(f"missing top-level field '{field}'")
        elif field == "schema_version":
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append("top-level 'schema_version' must be an int")
        elif field == "generated_at":
            if not _is_date_or_nonempty_str(value):
                errors.append(
                    "top-level 'generated_at' must be a date or non-empty string"
                )
        elif not isinstance(value, str) or not value.strip():
            errors.append(f"top-level '{field}' must be a non-empty string")

    entries = data["entries"]
    if not isinstance(entries, list) or not entries:
        return ["'entries' must be a non-empty list"]

    seen: set[str] = set()
    for idx, entry in enumerate(entries):
        loc = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: must be a mapping")
            continue
        errors.extend(_validate_entry(entry, loc, seen))

    only_dicts = [e for e in entries if isinstance(e, dict)]
    warnings = _shape_warnings(only_dicts)
    if warnings:
        if strict:
            errors.extend(warnings)
        else:
            for w in warnings:
                print(f"  - {w}", file=sys.stderr)

    return errors


def _cli_with_strict(argv: list[str]) -> int:
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
