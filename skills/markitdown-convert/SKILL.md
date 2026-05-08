---
name: markitdown-convert
description: Convert any file to Markdown using Microsoft MarkItDown. Use this skill whenever the user needs to extract text from PDFs, Word documents, Excel spreadsheets, PowerPoints, EPUBs, images, audio, HTML pages, CSV, JSON, XML, ZIP archives, Jupyter notebooks, Outlook .msg files, or any other document format. Also use it when the user asks to "convert to markdown", "extract text from", "read this file as text", or mentions specific file formats they want turned into readable markdown. This skill runs in the conda jarvis environment with markitdown v0.1.6b2.
---

# MarkItDown 文件转换

使用 Microsoft MarkItDown 将任意文件格式转换为 Markdown 文本。MarkItDown 已安装在 conda `jarvis` 环境（Python 3.12, markitdown v0.1.6b2）。

所有命令通过 `conda run -n jarvis` 执行。

## 快速决策表

| 用户需求 | 使用方式 |
|---------|---------|
| 快速转换一个本地文件 | CLI: `markitdown <file> -o output.md` |
| 转换后直接读入上下文 | CLI 输出到 stdout，捕获结果 |
| 批量转换多个文件 | Python API 循环 |
| 图片/音频需要文字描述 | Python API + LLM client |
| 流式数据/无文件路径 | Python API `convert_stream()` |
| URL 指向的文件 | Python API `convert_uri()` 或 CLI 管道 |

## CLI 用法

环境前缀：`conda run -n jarvis markitdown ...`

```bash
# 基本转换（输出到 stdout）
conda run -n jarvis markitdown "path/to/file.pdf"

# 保存到文件
conda run -n jarvis markitdown "path/to/file.pdf" -o output.md

# 管道输入
cat file.pdf | conda run -n jarvis markitdown

# 从 stdin 读取时指定格式
cat data.bin | conda run -n jarvis markitdown -x pdf
conda run -n jarvis markitdown -m application/pdf < data.bin

# 指定编码
conda run -n jarvis markitdown -c UTF-8 file.csv

# 查看已安装的第三方插件
conda run -n jarvis markitdown --list-plugins

# 使用第三方插件
conda run -n jarvis markitdown --use-plugins file.pdf

# 保留 base64 图片 data URI（默认会截断）
conda run -n jarvis markitdown --keep-data-uris file.html
```

## Python API 用法

执行脚本时写入临时 `.py` 文件然后运行（避免 conda run 内联脚本的换行问题）：

```bash
conda run -n jarvis python /path/to/temp_script.py
```

### 核心入口：convert()

智能分发，根据参数类型自动选择处理路径：

```python
from markitdown import MarkItDown

md = MarkItDown()

# 自动判断类型
result = md.convert("document.pdf")        # 本地文件
result = md.convert("https://example.com/") # URL
result = md.convert(response)               # requests.Response
result = md.convert(binary_stream)          # BinaryIO

print(result.text_content)  # Markdown 字符串
```

### 精确方法（推荐）

```python
# 本地文件
md.convert_local("/path/to/file.xlsx")

# 二进制流（需提示格式）
from markitdown import StreamInfo
md.convert_stream(io.BytesIO(raw_bytes),
    stream_info=StreamInfo(extension=".pdf"))

# HTTP 响应
import requests
r = requests.get(url, stream=True)
md.convert_response(r)

# URI（支持 http/https/file/data）
md.convert_uri("https://arxiv.org/pdf/2301.00001.pdf")
md.convert_uri("file:///C:/Users/me/data.csv")
```

### LLM 集成（图片/音频描述）

```python
from openai import OpenAI
from markitdown import MarkItDown

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("photo.jpg")
```

## 内置支持的格式

| 类别 | 格式 |
|------|------|
| 文档 | PDF, DOCX, PPTX, XLSX, XLS |
| 电子书 | EPUB |
| 图片 | 各图片格式（需 LLM 才有文字描述） |
| 音频 | 各音频格式（需 LLM） |
| 网页 | HTML, Wikipedia, YouTube, RSS |
| 数据 | CSV, JSON(via text), XML(via text) |
| 代码 | Jupyter Notebook (.ipynb) |
| 邮件 | Outlook .msg |
| 压缩 | ZIP（递归解压并转换内部文件） |
| 纯文本 | 所有纯文本格式（兜底） |

## 输出处理

`DocumentConverterResult` 对象包含：
- `result.text_content` — Markdown 文本（已规范化：统一换行、合并多余空行）
- `result.title` — 可选标题

## 注意事项

- 优先使用 `convert_local()` 而非 `convert()` 处理本地文件（安全，避免被误解析为 URL）
- 当前环境无第三方插件，可通过 `pip install markitdown-ocr` 安装 OCR 插件
- HTTP 请求默认 Accept 头为 `text/markdown`，利用支持 Markdown 输出的服务
