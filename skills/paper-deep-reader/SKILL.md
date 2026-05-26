---
name: paper-deep-reader
description: 精读文献。快速泛读请用paper-analyzer。
version: 1.0.0
author: Zhaohong Liu
tags:
  - zotero
  - obsidian
  - paper-analysis
  - deep-reading
---

# Paper Deep Reader（精读）

> **定位**：本 skill 实现深度论文精读——main agent 全局理解 + 6 个 subagent 并行分析 + Zotero/Obsidian 知识库横向对比 + Obsidian vault 结构化输出。如需快速泛读（单轮摘要），请使用 `paper-analyzer`。

## 核心能力

- **自适应 prompt 选择**：根据论文标题和摘要自动匹配领域专用 prompt（AI/ML、通用学术等），找不到匹配则用 default
- **Subagent 并行分析**：main agent 形成全局认知后，定制 6 个 subagent 并行撰写各 section，共享上下文，最后 main agent 合并审查
- **知识库横向对比**：Zotero MCP `semantic_search` + Obsidian `search_notes` + 可选 embedding 语义搜索
- **Obsidian 原生输出**：报告写入 vault，自动生成 `[[wikilinks]]` + frontmatter

## 配置

所有 API key 统一在 `stable-jarvis/.env` 中管理：

```bash
cp .env.example .env   # 然后编辑 .env 填入真实 key
```

`stable_jarvis` 包统一加载 `.env` 配置。

| 变量 | 说明 |
|------|------|
| `EMBEDDING_PROVIDER` | embedding 提供商（qwen/openai/local） |
| `EMBEDDING_MODEL` | embedding 模型名 |

其他依赖：
- `zotero-mcp` 已启动
- `obsidian` MCP 已配置

本 skill 的 Python 脚本位于 `scripts/` 子目录（相对于 skill 安装目录）。执行时请 `cd` 到 skill 目录或以绝对路径调用。

---

## Prompt 系统

本 skill 使用可扩展的领域专用 prompt 体系。Prompt 文件位于 `prompts/` 目录：

```
prompts/
├── categories.toml          # 领域注册表（名称、描述、关键词、persona）
├── default/                 # 通用学术 prompt（兜底，4 tasks）
│   ├── system.md            # 系统提示（persona + 写作要求）
│   ├── task-1.md            # 研究问题与背景
│   ├── task-2.md            # 核心方法与框架
│   ├── task-3.md            # 实证分析与相关工作
│   ├── task-4.md            # 局限性与批判性评价
│   └── report-template.md   # 报告结构建议
├── ai-ml/                   # AI/机器学习专用 prompt（5 tasks）
│   ├── task-1.md            # 研究问题与动机
│   ├── task-2.md            # 方法与算法设计
│   ├── task-3.md            # 相关工作与KB交叉分析
│   ├── task-4.md            # 实验与消融分析
│   ├── task-5.md            # 局限性与个人启发
│   └── ... (system.md + report-template.md)
└── rl/                      # RL/强化学习专用 prompt（6 tasks）
    ├── task-1.md            # Introduction & Related Work
    ├── task-2.md            # Algorithm & Architecture（含Mermaid）
    ├── task-3.md            # Formula Derivation & Theorems
    ├── task-4.md            # Literature Cross-Analysis（KB注入）
    ├── task-5.md            # Experiments & Results
    ├── task-6.md            # Weaknesses & Inspiration
    └── ... (system.md + report-template.md)
```

**添加新领域**：在 `categories.toml` 中注册，然后在 `prompts/` 下创建同名目录，放入 `system.md`、`task-N.md`（数量自定）、`report-template.md` 即可。无需修改任何代码。

---

## 工作流（7 阶段）

严格按以下阶段顺序执行。

---

### 阶段 1：定位论文

通过 Zotero MCP 定位论文并获取必要信息。

**步骤：**
1. 根据用户提供的标题/关键词/arxiv ID，调用 `zotero-mcp` 的 `search_library` 找到论文
2. 获取 `item_key`（父条目）、PDF attachment key
3. 调用 `get_item_details` 获取完整元数据（标题、作者、abstract、published date、arxiv ID）
4. 记录以下变量并保存为 `temp/deep-reader/meta.json`：
   - `item_key` — Zotero 父条目 key
   - `attachment_key` — PDF attachment key
   - `title` — 论文标题
   - `abstract` — 摘要
   - `authors` — 作者列表
   - `published` — 发表日期
   - `arxiv_id` — arXiv ID
   - `categories` — 领域分类

---

### 阶段 2：选择 Prompt 集合

根据阶段 1 获取的论文标题和摘要，匹配合适的领域专用 prompt。

**步骤：**
1. 读取 `prompts/categories.toml`，了解所有可用领域（名称、描述、关键词）
2. 根据论文标题和摘要，分析论文属于哪个领域
3. 选择最匹配的领域目录名（如 `ai-ml`），记录为 `PROMPT_SET`
4. 若无明确匹配，`PROMPT_SET=default`

无需脚本——直接根据 `categories.toml` 中的描述和关键词判断即可。

---

### 阶段 3：提取全文

**判断策略**：
- 如果 PDF 页数估计 < 20 页：直接用 Claude 多模态能力读取 PDF 内容
- 如果 PDF 页数 >= 20 页或无法判断：运行提取脚本

**提取脚本**（默认输出 Markdown，保留标题、LaTeX 公式、表格等结构信息）：
```bash
python scripts/extract_pdf_text.py --pdf <pdf_path> --output temp/deep-reader/paper.md
```
如需纯文本：
```bash
python scripts/extract_pdf_text.py --pdf <pdf_path> --output temp/deep-reader/paper.txt --plain
```

**长论文处理**：主 agent 自行分块摘要后派发 subagent，无需外部脚本。

---

### 阶段 4：构建 KB 上下文

两路独立搜索，不做去重/过滤/截断——subagent 有能力自行判断相关性。中间文件放 `temp/deep-reader/`。

**4a — Zotero 语义检索**
调用 `zotero-mcp` 的 `semantic_search`，query = `{title}\n{abstract}`，topK=10，minScore=0.3。
格式化为 `{title, text(abstract), published, source="zotero"}`，保存为 `temp/deep-reader/zotero_kb.json`。

**4b — Obsidian 语义搜索**
直接复用 `obsidian-semantic-search` skill 的向量库（共享 `temp/obsidian/embeddings.json`）。

索引管理遵循 `obsidian-semantic-search` SKILL.md 的判断逻辑：
```bash
# 检查索引状态
python skills/obsidian-semantic-search/scripts/build_index.py --stats

# 按需增量更新或 --force 重建
python skills/obsidian-semantic-search/scripts/build_index.py
```

搜索：
```bash
python skills/obsidian-semantic-search/scripts/search.py \
  "{title}\n{abstract}" --top-k 10 > temp/deep-reader/obsidian_kb.json
```
格式化为 `{title, text, path, source="obsidian-embed"}`。

两路结果直接交给 Phase 5，由文献交叉分析 subagent 自行判断哪些论文真正相关、标题相似的做去重——不做预过滤或预截断。

---

### 阶段 5：Subagent 并行深度分析

**无需外部脚本**。Main agent 驱动整个分析流程。

**前置条件**：`temp/deep-reader/` 下已准备好论文全文（`.md` 或 `.txt`）、`meta.json`、`zotero_kb.json`、`obsidian_kb.json`。

**若论文过长**（超过约 24,000 字符），主 agent 自行分块摘要后再派发——无需外部脚本。

---

**5a — Main agent 形成全局认知**

Main agent 读取以下内容，形成对论文的整体理解：
1. 论文全文（或分块摘要后的 condensed 版本）
2. KB 搜索结果（`zotero_kb.json` 和 `obsidian_kb.json`）
3. `prompts/{PROMPT_SET}/` 下所有 `task-*.md` 作为 subagent 任务参考模板
4. `prompts/{PROMPT_SET}/report-template.md` 了解最终报告结构

Main agent 识别论文特定的关注点——亮点、弱点、需要重点验证的声明、与 KB 论文的关键差异等。

---

**5b — Main agent 定制 subagent 任务**

`task-*.md` 文件的数量决定了 subagent 数量（rl=6, ai-ml=5, default=4）。每个 task 定义一个 subagent 的职责范围。

针对每个 task-N.md，main agent 编写定制指令，包含：

| 要素 | 说明 |
|------|------|
| Task 目标 | 参考 `task-N.md` 的分析框架和输出要求 |
| 论文特定关注点 | 如 "重点审查 pre-sampling phase 消融实验是否支撑方法声称" |
| 相关论文段落 | 与该 task 最相关的论文章节或关键段落 |
| KB context | **仅文献交叉分析 task 注入**（如 rl task-4、ai-ml task-3）。将 `zotero_kb.json` 和 `obsidian_kb.json` 的全部内容交给 subagent，由 subagent 自行判断相关性和去重 |
| 输出格式 | Markdown，参考 task-N.md 的最低字数要求 |

`task-N.md` 是**模板参考**——main agent 应根据具体论文调整指令，不要原文照抄。例如：若论文消融实验薄弱，应在实验分析 task 的指令中明确要求 subagent 指出这一点。

---

**5c — 并行 spawn subagent**

使用 `Agent` 工具并行 spawn 所有 subagent（数量 = `task-*.md` 文件数）。所有 subagent：
- 共享同一会话的论文全文上下文
- 接收 main agent 定制的 task 指令
- 各自返回对应 task 的 Markdown 产出

无需缓存——subagent 天然有上下文。

---

**5d — Main agent 合并与 double-check**

Main agent 收集全部 subagent 产出后：
1. **矛盾检查**：各 task 产出之间是否存在不一致或互相矛盾的判断
2. **事实验证**：对照论文原文验证关键数值和声称
3. **完整性检查**：是否遗漏重要分析维度
4. **渲染报告**：参考 `prompts/{PROMPT_SET}/report-template.md` 的结构建议，整合所有 subagent 产出为最终报告
5. 写入 `outputs/deep-reader/{arxiv_id}/report.md`

此步骤替代了旧的 Section 7（整合审查 API 调用）——main agent 拥有完整上下文，交叉审查更可靠。

---

### 阶段 6：写报告到 Obsidian

**报告模板**（参见 `reference/section-prompts.md` 中的 REPORT_TEMPLATE）。

**生成最终 Markdown**：
- 填充各 subagent 的产出（main agent 已完成合并审查）
- 生成 frontmatter（yaml）
- 添加 KB 相关论文的 `[[wikilinks]]`：
  - 对 KB 中找到的每篇论文，检查 Obsidian vault 中是否存在同名笔记
  - 若存在，添加 wikilink：`[[note_name]]`
  - 若不存在，仅用文本引用

**报告路径**：`outputs/deep-reader/{arxiv_id}/report.md`。

**写入 Obsidian**：
使用 `obsidian` MCP 的 `write_note`，路径为 `00 Inbox/{safe_title}.md`。
报告内容来自 `outputs/deep-reader/{arxiv_id}/report.md`。

**Frontmatter 格式**：
```yaml
---
tags:
  - paper-analysis
  - deep-reading
  - {domain_tags}
arxiv_id: "{arxiv_id}"
authors: "{authors}"
published: "{published}"
zotero_key: "{item_key}"
kb_related:
  - "[[related_paper_1]]"
  - "[[related_paper_2]]"
---
```

---

### 阶段 7：可选上传 Zotero Note

如果用户请求上传：
1. 将 Markdown 报告转换为 HTML（保留 LaTeX、wikilinks 转文本链接）
2. 通过 Zotero API 创建 Note 并挂载到 `item_key`

```bash
python scripts/upload_to_zotero.py --report <report_path> --zotero-key {item_key} --tags deep-reading,auto-generated
```

---

## 配置项

所有配置可通过环境变量或 `.env` 文件设置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EMBEDDING_PROVIDER` | `qwen` | embedding 提供商：qwen/openai/local |
| `EMBEDDING_MODEL` | 自动 | 覆盖默认 embedding 模型 |
| `OBSIDIAN_VAULT` | 自动检测 | Obsidian vault 根路径 |

---

## 与 paper-analyzer 对比

| 维度 | paper-analyzer（泛读） | paper-deep-reader（精读） |
|------|----------------------|--------------------------|
| LLM 调用 | 单轮 | 6 subagent 并行 + main agent 审查 |
| 长论文 | 上下文窗口截断 | 主 agent 自行分块处理 |
| KB 对比 | 无 | Zotero 语义 + Obsidian 向量检索 |
| 输出 | Zotero Note | Obsidian vault（wikilinks + frontmatter） |
| 上下文 | 单轮无状态 | 共享会话上下文，agent 间协同 |
| 适用场景 | 快速了解大意 | 深度理解、文献对比、知识积累 |
