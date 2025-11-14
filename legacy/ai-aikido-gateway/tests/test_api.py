"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from src.main import app

client = TestClient(app)


def test_chat_completions_endpoint_exists():
    """Test that the /v1/chat/completions endpoint exists"""
    # Send a request without API key (should fail with 500 since no key configured)
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    # Should get an error about missing API key, not 404
    assert response.status_code != 404, "Endpoint should exist"
    assert "X-Trace-Id" in response.headers
    assert response.headers["X-Trace-Id"]


def test_chat_completions_request_validation():
    """Test that request validation works"""
    # Missing required fields
    response = client.post(
        "/v1/chat/completions",
        json={},
    )
    # Should get validation error (422)
    assert response.status_code == 422


def test_chat_completions_model_validation():
    """Test that model field is required"""
    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert response.status_code == 422


def test_trace_id_round_trip():
    """Trace middleware should honour incoming IDs."""
    incoming = uuid4().hex
    response = client.post(
        "/v1/chat/completions",
        headers={"X-Trace-Id": incoming},
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    # Trace ID must echo back even on error
    assert response.headers.get("X-Trace-Id") == incoming


def test_openapi_includes_chat_endpoint():
    """Test that OpenAPI docs include the chat completion endpoint"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "/v1/chat/completions" in openapi_spec["paths"]


def test_settings_endpoint_returns_cost_alerts():
    response = client.get("/v1/settings")
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "settings"
    assert "cost_alerts" in payload
    alerts = payload["cost_alerts"]
    assert "default" in alerts


def test_semantic_threshold_update_requires_plugin():
    """Threshold endpoint should require semantic cache plugin."""
    response = client.post(
        "/v1/cache/semantic/threshold",
        json={"similarity_threshold": 0.9},
    )
    assert response.status_code == 503
    payload = response.json()
    assert "detail" in payload


def test_semantic_search_requires_plugin():
    """Semantic search endpoint should fail without plugin."""
    response = client.post(
        "/v1/cache/semantic/search",
        json={"prompt": "hello world", "limit": 2},
    )
    assert response.status_code == 503


def test_semantic_entries_requires_plugin():
    """Semantic entries endpoint should fail without plugin."""
    response = client.get("/v1/cache/semantic/entries")
    assert response.status_code == 503
