# GPT-5 and the Responses API

**Status**: 🟡 Partial Support (Chat Completions fallback)  
**Last Updated**: 2025-10-23

---

## Overview

GPT-5, GPT-5-mini, and GPT-5-nano are **reasoning models** that use a completely different API architecture from traditional OpenAI models. This document explains the differences and our current implementation strategy.

---

## API Architecture Differences

### Traditional Models (GPT-4o, GPT-4, GPT-3.5-Turbo)
- **Endpoint**: `/v1/chat/completions`
- **Input**: `messages` array
- **Parameters**: `temperature`, `top_p`, `max_tokens`, `presence_penalty`, `frequency_penalty`, `logprobs`
- **Response**: Simple completion text

### GPT-5 Reasoning Models
- **Endpoint**: `/v1/responses` (Responses API)
- **Input**: `input` (string or messages)
- **Parameters**: 
  - `reasoning.effort`: "minimal" | "low" | "medium" | "high"
  - `text.verbosity`: "low" | "medium" | "high"
  - `max_output_tokens`: Maximum response length
  - `previous_response_id`: For multi-turn reasoning
- **Response**: Completion + chain-of-thought reasoning
- **NOT Supported**: `temperature`, `top_p`, `logprobs`, `presence_penalty`, `frequency_penalty`, `max_tokens`, `max_completion_tokens`

---

## Current Implementation

### What We Do Now

1. **Use Chat Completions API for ALL models** (including GPT-5)
2. **Filter unsupported parameters** for GPT-5 models:
   - Remove: `temperature`, `top_p`, `logprobs`, `presence_penalty`, `frequency_penalty`
   - Convert: `max_tokens` / `max_completion_tokens` → (filtered out)
3. **OpenAI provides a fallback** that makes GPT-5 work with Chat Completions API

### Limitations

- ❌ No access to reasoning chain-of-thought
- ❌ No control over reasoning effort level
- ❌ No verbosity control
- ❌ No ability to pass `previous_response_id` for multi-turn reasoning
- ❌ Can't use `max_output_tokens`
- ❌ Missing performance benefits (higher cache hit rates, fewer reasoning tokens)

### Why This Approach?

✅ **Simplicity**: One API endpoint for all models  
✅ **Compatibility**: OpenAI-compatible interface works as expected  
✅ **Immediate availability**: GPT-5 works without major refactoring  
✅ **Gradual migration**: Can add Responses API support later  

---

## Future: Full Responses API Support

### Implementation Plan

#### 1. Detect API Type in Model Registry

```python
MODEL_REGISTRY = {
    "gpt-5": {
        "api_type": "responses",  # Use Responses API
        "reasoning_model": True,
        # ...
    },
    "gpt-4o": {
        "api_type": "chat_completions",  # Use Chat Completions
        # ...
    }
}
```

#### 2. Route Requests Based on API Type

```python
async def create_chat_completion(request_data):
    model_info = get_model_info(request_data.model)
    
    if model_info.get("api_type") == "responses":
        return await handle_responses_api(request_data)
    else:
        return await handle_chat_completions_api(request_data)
```

#### 3. Transform Parameters for Responses API

```python
def transform_to_responses_api(chat_request):
    """Convert Chat Completions request to Responses API format"""
    return {
        "model": chat_request.model,
        "input": chat_request.messages,  # Responses API accepts messages too
        "reasoning": {
            "effort": "low"  # Default, could be configurable
        },
        "max_output_tokens": chat_request.max_tokens or 1000
    }
```

#### 4. Transform Responses Back to Chat Completions Format

```python
def transform_from_responses_api(responses_response):
    """Convert Responses API response to Chat Completions format"""
    return {
        "id": responses_response.id,
        "object": "chat.completion",
        "created": responses_response.created,
        "model": responses_response.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": responses_response.output  # Map output to content
            },
            "finish_reason": responses_response.finish_reason
        }],
        "usage": responses_response.usage,
        # Optionally include reasoning chain in metadata
        "_reasoning": responses_response.reasoning if include_reasoning else None
    }
```

#### 5. Expose Reasoning Features (Optional)

```python
# Client could request reasoning via custom header or parameter
X-Include-Reasoning: true

# Response includes reasoning chain
{
    "choices": [...],
    "usage": {...},
    "reasoning": {
        "items": [
            {"type": "thought", "content": "Let me think..."},
            {"type": "tool_call", "tool": "calculator", "args": {...}},
            {"type": "thought", "content": "Based on the result..."}
        ]
    }
}
```

---

## Parameter Mapping Reference

| Chat Completions | Responses API | Notes |
|------------------|---------------|-------|
| `messages` | `input` | Both formats supported in Responses API |
| `max_tokens` | `max_output_tokens` | Different name, same concept |
| `max_completion_tokens` | `max_output_tokens` | Different name, same concept |
| `temperature` | ❌ Not supported | Use `reasoning.effort` instead |
| `top_p` | ❌ Not supported | Use `reasoning.effort` instead |
| `logprobs` | ❌ Not supported | N/A |
| `presence_penalty` | ❌ Not supported | N/A |
| `frequency_penalty` | ❌ Not supported | N/A |
| ❌ N/A | `reasoning.effort` | "minimal", "low", "medium", "high" |
| ❌ N/A | `text.verbosity` | "low", "medium", "high" |
| ❌ N/A | `previous_response_id` | For multi-turn reasoning |

---

## Migration Benefits

### Why Migrate to Responses API?

1. **Intelligence**: Access to chain-of-thought reasoning improves quality
2. **Efficiency**: Higher cache hit rates reduce costs
3. **Performance**: Fewer reasoning tokens, lower latency
4. **Control**: Explicit reasoning effort and verbosity settings
5. **Features**: Multi-turn reasoning, tool calling with reasoning context

### Migration Strategy

1. **Phase 1** (Current): Chat Completions fallback for GPT-5
2. **Phase 2**: Implement Responses API handler alongside Chat Completions
3. **Phase 3**: Route GPT-5 requests to Responses API automatically
4. **Phase 4**: Expose reasoning features as optional enhancement

---

## Testing GPT-5 Models

### Current Setup (Chat Completions)

```bash
# Works, but without reasoning features
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "max_completion_tokens": 50
  }'
```

### Future Setup (Responses API)

```bash
# Full reasoning capabilities
curl -X POST https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "input": "What is 2+2?",
    "reasoning": {
      "effort": "low"
    },
    "max_output_tokens": 50
  }'
```

---

## Model Recommendations

Based on OpenAI's guidance:

| Use Case | Recommended Model | Reasoning Effort |
|----------|-------------------|------------------|
| Replace o3 | gpt-5 | medium or high |
| Replace gpt-4.1 | gpt-5 | minimal or low |
| Replace o4-mini or gpt-4.1-mini | gpt-5-mini | (default) |
| Replace gpt-4.1-nano | gpt-5-nano | (default) |

---

## References

- [OpenAI GPT-5 Documentation](https://platform.openai.com/docs/guides/gpt-5)
- [Responses API Reference](https://platform.openai.com/docs/api-reference/responses)
- [Chat Completions API Reference](https://platform.openai.com/docs/api-reference/chat)
- [Reasoning Models Guide](https://platform.openai.com/docs/guides/reasoning)

---

## Decision Log

### 2025-10-23: Initial GPT-5 Support

**Decision**: Use Chat Completions fallback with parameter filtering

**Rationale**:
- Quickest path to GPT-5 availability
- Maintains OpenAI-compatible interface
- Can migrate to Responses API incrementally
- No breaking changes for existing clients

**Trade-offs**:
- Missing reasoning features (acceptable for initial release)
- Can't control reasoning effort (OpenAI provides sensible defaults)
- Lower efficiency than full Responses API (acceptable for now)

**Next Steps**:
- Document the architecture differences (this file)
- Add proper MODEL_REGISTRY configuration
- Filter unsupported parameters automatically
- Plan Phase 2 implementation with Responses API
