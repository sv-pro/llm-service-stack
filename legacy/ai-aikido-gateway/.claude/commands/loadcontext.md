# Load Context Command

**Purpose**: Load the project context from documentation files to quickly understand the current state.

## What to Load

When the user runs `/loadcontext`, you should:

1. **Read `docs/project/quick_start/CONTEXT.md`**:
   - Understand recent changes and fixes
   - Note active issues
   - Learn about key technical decisions
   - Understand architecture

2. **Read `docs/project/STATUS.md`**:
   - See what's working vs broken
   - Identify in-progress work
   - Note any blockers
   - Review performance metrics

3. **Read `docs/project/ROADMAP.md`**:
   - Understand upcoming work
   - See completed items
   - Note priorities
   - Review long-term goals

4. **Check Recent Git History**:
   - Run `git log --oneline -10` to see recent commits
   - Run `git status` to see current state

## Output Format

Provide a **structured summary** to the user:

```markdown
# Project Context Loaded

## Current State
- [Brief summary from STATUS.md]

## Recent Changes
- [Highlights from CONTEXT.md]

## Active Work
- [What's in progress]

## Next Steps
- [From ROADMAP.md]

## Git Status
- Branch: [current branch]
- Recent commits: [list]
- Uncommitted changes: [if any]
```

## When to Use

- **Start of session**: Get up to speed quickly
- **After long break**: Refresh your memory
- **New feature**: Understand current state before adding
- **Bug investigation**: Load context to understand recent changes
- **Code review**: Get full picture before reviewing

## Important Notes

- Synthesize information - don't just dump file contents
- Highlight the most important/recent items
- Note any inconsistencies between files
- Suggest updates if context seems stale
- Always check git status for uncommitted work
