# claude-memory

Long-term memory plugin for Claude Code. Automatically captures session knowledge into a structured, searchable knowledge base. No vector databases, no embeddings — just markdown and an index the LLM can reason over.

Inspired by [Karpathy's LLM Wiki](https://x.com/karpathy/status/1934372048824365261) architecture.

## Concept

Every time you close a Claude Code session, the plugin extracts what happened — files changed, decisions made, bugs found, action items — and saves it. Over time, these session logs get compiled into structured knowledge articles. When you start a new session, Claude reads the knowledge index and already has full context.

```
You work → Session ends → Flush agent extracts facts → Daily log
                                                           ↓
                                                 Compiler → Knowledge articles
                                                           ↓
                                             New session ← Claude reads index
```

Key principles:

- **Automatic** — session capture runs in the background via hooks, no manual action needed
- **Obsidian-compatible** — vaults contain only markdown, open them in Obsidian to browse
- **One command** — everything through `/memory`, behavior adapts to context
- **Two modes** — personal memory (private vault) and project memory (shared in repo)
- **Customizable** — COMPILE.md lets you define folder structure, naming, language, filtering

## Quick start

### 1. Install

```
/plugin marketplace add kraiStudio/claude-memory
/plugin install claude-memory@claude-memory --scope user
```

`--scope user` makes the plugin active in all your projects. This is the recommended setup.

> First session after install may take 10-20 seconds while `uv` installs Python dependencies. Subsequent sessions start instantly.

### 2. Set up

```
/memory
```

The wizard will ask:
- Where to store your vault (default: `~/Documents/Vaults/memory`)
- Global or project-only scope
- Timezone (auto-detected)

### 3. Scan your project

After setup, ask Claude to learn your project:

```
Analyze this project structure, read the key files, and add everything important to memory.
```

Claude will scan the codebase — directory tree, configs, entry points, services — and create knowledge articles in your vault. On the next session, Claude already knows your project architecture, tech stack, and key patterns without re-reading everything.

You can be specific:

```
Read all API routes and save the structure to memory.
Analyze the microservices in docker-compose and remember how they connect.
Look at the database schema and add it to memory.
```

This is one of the most powerful features — **you build project context once, and Claude remembers it forever**.

### 4. Done

Memory starts capturing from the next session. No further configuration needed.

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Code

## Two memory modes

### Personal mode

Your private memory, stored outside the project. Activated when there is no `.memory/` directory in the project.

```
~/Documents/Vaults/work/
├── daily/           # session logs (one file per day)
├── knowledge/       # compiled articles
│   ├── index.md     # knowledge base index — Claude reads this at session start
│   ├── log.md       # compilation log
│   ├── concepts/    # topic articles
│   ├── connections/  # cross-topic relationships
│   ├── decisions/   # architecture decisions (if configured in COMPILE.md)
│   ├── tasks/       # task articles (if configured in COMPILE.md)
│   └── qa/          # saved Q&A articles
└── raw/             # source library (PDFs, specs, notes — permanent storage)
```

How it works:
1. **SessionStart** hook reads `knowledge/index.md` and recent daily log, injects into conversation context
2. You work normally
3. **SessionEnd** hook extracts conversation transcript, spawns flush agent
4. Flush agent (Haiku) analyzes transcript, writes summary to today's daily log
5. After compile hour (default 18:00), compiler (Opus) turns daily logs into knowledge articles

### Project mode

Shared team knowledge, stored in the repo. Activated when `.memory/` directory exists in the project.

```
project/.memory/
├── knowledge/       # articles (no daily logs — flush writes articles directly)
│   ├── index.md
│   ├── concepts/
│   ├── connections/
│   └── qa/
└── raw/             # source library
```

How it works:
1. **SessionStart** hook reads `.memory/knowledge/index.md`
2. You work normally
3. **SessionEnd** hook spawns flush agent in project mode
4. Flush agent writes/updates articles directly in `.memory/knowledge/` — no daily logs, no compilation step
5. Only project-relevant knowledge is saved (architecture, decisions, patterns). Personal experiments are skipped.

### Mode detection

```
.memory/ exists in project?
  ├── Yes → project mode
  └── No  → personal mode (vault from config)
```

Modes are mutually exclusive. One project, one memory source. No mixing.

## Commands

Everything through one command — `/memory`. Behavior adapts to context.

### `/memory` (no arguments)

- **No config** → setup wizard (creates vault, config)
- **Config exists, project not connected** → connect wizard (pick vault or create `.memory/`)
- **Everything configured** → shows status: vault path, article count, last compile date

### `/memory` + question

Query the knowledge base:

```
/memory What auth approach did we decide on?
/memory How does the API gateway work?
```

Claude reads the index, picks relevant articles, synthesizes an answer. If an article references a source in `raw/`, Claude can read the original for more detail.

### `/memory compile`

Compile daily logs into knowledge articles. Interactive — asks what to compile:

- **New only** (default) — only changed/new daily logs
- **Everything** — recompile all from scratch (`--all` flag)
- **Specific file** — compile one daily log

Flags:
- `--dry-run` — show what will be compiled without doing it
- `--all` — force recompile everything
- `--file <name>` — compile specific file

```bash
# These are run internally by the /memory command:
uv run python scripts/compile.py --vault <path>
uv run python scripts/compile.py --vault <path> --all
uv run python scripts/compile.py --vault <path> --file 2026-04-15.md
uv run python scripts/compile.py --vault <path> --dry-run
```

### `/memory check`

Health check for the knowledge base. 7 checks:

| Check | Severity | What it finds |
|-------|----------|--------------|
| Broken wikilinks | Error | `[[concepts/foo]]` points to non-existent article |
| Orphan pages | Warning | Article exists but no other articles link to it |
| Uncompiled logs | Warning | Daily log not yet compiled |
| Stale articles | Warning | Source file changed after article was compiled |
| Missing backlinks | Suggestion | A links to B, but B doesn't link back (auto-fixable) |
| Sparse articles | Suggestion | Article has fewer than 200 words |
| Contradictions | Error | Two articles make conflicting claims (LLM-powered, optional) |

Flags:
- `--structural-only` — skip the LLM contradiction check (free, fast)

After the report, offers auto-fix for fixable issues.

Report saved to `~/.config/claude-memory/reports/lint-YYYY-MM-DD.md`.

### `/memory uninstall`

Cleanup wizard before removing the plugin:
1. Shows all vaults and article counts
2. Asks what to delete: config only, config + selected vaults, or everything
3. Reminds to run `/plugin uninstall claude-memory` after

### Adding files to the knowledge base

No special command needed. Just ask Claude naturally:

```
Add api-spec.pdf to the knowledge base
Process this file and add to memory
Add all PDFs from raw/ to the knowledge base
```

Claude reads the file, creates a knowledge article in `knowledge/`, copies the source to `raw/` (if not already there), and sets `sources:` in the article's frontmatter to reference the original.

The `raw/` directory is a permanent source library. Files are never deleted or moved — they stay as reference material that Claude can re-read when articles need more detail.

## Configuration

### config.yaml

All plugin config lives in `~/.config/claude-memory/config.yaml`. Managed by `/memory` wizard — you don't need to edit it manually.

```yaml
timezone: Europe/Moscow
compile_after_hour: 18

vaults:
  work:
    path: ~/Documents/Vaults/work
  personal:
    path: ~/Documents/Vaults/personal

projects:
  ~/Documents/Dev/Creative Lab: work
  ~/Documents/Personal: personal
```

- `default_vault` — used for projects not explicitly mapped
- `projects` — maps project directories to vault names
- `compile_after_hour` — when daily compilation triggers (24h format)
- `timezone` — for timestamps in daily logs

### COMPILE.md — custom compile rules

Create `knowledge/COMPILE.md` in your vault (or `.memory/knowledge/COMPILE.md` in project mode) to control how the compiler works:

```markdown
# Compile Rules

- Tasks and Fibery tickets go to knowledge/tasks/
- Architecture decisions go to knowledge/decisions/
- Everything else goes to knowledge/concepts/ and knowledge/connections/
- File names: kebab-case, English
- Article language: Russian
- If article mentions a team member — add tag: tags: [member-name]
- Skip trivial bugfix sessions
- Each task article must have fields: assignee, status, project
```

The compiler reads this file and follows your rules. Custom rules override defaults. No file = default behavior (concepts/, connections/, qa/ only).

To apply new rules to existing articles, run `/memory compile` with "Everything from scratch" option.

## Technical details

### Hooks

Three hooks run automatically via the plugin's `hooks.json`:

| Hook | When | What it does |
|------|------|-------------|
| SessionStart | Session opens | Reads `knowledge/index.md` + recent daily log, injects into context |
| SessionEnd | Session closes | Extracts transcript, spawns flush agent in background |
| PreCompact | Before context compression | Same as SessionEnd — captures context before it's lost |

### Flush agent

- Model: Haiku (cheap, ~$0.01/flush)
- Extracts: files modified, decisions made, discoveries, action items
- Echo detection: if the agent echoes the conversation instead of extracting, the response is discarded
- Quality rules: checks accuracy of facts, prevents inversion (e.g., "added" vs "removed")
- Offset tracking: each flush processes only new transcript lines since the last flush

### Compiler

- Model: Haiku (same as flush — cost-effective for structured output)
- Creates articles with YAML frontmatter, wikilinks, and cross-references
- Reads COMPILE.md for custom rules
- Hash-based deduplication: only recompiles changed daily logs
- Cost: ~$0.30-0.80 per daily log depending on length and model

### State management

Technical files are stored outside the vault (in `~/.config/claude-memory/`), keeping the vault Obsidian-clean:

```
~/.config/claude-memory/
├── config.yaml              # plugin configuration
├── state/
│   └── work.json            # compilation state per vault
└── reports/
    └── lint-2026-04-16.md   # health check reports
```

### Vault resolution priority

1. `.memory/` in project directory → project mode
2. `projects:` map in config.yaml (longest prefix match)
3. `default_vault` in config.yaml
4. `CLAUDE.local.md` with `memory_vault:` line (backward compatibility)
5. None → `/memory` wizard

## Scenarios

### New user, first time

1. Install plugin with `--scope user`
2. Run `/memory` → wizard creates vault
3. Ask Claude: "Analyze this project and add to memory" → Claude scans codebase, creates articles
4. Work normally. Memory captures automatically.
5. Next session — Claude already knows your project.

### New project, existing user

1. Open project in Claude Code
2. SessionStart says "No vault configured, run `/memory`"
3. Run `/memory` → connect wizard: pick existing vault or create new
4. Memory works from next session.

### Team project with shared memory

1. One person runs `/memory` → selects "Create project memory (.memory/)"
2. `.memory/` directory created in repo, committed to git
3. Everyone who clones the repo gets project memory automatically
4. Each session updates articles in `.memory/knowledge/`

### Obsidian browsing

1. Open Obsidian → "Open folder as vault" → select vault directory
2. Browse knowledge articles, see wikilink graph
3. `raw/` files visible as reference material
4. Edit articles manually if needed — compiler won't overwrite manual edits unless you run `--all`

### Custom folder structure

1. Create `knowledge/COMPILE.md` with your rules
2. Run `/memory compile` → "Everything from scratch"
3. Compiler reorganizes articles according to new rules
4. New sessions automatically follow the rules

## Best practices

- **One vault per domain** — work vault for work, personal for personal. Don't mix.
- **COMPILE.md early** — set up rules before you accumulate many articles. Easier than reorganizing later.
- **Check regularly** — run `/memory check --structural-only` periodically to catch broken links and orphans.
- **raw/ for important docs** — specs, API docs, design docs. Claude can reference them when answering questions.
- **Don't edit index.md manually** — the compiler maintains it. Your edits will be overwritten.
- **User scope** — always install with `--scope user`. Project scope means the plugin only works in that one project.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Claude Code

## License

MIT
