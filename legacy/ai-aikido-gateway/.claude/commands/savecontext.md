# Save Context Command

**Purpose**: Save the current project context, status, and roadmap to documentation files.

## What to Save

When the user runs `/savecontext`, you should:

1. **Update `docs/project/quick_start/CONTEXT.md`**:
   - Current project state
   - Recent changes and fixes
   - Active issues and their status
   - Key technical decisions
   - Architecture changes
   - Important findings from debugging/development

2. **Update `docs/project/STATUS.md`**:
   - What's working (features, tests, infrastructure)
   - What's in progress
   - Known issues
   - Blocked items
   - Performance metrics

3. **Update `docs/project/ROADMAP.md`**:
   - Completed items (move from in-progress)
   - Current sprint items
   - Upcoming features
   - Long-term goals
   - Technical debt items

## Format

- Use clear, concise language
- Include file references with line numbers
- Add timestamps for when changes were made
- Link commits where relevant
- Keep it scannable (use headers, bullets, code blocks)

## Example Flow

```markdown
## Recent Changes (2025-11-07)

### Semantic Cache Fixes
- Fixed config path expansion bug in plugins.yaml:38,62,92
- Fixed type error in preview_candidates (semantic_cache.py:336)
- Commit: 8678729

### Test Infrastructure
- Resolved memory leaks in test suite
- Fixed hanging tests in test_end_to_end.py
- Commits: e68a686, 46df0e2

### Next Steps
- Implement on-premise embedding service (sentence-transformers)
- Deploy Qdrant vector database
- See ROADMAP.md for full plan
```

## Important Notes

- Be comprehensive but concise
- Focus on actionable information
- Include enough detail for future context loading
- Don't duplicate information across files - use cross-references
- Always commit the changes after saving
