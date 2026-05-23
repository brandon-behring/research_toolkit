"""Tests for the synthesis_entry validator.

Covers:
- Positive: minimal valid entry with 3 URLs passes.
- Negative: <3 URLs fails.
- Negative: missing required field fails.
- Negative: invalid URL fails.
- Negative: volatility / status enum violation fails.
- Negative: tier_summary missing T1 fails.
- Positive: cert_task_areas + attribution_map + contradictions all optional.
"""
from __future__ import annotations

from pathlib import Path

from validators import synthesis_entry


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "synthesis_entry.yml"
    p.write_text(body, encoding="utf-8")
    return p


VALID_MINIMAL = """\
schema_version: 2
topic: test
generated_at: 2026-05-23
current_as_of: 2026-05-23
freshness_policy: strict_live

entries:
- synthesis_id: syn_test_minimal
  source_urls:
  - https://www.anthropic.com/engineering/multi-agent-research-system
  - https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them
  - https://www.anthropic.com/engineering/april-23-postmortem
  title: 'Minimal valid synthesis entry'
  claim_family: agentic_pattern
  volatility: evolving
  tier_summary: "T1: 3"
  status: unverified
"""


def test_accepts_minimal_valid_entry(tmp_path: Path) -> None:
    p = _write(tmp_path, VALID_MINIMAL)
    assert synthesis_entry.validate(p) == []


def test_accepts_optional_fields(tmp_path: Path) -> None:
    body = VALID_MINIMAL + (
        "  cert_task_areas:\n"
        "  - Escalation / ambiguity resolution patterns\n"
        "  attribution_map:\n"
        "    'Multi-agent systems benefit from explicit escalation criteria':\n"
        "    - https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them\n"
        "  contradictions: []\n"
    )
    p = _write(tmp_path, body)
    assert synthesis_entry.validate(p) == []


def test_rejects_under_3_source_urls(tmp_path: Path) -> None:
    body = """\
entries:
- synthesis_id: syn_test_too_few
  source_urls:
  - https://www.anthropic.com/engineering/multi-agent-research-system
  - https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them
  title: 'Only two sources'
  claim_family: agentic_pattern
  volatility: evolving
  tier_summary: "T1: 2"
  status: unverified
"""
    p = _write(tmp_path, body)
    errors = synthesis_entry.validate(p)
    assert any("source_urls" in e and "≥3" in e for e in errors), errors


def test_rejects_missing_required_field(tmp_path: Path) -> None:
    # Omit title.
    body = """\
entries:
- synthesis_id: syn_test_no_title
  source_urls:
  - https://a.example.com/1
  - https://a.example.com/2
  - https://a.example.com/3
  claim_family: agentic_pattern
  volatility: evolving
  tier_summary: "T1: 1, T2: 2"
  status: unverified
"""
    p = _write(tmp_path, body)
    errors = synthesis_entry.validate(p)
    assert any("missing required field 'title'" in e for e in errors), errors


def test_rejects_invalid_url(tmp_path: Path) -> None:
    body = """\
entries:
- synthesis_id: syn_test_bad_url
  source_urls:
  - not-a-valid-url
  - https://a.example.com/2
  - https://a.example.com/3
  title: 'Bad URL in list'
  claim_family: agentic_pattern
  volatility: evolving
  tier_summary: "T1: 1, T2: 2"
  status: unverified
"""
    p = _write(tmp_path, body)
    errors = synthesis_entry.validate(p)
    assert any("source_urls[0]" in e and "not a valid" in e for e in errors), errors


def test_rejects_invalid_volatility(tmp_path: Path) -> None:
    body = VALID_MINIMAL.replace("volatility: evolving", "volatility: super-volatile")
    p = _write(tmp_path, body)
    errors = synthesis_entry.validate(p)
    assert any("volatility" in e and "not in" in e for e in errors), errors


def test_rejects_tier_summary_without_t1(tmp_path: Path) -> None:
    body = VALID_MINIMAL.replace('tier_summary: "T1: 3"', 'tier_summary: "T2: 3, T3: 1"')
    p = _write(tmp_path, body)
    errors = synthesis_entry.validate(p)
    assert any("tier_summary" in e and "T1" in e for e in errors), errors


def test_rejects_malformed_tier_summary(tmp_path: Path) -> None:
    body = VALID_MINIMAL.replace('tier_summary: "T1: 3"', 'tier_summary: "mostly T1 and some T2"')
    p = _write(tmp_path, body)
    errors = synthesis_entry.validate(p)
    assert any("tier_summary" in e and "pattern" in e for e in errors), errors


def test_rejects_duplicate_synthesis_id(tmp_path: Path) -> None:
    body = VALID_MINIMAL + (
        "- synthesis_id: syn_test_minimal\n"  # duplicate
        "  source_urls:\n"
        "  - https://a.example.com/1\n"
        "  - https://a.example.com/2\n"
        "  - https://a.example.com/3\n"
        "  title: 'Dup'\n"
        "  claim_family: agentic_pattern\n"
        "  volatility: stable\n"
        '  tier_summary: "T1: 3"\n'
        "  status: unverified\n"
    )
    p = _write(tmp_path, body)
    errors = synthesis_entry.validate(p)
    assert any("duplicate synthesis_id" in e for e in errors), errors


def test_validates_template_file() -> None:
    """The shipped template must itself validate cleanly."""
    template_path = (
        Path(__file__).resolve().parent.parent
        / "templates"
        / "synthesis_entry.template.yml"
    )
    assert template_path.exists()
    # The template uses '<YYYY-MM-DD>' placeholders that yaml.safe_load handles
    # as strings — schema is valid even with placeholders.
    errors = synthesis_entry.validate(template_path)
    assert errors == [], errors
