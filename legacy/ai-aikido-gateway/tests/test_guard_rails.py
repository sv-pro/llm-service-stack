import pytest
from fastapi.testclient import TestClient

from src.core.config import ConfigLoader
from src.api import routes
from src.main import app


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


def test_openai_guard_rail_without_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY_BACKUP", raising=False)

    with TestClient(app) as client:
        pipeline = getattr(client.app.state, "plugin_pipeline", None)
        assert pipeline is not None
        openai_plugin = next(p for p in pipeline.plugins if p.name == "openai_proxy")
        assert openai_plugin.enabled is False
        assert openai_plugin.disabled_reason and "OPENAI_API_KEY" in openai_plugin.disabled_reason

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )

    assert response.status_code == 503
    payload = response.json().get("detail")
    assert payload is not None
    assert payload["error"]["type"] == "provider_not_configured"
    assert "OPENAI_API_KEY" in payload["error"]["message"]


def test_anthropic_guard_rail_without_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY_BACKUP", raising=False)

    with TestClient(app) as client:
        pipeline = getattr(client.app.state, "plugin_pipeline", None)
        assert pipeline is not None
        anthropic_plugin = next(p for p in pipeline.plugins if p.name == "anthropic_proxy")
        assert anthropic_plugin.enabled is False
        assert anthropic_plugin.disabled_reason and "ANTHROPIC_API_KEY" in anthropic_plugin.disabled_reason

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "claude-3-haiku-20240307",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )

    assert response.status_code == 503
    payload = response.json().get("detail")
    assert payload is not None
    assert payload["error"]["type"] == "provider_not_configured"
    assert "ANTHROPIC_API_KEY" in payload["error"]["message"]
