import json
import sqlite3
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from core.config import ConfigLoader
from src.main import app
from src.api import routes


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self):
        return self._payload

    def dict(self):
        return self._payload

    def json(self):
        return json.dumps(self._payload)


def _fetch_rows(db_path: str, query: str):
    connection = sqlite3.connect(db_path)
    try:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def _get_history_entries(db_path):
    if not db_path.exists():
        return []
    return _fetch_rows(str(db_path), "SELECT * FROM requests ORDER BY id ASC")


def _get_cache_entries(db_path):
    if not db_path.exists():
        return []
    return _fetch_rows(str(db_path), "SELECT * FROM cache_entries ORDER BY rowid ASC")


@pytest.fixture(autouse=True)
def _patch_plugin_data_paths(monkeypatch, tmp_path):
    original_load = ConfigLoader.load_plugin_configs

    def patched(self):
        configs = original_load(self)
        for cfg in configs:
            if cfg.name in {"history", "cache"}:
                cfg.config["db_path"] = str(tmp_path / f"{cfg.name}.db")
            elif cfg.name == "semantic_cache":
                # Disable semantic cache in tests to avoid memory leaks
                cfg.enabled = False
        return configs

    monkeypatch.setattr(ConfigLoader, "load_plugin_configs", patched)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    async def _sleep(_):
        return None

    monkeypatch.setattr(routes.asyncio, "sleep", _sleep)


@pytest.fixture
def openai_plugin_state(client):
    if not hasattr(app.state, "openai_proxy_plugin"):
        client.get("/health")
    plugin = app.state.openai_proxy_plugin
    original = deepcopy(plugin.api_keys)
    original_index = getattr(plugin, "_key_index", 0)
    original_enabled = plugin.enabled
    # Don't replace the lock - it's bound to the app's event loop
    plugin.enabled = True
    plugin.disabled_reason = None
    plugin.api_keys = [
        {"value": "openai-key-a", "label": "primary", "index": 1, "usage": 0},
        {"value": "openai-key-b", "label": "backup", "index": 2, "usage": 0},
    ]
    plugin._key_index = 0
    yield plugin
    plugin.api_keys = original
    plugin._key_index = original_index
    plugin.enabled = original_enabled
    plugin.disabled_reason = getattr(plugin, "disabled_reason", None)


@pytest.fixture
def anthropic_plugin_state(client):
    if not hasattr(app.state, "anthropic_proxy_plugin"):
        client.get("/health")
    plugin = app.state.anthropic_proxy_plugin
    original = deepcopy(plugin.api_keys)
    original_index = getattr(plugin, "_key_index", 0)
    original_enabled = plugin.enabled
    # Don't replace the lock - it's bound to the app's event loop
    plugin.enabled = True
    plugin.disabled_reason = None
    plugin.api_keys = [
        {"value": "anthropic-key", "label": "primary", "index": 1, "usage": 0},
    ]
    plugin._key_index = 0
    yield plugin
    plugin.api_keys = original
    plugin._key_index = original_index
    plugin.enabled = original_enabled
    plugin.disabled_reason = getattr(plugin, "disabled_reason", None)


def test_openai_happy_path(monkeypatch, client, openai_plugin_state, tmp_path):
    _ = openai_plugin_state  # Fixture used for side effects
    async def fake_acompletion(**kwargs):
        payload = {
            "id": "test",
            "object": "chat.completion",
            "created": 0,
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        return FakeResponse(payload)

    monkeypatch.setattr(routes.litellm, "acompletion", fake_acompletion)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "hi"}],
        },
    )

    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id")
    assert response.headers.get("X-Trace-Id")
    data = response.json()
    assert data["choices"][0]["message"]["content"] == "Hello!"
    assert "X-Gateway-Retries" in response.headers
    assert "openai" in response.headers["X-Gateway-Retries"]

    history_entries = _get_history_entries(tmp_path / "history.db")
    assert len(history_entries) == 1
    history_entry = history_entries[0]
    assert history_entry["model"] == "gpt-3.5-turbo"
    assert history_entry["cached"] == 0
    assert history_entry["response_text"] == "Hello!"

    cache_entries = _get_cache_entries(tmp_path / "cache.db")
    assert len(cache_entries) == 1
    cache_entry = cache_entries[0]
    assert cache_entry["model"] == "gpt-3.5-turbo"


def test_openai_fallback_sequence(monkeypatch, client, openai_plugin_state, tmp_path):
    _ = openai_plugin_state  # Fixture used for side effects
    call_counter = {"count": 0}

    async def fake_acompletion(**kwargs):
        call_counter["count"] += 1
        if call_counter["count"] < 4:
            raise Exception("timeout talking to provider")
        payload = {
            "id": "fallback",
            "object": "chat.completion",
            "created": 0,
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Recovered"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        return FakeResponse(payload)

    monkeypatch.setattr(routes.litellm, "acompletion", fake_acompletion)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "fallback please"}],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["content"] == "Recovered"
    # Fallback should have switched to gpt-3.5 model
    assert data["model"].startswith("gpt-3.5") or "gpt-3.5" in response.headers["X-Gateway-Retries"]
    # Retry header should mention fallback
    assert "fallback" in response.headers["X-Gateway-Retries"].lower()

    history_entries = _get_history_entries(tmp_path / "history.db")
    assert len(history_entries) == 1
    history_entry = history_entries[0]
    assert history_entry["model"] == "gpt-4"
    assert history_entry["cached"] == 0
    assert history_entry["response_text"] == "Recovered"

    cache_entries = _get_cache_entries(tmp_path / "cache.db")
    assert len(cache_entries) == 1
    cache_entry = cache_entries[0]
    assert cache_entry["model"] == "gpt-4"

    # Second identical request should be served from cache without new provider calls
    response_cached = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "fallback please"}],
        },
    )

    assert response_cached.status_code == 200
    assert response_cached.json()["choices"][0]["message"]["content"] == "Recovered"
    # No additional provider invocations should occur thanks to cache hit
    assert call_counter["count"] == 4

    history_entries = _get_history_entries(tmp_path / "history.db")
    assert len(history_entries) == 2
    assert history_entries[1]["cached"] == 1


def test_anthropic_happy_path(monkeypatch, client, anthropic_plugin_state, tmp_path):
    _ = anthropic_plugin_state  # Fixture used for side effects
    async def fake_acompletion(**kwargs):
        assert kwargs.get("custom_llm_provider") == "anthropic"
        payload = {
            "id": "anthropic",
            "object": "chat.completion",
            "created": 0,
            "model": kwargs.get("model", "claude-3-haiku-20240307"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hi from Claude"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        return FakeResponse(payload)

    monkeypatch.setattr(routes.litellm, "acompletion", fake_acompletion)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "claude-3-haiku-20240307",
            "messages": [{"role": "user", "content": "anthropic"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["choices"][0]["message"]["content"] == "Hi from Claude"

    history_entries = _get_history_entries(tmp_path / "history.db")
    assert len(history_entries) == 1
    history_entry = history_entries[0]
    assert history_entry["model"] == "claude-3-haiku-20240307"
    assert history_entry["cached"] == 0
    assert history_entry["response_text"] == "Hi from Claude"

    cache_entries = _get_cache_entries(tmp_path / "cache.db")
    assert len(cache_entries) == 1
    cache_entry = cache_entries[0]
    assert cache_entry["model"] == "claude-3-haiku-20240307"


def test_openai_all_attempts_fail_exposes_retry_headers(monkeypatch, client, openai_plugin_state, tmp_path):
    _ = openai_plugin_state  # Fixture used for side effects
    async def failing_acompletion(**kwargs):
        raise Exception("provider outage")

    monkeypatch.setattr(routes.litellm, "acompletion", failing_acompletion)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "cause failure"}],
        },
    )

    assert response.status_code == 502
    detail = response.json().get("detail", {})
    error_payload = detail.get("error", {})
    assert "provider outage" in error_payload.get("message", "")

    assert "X-Gateway-Retries" in response.headers
    retries_header = response.headers["X-Gateway-Retries"].lower()
    assert "openai:gpt-4" in retries_header
    assert "fallback error" in retries_header

    # Failed requests shouldn't persist cache/history rows
    assert _get_history_entries(tmp_path / "history.db") == []
    assert _get_cache_entries(tmp_path / "cache.db") == []
