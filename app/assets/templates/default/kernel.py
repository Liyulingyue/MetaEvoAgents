#!/usr/bin/env python3
"""
kernel.py — Lineage 自主内核

本脚本是 Lineage 的自包含运行核心，可独立于主框架执行。
它读取同级目录下的 instruction.md 作为 System Prompt，
从 tools/ 目录动态加载工具，在 vault/ 目录下执行 LLM + 工具循环。

用法：
    python kernel.py                    # 交互模式
    python kernel.py "你的目标"         # 单次目标模式
"""

import importlib.util
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import openai
from dotenv import load_dotenv

load_dotenv()


def load_tools_from_workspace(tools_dir: Path):
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
        spec = importlib.util.spec_from_file_location("_ws_reg", init_file)
        if spec and spec.loader:
            reg = importlib.util.module_from_spec(spec)
            sys.modules["_ws_reg"] = reg
            spec.loader.exec_module(reg)
            if hasattr(reg, "TOOL_DEFINITIONS"):
                definitions = reg.TOOL_DEFINITIONS
    return modules, definitions


def build_tool_schemas(definitions):
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


def execute_tool(
    tool_name: str, args: dict, modules: dict, definitions: dict, vault_path: str, lineage_root: str
):
    if not definitions or tool_name not in definitions:
        return None
    td = definitions[tool_name]
    mod = modules.get(td["module"])
    if not mod or not hasattr(mod, tool_name):
        return None
    fn = getattr(mod, tool_name)
    ctx = {"vault_root": vault_path, "lineage_root": lineage_root}
    if tool_name == "execute_bash":
        return fn(args.get("command", ""), ctx["vault_root"])
    elif tool_name == "read_file":
        return fn(args.get("path", ""), ctx["vault_root"])
    elif tool_name == "write_file":
        return fn(args.get("path", ""), args.get("content", ""), ctx["vault_root"])
    elif tool_name == "list_files":
        return fn(args.get("path", "."), ctx["vault_root"])
    elif tool_name == "search_files":
        return fn(args.get("query", ""), args.get("path", "."))
    elif tool_name == "update_instruction":
        return fn(args.get("new_content", ""), ctx["lineage_root"])
    return None


class KernelVault:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.modules, self.definitions = load_tools_from_workspace(self.vault_path.parent / "tools")

    def execute_tool(self, tool_name: str, args: dict) -> str:
        result = execute_tool(
            tool_name,
            args,
            self.modules,
            self.definitions,
            str(self.vault_path),
            str(self.vault_path.parent),
        )
        if result is not None:
            return result
        p = (
            self.vault_path / args.get("path", ".")
            if args.get("path", ".") != "."
            else self.vault_path
        )
        if not p.exists():
            return f"Error: Directory {args.get('path', '.')} does not exist."
        if not p.is_dir():
            return f"Error: {args.get('path', '.')} is not a directory."
        items = []
        for item in sorted(p.iterdir()):
            marker = "[DIR] " if item.is_dir() else "[FILE] "
            items.append(f"{marker}{item.name}")
        return "\n".join(items) if items else "(empty directory)"


def handle_tool_call(name: str, args: dict, vault: KernelVault, instruction_path: Path):
    result = vault.execute_tool(name, args)
    if result is not None:
        return result
    return f"Error: Unknown tool {name}"


class Kernel:
    def __init__(self, lineage_dir: str):
        self.lineage_dir = Path(lineage_dir).resolve()
        self.vault = KernelVault(str(self.lineage_dir / "vault"))
        self.instruction_path = self.lineage_dir / "instruction.md"
        self.memory_path = self.lineage_dir / "memory.log"
        self.vault_path = self.lineage_dir / "vault"

        self.system_prompt = self._load_instruction()
        self.schemas = build_tool_schemas(self.vault.definitions)
        self._log(
            f"KERNEL BOOT — lineage={self.lineage_dir.name}, vault={self.vault_path}, tools={list(self.vault.definitions.keys())}"
        )

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

        for _step_i in range(max_steps):
            messages = [{"role": "system", "content": self.system_prompt}] + history
            resp = client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                messages=messages,
                tools=self.schemas,
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
    print(
        f"[Kernel] Running lineage: {kernel.lineage_dir.name}, tools: {list(kernel.vault.definitions.keys())}"
    )
    result = kernel.run(objective, max_steps=10)
    print(f"\n{'=' * 50}")
    print(f"Result:\n{result}")


if __name__ == "__main__":
    main()
