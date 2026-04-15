---
name: memory-init
description: First-time setup for Claude Memory — creates your knowledge vault
---

# /memory-init — First-time setup

You are running the interactive setup wizard for Claude Memory. Guide the user through configuration step by step.

## Step 1: Check existing config

Read the file `~/.config/claude-memory/config.yaml`. If it exists:
- Show current config (vaults, default, timezone)
- Ask: "Memory is already configured. Want to reconfigure? (yes/no)"
- If no → stop

## Step 2: Vault location

Ask the user:

> Where should I store your knowledge vault?
> Default: ~/Documents/Vaults/memory

Accept their answer or use the default. Let them pick any path.

## Step 3: Vault name

Use the last segment of the path as the vault name (e.g., `~/Documents/Vaults/work` → `work`).

## Step 4: Scope

Ask:

> Use this vault:
> 1. Globally — for all projects by default
> 2. Only for this project

If global → set as `default_vault`.
If project-only → add current working directory to `projects` map.

## Step 5: Timezone

Auto-detect timezone by running:
```bash
readlink /etc/localtime | sed 's|.*/zoneinfo/||'
```

Show detected timezone and ask to confirm:
> Timezone detected: Europe/Moscow. OK? (yes / enter another)

## Step 6: Create everything

1. Create the vault directory structure:
```bash
mkdir -p <vault_path>/{daily,knowledge/{concepts,connections,qa}}
```

2. Create `<vault_path>/knowledge/index.md` if it doesn't exist:
```markdown
# Knowledge Base Index

| Article | Summary | Compiled From | Updated |
|---------|---------|---------------|---------|
```

3. Create `<vault_path>/knowledge/log.md` if it doesn't exist:
```markdown
# Knowledge Log
```

4. Write `~/.config/claude-memory/config.yaml`:
```yaml
timezone: <detected>
compile_after_hour: 18
default_vault: <name>  # only if global

vaults:
  <name>:
    path: <vault_path>

projects: {}  # or with current project mapped
```

Use the Write tool to create the file. Create `~/.config/claude-memory/` directory first if needed (via Bash: `mkdir -p ~/.config/claude-memory`).

## Step 7: Confirm

Tell the user:

> Done! Vault "<name>" created at <path>.
> Memory will start capturing from your next session.
>
> To connect another project to this vault or create a new one, run `/memory-connect` from that project.

## Rules

- Be concise and friendly
- Use the user's language (if they write in Russian, respond in Russian)
- Don't explain technical details unless asked
- If any step fails, explain what went wrong and how to fix it
