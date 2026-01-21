# unreal-python-mcp

MCP (Model Context Protocol) server for Unreal Python API documentation and execution.

Enables AI coding assistants like Claude Code to:
- Browse Unreal Python API documentation
- Search for classes and functions
- Execute Python code in Unreal Editor

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/unreal-python-mcp.git
cd unreal-python-mcp

# Install with uv
uv sync
```

## Claude Code Setup

Add to your Claude Code MCP configuration (`~/.config/claude/mcp.json` or project-level `.mcp.json`):

```json
{
  "mcpServers": {
    "unreal-python": {
      "command": "uv",
      "args": ["--directory", "D:\\UnrealProjects\\unreal-python-mcp", "run", "unreal-python-mcp"]
    }
  }
}
```

## Requirements

- Python 3.13+
- Unreal Editor with Python plugin enabled
- "Enable Remote Execution" checked in Editor Preferences > Plugins > Python

## Available Tools

| Tool | Description |
|------|-------------|
| `search_unreal_api` | Search API by class/function name |
| `get_unreal_class` | Get detailed class documentation |
| `exec_unreal_python` | Execute Python code in Unreal Editor |
| `list_unreal_instances` | List available Unreal Editor instances |
| `refresh_api_cache` | Refresh API documentation cache |

## Available Resources

| Resource | Description |
|----------|-------------|
| `unreal-python://llms-index` | Complete API index (llms.txt format) |
| `unreal-python://class/{name}` | Detailed class documentation |

## Usage Example

In Claude Code:

```
User: Actor クラスの位置を取得するメソッドを教えて

Claude: [Uses search_unreal_api("Actor")]
        [Uses get_unreal_class("Actor")]

        Actor の位置を取得するには get_actor_location() を使います。
```

```
User: Unreal で Hello World を出力して

Claude: [Uses exec_unreal_python("print('Hello World')")]

        実行結果: Hello World
```

## First-time Setup

1. Start Unreal Editor with a project
2. Enable Python Remote Execution in Editor Preferences
3. Use `refresh_api_cache` tool to fetch and cache the API documentation

## Development

```bash
# Run MCP dev server (with inspector)
uv run mcp dev src/unreal_python_mcp/server.py

# Run directly
uv run unreal-python-mcp
```

## License

MIT
