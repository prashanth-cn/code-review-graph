# Multi-Tool MCP Integration Guide

This document outlines how to integrate `code-review-graph` with various AI coding tools that support the Model Context Protocol (MCP).

## Supported Tools

| Tool | Config Location | Format | Status |
|------|----------------|--------|--------|
| Claude Code | `.mcp.json` (project) | JSON | ✅ Supported |
| Gemini CLI | `~/.gemini/settings.json` | JSON | ✅ Supported |
| Antigravity | `.vscode/mcp.json` (project) | JSON | ✅ Supported |
| Cursor | `.cursor/mcp.json` or `~/.cursor/mcp.json` | JSON | ✅ Supported |
| OpenCode | `~/.config/opencode/config.toml` | TOML | ✅ Supported |
| Windsurf | `.cursor/mcp.json` or `~/.cursor/mcp.json` | JSON | ✅ Supported (uses Cursor config) |

---

## Quick Install

### Install for All Tools

```bash
pip install code-review-graph
code-review-graph install --all
```

### Install for Specific Tools

```bash
# Claude Code (default)
code-review-graph install

# Gemini CLI
code-review-graph install --gemini

# Google Antigravity
code-review-graph install --antigravity

# Cursor / Windsurf
code-review-graph install --cursor

# OpenCode
code-review-graph install --opencode
```

---

## Manual Configuration

If you prefer to configure manually, follow the instructions for your specific tool below.

### Claude Code

**Project-level config** (recommended):

Create or update `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "code-review-graph": {
      "command": "uvx",
      "args": ["code-review-graph", "serve"]
    }
  }
}
```

Then restart Claude Code.

### Gemini CLI

**Global config**:

1. Open `~/.gemini/settings.json`
2. Add the `mcpServers` block:

```json
{
  "mcpServers": {
    "code-review-graph": {
      "command": "uvx",
      "args": ["code-review-graph", "serve"]
    }
  }
}
```

3. Restart Gemini CLI

### Antigravity

**Project-level config**:

Create `.vscode/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "code-review-graph": {
      "command": "uvx",
      "args": ["code-review-graph", "serve"]
    }
  }
}
```

**Note**: Use `${workspaceFolder}` in args if your tool needs the project path:

```json
{
  "mcpServers": {
    "code-review-graph": {
      "command": "uvx",
      "args": ["code-review-graph", "serve", "--repo", "${workspaceFolder}"]
    }
  }
}
```

### Cursor / Windsurf

**Global config** (applies to all projects):

Create or update `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "code-review-graph": {
      "command": "uvx",
      "args": ["code-review-graph", "serve"]
    }
  }
}
```

**Project-level config**:

Create `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "code-review-graph": {
      "command": "uvx",
      "args": ["code-review-graph", "serve"]
    }
  }
}
```

### OpenCode

**Global config**:

Create or update `~/.config/opencode/config.toml`:

```toml
[mcp]
enabled = true

[mcp.servers.code-review-graph]
command = "uvx"
args = ["code-review-graph", "serve"]
```

---

## Available Tools

Once installed, the following tools are available in your AI assistant:

| Tool | Description |
|------|-------------|
| `build_or_update_graph_tool` | Build or incrementally update the code knowledge graph |
| `get_impact_radius_tool` | Analyze the blast radius of changed files |
| `get_review_context_tool` | Generate token-optimized review context with structural summary |
| `query_graph_tool` | Query callers, callees, tests, imports, inheritance |
| `semantic_search_nodes_tool` | Search code entities by name or semantic similarity |
| `embed_graph_tool` | Compute vector embeddings for semantic search |
| `list_graph_stats_tool` | Get graph statistics (nodes, edges, languages) |
| `get_docs_section_tool` | Retrieve documentation sections |

---

## Usage After Installation

1. **Build the graph** (first time only):

   ```
   Build the code review graph for this project
   ```

2. **Review changes**:

   ```
   Review the changes since the last commit
   ```

3. **Query the graph**:

   ```
   Find all callers of the authenticate function
   ```

---

## Troubleshooting

### Graph not updating

Run manual update:

```bash
code-review-graph update
```

### Tools not appearing

- Restart the AI tool completely
- Verify the MCP server is running: `uvx code-review-graph serve`
- Check for errors in the tool's console/output

### Path issues

If the tool can't find your project, specify the repo explicitly:

```json
{
  "mcpServers": {
    "code-review-graph": {
      "command": "uvx",
      "args": ["code-review-graph", "serve", "--repo", "/path/to/your/project"]
    }
  }
}
```

---

## Security Notes

- The MCP server only reads files in the project directory
- No data is sent to external servers (except the LLM API)
- The graph database is stored locally in `.code-review-graph/graph.db`
- Review your tool's permission settings to control what the AI can access
