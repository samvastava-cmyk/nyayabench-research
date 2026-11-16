# Hetvābhāsa taxonomy

A machine-readable taxonomy of reasoning failures derived from the Navya-Nyāya account of *hetvābhāsa* (fallacious reasons). It has 13 categories, coded RF-01 to RF-12, with RF-07 split into RF-07a and RF-07b.

| File | Version | Note |
|---|---|---|
| `hetvabhasa_v1.json` | 1.0.0 | First version, March 2026 |
| `hetvabhasa_v2.json` | 2.0.0 | Revision, March 2026 |
| `hetvabhasa_v2.1.json` | 2.1 | Version used by the scorers and experiments in this repository |

Each file holds the category definitions, confusable pairs, a decision flowchart and notes for calibrating an LLM judge.

## Erratum for v2.1

The files are published as they were used in the experiments. Version 2.1 has known errors, found in a source check in November 2026:

- The Sanskrit passages stored in the file are paraphrases, not verbatim quotations from the *Tarka-Saṃgraha*, although the file marks them as verified.
- Nine categories are defined in the root text, not ten. RF-07b is derived from commentary.
- The printed edition named in the file is under verification.
- RF-10 has no direct textual source. RF-11 is verified as a concept but inferred as a hetvābhāsa category. The file states both.

A corrected version 2.2, with the passages quoted from the source text, will be added with the camera-ready paper.
