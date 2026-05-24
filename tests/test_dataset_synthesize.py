"""Tests for scripts/dataset_synthesize.py.

Uses a test-double Anthropic client (no live API calls). Covers:
- Recipe validation (happy + error paths)
- Cost computation (per-token math + cache discount/premium)
- Message-building (cache_control placement on system + last few_shot)
- Synthesis loop (bail-at-cost trip, resume from existing JSONL,
  manifest sha256, per-template metric aggregation)
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import dataset_synthesize as ds  # type: ignore[import-not-found]


# ---------- Test-double Anthropic client ----------


@dataclass
class _FakeUsage:
    input_tokens: int = 200
    output_tokens: int = 400
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


@dataclass
class _FakeBlock:
    type: str = "text"
    text: str = "Generated sample."


@dataclass
class _FakeMessage:
    content: list[_FakeBlock] = field(default_factory=list)
    usage: _FakeUsage = field(default_factory=_FakeUsage)


class _FakeMessages:
    def __init__(self, scenarios: list[_FakeMessage]) -> None:
        self.scenarios = scenarios
        self.call_count = 0
        self.last_call_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> _FakeMessage:
        self.last_call_kwargs = kwargs
        if self.call_count < len(self.scenarios):
            msg = self.scenarios[self.call_count]
        else:
            msg = self.scenarios[-1]
        self.call_count += 1
        return msg


class _FakeClient:
    def __init__(self, scenarios: list[_FakeMessage]) -> None:
        self.messages = _FakeMessages(scenarios)


def _make_scenario(text: str = "Output", **usage_kwargs: int) -> _FakeMessage:
    return _FakeMessage(
        content=[_FakeBlock(type="text", text=text)],
        usage=_FakeUsage(**usage_kwargs),
    )


# ---------- Recipe validation ----------


def _minimal_recipe_dict() -> dict[str, Any]:
    return {
        "model": "claude-sonnet-4-7",
        "templates": [
            {
                "id": "t1",
                "system": "You are a generator.",
                "user_prompt": "Generate one sample.",
                "target_count": 3,
            }
        ],
    }


def test_validate_recipe_happy_path() -> None:
    recipe, errors = ds.validate_recipe(_minimal_recipe_dict())
    assert errors == []
    assert recipe is not None
    assert recipe.model == "claude-sonnet-4-7"
    assert len(recipe.templates) == 1
    assert recipe.templates[0].target_count == 3


def test_validate_recipe_rejects_unknown_model() -> None:
    data = _minimal_recipe_dict()
    data["model"] = "claude-mythical-9000"
    recipe, errors = ds.validate_recipe(data)
    assert recipe is None
    assert any("not in pricing table" in e for e in errors)


def test_validate_recipe_rejects_duplicate_template_id() -> None:
    data = _minimal_recipe_dict()
    data["templates"].append(dict(data["templates"][0]))
    recipe, errors = ds.validate_recipe(data)
    assert recipe is None
    assert any("duplicate id" in e for e in errors)


def test_validate_recipe_rejects_zero_target_count() -> None:
    data = _minimal_recipe_dict()
    data["templates"][0]["target_count"] = 0
    recipe, errors = ds.validate_recipe(data)
    assert recipe is None
    assert any("target_count" in e for e in errors)


def test_validate_recipe_rejects_bad_temperature() -> None:
    data = _minimal_recipe_dict()
    data["defaults"] = {"temperature": 3.0}
    recipe, errors = ds.validate_recipe(data)
    assert recipe is None
    assert any("temperature" in e for e in errors)


def test_validate_recipe_few_shot_role_must_be_user_or_assistant() -> None:
    data = _minimal_recipe_dict()
    data["templates"][0]["few_shot"] = [
        {"role": "system", "content": "bad"},
    ]
    recipe, errors = ds.validate_recipe(data)
    assert recipe is None
    assert any("must be 'user' or 'assistant'" in e for e in errors)


# ---------- Cost computation ----------


def test_compute_call_cost_input_only() -> None:
    cost = ds.compute_call_cost(
        "claude-sonnet-4-7", input_tokens=1_000_000, output_tokens=0
    )
    assert cost == pytest.approx(3.0, rel=1e-6)


def test_compute_call_cost_output_only() -> None:
    cost = ds.compute_call_cost(
        "claude-sonnet-4-7", input_tokens=0, output_tokens=1_000_000
    )
    assert cost == pytest.approx(15.0, rel=1e-6)


def test_compute_call_cost_cache_read_discount() -> None:
    # Cache reads at 10% of input price.
    cost = ds.compute_call_cost(
        "claude-sonnet-4-7",
        input_tokens=0,
        output_tokens=0,
        cache_read_tokens=1_000_000,
    )
    assert cost == pytest.approx(0.30, rel=1e-6)


def test_compute_call_cost_cache_write_premium() -> None:
    # Cache writes at 125% of input price.
    cost = ds.compute_call_cost(
        "claude-sonnet-4-7",
        input_tokens=0,
        output_tokens=0,
        cache_creation_tokens=1_000_000,
    )
    assert cost == pytest.approx(3.75, rel=1e-6)


def test_compute_call_cost_unknown_model_zero() -> None:
    cost = ds.compute_call_cost("claude-fictional-9", input_tokens=1000, output_tokens=1000)
    assert cost == 0.0


# ---------- Message building (cache_control placement) ----------


def test_build_messages_system_block_has_cache_control() -> None:
    template = ds.Template(
        id="t1",
        system="You are a generator.",
        user_prompt="Go.",
        target_count=1,
        few_shot=[],
    )
    system_blocks, messages = ds.build_messages(template)
    assert len(system_blocks) == 1
    assert system_blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert system_blocks[0]["text"] == "You are a generator."
    # No few_shot → messages has only the final user prompt.
    assert len(messages) == 1
    assert messages[0]["role"] == "user"


def test_build_messages_few_shot_only_last_has_cache_control() -> None:
    template = ds.Template(
        id="t1",
        system="System.",
        user_prompt="Go.",
        target_count=1,
        few_shot=[
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
        ],
    )
    system_blocks, messages = ds.build_messages(template)
    assert len(messages) == 5  # 4 few-shot + 1 final user
    # Only the LAST few_shot message has cache_control.
    for i in range(3):  # first 3 few-shot
        assert "cache_control" not in messages[i]["content"][0]
    # 4th few-shot (index 3, last few-shot) has cache_control
    assert messages[3]["content"][0]["cache_control"] == {"type": "ephemeral"}
    # Final user message does NOT have cache_control
    assert "cache_control" not in messages[4]["content"][0]


# ---------- Synthesis loop ----------


def test_synthesize_happy_path_3_samples(tmp_path: Path) -> None:
    recipe = ds.Recipe(
        model="claude-sonnet-4-7",
        templates=[
            ds.Template(
                id="t1",
                        system="sys",
                user_prompt="gen",
                target_count=3,
                metadata={"domain": "test"},
            )
        ],
        sha256="abc123",
    )
    client = _FakeClient(
        scenarios=[
            _make_scenario(text="s1", input_tokens=10, output_tokens=20),
            _make_scenario(text="s2", input_tokens=10, output_tokens=20, cache_read_input_tokens=100),
            _make_scenario(text="s3", input_tokens=10, output_tokens=20, cache_read_input_tokens=100),
        ]
    )
    exit_code, manifest = ds.synthesize(
        recipe=recipe,
        output_dir=tmp_path,
        bail_at_cost=10.0,
        client=client,
    )
    assert exit_code == 0
    assert manifest["total_samples"] == 3
    assert manifest["bail_fired"] is False
    assert manifest["templates"]["t1"]["actual"] == 3

    # samples.jsonl exists + has 3 rows
    samples_path = tmp_path / "samples.jsonl"
    rows = [json.loads(line) for line in samples_path.read_text().strip().split("\n")]
    assert len(rows) == 3
    assert all(row["template_id"] == "t1" for row in rows)
    assert all(row["metadata"]["domain"] == "test" for row in rows)
    assert {row["content"] for row in rows} == {"s1", "s2", "s3"}

    # manifest.json exists + has correct sha256 of samples.jsonl
    expected_sha = hashlib.sha256(samples_path.read_bytes()).hexdigest()
    assert manifest["output_jsonl_sha256"] == expected_sha


def test_synthesize_bail_at_cost_fires(tmp_path: Path) -> None:
    recipe = ds.Recipe(
        model="claude-sonnet-4-7",
        templates=[
            ds.Template(
                id="t1",
                        system="sys",
                user_prompt="gen",
                target_count=100,
            )
        ],
        sha256="abc",
    )
    # Each call: 1M input tokens + 1M output tokens = $3 + $15 = $18.
    # bail_at_cost=10 → first call exceeds (or finishes the in-progress sample
    # and the loop's next-iteration check trips). With cost=18 per call,
    # the first sample is written, total_cost becomes 18.0, next iteration sees
    # 18 >= 10 and breaks.
    client = _FakeClient(
        scenarios=[
            _make_scenario(text="s1", input_tokens=1_000_000, output_tokens=1_000_000),
        ]
        * 5
    )
    exit_code, manifest = ds.synthesize(
        recipe=recipe,
        output_dir=tmp_path,
        bail_at_cost=10.0,
        client=client,
    )
    assert exit_code == 2
    assert manifest["bail_fired"] is True
    assert manifest["total_samples"] == 1  # only one sample landed
    assert manifest["templates"]["t1"]["actual"] == 1
    assert manifest["templates"]["t1"]["target"] == 100  # unchanged


def test_synthesize_resumes_from_existing_jsonl(tmp_path: Path) -> None:
    # Pre-seed samples.jsonl with 2 rows; target_count=3 → only 1 more call.
    samples_path = tmp_path / "samples.jsonl"
    samples_path.write_text(
        json.dumps({"id": "pre1", "template_id": "t1", "content": "prior1"}) + "\n"
        + json.dumps({"id": "pre2", "template_id": "t1", "content": "prior2"}) + "\n"
    )
    recipe = ds.Recipe(
        model="claude-sonnet-4-7",
        templates=[
            ds.Template(
                id="t1",
                        system="sys",
                user_prompt="gen",
                target_count=3,
            )
        ],
        sha256="abc",
    )
    client = _FakeClient(scenarios=[_make_scenario(text="s3", input_tokens=10, output_tokens=20)])
    exit_code, manifest = ds.synthesize(
        recipe=recipe,
        output_dir=tmp_path,
        bail_at_cost=10.0,
        client=client,
    )
    assert exit_code == 0
    assert client.messages.call_count == 1  # only 1 new call (2 already present)
    assert manifest["templates"]["t1"]["actual"] == 3
    rows = [json.loads(line) for line in samples_path.read_text().strip().split("\n")]
    assert len(rows) == 3
    assert [r.get("content") for r in rows] == ["prior1", "prior2", "s3"]


def test_synthesize_per_template_metrics_aggregate_correctly(tmp_path: Path) -> None:
    recipe = ds.Recipe(
        model="claude-sonnet-4-7",
        templates=[
            ds.Template(id="t1", system="s1", user_prompt="g1", target_count=2),
            ds.Template(id="t2", system="s2", user_prompt="g2", target_count=1),
        ],
        sha256="abc",
    )
    client = _FakeClient(
        scenarios=[
            _make_scenario(text="t1a", input_tokens=100, output_tokens=200, cache_creation_input_tokens=1000),
            _make_scenario(text="t1b", input_tokens=100, output_tokens=200, cache_read_input_tokens=1000),
            _make_scenario(text="t2a", input_tokens=100, output_tokens=200, cache_creation_input_tokens=500),
        ]
    )
    exit_code, manifest = ds.synthesize(
        recipe=recipe,
        output_dir=tmp_path,
        bail_at_cost=100.0,
        client=client,
    )
    assert exit_code == 0
    assert manifest["templates"]["t1"]["actual"] == 2
    assert manifest["templates"]["t2"]["actual"] == 1
    assert manifest["templates"]["t1"]["cache_read_tokens"] == 1000
    assert manifest["templates"]["t1"]["cache_creation_tokens"] == 1000
    assert manifest["templates"]["t2"]["cache_creation_tokens"] == 500
    assert manifest["total_samples"] == 3


# ---------- Recipe sha256 ----------


def test_recipe_sha256_is_deterministic(tmp_path: Path) -> None:
    recipe_path = tmp_path / "recipe.yml"
    recipe_path.write_text(yaml.safe_dump(_minimal_recipe_dict()))
    sha_1 = ds.recipe_sha256(recipe_path)
    sha_2 = ds.recipe_sha256(recipe_path)
    assert sha_1 == sha_2
    assert len(sha_1) == 64


# ---------- API exception handling (PR #16 review feedback) ----------


class _FailingMessages:
    """Test-double messages that raises on the Nth call."""

    def __init__(self, fail_at: int, exc: Exception, scenarios: list[_FakeMessage]) -> None:
        self.fail_at = fail_at
        self.exc = exc
        self.scenarios = scenarios
        self.call_count = 0

    def create(self, **kwargs: Any) -> _FakeMessage:
        if self.call_count == self.fail_at:
            self.call_count += 1
            raise self.exc
        msg = self.scenarios[min(self.call_count, len(self.scenarios) - 1)]
        self.call_count += 1
        return msg


class _FailingClient:
    def __init__(self, fail_at: int, exc: Exception, scenarios: list[_FakeMessage]) -> None:
        self.messages = _FailingMessages(fail_at, exc, scenarios)


def test_synthesize_catches_api_exception_writes_partial_manifest(tmp_path: Path) -> None:
    """API failure mid-loop: should write partial manifest with api_error
    field set; samples up to the failing call are persisted; exit code 3."""
    recipe = ds.Recipe(
        model="claude-sonnet-4-7",
        templates=[
            ds.Template(
                id="t1",
                system="sys",
                user_prompt="gen",
                target_count=5,
            )
        ],
        sha256="abc",
    )
    # Fail on the 3rd call (0-indexed: index 2). Samples 1 + 2 should land.
    client = _FailingClient(
        fail_at=2,
        exc=RuntimeError("simulated rate limit"),
        scenarios=[
            _make_scenario(text="s1", input_tokens=10, output_tokens=20),
            _make_scenario(text="s2", input_tokens=10, output_tokens=20),
        ],
    )
    exit_code, manifest = ds.synthesize(
        recipe=recipe,
        output_dir=tmp_path,
        bail_at_cost=100.0,
        client=client,
    )
    assert exit_code == 3
    assert manifest["bail_fired"] is False
    assert manifest["api_error"] is not None
    assert "RuntimeError" in manifest["api_error"]
    assert "simulated rate limit" in manifest["api_error"]
    assert manifest["total_samples"] == 2  # 2 samples landed before failure
    assert manifest["templates"]["t1"]["actual"] == 2

    # samples.jsonl has 2 rows
    samples_path = tmp_path / "samples.jsonl"
    rows = [json.loads(line) for line in samples_path.read_text().strip().split("\n") if line]
    assert len(rows) == 2

    # manifest.json was written despite exception
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()
    on_disk = json.loads(manifest_path.read_text())
    assert on_disk["api_error"] is not None
    assert on_disk["total_samples"] == 2


def test_synthesize_detects_orphan_rows_in_manifest(tmp_path: Path) -> None:
    """If samples.jsonl has rows with template_id NOT in the current
    recipe, synthesize should: preserve the rows, warn to stderr,
    and surface orphan_template_ids + orphan_row_count in the manifest."""
    samples_path = tmp_path / "samples.jsonl"
    # 3 rows: 2 for current template "t1" + 1 for orphan "tX"
    samples_path.write_text(
        json.dumps({"id": "p1", "template_id": "t1", "content": "kept1"}) + "\n"
        + json.dumps({"id": "p2", "template_id": "t1", "content": "kept2"}) + "\n"
        + json.dumps({"id": "p3", "template_id": "tX", "content": "orphan"}) + "\n"
    )
    recipe = ds.Recipe(
        model="claude-sonnet-4-7",
        templates=[
            ds.Template(id="t1", system="s", user_prompt="g", target_count=2),
        ],
        sha256="abc",
    )
    # t1 already at target (2 prior rows); no API calls needed.
    client = _FakeClient(scenarios=[_make_scenario()])
    exit_code, manifest = ds.synthesize(
        recipe=recipe,
        output_dir=tmp_path,
        bail_at_cost=100.0,
        client=client,
    )
    assert exit_code == 0
    assert client.messages.call_count == 0  # no work needed
    assert manifest["orphan_template_ids"] == ["tX"]
    assert manifest["orphan_row_count"] == 1
    # total_samples counts only recipe-relevant template_ids (excludes orphan)
    assert manifest["total_samples"] == 2
    # samples.jsonl is preserved unchanged (3 rows including orphan)
    rows = [json.loads(line) for line in samples_path.read_text().strip().split("\n") if line]
    assert len(rows) == 3
    assert {r["id"] for r in rows} == {"p1", "p2", "p3"}


def test_synthesize_resume_after_api_failure_continues(tmp_path: Path) -> None:
    """After an API failure, re-running with a working client should resume
    from existing JSONL + generate the remaining shortfall."""
    # Pre-seed samples.jsonl with 2 rows (simulating prior failed run).
    samples_path = tmp_path / "samples.jsonl"
    samples_path.write_text(
        json.dumps({"id": "p1", "template_id": "t1", "content": "prior1"}) + "\n"
        + json.dumps({"id": "p2", "template_id": "t1", "content": "prior2"}) + "\n"
    )
    recipe = ds.Recipe(
        model="claude-sonnet-4-7",
        templates=[
            ds.Template(
                id="t1",
                system="sys",
                user_prompt="gen",
                target_count=4,
            )
        ],
        sha256="abc",
    )
    # Working client; should make 2 more calls (4 target - 2 prior).
    client = _FakeClient(
        scenarios=[
            _make_scenario(text="s3", input_tokens=10, output_tokens=20),
            _make_scenario(text="s4", input_tokens=10, output_tokens=20),
        ]
    )
    exit_code, manifest = ds.synthesize(
        recipe=recipe,
        output_dir=tmp_path,
        bail_at_cost=100.0,
        client=client,
    )
    assert exit_code == 0
    assert client.messages.call_count == 2
    assert manifest["api_error"] is None
    assert manifest["templates"]["t1"]["actual"] == 4
