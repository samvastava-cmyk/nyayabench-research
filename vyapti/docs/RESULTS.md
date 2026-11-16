# Results

> **Camera-ready note (Nov 2026).** This document dates from the August 2026 submission. Where it differs from the camera-ready paper or [CHANGELOG.md](../CHANGELOG.md), those take precedence; in particular the specificity analysis, the textual status of the taxonomy, and the scorer versions behind the corpus-level results were corrected.


Every figure below was recomputed from raw run data during the pre-submission audit. Six numbers that appeared in earlier project documentation were wrong and are corrected here. Where a discrepancy remains unresolved, it is marked as such rather than smoothed over.

Prompt profile for all Phase 1 figures: `v10-rf07a-fix` — 676 lines, 66 few-shot exemplars, 31 conditional rules, 7 arbitration overrides. Judge: `gpt-4.1`, temperature 0.0, 1000-token cap.

---

## Headline

| Metric | Value | Source |
|---|---|---|
| Typed accuracy, held-out | **95.83%** (115/120) | v4 suite |
| Typed accuracy, contamination-free | **95.41%** (104/109) | 10 cases found verbatim in the prompt, removed |
| Independent re-run | **95.83%**, per-category identical | August 2026 |
| Precision / Recall / F1 | 82.8 / 100.0 / 90.6 | v5 balanced, n=160 |
| Precision / Recall / F1 | 75.3 / 97.0 / 84.8 | MAFALDA, n=200 |
| **Specificity** | **37.5% and 33.8%** | **the defect** |
| Portability | 94–96% across 4 architectures | 6 judge models |

The typed-accuracy figure is the one worth taking seriously: *given that a failure has been flagged, the category assigned is right 96 times in 100, and that survives both an independent re-run and the removal of every contaminated case.*

---

## The defect, stated properly

Specificity is **33.8%** on MAFALDA and **37.5%** on the balanced suite. The classifier flags roughly six in ten sound arguments.

Two things make this worse than a raw number suggests.

**An always-flag baseline reaches F1 80.6% on MAFALDA.** Against 84.8% for the classifier. On F1 alone, the typed classifier beats "shout at everything" by four points. What justifies the classifier is not F1 — it is the typed label, which the baseline cannot produce at all.

**Confidence thresholding does not fix it.** The classifier is *confidently* wrong: mean confidence 0.906 on false positives against 0.946 on correct negatives. The distributions overlap almost entirely. A 0.90 threshold buys 0.5 F1 points; 0.95 collapses recall to 3%. There is no operating point on this curve that rescues the instrument. The fix has to change the classifier, not post-process it.

### Diagnosed cause

NONE appears in **2 of 66** few-shot exemplars (3.0%). Real-world prevalence of sound arguments is around **32.5%**. The classifier is shown "nothing is wrong" as a valid answer in 3% of its calibration and asked to produce it a third of the time.

This is measurable directly from the released corpus. Across the 909 typed cases in `data/suites/`, **17 carry the NONE label — 1.9%**. The v4 held-out suite the headline number comes from contains **zero sound arguments**. The training signal and the evaluation signal share the same blind spot.

### Evidence the fix works

A pilot adding 8 NONE exemplars:

| | before | after |
|---|---|---|
| Specificity | 30.8% | **38.5%** |
| Precision | 73.5% | **76.0%** |
| Recall | 92.6% | **94.1%** ← *rose* |

Direction right on every metric, and recall did not pay for it. McNemar p = 0.13 on 7 discordant pairs — underpowered but monotone. Experiment 1 is the powered version.

---

## Cross-mapping against Western fallacy categories

Vyāpti was run over 2,372 cases from the LOGIC dataset (Jin et al., 2022) carrying gold Western fallacy labels.

| | |
|---|---|
| Coverage | 91.7% |
| Non-redundancy | **68.3%** of Vyāpti labels are not derivable from the Western label |
| Mutual information | **1.118 bits** vs 0.880 / 0.841 / 0.779 for raw frontier models (n=276) |

The mutual-information result is the strongest evidence that the taxonomy carries information a general-purpose model does not already produce: +27% to +43% over three frontier models asked the same question directly. The non-redundancy figure says the same thing from the other side — two thirds of the time, knowing the Western label does not tell you the Vyāpti label.

The confusion matrix is in [`results/crossmap_logic_2372.json`](../results/crossmap_logic_2372.json).

### The RF-01 sink

RF-01 absorbs the largest share of external classifications by a wide margin, and **51% of all false positives**. It has one worked exemplar against RF-07a's nine, and the broadest definition in the taxonomy. Uncertain cases fall into it because nothing else claims them.

> **Unresolved discrepancy.** Two RF-01 share figures exist in the project record: **49.2%** (paper audit) and **45.1%** (`results/crossmap_logic_2372.json`, dated 2026-03-18, over the same 2,372 cases). They have not been reconciled. Both are reported here; neither should be cited until the difference is traced. This is logged as a Phase 2 task.

Either way the conclusion holds: RF-01 takes roughly half of everything, which is what Experiment 2 is designed to change. Target is below 30% with per-category accuracy holding.

### Dead categories

RF-05, RF-07b, RF-10 and RF-11 fire on **18 of 2,174** external cases. RF-04 fires on 30. Five of twelve are effectively inert outside constructed test suites.

This motivates a **Vyāpti-8** production profile shipping alongside the full 13-category research taxonomy — the difference between a specification and an implementation. The research taxonomy stays complete and textually grounded; the production profile contains only what fires on real text. The set is defined in code as `vyapti.VYAPTI_8`.

---

## Leaderboard (VRS v2)

Frontier models scored on 50 elicitation prompts, 3 trials each, bootstrap 95% CIs. Judge `gpt-4.1` on scorer `v9-rf03-rf04-rf05-fix`. Raw: [`results/leaderboard_v2.json`](../results/leaderboard_v2.json).

| Rank | Model | VRS | 95% CI | Top failure |
|---|---|---|---|---|
| 1 | Claude Sonnet 4 | 72.7 | 60.0–84.0 | RF-01 |
| 2 | GPT-4.1 | 70.7 | 56.0–82.0 | RF-07b |
| 3 | GPT-4o | 66.0 | 54.0–78.0 | RF-01 |

Scorer accuracy on this run 93.33%; Vyāpti vs ground truth κ = 0.7908 (substantial agreement).

**Read these with care.** Confidence intervals are 22–28 points wide on 50 prompts. The three models are not separated by this evidence — the intervals overlap almost completely. Gemini models were excluded after API rate limiting, so the run is not a complete field. Treat the ranking as illustrative of the method, not as a claim about which model reasons better.

---

## The transfer finding

Running in parallel as Paper 2, and probably the most portable result here:

> **Exemplars transfer a formal scheme to a model. Definitional elaboration degrades it.**

The controlled comparison: elaborating the definitions moved κ 0.543 → 0.292. Replacing elaboration with calibrated exemplars moved accuracy 52% → 95.8%. Same taxonomy, same judge, opposite directions.

If this replicates on two or three unrelated classification schemes it is a methods result for anyone building an LLM judge, with a considerably wider audience than the hetvābhāsa work.

---

## Corrected counts

Earlier project documentation was wrong on all four:

| | wrong | correct |
|---|---|---|
| Prompt lines | 655 | **676** |
| Few-shot exemplars | 72 | **66** |
| Conditional rules | 17 | **31** |
| Arbitration overrides | ~8 | **7** |

---

## Reproducing

Offline — no API key, runs in seconds:

```bash
pytest tests/ -q                                    # 29 tests incl. corpus integrity
python scripts/audit_taxonomy.py                    # source-verification status
python scripts/audit_contamination.py --cross-suite # inter-suite leakage
```

With a key:

```bash
vyapti-smoke
vyapti-run data/suites/unseen_v4.jsonl -o runs/v4.jsonl --arm reference
```

The `reference` profile will not reproduce 95.83% — it carries no exemplars. That gap *is* the transfer finding, and measuring it is a legitimate use of this repository.
