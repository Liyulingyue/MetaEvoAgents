import json
import os
import sys
import importlib.util
from pathlib import Path
from datetime import datetime


def load_tools(tools_dir: Path):
    modules = {}
    definitions = {}
    if not tools_dir.exists():
        return modules, definitions
    for item in tools_dir.iterdir():
        if item.suffix == ".py" and item.name not in ("__init__.py",):
            name = item.stem
            spec = importlib.util.spec_from_file_location(name, item)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[name] = mod
                spec.loader.exec_module(mod)
                modules[name] = mod

    init_file = tools_dir / "__init__.py"
    if init_file.exists():
        spec = importlib.util.spec_from_file_location("_reg", init_file)
        if spec and spec.loader:
            reg = importlib.util.module_from_spec(spec)
            sys.modules["_reg"] = reg
            spec.loader.exec_module(reg)
            if hasattr(reg, "TOOL_DEFINITIONS"):
                definitions = reg.TOOL_DEFINITIONS
    return modules, definitions


def build_schemas(definitions):
    return [
        {
            "type": "function",
            "function": {
                "name": td["name"],
                "description": td["description"],
                "parameters": td["parameters"],
            },
        }
        for td in definitions.values()
    ]


def exec_tool(
    tool_name: str, args: dict, modules: dict, definitions: dict, vault_path: str, lineage_root: str
):
    if not definitions or tool_name not in definitions:
        return f"Error: Tool {tool_name} definition not found."
    td = definitions[tool_name]
    mod = modules.get(td["module"])
    if not mod or not hasattr(mod, tool_name):
        return f"Error: Tool {tool_name} implementation not found in {td['module']}."

    fn = getattr(mod, tool_name)

    # Mapping logic for tool arguments
    handlers = {
        "execute_bash": lambda: fn(args.get("command", ""), vault_path),
        "read_file": lambda: fn(args.get("path", ""), vault_path),
        "write_file": lambda: fn(args.get("path", ""), args.get("content", ""), vault_path),
        "list_files": lambda: fn(args.get("path", "."), vault_path),
        "search_files": lambda: fn(args.get("query", ""), args.get("path", ".")),
        "update_instruction": lambda: fn(args.get("new_content", ""), lineage_root),
        "broadcast_event": lambda: fn(
            args.get("type", "INFO"), args.get("message", ""), lineage_root
        ),
        "pray": lambda: fn(args.get("content", ""), lineage_root),
        "delegate_task": lambda: fn(
            args.get("target_lineage_id", ""), args.get("message", ""), lineage_root
        ),
        "birth": lambda: fn(args.get("child_id", ""), lineage_root),
        "offer_to_altar": lambda: fn(
            args.get("file_name", ""),
            args.get("description", ""),
            args.get("content"),
            lineage_root,
        ),
        "collect_from_altar": lambda: fn(args.get("file_name", ""), lineage_root),
        "listen_to_revelation": lambda: fn(lineage_root),
    }

    if tool_name in handlers:
        return handlers[tool_name]()
    return f"Error: No handler for tool {tool_name}."
