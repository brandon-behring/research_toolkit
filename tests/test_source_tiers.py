"""Tests for scripts/source_tiers.py.

Anchor cases on the canonical examples in ``references/citation_rules.md``
§ Source-tier worked examples table. If anyone edits that table, these tests
should be updated in lockstep — drift surfaces immediately.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.source_tiers import assign_tier, tier_summary  # noqa: E402


# ---------- T1: Anthropic + arxiv + major-vendor docs ----------


@pytest.mark.parametrize("url", [
    "https://anthropic.com/docs/getting-started",
    "https://www.anthropic.com/engineering/multi-agent-research-system",
    "https://anthropic.com/news/claude-3-5-sonnet",
    "https://anthropic.com/research/some-paper",
    "https://claude.com/blog/building-multi-agent-systems",
    "https://claude.com/docs/agents",
    "https://claude.com/resources/some-guide",
    "https://platform.claude.com/docs/api",
    "https://code.claude.com/docs/cli",
    "https://docs.claude.com/some-page",
    "https://modelcontextprotocol.io/spec",
    "https://blog.modelcontextprotocol.io/v1-release",
    "https://arxiv.org/abs/2211.09527",
    "https://www.arxiv.org/abs/2304.15004",
    "https://docs.aws.amazon.com/bedrock/latest/userguide",
    "https://cloud.google.com/vertex-ai/docs",
    "https://platform.openai.com/docs/api-reference",
])
def test_t1_canonical_urls(url: str) -> None:
    assert assign_tier(url) == "T1", f"{url!r} should be T1"


# ---------- T2: Anthropic-managed but not spec; Anthropic-owned GH; vendor blogs ----------


@pytest.mark.parametrize("url", [
    "https://anthropic.skilljar.com/some-course",
    "https://github.com/anthropics/claude-code",
    "https://github.com/anthropic-experimental/some-repo",
    "https://github.com/modelcontextprotocol/servers",
    "https://openai.com/blog/some-post",
    "https://www.openai.com/research/o1",
    "https://aws.amazon.com/blogs/machine-learning/some-post",
    "https://engineering.atspotify.com/some-post",
])
def test_t2_canonical_urls(url: str) -> None:
    assert assign_tier(url) == "T2", f"{url!r} should be T2"


# ---------- T3: substack / medium / dev.to / press / aggregators ----------


@pytest.mark.parametrize("url", [
    "https://someone.substack.com/p/post",
    "https://medium.com/@user/article",
    "https://towardsdatascience.medium.com/article",
    "https://dev.to/user/post",
    "https://techcrunch.com/2025/05/article",
    "https://www.theregister.com/article",
    "https://reuters.com/technology/some-story",
    "https://venturebeat.com/ai/some-post",
    "https://github.com/random-user/random-repo",  # generic GH → T3
])
def test_t3_canonical_urls(url: str) -> None:
    assert assign_tier(url) == "T3", f"{url!r} should be T3"


# ---------- Default + malformed handling ----------


@pytest.mark.parametrize("url", [
    "",
    "not a url",
    "ftp://example.com/file",
    "https://random-blog.example/post",
])
def test_unknown_defaults_to_t3(url: str) -> None:
    assert assign_tier(url) == "T3", f"{url!r} should default to T3"


# ---------- tier_summary format ----------


def test_tier_summary_mixed() -> None:
    urls = [
        "https://arxiv.org/abs/2304.15004",       # T1
        "https://arxiv.org/abs/2211.09527",       # T1
        "https://github.com/anthropics/skills",   # T2
        "https://example.com/some-blog",          # T3 (default)
    ]
    assert tier_summary(urls) == "T1: 2, T2: 1, T3: 1"


def test_tier_summary_all_t1() -> None:
    assert tier_summary(["https://arxiv.org/abs/x", "https://arxiv.org/abs/y"]) == "T1: 2, T2: 0, T3: 0"


def test_tier_summary_empty() -> None:
    assert tier_summary([]) == "T1: 0, T2: 0, T3: 0"


def test_tier_summary_matches_validator_pattern() -> None:
    """tier_summary output must match validators/synthesis_entry.py's TIER_SUMMARY_PATTERN."""
    import re
    from validators.synthesis_entry import TIER_SUMMARY_PATTERN
    out = tier_summary(["https://arxiv.org/abs/x", "https://github.com/anthropics/y"])
    assert TIER_SUMMARY_PATTERN.match(out), f"{out!r} does not match the validator's pattern"
