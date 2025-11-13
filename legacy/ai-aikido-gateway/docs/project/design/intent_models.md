# Intent & Playbook Data Model Specification

**Related roadmap stage:** [Stage 1 — Intent & Template Models](../ROADMAP.md#stage-1--intent--template-models-11-15-weeks)  
**Status:** Draft for implementation  
**Last updated:** 2025-11-02

This document describes the schema, storage layer, and API touch points required to persist the Intent → Template → Playbook → Execution hierarchy. It is the foundation for Stage 1 of the unified roadmap and feeds directly into later stages (Execution Engine, Builder UX, Routing, Feedback).

---

## 1. Domain Entities

| Entity | Purpose | Storage | Implementing Module |
|--------|---------|---------|---------------------|
| `Intent` | Describes *what* needs to be achieved (goal, inputs, outputs). | `intents` table | `src/core/models/intent.py` (`IntentRecord`) |
| `Template` | Reusable prompt/plan skeleton reused by multiple intents. | `templates` table | `src/core/models/template.py` (`TemplateRecord`) |
| `Playbook` | Concrete executable plan referencing steps and tools. | `playbooks` table | `src/core/models/playbook.py` (`PlaybookRecord`) |
| `Execution` | Runtime instance of a playbook run with metrics. | `executions` table | `src/core/models/execution.py` (`ExecutionRecord`) |

Each table should include `id`, `created_at`, `updated_at`, and soft delete (`archived_at`) timestamps for governance.

---

## 2. Pydantic Model Sketches

```python
# src/core/models/intent.py
class IntentRecord(BaseModel):
    id: UUID
    name: str
    slug: str  # unique, e.g. "incident.triage"
    goal: str
    input_schema: dict[str, Any]  # JSON Schema snippet
    output_schema: dict[str, Any]
    template_refs: list[str]  # `template@v#` identifiers
    embedding_vector: list[float] | None  # populated when vector inference runs
    tags: list[str] = []
    archived_at: datetime | None = None
```

```python
# src/core/models/template.py
class TemplateRecord(BaseModel):
    id: UUID
    name: str
    version: str  # `template@v1`
    content: str  # markdown or prompt DSL
    slots: list[TemplateSlot]
    registry_metadata: dict[str, Any] = {}
    checksum: str
```

```python
# src/core/models/playbook.py
class PlaybookRecord(BaseModel):
    id: UUID
    name: str  # aligns with intent slug
    version: str  # `playbook@v2`
    steps: list[PlaybookStep]
    tools_required: list[str]  # keys into capability registry
    budget_limits: dict[str, float]  # e.g. {"usd": 1.50, "latency_ms": 1500}
    policy_flags: list[str]
    template_ref: str | None  # back-reference to guiding template
```

```python
# src/core/models/execution.py
class ExecutionRecord(BaseModel):
    id: UUID
    playbook_ref: str  # `incident.triage@v2`
    intent_ref: str
    status: Literal["pending", "success", "failed"]
    metrics: ExecutionMetrics
    trace_id: str
    started_at: datetime
    finished_at: datetime | None
    feedback_ids: list[UUID] = []
```

Helper models (`TemplateSlot`, `PlaybookStep`, `ExecutionMetrics`) should live alongside these definitions for reuse by API serializers.

---

## 3. Data Relationships

```
Intent 1 ────┐
             ├── Template (versioned)
Intent n ────┘           │
                         ▼
                Playbook (versioned, must reference capability registry)
                         │
                         ▼
                      Execution (runtime metrics + feedback links)
```

- Templates may be shared across intents, but a playbook is always owned by a single intent.
- Executions link back to both `intent_ref` and `playbook_ref` for routing analytics.
- Feedback records (Stage 5) will store `execution_id` foreign keys.

---

## 4. Storage & Migration Strategy

- Add Alembic migrations (or equivalent) to create the four tables with indexes on `slug`, `version`, and timestamps.
- Use `UUID` primary keys; version fields should have unique constraints scoped to `(name, version)`.
- Introduce repository helpers in `src/core/context.py` or a new module `src/core/repository/intent_store.py`.
- Prepare read/write methods for the upcoming REST layer (`src/api/routes/intents.py`) sharing Pydantic models.

---

## 5. API Surface & Routing

Add FastAPI routers under `src/api/routes`:
- `GET /v1/intents` — list with pagination and optional tag filter.
- `POST /v1/intents` — create intent + optional template link.
- `PUT /v1/intents/{intent_id}` — update metadata, archive toggle.
- `GET /v1/playbooks/{playbook_ref}` — resolve current playbook config.
- `POST /v1/playbooks` — publish new version (requires validation service).
- `GET /v1/executions/{execution_id}` — fetch execution metrics for dashboard.

Routes should enforce authentication once Stage 0 auth scaffolding lands.

---

## 6. Vector Store Integration

- Store embedding vectors for intents and templates to enable semantic lookup (Stage 4 routing).
- Interface: define `EmbeddingBackend` protocol in `src/core/pipeline.py` or a new module such as `src/core/embeddings.py`.
- For MVP, support an in-memory FAISS/SC ANN stub; later swap to managed vector DB by configuration.
- Ingestion flow:
  1. Intent created or template updated.
  2. Background task computes embedding via selected provider.
  3. Vector store upsert keyed by `intent_ref` / `template_ref`.

---

## 7. Testing Considerations

- Unit tests for each repository method (`tests/unit/test_intent_store.py`).
- Integration tests mocking database to verify CRUD operations (`tests/integration/test_intent_api.py`).
- Contract tests for versioning semantics (creating duplicate versions must fail).
- Smoke test ensuring serialization round-trip between API models and stored records.

---

## 8. Open Questions

1. Should templates allow nested includes / modular composition? (defer to Stage 3 design review)
2. How do we represent tool capability requirements in the schema (`tools_required` vs normalized table)?
3. What retention policy do we want for execution logs (default 30 days vs configurable)?

Document updates here as decisions are made.
