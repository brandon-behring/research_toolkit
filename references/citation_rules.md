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
- `(post-2025; recheck)` — claim is from after the toolkit's coverage cutoff and may have drifted.
- `(unverified body claim)` — quantitative claim is from paper body, not abstract; reader should re-verify.

## Verbatim title rendering

In dossier tables, render titles **exactly as they appear in the primary source**, including:
- Capitalization (don't title-case if the source uses sentence case)
- Subtitles separated by `:`
- Acronyms in their canonical form (`ChatGPT` not `Chat-GPT`; `LLaMA` not `Llama` if the paper uses LLaMA)

In 5-bullet entry display names, you can shorten to a recognizable handle (e.g. `**GCG** — Zou et al. (2023)` instead of the full 100-character title), but the dossier table must preserve the verbatim title.
