from app.agents.result import AgentResult
from app.agents.lineage import LineageAgent, LineageManager
from app.agents.llm import LLMClient
from app.agents.tools import CodeTools, handle_tool_call, TOOL_SCHEMAS


def __getattr__(name: str):
    if name == "InnerAgent":
        from app.agents.inner import InnerAgent
        return InnerAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
