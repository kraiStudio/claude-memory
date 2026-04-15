---
name: memory
description: Set up, connect, query, or manage your Claude Memory vault
---

# /memory — Unified memory command

Determine what the user needs based on current state, then act accordingly.

## Step 1: Detect state

Read `~/.config/claude-memory/config.yaml`.

**State A — No config file exists:**
→ Go to "First-time setup" flow

**State B — Config exists, but current project is not connected (not in `projects:` map, no `default_vault`, no `.memory/` directory):**
→ Go to "Connect project" flow

**State C — Everything configured (project mapped or default vault exists or `.memory/` exists):**
→ Go to "Status / Query" flow

If the user provided arguments (a question, "compile", "compile raw"), skip state detection and go directly to the relevant action.

---

## First-time setup (State A)

Guide the user step by step:

1. **Vault path:**
   > Where to store your knowledge vault?
   > Default: ~/Documents/Vaults/memory

2. **Vault name:** Use the last segment of the path (e.g., `~/Documents/Vaults/work` → `work`).

3. **Scope:**
   > Use this vault:
   > 1. For all projects (global default)
   > 2. Only for this project

4. **Timezone:** Auto-detect:
   ```bash
   readlink /etc/localtime | sed 's|.*/zoneinfo/||'
   ```
   Ask to confirm.

5. **Create everything:**
   - Vault directory: `mkdir -p <path>/{daily,knowledge/{concepts,connections,qa},raw}`
   - `<path>/knowledge/index.md` with empty table template
   - `<path>/knowledge/log.md` with header
   - `~/.config/claude-memory/config.yaml` with vaults, projects, timezone, compile_after_hour

6. **Confirm:**
   > Done! Vault "<name>" created. Memory starts capturing from next session.

---

## Connect project (State B)

1. List existing vaults from config.
2. Offer options:
   > 1. "<vault1>" (<path1>)
   > 2. "<vault2>" (<path2>)
   > 3. Create new personal vault
   > 4. Create project memory (.memory/ in this repo)

3. **If existing vault:** Add current directory to `projects:` map in config.yaml.

4. **If new personal vault:** Ask name and path, create structure (same as first-time setup step 5), add to config.

5. **If project memory (.memory/):** Create directory structure:
   ```bash
   mkdir -p .memory/knowledge/{concepts,connections,qa} .memory/raw
   ```
   Create `.memory/knowledge/index.md` with empty table template.

6. **Confirm.**

---

## Status / Query (State C)

**No arguments — show status:**
- Current vault name and path (or ".memory/ (project mode)")
- Number of knowledge articles (count files in concepts/, connections/, qa/)
- Last compilation date (from state file)
- Number of daily logs

**Question argument — query knowledge base:**
```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/query.py "<question>" --vault <vault_path>
```

**"compile" argument — interactive compilation:**

Ask the user what to compile:

> What to compile?
> 1. New daily logs only (changed since last compile)
> 2. Everything from scratch
> 3. Specific file
> 4. Raw files from raw/

Based on choice, run the appropriate command:

- Option 1 (default):
  ```bash
  uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/compile.py --vault <vault_path>
  ```
- Option 2:
  ```bash
  uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/compile.py --vault <vault_path> --all
  ```
- Option 3: Ask which file, then:
  ```bash
  uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/compile.py --vault <vault_path> --file <filename>
  ```
- Option 4: Process raw files (see below)

Before running, you can show what will be compiled with `--dry-run`.

**"compile raw" or option 4 — compile raw files:**

1. List files in `<vault_path>/raw/` (exclude `processed/` subdirectory)
2. If no files → "No raw files to process."
3. For each file: read it, extract project-relevant knowledge, create/update articles in `knowledge/`
4. After processing each file, move it to `<vault_path>/raw/processed/`
5. Update `knowledge/index.md` with any new articles

**"check" argument — lint knowledge base:**

Run the lint script:
```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/lint.py --vault <vault_path>
```

For structural checks only (no LLM, free):
```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/lint.py --vault <vault_path> --structural-only
```

Show the report to the user. If fixable issues found, ask if they want auto-fix.

**"uninstall" argument — cleanup:**

1. Read `~/.config/claude-memory/config.yaml`
2. Show what will be affected:
   - Config file at `~/.config/claude-memory/`
   - List all vaults with article counts
3. Ask:
   > What to delete?
   > 1. Config only (keep all vaults)
   > 2. Config + select vaults to delete
   > 3. Everything (config + all vaults)
4. Perform deletions
5. Remind: "Now uninstall the plugin: `/plugin uninstall claude-memory`"

---

## Vault resolution

1. `.memory/` exists in project → use it (project mode)
2. Current directory in config `projects:` map → use mapped vault
3. `default_vault` in config → use it
4. Nothing → "Connect project" flow

## Rules

- Be concise and friendly
- Use the user's language (Russian if they write in Russian)
- When updating config.yaml, always read first, merge, then write back
- Don't explain technical details unless asked
