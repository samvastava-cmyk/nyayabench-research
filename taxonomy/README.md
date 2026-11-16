# Hetvābhāsa taxonomy

A machine-readable taxonomy of reasoning failures derived from the Navya-Nyāya account of *hetvābhāsa* (fallacious reasons). It has 13 categories, coded RF-01 to RF-12, with RF-07 split into RF-07a and RF-07b.

| File | Version | Note |
|---|---|---|
| `hetvabhasa_v1.json` | 1.0.0 | First version, March 2026 |
| `hetvabhasa_v2.json` | 2.0.0 | Revision, March 2026 |
| `hetvabhasa_v2.1.json` | 2.1 | Version used by the scorers and experiments in this repository. Has a known erratum; see below |
| `hetvabhasa_v2.2.json` | 2.2 | **Corrected, November 2026.** Sanskrit passages quoted exactly from the source text, with explicit textual status per category |

Each file holds the category definitions, confusable pairs, a decision flowchart and notes for calibrating an LLM judge.

## Erratum for v2.1

The files are published as they were used in the experiments. Version 2.1 has known errors, found in a source check in November 2026:

- The Sanskrit passages stored in the file are paraphrases, not verbatim quotations from the *Tarka-Saṃgraha*, although the file marks them as verified.
- Nine categories are defined in the root text, not ten. RF-07b is derived from commentary.
- The printed edition named in the file is under verification.
- RF-10 has no direct textual source. RF-11 is verified as a concept but inferred as a hetvābhāsa category. The file states both.

## Version 2.2, the correction

`hetvabhasa_v2.2.json` fixes all of the above:

- `source_passage_verbatim` now holds the defining sentence or standard example for
  each root-text category, quoted exactly from the GRETIL electronic text of the
  *Tarka-Samgraha*, with its section number (AnTs_52 to AnTs_57). Each quotation was
  checked against that file as an exact substring.
- `textual_status` states the basis of every category, in four values:

  | Status | Categories |
  |---|---|
  | `VERIFIED_ROOT_TEXT` — defined in the root text | RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07a, RF-08, RF-12 |
  | `DERIVED_FROM_COMMENTARY` — built from commentary on a root-text definition; the separate category is ours | RF-07b |
  | `INFERRED_CLASSICAL_DOCTRINE` — a classical doctrine; promoting it to a *hetvābhāsa* type is ours | RF-09, RF-11 |
  | `NO_TEXTUAL_SOURCE` — a modern addition | RF-10 |

- The v2.1 paraphrases are kept, renamed `source_quote_sanskrit_v2_1_paraphrase`, so the
  earlier state of the file stays inspectable.

**The definitions the scorer reads are byte-identical between v2.1 and v2.2.** Only the
provenance metadata changed, so no experimental result in this repository is affected.
The English glosses are ours; the Sanskrit quotations carry the source text's own
licence (see `../LICENSE-DATA`).

Nine categories, not ten, are defined in the root text. No scholar of Navya-Nyāya has
reviewed the taxonomy.
