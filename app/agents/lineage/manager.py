import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from app.agents.lineage.entity import LineageAgent
from app.core.config import settings


def init_workspace():
    for sub in ("lineages", "academy", "inner", "shrine"):
        (settings.workspace_root / sub).mkdir(parents=True, exist_ok=True)


def _bootstrap_lineage(lineage_id: str, lineage_path: Path) -> dict:
    templates_root = settings.templates_root
    shutil.copytree(templates_root, lineage_path, dirs_exist_ok=True)

    uid = str(uuid.uuid4())[:8]
    meta = {
        "uid": uid,
        "created_at": datetime.now().isoformat(),
        "parent_lineage_id": None,
        "template": "default",
    }
    meta_path = lineage_path / ".metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    env_path = lineage_path / ".env"
    env_path.write_text(
        f"OPENAI_API_KEY={settings.openai_api_key}\n"
        f"OPENAI_URL={settings.openai_url}\n"
        f"OPENAI_MODEL_NAME={settings.openai_model_name}\n",
        encoding="utf-8",
    )

    mem_path = lineage_path / "memory.log"
    with mem_path.open("a", encoding="utf-8") as f:
        f.write(
            f"[{datetime.now().isoformat()}] LINEAGE BORN\n"
            f"  UID: {uid}\n"
            f"  Lineage ID: {lineage_id}\n"
        )

    return meta


class LineageManager:
    def __init__(self):
        self.lineages: dict[str, LineageAgent] = {}
        init_workspace()

    def create(self, lineage_id: str) -> LineageAgent:
        lineage_path = settings.workspace_root / "lineages" / lineage_id
        if not lineage_path.exists():
            _bootstrap_lineage(lineage_id, lineage_path)
        return self.load(lineage_id)

    def load(self, lineage_id: str) -> LineageAgent:
        if lineage_id in self.lineages:
            return self.lineages[lineage_id]
        lineage_path = settings.workspace_root / "lineages" / lineage_id
        agent = LineageAgent(
            lineage_path,
            openai_api_key=settings.openai_api_key,
            openai_url=settings.openai_url,
            openai_model_name=settings.openai_model_name,
        )
        self.lineages[lineage_id] = agent
        return agent

    def all(self) -> dict[str, LineageAgent]:
        return self.lineages

    def exists(self, lineage_id: str) -> bool:
        return (settings.workspace_root / "lineages" / lineage_id).exists()
