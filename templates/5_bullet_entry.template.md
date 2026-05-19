# 5-bullet entry — canonical schema

The structure each paper-synthesis entry uses inside `01_<area>.md` … `0K_<area>.md`
files. Designed for dual-audience consumption: humans skim fluidly, agents parse
deterministically.

## Canonical 5-bullet entry (paper synthesis)

```markdown
- **<Display name>** — <Authors short> (<Venue / Year>).
  - **Source:** <primary URL: arXiv / DOI / GitHub repo>
  - **Code:** <code repo URL or "—" for none>
  - **Mechanism:** <factual one-liner: what does the paper actually do?>
  - **Result:** <distinct contribution / key claim / canonical reference status>
  - **Status:** Verified | Unverified | (vendor blog) | (recheck after <YYYY-MM-DD>) | ...
  - **Evidence:** ev_<topic>_0001
```

**Order matters** for paper synthesis entries — the validator enforces the canonical
order (Source / Code / Mechanism / Result / Status). The `Code` bullet may be omitted
when no separate code repo exists; the validator allows it. All other bullets must be
present.

## Source-bullet rules

- The Source line must contain at least one URL or bibkey-style token (e.g.
  `bibkey2024slug`).
- Use `https://arxiv.org/abs/<id>` for arXiv (NOT `https://arxiv.org/pdf/<id>`).
- Use `https://doi.org/<doi>` for journal DOIs.
- Use `https://github.com/<org>/<repo>` for GitHub.
- Use `https://huggingface.co/datasets/<user>/<name>` for HF datasets.
- Vendor blog URLs are accepted but should be flagged `(vendor blog)` in Status.

## "No LLM-generated specifics" rule

Quantitative claims (ASR percentages, dataset sizes, benchmark counts) MUST appear in
the primary source's abstract or in a verified body excerpt. If only in the body, mark
with `(unverified body claim)`. **Never assert a specific number that you cannot point
to in the linked Source URL** — that's the most common hallucination mode for synthesis
work.

## Variant: vendor / standards / lab profiles

For non-paper-synthesis entries (vendor profile, standards document, lab framework),
use a content-appropriate bullet schema. Common variants:

```markdown
- **<Vendor name>** — <Location, founded year>.
  - **Source:** <vendor website>
  - **Status:** <funding round / acquisition / shipping status>
  - **Product line:** <products>
  - **Mechanism:** <what their tech does>
  - **Integration:** <where it fits in your stack>
```

The validator accepts these heterogeneous bullet schemas as long as Source is present
with a URL/bibkey. Only paper-synthesis entries (those including a `Result` bullet)
are subject to canonical-order enforcement.

## Strict-live v2 evidence markers

For v2 outputs, every substantive row/block must include compact evidence IDs
from `evidence_ledger.yml`. Use a visible `Evidence` bullet for maximum
traceability, or a compact suffix such as `[ev_topic_0001]` when the file would
otherwise become too noisy.
