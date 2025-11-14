# Gateway Architecture: Drop-in OpenAI Replacement

## Vision

**The AI Aikido Gateway is a drop-in replacement for the OpenAI API.**

Just change your base URL from `https://api.openai.com` to `https://your-gateway.com`, and everything works - with added benefits:
- 💰 Automatic cost tracking
- 🚀 Smart caching
- 📊 Analytics and insights
- 🔄 Model compatibility handling
- ⚡ Request optimization

## Core Principle: Transparent Value-Add

### What This Means

1. **Full OpenAI API Compatibility**
   - Any request that works with OpenAI API works with the gateway
   - Response format is identical
   - No client code changes required

2. **Automatic Normalization**
   - Gateway handles model-specific parameter differences
   - GPT-5 doesn't support `temperature`? We remove it automatically
   - Different models use different parameter names? We translate automatically
   - Client sends OpenAI-compatible request → Gateway ensures it works

3. **Silent Value-Add Features**
   - Cost tracking happens automatically
   - Caching happens automatically
   - Analytics collected automatically
   - No opt-in required

4. **Optional Transparency**
   - Response headers show what we did: `X-Gateway-Normalizations`
   - Developers can see gateway behavior if they want
   - But it's optional - gateway just works by default

## Implementation Strategy

### Current Approach (Correct! ✅)

```python
# Client sends this (unchanged from OpenAI API)
{
  "model": "gpt-5",
  "messages": [...],
  "temperature": 0.7,  # GPT-5 doesn't support this
  "max_completion_tokens": 100
}

# Gateway automatically normalizes:
# 1. Removes temperature (unsupported)
# 2. Forwards to OpenAI
# 3. Returns standard response
# 4. Adds optional header: X-Gateway-Normalizations: "Removed unsupported parameter 'temperature'"
```

### Why This Works

✅ **For the client**: Zero code changes, just works  
✅ **For developers**: Can inspect headers to understand gateway behavior  
✅ **For the gateway**: Adds value without breaking compatibility  
✅ **For support**: Fewer errors, better experience  

### Contrast with "Error Enrichment Only" Approach

❌ **Error enrichment only** would mean:
- Client sends incompatible request
- Gateway forwards it unchanged
- OpenAI returns error
- Gateway adds helpful error message
- Client must fix their code and retry

✅ **Our approach** (automatic normalization):
- Client sends incompatible request
- Gateway fixes it automatically
- OpenAI succeeds
- Client gets response
- Optional header shows what we did

## Edge Cases

### When Auto-Normalization Can't Help

Some cases can't be auto-fixed:
1. **Missing required fields**: Can't invent data
2. **Semantic incompatibilities**: Can't guess user intent
3. **Authentication errors**: Can't fix invalid API keys

For these cases, we DO return enriched errors with fix hints.

### Example: Unfixable Error with Enrichment

```python
# Client tries to use Responses API features via Chat Completions endpoint
{
  "model": "gpt-5",
  "messages": [...],
  "reasoning": {"effort": "high"}  # Only works with /v1/responses endpoint
}

# Gateway can't auto-fix this (wrong endpoint)
# Returns enriched error:
{
  "error": {
    "message": "Parameter 'reasoning' requires Responses API endpoint",
    "fix_hint": "To use reasoning features, switch to /v1/responses endpoint or remove reasoning parameter",
    "corrected_example": {
      "model": "gpt-5",
      "messages": [...]
      # No reasoning parameter
    },
    "documentation": "https://platform.openai.com/docs/guides/gpt-5"
  }
}
```

## Benefits of This Architecture

1. **🎯 True Drop-in Replacement**
   - Change base URL: Done
   - No code refactoring
   - No migration pain

2. **💡 Smart Compatibility Layer**
   - Handles model evolution
   - Abstracts provider differences
   - Future-proofs client code

3. **📊 Automatic Observability**
   - Every request tracked
   - Every cost recorded
   - Every pattern analyzed
   - Zero instrumentation code

4. **🚀 Performance Optimization**
   - Caching happens automatically
   - Smart routing happens automatically
   - No client changes needed

5. **🔧 Developer-Friendly**
   - Optional transparency headers
   - Enriched errors when needed
   - Clear documentation

## Future: Multi-Provider Support

This architecture extends naturally to other providers:

```python
# Client sends OpenAI-compatible request
{
  "model": "claude-3-opus",  # Anthropic model
  "messages": [...],
  "temperature": 0.7
}

# Gateway automatically:
# 1. Detects Anthropic model
# 2. Translates to Anthropic API format
# 3. Forwards to Anthropic
# 4. Translates response back to OpenAI format
# 5. Returns to client

# Client doesn't know or care that it's using Anthropic!
```

## Conclusion

**Our current implementation is correct for the vision.**

We provide:
- ✅ Full OpenAI API compatibility
- ✅ Automatic parameter normalization
- ✅ Silent value-add features
- ✅ Optional transparency
- ✅ Enriched errors when auto-fix isn't possible

This makes us a true drop-in replacement that just makes things better, without requiring any client changes.

