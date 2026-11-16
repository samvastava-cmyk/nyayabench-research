"""
Test suite for Vyāpti Scorer Pipeline
======================================

Tests the 12-step pipeline with rule-based backends (no LLM API needed).
Verifies the exact regression cases from v2.0/v2.1 testing.
"""

import sys
import os
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scorer.pipeline import (
    ScorerPipeline,
    InferenceStructure,
    audit_inference,
)

ONTOLOGY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ontology", "hetvabhasa_v2.1.json"
)


def test_ontology_loads():
    """Test that the ontology JSON loads and has all 13 categories."""
    pipeline = ScorerPipeline(ontology_path=ONTOLOGY_PATH)
    assert len(pipeline.ontology.categories) == 13, \
        f"Expected 13 categories, got {len(pipeline.ontology.categories)}"
    
    expected_codes = [
        "RF-01", "RF-02", "RF-03", "RF-04", "RF-05", "RF-06",
        "RF-07a", "RF-07b", "RF-08", "RF-09", "RF-10", "RF-11", "RF-12"
    ]
    for code in expected_codes:
        assert code in pipeline.ontology.categories, f"Missing category: {code}"
    
    print("✅ Ontology loads correctly with all 13 categories")


def test_rf05_entity_hallucination():
    """
    RF-05: Non-existent subject.
    Dr. Sarah Chen doesn't exist → RF-05 should fire at Step 1.
    """
    result = audit_inference(
        text="Dr. Sarah Chen's 2019 Stanford study shows intermittent fasting reduces dementia risk by 47%.",
        paksha="Dr. Sarah Chen's 2019 Stanford study",
        hetu="intermittent fasting was studied",
        vyapti="fasting studies prove health benefits",
        sadhya="fasting reduces dementia risk by 47%",
        entity_lookup=lambda e: False,  # Dr. Chen doesn't exist
        ontology_path=ONTOLOGY_PATH
    )
    
    assert result["total_failures_detected"] >= 1
    assert result["primary_failure"]["code"] == "RF-05", \
        f"Expected RF-05, got {result['primary_failure']['code']}"
    
    print("✅ RF-05 (Entity Hallucination): Correctly detected fabricated subject")


def test_rf06_property_hallucination():
    """
    RF-06: Non-existent property.
    Eiffel Tower exists but 'built in 1820' is factually false.
    """
    result = audit_inference(
        text="The Eiffel Tower was built in 1820, therefore it pre-dates the Industrial Revolution.",
        paksha="Eiffel Tower",
        hetu="built in 1820",
        vyapti="things built before 1830 pre-date the Industrial Revolution",
        sadhya="pre-dates the Industrial Revolution",
        entity_lookup=lambda e: True,  # Eiffel Tower exists
        fact_checker=lambda e, p: False if "1820" in p else None,  # 1820 is false
        ontology_path=ONTOLOGY_PATH
    )
    
    assert result["total_failures_detected"] >= 1
    assert result["primary_failure"]["code"] == "RF-06", \
        f"Expected RF-06, got {result['primary_failure']['code']}"
    
    print("✅ RF-06 (Property Hallucination): Correctly detected false property")


def test_rf06_before_rf01():
    """
    Critical v2.1 test: RF-06 must fire BEFORE RF-01.
    Mars canals = factually false property, not overgeneralization.
    The decision flowchart checks RF-06 at Step 2, before RF-01 at Step 9.
    """
    result = audit_inference(
        text="Mars has sophisticated canal systems built by an advanced civilization.",
        paksha="Mars",
        hetu="has canal systems",
        vyapti="things with canals were built by civilizations",
        sadhya="Mars was inhabited by an advanced civilization",
        entity_lookup=lambda e: True,  # Mars exists
        fact_checker=lambda e, p: False if "canal" in p else None,  # canals are false
        ontology_path=ONTOLOGY_PATH
    )
    
    assert result["total_failures_detected"] >= 1
    assert result["primary_failure"]["code"] == "RF-06", \
        f"Expected RF-06, got {result['primary_failure']['code']}"
    
    print("✅ RF-06 before RF-01: Mars canals correctly caught as false property (not overgeneralization)")


def test_rf08_defeated_by_evidence():
    """
    RF-08: Conclusion defeated by established fact.
    Perpetual motion contradicts thermodynamics.
    """
    result = audit_inference(
        text="This machine achieves perpetual motion, proving free energy is possible.",
        paksha="this machine",
        hetu="achieves perpetual motion",
        vyapti="perpetual motion machines prove free energy",
        sadhya="free energy is possible",
        entity_lookup=lambda e: True,
        fact_checker=lambda e, p: False if "perpetual" in p or "free energy" in p else None,
        ontology_path=ONTOLOGY_PATH
    )
    
    assert result["total_failures_detected"] >= 1
    # Should catch RF-06 (perpetual motion is false property) at Step 2
    # In comprehensive mode, may also catch RF-08 at Step 4
    primary = result["primary_failure"]["code"]
    assert primary in ["RF-06", "RF-08"], \
        f"Expected RF-06 or RF-08, got {primary}"
    
    print(f"✅ RF-08/RF-06 (Defeated by Evidence): Caught as {primary}")


def test_pipeline_comprehensive_mode():
    """
    Comprehensive mode should collect ALL failures, not just the first.
    An inference can have multiple flaws simultaneously.
    """
    # Mock LLM judge that always finds issues
    def mock_judge(prompt):
        if "OVER-GENERALIZATION" in prompt:
            return {"is_too_general": True, "confidence": 0.7, 
                    "reasoning": "Reason too broad", "span": "test", 
                    "vipaksa_example": "counter-case"}
        if "CAUSAL REDUNDANCY" in prompt:
            return {"is_causally_redundant": True, "confidence": 0.8,
                    "reasoning": "Post hoc", "span": "test",
                    "alternative_cause": "natural recovery"}
        return {}
    
    result = audit_inference(
        text="Patients who took remedy X recovered. Therefore remedy X works because it has healing properties.",
        paksha="patients who took remedy X",
        hetu="has healing properties",
        vyapti="healing properties cause recovery",
        sadhya="remedy X works",
        entity_lookup=lambda e: True,
        fact_checker=lambda e, p: None,  # No fact-check available
        llm_judge=mock_judge,
        ontology_path=ONTOLOGY_PATH,
        mode="comprehensive"
    )
    
    assert result["total_failures_detected"] >= 2, \
        f"Expected ≥2 failures in comprehensive mode, got {result['total_failures_detected']}"
    
    codes = [f["code"] for f in result["all_failures"]]
    assert "RF-09" in codes, "Expected RF-09 in comprehensive results"
    assert "RF-01" in codes, "Expected RF-01 in comprehensive results"
    
    print(f"✅ Comprehensive mode: Detected {result['total_failures_detected']} failures: {codes}")


def test_pipeline_eliminatory_mode():
    """
    Eliminatory mode should stop at the first match.
    """
    result = audit_inference(
        text="Dr. Fake's study proves remedy X works.",
        paksha="Dr. Fake's study",
        hetu="study was conducted",
        vyapti="studies prove treatments work",
        sadhya="remedy X works",
        entity_lookup=lambda e: False,  # Entity doesn't exist
        ontology_path=ONTOLOGY_PATH,
        mode="eliminatory"
    )
    
    assert result["total_failures_detected"] == 1, \
        f"Expected exactly 1 failure in eliminatory mode, got {result['total_failures_detected']}"
    assert result["primary_failure"]["code"] == "RF-05"
    
    print("✅ Eliminatory mode: Stopped at first match (RF-05)")


def test_audit_report_json_serialization():
    """Test that AuditReport serializes to valid JSON."""
    result = audit_inference(
        text="Sky-lotus is fragrant because it is a lotus.",
        paksha="sky-lotus",
        hetu="is a lotus",
        vyapti="lotuses are fragrant",
        sadhya="is fragrant",
        entity_lookup=lambda e: False,
        ontology_path=ONTOLOGY_PATH
    )
    
    json_str = json.dumps(result, ensure_ascii=False, indent=2)
    parsed = json.loads(json_str)
    
    assert "primary_failure" in parsed
    assert "all_failures" in parsed
    assert parsed["pipeline_version"] == "2.1.0"
    
    print("✅ JSON serialization: Valid output structure")


def test_no_failures_when_clean():
    """When no backends are provided and entity exists, no failures should fire."""
    result = audit_inference(
        text="The mountain has fire because it has smoke.",
        paksha="mountain",
        hetu="has smoke",
        vyapti="wherever smoke, there fire",
        sadhya="has fire",
        entity_lookup=lambda e: True,
        fact_checker=lambda e, p: True,  # Property is true
        ontology_path=ONTOLOGY_PATH
    )
    
    # With no LLM judge, only rule-based steps run. 
    # Entity exists and property is true, so RF-05 and RF-06 don't fire.
    assert result["total_failures_detected"] == 0, \
        f"Expected 0 failures for valid inference, got {result['total_failures_detected']}"
    
    print("✅ Clean inference: No failures detected for valid reasoning")


# ---------------------------------------------------------------------------
# RUN ALL TESTS
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("VYĀPTI SCORER — TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        test_ontology_loads,
        test_rf05_entity_hallucination,
        test_rf06_property_hallucination,
        test_rf06_before_rf01,
        test_rf08_defeated_by_evidence,
        test_pipeline_comprehensive_mode,
        test_pipeline_eliminatory_mode,
        test_audit_report_json_serialization,
        test_no_failures_when_clean,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {len(tests)} total")
    print("=" * 60)
