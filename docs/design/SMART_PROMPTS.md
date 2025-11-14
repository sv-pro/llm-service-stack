# Smart Prompts Design (Stage 2)

## Overview

The Smart Prompt feature uses an LLM to improve naive user prompts, making them clearer, more specific, and more effective. This is the first step in teaching users about prompt structure while collecting data for template building (Stage 3).

**Repository:** llm-service-stack/
**Components:** Gateway endpoint + Prompt Studio UI
**Timeline:** 2-3 weeks

---

## User Flow

```
┌─────────────────────────────────────┐
│ Prompt Studio                       │
├─────────────────────────────────────┤
│ System: [You are a helpful...]     │
│ User: [make a react app]            │
│                                     │
│ [✨ Enhance Prompt] [Generate]      │
└─────────────────────────────────────┘
         ↓ (user clicks)
┌─────────────────────────────────────┐
│ 📝 Enhanced Prompt                  │
├─────────────────────────────────────┤
│ System:                             │
│ You are an expert React developer. │
│ Generate complete, production-ready │
│ code with TypeScript, modern hooks, │
│ and best practices.                 │
│                                     │
│ User:                               │
│ Create a modern React application   │
│ with the following requirements:    │
│ - TypeScript for type safety        │
│ - Component structure following...  │
│ - Routing with React Router         │
│ - State management with Context     │
│                                     │
│ Improvements Made:                  │
│ ✓ Added technical specificity       │
│ ✓ Clarified output format           │
│ ✓ Included best practices           │
│ ✓ Specified tech stack              │
│                                     │
│ Detected Intent: code_generation    │
│                                     │
│ [Use This] [Edit] [Save as Template]│
└─────────────────────────────────────┘
```

---

## Gateway API

### POST /v1/prompts/enhance

**Request:**
```json
{
  "system": "You are a helpful assistant.",
  "user": "make a react app",
  "context": {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7
  }
}
```

**Response:**
```json
{
  "enhanced": {
    "system": "You are an expert React developer...",
    "user": "Create a modern React application..."
  },
  "improvements": [
    "Added technical specificity",
    "Clarified output format",
    "Included best practices",
    "Specified tech stack"
  ],
  "detected_intent": "code_generation",
  "reasoning": "User wants to build a React application...",
  "confidence": 0.92,
  "original": {
    "system": "You are a helpful assistant.",
    "user": "make a react app"
  }
}
```

---

## Implementation

### Gateway (Python)

**File:** `gateway/app/main.py`

```python
from pydantic import BaseModel
from typing import Optional, List

class EnhancePromptRequest(BaseModel):
    system: str
    user: str
    context: Optional[dict] = {}

class EnhancePromptResponse(BaseModel):
    enhanced: dict
    improvements: List[str]
    detected_intent: str
    reasoning: str
    confidence: float
    original: dict

@app.post("/v1/prompts/enhance")
async def enhance_prompt(request: EnhancePromptRequest):
    """
    Use GPT-4 or Claude to improve a naive prompt.
    Returns enhanced version with metadata.
    """

    # Metaprompt for enhancement
    metaprompt = f"""You are a prompt engineering expert. Analyze and improve this prompt for clarity, specificity, and effectiveness.

Original Prompt:
System: {request.system}
User: {request.user}

Your task:
1. Rewrite both system and user prompts to be clearer and more specific
2. Add relevant context, constraints, and formatting instructions
3. Identify improvements made
4. Detect the user's intent category
5. Provide reasoning

Return JSON:
{{
  "enhanced_system": "...",
  "enhanced_user": "...",
  "improvements": ["improvement 1", "improvement 2", ...],
  "detected_intent": "code_generation|content_writing|data_analysis|...",
  "reasoning": "explanation of intent and improvements",
  "confidence": 0.0-1.0
}}"""

    # Call GPT-4 for enhancement
    response = await litellm.acompletion(
        model="gpt-4",
        messages=[{"role": "user", "content": metaprompt}],
        temperature=0.3,  # Lower temp for consistent results
        response_format={"type": "json_object"}
    )

    # Parse JSON response
    result = json.loads(response.choices[0].message.content)

    # Store for template building (Stage 3)
    await store_enhanced_prompt(
        original=request,
        enhanced=result,
        timestamp=datetime.utcnow()
    )

    return EnhancePromptResponse(
        enhanced={
            "system": result["enhanced_system"],
            "user": result["enhanced_user"]
        },
        improvements=result["improvements"],
        detected_intent=result["detected_intent"],
        reasoning=result["reasoning"],
        confidence=result["confidence"],
        original={
            "system": request.system,
            "user": request.user
        }
    )
```

---

### Prompt Studio (TypeScript)

**File:** `playground/app/prompt-studio/page.tsx`

Add state for enhanced prompts:

```typescript
// Add to state
const [enhancedPrompt, setEnhancedPrompt] = useState<{
  system: string;
  user: string;
  improvements: string[];
  intent: string;
  reasoning: string;
} | null>(null);
const [enhancing, setEnhancing] = useState(false);

// Handler
const handleEnhancePrompt = async () => {
  setEnhancing(true);
  setError(null);

  try {
    const res = await fetch(`${GATEWAY_URL}/v1/prompts/enhance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        system: systemPrompt,
        user: userMessage,
        context: {
          model: selectedModel,
          temperature
        }
      })
    });

    if (!res.ok) {
      throw new Error(`Enhancement failed: ${res.status}`);
    }

    const data = await res.json();

    setEnhancedPrompt({
      system: data.enhanced.system,
      user: data.enhanced.user,
      improvements: data.improvements,
      intent: data.detected_intent,
      reasoning: data.reasoning
    });

  } catch (err: any) {
    setError(err.message || 'Failed to enhance prompt');
  } finally {
    setEnhancing(false);
  }
};

// UI button (add after user message input)
<button
  onClick={handleEnhancePrompt}
  disabled={enhancing || !userMessage.trim()}
  className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-bold px-4 py-3 rounded-lg hover:from-purple-700 hover:to-purple-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
>
  {enhancing ? '✨ Enhancing...' : '✨ Enhance Prompt'}
</button>
```

Add enhanced prompt display:

```typescript
{enhancedPrompt && (
  <div className="mt-6 bg-purple-50 border-2 border-purple-200 rounded-lg p-5">
    <div className="flex items-center justify-between mb-3">
      <h3 className="text-lg font-bold text-purple-900">📝 Enhanced Prompt</h3>
      <span className="text-xs bg-purple-100 px-2 py-1 rounded border border-purple-300 font-semibold">
        Intent: {enhancedPrompt.intent}
      </span>
    </div>

    <div className="space-y-3">
      <div>
        <label className="block text-sm font-bold text-purple-900 mb-1">System:</label>
        <div className="bg-white border border-purple-200 rounded p-3 text-sm text-gray-900">
          {enhancedPrompt.system}
        </div>
      </div>

      <div>
        <label className="block text-sm font-bold text-purple-900 mb-1">User:</label>
        <div className="bg-white border border-purple-200 rounded p-3 text-sm text-gray-900">
          {enhancedPrompt.user}
        </div>
      </div>

      <div>
        <label className="block text-sm font-bold text-purple-900 mb-1">Improvements:</label>
        <ul className="bg-white border border-purple-200 rounded p-3 text-sm text-gray-900 space-y-1">
          {enhancedPrompt.improvements.map((improvement, i) => (
            <li key={i} className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              {improvement}
            </li>
          ))}
        </ul>
      </div>
    </div>

    <div className="flex gap-2 mt-4">
      <button
        onClick={() => {
          setSystemPrompt(enhancedPrompt.system);
          setUserMessage(enhancedPrompt.user);
          setEnhancedPrompt(null);
        }}
        className="flex-1 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 font-semibold"
      >
        Use This
      </button>
      <button
        onClick={() => {
          // TODO: Save as template (Stage 3)
          alert('Template saving coming in Stage 3!');
        }}
        className="flex-1 bg-white text-purple-600 border-2 border-purple-600 px-4 py-2 rounded-lg hover:bg-purple-50 font-semibold"
      >
        Save as Template
      </button>
      <button
        onClick={() => setEnhancedPrompt(null)}
        className="px-4 py-2 text-gray-600 hover:text-gray-900 font-semibold"
      >
        Cancel
      </button>
    </div>
  </div>
)}
```

---

## Data Collection

Store enhanced prompts for Stage 3 template building:

**Database Schema:**

```sql
CREATE TABLE enhanced_prompts (
  id TEXT PRIMARY KEY,
  original_system TEXT,
  original_user TEXT,
  enhanced_system TEXT,
  enhanced_user TEXT,
  improvements TEXT[],
  detected_intent TEXT,
  reasoning TEXT,
  confidence FLOAT,
  model_used TEXT,
  timestamp TIMESTAMP,
  user_feedback TEXT  -- 'used' | 'edited' | 'discarded'
);
```

Track user actions:
- Did they use the enhanced prompt?
- Did they edit it first?
- Did they discard it?

This data trains the template matcher in Stage 3.

---

## Testing

### Manual Testing
1. Enter various naive prompts
2. Click "Enhance Prompt"
3. Verify enhancements make sense
4. Test "Use This" button
5. Verify system/user prompts update

### Unit Tests
```python
def test_enhance_prompt_endpoint():
    request = {
        "system": "You are a helpful assistant.",
        "user": "make a react app"
    }
    response = client.post("/v1/prompts/enhance", json=request)
    assert response.status_code == 200
    assert "enhanced" in response.json()
    assert "improvements" in response.json()
    assert "detected_intent" in response.json()
```

---

## Cost Considerations

- Enhancement uses GPT-4: ~$0.001-0.003 per enhancement
- Cache enhanced prompts aggressively (high reuse expected)
- Consider using GPT-3.5-turbo for simple enhancements
- Add rate limiting (max 10 enhancements/minute per user)

---

## Success Metrics

- **Adoption:** >50% of users try enhancement feature
- **Reuse:** >70% of enhanced prompts are used (not discarded)
- **Quality:** User satisfaction >4/5
- **Data:** Collect 1000+ enhanced prompts for template building

---

## Next Steps

After Stage 2 is complete:
1. Analyze collected data for patterns
2. Identify common intents and prompt structures
3. Use data to seed Stage 3 template library
4. Refine metaprompt based on user feedback
