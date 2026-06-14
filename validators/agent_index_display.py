"""Audit-time enforcement of the display-vs-evidence contract in agent_index/.

The strict-live guarantee is that every Mechanism sentence SHOWN to a reader
(or an AI consuming the claim graph) is grounded in the cached source: the
displayed text must be a verbatim raw-byte substring of the cached source
snapshot (whitespace-normalized). ``scripts/render_agent_index.py`` enforces
this at WRITE time via its ``verify_display`` / ``build_anchor`` guard — a
display override is only emitted when it is still a substring, otherwise the
renderer falls back to the anchored excerpt.

This validator is the AUDIT-time half of the same contract. An agent_index
family file edited by hand, or rendered by an older path that lacked the
guard, could silently show a Mechanism sentence that is NOT in the cache,
breaking the anti-hallucination contract. This module re-checks, for every
rendered ``- **Mechanism:** ...`` bullet, that its display text is still a
normalized substring of the cached text the bullet is grounded in.

Scope: the substring contract enforces the *verbatim* guarantee, so it applies to
Mechanisms grounded in ``verbatim_match`` (or unspecified) evidence. A Mechanism
backed by ``extraction_method: paraphrase`` evidence is a *declared* paraphrase — a
synthesis of the source, not a verbatim claim — and is exempt from the substring
check (its cache linkage is still verified). This lets depth-expanded paraphrase
dossiers keep their synthesized Mechanism displays without weakening the contract
where verbatim is actually claimed.

Linkage (mirrors the renderer exactly — see ``_render_entry`` there):

1. Preferred (what shipped dossiers emit): an inline ``- **Evidence:**
   <evidence_id>`` bullet in the same block resolves the evidence record
   directly; its cache linkage (``excerpt_anchor.cache_id``, else ``cache_ids``,
   else a scalar ``cache_id`` — the same shapes ``v2_common`` reads) points at
   the cache_manifest entry whose ``text_path`` is the cached source.
2. Fallback (blocks with no Evidence bullet): the block's ``- **Source:**
   <bibkey>`` line + the family-file name are matched against
   ``pre_selection_manifest.yml`` selections (``family`` + ``bibkey``), then
   ``evidence_id`` → evidence_ledger record → cache_manifest ``text_path``.

A Mechanism bullet whose display text equals the anchored excerpt (the common
case) trivially passes; a cleaner display OVERRIDE passes iff it is still a
substring; a bullet with no resolvable cache linkage is a clear error (never
silently passed). The substring + normalization semantics reuse
``v2_common._normalize_ws`` so this validator agrees with the renderer.

Complements ``validators/agent_index.py`` (which checks the folder SCHEMA);
this is the CONTENT / substring check. Wired into ``validators/cross_stage.py``
so a normal cross-stage run includes the display audit.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.v2_common import (
    _normalize_ws,
    load_yaml_mapping,
    resolve_cache_path,
)

# A canonical 5-bullet block starts at a ``- **Source:**`` line and runs to the
# next Source line (or EOF). Mirrors agent_index.ENTRY_BLOCK_RE so we segment
# entries identically.
ENTRY_BLOCK_RE = re.compile(
    r"^\s*-\s*\*\*Source:\*\*.*?(?=^\s*-\s*\*\*Source:\*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)
SOURCE_LINE_RE = re.compile(r"^\s*-\s*\*\*Source:\*\*\s*(.+?)\s*$", re.MULTILINE)
MECHANISM_LINE_RE = re.compile(r"^\s*-\s*\*\*Mechanism:\*\*\s*(.+?)\s*$", re.MULTILINE)
EVIDENCE_LINE_RE = re.compile(r"^\s*-\s*\*\*Evidence:\*\*\s*(.+?)\s*$", re.MULTILINE)
# A Source line carries the bibkey as its first whitespace-delimited token
# (renderer emits ``- **Source:** {bibkey}``; richer dossiers may append a URL
# or title after it).
BIBKEY_TOKEN_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_\-]*)")


def _cache_entries(cache: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        e["cache_id"]: e
        for e in cache.get("entries", [])
        if isinstance(e, dict) and isinstance(e.get("cache_id"), str)
    }


def _evidence_by_id(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        e["evidence_id"]: e
        for e in evidence.get("entries", [])
        if isinstance(e, dict) and isinstance(e.get("evidence_id"), str)
    }


def _evidence_cache_ids(evidence: dict[str, Any]) -> list[str]:
    """Extract the cache_id(s) an evidence record points at (all known shapes).

    Mirrors how ``v2_common.verify_excerpt_anchor`` and ``collect_entry_ids``
    read the ledger: a v3 record anchors via ``excerpt_anchor.cache_id``; v2
    records carry a ``cache_ids`` list; a few legacy records use a scalar
    ``cache_id``. We try them in that order and dedupe, preserving order.
    """
    ids: list[str] = []
    anchor = evidence.get("excerpt_anchor")
    if isinstance(anchor, dict):
        aid = anchor.get("cache_id")
        if isinstance(aid, str) and aid.strip():
            ids.append(aid.strip())
    cache_ids = evidence.get("cache_ids")
    if isinstance(cache_ids, list):
        for cid in cache_ids:
            if isinstance(cid, str) and cid.strip():
                ids.append(cid.strip())
    scalar = evidence.get("cache_id")
    if isinstance(scalar, str) and scalar.strip():
        ids.append(scalar.strip())
    seen: set[str] = set()
    deduped: list[str] = []
    for cid in ids:
        if cid not in seen:
            seen.add(cid)
            deduped.append(cid)
    return deduped


def _read_cache_text(
    cache_id: str,
    cache_entries: dict[str, dict[str, Any]],
    cache_path: Path,
    cache_root: str | None,
) -> str | None:
    """Resolve + read the cached text for a single cache_id (mirrors the renderer)."""
    entry = cache_entries.get(cache_id)
    if entry is None:
        return None
    text_path = entry.get("text_path")
    if not isinstance(text_path, str) or not text_path.strip():
        return None
    resolved = resolve_cache_path(text_path, manifest_path=cache_path, cache_root=cache_root)
    try:
        return resolved.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None


def _cache_text_for_evidence(
    evidence: dict[str, Any],
    cache_entries: dict[str, dict[str, Any]],
    cache_path: Path,
    cache_root: str | None,
) -> tuple[str | None, str | None]:
    """Resolve cached text for an evidence record. Returns (text, error).

    Concatenates the text of every cache_id the record points at (almost always
    one) so a Mechanism display sentence verifies against any of the snapshots
    the evidence is anchored in. Exactly one of (text, error) is non-None.
    """
    cache_ids = _evidence_cache_ids(evidence)
    if not cache_ids:
        return None, "evidence record has no cache_id / cache_ids / excerpt_anchor.cache_id"
    texts: list[str] = []
    missing: list[str] = []
    for cid in cache_ids:
        text = _read_cache_text(cid, cache_entries, cache_path, cache_root)
        if text is None:
            missing.append(cid)
        else:
            texts.append(text)
    if not texts:
        return None, f"cache text could not be read for cache_id(s) {cache_ids}"
    return "\n".join(texts), None


def _bibkey_of(source_value: str) -> str | None:
    m = BIBKEY_TOKEN_RE.match(source_value.strip())
    return m.group(1) if m else None


def _selection_index(
    pre: dict[str, Any] | None,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Index pre_selection selections by ``(family, bibkey)`` for block lookup.

    ``family`` is the family-file stem (e.g. ``01_tool_poisoning``). When two
    selections share a (family, bibkey) the last wins — rare, and the substring
    check is still grounded in a legitimate evidence record for that bibkey.
    """
    index: dict[tuple[str, str], dict[str, Any]] = {}
    if pre is None:
        return index
    for sel in pre.get("selections", []):
        if not isinstance(sel, dict):
            continue
        family = sel.get("family")
        bibkey = sel.get("bibkey")
        if isinstance(family, str) and isinstance(bibkey, str):
            index[(family, bibkey)] = sel
    return index


def _resolve_cached_text_for_block(
    block: str,
    family_stem: str,
    *,
    evidence_by_id: dict[str, dict[str, Any]],
    selection_index: dict[tuple[str, str], dict[str, Any]],
    cache_entries: dict[str, dict[str, Any]],
    cache_path: Path,
    cache_root: str | None,
) -> tuple[str | None, str | None]:
    """Resolve the cached text a block's Mechanism is grounded in.

    Returns ``(cached_text, error)``. Exactly one is non-None: on success the
    cached text string; on failure a human-readable reason the linkage could
    not be resolved (so the caller can flag, never silently pass).
    """
    # Linkage 1: an inline Evidence bullet (most direct).
    ev_match = EVIDENCE_LINE_RE.search(block)
    if ev_match:
        ev_id = ev_match.group(1).strip()
        evidence = evidence_by_id.get(ev_id)
        if evidence is None:
            return None, f"Evidence id {ev_id!r} not found in evidence_ledger"
        cached, err = _cache_text_for_evidence(
            evidence, cache_entries, cache_path, cache_root
        )
        if err is not None:
            return None, f"evidence {ev_id!r}: {err}"
        return cached, None

    # Linkage 2: Source bibkey + family-file → pre_selection → evidence → cache.
    src_match = SOURCE_LINE_RE.search(block)
    if not src_match:
        return None, "block has no Source line to resolve a bibkey"
    bibkey = _bibkey_of(src_match.group(1))
    if not bibkey:
        return None, f"could not extract a bibkey from Source line {src_match.group(1)!r}"
    sel = selection_index.get((family_stem, bibkey))
    if sel is None:
        return None, (
            f"no pre_selection selection for (family={family_stem!r}, "
            f"bibkey={bibkey!r}); cannot link Mechanism to a cached source"
        )
    ev_id = sel.get("evidence_id")
    if not isinstance(ev_id, str):
        return None, f"selection for bibkey {bibkey!r} has no evidence_id"
    evidence = evidence_by_id.get(ev_id)
    if evidence is None:
        return None, f"evidence_id {ev_id!r} (bibkey {bibkey!r}) not in evidence_ledger"
    cached, err = _cache_text_for_evidence(
        evidence, cache_entries, cache_path, cache_root
    )
    if err is not None:
        return None, f"bibkey {bibkey!r} (evidence {ev_id!r}): {err}"
    return cached, None


def _evidence_for_block(
    block: str,
    family_stem: str,
    *,
    evidence_by_id: dict[str, dict[str, Any]],
    selection_index: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    """The evidence record a block's Mechanism is grounded in — inline Evidence
    bullet (preferred), else the Source bibkey via pre_selection. Mirrors the
    linkage in ``_resolve_cached_text_for_block``; returns None if unresolvable
    (the caller still runs the full cache-linkage check via that function)."""
    ev_match = EVIDENCE_LINE_RE.search(block)
    if ev_match:
        return evidence_by_id.get(ev_match.group(1).strip())
    src_match = SOURCE_LINE_RE.search(block)
    if src_match:
        bibkey = _bibkey_of(src_match.group(1))
        if bibkey:
            sel = selection_index.get((family_stem, bibkey))
            if sel and isinstance(sel.get("evidence_id"), str):
                return evidence_by_id.get(sel["evidence_id"])
    return None


def _is_paraphrase_only(evidence: dict[str, Any]) -> bool:
    """True if the evidence declares its support(s) as paraphrase and makes no
    verbatim_match claim. ``extraction_method`` lives per-support under ``supports``;
    a verbatim_match support (even alongside paraphrase) keeps the substring contract."""
    methods = {
        s.get("extraction_method")
        for s in evidence.get("supports", [])
        if isinstance(s, dict)
    }
    return "paraphrase" in methods and "verbatim_match" not in methods


def validate(project_dir: Path) -> list[str]:
    """Verify every agent_index Mechanism bullet is a substring of its cached source.

    ``project_dir`` is a strict-live project directory containing an
    ``agent_index/`` folder plus ``cache_manifest.yml``, ``evidence_ledger.yml``
    and (for the fallback linkage) ``pre_selection_manifest.yml``. Returns one
    error string per Mechanism bullet whose display text is NOT a
    whitespace-normalized substring of its cached source, plus one per bullet
    whose cache linkage cannot be resolved. Empty list = the display-vs-evidence
    contract holds.

    Projects without an ``agent_index/`` folder return ``[]`` (nothing to audit).
    """
    errors: list[str] = []
    index_dir = project_dir / "agent_index"
    if not index_dir.is_dir():
        return errors  # No agent_index to audit.

    cache_path = project_dir / "cache_manifest.yml"
    evidence_path = project_dir / "evidence_ledger.yml"
    pre_path = project_dir / "pre_selection_manifest.yml"

    family_files = sorted(
        p for p in index_dir.glob("*.md") if p.name.lower() != "readme.md"
    )
    if not family_files:
        return errors

    # Detect whether any family file even uses Mechanism bullets before
    # demanding the linkage artifacts (some dossiers are navigational only).
    has_mechanism = any(
        MECHANISM_LINE_RE.search(p.read_text(encoding="utf-8")) for p in family_files
    )
    if not has_mechanism:
        return errors

    # The display-vs-evidence contract only applies to strict-live (v2/v3)
    # dossiers — those that carry a content-addressed cache to ground against.
    # A v1-era / legacy agent_index (no cache_manifest.yml + evidence_ledger.yml)
    # has nothing to audit; skip gracefully (mirrors cross_stage's "skip if the
    # artifact is absent" philosophy) rather than reading a missing file. Only
    # the absence of BOTH means not-strict-live; a project with one but not the
    # other is malformed and still surfaces a clear error below.
    if not cache_path.exists() and not evidence_path.exists():
        return errors
    if not cache_path.exists():
        return ["cache_manifest.yml: not found (required to audit display-vs-evidence)"]
    if not evidence_path.exists():
        return ["evidence_ledger.yml: not found (required to audit display-vs-evidence)"]

    cache, cache_errs = load_yaml_mapping(cache_path)
    if cache_errs:
        return [f"cache_manifest.yml: {e}" for e in cache_errs]
    assert cache is not None
    evidence, ev_errs = load_yaml_mapping(evidence_path)
    if ev_errs:
        return [f"evidence_ledger.yml: {e}" for e in ev_errs]
    assert evidence is not None

    pre: dict[str, Any] | None = None
    if pre_path.exists():
        pre_data, pre_errs = load_yaml_mapping(pre_path)
        if pre_errs:
            return [f"pre_selection_manifest.yml: {e}" for e in pre_errs]
        pre = pre_data

    cache_root = cache.get("cache_root") if isinstance(cache.get("cache_root"), str) else None
    cache_entries = _cache_entries(cache)
    evidence_by_id = _evidence_by_id(evidence)
    selection_index = _selection_index(pre)

    for fpath in family_files:
        text = fpath.read_text(encoding="utf-8")
        for block in (m.group(0) for m in ENTRY_BLOCK_RE.finditer(text)):
            mech_match = MECHANISM_LINE_RE.search(block)
            if not mech_match:
                continue  # Block legitimately omits Mechanism — nothing to check.
            display = mech_match.group(1).strip()
            cached_text, link_err = _resolve_cached_text_for_block(
                block,
                fpath.stem,
                evidence_by_id=evidence_by_id,
                selection_index=selection_index,
                cache_entries=cache_entries,
                cache_path=cache_path,
                cache_root=cache_root,
            )
            short = display[:60] + ("..." if len(display) > 60 else "")
            if link_err is not None:
                errors.append(
                    f"{fpath.name}: Mechanism bullet ('{short}') has no resolvable "
                    f"cache linkage: {link_err}"
                )
                continue
            # Paraphrase exemption: a Mechanism grounded in extraction_method=paraphrase
            # evidence is a declared paraphrase (a synthesis of the source), not a
            # verbatim claim — the substring contract enforces the verbatim guarantee for
            # verbatim_match (or unspecified) evidence only. Cache linkage is still
            # required (checked above).
            ev_rec = _evidence_for_block(
                block, fpath.stem,
                evidence_by_id=evidence_by_id, selection_index=selection_index,
            )
            if ev_rec is not None and _is_paraphrase_only(ev_rec):
                continue
            assert cached_text is not None
            norm_display = _normalize_ws(display)
            norm_cached = _normalize_ws(cached_text)
            if not norm_display:
                errors.append(
                    f"{fpath.name}: Mechanism bullet is empty after normalization"
                )
            elif norm_display not in norm_cached:
                errors.append(
                    f"{fpath.name}: Mechanism display text NOT a substring of cached "
                    f"source (display-vs-evidence violation): '{short}'"
                )

    return errors


def _cli(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <project_dir>", file=sys.stderr)
        return 2
    target = Path(argv[1]).expanduser().resolve()
    if not target.exists():
        print(f"error: path does not exist: {target}", file=sys.stderr)
        return 2
    errors = validate(target)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(f"VALIDATION FAILED: {len(errors)} error(s) in {target}", file=sys.stderr)
        return 1
    print(f"OK: {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
