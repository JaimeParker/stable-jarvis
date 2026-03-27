---
name: knowledge-distillation-from-discussion
description: Distills a raw, text-based discussion (e.g., meeting notes, user-AI conversations in Markdown) into one or more structured, permanent 'evergreen' knowledge notes.
---

# Skill: Knowledge Distillation from Discussion

## Description

Distills a raw, text-based discussion (e.g., meeting notes, user-AI conversations in Markdown) into one or more structured, permanent 'evergreen' knowledge notes. This skill transforms a chronological 'fleeting note' into conceptual 'permanent notes', following the Zettelkasten/Evergreen methodology. It is designed to extract key insights, decisions, and concepts for a user's personal knowledge base (PKB).

**Trigger:** Use when the user wants to process a text-based discussion, conversation, or meeting notes to extract durable knowledge.

**Input:** The path to the source Markdown discussion note in the user's Obsidian vault.
**Output:** Creates one or more new, atomic notes with declarative titles and moves the original source note to the archive.

---

## Workflow

Follow this 4-stage process to execute the skill.

### 1. Isolate the Source (Fleeting Note)

1.  **Confirm Source:** Ask the user to provide the full path to the source discussion note within their Obsidian vault.
    - `ask_user(question="Please provide the path to the Markdown discussion note you want to process.")`
2.  **Read Content:** Use `mcp_obsidian_read_note` to load the content of the source file. Treat this content as a temporary "fleeting note".

### 2. Distill with AI-Powered Interrogation

1.  **Select Distillation Lens:** The goal is to extract specific types of insights, not just a generic summary. Ask the user what "lens" they want to apply to the discussion. Use `ask_user` with the following choices:
    *   **Core Concepts:** "Find the fundamental principles, arguments, and counter-arguments."
    *   **Outcomes & Decisions:** "Identify the central problem, the final decision, and any unresolved issues or action items."
    *   **Strategic Implications:** "Analyze the discussion for strategic trade-offs, risks, and long-term benefits."
2.  **Execute Distillation:** Based on the user's choice, apply the corresponding advanced prompt to the text content you read in Step 1.

    *   **If "Core Concepts":**
        > "Analyze this discussion and extract the 1-3 core principles or 'atomic ideas' that were debated. For each idea, provide a one-sentence summary, the main supporting argument, and any counter-arguments that were raised. Format the output clearly."
    *   **If "Outcomes & Decisions":**
        > "Review this discussion transcript. Identify: 1) The central problem being addressed. 2) The final consensus or decision reached. 3) Any unresolved 'open loops' or next steps. List action items as a Markdown checklist."
    *   **If "Strategic Implications":**
        > "Act as a CTO reviewing a technical discussion. Analyze this text and identify the key strategic implications. What are the trade-offs, potential risks, and long-term benefits of the proposed approaches? Structure the output logically."

### 3. Synthesize New, Atomic Notes (Evergreen Notes)

1.  **Propose Title:** Based on the distilled output from the LLM, formulate a **declarative title** for a new, permanent note. The title should be a full sentence that captures the core insight (e.g., "Decoupling navigation and manipulation simplifies aerial grasping policies").
2.  **Confirm Title and Path:** Present the proposed title to the user and ask them to confirm or edit it. At the same time, ask for the desired folder path for this new permanent note (e.g., `30 Zettelkasten/32 Permanent/`).
    - `ask_user(questions=[...])`
3.  **Structure Content:** Create the Markdown content for the new note. It must include:
    *   The distilled insights from Step 2, cleanly formatted.
    *   A source link back to the original discussion file, which will be archived. (e.g., `Source: [[50 Archive/Discussion - Hierarchical RL for Aerial Grasping.md]]`).
4.  **Write Note:** Use `mcp_obsidian_write_note` to save the new evergreen note to the confirmed path.

### 4. Integrate and Archive

1.  **Archive Original Note:** After successfully creating the new permanent note, move the original source discussion note to the archive. The user has specified this location.
    *   **Destination Path:** `/50 Archive/` + (original filename).
    *   **Tool:** Use `mcp_obsidian_move_note`. The `oldPath` is the source path from Step 1, and the `newPath` is the constructed archive path.
2.  **Confirm Completion:** Report back to the user, confirming that:
    *   The new evergreen note has been created at its new path.
    *   The original discussion note has been moved to the `50 Archive` directory.
    *   Remind the user to open the new note and add further links to connect it to their knowledge graph.
