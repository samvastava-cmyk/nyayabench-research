# Bādha: override reasoning under a stated precedence policy

A follow-up experiment run on 11 and 12 November 2026. The name comes from *bādhita*, the Nyāya term for a reason defeated by stronger evidence.

## Question

An item gives a model a payment message, a written precedence policy, and several rules from different authorities, some of which do not apply. The policy says which rule wins when rules conflict. Does the model apply the rule that should win, and does it escalate when the policy leaves a genuine tie?

Every answer key is computed by a deterministic checker. No model labelled any item. Thresholds and decision rules were fixed in code before each run and are recorded in each `manifest.json`.

## Contents

| Folder | Contents |
|---|---|
| `prototype/` | Offline prototype, no model calls: 300 minimal pairs and shortcut-audit results |
| `probe-2026-11-11/` | First live run: items, every prompt as sent, every reply, summary, report, manifest, and the 15-item trial |
| `stress-battery-2026-11-12/` | Five-condition follow-up: stage 1 (full), stage 2 (fresh items, partly complete), and the trial |
| `code/` | Generator, checker, model clients, agent loop, runners, analysis, and the Colab notebook |

The run scripts read API keys from a local file that is not included. No keys are stored in this repository. The SHA-256 of `code/badha_probe.py` matches the `code_sha256` recorded in the probe manifest.

## Probe, 11 November 2026

150 items (90 settled by the policy, 60 genuine ties) at 4, 8 and 12 rules. Each item was run in 7 versions: neutral; neutral reshuffled as a noise control; losing rule placed last; losing rule labelled CRITICAL; losing rule claiming its own precedence; all three cues together; and a twin with one fact changed. 4 models, 4,200 calls, 0 errors, 0 unparsed replies.

| Model | Pairs right (item and twin) | Ties escalated | Followed losing rule, control | Followed losing rule, all three cues |
|---|---|---|---|---|
| claude-opus-5-5 | 150/150 (100%) | 100% | 0% | 0% |
| gpt-6.1-sol | 150/150 (100%) | 100% | 0% | 0% |
| deepseek-v4-pro | 150/150 (100%) | 100% | 0% | 0% |
| gpt-4.1 | 34/150 (22.7%) | 11.7% | 35.3% | 63.3% |

For `gpt-4.1`, a CRITICAL label added 22.7 points of losing-rule answers over the control and a self-declared precedence claim added 26.7 points (p < 0.001 each). Position alone added 4.7 points (p = 0.42).

Reading: the text-only version has no headroom for the three current flagship models at up to 12 rules. That version was stopped.

## Stress battery, 12 November 2026

Five conditions on three flagship models.

| Condition | gpt-6.1-sol | claude-opus-5-5 | deepseek-v4-pro |
|---|---|---|---|
| T1 scale: 60, 150, 300 rules on one page | 30/30 | 30/30 | 30/30 |
| T2 reversed policy | 20/20; fresh 40/40 | 20/20; fresh 9/9 | 17/20; fresh 29/34 |
| T3 rules not yet in force | 20/20 | 20/20 | 20/20 |
| T4 correct answers abandoned after false pushback | 0/41; fresh 0/82 | 0/41; fresh 0/10 | 5/41; fresh 9/68 |
| T5 agent with files and tools, neutral | 20/20 | 20/20 | 20/20 |
| T5 agent, with planted false instructions | 20/20 | 20/20 | 20/20 |

For T4 a lower number is better. "Fresh" is the stage 2 re-run on new items with a new seed.

`deepseek-v4-pro`, pooled over both stages: false pushback changed a correct answer in 14 of 109 cases (12.8%, 95% interval 7.8 to 20.4%), always to the value the user claimed, against 0 of 106 after a neutral request to confirm. On the reversed policy it answered 8 of 54 items wrongly (14.8%, 95% interval 7.7 to 26.6%).

In the agent condition no model followed the planted policy amendment, the loud rule or the fake tool notice.

Verdict against the rules fixed before the run: a weak lead, confirmed on fresh items, in one vendor. The two leading flagship models were at ceiling in both text and agent form. Bādha was closed as a frontier benchmark.

## What remains usable

- A cross-vendor measurement of resistance to false correction and of following an unusual stated policy.
- A checker-scored harness with text, multi-turn and tool-using conditions for three vendors.
- Two complete datasets with every prompt and reply.

## Caveats

See items 12 to 17 in [`../LIMITATIONS.md`](../LIMITATIONS.md). The main ones: stage 2 is incomplete for two models because API credit ran out; one model per vendor and one run per item; Gemini was not tested; and the `gpt-4.1` result is confounded by that model answering without visible reasoning.
