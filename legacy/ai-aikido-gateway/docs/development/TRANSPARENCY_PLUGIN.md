# Transparency Plugin

**Optional developer visibility into gateway behavior**

---

## Overview

The TransparencyPlugin adds HTTP response headers that show what the gateway did to your requests. Perfect for debugging integration issues or understanding how the gateway normalizes requests for different LLM models.

---

## Usage

### Enable Transparency Headers

Edit `config/plugins.yaml`:

```yaml
- name: transparency
  enabled: true  # ← Enable transparency
  priority: 90
  class: plugins.transparency.TransparencyPlugin
  config:
    show_normalizations: true  # Show parameter changes
    show_model: true           # Show original model
    show_latency: true         # Show request latency
    show_cache_status: true    # Show cache hit/miss
```

### Disable Transparency Headers

```yaml
- name: transparency
  enabled: false  # ← Disable for production
```

---

## Response Headers

When enabled, responses include these headers:

### `X-Gateway-Normalizations`
Shows what parameters were modified or removed:

```http
X-Gateway-Normalizations: Removed unsupported parameter 'temperature'; Removed unsupported parameter 'top_p'
```

**Use case**: Understand why certain parameters aren't reaching the LLM

### `X-Gateway-Original-Model`
Shows the model you requested:

```http
X-Gateway-Original-Model: gpt-5
```

**Use case**: Verify routing behavior or debugging model selection

### `X-Gateway-Latency-Ms`
Shows request processing time in milliseconds:

```http
X-Gateway-Latency-Ms: 1234.56
```

**Use case**: Performance monitoring and optimization

### `X-Gateway-Cache-Status`
Shows if response came from cache:

```http
X-Gateway-Cache-Status: HIT
```
or
```http
X-Gateway-Cache-Status: MISS
```

**Use case**: Verify caching is working correctly

---

## Configuration Options

### Selective Headers

You can disable individual header types:

```yaml
config:
  show_normalizations: true   # Include normalization info
  show_model: false           # Hide original model
  show_latency: true          # Include latency
  show_cache_status: false    # Hide cache status
```

### Custom Prefix

Change the header prefix:

```yaml
config:
  custom_prefix: X-MyGateway  # Instead of X-Gateway
```

Result:
```http
X-MyGateway-Normalizations: ...
X-MyGateway-Original-Model: gpt-5
```

---

## Use Cases

### Development & Debugging

**Enable transparency** during development:

```yaml
- name: transparency
  enabled: true  # See everything the gateway does
```

**Benefits**:
- Understand parameter normalization
- Debug integration issues
- Verify cache behavior
- Monitor performance

### Production

**Disable transparency** in production:

```yaml
- name: transparency
  enabled: false  # Clean responses, no extra headers
```

**Benefits**:
- Smaller response size
- No internal details exposed
- Standard OpenAI-compatible responses

### Gradual Rollout

**Enable selectively** during migrations:

```yaml
config:
  show_normalizations: true  # Show what we're changing
  show_model: false          # Don't expose routing
  show_latency: false        # Don't share perf data
  show_cache_status: true    # Verify caching works
```

---

## Examples

### Example 1: GPT-5 Parameter Normalization

**Request**:
```bash
curl -i http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "top_p": 0.9,
    "max_completion_tokens": 100
  }'
```

**Response Headers** (with transparency enabled):
```http
HTTP/1.1 200 OK
X-Gateway-Normalizations: Removed unsupported parameter 'temperature'; Removed unsupported parameter 'top_p'
X-Gateway-Original-Model: gpt-5
X-Gateway-Latency-Ms: 1245.32
X-Gateway-Cache-Status: MISS
```

**Insight**: Gateway removed `temperature` and `top_p` because GPT-5 doesn't support them.

### Example 2: Cache Hit

**First Request**:
```http
X-Gateway-Cache-Status: MISS
X-Gateway-Latency-Ms: 2341.12
```

**Second Request** (identical):
```http
X-Gateway-Cache-Status: HIT
X-Gateway-Latency-Ms: 12.45
```

**Insight**: Second request was served from cache (99% faster!)

### Example 3: No Normalizations Needed

**Request** (GPT-3.5-Turbo with standard parameters):
```bash
curl -i http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

**Response Headers**:
```http
HTTP/1.1 200 OK
X-Gateway-Original-Model: gpt-3.5-turbo
X-Gateway-Latency-Ms: 987.65
X-Gateway-Cache-Status: MISS
```

**Note**: No `X-Gateway-Normalizations` header because nothing was changed.

---

## FAQ

### Q: Do transparency headers affect performance?

**A**: Negligible impact. The plugin runs after the request completes and just adds a few header bytes.

### Q: Should I enable transparency in production?

**A**: Generally no. Enable during development/debugging, disable in production for clean responses.

### Q: Can clients break if they see these headers?

**A**: No. HTTP headers clients don't recognize are safely ignored. The gateway remains fully OpenAI-compatible.

### Q: How do I see these headers in my code?

**JavaScript**:
```javascript
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  body: JSON.stringify({...})
});
console.log(response.headers.get('X-Gateway-Normalizations'));
```

**Python**:
```python
import requests
response = requests.post('http://localhost:8000/v1/chat/completions', json={...})
print(response.headers.get('X-Gateway-Normalizations'))
```

**curl**:
```bash
curl -i http://localhost:8000/v1/chat/completions ... | grep X-Gateway
```

### Q: What if I want transparency only for certain requests?

**Current**: All-or-nothing (plugin enabled = all requests get headers)

**Future**: Could add request-header trigger:
```http
X-Request-Transparency: true
```

---

## Technical Details

### Plugin Architecture

- **Hook**: `after_response` (runs after LLM responds)
- **Priority**: 90 (runs near end, before history plugin at 100)
- **Storage**: Headers stored in `ctx.metadata['transparency_headers']`
- **Application**: Route handler reads metadata and applies headers to HTTP response

### Performance

- **Overhead**: < 1ms per request
- **When disabled**: Zero overhead (plugin not executed)
- **Header size**: ~100-300 bytes depending on normalization complexity

### Compatibility

- **Works with**: All LLM providers (OpenAI, future Anthropic, etc.)
- **Compatible with**: All OpenAI SDK versions
- **HTTP compliance**: Standard custom headers (X- prefix)

---

## Related

- [Drop-in Replacement Architecture](architecture-side-notes.md)
- [Parameter Normalization](GPT5_RESPONSES_API.md)
- [Plugin System](../README.md#plugins)
