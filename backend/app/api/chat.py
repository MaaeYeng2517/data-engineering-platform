"""Chat API backed by the multi-provider LLM gateway.

The endpoints are public so the marketing site can offer a live assistant, so
they are rate limited per caller and never accept a client-supplied system
prompt. Authenticated callers may additionally ground an answer in knowledge
bases by passing ``kb_ids``.
"""
import json
import logging
import time
from collections import deque
from dataclasses import asdict
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.dependencies import get_optional_user
from backend.app.models.user import User
from backend.app.schemas import (
    ChatProviderInfo,
    ChatProvidersResponse,
    ChatRequest,
    ChatResponse,
    ChatSource,
    ChatTurn,
)
from backend.app.services.llm import (
    PROVIDER_OFFLINE,
    LLMError,
    LLMMessage,
    ProviderNotConfigured,
    ProviderNotFound,
    llm_gateway,
)
from backend.config import (
    CHAT_MAX_CONTEXT_CHARS,
    CHAT_MAX_MESSAGES,
    CHAT_MAX_TOKENS,
    CHAT_RATE_LIMIT_REQUESTS,
    CHAT_RATE_LIMIT_WINDOW_SECONDS,
    CHAT_SYSTEM_PROMPT,
    CHAT_TEMPERATURE,
)

logger = logging.getLogger(__name__)

router = APIRouter()

GROUNDING_LIMIT = 5
GROUNDING_SNIPPET_CHARS = 1200
MAX_TRACKED_CALLERS = 10_000

_GROUNDING_INSTRUCTIONS = (
    "\n\nYou are answering with passages retrieved from the user's knowledge "
    "bases. Use only what those passages support, cite them as [1], [2] and so "
    "on, and say plainly when the answer is not in them."
)


class RateLimiter:
    """Sliding-window limiter that keeps memory bounded."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = max(1, limit)
        self._window = max(1, window_seconds)
        self._hits: Dict[str, deque[float]] = {}

    def check(self, key: str) -> Tuple[bool, int]:
        """Record a hit and report whether it is allowed, plus a retry hint."""
        now = time.monotonic()
        bucket = self._hits.get(key)
        if bucket is None:
            bucket = self._hits[key] = deque()
        while bucket and now - bucket[0] >= self._window:
            bucket.popleft()

        if len(bucket) >= self._limit:
            return False, max(1, int(self._window - (now - bucket[0])) + 1)

        bucket.append(now)
        if len(self._hits) > MAX_TRACKED_CALLERS:
            self._evict(now)
        return True, 0

    def _evict(self, now: float) -> None:
        stale = [
            key
            for key, bucket in self._hits.items()
            if not bucket or now - bucket[-1] >= self._window
        ]
        for key in stale:
            self._hits.pop(key, None)
        # Still oversized under a flood of distinct callers: drop the oldest half.
        if len(self._hits) > MAX_TRACKED_CALLERS:
            oldest = sorted(self._hits.items(), key=lambda item: item[1][-1])[
                : len(self._hits) // 2
            ]
            for key, _ in oldest:
                self._hits.pop(key, None)


rate_limiter = RateLimiter(CHAT_RATE_LIMIT_REQUESTS, CHAT_RATE_LIMIT_WINDOW_SECONDS)


def _caller_key(request: Request, user: Optional[User]) -> str:
    if user is not None:
        return f"user:{user.id}"
    client = request.client
    return f"ip:{client.host if client else 'unknown'}"


def _enforce_rate_limit(request: Request, user: Optional[User]) -> None:
    allowed, retry_after = rate_limiter.check(_caller_key(request, user))
    if allowed:
        return
    logger.warning("Chat rate limit exceeded for %s", _caller_key(request, user))
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Too many chat requests. Try again in {retry_after}s.",
    )


def _to_messages(turns: Sequence[ChatTurn]) -> List[LLMMessage]:
    return [
        LLMMessage(role=turn.role, content=turn.content)
        for turn in turns[-CHAT_MAX_MESSAGES:]
    ]


async def _grounded_context(
    question: str, kb_ids: Sequence[Any], db: AsyncSession | None = None
) -> Tuple[str, List[ChatSource]]:
    """Retrieve passages for the question and turn them into prompt context."""
    if not kb_ids:
        return "", []

    from backend.app.services.retrieval import retrieval_engine

    try:
        result = await retrieval_engine.search(
            question, [str(kb_id) for kb_id in kb_ids], limit=GROUNDING_LIMIT, db=db
        )
    except Exception as exc:
        logger.warning("Grounding retrieval failed: %s", exc)
        return "", []

    blocks: List[str] = []
    sources: List[ChatSource] = []
    budget = CHAT_MAX_CONTEXT_CHARS
    for item in result.get("results", []):
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        metadata = item.get("metadata") or {}
        snippet = content[:GROUNDING_SNIPPET_CHARS]
        blocks.append(f"[{len(blocks) + 1}] {snippet}")
        sources.append(
            ChatSource(
                id=str(item.get("doc_id") or item.get("chunk_id") or len(blocks)),
                title=str(metadata.get("title") or "") or None,
                snippet=snippet,
                score=round(float(item.get("hybrid_score") or 0.0), 4),
            )
        )
        budget -= len(snippet)
        if budget <= 0:
            break

    if not blocks:
        return "", []
    return "\n\n".join(blocks) + _GROUNDING_INSTRUCTIONS, sources


def _system_prompt(context: str) -> str:
    return CHAT_SYSTEM_PROMPT if not context else CHAT_SYSTEM_PROMPT + context


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (ProviderNotFound, ProviderNotConfigured)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


def _sse(event: str, data: Dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


@router.get("/providers", response_model=ChatProvidersResponse)
async def list_providers():
    """Report which providers and models this deployment can actually serve."""
    try:
        infos = await llm_gateway.describe()
        default_provider, degraded = await llm_gateway.resolve()
    except LLMError as exc:
        raise _http_error(exc) from exc

    return ChatProvidersResponse(
        providers=[ChatProviderInfo(**asdict(info)) for info in infos],
        default_provider=default_provider.name,
        default_model=await default_provider.effective_default_model(),
        degraded=degraded,
    )


@router.post("", response_model=ChatResponse)
async def create_chat_completion(
    payload: ChatRequest,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Answer a chat turn with the selected or automatically resolved provider."""
    _enforce_rate_limit(request, user)

    turns = payload.turns()
    messages = _to_messages(turns)
    question = messages[-1].content
    context, sources = await _grounded_context(question, payload.kb_ids, db=db)

    try:
        result = await llm_gateway.generate(
            messages,
            system=_system_prompt(context),
            provider=payload.provider,
            model=payload.model,
            temperature=CHAT_TEMPERATURE if payload.temperature is None else payload.temperature,
            max_tokens=CHAT_MAX_TOKENS if payload.max_tokens is None else payload.max_tokens,
        )
    except LLMError as exc:
        logger.warning("Chat completion failed: %s", exc)
        raise _http_error(exc) from exc

    return ChatResponse(
        answer=result.content,
        provider=result.provider,
        model=result.model,
        finish_reason=result.finish_reason,
        latency_ms=round(result.latency_ms, 2),
        token_usage=result.usage(),
        sources=sources,
        degraded=result.provider == PROVIDER_OFFLINE,
    )


@router.post("/stream")
async def stream_chat_completion(
    payload: ChatRequest,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream the same answer as server-sent events.

    Emits ``meta`` (provider and model), then ``delta`` events, then ``done``.
    A failure after the first delta cannot be retried on another provider, so it
    is reported as an ``error`` event.
    """
    _enforce_rate_limit(request, user)

    turns = payload.turns()
    messages = _to_messages(turns)
    question = messages[-1].content
    context, sources = await _grounded_context(question, payload.kb_ids, db=db)

    options = {
        "system": _system_prompt(context),
        "provider": payload.provider,
        "model": payload.model,
        "temperature": CHAT_TEMPERATURE if payload.temperature is None else payload.temperature,
        "max_tokens": CHAT_MAX_TOKENS if payload.max_tokens is None else payload.max_tokens,
    }

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            async for event in llm_gateway.stream_events(messages, **options):
                if event["event"] == "done":
                    event = {**event, "sources": [source.model_dump() for source in sources]}
                yield _sse(event["event"], event)
        except Exception as exc:  # noqa: BLE001 - surfaced to the client as an event
            logger.warning("Chat stream failed: %s", exc)
            detail = str(exc) if isinstance(exc, LLMError) else "The chat stream ended unexpectedly."
            yield _sse("error", {"detail": detail[:400]})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )