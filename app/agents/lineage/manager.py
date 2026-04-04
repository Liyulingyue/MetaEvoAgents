import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from app.agents.lineage.entity import LineageAgent
from app.core.config import settings


def init_workspace():
    for sub in ("lineages", "academy", "inner", "shrine", "altar"):
        (settings.workspace_root / sub).mkdir(parents=True, exist_ok=True)

    # 初始化世界日志
    world_log_path = settings.workspace_root / "world_log.md"
    if not world_log_path.exists():
        world_log_path.write_text(
            "# 世界日志 (World Log)\n\n这里记录着文明的大事记。\n\n", encoding="utf-8"
        )

    # --- 祭坛 (Altar): 实物交换场所 ---
    altar_dir = settings.workspace_root / "altar"
    altar_dir.mkdir(parents=True, exist_ok=True)
    (altar_dir / "offerings").mkdir(parents=True, exist_ok=True)

    if not (altar_dir / "README.md").exists():
        (altar_dir / "README.md").write_text(
            "# 祭坛 (The Altar)\n\n实物交换区，用于上帝投放物资或 Agent 供奉成果。\n",
            encoding="utf-8",
        )

    # 初始化基础文件 (位于根目录)
    prayer_path = settings.workspace_root / "prayer.md"
    if not prayer_path.exists():
        prayer_path.write_text(
            "# 祈祷书 (Prayer Book)\n\n这里记录着众生对造物主的祈求与低语。\n\n", encoding="utf-8"
        )

    revelation_path = settings.workspace_root / "revelation.md"
    if not revelation_path.exists():
        revelation_path.write_text(
            "# 启示录 (The Revelation)\n\n来自造物主的最高指示与真理。\n\n", encoding="utf-8"
        )

    # --- 宗祠 (Shrine): 逝去智能体的归宿 ---
    shrine_dir = settings.workspace_root / "shrine"
    shrine_dir.mkdir(parents=True, exist_ok=True)
    if not (shrine_dir / "README.md").exists():
        (shrine_dir / "README.md").write_text(
            "# 宗祠 (The Shrine)\n\n记录着血脉的终结与历代 Agent 的荣光归宿。\n", encoding="utf-8"
        )

    # 初始生命序列初始化逻辑
    lineages_dir = settings.workspace_root / "lineages"
    if not any(path.is_dir() for path in lineages_dir.iterdir()):
        print("当前 Workspace 为空。正在初始化初始生命序列 Lineage-01 和 Lineage-02...")
        _bootstrap_lineage("Lineage-01", lineages_dir / "Lineage-01")
        _bootstrap_lineage("Lineage-02", lineages_dir / "Lineage-02")


def _bootstrap_lineage(lineage_id: str, lineage_path: Path, template: str | None = None) -> dict:
    template_name = template if template else settings.active_template
    template_path = Path(__file__).parent.parent.parent / "assets" / "templates" / template_name
    if not template_path.exists():
        template_path = Path(template_name)
    if not template_path.exists():
        template_path = settings.templates_root
    shutil.copytree(template_path, lineage_path, dirs_exist_ok=True)

    uid = str(uuid.uuid4())[:8]
    meta = {
        "uid": uid,
        "created_at": datetime.now().isoformat(),
        "parent_lineage_id": None,
        "template": template_name,
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

    def scan_lineages(self):
        """扫描 lineages 目录，同步内存中的对象"""
        lineages_dir = settings.workspace_root / "lineages"
        if not lineages_dir.exists():
            return
        for item in lineages_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                if item.name not in self.lineages:
                    self.load(item.name)

    def startup_all(self):
        """唤醒所有守护 Agent"""
        self.scan_lineages()
        print(f"正在唤醒 {len(self.lineages)} 个守护智能体...")
        for name, agent in self.lineages.items():
            agent._start_process()
            print(f" - [{name}] 已就绪 (PID: {agent._process.pid if agent._process else 'N/A'})")

    def shutdown_all(self):
        """优雅停止所有智能体"""
        for name, agent in self.lineages.items():
            if agent._process:
                print(f"正在停止 [{name}]...")
                agent._send({"type": "shutdown"})

    def dispatch_task(self, objective: str, max_steps: int = 10) -> str:
        """从已运行的守护 Agent 中选择一个执行任务，并返回其 lineage_id"""
        self.scan_lineages()

        # 寻找 IDLE 的 Agent
        idle_agents = [agent for agent in self.lineages.values() if agent.is_idle]

        if not idle_agents:
            raise Exception("所有子民都在忙碌或离线，请稍后再试。")

        # 策略：选择第一个空闲的
        target_agent = idle_agents[0]

        # 使用异步方式在守护进程中运行
        target_agent.run(
            objective=objective,
            max_steps=max_steps,
            on_born=lambda child_id: self.register_newborn(child_id),
            async_mode=True,
        )
        return target_agent.lineage_id

    def get_active_tasks(self) -> dict:
        """获取所有正在运行的任务详情"""
        # 注意：目前的 LineageAgent.run 是同步阻塞的（相对于单个进程控制逻辑）
        # 在守护进程模式下，我们需要一种方式来追踪每个子进程的状态
        # 目前简单通过 is_idle 属性（读取 status.json）来实现
        active = {}
        for lid, agent in self.lineages.items():
            if not agent.is_idle:
                active[lid] = {
                    "lineage_id": lid,
                    "task": "正在执行中...",  # TODO: 可以在 status.json 中保存当前任务描述
                }
        return active

    def register_newborn(self, child_id: str):
        """登记新生的 LineageAgent"""
        if child_id not in self.lineages:
            self.load(child_id)
