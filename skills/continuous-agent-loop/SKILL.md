---
name: continuous-agent-loop
description: "Implements continuous autonomous agent execution loops with quality gates, evaluation checkpoints, and graceful error recovery. Use when building agentic workflows that run iteratively, setting up self-correcting loops, configuring autonomous task execution with retry logic, or choosing between sequential, parallel, CI/PR, or RFC-based loop strategies."
---

# Continuous Agent Loop

Canonical loop patterns (v1.8+) for autonomous agent execution with quality gates and recovery controls. Supersedes `autonomous-loops` while keeping one-release compatibility.

## Loop Selection

```text
Start
  |
  +-- Need strict CI/PR control? -- yes --> continuous-pr
  |
  +-- Need RFC decomposition? -- yes --> rfc-dag
  |
  +-- Need exploratory parallel generation? -- yes --> infinite
  |
  +-- default --> sequential
```

## Recommended Production Stack

Combine these components for a robust agent loop:

1. **RFC decomposition** — `ralphinho-rfc-pipeline` breaks tasks into atomic work units
2. **Quality gates** — `plankton-code-quality` + `/quality-gate` validates each iteration
3. **Eval loop** — `eval-harness` runs acceptance criteria after each cycle
4. **Session persistence** — `nanoclaw-repl` preserves state across iterations

### Sequential Loop Example

```bash
# Basic sequential loop with quality gate
for iteration in $(seq 1 $MAX_ITERATIONS); do
  # Execute the task step
  claude --prompt "Complete step $iteration of the plan"

  # Quality gate: run tests/linting
  if ! /quality-gate --scope=changed-files; then
    echo "Quality gate failed at iteration $iteration"
    # Reduce scope to failing unit and retry
    /harness-audit --scope=failing-test
    continue
  fi

  # Eval: check acceptance criteria
  if /eval-harness --criteria=acceptance.yaml; then
    echo "All acceptance criteria met at iteration $iteration"
    break
  fi
done
```

## Failure Modes & Recovery

| Failure Mode | Detection | Recovery |
|---|---|---|
| Loop churn without progress | Same test fails 3+ consecutive iterations | Run `/harness-audit --scope=failing-test`, review output, reduce scope |
| Repeated retries with same root cause | Error message unchanged across iterations | Freeze loop, diagnose root cause, add explicit fix before resuming |
| Merge queue stalls | PR checks pending > 10 minutes | Check CI status with `gh pr checks`, resolve blocking check |
| Cost drift from unbounded escalation | Iteration count exceeds `MAX_ITERATIONS` | Hard-stop loop, summarize progress, ask user for direction |

## Best Practices

- Set explicit `MAX_ITERATIONS` (default: 5) to prevent runaway loops
- Include a quality gate check after every iteration before proceeding
- Log each iteration's outcome for debugging stalled loops
- Use `/harness-audit` to diagnose failures before retrying with the same approach
