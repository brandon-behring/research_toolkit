"""Validate strict-live v2 evidence_ledger.yml."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators._common import URL_RE
from validators.v2_common import (
    ALLOWED_RIGHTS_STATUS,
    ALLOWED_VERIFICATION_METHODS,
    is_v3_mapping,
    load_yaml_mapping,
    parse_iso_date,
    validate_nonempty_string,
    validate_strict_live_top,
    validate_string_list,
    verify_excerpt_anchor,
)

URL_PATTERN = re.compile(rf"^{URL_RE}$")
ALLOWED_SOURCE_TYPES = {
    "paper",
    "dataset",
    "repo",
    "vendor",
    "standard",
    "policy",
    "benchmark",
    "leaderboard",
    "blog",
    "api",
    "other",
}
ALLOWED_SOURCE_QUALITY = {"primary", "official", "secondary", "user_note"}
ALLOWED_EVIDENCE_ROLES = {
    "supports",
    "contradicts",
    "qualifies",
    "defines",
    "dates",
    "identifies",
    "mentions",  # v3: weak link, weaker than supports (Scite-style)
}
ALLOWED_EVIDENCE_ROLE_STRENGTHS = {"full", "partial", "none"}  # v3 only
ALLOWED_EXTRACTION_METHODS = {
    "verbatim_match",       # exact span in cache; substring + sha256 validated
    "paraphrase",           # claim derived from cache content but not verbatim
    "llm_inferred",         # synthesis; requires non-empty inference_chain
    "propagated_from_child",  # inherited from another evidence record
    "user_asserted",        # user takes responsibility
    "manual_override",      # requires source_quality: user_note
}
ALLOWED_CONFIDENCE_DOMAIN_LEVELS = {"high", "moderate", "low"}
EXTRACTION_METHOD_CAPS = {
    "verbatim_match": 1.0,
    "paraphrase": 0.85,
    "user_asserted": 0.95,
    "llm_inferred": 0.60,
    "propagated_from_child": 0.50,
    "manual_override": 1.0,  # user-controlled, but source_quality must be user_note
}
REQUIRED_ENTRY_FIELDS = (
    "evidence_id",
    "source_url",
    "source_type",
    "source_quality",
    "retrieved_at",
    "verification_method",
    "cache_ids",
    "supports",
    "excerpt",
    "rights_status",
)


def _validate_support(
    support: Any,
    *,
    loc: str,
    is_v3: bool = False,
    entry_source_quality: str | None = None,
    entry_excerpt: str | None = None,
    cache_entries_by_id: dict[str, Any] | None = None,
    manifest_path: Path | None = None,
    cache_root: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(support, dict):
        return [f"{loc}: must be a mapping"]
    for field in ("claim_id", "field_path", "evidence_role"):
        if field not in support:
            errors.append(f"{loc}: missing required field '{field}'")
        else:
            err = validate_nonempty_string(support[field], f"{loc}.{field}")
            if err:
                errors.append(err)
    role = support.get("evidence_role")
    if isinstance(role, str) and role not in ALLOWED_EVIDENCE_ROLES:
        errors.append(f"{loc}.evidence_role: {role!r} not in {sorted(ALLOWED_EVIDENCE_ROLES)}")

    if not is_v3:
        return errors

    # v3-only: per-link verification fields are required
    method = support.get("extraction_method")
    if method is None:
        errors.append(f"{loc}: missing required v3 field 'extraction_method'")
    elif method not in ALLOWED_EXTRACTION_METHODS:
        errors.append(
            f"{loc}.extraction_method: {method!r} not in {sorted(ALLOWED_EXTRACTION_METHODS)}"
        )

    link_conf = support.get("link_confidence")
    if link_conf is None:
        errors.append(f"{loc}: missing required v3 field 'link_confidence'")
    elif not isinstance(link_conf, (int, float)) or not 0 <= float(link_conf) <= 1:
        errors.append(f"{loc}.link_confidence: must be a number from 0 to 1")
    elif isinstance(method, str) and method in EXTRACTION_METHOD_CAPS:
        cap = EXTRACTION_METHOD_CAPS[method]
        if float(link_conf) > cap:
            errors.append(
                f"{loc}.link_confidence: {link_conf} exceeds cap {cap} for "
                f"extraction_method={method!r}"
            )

    strength = support.get("evidence_role_strength")
    if strength is None:
        errors.append(f"{loc}: missing required v3 field 'evidence_role_strength'")
    elif strength not in ALLOWED_EVIDENCE_ROLE_STRENGTHS:
        errors.append(
            f"{loc}.evidence_role_strength: {strength!r} not in {sorted(ALLOWED_EVIDENCE_ROLE_STRENGTHS)}"
        )

    # extraction_method-specific requirements
    if method == "verbatim_match":
        anchor = support.get("excerpt_anchor")
        if not isinstance(anchor, dict):
            errors.append(
                f"{loc}: extraction_method=verbatim_match requires excerpt_anchor mapping "
                f"(cache_id + text_path_offset + sha256_of_span)"
            )
        elif cache_entries_by_id is not None and entry_excerpt is not None and manifest_path is not None:
            for field in ("cache_id", "text_path_offset", "sha256_of_span"):
                if field not in anchor:
                    errors.append(f"{loc}.excerpt_anchor: missing required field {field!r}")
            if all(f in anchor for f in ("cache_id", "text_path_offset", "sha256_of_span")):
                errors.extend(
                    verify_excerpt_anchor(
                        excerpt=entry_excerpt,
                        cache_id=anchor["cache_id"],
                        text_path_offset=anchor["text_path_offset"],
                        sha256_of_span=anchor["sha256_of_span"],
                        cache_entries_by_id=cache_entries_by_id,
                        manifest_path=manifest_path,
                        cache_root=cache_root,
                        loc=loc,
                    )
                )

    elif method == "llm_inferred":
        chain = support.get("inference_chain")
        if not isinstance(chain, list) or not chain:
            errors.append(
                f"{loc}: extraction_method=llm_inferred requires non-empty inference_chain "
                f"(list of evidence_ids that ground this inference)"
            )

    elif method == "propagated_from_child":
        chain = support.get("inference_chain")
        if not isinstance(chain, list) or not chain:
            errors.append(
                f"{loc}: extraction_method=propagated_from_child requires non-empty inference_chain"
            )

    elif method == "manual_override":
        if entry_source_quality != "user_note":
            errors.append(
                f"{loc}: extraction_method=manual_override requires source_quality=user_note "
                f"(entry has source_quality={entry_source_quality!r})"
            )

    return errors


def _validate_entry(
    entry: dict[str, Any],
    *,
    loc: str,
    is_v3: bool = False,
    cache_entries_by_id: dict[str, Any] | None = None,
    manifest_path: Path | None = None,
    cache_root: str | None = None,
) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_ENTRY_FIELDS:
        if field not in entry:
            errors.append(f"{loc}: missing required field '{field}'")

    for field in ("evidence_id", "source_url", "source_type", "source_quality", "verification_method", "excerpt", "rights_status"):
        if field in entry:
            err = validate_nonempty_string(entry[field], f"{loc}.{field}")
            if err:
                errors.append(err)

    if isinstance(entry.get("source_url"), str) and not URL_PATTERN.match(entry["source_url"]):
        errors.append(f"{loc}.source_url: not a valid http(s) URL: {entry['source_url']!r}")

    if "retrieved_at" in entry:
        _, err = parse_iso_date(entry["retrieved_at"], f"{loc}.retrieved_at")
        if err:
            errors.append(err)

    source_type = entry.get("source_type")
    if isinstance(source_type, str) and source_type not in ALLOWED_SOURCE_TYPES:
        errors.append(f"{loc}.source_type: {source_type!r} not in {sorted(ALLOWED_SOURCE_TYPES)}")

    source_quality = entry.get("source_quality")
    if isinstance(source_quality, str) and source_quality not in ALLOWED_SOURCE_QUALITY:
        errors.append(
            f"{loc}.source_quality: {source_quality!r} not in {sorted(ALLOWED_SOURCE_QUALITY)}"
        )

    method = entry.get("verification_method")
    if isinstance(method, str) and method not in ALLOWED_VERIFICATION_METHODS:
        errors.append(
            f"{loc}.verification_method: {method!r} not in {sorted(ALLOWED_VERIFICATION_METHODS)}"
        )

    rights = entry.get("rights_status")
    if isinstance(rights, str) and rights not in ALLOWED_RIGHTS_STATUS:
        errors.append(f"{loc}.rights_status: {rights!r} not in {sorted(ALLOWED_RIGHTS_STATUS)}")

    if "cache_ids" in entry:
        errors.extend(validate_string_list(entry["cache_ids"], f"{loc}.cache_ids"))

    supports = entry.get("supports")
    if not isinstance(supports, list) or not supports:
        errors.append(f"{loc}.supports: must be a non-empty list")
    elif isinstance(supports, list):
        entry_excerpt = entry.get("excerpt") if isinstance(entry.get("excerpt"), str) else None
        entry_source_quality = (
            entry.get("source_quality") if isinstance(entry.get("source_quality"), str) else None
        )
        for idx, support in enumerate(supports):
            errors.extend(
                _validate_support(
                    support,
                    loc=f"{loc}.supports[{idx}]",
                    is_v3=is_v3,
                    entry_source_quality=entry_source_quality,
                    entry_excerpt=entry_excerpt,
                    cache_entries_by_id=cache_entries_by_id,
                    manifest_path=manifest_path,
                    cache_root=cache_root,
                )
            )

    if "confidence" in entry:
        confidence = entry["confidence"]
        if not isinstance(confidence, dict):
            errors.append(f"{loc}.confidence: must be a mapping when present")
        else:
            score = confidence.get("score")
            if score is not None and not (
                isinstance(score, (int, float)) and 0 <= float(score) <= 1
            ):
                errors.append(f"{loc}.confidence.score: must be a number from 0 to 1")

            # v3 optional: confidence.domains{} multi-domain GRADE-style
            domains = confidence.get("domains")
            if domains is not None:
                if not isinstance(domains, dict):
                    errors.append(f"{loc}.confidence.domains: must be a mapping when present")
                else:
                    for dkey, dval in domains.items():
                        if dval not in ALLOWED_CONFIDENCE_DOMAIN_LEVELS:
                            errors.append(
                                f"{loc}.confidence.domains.{dkey}: {dval!r} not in "
                                f"{sorted(ALLOWED_CONFIDENCE_DOMAIN_LEVELS)}"
                            )

    return errors


def validate(path: Path) -> list[str]:
    data, errors = load_yaml_mapping(path)
    if errors:
        return errors
    assert data is not None

    errors.extend(validate_strict_live_top(data))
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("'entries' must be a non-empty list")
        return errors

    is_v3 = is_v3_mapping(data)
    # For v3, attempt to load the sibling cache_manifest.yml so excerpt_anchor
    # substring validation can run. If not present, v3 is still validated for
    # field shape but substring checks are skipped (with a warning).
    cache_entries_by_id: dict[str, Any] | None = None
    manifest_path: Path | None = None
    cache_root_value: str | None = None
    if is_v3:
        manifest_candidate = path.parent / "cache_manifest.yml"
        if manifest_candidate.exists():
            manifest_path = manifest_candidate
            mdata, _ = load_yaml_mapping(manifest_candidate)
            if mdata is not None:
                cache_entries_by_id = {
                    e.get("cache_id"): e
                    for e in (mdata.get("entries") or [])
                    if isinstance(e, dict) and isinstance(e.get("cache_id"), str)
                }
                if isinstance(mdata.get("cache_root"), str):
                    cache_root_value = mdata["cache_root"]
        # If manifest is missing, the per-link verbatim_match checks will
        # skip substring validation (only field-shape errors will surface).

    seen: set[str] = set()
    for idx, entry in enumerate(entries):
        loc = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: must be a mapping")
            continue
        evidence_id = entry.get("evidence_id")
        if isinstance(evidence_id, str):
            if evidence_id in seen:
                errors.append(f"{loc}: duplicate evidence_id {evidence_id!r}")
            seen.add(evidence_id)
        errors.extend(
            _validate_entry(
                entry,
                loc=loc,
                is_v3=is_v3,
                cache_entries_by_id=cache_entries_by_id,
                manifest_path=manifest_path,
                cache_root=cache_root_value,
            )
        )
    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <evidence_ledger.yml>", file=sys.stderr)
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
