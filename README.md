# claude-memory

Vault-based long-term memory plugin for Claude Code.

Automatically captures session knowledge into Obsidian-compatible vaults, compiles daily logs into a structured knowledge base, and provides index-guided querying — no vector database, no embeddings.

Based on [Karpathy's LLM Wiki](https://x.com/karpathy/status/1934372048824365261) architecture.

## How it works

```
Session → Hooks capture context → Flush agent extracts facts → Daily log
                                                                   ↓
                                                        Compiler → Knowledge articles
                                                                   ↓
                                                        Query engine ← User questions
```

**Three hooks run automatically:**

| Hook | When | What it does |
|------|------|-------------|
| `SessionStart` | Session opens | Injects vault knowledge index + recent daily log into context |
| `SessionEnd` | Session closes | Extracts conversation transcript, spawns flush agent |
| `PreCompact` | Before auto-compaction | Same as SessionEnd — captures context before it's compressed |

**Flush agent** (Haiku) analyzes the transcript and extracts:
- Files modified and why
- Decisions made
- New knowledge discovered
- Action items

Results are appended to today's daily log in the vault.

**Compiler** (end-of-day) reads daily logs and produces structured wiki articles with cross-references.

**Query engine** reads the index, picks relevant articles, and synthesizes answers.

## Installation

```bash
/plugin marketplace add kraiStudio/claude-memory
/plugin install claude-memory@claude-memory
```

Or for development:

```bash
claude --plugin-dir /path/to/claude-memory
```

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Code

## Setup

After installing, run:

```
/memory-init
```

The wizard will ask:
1. Where to store your vault (default: `~/Documents/Vaults/memory`)
2. Use globally or for the current project only
3. Confirm your timezone

That's it. Memory starts capturing from the next session.

### Adding more projects

When you open a new project and want to connect it:

```
/memory-connect
```

Options:
- Connect to an existing vault (shared knowledge)
- Create a new vault (isolated knowledge)

### Example configurations

**Single vault for everything:**
```yaml
# ~/.config/claude-memory/config.yaml
timezone: Europe/Moscow
compile_after_hour: 18
default_vault: memory

vaults:
  memory:
    path: ~/Documents/Vaults/memory
```

**Work + Personal separation:**
```yaml
timezone: Europe/Moscow
compile_after_hour: 18
default_vault: work

vaults:
  work:
    path: ~/Documents/Vaults/work
  personal:
    path: ~/Documents/Vaults/personal

projects:
  ~/Documents/Personal: personal
```

**Multiple projects sharing a vault:**
```yaml
timezone: America/New_York
compile_after_hour: 18
default_vault: work

vaults:
  work:
    path: ~/Documents/Vaults/work
  side-project:
    path: ~/Documents/Vaults/side-project

projects:
  ~/Documents/Dev/my-app: side-project
  ~/Documents/Dev/my-api: side-project
```

## Commands

| Command | What it does |
|---------|-------------|
| `/memory-init` | First-time setup wizard |
| `/memory-connect` | Connect current project to a vault |
| `/memory` | Query the knowledge base or show status |
| `/memory compile` | Manually trigger knowledge compilation |

## Vault structure

```
~/Documents/Vaults/work/
├── daily/
│   ├── 2026-04-15.md          # Auto-generated daily logs
│   └── ...
└── knowledge/
    ├── index.md               # Knowledge base index
    ├── log.md                 # Compilation log
    ├── concepts/              # Concept articles
    ├── connections/           # Cross-concept relationship articles
    └── qa/                    # Filed Q&A articles
```

Vaults are Obsidian-compatible — open them as vaults for browsing and editing.

## Plugin structure

```
claude-memory/
├── .claude-plugin/
│   ├── plugin.json            # Plugin manifest
│   └── marketplace.json       # Marketplace index
├── hooks/
│   ├── hooks.json             # Hook declarations
│   ├── session-start.py       # Context injection
│   ├── session-end.py         # Transcript extraction + flush
│   └── pre-compact.py         # Pre-compaction flush
├── scripts/
│   ├── flush.py               # LLM extraction agent (Haiku)
│   ├── compile.py             # Knowledge compiler
│   ├── query.py               # Index-guided query engine
│   ├── config.py              # Central configuration
│   ├── resolve_vault.py       # Vault resolution
│   └── utils.py               # Wiki utilities
├── skills/
│   └── memory-query/SKILL.md  # Auto-activated query skill
├── commands/
│   ├── memory-init.md         # /memory-init setup wizard
│   ├── memory-connect.md      # /memory-connect project binding
│   └── memory.md              # /memory query and status
└── pyproject.toml
```

## Design decisions

- **No RAG** — index-guided retrieval. The LLM reads the index, picks articles, synthesizes. Simple, transparent, no infrastructure.
- **Haiku for extraction** — cheap (~$0.01/flush), follows instructions well, sufficient for summarization.
- **Echo detection** — if the flush agent echoes the conversation instead of extracting, the response is discarded and logged as `FLUSH_ECHO`.
- **Offset tracking** — each flush processes only new transcript lines since the last flush.
- **XML-wrapped context** — conversation transcript is wrapped in `<conversation_transcript>` tags to prevent the extraction agent from confusing input data with instructions.
- **Config over convention** — all settings in `~/.config/claude-memory/config.yaml`. No manual file editing required — managed by `/memory-init` and `/memory-connect`.

## License

MIT
