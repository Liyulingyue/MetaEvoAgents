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
    elif tool_name == "broadcast_event":
        return fn(args.get("type", "INFO"), args.get("message", ""), lineage_root)
    elif tool_name == "pray":
        return fn(args.get("content", ""), lineage_root)
    elif tool_name == "delegate_task":
        return fn(args.get("target_lineage_id", ""), args.get("message", ""), lineage_root)
    elif tool_name == "birth":
        return fn(args.get("child_id", ""), lineage_root)
    return None


class Engine:
    def __init__(self, cwd: str):
        self.lineage_dir = Path(cwd).resolve()
        self.vault_path = self.lineage_dir / "vault"
        self.instruction_path = self.lineage_dir / "instruction.md"
        self.memory_path = self.lineage_dir / "memory.md"
        self.history_path = self.lineage_dir / "history.json"
        self.vault_path.mkdir(parents=True, exist_ok=True)

        self.modules, self.definitions = load_tools(self.lineage_dir / "tools")
        self.schemas = build_schemas(self.definitions)
        self._log(f"ENGINE BOOT — tools={list(self.definitions.keys())}")

    def _log(self, entry: str):
        with open(self.memory_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {entry}\n")

    def _load_history(self) -> list:
        if self.history_path.exists():
            try:
                return json.loads(self.history_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_history(self, history: list):
        # 转换工具调用对象为可序列化字典
        serializable = []
        for m in history:
            if hasattr(m, "model_dump"):
                serializable.append(m.model_dump())
            else:
                serializable.append(m)
        self.history_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")

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

        # 加载历史记录 (短期会话历史)
        history = self._load_history()
        # 限制历史记录长度
        if len(history) > 20:
            history = history[-20:]

        self._log(f"SESSION START — session={session_id}, objective={objective}")
        self._write(
            {"type": "step", "session_id": session_id, "step": -1, "done": False, "event": "start"}
        )

        client = openai.OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_URL", "https://api.openai.com/v1"),
        )

        # 将当前用户目标作为新的 user 消息加入历史
        history.append({"role": "user", "content": objective})

        try:
            for step_i in range(max_steps):
                # 每次循环更新系统指令
                current_system = self._load_instruction()
                messages = [{"role": "system", "content": current_system}] + history
                
                resp = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                    messages=messages,
                    tools=self.schemas,
                    temperature=0.7,
                )
                msg_obj = resp.choices[0].message
                # 转换为字典以便存储
                msg_dict = msg_obj.model_dump()

                # 记录思考内容
                if msg_obj.content:
                    self._log(f"THOUGHT: {msg_obj.content}")

                if not msg_obj.tool_calls:
                    self._log(f"FINAL OUTPUT: {msg_obj.content or ''}")
                    self._log(f"SESSION END — session={session_id}, done=True")
                    
                    # 保存包含最后回答的历史
                    history.append(msg_dict)
                    self._save_history(history)
                    
                    self._write(
                        {
                            "type": "result",
                            "session_id": session_id,
                            "final_output": msg_obj.content or "",
                        }
                    )
                    return

                # Record assistant's tool calls in history
                history.append(msg_dict)

                for tc in msg_obj.tool_calls:
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
                    self._log(f"TOOL CALL — {tool_name}({tc.function.arguments})")

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
                    
                    # 记录工具执行结果
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tool_name,
                        "content": str(result)
                    })

                    if tool_name == "birth" and "Success" in str(result):
                        child_id = tool_args.get("child_id")
                        self._write(
                            {
                                "type": "born_notification",
                                "child_id": child_id,
                                "parent_id": self.lineage_dir.name,
                            }
                        )

                    self._write(
                        {
                            "type": "step",
                            "session_id": session_id,
                            "step": step_i,
                            "done": False,
                            "tool": tool_name,
                            "result": result,
                        }
                    )
            
            # 步数用尽，保存现状
            self._save_history(history)
            self._write({"type": "result", "session_id": session_id, "final_output": "Max steps reached."})

        except Exception as e:
            self._log(f"ERROR: {str(e)}")
            self._write({"type": "error", "message": str(e)})

    def introspect(self):
        vault_contents = []
        if self.vault_path.exists():
            for f in self.vault_path.rglob("*"):
                if f.is_file():
                    vault_contents.append(str(f.relative_to(self.vault_path)))
        metadata = {
            "instruction": self._load_instruction(),
            "lineage_id": self.lineage_dir.name,
        }
        tools = list(self.definitions.keys())
        self._write(
            {
                "type": "introspect_result",
                "vault_contents": vault_contents,
                "metadata": metadata,
                "tools": tools,
            }
        )

    def handle_stdin(self):
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                cmd = json.loads(line)
                ctype = cmd.get("type")
                if ctype == "run":
                    self.run(
                        cmd.get("session_id", str(uuid.uuid4())),
                        cmd.get("objective", "Wait for instruction."),
                        cmd.get("max_steps", 10),
                    )
                elif ctype == "introspect":
                    self.introspect()
                elif ctype == "sync":
                    self._write({"type": "sync_ok"})
                elif ctype == "shutdown":
                    sys.exit(0)
            except Exception as e:
                self._write({"type": "error", "message": f"STDIN ERROR: {str(e)}"})


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", help="Lineage root directory", default=os.getcwd())
    args = parser.parse_args()

    engine = Engine(args.cwd)
    engine.handle_stdin()

