---
name: memory
description: Query the knowledge base or check memory status
---

# /memory — Query or status

## If no arguments provided

Read `~/.config/claude-memory/config.yaml` and show status:
- List of vaults (name, path, article count)
- Which vault the current project uses
- Whether compilation is pending

To count articles, check `<vault_path>/knowledge/concepts/*.md`, `connections/*.md`, `qa/*.md`.

## If a question is provided

Query the active vault's knowledge base using the query script:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/query.py "<question>" --vault <vault_path>
```

The vault path is resolved from config.yaml based on the current project directory.

## If "compile" is provided

Trigger knowledge compilation:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/compile.py --vault <vault_path>
```

## Vault resolution

1. Read `~/.config/claude-memory/config.yaml`
2. Match current directory against `projects` map
3. Fall back to `default_vault`
4. If no config: suggest running `/memory-init`
