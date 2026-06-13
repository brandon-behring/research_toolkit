"""Regression tests for v1.6 dataset-research skills.

Coverage:
- dataset_ledger validator: positive/negative cases (required fields,
  task_family enum, URL format, bibkey uniqueness, auth_required type,
  anti-cheat heuristic, --strict promotion, standalone CLI).
- Skill-body lint tests: each new skill body references its expected
  pattern points (medium fixture, cross_stage validator, dataset_sources
  reference).
- Integration: handcrafted smoke fixture validates under the new validator
  and existing agent_index + cross_stage where applicable.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from validators import cross_stage, dataset_ledger

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / ".claude" / "skills"
TEMPLATES = REPO_ROOT / "templates"
REFERENCES = REPO_ROOT / "references"
VALIDATORS_DIR = REPO_ROOT / "validators"
SMOKE_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "_handcrafted_dataset_smoke" / "dataset_ledger.yml"
)


# ---------- dataset_ledger validator: required-field positive cases ----------


def _minimal_ledger(extra: str = "") -> str:
    """Build a minimal valid ledger string with all 6 required fields populated."""
    return (
        "entries:\n"
        "- bibkey: smoke2025example\n"
        "  primary_url: https://example.com/datasets/foo\n"
        "  name: 'Smoke Example Dataset'\n"
        "  source: huggingface\n"
        "  status: unverified\n"
        "  task_family: classification\n"
        + extra
    )


def test_dataset_ledger_accepts_minimal(tmp_path: Path) -> None:
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger(), encoding="utf-8")
    assert dataset_ledger.validate(p) == []


def test_dataset_ledger_accepts_smoke_fixture() -> None:
    """The handcrafted smoke fixture validates cleanly."""
    if not SMOKE_FIXTURE.exists():
        pytest.skip(f"{SMOKE_FIXTURE} not present")
    assert dataset_ledger.validate(SMOKE_FIXTURE) == []


def test_dataset_ledger_accepts_optional_fields(tmp_path: Path) -> None:
    """All optional fields accepted when well-formed."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(
        _minimal_ledger(
            "  license: CC-BY-4.0\n"
            "  size: '10GB'\n"
            "  rows: 5000000\n"
            "  columns: 3\n"
            "  schema_url: https://example.com/datasets/foo/schema\n"
            "  access_method: hf datasets\n"
            "  auth_required: false\n"
            "  citation: 'Smith et al. (2025)'\n"
        ),
        encoding="utf-8",
    )
    assert dataset_ledger.validate(p) == []


# ---------- dataset_ledger validator: required-field negative cases ----------


def test_dataset_ledger_rejects_missing_required_field(tmp_path: Path) -> None:
    """Missing `name` should fail."""
    text = (
        "entries:\n"
        "- bibkey: smoke2025example\n"
        "  primary_url: https://example.com\n"
        "  source: huggingface\n"
        "  status: unverified\n"
        "  task_family: classification\n"
    )
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(text, encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert any("missing required field 'name'" in e for e in errors), errors


def test_dataset_ledger_rejects_invalid_task_family(tmp_path: Path) -> None:
    """task_family not in fixed enum should fail."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger().replace(
        "task_family: classification", "task_family: not_in_enum"
    ), encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert any("not_in_enum" in e and "fixed enum" in e for e in errors), errors


@pytest.mark.parametrize(
    "valid_value",
    [
        "classification", "regression", "sequence_labeling", "generation",
        "retrieval", "ranking", "multimodal", "graph", "time_series",
        "tabular", "recommendation", "structured_prediction", "other",
    ],
)
def test_dataset_ledger_accepts_all_enum_values(tmp_path: Path, valid_value: str) -> None:
    """Each of the 13 task_family enum values is accepted."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger().replace(
        "task_family: classification", f"task_family: {valid_value}"
    ), encoding="utf-8")
    assert dataset_ledger.validate(p) == []


def test_dataset_ledger_rejects_duplicate_bibkey(tmp_path: Path) -> None:
    """Duplicate bibkeys are rejected."""
    text = (
        "entries:\n"
        "- bibkey: dup2025one\n"
        "  primary_url: https://example.com/a\n"
        "  name: 'A'\n"
        "  source: hf\n"
        "  status: unverified\n"
        "  task_family: classification\n"
        "- bibkey: dup2025one\n"
        "  primary_url: https://example.com/b\n"
        "  name: 'B'\n"
        "  source: hf\n"
        "  status: unverified\n"
        "  task_family: classification\n"
    )
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(text, encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert any("duplicate bibkey" in e for e in errors), errors


def test_dataset_ledger_rejects_malformed_url(tmp_path: Path) -> None:
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger().replace(
        "primary_url: https://example.com/datasets/foo",
        "primary_url: not-a-url",
    ), encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert any("not a valid http(s) URL" in e for e in errors), errors


def test_dataset_ledger_rejects_non_bool_auth_required(tmp_path: Path) -> None:
    """auth_required must be bool when present (not string '0' or 'false')."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(
        _minimal_ledger("  auth_required: 'false'\n"),  # quoted string, not bool
        encoding="utf-8",
    )
    errors = dataset_ledger.validate(p)
    assert any("auth_required" in e and "boolean" in e for e in errors), errors


# ---------- Anti-cheat heuristic ----------


def _ledger_n_verified(n: int) -> str:
    parts = ["entries:"]
    for i in range(n):
        parts.append(
            f"- bibkey: smoke{i:04d}example\n"
            f"  primary_url: https://example.com/datasets/{i}\n"
            f"  name: 'Smoke Dataset {i}'\n"
            f"  source: huggingface\n"
            f"  status: verified\n"
            f"  task_family: classification\n"
        )
    return "\n".join(parts)


def test_anti_cheat_quiet_under_threshold(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """<30 entries → no warning even if all verified."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_ledger_n_verified(20), encoding="utf-8")
    errors = dataset_ledger.validate(p)
    assert errors == []
    err = capsys.readouterr().err
    assert "memory-verification" not in err.lower()


def test_anti_cheat_warns_at_30_plus_all_verified(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """≥30 entries all-verified → warning to stderr (not error by default)."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_ledger_n_verified(35), encoding="utf-8")
    errors = dataset_ledger.validate(p, strict=False)
    assert errors == []
    err = capsys.readouterr().err
    assert "memory-verification" in err.lower()


def test_anti_cheat_strict_promotes(tmp_path: Path) -> None:
    """--strict promotes the heuristic warning to an error."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_ledger_n_verified(35), encoding="utf-8")
    errors = dataset_ledger.validate(p, strict=True)
    assert any("memory-verification" in e.lower() for e in errors), errors


# ---------- Standalone CLI invocation ----------


def test_dataset_ledger_runs_standalone(tmp_path: Path) -> None:
    """python validators/dataset_ledger.py path works without `python -m`."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_minimal_ledger(), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "dataset_ledger.py"), str(p)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_dataset_ledger_cli_strict_flag(tmp_path: Path) -> None:
    """--strict CLI flag promotes warning to error → exit 1."""
    p = tmp_path / "dataset_ledger.yml"
    p.write_text(_ledger_n_verified(35), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATORS_DIR / "dataset_ledger.py"), "--strict", str(p)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 1, f"stderr: {result.stderr}"


# ---------- Skill-body lint tests ----------


def test_dataset_gather_skill_references_dataset_sources() -> None:
    text = (SKILLS / "dataset-gather.md").read_text(encoding="utf-8")
    assert "dataset_sources.md" in text, (
        "/dataset-gather must reference references/dataset_sources.md"
    )
    assert "dataset_ledger.template.yml" in text, (
        "/dataset-gather must reference templates/dataset_ledger.template.yml"
    )


def test_dataset_index_skill_references_cross_stage() -> None:
    """v1.5.1 convention: post-stage validators must include cross_stage."""
    text = (SKILLS / "dataset-index.md").read_text(encoding="utf-8")
    assert "cross_stage" in text, (
        "/dataset-index must reference cross_stage validator (v1.5.1 convention)"
    )


def test_dataset_research_wrapper_mentions_both_substages() -> None:
    """The one-shot wrapper must reference both /dataset-gather and /dataset-index."""
    text = (SKILLS / "dataset-research.md").read_text(encoding="utf-8")
    assert "/dataset-gather" in text and "/dataset-index" in text, (
        "/dataset-research wrapper must mention both sub-stages it orchestrates"
    )


def test_all_three_dataset_skills_exist() -> None:
    for skill in ("dataset-gather", "dataset-index", "dataset-research"):
        path = SKILLS / f"{skill}.md"
        assert path.exists(), f"missing {path}"


# ---------- Integration: smoke fixture validates ----------


def test_smoke_fixture_passes_dataset_validator() -> None:
    """The handcrafted smoke fixture under tests/fixtures/_handcrafted_dataset_smoke
    validates cleanly. This catches schema-shape regressions in either the
    fixture or the validator."""
    if not SMOKE_FIXTURE.exists():
        pytest.skip(f"{SMOKE_FIXTURE} not present")
    assert dataset_ledger.validate(SMOKE_FIXTURE) == []


# ---------- v1.7: anti-domain-substitution rule lint ----------


def test_dataset_index_skill_has_anti_domain_substitution_rule() -> None:
    """v1.7 BURN_IN finding from v1.6 dogfood: Stage 4 substituted Cornell
    for UCR (Eamonn Keogh's actual affiliation). v1.7 codified the rule:
    Source URL is byte-for-byte from the ledger; never auto-correct domains.

    This lint test asserts the rule is present in the /dataset-index skill
    body so a future skill-body refactor doesn't accidentally drop it.
    """
    text = (SKILLS / "dataset-index.md").read_text(encoding="utf-8")
    assert "NO domain substitution" in text or "no domain auto-correct" in text.lower(), (
        "/dataset-index skill body must codify the v1.7 'no domain substitution from "
        "memory' rule. See tests/test_v1_6_dataset_skills.py docstring for context."
    )
    # Also verify the Cornell→UCR example is preserved as the canonical worked failure.
    assert "cornell" in text.lower() and "ucr" in text.lower(), (
        "Skill body should reference the Cornell→UCR example so a cold-reading "
        "subagent understands the failure mode concretely."
    )


# ---------- v1.9 Item 1: compound-license rule ----------


def test_dataset_gather_skill_has_compound_license_rule() -> None:
    """v1.9: /dataset-gather must codify the compound-license check (read prose
    for restrictive caveats beyond YAML license field). Codified after the
    Nectar v1.8 audit finding (apache-2.0 in YAML + non-commercial in prose).
    """
    text = (SKILLS / "dataset-gather.md").read_text(encoding="utf-8")
    assert "compound-license" in text.lower(), (
        "/dataset-gather must reference 'compound-license' rule"
    )
    assert "prose" in text.lower(), (
        "/dataset-gather rule must mention checking prose, not just YAML"
    )
    # Worked example must be preserved
    assert "nectar" in text.lower(), (
        "Skill body should reference the Nectar v1.8 worked failure example"
    )


def test_audit_protocol_has_compound_license_check() -> None:
    """v1.9: audit_protocol.md codifies the compound-license check as audit-stage
    hygiene when --focus is 'license risks'."""
    text = (REFERENCES / "audit_protocol.md").read_text(encoding="utf-8")
    assert "Compound-license check" in text or "compound-license" in text.lower(), (
        "audit_protocol.md must have a compound-license sub-section (v1.9)"
    )


# ---------- v1.9 Item 2: paired-pipeline cross-link convention ----------


def test_agent_index_template_has_paired_cross_link_convention() -> None:
    """v1.9: agent_index_README.template.md codifies the bidirectional cross-link
    pattern between paper synthesis ↔ dataset dossier on the same topic.
    """
    text = (TEMPLATES / "agent_index_README.template.md").read_text(encoding="utf-8")
    assert "Paired-pipeline cross-link convention" in text, (
        "agent_index_README.template.md must codify the paired-pipeline cross-link convention (v1.9)"
    )
    # Worked example must be preserved
    assert "vol29_rlhf" in text and "rlhf_datasets" in text, (
        "Template should reference vol29_rlhf ↔ rlhf_datasets as the v1.8 worked example"
    )


# ---------- v1.9 Item 3: cross_stage extension for dataset_ledger ----------


def _project_with_dataset_ledger(
    tmp_path: Path,
    *,
    ledger_entries: list[dict],
    synthesis_files: dict[str, str] | None = None,
) -> Path:
    """Build a tmp project dir with a dataset_ledger.yml and optional agent_index/."""
    project = tmp_path / "project"
    project.mkdir()
    parts = ["entries:"]
    for e in ledger_entries:
        parts.append(f"- bibkey: {e['bibkey']}")
        for k, v in e.items():
            if k == "bibkey":
                continue
            if isinstance(v, bool):
                parts.append(f"  {k}: {str(v).lower()}")
            else:
                parts.append(f"  {k}: {v}")
        parts.append("")
    (project / "dataset_ledger.yml").write_text("\n".join(parts), encoding="utf-8")
    if synthesis_files:
        ai = project / "agent_index"
        ai.mkdir()
        for name, content in synthesis_files.items():
            (ai / name).write_text(content, encoding="utf-8")
    return project


_BASE_ENTRY = {
    "primary_url": "https://huggingface.co/datasets/example/foo",
    "name": "Foo Dataset",
    "source": "huggingface",
    "status": "verified",
    "task_family": "classification",
}


def test_cross_stage_passes_clean_dataset_project(tmp_path: Path) -> None:
    """Dataset project with ledger entry that's also referenced in agent_index passes."""
    entry = {"bibkey": "foo2025example", **_BASE_ENTRY}
    synthesis = (
        "# Foo synthesis\n\n"
        "## A1. Datasets\n\n"
        "- **Foo Dataset** — example.\n"
        "  - **Source:** https://huggingface.co/datasets/example/foo\n"
        "  - **Access:** hf datasets; auth_required: N\n"
        "  - **Schema:** see card\n"
        "  - **Size+License:** 1MB; MIT\n"
        "  - **Tasks:** classification\n"
        "  - **Status:** Verified.\n"
    )
    project = _project_with_dataset_ledger(
        tmp_path, ledger_entries=[entry], synthesis_files={"01_subset.md": synthesis}
    )
    assert cross_stage.validate(project) == []


def test_cross_stage_warns_on_orphan_dataset_ledger_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Ledger has an entry that doesn't appear in any agent_index Source line → warning."""
    entries = [
        {"bibkey": "foo2025example", **_BASE_ENTRY},
        {  # orphan — not in synthesis below
            "bibkey": "bar2025orphan",
            **{**_BASE_ENTRY, "primary_url": "https://huggingface.co/datasets/example/bar"},
        },
    ]
    synthesis = (
        "# Synthesis\n\n## A1.\n\n"
        "- **Foo** — example.\n"
        "  - **Source:** https://huggingface.co/datasets/example/foo\n"
        "  - **Access:** hf datasets; N\n"
        "  - **Schema:** —\n"
        "  - **Size+License:** small; MIT\n"
        "  - **Tasks:** —\n"
        "  - **Status:** Verified.\n"
    )
    project = _project_with_dataset_ledger(
        tmp_path, ledger_entries=entries, synthesis_files={"01_subset.md": synthesis}
    )
    errors = cross_stage.validate(project, strict=False)
    assert errors == []  # default mode: warning only
    err = capsys.readouterr().err
    assert "stale ledger" in err.lower() or "no matching agent_index" in err.lower()


def test_cross_stage_warns_on_orphan_dataset_synthesis_reference(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Synthesis Source URL that's not in dataset_ledger → warning."""
    entry = {"bibkey": "foo2025example", **_BASE_ENTRY}
    synthesis = (
        "# Synthesis\n\n## A1.\n\n"
        "- **Foo** — example.\n"
        "  - **Source:** https://huggingface.co/datasets/example/foo\n"
        "  - **Access:** —\n"
        "  - **Schema:** —\n"
        "  - **Size+License:** —\n"
        "  - **Tasks:** —\n"
        "  - **Status:** Verified.\n\n"
        "- **Bar (orphan)** — example.\n"
        "  - **Source:** https://huggingface.co/datasets/example/bar-orphan\n"
        "  - **Access:** —\n"
        "  - **Schema:** —\n"
        "  - **Size+License:** —\n"
        "  - **Tasks:** —\n"
        "  - **Status:** Verified.\n"
    )
    project = _project_with_dataset_ledger(
        tmp_path, ledger_entries=[entry], synthesis_files={"01_subset.md": synthesis}
    )
    errors = cross_stage.validate(project, strict=False)
    assert errors == []
    err = capsys.readouterr().err
    assert "not in dataset_ledger" in err.lower() or "unattributed" in err.lower()


def test_cross_stage_strict_promotes_dataset_orphans(tmp_path: Path) -> None:
    """--strict promotes both orphan-direction warnings to errors."""
    entries = [
        {"bibkey": "foo2025example", **_BASE_ENTRY},
        {  # orphan in ledger
            "bibkey": "bar2025orphan",
            **{**_BASE_ENTRY, "primary_url": "https://huggingface.co/datasets/example/bar"},
        },
    ]
    synthesis = (
        "# Synthesis\n\n## A1.\n\n"
        "- **Foo** — example.\n"
        "  - **Source:** https://huggingface.co/datasets/example/foo\n"
        "  - **Access:** —\n"
        "  - **Schema:** —\n"
        "  - **Size+License:** —\n"
        "  - **Tasks:** —\n"
        "  - **Status:** Verified.\n"
    )
    project = _project_with_dataset_ledger(
        tmp_path, ledger_entries=entries, synthesis_files={"01_subset.md": synthesis}
    )
    errors = cross_stage.validate(project, strict=True)
    # Should have at least one error (stale ledger entry)
    assert errors, "--strict should promote orphan warnings to errors"
    assert any("stale" in e.lower() or "no matching" in e.lower() for e in errors), errors


def test_cross_stage_handles_both_bib_and_dataset_ledger_independently(
    tmp_path: Path,
) -> None:
    """When both bib_ledger.yml and dataset_ledger.yml exist, both flows run."""
    project = tmp_path / "project"
    project.mkdir()
    # Minimal valid bib_ledger
    (project / "bib_ledger.yml").write_text(
        (
            "entries:\n"
            "- bibkey: smoke2025paper\n"
            "  primary_url: https://arxiv.org/abs/2501.00001\n"
            "  title: 'A paper'\n"
            "  status: unverified\n"
            "  claim_family: example\n"
        ),
        encoding="utf-8",
    )
    # Minimal valid dataset_ledger
    (project / "dataset_ledger.yml").write_text(
        (
            "entries:\n"
            "- bibkey: smoke2025data\n"
            "  primary_url: https://huggingface.co/datasets/example/foo\n"
            "  name: 'A dataset'\n"
            "  source: huggingface\n"
            "  status: unverified\n"
            "  task_family: classification\n"
        ),
        encoding="utf-8",
    )
    # No agent_index/ → both flows run their schema checks but no orphan
    # detection (which requires agent_index/).
    errors = cross_stage.validate(project)
    assert errors == [], (
        f"clean both-ledgers project should pass; got {errors}"
    )


def test_cross_stage_passes_on_v1_6_medium_dataset_subset_fixture() -> None:
    """Backward compat: the v1.6 medium_dataset_subset fixture validates under
    the v1.9 cross_stage with dataset_ledger flow active. Catches schema-shape
    regressions in either the fixture or the validator."""
    fixture = REPO_ROOT / "tests" / "fixtures" / "medium_dataset_subset"
    if not fixture.exists():
        pytest.skip(f"{fixture} not present")
    assert cross_stage.validate(fixture) == []
    # Strict mode also passes (the fixture is intentionally curated to be clean).
    assert cross_stage.validate(fixture, strict=True) == []


def test_cross_stage_passes_on_real_rlhf_datasets_dir() -> None:
    """v1.8 dogfood project validates under v1.9 cross_stage. Skipped if the
    working copy isn't on this machine."""
    real = Path.home() / "Claude" / "research-dossiers" / "research_rlhf_datasets"
    if not real.exists():
        pytest.skip(f"{real} not present")
    # Default mode should pass (agent_index lives in interview_prep_series, not
    # co-located, so the orphan checks gracefully no-op when agent_index is
    # absent under the project_dir).
    assert cross_stage.validate(real) == []
