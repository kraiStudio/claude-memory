"""
SessionStart hook — injects knowledge base context from the resolved vault.

Supports both personal mode (vault) and project mode (.memory/).
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from config import config_exists
from resolve_vault import resolve_vault

MAX_CONTEXT_CHARS = 20_000
MAX_LOG_LINES = 30


def get_recent_log(daily_dir: Path) -> str:
    today = datetime.now(timezone.utc).astimezone()
    for offset in range(2):
        date = today - timedelta(days=offset)
        log_path = daily_dir / f"{date.strftime('%Y-%m-%d')}.md"
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8").splitlines()
            recent = lines[-MAX_LOG_LINES:] if len(lines) > MAX_LOG_LINES else lines
            return "\n".join(recent)
    return ""


def build_context_personal(vault_path: Path) -> str:
    parts = []
    today = datetime.now(timezone.utc).astimezone()
    parts.append(f"## Today\n{today.strftime('%A, %B %d, %Y')}")
    parts.append(f"## Active Vault\n{vault_path}")

    index_file = vault_path / "knowledge" / "index.md"
    if index_file.exists():
        parts.append(f"## Knowledge Base Index\n\n{index_file.read_text(encoding='utf-8')}")

    daily_dir = vault_path / "daily"
    recent_log = get_recent_log(daily_dir)
    if recent_log:
        parts.append(f"## Recent Daily Log\n\n{recent_log}")

    context = "\n\n---\n\n".join(parts)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n...(truncated)"
    return context


def build_context_project(memory_dir: Path) -> str:
    parts = []
    today = datetime.now(timezone.utc).astimezone()
    parts.append(f"## Today\n{today.strftime('%A, %B %d, %Y')}")
    parts.append(f"## Project Memory\n{memory_dir}")

    index_file = memory_dir / "knowledge" / "index.md"
    if index_file.exists():
        parts.append(f"## Knowledge Base Index\n\n{index_file.read_text(encoding='utf-8')}")

    context = "\n\n---\n\n".join(parts)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n...(truncated)"
    return context


def main():
    vault_info = resolve_vault()

    # .memory/ found — always use it regardless of config
    if vault_info and vault_info.mode == "project":
        context = build_context_project(vault_info.path)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
        print(json.dumps(output))
        return

    if not config_exists():
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "## Claude Memory\n\nPlugin installed but not configured. Run `/memory` to set up your knowledge vault.",
            }
        }
        print(json.dumps(output))
        return

    if vault_info is None:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "## Claude Memory\n\nNo vault configured for this project. Run `/memory` to connect it.",
            }
        }
        print(json.dumps(output))
        return

    context = build_context_personal(vault_info.path)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
