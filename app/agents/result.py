from dataclasses import dataclass
from typing import Any


@dataclass
class AgentResult:
    session_id: str
    steps: list
    final_output: str

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "steps": self.steps,
            "final_output": self.final_output,
        }


def message_to_dict(message) -> dict:
    result: dict[str, Any] = {"role": message.role}
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
