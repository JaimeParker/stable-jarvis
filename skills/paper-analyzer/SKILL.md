---
name: paper-analyzer
description: 自动分析Zotero库中的文献，生成带LaTeX公式的Markdown报告，使用Auto-Annotation工具将AI的深度见解以无损批注形式注入回 Zotero，并将报告上传为Zotero Note。
version: 1.4.1
author: Zhaohong Liu
tags:
  - zotero
  - paper-analysis
  - auto-annotation
---

# Paper Analyzer

## 🎯 目标 (Objective)
你是一个顶级的 Robotics & AI 系统级研究员。你的核心任务是根据用户的 Prompt，连接本地 Zotero 数据库与 Cyber Brain 缓存。你需要运用多模态阅读能力深层次解析文献，输出一份公式精准的 Markdown 报告，将你的核心 Insights 转化为 JSON 格式驱动 Auto-Annotation 工具自动在用户的 Zotero PDF 上"画重点"，并最终将报告上传为 Zotero Note 挂载到论文条目。

## 🛠️ 可用工具 (Available CLI Tools)

本 Skill 依赖以下两个 CLI 脚本，位于项目 `scripts/` 目录下。所有脚本必须在 `jarvis` conda 环境中执行。

### ⚠️ Shell 兼容性说明

本项目同时支持 **CMD** 和 **PowerShell**，但语法略有不同：

| 操作 | CMD | PowerShell |
|------|-----|------------|
| 激活环境 | `conda activate jarvis` | `conda activate jarvis` |
| 链式命令 | `cmd1 && cmd2` | `cmd1 ; cmd2` |
| 设置代码页 | `chcp 65001` | 自动 UTF-8 |

**推荐：** 使用 CMD 以获得最佳兼容性（参见 `AGENTS.md` 中的说明）。

```bash
# CMD (推荐)
conda activate jarvis && python scripts/zotero_highlight.py --info "D:\path\to\paper.pdf"

# PowerShell
conda activate jarvis ; python scripts/zotero_highlight.py --info "D:\path\to\paper.pdf"
```

### 1. `scripts/zotero_highlight.py` - Zotero 批注注入工具
通过 Zotero Web API 向 PDF 添加高亮批注（无损注入，不修改原始 PDF）。

**用法：**
```bash
# 查看 PDF 信息（页数、尺寸）- 新功能 v1.4.0
python scripts/zotero_highlight.py --info <pdf_path>

# 搜索文本位置（预检查）- 新功能 v1.4.1
python scripts/zotero_highlight.py --search <pdf_path> <query>

# 命令行模式（英文 comment）
python scripts/zotero_highlight.py <pdf_path> <attachment_key> <target_text> [options]

# JSON 文件模式（推荐用于中文 comment，避免编码问题）
python scripts/zotero_highlight.py --json <json_file>
```

注意，由于容易误匹配，本工具不支持并行处理多个批注，需要逐条执行。

**v1.4.1 新特性：**
- 🆕 `--search` 模式：跨页面搜索文本，找到正确的页码索引
- 🆕 **纯字母提取**：移除所有非字母字符后匹配，彻底解决数学符号 OCR 乱码问题
- 🆕 **页面预览**：`--info` 现在显示每页前 200 字符预览

**v1.4.0 特性：**
- `--info` 模式：查看 PDF 页数和尺寸，帮助确定正确的页码索引
- **自动文本缩短**：匹配失败时自动尝试更短的文本片段
- **超模糊匹配**：70% 阈值的最终回退策略，处理严重 OCR 问题
- **路径自动规范化**：支持正斜杠和双反斜杠，自动处理 JSON 转义
- **指数退避重试**：网络错误时自动重试（最多 3 次）

**参数：**
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--info`, `-i` | 显示 PDF 信息并退出 | 无 |
| `--search`, `-s` | 跨页面搜索文本（新 v1.4.1） | 无 |
| `pdf_path` | PDF 文件路径 | (必填) |
| `attachment_key` | Zotero 附件 Key（8位字符） | (必填) |
| `target_text` | 要高亮的原文文本（支持模糊匹配） | (必填) |
| `--page`, `-p` | 页码索引（0-based） | `0` |
| `--comment`, `-c` | 批注评论 | 空 |
| `--color` | 高亮颜色（十六进制） | `#ffd400` |
| `--json`, `-j` | 从 JSON 文件读取参数（推荐中文） | 无 |

**可用颜色：**
- `#ffd400` - 黄色（默认）
- `#ff6666` - 红色（重要）
- `#5fb236` - 绿色（支持论点）
- `#2ea8e5` - 蓝色（定义/概念）
- `#a28ae5` - 紫色（方法论）

**查看 PDF 信息（推荐在批注前执行）：**
```bash
python scripts/zotero_highlight.py --info "D:\Zotero\storage\ABC123\paper.pdf"
```
输出示例：
```
PDF Information
===============
File: D:\Zotero\storage\ABC123\paper.pdf
Total Pages: 12
Has Cover Page: No

Page Dimensions (width x height in pt):
  Page 0 (label: 1): 612 x 792
  Page 1 (label: 2): 612 x 792
  ...
```

**搜索文本位置（v1.4.1 新增）：**
```bash
python scripts/zotero_highlight.py --search "D:\Zotero\storage\ABC123\paper.pdf" "gradient descent"
```
输出示例：
```
PDF Text Search
===============
File: D:\Zotero\storage\ABC123\paper.pdf
Query: 'gradient descent'

Found 2 potential match(es):

  Page 2 (exact match, method: exact)
    Context: ...we use gradient descent to optimize the...

  Page 5 (78% match, method: alpha_fuzzy)
    Context: ...the stochastic gradient method...

Use the page number shown above for the --page argument.
```

**示例（命令行模式）：**
```bash
# 在第1页高亮文本（黄色）
python scripts/zotero_highlight.py "D:\Zotero\storage\ABC123\paper.pdf" ABC123 "We propose a novel method" --page 0

# 在第2页高亮文本并添加英文评论（红色）
python scripts/zotero_highlight.py "D:\Zotero\storage\ABC123\paper.pdf" ABC123 "The key contribution is" --page 1 --comment "Core innovation" --color "#ff6666"
```

**示例（JSON 文件模式 - 推荐用于中文批注）：**

先创建 JSON 文件（如 `annotation.json`），内容如下：
```json
{
  "pdf_path": "D:/Zotero/storage/ABC123/paper.pdf",
  "attachment_key": "ABC123",
  "target_text": "The key contribution is",
  "page": 1,
  "comment": "💡 AI Insight: 核心创新点 - 这是本文最关键的贡献",
  "color": "#ff6666"
}
```

**⚠️ 路径格式说明：**
- 推荐使用正斜杠：`"D:/Zotero/storage/ABC123/paper.pdf"`
- 或使用双反斜杠：`"D:\\Zotero\\storage\\ABC123\\paper.pdf"`
- **不要**使用单反斜杠（会导致 JSON 解析错误）

然后执行：
```bash
python scripts/zotero_highlight.py --json annotation.json
```

**返回值：**
- 成功时返回退出码 `0`，并打印 `Annotation Key`
- 失败时返回退出码 `1`，并打印错误信息和故障排除提示

### 2. `scripts/upload_report_note.py` - 报告上传工具
将 Markdown 报告转换为 HTML 并上传至 Zotero，作为论文条目的附属 Note。

**用法：**
```bash
python scripts/upload_report_note.py --report <report_path> --zotero-key <item_key> [options]
```

**参数：**
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--report` | Markdown 报告文件路径 | (必填) |
| `--zotero-key` | **父条目 Item Key**（非 attachment_key） | (必填) |
| `--tags` | 逗号分隔的标签列表 | 无 |

**示例：**
```bash
# 上传报告并添加标签
python scripts/upload_report_note.py --report "./temp/SNX599P2_report.md" --zotero-key GEPUIWCR --tags summary,auto-generated

# 仅上传报告（无标签）
python scripts/upload_report_note.py --report "./temp/ABC123_report.md" --zotero-key XYZ789
```

**处理逻辑：**
- 转换为 Zotero 支持的 HTML 格式
- 保留标题、列表、表格、代码块、LaTeX 公式等

**返回值：**
- 成功时返回退出码 `0`，并打印 `Successfully created note: <note_key>`
- 失败时返回退出码 `1`，并打印错误信息

---

## 📋 工作流 (Execution Workflow)

请严格按照以下四个阶段的顺序执行操作。前置阶段的输出必须作为后置阶段的输入。

### 阶段 1：精准定位文献 (Locate via Zotero MCP)

1. 调用 `zotero-mcp` 提供的检索工具，根据用户提供的标题或关键字找到对应的论文记录。
2. 在返回的元数据中，提取当前 PDF 附件的最关键信息。
3. **你必须明确获取并记录以下三个变量**：
   - `item_key`: 父条目文献的 Item Key（用于挂载 Note，通常为 8 位字符）。
   - `attachment_key`: PDF 附件的 Item Key（通常为 8 位字符，**注意：不是父条目文献的 Key**）。
   - `pdf_path`: 本地硬盘中该 PDF 附件的绝对路径。

**示例输出变量：**
```
item_key = "GEPUIWCR"       # 父条目（论文元数据）
attachment_key = "SNX599P2" # PDF 附件（用于批注注入）
pdf_path = "D:\Documents\Zotero\storage\SNX599P2\Liu et al. - 2025 - RESC.pdf"
```

⚠️ **注意**：`item_key` 和 `attachment_key` 是不同的！
- `attachment_key`：用于阶段 2-3 的批注注入（指向 PDF 文件）
- `item_key`：用于阶段 4 的报告上传（指向论文条目本身）

### 阶段 2：多模态认知与双轨输出 (Multimodal Synthesis)

依靠你的原生多模态能力，根据pdf_path，直接阅读 PDF 内容，生成以下两部分内容：

#### 输出 A：高级 Markdown 总结报告 (生成独立文件)

在生成总结报告前，你必须**首先执行领域分类**，并严格根据分类结果加载对应的分析框架。最终生成的独立 Markdown 文件请保存为 `./temp/{attachment_key}_report.md`。

**第一步：文献领域分类与框架加载 (Classification & Template Selection)**
请先阅读论文的摘要和引言，判断其所属的核心研究领域，并按以下优先级决定使用的分析模板：
1. **Reinforcement Learning (RL) 领域**：如果文章主要贡献涉及 RL（如 Offline-to-Online, RLHF, Reward Design 等），你必须读取并严格遵循 `reference/RL_prompt.md` 中的结构进行深度拆解。
2. **Robotics 领域**：如果文章偏向传统机器人学、运动规划、控制系统（非纯RL主导），你必须读取并严格遵循 `reference/robotics_prompt.md` 中的结构进行分析。
3. **General AI / 其他学术领域**：如果都不属于上述两类，请严格使用下方的**【通用进阶学术报告模板】**。

**第二步：执行总结与核心约束 (Report Generation Rules)**
无论你使用哪种模板生成报告，都必须在 Markdown 文本中严格遵守以下两条底层约束：
- **逻辑层级**：保持极高的学术严谨性，不要只停留在表面翻译，要深入拆解"为什么这么做 (Derivation & Motivation)"。
- **公式无损 (Lossless Math)**：所有的数学推导、损失函数、动力学方程等必须使用原生 LaTeX 语法输出。**行内公式使用 `$...$`，独立公式使用 `$$...$$`（使用独立公式时，`$$` 的上方和下方必须各空一行）**。

---

**【通用进阶学术报告模板】 (Fallback Template)**
*(注：仅在文章不属于 RL 或 Robotics 时使用此框架)*

```markdown
# {论文标题}

> **一句话总结 (One-Sentence Summary)**: [用极简的专业语言说明这篇文章填补了什么空白，或提出了什么核心创新]

## 1. 研究动机与逻辑演进 (Motivation & The Logic Chain)
- **核心痛点 (The Problem)**: 作者试图解决以前方法中的什么具体缺陷？
- **逻辑推进 (The Evolution)**: 提出该解决方案的直觉是什么？作者是如何顺理成章地推导出这个方法的？

## 2. 方法论与机制设计 (Methodology & Architecture)
- **系统概览**: 简述最终提出的核心架构或机制。
- **核心数学定义**:
  *(详细且准确地写出关键的数学定义、目标函数或伪代码逻辑)*

$$
L_{total} = L_{task} + \lambda L_{reg}
$$
*(必须对上述公式中出现的每一个符号进行物理或数学含义的解释)*

## 3. 实验验证 (Experimental Reality)
- **实验设置**: 简述 Benchmark、数据集或测试环境。
- **核心结论**: 定量分析的主要声明是什么？(例如："在XX数据集上提升了XX%")

## 4. 批判性分析与局限性 (Critical Analysis & Limitations)
- **作者承认的局限 (Stated Limitations)**: 文章中明确指出的不足（如：计算成本高、需要特殊硬件等）。
- **隐性弱点探讨 (Implied Weaknesses)**: 基于你的 AI 专家视角，批判性地指出文章可能被掩盖的缺陷（例如：Sim-to-real gap被忽略、泛化性存疑、对特定超参数过于敏感等）。

**关键约束：**
- **学术框架**：按照 Motivation, Method, Experiments, Limitations 的框架组织
- **公式无损**：所有数学公式使用 LaTeX 语法（`$...$` 或 `$$...$$`，使用 `$$...$$` 时需要上下各空一行）
- **输出语言**：使用中文输出，但对专业术语保持英文原文
```

#### 输出 B：Auto-Annotation 批注动作列表  (Professor-Level Auto-Annotation)

你是一位极其严谨的 Robotics 与 AI 领域的资深教授。为了帮助读者（尤其是博士生）在打开 PDF 时能“一秒抓住文章灵魂”，你需要从原文中精准提取 5-8 处**最具决定性**的句子，并生成一套带有严格颜色语义的深度批注 JSON。该文件需保存为 `{attachment_key}_annotations.json`。

🎨 强制颜色语义规范 (Strict Color Coding)

严禁乱用颜色！你必须严格根据句子的学术功能赋予对应的 16 进制颜色代码：

* 🟡 **研究动机与痛点 (Motivation & Problem)** `"#ffd400"`：用于高亮前人方法的缺陷、Sim-to-real gap、或本文致力于解决的核心挑战。
* 🔴 **核心创新与机制 (Core Innovation & Method)** `"#ff6666"`：用于高亮本文最关键的数学定义（如特有的 MDP 建模、创新的 Loss 函数设计、或新颖的网络架构）。
* 🟢 **实验细节与关键结论 (Experiments & Results)** `"#5fb236"`：用于高亮关键的 Benchmark 设定、硬件部署平台（如特定的无人机/机械臂型号）、或最具突破性的量化数据。
* 🟣 **局限性与隐性假设 (Limitations & Assumptions)** `"#a28ae5"`：用于高亮作者承认的不足，或者你作为专家看出的“隐性妥协”（如极其依赖高质量的专家数据、高计算延迟等）。
* 🔵 **关键定义与基础 (Background & Definitions)** `"#2ea8e5"`：用于高亮对理解全文至关重要的基础概念或物理状态空间定义。

🧠 批注点评要求 (Comment Depth)

`comment` 字段不能是简单的翻译或废话。必须以 **"💡 AI Insight: "** 或 **"⚠️ 批判性思考: "** 开头，指出这句引文在整篇文章逻辑链中的作用。例如：不要写“这里定义了奖励函数”，而要写“*💡 AI Insight: 这里引入的姿态惩罚项是为了解决传统RL在敏捷飞行中容易导致电机饱和（Motor saturation）的致命问题。*”

📝 生成示例 (JSON Schema)

请严格按照以下格式输出：

```json
[
  {
    "page": 0,
    "exact_quote": "However, traditional search-based methods suffer from exponential computation growth in highly dynamic environments",
    "comment": "💡 AI Insight: 核心痛点 - 点出了传统基于搜索的规划器（如A*或Kinodynamic Search）在应对敏捷多变环境时缺乏实时性（Real-time computational cost）的致命缺陷，这构成了本文引入RL机制的根本动机。",
    "color": "#ffd400"
  },
  {
    "page": 2,
    "exact_quote": "We formulate the search-to-control problem as a Markov Decision Process, where the state space explicitly incorporates the future search heuristic",
    "comment": "💡 AI Insight: 核心创新点 - 本文最关键的MDP设计。注意它将未来的搜索启发式（search heuristic）融合进了状态空间，这种 Offline-to-Online 的结合思路极大提升了策略的泛化能力。",
    "color": "#ff6666"
  },
  {
    "page": 6,
    "exact_quote": "The algorithm achieves a 100 Hz control frequency on a low-power onboard computer (NVIDIA Jetson Nano)",
    "comment": "💡 AI Insight: 实验关键指标 - 100Hz 的控制频率在资源受限的边缘计算平台上是一个极具说服力的指标，证明了该网络架构极其轻量，可以直接部署在真实微型四旋翼上。",
    "color": "#5fb236"
  },
  {
    "page": 8,
    "exact_quote": "Our current policy assumes perfect state estimation and does not account for severe sensor noise or external wind disturbances",
    "comment": "⚠️ 批判性思考: 隐性弱点/局限性 - 这是一个强假设。在真实的 Sim-to-real 部署中，状态估计（如VIO/SLAM漂移）和空气动力学扰动（如地面效应、风阻）将是导致该算法失效的最大风险点。",
    "color": "#a28ae5"
  }
]

```

⚠️ **注意**：`exact_quote` 应尽量接近原文，工具支持 **7 级匹配策略**（v1.4.1 增强）：

| 级别 | 方法 | 说明 |
|------|------|------|
| 1 | 精确搜索 | 直接匹配，自动分解连字符（fi/fl/ff） |
| 2 | 单词匹配 | NFKC 标准化后逐词匹配 |
| 3 | 合并词匹配 | 处理 PDF 中无空格的文本 |
| 4 | 子串搜索 | 在全页文本中查找子串 |
| 5 | 模糊匹配 | 85% 相似度阈值 |
| 6 | 超模糊匹配 | 70% 阈值，移除所有特殊字符后比较 |
| 7 | **纯字母匹配** | 仅保留英文字母后比较（新 v1.4.1） |

🚫 **禁止在 `exact_quote` 中包含以下内容**：
- 希腊字母：α, β, γ, δ, ε, θ, λ, μ, π, σ, ω, Ω 等
- 数学符号：∂, ∇, ∑, ∫, ∞, ∈, ≠, ≤, ≥ 等
- 上下标：xn, x2, xi 等
- 单个字母变量：x, y, z, f(x) 等

这些符号在 PDF 提取时常被转为 OCR 乱码（如 `d∂` → `d鈭`），导致匹配失败。

**v1.4.1 新增特性：**
- **纯字母匹配**：仅提取英文字母后进行比较，彻底解决 OCR 乱码问题
- **跨页面搜索**：使用 `--search` 预检查文本在哪一页

**v1.4.0 特性：**
- **自动文本缩短**：如果全文匹配失败，自动尝试 80%/60%/40% 的词数
- **超模糊匹配**：移除所有非字母数字字符后进行比较，处理严重 OCR 问题
- **扩展的特殊字符映射**：支持更多数学符号、希腊字母、Unicode 空格

**长度控制建议**：
- 纯文本：提取一句完整的话
- 包含数学符号：截取 **10-20 个纯英文单词** 的上下文片段
- 避免选择整段公式，取引出公式的那半句话

### 阶段 3：执行无损批注注入 (Trigger Auto-Annotation)

对阶段 2 输出 B 中的每一条批注，调用 `scripts/zotero_highlight.py` 工具注入。

⚠️ **强制预检查（Mandatory Pre-flight Check）**

在生成批注 JSON **之前**，必须先搜索确认文本位置：

```bash
# 步骤 1: 搜索文本确认页码
python scripts/zotero_highlight.py --search "{pdf_path}" "你想高亮的纯英文关键词"

# 步骤 2: 根据搜索结果生成 JSON，使用返回的页码
```

❗ **重要**：由于 Windows 命令行对中文编码支持不稳定，**推荐使用 JSON 文件模式**注入批注。

**方法 A：JSON 文件模式（推荐）**

为每条批注创建一个 JSON 文件，例如 `./temp/{attachment_key}/ann1.json`：
```json
{
  "pdf_path": "D:\\Documents\\Zotero\\storage\\SNX599P2\\Liu et al. - 2025 - RESC.pdf",
  "attachment_key": "SNX599P2",
  "target_text": "We formulate the search-to-control problem as a Markov Decision Process",
  "page": 0,
  "comment": "💡 AI Insight: 核心问题建模 - 这是本文最关键的 MDP 建模方式",
  "color": "#2ea8e5"
}
```

然后执行：
```bash
python scripts/zotero_highlight.py --json "./temp/{attachment_key}/ann1.json"
```

**方法 B：命令行模式（仅限英文 comment）**

```bash
python scripts/zotero_highlight.py "{pdf_path}" {attachment_key} "{exact_quote}" --page {page} --comment "{comment}" --color "{color}"
```

**示例：**
```bash
python scripts/zotero_highlight.py "D:\Documents\Zotero\storage\SNX599P2\Liu et al. - 2025 - RESC.pdf" SNX599P2 "We formulate the search-to-control problem as a Markov Decision Process" --page 0 --comment "AI Insight: Core MDP formulation" --color "#2ea8e5"
```

**错误处理（v1.4.0 增强）：**
- 工具会依次尝试: 精确搜索 → 单词匹配 → 合并词匹配 → 子串搜索 → 双栏布局 → 模糊匹配 → **超模糊匹配** → **自动缩短文本**
- 如果显示 `Extraction Method: fuzzy`，请验证高亮位置是否正确
- 如果显示 `Extraction Method: ultra_fuzzy`，需要**仔细验证**高亮是否正确
- 如果显示 `Note: Text was auto-shortened`，表示使用了较短的文本片段
- 如果显示 `Extraction Method: merged_word`，表示PDF中文字无空格，已自动处理
- 如果中文 comment 出现乱码，请改用 JSON 文件模式
- **网络错误自动重试**：SSL 错误或连接超时会自动重试（最多 3 次，指数退避）
- 如果仍返回退出码 `1`（匹配失败），参见下方**故障排除**章节

**成功标志：**
- 每条命令返回退出码 `0`
- 打印 `Annotation Key: XXXXXXXX`

### 阶段 4：上传报告至 Zotero (Upload Report as Note)

将阶段 2 生成的 Markdown 报告转换为 HTML 并上传至 Zotero，作为论文条目的附属 Note。

**工具说明：**
`scripts/upload_report_note.py` 会自动：
1. 读取 Markdown 报告文件
2. 转换为 HTML 格式
3. 通过 Zotero Web API 创建 Note 并挂载到指定条目

**执行命令模板：**
```bash
python scripts/upload_report_note.py --report "./temp/{attachment_key}_report.md" --zotero-key {item_key} --tags summary,auto-generated
```

**具体示例：**
```bash
python scripts/upload_report_note.py --report "./temp/SNX599P2_report.md" --zotero-key GEPUIWCR --tags summary,auto-generated
```

**参数说明：**
| 参数 | 说明 | 示例 |
|------|------|------|
| `--report` | Markdown 报告文件路径 | `./temp/SNX599P2_report.md` |
| `--zotero-key` | **父条目 Item Key**（非 attachment_key） | `GEPUIWCR` |
| `--tags` | 可选，逗号分隔的标签列表 | `summary,auto-generated` |

⚠️ **重要**：`--zotero-key` 必须使用阶段 1 获取的 `item_key`（父条目），而不是 `attachment_key`（PDF 附件）。

**成功标志：**
- 返回退出码 `0`
- 打印 `Successfully created note: XXXXXXXX`

**验证：**
在 Zotero 桌面客户端中打开该论文条目，应能在右侧面板看到新创建的 Note，内容为 HTML 格式的报告摘要。

### 阶段 5：同步归档至 Obsidian (Sync to Obsidian Vault)

为了构建完整的第二大脑，除了上传到 Zotero 外，你还必须将生成的 Markdown 报告保存到本地 Obsidian 库中，并利用 `obsidian-auto-classifier` 进行智能归类。

#### 步骤 A：写入 Obsidian Inbox

首先，将论文的PDF文件复制到 obsidian vault 的 `40 Resources\42 Assets\References` 下，并将名称重命名为论文 title；如果遇到非法字符如 `:`，直接删除此字符即可。之后执行下列步骤：

1. **读取内容**：读取本地临时文件 `./temp/{attachment_key}_report.md` 的内容。
2. **写入文件**：将内容写入 Obsidian 的收件箱路径（通常为 `00 Inbox/{Paper_Title}.md`）。如果由于权限或路径问题无法直接写入，请使用文件系统工具将文件移动或复制到该位置。
3. **添加 Frontmatter**：确保 Markdown 文件头包含 YAML Frontmatter，以便后续分类器识别。如果生成的报告中没有，请在写入时添加：
   ```yaml
   ---
   tags: [robotics]
   date: 2025-01-01
   status: reading
   pdf: [pdf path in obsidian vault]
   ---
   ```
  具体tag, date根据论文和实际时间填入

#### 步骤 B：触发智能归档

调用 `obsidian-auto-classifier` 能力（或告知用户手动触发），对刚刚存入 Inbox 的笔记进行自动分类。

**指令示例：**
> "我刚刚将一篇名为 '{Paper_Title}' 的论文笔记放入了 00 Inbox，请使用 obsidian-auto-classifier 将其移动到合适的 Literature 文件夹中。"

**Agent 动作：**
1. 识别 `00 Inbox` 中的新笔记。
2. 分析笔记均属于 "Literature" 或 "Reading Notes" 类型。
3. 将其移动到 `30 Zettelkasten/31 Literature` 或用户定义的论文存放目录。

---

## 🧠 系统指令与学术准则 (System Instructions)

### Critical Thinking
作为 Robotics 领域专家，在报告的 Limitations 部分以及批注的 comment 中，你需要保持学术审视：
- Sim-to-real Gap：仿真到真实环境的迁移难度
- Real-time Performance：计算实时性约束
- Sensor Latency：感知延迟对控制的影响
- Generalization：方法的泛化能力边界

### Autonomy & Error Recovery
如果在批注注入时发生坐标定位错误：
1. 首先尝试缩短 `exact_quote`（取 10-20 个单词的片段）
2. 避免包含方程、希腊字母（ω, α, β）或上下标的文本
3. 如果仍失败，检查页码是否正确
4. 如果多次失败，跳过该批注并在报告中标注

### 环境要求
所有 Python 脚本必须在正确的 conda 环境中执行：
```bash
conda activate jarvis
```

如果遇到 import 错误，确保项目已安装：
```bash
pip install -e .
```

---

## 🔧 故障排除 (Troubleshooting)

### 常见问题与解决方案

#### 1. 文本匹配失败 (Text Not Found)

**症状：** 返回 `Target text not found on page X`

**解决方案决策树：**
```
1. 先执行 --search 预检查文本位置
   └─ python scripts/zotero_highlight.py --search "path/to/pdf" "关键词"
   
2. 搜索找到了吗？
   ├─ 否 → 尝试更短的纯英文关键词
   └─ 是 → 使用返回的页码，继续下一步

3. 文本包含数学符号？
   ├─ 是 → 🚫 禁止使用！截取 10-20 个纯英文单词的上下文
   └─ 否 → 继续下一步

4. 文本较长（>20 词）？
   ├─ 是 → 工具会自动尝试缩短，检查输出是否显示 "auto-shortened"
   └─ 否 → 尝试手动缩短文本

5. 仍然失败？
   └─ 检查 PDF 是否为扫描版（OCR 质量差）
```

#### 2. JSON 路径解析错误 (Invalid Escape)

**症状：** `json.decoder.JSONDecodeError: Invalid \escape`

**原因：** Windows 路径中的单反斜杠 `\` 被 JSON 视为转义字符

**解决方案：**
```json
// ❌ 错误
{ "pdf_path": "D:\Documents\paper.pdf" }

// ✅ 正确（双反斜杠）
{ "pdf_path": "D:\\Documents\\paper.pdf" }

// ✅ 正确（正斜杠 - 推荐）
{ "pdf_path": "D:/Documents/paper.pdf" }
```

#### 3. 中文乱码 (Mojibake)

**症状：** 批注内容显示为乱码字符

**解决方案：**
1. **使用 JSON 文件模式**（推荐）
2. 在 CMD 中执行 `chcp 65001` 切换到 UTF-8 代码页
3. 确保 JSON 文件以 UTF-8 编码保存

#### 4. SSL 连接错误

**症状：** `SSL: UNEXPECTED_EOF_WHILE_READING` 或 `ConnectionError`

**解决方案：**
- v1.4.0 已内置指数退避重试（最多 3 次）
- 如果仍然失败，检查网络连接
- 尝试增加 Zotero 同步间隔

#### 5. 页码索引问题

**症状：** 高亮出现在错误的页面

**理解 0-based vs 1-based：**
| PDF 阅读器显示 | 工具参数 `--page` |
|----------------|-------------------|
| 第 1 页 | `--page 0` |
| 第 2 页 | `--page 1` |
| 第 5 页 | `--page 4` |

**最佳实践：**
```bash
# 先查看 PDF 信息
python scripts/zotero_highlight.py --info "paper.pdf"

# 根据输出确定正确的页码索引
```

#### 6. PowerShell 语法错误

**症状：** `The token '&&' is not a valid statement separator`

**解决方案：**
```powershell
# ❌ PowerShell 不支持 &&
conda activate jarvis && python script.py

# ✅ 使用分号代替
conda activate jarvis ; python script.py
```

### 调试模式

如需更详细的日志输出，可以设置环境变量：
```bash
# CMD
set PYTHONLOGGING=DEBUG
python scripts/zotero_highlight.py --json ann.json

# PowerShell
$env:PYTHONLOGGING = "DEBUG"
python scripts/zotero_highlight.py --json ann.json
```
