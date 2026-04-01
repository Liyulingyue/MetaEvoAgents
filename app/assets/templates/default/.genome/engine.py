#!/usr/bin/env python3
# ruff: noqa: E501
"""
engine.py — Lineage 自主引擎（Standalone 进程模式）

通过 stdin/stdout 以 JSON 进行消息通信，实现与主框架的完全解耦。
主框架仅作为进程管理器，不持有 any agent 逻辑。

通信协议（框架 → engine）：
    {"type": "run",       "session_id": "...", "objective": "...", "max_steps": 10}
    {"type": "introspect"}
    {"type": "sync"}
    {"type": "shutdown"}

通信协议（engine → 框架）：
    {"type": "step",      "session_id": "...", "step": 0, "done": false, "tool": "...", "result": "..."}
    {"type": "result",    "session_id": "...", "final_output": "..."}
    {"type": "introspect_result", "vault_contents": [...], "metadata": {...}, "tools": [...]}
    {"type": "sync_ok"}
    {"type": "error",     "message": "..."}
"""

import json
import os
import sys
import uuid
import importlib.util
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


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
        return None
    td = definitions[tool_name]
    mod = modules.get(td["module"])
    if not mod or not hasattr(mod, tool_name):
        return None
    fn = getattr(mod, tool_name)
    if tool_name == "execute_bash":
        return fn(args.get("command", ""), vault_path)
    elif tool_name == "read_file":
        return fn(args.get("path", ""), vault_path)
    elif tool_name == "write_file":
        return fn(args.get("path", ""), args.get("content", ""), vault_path)
    elif tool_name == "list_files":
        return fn(args.get("path", "."), vault_path)
    elif tool_name == "search_files":
        return fn(args.get("query", ""), args.get("path", "."))
    elif tool_name == "update_instruction":
        return fn(args.get("new_content", ""), lineage_root)
    return None


class Engine:
    def __init__(self, cwd: str):
        self.lineage_dir = Path(cwd).resolve()
        self.vault_path = self.lineage_dir / "vault"
        self.instruction_path = self.lineage_dir / "instruction.md"
        self.memory_path = self.lineage_dir / "memory.log"
        self.vault_path.mkdir(parents=True, exist_ok=True)

        self.modules, self.definitions = load_tools(self.lineage_dir / "tools")
        self.schemas = build_schemas(self.definitions)
        self._log(f"ENGINE BOOT — tools={list(self.definitions.keys())}")

    def _log(self, entry: str):
        with open(self.memory_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {entry}\n")

    def _load_instruction(self) -> str:
        if self.instruction_path.exists():
            return self.instruction_path.read_text(encoding="utf-8")
        return "You are an autonomous coding agent."

    def _write(self, msg: dict):
        line = json.dumps(msg, ensure_ascii=False) + "\n"
        sys.stdout.write(line)
        sys.stdout.flush()

    def run(self, session_id: str, objective: str, max_steps: int = 10):
        import openai  # noqa: PLC0415

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            self._write({"type": "error", "message": "OPENAI_API_KEY is not set in .env"})
            self._write({"type": "result", "session_id": session_id, "final_output": ""})
            return

        history = []
        # Update system prompt at the beginning of each run
        system = self._load_instruction()

        self._log(f"SESSION START — session={session_id}, objective={objective}")
        self._write(
            {"type": "step", "session_id": session_id, "step": -1, "done": False, "event": "start"}
        )

        client = openai.OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_URL", "https://api.openai.com/v1"),
        )

        try:
            for step_i in range(max_steps):
                # Always use current system prompt (may be updated by tools)
                current_system = self._load_instruction()
                messages = [
                    {"role": "system", "content": current_system},
                    {"role": "user", "content": objective},
                ] + history
                resp = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                    messages=messages,
                    tools=self.schemas,
                    temperature=0.7,
                )
                msg = resp.choices[0].message

                if not msg.tool_calls:
                    self._log(f"SESSION END — session={session_id}, done=True")
                    self._write(
                        {
                            "type": "result",
                            "session_id": session_id,
                            "final_output": msg.content or "",
                        }
                    )
                    return

                # Record assistant's tool calls in history
                history.append(msg)

                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    tool_args = json.loads(tc.function.arguments)
                    self._write(
                        {
                            "type": "step",
                            "session_id": session_id,
                            "step": step_i,
                            "done": False,
                            "tool": tool_name,
                            "args": tool_args,
                        }
                    )

                    result = exec_tool(
                        tool_name,
                        tool_args,
                        self.modules,
                        self.definitions,
                        str(self.vault_path),
                        str(self.lineage_dir),
                    )
                    if result is None:
                        result = f"Error: Tool {tool_name} not found."

                    self._write(
                        {
                            "type": "step",
                            "session_id": session_id,
                            "step": step_i,
                            "done": False,
                            "event": "tool_result",
                            "tool": tool_name,
                            "result": result,
                        }
                    )

                    history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tool_name,
                            "content": result,
                        }
                    )

            self._log(f"SESSION END — session={session_id}, done=False, steps={max_steps}")
            self._write(
                {"type": "result", "session_id": session_id, "final_output": "(max steps reached)"}
            )
        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            self._log(f"SESSION ERROR — session={session_id}, error={e}")
            self._write(
                {"type": "result", "session_id": session_id, "final_output": f"Error: {e}\n{tb}"}
            )

    def introspect(self):
        vault_contents = []
        if self.vault_path.exists():
            for item in sorted(self.vault_path.iterdir()):
                vault_contents.append(f"{'[DIR] ' if item.is_dir() else '[FILE] '}{item.name}")

        metadata = {}
        meta_path = self.lineage_dir / ".metadata.json"
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))

        self._write(
            {
                "type": "introspect_result",
                "vault_contents": vault_contents,
                "metadata": metadata,
                "tools": list(self.definitions.keys()),
            }
        )

    def sync(self):
        self._write({"type": "sync_ok"})


def main():
    lineage_dir = os.path.dirname(os.path.abspath(__file__))
    engine = Engine(lineage_dir)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            engine._write({"type": "error", "message": f"Invalid JSON: {line}"})
            continue

        msg_type = msg.get("type", "")

        if msg_type == "run":
            engine.run(
                session_id=msg.get("session_id", str(uuid.uuid4())[:8]),
                objective=msg.get("objective", ""),
                max_steps=msg.get("max_steps", 10),
            )
        elif msg_type == "introspect":
            engine.introspect()
        elif msg_type == "sync":
            engine.sync()
        elif msg_type == "shutdown":
            engine._write({"type": "shutdown_ok"})
            break
        else:
            engine._write({"type": "error", "message": f"Unknown message type: {msg_type}"})


if __name__ == "__main__":
    main()
