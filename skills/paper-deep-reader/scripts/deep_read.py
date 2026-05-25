#!/usr/bin/env python3
"""Execute 6-round deep reading analysis via external LLM API calls.

Reuses per-category section prompts to generate a deep-reading
report. Claude Code orchestrates Phases 1-3 and 5-6; this script handles
Phase 4: the actual 6 independent LLM API calls.

Prompt sets are stored in ../prompts/{category}/ as individual .md files.
See prompts/categories.toml for available categories.

Usage:
    python deep_read.py \\
        --content paper_text.txt \\
        --meta paper_meta.json \\
        --kb kb_context.json \\
        --output ./outputs/my_paper \\
        --prompt-set ai-ml \\
        --provider deepseek \\
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

# Trigger .env loading before any os.environ reads
import stable_jarvis  # noqa: F401

# ── Prompt loading ────────────────────────────────────────────────────────────

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

KB_SECTION_TEMPLATE = """\
## 知识库上下文（已读论文，可用于对比）

{entries}

---
"""


def _load_prompt_set(category: str) -> dict:
    """Load all prompt files from prompts/{category}/.

    Returns dict with keys: system, sections (list of 6), report_template,
    chunk_summary.
    """
    prompt_dir = PROMPTS_DIR / category
    if not prompt_dir.is_dir():
        print(f"Error: Prompt set '{category}' not found at {prompt_dir}", file=sys.stderr)
        available = [d.name for d in PROMPTS_DIR.iterdir() if d.is_dir()]
        print(f"  Available categories: {', '.join(sorted(available))}", file=sys.stderr)
        sys.exit(1)

    def _read(filename: str) -> str:
        path = prompt_dir / filename
        if not path.exists():
            print(f"Error: Missing prompt file: {path}", file=sys.stderr)
            sys.exit(1)
        return path.read_text(encoding="utf-8").strip()

    sections = []
    for i in range(1, 7):
        sections.append(_read(f"section-{i}.md"))

    return {
        "system": _read("system.md"),
        "sections": sections,
        "report_template": _read("report-template.md"),
        "chunk_summary": _read("chunk-summary.md"),
    }


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
    return _safe_format(KB_SECTION_TEMPLATE, entries="\n\n".join(lines))


def _chunk_text(text: str, size: int = 12000, overlap: int = 500) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def _summarize_chunks(title: str, chunks: list[str], complete_fn,
                      chunk_prompt_tpl: str) -> str:
    summaries = []
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        prompt = _safe_format(
            chunk_prompt_tpl,
            title=title,
            i=str(i + 1),
            total=str(total),
            chunk=chunk,
        )
        summaries.append(complete_fn("", prompt, max_tokens=1000))
    return "\n\n".join(f"[第{i+1}段摘要]\n{s}" for i, s in enumerate(summaries))


def _safe_format(template: str, **kwargs) -> str:
    """Replace {key} placeholders without interpreting curly braces in values.

    Python's str.format() treats any {…} in the substituted values as
    nested placeholders, so LaTeX like ``\\min_{i=1,2}`` in LLM answers
    triggers KeyError.  This helper only replaces the named keys.
    """
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def _prepare_content(title: str, full_text: str, complete_fn,
                     chunk_prompt_tpl: str) -> str:
    if len(full_text) <= 24000:
        return full_text
    chunks = _chunk_text(full_text)
    return _summarize_chunks(title, chunks, complete_fn, chunk_prompt_tpl)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="6-round deep reading via LLM API")
    ap.add_argument("--content", required=True, type=Path, help="Paper full text file")
    ap.add_argument("--meta", required=True, type=Path, help="Paper metadata JSON")
    ap.add_argument("--kb", type=Path, default=None, help="KB context JSON (omit to skip)")
    ap.add_argument("--output", "-o", required=True, type=Path, help="Output directory")
    ap.add_argument("--prompt-set", default="default",
                    help="Prompt category from prompts/ (default: default)")
    ap.add_argument("--provider", default=None,
                    help="LLM provider (anthropic|openai|deepseek|qwen)")
    ap.add_argument("--model", default=None, help="LLM model name")
    ap.add_argument("--force", action="store_true", help="Regenerate even if cached")
    args = ap.parse_args()

    # Load prompts from category directory
    prompts = _load_prompt_set(args.prompt_set)
    system_prompt = prompts["system"]
    section_prompts = prompts["sections"]
    report_template = prompts["report_template"]
    chunk_summary_tpl = prompts["chunk_summary"]

    print(f"[deep_read] Prompt set: {args.prompt_set}", file=sys.stderr)

    # Resolve provider/model from CLI > env
    provider = args.provider or os.environ.get("LLM_PROVIDER", "anthropic")
    model = args.model or os.environ.get("LLM_MODEL", "")
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
        from stable_jarvis.llm import complete

        content = _prepare_content(title, content_text, complete, chunk_summary_tpl)
        kb_section = _build_kb_section(kb_entries, arxiv_id)

        answers = []
        for i, prompt_tpl in enumerate(section_prompts):
            print(f"[deep_read] 第 {i+1}/6 轮 LLM 分析中...", file=sys.stderr)
            prompt = _safe_format(
                prompt_tpl,
                title=title,
                content=content,
                kb_section=kb_section,
            )
            try:
                answer = complete(system_prompt, prompt, max_tokens=4096)
            except Exception as exc:
                answer = f"[Error in section {i+1}: {exc}]"
                print(f"[deep_read] Error: {exc}", file=sys.stderr)
            answers.append(answer)

        cache_path.write_text(
            json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[deep_read] 缓存已保存 → {cache_path}", file=sys.stderr)

    # Render and write report
    report = _safe_format(
        report_template,
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
