# Dossier — vol25 prompt injection (recreated) compiled stats

**Compiled:** 2026-05-07
**Source ledger:** `../bib_ledger.yml`
**Source plan:** `../research_plan.md`
**Coverage cutoff:** May 2026.

## Topic-file split

| File | Claim families covered | Approx entries |
|---|---|---|
| `01_attacks_direct.md` | attack_direct_jailbreak + attack_white_box + attack_black_box | 23 |
| `02_attacks_indirect_agentic_multimodal.md` | attack_indirect_pi + attack_agentic + attack_multimodal + incidents_disclosure | 26 |
| `03_defenses.md` | defense_detection + defense_smoothing + defense_architectural + defense_latent_space + defense_alignment | 27 |
| `04_training_time_threats.md` | attack_training_time | 13 |
| `05_datasets_benchmarks.md` | evaluation | 18 |
| `06_tools_vendors.md` | red_teaming_tools | 24 |
| `07_standards_industry.md` | standards_governance + other | 16 |

## Total

~147 entries rendered across 7 topic files. (Some entries appear in tools/vendors that also have arXiv preprints — duplication reflects the bib_ledger taxonomy decisions, not editorial reuse.)

## Notes

- Bibkey-derived `Authors (year)` rendering was applied per BURN_IN Stage 2 #2; some heuristic entries may need WebFetch verification in a follow-up pass.
- Non-paper entries (vendor pages, standards docs, HF model/dataset cards) use the same 7-column table schema with `(no arXiv)` placeholders for the arXiv/DOI column. Validators apply looser checks to non-paper rows.
- Entries appearing in both A6 (tools) and A1 (papers) are intentional: GCG / NeMo Guardrails / others have both an academic paper and a code release. The dossier indexes both because downstream readers ask about both.
