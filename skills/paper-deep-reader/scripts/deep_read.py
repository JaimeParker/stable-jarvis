#!/usr/bin/env python3
"""Execute 6-round deep reading analysis via external LLM API calls.

Reuses paperwise's llm.client and section prompts to generate a deep-reading
report. Claude Code orchestrates Phases 1-3 and 5-6; this script handles
Phase 4: the actual 6 independent LLM API calls.

Usage:
    python deep_read.py \
        --content paper_text.txt \
        --meta paper_meta.json \
        --kb kb_context.json \
        --output ./outputs/my_paper \
        --provider deepseek \
        --model deepseek-chat

Input files:
    --content:  Plain text of the paper (may be chunk-summarized)
    --meta:     JSON with keys: title, arxiv_id, authors, published, categories
    --kb:       JSON array of KBEntry objects (from build_kb_context.py), or "-" to skip

Output:
    {output_dir}/report.md           — final Markdown report
    {output_dir}/analysis_cache.json — cached LLM answers (reused unless --force)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Load .env from stable-jarvis root before anything else
_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"
if _ENV_FILE.exists():
    with open(_ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if key and key not in os.environ:
                os.environ[key] = val

# Ensure paperwise is on sys.path
_PAPERWISE = Path(__file__).resolve().parents[4] / "3rd_party" / "paperwise"
if str(_PAPERWISE) not in sys.path:
    sys.path.insert(0, str(_PAPERWISE))

# ── Section prompts (inlined from paperwise for zero-import-friction) ────────

SYSTEM_PROMPT = """\
你是一位资深 AI 研究员，正在为自己撰写论文精读笔记。
写作要求：
- 语言为学术中文，表达精确，不啰嗦
- 每个 section 至少 200 字，重要内容可更长
- 用具体数字、公式、方法名支撑论点，不写空话
- 遇到方法细节时，解释清楚其设计动机，不只是罗列
- 知识库中有相关论文时，做有实质内容的横向对比，指出异同
- 不引用知识库和论文原文之外未出现的论文
- 所有数学公式必须使用 Markdown 格式：行内公式用 $...$，独立公式用 $$...$$，不得使用 \\( \\) 或 \\[ \\]\
"""

SECTION_PROMPTS = [
    # q1: 研究问题与动机
    """\
请深入分析这篇论文的研究问题与动机，至少 200 字：
- 领域背景：该问题属于哪个研究方向，当前主流方法是什么
- 核心痛点：现有方法存在哪些根本性缺陷或局限
- 研究动机：作者为什么认为这个问题值得解决，重要性体现在哪里
- 论文目标：作者的核心 claim 是什么

{kb_section}论文标题：{title}

论文内容：
{content}""",

    # q2: 核心方法
    """\
请深入分析这篇论文的核心方法，至少 300 字：
- 整体架构：方法的总体设计思路和模块划分
- 关键创新：与此前方法相比，最核心的技术创新是什么，解决了哪个具体问题
- 重要细节：关键模块的设计（可引用公式、超参数、算法步骤），并解释每个设计选择背后的动机
- 实现要点：训练策略、目标函数、推理方式中有哪些值得注意的地方

{kb_section}论文标题：{title}

论文内容：
{content}""",

    # q3: 实验设计与结果
    """\
请深入分析这篇论文的实验部分，至少 200 字：
- 任务与数据集：评估了哪些任务，使用了哪些数据集，规模如何
- 基线选取：与哪些方法进行了比较，这些基线的选取是否合理
- 主要结果：关键指标上的具体数字，提升幅度是否显著
- 消融实验：哪些组件被单独验证，结论是什么
- 结果可信度：实验设计有无明显缺陷或遗漏

{kb_section}论文标题：{title}

论文内容：
{content}""",

    # q4: 与相关工作的比较
    """\
请将这篇论文与相关工作进行深入比较，至少 200 字：
- 优势：本文方法在哪些方面明显优于已有工作，技术层面的原因是什么
- 不足：相比相关工作，本文在哪些场景或指标上仍有差距
- 差异化：本文与最相近的工作的本质区别是什么

【重要】若知识库中有相关论文，请优先与其进行具体对比，引用时注明论文标题和 arxiv ID。
不要编造知识库和论文原文中未出现的引用。

{kb_section}论文标题：{title}

论文内容：
{content}""",

    # q5: 局限性与未来工作
    """\
请分析这篇论文的局限性与未来方向，至少 150 字：
- 作者承认的局限：论文中明确提到的不足或适用范围限制
- 未被承认的潜在问题：你认为该方法可能存在但作者未讨论的问题
- 未来工作：论文提出或你认为值得探索的后续研究方向，尽量具体

{kb_section}论文标题：{title}

论文内容：
{content}""",

    # q6: 我的评价与启发
    """\
请写出你对这篇论文的个人评价与研究启发，至少 150 字：
- 论文价值：这篇论文在领域内的贡献和地位如何
- 方法迁移：核心思路是否可以迁移到其他问题，如何迁移
- 对自己研究的启发：这篇论文给你带来了哪些具体的想法或新的研究问题

{kb_section}论文标题：{title}

论文内容：
{content}""",
]

KB_SECTION_TEMPLATE = """\
## 知识库上下文（已读论文，可用于对比）

{entries}

---
"""

REPORT_TEMPLATE = """\
# {title}

**作者**：{authors}
**发表时间**：{published}
**Arxiv ID**：{arxiv_id}
**领域**：{categories}

---

## 1. 研究问题与动机

{q1}

## 2. 核心方法

{q2}

## 3. 实验设计与结果

{q3}

## 4. 与相关工作的比较

{q4}

## 5. 局限性与未来工作

{q5}

## 6. 我的评价与启发

{q6}
"""

# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_kb_section(kb_entries: list[dict], current_arxiv_id: str) -> str:
    """Build the KB context string injected into each LLM prompt."""
    entries = [e for e in kb_entries if e.get("arxiv_id") != current_arxiv_id][:5]
    if not entries:
        return ""
    lines = []
    for e in entries:
        lines.append(
            f"- **{e.get('title', 'Unknown')}** "
            f"({e.get('published', '')}, arxiv:{e.get('arxiv_id', 'N/A')})\n"
            f"  {e.get('text', '')[:600].strip()}"
        )
    print(f"[KB] 知识库提供 {len(entries)} 篇相关论文：", file=sys.stderr)
    for e in entries:
        print(f"  - {e.get('title', '')} ({e.get('arxiv_id', 'N/A')})", file=sys.stderr)
    return KB_SECTION_TEMPLATE.format(entries="\n\n".join(lines))


def _chunk_text(text: str, size: int = 12000, overlap: int = 500) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def _summarize_chunks(title: str, chunks: list[str], complete_fn) -> str:
    summaries = []
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        prompt = (
            f"这是论文《{title}》的第 {i+1}/{total} 段，"
            "请提取方法、实验、结论等关键信息，输出 400 字以内的中文摘要：\n\n" + chunk
        )
        summaries.append(complete_fn(SYSTEM_PROMPT, prompt, max_tokens=1000))
    return "\n\n".join(f"[第{i+1}段摘要]\n{s}" for i, s in enumerate(summaries))


def _prepare_content(title: str, full_text: str, complete_fn) -> str:
    if len(full_text) <= 24000:
        return full_text
    chunks = _chunk_text(full_text)
    return _summarize_chunks(title, chunks, complete_fn)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="6-round deep reading via LLM API")
    ap.add_argument("--content", required=True, type=Path, help="Paper full text file")
    ap.add_argument("--meta", required=True, type=Path, help="Paper metadata JSON")
    ap.add_argument("--kb", type=Path, default=None, help="KB context JSON (omit to skip)")
    ap.add_argument("--output", "-o", required=True, type=Path, help="Output directory")
    ap.add_argument("--provider", default=None, help="LLM provider (anthropic|openai|deepseek|qwen)")
    ap.add_argument("--model", default=None, help="LLM model name")
    ap.add_argument("--force", action="store_true", help="Regenerate even if cached")
    args = ap.parse_args()

    # Resolve provider/model from CLI > env > paperwise config
    from research_helper import config as rh_config

    provider = args.provider or rh_config.LLM_PROVIDER
    model = args.model or rh_config.LLM_MODEL
    os.environ["LLM_PROVIDER"] = provider
    os.environ["LLM_MODEL"] = model

    print(f"[deep_read] Provider: {provider}, Model: {model}", file=sys.stderr)

    # Load inputs
    content_text = args.content.read_text(encoding="utf-8")
    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    kb_entries: list[dict] = []
    if args.kb and str(args.kb) != "-":
        kb_entries = json.loads(args.kb.read_text(encoding="utf-8"))

    title = meta.get("title", "Unknown")
    arxiv_id = meta.get("arxiv_id", "")

    # Prep output dir and cache
    args.output.mkdir(parents=True, exist_ok=True)
    cache_path = args.output / "analysis_cache.json"

    answers: list[str]
    if not args.force and cache_path.exists():
        answers = json.loads(cache_path.read_text(encoding="utf-8"))
        if len(answers) == 6:
            print("[deep_read] 复用缓存的分析结果", file=sys.stderr)
        else:
            answers = []
    else:
        answers = []

    if not answers:
        from research_helper.llm.client import complete

        content = _prepare_content(title, content_text, complete)
        kb_section = _build_kb_section(kb_entries, arxiv_id)

        answers = []
        for i, prompt_tpl in enumerate(SECTION_PROMPTS):
            print(f"[deep_read] 第 {i+1}/6 轮 LLM 分析中...", file=sys.stderr)
            prompt = prompt_tpl.format(
                title=title,
                content=content,
                kb_section=kb_section,
            )
            try:
                answer = complete(SYSTEM_PROMPT, prompt, max_tokens=4096)
            except Exception as exc:
                answer = f"[Error in section {i+1}: {exc}]"
                print(f"[deep_read] Error: {exc}", file=sys.stderr)
            answers.append(answer)

        cache_path.write_text(json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[deep_read] 缓存已保存 → {cache_path}", file=sys.stderr)

    # Render and write report
    report = REPORT_TEMPLATE.format(
        title=title,
        authors=meta.get("authors", "Unknown"),
        published=meta.get("published", ""),
        arxiv_id=arxiv_id or "N/A",
        categories=meta.get("categories", "N/A"),
        q1=answers[0],
        q2=answers[1],
        q3=answers[2],
        q4=answers[3],
        q5=answers[4],
        q6=answers[5],
    )
    report_path = args.output / "report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"[deep_read] 报告已生成 → {report_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
