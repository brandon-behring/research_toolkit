#!/usr/bin/env python3
"""Emit a biblatex ``.bib`` from dossier ``bib_ledger.yml`` files.

The ledger ``authors`` field is a display string ("Surname et al. (Year)"),
unusable as a BibTeX author list, and the ledgers carry no ``doi``/``arxiv_id``/
``year`` field. But for arXiv sources the cached ``/abs/`` blob -- the same bytes
the excerpt anchors point into -- retains the Highwire ``citation_author`` /
``citation_title`` / ``citation_date`` / ``citation_arxiv_id`` meta tags, from
which a real biblatex record is reconstructed. Resolution order per entry:

1. Cache Highwire tags from the capture whose ``source_url == primary_url``.
2. arXiv Atom fallback (``export.arxiv.org``) if an arXiv entry's cache lacks the
   tags -- re-cached through ``cache_source`` (write-back) so it stays anchored;
   ``--no-live`` disables this.
3. Non-arXiv sources (GitHub/HF/blog) keep the ledger display string, and every
   such entry is listed on stderr for later hand-fixing.

Field VALUES escape ``& % # _ $`` only -- braces are BibTeX grouping and must
never be escaped (that destroys brace-protection, the bug in
``research-kb``'s ``bibtex_generator.py``).

Usage:
  emit_bibtex.py <dossier_or_ledger> [more...] [--out FILE] [--seed FILE]
                 [--no-live] [--no-overwrite] [--reconcile BIB [BIB ...]]

Exit codes: 0 ok; 1 data error (output failed self-validation); 2 usage.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from html import unescape
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from validators._common import ARXIV_ID_RE
from validators.bibtex_out import validate_text

_DEFAULT_CACHE_ROOT = Path.home() / "Claude" / "research_cache"
_BIB_ESCAPE = {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "$": r"\$"}
_ARXIV_ATOM_API = "http://export.arxiv.org/api/query?id_list="


def bib_escape(value: str) -> str:
    """Escape BibTeX-special chars in a field VALUE. Braces are NOT escaped."""
    return "".join(_BIB_ESCAPE.get(ch, ch) for ch in value)


def _highwire(text: str, field: str) -> list[str]:
    """All ``content`` values of ``<meta name="citation_<field>">`` (either attr order)."""
    out: list[str] = []
    for pat in (
        rf'<meta[^>]+name=["\']citation_{field}["\'][^>]+content=["\']([^"\']*)["\']',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']citation_{field}["\']',
    ):
        out += [unescape(m.group(1)) for m in re.finditer(pat, text, re.I)]
    return out


def _year(value: object | None) -> str | None:
    """First 4-digit run in ``value`` (handles a str, or a YAML ``datetime.date``)."""
    if not value:
        return None
    m = re.search(r"(\d{4})", str(value))
    return m.group(1) if m else None


def _to_last_first(name: str) -> str:
    """Normalise an author name to ``Family, Given`` for BibTeX.

    Highwire tags are already ``Surname, Forename`` (returned unchanged); arXiv
    Atom gives ``Forename Surname`` -- split on the last space (standard, imperfect
    for multi-word surnames like 'van der Berg')."""
    name = name.strip()
    if "," in name or " " not in name:
        return name
    given, _, family = name.rpartition(" ")
    return f"{family}, {given}"


def _from_blob(text: str) -> tuple[list[str], str | None, str | None, str | None]:
    """Return (authors, title, year, arxiv_id) from a cached blob's Highwire tags."""
    authors = [a.strip() for a in _highwire(text, "author") if a.strip()]
    titles = _highwire(text, "title")
    dates = _highwire(text, "date")
    ids = _highwire(text, "arxiv_id")
    title = " ".join(titles[0].split()) if titles else None
    year = _year(dates[0]) if dates else None
    aid = ids[0].strip() if ids else None
    return authors, title, year, aid


def _arxiv_id(url: str) -> str | None:
    """Bare arXiv id (version stripped) from a URL, else None."""
    m = ARXIV_ID_RE.search(url or "")
    return re.sub(r"v\d+$", "", m.group(1)) if m else None


def _find_abs_blob(
    entry: dict[str, Any], url: str, manifest: dict[str, dict], cache_root: Path
) -> str | None:
    """Text of the capture whose ``source_url == url`` and that bears author tags."""
    ordered = list(entry.get("cache_ids") or [])
    ordered += [cid for cid in manifest if cid not in ordered]
    for cid in ordered:
        m = manifest.get(cid)
        if not m or m.get("source_url") != url:
            continue
        tp = m.get("text_path")
        if not isinstance(tp, str):
            continue
        blob = cache_root / tp
        if blob.exists():
            text = blob.read_text(errors="replace")
            if "citation_author" in text:
                return text
    return None


def _atom(arxiv_id: str) -> dict[str, Any] | None:
    """Query the arXiv Atom API for the first entry's authors/title/year."""
    from urllib.request import urlopen  # local: keep the hot path import-light

    try:
        with urlopen(_ARXIV_ATOM_API + arxiv_id, timeout=20) as resp:  # noqa: S310
            xml = resp.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 -- a live lookup must never abort the emit
        return None
    entry = re.search(r"<entry>(.*?)</entry>", xml, re.S)
    if not entry:
        return None
    body = entry.group(1)
    names = re.findall(r"<author>\s*<name>([^<]+)</name>", body)
    title = re.search(r"<title>(.*?)</title>", body, re.S)
    published = re.search(r"<published>(\d{4})", body)
    return {
        "authors": [_to_last_first(unescape(n.strip())) for n in names],
        "title": " ".join(title.group(1).split()) if title else None,
        "year": published.group(1) if published else None,
    }


def _live_arxiv(arxiv_id: str, cache_root: Path, write_back: bool) -> dict[str, Any] | None:
    """Recover authors for an arXiv id whose cache lacked tags.

    Preferred path re-caches the ``/abs/`` page through ``cache_source`` so the
    Highwire tags become byte-anchored (write-back); the manifest line to add is
    printed for the dossier to adopt deliberately (matching cache_source's own
    "a skill appends them" contract). Falls back to a bare Atom read (flagged)."""
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"
    if write_back:
        try:
            from scripts import cache_source  # lazy: pulls heavy extractors

            entry = cache_source.cache_one(
                abs_url, cache_root=cache_root, fetched_at=date.today().isoformat(),
                topic="emit-bibtex",
            )
            tp = entry.get("text_path")
            if isinstance(tp, str):
                authors, title, year, _ = _from_blob((cache_root / tp).read_text(errors="replace"))
                if authors:
                    print(
                        f"note: re-cached {abs_url} for authors -- add cache_id "
                        f"{entry['cache_id']} to the dossier manifest to anchor it",
                        file=sys.stderr,
                    )
                    return {"authors": authors, "title": title, "year": year}
        except Exception as exc:  # noqa: BLE001
            print(f"warning: live re-cache of {abs_url} failed: {exc}", file=sys.stderr)
    atom = _atom(arxiv_id)
    if atom and atom["authors"]:
        print(
            f"warning: resolved {arxiv_id} authors via live arXiv Atom "
            f"(NOT anchored -- re-run cache-source to anchor)",
            file=sys.stderr,
        )
        return atom
    return None


def resolve_entry(
    entry: dict[str, Any], manifest: dict[str, dict], cache_root: Path,
    *, use_live: bool, write_back: bool,
) -> dict[str, Any]:
    """Resolve one ledger entry to a BibTeX record dict."""
    url = entry.get("primary_url", "") or ""
    arxiv_id = _arxiv_id(url)
    authors: list[str] = []
    title = year = None

    text = _find_abs_blob(entry, url, manifest, cache_root)
    if text is not None:
        authors, title, year, aid = _from_blob(text)
        arxiv_id = aid or arxiv_id
    if not authors and arxiv_id and use_live:
        live = _live_arxiv(arxiv_id, cache_root, write_back)
        if live:
            authors = live["authors"]
            title = title or live["title"]
            year = year or live["year"]

    display = False
    if not authors:
        authors = [entry.get("authors") or entry["bibkey"]]
        display = True
    title = title or entry.get("title") or ""
    year = year or _year(entry.get("published_online")) or _year(entry.get("authors")) or ""
    return {
        "bibkey": entry["bibkey"], "authors": authors, "title": str(title),
        "year": year, "eprint": arxiv_id, "url": url, "display": display,
    }


def format_entry(record: dict[str, Any]) -> str:
    """Render one resolved record as a biblatex ``@misc`` block (seed shape)."""
    lines = [f"@misc{{{record['bibkey']},"]
    lines.append(f"  author       = {{{' and '.join(bib_escape(a) for a in record['authors'])}}},")
    lines.append(f"  title        = {{{bib_escape(record['title'])}}},")
    if record["year"]:
        lines.append(f"  year         = {{{record['year']}}},")
    if record["eprint"]:
        lines.append(f"  eprint       = {{{record['eprint']}}},")
        lines.append("  archiveprefix = {arXiv},")
    if record["url"]:
        lines.append(f"  url          = {{{bib_escape(record['url'])}}},")
    lines.append("}")
    return "\n".join(lines)


def _load_dossier(src: Path) -> tuple[list[dict], dict[str, dict], Path]:
    """From a dossier dir or a ledger file, return (entries, manifest_idx, cache_root)."""
    ledger = src / "bib_ledger.yml" if src.is_dir() else src
    manifest_path = (src if src.is_dir() else src.parent) / "cache_manifest.yml"
    entries: list[dict] = []
    if ledger.exists():
        doc = yaml.safe_load(ledger.read_text()) or {}
        entries = [e for e in (doc.get("entries") or []) if isinstance(e, dict) and e.get("bibkey")]
    manifest: dict[str, dict] = {}
    cache_root = _DEFAULT_CACHE_ROOT
    if manifest_path.exists():
        mdoc = yaml.safe_load(manifest_path.read_text()) or {}
        root = mdoc.get("cache_root")
        if isinstance(root, str):
            cache_root = Path(root).expanduser()
        manifest = {c["cache_id"]: c for c in (mdoc.get("entries") or []) if isinstance(c, dict) and c.get("cache_id")}
    return entries, manifest, cache_root


def emit(
    sources: list[Path], *, use_live: bool, write_back: bool
) -> tuple[dict[str, dict], list[str], dict[str, list[str]]]:
    """Resolve every ledger entry across ``sources``; dedup by bibkey.

    Returns (bibkey -> record, warnings, reverse_collisions[url -> bibkeys])."""
    records: dict[str, dict] = {}
    warnings: list[str] = []
    by_url: dict[str, list[str]] = {}
    for src in sources:
        entries, manifest, cache_root = _load_dossier(src)
        if not entries:
            warnings.append(f"no bib_ledger entries under {src}")
        for entry in entries:
            bibkey = entry["bibkey"]
            by_url.setdefault((entry.get("primary_url") or "").strip(), []).append(bibkey)
            if bibkey in records:
                existing = records[bibkey]
                new = resolve_entry(entry, manifest, cache_root, use_live=use_live, write_back=write_back)
                if new["title"] and existing["title"] and new["title"] != existing["title"]:
                    warnings.append(f"duplicate bibkey {bibkey}: differing titles across dossiers; kept first")
                continue
            record = resolve_entry(entry, manifest, cache_root, use_live=use_live, write_back=write_back)
            records[bibkey] = record
            if record["display"]:
                warnings.append(f"display-string authors (hand-fix): {bibkey} = {entry.get('authors')!r}")
    reverse = {u: sorted(set(ks)) for u, ks in by_url.items() if u and len(set(ks)) > 1}
    return records, warnings, reverse


# --------------------------------------------------------------------------- #
# --reconcile: audit our output against external .bib files, keyed by arXiv id
# --------------------------------------------------------------------------- #
_BIB_ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", re.S)
_EPRINT_RE = re.compile(r"eprint\s*=\s*[{\"]?\s*([0-9]{4}\.[0-9]{4,5})", re.I)
_ARXIV_IN_URL_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})", re.I)
_FIELD_RE = lambda f: re.compile(rf"\b{f}\s*=\s*[{{\"](.+?)[}}\"]\s*,", re.S | re.I)  # noqa: E731


def _index_by_arxiv(text: str, source: str) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for _typ, key, body in _BIB_ENTRY_RE.findall(text):
        aid = None
        m = _EPRINT_RE.search(body) or _ARXIV_IN_URL_RE.search(body)
        if m:
            aid = m.group(1)
        if not aid:
            continue
        title = _FIELD_RE("title").search(body)
        idx[aid] = {"source": source, "key": key, "title": " ".join(title.group(1).split()) if title else ""}
    return idx


def reconcile(records: dict[str, dict], external: list[Path]) -> list[str]:
    """Report where the same arXiv id appears under differing keys/titles."""
    index: dict[str, list[dict]] = {}
    for aid, rec in {(r["eprint"] or ""): r for r in records.values() if r["eprint"]}.items():
        index.setdefault(aid, []).append({"source": "emit-bibtex", "key": rec["bibkey"], "title": rec["title"]})
    for path in external:
        if not path.exists():
            continue
        for aid, rec in _index_by_arxiv(path.read_text(errors="replace"), path.name).items():
            index.setdefault(aid, []).append(rec)
    report: list[str] = []
    for aid, hits in sorted(index.items()):
        if len(hits) < 2:
            continue
        keys = {h["key"] for h in hits}
        if len(keys) > 1:
            report.append(f"arXiv {aid}: differing keys {sorted(keys)} across {[h['source'] for h in hits]}")
    return report


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="emit-bibtex", description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("sources", nargs="+", help="dossier dir(s) or bib_ledger.yml path(s)")
    parser.add_argument("--out", help="write the .bib here (default: stdout)")
    parser.add_argument("--seed", help="prepend a hand-verified seed .bib (e.g. fields2023vlt)")
    parser.add_argument("--no-live", action="store_true", help="disable the live arXiv fallback")
    parser.add_argument("--no-overwrite", action="store_true", help="refuse to overwrite an existing --out")
    parser.add_argument("--reconcile", nargs="+", metavar="BIB", help="audit output against external .bib files")
    args = parser.parse_args(argv)

    sources = [Path(s).expanduser().resolve() for s in args.sources]
    for src in sources:
        if not src.exists():
            print(f"error: source does not exist: {src}", file=sys.stderr)
            return 2

    records, warnings, reverse = emit(sources, use_live=not args.no_live, write_back=not args.no_live)

    seed_keys: set[str] = set()
    seed_text = ""
    if args.seed:
        seed_path = Path(args.seed).expanduser().resolve()
        if not seed_path.exists():
            print(f"error: seed does not exist: {seed_path}", file=sys.stderr)
            return 2
        seed_text = seed_path.read_text(encoding="utf-8").rstrip()
        seed_keys = {k for _t, k, _b in _BIB_ENTRY_RE.findall(seed_text)}

    blocks = [format_entry(records[k]) for k in sorted(records) if k not in seed_keys]
    body = "\n\n".join(blocks) + "\n"
    text = (seed_text + "\n\n" + body) if seed_text else body

    errors = validate_text(text)
    if errors:
        for err in errors:
            print(f"error: emitted .bib failed validation: {err}", file=sys.stderr)
        return 1

    for warn in warnings:
        print(f"warning: {warn}", file=sys.stderr)
    for url, keys in sorted(reverse.items()):
        print(f"note: one URL, multiple bibkeys (both emitted): {keys} -> {url}", file=sys.stderr)
    if args.reconcile:
        for line in reconcile(records, [Path(p).expanduser().resolve() for p in args.reconcile]):
            print(f"reconcile: {line}", file=sys.stderr)

    emitted = [k for k in records if k not in seed_keys]
    n_display = sum(1 for k in emitted if records[k]["display"])
    print(
        f"emit-bibtex: {len(emitted) + len(seed_keys)} entries "
        f"({len(emitted) - n_display} cache/live-resolved, {n_display} display-string"
        f"{', ' + str(len(seed_keys)) + ' seed' if seed_keys else ''})",
        file=sys.stderr,
    )

    if args.out:
        out = Path(args.out).expanduser().resolve()
        if out.exists() and args.no_overwrite:
            print(f"error: refusing to overwrite (--no-overwrite): {out}", file=sys.stderr)
            return 2
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"emit-bibtex: wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
