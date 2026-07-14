"""Validate strict-live v2 cache_manifest.yml."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE
from research_toolkit.retrieval_security import (
    RetrievalSecurityError,
    durable_value_errors,
    validate_record_url,
)
from validators.v2_common import (
    ALLOWED_RIGHTS_STATUS,
    load_yaml_mapping,
    parse_iso_date,
    resolve_cache_path,
    validate_nonempty_string,
    validate_strict_live_top,
)

import re

URL_PATTERN = re.compile(rf"^{URL_RE}$")
# v2.3 extends extraction_status with rich/ok_text_only/degraded (#11 PDF cascade)
# and stub (#10 JS-shell detection). All additive — readers that don't know the
# new values can treat them as opaque strings.
ALLOWED_EXTRACTION_STATUS = {
    "ok",
    "rich",
    "ok_text_only",
    "degraded",
    "partial",
    "raw_only",
    "failed",
    "stub",
}
ALLOWED_RECORD_TYPES = {"capture", "revisit", "metadata", "conversion"}
ALLOWED_REVISIT_PROFILES = {"server-not-modified", "identical-payload-digest"}
# Current captures use the reviewed static HTTP boundary only. Historical
# browser-rendered entries must be quarantined outside a current manifest.
ALLOWED_FETCH_METHODS = {"urllib"}
ALLOWED_VISIBILITY = {"public", "authenticated", "private"}
# v2.1: WARC-inspired revisit records save storage on re-fetch when the
# remote content hasn't changed. A revisit record stores only the pointer
# back to the original capture (refers_to_cache_id) plus the http response
# metadata that justifies the revisit decision.
REQUIRED_ENTRY_FIELDS_CAPTURE = (
    "cache_id",
    "source_url",
    "fetched_at",
    "content_type",
    "bytes",
    "sha256",
    "raw_path",
    "text_path",
    "metadata_path",
    "restricted",
    "rights_status",
    "extraction_status",
)
REQUIRED_ENTRY_FIELDS_REVISIT = (
    "cache_id",
    "source_url",
    "fetched_at",
    "record_type",
    "refers_to_cache_id",
    "revisit_profile",
)
# Kept for backward compat — defaults to capture record fields
REQUIRED_ENTRY_FIELDS = REQUIRED_ENTRY_FIELDS_CAPTURE


def _url_fingerprint_errors(value: Any, loc: str) -> list[str]:
    """Retain the internal name while enforcing the full durable-value scan."""
    return durable_value_errors(value, loc)


def _validate_access_metadata(entry: dict[str, Any], loc: str) -> list[str]:
    """Validate access and rights metadata conservatively."""
    errors: list[str] = []
    if "restricted" in entry and not isinstance(entry["restricted"], bool):
        errors.append(f"{loc}.restricted: must be boolean")
    rights = entry.get("rights_status")
    if rights is not None and rights not in ALLOWED_RIGHTS_STATUS:
        errors.append(
            f"{loc}.rights_status: {rights!r} not in {sorted(ALLOWED_RIGHTS_STATUS)}"
        )
    visibility = entry.get("visibility")
    if visibility is not None and visibility not in ALLOWED_VISIBILITY:
        errors.append(
            f"{loc}.visibility: {visibility!r} not in {sorted(ALLOWED_VISIBILITY)}"
        )
    restricted = entry.get("restricted")
    if restricted is False:
        # ``restricted`` controls whether a cached body may leave the local
        # cache.  Reachability and reuse permission are independent: unless
        # both are explicitly public, the conservative representation is
        # restricted.  Missing legacy visibility is therefore treated as
        # unknown, not silently promoted to public.
        if rights != "public":
            errors.append(
                f"{loc}.restricted: must be true when rights_status is "
                f"{rights!r}; only explicit 'public' rights permit false"
            )
        if visibility != "public":
            errors.append(
                f"{loc}.restricted: must be true when visibility is "
                f"{visibility!r}; only explicit 'public' visibility permits false"
            )
    if "license" in entry:
        error = validate_nonempty_string(entry["license"], f"{loc}.license")
        if error:
            errors.append(error)
    errors.extend(_url_fingerprint_errors(entry, loc))
    return errors


def access_policy(entry: dict[str, Any]) -> dict[str, Any]:
    """Return the explicit legacy-cache policy propagated to metadata exports.

    Callers must validate the entry first.  Defaults are deliberately
    conservative so old records without an access field can never be
    interpreted as permission to redistribute a cached body.
    """
    rights = entry.get("rights_status")
    visibility = entry.get("visibility")
    restricted = entry.get("restricted")
    return {
        "vocabulary": "strict-live-cache-v2",
        "rights_status": rights if rights in ALLOWED_RIGHTS_STATUS else "unknown",
        "visibility": visibility if visibility in ALLOWED_VISIBILITY else "unknown",
        "restricted": restricted if isinstance(restricted, bool) else True,
        "body_exported": False,
    }


def load_access_policies(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Load cache-id access policy without requiring local cache bodies.

    Synthesis exports contain identifiers, hashes, and research metadata, not
    cached files.  This focused loader lets that metadata-only operation
    enforce rights contradictions even when the private cache is offline.
    Full cache validation remains the job of :func:`validate`.
    """
    data, errors = load_yaml_mapping(path)
    if errors:
        return {}, errors
    assert data is not None
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        return {}, ["'entries' must be a non-empty list"]

    policies: dict[str, dict[str, Any]] = {}
    for idx, entry in enumerate(entries):
        loc = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: must be a mapping")
            continue
        cache_id = entry.get("cache_id")
        error = validate_nonempty_string(cache_id, f"{loc}.cache_id")
        if error:
            errors.append(error)
            continue
        assert isinstance(cache_id, str)
        if cache_id in policies:
            errors.append(f"{loc}: duplicate cache_id {cache_id!r}")
            continue
        errors.extend(_validate_access_metadata(entry, loc))
        policies[cache_id] = access_policy(entry)
    return policies, errors


def _resolve(path: Path, value: str, cache_root: str | None = None) -> Path:
    """Resolve a path value from a manifest entry.

    Thin wrapper around ``v2_common.resolve_cache_path()`` (shared between
    cache_manifest.py and evidence_ledger.py per v2_common.py).

    v2.3+: when ``cache_root`` is set, relative path values are resolved
    against the EXPANDED cache_root (supports portable manifests where the
    cache lives in a shared location like ~/Claude/research_cache while the
    manifest is committed in a project repo elsewhere).

    v2.3.x: when cache_root is set, falls back to ``manifest_path.parent`` if
    the file doesn't exist in cache_root — supports mixed-cache-location
    dossiers where derived artifacts (pdftotext body_text/body_meta) live
    dossier-local per ADR-049 body-quote anchoring discipline. Closes #14.

    Falls back to manifest-co-located resolution (the v2.0-v2.2 behavior) when
    cache_root is not set. Absolute / ~-prefixed values always pass through
    expanduser.
    """
    return resolve_cache_path(value, manifest_path=path, cache_root=cache_root)


def _path_is_portable(value: str) -> bool:
    """v2.3+: writer-side guard. Manifest path values must be relative.

    Absolute paths (`/foo/bar`) and ~-prefixed paths (`~/Claude/...`) are not
    portable across machines. Validator rejects these as a regression guard for
    issue #13 (writer-side fix for #2 path portability).
    """
    if not value:
        return True
    return not (value.startswith("/") or value.startswith("~"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_entry(
    entry: dict[str, Any],
    *,
    loc: str,
    manifest_path: Path,
    cache_root: str | None = None,
    capture_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    record_type = entry.get("record_type", "capture")
    if record_type not in ALLOWED_RECORD_TYPES:
        errors.append(
            f"{loc}.record_type: {record_type!r} not in {sorted(ALLOWED_RECORD_TYPES)}"
        )

    is_revisit = record_type == "revisit"

    required_fields = (
        REQUIRED_ENTRY_FIELDS_REVISIT if is_revisit else REQUIRED_ENTRY_FIELDS_CAPTURE
    )
    for field in required_fields:
        if field not in entry:
            errors.append(f"{loc}: missing required field '{field}'")

    errors.extend(_validate_access_metadata(entry, loc))

    for field in ("source_url", "final_url"):
        value = entry.get(field)
        if value is None:
            continue
        error = validate_nonempty_string(value, f"{loc}.{field}")
        if error:
            errors.append(error)
            continue
        assert isinstance(value, str)
        if not URL_PATTERN.match(value):
            errors.append(f"{loc}.{field}: not a valid http(s) URL: {value!r}")
            continue
        try:
            validate_record_url(value, allow_public_query=True)
        except RetrievalSecurityError as exc:
            errors.append(f"{loc}.{field}: unsafe durable URL: {exc}")

    if is_revisit:
        profile = entry.get("revisit_profile")
        if profile is not None and profile not in ALLOWED_REVISIT_PROFILES:
            errors.append(
                f"{loc}.revisit_profile: {profile!r} not in {sorted(ALLOWED_REVISIT_PROFILES)}"
            )
        refers_to = entry.get("refers_to_cache_id")
        if isinstance(refers_to, str) and capture_ids is not None:
            if refers_to not in capture_ids:
                import difflib

                close = difflib.get_close_matches(
                    refers_to, capture_ids, n=2, cutoff=0.6
                )
                hint = f" (closest match: {close})" if close else ""
                errors.append(
                    f"{loc}.refers_to_cache_id: {refers_to!r} not found among "
                    f"capture entries in this manifest{hint}"
                )
        # Revisit records skip the SHA-256/file existence checks below
        return errors

    for field in (
        "cache_id",
        "source_url",
        "content_type",
        "sha256",
        "raw_path",
        "text_path",
        "metadata_path",
    ):
        if field in entry:
            err = validate_nonempty_string(entry[field], f"{loc}.{field}")
            if err:
                errors.append(err)

    if "fetched_at" in entry:
        _, err = parse_iso_date(entry["fetched_at"], f"{loc}.fetched_at")
        if err:
            errors.append(err)

    # published_online (optional, additive): ISO YYYY-MM-DD date the content first
    # appeared online (arXiv v1 / Crossref issued / page publish date). Display-only
    # content-age anchor, distinct from fetched_at; never required. Checked only
    # when present.
    if entry.get("published_online") is not None:
        _, err = parse_iso_date(entry["published_online"], f"{loc}.published_online")
        if err:
            errors.append(err)

    if "bytes" in entry:
        if not isinstance(entry["bytes"], int) or entry["bytes"] < 0:
            errors.append(f"{loc}.bytes: must be a non-negative integer")

    if isinstance(entry.get("sha256"), str) and not re.fullmatch(
        r"[0-9a-f]{64}", entry["sha256"]
    ):
        errors.append(f"{loc}.sha256: must be 64 lowercase hex characters")

    extraction = entry.get("extraction_status")
    if extraction is not None and extraction not in ALLOWED_EXTRACTION_STATUS:
        errors.append(
            f"{loc}.extraction_status: {extraction!r} not in {sorted(ALLOWED_EXTRACTION_STATUS)}"
        )

    # v2.3 optional field — list of human-readable warnings from cache_source.py
    # explaining why a non-ideal extraction_status was set.
    extraction_warnings = entry.get("extraction_warnings")
    if extraction_warnings is not None:
        if not isinstance(extraction_warnings, list):
            errors.append(f"{loc}.extraction_warnings: must be a list of strings")
        else:
            for i, w in enumerate(extraction_warnings):
                if not isinstance(w, str):
                    errors.append(f"{loc}.extraction_warnings[{i}]: must be a string")

    fetch_method = entry.get("fetch_method")
    if fetch_method is not None and fetch_method not in ALLOWED_FETCH_METHODS:
        errors.append(
            f"{loc}.fetch_method: {fetch_method!r} not in {sorted(ALLOWED_FETCH_METHODS)}"
        )

    raw_value = entry.get("raw_path")
    if isinstance(raw_value, str) and raw_value.strip():
        if not _path_is_portable(raw_value):
            errors.append(
                f"{loc}.raw_path: must be relative to cache_root (got {raw_value!r}); "
                f"absolute / ~-prefixed paths are not portable across machines. "
                f"Run scripts/migrate_manifest_paths.py to fix."
            )
        raw_path = _resolve(manifest_path, raw_value, cache_root=cache_root)
        if not raw_path.exists():
            errors.append(f"{loc}.raw_path: file does not exist: {raw_value}")
        elif raw_path.is_file():
            actual_hash = _sha256(raw_path)
            if isinstance(entry.get("sha256"), str) and actual_hash != entry["sha256"]:
                errors.append(
                    f"{loc}.sha256: expected {entry['sha256']}, actual {actual_hash}"
                )
            if (
                isinstance(entry.get("bytes"), int)
                and raw_path.stat().st_size != entry["bytes"]
            ):
                errors.append(
                    f"{loc}.bytes: expected {entry['bytes']}, actual {raw_path.stat().st_size}"
                )

    for field in ("text_path", "metadata_path"):
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            if not _path_is_portable(value):
                errors.append(
                    f"{loc}.{field}: must be relative to cache_root (got {value!r}); "
                    f"absolute / ~-prefixed paths are not portable across machines. "
                    f"Run scripts/migrate_manifest_paths.py to fix."
                )
            resolved = _resolve(manifest_path, value, cache_root=cache_root)
            if not resolved.exists():
                errors.append(f"{loc}.{field}: file does not exist: {value}")
            elif field == "metadata_path":
                try:
                    metadata = json.loads(resolved.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    errors.append(f"{loc}.metadata_path: JSON parse error: {exc}")
                else:
                    errors.extend(
                        durable_value_errors(metadata, f"{loc}.metadata_path")
                    )

    return errors


def validate(path: Path) -> list[str]:
    data, errors = load_yaml_mapping(path)
    if errors:
        return errors
    assert data is not None

    errors.extend(durable_value_errors(data, "cache_manifest"))
    errors.extend(validate_strict_live_top(data))
    cache_root_value: str | None = None
    if "cache_root" in data:
        err = validate_nonempty_string(data["cache_root"], "top-level.cache_root")
        if err:
            errors.append(err)
        elif isinstance(data["cache_root"], str):
            cache_root_value = data["cache_root"]

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("'entries' must be a non-empty list")
        return errors

    # First pass: collect capture cache_ids for revisit cross-reference
    capture_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("record_type", "capture") == "capture":
            cid = entry.get("cache_id")
            if isinstance(cid, str):
                capture_ids.add(cid)

    seen: set[str] = set()
    for idx, entry in enumerate(entries):
        loc = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: must be a mapping")
            continue
        cache_id = entry.get("cache_id")
        if isinstance(cache_id, str):
            if cache_id in seen:
                errors.append(f"{loc}: duplicate cache_id {cache_id!r}")
            seen.add(cache_id)
        errors.extend(
            _validate_entry(
                entry,
                loc=loc,
                manifest_path=path,
                cache_root=cache_root_value,
                capture_ids=capture_ids,
            )
        )
    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <cache_manifest.yml>", file=sys.stderr)
        return 2
    target = Path(argv[1]).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    errors = validate(target)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(f"VALIDATION FAILED: {len(errors)} error(s) in {target}", file=sys.stderr)
        return 1
    print(f"OK: {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
