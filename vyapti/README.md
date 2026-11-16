# Vyāpti

**A typed classifier for structural reasoning failure, built on the Navya-Nyāya theory of fallacious reasons (*hetvābhāsa*).**

Code, taxonomy, prompt and data for:

> Samarth Srivastava. 2026. *Beyond Scalar Judging: Typed Diagnosis of LLM Reasoning Failures with a Navya-Nyāya Taxonomy.* In Proceedings of the 23rd International Conference on Natural Language Processing (ICON 2026).

---

## What this is, and what it is not

Given an argument that is **already known or judged to be flawed**, Vyāpti names the kind of structural failure: an over-wide reason, a reason peculiar to one case, a rule applied without a condition it needs, and so on. On the paper's held-out suite of 120 flawed arguments it assigns the expected label in 95.8% of cases (95.4% after removing ten cases that overlap the prompt's examples), and that figure reproduces.

It is **not a detector**. Asked whether a text contains a failure at all, it says yes to most sound arguments; specificity is low and confidence does not separate its errors (paper, Table 4 and Section 5.4). Do not use it to screen text, gate content or score models unattended. Use it to type failures that a person or another system has already found.

Two further limits are measured in the paper. The 95.8% is agreement with the author's labels on the author's arguments, and the external-validation section reports how much survives on text written by others. And fallacies of relevance (ad hominem, ad populum, appeals to emotion) have no *hetvābhāsa* counterpart; the classifier sends them to RF-01.

## The taxonomy

`taxonomy/hetvabhasa_v2.2.json`: thirteen categories, each with Sanskrit term, IAST, English name, formal and intuitive definitions, and an explicit textual status.

| Code | Category | Textual status |
|---|---|---|
| RF-01 | Erratic, over-wide reason (*Sādhāraṇa*) | defined in the root text (TS 53) |
| RF-02 | Erratic, over-narrow reason (*Asādhāraṇa*) | defined in the root text (TS 53) |
| RF-03 | Contradictory reason (*Viruddha*) | defined in the root text (TS 54) |
| RF-04 | Counterbalanced reason (*Satpratipakṣa*) | defined in the root text (TS 55) |
| RF-05 | Non-existent locus (*Āśrayāsiddha*) | defined in the root text (TS 56) |
| RF-06 | Non-existent property (*Svarūpāsiddha*) | defined in the root text (TS 56) |
| RF-07a | Missing universal qualifier (*Sopādhika*) | defined in the root text (TS 56) |
| RF-07b | Missing contextual qualifier | derived from commentary on TS 56 |
| RF-08 | Defeated by stronger evidence (*Bādhita*) | defined in the root text (TS 57) |
| RF-09 | Explained by another cause (*Anyathāsiddha*) | classical doctrine; promotion to a *hetvābhāsa* type is ours |
| RF-10 | Performative self-refutation | no textual source |
| RF-11 | Blocked causal chain (*Pratibandha*) | classical doctrine; promotion to a *hetvābhāsa* type is ours |
| RF-12 | Erratic, no example possible (*Anupasaṃhārin*) | defined in the root text (TS 53); not in the classifier |

TS = *Tarka-Saṃgraha* of Annambhaṭṭa, section numbers of the GRETIL e-text. For the nine root-text categories the file's `source_passage_verbatim` field quotes the passage exactly; `python scripts/audit_taxonomy.py` lists everything and `pytest` checks the statuses. **Correction:** version 2.1 described ten categories as verbatim-attested and stored Sanskrit fields that paraphrased the text. See [CHANGELOG.md](CHANGELOG.md).

## How it works

```
text ──▶ [1] rule-based extraction ──▶ [2] LLM judge ──▶ [3] arbitration ──▶ label
         subject / reason / conclusion   typed verdict     7 deterministic overrides
```

The judge sees the argument, not any prompt that produced it. Arbitration never turns a NONE verdict into a failure. (The original research code could; this release cannot.) Details: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Install and run

```bash
git clone <this repository>
cd vyapti
pip install -e ".[analysis,dev]"
python scripts/fetch_external.py   # fills in LOGIC and MAFALDA texts locally (see Data)
pytest tests/ -q                   # offline tests, no API key needed

cp .env.example .env               # add your provider key(s)
export VYAPTI_PROMPT_DIR=prompts/production
vyapti-run data/suites/unseen_v4.jsonl -o runs/v4.jsonl
```

Two prompt profiles ship:

- `v10-rf07a-fix` in `prompts/production/`: the calibrated prompt the paper reports (66 worked examples, 31 rules). See [prompts/README.md](prompts/README.md), including a note on an earlier error in how two August experiments built this prompt.
- `reference`, built into the package: the twelve definitions and nothing else. This is the paper's definitions-only control.

## Data

| Group | Files | Items |
|---|---|---|
| Typed suites (12 files) | `data/suites/*.jsonl` | 1,069 rows: 1,028 written for this project, 40 MAFALDA references in `unseen_v5_balanced`, 1 empty row in `edge_cases_20` |
| LOGIC cross-map samples | `data/crossmap/*.jsonl` | 682 references |
| MAFALDA evaluation set | `data/external/mafalda_200.jsonl` | 200 references |
| Elicitation prompts | `data/generation/*.jsonl` | 100 |

Neither LOGIC (Jin et al., 2022) nor MAFALDA (Helwe et al., 2024) states a licence, so their texts are **not** redistributed here. Each item carries its row in the original release and a hash. `scripts/fetch_external.py` downloads both datasets at pinned commits, fills in the texts, and verifies every row.

Of the 1,028 suite items written for this project, 17 are sound arguments, and the held-out v4 suite contains none. That is a known defect and the main reason its accuracy figure says nothing about detection. [docs/DATA_CARD.md](docs/DATA_CARD.md) has provenance and known problems. Development suites (everything except `unseen_v4` and `unseen_v5_balanced`) were reached by hard-coded sentence matches in the original rule layer, and figures on them should not be cited.

## Results

`results/` holds the cross-taxonomy count matrices behind the paper's non-redundancy
analysis: `crossmap_logic_2372.json` (2,372 LOGIC arguments, scorer v8-v9) and a 500-case
summary. They contain counts only, no third-party text.

Run `python3 ../verify_results.py` from the repository root to recompute the paper's
headline figures from these files, including the 68.3% non-redundancy result and the
scope-boundary table.

The camera-ready runs (v10 on MAFALDA, the definitions-only controls, the
external-validation re-run and the sound-exemplar ladder) are not yet here; they will be
added under `results/camera_ready/` when the camera-ready paper is final. The eight-model
leaderboard is deliberately not included — see `LIMITATIONS.md` item 11 in the repository
root.

## Citing

```bibtex
@inproceedings{srivastava-2026-beyond,
  title     = {Beyond Scalar Judging: Typed Diagnosis of {LLM} Reasoning Failures
               with a {N}avya-{N}y{\=a}ya Taxonomy},
  author    = {Srivastava, Samarth},
  booktitle = {Proceedings of the 23rd International Conference on Natural
               Language Processing (ICON)},
  year      = {2026}
}
```

## Licence

Code: MIT ([../LICENSE](../LICENSE)). Taxonomy, prompts and the suites written for this project: CC BY 4.0 ([../LICENSE-DATA](../LICENSE-DATA)). The Sanskrit passages quoted in the taxonomy are short quotations from the *Tarka-Saṃgraha*, a public-domain seventeenth-century work; the GRETIL e-text is credited as the copy consulted. LOGIC and MAFALDA are referenced, not included.
