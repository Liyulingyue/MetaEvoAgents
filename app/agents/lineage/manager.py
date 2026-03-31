from app.agents.lineage.entity import LineageAgent
from app.core.config import settings


def init_workspace():
    for sub in ("lineages", "academy", "inner", "shrine"):
        (settings.workspace_root / sub).mkdir(parents=True, exist_ok=True)


class LineageManager:
    def __init__(self):
        self.lineages: dict[str, LineageAgent] = {}
        init_workspace()

    def load(self, lineage_id: str) -> LineageAgent:
        if lineage_id in self.lineages:
            return self.lineages[lineage_id]
        path = settings.workspace_root / "lineages" / lineage_id
        agent = LineageAgent(path)
        self.lineages[lineage_id] = agent
        return agent

    def all(self) -> dict[str, LineageAgent]:
        return self.lineages

    def exists(self, lineage_id: str) -> bool:
        return (settings.workspace_root / "lineages" / lineage_id).exists()
