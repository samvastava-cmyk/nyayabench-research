# Limitations

> **Camera-ready note (Nov 2026).** This document dates from the August 2026 submission. Where it differs from the camera-ready paper or [CHANGELOG.md](../CHANGELOG.md), those take precedence; in particular the specificity analysis, the textual status of the taxonomy, and the scorer versions behind the corpus-level results were corrected.


Everything known to be wrong with this artifact, with measurements. Nothing here is hedged and nothing is omitted because it is inconvenient.

---

## 1. Specificity is 33–37%

The instrument flags roughly six in ten sound arguments. It must not be used to screen text or as a gate; use it to type failures already found. Confidence thresholding does not fix it — the classifier is confidently wrong (0.906 mean confidence on false positives vs 0.946 on correct negatives).

**Status:** diagnosed, Experiment 1 designed. Full analysis in [RESULTS.md](RESULTS.md).

---

## 2. The evaluation corpus contains almost no sound arguments

Across the 909 typed cases released here, **17 carry the NONE label — 1.9%**, against a real-world prevalence near 32.5%.

| Suite | n | NONE | share |
|---|---|---|---|
| edge_cases_20 | 20 | 15 | 75.0% |
| external_20 | 20 | 2 | 10.0% |
| **every other typed suite** | **869** | **0** | **0.0%** |

The v4 held-out suite the headline 95.83% comes from contains **zero** sound arguments. A suite with no negatives cannot measure specificity at all, and a suite with no negatives cannot penalise over-flagging. The headline number is a *typed accuracy on flagged items* figure and should never be quoted as overall accuracy.

**Status:** the single most important structural flaw. Experiment 3 builds a corrected 300-case suite, 60% failure / 40% sound.

---

## 3. Sound arguments cannot be written by us

The obvious fix — write 120 sound arguments — reintroduces the circularity the paper already concedes: a taxonomy author writing the negative class defines what counts as sound by the same hand that defined what counts as failure.

Sound arguments must be **sourced externally**: MAFALDA gold-NONE (65 available), Argument Annotated Essays, IBM Debater evidence sets, FOLIO valid entailments. Register differences between sources must be documented, because a classifier can learn to detect *register* rather than *soundness*.

**Status:** open. This is the hard part of Experiment 3 and it is not solved.

---

## 4. Prompt contamination in the held-out suite

Ten of 120 v4 cases (8.3%) appear verbatim in the calibrated prompt. The contamination-free figure is reported alongside the raw one (95.41% vs 95.83%), and the difference is small — but the suite was not built to be clean and the audit was retrospective.

`scripts/audit_contamination.py` exists so that never happens again. Standing Phase 2 rule: **no new test set is reported on until it has been audited.**

**Status:** measured, mitigated in reporting, structurally fixed for future suites.

---

## 5. The Phase 1 rule layer contained item-specific tuning

The Phase 1 stage-1 module matched **74 content-bearing string literals** directly against input text — among them `"antibiotics cure infections"`, `"every fire produces smoke"`, `"studying once ensures top scores"`, `"sea level atmospheric pressure"` and `"MDR1 overexpression"`. Each is a specific benchmark item. A rule layer that recognises its own test set is not measuring generalisation.

This was found during the Phase 2 audit and had not previously been quantified. The measurement:

| Suite | cases matching ≥1 hard-coded literal | |
|---|---|---|
| external_20 | 8/20 | 40.0% |
| natural_language_50 | 19/50 | 38.0% |
| adversarial_30 | 10/30 | 33.3% |
| adversarial_100 | 28/100 | 28.0% |
| edge_cases_20 | 1/20 | 5.0% |
| standard_v1 | 2/50 | 4.0% |
| **unseen_v4 (the paper's held-out suite)** | **2/120** | **1.7%** |
| unseen_v1 / v2 / v3 | 3/369 | 0.8% |
| stress_150 | 1/150 | 0.7% |
| **Total** | **74/909** | **8.1%** |

**What this means.** The tuning was fitted against the early development suites — `external_20`, `natural_language_50`, the adversarial sets — where it touches a third to two fifths of cases. Any figure reported on those suites is compromised and should not be cited.

It reaches **1.7% of the v4 held-out suite**, so it cannot account for the headline 95.83%. Two cases out of 120 is inside the noise. The reported result survives.

**Status:** none of the 74 literals is reproduced in this repository. `tests/test_core.py::test_extraction_has_no_benchmark_literals` is a regression guard that fails the build if any returns. The v11 rule layer is structural only.

---

## 6. RF-01 is a sink, and two figures for it disagree

RF-01 absorbs roughly half of all external classifications and 51% of false positives, on one worked exemplar against RF-07a's nine.

Two share figures exist over the same 2,372 LOGIC cases:

- **49.2%** — paper audit
- **45.1%** — `results/crossmap_logic_2372.json`, dated 2026-03-18

They have not been reconciled. Neither should be cited until the difference is traced to a sampling or coverage-denominator difference.

**Status:** open, logged as a Phase 2 task. Experiment 2 targets RF-01 share below 30% regardless of which baseline is correct.

---

## 7. Five of twelve categories are inert on real text

RF-05, RF-07b, RF-10 and RF-11 fire on 18 of 2,174 external cases; RF-04 on 30. They fire readily on constructed suites and almost never on found text.

Two readings, and the honest position is that both are live:

1. These failure modes are genuinely rare in the corpora tested.
2. The classifier cannot detect them outside the register in which they were written.

Nothing here distinguishes the two. That would need a targeted corpus where the rare failures are known to occur.

**Status:** motivates the Vyāpti-8 production profile (`vyapti.VYAPTI_8`). The full 13-category taxonomy remains the research artifact.

---

## 8. RF-10 has no source

RF-10 (Performative Self-Refutation) is an inferred category with **no direct sūtra source**. It is marked `INFERRED` in the taxonomy metadata and reported as such. It is a useful category; it is not Navya-Nyāya.

RF-07b, RF-09 and RF-11 are concept-verified but their status as distinct *hetvābhāsa* sub-types is our classification, not the tradition's.

**Status:** disclosed in the artifact itself, not only in prose. `python scripts/audit_taxonomy.py` prints it.

---

## 9. Single judge, single vendor, for the headline number

All headline figures use `gpt-4.1`. Portability was tested — 94–96% across 4 architectures and 6 judge models — but the reported numbers rest on one model from one vendor at one point in time. Model deprecation alone will eventually invalidate them.

**Status:** portability measured; re-running against current frontier models is a Phase 2 task. If a newer model reaches parity without the 676-line prompt, that is itself a publishable finding.

---

## 10. Temperature was not set for every provider

In the multi-model portability run, temperature was set explicitly for some providers and left at the vendor default for Anthropic. This is a documented confound in the paper.

**Status:** structurally fixed. `vyapti.ChatClient` requires `temperature` as a positional argument and emits it explicitly on every provider's request payload. There is no default-by-omission path in this codebase.

---

## 11. The Phase 1 pipeline could fail silently

Two silent-failure paths existed, and both corrupted real runs:

- An unreachable judge returned `{"rf_code": "NONE", "source": "llm_unavailable"}` with no error. A full August experiment run was invalidated before anyone noticed.
- An unparseable response, or an unrecognised label, was coerced to `NONE`.

Both are indistinguishable from a genuine "this argument is sound" verdict. Both therefore *inflated the apparent sound-argument rate* — in the one metric the project most needs to be honest about.

**Status:** structurally fixed. `UnavailableJudgeError` and `MalformedJudgeResponseError` are raised, never swallowed; `JudgeVerdict` rejects unknown labels; the smoke test aborts a run in three calls if the judge is not answering. Four tests in `tests/test_core.py` assert this directly.

---

## 12. Leaderboard confidence intervals are too wide to rank

The VRS leaderboard's 95% CIs span 22–28 points on 50 prompts. The top three models are not distinguished by that evidence. The ranking illustrates the method; it is not a claim about which model reasons better.

**Status:** disclosed inline in [RESULTS.md](RESULTS.md). A ranking claim would need a far larger prompt set.

---

## 13. No external validity

Everything rests on two fallacy datasets and our own constructed suites. There is no evidence that a Vyāpti label tracks anything a person outside this project cares about.

The strongest available test: Reddit ChangeMyView carries an *outcome* signal. If arguments Vyāpti calls sound are more likely to have changed a mind, that is external validity — the first evidence that the taxonomy tracks something real rather than something we specified. That result would be worth more than another accuracy number.

**Status:** open. Highest-value item after the gate.

---

## 14. Taxonomy schema gap

RF-09, RF-10 and RF-11 declare `parent: "Extended"`, which is described in `extended_categories_note` but has no object in `parent_categories`. Harmless, but it means a naïve schema validator will fail on the released JSON.

**Status:** the loader recognises the documented sentinel. Slated for taxonomy v2.2.

---

## 15. Corpus provenance is thin

The typed suites were written by one person over six weeks. There is no second annotator on suite construction, no inter-annotator agreement on the gold labels themselves, and no adjudication protocol. κ = 0.7908 was measured for Vyāpti against ground truth — not for two humans against each other on the ground truth.

**Status:** open. A second annotator on any new suite is the minimum bar for Experiment 3.
