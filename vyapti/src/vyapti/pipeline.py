"""The three-stage classifier, assembled.

    text ──▶ [1] rule-based extraction ──▶ [2] LLM judge ──▶ [3] arbitration ──▶ label

Stage 1 is deterministic and free. Stage 2 is the only network call. Stage 3
is deterministic and logged.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from .arbitration import arbitrate
from .client import ChatClient
from .extract import extract
from .judge import PromptProfile, load_profile, parse_verdict, system_prompt
from .schemas import (
    CaseResult,
    MalformedJudgeResponseError,
    RFCode,
    UnavailableJudgeError,
)
from .taxonomy import Taxonomy, load_taxonomy


class VyaptiPipeline:
    """Classify arguments into hetvābhāsa categories."""

    def __init__(
        self,
        client: ChatClient,
        profile: PromptProfile | None = None,
        taxonomy: Taxonomy | None = None,
        use_arbitration: bool = True,
    ) -> None:
        self.client = client
        self.taxonomy = taxonomy or load_taxonomy()
        self.profile = profile or load_profile("reference", self.taxonomy)
        self.use_arbitration = use_arbitration

    async def classify(
        self,
        text: str,
        *,
        case_id: str = "adhoc",
        suite: str = "adhoc",
        gold_label: RFCode | None = None,
        run_id: str = "adhoc",
        arm: str = "adhoc",
        repeat: int = 0,
    ) -> CaseResult:
        """Run one case end to end.

        On judge failure the result is returned with ``status="error"`` and
        ``final_label=None`` — never with a fabricated label. Callers decide
        whether an error aborts the run; ``runner.py`` aborts on the smoke
        test and records-and-continues thereafter, so a single bad response
        cannot masquerade as a sound argument in the aggregate.
        """
        base = CaseResult(
            case_id=case_id,
            suite=suite,
            text=text,
            gold_label=gold_label,
            run_id=run_id,
            arm=arm,
            repeat=repeat,
            model=self.client.model,
            provider=self.client.provider,
            temperature=self.client.temperature,
            max_tokens=self.client.max_tokens,
            prompt_profile=self.profile.name,
            prompt_sha256=self.profile.sha256,
            taxonomy_version=self.taxonomy.version,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Stage 1 — deterministic
        structure = extract(text)
        base.structure = structure

        # Stage 2 — the judge
        rendered = self.profile.render(text, structure)
        try:
            response = await self.client.complete(system_prompt(), rendered)
        except UnavailableJudgeError as e:
            base.status = "error"
            base.error_type = "UnavailableJudgeError"
            base.error_detail = str(e)
            return base

        base.raw_response = response.text
        base.finish_reason = response.finish_reason
        base.prompt_tokens = response.prompt_tokens
        base.completion_tokens = response.completion_tokens
        base.latency_ms = response.latency_ms

        try:
            verdict = parse_verdict(response.text)
        except MalformedJudgeResponseError as e:
            base.status = "error"
            base.error_type = "MalformedJudgeResponseError"
            base.error_detail = str(e)
            return base

        base.judge_verdict = verdict

        # Stage 3 — deterministic arbitration
        final, steps = arbitrate(text, verdict.rf_code, structure, enabled=self.use_arbitration)
        base.arbitration = steps
        base.final_label = final
        return base

    @property
    def fingerprint(self) -> str:
        """A stable hash of everything that could change a result."""
        parts = "|".join(
            [
                self.client.provider,
                self.client.model,
                f"{self.client.temperature}",
                f"{self.client.max_tokens}",
                self.profile.name,
                self.profile.sha256,
                self.taxonomy.version,
                f"arb={self.use_arbitration}",
            ]
        )
        return hashlib.sha256(parts.encode()).hexdigest()[:16]
