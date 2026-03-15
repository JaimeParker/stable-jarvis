# Paper Finder

Use this skill when you want to discover recent arXiv papers for a specific research profile and write the results as Obsidian-compatible Markdown notes.

## Run Retrieval

Run the CLI from the repository root:

```bash
python skills/paper-finder/find_papers.py \
  --profile path/to/research-interest.json \
  --output path/to/obsidian/inbox
```

Optional semantic ranking:

```bash
python skills/paper-finder/find_papers.py \
  --profile path/to/research-interest.json \
  --output path/to/obsidian/inbox \
  --semantic-config path/to/semantic-config.json
```

`semantic-config.json` should match the fields expected by `stable_jarvis.paper_finder.semantic.SemanticConfig`.

## Build or Refresh a Profile

If the user does not already have a profile JSON, use Zotero MCP read tools to collect evidence first:

1. `zotero_list_collections`
2. `zotero_profile_evidence`

Then write a JSON profile matching the same structure used by `3rd_party/research-assist/profiles/research-interest.example.json`:

- `profile_id`
- `profile_name`
- `zotero_basis`
- `retrieval_defaults`
- `interests[]`

Prefer short `method_keywords` and only a small number of `query_aliases` per interest.

## Enrich Candidate Notes

After the Python retrieval run finishes, read the generated Obsidian note and use Zotero MCP read tools to gather nearby library evidence. Then update the note's frontmatter and the `Why It Matters`, `Quick Takeaways`, and `Caveats` sections using the prompt in `skills/paper-finder/prompts/enrich-candidate.prompt.txt`.

Do not write anything back into Zotero. This workflow is read-only against Zotero and writes only local Markdown notes.