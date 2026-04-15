"""
SessionStart hook — injects knowledge base context from the resolved vault.

If no config exists → prompts /memory-init.
If config exists but no vault for this project → works with default or prompts /memory-connect.
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


def build_context(vault_path: Path) -> str:
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


def maybe_trigger_compilation(vault_path: Path) -> None:
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
                try:
                    sp.Popen(
                        ["uv", "run", "--directory", str(ROOT), "python", str(compile_script), "--vault", str(vault_path)],
                        stdout=sp.DEVNULL, stderr=sp.DEVNULL,
                    )
                except Exception:
                    pass
            return


def main():
    if not config_exists():
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "## Claude Memory\n\nPlugin installed but not configured. Run `/memory-init` to set up your knowledge vault.",
            }
        }
        print(json.dumps(output))
        return

    vault_path = resolve_vault()

    if vault_path is None:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "## Claude Memory\n\nNo vault configured for this project. Run `/memory-connect` to connect it, or it will use the default vault.",
            }
        }
        print(json.dumps(output))
        return

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
