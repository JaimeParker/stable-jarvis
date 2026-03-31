---
name: iterative-retrieval
description: "Implements a 4-phase iterative context retrieval loop (dispatch → evaluate → refine → loop) for multi-agent workflows where subagents need progressively refined codebase context. Use when spawning subagents that need unpredictable context, building RAG-like retrieval pipelines for code exploration, or encountering context-too-large or missing-context failures in agent tasks."
---

# Iterative Retrieval Pattern

A 4-phase loop that progressively refines context retrieval for multi-agent workflows, solving the problem of subagents not knowing what context they need until they start working.

## When to Activate

- Spawning subagents that need codebase context they cannot predict upfront
- Building multi-agent workflows where context is progressively refined
- Encountering "context too large" or "missing context" failures in agent tasks
- Designing RAG-like retrieval pipelines for code exploration
- Optimizing token usage in agent orchestration

## The Loop

```
┌─────────────────────────────────────────────┐
│   ┌──────────┐      ┌──────────┐            │
│   │ DISPATCH │─────▶│ EVALUATE │            │
│   └──────────┘      └──────────┘            │
│        ▲                  │                 │
│        │                  ▼                 │
│   ┌──────────┐      ┌──────────┐            │
│   │   LOOP   │◀─────│  REFINE  │            │
│   └──────────┘      └──────────┘            │
│        Max 3 cycles, then proceed           │
└─────────────────────────────────────────────┘
```

### Phase 1: DISPATCH — Broad initial query

Start with high-level intent: file patterns, keywords, and exclusions. Cast a wide net.

### Phase 2: EVALUATE — Score relevance

Rate each retrieved file on a 0–1 scale:
- **0.8–1.0**: Directly implements target functionality
- **0.5–0.7**: Contains related patterns or types
- **0.2–0.4**: Tangentially related
- **0–0.2**: Not relevant — exclude in next cycle

Identify what context is still missing (gaps).

### Phase 3: REFINE — Narrow the search

- Add new patterns discovered in high-relevance files
- Add codebase-specific terminology (first cycle often reveals naming conventions)
- Exclude confirmed irrelevant paths
- Target specific gaps identified in evaluation

### Phase 4: LOOP — Repeat or stop

**Stop when:** 3+ high-relevance files (≥0.7) with no critical gaps, OR max 3 cycles reached.

## Practical Examples

### Bug Fix Context

```
Task: "Fix the authentication token expiry bug"

Cycle 1:
  DISPATCH: Search for "token", "auth", "expiry" in src/**
  EVALUATE: Found auth.ts (0.9), tokens.ts (0.8), user.ts (0.3)
  REFINE: Add "refresh", "jwt" keywords; exclude user.ts

Cycle 2:
  DISPATCH: Search refined terms
  EVALUATE: Found session-manager.ts (0.95), jwt-utils.ts (0.85)
  → Sufficient context — stop

Result: auth.ts, tokens.ts, session-manager.ts, jwt-utils.ts
```

### Feature Implementation

```
Task: "Add rate limiting to API endpoints"

Cycle 1:
  DISPATCH: Search "rate", "limit", "api" in routes/**
  EVALUATE: No matches — codebase uses "throttle" terminology
  REFINE: Add "throttle", "middleware" keywords

Cycle 2:
  DISPATCH: Search refined terms
  EVALUATE: Found throttle.ts (0.9), middleware/index.ts (0.7)
  REFINE: Need router patterns

Cycle 3:
  DISPATCH: Search "router", "express" patterns
  EVALUATE: Found router-setup.ts (0.8)
  → Sufficient context — stop

Result: throttle.ts, middleware/index.ts, router-setup.ts
```

## Integration Prompt Template

```markdown
When retrieving context for this task:
1. Start with broad keyword search
2. Evaluate each file's relevance (0-1 scale)
3. Identify what context is still missing
4. Refine search criteria and repeat (max 3 cycles)
5. Return files with relevance >= 0.7
```

## Best Practices

1. **Start broad, narrow progressively** — don't over-specify initial queries
2. **Learn codebase terminology** — first cycle often reveals naming conventions
3. **Track what's missing** — explicit gap identification drives refinement
4. **Stop at "good enough"** — 3 high-relevance files beats 10 mediocre ones
5. **Exclude confidently** — low-relevance files won't become relevant
