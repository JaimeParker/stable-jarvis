# Stable-JARVIS-Dev

A JARVIS like assistant for researchers, using AI client, agents, skills, and MCP architecture.

## 开发计划

### 第一部分：基础设施重组 (Infrastructure Reassembly)

我们依然采用【组合式二次开发】，但在写入层进行彻底重构。你将需要以下组件来构建你的 Zotero-Scholar-MCP：

读取与检索层：

* 54yyyu/zotero-mcp：用于根据你的 Prompt（如“找到关于强化学习在四旋翼敏捷飞行中的应用文献”）检索并返回 Zotero Item ID 和 PDF 附件 ID（Attachment Key）。

内容剥离层 (Extract)：

* ultimatile/arxiv-skills：优先尝试拉取 LaTeX 源文件以获取完美的数学公式（对于 RL 和 Motion Planning 论文至关重要）。
* pymupdf4llm：作为 Fallback，将本地 PDF 高质量转为 Markdown，并提取论文中的结构图、控制框图到本地缓存（为报告生成图文混排做准备）。

坐标映射层 (Locate) ：

* pymupdf 原生 API（如 page.search_for("text")）：这是重构后的关键。它仅用于只读搜索，找出需要高亮的关键句子在 PDF 页面上的绝对坐标（Bounding Box, Bbox）。

无损注入层 (Inject) ：

* 深度定制 urschrei/pyzotero：通过 Zotero Web API，构造并发送符合 Zotero 规范的 annotation 和 note JSON 数据包。

### 第二部分：实施全景工作流 (The Restructured Master Plan)

当你在 Gemini-CLI 等终端输入命令让 Agent 分析一篇论文（例如你的 "RESC" 四旋翼控制框架论文）时，系统将执行以下自动化流：

阶段 1：文献降维与报告生成
* 定位与提取：Agent 锁定论文，提取出包含数学公式的 Markdown 文本以及缓存的本地图表（如轨迹对比图）。
* 深度推理：Agent 加载 AcademicForge 中的科研分析 Prompt（如 paper-miner.md），基于 Robotics 的视角对 Markdown 文本进行分析，生成一份包含本地图片链接的详细 Markdown 报告。

阶段 2：智能锚点提取 (Smart Anchoring)

* 为了实现“原生批注”，必须在提示词（System Prompt）中强制 Agent 输出一种特定的中间数据格式。Agent 在生成报告的同时，需要输出一个批注动作列表：

```json
[
  {
    "type": "highlight",
    "exact_quote": "We formulate the search-to-control problem as a Markov Decision Process...",
    "comment": "这里定义了MDP的状态空间，注意与传统优化的区别。",
    "color": "#ff6666" 
  },
  {
    "type": "note",
    "content": "## Core Contributions\n1. 提出了新的RL架构..."
  }
]
```

（强制要求 exact_quote 必须是原文中一字不差的句子，这是定位坐标的前提）。

阶段 3：无损批注映射引擎 (The Non-Destructive Annotation Engine)
这是系统的核心开发难点。Python 编排脚本接收到上述 JSON 后，在后台默默执行：

* 坐标捕获 (PyMuPDF)：
脚本利用 pymupdf 打开该 PDF：

```python
# 伪代码
bboxes = page.search_for("We formulate the search-to-control problem as a...")
# 返回该句子在页面上的矩形坐标 [x0, y0, x1, y1]
```
* 坐标系转换 [Original Knowledge]：将 PyMuPDF 的坐标转换为 Zotero API 接受的 annotationPosition 格式（通常是一个包含 pageIndex 和 rects 的字符串化 JSON）。
* API 注入：使用 pyzotero 构造 POST 请求。
* 对于全局笔记，创建一个 itemType: "note"，作为该论文的子条目。
* 对于高亮，创建一个 itemType: "annotation"，指定 parentItem 为 PDF 附件的 Key，带上转换好的坐标和 Agent 写的点评（Comment）。

### 最终体验（目标）：
完成上述过程后，你打开 Zotero。论文下多了一篇精美的全局 Note。双击打开 PDF，你会看到高亮不仅完美贴合在原文上，而且侧边栏里安静地躺着你的 AI Agent 对这一段公式或算法的深度点评。你完全可以使用 Zotero 自己的工具对其进行二次编辑，原 PDF 文件大小和哈希值没有任何改变。

## Installation

```bash
# Clone the repository
git clone https://github.com/JaimeParker/JARVIS-Dev.git
cd JARVIS-Dev

# Activate your conda environment
conda activate jarvis

# Install in editable mode
pip install -e .
```

## Configuration

Configure Zotero credentials using one of these methods (in priority order):

### Option 1: Environment Variables (recommended for CI/production)

```bash
export ZOTERO_LIBRARY_ID="your_library_id"
export ZOTERO_API_KEY="your_api_key"
export ZOTERO_LIBRARY_TYPE="user"  # optional, default: user
```

### Option 2: Config File

Create `zotero.json` in one of these locations (first found wins):
- `./zotero.json` (current directory)
- `./user_info/zotero.json` (relative to cwd)
- `~/.config/stable-jarvis-dev/zotero.json` (user config dir)

```json
{
    "library_id": "your_library_id",
    "api_key": "your_api_key",
    "library_type": "user"
}
```

## Quick Start

### Auto-Annotation Example

```python
from stable_jarvis_dev import annotate

result = annotate(
    pdf_path="path/to/paper.pdf",
    attachment_key="ABC12345",
    target_text="text to highlight",
    comment="My note",
)

if result.success:
    print(f"Created annotation: {result.annotation_key}")
```

Or use the class-based API:

```python
from stable_jarvis_dev import ZoteroAnnotator

annotator = ZoteroAnnotator()
result = annotator.highlight(
    pdf_path="paper.pdf",
    attachment_key="ABC12345",
    target_text="important text",
    comment="This is a key finding",
    color="#ff6666",
)
```

You can also import from the submodule directly:

```python
from stable_jarvis_dev.annotation import ZoteroAnnotator, annotate
```

### PDF to Markdown Conversion

```python
from stable_jarvis_dev import PDFConverter, ConversionOptions

converter = PDFConverter()
result = converter.convert("paper.pdf")

if result.success:
    print(result.markdown)
```

### Image Extraction with Metadata

```python
from stable_jarvis_dev import PDFConverter

converter = PDFConverter()

# Extract high-quality images with position info
metadata = converter.extract_images_with_metadata(
    "paper.pdf",
    "./figures",
    quality="high",  # low/medium/high/epic
    name_prefix="SNX599P2",
)

# Save manifest JSON  
converter.save_image_manifest(metadata, "./figures/manifest.json")
# Output: [{"filename": "SNX599P2_fig1.png", "page": 1, "description": "Figure at the top of page 1"}, ...]
```

### Get Paper Metadata via Zotero MCP

现在gemini-cli已经配置好了zotero-mcp服务器，你可以直接通过MCP接口获取论文的元数据了。以下是一个示例交互：

```
 > what kind of metadata can you get from the zotero-mcp? for example, try to get metadata of paper RESC: A Reinforcement Learning Based Search-to-Control Planning Framework for Agile Quadrotors
✦ I will search for the paper in your Zotero library to retrieve its itemKey and then fetch its complete metadata.
✦ I'll retrieve the detailed metadata for the paper "RESC: A Reinforcement Learning Based Search-to-Control Planning Framework for Agile Quadrotors" using its itemKey.
✦ You can retrieve comprehensive bibliographic and research metadata from the Zotero MCP. Using the paper "RESC: A Reinforcement Learning Based
  Search-to-Control Planning Framework for Agile Quadrotors" as an example, here is the type of information available:


  Core Metadata for "RESC" (Key: GEPUIWCR)
   * Title: RESC: A Reinforcement Learning Based Search-to-Control Planning Framework for Agile Quadrotors
   * Authors: Zhaohong Liu, Wenxuan Gao, Yinshuai Sun, Peng Dong
   * Publication: IEEE Robotics and Automation Letters (Vol. 10, Issue 9, Sept 2025)
   * Pages: 9032-9039
   * DOI: 10.1109/LRA.2025.3592101
   * Abstract: A detailed summary of the search-to-control framework, visibility-based path searching, and RL-driven low-level control for agile
     flight.
   * Tags: Aerial systems, Aerodynamics, Heuristic algorithms, Integrated planning and control, Reinforcement learning, Quadrotors, etc.
   * Attachments: Path to the local PDF (D:\Documents\Zotero\storage\SNX599P2\...) and the original IEEE Xplore URL.
   * Zotero Link: zotero://select/library/items/GEPUIWCR


  Summary of Metadata Types
   1. Bibliographic: Title, creators, publication venue, volume/issue, dates, and pages.
   2. Identifiers: DOI, ISBN, ISSN, and original source URLs.
   3. Content Summaries: Full abstracts and any personal notes you've attached.
   4. Organization: Tags, collection memberships, and item relations.
   5. Files: Local file paths to PDFs/attachments, file sizes, and MD5 hashes (for verification).
   6. Fulltext Status: Whether the item is indexed for full-text search.

 > I need the attatchment key and the PDF path of this paper, can u provide?
✦ For the paper "RESC: A Reinforcement Learning Based Search-to-Control Planning Framework for Agile Quadrotors", here are the attachment details:


   * Attachment Key: SNX599P2
   * PDF Path: D:\Documents\Zotero\storage\SNX599P2\Liu 等 - 2025 - RESC A Reinforcement Learning Based Search-to-Control Planning Framework for
     Agile Quadrotors.pdf


  You can use the attachment key with the get_content tool to extract specific sections or the full text of the PDF.
```

必须注意，得到了两个key，一个是 Zotero Item Key（GEPUIWCR），另一个是 PDF Attachment Key（SNX599P2）。前者用于 API 调用获取元数据，后者用于定位本地 PDF 文件进行内容提取和注释。

## Project Structure

```
stable_jarvis_dev/
├── __init__.py              # Top-level re-exports
├── py.typed
├── annotation/              # PDF annotation via Zotero Web API
│   ├── __init__.py
│   ├── annotator.py         # High-level ZoteroAnnotator API
│   ├── config.py            # Configuration management
│   ├── coordinates.py       # PDF coordinate extraction (PyMuPDF)
│   └── zotero_client.py     # Zotero Web API client
└── report_generator/        # PDF processing and conversion
    ├── __init__.py
    ├── converter.py         # PDFConverter, image extraction, manifest
    └── py.typed
```

