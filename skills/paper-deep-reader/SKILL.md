---
name: paper-deep-reader
description: 精读文献。快速泛读请用paper-quick-read。
version: 1.0.0
author: Zhaohong Liu
tags:
  - zotero
  - obsidian
  - paper-analysis
  - deep-reading
---

# Paper Deep Reader（精读）

> **定位**：本 skill 实现深度论文精读——main agent 全局理解 + 6 个 subagent 并行分析 + Zotero/Obsidian 知识库横向对比 + Obsidian vault 结构化输出。如需快速泛读（单轮摘要），请使用 `paper-quick-read`。

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
- 如果 PDF 页数估计 < 20 页：用 Claude 多模态能力或 zotero mcp 读取 PDF 内容
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

**5a 必须产出：写入 `temp/deep-reader/global-understanding.md`**，作为所有 subagent 的共享前置阅读材料。内容必须包含：

| 内容 | 说明 |
|------|------|
| 论文概要 | 一句话贡献 + 核心方法 + 主要结果 |
| 复杂度评估 | **简单**（单点创新，如 BPPO）/ **中等**（2-3 个组件）/ **复杂**（系统级论文，如 LWD） |
| 重点分析方向 | 3-5 个最值得深挖的点（引导各 task 聚焦） |
| Task 边界表 | 每个 task 的**独占内容范围** + **禁止涉及的内容**（防止跨 task 重叠）+ **篇幅预算**（按复杂度：简单 50-70 行 / 中等 80-120 行 / 复杂 120-180 行） |
| 跨 task 注意事项 | 已知可能重叠的区域（如 "DIVL 的核心机制由 Task 2 负责架构描述、Task 3 负责公式推导，两者不得交叉展开"） |

此文件是 subagent 之间唯一的协调机制——没有它，6 个 subagent 就是 6 个独立审稿人各自写完整报告。

---

**5b — Main agent 定制 subagent 任务**

`task-*.md` 文件的数量决定了 subagent 数量（rl=6, ai-ml=5, default=4）。每个 task 定义一个 subagent 的职责范围。

**5b-1：划分 task 边界。** 在编写指令之前，主 agent 必须对照 `report-template.md` 的章节结构，明确划分每个 task 的独占内容范围、禁止涉及的内容、以及篇幅预算。这些边界写入 `global-understanding.md` 的 Task 边界表。此步骤是防止跨 task 冗余的关键——没有边界，每个 subagent 会趋向于写一篇完整报告。


针对每个 task-N.md，main agent 编写定制指令，包含：

| 要素 | 说明 |
|------|------|
| Task 目标 | 参考 `task-N.md` 的分析框架和输出要求，尽量按照要求 |
| 论文特定关注点 | 如 "重点审查 pre-sampling phase 消融实验是否支撑方法声称" |
| 相关论文段落 | 与该 task 最相关的论文章节或关键段落 |
| KB context | **仅文献交叉分析 task 注入**（如 rl task-4、ai-ml task-3）。将 `zotero_kb.json` 和 `obsidian_kb.json` 的全部内容交给 subagent，由 subagent 自行判断相关性和去重 |
| 输出格式 | Markdown，参考 task-N.md 的最低字数要求。**所有数学公式必须使用 LaTeX 格式：行内公式用 `$...$`，独立公式用 `$$...$$`，不得使用 \( \) 或 \[ \]**。**要求 subagent 使用 `##` 作为最高层级标题（不使用 `#`），并明确告知其产出将嵌入报告模板的哪个章节位置**（如 "你的产出将嵌入 `## 1. 研究问题与动机` 下"），以便 subagent 理解自身内容在整体报告中的定位 |
| 嵌入位置 | 告知 subagent 其产出将被嵌入报告模板的哪个章节（如 `## 1. 研究问题与动机`、`### 2.1 算法与架构`）。这帮助 subagent 理解内容定位，也为主 agent 后续组装时的标题降级提供依据 |
| 篇幅预算 | 根据 5a 的复杂度评估，为当前 task 分配预期行数范围（简单 50-70 / 中等 80-120 / 复杂 120-180）。同时告知 subagent 哪些主题由其他 task 负责，不得越界 |

`task-N.md` 是**模板参考**——main agent 应根据具体论文调整指令，不要原文照抄。例如：若论文消融实验薄弱，应在实验分析 task 的指令中明确要求 subagent 指出这一点。

---

**5c — 并行 spawn subagent**

使用 `Agent` 工具并行 spawn 所有 subagent（数量 = `task-*.md` 文件数）。所有 subagent：
- **每个 subagent 必须在启动时首先 Read `temp/deep-reader/global-understanding.md`**，了解：(a) 论文全局判断，(b) 自己的 task 边界和禁止范围，(c) 篇幅预算。
- 在 spawn subagent 之前，主 agent 必须确认 `global-understanding.md` 已写入且内容完整（包含所有 task 的边界表）。
- 接收 main agent 定制的 task 指令
- 各自返回对应 task 的 Markdown 产出

---

**5d — 第一次组装（纯拼接 + 重整标题层级）**

Main agent 收集全部 task-subagent 的原始产出后，按 `report-template.md` 的结构进行组装：

**步骤 1：重整标题层级。** Subagent 产出的标题层级可能与报告模板不匹配（如使用 `#` 顶级标题、层级跳跃、嵌套深度不当等）。主 agent 必须逐节审查各 subagent 产出的标题，将其调整到与嵌入位置匹配的正确层级：

- 先读取 `report-template.md`，明确每个 task 产出嵌入的父级标题级别（如 `## 1. 研究问题与动机` → 父级为 h2；`### 2.1 算法与架构` → 父级为 h3）
- 审查 subagent 产出中的实际标题使用情况
- 将标题调整到正确嵌套深度：位于 h2 父级下的，内容标题应从 h3 开始；位于 h3 父级下的，内容标题应从 h4 开始
- 不留孤立的 `#` 顶级标题（与论文标题冲突）；同级内容使用同级别标题；不出现层级跳跃

**步骤 2：章节顺序排列 + 移除废话。**
- 按 `report-template.md` 的章节顺序排列
- 移除 subagent 产出的前言/后记废话（如 "Now I will write the section..."）
- **允许**：删除跨 task 重复的段落——同一事实/分析在多个 section 出现时，保留信息最完整的一处，其余改为引用或直接删除
- **允许**：压缩啰嗦但信息密度低的段落（如过度展开的常识性解释）
- **禁止**：删除任何数据、公式、原文引用、实验数字
- **禁止**：改变 subagent 的实质性论点或分析结论
- **原则**：精简的目标是去冗余，不是压缩信息量。宁可保留疑似冗余的深度分析，不可删除关键论证
- 产生第一版组装报告 `report-v1.md`

---

**5e — 事实核查（Fact-Check Subagent）**

Spawn 1 个 fact-check subagent，专门对照论文原文核查所有 task-subagent 产出的准确性。

**输入**：论文原文 + 全部 task-subagent 原始产出 + 第一版组装报告

**核心约束**：极度依赖原文——每个判断必须有原文具体引用（章节号或原文摘录），不允许凭记忆或常识判断。

**输出格式**——逐条差异报告，每条标注：
- ✅ **正确**：声明与原文一致，附原文证据
- ❌ **错误**：声明与原文矛盾，附原文正确信息 + 建议修正
- ⚠️ **不可验证**：原文未涉及此声明（可能是 subagent 的合理推断或外部知识），标注为不可验证
- 🔶 **部分偏差**：数字正确但结论夸大、遗漏关键限定条件等情况，附修正建议

**不做的事**：
- 不检查 subagent 之间的内部一致性（那是 5f 主 agent 的活）
- 不生成新的分析内容
- 不修改 subagent 产出

此 subagent 的指令直接写在 Phase 5e 中，不需要独立的 `task-N.md` 文件——它不是 per-category 的，职责固定。

---

**5f — Main agent 审阅 + 修正循环（硬上限 3 轮）**

Main agent 审阅 fact-check subagent 的核查报告：

**若 ❌ + 🔶 数量较少**（10 条以内且无重大事实错误）→ 直接进入 5g，主 agent 按核查报告修正报告。

**若 ❌ + 🔶 较多或存在重大事实错误** → 将具体问题发回对应的 task-subagent，要求重新核查修正。修正后：
1. 回到 5d 重新拼接修正后的产出
2. 回到 5e fact-check subagent 重新审查（可只审修正部分）
3. 回到 5f 主 agent 再次评估

**硬上限：3 轮**（5e→5f→修正→5e→5f→修正→5e→5f→5g）。超过 3 轮后接受剩余问题，在报告末尾标注 "第 N 轮核查，剩余 X 条未解决"。

---

**5g — Main agent 最终修正与写入**

Main agent 根据事实核查结果对组装报告做最终修正：
1. 按 fact-check 报告中 ✅ 确认的保持原样
2. 按 ❌ 和 🔶 逐条修正（使用 fact-check subagent 提供的正确信息）
3. ⚠️ 不可验证项 → 在报告中标注 "[来源：subagent 推断，原文未直接涉及]" 或直接移除
4. 内部一致性检查：(a) 矛盾检查——同一数字/事实在不同 section 中是否有不同表述；(b) 重叠检查——同一内容是否被多个 task 重复覆盖，如有则去冗余（保留最完整处，其余删除或引用）；(c) 交叉引用检查——一个 section 提到的关键内容在另一个 section 是否被遗漏或矛盾
5. 写入最终版 `outputs/deep-reader/{arxiv_id}/report.md`

此流程确保报告的**事实准确性由原文锚定**，而非依赖 LLM 记忆。

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
