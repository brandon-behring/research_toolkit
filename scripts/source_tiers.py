"""Map source URLs to tier labels (T1 / T2 / T3) — v2.4+.

Single source of truth for host → tier assignment, extracted from the
canonical table in ``references/citation_rules.md`` § Source-tier worked
examples. Used by:

- ``scripts/scaffold_synthesis_entry.py`` to compute ``tier_summary``
  for new synthesis_entry.yml entries (the validator requires ≥1 T1).
- Future tooling that needs deterministic host-tier mapping.

**Spec of record:** the citation_rules.md table. Update this module in
lockstep with edits to the markdown table; tests anchor on the table's
canonical examples so drift surfaces immediately.

The mapping is a bounded list of regex patterns evaluated in order
(longest-match-wins). Unrecognized hosts default to T3 (the most
conservative tier — T3 doesn't count toward the synthesis validator's
≥1 T1 requirement).
"""
from __future__ import annotations

import re
from urllib.parse import urlparse


# Ordered list of (compiled regex against URL, tier) — first match wins.
# Patterns match the FULL URL (including scheme + path), not just the host,
# so we can distinguish `claude.com/blog/*` (T1) from `claude.com/<other>` (T3).
_RULES: list[tuple[re.Pattern[str], str]] = [
    # --- T1: Anthropic-authored docs / blog / news / API docs ---
    (re.compile(r"^https?://(?:www\.)?anthropic\.com/(docs|engineering|news|research)(/|$)"), "T1"),
    (re.compile(r"^https?://(?:www\.)?claude\.com/(blog|docs|resources)(/|$)"), "T1"),
    (re.compile(r"^https?://platform\.claude\.com/docs(/|$)"), "T1"),
    (re.compile(r"^https?://code\.claude\.com/docs(/|$)"), "T1"),
    (re.compile(r"^https?://docs\.claude\.com(/|$)"), "T1"),
    # --- T1: MCP spec ---
    (re.compile(r"^https?://(?:blog\.)?modelcontextprotocol\.io(/|$)"), "T1"),
    # --- T1: arXiv abstract pages (NOT /pdf/) ---
    (re.compile(r"^https?://(?:www\.)?arxiv\.org/abs/"), "T1"),
    # --- T1: major-vendor authoritative docs ---
    (re.compile(r"^https?://(?:docs\.)?aws\.amazon\.com/(bedrock|sagemaker)(/|$)"), "T1"),
    (re.compile(r"^https?://cloud\.google\.com/(vertex-ai|gemini)(/|$)"), "T1"),
    (re.compile(r"^https?://(?:learn|docs)\.microsoft\.com/.+(azure-openai|cognitive-services)"), "T1"),
    (re.compile(r"^https?://platform\.openai\.com/docs(/|$)"), "T1"),
    # --- T2: Anthropic-managed but not spec/docs ---
    (re.compile(r"^https?://anthropic\.skilljar\.com(/|$)"), "T2"),
    # --- T2: Anthropic-owned GitHub orgs (releases + READMEs) ---
    (re.compile(r"^https?://github\.com/(anthropics|anthropic-experimental)/"), "T2"),
    (re.compile(r"^https?://github\.com/modelcontextprotocol/"), "T2"),
    # --- T2: non-Anthropic vendor blogs (vendor-authoritative on vendor topics) ---
    # Vendor engineering blogs by recognizable companies. Mostly heuristic:
    # if the host is `<bigvendor>.com/(blog|engineering|news)`, treat as T2.
    (re.compile(r"^https?://(?:www\.)?openai\.com/(blog|news|research)(/|$)"), "T2"),
    (re.compile(r"^https?://(?:www\.)?aws\.amazon\.com/blogs(/|$)"), "T2"),
    (re.compile(r"^https?://(?:engineering|tech)\.[\w.-]+/"), "T2"),
    # --- T3: substack, medium, dev.to ---
    (re.compile(r"^https?://[\w-]+\.substack\.com(/|$)"), "T3"),
    (re.compile(r"^https?://(?:www\.)?medium\.com(/|$)"), "T3"),
    (re.compile(r"^https?://[\w-]+\.medium\.com(/|$)"), "T3"),
    (re.compile(r"^https?://(?:www\.)?dev\.to(/|$)"), "T3"),
    # --- T3: tech press / news ---
    (re.compile(
        r"^https?://(?:www\.)?(techcrunch|theregister|reuters|venturebeat|"
        r"theverge|wired|arstechnica|zdnet|cnet|bloomberg|axios)\.com(/|$)"
    ), "T3"),
    # --- T3: aggregators / awesome-lists / generic GitHub READMEs ---
    # Generic GitHub repos (not in T2 allowlist above) default to T3.
    (re.compile(r"^https?://github\.com/"), "T3"),
]


def assign_tier(url: str) -> str:
    """Return ``"T1"`` / ``"T2"`` / ``"T3"`` for ``url``.

    Unrecognized hosts default to T3 (most conservative). Empty / malformed
    URLs also return T3.
    """
    if not isinstance(url, str) or not url.strip():
        return "T3"
    # Quick sanity: must be a parseable http(s) URL.
    try:
        parsed = urlparse(url)
    except Exception:
        return "T3"
    if parsed.scheme not in ("http", "https"):
        return "T3"
    for pattern, tier in _RULES:
        if pattern.search(url):
            return tier
    return "T3"


def tier_summary(urls: list[str]) -> str:
    """Render a ``T<n>: N`` summary string matching the synthesis_entry validator.

    Always emits all three tiers in order ``T1: N1, T2: N2, T3: N3`` even when
    counts are zero — keeps the format predictable for downstream parsers and
    the validator's ``TIER_ENTRY_PATTERN`` regex accepts trailing zeros.
    """
    counts = {"T1": 0, "T2": 0, "T3": 0}
    for u in urls or []:
        counts[assign_tier(u)] += 1
    return f"T1: {counts['T1']}, T2: {counts['T2']}, T3: {counts['T3']}"
