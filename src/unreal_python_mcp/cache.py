"""
Cache management for Unreal Python API documentation.

Handles:
- Loading/saving cached documentation
- Converting JSON to llms.txt format
- Generating hierarchical indexes (summary, module-based, category-based)
- Searching the API index
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unreal_python_mcp.unreal_connection import UnrealConnection


# Default cache directory
def get_cache_dir() -> Path:
    """Get the cache directory path."""
    cache_dir = Path.home() / ".unreal-python-mcp" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


class CacheManager:
    """Manages the Unreal Python API documentation cache."""

    def __init__(self, cache_dir: Path | None = None, unreal_connection: "UnrealConnection | None" = None):
        self.cache_dir = cache_dir or get_cache_dir()
        self._toc_cache: dict | None = None
        self._llms_index_cache: str | None = None
        self._class_docs_cache: dict[str, dict] = {}
        self._unreal_connection: "UnrealConnection | None" = unreal_connection

    def set_unreal_connection(self, conn: "UnrealConnection") -> None:
        """Set the Unreal connection for lazy loading."""
        self._unreal_connection = conn

    def get_toc_path(self) -> Path:
        """Get the path to the cached TOC JSON file."""
        return self.cache_dir / "toc.json"

    def get_meta_path(self) -> Path:
        """Get the path to the cache metadata file."""
        return self.cache_dir / "meta.json"

    def get_class_doc_path(self, class_name: str) -> Path:
        """Get the path to a cached class documentation file."""
        classes_dir = self.cache_dir / "classes"
        classes_dir.mkdir(parents=True, exist_ok=True)
        return classes_dir / f"{class_name}.json"

    def get_llms_index_path(self) -> Path:
        """Get the path to the cached llms.txt file."""
        return self.cache_dir / "llms.txt"

    def load_toc(self) -> dict | None:
        """Load the cached TOC JSON."""
        if self._toc_cache is not None:
            return self._toc_cache

        toc_path = self.get_toc_path()
        if toc_path.exists():
            try:
                with open(toc_path, "r", encoding="utf-8") as f:
                    self._toc_cache = json.load(f)
                return self._toc_cache
            except (json.JSONDecodeError, IOError):
                pass
        return None

    def save_toc(self, toc: dict) -> None:
        """Save the TOC JSON to cache."""
        self._toc_cache = toc
        self._llms_index_cache = None  # Invalidate llms index cache

        toc_path = self.get_toc_path()
        with open(toc_path, "w", encoding="utf-8") as f:
            json.dump(toc, f, indent=2)

        # Update metadata
        meta = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "toc_entries": sum(len(v) for v in toc.values() if isinstance(v, dict)),
        }
        with open(self.get_meta_path(), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def get_llms_index(self) -> str:
        """
        Get the llms.txt formatted index.

        If cache exists, returns cached content.
        Otherwise, generates from TOC or returns a placeholder.
        """
        if self._llms_index_cache is not None:
            return self._llms_index_cache

        # Try to load from file
        llms_path = self.get_llms_index_path()
        if llms_path.exists():
            try:
                with open(llms_path, "r", encoding="utf-8") as f:
                    self._llms_index_cache = f.read()
                return self._llms_index_cache
            except IOError:
                pass

        # Generate from TOC
        toc = self.load_toc()
        if toc:
            self._llms_index_cache = self._generate_llms_index(toc)
            # Save to file
            with open(llms_path, "w", encoding="utf-8") as f:
                f.write(self._llms_index_cache)
            return self._llms_index_cache

        # Return placeholder
        return self._get_placeholder_llms_index()

    def _get_placeholder_llms_index(self) -> str:
        """Return a placeholder llms.txt when no cache is available."""
        return """# Unreal Python API
> Status: Cache not initialized
> Action: Run `refresh_api_cache` tool with Unreal Editor running

## How to Initialize

1. Start Unreal Editor with a project
2. Enable Python Remote Execution in Editor Preferences > Plugins > Python
3. Use the `refresh_api_cache` tool to fetch and cache the API documentation

## Available Tools

- `refresh_api_cache`: Fetch API documentation from Unreal Editor
- `search_unreal_api`: Search the API index
- `get_class_overview`: Get class overview (member name lists, 1-3KB)
- `get_member_info`: Get detailed info for a specific member
- `get_members_info`: Get detailed info for multiple members (batch)
- `exec_unreal_python`: Execute Python code in Unreal Editor
- `list_unreal_instances`: List available Unreal Editor instances
"""

    def _generate_llms_index(self, toc: dict) -> str:
        """
        Generate llms.txt format from TOC JSON.

        TOC format (from build_toc.py):
        {
            "Class": {"ClassName": {"func": [...], "cls_func": [...], "prop": [...], "const": [...]}},
            "Enum": {"EnumName": {"const": [...]}},
            "Struct": {...},
            "Delegate": {...},
            "Native": {...}
        }
        """
        lines = [
            "# Unreal Python API",
            f"> Generated: {datetime.now().strftime('%Y-%m-%d')}",
            "",
        ]

        # Classes
        if "Class" in toc and toc["Class"]:
            lines.append("## Classes")
            lines.append("")
            for class_name, members in sorted(toc["Class"].items()):
                func_count = len(members.get("func", []))
                prop_count = len(members.get("prop", []))
                lines.append(f"- [{class_name}](/class/{class_name}): {func_count} methods, {prop_count} properties")
            lines.append("")

        # Enums
        if "Enum" in toc and toc["Enum"]:
            lines.append("## Enums")
            lines.append("")
            for enum_name, members in sorted(toc["Enum"].items()):
                const_count = len(members.get("const", []))
                lines.append(f"- [{enum_name}](/enum/{enum_name}): {const_count} values")
            lines.append("")

        # Structs
        if "Struct" in toc and toc["Struct"]:
            lines.append("## Structs")
            lines.append("")
            for struct_name, members in sorted(toc["Struct"].items()):
                prop_count = len(members.get("prop", []))
                lines.append(f"- [{struct_name}](/struct/{struct_name}): {prop_count} properties")
            lines.append("")

        # Delegates
        if "Delegate" in toc and toc["Delegate"]:
            lines.append("## Delegates")
            lines.append("")
            for delegate_name in sorted(toc["Delegate"].keys()):
                lines.append(f"- [{delegate_name}](/delegate/{delegate_name})")
            lines.append("")

        # Native (functions)
        if "Native" in toc and toc["Native"]:
            lines.append("## Functions")
            lines.append("")
            for func_name in sorted(toc["Native"].keys()):
                lines.append(f"- [{func_name}](/func/{func_name})")
            lines.append("")

        return "\n".join(lines)

    def search_api(self, query: str, max_results: int = 20) -> list[str]:
        """
        Search the API index for matching entries.

        Args:
            query: Search query (supports partial matching and regex)
            max_results: Maximum number of results to return
        """
        toc = self.load_toc()
        if not toc:
            return ["Cache not initialized. Use refresh_api_cache tool first."]

        results = []
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error:
            # If invalid regex, use simple substring matching
            pattern = None

        for category, items in toc.items():
            if not isinstance(items, dict):
                continue

            for name, members in items.items():
                matched = False
                if pattern:
                    matched = pattern.search(name) is not None
                else:
                    matched = query.lower() in name.lower()

                if matched:
                    member_info = []
                    if members.get("func"):
                        member_info.append(f"{len(members['func'])} methods")
                    if members.get("prop"):
                        member_info.append(f"{len(members['prop'])} props")
                    if members.get("const"):
                        member_info.append(f"{len(members['const'])} consts")

                    info = f"[{category}] {name}"
                    if member_info:
                        info += f" ({', '.join(member_info)})"
                    results.append(info)

                    if len(results) >= max_results:
                        break

            if len(results) >= max_results:
                break

        return results

    def get_class_doc(self, class_name: str) -> dict | None:
        """
        Get detailed documentation for a class.

        First checks memory cache, then file cache, then fetches from Unreal.
        """
        # Check memory cache
        if class_name in self._class_docs_cache:
            return self._class_docs_cache[class_name]

        # Check file cache
        doc_path = self.get_class_doc_path(class_name)
        if doc_path.exists():
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                self._class_docs_cache[class_name] = doc
                return doc
            except (json.JSONDecodeError, IOError):
                pass

        # Fetch from Unreal (lazy loading)
        if self._unreal_connection is not None:
            doc_json = self._unreal_connection.fetch_class_doc(class_name)
            if doc_json:
                try:
                    doc = json.loads(doc_json)
                    self.save_class_doc(class_name, doc)
                    return doc
                except json.JSONDecodeError:
                    pass

        return None

    def save_class_doc(self, class_name: str, doc: dict) -> None:
        """Save class documentation to cache."""
        self._class_docs_cache[class_name] = doc
        doc_path = self.get_class_doc_path(class_name)
        with open(doc_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2)

    def refresh_from_unreal(self, conn: "UnrealConnection") -> None:
        """
        Refresh the cache by fetching documentation from Unreal Editor.

        Args:
            conn: UnrealConnection instance for communicating with Unreal
        """
        # Fetch TOC
        toc_json = conn.fetch_toc()
        if toc_json:
            toc = json.loads(toc_json)
            self.save_toc(toc)

        # Clear llms index cache to regenerate
        self._llms_index_cache = None
        llms_path = self.get_llms_index_path()
        if llms_path.exists():
            llms_path.unlink()

    # ========================================================================
    # Hierarchical Index Generation
    # ========================================================================

    def get_modules(self) -> dict[str, list[str]]:
        """
        Get a mapping of module names to class names.

        Includes both Class and Native categories (Native includes custom modules).

        Returns:
            Dict mapping module name to list of class names
        """
        toc = self.load_toc()
        if not toc:
            return {}

        modules: dict[str, list[str]] = defaultdict(list)

        # Process both Class and Native categories
        for category in ["Class", "Native"]:
            classes = toc.get(category, {})
            for class_name, class_data in classes.items():
                module = class_data.get("module", "Other")
                modules[module].append(class_name)

        # Sort class names within each module
        for module in modules:
            modules[module].sort()

        return dict(modules)

    def get_summary(self) -> str:
        """
        Get a lightweight summary of the API.

        Returns:
            Summary text (~2KB) with category counts and module list
        """
        toc = self.load_toc()
        if not toc:
            return self._get_placeholder_summary()

        lines = [
            "# Unreal Python API Summary",
            f"> Generated: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## Categories",
            "",
        ]

        # Category counts
        for category in ["Class", "Struct", "Enum", "Delegate", "Function", "Native"]:
            items = toc.get(category, {})
            if items:
                lines.append(f"- {category}: {len(items)} entries")

        lines.append("")
        lines.append("## Class Modules")
        lines.append("")
        lines.append("Classes are organized by module. Use `unreal-python://index/module/{name}` to get classes for a specific module.")
        lines.append("")

        # Module list with counts
        modules = self.get_modules()
        sorted_modules = sorted(modules.items(), key=lambda x: -len(x[1]))

        for module, classes in sorted_modules[:30]:  # Top 30 modules
            lines.append(f"- **{module}**: {len(classes)} classes")

        if len(sorted_modules) > 30:
            remaining = len(sorted_modules) - 30
            lines.append(f"- ... and {remaining} more modules")

        lines.append("")
        lines.append("## Other Resources")
        lines.append("")
        lines.append("- `unreal-python://index/enums` - All enums")
        lines.append("- `unreal-python://index/structs` - All structs")
        lines.append("- `unreal-python://index/delegates` - All delegates")
        lines.append("")
        lines.append("## Tools")
        lines.append("")
        lines.append("- `search_unreal_api(query)` - Search by name")
        lines.append("- `get_class_overview(name)` - Get class overview (member name lists)")
        lines.append("- `get_member_info(class, member)` - Get detailed member documentation")
        lines.append("- `get_members_info(class, members)` - Batch get member documentation")

        return "\n".join(lines)

    def _get_placeholder_summary(self) -> str:
        """Return a placeholder summary when no cache is available."""
        return """# Unreal Python API Summary
> Status: Cache not initialized
> Action: Run `refresh_api_cache` tool with Unreal Editor running

## How to Initialize

1. Start Unreal Editor with a project
2. Enable Python Remote Execution in Editor Preferences > Plugins > Python
3. Use the `refresh_api_cache` tool to fetch and cache the API documentation
"""

    def get_module_index(self, module_name: str) -> str:
        """
        Get the class index for a specific module.

        Args:
            module_name: The module name (e.g., "Engine", "UnrealEd")

        Returns:
            Formatted index of classes in the module
        """
        toc = self.load_toc()
        if not toc:
            return f"Cache not initialized. Use refresh_api_cache tool first."

        modules = self.get_modules()
        if module_name not in modules:
            available = ", ".join(sorted(modules.keys())[:10])
            return f"Module '{module_name}' not found. Available modules include: {available}..."

        lines = [
            f"# {module_name} Module Classes",
            f"> {len(modules[module_name])} classes",
            "",
        ]

        # Get classes from both Class and Native categories
        all_classes = {}
        all_classes.update(toc.get("Class", {}))
        all_classes.update(toc.get("Native", {}))

        for class_name in modules[module_name]:
            class_data = all_classes.get(class_name, {})
            func_count = len(class_data.get("func", []))
            prop_count = len(class_data.get("prop", []))
            lines.append(f"- [{class_name}](/class/{class_name}): {func_count} methods, {prop_count} properties")

        return "\n".join(lines)

    def get_enums_index(self) -> str:
        """
        Get the index of all enums.

        Returns:
            Formatted index of enums
        """
        toc = self.load_toc()
        if not toc:
            return "Cache not initialized. Use refresh_api_cache tool first."

        enums = toc.get("Enum", {})
        lines = [
            "# Unreal Python Enums",
            f"> {len(enums)} enums",
            "",
        ]

        for enum_name in sorted(enums.keys()):
            enum_data = enums.get(enum_name, {})
            const_count = len(enum_data.get("const", []))
            lines.append(f"- {enum_name}: {const_count} values")

        return "\n".join(lines)

    def get_structs_index(self) -> str:
        """
        Get the index of all structs.

        Returns:
            Formatted index of structs
        """
        toc = self.load_toc()
        if not toc:
            return "Cache not initialized. Use refresh_api_cache tool first."

        structs = toc.get("Struct", {})
        lines = [
            "# Unreal Python Structs",
            f"> {len(structs)} structs",
            "",
        ]

        for struct_name in sorted(structs.keys()):
            struct_data = structs.get(struct_name, {})
            prop_count = len(struct_data.get("prop", []))
            func_count = len(struct_data.get("func", []))
            if func_count > 0:
                lines.append(f"- {struct_name}: {prop_count} properties, {func_count} methods")
            else:
                lines.append(f"- {struct_name}: {prop_count} properties")

        return "\n".join(lines)

    def get_delegates_index(self) -> str:
        """
        Get the index of all delegates.

        Returns:
            Formatted index of delegates
        """
        toc = self.load_toc()
        if not toc:
            return "Cache not initialized. Use refresh_api_cache tool first."

        delegates = toc.get("Delegate", {})
        lines = [
            "# Unreal Python Delegates",
            f"> {len(delegates)} delegates",
            "",
        ]

        for delegate_name in sorted(delegates.keys()):
            lines.append(f"- {delegate_name}")

        return "\n".join(lines)

    def list_modules(self) -> list[str]:
        """
        List all available modules sorted by class count.

        Returns:
            List of module names
        """
        modules = self.get_modules()
        return sorted(modules.keys(), key=lambda m: -len(modules[m]))

    def get_class_overview(self, class_name: str, include_doc: bool = False) -> dict | None:
        """
        Get class overview with member name lists only (no detailed docs for each member).

        By default, uses only TOC data (no Unreal query required, very lightweight).
        Set include_doc=True to also fetch doc and bases from Unreal.

        Args:
            class_name: The class name
            include_doc: If True, fetch doc and bases from Unreal (default: False)

        Returns:
            Dict with name, module, and member name lists (plus doc/bases if include_doc=True)
        """
        toc = self.load_toc()
        if not toc:
            return None

        # Find class in TOC (check all categories)
        class_data = None
        for category in ["Class", "Struct", "Enum", "Native"]:
            if class_name in toc.get(category, {}):
                class_data = toc[category][class_name]
                break

        if not class_data:
            return None

        # Build overview from TOC data
        overview = {
            "name": class_name,
            "module": class_data.get("module"),
            "methods": class_data.get("func", []),
            "class_methods": class_data.get("cls_func", []),
            "properties": class_data.get("prop", []),
            "constants": class_data.get("const", []),
        }

        # Optionally fetch basic info (doc, bases) from Unreal
        if include_doc and self._unreal_connection is not None:
            basic_info_json = self._unreal_connection.fetch_class_basic_info(class_name)
            if basic_info_json:
                try:
                    basic_info = json.loads(basic_info_json)
                    overview["doc"] = basic_info.get("doc", "")
                    overview["bases"] = basic_info.get("bases", [])
                except json.JSONDecodeError:
                    pass

        return overview

    def get_member_info(self, class_name: str, member_name: str) -> dict | None:
        """
        Get detailed info for a specific member (method, property, or constant).

        Args:
            class_name: The class name
            member_name: The member name

        Returns:
            Dict with member details (type, doc, signature, etc.)
        """
        if self._unreal_connection is None:
            return None

        member_json = self._unreal_connection.fetch_member_info(class_name, member_name)
        if member_json:
            try:
                return json.loads(member_json)
            except json.JSONDecodeError:
                pass

        return None

    def get_members_info(self, class_name: str, member_names: list[str]) -> list[dict]:
        """
        Get detailed info for multiple members at once (batch operation).

        Args:
            class_name: The class name
            member_names: List of member names to fetch

        Returns:
            List of member info dicts (skips members that couldn't be fetched)
        """
        results = []
        for member_name in member_names:
            member_info = self.get_member_info(class_name, member_name)
            if member_info:
                results.append(member_info)
        return results
