# Prompts

`production/v10-rf07a-fix.txt` is the calibrated judge prompt the paper reports (v10, 66 worked examples, 31 rules),
rendered from the original source: the taxonomy definitions block is filled in and literal braces are single.
sha256 `54b87b1d8b2a70d373558786406726cbc56acb659d00dd389a746c671f2a74dd`.

Use it with `VYAPTI_PROMPT_DIR=prompts/production` and profile name `v10-rf07a-fix`.

**Note on an earlier error.** Two experiments run on 18 Aug 2026 copied this prompt out of its Python source without
evaluating it, so the model saw the literal placeholder `{self.taxonomy_prompt}` instead of the definitions, and doubled
braces. Their results are not used in the paper; corrected re-runs are. Both versions are compared in the camera-ready
results.

The `reference` profile (definitions only) is built into the package and needs no file.
