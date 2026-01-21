"""
Unreal Editor connection management using upyrc.

Handles:
- Discovering Unreal Editor instances
- Executing Python code
- Fetching API documentation
"""

from __future__ import annotations

import socket
from pathlib import Path

from upyrc import upyre


# Python scripts to execute in Unreal
SCRIPT_DIR = Path(__file__).parent / "scripts"


class UnrealConnection:
    """Manages connection to Unreal Editor via upyrc."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def list_instances(self) -> str:
        """
        List all running Unreal Editor instances with Remote Execution enabled.

        Returns:
            Formatted string of discovered instances
        """
        try:
            instances = self._discover_instances()
        except Exception as e:
            return f"Error during discovery: {e}"

        if not instances:
            return (
                "No Unreal Editor instances found.\n"
                "Make sure:\n"
                "  - Unreal Editor is running\n"
                "  - Python plugin is enabled\n"
                "  - 'Enable Remote Execution' is checked in Editor Preferences > Plugins > Python"
            )

        lines = [f"Found {len(instances)} instance(s):"]
        for inst in instances:
            lines.append(f"  - {inst['project_name']} (Unreal {inst['engine_version']})")
        return "\n".join(lines)

    def _discover_instances(self, timeout: float = 1.0) -> list[dict]:
        """Discover all running Unreal Editor instances."""
        config = upyre.RemoteExecutionConfig()
        instances = []

        mcastsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        mcastsock.settimeout(timeout)
        mcastsock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, config.IP_MULTICAST_TTL)
        mcastsock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        mcastsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mcastsock.bind((config.MULTICAST_BIND_ADDRESS, config.MULTICAST_GROUP[1]))
        membership_request = socket.inet_aton(config.MULTICAST_GROUP[0]) + socket.inet_aton(config.MULTICAST_BIND_ADDRESS)
        mcastsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_request)

        try:
            ping_message = upyre.PingMessage(config)
            ping_message.send(mcastsock)

            seen_nodes = set()
            for result in ping_message.raw_receive(mcastsock):
                if result.get("type") == "pong":
                    node_id = result.get("source", "")
                    if node_id and node_id not in seen_nodes:
                        seen_nodes.add(node_id)
                        data = result.get("data", {})
                        instances.append({
                            "node_id": node_id,
                            "project_name": data.get("project_name", "Unknown"),
                            "engine_version": data.get("engine_version", "Unknown"),
                        })
        finally:
            mcastsock.close()

        return instances

    def execute(self, code: str) -> str:
        """
        Execute Python code in Unreal Editor.

        Args:
            code: Python code to execute

        Returns:
            Execution result or error message
        """
        config = upyre.RemoteExecutionConfig()

        try:
            conn = upyre.PythonRemoteConnection(config)
            conn.open_connection()
        except upyre.ConnectionError:
            return (
                "Error: Could not connect to Unreal Editor.\n"
                "Make sure:\n"
                "  - Unreal Editor is running\n"
                "  - Python plugin is enabled\n"
                "  - 'Enable Remote Execution' is checked in Editor Preferences > Plugins > Python"
            )
        except Exception as e:
            return f"Error connecting to Unreal Editor: {e}"

        try:
            result = conn.execute_python_command(
                code,
                exec_type=upyre.ExecTypes.EXECUTE_FILE,
                timeout=self.timeout,
                raise_exc=False,
            )

            output_lines = []

            # Collect output
            if result.output:
                for entry in result.output:
                    output_type = entry.get("type", "Info")
                    output_text = entry.get("output", "")
                    if output_type == "Warning":
                        output_lines.append(f"Warning: {output_text}")
                    elif output_type == "Error":
                        output_lines.append(f"Error: {output_text}")
                    else:
                        output_lines.append(output_text)

            if result.success:
                result_value = result.data.get("result", "None")
                if result_value and result_value != "None":
                    output_lines.append(result_value)
                return "\n".join(output_lines) if output_lines else "(no output)"
            else:
                error_msg = result.result
                if error_msg and error_msg != "None":
                    output_lines.append(f"Execution failed: {error_msg}")
                return "\n".join(output_lines)

        except socket.timeout:
            return f"Error: Execution timed out after {self.timeout} seconds."
        except Exception as e:
            return f"Error during execution: {e}"
        finally:
            try:
                conn.close_connection()
            except Exception:
                pass

    def fetch_toc(self) -> str | None:
        """
        Fetch the API TOC (Table of Contents) from Unreal Editor.

        Returns:
            JSON string of the TOC, or None if failed
        """
        # build_toc.py の get_table_of_content_json() を実行
        code = '''
import inspect
import types
import json
import unreal

class UnrealClassRepresentation:
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj
        self.methods = []
        self.class_methods = []
        self.properties = []
        self.constants = []
        self._categorize_members()

    def _categorize_members(self):
        for member_name, member in inspect.getmembers(self.obj):
            if member_name.startswith('_'):
                continue
            if isinstance(member, property):
                self.properties.append(member_name)
            elif inspect.isfunction(member) or inspect.ismethod(member):
                self.methods.append(member_name)
            elif isinstance(member, classmethod) or (inspect.isbuiltin(member) and 'method' in str(type(member))):
                self.class_methods.append(member_name)
            elif not callable(member):
                self.constants.append(member_name)

    def to_dict(self):
        return {
            "func": self.methods,
            "cls_func": self.class_methods,
            "prop": self.properties,
            "const": self.constants
        }

def get_table_of_content():
    toc = {"Class": {}, "Enum": {}, "Struct": {}, "Delegate": {}, "Native": {}}

    for name, obj in inspect.getmembers(unreal):
        if name.startswith('_'):
            continue

        if inspect.isclass(obj):
            if issubclass(obj, unreal.EnumBase):
                toc["Enum"][name] = {"const": [m for m in dir(obj) if not m.startswith('_') and m.isupper()]}
            elif issubclass(obj, unreal.StructBase):
                rep = UnrealClassRepresentation(name, obj)
                toc["Struct"][name] = rep.to_dict()
            elif issubclass(obj, (unreal.DelegateBase, unreal.MulticastDelegateBase)):
                toc["Delegate"][name] = {}
            else:
                rep = UnrealClassRepresentation(name, obj)
                toc["Class"][name] = rep.to_dict()
        elif callable(obj):
            toc["Native"][name] = {}

    return toc

result = json.dumps(get_table_of_content())
print(result)
'''
        output = self.execute(code)

        # 出力から JSON を抽出
        if output and not output.startswith("Error"):
            # 最初の { から最後の } までを抽出
            try:
                start = output.index("{")
                end = output.rindex("}") + 1
                json_str = output[start:end]
                # 有効な JSON かチェック
                import json
                json.loads(json_str)
                return json_str
            except (ValueError, json.JSONDecodeError):
                pass

        return None

    def fetch_class_doc(self, class_name: str) -> str | None:
        """
        Fetch detailed documentation for a specific class.

        Args:
            class_name: The class name to fetch documentation for

        Returns:
            JSON string of the class documentation, or None if failed
        """
        code = f'''
import inspect
import json
import unreal

def get_class_doc(class_name):
    obj = getattr(unreal, class_name, None)
    if obj is None:
        return None

    doc = {{
        "name": class_name,
        "doc": inspect.getdoc(obj) or "",
        "bases": [b.__name__ for b in getattr(obj, '__bases__', []) if hasattr(b, '__name__')],
        "is_class": inspect.isclass(obj),
        "members": {{
            "methods": [],
            "properties": [],
            "constants": []
        }}
    }}

    for name, member in inspect.getmembers(obj):
        if name.startswith('_'):
            continue

        member_info = {{"name": name, "doc": inspect.getdoc(member) or ""}}

        if isinstance(member, property):
            doc["members"]["properties"].append(member_info)
        elif callable(member):
            try:
                sig = str(inspect.signature(member))
            except (ValueError, TypeError):
                sig = "()"
            member_info["signature"] = sig
            doc["members"]["methods"].append(member_info)
        else:
            member_info["value"] = repr(member)[:100]
            doc["members"]["constants"].append(member_info)

    return doc

result = get_class_doc("{class_name}")
if result:
    print(json.dumps(result))
else:
    print("null")
'''
        output = self.execute(code)

        if output and not output.startswith("Error"):
            try:
                start = output.index("{")
                end = output.rindex("}") + 1
                json_str = output[start:end]
                import json
                json.loads(json_str)
                return json_str
            except (ValueError, json.JSONDecodeError):
                pass

        return None
