import uuid
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from app.core.config import settings
from app.agents.llm import LLMClient
from app.agents.tools import CodeTools, handle_tool_call, register_agent_tool
from app.agents.result import AgentResult, message_to_dict


class LineageAgent:
    lineage_root: Path
    lineage_id: str
    vault_path: Path
    logs_path: Path
    kernel_path: Path
    metadata: dict
    instruction: str
    system_prompt: str
    assets: str

    def __init__(self, lineage_root: Path):
        self.lineage_root = Path(lineage_root).resolve()
        self.lineage_id = self.lineage_root.name
        self.vault_path = self.lineage_root / "vault"
        self.logs_path = self.lineage_root / "logs"
        self.kernel_path = self.lineage_root / "kernel.py"

        if not self.lineage_root.exists():
            self._bootstrap_from_template()

        self._load_identity()
        self._lock_permissions()
        self._introspect()

    def _bootstrap_from_template(self):
        templates_root = settings.templates_root
        shutil.copytree(templates_root, self.lineage_root, dirs_exist_ok=True)
        self._record_birth()

    def _record_birth(self):
        metadata = self._read_metadata()
        metadata["uid"] = str(uuid.uuid4())[:8]
        metadata["created_at"] = datetime.now().isoformat()
        self._write_metadata(metadata)

        with self.lineage_root.joinpath("memory.log").open("a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().isoformat()}] LINEAGE BORN\n"
                f"  UID: {metadata['uid']}\n"
                f"  Template: {metadata.get('template', 'default')}\n"
                f"  Lineage ID: {self.lineage_id}\n"
            )

    def _load_identity(self):
        self.metadata = self._read_metadata()
        self.instruction = self.lineage_root.joinpath("instruction.md").read_text(encoding="utf-8")
        self.system_prompt = self.instruction

    def _lock_permissions(self):
        CodeTools.set_workspace(str(self.vault_path))
        register_agent_tool("update_instruction", self._tool_update_instruction)

    def _introspect(self):
        vault_contents = CodeTools.list_files(str(self.vault_path))
        self.assets = vault_contents
        self._append_memory(
            f"[{datetime.now().isoformat()}] INTROSPECTION\n"
            f"  Vault contents: {vault_contents}\n"
        )

    def _read_metadata(self) -> dict:
        return json.loads(
            self.lineage_root.joinpath(".metadata.json").read_text(encoding="utf-8")
        )

    def _write_metadata(self, data: dict):
        self.lineage_root.joinpath(".metadata.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _append_memory(self, entry: str):
        with self.lineage_root.joinpath("memory.log").open("a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def _tool_update_instruction(self, new_content: str) -> str:
        self.lineage_root.joinpath("instruction.md").write_text(new_content, encoding="utf-8")
        self.instruction = new_content
        self.system_prompt = new_content
        self.sync_to_disk()
        self._append_memory(
            f"[{datetime.now().isoformat()}] INSTRUCTION UPDATED\n"
            f"  Length: {len(new_content)} chars\n"
        )
        return "Instruction updated successfully."

    def sync_to_disk(self):
        self._write_metadata(self.metadata)
        self.lineage_root.joinpath("instruction.md").write_text(
            self.instruction, encoding="utf-8"
        )

    def run(
        self,
        objective: str,
        max_steps: int = 10,
        streaming: bool = False,
        on_step: Optional[Callable] = None,
    ):
        self.system_prompt = self.lineage_root.joinpath("instruction.md").read_text(encoding="utf-8")

        session_id = str(uuid.uuid4())[:8]
        history = [{"role": "user", "content": f"Your objective: {objective}"}]
        steps = []

        self._append_memory(
            f"[{datetime.now().isoformat()}] SESSION START\n"
            f"  Session ID: {session_id}\n"
            f"  Objective: {objective}\n"
        )

        for step_i in range(max_steps):
            llm = LLMClient()
            messages = [{"role": "system", "content": self.system_prompt}] + history
            message = llm.run(messages)

            step = {"step": step_i, "message": message, "done": False}

            if not message.tool_calls:
                step["done"] = True
                final_output = message.content or ""
                steps.append(step)
                self._log_session(session_id, steps)
                if streaming:
                    self._print_step(step)
                    if on_step:
                        on_step(step)
                return AgentResult(session_id, steps, final_output)

            for tc in message.tool_calls:
                result = handle_tool_call(tc.function.name, json.loads(tc.function.arguments))
                self.sync_to_disk()
                history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": result,
                })
                step["tool_result"] = result

            history.append(message_to_dict(message))
            steps.append(step)

            if streaming:
                self._print_step(step)
                if on_step:
                    on_step(step)

        self._log_session(session_id, steps)
        return AgentResult(
            session_id=session_id,
            steps=steps,
            final_output=steps[-1].get("tool_result", "") if steps else "",
        )

    def _log_session(self, session_id: str, steps: list):
        self.logs_path.mkdir(exist_ok=True)
        self.logs_path.joinpath(f"{session_id}.log").write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "steps": len(steps),
                    "timestamp": datetime.now().isoformat(),
                    "vault": str(self.vault_path),
                    "lineage_id": self.lineage_id,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _print_step(self, step):
        print(f"\n{'='*50}")
        print(f"[Step {step['step']}]")
        message = step["message"]

        if message.tool_calls:
            tools = [tc.function.name for tc in message.tool_calls]
            print(f"Tools: {', '.join(tools)}")
            if "tool_result" in step:
                result = step["tool_result"]
                print(f"Output:\n{result[:500]}..." if len(result) > 500 else f"Output:\n{result}")
        else:
            print(f"Response: {message.content}")

        if step["done"]:
            print("Done!")
