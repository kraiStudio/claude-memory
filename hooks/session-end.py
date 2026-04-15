"""
SessionEnd hook — captures conversation transcript for memory extraction.

Resolves the vault, extracts conversation context, and spawns flush.py.
Skips gracefully if no vault is configured.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Recursion guard
if os.environ.get("CLAUDE_INVOKED_BY"):
    sys.exit(0)

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
STATE_FILE = SCRIPTS_DIR / "last-flush.json"

sys.path.insert(0, str(SCRIPTS_DIR))
from resolve_vault import resolve_vault

logging.basicConfig(
    filename=str(SCRIPTS_DIR / "flush.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [hook] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MAX_CONTEXT_CHARS = 50_000
MIN_TURNS_TO_FLUSH = 1


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def extract_conversation_context(
    transcript_path: Path, skip_lines: int = 0
) -> tuple[str, int, int]:
    turns: list[str] = []
    line_number = 0

    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line_number += 1
            if line_number <= skip_lines:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg = entry.get("message", {})
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
            else:
                role = entry.get("role", "")
                content = entry.get("content", "")

            if role not in ("user", "assistant"):
                continue

            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        btype = block.get("type", "")
                        if btype == "text":
                            text_parts.append(block.get("text", ""))
                        elif btype == "tool_use":
                            tool_name = block.get("name", "unknown")
                            tool_input = block.get("input", {})
                            summary_parts = [f"[Tool: {tool_name}"]
                            if isinstance(tool_input, dict):
                                for key in ("file_path", "command", "pattern", "database", "content", "old_string", "new_string"):
                                    if key in tool_input:
                                        val = str(tool_input[key])[:200]
                                        summary_parts.append(f" {key}={val}")
                            text_parts.append("".join(summary_parts) + "]")
                        elif btype == "tool_result":
                            result_content = block.get("content", "")
                            if isinstance(result_content, list):
                                result_text = " ".join(r.get("text", "") for r in result_content if isinstance(r, dict))
                            else:
                                result_text = str(result_content)
                            if result_text.strip():
                                text_parts.append(f"[Result: {result_text[:300].strip()}]")
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)

            if isinstance(content, str) and content.strip():
                label = "User" if role == "user" else "Assistant"
                turns.append(f"**{label}:** {content.strip()}\n")

    context = "\n".join(turns)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[-MAX_CONTEXT_CHARS:]
        boundary = context.find("\n**")
        if boundary > 0:
            context = context[boundary + 1:]

    return context, len(turns), line_number


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        try:
            hook_input: dict = json.loads(raw_input)
        except json.JSONDecodeError:
            fixed_input = re.sub(r'(?<!\\)\\(?!["\\])', r'\\\\', raw_input)
            hook_input = json.loads(fixed_input)
    except (json.JSONDecodeError, ValueError, EOFError) as e:
        logging.error("Failed to parse stdin: %s", e)
        return

    session_id = hook_input.get("session_id", "unknown")
    source = hook_input.get("source", "unknown")
    transcript_path_str = hook_input.get("transcript_path", "")

    vault_info = resolve_vault()
    if vault_info is None:
        logging.info("SKIP: no vault configured for cwd=%s", os.environ.get("CLAUDE_CWD", os.getcwd()))
        return

    vault_path = vault_info.path
    vault_mode = vault_info.mode
    logging.info("SessionEnd fired: session=%s source=%s vault=%s mode=%s", session_id, source, vault_path, vault_mode)

    if not transcript_path_str or not isinstance(transcript_path_str, str):
        logging.info("SKIP: no transcript path")
        return

    transcript_path = Path(transcript_path_str)
    if not transcript_path.exists():
        logging.info("SKIP: transcript missing: %s", transcript_path_str)
        return

    state = load_state()
    state_key = f"{vault_path}:{session_id}"
    skip_lines = 0
    session_state = state.get(state_key, {})
    if session_state:
        skip_lines = session_state.get("lines_flushed", 0)
        logging.info("Resuming from line %d for %s", skip_lines, state_key)

    try:
        context, turn_count, total_lines = extract_conversation_context(transcript_path, skip_lines)
    except Exception as e:
        logging.error("Context extraction failed: %s", e)
        return

    if not context.strip():
        logging.info("SKIP: empty context (no new turns since line %d)", skip_lines)
        return

    if turn_count < MIN_TURNS_TO_FLUSH:
        logging.info("SKIP: only %d new turns (min %d)", turn_count, MIN_TURNS_TO_FLUSH)
        return

    state[state_key] = {
        "lines_flushed": total_lines,
        "timestamp": datetime.now(timezone.utc).timestamp(),
    }
    save_state(state)

    timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
    context_file = SCRIPTS_DIR / f"session-flush-{session_id}-{timestamp}.md"
    context_file.write_text(context, encoding="utf-8")

    flush_script = SCRIPTS_DIR / "flush.py"
    cmd = [
        "uv", "run", "--directory", str(ROOT),
        "python", str(flush_script), str(context_file), session_id, str(vault_path), vault_mode,
    ]

    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
        logging.info(
            "Spawned flush.py for session %s (lines %d-%d, %d turns, %d chars) -> %s",
            session_id, skip_lines, total_lines, turn_count, len(context), vault_path,
        )
    except Exception as e:
        logging.error("Failed to spawn flush.py: %s", e)


if __name__ == "__main__":
    main()
