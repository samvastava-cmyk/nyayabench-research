# Changelog

## 2026-11-16, second release

Added, so that the figures in this repository can be checked by a reader rather
than taken on trust:

- **`verify_results.py`** — recomputes every headline figure from the released
  files, in one command, with no dependencies and no API calls. It prints each
  recomputed value beside the value claimed in the paper and exits non-zero on
  any disagreement. Twelve checks.
- **`vyapti/`** — the Vyapti pipeline as a self-contained, installable package:
  all three stages (extraction, LLM judge, arbitration), the calibrated v10
  prompt as a rendered text file, the definitions-only reference profile used as
  the paper's control, the evaluation suites, the cross-taxonomy result files and
  30 offline tests. This closes the gap noted in the first release, where only
  the judge stage was published and the v10 result could not be re-run end to
  end.
- **`taxonomy/hetvabhasa_v2.2.json`** — the corrected taxonomy. The Sanskrit
  passages are now quoted exactly from the GRETIL e-text of the
  *Tarka-Samgraha*, each with its section reference, and every category carries
  an explicit `textual_status`. The v2.1 paraphrases are kept under a renamed
  field for provenance. The definitions the scorer uses are byte-identical to
  v2.1, so this changes the taxonomy's documentation and not its behaviour.
- **`LICENSE`** (MIT, code) and **`LICENSE-DATA`** (CC BY 4.0, taxonomy and
  data, with three stated exceptions). The first release carried no licence.
  The quoted Sanskrit sentences are treated as what they are — short quotations
  from a public-domain work — with the GRETIL e-text credited as the copy
  consulted rather than as a licensor, so no non-commercial or share-alike term
  is imported into this repository.

Disclosed for the first time in `LIMITATIONS.md`:

- **Item 18.** The rule layer of the original development code contained literal
  string matches on 74 benchmark sentences. They reach 2 of the 120 held-out
  cases, so the 115/120 figure survives, but figures on the development suites
  are compromised and are not cited. The package in `vyapti/` contains none of
  them.
- **Item 19.** The original arbitration stage could overturn a NONE verdict into
  a failure code, which inflates apparent failure rates. The released package
  never does this.

Both items are also disclosed in the camera-ready paper.

## 2026-11-16, first release

Initial public release: taxonomy versions 1 to 2.1, the March 2026 Vyapti
prototype scorer, the NyayaBench prompt sets and scorer test suites, the VRS v10
judge prompt and its validation report, and the Badha experiment with every
prompt and model reply.
