# Citation rules

URL rendering and citation conventions used across `/research-gather`, `/dossier-build`, and `/agent-index`. The validators don't enforce most of this (they only check URL well-formedness), but consistent application makes the dossier and agent-index hand-readable.

## URL canonical forms

| Source type | Canonical URL form | Example |
|---|---|---|
| arXiv preprint | `https://arxiv.org/abs/<id>` | `https://arxiv.org/abs/2211.09527` |
| arXiv (NOT PDF) | Never use `/pdf/<id>` — abs page is the canonical citation handle | — |
| Journal DOI | `https://doi.org/<doi>` | `https://doi.org/10.1145/3461702.3462624` |
| GitHub repo | `https://github.com/<org>/<repo>` | `https://github.com/numenta/NAB` |
| Hugging Face dataset | `https://huggingface.co/datasets/<user>/<name>` | `https://huggingface.co/datasets/walledai/AdvBench` |
| Hugging Face model | `https://huggingface.co/<user>/<name>` | `https://huggingface.co/meta-llama/Llama-Guard-3-8B` |
| Vendor blog | Full URL of the specific post (not the blog index) | `https://www.lakera.ai/blog/the-year-of-the-agent-prompt-injection-in-the-real-world` |
| Conference proceedings | DOI if available, else the proceedings page URL | — |

## YAML quoting in ledger values

Any YAML string value containing `:`, `#`, `[`, `{`, `}`, `&`, `*`, `?`, `|`, `>`, `!`, `%`, `@`, `` ` ``, or starting with `-` MUST be double-quoted. Otherwise the value parses as a nested mapping, list, alias, or tag — and silently breaks frontmatter-driven tools.

Applies especially to fields where colons are common:
- `title:` when the title contains a subtitle separator — `title: "Even Claude agrees: hole in its sandbox was real and dangerous"`
- `venue:` when the venue includes a track separator — `venue: "ACL 2024: Findings"`
- `authors:` when authors include compound surnames or list separators — quote when in doubt
- Any `source_title:` or `note:` field if your source's headline contains a colon (common in security advisories, postmortems, academic papers).

**Rule of thumb: when in doubt, quote.** PyYAML and the validators accept either form for plain strings; readers and downstream tools may silently misparse the unquoted form. The cost of an extra quote is zero; the cost of a misparsed entry is invisible until something downstream breaks.

## Bibkey convention

`{firstauthor_lowercase}{year}{slug}` where:
- `firstauthor_lowercase`: surname only, lowercase, no spaces (e.g. `perez`, `vandermerwe`)
- `year`: 4-digit year of publication (or arXiv submission if unpublished)
- `slug`: 1–3 lowercase words distilling the title (e.g. `ignore`, `selfreminder`, `gcg`)

Examples:
- `perez2022ignore` — Perez & Ribeiro 2022 "Ignore Previous Prompt"
- `zou2023universal` — Zou et al. 2023 GCG ("Universal and Transferable…")
- `kim2024selfreminder` — Kim et al. 2024 "Self-Reminder"

The bibkey is unique across the entire `bib_ledger.yml`. Two entries colliding on bibkey is a validator error. Use slug variations (`zou2023gcg` vs `zou2023universal`) to distinguish.

## "No LLM-generated specifics" rule

This is the most important content rule for `/agent-index` and `/dossier-audit`.

**Rule:** Any quantitative claim asserted in the dossier or synthesis MUST appear in:
1. The primary source's abstract (preferred), OR
2. A verified body excerpt that you can quote, OR
3. A vendor / regulatory press release that you've actually read.

**Forbidden:** asserting a specific number (e.g. "95% ASR", "1,200 entries", "3.4× speedup") because it sounds plausible or because you saw it referenced indirectly.

**When unsure:** generalize. "High ASR" instead of "95% ASR". "Hundreds of entries" instead of "1,200 entries". "Substantial speedup" instead of "3.4× speedup". Mark `(unverified body claim)` if the number was in the body but you didn't fetch the body.

## Author rendering

For dossier table cells:
- 1 author: `Surname (year)`
- 2 authors: `First & Second (year)`
- 3 authors: `First, Second, Third (year)`
- 4+ authors: `First et al. (year)`

For 5-bullet entries (display name line):
- 1 author: `Surname (Venue Year)`
- 2 authors: `First & Second (Venue Year)`
- 3+ authors: `First et al. (Venue Year)`

## Status flags

- `Verified` — title, authors, year all cross-checked against primary source.
- `Unverified` — bibkey resolves locally but no primary-source check yet.
- `(vendor blog)` — sourced from a vendor blog or press release; treat numbers with skepticism.
- `(recheck after YYYY-MM-DD)` — time-sensitive claim should be refreshed after the listed strict-live date.
- `(unverified body claim)` — quantitative claim is from paper body, not abstract; reader should re-verify.

## Source-tier worked examples (host pattern → tier)

Tier assignment is the single most common source of agent drift during `/research-gather`. Use this table for quick pattern-match before writing a `bib_ledger` entry:

| Host pattern | Tier | Notes |
|---|---|---|
| `anthropic.com/docs/*`, `anthropic.com/engineering/*`, `anthropic.com/news/*` | **T1-official** | Anthropic-authored docs / blog / news |
| `claude.com/blog/*`, `claude.com/docs/*`, `claude.com/resources/*` | **T1-official** | Anthropic-authored (Claude.com is the consumer Anthropic property) |
| `platform.claude.com/docs/*`, `code.claude.com/docs/*`, `docs.claude.com/*` | **T1-official** | Anthropic-authored API + Claude Code docs |
| `modelcontextprotocol.io/*`, `blog.modelcontextprotocol.io/*` | **T1-official** | Spec-authoritative (MCP donated to Agentic AI Foundation but spec authorship traces to Anthropic) |
| `arxiv.org/abs/*` | **T1-official** | Primary academic source (the abstract page, not `/pdf/`) |
| Major vendor docs (`aws.amazon.com/bedrock/*`, `cloud.google.com/vertex-ai/*`, etc.) | **T1-official** | Vendor-authored docs |
| `anthropic.skilljar.com/*` | **T2-release-notes** | Anthropic-managed Academy course pages — Anthropic-managed but not spec/docs |
| `github.com/<anthropic-org>/<repo>` releases + README | **T2-release-notes** | Anthropic-owned repo metadata |
| `github.com/<other-org>/<repo>` releases + README | **T2-release-notes** if a primary tool of the topic; else **T3** | E.g., MCP servers in `modelcontextprotocol/servers` are T2 |
| Vendor blogs for non-Anthropic vendors (vendor-authoritative on vendor topics) | **T2-release-notes** | E.g., AWS announcing a Bedrock feature = T2-AWS-authoritative |
| Substack, dev.to, Medium, third-party tech blogs | **T3-practitioner** | Even if citing primary sources accurately |
| Press / news (TechCrunch, The Register, Reuters, etc.) | **T3-practitioner** | Even when reporting Anthropic announcements — find Anthropic's primary source instead |
| Aggregator sites (cert-prep sites, awesome lists) | **T3-practitioner** | Useful for discovery; never the primary citation |

**Strict rule**: third-party citing T1 ≠ T1. If three Substack posts each quote the same Anthropic announcement, the tier of the Substack posts is still T3; the announcement at `anthropic.com/news/...` is T1.

**Boundary cases**:
- Conference papers presented at workshops (no proceedings DOI): treat as **T1-official** if the paper exists on arXiv; otherwise the workshop's official site is T1.
- Pre-prints later published: keep the arXiv URL as the bibkey's primary URL; the published version's DOI goes into a `published_url:` field if useful.
- Anthropic employees writing on their personal Substack about Anthropic features: **T2-release-notes** (semi-official; the byline is Anthropic but the venue isn't).

## v2 evidence IDs (strict-live projects only)

Strict-live v2 projects pair every substantive claim with one or more
evidence IDs that resolve to entries in `evidence_ledger.yml`. Two equivalent
inline forms (see `references/dual_audience_design.md` § Evidence-ID rendering
for the full spec):

- **Sixth bullet** of a 5-bullet entry block:
  `- **Evidence:** ev_<topic>_0001` (one bullet per claim, lists all
  supporting evidence IDs space-separated or comma-separated within the bullet)
- **Inline suffix** on the claim text:
  `... 17% jailbreak rate [ev_jailbreak_rate]` (square brackets are
  load-bearing — agent grep relies on `\[ev_[a-z0-9_]+\]`)

Evidence-ID format: `ev_<topic_slug>_NNNN` (zero-padded number; topic_slug
matches the project's top-level `topic:` field). IDs are stable references,
not URLs — they only resolve via lookup in `evidence_ledger.yml`.

When citing multiple evidence IDs inline, list all inside one bracket pair:
`[ev_jailbreak_rate, ev_jailbreak_corroboration]`.

For v1.x projects (no evidence_ledger.yml), skip the evidence bullet / inline
suffix entirely — the Status flag (`Verified`, `Unverified`, etc.) carries the
trust signal.

### v2.2 atomic claim IDs (`/agent-index` Attribute-First output)

For v2.2+ projects, individual claim_ids inside `evidence_ledger.yml`
follow the atomic-decomposition pattern:

```
claim_<topic_slug>_b<bullet>_a<atom>_<descriptor>
```

Each 5-bullet block emits 2–5 such claim_ids — one per atomic fact —
instead of one bullet-level claim_id. Atom_ids appear in inline suffixes
exactly like evidence_ids do; the bracket-grep convention extends:

```markdown
- **Result:** 91.2% accuracy [claim_atomic_demo_b1_a1_accuracy], 42ms latency [claim_atomic_demo_b1_a2_latency]
```

The Attribute-First contract (Phase 2 of `/agent-index`) requires that
every cited claim_id has a matching atom selection in
`pre_selection_manifest.yml`. Validators reject bullets that cite
spans outside the pre-selection commitment.

### JS-rendered / fragmented sources (no contiguous span)

Slate/JS-rendered blogs and SPA dashboards (e.g. Manus) fragment prose across
many `<span>` nodes, so the **cached text often has no sentence-length
contiguous span** — only a sub-sentence string substring-matches the cache.
When anchoring an excerpt for such a source:

- **Reuse the gather-time anchor** — the exact span that was actually found in
  the cached render at gather time — rather than re-selecting a longer, nicer
  quote at agent-index time that will *not* substring-match. The byte-exact
  substring guarantee is non-negotiable; a shorter true span beats a longer
  span that fails the anchor check.
- If even a short span won't match, the source is a candidate for the
  `escalate_to_manual` path (the render is too fragmented to anchor cleanly)
  rather than forcing a span that breaks citation-audit.

This is a known render class, not a bug — the same anchor producer
(`build_excerpt_anchor.build_anchor`, `occurrence=1`) is used everywhere, so an
anchor that verified at gather time verifies at index time on the same cached
bytes. (Surfaced as `ctxasm-2` in the context-assembly pilot.)

## Escalation reason cheatsheet (v2.3+)

When `/research-gather` Phase 2 fetches a source, the `gather_trace.yml`
record sets `decision` to one of `accept` / `reject` / `escalate_to_manual`.
The escalate-to-manual path is for sources that are real and accessible
but don't cleanly fit the current dossier. Use the following canonical
reasons so future authors recognize the pattern:

| Reason | When to use | Disposition |
|---|---|---|
| `survey of what we already have` | A survey / review paper covers the same primary sources you've already cited individually. Adds breadth-of-citation but no new mechanism. | Escalate; the human decides whether to cite as a secondary corroboration or skip entirely. |
| `borderline scope` | Real source, technically relevant, but its claim_family is closer to a sibling dossier (e.g., a security-of-RAG paper showing up during a search for evaluation methodology). | Escalate; consider whether to move to the sibling dossier or drop. |
| `vendor marketing` | Vendor blog / press release with no methodology, no benchmarks, no reproducible artifacts. | Reject. The mention is interesting; the citation isn't load-bearing. |
| `login-gated / paywalled` | Real source but you can't access it without authentication beyond what the toolkit's cache can handle. | Escalate; the human can decide to obtain access or find an open mirror. Set `rights_status: restricted` if cached via authenticated access. |

These four cover ~80% of `escalate_to_manual` cases observed across the
v2.2 dogfood arc (Phases 2-4) and the consumer:guides experimentation
sprint. New patterns surfaced by future dogfoods should be appended here
rather than reinvented.

## Verbatim title rendering

In dossier tables, render titles **exactly as they appear in the primary source**, including:
- Capitalization (don't title-case if the source uses sentence case)
- Subtitles separated by `:`
- Acronyms in their canonical form (`ChatGPT` not `Chat-GPT`; `LLaMA` not `Llama` if the paper uses LLaMA)

In 5-bullet entry display names, you can shorten to a recognizable handle (e.g. `**GCG** — Zou et al. (2023)` instead of the full 100-character title), but the dossier table must preserve the verbatim title.
