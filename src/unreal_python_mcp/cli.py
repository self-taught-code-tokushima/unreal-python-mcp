"""
CLI tools for Unreal Python MCP.

Provides command-line utilities for managing the Unreal Python API cache.
"""

from __future__ import annotations

import sys


def refresh_cache() -> None:
    """
    CLI entry point: Refresh the Unreal Python API documentation cache.

    This fetches the latest API documentation from a running Unreal Editor
    and updates the local cache. Requires Unreal Editor to be running with
    Remote Execution enabled.

    Usage:
        uvx unreal-python-mcp-refresh
    """
    from unreal_python_mcp.cache import CacheManager
    from unreal_python_mcp.unreal_connection import UnrealConnection

    try:
        print("Connecting to Unreal Editor...")
        conn = UnrealConnection()

        print("Refreshing API cache...")
        cache = CacheManager()
        cache.refresh_from_unreal(conn)

        print("✓ Cache refreshed successfully")
        sys.exit(0)

    except Exception as e:
        print(f"✗ Failed to refresh cache: {e}", file=sys.stderr)
        print("\nMake sure:", file=sys.stderr)
        print("  1. Unreal Editor is running", file=sys.stderr)
        print("  2. Python Remote Execution is enabled in Editor Preferences", file=sys.stderr)
        print("     (Editor Preferences > Plugins > Python > Enable Remote Execution)", file=sys.stderr)
        sys.exit(1)
