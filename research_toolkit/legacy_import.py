"""One-way, idempotent importer from strict-live v2/v3 dossier artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlsplit

import yaml

from research_toolkit import PLUGIN_VERSION, __version__
from research_toolkit.canonical import validate_dossier
from research_toolkit.contracts import SCHEMA_VERSION
from research_toolkit.retrieval_security import (
    RetrievalSecurityError,
    record_safe_url,
    validate_record_url,
)

_URL_IN_TEXT = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_PRIVATE_DIRECTORY_MODE = 0o700
_PRIVATE_FILE_MODE = 0o600


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"required legacy artifact is missing: {path.name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"legacy artifact root must be a mapping: {path.name}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise ValueError(f"required legacy artifact is missing: {path.name}") from exc
    records: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"{path.name}:{number}: record must be an object")
        records.append(item)
    return records


def _iso_datetime(value: Any, fallback: str) -> str:
    text = _record_safe_text(value or fallback)
    if "T" in text:
        return text if text.endswith("Z") or "+" in text else f"{text}Z"
    return f"{text}T00:00:00Z"


def _safe_id(value: str, prefix: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._:-]+", "_", value).strip("_.:-")
    if not normalized or not normalized[0].isalpha():
        normalized = f"item_{normalized}"
    return normalized if normalized.startswith(f"{prefix}_") else f"{prefix}_{normalized}"


def _jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in records)


def _rights_status(value: Any) -> str:
    normalized = str(value or "unknown").replace("_", "-")
    if normalized == "cache-only":
        return "restricted"
    return normalized if normalized in {"public", "private-use", "restricted"} else "unknown"


def _record_safe_url(value: Any, loc: str) -> str:
    """Return a durable redacted URL or reject an ambiguous legacy value."""
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{loc}: source URL is required")
    try:
        parsed = urlsplit(raw)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError(f"{loc}: source URL cannot be parsed safely") from exc
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"{loc}: credentials in source URLs are not allowed")
    safe = record_safe_url(raw)
    try:
        validate_record_url(safe, allow_public_query=True)
    except RetrievalSecurityError as exc:
        raise ValueError(f"{loc}: unsafe source URL: {exc}") from exc
    return safe


def _record_safe_text(value: Any) -> str:
    """Redact URL secrets embedded in free-form legacy prose."""
    text = str(value or "")

    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        trailing = ""
        while raw and raw[-1] in ".,;:!?)]}":
            trailing = raw[-1] + trailing
            raw = raw[:-1]
        return record_safe_url(raw) + trailing

    return _URL_IN_TEXT.sub(replace, text)


def _legacy_identifier(value: Any, loc: str) -> str:
    """Accept a legacy identifier only when it contains no URL material."""
    text = str(value or "")
    if _record_safe_text(text) != text:
        raise ValueError(f"{loc}: URLs are not allowed in legacy identifiers")
    return text


def _source_id(*, ordinal: int) -> str:
    """Allocate an opaque deterministic ID without trusting legacy labels."""
    return f"src_legacy_{ordinal:04d}"


def _verify_private_directory(path: Path) -> None:
    info = os.lstat(path)
    if not stat.S_ISDIR(info.st_mode):
        raise NotADirectoryError(f"import output is not a directory: {path}")
    if stat.S_IMODE(info.st_mode) != _PRIVATE_DIRECTORY_MODE:
        raise PermissionError(f"import directory must have mode 0700: {path}")


def _verify_private_file(path: Path) -> None:
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise PermissionError(f"import output is not a regular file: {path}")
    if stat.S_IMODE(info.st_mode) != _PRIVATE_FILE_MODE:
        raise PermissionError(f"import file must have mode 0600: {path}")


def _create_missing_private_directories(path: Path) -> None:
    """Create only missing ancestors, leaving an existing external parent alone."""
    missing: list[Path] = []
    current = path
    while True:
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            missing.append(current)
            parent = current.parent
            if parent == current:
                raise
            current = parent
            continue
        if not stat.S_ISDIR(info.st_mode):
            raise NotADirectoryError(f"import path parent is not a directory: {current}")
        break

    for directory in reversed(missing):
        try:
            os.mkdir(directory, _PRIVATE_DIRECTORY_MODE)
        except FileExistsError:
            # A concurrent creator still has to satisfy the checks below.
            pass
        os.chmod(directory, _PRIVATE_DIRECTORY_MODE)
        _verify_private_directory(directory)


def _ensure_private_directory_tree(root: Path, path: Path) -> None:
    """Create/tighten every importer-owned directory from ``root`` to ``path``."""
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"import path escapes private output root: {path}") from exc

    _create_missing_private_directories(root.parent)
    current = root
    for part in (Path(), *relative.parts):
        if part != Path():
            current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            try:
                os.mkdir(current, _PRIVATE_DIRECTORY_MODE)
            except FileExistsError:
                pass
        else:
            if not stat.S_ISDIR(info.st_mode):
                raise NotADirectoryError(f"import output is not a directory: {current}")
        os.chmod(current, _PRIVATE_DIRECTORY_MODE)
        _verify_private_directory(current)


def _existing_regular_bytes(path: Path) -> bytes | None:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise PermissionError(f"import output is not a regular file: {path}")
    return path.read_bytes()


def _write_idempotent(
    path: Path,
    content: bytes,
    *,
    private_root: Path,
) -> None:
    _ensure_private_directory_tree(private_root, path.parent)
    existing = _existing_regular_bytes(path)
    if existing is not None:
        if existing != content:
            raise FileExistsError(f"refusing to replace differing imported artifact: {path}")
        os.chmod(path, _PRIVATE_FILE_MODE)
        _verify_private_file(path)
        return

    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        os.fchmod(fd, _PRIVATE_FILE_MODE)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise PermissionError(f"import temporary path is not a regular file: {path}")
        if stat.S_IMODE(info.st_mode) != _PRIVATE_FILE_MODE:
            raise PermissionError(f"import temporary file must have mode 0600: {path}")
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp_path, path, follow_symlinks=False)
        except FileExistsError:
            # Preserve idempotence if a concurrent writer won the create race.
            existing = _existing_regular_bytes(path)
            if existing != content:
                raise FileExistsError(
                    f"refusing to replace differing imported artifact: {path}"
                )
            os.chmod(path, _PRIVATE_FILE_MODE)
        _verify_private_file(path)
    finally:
        if fd >= 0:
            os.close(fd)
        temp_path.unlink(missing_ok=True)


def import_legacy(legacy: Path, target: Path) -> list[Path]:
    """Import one legacy dossier, returning canonical files written or confirmed."""
    legacy = legacy.expanduser().resolve()
    target = target.expanduser().resolve()
    bib = _load_yaml(legacy / "bib_ledger.yml")
    evidence_legacy = _load_yaml(legacy / "evidence_ledger.yml")
    graph = _load_jsonl(legacy / "claim_graph.jsonl")
    topic = _record_safe_text(
        bib.get("topic") or legacy.name.removeprefix("research_") or "unknown"
    )
    current = _record_safe_text(
        bib.get("current_as_of") or bib.get("generated_at") or date.today()
    )
    imported_at = _iso_datetime(current, current)

    sources: list[dict[str, Any]] = []
    url_to_source: dict[str, str] = {}
    bib_by_url: dict[str, dict[str, Any]] = {}
    source_ordinal = 0
    for entry_index, entry in enumerate(bib.get("entries", [])):
        if not isinstance(entry, dict):
            continue
        raw_url = entry.get("primary_url")
        if not raw_url:
            continue
        url = _record_safe_url(raw_url, f"bib_ledger.yml.entries[{entry_index}].primary_url")
        if url in url_to_source:
            bib_by_url.setdefault(url, entry)
            continue
        source_ordinal += 1
        source_id = _source_id(ordinal=source_ordinal)
        url_to_source[url] = source_id
        bib_by_url[url] = entry
        host = urlparse(url).hostname or "unknown"
        sources.append(
            {
                "schema_version": SCHEMA_VERSION,
                "source_id": source_id,
                "requested_url": url,
                "canonical_url": url,
                "source_kind": _record_safe_text(
                    entry.get("claim_family") or "unknown"
                ),
                "title": _record_safe_text(
                    entry.get("title") or f"Legacy source {source_ordinal}"
                ),
                "authority_scope": "legacy-unreviewed",
                "independence_cluster": host,
                "rights_status": "unknown",
                "visibility": "unknown",
                "retrieved_at": _iso_datetime(entry.get("retrieved_at"), current),
            }
        )

    graph_claims = {
        _legacy_identifier(item.get("id"), f"claim_graph.jsonl[{item_index}].id"): item
        for item_index, item in enumerate(graph)
        if item.get("record_type") == "claim"
    }
    evidence: list[dict[str, Any]] = []
    supported_claim_ids: set[str] = set()
    for evidence_index, item in enumerate(evidence_legacy.get("entries", [])):
        if not isinstance(item, dict):
            continue
        source_url = _record_safe_url(
            item.get("source_url"),
            f"evidence_ledger.yml.entries[{evidence_index}].source_url",
        )
        source_id = url_to_source.get(source_url)
        if source_id is None:
            source_ordinal += 1
            source_id = _source_id(ordinal=source_ordinal)
            url_to_source[source_url] = source_id
            sources.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "source_id": source_id,
                    "requested_url": source_url,
                    "canonical_url": source_url,
                    "source_kind": _record_safe_text(
                        item.get("source_type") or "unknown"
                    ),
                    "title": source_url,
                    "authority_scope": "legacy-unreviewed",
                    "independence_cluster": urlparse(source_url).hostname or "unknown",
                    "rights_status": _rights_status(item.get("rights_status")),
                    "visibility": "unknown",
                    "retrieved_at": _iso_datetime(item.get("retrieved_at"), current),
                }
            )
        supports: list[dict[str, Any]] = []
        link_confidence = 0.0
        extraction_method = "legacy-unreviewed"
        for support in item.get("supports", []):
            if not isinstance(support, dict) or not support.get("claim_id"):
                continue
            claim_id = _legacy_identifier(
                support["claim_id"],
                (
                    f"evidence_ledger.yml.entries[{evidence_index}]"
                    ".supports[].claim_id"
                ),
            )
            supported_claim_ids.add(claim_id)
            confidence = float(support.get("link_confidence") or 0.0)
            link_confidence = max(link_confidence, confidence)
            extraction_method = _record_safe_text(
                support.get("extraction_method") or extraction_method
            )
            supports.append(
                {
                    "claim_id": claim_id,
                    "evidence_role": _record_safe_text(
                        support.get("evidence_role") or "supports"
                    ),
                    "strength": _record_safe_text(
                        support.get("evidence_role_strength") or "unknown"
                    ),
                }
            )
        evidence.append(
            {
                "schema_version": SCHEMA_VERSION,
                "evidence_id": _legacy_identifier(
                    item.get("evidence_id"),
                    f"evidence_ledger.yml.entries[{evidence_index}].evidence_id",
                ),
                "source_id": source_id,
                "excerpt": _record_safe_text(item.get("excerpt")),
                "extraction_method": extraction_method,
                "link_confidence": link_confidence,
                "supports": supports,
                "retrieved_at": _iso_datetime(item.get("retrieved_at"), current),
                "rights_status": _rights_status(item.get("rights_status")),
            }
        )

    claims: list[dict[str, Any]] = []
    all_claim_ids = sorted(set(graph_claims) | supported_claim_ids)
    for claim_id in all_claim_ids:
        item = graph_claims.get(claim_id, {})
        confidence = item.get("confidence", {})
        if isinstance(confidence, dict):
            confidence = confidence.get("score", 0.0)
        evidence_ids = sorted(
            row["evidence_id"]
            for row in evidence
            if any(link["claim_id"] == claim_id for link in row["supports"])
        )
        text = _record_safe_text(
            item.get("text")
            or f"Unresolved legacy claim {claim_id}; semantic review required."
        )
        claims.append(
            {
                "schema_version": SCHEMA_VERSION,
                "claim_id": claim_id,
                "text": text,
                "claim_type": _record_safe_text(item.get("claim_type") or "legacy"),
                "status": "unresolved",
                "evidence_ids": evidence_ids,
                "confidence": float(confidence or 0.0),
                "created_at": imported_at,
            }
        )

    watch: list[dict[str, Any]] = []
    tier_map = {"volatile": "volatile", "active": "active", "stable": "stable"}
    for source in sources:
        entry = bib_by_url.get(source["canonical_url"], {})
        days = int(entry.get("stale_after_days") or 365)
        watch.append(
            {
                "schema_version": SCHEMA_VERSION,
                "source_id": source["source_id"],
                "canonical_url": source["canonical_url"],
                "volatility": tier_map.get(str(entry.get("freshness_tier")), "archival"),
                "cadence_days": days,
                "owner": "unassigned",
                "last_retrieved_at": source["retrieved_at"],
                "last_semantic_review_at": None,
                "next_check_at": current[:10],
                "events": [],
                "status": "active",
                "notes": "Legacy verification was structural; semantic review is due immediately.",
            }
        )

    # Never persist a hash of raw legacy inputs: those files may contain a
    # secret-bearing URL, and its digest would be an offline guessing oracle.
    run_id = "legacy-import-v1"
    files: dict[Path, bytes] = {
        Path("dossier.yaml"): yaml.safe_dump(
            {
                "schema_version": SCHEMA_VERSION,
                "dossier_id": _safe_id(topic, "dossier"),
                "topic": topic,
                "kind": "research",
                "status": "needs-review",
                "created_at": current[:10],
            },
            sort_keys=False,
        ).encode(),
        Path("sources.jsonl"): _jsonl(sorted(sources, key=lambda row: row["source_id"])).encode(),
        Path("evidence.jsonl"): _jsonl(sorted(evidence, key=lambda row: row["evidence_id"])).encode(),
        Path("claims.jsonl"): _jsonl(claims).encode(),
        Path("reviews.jsonl"): b"",
        Path("watch.jsonl"): _jsonl(sorted(watch, key=lambda row: row["source_id"])).encode(),
        Path("derived/consumer-bindings.jsonl"): b"",
        Path("runs") / run_id / "search-decisions.jsonl": b"",
        Path("runs") / run_id / "refresh-events.jsonl": b"",
    }

    output_refs = [
        {"path": str(path), "sha256": hashlib.sha256(content).hexdigest()}
        for path, content in sorted(files.items(), key=lambda pair: str(pair[0]))
    ]
    run = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "topic": topic,
        "started_at": imported_at,
        "completed_at": imported_at,
        "status": "complete",
        "toolkit": {
            "commit": "legacy-unrecorded",
            "skills_version": PLUGIN_VERSION,
            "cli_version": __version__,
        },
        "repositories": [],
        "environment": {
            "python": platform.python_version(),
            "os": platform.system(),
            "model": "not-used",
            "effort": "deterministic-import",
            "tool_policy": "local-read-write",
        },
        "decision_log": [],
        "searches": [],
        "inputs": [],
        "outputs": output_refs,
        "attempts": [{"stage": "legacy-import", "attempt": 1, "exit_code": 0}],
    }
    files[Path("runs") / run_id / "manifest.json"] = (
        json.dumps(run, indent=2, sort_keys=True) + "\n"
    ).encode()

    # Build and validate a complete staging tree before touching the target.
    # This prevents a malformed legacy record from leaving a partially imported
    # dossier behind. Only byte-identical pre-existing outputs are accepted.
    _create_missing_private_directories(target.parent)
    with tempfile.TemporaryDirectory(
        prefix=".research-toolkit-legacy-import-",
        dir=target.parent,
    ) as temp_dir:
        staged = Path(temp_dir) / "dossier"
        for relative, content in sorted(files.items(), key=lambda pair: str(pair[0])):
            _write_idempotent(
                staged / relative,
                content,
                private_root=staged,
            )

        errors = validate_dossier(staged)
        if errors:
            raise ValueError(
                "staged imported dossier failed validation:\n" + "\n".join(errors)
            )

        for relative, content in sorted(files.items(), key=lambda pair: str(pair[0])):
            path = target / relative
            existing = _existing_regular_bytes(path)
            if existing is not None and existing != content:
                raise FileExistsError(
                    f"refusing to replace differing imported artifact: {path}"
                )

        written: list[Path] = []
        for relative, content in sorted(files.items(), key=lambda pair: str(pair[0])):
            path = target / relative
            _write_idempotent(path, content, private_root=target)
            written.append(path)

    # The staged tree already passed, but revalidate the resulting target to
    # catch an unexpected local filesystem race rather than reporting success.
    errors = validate_dossier(target)
    if errors:
        raise ValueError("imported dossier failed validation:\n" + "\n".join(errors))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="research-toolkit import-legacy")
    parser.add_argument("legacy", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args(argv)
    try:
        paths = import_legacy(args.legacy, args.target)
    except (FileExistsError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"OK: imported or confirmed {len(paths)} canonical artifacts in {args.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
