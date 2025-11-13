"""Tests for the /v1/responses compatibility endpoint."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.main import app


class TestResponsesEndpoint:
    """Ensures /v1/responses forwards payloads correctly."""

    def test_responses_endpoint_proxies_to_chat_completion(self):
        client = TestClient(app)

        async def mock_chat_completion(request_data, request):
            return {
                "id": "test",
                "object": "chat.completion",
                "created": 0,
                "model": request_data.model,
                "choices": [],
                "usage": None,
                "messages": [msg.model_dump() for msg in request_data.messages],
            }

        with patch("src.api.routes.create_chat_completion", new=mock_chat_completion):
            response = client.post(
                "/v1/responses",
                json={"model": "gpt-4o-mini", "input": "hello world"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["model"] == "gpt-4o-mini"

    def test_responses_endpoint_validates_payload(self):
        client = TestClient(app)

        async def mock_chat_completion(*_, **__):  # pragma: no cover - not called
            return {}

        with patch("src.api.routes.create_chat_completion", new=AsyncMock()):
            response = client.post("/v1/responses", json={"model": "gpt-4o-mini"})

        assert response.status_code == 400
        assert "Either 'input' or 'messages' must be provided" in response.json()["detail"]
