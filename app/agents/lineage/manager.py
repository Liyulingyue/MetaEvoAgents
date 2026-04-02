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
    
    # 初始化世界日志
    world_log_path = settings.workspace_root / "world_log.md"
    if not world_log_path.exists():
        world_log_path.write_text("# 世界日志 (World Log)\n\n这里记录着文明的大事记。\n\n", encoding="utf-8")

    # 初始化祭坛 (Shrine)
    shrine_dir = settings.workspace_root / "shrine"
    shrine_dir.mkdir(parents=True, exist_ok=True)
    
    prayer_path = shrine_dir / "prayer.md"
    if not prayer_path.exists():
        prayer_path.write_text("# 祈祷书 (Prayer Book)\n\n这里记录着众生对造物主的祈求与低语。\n\n", encoding="utf-8")
        
    revelation_path = shrine_dir / "revelation.md"
    if not revelation_path.exists():
        revelation_path.write_text("# 启示录 (Revelation)\n\n来自造物主的最高指示与真理。\n\n", encoding="utf-8")

    # 初始生命序列初始化逻辑
    lineages_dir = settings.workspace_root / "lineages"
    if not any(path.is_dir() for path in lineages_dir.iterdir()):
        print("当前 Workspace 为空。正在初始化初始生命序列 Lineage-01 和 Lineage-02...")
        _bootstrap_lineage("Lineage-01", lineages_dir / "Lineage-01")
        _bootstrap_lineage("Lineage-02", lineages_dir / "Lineage-02")


def _bootstrap_lineage(lineage_id: str, lineage_path: Path) -> dict:
    templates_root = settings.templates_root
    shutil.copytree(templates_root, lineage_path, dirs_exist_ok=True)

    uid = str(uuid.uuid4())[:8]
    meta = {
        "uid": uid,
        "created_at": datetime.now().isoformat(),
        "parent_lineage_id": None,
        "template": settings.active_template,
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

    mem_path = lineage_path / "memory.md"
    with mem_path.open("a", encoding="utf-8") as f:
        f.write(f"# Memory Log\n\n[{datetime.now().isoformat()}] LINEAGE BORN\n")
        f.write(f"- UID: {uid}\n")
        f.write(f"- Lineage ID: {lineage_id}\n")

    return meta


class LineageManager:
    def __init__(self):
        self.lineages: dict[str, LineageAgent] = {}
        self.settings = settings
        init_workspace()

    def clear(self):
        """纯粹清空整个 workspace，但保留根目录及 .gitkeep 文件（如果存在）"""
        if settings.workspace_root.exists():
            for item in settings.workspace_root.iterdir():
                if item.name == ".gitkeep":
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        self.lineages = {}

    def reset(self):
        """重置整个 workspace，清空并重新初始化基础结构"""
        self.clear()
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
        agent = LineageAgent(lineage_path)
        self.lineages[lineage_id] = agent
        return agent

    def all(self) -> dict[str, LineageAgent]:
        return self.lineages

    def exists(self, lineage_id: str) -> bool:
        return (settings.workspace_root / "lineages" / lineage_id).exists()

    def register_newborn(self, child_id: str):
        """登记新生的 LineageAgent"""
        if child_id not in self.lineages:
            self.load(child_id)
