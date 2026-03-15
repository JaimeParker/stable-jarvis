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

## 🛠️ Built-in Skills

The framework includes several specialized skills that can be activated by the agent:

-   **`paper-analyzer`**: The core research skill. Orchestrates Zotero-MCP, multi-modal PDF reading, and Zotero Web API to generate deep technical reports and native annotations.
-   **`paper-finder`**: A profile-driven paper discovery skill. It queries arXiv with your research-interest profile, ranks candidates (lexical + optional semantic), and writes Obsidian-ready Markdown notes.
-   **`arxiv-search`**: Direct integration with arXiv to retrieve the latest preprints in computer science, physics, and mathematics.
-   **`web-research`**: Executes structured, deep-dive investigations using sub-agents to synthesize information from across the web.
-   **`weekly-report-generator`**: Automatically synthesizes your progress from Obsidian daily notes into a professional one-page PPTX slide.
-   **`notion-to-markdown`**: Seamlessly migrates Notion pages into your local Obsidian vault with perfect LaTeX and image localization.
-   **`obsidian-auto-classifier`**: Intelligently categorizes and archives notes within your vault based on their content and intent.
-   **`pptx` / `obsidian-markdown`**: Low-level utilities for programmatic slide generation and managing complex Obsidian syntax (wikilinks, callouts, etc.).

## 🧩 Dependencies & MCP Servers

To unlock the full power of Stable-JARVIS, you must have the following MCP servers installed and configured in your client:

-   **Zotero MCP**: [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp) — For library search and metadata retrieval.
-   **Obsidian MCP**: [bitbonsai/mcpvault](https://github.com/bitbonsai/mcpvault) — For interacting with your local "Cyber Brain."
-   **Notion MCP**: [Official Notion MCP Guide](https://developers.notion.com/guides/mcp) — For syncing with your information exchange platform.

> 💡 **Coming Soon**: Keep an eye out for our upcoming **Feishu MCP** integration!

## 🖥️ Client Configuration

Stable-JARVIS relies on a core context file to guide the AI agent's personality and logic. Depending on your chosen client, you should ensure the appropriate file exists in your project root:

-   **Gemini CLI**: Uses `GEMINI.md`
-   **Claude Code**: Uses `CLAUDE.md` (You can simply copy `GEMINI.md` to `CLAUDE.md`)
-   **Other Clients**: Refer to your client's documentation for its specific context file naming convention.

## 🌟 Key Features

- **Non-Destructive PDF Annotation**: Extracts text coordinates using `PyMuPDF` and injects highlights, comments, and notes directly via the Zotero Web API. The original PDF file hash remains completely unchanged.
- **High-Fidelity PDF to Markdown**: Converts complex academic papers (including math formulas) into LLM-friendly Markdown using `pymupdf4llm` and LaTeX source retrieval.
- **Semantic Image Extraction**: Automatically pulls figures and diagrams from PDFs, saving them locally with structural metadata manifests.
- **Zotero MCP Integration**: Seamlessly interfaces with the Zotero library to retrieve paper metadata, Item IDs, and local attachment keys based on natural language prompts.
- **Agentic Workflow Ready**: Designed to be driven by AI agents (like Gemini-CLI) executing multi-step research tasks autonomously.

## 🏗️ Architecture & Workflow

The system is built on a composite architecture that executes the following automated workflow when analyzing a paper:

1. **Dimensionality Reduction & Extraction**
   - **Retrieval**: Uses Zotero-MCP to find the target paper and its local PDF attachment key.
   - **Parsing**: Converts the PDF into Markdown text (preserving equations) and extracts local structural images for multimodal analysis.

2. **Smart Anchoring**
   - The AI Agent reads the parsed text and generates a structured research report.
   - Simultaneously, it outputs an "annotation action list" in JSON format, capturing exact quotes from the text, assigned colors, and analytical commentary.

3. **Non-Destructive Annotation Engine**
   - **Locate**: Scans the PDF to find the absolute page coordinates (bounding boxes) for the exact quotes returned by the LLM.
   - **Inject**: Transforms these coordinates into Zotero's native `annotationPosition` format and pushes them via the Zotero API, making the highlights and notes natively accessible and editable within Zotero's built-in PDF reader.

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/JaimeParker/stable-jarvis.git
cd stable-jarvis

# Ensure you are in your preferred virtual environment (e.g., conda activate jarvis)
# Install the package in editable mode with dependencies
pip install -e .
```

## ⚙️ Configuration

Configure Zotero credentials using one of these methods (in priority order):

### 🛠️ Personalization (Mandatory)

Before using the assistant, you **must** initialize your research identity by renaming the following template files and filling in your details:

1.  **System Prompt**: Rename `GEMINI.md.template` to `GEMINI.md`. Replace the placeholders with your research area and name. This file defines the agent's logic.
2.  **Daily Plan**: Rename `.gemini/commands/daily/plan.toml.template` to `.gemini/commands/daily/plan.toml` and update it with your active project names.
3.  **Zotero Credentials**: Rename `config/zotero.json.template` to `config/zotero.json` and enter your API keys. (Alternatively, use environment variables below).

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
JARVIS-Dev/
├── src/
│   ├── stable_jarvis/
│   │   ├── annotation/              # Non-destructive Zotero annotation engine
│   │   │   ├── annotator.py         # High-level annotation API
│   │   │   ├── config.py            # Credential configuration
│   │   │   ├── coordinates.py       # PyMuPDF coordinate extraction
│   │   │   └── zotero_client.py     # Zotero Web API interactions
│   │   └── report_generator/        # PDF extraction and conversion
│   │       └── converter.py         # PDF-to-MD and Image extraction
│   ├── scripts/                     # CLI execution scripts for skills
│   └── tests/                       # Unit tests
├── skills/                          # Specialized AI agent skills
├── pyproject.toml                   # Project metadata and build configuration
└── README.md
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

All credit goes to the original authors for these foundational capabilities.
