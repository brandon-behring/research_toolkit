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


def _load_synthesis_entries(project_dir: Path) -> dict[str, dict[str, Any]]:
    """v2.3 C2: load any synthesis_entry.yml in the project, indexed by synthesis_id.

    The synthesis_entry validator (daf6699) handles cross-source consolidation
    entries with attribution_map. This loader makes them available to the
    claim-text resolver below. Returns ``{}`` when no synthesis_entry.yml is
    present (most projects).
    """
    path = project_dir / "synthesis_entry.yml"
    if not path.exists():
        return {}
    data, errors = load_yaml_mapping(path)
    if errors:
        raise SystemExit(f"synthesis_entry.yml: {'; '.join(errors)}")
    if not isinstance(data, dict):
        return {}
    entries = data.get("entries") or []
    by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        sid = entry.get("synthesis_id")
        if isinstance(sid, str) and sid.strip():
            by_id[sid] = entry
    return by_id


def _load_pre_selection(project_dir: Path) -> dict[str, dict[str, Any]]:
    """v2.3 C2: load pre_selection_manifest.yml, indexed by atom_id.

    Only the selections that carry ``synthesis_entry_ref`` matter for the
    resolver — other selections fall through to the existing tiebreak. We
    index by atom_id (claim_id), assuming one selection per atom (which is
    the v2.2 Attribute-First contract).
    """
    path = project_dir / "pre_selection_manifest.yml"
    if not path.exists():
        return {}
    data, errors = load_yaml_mapping(path)
    if errors:
        # Don't hard-fail on a malformed pre_selection_manifest — the
        # dedicated validator surfaces those errors. Just skip C2 wire-up.
        return {}
    if not isinstance(data, dict):
        return {}
    by_atom: dict[str, dict[str, Any]] = {}
    for selection in data.get("selections") or []:
        if not isinstance(selection, dict):
            continue
        atom_id = selection.get("atom_id")
        if isinstance(atom_id, str):
            by_atom[atom_id] = selection
    return by_atom


def _resolve_synthesis_attribution(
    *,
    selection: dict[str, Any],
    synthesis_entries: dict[str, dict[str, Any]],
    excerpt_supporters: list[dict[str, Any]],
    fallback_text: str,
    claim_id: str,
) -> tuple[str, list[str], str | None]:
    """v2.3 C2: resolve claim text from synthesis_entry attribution.

    Returns ``(claim_text, warnings, synthesis_entry_id_used)``. Resolution
    order:

    1. ``synthesis_entry_ref`` present and synthesis_entry exists:
       a. If ``attribution_map`` has a key that overlaps with ``fallback_text``
          (longest-substring match wins; WARN on exact-length tie listing both),
          use the matched key as claim text.
       b. Else use ``synthesis_entry.title`` as claim text.
       In both cases corroborate by asserting source_urls set equality between
       the synthesis_entry and the supporting evidence; mismatch → WARN.
    2. ``synthesis_entry_ref`` absent OR target missing → fall back to
       ``fallback_text`` (existing tiebreak). Dangling refs emit a WARN.
    """
    warnings: list[str] = []
    ref = selection.get("synthesis_entry_ref") if isinstance(selection, dict) else None
    if not isinstance(ref, str) or not ref.strip():
        return fallback_text, warnings, None

    synth = synthesis_entries.get(ref)
    if synth is None:
        warnings.append(
            f"claim {claim_id}: synthesis_entry_ref={ref!r} not found in "
            f"synthesis_entry.yml — falling back to excerpt tiebreak"
        )
        return fallback_text, warnings, None

    # Corroboration check: source_urls set equality.
    ev_urls = {
        ev.get("source_url")
        for ev in excerpt_supporters
        if isinstance(ev.get("source_url"), str)
    }
    synth_urls = {
        u for u in (synth.get("source_urls") or []) if isinstance(u, str)
    }
    if ev_urls != synth_urls:
        only_in_ev = sorted(ev_urls - synth_urls)
        only_in_synth = sorted(synth_urls - ev_urls)
        warnings.append(
            f"claim {claim_id}: source_urls mismatch between supporting "
            f"evidence and synthesis_entry {ref!r}. Only in evidence: "
            f"{only_in_ev}; only in synthesis_entry: {only_in_synth}. "
            f"This indicates drift — either the synthesis_entry needs updating "
            f"or the wrong selection is referencing it."
        )

    attribution_map = synth.get("attribution_map")
    title = synth.get("title")
    if isinstance(attribution_map, dict) and attribution_map:
        matched_key = _attribution_map_longest_match(
            attribution_map, fallback_text, warnings, claim_id, ref
        )
        if matched_key is not None:
            return matched_key, warnings, ref

    if isinstance(title, str) and title.strip():
        return title.strip(), warnings, ref

    # Synthesis entry exists but has neither attribution_map matches nor title
    return fallback_text, warnings, ref


def _attribution_map_longest_match(
    attribution_map: dict[str, Any],
    claim_text: str,
    warnings: list[str],
    claim_id: str,
    synth_id: str,
) -> str | None:
    """v2.3 C2: longest-substring-match against claim_text; WARN on exact tie.

    Returns the matched key, or None if no key matches.
    """
    if not claim_text or not attribution_map:
        return None
    # Score each key by length of longest common substring with claim_text.
    # For practical claims (~200 chars) and attribution maps (~5 keys), this
    # is O(n*m) but n+m is small — no perf concern.
    candidates: list[tuple[int, str]] = []
    for key in attribution_map.keys():
        if not isinstance(key, str) or not key.strip():
            continue
        # Substring match in either direction (key in claim OR claim in key)
        # captures "longest match" cleanly.
        if key in claim_text or claim_text in key:
            score = len(key) if key in claim_text else len(claim_text)
            candidates.append((score, key))
        else:
            # Fall back to longest-common-substring length for partial overlap
            lcs = _longest_common_substring_len(key, claim_text)
            if lcs >= 10:  # arbitrary threshold to avoid noise
                candidates.append((lcs, key))

    if not candidates:
        return None
    candidates.sort(key=lambda pair: (-pair[0], pair[1]))
    best_score = candidates[0][0]
    tied = [k for s, k in candidates if s == best_score]
    if len(tied) > 1:
        warnings.append(
            f"claim {claim_id}: attribution_map in synthesis_entry {synth_id!r} "
            f"has multiple keys tied at substring-match length {best_score}: "
            f"{tied!r}. Picking first by source-order ({tied[0]!r}). "
            f"Consider tightening the attribution_map keys for disambiguation."
        )
    return tied[0]


def _longest_common_substring_len(a: str, b: str) -> int:
    """Length of the longest substring shared between a and b. O(len(a)*len(b))."""
    if not a or not b:
        return 0
    # Suffix-DP — small strings only, no need for suffix arrays.
    prev = [0] * (len(b) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


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

    # v2.3 C2: synthesis_entry.yml + pre_selection_manifest.yml drive claim-text
    # resolution for synthesis atoms. Both are optional — when absent, fall
    # through to the existing tiebreak behavior.
    synthesis_entries = _load_synthesis_entries(project_dir)
    pre_selections = _load_pre_selection(project_dir)
    all_warnings: list[str] = []

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
        fallback_text = str(best.get("excerpt") or "").strip() or "(no excerpt provided)"

        # v2.3 C2: when pre_selection_manifest carries synthesis_entry_ref for
        # this atom, resolve via the synthesis_entry's attribution_map / title.
        # Otherwise fall back to the v2.2 longest-excerpt tiebreak.
        selection = pre_selections.get(claim_id, {})
        text, c2_warnings, synth_id_used = _resolve_synthesis_attribution(
            selection=selection,
            synthesis_entries=synthesis_entries,
            excerpt_supporters=supporters,
            fallback_text=fallback_text,
            claim_id=claim_id,
        )
        all_warnings.extend(c2_warnings)

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

        # v2.3 C1 (backlog Item 2): per-claim cross-source corroboration count.
        # The aggregation half (multi-evidence binding into synthesis claims)
        # already shipped in v2.2; this surfaces the scoring as a first-class
        # field. Defined as the number of UNIQUE source_urls across the claim's
        # supporting evidence — synthesis claims naturally have count >= 3 (the
        # synthesis_entry validator's bar); primary atoms typically 1.
        corroboration_count = len({
            ev.get("source_url")
            for ev in supporters
            if isinstance(ev.get("source_url"), str) and ev.get("source_url")
        })

        record = {
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
        }
        # Additive: omit when 0/1 to keep small-corpus fixtures byte-stable
        # against the v2.2 baseline (no spurious diff just for primary atoms).
        if corroboration_count >= 2:
            record["corroboration_count"] = corroboration_count
        # v2.3 C2: persist the resolved synthesis_entry id for downstream
        # surfaces (dashboard link, agent-index attribution display).
        if synth_id_used:
            record["synthesis_entry_id"] = synth_id_used
        records.append(record)

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

    # v2.3 C2: emit any synthesis-attribution warnings to stderr so reviewers
    # see drift between synthesis_entry source_urls and the supporting
    # evidence's source_urls. Doesn't fail the build — drift is a curation
    # signal, not a structural error.
    for w in all_warnings:
        print(f"WARN: {w}", file=sys.stderr)

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
