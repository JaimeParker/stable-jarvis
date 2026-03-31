---
name: academic-grant-writer
description: "Drafts academic research proposals and grant applications from requirement files, producing structured prose with Total-Part-Total (总分总) organization, LaTeX notation, and word count compliance. Use when writing grant sections, drafting research proposals, or converting technical requirements into formal academic prose with specific word count constraints."
---

# Academic Grant Writer

Converts sparse technical requirements into dense, logically rigorous academic prose that meets specific word count and structural constraints for grant applications.

## Persona & Constraints

- **Tone**: Academic, objective, critical, and precise (Senior Robotics & AI Professor perspective)
- Strictly follow "Total-Part-Total" (总分总) structures
- Word count targets: definitions (~100), overviews (~300), detailed breakdowns (~2000)
- Use LaTeX for mathematical notation; prioritize technical schematic descriptions over long-form formulas

## Workflow

### 1. Initialization & Clarification

The user MUST provide an initial requirement file (e.g., `撰写要求.md`). Validate for:
- Clear goal and section ID (e.g., 1.5)
- Logical hierarchy/logic tree
- Templates and word count constraints
- Specific technical "must-haves"

If requirements are underspecified, use `ask_user` to gather details before proceeding.

### 2. Strategic Planning & Outlining

Use `enter_plan_mode` to generate an `大纲.md` (Outline). The outline must map requirement logic to specific sub-sections (e.g., 1.5 → 1.5.1, 1.5.2) and list key technical "cutting points" for 2000-word sections.

### 3. Multi-Source Literature Research

1. **Local**: Search existing project files and local research notes
2. **Zotero**: Use `mcp_zotero` to retrieve papers, abstracts, and annotations
3. **Web**: Use `web-research` skill for SOTA benchmarks and recent arXiv preprints
- DO NOT use `exa-search` unless specifically authorized for commercial/company intel
- Store results in structured research notes (e.g., `findings_xxx.md`)

### 4. Iterative Drafting

1. Draft ~600-word overview: "Core Idea → Firstly → Secondly → Lastly" template
2. Draft each sub-section following the 100/300/2000 word split
3. Verify word counts using `run_shell_command` with `wc -w`

### 5. Final Synthesis & Peer Review

- Combine segments into the final `.md` file
- Academic Peer Review: check logical consistency, term accuracy (e.g., VLA, CBF, Null-space), and LaTeX formatting
- Verify connection between sub-sections and broader project goals

## Example

```
"Jarvis, use the academic-grant-writer skill to complete section 2.5
of the proposal based on requirements.md in the temp folder."
```
