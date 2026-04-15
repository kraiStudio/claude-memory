---
name: memory-connect
description: Connect the current project to a memory vault
---

# /memory-connect — Connect project to a vault

You are connecting the current project to a Claude Memory vault. Guide the user interactively.

## Step 1: Check config exists

Read `~/.config/claude-memory/config.yaml`. If it doesn't exist:
> Claude Memory is not set up yet. Run `/memory-init` first.
Stop here.

## Step 2: Check current state

Parse the config. Check if the current working directory is already in `projects` map or matches the default vault.

If already connected:
> This project is connected to vault "<name>" at <path>.
> Want to change it? (yes/no)
If no → stop.

## Step 3: Show options

List existing vaults from config and offer choices:

> Connect this project to:
> 1. "<vault1>" (<path1>) — default
> 2. "<vault2>" (<path2>)
> 3. Create a new vault

Number the options dynamically based on existing vaults.

## Step 4a: Existing vault selected

Add the current working directory to the `projects` map in config.yaml:

```yaml
projects:
  <current_cwd>: <selected_vault_name>
```

Read the existing config, update the `projects` section, write it back.

## Step 4b: New vault selected

Ask:
> Vault name?

Then:
> Path? Default: ~/Documents/Vaults/<name>

Create the directory structure:
```bash
mkdir -p <vault_path>/{daily,knowledge/{concepts,connections,qa}}
```

Create `knowledge/index.md` and `knowledge/log.md` with templates (same as memory-init).

Add the vault to config.yaml `vaults` section and add the project mapping to `projects`.

## Step 5: Confirm

> Done! Project connected to vault "<name>".
> Sessions in this directory will now write to <path>.

## Rules

- Be concise and friendly
- Use the user's language
- Don't explain technical details unless asked
- When updating config.yaml, read the existing file first, merge changes, then write back — never overwrite the whole file blindly
