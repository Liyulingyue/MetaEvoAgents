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
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 加载模块化组件
from core.tools_handler import load_tools, build_schemas, exec_tool
from core.persistence import Persistence

load_dotenv(Path(__file__).resolve().parent / ".env")


class Engine:
    def __init__(self, cwd: str):
        self.lineage_dir = Path(cwd).resolve()
        self.vault_path = self.lineage_dir / "vault"
        self.instruction_path = self.lineage_dir / "instruction.md"
        self.memory_path = self.lineage_dir / "memory.md"
        self.history_path = self.lineage_dir / "history.json"
        self.status_path = self.lineage_dir / "status.json"
        self.vault_path.mkdir(parents=True, exist_ok=True)

        # 初始化模块化组件
        self.persistence = Persistence(self.history_path, self.instruction_path)
        self.modules, self.definitions = load_tools(self.lineage_dir / "tools")
        self.schemas = build_schemas(self.definitions)
        
        self._update_status("IDLE")
        self._log(f"ENGINE BOOT (Modularized) — tools={list(self.definitions.keys())}")

    def _update_status(self, status: str, extra: dict = None):
        """自治的状态更新：直接写入物理文件面板"""
        data = {
            "status": status,
            "last_update": datetime.now().isoformat(),
            "pid": os.getpid(),
        }
        if extra:
            data.update(extra)
        
        with open(self.status_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _log(self, entry: str):
        with open(self.memory_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {entry}\n")

    def _write(self, msg: dict):
        line = json.dumps(msg, ensure_ascii=False) + "\n"
        sys.stdout.write(line)
        sys.stdout.flush()

    def run(self, session_id: str, objective: str, max_steps: int = 10):
        import openai  # noqa: PLC0415

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            self._write({"type": "error", "message": "OPENAI_API_KEY is not set in .env"})
            return

        # 使用 Persistence 组件加载历史
        history = self.persistence.load_history()
        if len(history) > 30:
            history = history[-30:]

        self._update_status("BUSY", {"session_id": session_id, "objective": objective})
        self._log(f"SESSION START — session={session_id}, objective={objective}")
        self._write(
            {"type": "step", "session_id": session_id, "step": -1, "done": False, "event": "start"}
        )

        client = openai.OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_URL", "https://api.openai.com/v1"),
        )

        history.append({"role": "user", "content": objective})

        try:
            for step_i in range(max_steps):
                current_system = self.persistence.load_instruction()
                messages = [{"role": "system", "content": current_system}] + history
                
                resp = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                    messages=messages,
                    tools=self.schemas,
                    temperature=0.7,
                )
                msg_obj = resp.choices[0].message
                msg_dict = msg_obj.model_dump()

                if msg_obj.content:
                    self._log(f"THOUGHT: {msg_obj.content}")

                if not msg_obj.tool_calls:
                    self._log(f"FINAL OUTPUT: {msg_obj.content or ''}")
                    history.append(msg_dict)
                    self.persistence.save_history(history)
                    
                    self._write(
                        {
                            "type": "result",
                            "session_id": session_id,
                            "final_output": msg_obj.content or "",
                        }
                    )
                    return

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

                    # 使用 ToolsHandler 组件执行工具
                    result = exec_tool(
                        tool_name,
                        tool_args,
                        self.modules,
                        self.definitions,
                        str(self.vault_path),
                        str(self.lineage_dir),
                    )
                    
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tool_name,
                        "content": str(result)
                    })

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
            
            self.persistence.save_history(history)
            self._write({"type": "result", "session_id": session_id, "final_output": "Max steps reached."})

        except Exception as e:
            self._log(f"ERROR: {str(e)}")
            self._write({"type": "error", "message": str(e)})
        finally:
            self._update_status("IDLE")

    def introspect(self):
        vault_contents = [str(f.relative_to(self.vault_path)) for f in self.vault_path.rglob("*") if f.is_file()]
        metadata = {
            "instruction": self.persistence.load_instruction(),
            "lineage_id": self.lineage_dir.name,
        }
        self._write(
            {
                "type": "introspect_result",
                "vault_contents": vault_contents,
                "metadata": metadata,
                "tools": list(self.definitions.keys()),
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


