# Stable-JARVIS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[English](README_en.md) | 简体中文

**Stable-JARVIS** 是专为学术研究打造的 AI 助手框架，以 **Zotero** 为文献处理引擎、**Obsidian** 为数字大脑，通过 LLM 智能体 + MCP 协议自动化科研全流程。

框架由 `skills/` 和 `agents/` 两个核心目录驱动——技能封装了可复用的 AI 工作流（文献检索、论文精读、笔记分类、格式转换等），智能体提供专业领域审查能力（代码审查、架构设计、安全审计等）。兼容 Claude Code、Gemini CLI、Codex、OpenCode 等支持 MCP 的客户端。

---

## 核心能力

Stable-JARVIS 的能力分为三大类。详见 **[docs/features.md](docs/features.md)**。

### 文献处理

从论文发现到深度精读的完整工具链：

- **`paper-finder`** — 画像驱动的 arXiv 论文发现，输出 Obsidian 笔记
- **`paper-analyzer`** — 文献泛读，单轮 LLM 生成摘要级报告并上传 Zotero Note
- **`paper-deep-reader`** — 文献精读，6-section 深度报告，Zotero与Obsidian知识库联合分析，wikilinks 输出
- **`paper-code-audit`** — 论文配套代码可复现性审计

### 数据转换与知识管理

跨平台知识迁移与笔记增强：

- **`notion-to-markdown`** — Notion → Obsidian 无缝迁移，LaTeX 规范化
- **`obsidian-auto-classifier`** — 智能笔记分类与归档
- **`obsidian-batch-yaml`** — 批量 AI 生成 frontmatter（tags、summary、aliases）
- **`markitdown-convert`** — 多格式（PDF/DOCX/PPTX）转 Markdown
- **`weekly-report-generator`** — 从 Obsidian 每日笔记自动合成 PPTX 周报
- **`knowledge-distillation-from-discussion`** — 讨论记录中提炼结构化知识

### 编程与自动化

来自上游开源社区的 15+ 编程规范、设计模式和自动化技能，涵盖 Python/C++ 编码标准、Docker 模式、持续学习系统、前端设计等。另有 8 个专业审查智能体（架构、代码、安全、构建等）。

---

## 安装

```bash
# 克隆仓库
git clone https://github.com/JaimeParker/stable-jarvis.git
cd stable-jarvis

# 初始化上游技能子模块并创建符号链接
git submodule update --init --recursive
bash scripts/sync-upstream.sh --apply

# 以开发者模式安装该包及其依赖
pip install -e .

# 如需使用 paper-finder 语义搜索（--semantic），安装 semantic 扩展
pip install -e '.[semantic]'
```

之后若需拉取上游最新更新：

```bash
git submodule update --remote
bash scripts/sync-upstream.sh --apply
```

### 平台安装脚本

项目提供了交互式脚本，帮助为指定客户端安装技能、智能体和命令：

- **Windows**：以管理员身份运行 PowerShell，执行 `.\install.windows.ps1`（首次可能需要 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`）
- **macOS / Linux**：执行 `bash install.sh`（macOS 也可用 `bash install_mac.sh`）

脚本会引导你选择客户端和要安装的资产类别。

---

## 配置

### API 密钥

所有 API 密钥统一在项目根目录的 `.env` 文件中管理：

```bash
cp .env.example .env
# 编辑 .env，填入真实 key
```

主要变量：

```bash
# LLM（paper-deep-reader 精读）
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-pro
DEEPSEEK_API_KEY=sk-your-key-here

# Embedding（paper-deep-reader + paper-finder）
EMBEDDING_PROVIDER=qwen
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
EMBEDDING_API_KEY=sk-your-key-here
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1

# Zotero（paper-analyzer + paper-deep-reader）
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
ZOTERO_LIBRARY_TYPE=user

# Exa Search（exa-search skill）
EXA_API_KEY=your-exa-key-here
```

> `.env` 已被 `.gitignore` 排除。`stable_jarvis` 包在 import 时自动加载 `.env`。同名系统环境变量优先级更高。

### 客户端指令文件

根据使用的客户端选择对应模板：

- **Gemini CLI**：重命名 `GEMINI.md.template` → `GEMINI.md`
- **Codex**：复制 `AGENTS.md.template` → `AGENTS.md`

将占位符替换为你的研究领域和姓名。

### 其他初始化

- **每日计划**：复制 `commands/daily/plan.toml.template` → `commands/daily/plan.toml`，按项目修改
- **研究画像**：参考 `config/research-interest.example.json` 创建你的检索画像

### Embedding 推荐

使用 SiliconFlow 服务时，推荐从 `Qwen/Qwen3-Embedding-8B` 开始，`EMBEDDING_BASE_URL` 设为 `https://api.siliconflow.cn/v1`。详见 [SiliconFlow Models](https://cloud.siliconflow.cn/me/models?types=embedding)。

---

## 依赖与 MCP 服务器

要发挥全部能力，需要在客户端中配置以下 MCP 服务器：

- **Zotero MCP**: [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp) — 文献库搜索与元数据检索
- **Obsidian MCP**: [bitbonsai/mcpvault](https://github.com/bitbonsai/mcpvault) — 本地数字大脑交互
- **Notion MCP**: [官方 Notion MCP 指南](https://developers.notion.com/guides/mcp) — 协作平台同步

> 使用飞书的团队推荐 [飞书 CLI](https://github.com/larksuite/cli) 进行集成。

---

## 笔记管理哲学：数字大脑

本框架基于特定的知识管理层级构建，确保用户与 AI 智能体拥有最高的执行效率：

- **Zotero (实验室)**：深度阅读文献的核心工作区，原始数据（PDF）被深度处理和分析的地方。
- **Obsidian (本地数字大脑)**：经过精选的本地知识库，仅包含已总结、用户验证的高信号信息。它充当智能体读取和引用的外部逻辑引擎，严格用于**知识摄取与合成**。
- **Notion (交换站)**：协作、快速记录、数据库管理的动态平台，充当原始信息的"收件箱"和共享结果的"输出口"。

### Obsidian 库架构

采用 PARA 风格层级结构（00 Inbox → 10 Projects → 20 Areas → 30 Zettelkasten → 40 Resources → 50 Archive → 60 System），由 `paper-finder` 等技能自动填充内容。

→ 完整架构见 **[docs/obsidian_guide.md](docs/obsidian_guide.md)**

---

## 快速开始

### PDF 转 Markdown

```python
from stable_jarvis import PDFConverter

converter = PDFConverter()
result = converter.convert("paper.pdf")

if result.success:
    print(result.markdown)  # 可供 LLM 阅读的 Markdown 内容
```

### 提取图像与元数据

从论文中提取图表并生成结构化清单，配合 Markdown 输出可生成带图报告：

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

更多功能（论文发现 CLI 等）详见 **[docs/features.md](docs/features.md)**。

---

## 贡献与社区飞轮

欢迎提交 PR。无论是添加新技能、改进 PDF 解析，还是优化数字大脑逻辑。

**贡献规则：**

- **上游技能**（来自开源社区）：请先向上游仓库提交修改，然后通过 `sync-upstream.sh --apply` 同步回本仓库。参见 `skill-taxonomy.xml` 中的 `upstream` 属性确认技能来源。
- **自研技能**：直接 PR 到本仓库。新增技能/智能体/命令时，请在 `skill-taxonomy.xml` 相应类别中声明。

欢迎访问 [issues 页面](https://github.com/JaimeParker/stable-jarvis/issues) 开始贡献。

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 致谢

本仓库通过 git submodule 符号链接跟踪以下开源技能仓库：

- **`arxiv-search`**, **`web-research`**: 来自 [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)
- **`skill-creator`**, **`pptx`**: 来自 [anthropics/skills](https://github.com/anthropics/skills)
- **`obsidian-markdown`**: 来自 [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)
- **`premium-frontend-ui`**, **`web-coder`**: 来自 [github/awesome-copilot](https://github.com/github/awesome-copilot)
- **`autonomous-loops`**, **`verification-loop`**, **`deep-research`**, **`iterative-retrieval`**, **`python-patterns`**, **`cpp-coding-standards`**, **`videodb`**, **`docker-patterns`**, **`continuous-agent-loop`**, **`continuous-learning`**, **`continuous-learning-v2`**, **`exa-search`**: 来自 [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)
- **`brainstorming`**, **`executing-plans`**, **`writing-plans`**: 来自 [obra/superpowers](https://github.com/obra/superpowers)
- **`paper-finder`** 的源代码来自 [zhanglg12/research-assist](https://github.com/zhanglg12/research-assist)

其余技能为本项目自行开发。感谢上述开源作者提供的核心能力。
