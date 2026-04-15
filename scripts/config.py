"""Central configuration — reads from ~/.config/claude-memory/config.yaml."""

import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

CONFIG_DIR = Path.home() / ".config" / "claude-memory"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"


def load_config() -> dict:
    """Load global config from ~/.config/claude-memory/config.yaml."""
    if CONFIG_FILE.exists():
        try:
            return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save config to ~/.config/claude-memory/config.yaml."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(yaml.dump(config, default_flow_style=False, allow_unicode=True), encoding="utf-8")


def config_exists() -> bool:
    return CONFIG_FILE.exists()


_config = load_config()

TIMEZONE = os.getenv("TIMEZONE", _config.get("timezone", "UTC"))
COMPILE_AFTER_HOUR = int(os.getenv("COMPILE_AFTER_HOUR", str(_config.get("compile_after_hour", 18))))


# ── Vault path helpers (set dynamically per-session) ─────────────────

DAILY_DIR = ROOT_DIR / "daily"
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"
CONNECTIONS_DIR = KNOWLEDGE_DIR / "connections"
QA_DIR = KNOWLEDGE_DIR / "qa"
INDEX_FILE = KNOWLEDGE_DIR / "index.md"
LOG_FILE = KNOWLEDGE_DIR / "log.md"
STATE_FILE = SCRIPTS_DIR / "state.json"


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
