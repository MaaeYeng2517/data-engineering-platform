"""Tests for the LLM gateway, the chat schema and the chat endpoints.

Every test runs against the offline provider: real provider credentials are
neutralised so the suite is hermetic and never touches the network.
"""
import json

import httpx
import pytest
import pytest_asyncio

import backend.app.services.llm as llm_module
from backend.app.api.chat import RateLimiter, _sse
from backend.app.schemas import ChatRequest
from backend.app.services.llm import (
    LLMError,
    LLMMessage,
    LLMGateway,
    OfflineProvider,
    normalize_messages,
)
from backend.main import app


@pytest.fixture(autouse=True)
def isolated_providers(monkeypatch):
    """Disable credentialed providers so results never depend on the host env."""
    monkeypatch.setattr(llm_module, "OPENAI_API_KEY", "")
    monkeypatch.setattr(llm_module, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(llm_module, "GOOGLE_API_KEY", "")
    monkeypatch.setattr(llm_module, "OLLAMA_BASE_URL", "")
    monkeypatch.setattr(llm_module, "LLM_PROVIDER", "")
    monkeypatch.setattr(llm_module, "LLM_OFFLINE_FALLBACK", True)


class BrokenProvider(OfflineProvider):
    """A provider that looks healthy but always fails, for fallback coverage."""

    name = "openai"
    label = "Broken"
    default_model_name = "broken-1"

    def default_model(self) -> str:
        return self.default_model_name

    def is_configured(self) -> bool:
        return True

    async def available(self) -> bool:
        return True

    async def generate(self, messages, system=None, options=None):
        raise LLMError("provider exploded")

    async def stream(self, messages, system=None, options=None):
        raise LLMError("provider exploded")
        yield ""  # pragma: no cover - marks this as an async generator


# --- message normalisation ---------------------------------------------------


def test_message_from_dict_and_string():
    assert LLMMessage.from_any({"role": "assistant", "content": " hi "}) == LLMMessage(
        role="assistant", content="hi"
    )
    assert LLMMessage.from_any("hello") == LLMMessage(role="user", content="hello")


def test_message_rejects_unknown_role_and_blank_content():
    with pytest.raises(LLMError):
        LLMMessage.from_any({"role": "root", "content": "sudo"})
    with pytest.raises(LLMError):
        LLMMessage.from_any({"role": "user", "content": "   "})
    with pytest.raises(LLMError):
        LLMMessage.from_any(object())


def test_normalize_messages_keeps_newest_turns():
    messages = normalize_messages(
        [
            {"role": "user", "content": "one"},
            {"role": "assistant", "content": "two"},
            {"role": "user", "content": "three"},
        ],
        limit=2,
    )
    assert [message.content for message in messages] == ["two", "three"]


def test_alternating_messages_merges_and_drops_leading_model_turn():
    turns = llm_module._alternating_messages(
        [
            LLMMessage("assistant", "unsolicited"),
            LLMMessage("user", "first"),
            LLMMessage("user", "second"),
            LLMMessage("assistant", "reply"),
        ],
        model_role="model",
    )
    assert turns == [
        {"role": "user", "content": "first\n\nsecond"},
        {"role": "model", "content": "reply"},
    ]


# --- gateway ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_offline_provider_reports_the_missing_configuration():
    provider = OfflineProvider()
    result = await provider.generate([LLMMessage("user", "What is DataAir?")])

    assert result.provider == "offline"
    assert "Sorry, I'm not service" in result.content
    assert "OPENAI_API_KEY" in result.content
    assert result.usage()["total"] > 0


@pytest.mark.asyncio
async def test_offline_stream_reassembles_into_one_answer():
    provider = OfflineProvider()
    chunks = [chunk async for chunk in provider.stream([LLMMessage("user", "hi")])]
    assert len(chunks) > 1
    assert "".join(chunks).strip() == (
        await provider.generate([LLMMessage("user", "hi")])
    ).content.strip()


@pytest.mark.asyncio
async def test_gateway_falls_back_to_offline_when_a_provider_fails():
    gateway = LLMGateway()
    gateway._providers["openai"] = BrokenProvider()

    result = await gateway.generate([LLMMessage("user", "hello")])

    assert result.provider == "offline"
    assert result.content.strip()


@pytest.mark.asyncio
async def test_gateway_stream_falls_back_before_any_token_is_emitted():
    gateway = LLMGateway()
    gateway._providers["openai"] = BrokenProvider()

    text = "".join(
        [chunk async for chunk in gateway.stream([LLMMessage("user", "hello")])]
    )
    assert "Sorry, I'm not service" in text


@pytest.mark.asyncio
async def test_gateway_stream_events_carry_meta_delta_and_done():
    events = [
        event
        async for event in LLMGateway().stream_events([LLMMessage("user", "hello")])
    ]
    assert events[0]["event"] == "meta"
    assert events[0]["provider"] == "offline"
    assert any(event["event"] == "delta" for event in events)
    done = events[-1]
    assert done["event"] == "done"
    assert done["degraded"] is True
    assert done["token_usage"]["total"] > 0


@pytest.mark.asyncio
async def test_gateway_rejects_unknown_and_unconfigured_providers():
    gateway = LLMGateway()

    with pytest.raises(llm_module.ProviderNotFound):
        await gateway.generate([LLMMessage("user", "hi")], provider="does-not-exist")
    with pytest.raises(llm_module.ProviderNotConfigured):
        await gateway.generate([LLMMessage("user", "hi")], provider="anthropic")


@pytest.mark.asyncio
async def test_gateway_without_fallback_raises_instead_of_degrading(monkeypatch):
    monkeypatch.setattr(llm_module, "LLM_OFFLINE_FALLBACK", False)
    gateway = LLMGateway()
    gateway._providers["openai"] = BrokenProvider()

    with pytest.raises(LLMError):
        await gateway.generate([LLMMessage("user", "hi")])


@pytest.mark.asyncio
async def test_describe_never_calls_an_unconfigured_provider():
    infos = {info.name: info for info in await LLMGateway().describe()}

    assert infos["anthropic"].configured is False
    assert infos["anthropic"].available is False
    assert infos["anthropic"].models == ["claude-haiku-4-5"]
    assert infos["offline"].available is True


# --- request schema ---------------------------------------------------------


def test_chat_request_accepts_history_and_appends_the_new_message():
    request = ChatRequest(
        messages=[{"role": "user", "content": "first"}, {"role": "assistant", "content": "reply"}],
        message="  second  ",
    )
    turns = request.turns()
    assert [turn.role for turn in turns] == ["user", "assistant", "user"]
    assert turns[-1].content == "second"


def test_chat_request_requires_input_and_a_trailing_user_turn():
    with pytest.raises(ValueError):
        ChatRequest()
    with pytest.raises(ValueError):
        ChatRequest(messages=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "bye"}])
    with pytest.raises(ValueError):
        ChatRequest(message="   ")


# --- rate limiting ----------------------------------------------------------


def test_rate_limiter_allows_a_full_window_then_blocks():
    limiter = RateLimiter(limit=3, window_seconds=60)

    assert [limiter.check("1.2.3.4")[0] for _ in range(4)] == [True, True, True, False]
    # A different caller keeps its own budget.
    assert limiter.check("5.6.7.8")[0] is True
    blocked, retry_after = limiter.check("1.2.3.4")
    assert blocked is False
    assert retry_after > 0


def test_sse_frames_are_utf8_and_machine_readable():
    frame = _sse("delta", {"text": "สวัสดี"})
    assert frame.endswith(b"\n\n")
    assert b"event: delta" in frame
    assert json.loads(frame.decode("utf-8").split("data: ")[1])["text"] == "สวัสดี"


# --- endpoints --------------------------------------------------------------


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_providers_endpoint_lists_every_provider(client):
    response = await client.get("/api/v1/chat/providers")
    assert response.status_code == 200

    body = response.json()
    names = {provider["name"] for provider in body["providers"]}
    assert names == {"openai", "anthropic", "google", "ollama", "offline"}
    assert body["default_provider"] == "offline"
    assert body["degraded"] is True


@pytest.mark.asyncio
async def test_chat_endpoint_answers_without_authentication(client):
    response = await client.post(
        "/api/v1/chat", json={"message": "What is DataAir?", "provider": "offline"}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["provider"] == "offline"
    assert body["degraded"] is True
    assert "Sorry, I'm not service" in body["answer"]
    assert body["token_usage"]["total"] > 0


@pytest.mark.asyncio
async def test_chat_endpoint_rejects_an_unknown_provider(client):
    response = await client.post(
        "/api/v1/chat", json={"message": "hi", "provider": "not-a-provider"}
    )
    assert response.status_code == 400
    assert "not-a-provider" in response.json()["detail"]


@pytest.mark.asyncio
async def test_chat_endpoint_rejects_an_empty_body(client):
    response = await client.post("/api/v1/chat", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stream_endpoint_emits_meta_deltas_and_done(client):
    async with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"message": "stream this", "provider": "offline"},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join([chunk async for chunk in response.aiter_text()])

    events = [
        json.loads(line[len("data: ") :])
        for line in body.splitlines()
        if line.startswith("data: ")
    ]
    kinds = [event["event"] for event in events]
    assert kinds[0] == "meta"
    assert kinds[-1] == "done"
    assert "delta" in kinds
    assert "".join(event.get("text", "") for event in events if event["event"] == "delta").strip()
    assert events[-1]["sources"] == []
