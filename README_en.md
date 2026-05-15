# Stable-JARVIS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Stable-JARVIS** is an AI-powered assistant framework designed for academic researchers. It leverages Model Context Protocol (MCP) architecture, LLM agents, and a suite of specialized programmatic skills to automate the entire research lifecycle—from searching arXiv and conducting structured web-based literature reviews to generating high-fidelity Markdown reports, managing a personal "Cyber Brain" in Obsidian, and uploading analysis reports to Zotero.

Stable-JARVIS is designed to be driven by modern AI interfaces including **Gemini CLI**, **Claude Code**, **Codex**, **OpenCode**, and other MCP-compatible agents.

## 🧠 Note Management Philosophy: The Cyber Brain

This framework is built upon a specific hierarchy of knowledge management to ensure peak efficiency for both the user and their AI agents:

-   **Zotero (The Laboratory)**: The primary workspace for deep, careful literature reading. This is where raw data (PDFs) is processed and deeply analyzed.
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

-   **`paper-analyzer`**: The core research skill. Orchestrates Zotero-MCP, multi-modal PDF reading, and Zotero Web API to generate deep technical reports and upload them as Zotero Notes.
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

## 💻 Installation

This project provides interactive scripts to help you install the skills, agents, and commands. Please use the script appropriate for your operating system.

**Prerequisite: Initialize upstream skill submodules**

This project links upstream open-source skill repositories via git submodules. You must initialize them before first use:

```bash
git submodule update --init --recursive
bash scripts/sync-upstream.sh --apply
```

To pull the latest upstream updates later:
```bash
git submodule update --remote
bash scripts/sync-upstream.sh --apply
```

### Windows

1.  Open a new PowerShell terminal **as an Administrator**.
2.  Navigate to the repository root directory.
3.  If you haven't already, you may need to allow script execution by running:
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```
4.  Run the installation script:
    ```powershell
    .\install.windows.ps1
    ```

### macOS / Linux

1.  Open a terminal.
2.  Navigate to the repository root directory.
3.  Run the installation script:
    ```bash
    bash install.sh
    ```
    *(macOS users can also use `bash install_mac.sh`)*

The script will guide you through selecting your client and the asset categories to install.

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

1.  **Instruction Files**: Choose the file that matches your client. For Gemini, rename `GEMINI.md.template` to `GEMINI.md`. For Codex, copy `AGENTS.md.template` to `AGENTS.md`. Replace the placeholders with your research area and name. These files define the agent's core behavior.
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

### 1. PDF to Markdown Conversion

```python
from stable_jarvis import PDFConverter

converter = PDFConverter()
result = converter.convert("paper.pdf")

if result.success:
    print(result.markdown) # LLM-ready markdown content
```

### 2. Image Extraction with Metadata

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

### 3. Profile-driven Paper Finder (Obsidian notes)

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
├── skill-taxonomy.xml                # Skill classification & upstream source definitions (data source for install scripts)
├── upstream/                         # Upstream skill repositories (git submodules)
│   ├── everything-claude-code/       # From affaan-m/everything-claude-code
│   ├── anthropics-skills/            # From anthropics/skills
│   ├── obsidian-skills/              # From kepano/obsidian-skills
│   └── superpowers/                  # From obra/superpowers
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

If you are contributing new skills, agents, or commands, please ensure you declare them in the appropriate category within `skill-taxonomy.xml`. All three installation scripts (`install.sh`, `install_mac.sh`, `install.windows.ps1`) automatically read classifications from this file. For skills sourced from upstream repositories, add the `upstream="repo-name"` attribute.

Feel free to check the [issues page](https://github.com/JaimeParker/JARVIS-Dev/issues) to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

This repository tracks the following open-source skill repositories via git submodule symlinks:

-   **`arxiv-search`**, **`web-research`**: From [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents/tree/main/libs/cli/examples/skills).
-   **`skill-creator`**, **`pptx`**: From [anthropics/skills](https://github.com/anthropics/skills).
-   **`obsidian-markdown`**: From [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills).
-   **`premium-frontend-ui`**, **`web-coder`**: From [github/awesome-copilot](https://github.com/github/awesome-copilot).
-   **`autonomous-loops`**, **`verification-loop`**, **`deep-research`**, **`iterative-retrieval`**, **`python-patterns`**, **`cpp-coding-standards`**, **`videodb`**, **`docker-patterns`**, **`continuous-agent-loop`**, **`continuous-learning`**, **`continuous-learning-v2`**, **`exa-search`**: From [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code).
-   **`brainstorming`**, **`executing-plans`**, **`writing-plans`**: From [obra/superpowers](https://github.com/obra/superpowers).

All other skills are developed in-house. Credit goes to the original authors for these foundational capabilities.
