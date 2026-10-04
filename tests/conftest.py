"""Shared test configuration.

Every test runs against the deterministic offline provider. Without this pin a
developer who exports an API key (or has Ollama running) would make the suite
call a real model, which is slow, costs money and fails on a network hiccup.
`LLM_PROVIDER` is the same switch a deployment uses to pin a provider.
"""
import pytest

from backend.app.services import llm as llm_module


@pytest.fixture(autouse=True)
def offline_llm_provider(monkeypatch):
    """Route every generation in the suite through the offline responder."""
    monkeypatch.setattr(llm_module, "LLM_PROVIDER", llm_module.PROVIDER_OFFLINE)
