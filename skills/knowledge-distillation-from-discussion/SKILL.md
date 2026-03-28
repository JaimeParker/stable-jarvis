---
name: knowledge-distillation-from-discussion
description: Distills a raw, text-based discussion (e.g., meeting notes, user-AI conversations in Markdown) into one or more structured, permanent 'evergreen' knowledge notes.
---

# Skill: Knowledge Distillation from Discussion

## Description

Distills a raw, text-based discussion (e.g., meeting notes, user-AI conversations in Markdown) into one or more structured, permanent 'evergreen' knowledge notes. This skill transforms a chronological 'fleeting note' into conceptual 'permanent notes', following the Zettelkasten/Evergreen methodology. It is designed to extract key insights, decisions, and concepts for a user's personal knowledge base (PKB).

**Trigger:** Use when the user wants to process a text-based discussion, conversation, or meeting notes to extract durable knowledge.

**Input:** The path to the source Markdown discussion note in the user's Obsidian vault.
**Output:** Creates one or more new, atomic notes with declarative titles, updates relevant MOCs, and moves the original source note to the discussions archive.

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
        > "Analyze this discussion and extract the 1-3 core principles or 'atomic ideas' that were debated. For each idea, provide a one-sentence summary. Then, for each idea, detail the main supporting argument and any counter-arguments that were raised. Format the output so it can be structured into 'Core Insight' and 'Supporting Arguments' sections."
    *   **If "Outcomes & Decisions":**
        > "Review this discussion transcript. Format the output to clearly separate the 'Problem', 'Final Decision', and 'Action Items'. For the final decision, explain the consensus that was reached. For action items, list them as a Markdown checklist."
    *   **If "Strategic Implications":**
        > "Act as a CTO reviewing a technical discussion. Structure the output to clearly distinguish between 'Strategic Implications', 'Trade-offs', and 'Risks', based on the content of the discussion."

### 3. Synthesize New, Atomic Notes (Evergreen Notes)

1.  **Propose Title:** Based on the distilled output from the LLM, formulate a **declarative title** for a new, permanent note. The title should be a full sentence that captures the core insight (e.g., "Decoupling navigation and manipulation simplifies aerial grasping policies").
2.  **Confirm Title and Path:** Present the proposed title to the user and ask them to confirm or edit it. At the same time, ask for the desired folder path for this new permanent note (e.g., `30 Zettelkasten/32 Permanent/`).
    - `ask_user(questions=[...])`
3.  **Structure Content:** Create the Markdown content for the new note using the exact template below. You **MUST** map the insights from the distillation lens chosen in Step 2 into the appropriate sections of this template.

    **Template:**
    ```markdown
    ---
    tags: [distilled-insight, add-2-to-3-relevant-topic-tags]
    date: {{current_date}}
    type: evergreen
    ---
    # {{The Declarative Title}}

    **TL;DR:** [Write a one-sentence summary of the core insight or decision.]

    ### Context / Problem
    [Based on the distilled output, briefly describe the context or the problem that was being discussed.]

    ### Core Insight / Decision
    [Place the primary distilled knowledge here. For example, if the lens was 'Outcomes & Decisions', this section should contain the final consensus. If the lens was 'Core Concepts', this should contain the main principle.]

    ### Supporting Arguments / Caveats
    [Place secondary information here. For example, supporting arguments, counter-arguments, unresolved issues, or identified risks and trade-offs.]

    ---
    Source: [[50 Archive/Discussions/{{original_filename}}]]
    ```
4.  **Write Note:** Use `mcp_obsidian_write_note` to save the new evergreen note to the confirmed path.

### 4. Integrate and Archive

1.  **Update MOCs:**
    *   **Search:** Use `mcp_obsidian_search_notes` with the query "MOC" to find potentially relevant Maps of Content.
    *   **Identify:** Present the list of candidate MOCs to the user and ask which one(s) should be updated with a link to the new permanent note.
    *   **Patch:** Use `mcp_obsidian_patch_note` or `mcp_obsidian_read_note` followed by `mcp_obsidian_write_note` to add the wikilink to the selected MOC(s). Provide a brief summary of the new note's context next to the link.
2.  **Archive Original Note:** Move the original source discussion note to the specific discussions archive.
    *   **Destination Path:** `50 Archive/Discussions/` + (original filename).
    *   **Tool:** Use `mcp_obsidian_move_note`. The `oldPath` is the source path from Step 1, and the `newPath` is the constructed archive path.
3.  **Confirm Completion:** Report back to the user, confirming that:
    *   The new evergreen note has been created.
    *   The relevant MOCs have been updated.
    *   The original discussion note has been moved to `50 Archive/Discussions/`.
