import os
import json
import subprocess
from pathlib import Path

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "Execute a bash command in the local environment. Use this for running tests, checking status, or searching.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to run."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file from the disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."}
                },
                "required": ["path"]
            }
        }
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
                    "content": {"type": "string", "description": "The content to write."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The directory path (defaults to current)."}
                }
            }
        }
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
                    "path": {"type": "string", "description": "The directory path to search in (defaults to current)."}
                },
                "required": ["query"]
            }
        }
    }
]


class CodeTools:
    _workspace_root: str = ""

    @classmethod
    def set_workspace(cls, path: str):
        cls._workspace_root = str(Path(path).resolve())

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

    @staticmethod
    def execute_bash(command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
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
            return p.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @staticmethod
    def write_file(path: str, content: str) -> str:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding='utf-8')
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    @staticmethod
    def list_files(path: str = ".") -> str:
        try:
            p = Path(path)
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
                f"grep -ril \"{query}\" {path}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout.strip()
            return output if output else "No matches found."
        except Exception as e:
            return f"Error searching files: {str(e)}"


def handle_tool_call(tool_name: str, args: dict) -> str:
    if tool_name == "execute_bash":
        return CodeTools.execute_bash(args.get("command", ""))
    elif tool_name == "read_file":
        return CodeTools.read_file(args.get("path", ""))
    elif tool_name == "write_file":
        return CodeTools.write_file(args.get("path", ""), args.get("content", ""))
    elif tool_name == "list_files":
        return CodeTools.list_files(args.get("path", "."))
    elif tool_name == "search_files":
        return CodeTools.search_files(args.get("query", ""), args.get("path", "."))
    return f"Error: Tool {tool_name} not found."
