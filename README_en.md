# Stable-JARVIS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Stable-JARVIS** is an AI-powered assistant framework designed for academic researchers. It leverages Model Context Protocol (MCP) architecture, LLM agents, and a suite of specialized programmatic skills to automate the entire research lifecycle—from searching arXiv and conducting structured web-based literature reviews to generating high-fidelity Markdown reports, managing a personal "Cyber Brain" in Obsidian, and injecting native annotations back into Zotero.

Stable-JARVIS is designed to be driven by modern AI interfaces including **Gemini CLI**, **Claude Code**, **Codex**, **OpenCode**, and other MCP-compatible agents.

## 🧠 Note Management Philosophy: The Cyber Brain

This framework is built upon a specific hierarchy of knowledge management to ensure peak efficiency for both the user and their AI agents:

-   **Zotero (The Laboratory)**: The primary workspace for deep, careful literature reading. This is where raw data (PDFs) is processed and initially annotated using the non-destructive engine.
-   **Obsidian (The Local Cyber Brain)**: A curated, local knowledge base. It is a "clean room" containing only summarized, user-verified, and high-signal information. It functions as an external logical engine for coding agents to read and reference, effectively forming your "Cyber Brain." In this ecosystem, Obsidian is strictly for **ingestion and synthesis**—it is the source of truth, not a broad distribution channel.
-   **Notion (The Exchange & Input Box)**: A dynamic platform for collaboration, quick notes, database management, and cross-team discussion. It acts as the "Inbox" for raw information and the "Output" for shared results and sharing.

### 📁 Recommended Obsidian Vault Structure

To maximize the efficiency of Stable-JARVIS skills (like `paper-finder` and `daily plan`), we recommend structuring your Obsidian vault using the following logic:

```text
/ (Vault Root)
├── 00 Inbox/                # Inbox for new notes, paper drafts, and uncategorized info
├── 10 Projects/             # Active Research Projects
├── 20 Areas/                # Long-term research areas and interests
├── 30 Zettelkasten/         # Permanent, atomic knowledge notes
├── 40 Resources/            # Reference materials
│   └── 42 Assets/
│       └── Templates/       # Core templates (e.g., Daily Note Template.md)
├── 50 Archive/              # Archived or inactive projects
│   └── Daily Notes/         # Daily logs in YYYY-MM-DD.md format
└── 60 System/               # Vault metadata and configuration
```

## 🛠️ Built-in Skills

The framework includes several specialized skills that can be activated by the agent:

-   **`paper-analyzer`**: The core research skill. Orchestrates Zotero-MCP, multi-modal PDF reading, and Zotero Web API to generate deep technical reports and native annotations.
-   **`paper-finder`**: A profile-driven paper discovery skill. It queries arXiv with your research-interest profile, ranks candidates (lexical + optional semantic), and writes Obsidian-ready Markdown notes.
-   **`weekly-report-generator`**: Automatically synthesizes your progress from Obsidian daily notes into a professional one-page PPTX slide.
-   **`notion-to-markdown`**: Seamlessly migrates Notion pages into your local Obsidian vault with perfect LaTeX and image localization.
-   **`obsidian-auto-classifier`**: Intelligently categorizes and archives notes within your vault based on their content and intent.
-   ...

## 🧩 Dependencies & MCP Servers

To unlock the full power of Stable-JARVIS, you must have the following MCP servers installed and configured in your client:

-   **Zotero MCP**: [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp) — For library search and metadata retrieval.
-   **Obsidian MCP**: [bitbonsai/mcpvault](https://github.com/bitbonsai/mcpvault) — For interacting with your local "Cyber Brain."
-   **Notion MCP**: [Official Notion MCP Guide](https://developers.notion.com/guides/mcp) — For syncing with your information exchange platform.

> 💡 **Coming Soon**: Keep an eye out for our upcoming **Feishu MCP** integration!

## 💻 Client Installation & Integration

Stable-JARVIS supports multiple AI clients. For the best experience, we recommend **symlinking** the provided agents and skills so that updates in this repository are automatically reflected in your client.

### 1. Gemini CLI
Gemini CLI automatically registers `.toml` files in `.gemini/commands/` and manages skills via the `skills` command. It also supports sub-agents defined in Markdown files.

- **Configure Exa Search (MCP)**:
  Add the following to `~/.gemini/settings.json` to enable the remote Exa MCP service:
  ```json
  {
    "mcpServers": {
      "exa": {
        "httpUrl": "https://mcp.exa.ai/mcp"
      }
    }
  }
  ```
- **Installing Subagents (Recommended)**:
  ```bash
  # Global Installation (Recommended)
  mkdir -p ~/.gemini/agents
  ln -s $(pwd)/agents/*.md ~/.gemini/agents/

  # Workspace-local (Optional)
  mkdir -p .gemini/agents
  ln -s $(pwd)/agents/*.md .gemini/agents/
  ```
- **Installing Commands**:
  ```bash
  # Symlink commands to the project-local configuration
  mkdir -p .gemini/commands
  ln -s $(pwd)/commands/daily/plan.toml .gemini/commands/daily:plan.toml
  ln -s $(pwd)/commands/paper/analyze.toml .gemini/commands/paper:analyze.toml
  # Reload in Gemini CLI: /commands reload
  ```
- **Installing Skills**:
  ```bash
  # Link skills to global scope (Recommended)
  gemini skills link ./skills

  # Workspace-local (Optional)
  gemini skills link ./skills --scope workspace
  ```

### 2. Claude Code
Claude Code looks for agent definitions and skills in `.claude/` directories.

- **Installing Agents (Recommended)**:
  ```bash
  # Global Registration (Recommended)
  mkdir -p ~/.claude/agents
  ln -s $(pwd)/agents/*.md ~/.claude/agents/

  # Project-Level Registration (Optional)
  mkdir -p .claude/agents
  ln -s $(pwd)/agents/*.md .claude/agents/
  ```
- **Integrating Skills**:
  ```bash
  # Link skill directories globally (Recommended)
  mkdir -p ~/.claude/skills
  ln -s $(pwd)/skills/* ~/.claude/skills/

  # Project-Level (Optional)
  mkdir -p .claude/skills
  ln -s $(pwd)/skills/* .claude/skills/
  ```
- **Configure Exa Search (MCP)**:
  ```bash
  # Run the following to add the Exa MCP server. Replace YOUR_API_KEY with your actual key.
  claude mcp add --transport http exa "https://mcp.exa.ai/mcp?exaApiKey=YOUR_API_KEY&tools=web_search_exa,get_code_context_exa"
  ```

### 3. Codex / GitHub Copilot
For GitHub Copilot Extensions or custom agents, instructions and skills can be linked as follows:

- **Installing Agents**:
  ```bash
  # Global instructions (Recommended)
  mkdir -p ~/.copilot/instructions
  ln -s $(pwd)/GEMINI.md ~/.copilot/instructions/stable-jarvis.md

  # Workspace-local (Optional)
  mkdir -p .github/instructions
  ln -s $(pwd)/GEMINI.md .github/instructions/stable-jarvis.md
  ```
- **Installing Skills**:
  ```bash
  # Link skill directories globally (Recommended)
  mkdir -p ~/.copilot/skills
  ln -s $(pwd)/skills/* ~/.copilot/skills/

  # Workspace-local (Optional)
  mkdir -p .github/skills
  ln -s $(pwd)/skills/* .github/skills/
  ```

---

## 🔒 Security & Environment Variables

To protect your API keys from leakage, Stable-JARVIS recommends using **System Environment Variables** instead of local configuration files.

### Core API Key Configuration
Add the following lines to your `~/.bashrc` or `~/.zshrc`:

```bash
# Exa Search API Key (Shared by Claude Code and Gemini-CLI)
export EXA_API_KEY="YOUR_EXA_API_KEY"

# Zotero Credentials
export ZOTERO_LIBRARY_ID="YOUR_ID"
export ZOTERO_API_KEY="YOUR_KEY"

# Semantic Search Embedding API (If using paper-finder --semantic)
export STABLE_JARVIS_SEMANTIC_API_KEY="YOUR_KEY"
export STABLE_JARVIS_SEMANTIC_API_BASE_URL="https://api.your-provider.com/v1"
```

> 💡 **Note**: If environment variables are set, Stable-JARVIS will **prioritize** them and ignore the corresponding fields in `config/api_keys.json` or `config/zotero.json`. This prevents accidental commits of sensitive keys to the repository.

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/JaimeParker/stable-jarvis.git
cd stable-jarvis

# Ensure you are in your preferred virtual environment (e.g., conda activate jarvis)
# Install the package in editable mode with dependencies
pip install -e .

# If you want semantic search in paper-finder (--semantic), install semantic extras
pip install -e '.[semantic]'
```

## ⚙️ Configuration

Configure Zotero credentials using one of these methods (in priority order):

### 🛠️ Personalization (Mandatory)

Before using the assistant, you **must** initialize your research identity by renaming the following template files and filling in your details:

1.  **System Prompt**: Rename `GEMINI.md.template` to `GEMINI.md`. Replace the placeholders with your research area and name. This file defines the agent's logic.
2.  **Daily Plan Command**: The `daily plan` command must be configured by yourself. We provide a template at `commands/daily/plan.toml.template`; copy it to `commands/daily/plan.toml` and customize it for your active projects.
3.  **Zotero Credentials**: Rename `config/zotero.json.template` to `config/zotero.json` and enter your API keys. (Alternatively, use environment variables below).
4.  **Semantic Search Credentials (Optional)**: If you want to use `paper-finder --semantic`, create `config/api_keys.json` from `config/api_keys.json.template` and fill in `semantic_model.api_base_url`, `semantic_model.api_key`, and `semantic_model.model` (or use environment variables instead).

### Option 1: Environment Variables (Recommended)

```bash
export ZOTERO_LIBRARY_ID="your_library_id"
export ZOTERO_API_KEY="your_api_key"
export ZOTERO_LIBRARY_TYPE="user"  # Optional, defaults to "user"
```

### Option 2: Configuration File

Create a `zotero.json` file in one of the following locations (searched in order):
1. `./zotero.json` (Current working directory)
2. `./config/zotero.json` (Relative to current working directory)
3. `~/.config/stable-jarvis/zotero.json` (User config directory)

**Example `zotero.json`:**
```json
{
    "library_id": "your_library_id",
    "api_key": "your_api_key",
    "library_type": "user"
}
```

To enable semantic search in `paper-finder`, you also need `config/api_keys.json`. You can copy `config/api_keys.json.template` and fill it like this:

```json
{
    "semantic_model": {
        "api_base_url": "https://api.your-provider.com/v1",
        "api_key": "your_semantic_api_key",
        "model": "your-embedding-model"
    }
}
```

Or configure semantic search directly with environment variables:

```bash
export STABLE_JARVIS_SEMANTIC_API_BASE_URL="https://api.your-provider.com/v1"
export STABLE_JARVIS_SEMANTIC_API_KEY="your_semantic_api_key"
export STABLE_JARVIS_SEMANTIC_MODEL="your-embedding-model"
```

If you are using SiliconFlow's embedding service, a good starting choice is `Qwen/Qwen3-Embedding-8B`, refer to [SiliconFlow Embedding Models](https://cloud.siliconflow.cn/me/models?types=embedding).

## 📖 Quick Start

### 1. Auto-Annotation

Inject a highlight and comment into a Zotero PDF attachment programmatically.

```python
from stable_jarvis import annotate

result = annotate(
    pdf_path="/path/to/local/paper.pdf",
    attachment_key="ABC12345", # The Zotero Attachment Key for the PDF
    target_text="We formulate the search-to-control problem as a Markov Decision Process",
    comment="This defines the MDP state space. Important distinction.",
    color="#ff6666" 
)

if result.success:
    print(f"Successfully created annotation! Zotero Key: {result.annotation_key}")
```

### 2. PDF to Markdown Conversion

```python
from stable_jarvis import PDFConverter

converter = PDFConverter()
result = converter.convert("paper.pdf")

if result.success:
    print(result.markdown) # LLM-ready markdown content
```

### 3. Image Extraction with Metadata

Extract figures from a paper and generate a structural manifest.

```python
from stable_jarvis import PDFConverter

converter = PDFConverter()

# Extract high-quality images and retrieve positioning metadata
metadata = converter.extract_images_with_metadata(
    "paper.pdf",
    output_dir="./figures",
    quality="high",  # Options: low, medium, high, epic
    name_prefix="ABC12345",
)

# Save the manifest JSON for the LLM to reference
converter.save_image_manifest(metadata, "./figures/manifest.json")
# Output example: [{"filename": "ABC12345_fig1.png", "page": 1, "description": "Figure at the top of page 1"}]
```

### 4. Profile-driven Paper Finder (Obsidian notes)

```bash
# Run profile-based retrieval and write markdown notes
conda run -n jarvis python skills/paper-finder/find_papers.py \
    --profile path/to/research-interest.json \
    --output path/to/obsidian/inbox

# Enable semantic ranking (reads semantic_model from config/api_keys.json)
conda run -n jarvis python skills/paper-finder/find_papers.py \
    --profile path/to/research-interest.json \
    --output path/to/obsidian/inbox \
    --semantic
```

## 📁 Project Structure

```text
stable-jarvis/
├── config/                          # Local config templates and credential files
│   ├── zotero.json.template         # Zotero API config template
│   ├── api_keys.json.template       # Semantic search config template for paper-finder
│   └── research-interest.example.json  # Example research profile
├── commands/                        # Client / agent command templates
│   ├── daily/                       # Daily planning commands
│   └── paper/                       # Paper-related commands
├── src/
│   ├── stable_jarvis/
│   │   ├── annotation/              # Non-destructive Zotero annotation engine
│   │   │   ├── annotator.py         # High-level annotation API
│   │   │   ├── config.py            # Credential configuration
│   │   │   ├── coordinates.py       # PyMuPDF coordinate extraction
│   │   │   └── zotero_client.py     # Zotero Web API interactions
│   │   ├── notion_to_obsidian/      # Notion-to-Obsidian migration utilities
│   │   ├── paper_finder/            # Profile-driven arXiv retrieval, ranking, and Obsidian note output
│   │   └── report_generator/        # PDF extraction and conversion
│   │       └── converter.py         # PDF-to-Markdown and image extraction
│   ├── scripts/                     # CLI execution scripts for skills
│   └── tests/                       # Unit tests
├── skills/                          # Specialized AI agent skills
│   ├── paper-finder/                # Paper discovery skill wrapper and prompts
│   ├── paper-analyzer/              # Deep paper analysis skill
│   └── ...
├── pyproject.toml                   # Project metadata and build configuration
└── README.md                        # Chinese documentation
```

## 🤝 Contributing & Community Flywheel

We want Stable-JARVIS to be a **community flywheel**: every new skill, bug fix, or documentation improvement makes the entire academic ecosystem faster and smarter for everyone.

**PRs are extremely welcome!** Whether you're adding a new research skill, improving the PDF parsing engine, or refining the "Cyber Brain" logic, your contributions are the fuel for this project.

Feel free to check the [issues page](https://github.com/JaimeParker/JARVIS-Dev/issues) to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

Some of the built-in AI agent skills in this repository are adapted from the following open-source ecosystems:

-   **`arxiv-search`**, **`web-research`**: Adapted from [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents/tree/master/libs/deepagents-cli/examples/skills/).
-   **`skill-creator`**, **`pptx`**: Adapted from [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills).
-   **`obsidian-markdown`**: Adapted from [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills).
-   **`paper-finder`**: Adapted from [zhanglg12/research-assist](https://github.com/zhanglg12/research-assist).
-   **`autonomous-loops`**, **`verification-loop`**, **`deep-research`**, **`iterative-retrieval`**, **`python-patterns`**, **`cpp-coding-standards`**, **`videodb`**, **`docker-patterns`**, **`continuous-agent-loop`**, **`continuous-learning`**, **`exa-search`**, **`tech-doc-writing`**: Adapted from [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code).
-   **`brainstorming`**, **`executing-plans`**, **`writing-plans`**: Adapted from [obra/superpowers](https://github.com/obra/superpowers).

All credit goes to the original authors for these foundational capabilities.
