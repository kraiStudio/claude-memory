"""
SessionStart hook — injects knowledge base context from the resolved vault.

Determines which vault to use based on CLAUDE.local.md in the working directory,
then reads the vault's index and recent daily log into the conversation context.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from resolve_vault import resolve_vault

MAX_CONTEXT_CHARS = 20_000
MAX_LOG_LINES = 30


def get_recent_log(daily_dir: Path) -> str:
    """Read the most recent daily log (today or yesterday)."""
    today = datetime.now(timezone.utc).astimezone()

    for offset in range(2):
        date = today - timedelta(days=offset)
        log_path = daily_dir / f"{date.strftime('%Y-%m-%d')}.md"
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8").splitlines()
            recent = lines[-MAX_LOG_LINES:] if len(lines) > MAX_LOG_LINES else lines
            return "\n".join(recent)

    return "(no recent daily log)"


def build_context(vault_path: Path) -> str:
    """Assemble the context to inject into the conversation."""
    parts = []

    today = datetime.now(timezone.utc).astimezone()
    parts.append(f"## Today\n{today.strftime('%A, %B %d, %Y')}")

    parts.append(f"## Active Vault\n{vault_path}")

    knowledge_dir = vault_path / "knowledge"
    index_file = knowledge_dir / "index.md"
    if index_file.exists():
        index_content = index_file.read_text(encoding="utf-8")
        parts.append(f"## Knowledge Base Index\n\n{index_content}")

    daily_dir = vault_path / "daily"
    recent_log = get_recent_log(daily_dir)
    parts.append(f"## Recent Daily Log\n\n{recent_log}")

    context = "\n\n---\n\n".join(parts)

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n...(truncated)"

    return context


def maybe_trigger_compilation(vault_path: Path) -> None:
    """Spawn compile.py if the vault has uncompiled daily logs from past days."""
    import hashlib
    import subprocess as sp

    daily_dir = vault_path / "daily"
    if not daily_dir.exists():
        return

    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")

    state_file = vault_path / "knowledge" / "state.json"
    ingested = {}
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            ingested = data.get("ingested", {})
        except (json.JSONDecodeError, OSError):
            pass

    for log_path in sorted(daily_dir.glob("*.md")):
        if log_path.stem == today:
            continue
        current_hash = hashlib.sha256(log_path.read_bytes()).hexdigest()[:16]
        prev = ingested.get(log_path.name, {})
        if not prev or prev.get("hash") != current_hash:
            compile_script = ROOT / "scripts" / "compile.py"
            if compile_script.exists():
                cmd = [
                    "uv", "run", "--directory", str(ROOT),
                    "python", str(compile_script),
                    "--vault", str(vault_path),
                ]
                try:
                    sp.Popen(cmd, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
                except Exception:
                    pass
            return


def main():
    vault_path = resolve_vault()
    maybe_trigger_compilation(vault_path)
    context = build_context(vault_path)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
