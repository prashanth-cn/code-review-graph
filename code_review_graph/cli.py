"""CLI entry point for code-review-graph.

Usage:
    code-review-graph install
    code-review-graph init
    code-review-graph build [--base BASE]
    code-review-graph update [--base BASE]
    code-review-graph watch
    code-review-graph status
    code-review-graph serve
    code-review-graph visualize
"""

from __future__ import annotations

import sys

# Python version check — must come before any other imports
if sys.version_info < (3, 10):
    print("code-review-graph requires Python 3.10 or higher.")
    print(f"  You are running Python {sys.version}")
    print()
    print("Install Python 3.10+: https://www.python.org/downloads/")
    sys.exit(1)

import argparse
import json
import logging
import os
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Optional


def _get_version() -> str:
    """Get the installed package version."""
    try:
        return pkg_version("code-review-graph")
    except Exception:
        return "dev"


def _supports_color() -> bool:
    """Check if the terminal likely supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


def _print_banner() -> None:
    """Print the startup banner with graph art and available commands."""
    color = _supports_color()
    version = _get_version()

    # ANSI escape codes
    c = "\033[36m" if color else ""  # cyan — graph art
    y = "\033[33m" if color else ""  # yellow — center node
    b = "\033[1m" if color else ""  # bold
    d = "\033[2m" if color else ""  # dim
    g = "\033[32m" if color else ""  # green — commands
    r = "\033[0m" if color else ""  # reset

    print(f"""
{c}  ●──●──●{r}
{c}  │╲ │ ╱│{r}       {b}code-review-graph{r}  {d}v{version}{r}
{c}  ●──{y}◆{c}──●{r}
{c}  │╱ │ ╲│{r}       {d}Structural knowledge graph for{r}
{c}  ●──●──●{r}       {d}smarter code reviews{r}

  {b}Commands:{r}
    {g}install{r}     Set up MCP for Claude/Gemini/Cursor/OpenCode
    {g}init{r}        Alias for install
    {g}build{r}       Full graph build {d}(parse all files){r}
    {g}update{r}      Incremental update {d}(changed files only){r}
    {g}watch{r}       Auto-update on file changes
    {g}status{r}      Show graph statistics
    {g}visualize{r}   Generate interactive HTML graph
    {g}serve{r}       Start MCP server

  {d}Run{r} {b}code-review-graph <command> --help{r} {d}for details{r}
""")


def _get_mcp_config(with_repo: bool = False, repo_path: Optional[str] = None) -> dict:
    """Build the MCP server configuration."""
    args = ["code-review-graph", "serve"]
    if with_repo and repo_path:
        args.extend(["--repo", repo_path])
    return {
        "mcpServers": {
            "code-review-graph": {
                "command": "uvx",
                "args": args,
            }
        }
    }


def _handle_init(args: argparse.Namespace) -> None:
    """Set up MCP server configurations for supported AI tools."""
    from .incremental import find_repo_root

    repo_root = Path(args.repo) if args.repo else find_repo_root()
    if not repo_root:
        repo_root = Path.cwd()

    dry_run = getattr(args, "dry_run", False)
    repo_path = str(repo_root)

    tools = []
    if args.all:
        tools = ["claude", "gemini", "antigravity", "cursor", "opencode"]
    else:
        if args.claude:
            tools.append("claude")
        if args.gemini:
            tools.append("gemini")
        if args.antigravity:
            tools.append("antigravity")
        if args.cursor:
            tools.append("cursor")
        if args.opencode:
            tools.append("opencode")

    if not tools:
        tools = ["claude"]

    for tool in tools:
        if tool == "claude":
            result = _install_claude_code(repo_root, dry_run, repo_path)
        elif tool == "gemini":
            result = _install_gemini_cli(dry_run, repo_path)
        elif tool == "antigravity":
            result = _install_antigravity(repo_root, dry_run, repo_path)
        elif tool == "cursor":
            result = _install_cursor(dry_run, repo_path)
        elif tool == "opencode":
            result = _install_opencode(dry_run, repo_path)
        else:
            result = f"Unknown tool: {tool}"
        print(result)

    print()
    if not dry_run:
        print("Next steps:")
        print("  1. code-review-graph build    # build the knowledge graph")
        print("  2. Restart your AI tool      # to pick up the new MCP server")


def _install_claude_code(repo_root: Path, dry_run: bool, repo_path: str) -> str:
    """Install for Claude Code."""
    mcp_path = repo_root / ".mcp.json"
    mcp_config = _get_mcp_config(with_repo=False, repo_path=repo_path)

    if mcp_path.exists():
        try:
            existing = json.loads(mcp_path.read_text())
            if "code-review-graph" in existing.get("mcpServers", {}):
                return f"Claude Code: Already configured in {mcp_path}"
            existing.setdefault("mcpServers", {}).update(mcp_config["mcpServers"])
            mcp_config = existing
        except (json.JSONDecodeError, KeyError):
            pass

    if dry_run:
        print(f"[dry-run] Would write to {mcp_path}:")
        print(json.dumps(mcp_config, indent=2))
        return f"[dry-run] Claude Code: Would create {mcp_path}"

    mcp_path.write_text(json.dumps(mcp_config, indent=2) + "\n")
    return f"Claude Code: Created {mcp_path}"


def _install_gemini_cli(dry_run: bool, repo_path: str) -> str:
    """Install for Gemini CLI."""
    gemini_dir = Path.home() / ".gemini"
    settings_path = gemini_dir / "settings.json"
    mcp_config = _get_mcp_config(with_repo=True, repo_path=repo_path)

    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text())
            if "code-review-graph" in existing.get("mcpServers", {}):
                return f"Gemini CLI: Already configured in {settings_path}"
            existing.setdefault("mcpServers", {}).update(mcp_config["mcpServers"])
            mcp_config = existing
        except (json.JSONDecodeError, KeyError):
            pass

    if dry_run:
        print(f"[dry-run] Would write to {settings_path}:")
        print(json.dumps(mcp_config, indent=2))
        return f"[dry-run] Gemini CLI: Would create {settings_path}"

    gemini_dir.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(mcp_config, indent=2) + "\n")
    return f"Gemini CLI: Created {settings_path}"


def _install_antigravity(repo_root: Path, dry_run: bool, repo_path: str) -> str:
    """Install for Antigravity."""
    mcp_path = repo_root / ".vscode" / "mcp.json"
    mcp_config = _get_mcp_config(with_repo=True, repo_path=repo_path)

    if mcp_path.exists():
        try:
            existing = json.loads(mcp_path.read_text())
            if "code-review-graph" in existing.get("mcpServers", {}):
                return f"Antigravity: Already configured in {mcp_path}"
            existing.setdefault("mcpServers", {}).update(mcp_config["mcpServers"])
            mcp_config = existing
        except (json.JSONDecodeError, KeyError):
            pass

    if dry_run:
        print(f"[dry-run] Would write to {mcp_path}:")
        print(json.dumps(mcp_config, indent=2))
        return f"[dry-run] Antigravity: Would create {mcp_path}"

    (repo_root / ".vscode").mkdir(parents=True, exist_ok=True)
    mcp_path.write_text(json.dumps(mcp_config, indent=2) + "\n")
    return f"Antigravity: Created {mcp_path}"


def _install_cursor(dry_run: bool, repo_path: str) -> str:
    """Install for Cursor/Windsurf (uses Cursor config)."""
    cursor_dir = Path.home() / ".cursor"
    cursor_path = cursor_dir / "mcp.json"
    mcp_config = _get_mcp_config(with_repo=True, repo_path=repo_path)

    if cursor_path.exists():
        try:
            existing = json.loads(cursor_path.read_text())
            if "code-review-graph" in existing.get("mcpServers", {}):
                return f"Cursor/Windsurf: Already configured in {cursor_path}"
            existing.setdefault("mcpServers", {}).update(mcp_config["mcpServers"])
            mcp_config = existing
        except (json.JSONDecodeError, KeyError):
            pass

    if dry_run:
        print(f"[dry-run] Would write to {cursor_path}:")
        print(json.dumps(mcp_config, indent=2))
        return f"[dry-run] Cursor/Windsurf: Would create {cursor_path}"

    cursor_dir.mkdir(parents=True, exist_ok=True)
    cursor_path.write_text(json.dumps(mcp_config, indent=2) + "\n")
    return f"Cursor/Windsurf: Created {cursor_path}"


def _install_opencode(dry_run: bool, repo_path: str) -> str:
    """Install for OpenCode."""
    opencode_dir = Path.home() / ".config" / "opencode"
    config_path = opencode_dir / "config.toml"

    toml_lines = []
    if config_path.exists():
        try:
            content = config_path.read_text()
            if "[mcp.servers.code-review-graph]" in content:
                return f"OpenCode: Already configured in {config_path}"
            toml_lines = content.strip().split("\n")
        except Exception:
            pass

    mcp_section = [
        "[mcp]",
        "enabled = true",
        "",
        "[mcp.servers.code-review-graph]",
        'command = "uvx"',
        f'args = ["code-review-graph", "serve", "--repo", "{repo_path}"]',
    ]

    if toml_lines:
        final_content = "\n".join(toml_lines + ["", "", ""] + mcp_section)
    else:
        final_content = "\n".join(mcp_section)

    if dry_run:
        print(f"[dry-run] Would write to {config_path}:")
        print(final_content)
        return f"[dry-run] OpenCode: Would create {config_path}"

    opencode_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(final_content + "\n")
    return f"OpenCode: Created {config_path}"


def main() -> None:
    """Main CLI entry point."""
    ap = argparse.ArgumentParser(
        prog="code-review-graph",
        description="Persistent incremental knowledge graph for code reviews",
    )
    ap.add_argument("-v", "--version", action="store_true", help="Show version and exit")
    sub = ap.add_subparsers(dest="command")

    # install (primary) + init (alias)
    install_cmd = sub.add_parser(
        "install", help="Register MCP server with AI tools (creates config files)"
    )
    install_cmd.add_argument("--repo", default=None, help="Repository root (auto-detected)")
    install_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files",
    )
    install_cmd.add_argument("--all", action="store_true", help="Install for all supported tools")
    install_cmd.add_argument("--claude", action="store_true", help="Install for Claude Code")
    install_cmd.add_argument("--gemini", action="store_true", help="Install for Gemini CLI")
    install_cmd.add_argument("--antigravity", action="store_true", help="Install for Antigravity")
    install_cmd.add_argument("--cursor", action="store_true", help="Install for Cursor / Windsurf")
    install_cmd.add_argument("--opencode", action="store_true", help="Install for OpenCode")

    init_cmd = sub.add_parser("init", help="Alias for install")
    init_cmd.add_argument("--repo", default=None, help="Repository root (auto-detected)")
    init_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files",
    )
    init_cmd.add_argument("--all", action="store_true", help="Install for all supported tools")
    init_cmd.add_argument("--claude", action="store_true", help="Install for Claude Code")
    init_cmd.add_argument("--gemini", action="store_true", help="Install for Gemini CLI")
    init_cmd.add_argument("--antigravity", action="store_true", help="Install for Antigravity")
    init_cmd.add_argument("--cursor", action="store_true", help="Install for Cursor / Windsurf")
    init_cmd.add_argument("--opencode", action="store_true", help="Install for OpenCode")

    # build
    build_cmd = sub.add_parser("build", help="Full graph build (re-parse all files)")
    build_cmd.add_argument("--repo", default=None, help="Repository root (auto-detected)")

    # update
    update_cmd = sub.add_parser("update", help="Incremental update (only changed files)")
    update_cmd.add_argument("--base", default="HEAD~1", help="Git diff base (default: HEAD~1)")
    update_cmd.add_argument("--repo", default=None, help="Repository root (auto-detected)")

    # watch
    watch_cmd = sub.add_parser("watch", help="Watch for changes and auto-update")
    watch_cmd.add_argument("--repo", default=None, help="Repository root (auto-detected)")

    # status
    status_cmd = sub.add_parser("status", help="Show graph statistics")
    status_cmd.add_argument("--repo", default=None, help="Repository root (auto-detected)")

    # visualize
    vis_cmd = sub.add_parser("visualize", help="Generate interactive HTML graph visualization")
    vis_cmd.add_argument("--repo", default=None, help="Repository root (auto-detected)")

    # serve
    sub.add_parser("serve", help="Start MCP server (stdio transport)")

    args = ap.parse_args()

    if args.version:
        print(f"code-review-graph {_get_version()}")
        return

    if not args.command:
        _print_banner()
        return

    if args.command == "serve":
        from .main import main as serve_main

        serve_main()
        return

    if args.command in ("init", "install"):
        _handle_init(args)
        return

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    from .graph import GraphStore
    from .incremental import (
        find_project_root,
        find_repo_root,
        full_build,
        get_db_path,
        incremental_update,
        watch,
    )

    if args.command == "update":
        # update requires git for diffing
        repo_root = Path(args.repo) if args.repo else find_repo_root()
        if not repo_root:
            logging.error("Not in a git repository. 'update' requires git for diffing.")
            logging.error("Use 'build' for a full parse, or run 'git init' first.")
            sys.exit(1)
    else:
        repo_root = Path(args.repo) if args.repo else find_project_root()

    db_path = get_db_path(repo_root)
    store = GraphStore(db_path)

    try:
        if args.command == "build":
            result = full_build(repo_root, store)
            print(
                f"Full build: {result['files_parsed']} files, "
                f"{result['total_nodes']} nodes, {result['total_edges']} edges"
            )
            if result["errors"]:
                print(f"Errors: {len(result['errors'])}")

        elif args.command == "update":
            result = incremental_update(repo_root, store, base=args.base)
            print(
                f"Incremental: {result['files_updated']} files updated, "
                f"{result['total_nodes']} nodes, {result['total_edges']} edges"
            )

        elif args.command == "status":
            stats = store.get_stats()
            print(f"Nodes: {stats.total_nodes}")
            print(f"Edges: {stats.total_edges}")
            print(f"Files: {stats.files_count}")
            print(f"Languages: {', '.join(stats.languages)}")
            print(f"Last updated: {stats.last_updated or 'never'}")

        elif args.command == "watch":
            watch(repo_root, store)

        elif args.command == "visualize":
            from .visualization import generate_html

            html_path = repo_root / ".code-review-graph" / "graph.html"
            generate_html(store, html_path)
            print(f"Visualization: {html_path}")
            print("Open in browser to explore your codebase graph.")

    finally:
        store.close()
