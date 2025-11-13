"""
Tests for main FastAPI application and basic endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check(client: TestClient):
    """Test the health check endpoint returns 200 and correct structure."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "ai-aikido-gateway"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


@pytest.mark.unit
def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns service information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "AI Aikido Gateway"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


@pytest.mark.unit
def test_openapi_docs_available(client: TestClient):
    """Test that OpenAPI documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
