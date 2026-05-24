#!/usr/bin/env python3
"""Build semantic search index over Obsidian vault — one embedding per note, full text.

Embeds the complete body of each .md file (frontmatter excluded). No section
splitting, no truncation. Tracks mtime for incremental rebuilds.

Usage:
    python build_index.py                          # incremental rebuild
    python build_index.py --force                  # full rebuild
    python build_index.py --vault /path/to/vault
    python build_index.py --provider qwen
    python build_index.py --stats                  # print index stats only
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path

from stable_jarvis.llm import embed

INDEX_PATH = Path("temp/obsidian/embeddings.json")
MAX_CHARS = 60000  # safety limit: ~30K tokens for Qwen3-Embedding-8B (32K max)


def _find_vault() -> Path:
    env = os.environ.get("OBSIDIAN_VAULT", "")
    if env:
        return Path(env)
    candidates = [
        Path.home() / "Documents" / "Obsidian",
        Path.home() / "Obsidian",
        Path.home() / "vault",
    ]
    for c in candidates:
        if (c / ".obsidian").is_dir():
            return c
    print("Error: Cannot locate Obsidian vault. Set OBSIDIAN_VAULT env var.", file=sys.stderr)
    sys.exit(1)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_text = text[4:end]
    body = text[end + 5:]
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
    return fm, body


def _extract_title(text: str, path_stem: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            return stripped[2:].strip()
    return path_stem


def _iter_notes(vault: Path):
    """Yield (rel_path, title, arxiv_id, body_text, mtime) for each .md file."""
    for md in sorted(vault.rglob("*.md")):
        if any(p.startswith(".") for p in md.relative_to(vault).parts):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue

        mtime = md.stat().st_mtime
        title = _extract_title(text, md.stem)
        fm, body = _parse_frontmatter(text)
        arxiv_id = fm.get("arxiv_id", "")

        body = body.strip()
        if not body:
            continue

        truncated = False
        if len(body) > MAX_CHARS:
            body = body[:MAX_CHARS]
            truncated = True

        rel = str(md.relative_to(vault))
        yield rel, title, arxiv_id, body, mtime, truncated


def _load_existing() -> dict[str, dict]:
    """Load existing index as {path: entry} lookup."""
    if not INDEX_PATH.exists():
        return {}
    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {e["path"]: e for e in data}


def cmd_build(vault: Path, provider: str | None, force: bool = False):
    if provider:
        os.environ["EMBEDDING_PROVIDER"] = provider

    existing = {} if force else _load_existing()

    notes = list(_iter_notes(vault))
    if not notes:
        print("No notes found in vault.", file=sys.stderr)
        sys.exit(1)

    current_paths: set[str] = set()
    to_embed: list[tuple[str, str, str, str, float]] = []
    reused = 0
    truncation_warnings: list[str] = []

    for rel, title, arxiv_id, body, mtime, truncated in notes:
        current_paths.add(rel)

        if truncated:
            truncation_warnings.append(f"  {rel} ({len(body):,} chars → truncated to {MAX_CHARS:,})")

        if rel in existing:
            old_entry = existing[rel]
            old_mtime = old_entry.get("mtime", 0)
            if abs(mtime - old_mtime) < 1.0:
                reused += 1
                continue

        to_embed.append((rel, title, arxiv_id, body, mtime))

    removed = set(existing.keys()) - current_paths

    if not to_embed and not removed:
        ep = os.environ.get("EMBEDDING_PROVIDER", "local")
        print(
            f"Index is up to date ({len(existing)} notes). Provider: {ep}. Use --force to rebuild.",
            file=sys.stderr,
        )
        return

    if truncation_warnings:
        print(f"Warning: {len(truncation_warnings)} note(s) exceed {MAX_CHARS:,} char limit:", file=sys.stderr)
        for w in truncation_warnings:
            print(w, file=sys.stderr)

    # Build new index: keep reused entries, embed new/changed ones
    new_data: list[dict] = []
    for path in set(existing.keys()) & current_paths:
        if path not in {t[0] for t in to_embed}:
            new_data.append(existing[path])

    if to_embed:
        ep = os.environ.get("EMBEDDING_PROVIDER", "local")
        texts = [t[3] for t in to_embed]
        total_chars = sum(len(t) for t in texts)
        print(
            f"Embedding {len(texts)} notes ({total_chars:,} chars total, "
            f"{reused} reused, {len(removed)} removed) with provider={ep}...",
            file=sys.stderr,
        )

        embeddings = embed(texts)

        for (rel, title, arxiv_id, body, mtime), vec in zip(to_embed, embeddings):
            new_data.append({
                "path": rel,
                "title": title,
                "arxiv_id": arxiv_id,
                "text_snippet": body[:200],
                "embedding": vec,
                "mtime": mtime,
            })

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(new_data, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(new_data)} notes → {INDEX_PATH}", file=sys.stderr)


def cmd_stats():
    if not INDEX_PATH.exists():
        print("No index found. Run --build first.", file=sys.stderr)
        sys.exit(1)
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    print(f"Index: {INDEX_PATH}")
    print(f"  Notes: {len(data)}")
    if data:
        total_chars = sum(len(e.get("text_snippet", "")) for e in data)
        newest = max(e.get("mtime", 0) for e in data)
        oldest = min(e.get("mtime", 0) for e in data)
        print(f"  Newest: {time.ctime(newest)}")
        print(f"  Oldest: {time.ctime(oldest)}")


def cmd_clear():
    if INDEX_PATH.exists():
        INDEX_PATH.unlink()
        print(f"Removed {INDEX_PATH}", file=sys.stderr)
    else:
        print("No index to clear.", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Build semantic index over Obsidian vault")
    ap.add_argument("--build", action="store_true", default=True,
                    help="Build/rebuild the embedding index (default)")
    ap.add_argument("--force", action="store_true",
                    help="Force full rebuild, ignoring cached mtime")
    ap.add_argument("--stats", action="store_true", help="Print index statistics")
    ap.add_argument("--clear", action="store_true", help="Remove the index file")
    ap.add_argument("--vault", type=Path, default=None, help="Obsidian vault path")
    ap.add_argument("--provider", type=str, default=None,
                    help="Embedding provider: qwen|openai|local")
    args = ap.parse_args()

    vault = args.vault or _find_vault()

    if args.clear:
        cmd_clear()
    elif args.stats:
        cmd_stats()
    else:
        cmd_build(vault, args.provider, force=args.force)


if __name__ == "__main__":
    main()
