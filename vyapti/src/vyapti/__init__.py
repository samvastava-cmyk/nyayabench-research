"""Vyāpti — a typed classifier for structural reasoning failure.

Built on a taxonomy derived from Navya-Nyāya *hetvābhāsa*, the Indian logical
tradition's theory of fallacious reasons. See README.md.

What this is, stated plainly: a high-recall, low-specificity screening
instrument. It catches essentially every structural failure present (recall
97–100%) and also flags roughly six in ten sound arguments (specificity
33–37%). Use it to decide what a human should read, never to make the call.
"""

from .arbitration import arbitrate
from .client import ChatClient
from .extract import extract
from .judge import load_profile, parse_verdict
from .pipeline import VyaptiPipeline
from .schemas import (
    VYAPTI_8,
    CaseResult,
    InferenceStructure,
    JudgeVerdict,
    MalformedJudgeResponseError,
    RFCode,
    RunConfig,
    UnavailableJudgeError,
)
from .taxonomy import Category, Taxonomy, load_taxonomy

__version__ = "0.11.0.dev0"

__all__ = [
    "VyaptiPipeline",
    "ChatClient",
    "Taxonomy",
    "Category",
    "load_taxonomy",
    "load_profile",
    "parse_verdict",
    "extract",
    "arbitrate",
    "RFCode",
    "VYAPTI_8",
    "InferenceStructure",
    "JudgeVerdict",
    "CaseResult",
    "RunConfig",
    "UnavailableJudgeError",
    "MalformedJudgeResponseError",
    "__version__",
]
