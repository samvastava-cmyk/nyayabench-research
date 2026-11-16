# Limitations and corrections in progress

This file lists what is weak, unverified or under correction in the work recorded in this repository. It is meant to be read before any result is relied on.

## Scorer (VRS)

1. **Specificity is low.** The paper reports specificity of 37.5% on a balanced set of 160 cases and 33.8% on 200 MAFALDA cases. The scorer flags many sound arguments as flawed. The 115/120 figure in the README measures something different: whether a flawed argument is assigned the expected category.
2. **The held-out suite is small and synthetic.** It has 120 cases, 10 per category, constructed for this project. Labels were assigned during construction. Ten of the 120 cases also appear verbatim among the exemplars in the judge prompt; the paper reports the figure with those removed as 104/109 (95.41%).
3. **Scorer versions differ across experiments.** The held-out validation used v10. The MAFALDA-200 run used v9. The 2,372-case LOGIC cross-taxonomy mapping used v8 and v9.
4. **Cross-taxonomy mappings are classifier outputs.** They are not independently adjudicated ground-truth labels.
5. **Only the judge stage of VRS is in this release.** `nyayabench/scorer/llm_reasoning_judge.py` holds the full v10 judge prompt as it was run, but the file depends on the original development platform and does not run on its own. The extraction and arbitration stages are not yet included, so the v10 result cannot be re-run end to end from this repository alone. The script that wrote `v10_full_validation_report.json` is also not in the source repository; the report file is the record of that run. The paper reports an independent re-run with the same per-category results.
6. **Independent expert review is outstanding.** Review of the taxonomy and of the labels by independent experts is a stated next step, not completed work.

## Taxonomy

7. **Source quotations in v2.1 are paraphrases.** A check in November 2026 against the GRETIL e-text of the *Tarka-Saṃgraha* found that the Sanskrit passages stored in `hetvabhasa_v2.1.json` are paraphrases, not verbatim quotations, although fields in that file mark them as verified. The same check found that nine categories are defined in the root text, not ten: RF-07b is derived from commentary. A corrected version 2.2 will be added with the camera-ready paper.
8. **Edition attribution is being verified.** The printed edition named in the v2.1 file is under verification.
9. **Not every category has a classical source.** RF-10 has no direct textual source. RF-11 is verified as a concept but inferred as a hetvābhāsa category.

## Paper

10. **Claims under revision.** The camera-ready version revises claims in the submitted version about the effect of worked exemplars versus definitions. Two follow-up experiments from August 2026 that bear on those claims were found to have been run with an incorrectly constructed prompt and are being re-run. Those claims should not be relied on until the final version is published.

## Leaderboard

11. **Pilot only.** The eight-model leaderboard was a pilot on a small prompt set. Mid-table positions were unstable when the prompt set was expanded, and one model's expansion run was incomplete because of API errors. It measures one dimension of reasoning as judged by one scorer, not overall model capability. It is not included in this release.

## Bādha

12. **Negative result.** Current flagship models were at ceiling on the text version and on the agent version. The only confirmed effects are in one vendor's model.
13. **One run per item, one model per vendor, default settings.** Gemini was not tested.
14. **The confirmation run is incomplete.** Two API accounts ran out of credit during the stage 2 re-run. `responses.jsonl` in that folder contains the failed calls; `responses_valid.*` contains only completed ones. Jobs were shuffled, so the missing ones are a random subset.
15. **Confound in the gpt-4.1 result.** That model answered in about four output tokens with no visible working; the other three reasoned first. The run cannot separate model age from the effect of reasoning.
16. **Twins are not balanced by deciding principle** in the probe; twins of tie items are mostly non-ties.
17. **The offline prototype cannot be re-run from this repository.** `badha/prototype/badha_precedence_prototype.py` compares against a separate rule-precedence engine that is not included. Its outputs are included.

## General

18. **Solo, part-time work.** One author, no institutional affiliation, no independent replication to date.
