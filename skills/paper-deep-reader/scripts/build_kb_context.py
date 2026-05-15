#!/usr/bin/env python3
"""Build KB context JSON from Zotero MCP results and Obsidian search results.

Reads two JSON files:
    --zotero    Output from Zotero MCP semantic_search (formatted as KBEntry array)
    --obsidian  Output from search_obsidian.py --embed or Obsidian MCP results

Merges, deduplicates by arxiv_id, excludes the current paper, and writes
a combined JSON array suitable for deep_read.py's --kb flag.

Usage:
    python build_kb_context.py \
        --zotero zotero_results.json \
        --obsidian obsidian_results.json \
        --exclude 2310.01234 \
        --top-k 5 \
        --output kb_context.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"Warning: {path} not found, skipping.", file=sys.stderr)
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Warning: {path} invalid JSON: {exc}", file=sys.stderr)
        return []
    if not isinstance(data, list):
        print(f"Warning: {path} is not a JSON array, skipping.", file=sys.stderr)
        return []
    return data


def merge(zotero: list[dict], obsidian: list[dict], exclude_arxiv: str, top_k: int) -> list[dict]:
    best: dict[str, dict] = {}

    # Priority: zotero > obsidian-embed > obsidian
    for entry in zotero:
        aid = entry.get("arxiv_id", "").strip()
        if not aid or aid == exclude_arxiv:
            continue
        entry["source"] = entry.get("source", "zotero")
        if aid not in best:
            best[aid] = entry

    for entry in obsidian:
        aid = entry.get("arxiv_id", "").strip()
        # If entry has no arxiv_id, use title as key
        key = aid if aid else entry.get("title", "").strip()
        if not key or aid == exclude_arxiv:
            continue
        entry["source"] = entry.get("source", "obsidian")
        if key not in best:
            best[key] = entry

    entries = list(best.values())

    # Sort: prefer entries with distance score, then by source priority
    def _sort_key(e: dict) -> tuple:
        src_order = {"zotero": 0, "obsidian-embed": 1, "obsidian": 2}
        return (src_order.get(e.get("source", ""), 9), e.get("distance", 1.0))

    entries.sort(key=_sort_key)
    return entries[:top_k]


def main():
    ap = argparse.ArgumentParser(description="Build KB context from Zotero + Obsidian")
    ap.add_argument("--zotero", type=Path, required=True, help="Zotero semantic_search results JSON")
    ap.add_argument("--obsidian", type=Path, required=True, help="Obsidian search results JSON")
    ap.add_argument("--exclude", type=str, default="", help="arxiv_id to exclude (current paper)")
    ap.add_argument("--top-k", type=int, default=5, help="Max results (default: 5)")
    ap.add_argument("--output", "-o", type=Path, required=True, help="Output JSON file")
    args = ap.parse_args()

    zotero_entries = load_json(args.zotero)
    obsidian_entries = load_json(args.obsidian)

    merged = merge(zotero_entries, obsidian_entries, args.exclude, args.top_k)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Merged {len(zotero_entries)} Zotero + {len(obsidian_entries)} Obsidian → "
          f"{len(merged)} entries → {args.output}", file=sys.stderr)

    if len(merged) < args.top_k:
        print(f"Warning: only {len(merged)} entries after merge (requested {args.top_k})", file=sys.stderr)


if __name__ == "__main__":
    main()
