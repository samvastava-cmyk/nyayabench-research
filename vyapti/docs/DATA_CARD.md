# Data Card

> **Camera-ready note (Nov 2026).** This document dates from the August 2026 submission. Where it differs from the camera-ready paper or [CHANGELOG.md](../CHANGELOG.md), those take precedence; in particular the specificity analysis, the textual status of the taxonomy, and the scorer versions behind the corpus-level results were corrected.


15 datasets, 1,691 items. JSONL, one object per line, UTF-8. Manifest with full label distributions: [`data/manifest.json`](../data/manifest.json).

## The headline fact is a flaw

Across the 909 typed cases, **17 are sound arguments (1.9%)**, against a real-world prevalence near 32.5%. The v4 held-out suite the paper reports on contains zero. This is the diagnosed root cause of the specificity defect, and it is verifiable directly from these files. See [LIMITATIONS.md](LIMITATIONS.md) §2.

## Schema

```json
{"id": "V4-001", "suite": "unseen_v4", "text": "...", "label": "RF-07a",
 "domain": null, "difficulty": null, "edge_type": null, "note": null,
 "text_sha256_16": "a1b2c3d4e5f60718"}
```

`label` is one of the 13 taxonomy codes or `NONE`. `text_sha256_16` is a truncated SHA-256 of the lower-cased normalised text, for duplicate detection across suites.

Cross-map records carry `western_label` and `source` instead of `label`. Generation records carry `prompt`, `domain` and `reasoning_target`, and are unlabelled.

## Typed benchmark suites

| Suite | n | NONE | categories | notes |
|---|---|---|---|---|
| `standard_v1` | 50 | 0 (0.0%) | 12 | First public benchmark suite. Balanced across 12 categories, zero sound arguments. |
| `unseen_v1` | 132 | 0 (0.0%) | 11 | Filename said 150; the file contains 132 cases. Published under the true count. |
| `unseen_v2` | 137 | 0 (0.0%) | 12 | 137 cases. |
| `unseen_v3` | 100 | 0 (0.0%) | 12 | 100 cases. |
| `unseen_v4` | 120 | 0 (0.0%) | 12 | The held-out suite reported in the ICON 2026 paper (95.83%, 115/120). Perfectly balanced, 10 per category, zero sound arguments. |
| `stress_150` | 150 | 0 (0.0%) | 12 | Long-form, multi-clause stress cases. |
| `adversarial_30` | 30 | 0 (0.0%) | 12 | Adversarial pilot. |
| `adversarial_100` | 100 | 0 (0.0%) | 12 | Adversarial suite, balanced across 12 categories. |
| `natural_language_50` | 50 | 0 (0.0%) | 7 | Filename said 200; the file contains 50 cases. Published under the true count. Covers RF-01..RF-07a only. |
| `edge_cases_20` | 20 | 15 (75.0%) | 3 | The only suite with a meaningful sound-argument share (15/20 NONE). |
| `external_20` | 20 | 2 (10.0%) | 12 | Externally sourced probe set; includes 2 sound arguments. |

### Label distribution

| Suite | RF-01 | RF-02 | RF-03 | RF-04 | RF-05 | RF-06 | RF-07a | RF-07b | RF-08 | RF-09 | RF-10 | RF-11 | NONE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `standard_v1` | 5 | 4 | 4 | 4 | 4 | 5 | 5 | 5 | 4 | 4 | 3 | 3 | · |
| `unseen_v1` | 15 | 10 | 12 | 12 | 8 | 10 | 18 | 15 | 15 | 12 | 5 | · | · |
| `unseen_v2` | 14 | 10 | 11 | 11 | 8 | 10 | 18 | 15 | 14 | 12 | 10 | 4 | · |
| `unseen_v3` | 10 | 7 | 9 | 9 | 6 | 7 | 12 | 10 | 10 | 8 | 6 | 6 | · |
| `unseen_v4` | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | · |
| `stress_150` | 14 | 11 | 13 | 13 | 9 | 11 | 19 | 15 | 13 | 12 | 8 | 12 | · |
| `adversarial_30` | 5 | 2 | 2 | 3 | 3 | 3 | 2 | 2 | 2 | 2 | 2 | 2 | · |
| `adversarial_100` | 9 | 8 | 9 | 8 | 8 | 8 | 9 | 8 | 8 | 8 | 8 | 9 | · |
| `natural_language_50` | 8 | 8 | 8 | 8 | 8 | 8 | 2 | · | · | · | · | · | · |
| `edge_cases_20` | 1 | 2 | · | · | · | · | 2 | · | · | · | · | · | 15 |
| `external_20` | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | 1 | 2 |

## Cross-mapping suites

Sampled from the **LOGIC** dataset (Jin et al., 2022, EMNLP Findings), carrying gold Western fallacy labels. Used to measure whether Vyāpti labels carry information the Western label does not — 68.3% non-redundancy, +27–43% mutual information over frontier models.

**`logic_195`** — 195 cases across 13 Western categories.

| Western label | n |
|---|---|
| ad hominem | 15 |
| ad populum | 15 |
| appeal to emotion | 15 |
| circular reasoning | 15 |
| equivocation | 15 |
| fallacy of credibility | 15 |
| fallacy of extension | 15 |
| fallacy of logic | 15 |
| fallacy of relevance | 15 |
| false causality | 15 |
| false dilemma | 15 |
| faulty generalization | 15 |
| intentional | 15 |

**`logic_487`** — 487 cases across 13 Western categories.

| Western label | n |
|---|---|
| ad hominem | 38 |
| ad populum | 38 |
| appeal to emotion | 38 |
| circular reasoning | 38 |
| equivocation | 31 |
| fallacy of credibility | 38 |
| fallacy of extension | 38 |
| fallacy of logic | 38 |
| fallacy of relevance | 38 |
| false causality | 38 |
| false dilemma | 38 |
| faulty generalization | 38 |
| intentional | 38 |

**Licensing.** LOGIC states no licence, so these files carry row references into LOGIC's `data/edu_all.csv` (pinned commit) and a hash, not texts. `scripts/fetch_external.py` restores and verifies them. Cite Jin et al. (2022) if you use them.

## Generation prompts

Elicitation prompts used to produce model output for VRS leaderboard scoring. Unlabelled — there is no gold failure category, because the point is to see what a model does unprompted.

**`reasoning_prompts_v1`** — 50 prompts. Domains: economics_finance (10), law_ethics_society (10), medicine_health (10), science_environment (10), technology_engineering (10).

**`reasoning_prompts_v2`** — 50 prompts. Domains: economics_finance (10), law_policy_society (10), medicine_health (10), science_environment (10), technology_engineering (10).

## Known problems with this corpus

**Almost no sound arguments.** 1.9% NONE. Stated above; the single most important flaw.

**Two filenames lied about their size.** `vyapti_unseen_150.json` held 132 cases and `vyapti_natural_language_200.json` held 50. Both are published under their true counts as `unseen_v1` (132) and `natural_language_50` (50). Any earlier figure citing n=150 or n=200 for those suites is wrong in its denominator.

**Cross-suite duplicates.** 2 exact-text groups covering 4 items appear in more than one typed suite (`unseen_v2:127`/`unseen_v3:92`, and `adversarial_100:14`/`natural_language_50:14`). Small, but it means those suites are not fully independent. Listed in `data/manifest.json` under `cross_suite_exact_duplicates`.

**Prompt contamination.** 10 of 120 v4 cases (8.3%) appear verbatim in the calibrated prompt. The contamination-free figure is reported alongside the raw one. Audit any suite yourself with `python scripts/audit_contamination.py <suite>`.

**Single author, no second annotator.** Every typed suite was written and labelled by one person. There is no inter-annotator agreement figure on the gold labels themselves and no adjudication protocol. κ = 0.7908 measures Vyāpti against ground truth, not two humans against each other.

**Development suites are compromised by rule-layer tuning.** `external_20`, `natural_language_50`, `adversarial_30` and `adversarial_100` have 28–40% of cases matching a hard-coded literal in the Phase 1 rule layer. Do not cite figures computed on them. The v4 held-out suite is at 1.7% and is unaffected. Full table: [LIMITATIONS.md](LIMITATIONS.md) §5.

**English only.** Despite the Sanskrit sources, every case is in English. Whether the taxonomy transfers across languages is untested.

## What is not here

- **MAFALDA cases.** Referenced throughout the results but not redistributed; get them from the original authors.
- **The v5 balanced suite (n=160).** Reported in the paper; not located during the Phase 2 extraction. Tracked as an open item.
- **The calibrated prompt profile.** See [prompts/README.md](../prompts/README.md).

## Intended and unintended use

**Intended.** Benchmarking typed reasoning-failure detection; replicating the cross-mapping and mutual-information analyses; studying exemplar-vs-definition transfer; extending the taxonomy.

**Not intended.** Training data for a production classifier (too small, too skewed, single author). Any deployment where a false alarm carries a cost — specificity is 33–37%. Evidence that the taxonomy tracks anything outside this project; there is no external validity result yet.

## Licence

Taxonomy and Vyāpti-authored suites: **CC-BY-4.0**. LOGIC and MAFALDA: referenced, not included. Code: MIT.
