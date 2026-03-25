# Stable-JARVIS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[English](README_en.md) | 简体中文

**Stable-JARVIS** 是专为学术研究人员设计的 AI 助手框架。它利用模型上下文协议 (MCP) 架构、LLM 智能体和一系列专用的编程技能，实现了科研全生命周期的自动化：从 arXiv 检索和多维网页调研，到深度文献解析、生成结构化 Markdown 报告、管理 Obsidian “数字大脑”，以及将原生批注无损写回 Zotero 中。

Stable-JARVIS 旨在由现代 AI 接口驱动，包括 **Gemini CLI**, **Claude Code**, **Codex**, **OpenCode** 以及其他兼容 MCP 的智能体。

## 🧠 笔记管理哲学：数字大脑 (Cyber Brain)

本框架基于特定的知识管理层级构建，以确保用户及其 AI 智能体拥有最高的执行效率：

-   **Zotero (实验室)**：深度、仔细阅读文献的核心工作区。这是原始数据 (PDF) 被处理并通过无损引擎进行初始批注的地方。
-   **Obsidian (本地数字大脑)**：经过精选的本地知识库。它是一个“无尘室”，仅包含经过总结、用户验证和高信号的信息。它充当编程智能体读取和引用的外部逻辑引擎，构成了您的“数字大脑”。在这个生态系统中，Obsidian 严格用于**知识摄取与合成**——它是事实的来源，而非信息分发渠道。
-   **Notion (交换站与输入框)**：用于协作、快速记录、数据库管理和跨团队讨论的动态平台。它充当原始信息的“收件箱”以及共享结果和发布的“输出口”。

### 📁 推荐的 Obsidian 库架构 (Recommended Vault Structure)

为了让 Stable-JARVIS 技能（如 `paper-finder` 和 `daily plan`）发挥最佳性能，建议您的 Obsidian 库采用以下层次结构：

```text
/ (Vault Root)
├── 00 Inbox/                # 新建笔记、论文草案及待分类信息的收件箱
├── 10 Projects/             # 当前正在进行的科研项目 (Active Projects)
├── 20 Areas/                # 持续关注的研究领域 (Research Areas)
├── 30 Zettelkasten/         # 永久性的知识点原子笔记 (Permanent Notes)
├── 40 Resources/            # 长期参考资料
│   └── 42 Assets/
│       └── Templates/       # 包含 Daily Note Template.md 等核心模板
├── 50 Archive/              # 已完成或非活跃的项目归档
│   └── Daily Notes/         # 存放 YYYY-MM-DD.md 格式的每日笔记
└── 60 System/               # 库自身的元数据与配置
```

## 🛠️ 内置技能 (Built-in Skills)

框架包含多个可供智能体调用的专用技能：

-   **`paper-analyzer`**: 核心科研技能。编排 Zotero-MCP、多模态 PDF 阅读和 Zotero Web API，生成深度技术报告和原生批注。
-   **`paper-finder`**: 基于研究兴趣画像的论文发现技能。按 profile 检索 arXiv，执行词法+可选语义排序，并输出 Obsidian 可直接摄取的 Markdown 笔记。
-   **`weekly-report-generator`**: 自动将 Obsidian 每日笔记中的进度合成到专业的单页 PPTX 幻灯片中。
-   **`notion-to-markdown`**: 将 Notion 页面无缝迁移到本地 Obsidian 库中，并实现完美的 LaTeX 公式和图像本地化。
-   **`obsidian-auto-classifier`**: 根据内容和意图，智能地对库中的笔记进行分类和归档。
-   ...

## 🧩 依赖与 MCP 服务器

要释放 Stable-JARVIS 的全部威力，您必须在客户端中安装并配置以下 MCP 服务器：

-   **Zotero MCP**: [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp) — 用于库搜索和元数据检索。
-   **Obsidian MCP**: [bitbonsai/mcpvault](https://github.com/bitbonsai/mcpvault) — 用于与您的本地“数字大脑”交互。
-   **Notion MCP**: [官方 Notion MCP 指南](https://developers.notion.com/guides/mcp) — 用于与您的信息交换平台同步。

> 💡 **即将到来**：敬请关注我们即将推出的 **Feishu (飞书) MCP** 集成！

## 💻 客户端安装与集成 (Client Installation & Integration)

Stable-JARVIS 支持多种 AI 客户端。为了获得最佳体验，我们建议使用 **符号链接 (Symlink)** 来注册提供的智能体和技能，这样仓库中的更新将自动反映在您的客户端中。

### 1. Gemini CLI
Gemini CLI 自动识别 `.gemini/commands/` 下的 `.toml` 文件，通过 `skills` 命令管理技能，并支持通过 Markdown 文件定义的子智能体。

- **配置 Exa Search (MCP)**:
  在 `~/.gemini/settings.json` 中添加以下配置以启用远程 Exa MCP 服务：
  ```json
  {
    "mcpServers": {
      "exa": {
        "httpUrl": "https://mcp.exa.ai/mcp"
      }
    }
  }
  ```
- **安装子智能体 (Subagents)**:
  ```bash
  # 全局安装 (推荐)
  mkdir -p ~/.gemini/agents
  ln -s $(pwd)/agents/*.md ~/.gemini/agents/

  # 项目局部安装 (可选)
  mkdir -p .gemini/agents
  ln -s $(pwd)/agents/*.md .gemini/agents/
  ```
- **安装命令 (Commands)**:
  ```bash
  # 将本项目命令链接到项目局部配置
  mkdir -p .gemini/commands
  ln -s $(pwd)/commands/daily/plan.toml .gemini/commands/daily:plan.toml
  ln -s $(pwd)/commands/paper/analyze.toml .gemini/commands/paper:analyze.toml
  # 在 Gemini CLI 中刷新命令: /commands reload
  ```
- **安装技能 (Skills)**:
  ```bash
  # 链接技能到全局作用域 (推荐)
  gemini skills link ./skills

  # 链接到项目局部作用域 (可选)
  gemini skills link ./skills --scope workspace
  ```

### 2. Claude Code
Claude Code 在 `.claude/` 目录下查找智能体定义和技能。

- **安装智能体 (Agents)**:
  ```bash
  # 全局注册 (推荐)
  mkdir -p ~/.claude/agents
  ln -s $(pwd)/agents/*.md ~/.claude/agents/

  # 项目内注册 (可选)
  mkdir -p .claude/agents
  ln -s $(pwd)/agents/*.md .claude/agents/
  ```
- **集成技能 (Skills)**:
  ```bash
  # 全局链接技能目录 (推荐)
  mkdir -p ~/.claude/skills
  ln -s $(pwd)/skills/* ~/.claude/skills/

  # 项目内局部链接 (可选)
  mkdir -p .claude/skills
  ln -s $(pwd)/skills/* .claude/skills/
  ```
- **配置 Exa Search (MCP)**:
  ```bash
  # 运行以下命令添加 Exa MCP 服务器，将 YOUR_API_KEY 替换为您的真实 Key
  claude mcp add --transport http exa "https://mcp.exa.ai/mcp?exaApiKey=YOUR_API_KEY&tools=web_search_exa,get_code_context_exa"
  ```

### 3. Codex / GitHub Copilot
对于 Codex，请使用 `AGENTS.md` 作为仓库级指令文件。对于 GitHub Copilot 扩展或自定义智能体，可以通过以下方式链接指令和技能：

- **安装指令文件**:
  ```bash
  # Codex 仓库内指令 (推荐新手使用)
  cp AGENTS.md.template AGENTS.md

  # GitHub Copilot 全局指令链接 (可选)
  mkdir -p ~/.copilot/instructions
  ln -s $(pwd)/AGENTS.md ~/.copilot/instructions/stable-jarvis.md

  # 项目局部链接 (可选)
  mkdir -p .github/instructions
  ln -s $(pwd)/AGENTS.md .github/instructions/stable-jarvis.md
  ```
- **安装技能 (Skills)**:
  ```bash
  # 全局链接技能目录 (推荐)
  mkdir -p ~/.copilot/skills
  ln -s $(pwd)/skills/* ~/.copilot/skills/

  # 项目局部链接 (可选)
  mkdir -p .github/skills
  ln -s $(pwd)/skills/* .github/skills/
  ```

---

## 🔒 安全与环境变量配置 (Security & Environment Variables)

为了保护您的 API 密钥不被泄露，Stable-JARVIS 建议优先使用**系统环境变量**而非本地配置文件。

### 核心 API 密钥配置
在您的 `~/.bashrc` 或 `~/.zshrc` 中添加以下行：

```bash
# Exa Search API Key (Claude Code 与 Gemini-CLI 共用)
export EXA_API_KEY="您的_EXA_API_KEY"

# Zotero 凭证
export ZOTERO_LIBRARY_ID="您的_ID"
export ZOTERO_API_KEY="您的_KEY"

# 语义搜索 Embedding API (如果您使用 paper-finder --semantic)
export STABLE_JARVIS_SEMANTIC_API_KEY="您的_KEY"
export STABLE_JARVIS_SEMANTIC_API_BASE_URL="https://api.your-provider.com/v1"
```

> 💡 **注意**：如果您已经设置了环境变量，Stable-JARVIS 将**优先**使用它们，而忽略 `config/api_keys.json` 或 `config/zotero.json` 中的相应字段。这能有效防止 API Key 被误提交到版本库中。

---

## 🚀 安装

```bash
# 克隆仓库
git clone https://github.com/JaimeParker/stable-jarvis.git
cd stable-jarvis

# 确保你处于首选的虚拟环境中（如：conda activate jarvis）
# 以开发者模式安装该包及其依赖
pip install -e .

# 如需使用 paper-finder 的语义搜索（--semantic），请安装 semantic 扩展依赖
pip install -e '.[semantic]'
```

## ⚙️ 配置

批注引擎需要 Zotero API 凭证。你可以通过环境变量或配置文件提供这些信息。[Notion helper page](https://zhliu25.notion.site/stable-jarvis-3191d1c4d39280b68608e1430ef82dcb)

### 🛠️ 个性化定制 (必读)

在开始使用之前，您**必须**通过重命名以下模板文件并填写您的个人信息来初始化您的科研身份：

1.  **指令文件**: 根据您使用的客户端选择对应文件。Gemini 用户请将 `GEMINI.md.template` 重命名为 `GEMINI.md`；Codex 用户请将 `AGENTS.md.template` 复制为 `AGENTS.md`。将占位符替换为您具体的研究领域和姓名。这些文件定义了智能体的核心行为。
2.  **每日计划命令**: `daily plan` 需要您自行配置；项目已提供模板 `commands/daily/plan.toml.template`，请复制为 `commands/daily/plan.toml` 后按您的项目实际情况修改。
3.  **Zotero 凭证**: 将 `config/zotero.json.template` 重命名为 `config/zotero.json` 并填入您的 API 密钥（或者使用下方的环境变量方式）。
4.  **语义搜索凭证（可选）**: 如果您要使用 `paper-finder --semantic`，请基于 `config/api_keys.json.template` 创建 `config/api_keys.json`，并填写 `semantic_model.api_base_url`、`semantic_model.api_key` 与 `semantic_model.model`（或改用环境变量方式）。

### 选项 1：环境变量（推荐用于 CI/生产环境）

```bash
export ZOTERO_LIBRARY_ID="你的_library_id"
export ZOTERO_API_KEY="你的_api_key"
export ZOTERO_LIBRARY_TYPE="user"  # 可选，默认为 "user"
```

### 选项 2：配置文件

在以下任一位置创建一个 `zotero.json` 文件（系统按顺序搜索，找到即止）：
1. `./zotero.json` (当前工作目录)
2. `./config/zotero.json` (相对当前工作目录)
3. `~/.config/stable-jarvis/zotero.json` (用户配置目录)

**`zotero.json` 示例：**
```json
{
    "library_id": "你的_library_id",
    "api_key": "你的_api_key",
    "library_type": "user"
}
```

如需启用 `paper-finder` 的语义搜索，还需要准备 `config/api_keys.json`。可直接复制模板 `config/api_keys.json.template`，并填写如下字段：

```json
{
    "semantic_model": {
        "api_base_url": "https://api.your-provider.com/v1",
        "api_key": "your_semantic_api_key",
        "model": "your-embedding-model"
    }
}
```

或者也可以直接使用环境变量配置语义搜索：

```bash
export STABLE_JARVIS_SEMANTIC_API_BASE_URL="https://api.your-provider.com/v1"
export STABLE_JARVIS_SEMANTIC_API_KEY="your_semantic_api_key"
export STABLE_JARVIS_SEMANTIC_MODEL="your-embedding-model"
```

如果您使用的是 SiliconFlow 的 embedding 服务，建议从 `Qwen/Qwen3-Embedding-8B` 开始尝试，参考[SiliconFlow Embedding Models](https://cloud.siliconflow.cn/me/models?types=embedding)。比如 `api_base_url` 可以是 `https://api.siliconflow.cn/v1`，`model` 则是 `Qwen/Qwen3-Embedding-8B`。

## 📖 快速开始

### 1. 自动批注

通过代码向 Zotero 的 PDF 附件注入高亮和评论。

```python
from stable_jarvis import annotate

result = annotate(
    pdf_path="/path/to/local/paper.pdf",
    attachment_key="ABC12345", # PDF 的 Zotero Attachment Key
    target_text="We formulate the search-to-control problem as a Markov Decision Process",
    comment="这里定义了 MDP 的状态空间，是一个重要的区别。",
    color="#ff6666" 
)

if result.success:
    print(f"成功创建批注！Zotero Key: {result.annotation_key}")
```

### 2. PDF 转 Markdown

```python
from stable_jarvis import PDFConverter

converter = PDFConverter()
result = converter.convert("paper.pdf")

if result.success:
    print(result.markdown) # 可供 LLM 阅读的 Markdown 内容
```

### 3. 提取图像与元数据

从论文中提取图表并生成结构化清单。

```python
from stable_jarvis import PDFConverter

converter = PDFConverter()

# 提取高质量图像并检索定位元数据
metadata = converter.extract_images_with_metadata(
    "paper.pdf",
    output_dir="./figures",
    quality="high",  # 选项: low, medium, high, epic
    name_prefix="ABC12345"
)

# 保存清单 JSON 以供 LLM 引用
converter.save_image_manifest(metadata, "./figures/manifest.json")
# 输出示例: [{"filename": "ABC12345_fig1.png", "page": 1, "description": "Figure at the top of page 1"}]
```

### 4. 画像驱动的论文发现（输出 Obsidian 笔记）

```bash
# 运行基于 profile 的检索与排序，输出 Markdown 笔记
conda run -n jarvis python skills/paper-finder/find_papers.py \
    --profile path/to/research-interest.json \
    --output path/to/obsidian/inbox

# 启用语义排序（自动读取 config/api_keys.json 中 semantic_model）
conda run -n jarvis python skills/paper-finder/find_papers.py \
    --profile path/to/research-interest.json \
    --output path/to/obsidian/inbox \
    --semantic
```

## 📁 项目结构

```text
stable-jarvis/
├── config/                          # 本地配置模板与凭证文件
│   ├── zotero.json.template         # Zotero API 配置模板
│   ├── api_keys.json.template       # paper-finder 语义搜索配置模板
│   └── research-interest.example.json  # 研究兴趣画像示例
├── commands/                        # 面向客户端/智能体的命令模板
│   ├── daily/                       # 每日计划命令
│   └── paper/                       # 论文相关命令
├── src/
│   ├── stable_jarvis/
│   │   ├── annotation/              # 无损 Zotero 批注引擎
│   │   │   ├── annotator.py         # 高级批注 API
│   │   │   ├── config.py            # 凭证配置
│   │   │   ├── coordinates.py       # PyMuPDF 坐标提取
│   │   │   └── zotero_client.py     # Zotero Web API 交互
│   │   ├── notion_to_obsidian/      # Notion 页面迁移到 Obsidian
│   │   ├── paper_finder/            # 画像驱动的 arXiv 检索、排序与 Obsidian 输出
│   │   └── report_generator/        # PDF 提取与转换
│   │       └── converter.py         # PDF 转 Markdown 与图像提取
│   ├── scripts/                     # 供技能 (skills) 调用的 CLI 执行脚本
│   └── tests/                       # 单元测试
├── skills/                          # 专用的 AI 智能体技能 (Agent Skills)
│   ├── paper-finder/                # 论文发现 skill 包装层与提示词
│   ├── paper-analyzer/              # 深度论文分析 skill
│   └── ...
├── pyproject.toml                   # 项目元数据与构建配置
└── README_en.md                     # 英文文档
```

## 🤝 贡献与社区飞轮 (Flywheel)

我们希望将 Stable-JARVIS 打造为一个**社区飞轮**：每一个新技能、每一次 Bug 修复或文档改进，都会让整个学术生态系统对每个人来说都变得更快、更智能。

**非常欢迎提交 PR！** 无论您是添加新的科研技能、改进 PDF 解析引擎，还是优化“数字大脑”逻辑，您的贡献都是本项目前进的动力。

欢迎访问 [issues 页面](https://github.com/JaimeParker/JARVIS-Dev/issues) 开始贡献。

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢 (Acknowledgements)

本仓库内置的部分 AI 智能体技能改编自以下开源生态系统：

-   **`arxiv-search`**, **`web-research`**: 改编自 [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents/tree/master/libs/deepagents-cli/examples/skills/)。
-   **`skill-creator`**, **`pptx`**: 改编自 [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills)。
-   **`obsidian-markdown`**: 改编自 [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)。
-   **`paper-finder`**: 改编自 [zhanglg12/research-assist](https://github.com/zhanglg12/research-assist)。
-   **`autonomous-loops`**, **`verification-loop`**, **`deep-research`**, **`iterative-retrieval`**, **`python-patterns`**, **`cpp-coding-standards`**, **`videodb`**, **`docker-patterns`**, **`continuous-agent-loop`**, **`continuous-learning`**, **`exa-search`**, **`tech-doc-writing`**: 改编自 [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)。
-   **`brainstorming`**, **`executing-plans`**, **`writing-plans`**: 改编自 [obra/superpowers](https://github.com/obra/superpowers)。

感谢原作者提供的这些核心能力。
