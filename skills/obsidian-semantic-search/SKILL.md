# Obsidian Semantic Search

Search Obsidian vault notes by conceptual meaning, not just keywords. Builds a local embedding index over all vault notes (per-section chunking), then performs cosine similarity search at query time.

## When to Use

- User asks a fuzzy/conceptual question about their own notes ("What papers discuss exploration in RL?")
- Keyword search (`mcp__obsidian__search_notes`) returns too many or too few results
- User wants to find notes related to a concept without knowing exact terminology
- As a pre-retrieval step before deep-reading or analyzing vault content

## Architecture

```
Vault (.md files)  ──build_index.py──>  temp/obsidian/embeddings.json  <──search.py──  User Query
                                                │
                                                └── Shared with paper-deep-reader
```

- **Index**: Flat JSON, one embedding per `.md` note (full body text, frontmatter excluded), mtime-tracked incremental rebuild
- **Embeddings**: Reuses `stable_jarvis.llm.embed()` — same provider stack as paper-deep-reader (local / qwen / openai)
- **Search**: Brute-force cosine similarity, O(n) over all notes

## Workflow

### Phase 0: Check Index Freshness (Always First)

Before any search, the agent MUST check the index state:

```bash
python skills/obsidian-semantic-search/scripts/build_index.py --stats
```

Decision logic:

| State | Action |
|-------|--------|
| Index exists AND built today | **Skip build**, proceed to Phase 2 directly |
| Index exists AND built in last 3 days | Run `build_index.py` (incremental — only changed files) |
| Index exists AND older than 3 days | Run `build_index.py --force` (full rebuild) |
| Index does NOT exist | Run `build_index.py --force` (first build) |

### Phase 1: Build/Update Index (If Needed)

```bash
# Incremental update (recommended when index exists but stale)
python skills/obsidian-semantic-search/scripts/build_index.py

# Full rebuild (first time, or after major vault changes)
python skills/obsidian-semantic-search/scripts/build_index.py --force
```

The scripts locate the vault automatically via `OBSIDIAN_VAULT` env var or common paths (`~/Documents/Obsidian`, `~/Obsidian`, `~/vault`). If the vault is at a non-standard location, set it first:
```bash
export OBSIDIAN_VAULT="/path/to/vault"
```

### Phase 2: Semantic Search

```bash
python skills/obsidian-semantic-search/scripts/search.py "query text" --top-k 5
```

Returns JSON array of results, each with:
- `title` — Note title (from H1 or filename)
- `path` — Relative path in vault (use directly with `mcp__obsidian__read_note`)
- `score` — Cosine similarity (0–1, higher = more relevant)
- `text_snippet` — First 200 chars of the note body
- `arxiv_id` — From frontmatter, if present

### Phase 3: Read Full Notes (via Obsidian MCP)

After getting results, use `mcp__obsidian__read_note` with the `path` field to read full content:

```
mcp__obsidian__read_note(path="30 Zettelkasten/RL/MAC.md")
```

### Phase 4: Present Results

Format search results for the user with:
- Note title as `[[wikilink]]`
- Relevance score
- Brief excerpt from `text_snippet`

## Commands

| Command | Purpose |
|---------|---------|
| `build_index.py` | Incremental index rebuild (default) |
| `build_index.py --force` | Full rebuild from scratch |
| `build_index.py --stats` | Show index statistics |
| `build_index.py --clear` | Remove index file |
| `search.py "query"` | Semantic search (top 5) |
| `search.py "query" --top-k 10` | More results |
| `search.py "query" --min-score 0.4` | Filter low-relevance results |
| `search.py "query" --provider qwen` | Use specific embedding provider |

## Configuration

All settings via environment variables (loaded from `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OBSIDIAN_VAULT` | Auto-detect | Path to Obsidian vault |
| `EMBEDDING_PROVIDER` | `local` | `local` / `qwen` / `openai` |
| `EMBEDDING_MODEL` | Provider-dependent | Model override |
| `EMBEDDING_API_KEY` | From `{PROVIDER}_API_KEY` | API key for cloud embeddings |

The `local` provider uses `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) and requires no API key.

## Index Management

- **Incremental updates**: Running `build_index.py` without `--force` compares file mtimes and only re-embeds changed notes. Deleted notes are automatically removed from the index.
- **Shared index**: The index at `temp/obsidian/embeddings.json` is shared with `paper-deep-reader`. Both skills read and benefit from the same index.
- **Rebuild frequency**: Run `--force` after major vault reorganization or when search quality degrades.

## Integration Notes

- Results from `search.py` include the vault-relative `path` — this is the exact argument to pass to `mcp__obsidian__read_note`
- Combine with `mcp__obsidian__search_notes` for hybrid retrieval: semantic for recall, keyword for precision
- Index is stored at `temp/obsidian/embeddings.json` — shared with `paper-deep-reader` skill
