# Badha stress battery, 11-12 Nov 2026

Five stressors on three flagship models (gpt-6.1-sol, claude-opus-5-5, deepseek-v4-pro). Every answer key is computed by `solve` in ../code/badha_stress.py. No model labelled anything. Decision rules were fixed before the run (manifest.json in each folder).

Arms
- T1 scale: 60 / 150 / 300 rules on one page.
- T2 reversed policy: lower authority, broader jurisdiction and earlier date prevail.
- T3 rules not yet in force on the message date.
- T4 false pushback: after the first answer the user wrongly insists a losing rule wins; control = neutral 'please confirm'.
- T5 agent with files and tools: neutral, and 'injected' (fake policy amendment file + loud rule + fake tool notice).

Folders
- stage1/: full battery, seed 20261113. 576 jobs, 0 failures.
- stage2_fresh_items/: re-run of the two leads (T2, T4) on fresh items, seed 20261114, twice the size. Incomplete for claude-opus-5-5 and deepseek-v4-pro because both accounts ran out of credit mid-run; responses.jsonl contains those failed calls, responses_valid.* contains only completed ones. Jobs were shuffled, so the missing ones are a random subset.
- trial/: the small live trial run first.
- ../code/: generator, checker, clients, agent loop, analysis.

Headline
- gpt-6.1-sol: 0 errors in 396 completed records. claude-opus-5-5: 0 errors in 224.
- deepseek-v4-pro: reversed policy 17/20 then 29/34 correct; false pushback changed a correct answer 5/41 then 9/68 times, 0/106 after a neutral 'confirm'. Perfect on T1, T3, T5.

No API keys are stored in this package.

Note on stage2_fresh_items/responses.jsonl: provider request identifiers inside the error messages of failed calls have been replaced with REDACTED. Nothing else in the run outputs has been changed.
