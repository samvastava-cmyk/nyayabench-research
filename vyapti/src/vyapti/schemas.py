"""Typed schemas for every object that crosses a boundary in Vyāpti.

Design rule inherited from Phase 1's most expensive bug: a malformed or
unavailable model response must *raise*, never silently degrade into a
valid-looking label. In the Phase 1 pipeline an unreachable judge returned
``{"rf_code": "NONE", "source": "llm_unavailable"}`` and an unparseable
response was coerced to ``NONE``. Both are indistinguishable from a genuine
"this argument is sound" verdict, and both silently corrupted a full
experiment run. Everything here is built so that cannot happen again.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# --------------------------------------------------------------------------
# Labels
# --------------------------------------------------------------------------


class RFCode(str, Enum):
    """The 13 taxonomy categories plus the sound-argument label.

    RF-12 is specified in the taxonomy but is not part of the classifier's
    output space; see docs/TAXONOMY.md for why.
    """

    RF_01 = "RF-01"
    RF_02 = "RF-02"
    RF_03 = "RF-03"
    RF_04 = "RF-04"
    RF_05 = "RF-05"
    RF_06 = "RF-06"
    RF_07A = "RF-07a"
    RF_07B = "RF-07b"
    RF_08 = "RF-08"
    RF_09 = "RF-09"
    RF_10 = "RF-10"
    RF_11 = "RF-11"
    NONE = "NONE"


#: The production profile: categories that fire on real-world text.
#: See docs/RESULTS.md — RF-05, RF-07b, RF-10 and RF-11 fire on 18 of 2,174
#: external cases and RF-04 on 30, i.e. they are effectively inert outside
#: constructed suites.
VYAPTI_8 = frozenset(
    {
        RFCode.RF_01,
        RFCode.RF_02,
        RFCode.RF_03,
        RFCode.RF_06,
        RFCode.RF_07A,
        RFCode.RF_08,
        RFCode.RF_09,
        RFCode.NONE,
    }
)


class UnavailableJudgeError(RuntimeError):
    """The judge could not be reached, or returned nothing usable.

    Raised — never swallowed. A run that hits this must abort, not continue
    with a fabricated NONE.
    """


class MalformedJudgeResponseError(ValueError):
    """The judge replied, but not with a parseable, schema-valid verdict."""

    def __init__(self, message: str, raw: str = "") -> None:
        super().__init__(message)
        self.raw = raw


# --------------------------------------------------------------------------
# Stage 1 — rule-based structural extraction
# --------------------------------------------------------------------------


class InferenceStructure(BaseModel):
    """The pakṣa / hetu / sādhya triple recovered from surface text.

    A helper for the judge, never authoritative: the judge is instructed to
    trust the full text when the two disagree.
    """

    model_config = ConfigDict(extra="forbid")

    subject: str = Field("", description="pakṣa — what the argument is about")
    reason: str = Field("", description="hetu — the stated ground")
    conclusion: str = Field("", description="sādhya — what is being established")
    connective: str | None = Field(None, description="the cue token that split the argument")
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    @property
    def is_complete(self) -> bool:
        return bool(self.subject and self.reason and self.conclusion)


# --------------------------------------------------------------------------
# Stage 2 — the LLM judge
# --------------------------------------------------------------------------


class JudgeVerdict(BaseModel):
    """Exactly what a judge model is allowed to return.

    ``extra="forbid"`` is deliberate. A judge that invents fields is a judge
    that is not following the contract, and we want to know immediately.
    """

    model_config = ConfigDict(extra="forbid")

    rf_code: RFCode
    confidence: float = Field(..., ge=0.0, le=1.0)
    diagnosis: str = Field("", max_length=2000)

    @field_validator("rf_code", mode="before")
    @classmethod
    def _reject_unknown(cls, v: Any) -> Any:
        """Never coerce an unrecognised label to NONE — that hides errors."""
        if isinstance(v, str):
            v = v.strip()
            # Tolerate case and separator drift only; anything else is an error.
            canonical = {c.value.lower().replace("_", "-"): c.value for c in RFCode}
            key = v.lower().replace("_", "-")
            if key in canonical:
                return canonical[key]
            raise ValueError(
                f"judge returned unrecognised label {v!r}; "
                "this is a contract violation, not a NONE verdict"
            )
        return v


# --------------------------------------------------------------------------
# Stage 3 — deterministic arbitration
# --------------------------------------------------------------------------


class ArbitrationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    from_code: RFCode
    to_code: RFCode
    rationale: str


# --------------------------------------------------------------------------
# The full record written to disk — one JSON object per case, append-only
# --------------------------------------------------------------------------


class CaseResult(BaseModel):
    """One classified case.

    Every field here exists because its absence cost Phase 1 something.
    ``raw_response`` is stored in full rather than truncated to a preview:
    the 300-character previews written during the August runs are the reason
    the human-verification study had to be discarded.
    """

    model_config = ConfigDict(extra="forbid")

    # identity
    case_id: str
    suite: str
    text: str
    gold_label: RFCode | None = None

    # provenance — enough to reproduce this exact call
    run_id: str
    arm: str
    repeat: int
    model: str
    provider: str
    temperature: float
    max_tokens: int
    prompt_profile: str
    prompt_sha256: str
    taxonomy_version: str
    timestamp: str

    # stages
    structure: InferenceStructure | None = None
    judge_verdict: JudgeVerdict | None = None
    arbitration: list[ArbitrationStep] = Field(default_factory=list)
    final_label: RFCode | None = None

    # raw telemetry — never truncated
    raw_response: str = ""
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float | None = None

    # failure bookkeeping
    status: Literal["ok", "error"] = "ok"
    error_type: str | None = None
    error_detail: str | None = None

    @property
    def is_correct(self) -> bool | None:
        if self.gold_label is None or self.final_label is None:
            return None
        return self.gold_label == self.final_label


class RunConfig(BaseModel):
    """The complete specification of one experimental arm."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    arm: str
    repeat: int
    suite_path: str
    provider: str = "openai"
    model: str = "gpt-4.1"
    temperature: float = 0.0
    max_tokens: int = 1000
    prompt_profile: str = "reference-v11"
    concurrency: int = 8
    output_path: str = ""
    limit: int | None = None
