"""
Gateway authentication scaffolding.

Provides lightweight validation for gateway-issued API keys based on the tenant
configuration loaded at startup. Intended as a stepping stone toward full
multi-tenant auth.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED

from src.core.config import TenantRegistry


def _is_auth_enabled(request: Request) -> bool:
    return bool(getattr(request.app.state, "auth_required", False))


def _get_tenant_registry(request: Request) -> TenantRegistry:
    registry = getattr(request.app.state, "tenant_registry", None)
    if registry is None:
        return TenantRegistry()
    return registry


def authenticate_request(request: Request) -> Optional[str]:
    """
    Validate the gateway API key if authentication is enabled.

    Returns:
        The tenant identifier when authentication succeeds, otherwise None
        if authentication is disabled.

    Raises:
        HTTPException: when authentication is required but fails.
    """
    if not _is_auth_enabled(request):
        return None

    registry = _get_tenant_registry(request)
    if registry.is_empty():
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Gateway authentication enabled but no tenants are configured.",
        )

    key_value = request.headers.get("x-gateway-key")
    if not key_value:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing gateway API key.",
        )

    match = registry.find_api_key(key_value)
    if not match:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid gateway API key.",
        )

    tenant, api_key = match
    request.state.tenant_id = tenant.tenant_id
    request.state.gateway_key_id = api_key.key_id
    return tenant.tenant_id
