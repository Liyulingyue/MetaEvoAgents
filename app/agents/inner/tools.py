import importlib.util
import subprocess
import sys
from pathlib import Path

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "Execute a bash command in the vault directory.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The command to run."}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file from the vault.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path to the file."}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file with the provided content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "content": {"type": "string", "description": "The content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path (defaults to vault root).",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for a specific string in files within a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The text to search for."},
                    "path": {
                        "type": "string",
                        "description": "The directory path to search in (defaults to current).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_instruction",
            "description": "Update the agent's own instruction.md (its soul/personality).",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_content": {
                        "type": "string",
                        "description": "The new instruction content to write.",
                    }
                },
                "required": ["new_content"],
            },
        },
    },
]


class WorkspaceToolLoader:
    def __init__(self, lineage_root: str):
        self.lineage_root = Path(lineage_root).resolve()
        self.tools_root = self.lineage_root / "tools"
        self._modules: dict = {}
        self._registry: dict = {}
        self._load()

    def _load(self):
        if not self.tools_root.exists():
            return
        for item in self.tools_root.iterdir():
            if item.suffix == ".py" and item.name not in ("__init__.py", "registry.py"):
                module_name = item.stem
                spec = importlib.util.spec_from_file_location(module_name, item)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    self._modules[module_name] = module
        registry_path = self.tools_root / "__init__.py"
        if registry_path.exists():
            spec = importlib.util.spec_from_file_location("ws_registry", registry_path)
            if spec and spec.loader:
                reg_module = importlib.util.module_from_spec(spec)
                sys.modules["ws_registry"] = reg_module
                spec.loader.exec_module(reg_module)
                if hasattr(reg_module, "TOOL_DEFINITIONS"):
                    self._registry = reg_module.TOOL_DEFINITIONS

    def get_schemas(self):
        if self._registry:
            return [
                {
                    "type": "function",
                    "function": {
                        "name": td["name"],
                        "description": td["description"],
                        "parameters": td["parameters"],
                    },
                }
                for td in self._registry.values()
            ]
        return TOOL_SCHEMAS

    def execute(self, tool_name: str, args: dict) -> str | None:
        if self._registry and tool_name in self._registry:
            td = self._registry[tool_name]
            module = self._modules.get(td["module"])
            if module and hasattr(module, tool_name):
                ctx = {
                    "lineage_root": str(self.lineage_root),
                    "vault_root": str(self.lineage_root / "vault"),
                }
                if tool_name == "execute_bash":
                    return getattr(module, tool_name)(args.get("command", ""), ctx["vault_root"])
                elif tool_name == "read_file":
                    return getattr(module, tool_name)(args.get("path", ""), ctx["vault_root"])
                elif tool_name == "write_file":
                    return getattr(module, tool_name)(
                        args.get("path", ""), args.get("content", ""), ctx["vault_root"]
                    )
                elif tool_name == "list_files":
                    return getattr(module, tool_name)(args.get("path", "."), ctx["vault_root"])
                elif tool_name == "search_files":
                    return getattr(module, tool_name)(args.get("query", ""), args.get("path", "."))
                elif tool_name == "update_instruction":
                    return getattr(module, tool_name)(
                        args.get("new_content", ""), ctx["lineage_root"]
                    )
        return None

    def has_tools(self) -> bool:
        return bool(self._registry)


class CodeTools:
    _workspace_root: str = ""

    @classmethod
    def set_workspace(cls, path: str):
        cls._workspace_root = str(Path(path).resolve())

    @classmethod
    def get_workspace(cls) -> str:
        return cls._workspace_root

    @classmethod
    def _resolve_path(cls, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            p = p.relative_to("/")
        else:
            p = Path(cls._workspace_root) / p
        resolved = Path(p).resolve()
        try:
            resolved.relative_to(Path(cls._workspace_root))
        except ValueError:
            return Path(cls._workspace_root)
        return resolved

    @classmethod
    def execute_bash(cls, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cls._workspace_root,
            )
            output = result.stdout + result.stderr
            return output if output else "(empty output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"

    @staticmethod
    def read_file(path: str) -> str:
        try:
            p = Path(path)
            if not p.exists():
                return f"Error: File {path} does not exist."
            return p.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @staticmethod
    def write_file(path: str, content: str) -> str:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    @classmethod
    def list_files(cls, path: str = ".") -> str:
        try:
            p = cls._resolve_path(path)
            if not p.exists():
                return f"Error: Directory {path} does not exist."
            if not p.is_dir():
                return f"Error: {path} is not a directory."

            items = []
            for item in p.iterdir():
                marker = "[DIR] " if item.is_dir() else "[FILE] "
                items.append(f"{marker}{item.name}")

            return "\n".join(sorted(items)) if items else "(empty directory)"
        except Exception as e:
            return f"Error listing files: {str(e)}"

    @staticmethod
    def search_files(query: str, path: str = ".") -> str:
        try:
            result = subprocess.run(
                f'grep -ril "{query}" {path}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout.strip()
            return output if output else "No matches found."
        except Exception as e:
            return f"Error searching files: {str(e)}"


_agent_tools: dict = {}


def register_agent_tool(name: str, func):
    _agent_tools[name] = func


_workspace_loader: WorkspaceToolLoader | None = None


def set_workspace_loader(loader: WorkspaceToolLoader | None):
    global _workspace_loader
    _workspace_loader = loader


def get_schemas_from_workspace(lineage_root: str):
    loader = WorkspaceToolLoader(lineage_root)
    if loader.has_tools():
        return loader.get_schemas()
    return TOOL_SCHEMAS


def handle_tool_call(
    tool_name: str, args: dict, lineage_root: str | None = None
) -> tuple[str, bool]:
    global _workspace_loader
    instruction_updated = False

    if _workspace_loader is not None:
        result = _workspace_loader.execute(tool_name, args)
        if result is not None:
            if tool_name == "update_instruction":
                instruction_updated = True
            return result, instruction_updated

    if tool_name in _agent_tools:
        return _agent_tools[tool_name](**args), False
    elif tool_name == "execute_bash":
        return CodeTools.execute_bash(args.get("command", "")), False
    elif tool_name == "read_file":
        return CodeTools.read_file(args.get("path", "")), False
    elif tool_name == "write_file":
        return CodeTools.write_file(args.get("path", ""), args.get("content", "")), False
    elif tool_name == "list_files":
        return CodeTools.list_files(args.get("path", ".")), False
    elif tool_name == "search_files":
        return CodeTools.search_files(args.get("query", ""), args.get("path", ".")), False
    return f"Error: Tool {tool_name} not found.", False
