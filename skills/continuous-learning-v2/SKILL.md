---
name: continuous-learning-v2
description: "Automatically learns reusable patterns from Claude Code sessions using hooks, creating project-scoped instincts with confidence scoring that evolve into skills, commands, or agents. Use when setting up automatic session learning, configuring instinct-based behavior extraction, reviewing or evolving learned instincts, or managing project-scoped vs global pattern libraries."
version: 2.1.0
---

# Continuous Learning v2.1 - Instinct-Based Architecture

Turns Claude Code sessions into reusable knowledge through atomic "instincts" — small learned behaviors with confidence scoring, scoped per project to prevent cross-project contamination.

## Quick Start

### 1. Enable Observation Hooks

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/skills/continuous-learning-v2/hooks/observe.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/skills/continuous-learning-v2/hooks/observe.sh"
      }]
    }]
  }
}
```

For manual installs, replace `${CLAUDE_PLUGIN_ROOT}` with `~/.claude`.

### 2. Verify Hooks Are Working

After running any tool in a git repo, confirm observations are captured:

```bash
# Find your project hash
cat ~/.claude/homunculus/projects.json

# Check observations are recording
tail -1 ~/.claude/homunculus/projects/<hash>/observations.jsonl
```

### 3. Use Instinct Commands

| Command | Description |
|---------|-------------|
| `/instinct-status` | Show all instincts (project + global) with confidence scores |
| `/evolve` | Cluster related instincts into skills/commands/agents, suggest promotions |
| `/instinct-export` | Export instincts (filterable by scope/domain) |
| `/instinct-import <file>` | Import instincts with scope control |
| `/promote [id]` | Promote project instincts to global scope |
| `/projects` | List all known projects and instinct counts |

## The Instinct Model

An instinct is a small learned behavior:

```yaml
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
scope: project
project_id: "a1b2c3d4e5f6"
---
# Prefer Functional Style
## Action
Use functional patterns over classes when appropriate.
## Evidence
- Observed 5 instances of functional pattern preference
- User corrected class-based approach to functional on 2025-01-15
```

**Properties:** Atomic (one trigger, one action) · Confidence-weighted (0.3 tentative → 0.9 near-certain) · Domain-tagged · Evidence-backed · Scope-aware (project or global)

## How It Works

```
Session Activity (in a git repo)
      | Hooks capture prompts + tool use (100% reliable)
      v
  observations.jsonl (per-project)
      | Observer agent analyzes (background, Haiku)
      v
  Pattern Detection → Creates/updates instincts
      | /evolve clusters + /promote
      v
  Evolved skills/commands/agents (project or global)
```

## Scope Decision Guide

| Pattern Type | Scope | Examples |
|-------------|-------|---------|
| Language/framework conventions | **project** | "Use React hooks", "Follow Django REST patterns" |
| File structure preferences | **project** | "Tests in `__tests__`/", "Components in src/components/" |
| Security practices | **global** | "Validate user input", "Sanitize SQL" |
| Tool workflow preferences | **global** | "Grep before Edit", "Read before Write" |
| Git practices | **global** | "Conventional commits", "Small focused commits" |

## Instinct Promotion (Project → Global)

When the same instinct appears in 2+ projects with average confidence ≥ 0.8, it qualifies for promotion:

```bash
# Promote a specific instinct
python3 instinct-cli.py promote prefer-explicit-errors

# Auto-promote all qualifying instincts
python3 instinct-cli.py promote

# Preview without changes
python3 instinct-cli.py promote --dry-run
```

## Configuration

Edit `config.json` to control the background observer:

```json
{
  "version": "2.1",
  "observer": {
    "enabled": false,
    "run_interval_minutes": 5,
    "min_observations_to_analyze": 20
  }
}
```

## Confidence Scoring

| Score | Meaning | Behavior |
|-------|---------|----------|
| 0.3 | Tentative | Suggested but not enforced |
| 0.5 | Moderate | Applied when relevant |
| 0.7 | Strong | Auto-approved for application |
| 0.9 | Near-certain | Core behavior |

Confidence increases with repeated observation and lack of correction; decreases when user explicitly corrects the behavior or contradicting evidence appears.
