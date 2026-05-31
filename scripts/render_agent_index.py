#!/usr/bin/env python3
"""Render a sources.json + render_config.yml into pre_selection_manifest.yml + agent_index/.

Committed, parameterized successor to the per-topic ``~/Claude/_render_topicN.py``
scratch renderers. Those were one stable ENGINE copied per topic with the per-topic
DATA hardcoded as Python literals (RESULT, FAMILIES, GLOSSARY, LOOKUP, scope text,
MECH_DISPLAY). Here the engine lives once and ALL per-topic content comes from a
sidecar ``render_config.yml`` (see templates/render_config.schema.yml), so a new topic
needs a config (data), not ~200 lines of bespoke Python.

Engine vs data split:
  ENGINE (this file): read sources.json, anchor each evidence excerpt against the
    content-addressed cache (first exact byte occurrence, [start, end], sha256 of the
    span) via build_anchor(), write the Attribute-First pre_selection_manifest.yml
    (schema_version 3 — span selections committed BEFORE prose), and render agent_index/
    (00_overview.md glossary, one file per claim_family of 5-bullet
    Source/Code/Mechanism/Result/Status blocks [+Published online], README.md with
    purpose/scope/coverage/lookup-recipes).
  DATA (render_config.yml): topic, today, cache_root, title, blurb, families, results,
    glossary, lookup_recipes, scope text, mechanism_display overrides.

Display-verify guard (verify_display): when a Mechanism bullet shows a DISPLAY sentence
(mechanism_display[bibkey]) that differs from the anchored evidence excerpt, the display
text MUST be a verbatim raw-byte substring of that source's cached text; the renderer
aborts (non-zero exit) otherwise. display != evidence — the ledger excerpt/anchor in
pre_selection_manifest.yml is unchanged. This is the same trust guard the Phase 2
validator also enforces.

Exit codes: 0 ok; 1 data error (missing config key, missing RESULT, anchor/display
failure); 2 usage (file not found, bad CLI).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_excerpt_anchor import build_anchor

ABSTRACT_MARKUP = '<span class="descriptor">Abstract:</span>'


class RenderError(Exception):
    """Raised on a data error (missing field, anchor miss, failed display guard)."""


def _blob_path(cache_root: Path, sha: str) -> Path:
    return cache_root / "text" / "sha256" / f"{sha}.txt"


def _clean(excerpt: str) -> str:
    """Strip the arXiv abstract markup prefix (matches the scratch engine's clean())."""
    return excerpt.replace(ABSTRACT_MARKUP, "").strip()


def verify_display(cache_root: Path, sha: str, sentence: str, bibkey: str) -> str:
    """Assert a DISPLAY Mechanism sentence is a verbatim raw-byte substring of the snapshot.

    Returns the sentence on success; raises RenderError (-> non-zero exit) otherwise.
    This is the trust guard preventing display prose from drifting from the cached bytes.
    """
    if _blob_path(cache_root, sha).read_bytes().find(sentence.encode("utf-8")) < 0:
        raise RenderError(
            f"DISPLAY ERROR: mechanism_display for {bibkey} is not a verbatim "
            f"raw-byte substring of {sha}.txt: {sentence[:60]!r}"
        )
    return sentence


def build_manifest(sources: list[dict[str, Any]], topic: str, today: str, cache_root: Path) -> dict[str, Any]:
    """Anchor every source's excerpt and build the schema-3 pre_selection_manifest dict.

    Reuses build_anchor() from scripts/build_excerpt_anchor.py (occurrence=1 == first
    exact byte match) so the offsets+span hash match the committed anchor producer.
    """
    selections: list[dict[str, Any]] = []
    for i, src in enumerate(sources, 1):
        sha = src["sha"]
        excerpt = src["excerpt"]
        text_bytes = _blob_path(cache_root, sha).read_bytes()
        try:
            anchor = build_anchor(text_bytes, excerpt, occurrence=1)
        except ValueError as exc:
            raise RenderError(f"ANCHOR ERROR for {src['bibkey']} ({sha}.txt): {exc}") from exc
        selections.append(
            {
                "selection_id": f"sel_{src['bibkey']}",
                "bullet_id": f"B{i}",
                "atom_id": f"claim_{topic}_{src['n']}",
                "cache_id": "cache_" + sha[:16],
                "span": {
                    "text_path_offset": anchor["text_path_offset"],
                    "sha256_of_span": anchor["sha256_of_span"],
                    "excerpt": excerpt,
                },
            }
        )
    return {
        "schema_version": 3,
        "topic": topic,
        "generated_at": today,
        "current_as_of": today,
        "freshness_policy": "strict_live",
        "selections": selections,
    }


def _entry_md(src: dict[str, Any], config: dict[str, Any], cache_root: Path) -> str:
    """Render one source as a 5-bullet block (+ Published online when present)."""
    results = config["results"]
    mech_display = config.get("mechanism_display") or {}
    bibkey = src["bibkey"]
    if bibkey not in results:
        raise RenderError(f"MISSING RESULT for {bibkey}")
    code = src.get("code_url", "—")
    status = "Verified." + ("" if src.get("code_url") else " (no widely-known repo)")
    if bibkey in mech_display:
        mech = verify_display(cache_root, src["sha"], mech_display[bibkey], bibkey)
    else:
        mech = _clean(src["excerpt"])
    pub = src.get("published_online")
    pub_line = f"  - **Published online:** {pub}\n" if pub else ""
    return (
        f"- **{src['title']}** — {src['authors']} ({src['venue']}).\n"
        f"  - **Source:** {src['primary_url']}\n"
        f"  - **Code:** {code}\n"
        f"  - **Mechanism:** {mech}\n"
        f"  - **Result:** {results[bibkey]}\n"
        f"  - **Status:** {status}\n"
        f"{pub_line}"
        f"  - **Evidence:** ev_{config['topic']}_{src['n']}\n"
    )


def _family_md(heading: str, family_blurb: str, rows: list[dict[str, Any]], config: dict[str, Any], cache_root: Path) -> str:
    """Render one family file: heading, a descriptive blurb line, then the 5-bullet blocks."""
    body = f"# {heading}\n\n_{family_blurb} {len(rows)} entries._\n\n"
    body += "\n".join(_entry_md(s, config, cache_root) for s in rows)
    return body


def _overview_md(config: dict[str, Any]) -> str:
    """Render 00_overview.md: heading + blurb + glossary.

    The H1 uses ``overview_heading`` if set, else ``title``; the blurb is emitted
    verbatim (carry any markdown emphasis you want in the config value).
    """
    heading = config.get("overview_heading") or config["title"]
    out = [
        f"<!-- AGENT-INDEX: overview {config['topic']} -->",
        "",
        f"# Overview — {heading}",
        "",
        config["blurb"],
        "",
        "## Glossary",
        "",
    ]
    glossary = config.get("glossary") or []
    out.append("\n".join(f"- **{g['term']}** — {g['definition']}" for g in glossary))
    return "\n".join(out) + "\n"


def _readme_md(config: dict[str, Any], by_family: dict[str, list[dict[str, Any]]], n_sources: int) -> str:
    families = config["families"]
    rd = [
        f"<!-- AGENT-INDEX: {config['topic']} | {n_sources} sources | strict-live v2.2+ -->",
        "",
        f"# {config['title']} — Agent Index",
        "",
        f"**Purpose:** {config['blurb']}",
        f"**Coverage:** {n_sources} primary sources across {len(families)} claim families.",
        "",
        "## Scope boundary",
        "",
    ]
    scope = config.get("readme_scope")
    if scope:
        rd.append(scope)
        rd.append("")
    rd.append(f"- **In:** {config.get('scope_in', 'n/a')}")
    rd.append(f"- **Out:** {config.get('scope_out', 'n/a')}")
    rd.append("")
    rd.append("## How this is organized")
    rd.append("")
    rd.append("| File | Contents |")
    rd.append("|---|---|")
    rd.append("| `00_overview.md` | Overview + glossary |")
    for fam in families:
        rd.append(f"| `{fam['file']}` | {fam['heading']} |")
    rd.append("")
    rd.append("## Coverage")
    rd.append("")
    for fam in families:
        cnt = len(by_family.get(fam["claim_family"], []))
        rd.append(f"- {fam['heading']} (`{fam['file']}`): {cnt} sources")
    rd.append("")
    rd.append("## Lookup recipes")
    rd.append("")
    for recipe in config.get("lookup_recipes") or []:
        rd.append(f"- **{recipe['question']}** → `{recipe['file']}` § {recipe['ref']}")
    return "\n".join(rd) + "\n"


def render(sources_doc: dict[str, Any], project_dir: Path, config: dict[str, Any], cache_root: Path, topic: str, today: str) -> dict[str, Any]:
    """Write pre_selection_manifest.yml + agent_index/ for one topic; return the manifest dict."""
    sources = sources_doc["sources"]
    known_families = {fam["claim_family"] for fam in config["families"]}
    for src in sources:
        if src["claim_family"] not in known_families:
            raise RenderError(f"UNKNOWN FAMILY for {src['bibkey']}: {src['claim_family']}")
        if src["bibkey"] not in config["results"]:
            raise RenderError(f"MISSING RESULT for {src['bibkey']}")

    index_dir = project_dir / "agent_index"
    index_dir.mkdir(parents=True, exist_ok=True)

    # Attribute-First: commit span selections BEFORE any prose.
    manifest = build_manifest(sources, topic, today, cache_root)
    (project_dir / "pre_selection_manifest.yml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=4096),
        encoding="utf-8",
    )

    by_family: dict[str, list[dict[str, Any]]] = {}
    for src in sources:
        by_family.setdefault(src["claim_family"], []).append(src)

    family_blurb = config.get("family_blurb") or f"Topic: {topic}."
    for fam in config["families"]:
        rows = by_family.get(fam["claim_family"])
        if not rows:
            continue  # no empty family files
        (index_dir / fam["file"]).write_text(
            _family_md(fam["heading"], family_blurb, rows, config, cache_root), encoding="utf-8"
        )

    (index_dir / "00_overview.md").write_text(_overview_md(config), encoding="utf-8")
    (index_dir / "README.md").write_text(_readme_md(config, by_family, len(sources)), encoding="utf-8")
    return manifest


def load_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RenderError(f"config must be a mapping, got {type(data).__name__}")
    for key in ("topic", "title", "blurb", "families", "results"):
        if key not in data:
            raise RenderError(f"missing required config key: {key}")
    return data


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="render_agent_index",
        description="Render sources.json + render_config.yml into pre_selection_manifest.yml + agent_index/.",
    )
    parser.add_argument("sources", help="sources.json (gather manifest: {topic, today, cache_root, sources:[...]})")
    parser.add_argument("project_dir", help="project directory to write into")
    parser.add_argument("--config", default=None, help="render_config.yml (default: <project_dir>/render_config.yml)")
    parser.add_argument("--cache-root", default=None, help="override cache_root (CLI > config > sources.json)")
    parser.add_argument("--today", default=None, help="override today (CLI > config > sources.json)")
    args = parser.parse_args(argv)

    sources_path = Path(args.sources).expanduser()
    if not sources_path.exists():
        print(f"error: sources not found: {sources_path}", file=sys.stderr)
        return 2
    project_dir = Path(args.project_dir).expanduser()
    config_path = Path(args.config).expanduser() if args.config else project_dir / "render_config.yml"
    if not config_path.exists():
        print(f"error: render config not found: {config_path}", file=sys.stderr)
        return 2

    try:
        sources_doc = json.loads(sources_path.read_text(encoding="utf-8"))
        config = load_config(config_path)
    except RenderError as exc:
        print(f"error: {config_path}: {exc}", file=sys.stderr)
        return 1
    except (ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    topic = config.get("topic") or sources_doc.get("topic")
    if not topic:
        print("error: topic not set in config or sources.json", file=sys.stderr)
        return 1
    today = args.today or config.get("today") or sources_doc.get("today")
    if not today:
        print("error: today not set via --today, config, or sources.json", file=sys.stderr)
        return 1
    cache_root_value = args.cache_root or config.get("cache_root") or sources_doc.get("cache_root")
    if not cache_root_value:
        print("error: cache_root not set via --cache-root, config, or sources.json", file=sys.stderr)
        return 1
    cache_root = Path(cache_root_value).expanduser()

    try:
        render(sources_doc, project_dir, config, cache_root, topic, today)
    except RenderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"error: cached text not found: {exc}", file=sys.stderr)
        return 1

    n = len(sources_doc["sources"])
    print(
        f"wrote pre_selection_manifest ({n} selections) + agent_index/ "
        f"({len(config['families'])} families + README + 00_overview)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
