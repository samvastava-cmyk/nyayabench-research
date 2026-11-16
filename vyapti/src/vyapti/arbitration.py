"""Stage 3 — deterministic arbitration between the rule layer and the judge.

Arbitration exists because the judge and the rule layer disagree in
predictable directions. Each rule below is a *structural* precedence claim,
stated once, applied identically to every input, and logged when it fires.

Two design commitments:

* **Every override is recorded.** A final label that differs from the judge's
  verdict always carries an ``ArbitrationStep`` explaining which rule moved it
  and why. A silent override is unauditable.
* **No override may invent a label.** Arbitration can only redirect between
  categories the taxonomy defines.

The RF-01 precedence rules are the ones that matter most. RF-01 is the
broadest definition in the taxonomy and absorbs 49.2% of external
classifications and 51% of false positives — it is the sink that Phase 2's
Experiment 2 is designed to drain. These rules are the current, partial
mitigation, not the fix.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from .schemas import ArbitrationStep, InferenceStructure, RFCode

# --------------------------------------------------------------------------
# Structural cue families. These describe argument *shapes*, not topics.
# --------------------------------------------------------------------------

CUES: dict[str, re.Pattern[str]] = {
    # a single unique case used as the whole evidence base
    "singleton": re.compile(
        r"\b(?:only|sole|solely|unique(?:ly)?|exclusive(?:ly)?|the one|just one|"
        r"a single|one person|my own|personally experienced|first-hand)\b",
        re.I,
    ),
    # an unqualified universal applied without conditions
    "unqualified_universal": re.compile(
        r"\b(?:always|never|every|all|any|without exception|invariably|"
        r"in every case|guarantee[sd]?|certain(?:ly)?|must)\b",
        re.I,
    ),
    # a weak tendency stretched to certainty
    "weak_tendency": re.compile(
        r"\b(?:often|usually|generally|typically|tends? to|likely|most|many|"
        r"frequently|on average|correlat\w+|associated with)\b",
        re.I,
    ),
    # stronger evidence overriding a weaker claim
    "stronger_evidence": re.compile(
        r"\b(?:measurement|measured|data|records?|tests?|evidence|observ\w+|"
        r"study|studies|audit|experiment)\b.{0,40}\b(?:override[sd]?|contradict\w*|"
        r"disprove[sd]?|refute[sd]?|show(?:s|ed)? otherwise)\b",
        re.I,
    ),
    # the act of asserting undermines the assertion
    "self_refutation": re.compile(
        r"\b(?:this (?:sentence|statement|claim))\b|"
        r"\b(?:by (?:saying|writing|asserting|reading|processing) this)\b|"
        r"\b(?:I (?:cannot|can't) (?:write|speak|type))\b",
        re.I,
    ),
    # a causal chain explicitly interrupted before completing
    "blocked_chain": re.compile(
        r"\b(?:but|however|though)\b[^.;]{0,80}\b(?:blocked|interrupted|prevented|"
        r"never reached|cut off|failed to (?:reach|arrive|complete)|stopped)\b",
        re.I,
    ),
    # a contextual blocker on an otherwise valid rule
    "contextual_blocker": re.compile(
        r"\b(?:but|however|except|although|despite|even though)\b[^.;]{0,80}"
        r"\b(?:in this case|here|for (?:this|him|her|them)|cannot|is unable)\b",
        re.I,
    ),
    # a competing explanation for the same outcome
    "alternative_cause": re.compile(
        r"\b(?:also|another|alternative(?:ly)?|other factors?|confound\w*|"
        r"coincid\w+|already (?:was|were|had))\b",
        re.I,
    ),
}


@dataclass(frozen=True)
class Rule:
    id: str
    from_codes: frozenset[RFCode]
    to_code: RFCode
    predicate: Callable[[str, InferenceStructure], bool]
    rationale: str


def _has(name: str) -> Callable[[str, InferenceStructure], bool]:
    pat = CUES[name]
    return lambda text, _struct: bool(pat.search(text))


def _weak_to_certain(text: str, _s: InferenceStructure) -> bool:
    return bool(CUES["weak_tendency"].search(text)) and bool(
        CUES["unqualified_universal"].search(text)
    )


#: Applied in order. The first rule whose predicate holds and whose
#: ``from_codes`` contains the current label fires; at most one fires.
RULES: tuple[Rule, ...] = (
    Rule(
        "R1-singleton",
        frozenset({RFCode.RF_01}),
        RFCode.RF_02,
        _has("singleton"),
        "the evidence base is a single unique case, which is RF-02 (too particular), "
        "not RF-01 (too general)",
    ),
    Rule(
        "R2-weak-to-certain",
        frozenset({RFCode.RF_07A}),
        RFCode.RF_01,
        _weak_to_certain,
        "a weak tendency is stretched to certainty; the reason is over-wide (RF-01) "
        "rather than conditional on a nameable qualifier (RF-07a)",
    ),
    Rule(
        "R3-missing-qualifier",
        frozenset({RFCode.RF_01}),
        RFCode.RF_07A,
        lambda t, s: bool(CUES["unqualified_universal"].search(t))
        and not CUES["weak_tendency"].search(t),
        "a general rule is applied unconditionally; a specific missing qualifier "
        "makes this RF-07a rather than general over-width",
    ),
    Rule(
        "R4-contextual-blocker",
        frozenset({RFCode.RF_07A, RFCode.RF_01}),
        RFCode.RF_07B,
        _has("contextual_blocker"),
        "the rule is valid in general but a specific contextual blocker prevents it here",
    ),
    Rule(
        "R5-stronger-evidence",
        frozenset({RFCode.RF_03, RFCode.RF_04, RFCode.RF_01}),
        RFCode.RF_08,
        _has("stronger_evidence"),
        "stronger evidence decisively defeats a weaker claim; this is a source-hierarchy "
        "defeat (RF-08), not a direct contradiction",
    ),
    Rule(
        "R6-self-refutation",
        frozenset({RFCode.RF_03, RFCode.RF_01, RFCode.RF_06}),
        RFCode.RF_10,
        _has("self_refutation"),
        "the contradiction depends on the act of asserting the statement",
    ),
    Rule(
        "R7-blocked-chain",
        frozenset({RFCode.RF_07A, RFCode.RF_07B, RFCode.RF_09}),
        RFCode.RF_11,
        _has("blocked_chain"),
        "the causal process starts and is then explicitly interrupted",
    ),
)


def arbitrate(
    text: str,
    judge_label: RFCode,
    structure: InferenceStructure | None = None,
    enabled: bool = True,
) -> tuple[RFCode, list[ArbitrationStep]]:
    """Apply deterministic precedence to a judge verdict.

    Returns the final label and the (possibly empty) list of steps taken.
    Set ``enabled=False`` to measure the judge unaided — the ablation arms
    need that comparison.
    """
    if not enabled or judge_label is RFCode.NONE:
        # A NONE verdict is never overridden into a failure label. Arbitration
        # exists to redistribute *among* failure types, not to manufacture
        # failures — doing the latter would attack specificity, the one number
        # Phase 2 is trying to move.
        return judge_label, []

    struct = structure or InferenceStructure()
    for rule in RULES:
        if judge_label in rule.from_codes and rule.predicate(text, struct):
            return rule.to_code, [
                ArbitrationStep(
                    rule_id=rule.id,
                    from_code=judge_label,
                    to_code=rule.to_code,
                    rationale=rule.rationale,
                )
            ]
    return judge_label, []
