# Context Management Protocol

**For Claude Code Internal Use**

This document defines how Claude Code should manage project context across sessions.

## File Structure

```
docs/project/
├── quick_start/
│   └── CONTEXT.md          # Current state, recent changes, technical decisions
├── STATUS.md               # What's working, in-progress, blocked
└── ROADMAP.md              # Completed, current, upcoming, long-term
```

## When to Save Context

**Automatic (Proactive)**:
- After fixing major bugs
- After completing significant features
- After making architecture changes
- At end of long work sessions
- Before major refactoring

**On Request**:
- User runs `/savecontext`
- User asks to "save the context" or "document changes"

## When to Load Context

**Automatic (Proactive)**:
- Start of new session (if no recent context in conversation)
- User asks about project state
- Before starting new major work

**On Request**:
- User runs `/loadcontext`
- User asks "what's the status?" or "where are we?"

## File Purposes

### CONTEXT.md
**Purpose**: Working memory - what happened recently

**Contents**:
- Session-by-session updates
- Bug fixes with details
- Technical decisions and why
- Code changes with file:line references
- Commit hashes for tracking
- Active issues and investigations

**Update Frequency**: After each significant change

**Example Structure**:
```markdown
# Project Context

## Session: 2025-11-07

### Semantic Cache Fixes
**Issue**: Config couldn't parse ${VAR:-default} syntax
**Fix**: Replaced with hardcoded paths in plugins.yaml:38,62,92
**Files**: config/plugins.yaml, src/plugins/semantic_cache.py:336
**Commit**: 8678729

### Memory Leak Resolution
**Issue**: FAISS accumulating in test memory
**Fix**: Disable semantic_cache in test fixtures
**Files**: tests/test_end_to_end.py:65, tests/test_guard_rails.py:18
**Commits**: e68a686, 46df0e2

## Active Investigations
- None

## Next Session
- Implement on-premise embedding service
- See docs/project/design/SEMANTIC_EMBEDDINGS_PLAN.md
```

### STATUS.md
**Purpose**: Current state snapshot - truth source for "what works"

**Contents**:
- ✅ Working features
- 🚧 In progress
- ❌ Known issues
- 🚫 Blockers
- 📊 Metrics (test pass rate, performance, etc.)

**Update Frequency**: When state changes (feature complete, bug discovered, etc.)

**Example Structure**:
```markdown
# Project Status

**Last Updated**: 2025-11-07 16:50 UTC

## Working ✅
- Gateway API (8000) - all endpoints operational
- Cache system (verbatim + semantic)
  - Test pass rate: 100% (175/175)
- Provider plugins (OpenAI, Anthropic)
- Request history tracking
- Dashboard UI

## In Progress 🚧
- On-premise embedding service (planned)
- Qdrant vector database integration (planned)

## Known Issues ❌
- None

## Blockers 🚫
- None

## Metrics 📊
- Tests: 175 passed, 0 failed
- Test time: ~17s
- Coverage: (not tracked)
- Memory: No leaks detected
```

### ROADMAP.md
**Purpose**: Future direction - what's coming

**Contents**:
- ✅ Completed milestones
- 🎯 Current sprint
- 📋 Backlog
- 🔮 Future ideas
- 💰 Cost optimizations
- 🔧 Technical debt

**Update Frequency**: Sprint planning, milestone completion

**Example Structure**:
```markdown
# Project Roadmap

## Completed ✅

### Phase 1: Core Gateway (Complete)
- [x] Basic proxy functionality
- [x] Request routing
- [x] Error handling

### Phase 2: Caching (Complete)
- [x] Verbatim cache
- [x] Semantic cache (FAISS + OpenAI)
- [x] Cache metrics

## Current Sprint 🎯

### On-Premise Embeddings
**Goal**: Replace OpenAI embeddings with local sentence-transformers
**Status**: Planning complete, ready to implement
**Priority**: High (cost reduction)
**Timeline**: 1-2 weeks

**Tasks**:
- [ ] Create embedding service (Docker)
- [ ] Implement sentence-transformers provider
- [ ] Deploy Qdrant vector database
- [ ] Update semantic cache plugin
- [ ] Test & benchmark performance

## Backlog 📋

### Authentication System
**Priority**: Medium
**Effort**: 2-3 days
- API key management
- Rate limiting per key
- Usage tracking

### Advanced Caching
**Priority**: Low
**Effort**: 1 week
- Cache warming
- Distributed cache (Redis)
- Cache invalidation strategies

## Technical Debt 🔧
- Pydantic V1 deprecation warnings (low priority)
- Test collection warning for TestPlugin class
```

## Commit Protocol

**After saving context**:
```bash
git add docs/project/
git commit -m "docs: update project context and status

- Document recent fixes for semantic cache and tests
- Update STATUS.md with current state (all tests passing)
- Add on-premise embedding plan to ROADMAP.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Cross-Referencing

When changes span multiple concerns:
- **CONTEXT.md**: Details of what changed and why
- **STATUS.md**: Impact on current state
- **ROADMAP.md**: Move completed items, update next steps

Example:
```markdown
# In CONTEXT.md
## Semantic Cache Refactor
Fixed critical bugs in semantic cache. See STATUS.md for impact.
Full implementation plan in docs/project/design/SEMANTIC_EMBEDDINGS_PLAN.md

# In STATUS.md
## Working ✅
- Semantic cache (fixed bugs, see CONTEXT.md for details)

# In ROADMAP.md
## Completed ✅
- [x] Fix semantic cache config parsing (CONTEXT.md 2025-11-07)
```

## Best Practices

1. **Be Specific**: Include file paths, line numbers, commit hashes
2. **Be Concise**: Each entry should be scannable in < 30 seconds
3. **Be Timely**: Update right after changes, not days later
4. **Be Consistent**: Use same format across sessions
5. **Be Honest**: Document failures and blockers, not just wins
6. **Cross-Reference**: Link related information across files
7. **Commit Together**: Always commit context updates with related code

## Anti-Patterns

❌ **Don't**:
- Write essay-length explanations
- Duplicate information across files
- Wait until "later" to update
- Skip commit messages
- Forget timestamps
- Use vague descriptions

✅ **Do**:
- Use bullets and headers
- Cross-reference between files
- Update immediately
- Write clear commit messages
- Always timestamp
- Be specific and actionable
