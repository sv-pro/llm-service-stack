# Templates & Arguments Design (Stages 3-4)

## Overview

**Stage 3 (Template Match):** Semantic retrieval of existing templates
**Stage 4 (Argument Extraction):** Fill template parameters from natural language

**Repository:** llm-service-stack/
**Timeline:** 4-6 weeks

---

## Stage 3: Template Match

### What is a Template?

A template is a proven prompt structure with:
- Reusable prompt text (system + user)
- Required/optional arguments
- Usage statistics (cost, latency, success rate)
- Semantic embedding for matching

### Template Schema

```typescript
interface Template {
  id: string;
  name: string;
  description: string;

  // Prompt structure
  system_template: string;  // "You are {role}. {instructions}"
  user_template: string;    // "Analyze {code} for {focus_areas}"

  // Arguments
  required_args: Argument[];
  optional_args: Argument[];

  // Matching
  embedding: number[];  // Precomputed from description + templates
  keywords: string[];

  // Statistics
  usage_count: number;
  avg_cost: number;
  avg_latency_ms: number;
  success_rate: number;

  // Metadata
  created_at: Date;
  created_by: string;
  category: string;  // code_review, content_writing, etc.
  tags: string[];
}

interface Argument {
  name: string;
  type: 'string' | 'number' | 'enum' | 'array';
  description: string;
  required: boolean;
  default?: any;
  enum_values?: string[];  // for type='enum'
  validation?: string;  // regex or rule
}
```

### Semantic Matching

Reuse existing semantic cache infrastructure:

```python
@app.post("/v1/templates/match")
async def match_templates(request: MatchRequest):
    """
    Find best matching templates for user prompt.
    Returns ranked list with similarity scores.
    """
    # Generate embedding for user prompt
    embedding = await generate_embedding(request.prompt)

    # Semantic search in template library
    templates = await template_store.find_similar(
        embedding=embedding,
        top_k=5,
        min_similarity=0.75
    )

    # Rank by similarity + usage stats
    ranked = rank_templates(templates, weights={
        'similarity': 0.6,
        'success_rate': 0.2,
        'usage_count': 0.1,
        'recency': 0.1
    })

    return {
        'matches': ranked,
        'query': request.prompt
    }
```

### UI: Template Suggestions

```typescript
// Prompt Studio shows matches above input
{templateMatches.length > 0 && (
  <div className="mb-4 bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
    <h3 className="text-sm font-bold text-blue-900 mb-2">
      🔍 Similar templates found:
    </h3>
    {templateMatches.map(match => (
      <div key={match.id} className="bg-white border border-blue-200 rounded p-3 mb-2">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-bold text-gray-900">{match.name}</div>
            <div className="text-xs text-gray-600">
              {(match.similarity * 100).toFixed(0)}% match |
              Used {match.usage_count} times |
              Avg cost: ${match.avg_cost.toFixed(4)}
            </div>
          </div>
          <button
            onClick={() => selectTemplate(match)}
            className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
          >
            Use This
          </button>
        </div>
      </div>
    ))}
  </div>
)}
```

---

## Stage 4: Argument Extraction

### Automatic Extraction

Use LLM to extract arguments from natural language:

```python
@app.post("/v1/templates/extract-args")
async def extract_arguments(request: ExtractArgsRequest):
    """
    Extract argument values from user prompt based on template.
    """
    template = await template_store.get(request.template_id)

    extraction_prompt = f"""
Template: {template.name}
Required arguments: {json.dumps(template.required_args)}
Optional arguments: {json.dumps(template.optional_args)}

User request: "{request.user_prompt}"

Extract argument values from the user request.
Return JSON with extracted values. Set missing required args to null.
"""

    response = await litellm.acompletion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": extraction_prompt}],
        response_format={"type": "json_object"}
    )

    extracted = json.loads(response.choices[0].message.content)

    # Validate
    missing = validate_required_args(extracted, template)

    if missing:
        return {
            "status": "incomplete",
            "extracted": extracted,
            "missing": missing,
            "prompt": f"Please provide: {', '.join(missing)}"
        }

    return {
        "status": "complete",
        "template_id": template.id,
        "args": extracted
    }
```

### UI: Interactive Argument Form

```typescript
// After selecting template, show argument form
{selectedTemplate && (
  <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-4">
    <h3 className="font-bold text-gray-900 mb-3">
      Template: {selectedTemplate.name}
    </h3>

    {/* Auto-extracted arguments */}
    {selectedTemplate.required_args.map(arg => (
      <div key={arg.name} className="mb-3">
        <label className="block text-sm font-semibold text-gray-900 mb-1">
          {arg.description}
          {arg.required && <span className="text-red-600">*</span>}
        </label>

        {arg.type === 'enum' ? (
          <select
            value={args[arg.name] || ''}
            onChange={e => setArgs({...args, [arg.name]: e.target.value})}
            className="w-full border-2 border-gray-300 rounded p-2"
          >
            <option value="">Select...</option>
            {arg.enum_values.map(val => (
              <option key={val} value={val}>{val}</option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={args[arg.name] || ''}
            onChange={e => setArgs({...args, [arg.name]: e.target.value})}
            className="w-full border-2 border-gray-300 rounded p-2"
            placeholder={arg.description}
          />
        )}

        {extractedArgs[arg.name] && (
          <div className="text-xs text-green-600 mt-1">
            ✓ Auto-extracted: {extractedArgs[arg.name]}
          </div>
        )}
      </div>
    ))}

    <button
      onClick={() => executeTemplate(selectedTemplate, args)}
      disabled={!allRequiredArgsFilled(args)}
      className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:bg-gray-300"
    >
      Execute Template
    </button>
  </div>
)}
```

---

## Template Library Management

### Creating Templates

**From Enhanced Prompts (Stage 2):**
- User clicks "Save as Template" after enhancement
- System suggests template structure
- User fills in arguments and metadata

**Manual Creation:**
- Template editor UI in Prompt Studio
- Define arguments with types and validation
- Test with sample inputs

### Template Storage

```python
class TemplateStore:
    """PostgreSQL + pgvector for template storage and search."""

    async def save(self, template: Template) -> str:
        """Save template with precomputed embedding."""
        # Generate embedding
        text = f"{template.description} {template.system_template} {template.user_template}"
        embedding = await generate_embedding(text)

        # Store in PostgreSQL
        result = await db.execute(
            """
            INSERT INTO templates (id, name, description, system_template,
                                   user_template, required_args, optional_args,
                                   embedding, created_at, category)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            template.id, template.name, template.description,
            template.system_template, template.user_template,
            json.dumps(template.required_args), json.dumps(template.optional_args),
            embedding, datetime.utcnow(), template.category
        )
        return result['id']

    async def find_similar(self, embedding: List[float], top_k: int = 5) -> List[Template]:
        """Semantic search using pgvector."""
        results = await db.fetch(
            """
            SELECT *, embedding <-> $1 AS distance
            FROM templates
            WHERE embedding <-> $1 < 0.3  -- similarity > 0.7
            ORDER BY distance
            LIMIT $2
            """,
            embedding, top_k
        )
        return [Template(**row) for row in results]
```

---

## Testing

### Template Matching
- Input: "review my python code"
- Expected: Code review template (high similarity)
- Expected: NOT content writing templates

### Argument Extraction
- Template: Code Review
- Input: "review this python code for bugs"
- Expected: language="python", focus_areas=["bugs"]

### Edge Cases
- No matching templates (suggest creating new)
- Multiple good matches (show ranked list)
- Incomplete arguments (show form with extracted + missing)

---

## Success Metrics

**Stage 3:**
- Template reuse rate >70%
- Match accuracy >85% (correct template selected)
- Cost savings 40-60% vs always enhancing

**Stage 4:**
- Argument extraction accuracy >80%
- User corrections needed <20% of time
- Time to execution reduced by 50%

---

## Next Steps

- Stage 5: Freeze extracted arguments into deterministic artifacts
- Build template contribution system (users share templates)
- Add template versioning and A/B testing
