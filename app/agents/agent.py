import uuid
import json
from pathlib import Path
from typing import Optional, Callable

from app.core.config import settings
from app.agents.llm import LLMClient
from app.agents.tools import CodeTools, handle_tool_call


workspace_root = settings.workspace_root

SYSTEM_PROMPT = """You are an autonomous coding agent in a digital civilization simulator.
Your goal is to solve the user's request by taking action in the local environment.

RULES:
1. Use tools to explore, read, write files, and run commands as needed.
2. Start by exploring the environment if needed (use `list_files` or `execute_bash`).
3. After writing code, verify it by running tests or checking file content.
4. If a task is complex, break it down: Plan -> Action -> Verify.
5. Be concise and professional.

Current working directory: {workspace_path}
"""


def build_system_prompt(workspace_path: str) -> str:
    return SYSTEM_PROMPT.format(workspace_path=workspace_path)


def init_workspace():
    for sub in ("lineage", "heritage", "guixu"):
        (workspace_root / sub).mkdir(parents=True, exist_ok=True)


init_workspace()


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

            self.history.append(message)
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
