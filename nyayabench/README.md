# NyāyaBench: benchmark sets, scorer test suites and validation result

Material from the NyāyaBench platform built between March and April 2026. All sets in this folder were constructed for this project. No third-party dataset text is included.

## `benchmark-sets/`

Frozen sets. `BENCHMARK_VERSIONS.md` is the original version log; the three SHA-256 hashes it lists match the files here. Paths in that log refer to the original development environment.

| File | Cases | Purpose |
|---|---|---|
| `nyayabench_standard_v1.json` | 50 | Labelled arguments for scorer validation, each with an expected category |
| `nyayabench_reasoning_prompts_v1.json` | 50 | Open-ended reasoning prompts. Deprecated: they elicited meta-analysis instead of direct reasoning |
| `nyayabench_reasoning_prompts_v2.json` | 50 | Redesigned prompts across five domains, used for multi-model benchmarking. No fixed ground truth |
| `nyayabench_reasoning_prompts_v2_1_expansion.json` | 50 | Expansion set added 28 March 2026 |

## `scorer-test-suites/`

Arguments with an expected reasoning-failure category, used to develop and test the scorer.

| File | Cases | Note |
|---|---|---|
| `vyapti_unseen_v4.json` | 120 | The held-out suite for the v10 result: 10 cases in each of 12 categories |
| `vyapti_unseen_v3.json` | 100 | Earlier held-out suite |
| `vyapti_unseen_v2.json` | 137 | Earlier held-out suite |
| `vyapti_unseen_150.json` | 132 | Earlier held-out suite. The file name says 150; the file holds 132 cases |
| `vyapti_stress_150.json` | 150 | Stress cases |
| `vyapti_adversarial_100.json` | 100 | Adversarial cases, with notes |
| `vyapti_adversarial_30.json` | 30 | Adversarial cases |
| `vyapti_natural_language_200.json` | 50 | Natural-language phrasing. The file name says 200; the file holds 50 cases |
| `vyapti_edge_cases.json` | 20 | Edge cases, with edge type |

Earlier suites were used while the scorer was being developed, so results on them are not held-out results.

## `results/`

`v10_full_validation_report.json`: scorer version `v10-rf07a-fix`, judge model `gpt-4.1`, 19 March 2026, on `vyapti_unseen_v4.json`. 115 of 120 correct (95.83%), 0 call errors. The file holds the expected category, predicted category and confidence for every case, and per-category totals.

| Category | Correct | Category | Correct |
|---|---|---|---|
| RF-01 | 9/10 | RF-07a | 10/10 |
| RF-02 | 10/10 | RF-07b | 10/10 |
| RF-03 | 8/10 | RF-08 | 10/10 |
| RF-04 | 10/10 | RF-09 | 10/10 |
| RF-05 | 9/10 | RF-10 | 9/10 |
| RF-06 | 10/10 | RF-11 | 10/10 |

Read this with `LIMITATIONS.md`, items 1 to 6. In particular, ten of the 120 cases overlap with exemplars in the judge prompt, and the result cannot yet be re-run end to end from this repository.

## `scorer/`

`llm_reasoning_judge.py`: the judge stage of the Vyāpti Reasoning Scorer, prompt version `v10-rf07a-fix`, published as it was run. The file is 676 lines. The prompt itself is the text returned by `_build_prompt` (lines 113 to 618): category definitions, disambiguation rules and worked exemplars. The judge model is set to `gpt-4.1`.

The full scorer has three stages: rule-based extraction of the inference structure, this LLM judge, and deterministic arbitration. Only the judge stage is published here. The file imports libraries from the original development platform and a database client, so it does not run on its own. A self-contained, tested package of all three stages will be added with the camera-ready paper.
