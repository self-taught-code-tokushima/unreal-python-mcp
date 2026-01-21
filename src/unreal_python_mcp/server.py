"""
MCP Server for Unreal Python API

Provides:
- Resources: llms-index (API documentation index), class docs
- Tools: search_unreal_api, exec_unreal_python
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from unreal_python_mcp import __version__
from unreal_python_mcp.cache import CacheManager
from unreal_python_mcp.unreal_connection import UnrealConnection

# Initialize MCP server
mcp = FastMCP("Unreal Python API")

# Global instances
_cache_manager: CacheManager | None = None
_unreal_connection: UnrealConnection | None = None


def get_cache_manager() -> CacheManager:
    """Get or create the cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_unreal_connection() -> UnrealConnection:
    """Get or create the Unreal connection instance."""
    global _unreal_connection
    if _unreal_connection is None:
        _unreal_connection = UnrealConnection()
    return _unreal_connection


# ============================================================================
# Resources
# ============================================================================

@mcp.resource("unreal-python://llms-index")
def get_llms_index() -> str:
    """
    Complete Unreal Python API index in llms.txt format.

    You MUST read this resource first to find the correct class/function name,
    then use get_unreal_class tool or read unreal-python://class/{name} resource
    to get detailed documentation.
    """
    cache = get_cache_manager()
    return cache.get_llms_index()


@mcp.resource("unreal-python://class/{name}")
def get_class_resource(name: str) -> str:
    """
    Get detailed documentation for a specific Unreal Python class.

    Args:
        name: The class name (e.g., "Actor", "EditorAssetLibrary")
    """
    cache = get_cache_manager()
    doc = cache.get_class_doc(name)
    if doc:
        return json.dumps(doc, indent=2)
    return json.dumps({"error": f"Class '{name}' not found"})


# ============================================================================
# Tools
# ============================================================================

@mcp.tool()
def search_unreal_api(query: str) -> str:
    """
    Search Unreal Python API by class or function name.

    Returns matching entries from the API index. Use this to find
    the correct class/function name before getting detailed documentation.

    Args:
        query: Search query (supports partial matching and regex)
    """
    cache = get_cache_manager()
    results = cache.search_api(query)
    if not results:
        return f"No results found for '{query}'"
    return "\n".join(results)


@mcp.tool()
def get_unreal_class(class_name: str) -> str:
    """
    Get detailed documentation for a specific Unreal Python class.

    Returns the class documentation including methods, properties,
    inheritance information, and docstrings.

    Args:
        class_name: The exact class name (e.g., "Actor", "EditorAssetLibrary")
    """
    cache = get_cache_manager()
    doc = cache.get_class_doc(class_name)
    if doc:
        return json.dumps(doc, indent=2)
    return json.dumps({"error": f"Class '{class_name}' not found. Use search_unreal_api to find the correct name."})


@mcp.tool()
def exec_unreal_python(code: str) -> str:
    """
    Execute Python code in the running Unreal Editor.

    Requires Unreal Editor to be running with Python Remote Execution enabled.
    Check Editor Preferences > Plugins > Python > Enable Remote Execution.

    Args:
        code: Python code to execute in Unreal Editor
    """
    conn = get_unreal_connection()
    return conn.execute(code)


@mcp.tool()
def list_unreal_instances() -> str:
    """
    List all running Unreal Editor instances with Remote Execution enabled.

    Use this to check if Unreal Editor is available for code execution.
    """
    conn = get_unreal_connection()
    return conn.list_instances()


@mcp.tool()
def refresh_api_cache() -> str:
    """
    Refresh the Unreal Python API documentation cache.

    This fetches the latest API documentation from a running Unreal Editor
    and updates the local cache. Requires Unreal Editor to be running.
    """
    cache = get_cache_manager()
    conn = get_unreal_connection()
    try:
        cache.refresh_from_unreal(conn)
        return "Cache refreshed successfully"
    except Exception as e:
        return f"Failed to refresh cache: {e}"


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
