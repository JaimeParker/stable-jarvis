# Stable-JARVIS 能力目录

Stable-JARVIS 通过 `skills/` 和 `agents/` 两个目录提供可扩展的 AI 能力。技能分为**自研技能**（本项目开发）和**上游技能**（来自开源社区，通过 git submodule 同步）。

---

## 文献处理 (Literature)

科研文献全流程自动化——从发现、检索、泛读到深度精读。

### 自研技能

**`paper-finder`** — 论文发现引擎
- 基于研究兴趣画像（JSON profile）检索 arXiv
- 支持词法排序 + 可选语义排序（需配置 embedding）
- 输出 Obsidian 兼容的 Markdown 笔记，自动存入 Inbox
- 用法：`python skills/paper-finder/find_papers.py --profile <profile.json> --output <obsidian/inbox> [--semantic]`

**`paper-analyzer`** — 文献泛读
- 编排 Zotero MCP + 多模态 PDF 阅读，单轮 LLM 生成摘要级报告
- 自动上传为 Zotero Note，适合快速筛选大量文献
- 从 Zotero 库中直接调用，无需手动导出 PDF

**`paper-deep-reader`** — 文献精读
- Zotero MCP → Obsidian 知识库 → 6-section 深度报告
- 分块摘要、KB 横向对比、多 LLM 提供商支持
- 输出 Obsidian wikilinks 格式，自动关联已有笔记

**`paper-code-audit`** — 论文代码审计
- 对论文配套代码仓库进行系统性审查
- 检查可复现性、代码质量、与论文描述的一致性

### 上游技能

| 技能 | 来源 | 说明 |
|---|---|---|
| `arxiv-search` | deepagents | arXiv 学术搜索与摘要获取 |
| `web-research` | deepagents | 多源网络搜索与综合报告 |
| `exa-search` | everything-claude-code | Exa 神经搜索引擎 |

---

## 数据转换与知识管理 (Data Conversion & Knowledge Management)

在不同平台和格式之间无缝迁移、整理和增强知识资产。

### 自研技能

**`notion-to-markdown`** — Notion → Obsidian 迁移
- 将 Notion 页面转换为 Obsidian 友好的 Markdown
- LaTeX 公式规范化、图片本地化下载
- 属性到 frontmatter 的自动映射

**`obsidian-auto-classifier`** — 笔记自动分类
- 分析笔记内容与意图，智能归入合适的文件夹
- 支持 PARA、Zettelkasten 及自定义分类体系
- 利用 Obsidian MCP 读写 vault

**`obsidian-batch-yaml`** — 批量 YAML 增强
- 扫描指定目录（00/10/20/30），分析笔记内容
- 智能合并 AI 生成的 frontmatter（tags、summary、aliases）
- 可控标签分类体系，拒绝噪音标签

**`markitdown-convert`** — 多格式转 Markdown
- 将各种文档格式（PDF、DOCX、PPTX 等）转换为 Markdown
- 基于 Microsoft MarkItDown 库

**`markdown-to-html`** — Markdown 转 HTML
- 支持 GFM、CommonMark 及标准 Markdown 风格
- CLI 和 Node.js 两种工作流

**`knowledge-distillation-from-discussion`** — 讨论知识提炼
- 从对话、讨论记录中提取结构化知识
- 生成可供后续检索的知识卡片

**`tech-doc-writing`** — 技术文档写作
- 辅助撰写技术文档、API 文档和设计说明
- 来自ECC，但是现在被作者删了

**`weekly-report-generator`** — 周报生成器
- 从 Obsidian 每日笔记自动合成周报
- 输出为专业单页 PPTX 幻灯片

### 上游技能

| 技能 | 来源 | 说明 |
|---|---|---|
| `obsidian-markdown` | obsidian-skills | Obsidian 风格 Markdown 编辑（wikilinks、callouts、frontmatter） |
| `pptx` | anthropics-skills | PPTX 演示文稿创建与编辑 |
| `skill-creator` | anthropics-skills | 新技能创建向导 |

---

## 编程与自动化 (Coding & Automation)

来自上游社区的编程规范、设计模式和自动化工作流技能。

| 技能 | 来源 | 说明 |
|---|---|---|
| `brainstorming` | superpowers | 结构化头脑风暴 |
| `executing-plans` | superpowers | 按计划逐步执行任务 |
| `writing-plans` | superpowers | 任务规划与方案设计 |
| `python-patterns` | everything-claude-code | Python 最佳实践与 PEP 8 |
| `cpp-coding-standards` | everything-claude-code | C++ Core Guidelines |
| `docker-patterns` | everything-claude-code | Docker 与 Compose 模式 |
| `verification-loop` | everything-claude-code | 综合验证系统 |
| `iterative-retrieval` | everything-claude-code | 渐进式上下文检索 |
| `continuous-agent-loop` | everything-claude-code | 持续自主智能体循环 |
| `continuous-learning-v2` | everything-claude-code | 基于本能的会话学习系统 |
| `autonomous-loops` | everything-claude-code | 自主循环模式 |
| `deep-research` | everything-claude-code | 深度调研 |
| `premium-frontend-ui` | awesome-copilot | 前端 UI 设计指南 |
| `web-coder` | awesome-copilot | Web 开发专家 |
| `videodb` | everything-claude-code | 视频/音频处理 |

---

## 智能体 (Agents)

所有智能体均来自 `everything-claude-code` 上游仓库，由 git submodule 同步。

| 智能体 | 用途 |
|---|---|
| `architect` | 软件架构设计与技术决策 |
| `code-reviewer` | 代码审查（质量、安全、可维护性） |
| `build-error-resolver` | 构建与类型错误修复 |
| `python-reviewer` | Python 专项审查（PEP 8、类型提示） |
| `security-reviewer` | 安全漏洞检测与修复 |
| `doc-updater` | 文档与代码图谱更新 |
| `planner` | 任务规划与方案设计 |
| `loop-operator` | 循环任务执行管理 |
