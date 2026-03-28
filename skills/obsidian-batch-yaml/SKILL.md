---
name: obsidian-batch-yaml
description: Autonomously scans specific directories (00, 10, 20, 30) in an Obsidian vault, analyzes note content, and intelligently merges AI-generated YAML frontmatter (tags, summary, aliases) into the notes.
---

# Skill: Obsidian Batch YAML

## Description

This skill automates the process of enhancing your Obsidian "Cyber Brain" by adding structured, AI-suitable YAML frontmatter to existing Markdown notes. It is designed to run autonomously across your most active research and project folders.

**Trigger:** Use when the user wants to "standardize", "process", or "add metadata/tags/summaries" to existing notes in the `00`, `10`, `20`, or `30` directories.

**Input:** Obsidian vault directories `00`, `10`, `20`, and `30`.
**Output:** Updated Markdown notes with merged YAML frontmatter including `tags`, `summary`, and `aliases`.

---

## Workflow

Follow this iterative, batch-based process to execute the skill.

### 1. Discovery

1.  **User Declaration (Optional):** Check if the user has explicitly provided a list of notes to process. This can be:
    - A list of note file paths (relative to the Obsidian vault root)
    - A list of note names
    - An example: `["00 Inbox/Research Notes.md", "10 Projects/AI Systems.md", "20 Areas/Machine Learning.md"]`
2.  **Automatic Discovery:** If no explicit list is provided, identify all Markdown (`.md`) files within the target directories:
    - `00 Inbox/`
    - `10 Projects/`
    - `20 Areas/`
    - `30 Zettelkasten/`
3.  **Filter & Batch:** Exclude any files that are clearly non-content (e.g., templates, system logs). Organize the remaining files into batches of **5 notes** to maintain efficiency.

### 2. Batch Processing Loop

For each batch of 5 notes, perform the following steps for every note:

#### A. Read & Analyze
1.  **Read Note:** Use `mcp_obsidian_read_note` to load the full content, including any existing YAML.
2.  **Analyze Content:** Analyze the body text to generate the following metadata:
    - `summary`: A concise, 1-2 sentence TL;DR of the core insight.
    - `tags`: 2-4 highly relevant conceptual tags (e.g., `reinforcement-learning`, `system-architecture`).
    - `aliases`: 1-3 alternative titles or keywords for easier cross-linking.

#### B. Intelligent Merge Logic
1.  **Parse Existing YAML:** If the note has a frontmatter block (between `---` delimiters), extract the existing fields.
2.  **Merge Data:**
    - **Tags:** Combine existing tags with newly generated ones. Ensure no duplicates. Format as a YAML list.
    - **Aliases:** Combine existing aliases with newly generated ones. Ensure no duplicates.
    - **Summary:** Add the new `summary` field. If one already exists, replace it only if the existing one is empty or significantly less informative.
    - **Preserve Others:** Keep all other existing fields (e.g., `date`, `type`, `source`) exactly as they are.
3.  **Construct New YAML:** Assemble the merged fields into a clean YAML block at the top of the file.

#### C. Write Update
1.  **Apply Update:** Use `mcp_obsidian_patch_note` (if replacing only the top block) or `mcp_obsidian_write_note` to save the updated note.
2.  **Log Progress:** Keep a brief internal log of which files have been updated in this turn.

### 3. Continuation & Finalization

1.  **Check for Next Batch:** After completing a batch, automatically proceed to the next until all identified files are processed.
2.  **Final Report:** Once the entire scope is complete, provide a summary to the user:
    - Total notes processed.
    - Folders covered.
    - A few examples of the generated metadata to confirm quality.

---

## User Declaration Format

Users can explicitly declare which notes should be processed by providing:

**Single Note:**
**Single Folder:**
```
"Process this folder: Research"
"Add YAML to: 10 Projects"
"Handle all notes in: 20 Areas/ML Systems"
```

**Single Note:**
```
"Process this note: My Research Note.md"
"Add YAML to: 10 Projects/AI Research.md"
```

**Multiple Notes (List Format):**
```
["00 Inbox/Note 1.md", "10 Projects/Note 2.md", "20 Areas/Note 3.md"]
```

**Mixed Format (Folders and Notes):**
```
["Research/Deep Learning", "10 Projects/AI Systems.md", "00 Inbox/Quick Notes.md"]
```

**Declaration Rules:**
- **Folder paths:** Relative to Obsidian vault root (e.g., `"Research"`, `"10 Projects/Subdir"`)
- **Note paths:** Must include `.md` extension (e.g., `"10 Projects/Note.md"`)
- **Path separators:** Use forward slashes `/` 
- The skill will automatically recursively scan folders for all `.md` files

**Batch Processing:**
If a user provides more than 5 items (folders or notes), they will automatically be split into batches of 5 and processed iteratively.

---

## Technical Constraints

- **Atomicity:** Ensure the note content below the YAML block remains completely unchanged.
- **Safety:** If a note read fails or content is ambiguous, skip that note and move to the next to prevent stalling the loop.
- **Formatting:** Always use valid YAML syntax (e.g., spaces after colons, correct list formatting).
