"""Resolve the vault path from CLAUDE.local.md in the working directory."""

import os
from pathlib import Path

DEFAULT_VAULT = Path.home() / "Documents" / "Vaults" / "work"


def resolve_vault(cwd: str | Path | None = None) -> Path:
    """Find memory_vault path from CLAUDE.local.md, fall back to default work vault."""
    if cwd is None:
        cwd = os.environ.get("CLAUDE_CWD", os.getcwd())

    cwd = Path(cwd)

    # Walk up from cwd looking for CLAUDE.local.md with memory_vault
    search_dir = cwd
    for _ in range(10):
        for name in ["CLAUDE.local.md", ".claude/CLAUDE.local.md"]:
            local_md = search_dir / name
            if local_md.exists():
                for line in local_md.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped.startswith("memory_vault:"):
                        vault_path = stripped.split(":", 1)[1].split("#")[0].strip()
                        vault_path = Path(vault_path).expanduser().resolve()
                        if vault_path.exists():
                            return vault_path
        parent = search_dir.parent
        if parent == search_dir:
            break
        search_dir = parent

    DEFAULT_VAULT.mkdir(parents=True, exist_ok=True)
    return DEFAULT_VAULT
