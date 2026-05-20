#!/usr/bin/env python3
"""Build a strict-live v2 claim_graph.jsonl from a project's ledgers.

Reads bib_ledger.yml + dataset_ledger.yml + evidence_ledger.yml + cache_manifest.yml
and emits a complete claim_graph.jsonl with entity / source / claim / evidence /
cache_blob records. Deterministic ordering and key sorting make the output
byte-stable for diffing.

Overwrites the target by default; --no-overwrite refuses if the target exists.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators import claim_graph
from validators.v2_common import load_yaml_mapping


SOURCE_QUALITY_SCORE = {
    "primary": 0.95,
    "official": 0.85,
    "secondary": 0.60,
    "user_note": 0.50,
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", text.lower()).strip("_") or "item"


def _entity_type_for_bib(entry: dict[str, Any]) -> str:
    cf = entry.get("claim_family", "")
    if isinstance(cf, str) and cf in claim_graph.ALLOWED_ENTITY_TYPES:
        return cf
    if isinstance(cf, str):
        lowered = cf.lower()
        if "dataset" in lowered:
            return "dataset"
        if "benchmark" in lowered:
            return "benchmark"
        if "standard" in lowered:
            return "standard"
        if "policy" in lowered:
            return "policy"
    return "paper"


def _entity_type_for_dataset(entry: dict[str, Any]) -> str:
    src = entry.get("source", "")
    if isinstance(src, str) and src in claim_graph.ALLOWED_ENTITY_TYPES:
        return src
    return "dataset"


def _quality_score(evidence: dict[str, Any]) -> float:
    return SOURCE_QUALITY_SCORE.get(evidence.get("source_quality", ""), 0.0)


def _coerce_aliases(value: Any) -> list[str]:
    """Return a list of non-empty alias strings, or [] if none."""
    if not isinstance(value, list):
        return []
    return [a for a in value if isinstance(a, str) and a.strip()]


def _load_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data, errors = load_yaml_mapping(path)
    if errors:
        raise SystemExit(f"{path.name}: {'; '.join(errors)}")
    return data or {}


def build(project_dir: Path) -> list[dict[str, Any]]:
    evidence_data = _load_optional(project_dir / "evidence_ledger.yml")
    if not evidence_data:
        raise SystemExit(f"evidence_ledger.yml missing in {project_dir}")

    topic = evidence_data.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise SystemExit("evidence_ledger.yml: missing required field 'topic'")
    evidence_entries = evidence_data.get("entries") or []

    bib_entries = _load_optional(project_dir / "bib_ledger.yml").get("entries") or []
    dataset_entries = _load_optional(project_dir / "dataset_ledger.yml").get("entries") or []
    cache_entries = _load_optional(project_dir / "cache_manifest.yml").get("entries") or []

    records: list[dict[str, Any]] = []

    # entity records
    seen_entity_ids: set[str] = set()
    for entry in bib_entries:
        if not isinstance(entry, dict):
            continue
        bibkey = entry.get("bibkey")
        if not isinstance(bibkey, str):
            continue
        ent_id = f"ent_{bibkey}"
        if ent_id in seen_entity_ids:
            continue
        seen_entity_ids.add(ent_id)
        record: dict[str, Any] = {
            "record_type": "entity",
            "id": ent_id,
            "topic": topic,
            "entity_type": _entity_type_for_bib(entry),
            "canonical_name": entry.get("title", bibkey),
        }
        aliases = _coerce_aliases(entry.get("aliases"))
        if aliases:
            record["aliases"] = aliases
        records.append(record)
    for entry in dataset_entries:
        if not isinstance(entry, dict):
            continue
        bibkey = entry.get("bibkey")
        if not isinstance(bibkey, str):
            continue
        ent_id = f"ent_{bibkey}"
        if ent_id in seen_entity_ids:
            continue
        seen_entity_ids.add(ent_id)
        record = {
            "record_type": "entity",
            "id": ent_id,
            "topic": topic,
            "entity_type": _entity_type_for_dataset(entry),
            "canonical_name": entry.get("name", bibkey),
        }
        aliases = _coerce_aliases(entry.get("aliases"))
        if aliases:
            record["aliases"] = aliases
        records.append(record)

    # source records (group by primary_url, union cache_ids)
    sources_by_url: dict[str, set[str]] = defaultdict(set)
    for entry in list(bib_entries) + list(dataset_entries):
        if not isinstance(entry, dict):
            continue
        url = entry.get("primary_url")
        if not isinstance(url, str):
            continue
        for cid in entry.get("cache_ids") or []:
            if isinstance(cid, str):
                sources_by_url[url].add(cid)
    for url in sorted(sources_by_url.keys()):
        cache_ids = sorted(sources_by_url[url])
        if not cache_ids:
            continue
        records.append({
            "record_type": "source",
            "id": f"src_{_slug(url)}",
            "topic": topic,
            "source_url": url,
            "cache_ids": cache_ids,
        })

    # claim records (group evidence by claim_id)
    claims_to_evidences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev_entry in evidence_entries:
        if not isinstance(ev_entry, dict):
            continue
        for support in ev_entry.get("supports") or []:
            if not isinstance(support, dict):
                continue
            cid = support.get("claim_id")
            if isinstance(cid, str):
                claims_to_evidences[cid].append(ev_entry)

    # evidence_id → set of bib/dataset entities referencing it
    evidence_to_entities: dict[str, set[str]] = defaultdict(set)
    for entry in list(bib_entries) + list(dataset_entries):
        if not isinstance(entry, dict):
            continue
        bibkey = entry.get("bibkey")
        if not isinstance(bibkey, str):
            continue
        for ev_id in entry.get("evidence_ids") or []:
            if isinstance(ev_id, str):
                evidence_to_entities[ev_id].add(f"ent_{bibkey}")

    for claim_id in sorted(claims_to_evidences.keys()):
        supporters = claims_to_evidences[claim_id]
        ranked = sorted(
            supporters,
            key=lambda ev: (_quality_score(ev), len(str(ev.get("excerpt") or ""))),
            reverse=True,
        )
        best = ranked[0]
        text = str(best.get("excerpt") or "").strip() or "(no excerpt provided)"

        evidence_ids = sorted({
            ev["evidence_id"] for ev in supporters
            if isinstance(ev.get("evidence_id"), str)
        })

        entity_ids: set[str] = set()
        for ev_id in evidence_ids:
            entity_ids.update(evidence_to_entities.get(ev_id, set()))
        if not entity_ids:
            raise SystemExit(
                f"claim {claim_id!r}: no bib/dataset entry lists any of its "
                f"evidence_ids {evidence_ids!r} in its own evidence_ids field. "
                f"Cannot derive entity_ids."
            )

        score = max(_quality_score(ev) for ev in supporters)
        factors: set[str] = set()
        for ev in supporters:
            q = ev.get("source_quality")
            if isinstance(q, str):
                factors.add(f"source: {q}")
            m = ev.get("verification_method")
            if isinstance(m, str):
                factors.add(f"verified: {m}")
        if not factors:
            factors = {"derived from evidence_ledger"}

        records.append({
            "record_type": "claim",
            "id": claim_id,
            "topic": topic,
            "claim_type": "fact",
            "text": text,
            "status": "active",
            "evidence_ids": evidence_ids,
            "entity_ids": sorted(entity_ids),
            "confidence": {
                "score": score,
                "factors": sorted(factors),
            },
        })

    # evidence records
    for ev_entry in sorted(
        evidence_entries,
        key=lambda e: e.get("evidence_id", "") if isinstance(e, dict) else "",
    ):
        if not isinstance(ev_entry, dict):
            continue
        ev_id = ev_entry.get("evidence_id")
        if not isinstance(ev_id, str):
            continue
        claim_ids = sorted({
            s["claim_id"] for s in (ev_entry.get("supports") or [])
            if isinstance(s, dict) and isinstance(s.get("claim_id"), str)
        })
        cache_ids = sorted({
            c for c in (ev_entry.get("cache_ids") or []) if isinstance(c, str)
        })
        if not claim_ids or not cache_ids:
            continue
        records.append({
            "record_type": "evidence",
            "id": f"graph_{ev_id}",
            "topic": topic,
            "evidence_id": ev_id,
            "claim_ids": claim_ids,
            "cache_ids": cache_ids,
        })

    # cache_blob records
    for cache_entry in sorted(
        cache_entries,
        key=lambda c: c.get("cache_id", "") if isinstance(c, dict) else "",
    ):
        if not isinstance(cache_entry, dict):
            continue
        cid = cache_entry.get("cache_id")
        sha = cache_entry.get("sha256")
        if not isinstance(cid, str) or not isinstance(sha, str):
            continue
        records.append({
            "record_type": "cache_blob",
            "id": f"graph_{cid}",
            "topic": topic,
            "cache_id": cid,
            "sha256": sha,
        })

    return records


def write(records: list[dict[str, Any]], output: Path) -> None:
    tmp = output.with_suffix(output.suffix + ".tmp")
    output.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records
    ) + "\n"
    tmp.write_text(content, encoding="utf-8")
    errors = claim_graph.validate(tmp)
    if errors:
        tmp.unlink(missing_ok=True)
        raise SystemExit(
            "generated claim_graph failed validation:\n" + "\n".join(errors)
        )
    tmp.replace(output)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_dir", help="Project directory containing v2 ledgers")
    parser.add_argument(
        "--output",
        help="Output path (default: <project_dir>/claim_graph.jsonl)",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Fail if the output already exists",
    )
    args = parser.parse_args(argv[1:])

    project = Path(args.project_dir).expanduser().resolve()
    if not project.is_dir():
        print(f"error: not a directory: {project}", file=sys.stderr)
        return 2

    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else project / "claim_graph.jsonl"
    )
    if args.no_overwrite and output.exists():
        print(f"error: refusing to overwrite existing {output}", file=sys.stderr)
        return 2

    records = build(project)
    write(records, output)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
