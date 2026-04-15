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
- Claude Code with Agent SDK

### Post-install setup

1. Create a vault directory:

```bash
mkdir -p ~/Documents/Vaults/work/{daily,knowledge/{concepts,connections,qa}}
```

2. Add `CLAUDE.local.md` to your project root:

```markdown
memory_vault: ~/Documents/Vaults/work
```

3. Create `.env` in the plugin directory:

```
TIMEZONE=Europe/Moscow
COMPILE_AFTER_HOUR=18
```

## Vault structure

```
~/Documents/Vaults/work/
├── daily/
│   ├── 2026-04-15.md          # Auto-generated daily logs
│   └── ...
└── knowledge/
    ├── index.md               # Knowledge base index (auto-maintained)
    ├── log.md                 # Compilation log
    ├── concepts/              # Concept articles
    ├── connections/           # Cross-concept relationship articles
    └── qa/                    # Filed Q&A articles
```

Vaults are Obsidian-compatible — open them as vaults for browsing and editing.

## Commands

### /memory

```
/memory <question>     — query the knowledge base
/memory compile        — compile daily logs into knowledge articles
/memory status         — show vault stats
```

## Multi-vault support

Each project can point to its own vault via `CLAUDE.local.md`:

```markdown
memory_vault: ~/Documents/Vaults/creative-lab
```

If no `CLAUDE.local.md` is found, defaults to `~/Documents/Vaults/work`.

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
│   ├── config.py              # Path configuration
│   ├── resolve_vault.py       # Vault resolution from CLAUDE.local.md
│   └── utils.py               # Wiki utilities
├── skills/
│   └── memory-query/SKILL.md  # Auto-activated query skill
├── commands/
│   └── memory.md              # /memory command
└── pyproject.toml
```

## Key design decisions

- **No RAG** — index-guided retrieval. The LLM reads the index, picks articles, synthesizes. Simple, transparent, no infrastructure.
- **Haiku for extraction** — cheap (~$0.01/flush), follows instructions well, sufficient for summarization.
- **Echo detection** — if the flush agent echoes the conversation instead of extracting, the response is discarded and logged as `FLUSH_ECHO`.
- **Offset tracking** — each flush processes only new transcript lines since the last flush (vault-local state keys).
- **XML-wrapped context** — conversation transcript is wrapped in `<conversation_transcript>` tags to prevent the extraction agent from confusing input data with instructions.

## License

MIT
