"""Tests for validators/topic_backlog.py: positive + negative cases.

The topic_backlog validator gates /topic-discovery output. Positive: a minimal
backlog with both deepen + adjacent entries, plus the shipped template.
Negatives: one corruption per rule, each asserting an identifying error
substring. Plus the both-kinds anti-cheat (>=8 one-sided entries) under --strict.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from validators import topic_backlog

REPO_ROOT = Path(__file__).resolve().parent.parent


def _deepen_entry(topic_id: str = "dml-het-effects") -> dict:
    return {
        "topic_id": topic_id,
        "title": "Double ML for heterogeneous treatment effects",
        "kind": "deepen",
        "track": 2,
        "priority": "P0",
        "rationale": "vol02 ch15 frontier; matches causal interest",
        "claim_family_seeds": ["identification", "estimation", "inference"],
        "status": "proposed",
        "source_volume": "vol02_causal_inference",
        "source_los": ["CI-15.2"],
        "seed_sources": ["https://arxiv.org/abs/1608.00060"],
    }


def _adjacent_entry(topic_id: str = "behavioral-econ-product") -> dict:
    return {
        "topic_id": topic_id,
        "title": "Behavioral economics for product experimentation",
        "kind": "adjacent",
        "track": "cross",
        "priority": "P1",
        "rationale": "scaffold vol21; bridges vol01 + vol13",
        "claim_family_seeds": ["choice-architecture", "field-experiments", "welfare"],
        "status": "proposed",
    }


def _minimal_backlog(entries: list[dict] | None = None) -> dict:
    return {
        "schema_version": 1,
        "source_corpus": "interview_prep_series",
        "generated_at": "2026-05-24",
        "entries": entries
        if entries is not None
        else [_deepen_entry(), _adjacent_entry()],
    }


def _write(tmp_path: Path, data: dict, name: str = "topic_backlog.yml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


# ---------- positive cases ----------


def test_topic_backlog_accepts_minimal(tmp_path: Path) -> None:
    assert topic_backlog.validate(_write(tmp_path, _minimal_backlog())) == []


def test_topic_backlog_accepts_shipped_template() -> None:
    # The committed template must stay schema-valid.
    template = REPO_ROOT / "templates" / "topic_backlog.template.yml"
    assert topic_backlog.validate(template) == []


# ---------- negative cases (one rule each) ----------


def test_topic_backlog_rejects_duplicate_topic_id(tmp_path: Path) -> None:
    data = _minimal_backlog([_deepen_entry("dup"), _adjacent_entry("dup")])
    errors = topic_backlog.validate(_write(tmp_path, data))
    assert any("duplicate topic_id" in e for e in errors), errors


def test_topic_backlog_rejects_too_few_claim_family_seeds(tmp_path: Path) -> None:
    entry = _deepen_entry()
    entry["claim_family_seeds"] = ["only", "two"]
    errors = topic_backlog.validate(_write(tmp_path, _minimal_backlog([entry, _adjacent_entry()])))
    assert any("claim_family_seeds" in e and "at least 3" in e for e in errors), errors


def test_topic_backlog_rejects_bad_status(tmp_path: Path) -> None:
    entry = _deepen_entry()
    entry["status"] = "bogus"
    errors = topic_backlog.validate(_write(tmp_path, _minimal_backlog([entry, _adjacent_entry()])))
    assert any("not in" in e and "status" in e for e in errors), errors


def test_topic_backlog_rejects_bad_kind(tmp_path: Path) -> None:
    entry = _deepen_entry()
    entry["kind"] = "tangential"
    errors = topic_backlog.validate(_write(tmp_path, _minimal_backlog([entry, _adjacent_entry()])))
    assert any("not in" in e and "kind" in e for e in errors), errors


def test_topic_backlog_rejects_deepen_without_source_volume(tmp_path: Path) -> None:
    entry = _deepen_entry()
    del entry["source_volume"]
    errors = topic_backlog.validate(_write(tmp_path, _minimal_backlog([entry, _adjacent_entry()])))
    assert any("requires source_volume" in e for e in errors), errors


def test_topic_backlog_rejects_non_kebab_topic_id(tmp_path: Path) -> None:
    errors = topic_backlog.validate(
        _write(tmp_path, _minimal_backlog([_deepen_entry("Not Kebab"), _adjacent_entry()]))
    )
    assert any("kebab" in e for e in errors), errors


def test_topic_backlog_rejects_invalid_seed_source_url(tmp_path: Path) -> None:
    entry = _deepen_entry()
    entry["seed_sources"] = ["not-a-url"]
    errors = topic_backlog.validate(_write(tmp_path, _minimal_backlog([entry, _adjacent_entry()])))
    assert any("seed_sources" in e and "not a valid" in e for e in errors), errors


def test_topic_backlog_rejects_missing_required_field(tmp_path: Path) -> None:
    entry = _adjacent_entry()
    del entry["rationale"]
    errors = topic_backlog.validate(_write(tmp_path, _minimal_backlog([_deepen_entry(), entry])))
    assert any("missing required field" in e and "rationale" in e for e in errors), errors


def test_topic_backlog_rejects_missing_top_level_field(tmp_path: Path) -> None:
    data = _minimal_backlog()
    del data["schema_version"]
    errors = topic_backlog.validate(_write(tmp_path, data))
    assert any("schema_version" in e for e in errors), errors


# ---------- both-kinds anti-cheat (>= 8 entries) ----------


def test_topic_backlog_warns_one_axis_default_errors_strict(tmp_path: Path) -> None:
    # 8 deepen entries, no adjacent → one-axis backlog.
    entries = [_deepen_entry(f"deepen-{i}") for i in range(8)]
    path = _write(tmp_path, _minimal_backlog(entries))
    # Default: warning to stderr, not a hard error.
    assert topic_backlog.validate(path) == []
    # Strict: warning promotes to error.
    errors = topic_backlog.validate(path, strict=True)
    assert any("one-axis" in e for e in errors), errors


# ---------- research-program backlog (kind: topic-backlog + candidates:) ----------
#
# A legitimately different, hand-authored schema that shares the filename
# pattern. The validator must recognize it via the discriminator and apply the
# lenient candidates rules (id + label) instead of the /topic-discovery rules.


def _rp_candidate(cid: str = "kv-cache-stability") -> dict:
    return {
        "id": cid,
        "parent": "ctx-assembly",
        "label": "KV-cache stability (the assembly invariant)",
        "seed": "deep-dive 1.2",
        "note": "Likely a core sub-area, not its own node.",
    }


def _rp_backlog(candidates: list[dict] | None = None) -> dict:
    return {
        "schema_version": "1.0",  # STRING — the research-program file uses "1.0"
        "kind": "topic-backlog",
        "generated_at": "2026-05-26",
        "note": "Append-only candidate sub-topics surfaced from the launchpad docs.",
        "candidates": candidates
        if candidates is not None
        else [_rp_candidate(), _rp_candidate("compaction-strategies")],
    }


def test_topic_backlog_accepts_research_program_shape(tmp_path: Path) -> None:
    # Full research-program shape (string schema_version, kind, candidates).
    assert topic_backlog.validate(_write(tmp_path, _rp_backlog())) == []


def test_topic_backlog_accepts_research_program_minimal_candidate(tmp_path: Path) -> None:
    # Only id + label are required; optional parent/seed/note/status omitted.
    data = _rp_backlog([{"id": "instruction-budget", "label": "Instruction budget"}])
    assert topic_backlog.validate(_write(tmp_path, data)) == []


def test_topic_backlog_accepts_real_research_program_file() -> None:
    # The live hand-authored backlog must validate (the bug this fix targets).
    rp_file = Path(
        "/Users/brandonbehring/claude-books/docs/research-program/topic-backlog.yml"
    )
    if rp_file.exists():
        assert topic_backlog.validate(rp_file) == []


def test_topic_backlog_routes_candidates_without_kind(tmp_path: Path) -> None:
    # Discriminator's second branch: candidates present, entries absent, no kind.
    data = _rp_backlog()
    del data["kind"]
    errors = topic_backlog.validate(_write(tmp_path, data))
    # Routed to the research-program path, which then flags the missing kind.
    assert any("kind" in e and "topic-backlog" in e for e in errors), errors


def test_topic_backlog_rejects_research_program_duplicate_id(tmp_path: Path) -> None:
    data = _rp_backlog([_rp_candidate("dup"), _rp_candidate("dup")])
    errors = topic_backlog.validate(_write(tmp_path, data))
    assert any("duplicate id" in e for e in errors), errors


def test_topic_backlog_rejects_research_program_non_kebab_id(tmp_path: Path) -> None:
    data = _rp_backlog([_rp_candidate("Not Kebab")])
    errors = topic_backlog.validate(_write(tmp_path, data))
    assert any("kebab" in e for e in errors), errors


def test_topic_backlog_rejects_research_program_missing_label(tmp_path: Path) -> None:
    data = _rp_backlog([{"id": "no-label-here"}])
    errors = topic_backlog.validate(_write(tmp_path, data))
    assert any("missing required field 'label'" in e for e in errors), errors


def test_topic_backlog_rejects_research_program_empty_optional_field(tmp_path: Path) -> None:
    cand = _rp_candidate()
    cand["status"] = "   "  # present but empty → reject (omit instead)
    errors = topic_backlog.validate(_write(tmp_path, _rp_backlog([cand])))
    assert any("status" in e and "non-empty" in e for e in errors), errors


def test_topic_backlog_rejects_research_program_empty_candidates(tmp_path: Path) -> None:
    data = _rp_backlog([])
    errors = topic_backlog.validate(_write(tmp_path, data))
    assert any("candidates" in e and "non-empty list" in e for e in errors), errors
