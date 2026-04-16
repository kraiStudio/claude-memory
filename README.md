# claude-memory

Long-term memory plugin for Claude Code. Automatically captures what you do and builds a searchable knowledge base.

## Quick start

Install:
```
/plugin marketplace add kraiStudio/claude-memory
/plugin install claude-memory@claude-memory --scope user
```

Set up (first time):
```
/memory
```

The wizard creates your vault and starts capturing. That's it.

> First session after install may take 10-20 seconds (installing dependencies).

## What it does

Every time you close a session, the plugin extracts what changed — files edited, decisions made, things discovered — and saves it to your vault. Over time, it compiles these into a structured knowledge base.

When you start a new session, Claude already knows what happened before.

```
You work → Session ends → Flush extracts facts → Daily log
                                                      ↓
                                              Compiler → Knowledge articles
                                                      ↓
                                          Next session ← Claude reads index
```

## Two modes

**Personal** — your private memory, stored outside the project:
```
~/Documents/Vaults/work/
├── daily/           # session logs
├── knowledge/       # compiled articles
└── raw/             # source library (PDFs, specs, notes)
```

**Project** — shared team knowledge, stored in the repo:
```
project/.memory/
├── knowledge/       # articles (no daily logs)
└── raw/             # source library
```

Mode switches automatically: if `.memory/` exists in the project — project mode. Otherwise — personal.

Both are Obsidian-compatible. Open as vault to browse.

## Commands

Everything through one command — `/memory`:

| What you type | What happens |
|---------------|-------------|
| `/memory` | Status, or setup wizard if not configured |
| `/memory` + question | Query the knowledge base |
| `/memory compile` | Compile daily logs into articles |
| `/memory check` | Health check (broken links, orphans, stale articles) |
| `/memory uninstall` | Clean up before removing the plugin |

To add files to the knowledge base, just ask Claude naturally: "add this file to memory", "process api-spec.pdf". The file goes to `raw/` as a permanent source, and a knowledge article is created referencing it.

## Customization

Create `knowledge/COMPILE.md` in your vault to control how the compiler works:

```markdown
# Compile Rules

- Tasks go to knowledge/tasks/ (not concepts/)
- File names: kebab-case, English only
- Skip minor bugfix sessions
- Architecture decisions go to knowledge/decisions/
- Each article must have a "Status" section
```

The compiler reads this file and follows your rules. No file = default behavior.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Claude Code

## License

MIT
