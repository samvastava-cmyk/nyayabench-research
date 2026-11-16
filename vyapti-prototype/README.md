# Vyāpti prototype scorer (March 2026)

The first implementation of the Vyāpti scorer: a rule-based pipeline that walks the 12-step decision flowchart in the taxonomy and returns typed reasoning-failure classifications for a parsed inference.

This is a historical prototype. The later scorer used for the results in `nyayabench/` (VRS v10) has a different design: rule-based extraction, an LLM judge, then deterministic arbitration. Its judge stage, with the full prompt, is in `../nyayabench/scorer/`.

| Path | Contents |
|---|---|
| `ontology/hetvabhasa_v2.1.json` | The taxonomy file the pipeline loads (identical to `taxonomy/hetvabhasa_v2.1.json`) |
| `scorer/pipeline.py` | Inference parser, 12 step classifiers, pipeline and report formatter |
| `tests/test_pipeline.py` | Nine tests |

## Running the tests

Python 3, standard library only.

```bash
cd vyapti-prototype
python3 tests/test_pipeline.py
```

Expected output ends with `RESULTS: 9 passed, 0 failed, 9 total`.

## Scope

The nine tests check that the pipeline loads the taxonomy and behaves as designed on hand-written examples. They are not an accuracy evaluation.
