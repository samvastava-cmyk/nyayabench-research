"""Stage 1 — rule-based recovery of the inference structure.

Splits surface text into the Nyāya triple: pakṣa (subject), hetu (reason),
sādhya (conclusion). This is cheap, deterministic and deliberately shallow —
its output is a *hint* passed to the judge, never a verdict.

Deliberate omission
-------------------
The Phase 1 implementation of this stage carried 74 content-bearing string
literals matched directly against the input — things like
``"antibiotics cure infections"``, ``"every fire produces smoke"`` and
``"sea level atmospheric pressure"`` — each one a specific benchmark item.
None of them are reproduced here. A rule layer that recognises its own test
set is not measuring generalisation.

The audit of what that tuning was worth is in ``docs/LIMITATIONS.md``: those
literals match 8.1% of the released corpus overall but only 1.7% of the v4
held-out suite the paper reports on.
"""

from __future__ import annotations

import re

from .schemas import InferenceStructure

# Explicit reason→conclusion connectives, ordered most to least specific.
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(?P<conclusion>.+?)\s+because\s+(?P<reason>.+)$", re.I), "because"),
    (re.compile(r"^(?P<conclusion>.+?)\s+due to\s+(?P<reason>.+)$", re.I), "due to"),
    (re.compile(r"^(?P<conclusion>.+?)\s+owing to\s+(?P<reason>.+)$", re.I), "owing to"),
    (re.compile(r"^(?P<conclusion>.+?),?\s+since\s+(?P<reason>.+)$", re.I), "since"),
    (re.compile(r"^(?P<reason>.+?),\s*(?:therefore|thus|hence|so)\s+(?P<conclusion>.+)$", re.I), "therefore"),
    (re.compile(r"^(?:since|given that|as)\s+(?P<reason>.+?),\s*(?P<conclusion>.+)$", re.I), "given that"),
    (re.compile(r"^(?:if)\s+(?P<reason>.+?),\s*(?:then\s+)?(?P<conclusion>.+)$", re.I), "if/then"),
)

_LEADING_CUE = re.compile(r"^(?:therefore|thus|hence|so|this proves|this means|which means)\b[,:]?\s*", re.I)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_SECOND_SENTENCE_CUE = re.compile(r"^(?:this proves|this means|therefore|thus|hence|so)\b", re.I)

# Copula / modal boundary used to guess where the subject ends.
_SUBJECT_BOUNDARY = re.compile(
    r"^(?P<subject>.+?)\s+(?:is|are|was|were|will|would|should|must|can|cannot|"
    r"could|has|have|had|does|do|did|proves?|proved|means?|shows?|seems?|appears?)\b",
    re.I,
)

_CONTRAST = re.compile(r"\b(?:but|however|except|although|though|despite|even though|whereas)\b", re.I)


def _clean(fragment: str | None) -> str:
    if not fragment:
        return ""
    return re.sub(r"\s+", " ", fragment).strip(" ,;:.—-")


def _strip_cue(text: str) -> str:
    return _clean(_LEADING_CUE.sub("", text))


def extract_subject(conclusion: str) -> str:
    """Best-effort pakṣa from the conclusion clause."""
    conclusion = _strip_cue(conclusion)
    if not conclusion:
        return ""
    m = _SUBJECT_BOUNDARY.search(conclusion)
    if m:
        return _clean(m.group("subject"))
    return _clean(conclusion.split(",", 1)[0])


def extract_reason_and_conclusion(text: str) -> tuple[str, str, str | None]:
    """Return ``(reason, conclusion, connective)``.

    Falls back to a two-sentence heuristic, then to treating the whole text
    as the conclusion with no recovered reason.
    """
    text = _clean(text)
    for pattern, name in _PATTERNS:
        m = pattern.search(text)
        if m:
            g = m.groupdict()
            return _clean(g.get("reason")), _strip_cue(_clean(g.get("conclusion"))), name

    sentences = [_clean(s) for s in _SENTENCE_SPLIT.split(text) if _clean(s)]
    if len(sentences) >= 2 and _SECOND_SENTENCE_CUE.match(sentences[1]):
        return sentences[0], _strip_cue(sentences[1]), "sentence-adjacency"

    return "", (sentences[0] if sentences else text), None


def extract_context_conditions(text: str) -> list[str]:
    """Contrastive clauses that may block an otherwise valid rule.

    Purely structural: it finds the clause introduced by a contrast marker.
    It does not know about any particular subject matter, and by design it
    cannot recognise a benchmark item.
    """
    out: list[str] = []
    for m in re.finditer(r"\b(?:but|however|except|although|though|despite|even though|whereas)\s+([^.;]+)", text, re.I):
        frag = _clean(m.group(1))
        if frag:
            out.append(frag)
    return list(dict.fromkeys(out))


def extract(text: str) -> InferenceStructure:
    """Stage 1 entry point."""
    reason, conclusion, connective = extract_reason_and_conclusion(text)
    subject = extract_subject(conclusion or text)

    # Confidence reflects how much of the triple an explicit cue gave us.
    if connective and reason and conclusion and subject:
        confidence = 0.9
    elif connective and conclusion:
        confidence = 0.6
    elif conclusion:
        confidence = 0.3
    else:
        confidence = 0.0

    return InferenceStructure(
        subject=subject,
        reason=reason,
        conclusion=conclusion,
        connective=connective,
        confidence=confidence,
    )
