"""Tests for scripts/scaffold_synthesis_entry.py (v2.4)."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import subprocess

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import scaffold_synthesis_entry as scaffold  # noqa: E402


def _make_project(
    base: Path,
    synthesis_atoms: list[dict],
    *,
    topic: str = "scaffold_test",
) -> Path:
    """Scaffold a minimal project dir for scaffold tests.

    Each ``synthesis_atoms`` entry is ``{atom_id, source_urls, claim_family, freshness_tier, text}``.
    Builds claim_graph.jsonl + evidence_ledger.yml + bib_ledger.yml so that
    scaffold_synthesis_entry.py has everything it needs.
    """
    project = base / "project"
    project.mkdir()

    cg_records = []
    ev_entries = []
    bib_entries = []

    for atom in synthesis_atoms:
        atom_id = atom["atom_id"]
        urls = atom["source_urls"]
        cf = atom.get("claim_family", "paper")
        ft = atom.get("freshness_tier", "stable")
        text = atom.get("text", f"Synthesis claim for {atom_id}")

        # Build bib + evidence entries per source URL
        evidence_ids = []
        entity_ids = []
        for i, url in enumerate(urls):
            bibkey = f"{atom_id.replace('claim_synthesis_', '')}_src{i}"
            ev_id = f"ev_{bibkey}"
            evidence_ids.append(ev_id)
            entity_ids.append(f"ent_{bibkey}")

            bib_entries.append({
                "bibkey": bibkey,
                "title": f"Source {i} for {atom_id}",
                "primary_url": url,
                "claim_family": cf,
                "freshness_tier": ft,
                "status": "verified",
                "evidence_ids": [ev_id],
            })
            ev_entries.append({
                "evidence_id": ev_id,
                "source_url": url,
                "source_type": "paper",
                "source_quality": "primary",
                "retrieved_at": "2026-05-23",
                "verification_method": "webfetch",
                "supports": [{
                    "claim_id": atom_id,
                    "field_path": "agent_index/0K_test.md",
                    "evidence_role": "supports",
                    "evidence_role_strength": "full",
                    "extraction_method": "paraphrase",
                    "link_confidence": 0.7,
                }],
                "excerpt": f"Excerpt from source {i}",
                "rights_status": "private_use",
            })

        # claim record (mimics build_claim_graph output)
        record = {
            "record_type": "claim",
            "id": atom_id,
            "topic": topic,
            "claim_type": "fact",
            "text": text,
            "status": "active",
            "evidence_ids": sorted(evidence_ids),
            "entity_ids": sorted(entity_ids),
            "confidence": {"score": 0.7, "factors": ["source: primary"]},
            "corroboration_count": len(set(urls)),
        }
        cg_records.append(record)

    (project / "claim_graph.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in cg_records) + "\n",
        encoding="utf-8",
    )
    (project / "evidence_ledger.yml").write_text(
        yaml.safe_dump({
            "schema_version": 3,
            "topic": topic,
            "generated_at": "2026-05-23",
            "current_as_of": "2026-05-23",
            "freshness_policy": "strict_live",
            "entries": ev_entries,
        }, sort_keys=False),
        encoding="utf-8",
    )
    (project / "bib_ledger.yml").write_text(
        yaml.safe_dump({
            "schema_version": 3,
            "topic": topic,
            "generated_at": "2026-05-23",
            "current_as_of": "2026-05-23",
            "freshness_policy": "strict_live",
            "claim_family_taxonomy": ["paper"],
            "entries": bib_entries,
        }, sort_keys=False),
        encoding="utf-8",
    )
    return project


# ---------- Happy path ----------


def test_scaffold_emits_synthesis_entry_with_correct_fields(tmp_path: Path) -> None:
    project = _make_project(tmp_path, [
        {
            "atom_id": "claim_synthesis_scaffold_test_emergence",
            "source_urls": [
                "https://arxiv.org/abs/2304.15004",
                "https://arxiv.org/abs/2505.01234",
                "https://arxiv.org/abs/2502.03200",
            ],
            "claim_family": "paper",
            "freshness_tier": "stable",
            "text": "Synthesis claim about emergence",
        },
    ])
    output = tmp_path / "synthesis_entry.yml"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scaffold_synthesis_entry.py"),
            str(project),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    data = yaml.safe_load(output.read_text(encoding="utf-8"))
    entries = data["entries"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["synthesis_id"] == "syn_scaffold_test_emergence"
    assert sorted(entry["source_urls"]) == sorted([
        "https://arxiv.org/abs/2304.15004",
        "https://arxiv.org/abs/2505.01234",
        "https://arxiv.org/abs/2502.03200",
    ])
    assert entry["title"] == "Synthesis claim about emergence"
    assert entry["claim_family"] == "paper"
    assert entry["volatility"] == "stable"  # all freshness_tier=stable
    assert entry["tier_summary"] == "T1: 3, T2: 0, T3: 0"  # all arxiv
    assert entry["status"] == "unverified"
    # attribution_map intentionally absent (placeholder for author)
    assert "attribution_map" not in entry


# ---------- Skip non-qualifying atoms ----------


def test_scaffold_skips_atoms_with_corroboration_under_3(tmp_path: Path) -> None:
    """corroboration_count < 3 means it doesn't qualify as a synthesis."""
    project = _make_project(tmp_path, [
        {
            "atom_id": "claim_synthesis_scaffold_test_weak",
            "source_urls": [
                "https://arxiv.org/abs/2304.15004",
                "https://arxiv.org/abs/2505.01234",
            ],  # only 2 sources
            "claim_family": "paper",
        },
    ])
    output = tmp_path / "synthesis_entry.yml"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scaffold_synthesis_entry.py"),
            str(project),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert "corroboration_count=2 < 3" in result.stderr
    assert not output.exists()


# ---------- Refuse overwrite without --merge ----------


def test_scaffold_refuses_overwrite_without_merge(tmp_path: Path) -> None:
    project = _make_project(tmp_path, [
        {
            "atom_id": "claim_synthesis_scaffold_test_a",
            "source_urls": [
                "https://arxiv.org/abs/2304.15004",
                "https://arxiv.org/abs/2505.01234",
                "https://arxiv.org/abs/2502.03200",
            ],
        },
    ])
    output = tmp_path / "synthesis_entry.yml"
    output.write_text("schema_version: 2\nentries: []\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scaffold_synthesis_entry.py"),
            str(project),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 1
    assert "refusing to overwrite" in result.stderr


# ---------- --merge preserves hand-authored entries ----------


def test_scaffold_merge_preserves_existing(tmp_path: Path) -> None:
    project = _make_project(tmp_path, [
        {
            "atom_id": "claim_synthesis_scaffold_test_b",
            "source_urls": [
                "https://arxiv.org/abs/2304.15004",
                "https://arxiv.org/abs/2505.01234",
                "https://arxiv.org/abs/2502.03200",
            ],
        },
    ])
    output = tmp_path / "synthesis_entry.yml"
    # Hand-authored entry already in the file
    hand_authored = {
        "synthesis_id": "syn_handauthored_keepme",
        "source_urls": [
            "https://arxiv.org/abs/1111.11111",
            "https://arxiv.org/abs/2222.22222",
            "https://arxiv.org/abs/3333.33333",
        ],
        "title": "Hand-authored synthesis that must survive merge",
        "claim_family": "paper",
        "volatility": "stable",
        "tier_summary": "T1: 3, T2: 0, T3: 0",
        "status": "verified",
        "attribution_map": {"key1": ["https://arxiv.org/abs/1111.11111"]},
    }
    output.write_text(
        yaml.safe_dump({
            "schema_version": 2,
            "topic": "scaffold_test",
            "generated_at": "2026-05-20",
            "current_as_of": "2026-05-20",
            "freshness_policy": "strict_live",
            "entries": [hand_authored],
        }, sort_keys=False),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scaffold_synthesis_entry.py"),
            str(project),
            "--output",
            str(output),
            "--merge",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr

    data = yaml.safe_load(output.read_text(encoding="utf-8"))
    by_id = {e["synthesis_id"]: e for e in data["entries"]}
    # Both entries present
    assert "syn_handauthored_keepme" in by_id
    assert "syn_scaffold_test_b" in by_id
    # Hand-authored is preserved verbatim (including attribution_map)
    preserved = by_id["syn_handauthored_keepme"]
    assert preserved["attribution_map"] == {"key1": ["https://arxiv.org/abs/1111.11111"]}
    assert preserved["status"] == "verified"


# ---------- --merge is idempotent ----------


def test_scaffold_merge_is_idempotent(tmp_path: Path) -> None:
    project = _make_project(tmp_path, [
        {
            "atom_id": "claim_synthesis_scaffold_test_c",
            "source_urls": [
                "https://arxiv.org/abs/2304.15004",
                "https://arxiv.org/abs/2505.01234",
                "https://arxiv.org/abs/2502.03200",
            ],
        },
    ])
    output = tmp_path / "synthesis_entry.yml"

    # First run: creates the file
    r1 = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scaffold_synthesis_entry.py"),
            str(project),
            "--output",
            str(output),
            "--merge",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r1.returncode == 0
    before = output.read_text(encoding="utf-8")

    # Second run: no change (synthesis_id already present)
    r2 = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scaffold_synthesis_entry.py"),
            str(project),
            "--output",
            str(output),
            "--merge",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r2.returncode == 0
    assert "no new synthesis entries to draft" in r2.stderr
    # File should not have been touched on the second run
    assert output.read_text(encoding="utf-8") == before


# ---------- Output passes the synthesis_entry validator ----------


def test_scaffold_output_passes_validator(tmp_path: Path) -> None:
    project = _make_project(tmp_path, [
        {
            "atom_id": "claim_synthesis_scaffold_test_validated",
            "source_urls": [
                "https://arxiv.org/abs/2304.15004",
                "https://arxiv.org/abs/2505.01234",
                "https://arxiv.org/abs/2502.03200",
            ],
            "freshness_tier": "active",
            "claim_family": "paper",
        },
    ])
    output = tmp_path / "synthesis_entry.yml"
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scaffold_synthesis_entry.py"),
            str(project),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    from validators import synthesis_entry
    errors = synthesis_entry.validate(output)
    assert errors == [], errors


# ---------- Volatility inheritance ----------


def test_scaffold_volatility_picks_most_volatile(tmp_path: Path) -> None:
    """When supporters have mixed freshness_tier values, scaffold picks the
    most-volatile mapping (per the template comment: 'synthesis inherits
    least-stable source's volatility')."""
    project = _make_project(tmp_path, [
        {
            "atom_id": "claim_synthesis_scaffold_test_volatile",
            "source_urls": [
                "https://arxiv.org/abs/2304.15004",
                "https://arxiv.org/abs/2505.01234",
                "https://arxiv.org/abs/2502.03200",
            ],
            "freshness_tier": "volatile",  # → fast-moving
        },
    ])
    output = tmp_path / "synthesis_entry.yml"
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "scaffold_synthesis_entry.py"),
            str(project),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    data = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert data["entries"][0]["volatility"] == "fast-moving"


# ---------- Unit: atom_id → synthesis_id helper ----------


@pytest.mark.parametrize("atom,expected", [
    ("claim_synthesis_emergence_debate", "syn_emergence_debate"),
    ("claim_synthesis_eval_drift_dynamic_eval", "syn_eval_drift_dynamic_eval"),
])
def test_atom_to_synthesis_id_happy(atom: str, expected: str) -> None:
    assert scaffold._atom_to_synthesis_id(atom) == expected


def test_atom_to_synthesis_id_rejects_non_synthesis() -> None:
    with pytest.raises(ValueError):
        scaffold._atom_to_synthesis_id("claim_topic_b1_a1_descriptor")
