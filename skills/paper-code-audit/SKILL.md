---
name: paper-code-audit
description: Perform three-way cross-validation of a research paper by comparing the original paper text (via Zotero), official code implementation (via Git), and personal Obsidian notes. Use this skill whenever the user wants to "audit a paper", "verify paper claims against code", "cross-check notes with implementation", "triangulate paper + code + notes", "find discrepancies between paper and code", or mentions wanting a deep, structured comparison of a paper's claims against its implementation and their own notes. Also trigger when the user asks to "analyze this paper thoroughly" with code available, or when they want to systematically reconcile what the paper says, what the code does, and what their notes claim.
---

# Paper-Code-Audit: 论文-代码-笔记三方交叉验证

对一篇研究论文进行系统性三方对比：**论文原文**（Zotero 全文 + annotations）→ **官方代码**（Git clone 到本地精读）→ **个人笔记**（Obsidian 已有笔记），找出所有偏差并输出结构化分析报告到 Obsidian。

## 前置依赖

此 skill 需要以下 MCP 工具可用：
- `mcp__zotero-mcp__*` — Zotero 文献库访问（搜索、全文提取、annotations）
- `mcp__obsidian__*` — Obsidian vault 笔记读写
- Git CLI — 克隆代码仓库
- Bash/Python — 辅助文本提取

## 工作流总览

```
Phase 1: Source Acquisition
  ├── Zotero: search by title → get full text + annotations
  ├── Obsidian: search by paper title/keywords → read existing notes
  └── Git: clone repo to reference/<repo-name>/

Phase 2: Deep Reading
  ├── Read all source files in the repo
  ├── Read config files and hyperparameters
  ├── Read paper full text (algorithms, equations, implementation details)
  └── Read Obsidian notes in full

Phase 3: Cross-Comparison (see detailed checklist below)

Phase 4: Documentation
  ├── Write discrepancy note to Obsidian (same dir as existing notes)
  └── Update relevant MOC(s) with link to new note
```

---

## Phase 1: Source Acquisition

### 1.1 Zotero — 获取论文原文

通过论文标题在 Zotero 中搜索：

```
mcp__zotero-mcp__search_library(title="<exact paper title>", includeAttachments="true")
```

获取到 item key 后，并行拉取三个信息源：
- **全文**: `mcp__zotero-mcp__get_content(itemKey="<key>", mode="complete", format="text")`
- **摘要**: `mcp__zotero-mcp__get_item_abstract(itemKey="<key>")`
- **Annotations**: `mcp__zotero-mcp__get_annotations(itemKey="<key>")`

Zotero 连接可能不稳定。若 `get_content` 返回 socket closed，先尝试 `fulltext_database(action="get", itemKeys=["<key>"])` 从缓存读取。若仍失败，降级使用 abstract + annotations。

全文文本量大时（>25K tokens），用 Python 脚本按关键词分段提取：
```bash
python3 -c "
import json
with open('<cached-fulltext.json>', encoding='utf-8') as f:
    text = json.load(f)[0]['text']
# Extract sections around keywords
for kw in ['Algorithm', 'loss', 'hyperparam', 'Implementation', 'horizon']:
    idx = text.lower().find(kw.lower())
    if idx >= 0:
        print(text[max(0,idx-80):idx+800])
        print('---')
"
```

### 1.2 Obsidian — 获取已有笔记

```
mcp__obsidian__search_notes(query="<paper title keywords>", limit=5, searchContent=true)
```

找到笔记路径后读取全文：
```
mcp__obsidian__read_note(path="<note-path>")
```

若笔记关联了 MOC（通过 `search_notes` 结果的 excerpt 或 MOC 文件名判断），记录 MOC 路径供后续更新。

### 1.3 Git — 克隆代码仓库

从论文中获取 GitHub URL（通常在 abstract 末尾或 footnote 中），Clone 到 reference 目录：

```bash
mkdir -p D:/Projects/reference && cd D:/Projects/reference && git clone <repo-url> <repo-name>
```

若论文未直接提供 URL，从 Zotero notes/comments 中搜索（annotations 中常见 `Code: https://github.com/...`）。

---

## Phase 2: Deep Reading

### 2.1 代码精读

按以下优先级读取所有源文件：
1. **入口文件**: `train.py`, `main.py`, `run.py`
2. **核心算法**: `algorithm/<name>.py`, `agent.py`, `model.py`
3. **网络/工具**: `helper.py`, `utils.py`, `networks.py`
4. **配置文件**: `config.yaml`, `cfgs/default.yaml`, `cfgs/**/*.yaml`
5. **环境接口**: `env.py`, `environment.py`

### 2.2 论文精读

重点关注以下章节：
- **Algorithm 伪代码** (Algorithm 1/2/3)
- **Implementation details** 段落
- **Loss functions / Objectives** 公式
- **Hyperparameters** 表格或段落
- **Architecture** 描述（encoder/decoder/network layers）

### 2.3 笔记精读

完整阅读 Obsidian 笔记，提取：
- 对算法原理的解读
- 对超参数的记录
- 对架构的描述
- 对训练流程的说明
- 既往的批判性分析

---

## Phase 3: Cross-Comparison Checklist

按此清单逐项对比，每项标注 **一致 / 偏差 / 代码未实现 / 笔记有误**：

### Architecture
| # | 检查项 | 论文 | 代码 | 笔记 |
|---|--------|------|------|------|
| A1 | Encoder 结构 (layers, dims, activations) | | | |
| A2 | Dynamics/Transition model | | | |
| A3 | Reward predictor | | | |
| A4 | Value/Critic network(s) | | | |
| A5 | Policy/Actor network | | | |
| A6 | Target network 更新机制 | | | |

### Hyperparameters
| # | 检查项 | 论文值 | 代码值 | 笔记值 |
|---|--------|--------|--------|--------|
| H1 | Learning rate | | | |
| H2 | Batch size | | | |
| H3 | Discount factor γ | | | |
| H4 | Planning/rollout horizon | | | |
| H5 | Loss coefficients | | | |
| H6 | Network dimensions | | | |
| H7 | EMA τ / update frequency | | | |
| H8 | Exploration parameters | | | |
| H9 | Gradient clip norm | | | |

### Loss Functions
| # | 检查项 | 论文公式 | 代码实现 | 笔记描述 |
|---|--------|---------|---------|---------|
| L1 | Reward loss 形式 | | | |
| L2 | Value/TD loss 形式 | | | |
| L3 | Consistency/regularization loss | | | |
| L4 | Policy/Actor loss | | | |
| L5 | 额外 loss terms | | | |

### Algorithm Flow
| # | 检查项 | 论文 | 代码 | 笔记 |
|---|--------|------|------|------|
| F1 | Planning 流程 (采样→rollout→打分→更新) | | | |
| F2 | Training 流程 (采样→encode→unroll→loss→backprop) | | | |
| F3 | 数据流 (buffer 采样方式、序列长度) | | | |
| F4 | Exploration 策略 | | | |
| F5 | Warm-start / momentum 细节 | | | |

### Engineering Details
| # | 检查项 | 代码实际 | 笔记是否覆盖 |
|---|--------|---------|-------------|
| E1 | Loss clamping / gradient protection | | |
| E2 | Device placement (GPU/CPU buffer) | | |
| E3 | Frame stacking / preprocessing | | |
| E4 | Action repeat / episode length 计算 | | |
| E5 | Per-task config overrides | | |

---

## Phase 4: Documentation

### 4.1 编写偏差分析笔记

在 Obsidian 中已有笔记的同目录下创建新笔记，命名格式：`<PaperName> Code vs Note 偏差分析.md`

**报告结构：**
```markdown
# <PaperName> Code vs Note 偏差分析

对比对象：
- **论文**: <citation>
- **官方代码**: <repo-url> (reference/<repo-name>/)
- **已有笔记**: [[<existing-note>]]

总体结论：<一句话总结一致性>

---

## 1. <偏差类别 1>

**笔记说法**：...
**代码实际**：...
**结论**：...

---

## 2. <偏差类别 2>
...

---

## 总结

| 偏差类型 | 严重程度 | 说明 |
|----------|---------|------|
| ... | 高/中/低 | ... |
```

严重程度判断标准：
- **高**: 笔记对算法的核心理解有误，影响对方法本质的把握
- **中**: 概念层面混淆或重要工程细节遗漏
- **低**: 数值精确度差异、off-by-one、注释级细节

### 4.2 更新 MOC

在相关 MOC 中将新笔记添加为已有论文笔记的子链接：

```
mcp__obsidian__patch_note(
    path="<MOC-path>",
    oldString="- [[<existing-note>]] <原有描述>",
    newString="- [[<existing-note>]] <原有描述>\n\t- [[<new-note>]] 代码、论文、笔记的三方对比与偏差记录"
)
```

若原笔记隶属多个 MOC，选择最相关的（通常是与论文领域直接对应的 MOC 章节）。

---

## 容错与降级策略

| 场景 | 处理方式 |
|------|---------|
| Zotero 全文获取失败 | 使用 abstract + annotations + fulltext_database cache |
| 论文无公开代码 | 跳过 Phase 2.1 代码部分，仅做论文 vs 笔记对比，报告中注明 |
| Obsidian 无相关笔记 | 跳过笔记对比，仅做论文 vs 代码对比 |
| Git clone 失败 (SSH/网络) | 尝试 https URL 替代 git@ URL |
| 代码语言非 Python | 仍按 Phase 2 流程推进，可能需关注不同文件约定 |
| MOC 结构不明确 | 将新笔记放在原笔记同目录，用户手动链接 |

---

## 注意事项

- Phase 3 的 checklist 是**最小检查集**——根据论文具体内容扩展（如多任务/多模态论文需额外检查 task embedding、action masking 等）
- 偏差分析笔记应保持**客观、精确**：每条偏差引用具体的文件路径和行号
- 如果三方完全一致（罕见但可能），仍然输出笔记，确认"无偏差"，这对学术记录同样有价值
- Zotero 全文提取可能因 PDF 格式而异（公式可能显示为乱码），此时以代码和笔记为主进行交叉验证
