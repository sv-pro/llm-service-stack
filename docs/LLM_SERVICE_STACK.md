# LLM Service Stack

The LLM Service Stack is a modular backend architecture for building your own ChatGPT-style service, developer studio, and safe foundation for future agents.  
It consists of several independent modules that can be deployed, scaled, and evolved separately.

## gateway/ — LLM Gateway (FastAPI + LiteLLM)

A controlled entry point for all LLM requests.

- FastAPI-based service  
- OpenAI-compatible API  
- Uses LiteLLM for provider routing  
- Request caching (simple/semantic-ready)  
- Token and cost accounting  
- Usage logs with trace IDs  
- Internal endpoints for metrics, inspector, dashboard  
- SQLite/DuckDB for local usage storage  

Acts as the “LLM kernel” for the entire stack.

## app-server/ — Application Server (Next.js or Express)

Provides identity, sessions, API keys, and serves as the public API.

- User accounts  
- Conversations and messages  
- API key creation and usage limits  
- Public OpenAI-compatible endpoint  
- Proxies requests to the Gateway with per-user identities  
- Integrates with web-chat and playground  
- Can be extended with billing, quotas, or multi-tenancy  

Forms the boundary between external clients and the internal LLM Gateway.

## playground/ — Control Panel (Developer Studio)

A developer and operator interface for working with the system.

### Includes:

- **Prompt Studio**  
  - LLM Playground  
  - Generate Prompt feature (facade for future Intent Engine)

- **Usage Inspector**  
  - request logs  
  - traces  
  - token usage and cache hits  

- **Dashboard**  
  - aggregated usage  
  - cost metrics  
  - model distribution  
  - cache efficiency  
  - latency statistics  

- **Settings**  
  - model limits  
  - default params  
  - API key management  
  - system configuration  

This module turns the system from a chat toy into an observable and manageable platform.

## web-chat/ — Reference Web Client

A minimal chat UI demonstrating how external applications interact with the stack.

- Connects to app-server’s public OpenAI-compatible endpoint  
- Shows typical request/response flow  
- Useful for demos, testing, internal use, and onboarding  

Purely optional but extremely helpful during early development.

## (future) tools-gateway/ — MCP / Tools Layer

Optional future addition:

- MCP tool registry  
- Sandboxed tool execution  
- Policy-based restrictions  
- Tool-call tracing  
- Foundation for safe, capable agents  

Completes the “action” layer on top of the LLM Gateway.

## Repository Structure

llm-service-stack/  
  gateway/  
  app-server/  
  playground/  
  web-chat/  
  (future) tools-gateway/  
  docker-compose.yml  
  ARCHITECTURE.md  
  EVOLUTION.md  

## Summary

The LLM Service Stack provides:

- A controllable LLM entry point (gateway)  
- A full backend for users, sessions, and API keys (app-server)  
- A development and operations interface (playground)  
- A reference client (web-chat)  
- Optional future tools (MCP gateway)  

Together these modules form a clean, extensible foundation for building custom LLM services and, later, structured intent-driven agent systems.
