---
name: memory-query
description: Query the vault knowledge base to recall past decisions, discoveries, and context. Use when the user asks to recall, remember, or look up something from past sessions, or when you need historical context about a project.
version: 1.0.0
---

# Memory Query

Query the vault-based knowledge base to find past decisions, discoveries, preferences, and context.

## When to use

- User asks "do you remember...", "what did we decide about...", "look up..."
- You need historical context about a project or architecture decision
- User references something from a past session

## How to query

Run the query script against the active vault:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/query.py "the question" --vault <vault_path>
```

The vault path is resolved from `~/.config/claude-memory/config.yaml` based on the current project, or from `.memory/` if in project mode.

## How it works

The query engine reads the knowledge base index, identifies relevant articles, and synthesizes an answer. No vector database — just structured markdown and index-guided retrieval.

If an article references a source in `raw/` and you need more detail, read the original file from `<vault>/raw/` for full context.

## File back

To save the answer as a Q&A article in the knowledge base, add `--file-back`:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/query.py "the question" --vault <vault_path> --file-back
```
