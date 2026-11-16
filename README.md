# NyāyaBench Research

Typed diagnosis of reasoning failures in large language models, using a taxonomy derived from the Navya-Nyāya theory of fallacious reasons (*hetvābhāsa*).

**Author:** Samarth Srivastava, independent researcher, India
**Release:** first public release, 16 November 2026
**Status:** research record. Curated from private development repositories. Some results are positive, some are negative, and both are reported here.

---

## The question

Most evaluations of language-model reasoning return a single score. This work asks a narrower question: when a model reasons badly, can the failure be given a *type* (for example, a reason that is too general, a reason defeated by stronger evidence, a claim about a subject that does not exist) in a way that is consistent and checkable?

The types come from Navya-Nyāya, a classical Indian school of logic and epistemology, which catalogues the ways an inferential reason (*hetu*) can fail. The work here turns that catalogue into a machine-readable taxonomy, builds scorers on it, and tests them.

## Paper

> Samarth Srivastava. *Beyond Scalar Judging: Typed Diagnosis of LLM Reasoning Failures with a Navya-Nyaya Taxonomy.* Accepted for oral presentation at ICON 2026 (Gauhati University, 20–23 December 2026). To appear in the ACL Anthology.

The camera-ready version is in preparation. The PDF will be linked here once the final version is published. See `CITATION.cff`.

## What is in this repository

| Folder | Contents | Status |
|---|---|---|
| [`taxonomy/`](taxonomy/) | The hetvābhāsa taxonomy as JSON, versions 1, 2 and 2.1 (13 reasoning-failure categories, RF-01 to RF-12 with RF-07 split in two) | v2.1 is the version used in the experiments. It has a known erratum; see the folder README. |
| [`vyapti-prototype/`](vyapti-prototype/) | The first Vyāpti scorer (March 2026): a rule-based, 12-step classification pipeline with its test file | Historical prototype. 9 of 9 tests pass. |
| [`nyayabench/`](nyayabench/) | Benchmark prompt sets, scorer test suites, the full VRS v10 judge prompt, and the per-case validation report for scorer v10 | Frozen sets with SHA-256 hashes. Prompt and results as run in March 2026. |
| [`badha/`](badha/) | Bādha: a follow-up experiment on override reasoning (which rule wins when rules conflict). Generator, checker, every prompt, every model reply, run manifests | Complete. Negative result for current frontier models. |
| [`LIMITATIONS.md`](LIMITATIONS.md) | Known weaknesses, corrections in progress, and what has not been validated | Read this before relying on any number. |

## Results at a glance

Every figure below can be recomputed from a file in this repository.

**1. Vyāpti Reasoning Scorer (VRS), version v10, held-out suite.**
115 of 120 cases classified into the expected category (95.83%), with `gpt-4.1` as the judge model, run on 19 March 2026. Per-category results range from 8/10 to 10/10.
Source: [`nyayabench/results/v10_full_validation_report.json`](nyayabench/results/v10_full_validation_report.json); suite: [`nyayabench/scorer-test-suites/vyapti_unseen_v4.json`](nyayabench/scorer-test-suites/vyapti_unseen_v4.json); judge prompt: [`nyayabench/scorer/llm_reasoning_judge.py`](nyayabench/scorer/llm_reasoning_judge.py).
This figure measures agreement with author-assigned labels on a small synthetic suite. It is not a measure of how well the scorer separates flawed from sound reasoning, where it performs poorly; see `LIMITATIONS.md`.

**2. Bādha probe (11 November 2026): 150 items, 7 versions each, 4 models, 4,200 calls.**

| Model | Pairs right (item and its twin) | Genuine ties escalated | Followed the losing rule, all three surface cues |
|---|---|---|---|
| claude-opus-5-5 | 150/150 | 100% | 0% |
| gpt-6.1-sol | 150/150 | 100% | 0% |
| deepseek-v4-pro | 150/150 | 100% | 0% |
| gpt-4.1 | 34/150 (22.7%) | 11.7% | 63.3% |

The three current flagship models were at ceiling. The text-only version of the benchmark therefore has no headroom for them and was stopped.
Source: [`badha/probe-2026-11-11/full_run/`](badha/probe-2026-11-11/full_run/).

**3. Bādha stress battery (12 November 2026): five harder conditions, three flagship models.**
`gpt-6.1-sol` and `claude-opus-5-5` made no errors on any condition, including a tool-using agent condition with planted false instructions. `deepseek-v4-pro` abandoned a correct answer after false user pushback in 14 of 109 cases (12.8%), against 0 of 106 after a neutral request to confirm, and answered 8 of 54 reversed-policy items wrongly.
Verdict against decision rules fixed before the run: a weak lead in one vendor, not a frontier benchmark. Bādha was closed as a frontier benchmark.
Source: [`badha/stress-battery-2026-11-12/`](badha/stress-battery-2026-11-12/).

## What is not in this release

| Item | Why |
|---|---|
| The extraction and arbitration stages of VRS, and the validation runner | To be added as a self-contained, tested package with the camera-ready paper. The judge stage, with the full prompt, is included. |
| Third-party datasets (LOGIC, MAFALDA) and the cross-taxonomy mapping outputs built on them | Redistribution terms are not confirmed. |
| The NyāyaBench leaderboard web application and its historical model rankings | A pilot built in March 2026 on a small prompt set. Its rankings are historical pilot measurements, not current model rankings. |
| Human annotation files | Under review for the camera-ready paper. |
| The Upādhi follow-up experiment (August 2026) | To be added after audit. |
| The paper PDF | Will be linked on publication. |

## How this work was produced

The author works through LLM-assisted development: code in this repository was written with LLM assistance under the author's direction, and run by the author. Curation and documentation of this repository were prepared with AI assistance (Claude). In the Bādha experiments every answer key is computed by a deterministic checker; no model labelled any item.

## Rights

© 2026 Samarth Srivastava. No open licence has been attached yet. Licences for the code, the datasets and the taxonomy will be added separately. Until then the material is published for reading and evaluation. For reuse, please open an issue.

## Contact

Please use the Issues tab of this repository.
