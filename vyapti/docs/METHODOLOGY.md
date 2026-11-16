# Methodology

> **Camera-ready note (Nov 2026).** This document dates from the August 2026 submission. Where it differs from the camera-ready paper or [CHANGELOG.md](../CHANGELOG.md), those take precedence; in particular the specificity analysis, the textual status of the taxonomy, and the scorer versions behind the corpus-level results were corrected.


```
text ──▶ [1] rule-based extraction ──▶ [2] LLM judge ──▶ [3] arbitration ──▶ label
         deterministic, free            one API call     deterministic, logged
```

---

## Stage 1 — structural extraction

Recovers the Nyāya triple from surface text:

- **pakṣa** — the subject the argument is about
- **hetu** — the reason offered
- **sādhya** — what is being established

Implementation: `src/vyapti/extract.py`. Ordered connective patterns (`because`, `due to`, `since`, `therefore`, `given that`, `if/then`), a two-sentence adjacency fallback, and a copula-boundary heuristic for the subject. Contrastive clauses (`but`, `however`, `except`, `although`) are collected separately as candidate blockers.

Its output is a **hint**, never a verdict. The judge is explicitly instructed to trust the full text when the two conflict, because the extractor will compress or misplace a clause on anything longer than two sentences.

**What is deliberately absent.** The Phase 1 extractor matched 74 content-bearing string literals against input text — specific benchmark sentences. None are reproduced. `tests/test_core.py` fails the build if any return. Measurement of what that tuning was worth: [LIMITATIONS.md](LIMITATIONS.md) §5.

---

## Stage 2 — the LLM judge

One call. A prompt profile renders taxonomy definitions, the input text, the extracted structure, and an output contract; the model returns strict JSON.

```json
{"rf_code": "RF-07a", "confidence": 0.82, "diagnosis": "..."}
```

### Prompt profiles

A profile is the difference between a taxonomy and a classifier.

| Profile | Contents | Distributed |
|---|---|---|
| `reference` | Taxonomy definitions + output contract. No exemplars, no conditional rules. | **Yes** |
| `production` (`v10-rf07a-fix`) | 676 lines. 66 few-shot exemplars, 31 conditional disambiguation rules. | **No** — see [prompts/README.md](../prompts/README.md) |

Profiles are loaded by name from `$VYAPTI_PROMPT_DIR`. Requesting an unavailable profile **raises** rather than falling back to `reference` — running the wrong profile without knowing is the exact class of error this codebase is built against.

Every profile is SHA-256 hashed and the hash is written into every result record, so any figure can be traced back to the exact prompt that produced it.

### Failure handling

This is the part that matters most, and it is where Phase 1 lost real work.

| Condition | Phase 1 | Here |
|---|---|---|
| Judge unreachable | returned `{"rf_code": "NONE"}` silently | `UnavailableJudgeError` |
| Unparseable response | coerced to `NONE` | `MalformedJudgeResponseError` |
| Unrecognised label | coerced to `NONE` | rejected by `JudgeVerdict` |
| Empty completion | recorded as a result | raises |

Each of the old behaviours is indistinguishable from a genuine "this argument is sound" verdict — so each one *inflated the apparent sound-argument rate*, in the one metric this project most needs to be honest about. A full August run was invalidated by the first row before anyone noticed.

### Provider handling

`src/vyapti/client.py` calls OpenAI, Anthropic, Google and DeepSeek directly over HTTPS. No broker package, no shared key.

**Temperature is a required argument** and is emitted in every request payload for every provider. There is no path through this module where temperature is omitted. The Anthropic omission in the Phase 1 portability run is a documented confound in the paper; it cannot recur here by construction.

Retries: exponential backoff with jitter on 429 and 5xx, six attempts. 4xx raises immediately — a bad key should stop a run, not retry into a rate limit.

---

## Stage 3 — deterministic arbitration

Seven precedence rules resolve predictable judge–rule disagreements. Implementation: `src/vyapti/arbitration.py`.

Each rule is a *structural* claim about argument shape, applied identically to every input:

| Rule | Redirect | When |
|---|---|---|
| R1 | RF-01 → RF-02 | the evidence base is a single unique case |
| R2 | RF-07a → RF-01 | a weak tendency is stretched to certainty |
| R3 | RF-01 → RF-07a | a general rule applied without its conditions |
| R4 | RF-01/07a → RF-07b | a specific contextual blocker prevents the rule here |
| R5 | RF-03/04/01 → RF-08 | stronger evidence decisively defeats a weaker claim |
| R6 | RF-03/01/06 → RF-10 | the contradiction depends on the act of asserting |
| R7 | RF-07a/07b/09 → RF-11 | the causal process starts and is explicitly interrupted |

Two invariants:

**Every override is logged.** A final label differing from the judge's verdict always carries an `ArbitrationStep` naming the rule and its rationale. A silent override is unauditable.

**NONE is never overridden into a failure.** Arbitration redistributes *among* failure types. Allowing it to manufacture failures would attack specificity — the one number Phase 2 exists to move.

Arbitration can be disabled (`use_arbitration=False`, `--no-arbitration`) to measure the judge unaided. The ablation arms need that comparison.

---

## Running an experiment

`src/vyapti/runner.py`. Three rules, each bought with a lost Phase 1 run:

1. **Smoke test first.** Three known cases, before any suite. Aborts in seconds if the judge is unreachable or the profile isn't being applied — rather than after 3,000 calls. The third case is a *sound* argument, because a profile that cannot say NONE is a profile that will silently fail the thing being measured.
2. **Append and flush per case.** JSON Lines, `fsync` after every write. Re-running the same output path resumes from completed case IDs. The August runs were lost twice.
3. **Never truncate.** Full response text, finish reason, prompt and completion tokens, latency. Three-hundred-character previews cost the Phase 1 human-verification study.

Concurrency is a semaphore over async HTTP — 3,000 calls in roughly fifteen minutes at concurrency 8, rather than two hours serial.

---

## Metrics

| Function | Reports |
|---|---|
| `binary_metrics` | precision, recall, **specificity**, F1, accuracy over flag-vs-sound |
| `typed_accuracy` | exact-label accuracy on correctly flagged failures, per category |
| `label_share` | prediction share per label — the RF-01 sink measurement |
| `confidence_split` | mean judge confidence on false positives vs true negatives |

`confidence_split` is not a standard evaluation metric and exists for one reason: it is what proved confidence thresholding cannot fix specificity (0.906 vs 0.946). Re-measure it every arm — if that gap ever widens materially, thresholding becomes viable again.

Positive class throughout is "this argument has a structural failure". Specificity is reported explicitly and prominently because it is the defect.

---

## Contamination auditing

`src/vyapti/contamination.py`, driven by `scripts/audit_contamination.py`. N-gram overlap between a suite and a reference corpus — normally the prompt profile in use.

Standing Phase 2 rule: **no new test set is reported on until it has been audited here.** The paper's 8.3% v4 contamination figure was found retrospectively. That is the last time.
