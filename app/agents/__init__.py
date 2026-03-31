from app.agents.lineage import LineageAgent as LineageAgent  # noqa: F401
from app.agents.lineage import LineageManager as LineageManager  # noqa: F401
from app.agents.llm import LLMClient as LLMClient  # noqa: F401
from app.agents.result import AgentResult as AgentResult  # noqa: F401

__all__ = ["LineageAgent", "LineageManager", "LLMClient", "AgentResult", "InnerAgent"]


def __getattr__(name: str):
    if name == "InnerAgent":
        from app.agents.inner import InnerAgent

        return InnerAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
