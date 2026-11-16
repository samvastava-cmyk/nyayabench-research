# NyāyaBench Research

Typed diagnosis of reasoning failures in large language models, using a taxonomy derived from the Navya-Nyāya theory of fallacious reasons (*hetvābhāsa*).

**Author:** Samarth Srivastava, independent researcher, India
**Release:** first public release, 16 November 2026
**Status:** research record. Curated from private development repositories. Some results are positive, some are negative, and both are reported here.
**Changes:** see [`CHANGELOG.md`](CHANGELOG.md).

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
| [`taxonomy/`](taxonomy/) | The hetvābhāsa taxonomy as JSON, versions 1 to 2.2 (13 reasoning-failure categories, RF-01 to RF-12 with RF-07 split in two) | v2.1 was used in the experiments; **v2.2 corrects its source attributions** and carries the Sanskrit passages verbatim. Definitions are byte-identical, so no result changes. |
| [`vyapti/`](vyapti/) | The pipeline as an installable package: all three stages, the calibrated v10 prompt, the definitions-only control, the evaluation suites, the cross-taxonomy results, 30 offline tests | Runnable. `pip install -e .` then `pytest`. Added November 2026. |
| [`vyapti-prototype/`](vyapti-prototype/) | The first Vyāpti scorer (March 2026): a rule-based, 12-step classification pipeline with its test file | Historical prototype. 9 of 9 tests pass. |
| [`nyayabench/`](nyayabench/) | Benchmark prompt sets, scorer test suites, the full VRS v10 judge prompt, and the per-case validation report for scorer v10 | Frozen sets with SHA-256 hashes. Prompt and results as run in March 2026. |
| [`badha/`](badha/) | Bādha: a follow-up experiment on override reasoning (which rule wins when rules conflict). Generator, checker, every prompt, every model reply, run manifests | Complete. Negative result for current frontier models. |
| [`LIMITATIONS.md`](LIMITATIONS.md) | Known weaknesses, corrections in progress, development artifacts found by audit, and what has not been validated | Read this before relying on any number. 20 items. |
| [`verify_results.py`](verify_results.py) | Recomputes every figure below from the released files, in one command | `python3 verify_results.py`. No dependencies, no API calls. 12 checks. |

## Results at a glance

Every figure below can be recomputed from a file in this repository. To check them
yourself, clone the repository and run:

```
python3 verify_results.py
```

It needs no dependencies and makes no API calls. It recomputes each number, prints it
beside the value claimed here, and exits non-zero if any disagree.

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
| The original validation runner | The script that produced `v10_full_validation_report.json` was not kept. The report file is the record of that run. The pipeline in `vyapti/` reproduces the method, with the two differences in `LIMITATIONS.md` items 18 and 19. |
| The texts of the third-party datasets (LOGIC, MAFALDA) | Neither states a licence, so neither is redistributed. `vyapti/data/` carries row references and hashes; `vyapti/scripts/fetch_external.py` fetches the texts from the original repositories at pinned commits and verifies every row. The cross-taxonomy **count matrices** built on them are included, and contain no third-party text. |
| The NyāyaBench leaderboard web application and its historical model rankings | A pilot built in March 2026 on a small prompt set. Its rankings are historical pilot measurements, not current model rankings. |
| Human annotation files | Under review for the camera-ready paper. |
| The Upādhi follow-up experiment (August 2026) | To be added after audit. |
| The paper PDF | Will be linked on publication. |

## How this work was produced

The author works through LLM-assisted development: code in this repository was written with LLM assistance under the author's direction, and run by the author. Curation and documentation of this repository were prepared with AI assistance (Claude). In the Bādha experiments every answer key is computed by a deterministic checker; no model labelled any item.

## Rights

© 2026 Samarth Srivastava.

- **Code** — MIT, see [`LICENSE`](LICENSE).
- **Taxonomy, prompts, benchmark sets, test suites, Bādha items and run records, documentation** — CC BY 4.0, see [`LICENSE-DATA`](LICENSE-DATA).

Three exceptions are stated in `LICENSE-DATA`: the Sanskrit passages quoted in the taxonomy
are short quotations from the *Tarka-Saṃgraha*, a public-domain seventeenth-century work, with
the GRETIL e-text credited as the copy consulted; LOGIC and MAFALDA are referenced rather than
included; and the code is MIT rather than CC BY.

If you use this work, please cite the paper — see [`CITATION.cff`](CITATION.cff).

## Contact

Please use the Issues tab of this repository.
