# Gateway Multi-Tenant Authentication & Anti-Relay Design

**Last Updated:** 2025-10-27

## Goals

1. Allow registered customers to route OpenAI-compatible traffic through the gateway using their own provider keys while maintaining cost visibility and plugin features.
2. Prevent the gateway from becoming an open relay. Every request must be tied to a known tenant with explicit quotas and logging; gateway-owned provider keys are reserved for private/system tenants only.
3. Support "internal" or "private" clients (same subnet, friendly subnet, or custom header identifier) with streamlined access controls while still auditing their usage.
4. Integrate with LiteLLM's existing auth middleware to reuse proven patterns where possible and minimise bespoke code.

## Requirements

### Tenant Identity & Registration
- Maintain a `tenants` table containing:
  - `tenant_id` (UUID or slug)
  - `name`, `contact_email`
  - `status` (active, suspended)
  - `gateway_api_key` (hashed)
  - `allowed_provider_keys` (encrypted, optional)
  - `quota_plan` (requests/day, tokens/day, etc.)
  - `allowed_subnets` (CIDR list, optional)
  - `custom_headers` (list of expected header values, optional)
- Provide an internal admin CLI/endpoint to create, rotate, and revoke credentials.

### Credential Formats
- Incoming requests must provide **two** credentials:
  1. `Authorization: Bearer <gateway_api_key>` — issued by the gateway. Required for all external tenants.
  2. Optional provider key (e.g. `OPENAI_API_KEY`) in request body or header. Stored per tenant for caching, cost attribution, and failover; validated against allow-list to avoid unbounded pass-through.
- For private tenants in trusted networks:
  - Allow requests from approved subnets to fallback to header-based hints (`X-Gateway-Tenant`) if gateway key is omitted.
  - Apply strict rate limits and logging even for internal traffic.

### Request Flow
1. **Auth plugin** (new) executes before proxies:
   - Extracts gateway key from Authorization header.
   - If missing, evaluates subnet rules and custom headers for private tenants.
   - Looks up tenant, verifies status/quota, attaches tenant metadata to `RequestContext`.
2. **Provider key resolution**:
   - If request payload contains `api_key`, ensure it matches an allow-listed key for the tenant.
   - Otherwise, inject stored tenant key (if configured) before LiteLLM proxy executes.
3. **LiteLLM proxy** executes using resolved provider key.
4. **Logging & quotas** updated in `after_response`:
   - Increment per-tenant counters.
   - Record provider usage for cost attribution.
   - Emit transparency headers `X-Gateway-Tenant`, `X-Gateway-Quota-Remaining`.

### Anti-Relay Controls
- Reject any request without tenant identification (gateway key, subnet rule, or header). Return 401 `Tenant authentication required`.
- For tenants marked "external":
  - Require gateway key on *every* request.
  - Reject unknown provider keys.
- For tenants marked "private":
  - Enforce subnet whitelists and header hints.
  - Optionally auto-issue ephemeral gateway keys for scheduled jobs that leave the trusted network.
- Add auditing:
  - Record gateway key or header used, subnet detected, and provider key fingerprint.
  - Provide dashboards to review suspicious patterns (rapid key rotation, repeated 401s).

### LiteLLM Integration
- Leverage `litellm.auth_callback` to enforce tenant checks before provider call.
- Use `litellm.override_openai_api_base` to inject tenant-specific provider URLs (if future multi-provider support requires).
- Keep the request payload OpenAI-compatible; only mutate headers / context metadata.

## Implementation Plan

1. **Data model & admin tooling**
   - Create tenant repository (SQLite or Postgres) with CLI commands for CRUD.
   - Hash gateway keys using bcrypt or Argon2.
2. **Auth plugin**
   - Pre-request hook validating credentials and quotas.
   - Dependencies: IP detection middleware, header parsing.
3. **Provider key resolver**
   - Extend LiteLLM proxy plugins to pull tenant key when missing.
   - Align with existing guard-rail behaviour (disable when no tenant key and no request key).
4. **Transparency & logging**
   - Add headers to show tenant and rate-limit state.
   - Extend RequestHistory schema with `tenant_id`, `provider_key_fingerprint`.
5. **Private network support**
   - Maintain CIDR allow list per tenant.
   - Add network middleware to compute source subnet (from `X-Forwarded-For` when behind LB).
6. **Documentation & onboarding**
   - Update README/Settings page with instructions for generating gateway keys.
   - Provide sample curl using both gateway key and tenant-provided provider key.

## Future Enhancements
- Self-service tenant portal for key rotation.
- JWT-based gateway tokens to embed quotas and metadata.
- Automated alerts when provider keys appear to be leaked (sudden unknown tenant usage).
- Shared provider key pools for cost-optimised tenants (gateway-managed).
