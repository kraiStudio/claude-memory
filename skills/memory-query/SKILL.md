---
name: memory-query
description: Query the vault knowledge base to recall past decisions, discoveries, and context. Use this skill whenever the user mentions remembering, recalling, past sessions, previous decisions, project history, or asks questions like "what did we decide", "do you remember", "look up", "what happened with". Also trigger when the user asks about project architecture, past bugs, earlier conversations, or any historical context — even if they don't explicitly say "memory" or "recall".
version: 0.2.0
---

# Memory Query

Query the vault-based knowledge base to find past decisions, discoveries, preferences, and context.

## When to use

- User asks "do you remember...", "what did we decide about...", "look up..."
- User references something from a past session or earlier work
- You need historical context about a project, architecture, or decision
- User asks about project structure, patterns, or conventions already documented
- User mentions a person, task, or concept that might have a knowledge article

## How to query

Run the query script against the active vault:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/query.py "the question" --vault <vault_path>
```

**Vault resolution:**
1. If `.memory/` exists in the project → use `.memory/` path
2. Otherwise → resolve from `~/.config/claude-memory/config.yaml` based on current project directory

## How it works

The query engine reads the knowledge base index, identifies relevant articles, and synthesizes an answer. No vector database — just structured markdown and index-guided retrieval.

If an article references a source in `raw/` and you need more detail than the article provides, read the original file from `<vault>/raw/` for full context.

## File back

To save the answer as a Q&A article in the knowledge base (useful for frequently asked questions), add `--file-back`:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/query.py "the question" --vault <vault_path> --file-back
```

## Examples

**Example 1:**
User: "What auth approach did we pick for the API?"
→ Run query, find decision article, return summary with source references.

**Example 2:**
User: "How do the microservices connect?"
→ Run query, find architecture articles, synthesize a connection overview.

**Example 3:**
User: "What was that bug we found with the webhook handler?"
→ Run query, search discovery/bug articles, return details with session source.
