#!/usr/bin/env python3
"""Produce a v3 excerpt_anchor (text_path_offset + sha256_of_span) for a verbatim excerpt.

The missing companion to ``scripts/verify_citations.py`` /
``validators.v2_common.verify_excerpt_anchor``: that code only *checks* excerpt
anchors, leaving the offsets+hash to be hand-computed. Given a cached source and a
verbatim excerpt copied from its cached text, this emits the byte ``text_path_offset``
and ``sha256_of_span`` that an ``evidence_ledger.yml`` ``supports[].excerpt_anchor``
requires.

Correctness guarantees:
- The cached text is resolved with the SAME ``resolve_cache_path()`` the verifier
  uses (honoring the manifest's ``cache_root``), so the producer and verifier never
  disagree about which file to read.
- The emitted anchor is self-verified by ``verify_excerpt_anchor()`` (the exact check
  the citation audit runs) before it is printed. A zero exit therefore guarantees the
  anchor passes ``verify_citations.py``.
- Matching is whitespace-tolerant — the excerpt is matched as a token sequence
  separated by arbitrary whitespace, mirroring the verifier's whitespace-normalized
  excerpt-equality — with an exact-byte fast path. Byte offsets are computed against
  the raw cached bytes (not the decoded string), so multi-byte characters before the
  span do not skew them.

Usage:
  # manifest mode — resolves text_path via cache_root, emits cache_id:
  build_excerpt_anchor.py <cache_manifest.yml> --cache-id <id> [--excerpt STR | --excerpt-file F]
  # direct text-file mode:
  build_excerpt_anchor.py --text-path <file> [--excerpt STR | --excerpt-file F]
  # (excerpt defaults to stdin if neither --excerpt nor --excerpt-file is given)

Exit codes: 0 ok; 1 excerpt not found / ambiguous / non-UTF-8 text / manifest data
error / self-verify failed; 2 usage / file-not-found.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators.v2_common import (
    load_yaml_mapping,
    resolve_cache_path,
    verify_excerpt_anchor,
)


def _select(matches: list[tuple[int, int]], occurrence: int | None) -> tuple[int, int]:
    """Pick one (start, end) span from candidate matches, honoring ``occurrence`` (1-based)."""
    if not matches:
        raise ValueError("excerpt not found in cached text (copy it verbatim from the cached text)")
    if len(matches) == 1:
        return matches[0]
    if occurrence is None:
        raise ValueError(
            f"excerpt matches {len(matches)} spans; lengthen it to be unique, "
            f"or pass --occurrence 1..{len(matches)}"
        )
    if not 1 <= occurrence <= len(matches):
        raise ValueError(f"occurrence {occurrence} out of range 1..{len(matches)}")
    return matches[occurrence - 1]


def find_span(text_bytes: bytes, excerpt: str, occurrence: int | None = None) -> tuple[int, int]:
    """Return the [start, end) BYTE offsets of ``excerpt`` within ``text_bytes``.

    Collects exact byte matches first; otherwise matches the excerpt as a sequence of
    tokens separated by arbitrary whitespace (``\\s+``), mirroring the verifier's
    whitespace-normalized equality. Offsets are byte offsets into the raw ``text_bytes``
    (multi-byte characters before the span are counted correctly). When the excerpt
    occurs more than once, ``occurrence`` (1-based) selects which span; without it,
    ambiguity raises. Raises ValueError if the excerpt is absent, ambiguous-without-
    occurrence, or the text is not UTF-8 (only when the whitespace path is needed).
    """
    needle = excerpt.encode("utf-8")
    exact: list[tuple[int, int]] = []
    i = text_bytes.find(needle)
    while i != -1:
        exact.append((i, i + len(needle)))
        i = text_bytes.find(needle, i + 1)
    if exact:
        return _select(exact, occurrence)

    try:
        text = text_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"excerpt not found by exact match and cached text is not clean UTF-8 ({exc}); "
            "copy the excerpt verbatim from the cached text"
        ) from exc

    tokens = excerpt.split()
    if not tokens:
        raise ValueError("excerpt is empty")
    pattern = r"\s+".join(re.escape(tok) for tok in tokens)
    spans = [
        (len(text[: m.start()].encode("utf-8")), len(text[: m.end()].encode("utf-8")))
        for m in re.finditer(pattern, text)
    ]
    return _select(spans, occurrence)


def build_anchor(text_bytes: bytes, excerpt: str, occurrence: int | None = None) -> dict[str, Any]:
    """Compute the {text_path_offset, sha256_of_span} anchor for a verbatim excerpt."""
    start, end = find_span(text_bytes, excerpt, occurrence)
    span_sha = hashlib.sha256(text_bytes[start:end]).hexdigest()
    return {"text_path_offset": [start, end], "sha256_of_span": span_sha}


def _read_excerpt(args: argparse.Namespace) -> str | None:
    if args.excerpt is not None:
        return args.excerpt.strip()
    if args.excerpt_file:
        try:
            return Path(args.excerpt_file).expanduser().read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            print(f"error: excerpt-file not found: {args.excerpt_file}", file=sys.stderr)
            return None
    return sys.stdin.read().strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="build_excerpt_anchor",
        description=__doc__.splitlines()[0] if __doc__ else None,
    )
    parser.add_argument("manifest", nargs="?", help="cache_manifest.yml (manifest mode)")
    parser.add_argument("--cache-id", help="cache_id within the manifest (manifest mode)")
    parser.add_argument(
        "--text-path", help="cached text file directly (alternative to manifest + --cache-id)"
    )
    parser.add_argument("--excerpt", help="verbatim excerpt (else --excerpt-file, else stdin)")
    parser.add_argument("--excerpt-file", help="file holding the verbatim excerpt")
    parser.add_argument(
        "--occurrence",
        type=int,
        help="1-based index to disambiguate when the excerpt appears multiple times "
        "(common for HTML abstract pages that duplicate the abstract)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of paste-ready YAML")
    args = parser.parse_args(argv)

    excerpt = _read_excerpt(args)
    if excerpt is None:
        return 2
    if not excerpt:
        print("error: empty excerpt", file=sys.stderr)
        return 2

    # Resolve the cached text + the context needed to self-verify against the manifest.
    if args.text_path:
        text_file = Path(args.text_path).expanduser().resolve()
        cache_id = args.cache_id or "_local"
        cache_entries_by_id: dict[str, Any] = {cache_id: {"text_path": str(text_file)}}
        manifest_path = text_file.parent
        cache_root: str | None = None
        emit_cache_id = args.cache_id
    else:
        if not args.manifest or not args.cache_id:
            print(
                "error: provide <cache_manifest.yml> --cache-id <id>, or --text-path <file>",
                file=sys.stderr,
            )
            return 2
        manifest_path = Path(args.manifest).expanduser().resolve()
        mdata, merrs = load_yaml_mapping(manifest_path)
        if mdata is None:
            print(f"error: cannot read manifest: {'; '.join(merrs) or manifest_path}", file=sys.stderr)
            return 2
        cache_root = mdata.get("cache_root") if isinstance(mdata.get("cache_root"), str) else None
        cache_entries_by_id = {
            e["cache_id"]: e
            for e in (mdata.get("entries") or [])
            if isinstance(e, dict) and isinstance(e.get("cache_id"), str)
        }
        cache_id = args.cache_id
        entry = cache_entries_by_id.get(cache_id)
        if entry is None:
            print(f"error: cache_id not found in manifest: {cache_id!r}", file=sys.stderr)
            return 1
        text_path_value = entry.get("text_path")
        if not isinstance(text_path_value, str):
            print(f"error: manifest entry {cache_id!r} has no text_path", file=sys.stderr)
            return 1
        text_file = resolve_cache_path(text_path_value, manifest_path=manifest_path, cache_root=cache_root)
        emit_cache_id = cache_id

    try:
        text_bytes = text_file.read_bytes()
    except FileNotFoundError:
        print(f"error: text file not found: {text_file}", file=sys.stderr)
        return 2

    try:
        anchor = build_anchor(text_bytes, excerpt, args.occurrence)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Self-verify with the exact function the citation audit runs.
    verify_errs = verify_excerpt_anchor(
        excerpt=excerpt,
        cache_id=cache_id,
        text_path_offset=anchor["text_path_offset"],
        sha256_of_span=anchor["sha256_of_span"],
        cache_entries_by_id=cache_entries_by_id,
        manifest_path=manifest_path,
        loc="build_excerpt_anchor",
        cache_root=cache_root,
    )
    if verify_errs:
        for e in verify_errs:
            print(f"error: self-verify failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        out: dict[str, Any] = {}
        if emit_cache_id:
            out["cache_id"] = emit_cache_id
        out.update(anchor)
        print(json.dumps(out))
    else:
        start, end = anchor["text_path_offset"]
        print("excerpt_anchor:")
        if emit_cache_id:
            print(f"  cache_id: {emit_cache_id}")
        print(f"  text_path_offset: [{start}, {end}]")
        print(f"  sha256_of_span: {anchor['sha256_of_span']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
