"""Multi-provider LLM gateway.

Chat and RAG generation go through one interface, so a deployment can mix
OpenAI, Anthropic, Google Gemini and a local Ollama runtime behind a single API.
Providers are constructed lazily, discovered models are cached, and every
failure degrades to the next configured provider and finally to a deterministic
offline responder, mirroring :mod:`backend.app.services.embedding`.
"""
import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Iterable, List, Optional, Sequence

import httpx

from backend.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    GEMINI_MODEL,
    GOOGLE_API_BASE,
    GOOGLE_API_KEY,
    LLM_MODEL_CACHE_TTL,
    LLM_OFFLINE_FALLBACK,
    LLM_PROVIDER,
    LLM_REQUEST_TIMEOUT,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)

PROVIDER_OFFLINE = "offline"
PROVIDER_ORDER = ("openai", "anthropic", "google", "ollama", PROVIDER_OFFLINE)
VALID_ROLES = ("system", "user", "assistant")

# Model id fragments that never belong in a chat model picker.
_NON_CHAT_MODEL_MARKERS = (
    "embedding",
    "moderation",
    "dall-e",
    "tts",
    "whisper",
    "realtime",
    "audio",
    "image",
    "search",
    "transcribe",
    "live-api",
)
_CHAT_MODEL_MARKERS = ("gpt-", "chatgpt", "o1", "o3", "o4", "gpt5", "claude", "gemini")


class LLMError(RuntimeError):
    """Raised when a provider cannot produce a completion."""


class ProviderNotConfigured(LLMError):
    """Raised when the requested provider has no usable configuration."""


class ProviderNotFound(LLMError):
    """Raised when the requested provider name is not registered."""


@dataclass(frozen=True)
class LLMMessage:
    """A single normalised conversation turn."""

    role: str
    content: str

    @classmethod
    def from_any(cls, value: Any) -> "LLMMessage":
        """Accept a dict, an existing message, or a bare string."""
        if isinstance(value, LLMMessage):
            return value
        if isinstance(value, str):
            return cls(role="user", content=value.strip())
        if isinstance(value, dict):
            role = str(value.get("role") or "user").strip().lower()
            content = str(value.get("content") or "").strip()
            if role not in VALID_ROLES:
                raise LLMError(f"Unsupported message role: {role}")
            if not content:
                raise LLMError(f"Message with role '{role}' has no content")
            return cls(role=role, content=content)
        raise LLMError(f"Unsupported message type: {type(value).__name__}")


@dataclass(frozen=True)
class GenerationOptions:
    """Per-call overrides applied on top of the configured defaults."""

    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[float] = None

    def resolve_model(self, default: str) -> str:
        return self.model or default

    def resolve_timeout(self) -> float:
        return float(self.timeout or LLM_REQUEST_TIMEOUT)


@dataclass
class LLMResult:
    """A completed generation with provider attribution and token usage."""

    content: str
    provider: str
    model: str
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def usage(self) -> Dict[str, int]:
        return {
            "prompt": self.prompt_tokens,
            "completion": self.completion_tokens,
            "total": self.total_tokens,
        }


@dataclass(frozen=True)
class ProviderInfo:
    """Discovery payload for the provider picker."""

    name: str
    label: str
    configured: bool
    available: bool
    default_model: str
    models: List[str]
    requires_key: bool


def _chat_payload(messages: Sequence[LLMMessage]) -> List[Dict[str, str]]:
    """Drop system turns, which every provider takes as a separate argument."""
    return [
        {"role": message.role, "content": message.content}
        for message in messages
        if message.role != "system"
    ]


def _alternating_messages(messages: Sequence[LLMMessage], model_role: str) -> List[Dict[str, str]]:
    """Merge repeated roles for providers that reject them.

    Anthropic and Gemini require strictly alternating turns, so consecutive
    messages with the same role are concatenated and a leading assistant turn is
    dropped rather than failing the whole request.
    """
    merged: List[Dict[str, str]] = []
    for message in messages:
        role = model_role if message.role == "assistant" else "user"
        if not message.content.strip():
            continue
        if merged and merged[-1]["role"] == role:
            merged[-1]["content"] = f"{merged[-1]['content']}\n\n{message.content}"
            continue
        merged.append({"role": role, "content": message.content})

    while merged and merged[0]["role"] == model_role:
        merged.pop(0)
    return merged


class LLMProvider(ABC):
    """Common surface every provider adapter implements."""

    name: str = ""
    label: str = ""
    requires_key: bool = True

    @abstractmethod
    def default_model(self) -> str:
        """Model used when a caller does not request one."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the provider has everything it needs to answer."""

    @abstractmethod
    async def generate(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> LLMResult:
        """Return a complete answer in one call."""

    @abstractmethod
    def stream(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> AsyncIterator[str]:
        """Yield answer fragments as the provider produces them."""

    async def list_models(self) -> List[str]:
        """Model ids this provider can currently serve."""
        return [self.default_model()]

    async def effective_default_model(self) -> str:
        """The model that will actually serve a request right now."""
        return self.default_model()

    async def available(self) -> bool:
        """Whether the provider can serve a request right now."""
        return self.is_configured()

    async def describe(self) -> ProviderInfo:
        configured = self.is_configured()
        # Never reach out to a provider that has no credential, so discovery
        # stays free when a deployment only enables one provider.
        models = await self.list_models() if configured else []
        pinned = self.default_model()
        effective = await self.effective_default_model() if configured else pinned
        if not models:
            models = [effective]
        for preferred in (effective, pinned):
            if preferred in models:
                models = [preferred] + [model for model in models if model != preferred]
        return ProviderInfo(
            name=self.name,
            label=self.label,
            configured=configured,
            available=await self.available() if configured else False,
            default_model=effective,
            models=models,
            requires_key=self.requires_key,
        )


class OpenAIProvider(LLMProvider):
    """OpenAI chat completions, including OpenAI-compatible gateways."""

    name = "openai"
    label = "OpenAI"

    def __init__(self) -> None:
        self._client: Any | None = None

    def default_model(self) -> str:
        return OPENAI_MODEL

    def is_configured(self) -> bool:
        return bool(OPENAI_API_KEY)

    def _openai_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - depends on install extras
            raise LLMError("The openai package is not installed") from exc
        self._client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        return self._client

    @staticmethod
    def _is_chat_model(model_id: str) -> bool:
        lowered = model_id.lower()
        if any(marker in lowered for marker in _NON_CHAT_MODEL_MARKERS):
            return False
        return True

    async def list_models(self) -> List[str]:
        try:
            client = self._openai_client()
            response = await client.models.list()
        except Exception as exc:
            logger.warning("OpenAI model discovery failed (%s); using the default model", exc)
            return [self.default_model()]

        models = sorted(
            {
                str(getattr(item, "id", "")).strip()
                for item in getattr(response, "data", []) or []
                if str(getattr(item, "id", "")).strip()
            }
        )
        chat_models = [model for model in models if self._is_chat_model(model)]
        ordered = [model for model in chat_models if model.lower().startswith(_CHAT_MODEL_MARKERS)]
        ordered += [model for model in chat_models if model not in ordered]
        return ordered or chat_models or [self.default_model()]

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> LLMResult:
        options = options or GenerationOptions()
        client = self._openai_client()
        payload: List[Dict[str, str]] = _chat_payload(messages)
        if system:
            payload.insert(0, {"role": "system", "content": system})

        started = time.perf_counter()
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=options.resolve_model(self.default_model()),
                messages=payload,
                temperature=options.temperature,
                max_tokens=options.max_tokens,
            ),
            timeout=options.resolve_timeout(),
        )
        latency_ms = (time.perf_counter() - started) * 1000

        choice = response.choices[0] if response.choices else None
        usage = getattr(response, "usage", None)
        return LLMResult(
            content=(getattr(choice.message, "content", None) or "") if choice else "",
            provider=self.name,
            model=response.model or options.resolve_model(self.default_model()),
            finish_reason=getattr(choice, "finish_reason", None) or "stop",
            latency_ms=latency_ms,
            prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
        )

    async def stream(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> AsyncIterator[str]:
        options = options or GenerationOptions()
        client = self._openai_client()
        payload: List[Dict[str, str]] = _chat_payload(messages)
        if system:
            payload.insert(0, {"role": "system", "content": system})

        stream = await client.chat.completions.create(
            model=options.resolve_model(self.default_model()),
            messages=payload,
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = getattr(chunk.choices[0], "delta", None)
            text = getattr(delta, "content", None)
            if text:
                yield text


class AnthropicProvider(LLMProvider):
    """Anthropic Messages API."""

    name = "anthropic"
    label = "Anthropic"

    def __init__(self) -> None:
        self._client: Any | None = None

    def default_model(self) -> str:
        return ANTHROPIC_MODEL

    def is_configured(self) -> bool:
        return bool(ANTHROPIC_API_KEY)

    def _anthropic_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:  # pragma: no cover - depends on install extras
            raise LLMError("The anthropic package is not installed") from exc
        self._client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        return self._client

    async def list_models(self) -> List[str]:
        try:
            client = self._anthropic_client()
            response = await client.models.list()
        except Exception as exc:
            logger.warning("Anthropic model discovery failed (%s); using the default model", exc)
            return [self.default_model()]

        models = sorted(
            {
                str(getattr(item, "id", "")).strip()
                for item in getattr(response, "data", []) or []
                if str(getattr(item, "id", "")).strip()
            }
        )
        preferred = [model for model in models if model == self.default_model()]
        return preferred + [model for model in models if model not in preferred]

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> LLMResult:
        options = options or GenerationOptions()
        client = self._anthropic_client()
        model = options.resolve_model(self.default_model())

        started = time.perf_counter()
        response = await asyncio.wait_for(
            client.messages.create(
                model=model,
                max_tokens=options.max_tokens or 1024,
                system=system or "",
                messages=_alternating_messages(messages, model_role="assistant"),
                temperature=options.temperature,
            ),
            timeout=options.resolve_timeout(),
        )
        latency_ms = (time.perf_counter() - started) * 1000

        content = "".join(
            block.text
            for block in getattr(response, "content", []) or []
            if getattr(block, "type", "text") == "text"
        )
        usage = getattr(response, "usage", None)
        return LLMResult(
            content=content,
            provider=self.name,
            model=str(getattr(response, "model", model) or model),
            finish_reason=getattr(response, "stop_reason", None) or "stop",
            latency_ms=latency_ms,
            prompt_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        )

    async def stream(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> AsyncIterator[str]:
        options = options or GenerationOptions()
        client = self._anthropic_client()

        async with client.messages.stream(
            model=options.resolve_model(self.default_model()),
            max_tokens=options.max_tokens or 1024,
            system=system or "",
            messages=_alternating_messages(messages, model_role="assistant"),
            temperature=options.temperature,
        ) as stream:
            async for text in stream.text_stream:
                if text:
                    yield text


class GoogleProvider(LLMProvider):
    """Google Gemini via the generateContent REST API.

    The Gemini 3 family rejects some sampling parameters, so a 400 caused by
    sampling is retried once with temperature removed.
    """

    name = "google"
    label = "Google Gemini"

    def __init__(self) -> None:
        self._models: tuple[str, float] | None = None

    def default_model(self) -> str:
        return GEMINI_MODEL

    def is_configured(self) -> bool:
        return bool(GOOGLE_API_KEY)

    def _headers(self) -> Dict[str, str]:
        return {"x-goog-api-key": GOOGLE_API_KEY, "Content-Type": "application/json"}

    def _payload(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str],
        options: GenerationOptions,
        include_temperature: bool = True,
    ) -> Dict[str, Any]:
        generation_config: Dict[str, Any] = {}
        if options.max_tokens:
            generation_config["maxOutputTokens"] = options.max_tokens
        if include_temperature and options.temperature is not None:
            generation_config["temperature"] = options.temperature

        payload: Dict[str, Any] = {
            "contents": [
                {"role": turn["role"], "parts": [{"text": turn["content"]}]}
                for turn in _alternating_messages(messages, model_role="model")
            ]
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if generation_config:
            payload["generationConfig"] = generation_config
        return payload

    async def _post(
        self,
        method: str,
        model: str,
        payload: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        url = f"{GOOGLE_API_BASE}/models/{model}:{method}"
        async with httpx.AsyncClient(timeout=timeout or LLM_REQUEST_TIMEOUT) as client:
            return await client.post(url, headers=self._headers(), params=params, json=payload)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return
        raise LLMError(f"Gemini request failed ({response.status_code}): {response.text[:300]}")

    async def list_models(self) -> List[str]:
        if not GOOGLE_API_KEY:
            return [self.default_model()]
        cached = self._models
        if cached and time.monotonic() - cached[1] < LLM_MODEL_CACHE_TTL:
            return list(cached[0])

        models: List[str] = []
        try:
            url = f"{GOOGLE_API_BASE}/models"
            async with httpx.AsyncClient(timeout=min(LLM_REQUEST_TIMEOUT, 15.0)) as client:
                response = await client.get(url, headers=self._headers(), params={"pageSize": 200})
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("models", []) or []:
                model_id = str(item.get("name") or "").split("/")[-1].strip()
                supported = item.get("supportedGenerationMethods") or []
                if model_id and (not supported or "generateContent" in supported):
                    models.append(model_id)
        except Exception as exc:
            logger.warning("Gemini model discovery failed (%s); using the default model", exc)

        if not models:
            models = [self.default_model()]

        ordered = [self.default_model()] + [model for model in sorted(models) if model != self.default_model()]
        self._models = (tuple(ordered), time.monotonic())
        return list(ordered)

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> LLMResult:
        options = options or GenerationOptions()
        model = options.resolve_model(self.default_model())
        payload = self._payload(messages, system, options)

        started = time.perf_counter()
        response = await self._post("generateContent", model, payload, timeout=options.resolve_timeout())
        if response.status_code == 400 and options.temperature is not None:
            response = await self._post(
                "generateContent",
                model,
                self._payload(messages, system, options, include_temperature=False),
                timeout=options.resolve_timeout(),
            )
        self._raise_for_status(response)
        latency_ms = (time.perf_counter() - started) * 1000

        body = response.json()
        candidates = body.get("candidates") or []
        candidate = candidates[0] if candidates else {}
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(str(part.get("text") or "") for part in parts if part.get("text"))
        usage = body.get("usageMetadata") or {}
        return LLMResult(
            content=text,
            provider=self.name,
            model=model,
            finish_reason=candidate.get("finishReason") or "stop",
            latency_ms=latency_ms,
            prompt_tokens=int(usage.get("promptTokenCount") or 0),
            completion_tokens=int(usage.get("candidatesTokenCount") or 0),
        )

    async def stream(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> AsyncIterator[str]:
        options = options or GenerationOptions()
        model = options.resolve_model(self.default_model())
        payload = self._payload(messages, system, options)
        url = f"{GOOGLE_API_BASE}/models/{model}:streamGenerateContent"

        async with httpx.AsyncClient(timeout=options.resolve_timeout()) as client:
            async with client.stream(
                "POST", url, headers=self._headers(), params={"alt": "sse"}, json=payload
            ) as response:
                self._raise_for_status(response)
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    chunk = line[len("data:") :].strip()
                    if not chunk or chunk == "[DONE]":
                        continue
                    try:
                        body = json.loads(chunk)
                    except ValueError:
                        continue
                    for candidate in body.get("candidates") or []:
                        for part in (candidate.get("content") or {}).get("parts") or []:
                            text = part.get("text")
                            if text:
                                yield str(text)


class OllamaProvider(LLMProvider):
    """Local Ollama runtime reached over its HTTP API."""

    name = "ollama"
    label = "Ollama (local)"
    requires_key = False

    def __init__(self) -> None:
        self._reachable: tuple[bool, float] | None = None
        self._models: tuple[List[str], float] | None = None

    def default_model(self) -> str:
        return OLLAMA_MODEL

    def is_configured(self) -> bool:
        return bool(OLLAMA_BASE_URL)

    async def _is_reachable(self) -> bool:
        if not OLLAMA_BASE_URL:
            return False
        cached = self._reachable
        if cached and time.monotonic() - cached[1] < 30.0:
            return cached[0]
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            # Anything other than 200 means something else is on the port, or a
            # proxy is answering for it, so do not offer the provider.
            reachable = response.status_code == 200
        except Exception as exc:
            logger.debug("Ollama at %s is not reachable: %s", OLLAMA_BASE_URL, exc)
            reachable = False
        self._reachable = (reachable, time.monotonic())
        return reachable

    async def available(self) -> bool:
        return await self._is_reachable()

    async def list_models(self) -> List[str]:
        if not OLLAMA_BASE_URL:
            return [self.default_model()]
        cached = self._models
        if cached and time.monotonic() - cached[1] < LLM_MODEL_CACHE_TTL:
            return list(cached[0])

        models: List[str] = []
        try:
            async with httpx.AsyncClient(timeout=min(LLM_REQUEST_TIMEOUT, 10.0)) as client:
                response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            for item in response.json().get("models", []) or []:
                name = str(item.get("name") or item.get("model") or "").strip()
                if name:
                    models.append(name)
        except Exception as exc:
            logger.debug("Ollama model discovery failed: %s", exc)

        if not models:
            # Nothing is installed, or the runtime is unreachable. Report the
            # pinned model so the caller can still attempt a request.
            return [self.default_model()]

        # The runtime lists models most recently modified first, which is the
        # best available guess at what this machine is set up to serve.
        ordered = list(dict.fromkeys(models))
        self._models = (ordered, time.monotonic())
        return list(ordered)

    def _payload(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str],
        model: str,
        options: GenerationOptions,
        stream: bool,
    ) -> Dict[str, Any]:
        payload: List[Dict[str, str]] = []
        if system:
            payload.append({"role": "system", "content": system})
        payload.extend(_chat_payload(messages))

        options_body: Dict[str, Any] = {}
        if options.temperature is not None:
            options_body["temperature"] = options.temperature
        if options.max_tokens:
            options_body["num_predict"] = options.max_tokens

        body: Dict[str, Any] = {
            "model": model,
            "messages": payload,
            "stream": stream,
        }
        if options_body:
            body["options"] = options_body
        return body

    async def _resolve_model(self, options: GenerationOptions) -> str:
        """Use the requested model when the runtime has it, otherwise the first installed one."""
        requested = options.resolve_model(self.default_model())
        models = await self.list_models()
        if requested in models:
            return requested
        if models == [self.default_model()]:
            # Discovery failed, so there is nothing better to offer.
            return requested
        if any(model.split(":")[0] == requested.split(":")[0] for model in models):
            return next(model for model in models if model.split(":")[0] == requested.split(":")[0])
        logger.info(
            "Ollama model '%s' is not installed on this runtime; using '%s'",
            requested,
            models[0],
        )
        return models[0]

    async def effective_default_model(self) -> str:
        """Prefer an installed model over the pinned default, which may be absent."""
        return await self._resolve_model(GenerationOptions())

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> LLMResult:
        options = options or GenerationOptions()
        if not await self.available():
            raise ProviderNotConfigured(f"Ollama is not reachable at {OLLAMA_BASE_URL}")
        model = await self._resolve_model(options)

        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=options.resolve_timeout()) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=self._payload(messages, system, model, options, stream=False),
            )
        response.raise_for_status()
        latency_ms = (time.perf_counter() - started) * 1000

        body = response.json()
        return LLMResult(
            content=str((body.get("message") or {}).get("content") or ""),
            provider=self.name,
            model=str(body.get("model") or model),
            finish_reason="stop" if body.get("done") else "length",
            latency_ms=latency_ms,
            prompt_tokens=int(body.get("prompt_eval_count") or 0),
            completion_tokens=int(body.get("eval_count") or 0),
        )

    async def stream(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> AsyncIterator[str]:
        options = options or GenerationOptions()
        if not await self.available():
            raise ProviderNotConfigured(f"Ollama is not reachable at {OLLAMA_BASE_URL}")
        model = await self._resolve_model(options)

        async with httpx.AsyncClient(timeout=options.resolve_timeout()) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json=self._payload(messages, system, model, options, stream=True),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        body = json.loads(line)
                    except ValueError:
                        continue
                    text = (body.get("message") or {}).get("content")
                    if text:
                        yield str(text)
                    if body.get("done"):
                        break


class OfflineProvider(LLMProvider):
    """Deterministic responder used when no credentialed provider answers.

    Keeping a working path here means the chat endpoint, the RAG pipeline and CI
    all behave the same way with and without provider keys, and the reply tells
    the operator exactly which variable is missing.
    """

    name = PROVIDER_OFFLINE
    label = "Offline assistant"
    requires_key = False

    def default_model(self) -> str:
        return "deterministic"

    def is_configured(self) -> bool:
        return True

    async def available(self) -> bool:
        return True

    def _reply(self, messages: Sequence[LLMMessage], system: Optional[str]) -> str:
        return (
            "Sorry, I'm not service.\n\n"
            "No AI provider is configured for this deployment, so I cannot answer yet. "
            "Set OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY or OLLAMA_BASE_URL "
            "to enable live answers."
        )

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> LLMResult:
        started = time.perf_counter()
        content = self._reply(messages, system)
        return LLMResult(
            content=content,
            provider=self.name,
            model=self.default_model(),
            finish_reason="stop",
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=sum(len(message.content.split()) for message in messages),
            completion_tokens=len(content.split()),
        )

    async def stream(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        options: Optional[GenerationOptions] = None,
    ) -> AsyncIterator[str]:
        text = self._reply(messages, system)
        for chunk in text.split(" "):
            yield f"{chunk} "
            await asyncio.sleep(0)


@dataclass
class _Attempt:
    """Bookkeeping for one provider in a fallback chain."""

    provider: LLMProvider
    degraded: bool = False


class LLMGateway:
    """Resolve a provider, then generate with graceful degradation."""

    def __init__(self) -> None:
        self._providers: Dict[str, LLMProvider] = {}

    def _provider(self, name: str) -> LLMProvider:
        provider = self._providers.get(name)
        if provider is None:
            factory = {
                "openai": OpenAIProvider,
                "anthropic": AnthropicProvider,
                "google": GoogleProvider,
                "ollama": OllamaProvider,
                PROVIDER_OFFLINE: OfflineProvider,
            }.get(name)
            if factory is None:
                raise ProviderNotFound(
                    f"Unknown LLM provider '{name}'. Available: {', '.join(PROVIDER_ORDER)}"
                )
            provider = factory()
            self._providers[name] = provider
        return provider

    def providers(self) -> List[LLMProvider]:
        return [self._provider(name) for name in PROVIDER_ORDER]

    async def _chain(self, preferred: Optional[str]) -> List[_Attempt]:
        """Ordered fallbacks: requested provider, then configured ones, then offline."""
        if preferred:
            provider = self._provider(preferred.lower())
            if not provider.is_configured():
                raise ProviderNotConfigured(
                    f"LLM provider '{preferred}' is not configured on this deployment"
                )
            return [_Attempt(provider=provider)]

        chain: List[_Attempt] = []
        for name in PROVIDER_ORDER:
            if name == PROVIDER_OFFLINE:
                continue
            provider = self._provider(name)
            if await provider.available():
                chain.append(_Attempt(provider=provider))

        if LLM_PROVIDER:
            requested = self._provider(LLM_PROVIDER)
            if await requested.available():
                chain = [attempt for attempt in chain if attempt.provider.name != requested.name]
                chain.insert(0, _Attempt(provider=requested))
            else:
                logger.warning(
                    "LLM_PROVIDER=%s is not available on this deployment; "
                    "falling back to auto-selection",
                    LLM_PROVIDER,
                )

        if LLM_OFFLINE_FALLBACK:
            # Auto-selection never hard-fails: a provider that is reachable but
            # broken still degrades to the offline responder rather than erroring.
            chain.append(_Attempt(provider=self._provider(PROVIDER_OFFLINE), degraded=True))
        return chain

    async def resolve(
        self,
        preferred: Optional[str] = None,
    ) -> tuple[LLMProvider, bool]:
        """Return the provider that will serve a request and whether it is degraded."""
        chain = await self._chain(preferred)
        if not chain:
            raise ProviderNotConfigured("No LLM provider is configured on this deployment")
        first = chain[0]
        return first.provider, first.degraded

    async def describe(self) -> List[ProviderInfo]:
        return [await provider.describe() for provider in self.providers()]

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> LLMResult:
        """Generate an answer, trying each configured provider in turn."""
        chain = await self._chain(provider)
        if not chain:
            raise ProviderNotConfigured("No LLM provider is configured on this deployment")

        options = GenerationOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        errors: List[str] = []
        for index, attempt in enumerate(chain):
            last_candidate = index == len(chain) - 1
            try:
                result = await attempt.provider.generate(messages, system, options)
            except Exception as exc:
                errors.append(f"{attempt.provider.name}: {exc}")
                logger.warning(
                    "LLM provider %s failed (%s); %s",
                    attempt.provider.name,
                    exc,
                    "no further provider is available"
                    if last_candidate
                    else f"falling back to {chain[index + 1].provider.name}",
                )
                continue

            if result.content.strip():
                return result
            errors.append(f"{attempt.provider.name}: empty response")

        raise LLMError("Every LLM provider failed. " + "; ".join(errors))

    async def stream(
        self,
        messages: Sequence[LLMMessage],
        system: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """Stream an answer; only providers that fail before any output are skipped."""
        chain = await self._chain(provider)
        if not chain:
            raise ProviderNotConfigured("No LLM provider is configured on this deployment")

        options = GenerationOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        emitted = False
        errors: List[str] = []
        for index, attempt in enumerate(chain):
            try:
                async for chunk in attempt.provider.stream(messages, system, options):
                    emitted = True
                    if chunk:
                        yield chunk
            except Exception as exc:
                if emitted:
                    raise
                errors.append(f"{attempt.provider.name}: {exc}")
                logger.warning("LLM provider %s failed to stream (%s)", attempt.provider.name, exc)
                continue
            return

        raise LLMError("Every LLM provider failed to stream. " + "; ".join(errors))

    async def stream_events(
        self,
        messages: Sequence[LLMMessage],
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Yield ``meta``/``delta``/``done`` events for a streaming response.

        The leading ``meta`` event tells the client which provider and model
        answered before the first token arrives, so the UI can label the message
        even when a fallback provider was selected.
        """
        chain = await self._chain(kwargs.get("provider"))
        if not chain:
            raise ProviderNotConfigured("No LLM provider is configured on this deployment")

        attempt = chain[0]
        model = kwargs.get("model") or await attempt.provider.effective_default_model()
        degraded = attempt.degraded or attempt.provider.name == PROVIDER_OFFLINE
        yield {
            "event": "meta",
            "provider": attempt.provider.name,
            "model": model,
            "degraded": degraded,
        }

        started = time.perf_counter()
        text_parts: List[str] = []
        async for chunk in self.stream(messages, **kwargs):
            text_parts.append(chunk)
            yield {"event": "delta", "text": chunk}

        prompt_tokens = sum(len(message.content.split()) for message in messages)
        completion_tokens = len("".join(text_parts).split())
        yield {
            "event": "done",
            "provider": attempt.provider.name,
            "model": model,
            "degraded": degraded,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "token_usage": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": prompt_tokens + completion_tokens,
            },
        }


llm_gateway = LLMGateway()


def normalize_messages(values: Iterable[Any], limit: int | None = None) -> List[LLMMessage]:
    """Validate, drop empties and trim a conversation to the newest turns."""
    messages = [LLMMessage.from_any(value) for value in values]
    if limit is not None and len(messages) > limit:
        messages = messages[-limit:]
    return messages