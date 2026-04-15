"""Resolve the vault path for the current project.

Priority:
1. config.yaml projects map (longest prefix match on cwd)
2. config.yaml default_vault
3. CLAUDE.local.md memory_vault: line (backward compatibility)
4. None (no vault configured)
"""

import os
from pathlib import Path

from config import load_config


def resolve_vault(cwd: str | Path | None = None) -> Path | None:
    """Find the vault path for the current working directory.

    Returns None if no vault is configured (caller should prompt setup).
    """
    if cwd is None:
        cwd = os.environ.get("CLAUDE_CWD", os.getcwd())
    cwd = Path(cwd).resolve()

    config = load_config()

    if config:
        vaults = config.get("vaults", {})

        # 1. Check projects map — longest prefix match
        projects = config.get("projects", {})
        best_match = None
        best_len = 0
        for project_path, vault_name in projects.items():
            p = Path(project_path).expanduser().resolve()
            try:
                cwd.relative_to(p)
                if len(str(p)) > best_len:
                    best_match = vault_name
                    best_len = len(str(p))
            except ValueError:
                continue

        if best_match and best_match in vaults:
            vault_path = Path(vaults[best_match]["path"]).expanduser().resolve()
            if vault_path.exists():
                return vault_path

        # 2. Default vault
        default_name = config.get("default_vault")
        if default_name and default_name in vaults:
            vault_path = Path(vaults[default_name]["path"]).expanduser().resolve()
            if vault_path.exists():
                return vault_path

    # 3. Fallback: CLAUDE.local.md (backward compatibility)
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

    return None
