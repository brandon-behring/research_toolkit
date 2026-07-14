"""Validate and initialize clean-break canonical research dossiers."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from research_toolkit import PLUGIN_VERSION, __version__
from research_toolkit.contracts import SCHEMA_VERSION, validate_record

JSONL_CONTRACTS = {
    "sources.jsonl": "source-record",
    "evidence.jsonl": "evidence-record",
    "claims.jsonl": "claim-record",
    "reviews.jsonl": "claim-review-record",
    "watch.jsonl": "source-watch-record",
}

RELEASE_FILES = (
    "derived/claim-graph.jsonl",
    "derived/agent-index.md",
    "derived/citation-report.json",
    "derived/synthesis-export.jsonl",
    "release.json",
)


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Load a JSONL file while retaining all parse and shape errors."""
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [], [f"{path.name}: required file is missing"]
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.name}:{number}: record must be an object")
            continue
        records.append(value)
    return records, errors


def _load_object(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        if path.suffix in {".yaml", ".yml"}:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [f"{path.name}: required file is missing"]
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        return {}, [f"{path.name}: cannot parse: {exc}"]
    if not isinstance(value, dict):
        return {}, [f"{path.name}: root must be an object"]
    return value, []


def _duplicates(records: list[dict[str, Any]], key: str, label: str) -> list[str]:
    seen: set[str] = set()
    errors: list[str] = []
    for index, record in enumerate(records):
        value = record.get(key)
        if not isinstance(value, str):
            continue
        if value in seen:
            errors.append(f"{label}[{index}].{key}: duplicate id {value!r}")
        seen.add(value)
    return errors


def _load_contract_file(root: Path, filename: str) -> tuple[list[dict[str, Any]], list[str]]:
    records, errors = read_jsonl(root / filename)
    schema_name = JSONL_CONTRACTS[filename]
    for index, record in enumerate(records):
        errors.extend(
            f"{filename}[{index}]: {error}" for error in validate_record(record, schema_name)
        )
    return records, errors


def _validate_release_artifacts(root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for index, artifact in enumerate(release.get("artifacts", [])):
        if not isinstance(artifact, dict):
            continue
        relative = artifact.get("path")
        if not isinstance(relative, str):
            continue
        path = (root / relative).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            errors.append(f"release.json.artifacts[{index}].path: escapes dossier root")
            continue
        if not path.is_file():
            errors.append(f"release.json.artifacts[{index}].path: file does not exist: {relative}")
            continue
        expected = artifact.get("sha256")
        if isinstance(expected, str) and sha256_file(path) != expected:
            errors.append(f"release.json.artifacts[{index}].sha256: digest mismatch for {relative}")
    return errors


def validate_dossier(root: Path, *, require_release: bool = False) -> list[str]:
    """Validate canonical files, record contracts, references, and release hashes."""
    root = root.expanduser().resolve()
    errors: list[str] = []

    manifest, manifest_errors = _load_object(root / "dossier.yaml")
    errors.extend(manifest_errors)
    if manifest:
        errors.extend(validate_record(manifest, "dossier-manifest"))

    loaded: dict[str, list[dict[str, Any]]] = {}
    for filename in JSONL_CONTRACTS:
        loaded[filename], file_errors = _load_contract_file(root, filename)
        errors.extend(file_errors)

    sources = loaded["sources.jsonl"]
    evidence = loaded["evidence.jsonl"]
    claims = loaded["claims.jsonl"]
    reviews = loaded["reviews.jsonl"]
    watches = loaded["watch.jsonl"]

    for records, key, label in (
        (sources, "source_id", "sources"),
        (evidence, "evidence_id", "evidence"),
        (claims, "claim_id", "claims"),
        (reviews, "review_id", "reviews"),
        (watches, "source_id", "watch"),
    ):
        errors.extend(_duplicates(records, key, label))

    source_ids = {item.get("source_id") for item in sources}
    evidence_ids = {item.get("evidence_id") for item in evidence}
    claim_ids = {item.get("claim_id") for item in claims}

    for index, item in enumerate(evidence):
        if item.get("source_id") not in source_ids:
            errors.append(f"evidence[{index}].source_id: unresolved source {item.get('source_id')!r}")
        for support in item.get("supports", []):
            if support.get("claim_id") not in claim_ids:
                errors.append(
                    f"evidence[{index}].supports: unresolved claim {support.get('claim_id')!r}"
                )
            else:
                claim = next(row for row in claims if row.get("claim_id") == support.get("claim_id"))
                if item.get("evidence_id") not in claim.get("evidence_ids", []):
                    errors.append(
                        f"evidence[{index}].supports: claim {support.get('claim_id')!r} "
                        f"does not list evidence {item.get('evidence_id')!r}"
                    )
    for index, item in enumerate(claims):
        for evidence_id in item.get("evidence_ids", []):
            if evidence_id not in evidence_ids:
                errors.append(f"claims[{index}].evidence_ids: unresolved evidence {evidence_id!r}")
            else:
                evidence_record = next(
                    row for row in evidence if row.get("evidence_id") == evidence_id
                )
                linked_claims = {
                    link.get("claim_id") for link in evidence_record.get("supports", [])
                }
                if item.get("claim_id") not in linked_claims:
                    errors.append(
                        f"claims[{index}].evidence_ids: evidence {evidence_id!r} "
                        f"does not link claim {item.get('claim_id')!r}"
                    )
    for index, item in enumerate(reviews):
        if item.get("claim_id") not in claim_ids:
            errors.append(f"reviews[{index}].claim_id: unresolved claim {item.get('claim_id')!r}")
        for evidence_id in item.get("evidence_ids", []):
            if evidence_id not in evidence_ids:
                errors.append(f"reviews[{index}].evidence_ids: unresolved evidence {evidence_id!r}")
    for index, item in enumerate(watches):
        if item.get("source_id") not in source_ids:
            errors.append(f"watch[{index}].source_id: unresolved source {item.get('source_id')!r}")

    run_manifests = sorted((root / "runs").glob("*/manifest.json"))
    if not run_manifests:
        errors.append("runs: at least one runs/<run-id>/manifest.json is required")
    for manifest_path in run_manifests:
        run, run_errors = _load_object(manifest_path)
        errors.extend(f"{manifest_path.relative_to(root)}: {error}" for error in run_errors)
        if run:
            errors.extend(
                f"{manifest_path.relative_to(root)}: {error}"
                for error in validate_record(run, "research-run-manifest")
            )

        run_dir = manifest_path.parent
        decisions, decision_errors = read_jsonl(run_dir / "search-decisions.jsonl")
        errors.extend(
            f"{run_dir.relative_to(root)}/search-decisions.jsonl: {error}"
            for error in decision_errors
        )
        for index, decision in enumerate(decisions):
            required = {"decision_id", "query", "source_url", "decision", "reason", "decided_at"}
            missing = sorted(required - set(decision))
            if missing:
                errors.append(
                    f"{run_dir.relative_to(root)}/search-decisions.jsonl[{index}]: "
                    f"missing fields {missing}"
                )

        events, event_errors = read_jsonl(run_dir / "refresh-events.jsonl")
        errors.extend(
            f"{run_dir.relative_to(root)}/refresh-events.jsonl: {error}"
            for error in event_errors
        )
        for index, event in enumerate(events):
            errors.extend(
                f"{run_dir.relative_to(root)}/refresh-events.jsonl[{index}]: {error}"
                for error in validate_record(event, "refresh-event")
            )
            if event.get("source_id") not in source_ids:
                errors.append(
                    f"{run_dir.relative_to(root)}/refresh-events.jsonl"
                    f"[{index}].source_id: unresolved source {event.get('source_id')!r}"
                )
            for affected_claim in event.get("affected_claim_ids", []):
                if affected_claim not in claim_ids:
                    errors.append(
                        f"{run_dir.relative_to(root)}/refresh-events.jsonl"
                        f"[{index}].affected_claim_ids: unresolved claim {affected_claim!r}"
                    )

    bindings_path = root / "derived" / "consumer-bindings.jsonl"
    binding_ids: set[str] = set()
    bindings: list[dict[str, Any]] = []
    if bindings_path.exists():
        bindings, binding_errors = read_jsonl(bindings_path)
        errors.extend(binding_errors)
        errors.extend(_duplicates(bindings, "binding_id", "consumer-bindings"))
        binding_ids = {binding.get("binding_id") for binding in bindings}
        for index, binding in enumerate(bindings):
            errors.extend(
                f"derived/consumer-bindings.jsonl[{index}]: {error}"
                for error in validate_record(binding, "consumer-binding")
            )
            if binding.get("claim_id") not in claim_ids:
                errors.append(
                    "derived/consumer-bindings.jsonl"
                    f"[{index}].claim_id: unresolved claim {binding.get('claim_id')!r}"
                )

    for event_path in sorted((root / "runs").glob("*/refresh-events.jsonl")):
        events, _ = read_jsonl(event_path)
        for index, event in enumerate(events):
            for binding_id in event.get("affected_consumer_binding_ids", []):
                if binding_id not in binding_ids:
                    errors.append(
                        f"{event_path.relative_to(root)}[{index}]"
                        f".affected_consumer_binding_ids: unresolved binding {binding_id!r}"
                    )

    lock_path = root / "research-lock.json"
    if lock_path.exists():
        lock, lock_errors = _load_object(lock_path)
        errors.extend(lock_errors)
        if lock:
            errors.extend(validate_record(lock, "research-lock"))

    if require_release:
        for relative in RELEASE_FILES:
            if not (root / relative).is_file():
                errors.append(f"{relative}: required release artifact is missing")
        if not bindings_path.is_file():
            errors.append("derived/consumer-bindings.jsonl: required release artifact is missing")

        reviewed_claims = {
            item.get("claim_id")
            for item in reviews
            if item.get("disposition") in {"supported", "narrow"}
            and item.get("entailment") in {"full", "partial"}
        }
        for item in claims:
            if item.get("status") == "active" and item.get("claim_id") not in reviewed_claims:
                errors.append(
                    f"claims: active claim {item.get('claim_id')!r} lacks an accepting semantic review"
                )
            if item.get("status") == "unresolved":
                errors.append(f"claims: unresolved claim blocks release: {item.get('claim_id')!r}")
        for item in sources:
            if item.get("rights_status") == "unknown":
                errors.append(
                    f"sources: unknown rights status blocks release: {item.get('source_id')!r}"
                )
        for item in bindings:
            if item.get("status") != "active":
                errors.append(
                    f"consumer-bindings: non-active binding blocks release: {item.get('binding_id')!r}"
                )

    release_path = root / "release.json"
    if release_path.exists():
        release, release_errors = _load_object(release_path)
        errors.extend(release_errors)
        if release:
            errors.extend(validate_record(release, "research-release-manifest"))
            errors.extend(_validate_release_artifacts(root, release))
            failed_validators = [
                item.get("name")
                for item in release.get("validators", [])
                if item.get("status") == "fail"
            ]
            if failed_validators:
                errors.append(f"release.json.validators: failing gates {failed_validators}")
            declared = {
                item.get("path") for item in release.get("artifacts", []) if isinstance(item, dict)
            }
            essential = set(JSONL_CONTRACTS) | {
                "dossier.yaml",
                "derived/claim-graph.jsonl",
                "derived/agent-index.md",
                "derived/citation-report.json",
                "derived/consumer-bindings.jsonl",
                "derived/synthesis-export.jsonl",
            }
            missing = sorted(essential - declared)
            if missing:
                errors.append(f"release.json.artifacts: missing canonical release files {missing}")
            cutoff_value = release.get("freshness_cutoff")
            if isinstance(cutoff_value, str):
                try:
                    cutoff = date.fromisoformat(cutoff_value)
                except ValueError:
                    cutoff = None
                if cutoff is not None:
                    for item in watches:
                        next_value = item.get("next_check_at")
                        if item.get("status") != "active" or not isinstance(next_value, str):
                            continue
                        if item.get("last_semantic_review_at") is None:
                            errors.append(
                                "watch: source has no semantic review: "
                                f"{item.get('source_id')!r}"
                            )
                        try:
                            next_check = date.fromisoformat(next_value)
                        except ValueError:
                            continue
                        if next_check <= cutoff:
                            errors.append(
                                "watch: source review is due at release cutoff: "
                                f"{item.get('source_id')!r} ({next_value})"
                            )

    return errors


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def initialize_dossier(
    root: Path,
    *,
    dossier_id: str,
    topic: str,
    run_id: str,
    run_date: date,
    kind: str,
) -> None:
    """Create an empty canonical dossier and planned run, refusing collisions."""
    root = root.expanduser().resolve()
    if (root / "dossier.yaml").exists():
        raise FileExistsError(f"canonical dossier already exists: {root}")
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"refusing to initialize non-empty directory: {root}")

    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "dossier_id": dossier_id,
        "topic": topic,
        "kind": kind,
        "status": "planning",
        "created_at": run_date.isoformat(),
    }
    _atomic_text(root / "dossier.yaml", yaml.safe_dump(manifest, sort_keys=False))
    for filename in JSONL_CONTRACTS:
        _atomic_text(root / filename, "")

    run = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "topic": topic,
        "started_at": f"{run_date.isoformat()}T00:00:00Z",
        "status": "planned",
        "toolkit": {
            "commit": os.environ.get("RESEARCH_TOOLKIT_COMMIT", "unrecorded"),
            "skills_version": PLUGIN_VERSION,
            "cli_version": __version__,
        },
        "repositories": [],
        "environment": {
            "python": platform.python_version(),
            "os": platform.platform(),
            "model": "unselected",
            "effort": "unselected",
            "tool_policy": "unselected",
        },
        "decision_log": [],
        "searches": [],
        "inputs": [],
        "outputs": [],
        "attempts": [],
    }
    _atomic_text(
        root / "runs" / run_id / "manifest.json",
        json.dumps(run, indent=2, sort_keys=True) + "\n",
    )
    _atomic_text(root / "runs" / run_id / "search-decisions.jsonl", "")
    _atomic_text(root / "runs" / run_id / "refresh-events.jsonl", "")
    _atomic_text(root / "derived" / "consumer-bindings.jsonl", "")


def due_watch_records(root: Path, today: date) -> tuple[list[dict[str, Any]], list[str]]:
    """Return watch records due on or before ``today`` after dossier validation."""
    errors = validate_dossier(root)
    records, parse_errors = read_jsonl(root / "watch.jsonl")
    errors.extend(parse_errors)
    due: list[dict[str, Any]] = []
    for item in records:
        if item.get("status") != "active":
            continue
        value = item.get("next_check_at")
        if not isinstance(value, str):
            continue
        try:
            check_date = date.fromisoformat(value[:10])
        except ValueError:
            continue
        if check_date <= today:
            due.append(item)
    return due, errors


def impact_graph(root: Path, *, source_id: str | None, claim_id: str | None) -> dict[str, Any]:
    """Return deterministic source/evidence/claim/consumer impact paths."""
    sources, _ = read_jsonl(root / "sources.jsonl")
    evidence, _ = read_jsonl(root / "evidence.jsonl")
    claims, _ = read_jsonl(root / "claims.jsonl")
    bindings, _ = read_jsonl(root / "derived" / "consumer-bindings.jsonl")

    selected_claims: set[str] = set()
    selected_evidence: set[str] = set()
    selected_sources: set[str] = set()
    if source_id:
        selected_sources.add(source_id)
        for item in evidence:
            if item.get("source_id") == source_id:
                selected_evidence.add(item.get("evidence_id"))
                selected_claims.update(
                    support.get("claim_id") for support in item.get("supports", [])
                )
    if claim_id:
        selected_claims.add(claim_id)
        for item in claims:
            if item.get("claim_id") == claim_id:
                selected_evidence.update(item.get("evidence_ids", []))
        for item in evidence:
            if item.get("evidence_id") in selected_evidence:
                selected_sources.add(item.get("source_id"))

    return {
        "sources": sorted(
            item for item in selected_sources if any(row.get("source_id") == item for row in sources)
        ),
        "evidence": sorted(item for item in selected_evidence if isinstance(item, str)),
        "claims": sorted(item for item in selected_claims if isinstance(item, str)),
        "consumers": sorted(
            (
                row
                for row in bindings
                if row.get("claim_id") in selected_claims
            ),
            key=lambda row: row.get("binding_id", ""),
        ),
    }


def find_dossiers(root: Path) -> list[Path]:
    """Return canonical dossier roots beneath ``root`` without descending into runs."""
    root = root.expanduser().resolve()
    return sorted(path.parent for path in root.rglob("dossier.yaml") if "runs" not in path.parts)
