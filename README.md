# unreal-python-mcp

MCP (Model Context Protocol) server for Unreal Python API documentation and execution.

Enables AI coding assistants like Claude Code to:
- Browse Unreal Python API documentation
- Search for classes and functions
- Execute Python code in Unreal Editor

## Installation

```bash
# Clone the repository
git clone https://github.com/self-taught-code-tokushima/unreal-python-mcp.git
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
| `list_modules` | List available Unreal modules |
| `exec_unreal_python` | Execute Python code in Unreal Editor |
| `list_unreal_instances` | List available Unreal Editor instances |
| `refresh_api_cache` | Refresh API documentation cache |

## Available Resources

### Hierarchical Index

Classes are organized by module to minimize context usage.

| Resource | Size | Description |
|----------|------|-------------|
| `unreal-python://index/summary` | ~2KB | **Start here.** API overview with module list |
| `unreal-python://index/module/{name}` | ~20-90KB | Classes for a specific module |
| `unreal-python://index/enums` | ~50KB | All enums |
| `unreal-python://index/structs` | ~200KB | All structs |
| `unreal-python://index/delegates` | ~10KB | All delegates |

Common modules:
- `Engine` (994 classes): Core classes - Actor, World, GameplayStatics
- `UnrealEd` (204 classes): Editor utilities - EditorAssetLibrary
- `UMG` (110 classes): UI/Widget classes
- `Niagara` (98 classes): Particle system

### Class Documentation

| Resource | Description |
|----------|-------------|
| `unreal-python://class/{name}` | Detailed class documentation |

## Usage Example

In Claude Code:

```
User: Actor クラスの位置を取得するメソッドを教えて

Claude: [Reads unreal-python://index/summary]
        → Engine モジュールに Actor があることを確認

        [Reads unreal-python://index/module/Engine]
        → Actor: 145 methods, 48 properties

        [Uses get_unreal_class("Actor")]
        → 詳細ドキュメントを取得

        Actor の位置を取得するには get_actor_location() を使います。
        返り値は Vector 型です。
```

```
User: EditorAssetLibrary の使い方を教えて

Claude: [Reads unreal-python://index/summary]
        → UnrealEd モジュールにあることを確認

        [Reads unreal-python://index/module/UnrealEd]
        [Uses get_unreal_class("EditorAssetLibrary")]

        EditorAssetLibrary はエディタ専用のアセット操作ユーティリティです...
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
