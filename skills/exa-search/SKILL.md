---
name: exa-search
description: Neural search via Exa MCP for web, code, and company research. Use when the user needs web search, code examples, company intel, people lookup, or AI-powered deep research with Exa's neural search engine.
origin: ECC
---

# Exa Search

Neural search for web content, code, companies, and people via the Exa MCP server.

## When to Activate

- User needs current web information or news.
- Searching for code examples, API docs, or technical references.
- **Academic Research**: Finding specific research papers or academic discussions.
- **Deep Literature Review**: When a query requires a multi-step, synthesized report (Deep Researcher).
- User says "search for", "look up", "find", or "what's the latest on".

## 🛡️ Interaction Protocol - Important

**Before performing any search operation, the Agent MUST follow this workflow:**

1.  **Assess Task Complexity**:
    *   For simple queries: Ask about **Category** and **Domain** filters.
    *   For complex topics (e.g., reviews, comparative analysis): Propose the **"Deep Researcher"** mode (explaining that it generates an exhaustive, synthesized report asynchronously).
2.  **Actively Inquire Filtering Needs**: Unless the user has already specified conditions in their prompt, the Agent must ask:
    *   **Category Filter**: Should the search be limited to `research paper`, `news`, `github`, or `tweet`?
    *   **Domain Filter**: Should specific sites be included or excluded (e.g., `include arxiv.org`)?
3.  **Provide Suggestions**: Suggest the most appropriate category and domain filters based on the query context.
4.  **Confirm and Execute**: Adjust tool selection and parameters based on the user's response before proceeding.

## MCP Requirement

Exa MCP server must be configured in `settings.json`. To enable all capabilities, ensure the HTTP URL or transport configuration includes the necessary tools if using a custom proxy, or simply use the standard remote URL:
`https://mcp.exa.ai/mcp?exaApiKey=YOUR_KEY&tools=web_search_exa,web_search_advanced_exa,get_code_context_exa,crawling_exa,deep_researcher_start,deep_researcher_check`

For simple search needs, use: `https://mcp.exa.ai/mcp?tools=get_code_context_exa,people_search_exa`

## Core Tools & Parameters

### 1. Basic & Advanced Search
- **`web_search_exa`**: Simple neural search.
- **`web_search_advanced_exa`**: Supports advanced filtering like `includeDomains`, `excludeDomains`, and `startPublishedDate`.
- **`get_code_context_exa`**: Optimized for finding technical code and documentation.

### 2. Content Extraction
- **`crawling_exa(url: string)`**: Retrieves the **full text content** of a specific URL, rather than just search snippets.

### 3. Deep Researcher Mode
- **`deep_researcher_start(query: string)`**: Initiates an autonomous research agent. Returns a `taskId`.
- **`deep_researcher_check(taskId: string)`**: Polls for status and retrieves the final synthesized report with citations.

## Usage Patterns

### 1. Pattern: Simple Search
**User**: "Find me the latest progress on xxx."
**Agent**: "I can search that for you. To make the results more precise, would you like to limit the search to **research papers**? I also suggest including `arxiv.org` and `paperswithcode.com` to find implementation details. Does that sound good?"

### 2. Pattern: Deep Research Task
**User**: "Compare the pros and cons of major xxx algorithms in 2026."
**Agent**: "This is a complex research topic. I suggest using the **'Deep Researcher'** mode. It will take about 1-2 minutes to autonomously synthesize a detailed report comparing multiple sources. Should I start this research task for you?"

## Related Skills
- `deep-research` — For generating long-form, exhaustive research reports.
- `paper-finder` — Use Exa as a backend for semantic discovery beyond arXiv.
