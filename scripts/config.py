"""Path constants and configuration for the vault-based memory system."""

import os
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DAILY_DIR = ROOT_DIR / "daily"
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"
CONNECTIONS_DIR = KNOWLEDGE_DIR / "connections"
QA_DIR = KNOWLEDGE_DIR / "qa"
SCRIPTS_DIR = ROOT_DIR / "scripts"
HOOKS_DIR = ROOT_DIR / "hooks"

INDEX_FILE = KNOWLEDGE_DIR / "index.md"
LOG_FILE = KNOWLEDGE_DIR / "log.md"
STATE_FILE = SCRIPTS_DIR / "state.json"

TIMEZONE = os.getenv("TIMEZONE", "UTC")


def set_vault(vault_path: Path) -> None:
    """Override paths to target a specific vault directory."""
    global DAILY_DIR, KNOWLEDGE_DIR, CONCEPTS_DIR, CONNECTIONS_DIR, QA_DIR, INDEX_FILE, LOG_FILE, STATE_FILE
    DAILY_DIR = vault_path / "daily"
    KNOWLEDGE_DIR = vault_path / "knowledge"
    CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"
    CONNECTIONS_DIR = KNOWLEDGE_DIR / "connections"
    QA_DIR = KNOWLEDGE_DIR / "qa"
    INDEX_FILE = KNOWLEDGE_DIR / "index.md"
    LOG_FILE = KNOWLEDGE_DIR / "log.md"
    STATE_FILE = KNOWLEDGE_DIR / "state.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def today_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
