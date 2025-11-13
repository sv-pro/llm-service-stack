# Playground Advanced Request Builder

**Last Updated:** 2025-10-27

## Objectives

1. Expose every meaningful parameter of the gateway’s OpenAI-compatible request so developers can experiment without leaving the dashboard.
2. Keep the UI and generated API payload in lockstep (curl snippet + raw JSON body).
3. Surface plugin/tooling metadata (e.g., LiteLLM tools, MCP references) while keeping the UX approachable.
4. Provide copy/export actions and presets that help teams share reproducible requests.

## Scope

### Editable Fields
- Model selection (including tenant-specific defaults).
- System prompt (string, optional).
- Conversation/session prompts (array editor – add/remove assistant/user messages).
- Temperature, top_p, frequency_penalty, presence_penalty.
- Max tokens vs max_completion_tokens (auto-tuned per model but override-able).
- Response format (e.g., `response_format: { "type": "json_object" }`).
- Seed/request ID to support deterministic runs.
- Custom headers (key/value table) merged into fetch request.
- Tools / MCP declarations:
  - Standard OpenAI functions schema.
  - LiteLLM toolset hints (e.g., `spider`, `bash`).
  - MCP connectors (e.g., `tools: [{ "type": "mcp", "name": "filesystem", ... }]`).
- API overrides: base URL, API version, gateway auth key (for testing only).

### Read-only/Computed
- Final JSON payload (pretty printed).
- Equivalent curl command (multi-line with headers backslash-escaped).
- Transparency notes (e.g., “`max_tokens` renamed to `max_completion_tokens` for gpt-4o”).
- Gateway metadata (tenant ID, active plugins) pulled from Settings.

### Presets & Persistence
- Local storage to remember last-used configuration (per tenant/model).
- Optional tenant-level presets (requires backend support) – nice-to-have.
- Allow export/import of presets as JSON.

## UX Outline

```
┌─────────────────────┬─────────────────────────────┐
│ Request Builder     │ CLI Preview                  │
│ ─ Model dropdown    │ curl http://...              │
│ ─ System prompt     │   -H "Authorization: Bearer" │
│ ─ Messages editor   │   -d '{ ... }'               │
│ ─ Parameters (grid) │ [Copy curl] [Copy JSON]      │
│ ─ Headers table     │ Transparency hints           │
│ ─ Tools table       │                             │
│ [Save preset] [Send]│                             │
└─────────────────────┴─────────────────────────────┘
```

## Frontend Implementation Plan

1. **State model**
   - Introduce a `requestConfig` object in React state covering prompts, params, headers, tools.
   - Use a serializer helper (`buildRequestPayload(requestConfig)`) to centralize conversions (tokens, tool schema, etc.).

2. **Form components**
   - Reuse existing prompt text area; add a messages list with add/remove rows.
   - Create parameter sliders/inputs for the numeric fields.
   - Build a generic table component for headers/tools with validation.
   - Provide tabs or accordions for advanced sections (response_format, seed, tool choices) to avoid overwhelming new users.

3. **Serialization & Preview**
   - Generate payload + curl snippet on every change using `useMemo`.
   - Ensure payload matches OpenAI schema; apply model-specific tweaks (e.g., `max_tokens` renaming).
   - Display normalization warnings (leveraging existing transparency metadata if available).

4. **Copy actions & feedback**
   - Use `navigator.clipboard.writeText` with success toasts (reusing CLI panel feedback component).
   - Offer a “Download JSON” button.

5. **Presets**
   - Store last config in `localStorage` keyed by tenant/model.
   - Provide Save/Delete preset buttons (v1 local, v2 backend sync).

## Backend / API Considerations

- No server change needed for basic functionality; gateway already accepts OpenAI payloads.
- Optional future: `/v1/playground/presets` endpoints for tenant-synced presets.
- Expose active plugin list + normalization rules via `/settings` API so UI can show tool defaults.

## Testing

- Extend Playwright suite: ensure editing fields updates previews and requests succeed.
- Add unit tests for `buildRequestPayload` covering edge cases (empty system prompt, tool arrays).
- Include guard-rail tests ensuring unauthorized headers/tools are rejected client-side.

## Timeline

1. Prototype UI without presets – 1 sprint.
2. Wire serialization + previews – mid sprint.
3. Copy feedback + local storage persistence – end sprint.
4. Optional backend presets & Settings integration – follow-up iteration.
