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

Three hooks run automatically:

| Hook | When | What it does |
|------|------|-------------|
| SessionStart | Session opens | Injects knowledge index + recent log into context |
| SessionEnd | Session closes | Extracts transcript, spawns flush agent |
| PreCompact | Before compaction | Captures context before compression |

## Installation

```bash
/plugin marketplace add kraiStudio/claude-memory
/plugin install claude-memory@claude-memory --scope user
```

> **First run** may take 10-20 seconds while `uv` installs Python dependencies. Subsequent sessions start instantly.

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Code

## Setup

After installing, run:

```
/memory
```

The wizard will ask where to store your vault, detect your timezone, and set everything up. One command for everything:

| State | What `/memory` does |
|-------|-------------------|
| First run | Setup wizard — creates vault and config |
| New project | Connect wizard — link to existing vault or create new |
| Configured | Show status or query the knowledge base |

### Example: query

```
/memory What auth approach did we decide on?
```

### Example: compile

```
/memory compile
```

## Two memory modes

**Personal memory** — your private knowledge vault outside the project:

```
~/Documents/Vaults/work/
├── daily/              # session logs
├── knowledge/          # compiled articles
│   ├── index.md
│   ├── concepts/
│   ├── connections/
│   └── qa/
└── raw/                # files for manual compilation
```

**Project memory** — shared team knowledge inside the repo:

```
project/.memory/
├── knowledge/          # articles (no daily logs)
│   ├── index.md
│   ├── concepts/
│   ├── connections/
│   └── qa/
└── raw/
```

Mode is determined automatically: `.memory/` in project → project mode. Otherwise → personal mode.

Vaults are Obsidian-compatible — only markdown files, no technical clutter. State files are stored in `~/.config/claude-memory/`.

## Configuration

All config lives in `~/.config/claude-memory/config.yaml`, managed by `/memory`:

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
  ~/Documents/Dev/Creative Lab: creative-lab
```

## Design decisions

- **No RAG** — index-guided retrieval. Simple, transparent, no infrastructure.
- **Haiku for extraction** — cheap (~$0.01/flush), sufficient for summarization.
- **Opus for compilation** — higher quality for structured knowledge articles.
- **Echo detection** — discards responses where the agent echoes conversation instead of extracting.
- **Offset tracking** — each flush processes only new transcript lines.
- **Obsidian-first** — vaults contain only markdown. Technical files stored separately.

## License

MIT
