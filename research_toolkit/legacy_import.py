"""One-way, idempotent importer from strict-live v2/v3 dossier artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from research_toolkit import PLUGIN_VERSION, __version__
from research_toolkit.canonical import sha256_file, validate_dossier
from research_toolkit.contracts import SCHEMA_VERSION


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
    text = str(value or fallback)
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
    return normalized if normalized in {"public", "private-use", "restricted"} else "unknown"


def _write_idempotent(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError(f"refusing to replace differing imported artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _legacy_digest(root: Path, names: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for name in names:
        path = root / name
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def import_legacy(legacy: Path, target: Path) -> list[Path]:
    """Import one legacy dossier, returning canonical files written or confirmed."""
    legacy = legacy.expanduser().resolve()
    target = target.expanduser().resolve()
    bib = _load_yaml(legacy / "bib_ledger.yml")
    evidence_legacy = _load_yaml(legacy / "evidence_ledger.yml")
    graph = _load_jsonl(legacy / "claim_graph.jsonl")
    topic = str(bib.get("topic") or legacy.name.removeprefix("research_") or "unknown")
    current = str(bib.get("current_as_of") or bib.get("generated_at") or date.today())
    imported_at = _iso_datetime(current, current)

    sources: list[dict[str, Any]] = []
    url_to_source: dict[str, str] = {}
    bib_by_url: dict[str, dict[str, Any]] = {}
    for entry in bib.get("entries", []):
        if not isinstance(entry, dict):
            continue
        url = str(entry.get("primary_url") or "")
        if not url:
            continue
        bibkey = str(entry.get("bibkey") or hashlib.sha256(url.encode()).hexdigest()[:12])
        source_id = _safe_id(bibkey, "src")
        url_to_source[url] = source_id
        bib_by_url[url] = entry
        host = urlparse(url).hostname or "unknown"
        sources.append(
            {
                "schema_version": SCHEMA_VERSION,
                "source_id": source_id,
                "requested_url": url,
                "canonical_url": url,
                "source_kind": str(entry.get("claim_family") or "unknown"),
                "title": str(entry.get("title") or bibkey),
                "authority_scope": "legacy-unreviewed",
                "independence_cluster": host,
                "rights_status": "unknown",
                "visibility": "unknown",
                "retrieved_at": _iso_datetime(entry.get("retrieved_at"), current),
            }
        )

    graph_claims = {
        str(item.get("id")): item for item in graph if item.get("record_type") == "claim"
    }
    evidence: list[dict[str, Any]] = []
    supported_claim_ids: set[str] = set()
    for item in evidence_legacy.get("entries", []):
        if not isinstance(item, dict):
            continue
        source_url = str(item.get("source_url") or "")
        source_id = url_to_source.get(source_url)
        if source_id is None:
            source_id = _safe_id(hashlib.sha256(source_url.encode()).hexdigest()[:12], "src")
            url_to_source[source_url] = source_id
            sources.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "source_id": source_id,
                    "requested_url": source_url,
                    "canonical_url": source_url,
                    "source_kind": str(item.get("source_type") or "unknown"),
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
            claim_id = str(support["claim_id"])
            supported_claim_ids.add(claim_id)
            confidence = float(support.get("link_confidence") or 0.0)
            link_confidence = max(link_confidence, confidence)
            extraction_method = str(support.get("extraction_method") or extraction_method)
            supports.append(
                {
                    "claim_id": claim_id,
                    "evidence_role": str(support.get("evidence_role") or "supports"),
                    "strength": str(support.get("evidence_role_strength") or "unknown"),
                }
            )
        evidence.append(
            {
                "schema_version": SCHEMA_VERSION,
                "evidence_id": str(item.get("evidence_id")),
                "source_id": source_id,
                "excerpt": str(item.get("excerpt") or ""),
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
        text = str(item.get("text") or f"Unresolved legacy claim {claim_id}; semantic review required.")
        claims.append(
            {
                "schema_version": SCHEMA_VERSION,
                "claim_id": claim_id,
                "text": text,
                "claim_type": str(item.get("claim_type") or "legacy"),
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

    legacy_names = ("bib_ledger.yml", "evidence_ledger.yml", "claim_graph.jsonl")
    source_digest = _legacy_digest(legacy, legacy_names)
    run_id = f"legacy-import-{source_digest[:12]}"
    files: dict[Path, bytes] = {
        Path("dossier.yaml"): yaml.safe_dump(
            {
                "schema_version": SCHEMA_VERSION,
                "dossier_id": _safe_id(topic, "dossier"),
                "topic": topic,
                "kind": "research",
                "status": "needs-review",
                "created_at": current[:10],
                "legacy_input_digest": source_digest,
            },
            sort_keys=False,
        ).encode(),
        Path("sources.jsonl"): _jsonl(sorted(sources, key=lambda row: row["source_id"])).encode(),
        Path("evidence.jsonl"): _jsonl(sorted(evidence, key=lambda row: row["evidence_id"])).encode(),
        Path("claims.jsonl"): _jsonl(claims).encode(),
        Path("reviews.jsonl"): b"",
        Path("watch.jsonl"): _jsonl(sorted(watch, key=lambda row: row["source_id"])).encode(),
        Path("derived/claim-graph.jsonl"): (legacy / "claim_graph.jsonl").read_bytes(),
        Path("derived/consumer-bindings.jsonl"): b"",
        Path("runs") / run_id / "search-decisions.jsonl": b"",
        Path("runs") / run_id / "refresh-events.jsonl": b"",
    }
    optional = {
        "synthesis_export.jsonl": "derived/synthesis-export.jsonl",
        "agent_index/README.md": "derived/agent-index.md",
    }
    for old, new in optional.items():
        path = legacy / old
        if path.is_file():
            files[Path(new)] = path.read_bytes()

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
        "inputs": [
            {"path": name, "sha256": sha256_file(legacy / name)} for name in legacy_names
        ],
        "outputs": output_refs,
        "attempts": [{"stage": "legacy-import", "attempt": 1, "exit_code": 0}],
    }
    files[Path("runs") / run_id / "manifest.json"] = (
        json.dumps(run, indent=2, sort_keys=True) + "\n"
    ).encode()

    written: list[Path] = []
    for relative, content in sorted(files.items(), key=lambda pair: str(pair[0])):
        path = target / relative
        _write_idempotent(path, content)
        written.append(path)

    errors = validate_dossier(target)
    if errors:
        raise ValueError("imported dossier failed validation:\n" + "\n".join(errors))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m research_toolkit.legacy_import")
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
