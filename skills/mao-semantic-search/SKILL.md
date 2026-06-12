# Mao Semantic Search

Search Mao Zedong Selected Works by conceptual meaning using vector embeddings. Builds a local embedding index over all 230 articles across 5 volumes, then performs cosine similarity search at query time.

## When to Use

- User asks a thematic/conceptual question about Mao's works ("What did Mao say about guerrilla warfare?")
- Keyword search over the .md files is insufficient
- User wants to find passages related to a concept without knowing exact terminology
- As a pre-retrieval step before deep-reading specific articles

## Architecture

```
assets/mao-selected-works/  ──build_index.py──>  temp/mao/embeddings.json  <──search.py──  User Query
(.md files, 5 vols)                             │
                                                 └── JSON index, 230 entries
```

- **Index**: Flat JSON, one embedding per article (full body text, frontmatter excluded), stored at `temp/mao/embeddings.json`
- **Embeddings**: Reuses `stable_jarvis.llm.embed()` — same provider stack as obsidian-semantic-search (local / qwen / openai)
- **Search**: Brute-force cosine similarity, O(n) over all articles

## Workflow

### Phase 0: Check Index Freshness (Always First)

Before any search, the agent MUST check the index state:

```bash
python skills/mao-semantic-search/scripts/build_index.py --stats
```

Decision logic:

| State | Action |
|-------|--------|
| Index exists | **Skip build**, proceed to Phase 2 directly |
| Index does NOT exist | Run `build_index.py` (full build, ~230 articles) |

The index is static — articles don't change, so rebuild is only needed once.

### Phase 1: Build Index (If Needed)

```bash
python skills/mao-semantic-search/scripts/build_index.py
```

With optional provider override:
```bash
python skills/mao-semantic-search/scripts/build_index.py --provider qwen
```

The scripts locate the Mao works automatically via `MAO_WORKS_DIR` env var or the default path `assets/mao-selected-works/`. If the works are at a non-standard location, set it first:
```bash
export MAO_WORKS_DIR="/path/to/mao-selected-works"
```

### Phase 2: Semantic Search

```bash
python skills/mao-semantic-search/scripts/search.py "query text" --top-k 5
```

Returns JSON array of results, each with:
- `title` — Article title
- `volume` — Volume number (1–5)
- `path` — Relative path in mao-selected-works/ (for reading full text)
- `score` — Cosine similarity (0–1, higher = more relevant)
- `text_snippet` — First 200 chars of the article body

### Phase 3: Read Full Articles

After getting results, use the `Read` tool with the `path` field to read full content:

```
Read(assets/mao-selected-works/vol-01/001-中国社会各阶级的分析.md)
```

### Phase 4: Present Results

Format search results for the user with:
- Article title and volume
- Relevance score
- Brief excerpt from `text_snippet`
- Direct path for further reading

## Commands

| Command | Purpose |
|---------|---------|
| `build_index.py` | Build embedding index (full build) |
| `build_index.py --provider qwen` | Build with specific embedding provider |
| `build_index.py --stats` | Show index statistics |
| `build_index.py --clear` | Remove index file |
| `search.py "query"` | Semantic search (top 5) |
| `search.py "query" --top-k 10` | More results |
| `search.py "query" --min-score 0.4` | Filter low-relevance results |
| `search.py "query" --provider qwen` | Use specific embedding provider |
| `search.py "query" --volume 1` | Search only within a specific volume |

## Configuration

All settings via environment variables (loaded from `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MAO_WORKS_DIR` | `assets/mao-selected-works/` | Path to Mao Selected Works .md files |
| `EMBEDDING_PROVIDER` | `local` | `local` / `qwen` / `openai` |
| `EMBEDDING_MODEL` | Provider-dependent | Model override |
| `EMBEDDING_API_KEY` | From `{PROVIDER}_API_KEY` | API key for cloud embeddings |

The `local` provider uses `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) and requires no API key.

## Index Management

- **Static index**: Articles don't change, so the index is built once and reused indefinitely
- **Index size**: ~230 embeddings, ~4MB total article text, resulting index ~200–400KB
- **Rebuild**: Only needed if the source .md files are regenerated or updated
