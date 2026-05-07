# <Topic file title> — <Sub-section name>

A 1–2 sentence intro establishing what this file covers and what's in scope.

## A1. <Sub-section name>

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| <paper title> | <First, Second & Third> (<year>) | <Venue or arXiv preprint> | arXiv:<id> | <org>/<repo> | <factual one-liner> | <distinct contribution this paper makes vs prior work> |
| <paper title> | <Authors> (<year>) | <Venue> | arXiv:<id> | — | <one-liner> | <key contribution> |

## A2. <Sub-section name>

| Title | Authors (year) | Venue | arXiv/DOI | GitHub | One-line description | Key contribution |
|-------|----------------|-------|-----------|--------|----------------------|------------------|
| ... | ... | ... | ... | ... | ... | ... |

---

**Schema rules** (enforced by validators/dossier.py):

- First 4 columns must be exactly: `Title | Authors (year) | Venue | arXiv/DOI`.
- Column 5 must start with `GitHub`, `HF`, `Code`, or `Repo`. Common variants accepted:
  `GitHub`, `GitHub / HF`, `HF`, `Code`, `Repo`. (Use `—` in the cell for entries without a code repo.)
- Additional columns (One-line description, Key contribution, Mechanism, Threat surface,
  Dataset, …) are flexible — each topic file picks the editorial shape that fits its content.
- Title and Authors cells must be non-empty on every data row.
- At least one of arXiv/DOI or GitHub must be filled per row (use `arXiv:N/A` or `(no arXiv)`
  in arXiv cell when the source is a blog post or conference talk without preprint).

For non-paper entries (regulatory documents, system cards, vendor reports), use a different
table schema with column 2 != "Authors (year)". Validators detect non-paper tables and
apply looser checks (Title non-empty + URL recommended).
