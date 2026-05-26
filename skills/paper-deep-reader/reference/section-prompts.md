# Task-Based Prompt System for Deep Reading

Analysis prompts are stored as `task-N.md` files under `prompts/{category}/`. Each file defines a **subagent job description** — the responsibilities, analysis dimensions, and output requirements for one subagent. The main agent reads these as conceptual guidance, then writes customized instructions for each subagent based on the specific paper.

## Architecture

```
prompts/
├── categories.toml              # Category registry
├── default/                     # 4 tasks — generic academic
│   ├── system.md
│   ├── task-1.md ~ task-4.md
│   └── report-template.md
├── ai-ml/                       # 5 tasks — AI/ML
│   ├── system.md
│   ├── task-1.md ~ task-5.md
│   └── report-template.md
└── rl/                          # 6 tasks — RL (most detailed)
    ├── system.md
    ├── task-1.md ~ task-6.md
    └── report-template.md
```

## How It Works

1. **Phase 2**: Main agent reads `categories.toml` and matches paper to a category
2. **Phase 5a**: Main agent reads all `task-N.md` files in the category — the count determines subagent count
3. **Phase 5b**: Main agent writes customized instructions for each subagent, adapting `task-N.md` guidance to the specific paper
4. **Phase 5c**: Subagents are spawned in parallel, each producing Markdown output
5. **Phase 5d**: Main agent merges outputs, cross-checks for consistency, and renders the final report using `report-template.md` as a structural guide

## Task Splits by Category

### rl (6 tasks)
| Task | Focus |
|------|-------|
| task-1 | Introduction & Related Work — problem, gap, logic chain |
| task-2 | Algorithm & Architecture — method, loop, Mermaid, network I/O |
| task-3 | Formula Derivation & Theorems — equation evolution, loss trace |
| task-4 | Literature Cross-Analysis — KB retrieval, philosophical/technical contrast |
| task-5 | Experiments & Results — benchmarks, ablations, key findings |
| task-6 | Weaknesses & Inspiration — Grill, future work, personal takeaways |

### ai-ml (5 tasks)
| Task | Focus |
|------|-------|
| task-1 | Research Problem & Motivation |
| task-2 | Method & Algorithm Design (architecture + formulas merged) |
| task-3 | Related Work & KB Cross-Analysis |
| task-4 | Experiments & Ablation Analysis |
| task-5 | Limitations & Personal Insights |

### default (4 tasks)
| Task | Focus |
|------|-------|
| task-1 | Research Problem & Background |
| task-2 | Core Method & Framework |
| task-3 | Empirical Analysis & Related Work |
| task-4 | Limitations & Critical Evaluation |

## No Placeholders

`task-N.md` files contain **no `{placeholder}` variables**. They are pure conceptual descriptions of what each subagent should produce. The main agent reads the text as-is and writes task-specific instructions in its own words.

No files in `prompts/{category}/` use placeholders. All task descriptions are pure conceptual guidance.

## Adding a New Category

1. Create `prompts/{category}/` directory
2. Add `system.md` (persona + writing rules)
3. Add `task-1.md` through `task-N.md` (any number — 4 to 6 recommended)
4. Add `report-template.md` (suggested report structure)
5. Register in `prompts/categories.toml`
