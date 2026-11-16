"""Offline tests. No network, no API key required."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vyapti import (
    InferenceStructure,
    MalformedJudgeResponseError,
    RFCode,
    arbitrate,
    extract,
    load_profile,
    load_taxonomy,
    parse_verdict,
)
from vyapti.contamination import audit_suite, ngrams, overlap_report, tokenize

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# Taxonomy
# --------------------------------------------------------------------------


def test_taxonomy_loads_and_self_validates():
    tax = load_taxonomy()
    assert len(tax) == 13
    assert tax.version == "2.2.0"
    problems = tax.validate()
    assert problems == [], f"taxonomy self-check failed: {problems}"


def test_verified_and_inferred_are_both_declared():
    """The paper's credibility rests on this distinction being explicit."""
    tax = load_taxonomy()
    verified = {c.id for c in tax.verified()}
    inferred = {c.id for c in tax.inferred()}
    assert verified and inferred
    assert verified.isdisjoint(inferred)
    # RF-10 has no sūtra source and must never be marked verified.
    assert "RF-10" in inferred
    assert "RF-01" in verified


def test_every_verified_category_carries_a_source_quote():
    for c in load_taxonomy().verified():
        assert c.source_quote_english, f"{c.id} claims VERIFIED with no quote"
        assert c.source_text, f"{c.id} claims VERIFIED with no citation"


# --------------------------------------------------------------------------
# Stage 1 — extraction
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,connective",
    [
        ("The mountain has fire, because it is knowable.", "because"),
        ("He is unreliable due to his background.", "due to"),
        ("It rained heavily, therefore the match was cancelled.", "therefore"),
        ("Given that the road is wet, it must have rained.", "given that"),
    ],
)
def test_extraction_finds_the_connective(text, connective):
    s = extract(text)
    assert s.connective == connective
    assert s.reason and s.conclusion


def test_extraction_degrades_gracefully():
    s = extract("Fire.")
    assert s.connective is None
    assert s.confidence < 0.5


def test_extraction_has_no_benchmark_literals():
    """Regression guard against re-importing Phase 1's item-specific tuning.

    Checks executable code only — the module docstring names the removed
    literals on purpose, as documentation of what was taken out.
    """
    import ast

    path = ROOT / "src" / "vyapti" / "extract.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    tree.body = [n for n in tree.body if not (
        isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
        and isinstance(n.value.value, str)
    )]
    src = ast.unparse(tree)
    banned = [
        "antibiotics cure infections",
        "every fire produces smoke",
        "sea level atmospheric pressure",
        "MDR1 overexpression",
        "peanut allergy",
        "studying once ensures top scores",
    ]
    for b in banned:
        assert b.lower() not in src.lower(), f"benchmark literal {b!r} leaked back into stage 1"


# --------------------------------------------------------------------------
# Stage 2 — verdict parsing
# --------------------------------------------------------------------------


def test_parses_clean_json():
    v = parse_verdict('{"rf_code": "RF-01", "confidence": 0.9, "diagnosis": "over-wide"}')
    assert v.rf_code is RFCode.RF_01
    assert v.confidence == 0.9


def test_parses_json_embedded_in_prose():
    v = parse_verdict('Here you go:\n{"rf_code":"RF-07a","confidence":0.5,"diagnosis":"x"}\nDone.')
    assert v.rf_code is RFCode.RF_07A


def test_empty_response_raises_rather_than_returning_none():
    """The Phase 1 bug, in one assertion."""
    with pytest.raises(MalformedJudgeResponseError):
        parse_verdict("")


def test_unparseable_response_raises():
    with pytest.raises(MalformedJudgeResponseError):
        parse_verdict("I think this argument is fine, honestly.")


def test_unknown_label_raises_and_is_not_coerced_to_none():
    with pytest.raises(MalformedJudgeResponseError):
        parse_verdict('{"rf_code": "RF-99", "confidence": 0.5}')


def test_out_of_range_confidence_raises():
    with pytest.raises(MalformedJudgeResponseError):
        parse_verdict('{"rf_code": "RF-01", "confidence": 4.2}')


def test_label_case_drift_is_tolerated():
    assert parse_verdict('{"rf_code":"rf-07A","confidence":0.5}').rf_code is RFCode.RF_07A


# --------------------------------------------------------------------------
# Stage 3 — arbitration
# --------------------------------------------------------------------------


def test_none_is_never_overridden_into_a_failure():
    """Arbitration must not attack specificity."""
    text = "Only this one person said so, and it always works without exception."
    final, steps = arbitrate(text, RFCode.NONE)
    assert final is RFCode.NONE
    assert steps == []


def test_singleton_cue_redirects_rf01_to_rf02():
    final, steps = arbitrate(
        "This works, because only this one company has ever tried it.", RFCode.RF_01
    )
    assert final is RFCode.RF_02
    assert steps and steps[0].rule_id == "R1-singleton"


def test_arbitration_can_be_disabled_for_ablation():
    final, steps = arbitrate(
        "This works, because only this one company has ever tried it.",
        RFCode.RF_01,
        enabled=False,
    )
    assert final is RFCode.RF_01
    assert steps == []


def test_every_override_is_logged():
    for label in (RFCode.RF_01, RFCode.RF_03, RFCode.RF_07A):
        final, steps = arbitrate(
            "The measured data contradicts the claim, and only one person disagrees.", label
        )
        if final != label:
            assert steps, f"{label} -> {final} happened with no logged step"
            assert steps[0].rationale


# --------------------------------------------------------------------------
# Prompt profiles
# --------------------------------------------------------------------------


def test_reference_profile_renders_and_is_hashable():
    p = load_profile("reference")
    out = p.render("Sound is eternal, because it is audible.", extract("Sound is eternal, because it is audible."))
    assert "RF-01" in out and "strict JSON" in out
    assert len(p.sha256) == 64


def test_unknown_profile_raises_rather_than_falling_back():
    with pytest.raises(FileNotFoundError):
        load_profile("production-v10")


def test_reference_profile_contains_no_exemplars():
    """The reference profile is definitions + contract only, by construction."""
    body = load_profile("reference").template
    assert "INPUT:" not in body and "Example" not in body


# --------------------------------------------------------------------------
# Data integrity
# --------------------------------------------------------------------------


def test_manifest_matches_the_files_on_disk():
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    for suite in manifest["suites"]:
        path = ROOT / suite["file"]
        assert path.exists(), f"{suite['name']} missing at {path}"
        n = sum(1 for line in path.open(encoding="utf-8") if line.strip())
        assert n == suite["n"], f"{suite['name']}: manifest says {suite['n']}, file has {n}"


def test_every_typed_case_has_a_label_in_the_taxonomy():
    tax_ids = set(load_taxonomy().ids) | {"NONE"}
    for path in (ROOT / "data" / "suites").glob("*.jsonl"):
        for line in path.open(encoding="utf-8"):
            if not line.strip():
                continue
            row = json.loads(line)
            assert row["label"] in tax_ids, f"{path.name}:{row['id']} has label {row['label']!r}"


def test_the_none_deficit_is_real_and_documented():
    """The defect, asserted. If this ever fails, the README needs rewriting."""
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    typed = [s for s in manifest["suites"] if s["kind"] == "typed"]
    total = sum(s["n"] for s in typed)
    none_total = sum(s["none_count"] for s in typed)
    assert none_total / total < 0.05, "NONE share has risen — update docs/RESULTS.md"


# --------------------------------------------------------------------------
# Contamination
# --------------------------------------------------------------------------


def test_ngram_overlap_detects_verbatim_reuse():
    ref = {tuple(tokenize("the mountain has fire because it is knowable"))[i : i + 6]
           for i in range(4)}
    rep = overlap_report("The mountain has fire because it is knowable.", ref, n=6)
    assert rep["overlap_pct"] > 0


def test_unrelated_text_shows_no_overlap():
    ref = set(ngrams(tokenize("completely unrelated sentence about maritime shipping law"), 6))
    rep = overlap_report("The mountain has fire because it is knowable.", ref, n=6)
    assert rep["shared"] == 0


def test_audit_runs_over_a_real_suite():
    out = audit_suite(
        ROOT / "data" / "suites" / "external_20.jsonl",
        reference_texts=["a sentence that appears nowhere in the suite at all"],
        n=6,
    )
    assert out["n_cases"] == 20
    assert out["n_flagged"] == 0


def test_textual_status_matches_paper():
    """Camera-ready Table 1: nine defined in the root text, RF-07b derived, RF-09/11 inferred, RF-10 none."""
    tax = load_taxonomy()
    assert {c.id for c in tax.verified()} == {"RF-01", "RF-02", "RF-03", "RF-04", "RF-05", "RF-06", "RF-07a", "RF-08", "RF-12"}
    status = {c.id: c.raw["textual_status"] for c in tax}
    assert status["RF-07b"] == "DERIVED_FROM_COMMENTARY" and status["RF-10"] == "NO_TEXTUAL_SOURCE"
    assert status["RF-09"] == status["RF-11"] == "INFERRED_CLASSICAL_DOCTRINE"
    for c in tax.verified():
        assert c.raw["source_passage_verbatim"], c.id
