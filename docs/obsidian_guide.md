# Obsidian 数字大脑架构指南 / Obsidian Cyber Brain Guide

## 笔记管理哲学：数字大脑 (Cyber Brain)

本框架基于特定的知识管理层级构建，以确保用户及其 AI 智能体拥有最高的执行效率：

- **Zotero (实验室)**：深度、仔细阅读文献的核心工作区。这是原始数据 (PDF) 被深度处理和分析的地方。
- **Obsidian (本地数字大脑)**：经过精选的本地知识库。它是一个"无尘室"，仅包含经过总结、用户验证和高信号的信息。它充当编程智能体读取和引用的外部逻辑引擎，构成了您的"数字大脑"。在这个生态系统中，Obsidian 严格用于**知识摄取与合成**——它是事实的来源，而非信息分发渠道。
- **Notion (交换站与输入框)**：用于协作、快速记录、数据库管理和跨团队讨论的动态平台。它充当原始信息的"收件箱"以及共享结果和发布的"输出口"。

---

## Note Management Philosophy: The Cyber Brain

This framework is built upon a specific hierarchy of knowledge management to ensure peak efficiency for both the user and their AI agents:

- **Zotero (The Laboratory)**: The primary workspace for deep, careful literature reading. This is where raw data (PDFs) is processed and deeply analyzed.
- **Obsidian (The Local Cyber Brain)**: A curated, local knowledge base. It is a "clean room" containing only summarized, user-verified, and high-signal information. It functions as an external logical engine for coding agents to read and reference, effectively forming your "Cyber Brain." In this ecosystem, Obsidian is strictly for **ingestion and synthesis** — it is the source of truth, not a broad distribution channel.
- **Notion (The Exchange & Input Box)**: A dynamic platform for collaboration, quick notes, database management, and cross-team discussion. It acts as the "Inbox" for raw information and the "Output" for shared results and sharing.

---

## 推荐的 Obsidian 库架构 / Recommended Vault Structure

为了让 Stable-JARVIS 技能（如 `paper-finder` 和 `daily plan`）发挥最佳性能，建议您的 Obsidian 库采用以下层次结构：

```text
/ (Vault Root)
├── 00 Inbox/                # 新建笔记、论文草案及待分类信息的收件箱
├── 10 Projects/             # 当前正在进行的科研项目 (Active Projects)
├── 20 Areas/                # 持续关注的研究领域 (Research Areas)
├── 30 Zettelkasten/         # 永久性的知识点原子笔记
│   ├── 31 Literature/       #   文献阅读笔记
│   ├── 32 Permanent/        #   永久笔记
│   └── 33 Maps of Content/  #   内容地图 (MOC)
├── 40 Resources/            # 长期参考资料
│   └── 42 Assets/
│       └── Templates/       # 包含 Daily Note Template.md 等核心模板
├── 50 Archive/              # 已完成或非活跃的项目归档
│   └── Daily Notes/         # 存放 YYYY-MM-DD.md 格式的每日笔记
└── 60 System/               # 库自身的元数据与配置
    └── Tag Taxonomy.md      # 受控标签词汇表
```

### 各目录说明

| 目录 | 用途 |
|---|---|
| `00 Inbox/` | 快速捕获：新想法、论文草稿、待处理的临时笔记 |
| `10 Projects/` | 活跃项目：有明确目标和截止日期的当前工作 |
| `20 Areas/` | 持续责任区：没有截止日期的长期关注领域 |
| `30 Zettelkasten/` | 知识网络：原子化的永久笔记，通过 wikilinks 互连 |
| `40 Resources/` | 参考资料：模板、附件、静态资源 |
| `50 Archive/` | 冷存储：已完成/非活跃项目，每日笔记归档 |
| `60 System/` | 库元数据：标签分类法、配置、脚本 |
