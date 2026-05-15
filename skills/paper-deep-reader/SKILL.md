---
name: paper-deep-reader
description: 精读：Zotero MCP → Obsidian 知识库 → 6-section 深度报告。支持分块摘要、KB横向对比、多LLM提供商、wikilinks输出。快速泛读请用paper-analyzer。
version: 1.0.0
author: Zhaohong Liu
tags:
  - zotero
  - obsidian
  - paper-analysis
  - deep-reading
---

# Paper Deep Reader（精读）

> **定位**：本 skill 实现深度论文精读——6 轮独立 LLM 调用分解分析 + Zotero/Obsidian 知识库横向对比 + Obsidian vault 结构化输出。如需快速泛读（单轮摘要），请使用 `paper-analyzer`。

## 核心能力

- **分块摘要压缩**：长论文超过阈值时自动分块，每块先 LLM 摘要再拼接，确保全貌不丢
- **6-section 分解分析**：每轮 LLM 独立调用，各有针对性 prompt，避免上下文挤压
- **知识库横向对比**：Zotero MCP `semantic_search` + Obsidian `search_notes` + 可选 embedding 语义搜索
- **多 LLM 提供商**：支持 anthropic / openai / deepseek / qwen
- **Obsidian 原生输出**：报告写入 vault，自动生成 `[[wikilinks]]` + frontmatter
- **缓存复用**：每轮 LLM 回答缓存，避免重复调用

## 配置

运行前确保：
- `zotero-mcp` 已启动
- `obsidian` MCP 已配置
- （可选）`research-helper` 已安装：`pip install -e 3rd_party/paperwise`
- （可选）embedding provider 已配置：`EMBEDDING_PROVIDER=qwen|openai|local`

---

## 工作流（6 阶段）

严格按以下阶段顺序执行。

---

### 阶段 1：定位论文

通过 Zotero MCP 定位论文并获取必要信息。

**步骤：**
1. 根据用户提供的标题/关键词/arxiv ID，调用 `zotero-mcp` 的 `search_library` 找到论文
2. 获取 `item_key`（父条目）、PDF attachment key
3. 调用 `get_item_details` 获取完整元数据（标题、作者、abstract、published date、arxiv ID）
4. 记录以下变量供后续阶段使用：
   - `item_key` — Zotero 父条目 key
   - `attachment_key` — PDF attachment key
   - `title` — 论文标题
   - `abstract` — 摘要
   - `authors` — 作者列表
   - `published` — 发表日期
   - `arxiv_id` — arXiv ID

---

### 阶段 2：提取全文

**判断策略**：
- 如果 PDF 页数估计 < 20 页：直接用 Claude 多模态能力读取 PDF 内容
- 如果 PDF 页数 >= 20 页或无法判断：运行提取脚本

**提取脚本**：
```bash
python scripts/extract_pdf_text.py --pdf <pdf_path> --output <output_path>.txt
```

**长论文分块摘要**：
当提取文本超过 24,000 字符时，按 12,000 字符分块（重叠 500），每块用 LLM 摘要成 400 字中文，拼接为后续 prompt 的 `{content}`。

分块摘要 prompt：
```
这是论文《{title}》的第 {i}/{total} 段，请提取方法、实验、结论等关键信息，输出 400 字以内的中文摘要：

{chunk}
```

---

### 阶段 3：构建 KB 上下文

替代 ChromaDB 的知识库上下文，三路合并：

**3a — Zotero 语义检索**
```bash
# 使用 Zotero MCP semantic_search
```
调用 `zotero-mcp` 的 `semantic_search`，query = `{title}\n{abstract}`，topK=10，minScore=0.3。
过滤掉当前论文（按 arxiv_id），保留 top-5。
格式化为 KBEntry：`{title, arxiv_id, text(abstract), published, source="zotero"}`。

**3b — Obsidian 内容搜索**
调用 `obsidian` MCP 的 `search_notes`，query = `{title}` 的前 50 个字符，limit=10。
读取匹配的笔记，提取其 wikilinks 和摘要内容。
格式化为 KBEntry：`{title(from note), arxiv_id(from frontmatter), text(first 600 chars), source="obsidian"}`。

**3c — Obsidian 语义搜索（可选）**
如果配置了 embedding provider：
```bash
python scripts/search_obsidian.py --embed "{title}\n{abstract}" --top-k 5
```
格式化为 KBEntry：`{title, arxiv_id, text, published, source="obsidian-embed"}`。

**合并去重**：
- 按 arxiv_id 去重（优先级：zotero > obsidian-embed > obsidian）
- 排除当前论文
- 取 top-5
- 构建 `kb_section` 字符串注入后续 prompt

---

### 阶段 4：6 轮深度分析

**前提**：读取 `reference/section-prompts.md` 获取完整的 6 个 section prompt 模板。

每轮分析是**独立的 LLM 调用**，共用同一个 system prompt 和 kb_section。

**System Prompt**：
```
你是一位资深 AI 研究员，正在为自己撰写论文精读笔记。
写作要求：
- 语言为学术中文，表达精确，不啰嗦
- 每个 section 至少 200 字，重要内容可更长
- 用具体数字、公式、方法名支撑论点，不写空话
- 遇到方法细节时，解释清楚其设计动机，不只是罗列
- 知识库中有相关论文时，做有实质内容的横向对比，指出异同
- 不引用知识库和论文原文之外未出现的论文
- 所有数学公式必须使用 Markdown 格式：行内公式用 $...$，独立公式用 $$...$$，不得使用 \( \) 或 \[ \]
```

**执行**：
对 `reference/section-prompts.md` 中的每个 section prompt，依次：
1. 用 `{title}`, `{content}`, `{kb_section}` 填充模板
2. 调用 LLM（使用 Claude 当前会话能力）
3. 保存回答
4. 将中间结果缓存到 `{output_dir}/analysis_cache.json`

**LLM 提供商切换**：
如果用户指定 `--provider deepseek`，使用 deepseek API 完成 6 轮调用（通过 Bash 调用 paperwise 的 paperwise CLI 或直接用 curl）。

---

### 阶段 5：写报告到 Obsidian

**报告模板**（参见 `reference/section-prompts.md` 中的 REPORT_TEMPLATE）。

**生成最终 Markdown**：
- 填充 6 个 section 的回答
- 生成 frontmatter（yaml）
- 添加 KB 相关论文的 `[[wikilinks]]`：
  - 对 KB 中找到的每篇论文，检查 Obsidian vault 中是否存在同名笔记
  - 若存在，添加 wikilink：`[[note_name]]`
  - 若不存在，仅用文本引用

**写入 Obsidian**：
使用 `obsidian` MCP 的 `write_note`，路径为 `00 Inbox/{safe_title}.md`。

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

### 阶段 6：可选上传 Zotero Note

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
| `LLM_PROVIDER` | 当前会话 | 6 轮分析的 LLM 提供商（默认用 Claude） |
| `CHUNK_SIZE` | `12000` | 分块大小（字符） |
| `CHUNK_OVERLAP` | `500` | 分块重叠（字符） |
| `OBSIDIAN_VAULT` | 自动检测 | Obsidian vault 根路径 |

---

## 与 paper-analyzer 对比

| 维度 | paper-analyzer（泛读） | paper-deep-reader（精读） |
|------|----------------------|--------------------------|
| LLM 调用 | 单轮 | 6 轮独立 |
| 长论文 | 上下文窗口截断 | 分块摘要压缩 |
| KB 对比 | 无 | Zotero + Obsidian + embedding |
| 输出 | Zotero Note | Obsidian vault（wikilinks + frontmatter） |
| 缓存 | 无 | analysis_cache.json |
| 适用场景 | 快速了解大意 | 深度理解、文献对比、知识积累 |
