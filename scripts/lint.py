"""
Knowledge base health checks — structural and semantic validation.

7 checks:
1. Broken wikilinks — link points to non-existent article (error)
2. Orphan pages — article not referenced by any other article (warning)
3. Uncompiled sources — daily log not yet compiled (warning)
4. Stale articles — source changed after compilation (warning)
5. Missing backlinks — A→B exists but B→A doesn't (suggestion, auto-fixable)
6. Sparse articles — fewer than 200 words (suggestion)
7. Contradictions — LLM detects conflicting claims (optional, costs money)

Usage:
    uv run python lint.py --vault ~/Documents/Vaults/work
    uv run python lint.py --vault ~/Documents/Vaults/work --structural-only
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
from config import now_iso

ROOT_DIR = Path(__file__).resolve().parent.parent

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_SUGGESTION = "suggestion"


class Finding:
    def __init__(self, check: str, severity: str, message: str, file: str = "", auto_fixable: bool = False):
        self.check = check
        self.severity = severity
        self.message = message
        self.file = file
        self.auto_fixable = auto_fixable

    def __str__(self):
        prefix = {"error": "❌", "warning": "⚠️", "suggestion": "💡"}.get(self.severity, "•")
        fix = " (auto-fixable)" if self.auto_fixable else ""
        loc = f" in `{self.file}`" if self.file else ""
        return f"{prefix} [{self.check}]{loc}: {self.message}{fix}"


def check_broken_links() -> list[Finding]:
    """Check for wikilinks pointing to non-existent articles."""
    from utils import extract_wikilinks, list_wiki_articles, wiki_article_exists
    from config import KNOWLEDGE_DIR

    findings = []
    for article in list_wiki_articles():
        content = article.read_text(encoding="utf-8")
        links = extract_wikilinks(content)
        rel = str(article.relative_to(KNOWLEDGE_DIR))
        for link in links:
            if link.startswith("daily/"):
                continue
            if not wiki_article_exists(link):
                findings.append(Finding(
                    "broken-link", SEVERITY_ERROR,
                    f"[[{link}]] does not exist",
                    file=rel,
                ))
    return findings


def check_orphan_pages() -> list[Finding]:
    """Find articles with zero inbound references."""
    from utils import count_inbound_links, list_wiki_articles
    from config import KNOWLEDGE_DIR

    findings = []
    for article in list_wiki_articles():
        rel = str(article.relative_to(KNOWLEDGE_DIR)).replace(".md", "")
        inbound = count_inbound_links(rel, exclude_file=article)
        if inbound == 0:
            findings.append(Finding(
                "orphan", SEVERITY_WARNING,
                f"No other articles link to this page",
                file=f"{rel}.md",
            ))
    return findings


def check_uncompiled_sources() -> list[Finding]:
    """Check for daily logs not yet compiled."""
    from utils import file_hash, load_state
    from config import DAILY_DIR

    if not DAILY_DIR.exists():
        return []

    state = load_state()
    ingested = state.get("ingested", {})
    findings = []

    for log_path in sorted(DAILY_DIR.glob("*.md")):
        prev = ingested.get(log_path.name, {})
        if not prev:
            findings.append(Finding(
                "uncompiled", SEVERITY_WARNING,
                f"Daily log not compiled",
                file=f"daily/{log_path.name}",
            ))
    return findings


def check_stale_articles() -> list[Finding]:
    """Check for source files that changed after compilation."""
    from utils import file_hash, load_state
    from config import DAILY_DIR

    if not DAILY_DIR.exists():
        return []

    state = load_state()
    ingested = state.get("ingested", {})
    findings = []

    for log_path in sorted(DAILY_DIR.glob("*.md")):
        prev = ingested.get(log_path.name, {})
        if prev:
            current_hash = file_hash(log_path)
            if prev.get("hash") != current_hash:
                findings.append(Finding(
                    "stale", SEVERITY_WARNING,
                    f"Source changed after compilation (hash mismatch)",
                    file=f"daily/{log_path.name}",
                ))
    return findings


def check_missing_backlinks() -> list[Finding]:
    """Find asymmetric links: A→B but not B→A."""
    from utils import extract_wikilinks, list_wiki_articles, wiki_article_exists
    from config import KNOWLEDGE_DIR

    findings = []
    for article in list_wiki_articles():
        content = article.read_text(encoding="utf-8")
        links = extract_wikilinks(content)
        rel_self = str(article.relative_to(KNOWLEDGE_DIR)).replace(".md", "")

        for link in links:
            if link.startswith("daily/"):
                continue
            target_path = KNOWLEDGE_DIR / f"{link}.md"
            if not target_path.exists():
                continue
            target_content = target_path.read_text(encoding="utf-8")
            target_links = extract_wikilinks(target_content)
            if rel_self not in target_links:
                findings.append(Finding(
                    "no-backlink", SEVERITY_SUGGESTION,
                    f"Links to [[{link}]] but [[{link}]] doesn't link back",
                    file=f"{rel_self}.md",
                    auto_fixable=True,
                ))
    return findings


def check_sparse_articles() -> list[Finding]:
    """Find articles with fewer than 200 words."""
    from utils import get_article_word_count, list_wiki_articles
    from config import KNOWLEDGE_DIR

    findings = []
    for article in list_wiki_articles():
        word_count = get_article_word_count(article)
        if word_count < 200:
            rel = str(article.relative_to(KNOWLEDGE_DIR))
            findings.append(Finding(
                "sparse", SEVERITY_SUGGESTION,
                f"Only {word_count} words (minimum recommended: 200)",
                file=rel,
            ))
    return findings


async def check_contradictions() -> list[Finding]:
    """Use LLM to detect conflicting claims across the knowledge base."""
    from utils import read_all_wiki_content
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    wiki_content = read_all_wiki_content()
    if len(wiki_content) < 500:
        return []

    prompt = f"""Analyze this knowledge base for contradictions — places where two articles
make conflicting claims or give inconsistent recommendations.

{wiki_content}

For each contradiction found, output exactly this format (one per line):
CONTRADICTION: [file1] vs [file2] - description of the conflict

If no contradictions found, respond with: NO_CONTRADICTIONS"""

    response = ""
    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                model="claude-haiku-4-5-20251001",
                cwd=str(ROOT_DIR),
                allowed_tools=[],
                max_turns=2,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response += block.text
    except Exception as e:
        return [Finding("contradiction-check", SEVERITY_WARNING, f"LLM check failed: {e}")]

    findings = []
    for line in response.strip().splitlines():
        line = line.strip()
        if line.startswith("CONTRADICTION:"):
            desc = line[len("CONTRADICTION:"):].strip()
            findings.append(Finding("contradiction", SEVERITY_ERROR, desc))

    return findings


def generate_report(findings: list[Finding], vault_path: Path) -> str:
    """Generate a markdown lint report."""
    from utils import list_wiki_articles
    from config import DAILY_DIR

    article_count = len(list_wiki_articles())
    daily_count = len(list(DAILY_DIR.glob("*.md"))) if DAILY_DIR.exists() else 0

    errors = [f for f in findings if f.severity == SEVERITY_ERROR]
    warnings = [f for f in findings if f.severity == SEVERITY_WARNING]
    suggestions = [f for f in findings if f.severity == SEVERITY_SUGGESTION]
    fixable = [f for f in findings if f.auto_fixable]

    lines = [
        f"# Lint Report: {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')}",
        f"\nVault: `{vault_path}`",
        f"Articles: {article_count} | Daily logs: {daily_count}",
        f"\n## Summary",
        f"- {len(errors)} errors",
        f"- {len(warnings)} warnings",
        f"- {len(suggestions)} suggestions",
        f"- {len(fixable)} auto-fixable",
    ]

    if errors:
        lines.append("\n## Errors")
        for f in errors:
            lines.append(f"- {f}")
    if warnings:
        lines.append("\n## Warnings")
        for f in warnings:
            lines.append(f"- {f}")
    if suggestions:
        lines.append("\n## Suggestions")
        for f in suggestions:
            lines.append(f"- {f}")

    if not findings:
        lines.append("\n✅ Knowledge base is healthy — no issues found.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Knowledge base health checks")
    parser.add_argument("--vault", type=str, required=True, help="Vault path")
    parser.add_argument("--structural-only", action="store_true", help="Skip LLM contradiction check")
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    config.set_vault(vault)

    for d in [vault / "knowledge" / "concepts", vault / "knowledge" / "connections", vault / "knowledge" / "qa"]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"Running lint on {vault}...")

    findings: list[Finding] = []

    # Structural checks (free, fast)
    findings.extend(check_broken_links())
    findings.extend(check_orphan_pages())
    findings.extend(check_uncompiled_sources())
    findings.extend(check_stale_articles())
    findings.extend(check_missing_backlinks())
    findings.extend(check_sparse_articles())

    # Semantic check (LLM, costs money)
    if not args.structural_only:
        print("Running contradiction check (LLM)...")
        findings.extend(asyncio.run(check_contradictions()))

    # Generate and save report
    report = generate_report(findings, vault)
    print(report)

    # Save report
    from config import CONFIG_DIR
    reports_dir = CONFIG_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / f"lint-{datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d')}.md"
    report_file.write_text(report, encoding="utf-8")
    print(f"\nReport saved: {report_file}")

    # Update state
    from utils import load_state, save_state
    state = load_state()
    state["last_lint"] = now_iso()
    save_state(state)

    # Exit code
    errors = [f for f in findings if f.severity == SEVERITY_ERROR]
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
