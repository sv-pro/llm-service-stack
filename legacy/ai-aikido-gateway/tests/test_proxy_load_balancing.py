import pytest

from plugins.openai_proxy import OpenAIProxyPlugin
from src.api import routes
from typing import Any, Dict


@pytest.mark.asyncio
async def test_openai_proxy_key_rotation():
    plugin = OpenAIProxyPlugin(
        name="openai_proxy",
        config={"api_keys": ["key_a", {"key": "key_b", "label": "backup"}]},
    )
    await plugin.on_startup()

    key1, meta1 = await plugin.acquire_api_key()
    key2, meta2 = await plugin.acquire_api_key()
    key3, meta3 = await plugin.acquire_api_key()

    assert key1 == "key_a"
    assert meta1["label"] == "key_1"
    assert key2 == "key_b"
    assert meta2["label"] == "backup"
    assert key3 == "key_a"
    assert meta3["index"] == 1


@pytest.mark.asyncio
async def test_call_with_retries_rotates_keys():
    attempt_log = []
    keys = [
        ("key_a", {"label": "primary", "pool_size": 2, "index": 1, "usage": 0}),
        ("key_b", {"label": "backup", "pool_size": 2, "index": 2, "usage": 0}),
    ]
    state = {"idx": 0}

    async def acquire_key(attempt: int):
        value, meta = keys[state["idx"] % len(keys)]
        state["idx"] += 1
        meta = dict(meta)
        meta["usage"] = meta.get("usage", 0) + 1
        return value, meta

    async def call_func(key: str, meta: Dict[str, Any]):
        if meta["label"] == "primary":
            raise Exception("timeout")
        return {"ok": True}

    payload = {"model": "gpt-4"}
    result, meta = await routes._call_with_retries(
        call_func,
        provider="openai",
        model_id="gpt-4",
        payload=payload,
        attempt_log=attempt_log,
        acquire_key=acquire_key,
        max_attempts=2,
        backoff_base=0,
    )

    assert result["ok"] is True
    assert meta["label"] == "backup"
    assert len(attempt_log) == 2
    assert attempt_log[0]["key"]["label"] == "primary"
    assert attempt_log[1]["key"]["label"] == "backup"
