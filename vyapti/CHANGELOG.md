# Changelog

## Camera-ready release (November 2026)

Corrections to the reviewed submission and to the August 2026 package, found by reviewers or by the author's own audit. Each is also stated in the paper where it applies.

**Taxonomy**
- v2.2. Nine categories are defined in the root text of the *Tarka-Saṃgraha*, not ten: RF-07b has no defining passage and is derived from commentary.
- The v2.1 `source_quote_sanskrit` fields paraphrased the text rather than quoting it. They are kept, renamed `source_quote_sanskrit_v2_1_paraphrase`, for provenance. A new `source_passage_verbatim` field quotes the GRETIL e-text exactly.
- Explicit `textual_status` field. The classifier's definitions are unchanged (byte-identical definition block).

**Prompt**
- The calibrated v10 prompt is now public (`prompts/production/`).
- Two experiments run on 18 Aug 2026 (the sound-exemplar ladder and the external validation) built this prompt incorrectly: the definitions placeholder was left unfilled and literal braces were doubled. Their figures are not used in the paper. Corrected re-runs are in `results/camera_ready/`, which also reports the incorrect build as a separate arm, so the size of the error is visible.

**Pipeline**
- The rule layer of the original research code contained literal matches on 74 benchmark sentences. They reach 2 of 120 held-out cases and up to 40% of some development suites. This release contains none.
- The original arbitration could turn a NONE verdict into a failure label; this release never does.

**Results and versions**
- The corpus-level analyses (the 2,372-case LOGIC mapping and the 276-case information comparison) were run with scorer v8–v9 during calibration, not v10. The submitted paper's MAFALDA detection figures were v9; the camera-ready figures are v10.
- Specificity is reported separately for sound texts that argue and those that do not; the pooled figure overstated performance on real arguments.
- RF-01's size is partly a scope boundary: fallacies of relevance have no *hetvābhāsa* counterpart.

**Data**
- LOGIC and MAFALDA texts are no longer redistributed. Items carry row references and hashes; `scripts/fetch_external.py` restores them from pinned commits.

## August 2026

Initial package accompanying the ICON 2026 submission.
