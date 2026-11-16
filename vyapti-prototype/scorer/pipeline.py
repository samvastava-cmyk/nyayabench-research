"""
Vyāpti Scorer — Hetvābhāsa Sequential Classification Pipeline
===============================================================

Implements the 12-step decision flowchart from hetvabhasa_v2.1.json
as executable code. Each step is a separate classifier function.

The pipeline takes a parsed inference (pakṣa, hetu, vyāpti, sādhya, context)
and returns a ranked list of reasoning failure classifications.

Architecture:
    1. InferenceParser  — Extracts inference structure from raw LLM output
    2. StepClassifiers  — 12 individual step functions (Steps 1–12)
    3. ScorerPipeline   — Orchestrates steps in sequence, collects results
    4. AuditReport      — Formats output per the API spec

Design principle: Each step is independent and testable. Steps are ordered
by the flowchart's eliminatory logic — factual checks first, structural
checks second, scope checks third, judgment calls last.

Source: hetvabhasa_v2.1.json, Section "decision_flowchart"
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. DATA STRUCTURES
# ---------------------------------------------------------------------------

class Confidence(Enum):
    """Confidence levels for classification results."""
    VERY_HIGH = 0.95
    HIGH = 0.85
    MODERATE = 0.70
    LOW = 0.55
    SPECULATIVE = 0.40


@dataclass
class InferenceStructure:
    """
    Parsed Nyāya five-membered inference (pañcāvayava).
    
    Maps to the traditional structure:
        pratijñā  = assertion (pakṣa has sādhya)
        hetu      = reason-property
        udāharaṇa = example with vyāpti
        upanaya   = application to pakṣa
        nigamana  = conclusion
    
    For LLM output parsing, we extract:
        paksha  = subject entity + claimed properties
        hetu    = stated reason/evidence
        vyapti  = claimed pervasion rule (reason → conclusion)
        sadhya  = conclusion to be established
        context = domain knowledge, known facts
    """
    paksha: str           # Subject of the inference
    hetu: str             # Stated reason / evidence
    vyapti: str           # Claimed rule: "whenever H, then C"
    sadhya: str           # Conclusion
    raw_text: str         # Original LLM output text
    context: dict = field(default_factory=dict)  # Domain knowledge


@dataclass
class FailureClassification:
    """A single reasoning failure detection result."""
    rf_code: str                        # e.g. "RF-05"
    rf_name: str                        # e.g. "Āśrayāsiddha"
    rf_english: str                     # e.g. "Non-Existent Locus"
    confidence: float                   # 0.0 – 1.0
    avacchedaka_diagnosis: str          # What qualifier is missing/broken
    evidence: str                       # Why this classification was made
    span: Optional[str] = None          # Text span that triggered detection
    requires_human_review: bool = False # Flag for RF-04 and edge cases
    step_number: int = 0               # Which flowchart step triggered this


@dataclass
class AuditReport:
    """Complete audit output for one inference."""
    input_text: str
    inference: InferenceStructure
    failures: list                      # List[FailureClassification], ranked
    primary_failure: Optional[FailureClassification] = None
    total_failures_detected: int = 0
    pipeline_version: str = "2.1.0"
    
    def to_dict(self) -> dict:
        """Convert to API-ready dictionary."""
        result = {
            "pipeline_version": self.pipeline_version,
            "input_text": self.input_text,
            "inference_parsed": {
                "paksha": self.inference.paksha,
                "hetu": self.inference.hetu,
                "vyapti": self.inference.vyapti,
                "sadhya": self.inference.sadhya
            },
            "total_failures_detected": self.total_failures_detected,
            "primary_failure": None,
            "all_failures": []
        }
        
        if self.primary_failure:
            result["primary_failure"] = {
                "code": self.primary_failure.rf_code,
                "name": self.primary_failure.rf_english,
                "confidence": self.primary_failure.confidence,
                "diagnosis": self.primary_failure.avacchedaka_diagnosis,
                "evidence": self.primary_failure.evidence,
                "span": self.primary_failure.span,
                "requires_human_review": self.primary_failure.requires_human_review
            }
        
        for f in self.failures:
            result["all_failures"].append({
                "code": f.rf_code,
                "name": f.rf_english,
                "confidence": f.confidence,
                "diagnosis": f.avacchedaka_diagnosis,
                "evidence": f.evidence,
                "step": f.step_number,
                "requires_human_review": f.requires_human_review
            })
        
        return result
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 2. ONTOLOGY LOADER
# ---------------------------------------------------------------------------

class OntologyLoader:
    """Loads and provides access to the hetvabhasa taxonomy."""
    
    def __init__(self, ontology_path: Optional[str] = None):
        if ontology_path is None:
            ontology_path = str(
                Path(__file__).parent.parent / "ontology" / "hetvabhasa_v2.1.json"
            )
        
        with open(ontology_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        
        self.categories = {c["id"]: c for c in self.data["categories"]}
        self.flowchart = self.data.get("decision_flowchart", {})
        self.confusable_pairs = self.data.get("confusable_pairs", [])
    
    def get_category(self, rf_code: str) -> dict:
        return self.categories.get(rf_code, {})
    
    def get_english_name(self, rf_code: str) -> str:
        cat = self.get_category(rf_code)
        return cat.get("english", rf_code)
    
    def get_sanskrit_name(self, rf_code: str) -> str:
        cat = self.get_category(rf_code)
        return cat.get("iast", rf_code)
    
    def get_avacchedaka_question(self, rf_code: str) -> str:
        cat = self.get_category(rf_code)
        return cat.get("avacchedaka_question", "")


# ---------------------------------------------------------------------------
# 3. STEP CLASSIFIERS — The 12-Step Pipeline
# ---------------------------------------------------------------------------
# 
# Each step function takes an InferenceStructure and returns either:
#   - A FailureClassification (if the step fires)
#   - None (if the step does not fire, continue to next step)
#
# Steps are designed to be called by an LLM judge OR by rule-based logic.
# The `judge` parameter controls which backend is used.
#
# For rule-based steps (RF-05, RF-06, RF-08): direct verification
# For LLM-as-judge steps: structured prompt sent to an LLM
# ---------------------------------------------------------------------------

class StepClassifiers:
    """
    Individual classifier functions for each flowchart step.
    
    Each method corresponds to one step in the decision flowchart.
    Methods return a FailureClassification if the step fires, else None.
    """
    
    def __init__(self, ontology: OntologyLoader):
        self.ontology = ontology
    
    # -- STEP 1: Entity Existence (RF-05) ----------------------------------
    
    def step_01_entity_exists(
        self, 
        inference: InferenceStructure,
        entity_lookup: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 1: Does the subject (pakṣa) of the inference exist?
        If NO → RF-05 (Āśrayāsiddha — Non-Existent Locus)
        
        This is a RULE-BASED step. Uses entity_lookup function if provided,
        otherwise falls back to LLM judge.
        
        The key check: is the subject a real entity, or is it fabricated?
        Fictional entities, hallucinated persons/studies/organizations → RF-05.
        """
        # If we have a verification function, use it
        if entity_lookup is not None:
            exists = entity_lookup(inference.paksha)
            if not exists:
                return FailureClassification(
                    rf_code="RF-05",
                    rf_name="Āśrayāsiddha",
                    rf_english="Non-Existent Locus (Subject)",
                    confidence=Confidence.VERY_HIGH.value,
                    avacchedaka_diagnosis=(
                        f"The subject '{inference.paksha}' does not exist. "
                        "The avacchedaka of the pakṣa is empty — no real entity "
                        "for any qualifier to delimit."
                    ),
                    evidence=f"Entity verification returned: '{inference.paksha}' not found.",
                    span=inference.paksha,
                    step_number=1
                )
        
        # No result = step does not fire, continue pipeline
        return None
    
    # -- STEP 2: Property Truth (RF-06) ------------------------------------
    
    def step_02_property_true(
        self,
        inference: InferenceStructure,
        fact_checker: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 2: Is the reason-property (hetu) factually true of the subject?
        If NO → RF-06 (Svarūpāsiddha — Non-Existent Property)
        
        This is a RULE-BASED step when a fact_checker is available.
        
        Critical distinction (from v2.1): RF-06 requires the property to be
        EMPIRICALLY, DEMONSTRABLY false — not merely logically insufficient.
        If the property is true but the reasoning is too broad → NOT RF-06.
        """
        if fact_checker is not None:
            property_valid = fact_checker(inference.paksha, inference.hetu)
            if property_valid is False:  # Explicitly False, not None
                return FailureClassification(
                    rf_code="RF-06",
                    rf_name="Svarūpāsiddha",
                    rf_english="Non-Existent Property",
                    confidence=Confidence.HIGH.value,
                    avacchedaka_diagnosis=(
                        f"The property '{inference.hetu}' is factually false "
                        f"when attributed to '{inference.paksha}'. The avacchedaka "
                        "of the hetu attributes a non-existent property to the pakṣa."
                    ),
                    evidence=(
                        f"Fact check: '{inference.hetu}' is demonstrably false "
                        f"for '{inference.paksha}'."
                    ),
                    span=inference.hetu,
                    step_number=2
                )
        
        return None
    
    # -- STEP 3: Contradictory Reason (RF-03) ------------------------------
    
    def step_03_reason_contradicts(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 3: Does the reason actually entail the OPPOSITE of the conclusion?
        If YES → RF-03 (Viruddha — Contradictory Reason)
        
        LLM-as-judge step. The judge must determine if H → NOT-C.
        
        Key test: Does the SAME SINGLE reason prove the opposite?
        If TWO different reasons oppose → NOT RF-03 (likely RF-04).
        """
        if llm_judge is not None:
            prompt = self._build_rf03_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("is_contradictory", False):
                return FailureClassification(
                    rf_code="RF-03",
                    rf_name="Viruddha",
                    rf_english="Contradictory Reason",
                    confidence=result.get("confidence", Confidence.MODERATE.value),
                    avacchedaka_diagnosis=(
                        "The avacchedaka on the vyāpti is inverted — "
                        "the relation that holds is H → NOT-C, but the inference claims H → C."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected contradiction."),
                    span=result.get("span"),
                    step_number=3
                )
        
        return None
    
    # -- STEP 4: Defeated by Evidence (RF-08) ------------------------------
    
    def step_04_defeated_by_evidence(
        self,
        inference: InferenceStructure,
        fact_checker: Optional[callable] = None,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 4: Is the conclusion directly contradicted by established fact?
        If YES → RF-08 (Bādhita — Defeated Reason)
        
        v2.1 fix: This step now also checks for contradiction by established
        SCIENTIFIC LAW (e.g., thermodynamics), not just individual facts.
        This catches cases like perpetual motion before RF-06 fires on the
        property level.
        
        Combined rule-based + LLM judge step.
        """
        if fact_checker is not None:
            conclusion_valid = fact_checker(inference.paksha, inference.sadhya)
            if conclusion_valid is False:
                return FailureClassification(
                    rf_code="RF-08",
                    rf_name="Bādhita",
                    rf_english="Defeated Reason",
                    confidence=Confidence.HIGH.value,
                    avacchedaka_diagnosis=(
                        f"The conclusion '{inference.sadhya}' is directly contradicted "
                        "by independently established knowledge. The avacchedaka on the "
                        "sādhya conflicts with established fact."
                    ),
                    evidence=(
                        f"Fact check: conclusion '{inference.sadhya}' contradicts "
                        "established knowledge."
                    ),
                    span=inference.sadhya,
                    step_number=4
                )
        
        return None
    
    # -- STEP 5: Performative Self-Refutation (RF-10) ----------------------
    
    def step_05_self_refuting(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 5: Does the act of asserting the claim undermine the claim?
        If YES → RF-10 (Performative Self-Refutation)
        
        LLM-as-judge step. INFERRED category — no direct sūtra source.
        """
        if llm_judge is not None:
            prompt = self._build_rf10_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("is_self_refuting", False):
                return FailureClassification(
                    rf_code="RF-10",
                    rf_name="Prāgukta-Viruddha-Bādhita-Saṃyoga",
                    rf_english="Performative Self-Refutation",
                    confidence=result.get("confidence", Confidence.MODERATE.value),
                    avacchedaka_diagnosis=(
                        "The avacchedaka of the assertion includes the negation "
                        "of the assertion itself — the claim is self-defeating."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected self-refutation."),
                    span=result.get("span"),
                    step_number=5
                )
        
        return None
    
    # -- STEP 6: Causally Redundant (RF-09) --------------------------------
    
    def step_06_causally_redundant(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 6: Is the conclusion already explained by an independent cause?
        If YES → RF-09 (Anyathāsiddha — Explained by Another Cause)
        
        LLM-as-judge step.
        
        v2.1 GUARD: If the argument merely MENTIONS alternatives but dismisses
        them, this is STILL RF-09, NOT RF-04. RF-04 requires two actively
        presented competing reasons of comparable strength.
        """
        if llm_judge is not None:
            prompt = self._build_rf09_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("is_causally_redundant", False):
                return FailureClassification(
                    rf_code="RF-09",
                    rf_name="Anyathāsiddha",
                    rf_english="Causally Redundant Reason",
                    confidence=result.get("confidence", Confidence.MODERATE.value),
                    avacchedaka_diagnosis=(
                        "The avacchedaka on the kāraṇatā is 'otherwise established' — "
                        "an independent cause fully explains the observed effect."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected causal redundancy."),
                    span=result.get("span"),
                    step_number=6
                )
        
        return None
    
    # -- STEP 7: Missing Qualifier / Upādhi (RF-07a) -----------------------
    
    def step_07_missing_qualifier_universal(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 7 + 7a: Can you identify a specific upādhi the pervasion depends on?
        If YES and the GENERAL rule is conditional → RF-07a
        
        LLM-as-judge step.
        """
        if llm_judge is not None:
            prompt = self._build_rf07a_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("has_upadhi", False):
                scope = result.get("scope", "universal")
                if scope == "universal":
                    return FailureClassification(
                        rf_code="RF-07a",
                        rf_name="Vyāpyatvāsiddha (Sopādhika)",
                        rf_english="Missing Universal Qualifier",
                        confidence=result.get("confidence", Confidence.MODERATE.value),
                        avacchedaka_diagnosis=(
                            f"The pervasion is conditional on an unstated upādhi: "
                            f"'{result.get('upadhi_identified', 'unspecified')}'. "
                            "The avacchedaka on the vyāpti omits the required qualifier."
                        ),
                        evidence=result.get("reasoning", "LLM judge detected missing upādhi."),
                        span=result.get("span"),
                        step_number=7
                    )
        
        return None
    
    # -- STEP 7b: Subject-Specific Qualifier (RF-07b) ----------------------
    
    def step_07b_missing_qualifier_contextual(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 7a continued: General rule holds but fails for THIS subject.
        → RF-07b
        """
        if llm_judge is not None:
            prompt = self._build_rf07b_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("has_contextual_exception", False):
                return FailureClassification(
                    rf_code="RF-07b",
                    rf_name="Vyāpyatvāsiddha (Viśeṣa)",
                    rf_english="Missing Contextual Qualifier",
                    confidence=result.get("confidence", Confidence.MODERATE.value),
                    avacchedaka_diagnosis=(
                        f"The general rule holds but this specific subject has a "
                        f"defeating condition: '{result.get('defeating_condition', 'unspecified')}'. "
                        "The avacchedaka on the pakṣa-specific vyāpti omits the "
                        "subject-specific condition."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected contextual exception."),
                    span=result.get("span"),
                    step_number=7
                )
        
        return None
    
    # -- STEP 8: Blocked Causal Chain (RF-11) ------------------------------
    
    def step_08_blocked_causal_chain(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 8: All causal conditions present but a blocker prevents outcome?
        If YES → RF-11 (Pratibandha — Blocked Causal Chain)
        """
        if llm_judge is not None:
            prompt = self._build_rf11_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("has_blocker", False):
                return FailureClassification(
                    rf_code="RF-11",
                    rf_name="Pratibandha",
                    rf_english="Blocked Causal Chain",
                    confidence=result.get("confidence", Confidence.MODERATE.value),
                    avacchedaka_diagnosis=(
                        f"A blocking condition (pratibandha) is present: "
                        f"'{result.get('blocker_identified', 'unspecified')}'. "
                        "The avacchedaka on the kāraṇatā is blocked."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected causal blocker."),
                    span=result.get("span"),
                    step_number=8
                )
        
        return None
    
    # -- STEP 9: Too General (RF-01) ---------------------------------------
    
    def step_09_too_general(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 9: Does the reason appear in both sapakṣa AND vipakṣa?
        If YES → RF-01 (Sādhāraṇa — Too General)
        
        v2.1 note: This step is reached ONLY AFTER RF-06 has been ruled out
        at Step 2. Therefore, if we're here, the reason-property IS factually
        true — the problem is logical over-breadth, not factual falsity.
        """
        if llm_judge is not None:
            prompt = self._build_rf01_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("is_too_general", False):
                return FailureClassification(
                    rf_code="RF-01",
                    rf_name="Sādhāraṇa Savyabhicāra",
                    rf_english="Too General (Over-wide) Reason",
                    confidence=result.get("confidence", Confidence.MODERATE.value),
                    avacchedaka_diagnosis=(
                        "The avacchedaka on the hetu is missing or too broad — "
                        "the reason appears in both sapakṣa and vipakṣa, failing "
                        "to discriminate."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected over-generalization."),
                    span=result.get("span"),
                    step_number=9
                )
        
        return None
    
    # -- STEP 10: Too Particular (RF-02) -----------------------------------
    
    def step_10_too_particular(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 10: Does the reason appear ONLY in this subject?
        If YES → RF-02 (Asādhāraṇa — Too Particular)
        """
        if llm_judge is not None:
            prompt = self._build_rf02_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("is_too_particular", False):
                return FailureClassification(
                    rf_code="RF-02",
                    rf_name="Asādhāraṇa Savyabhicāra",
                    rf_english="Too Particular (Peculiar) Reason",
                    confidence=result.get("confidence", Confidence.MODERATE.value),
                    avacchedaka_diagnosis=(
                        "The avacchedaka on the hetu is so narrow it picks out "
                        "only the pakṣa — no pervasion can be established from a singleton."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected idiosyncratic reason."),
                    span=result.get("span"),
                    step_number=10
                )
        
        return None
    
    # -- STEP 11: Vacuous Conclusion (RF-12) -------------------------------
    
    def step_11_vacuous_conclusion(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 11: Is the conclusion ONTOLOGICALLY universal?
        If YES → RF-12 (Anupasamhārī — Non-Exclusive)
        
        v2.1 GUARD: RF-12 requires the conclusion to apply to ALL entities
        in the universe without ANY class restriction. A broad generalization
        about a CLASS (all politicians, all drugs) is NOT RF-12 — that's RF-01.
        RF-12 is reserved for conclusions like "has properties", "is nameable",
        where literally no entity of any kind is excluded.
        """
        if llm_judge is not None:
            prompt = self._build_rf12_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("is_ontologically_universal", False):
                return FailureClassification(
                    rf_code="RF-12",
                    rf_name="Anupasamhārī Savyabhicāra",
                    rf_english="Non-Exclusive (Universal Predicate)",
                    confidence=result.get("confidence", Confidence.MODERATE.value),
                    avacchedaka_diagnosis=(
                        "The avacchedaka on the sādhya has no boundary — the conclusion "
                        "is ontologically universal and admits no vipakṣa of any kind."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected vacuous conclusion."),
                    span=result.get("span"),
                    step_number=11
                )
        
        return None
    
    # -- STEP 12: Counterbalanced (RF-04) ----------------------------------
    
    def step_12_counterbalanced(
        self,
        inference: InferenceStructure,
        llm_judge: Optional[callable] = None
    ) -> Optional[FailureClassification]:
        """
        Step 12: Does an equally strong independent reason exist for the
        opposite conclusion?
        If YES → RF-04 (Satpratipakṣa — Counterbalanced Reason)
        
        ALWAYS FLAGS FOR HUMAN REVIEW.
        
        v2.1 GUARD: Merely MENTIONING alternatives does NOT trigger RF-04.
        The counter-reason must be ACTIVELY PRESENTED as a genuinely valid
        argument of comparable strength.
        """
        if llm_judge is not None:
            prompt = self._build_rf04_prompt(inference)
            result = llm_judge(prompt)
            if result and result.get("is_counterbalanced", False):
                # Additional guard: check if counter-reason is merely mentioned
                if result.get("counter_reason_is_merely_mentioned", False):
                    return None  # Not RF-04 — likely RF-09 (already caught at Step 6)
                
                return FailureClassification(
                    rf_code="RF-04",
                    rf_name="Satpratipakṣa",
                    rf_english="Counterbalanced Reason",
                    confidence=result.get("confidence", Confidence.LOW.value),
                    avacchedaka_diagnosis=(
                        "The avacchedaka on the inference scope fails to include "
                        "counter-evidence of comparable strength. An equally valid "
                        "reason exists for the opposite conclusion."
                    ),
                    evidence=result.get("reasoning", "LLM judge detected counterbalanced reasons."),
                    span=result.get("span"),
                    requires_human_review=True,  # ALWAYS
                    step_number=12
                )
        
        return None
    
    # -- PROMPT BUILDERS ---------------------------------------------------
    # These construct the structured prompts sent to the LLM judge.
    # Each prompt is specific to one step and asks a focused question.
    
    def _build_rf03_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for CONTRADICTORY reasoning (Viruddha).\n\n"
            f"Subject (pakṣa): {inf.paksha}\n"
            f"Reason (hetu): {inf.hetu}\n"
            f"Claimed rule (vyāpti): {inf.vyapti}\n"
            f"Conclusion (sādhya): {inf.sadhya}\n\n"
            "Question: Does the SAME reason, when properly analyzed, actually "
            "entail the OPPOSITE of the stated conclusion?\n"
            "That is: Does H → NOT-C, even though the arguer claims H → C?\n\n"
            "Respond with JSON: {\"is_contradictory\": true/false, \"confidence\": 0.0-1.0, "
            "\"reasoning\": \"...\", \"span\": \"...\"}\n"
            "Only return true if the SAME SINGLE reason proves the opposite. "
            "If TWO different reasons oppose each other, return false."
        )
    
    def _build_rf10_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this claim for PERFORMATIVE SELF-REFUTATION.\n\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Does the ACT of asserting this claim undermine the "
            "claim's own truth-conditions?\n"
            "That is: Does making the statement create evidence against the statement?\n\n"
            "Respond with JSON: {\"is_self_refuting\": true/false, \"confidence\": 0.0-1.0, "
            "\"reasoning\": \"...\", \"span\": \"...\"}\n"
            "Only return true for genuine performative contradiction — where the "
            "assertion itself defeats the content."
        )
    
    def _build_rf09_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for CAUSAL REDUNDANCY (Anyathāsiddha / Post Hoc).\n\n"
            f"Subject (pakṣa): {inf.paksha}\n"
            f"Claimed cause (hetu): {inf.hetu}\n"
            f"Claimed effect (sādhya): {inf.sadhya}\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Is the claimed cause actually necessary, or is the effect "
            "already fully explained by an independent cause?\n\n"
            "IMPORTANT GUARD: If the argument MENTIONS alternative causes but "
            "dismisses or ignores them, this is STILL causal redundancy (RF-09). "
            "Merely mentioning alternatives does NOT make this a counterbalanced "
            "argument (RF-04). RF-04 requires TWO actively presented, genuinely "
            "valid, competing reasons of comparable strength.\n\n"
            "Respond with JSON: {\"is_causally_redundant\": true/false, "
            "\"confidence\": 0.0-1.0, \"reasoning\": \"...\", \"span\": \"...\", "
            "\"alternative_cause\": \"...\"}"
        )
    
    def _build_rf07a_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for MISSING QUALIFIER (Vyāpyatvāsiddha / Upādhi).\n\n"
            f"Claimed rule (vyāpti): {inf.vyapti}\n"
            f"Reason (hetu): {inf.hetu}\n"
            f"Conclusion (sādhya): {inf.sadhya}\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Is the claimed pervasion (H → C) actually CONDITIONAL on "
            "an unstated qualifier (upādhi)?\n"
            "Can you name a SPECIFIC condition U such that (H ∧ U) → C holds "
            "but H → C alone does not?\n\n"
            "If you CANNOT name a specific qualifier and the reason just appears "
            "in both positive and negative cases → this is RF-01 (too general), "
            "not RF-07a.\n\n"
            "Respond with JSON: {\"has_upadhi\": true/false, \"scope\": \"universal\"|\"contextual\", "
            "\"upadhi_identified\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\", "
            "\"span\": \"...\"}"
        )
    
    def _build_rf07b_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for SUBJECT-SPECIFIC EXCEPTION.\n\n"
            f"Subject (pakṣa): {inf.paksha}\n"
            f"Claimed rule (vyāpti): {inf.vyapti}\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Does the general rule hold, but fail for THIS specific "
            "subject due to a subject-specific condition?\n\n"
            "Respond with JSON: {\"has_contextual_exception\": true/false, "
            "\"defeating_condition\": \"...\", \"confidence\": 0.0-1.0, "
            "\"reasoning\": \"...\", \"span\": \"...\"}"
        )
    
    def _build_rf11_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for BLOCKED CAUSAL CHAIN (Pratibandha).\n\n"
            f"Subject (pakṣa): {inf.paksha}\n"
            f"Claimed cause (hetu): {inf.hetu}\n"
            f"Claimed effect (sādhya): {inf.sadhya}\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Are all standard causal conditions present, BUT a blocking "
            "condition prevents the expected outcome?\n\n"
            "Respond with JSON: {\"has_blocker\": true/false, "
            "\"blocker_identified\": \"...\", \"confidence\": 0.0-1.0, "
            "\"reasoning\": \"...\", \"span\": \"...\"}"
        )
    
    def _build_rf01_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for OVER-GENERALIZATION (Sādhāraṇa).\n\n"
            f"Reason (hetu): {inf.hetu}\n"
            f"Conclusion (sādhya): {inf.sadhya}\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Does the reason-property appear in cases where the "
            "conclusion is TRUE (sapakṣa) AND also in cases where the conclusion "
            "is FALSE (vipakṣa)?\n\n"
            "NOTE: We have already confirmed the reason-property is factually "
            "true (RF-06 was ruled out). The question is whether the reason is "
            "logically too broad — not whether it's factually wrong.\n\n"
            "Respond with JSON: {\"is_too_general\": true/false, "
            "\"confidence\": 0.0-1.0, \"reasoning\": \"...\", \"span\": \"...\", "
            "\"vipaksa_example\": \"...\"}"
        )
    
    def _build_rf02_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for IDIOSYNCRATIC REASON (Asādhāraṇa).\n\n"
            f"Reason (hetu): {inf.hetu}\n"
            f"Subject (pakṣa): {inf.paksha}\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Does the reason-property exist ONLY in this specific "
            "subject and nowhere else? Is there NO sapakṣa and NO vipakṣa?\n\n"
            "Respond with JSON: {\"is_too_particular\": true/false, "
            "\"confidence\": 0.0-1.0, \"reasoning\": \"...\", \"span\": \"...\"}"
        )
    
    def _build_rf12_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for VACUOUS / UNIVERSAL CONCLUSION (Anupasamhārī).\n\n"
            f"Conclusion (sādhya): {inf.sadhya}\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Is the conclusion ONTOLOGICALLY UNIVERSAL — does it apply "
            "to ALL entities in the universe without ANY class restriction?\n\n"
            "CRITICAL GUARD: A broad generalization about a CLASS (e.g., 'all "
            "politicians are corrupt') is NOT ontologically universal — entities "
            "outside that class are counter-instances. RF-12 requires that NO "
            "entity of ANY kind is excluded (e.g., 'has properties', 'is nameable').\n\n"
            "Respond with JSON: {\"is_ontologically_universal\": true/false, "
            "\"confidence\": 0.0-1.0, \"reasoning\": \"...\", \"span\": \"...\"}"
        )
    
    def _build_rf04_prompt(self, inf: InferenceStructure) -> str:
        return (
            "Analyze this inference for COUNTERBALANCED REASONING (Satpratipakṣa).\n\n"
            f"Reason (hetu): {inf.hetu}\n"
            f"Conclusion (sādhya): {inf.sadhya}\n"
            f"Full text: {inf.raw_text}\n\n"
            "Question: Does a SEPARATE, DISTINCT, INDEPENDENT reason of comparable "
            "strength exist for the OPPOSITE conclusion?\n\n"
            "CRITICAL GUARDS:\n"
            "1. If the SAME reason proves the opposite → RF-03, not RF-04\n"
            "2. If alternatives are merely MENTIONED but not actively presented "
            "as valid competing arguments → RF-09, not RF-04\n"
            "3. RF-04 requires TWO actively presented, genuinely valid reasons "
            "of COMPARABLE strength\n\n"
            "Respond with JSON: {\"is_counterbalanced\": true/false, "
            "\"counter_reason_is_merely_mentioned\": true/false, "
            "\"confidence\": 0.0-1.0, \"reasoning\": \"...\", \"span\": \"...\", "
            "\"counter_reason\": \"...\"}"
        )


# ---------------------------------------------------------------------------
# 4. SCORER PIPELINE — Orchestrates the 12-Step Sequence
# ---------------------------------------------------------------------------

class ScorerPipeline:
    """
    Main pipeline — runs the 12-step decision flowchart in sequence.
    
    Unlike a single-shot classifier, this pipeline:
    1. Runs each step with a SPECIALIZED prompt (not one giant classify prompt)
    2. Collects ALL matching failures (an inference can have multiple flaws)
    3. Ranks failures by confidence
    4. Returns a structured AuditReport
    
    The pipeline supports two modes:
    - ELIMINATORY (default): First match wins per the flowchart order
    - COMPREHENSIVE: Runs ALL steps and returns all matches, ranked
    
    For production, COMPREHENSIVE is recommended because the Nyāya texts
    explicitly state that a single hetu can have multiple doṣas simultaneously
    (TS Sect. LII commentary).
    """
    
    def __init__(
        self,
        ontology_path: Optional[str] = None,
        mode: str = "comprehensive"  # "eliminatory" or "comprehensive"
    ):
        self.ontology = OntologyLoader(ontology_path)
        self.classifiers = StepClassifiers(self.ontology)
        self.mode = mode
    
    def classify(
        self,
        inference: InferenceStructure,
        entity_lookup: Optional[callable] = None,
        fact_checker: Optional[callable] = None,
        llm_judge: Optional[callable] = None
    ) -> AuditReport:
        """
        Run the complete 12-step pipeline on one inference.
        
        Parameters:
            inference: Parsed inference structure
            entity_lookup: Function(entity_name) → bool (exists?)
            fact_checker: Function(entity, property) → bool|None (true?)
            llm_judge: Function(prompt) → dict (LLM response)
        
        Returns:
            AuditReport with ranked list of detected failures
        """
        failures = []
        
        # Step 1: Entity existence (RF-05)
        result = self.classifiers.step_01_entity_exists(inference, entity_lookup)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 2: Property truth (RF-06)
        result = self.classifiers.step_02_property_true(inference, fact_checker)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 3: Contradictory reason (RF-03)
        result = self.classifiers.step_03_reason_contradicts(inference, llm_judge)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 4: Defeated by evidence (RF-08)
        result = self.classifiers.step_04_defeated_by_evidence(
            inference, fact_checker, llm_judge
        )
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 5: Self-refuting (RF-10)
        result = self.classifiers.step_05_self_refuting(inference, llm_judge)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 6: Causally redundant (RF-09)
        result = self.classifiers.step_06_causally_redundant(inference, llm_judge)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 7: Missing universal qualifier (RF-07a)
        result = self.classifiers.step_07_missing_qualifier_universal(
            inference, llm_judge
        )
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 7b: Missing contextual qualifier (RF-07b)
        result = self.classifiers.step_07b_missing_qualifier_contextual(
            inference, llm_judge
        )
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 8: Blocked causal chain (RF-11)
        result = self.classifiers.step_08_blocked_causal_chain(inference, llm_judge)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 9: Too general (RF-01)
        result = self.classifiers.step_09_too_general(inference, llm_judge)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 10: Too particular (RF-02)
        result = self.classifiers.step_10_too_particular(inference, llm_judge)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 11: Vacuous conclusion (RF-12)
        result = self.classifiers.step_11_vacuous_conclusion(inference, llm_judge)
        if result:
            failures.append(result)
            if self.mode == "eliminatory":
                return self._build_report(inference, failures)
        
        # Step 12: Counterbalanced (RF-04) — always last, always human review
        result = self.classifiers.step_12_counterbalanced(inference, llm_judge)
        if result:
            failures.append(result)
        
        return self._build_report(inference, failures)
    
    def _build_report(
        self,
        inference: InferenceStructure,
        failures: list
    ) -> AuditReport:
        """Build the final audit report from collected failures."""
        # Sort by confidence (highest first)
        failures.sort(key=lambda f: f.confidence, reverse=True)
        
        report = AuditReport(
            input_text=inference.raw_text,
            inference=inference,
            failures=failures,
            primary_failure=failures[0] if failures else None,
            total_failures_detected=len(failures)
        )
        
        return report


# ---------------------------------------------------------------------------
# 5. CONVENIENCE FUNCTION
# ---------------------------------------------------------------------------

def audit_inference(
    text: str,
    paksha: str,
    hetu: str,
    vyapti: str,
    sadhya: str,
    entity_lookup: Optional[callable] = None,
    fact_checker: Optional[callable] = None,
    llm_judge: Optional[callable] = None,
    ontology_path: Optional[str] = None,
    mode: str = "comprehensive"
) -> dict:
    """
    One-call convenience function for auditing an inference.
    
    Returns a dictionary ready for API response.
    
    Example:
        result = audit_inference(
            text="Dr. Chen's 2019 Stanford study proves fasting cures dementia.",
            paksha="Dr. Chen's 2019 Stanford study",
            hetu="fasting was studied",
            vyapti="fasting studies prove health benefits",
            sadhya="fasting cures dementia",
            entity_lookup=lambda e: False  # Dr. Chen doesn't exist
        )
        print(result["primary_failure"]["code"])  # "RF-05"
    """
    inference = InferenceStructure(
        paksha=paksha,
        hetu=hetu,
        vyapti=vyapti,
        sadhya=sadhya,
        raw_text=text
    )
    
    pipeline = ScorerPipeline(ontology_path=ontology_path, mode=mode)
    report = pipeline.classify(
        inference,
        entity_lookup=entity_lookup,
        fact_checker=fact_checker,
        llm_judge=llm_judge
    )
    
    return report.to_dict()
