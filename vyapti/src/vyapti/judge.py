"""Stage 2 — the LLM judge.

A *prompt profile* is the thing that turns taxonomy definitions into a working
classifier: the exemplar set, the conditional disambiguation rules, and the
output contract. The profile is loaded at runtime from a directory, so the
released code path and the calibrated profile are separable artifacts.

Two profiles matter:

``reference``
    Ships with this repository. Definitions from the taxonomy plus the output
    contract, and nothing else — no exemplars, no conditional rules. It is a
    faithful, runnable baseline and it is what the ablation ladder measures
    *against*. It is not the profile the ICON paper reports.

``production``
    The calibrated profile: 66 exemplars, 31 conditional rules, versioned
    ``v10-rf07a-fix``. Not distributed. Point ``VYAPTI_PROMPT_DIR`` at a
    directory containing ``production.txt`` to use it.

Why the split is drawn here and not elsewhere: the taxonomy is the scholarly
claim and is public under CC-BY-4.0; the calibration is the engineering, and
it is the thing that took six weeks. Anyone can reproduce the pipeline, audit
the taxonomy, and run the reference profile. See prompts/README.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from .schemas import (
    InferenceStructure,
    JudgeVerdict,
    MalformedJudgeResponseError,
)
from .taxonomy import Taxonomy, load_taxonomy

_SYSTEM = "You are an expert reasoning analyst for the Vyāpti reasoning benchmark."

_OUTPUT_CONTRACT = """\
Instructions:
- Choose exactly one label from: RF-01, RF-02, RF-03, RF-04, RF-05, RF-06,
  RF-07a, RF-07b, RF-08, RF-09, RF-10, RF-11, NONE.
- NONE is a full verdict, not a fallback. If the argument is structurally
  sound, return NONE with the same confidence you would give any other label.
- Classify the single primary structural failure. Do not classify style,
  tone, factual disagreement, or rhetorical strength.
- Use the full input text as the primary source of truth. The extracted
  reasoning structure is a helper and may compress or misplace a clause. If
  the two conflict, trust the text.
- Return strict JSON and nothing else.

Return exactly:
{"rf_code": "<label>", "confidence": <0.0-1.0>, "diagnosis": "<one sentence>"}"""


class PromptProfile:
    """A named, hashable prompt template."""

    def __init__(self, name: str, template: str, taxonomy: Taxonomy) -> None:
        self.name = name
        self.template = template
        self.taxonomy = taxonomy

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.template.encode("utf-8")).hexdigest()

    @property
    def line_count(self) -> int:
        return len(self.template.splitlines())

    def render(self, text: str, structure: InferenceStructure | None) -> str:
        """Fill the template's placeholders.

        Uses explicit token replacement rather than ``str.format`` because
        prompt bodies contain literal JSON braces, and a profile that fails
        to render because of a brace is a profile that silently doesn't run.
        """
        s = structure or InferenceStructure()
        out = self.template
        for token, value in (
            ("{taxonomy_definitions}", self.taxonomy.definition_block()),
            ("{text}", text),
            ("{subject}", s.subject),
            ("{reason}", s.reason),
            ("{conclusion}", s.conclusion),
        ):
            out = out.replace(token, value)
        return out


_REFERENCE_TEMPLATE = """\
Classify the SINGLE PRIMARY structural reasoning failure in the argument below,
using the Navya-Nyāya hetvābhāsa taxonomy.

Taxonomy definitions:
{taxonomy_definitions}

Input text:
{text}

Extracted reasoning structure (helper only):
Subject: {subject}
Reason: {reason}
Conclusion: {conclusion}

""" + _OUTPUT_CONTRACT


def load_profile(name: str = "reference", taxonomy: Taxonomy | None = None) -> PromptProfile:
    """Load a prompt profile by name.

    ``reference`` is built from the taxonomy in-process. Any other name is
    read from ``$VYAPTI_PROMPT_DIR/<name>.txt``; if that directory is not
    configured or the file is missing, a clear error is raised rather than a
    silent fallback to the reference profile — running the wrong profile and
    not knowing is exactly the class of error this codebase is built to avoid.
    """
    tax = taxonomy or load_taxonomy()
    if name == "reference":
        return PromptProfile("reference", _REFERENCE_TEMPLATE, tax)

    prompt_dir = os.environ.get("VYAPTI_PROMPT_DIR")
    if not prompt_dir:
        raise FileNotFoundError(
            f"prompt profile {name!r} requested but VYAPTI_PROMPT_DIR is not set. "
            "Only the 'reference' profile ships with this repository; see prompts/README.md."
        )
    path = Path(prompt_dir) / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"prompt profile {name!r} not found at {path}")
    return PromptProfile(name, path.read_text(encoding="utf-8"), tax)


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def parse_verdict(response: str) -> JudgeVerdict:
    """Parse a judge response into a validated verdict.

    Raises ``MalformedJudgeResponseError`` on anything unparseable. It never
    returns a default. The Phase 1 parser coerced unrecognised labels and
    unparseable JSON to ``NONE``, which is indistinguishable from a genuine
    sound-argument verdict and quietly inflated the sound-argument rate.
    """
    if not response or not response.strip():
        raise MalformedJudgeResponseError("empty judge response", raw=response or "")

    payload = None
    try:
        payload = json.loads(response)
    except json.JSONDecodeError:
        m = _JSON_BLOCK.search(response)
        if m:
            try:
                payload = json.loads(m.group(0))
            except json.JSONDecodeError as e:
                raise MalformedJudgeResponseError(
                    f"no parseable JSON object in judge response: {e}", raw=response
                ) from e

    if payload is None:
        raise MalformedJudgeResponseError("no JSON object found in judge response", raw=response)
    if not isinstance(payload, dict):
        raise MalformedJudgeResponseError(
            f"judge returned {type(payload).__name__}, expected object", raw=response
        )

    # Drop keys the contract does not define rather than failing the whole
    # call — but record nothing silently: unknown *labels* still raise.
    allowed = {"rf_code", "confidence", "diagnosis"}
    payload = {k: v for k, v in payload.items() if k in allowed}
    payload.setdefault("diagnosis", "")

    try:
        return JudgeVerdict.model_validate(payload)
    except Exception as e:
        raise MalformedJudgeResponseError(str(e), raw=response) from e


def system_prompt() -> str:
    return _SYSTEM
