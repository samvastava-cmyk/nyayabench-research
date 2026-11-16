"""A thin, provider-agnostic async chat client.

Three properties this module exists to guarantee:

1. **No hidden broker.** Phase 1 called every model through a third-party
   integration package keyed on ``EMERGENT_LLM_KEY``. When that package was
   absent the judge returned a valid-looking ``NONE`` with no error, and an
   entire experiment run was silently invalidated. Here every provider is a
   direct HTTPS call and a missing key raises at construction time.

2. **Temperature is always explicit.** The ICON paper carries a documented
   confound because temperature was set for some providers and left at the
   default for Anthropic. Every request built here carries an explicit
   temperature, for every provider, with no default-by-omission path.

3. **Full telemetry.** Responses come back with finish reason, token counts
   and latency attached, never truncated.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .schemas import UnavailableJudgeError


@dataclass
class ChatResponse:
    text: str
    finish_reason: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_ms: float
    model: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)


class RetryableHTTPError(Exception):
    """Transient failure worth retrying (429, 5xx, timeout)."""


@dataclass(frozen=True)
class ProviderSpec:
    env_var: str
    url: str
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer "


PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec("OPENAI_API_KEY", "https://api.openai.com/v1/chat/completions"),
    "anthropic": ProviderSpec(
        "ANTHROPIC_API_KEY",
        "https://api.anthropic.com/v1/messages",
        auth_header="x-api-key",
        auth_prefix="",
    ),
    "deepseek": ProviderSpec("DEEPSEEK_API_KEY", "https://api.deepseek.com/chat/completions"),
    "google": ProviderSpec(
        "GOOGLE_API_KEY",
        "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        auth_header="x-goog-api-key",
        auth_prefix="",
    ),
}


class ChatClient:
    """One client, many providers, one contract.

    Parameters
    ----------
    provider:
        One of ``PROVIDERS``.
    model:
        Provider-specific model identifier.
    temperature:
        Required. There is no default — passing it is the point.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        temperature: float,
        max_tokens: int = 1000,
        timeout: float = 120.0,
        api_key: str | None = None,
        concurrency: int = 8,
    ) -> None:
        if provider not in PROVIDERS:
            raise ValueError(f"unknown provider {provider!r}; known: {sorted(PROVIDERS)}")
        self.spec = PROVIDERS[provider]
        self.provider = provider
        self.model = model
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout = timeout
        self._sem = asyncio.Semaphore(concurrency)

        self.api_key = api_key or os.environ.get(self.spec.env_var) or ""
        if not self.api_key:
            raise UnavailableJudgeError(
                f"no API key for provider {provider!r}: set {self.spec.env_var}. "
                "Refusing to construct a client that would silently return nothing."
            )

    # -- request construction ---------------------------------------------

    def _build(self, system: str, user: str) -> tuple[str, dict[str, str], dict[str, Any]]:
        headers = {
            self.spec.auth_header: f"{self.spec.auth_prefix}{self.api_key}",
            "content-type": "application/json",
        }
        url = self.spec.url

        if self.provider == "anthropic":
            headers["anthropic-version"] = "2023-06-01"
            payload: dict[str, Any] = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,  # never omitted
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        elif self.provider == "google":
            url = url.format(model=self.model)
            payload = {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens,
                },
            }
        else:  # openai-compatible
            payload = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        return url, headers, payload

    # -- response parsing --------------------------------------------------

    def _parse(self, data: dict[str, Any], latency_ms: float) -> ChatResponse:
        if self.provider == "anthropic":
            blocks = data.get("content") or []
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            usage = data.get("usage", {})
            return ChatResponse(
                text=text,
                finish_reason=data.get("stop_reason"),
                prompt_tokens=usage.get("input_tokens"),
                completion_tokens=usage.get("output_tokens"),
                latency_ms=latency_ms,
                model=data.get("model", self.model),
                provider=self.provider,
                raw=data,
            )
        if self.provider == "google":
            cands = data.get("candidates") or []
            text = ""
            finish = None
            if cands:
                finish = cands[0].get("finishReason")
                parts = (cands[0].get("content") or {}).get("parts") or []
                text = "".join(p.get("text", "") for p in parts)
            usage = data.get("usageMetadata", {})
            return ChatResponse(
                text=text,
                finish_reason=finish,
                prompt_tokens=usage.get("promptTokenCount"),
                completion_tokens=usage.get("candidatesTokenCount"),
                latency_ms=latency_ms,
                model=self.model,
                provider=self.provider,
                raw=data,
            )
        choices = data.get("choices") or []
        text = choices[0]["message"]["content"] if choices else ""
        usage = data.get("usage", {})
        return ChatResponse(
            text=text or "",
            finish_reason=choices[0].get("finish_reason") if choices else None,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            latency_ms=latency_ms,
            model=data.get("model", self.model),
            provider=self.provider,
            raw=data,
        )

    # -- public API --------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(RetryableHTTPError),
        stop=stop_after_attempt(6),
        wait=wait_exponential_jitter(initial=2, max=60),
        reraise=True,
    )
    async def _post(self, client: httpx.AsyncClient, url, headers, payload) -> dict[str, Any]:
        try:
            r = await client.post(url, headers=headers, json=payload, timeout=self.timeout)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            raise RetryableHTTPError(str(e)) from e
        if r.status_code == 429 or r.status_code >= 500:
            raise RetryableHTTPError(f"HTTP {r.status_code}: {r.text[:400]}")
        if r.status_code >= 400:
            raise UnavailableJudgeError(f"HTTP {r.status_code} from {self.provider}: {r.text[:600]}")
        return r.json()

    async def complete(self, system: str, user: str) -> ChatResponse:
        url, headers, payload = self._build(system, user)
        async with self._sem:
            t0 = time.perf_counter()
            async with httpx.AsyncClient() as client:
                data = await self._post(client, url, headers, payload)
            latency_ms = (time.perf_counter() - t0) * 1000
        resp = self._parse(data, latency_ms)
        if not resp.text.strip():
            raise UnavailableJudgeError(
                f"{self.provider}/{self.model} returned an empty completion "
                f"(finish_reason={resp.finish_reason!r}). Aborting rather than "
                "recording this as a NONE verdict."
            )
        return resp
