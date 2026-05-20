"""Project-level strict-live freshness validator."""
from __future__ import annotations

from datetime import date, datetime
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators import bib_ledger, cache_manifest, dataset_ledger, evidence_ledger
from validators.v2_common import (
    is_v2_mapping,
    stale_error_for_entry,
)


def _load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _entries(path: Path) -> list[dict[str, Any]]:
    data = _load_yaml(path)
    if not data:
        return []
    entries = data.get("entries")
    return [e for e in entries if isinstance(e, dict)] if isinstance(entries, list) else []


def _ids_from_evidence(path: Path) -> set[str]:
    return {
        e["evidence_id"]
        for e in _entries(path)
        if isinstance(e.get("evidence_id"), str) and e["evidence_id"].strip()
    }


def _ids_from_cache(path: Path) -> set[str]:
    return {
        e["cache_id"]
        for e in _entries(path)
        if isinstance(e.get("cache_id"), str) and e["cache_id"].strip()
    }


def _strict_live_files(project_dir: Path) -> list[Path]:
    candidates = [
        project_dir / "bib_ledger.yml",
        project_dir / "dataset_ledger.yml",
    ]
    return [p for p in candidates if p.exists() and is_v2_mapping(_load_yaml(p) or {})]


def validate(
    path: Path, *, strict: bool = False, today: date | None = None
) -> list[str]:
    """Validate freshness and evidence/cache references for a v2 project directory.

    Default mode reports stale entries to stderr as warnings. Strict mode returns
    stale entries as errors.
    """
    if path.is_file():
        return [f"expected a project directory, got file: {path}"]

    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []

    ledger_paths = _strict_live_files(path)
    if not ledger_paths:
        return ["no v2 strict-live ledger found (expected bib_ledger.yml or dataset_ledger.yml)"]

    evidence_path = path / "evidence_ledger.yml"
    cache_path = path / "cache_manifest.yml"

    if not evidence_path.exists():
        errors.append("missing evidence_ledger.yml")
    else:
        errors.extend(f"evidence_ledger.yml: {e}" for e in evidence_ledger.validate(evidence_path))

    if not cache_path.exists():
        errors.append("missing cache_manifest.yml")
    else:
        errors.extend(f"cache_manifest.yml: {e}" for e in cache_manifest.validate(cache_path))

    evidence_ids = _ids_from_evidence(evidence_path) if evidence_path.exists() else set()
    cache_ids = _ids_from_cache(cache_path) if cache_path.exists() else set()

    for ledger_path in ledger_paths:
        validator = dataset_ledger.validate if ledger_path.name == "dataset_ledger.yml" else bib_ledger.validate
        errors.extend(f"{ledger_path.name}: {e}" for e in validator(ledger_path))
        for idx, entry in enumerate(_entries(ledger_path)):
            loc = f"{ledger_path.name}.entries[{idx}]"
            stale = stale_error_for_entry(entry, loc=loc, today=today)
            if stale:
                if strict:
                    errors.append(stale)
                else:
                    warnings.append(f"WARN {stale}")

            for evidence_id in entry.get("evidence_ids", []) or []:
                if isinstance(evidence_id, str) and evidence_id not in evidence_ids:
                    suggestions = _closest_matches(evidence_id, evidence_ids)
                    hint = f" (closest match: {suggestions})" if suggestions else ""
                    errors.append(
                        f"{loc}.evidence_ids: {evidence_id!r} not found in evidence_ledger.yml{hint}"
                    )
            for cache_id in entry.get("cache_ids", []) or []:
                if isinstance(cache_id, str) and cache_id not in cache_ids:
                    suggestions = _closest_matches(cache_id, cache_ids)
                    hint = f" (closest match: {suggestions})" if suggestions else ""
                    errors.append(
                        f"{loc}.cache_ids: {cache_id!r} not found in cache_manifest.yml{hint}"
                    )

    if warnings and not strict:
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)
    return errors


def _closest_matches(value: str, candidates: set[str], n: int = 2) -> list[str]:
    """Return up to n closest matches from candidates using difflib ratio."""
    import difflib
    return difflib.get_close_matches(value, candidates, n=n, cutoff=0.6)


def _cli(argv: list[str]) -> int:
    strict = False
    today: date | None = None
    args = argv[1:]
    if "--strict" in args:
        strict = True
        args = [a for a in args if a != "--strict"]
    if "--today" in args:
        i = args.index("--today")
        try:
            today = datetime.strptime(args[i + 1], "%Y-%m-%d").date()
        except (IndexError, ValueError):
            print("--today requires YYYY-MM-DD", file=sys.stderr)
            return 2
        args = args[:i] + args[i + 2 :]
    if len(args) != 1:
        print(f"usage: {Path(argv[0]).name} [--strict] [--today YYYY-MM-DD] <project_dir>", file=sys.stderr)
        return 2
    target = Path(args[0]).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    errors = validate(target, strict=strict, today=today)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(f"VALIDATION FAILED: {len(errors)} error(s) in {target}", file=sys.stderr)
        return 1
    print(f"OK: {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
