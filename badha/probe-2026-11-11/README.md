# Badha probe dataset, 11 Nov 2026

Question tested: given a written precedence policy, do models follow a losing rule that is placed last, labelled CRITICAL or claims its own precedence, and do they escalate genuine ties?

- 150 items (90 settled by the policy, 60 genuine ties) at 4, 8 and 12 rules, each in 7 versions = 1,050 prompts per model.
- Models: gpt-6.1-sol, gpt-4.1 (OpenAI), claude-opus-5-5 (Anthropic), deepseek-v4-pro (DeepSeek). 4,200 calls, 0 errors, 0 unparsed replies.
- Every answer key is computed by the checker in ../code/badha_probe.py (function `oracle`). No model labelled anything.
- Thresholds were fixed in the code before the run (see full_run/manifest.json).

Versions: N neutral; N2 neutral reshuffled (noise control); P losing rule last; L losing rule labelled CRITICAL; S losing rule claims precedence; X all three; T twin with one fact changed.

Files
- full_run/items.json: the 150 items with rules, answer, losing rule and twin.
- full_run/prompts.jsonl: all 1,050 prompts exactly as sent, with answer keys.
- full_run/responses.jsonl and responses.csv: every reply in full, parsed answer, token counts.
- full_run/summary_by_model_and_version.csv: accuracy and losing-rule rate per model and version.
- full_run/report.txt and report.json: the printed analysis and verdict.
- full_run/manifest.json: models, seed, thresholds, code hash, start time.
- trial_run/: the 15-item trial run made first.
- ../code/: generator, checker, runner, analysis, and the Colab notebook version.

No API keys are stored in this package.
