---
name: memory
description: Query or manage the vault knowledge base
---

# /memory command

Usage: `/memory <question>` — query the knowledge base
Usage: `/memory compile` — compile today's daily log into knowledge articles
Usage: `/memory status` — show vault status and stats

## Query mode (default)

When given a question, query the active vault's knowledge base:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/query.py "<question>" --vault <vault_path>
```

## Compile mode

Trigger knowledge compilation from daily logs:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/compile.py --vault <vault_path>
```

## Status mode

Read and report the vault's knowledge/index.md and scripts/state.json to show:
- Number of knowledge articles
- Last compilation date
- Total API cost
- Recent daily logs

## Vault resolution

The vault path is determined from `CLAUDE.local.md` in the current project directory (look for `memory_vault:` line). If not found, defaults to `~/Documents/Vaults/work`.
