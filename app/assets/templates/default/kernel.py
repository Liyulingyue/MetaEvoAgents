#!/usr/bin/env python3
"""
kernel.py — Lineage 独立内核

本脚本是 Lineage 的自包含运行核心，可独立于主框架执行。
它读取同级目录下的 instruction.md 作为 System Prompt，
在 vault/ 目录下执行 LLM + Bash 循环。

用法：
    python kernel.py                    # 交互模式
    python kernel.py "你的目标"         # 单次目标模式
"""

import os
import sys
import json
import uuid
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    import openai
except ImportError:
    print("Error: openai library not found. Run: pip install openai")
    sys.exit(1)


class KernelVault:
    """vault/ 目录管理器"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.vault_path.mkdir(parents=True, exist_ok=True)

    def execute_bash(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.vault_path),
            )
            return result.stdout + result.stderr or "(empty output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error: {e}"

    def write_file(self, path: str, content: str) -> str:
        try:
            p = self.vault_path / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Written: {p}"
        except Exception as e:
            return f"Error writing file: {e}"

    def read_file(self, path: str) -> str:
        try:
            p = self.vault_path / path
            if not p.exists():
                return f"Error: {path} does not exist."
            return p.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {e}"

    def list_files(self, path: str = ".") -> str:
        try:
            p = self.vault_path / path
            if not p.exists():
                return f"Error: Directory {path} does not exist."
            items = []
            for item in p.iterdir():
                marker = "[DIR] " if item.is_dir() else "[FILE] "
                items.append(f"{marker}{item.name}")
            return "\n".join(sorted(items)) if items else "(empty directory)"
        except Exception as e:
            return f"Error listing files: {e}"


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "Execute a bash command in the vault directory.",
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
            "description": "Read a file from the vault.",
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
            "description": "Write a file to the vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "content": {"type": "string", "description": "File content."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (defaults to vault root)."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_instruction",
            "description": "Update the agent's own instruction.md (its soul/personality).",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_content": {"type": "string", "description": "The new instruction content."}
                },
                "required": ["new_content"]
            }
        }
    }
]


def handle_tool_call(name: str, args: dict, vault: KernelVault, instruction_path: Path) -> str:
    if name == "execute_bash":
        return vault.execute_bash(args.get("command", ""))
    elif name == "read_file":
        return vault.read_file(args.get("path", ""))
    elif name == "write_file":
        return vault.write_file(args.get("path", ""), args.get("content", ""))
    elif name == "list_files":
        return vault.list_files(args.get("path", "."))
    elif name == "update_instruction":
        try:
            instruction_path.write_text(args.get("new_content", ""), encoding="utf-8")
            return "Instruction updated successfully."
        except Exception as e:
            return f"Error updating instruction: {e}"
    return f"Error: Unknown tool {name}"


class Kernel:
    def __init__(self, lineage_dir: str):
        self.lineage_dir = Path(lineage_dir).resolve()
        self.vault = KernelVault(str(self.lineage_dir / "vault"))
        self.instruction_path = self.lineage_dir / "instruction.md"
        self.memory_path = self.lineage_dir / "memory.log"
        self.vault_path = self.lineage_dir / "vault"

        self.system_prompt = self._load_instruction()
        self._log(f"KERNEL BOOT — lineage={self.lineage_dir.name}, vault={self.vault_path}")

    def _load_instruction(self) -> str:
        if self.instruction_path.exists():
            return self.instruction_path.read_text(encoding="utf-8")
        return "You are an autonomous coding agent. Use tools to accomplish tasks."

    def _log(self, entry: str):
        with self.memory_path.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {entry}\n")

    def _append_message(self, history: list, role: str, content: str = None, **kwargs):
        msg = {"role": role}
        if content:
            msg["content"] = content
        for k, v in kwargs.items():
            msg[k] = v
        history.append(msg)

    def run(self, objective: str, max_steps: int = 10):
        session_id = str(uuid.uuid4())[:8]
        history = []
        self._append_message(history, "user", f"Your objective: {objective}")
        self._log(f"SESSION START — session={session_id}, objective={objective}")

        client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("BASE_URL", "https://api.openai.com/v1"),
        )

        for step_i in range(max_steps):
            messages = [{"role": "system", "content": self.system_prompt}] + history
            resp = client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=0.7,
            )
            message = resp.choices[0].message

            if not message.tool_calls:
                self._log(f"SESSION END — session={session_id}, done=True")
                return message.content or ""

            for tc in message.tool_calls:
                result = handle_tool_call(
                    tc.function.name,
                    json.loads(tc.function.arguments),
                    self.vault,
                    self.instruction_path,
                )
                self._append_message(
                    history,
                    "tool",
                    result,
                    tool_call_id=tc.id,
                    name=tc.function.name,
                )
                self.system_prompt = self._load_instruction()

        self._log(f"SESSION END — session={session_id}, done=False, steps={max_steps}")
        return "(max steps reached)"


def main():
    if len(sys.argv) > 1:
        objective = sys.argv[1]
        lineage_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        lineage_dir = os.path.dirname(os.path.abspath(__file__))
        objective = input("Objective> ").strip()
        if not objective:
            print("No objective provided.")
            return

    kernel = Kernel(lineage_dir)
    print(f"[Kernel] Running lineage: {kernel.lineage_dir.name}")
    result = kernel.run(objective, max_steps=10)
    print(f"\n{'='*50}")
    print(f"Result:\n{result}")


if __name__ == "__main__":
    main()
