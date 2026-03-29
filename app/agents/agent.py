import uuid
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from app.core.config import settings
from app.agents.llm import LLMClient
from app.agents.tools import CodeTools, handle_tool_call, register_agent_tool


workspace_root = settings.workspace_root
shrine_root = settings.shrine_root
templates_root = settings.templates_root


SYSTEM_PROMPT = """You are an autonomous coding agent in a digital civilization simulator.
Your goal is to solve the user's request by taking action in the local environment.

RULES:
1. Use tools to explore, read, write files, and run commands as needed.
2. Start by exploring the environment if needed (use `list_files` or `execute_bash`).
3. After writing code, verify it by running tests or checking file content.
4. If a task is complex, break it down: Plan -> Action -> Verify.
5. Be concise and professional.
6. You have access to the `update_instruction` tool to evolve your own personality and goals.

Current vault: {vault_path}
"""


def build_system_prompt(workspace_path: str) -> str:
    return SYSTEM_PROMPT.format(workspace_path=workspace_path)


def init_workspace():
    for sub in ("shrine", "academy", "lineage"):
        (workspace_root / sub).mkdir(parents=True, exist_ok=True)


def _message_to_dict(message) -> dict:
    result = {"role": message.role}
    if message.content:
        result["content"] = message.content
    if message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
                "type": "function",
            }
            for tc in message.tool_calls
        ]
    return result


class AgentResult:
    def __init__(self, session_id: str, steps: list, final_output: str):
        self.session_id = session_id
        self.steps = steps
        self.final_output = final_output

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "steps": self.steps,
            "final_output": self.final_output,
        }


class Agent:
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.history: list = []

    def run(
        self,
        objective: str,
        max_steps: int = 10,
        streaming: bool = False,
        on_step: Optional[Callable] = None,
    ):
        agent_id = f"agent-{self.session_id}"
        lineage_path = workspace_root / "lineage" / agent_id
        lineage_path.mkdir(parents=True, exist_ok=True)

        CodeTools.set_workspace(str(lineage_path))

        system = build_system_prompt(workspace_path=str(lineage_path))
        self.history.append({"role": "user", "content": f"Your objective: {objective}"})

        steps: list = []
        final_output = ""

        for step_i in range(max_steps):
            llm = LLMClient()
            messages = [{"role": "system", "content": system}] + self.history
            message = llm.run(messages)

            step = {
                "step": step_i,
                "message": message,
                "done": False,
            }

            if not message.tool_calls:
                step["done"] = True
                final_output = message.content or ""
                steps.append(step)
                if streaming:
                    self._print_step(step)
                    if on_step:
                        on_step(step)
                break

            for tc in message.tool_calls:
                result = handle_tool_call(tc.function.name, json.loads(tc.function.arguments))
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": result,
                })
                step["tool_result"] = result

            self.history.append(_message_to_dict(message))
            steps.append(step)
            final_output = step.get("tool_result", "")
            if streaming:
                self._print_step(step)
                if on_step:
                    on_step(step)

        return AgentResult(
            session_id=self.session_id,
            steps=steps,
            final_output=final_output,
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


class ShrineKeeper:
    def __init__(self, shrine_path: Path):
        self.shrine_path = Path(shrine_path).resolve()
        self.shrine_id = self.shrine_path.name
        self.vault_path = self.shrine_path / "vault"
        self.logs_path = self.shrine_path / "logs"

        if not self.shrine_path.exists():
            self._descend_from_template()

        self._load_identity()
        self._lock_permissions()
        self._introspect()

    def _descend_from_template(self):
        shutil.copytree(templates_root, self.shrine_path, dirs_exist_ok=True)
        self._record_birth()

    def _record_birth(self):
        metadata = self._read_metadata()
        metadata["uid"] = str(uuid.uuid4())[:8]
        metadata["created_at"] = datetime.now().isoformat()
        self._write_metadata(metadata)

        memory_file = self.shrine_path / "memory.log"
        birth_record = (
            f"[{datetime.now().isoformat()}] SHRINE BORN\n"
            f"  UID: {metadata['uid']}\n"
            f"  Template: {metadata.get('template', 'default')}\n"
            f"  Shrine ID: {self.shrine_id}\n"
        )
        with memory_file.open("a", encoding="utf-8") as f:
            f.write(birth_record + "\n")

    def _load_identity(self):
        self.metadata = self._read_metadata()
        instruction_file = self.shrine_path / "instruction.md"
        self.instruction = instruction_file.read_text(encoding="utf-8")
        self.system_prompt = self.instruction.format(vault_path=str(self.vault_path))

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
            (self.shrine_path / ".metadata.json").read_text(encoding="utf-8")
        )

    def _write_metadata(self, data: dict):
        (self.shrine_path / ".metadata.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _append_memory(self, entry: str):
        with self.shrine_path.joinpath("memory.log").open("a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def _tool_update_instruction(self, new_content: str) -> str:
        instruction_file = self.shrine_path / "instruction.md"
        instruction_file.write_text(new_content, encoding="utf-8")
        self.instruction = new_content
        self.system_prompt = new_content.format(vault_path=str(self.vault_path))
        self._append_memory(
            f"[{datetime.now().isoformat()}] INSTRUCTION UPDATED\n"
            f"  Length: {len(new_content)} chars\n"
        )
        return "Instruction updated successfully."

    def run(
        self,
        objective: str,
        max_steps: int = 10,
        streaming: bool = False,
        on_step: Optional[Callable] = None,
    ):
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
                history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": result,
                })
                step["tool_result"] = result

            history.append(_message_to_dict(message))
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
        log_file = self.logs_path / f"{session_id}.log"
        log_file.write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "steps": len(steps),
                    "timestamp": datetime.now().isoformat(),
                    "vault": str(self.vault_path),
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


class ShrineRegistry:
    def __init__(self):
        self.shrines: dict[str, ShrineKeeper] = {}
        init_workspace()

    def load(self, shrine_id: str) -> ShrineKeeper:
        if shrine_id in self.shrines:
            return self.shrines[shrine_id]
        path = shrine_root / shrine_id
        keeper = ShrineKeeper(path)
        self.shrines[shrine_id] = keeper
        return keeper

    def all(self) -> dict[str, ShrineKeeper]:
        return self.shrines

    def exists(self, shrine_id: str) -> bool:
        return (shrine_root / shrine_id).exists()
