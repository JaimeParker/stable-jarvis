# Stable-JARVIS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[English](README_en.md) | [简体中文](README.md)

**Stable-JARVIS** is an AI-powered assistant framework designed for academic research. It pairs **Zotero** as the literature processing engine with **Obsidian** as the "Cyber Brain," using LLM agents + MCP protocols to automate the full research pipeline.

The framework is driven by two core directories — `skills/` and `agents/`. Skills encapsulate reusable AI workflows (literature discovery, deep reading, note classification, format conversion, etc.), while agents provide specialized review capabilities (code review, architecture design, security auditing, etc.). Compatible with Claude Code, Gemini CLI, Codex, OpenCode, and other MCP-compatible clients.

---

## Core Capabilities

Stable-JARVIS capabilities fall into three categories. See **[docs/features.md](docs/features.md)** for full details.

### Literature Processing

A complete toolchain from paper discovery to deep reading:

- **`paper-finder`** — Profile-driven arXiv paper discovery, outputs Obsidian notes
- **`paper-analyzer`** — Literature skim-reading, single-pass LLM generates summary reports and uploads as Zotero Notes
- **`paper-deep-reader`** — Deep paper reading, 6-section reports with Zotero + Obsidian KB joint analysis, wikilinks output
- **`paper-code-audit`** — Reproducibility audit for paper companion code repositories

### Data Conversion & Knowledge Management

Cross-platform knowledge migration and note enrichment:

- **`notion-to-markdown`** — Notion → Obsidian seamless migration with LaTeX normalization
- **`obsidian-auto-classifier`** — Intelligent note classification and archiving
- **`obsidian-batch-yaml`** — Batch AI-generated frontmatter (tags, summary, aliases)
- **`markitdown-convert`** — Multi-format (PDF/DOCX/PPTX) to Markdown conversion
- **`weekly-report-generator`** — Auto-synthesize Obsidian daily notes into professional PPTX slides
- **`knowledge-distillation-from-discussion`** — Extract structured knowledge from discussions

### Coding & Automation

15+ coding standards, design patterns, and automation skills from the upstream open-source community, covering Python/C++ coding standards, Docker patterns, continuous learning systems, frontend design, and more. Plus 8 specialized review agents (architecture, code, security, builds, etc.).

---

## Installation

```bash
# Clone the repository
git clone https://github.com/JaimeParker/stable-jarvis.git
cd stable-jarvis

# Initialize upstream skill submodules and create symlinks
git submodule update --init --recursive
bash scripts/sync-upstream.sh --apply

# Install the package in editable mode with dependencies
pip install -e .

# If you want semantic search in paper-finder (--semantic), install semantic extras
pip install -e '.[semantic]'
```

To pull the latest upstream updates later:

```bash
git submodule update --remote
bash scripts/sync-upstream.sh --apply
```

### Platform Install Scripts

Interactive scripts are provided to help install skills, agents, and commands for your chosen client:

- **Windows**: Run PowerShell as Administrator, execute `.\install.windows.ps1` (first-time users may need `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)
- **macOS / Linux**: Run `bash install.sh` (macOS users can also use `bash install_mac.sh`)

The script will guide you through selecting your client and the asset categories to install.

---

## Configuration

### API Keys

All API keys are managed centrally in the `.env` file at the project root:

```bash
cp .env.example .env
# Edit .env with your actual keys
```

Key variables:

```bash
# LLM (paper-deep-reader)
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-pro
DEEPSEEK_API_KEY=sk-your-key-here

# Embedding (paper-deep-reader + paper-finder)
EMBEDDING_PROVIDER=qwen
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
EMBEDDING_API_KEY=sk-your-key-here
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1

# Zotero (paper-analyzer + paper-deep-reader)
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
ZOTERO_LIBRARY_TYPE=user

# Exa Search (exa-search skill)
EXA_API_KEY=your-exa-key-here
```

> `.env` is excluded by `.gitignore`. The `stable_jarvis` package auto-loads `.env` on import. System environment variables with the same name take precedence.

### Client Instruction Files

Choose the template matching your client:

- **Gemini CLI**: Rename `GEMINI.md.template` → `GEMINI.md`
- **Codex**: Copy `AGENTS.md.template` → `AGENTS.md`

Replace the placeholders with your research area and name.

### Other Initialization

- **Daily plan**: Copy `commands/daily/plan.toml.template` → `commands/daily/plan.toml` and customize for your projects
- **Research profile**: Reference `config/research-interest.example.json` to create your search profile

### Embedding Recommendations

If using SiliconFlow's embedding service, start with `Qwen/Qwen3-Embedding-8B` and set `EMBEDDING_BASE_URL` to `https://api.siliconflow.cn/v1`. See [SiliconFlow Models](https://cloud.siliconflow.cn/me/models?types=embedding).

---

## Dependencies & MCP Servers

To unlock the full power of Stable-JARVIS, configure the following MCP servers in your client:

- **Zotero MCP**: [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp) — Library search and metadata retrieval
- **Obsidian MCP**: [bitbonsai/mcpvault](https://github.com/bitbonsai/mcpvault) — Local Cyber Brain interaction
- **Notion MCP**: [Official Notion MCP Guide](https://developers.notion.com/guides/mcp) — Collaboration platform sync

> For teams using Feishu/Lark, we recommend the [Feishu CLI](https://github.com/larksuite/cli).

---

## Note Management Philosophy: The Cyber Brain

This framework is built upon a specific hierarchy of knowledge management to ensure peak efficiency for both the user and their AI agents:

- **Zotero (The Laboratory)**: The primary workspace for deep literature reading. This is where raw data (PDFs) is processed and deeply analyzed.
- **Obsidian (The Local Cyber Brain)**: A curated, local knowledge base. It is a "clean room" containing only summarized, user-verified, high-signal information. It functions as an external logical engine for agents to read and reference, strictly used for **knowledge ingestion and synthesis**.
- **Notion (The Exchange)**: A dynamic platform for collaboration, quick notes, and database management. It acts as the "Inbox" for raw information and the "Output" for shared results.

### Obsidian Vault Architecture

A PARA-style hierarchy (00 Inbox → 10 Projects → 20 Areas → 30 Zettelkasten → 40 Resources → 50 Archive → 60 System), auto-populated by skills such as `paper-finder`.

→ Full architecture: **[docs/obsidian_guide.md](docs/obsidian_guide.md)**

---

## Quick Start

### PDF to Markdown

```python
from stable_jarvis import PDFConverter

converter = PDFConverter()
result = converter.convert("paper.pdf")

if result.success:
    print(result.markdown)  # LLM-ready Markdown content
```

### Image Extraction with Metadata

Extract figures from papers and generate a structured manifest for figure-rich Markdown reports:

```python
from stable_jarvis import PDFConverter

converter = PDFConverter()

# Extract high-quality images and retrieve positioning metadata
metadata = converter.extract_images_with_metadata(
    "paper.pdf",
    output_dir="./figures",
    quality="high",  # Options: low, medium, high, epic
    name_prefix="ABC12345"
)

# Save the manifest JSON for LLM reference
converter.save_image_manifest(metadata, "./figures/manifest.json")
# Output: [{"filename": "ABC12345_fig1.png", "page": 1, "description": "Figure at the top of page 1"}]
```

For more features (paper-finder CLI, etc.), see **[docs/features.md](docs/features.md)**.

---

## Contributing & Community Flywheel

PRs are welcome — whether adding new skills, improving PDF parsing, or refining the Cyber Brain logic.

**Contribution Rules:**

- **Upstream skills** (from open-source communities): Submit changes to the upstream repository first, then sync back via `sync-upstream.sh --apply`. Check the `upstream` attribute in `skill-taxonomy.xml` to confirm a skill's origin.
- **Custom skills**: PR directly to this repository. When adding new skills, agents, or commands, declare them in the appropriate category within `skill-taxonomy.xml`.

Feel free to check the [issues page](https://github.com/JaimeParker/stable-jarvis/issues) to get started.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgements

This repository tracks the following open-source skill repositories via git submodule symlinks:

- **`arxiv-search`**, **`web-research`**: From [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)
- **`skill-creator`**, **`pptx`**: From [anthropics/skills](https://github.com/anthropics/skills)
- **`obsidian-markdown`**: From [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)
- **`premium-frontend-ui`**, **`web-coder`**: From [github/awesome-copilot](https://github.com/github/awesome-copilot)
- **`autonomous-loops`**, **`verification-loop`**, **`deep-research`**, **`iterative-retrieval`**, **`python-patterns`**, **`cpp-coding-standards`**, **`videodb`**, **`docker-patterns`**, **`continuous-agent-loop`**, **`continuous-learning`**, **`continuous-learning-v2`**, **`exa-search`**: From [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)
- **`brainstorming`**, **`executing-plans`**, **`writing-plans`**: From [obra/superpowers](https://github.com/obra/superpowers)
- **`paper-finder`** source code from [zhanglg12/research-assist](https://github.com/zhanglg12/research-assist)

All other skills are developed in-house. Credit goes to the original authors for these foundational capabilities.
