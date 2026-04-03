from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.routes.shared import manager, settings

world_router = APIRouter(prefix="/agent", tags=["world"])


class RevelationRequest(BaseModel):
    message: str


@world_router.get("/world/prayer")
async def get_prayer():
    prayer_path = settings.workspace_root / "prayer.md"
    if prayer_path.exists():
        return {"content": prayer_path.read_text(encoding="utf-8")}
    return {"content": ""}


@world_router.get("/world/revelation")
async def get_revelation():
    revelation_path = settings.workspace_root / "revelation.md"
    if revelation_path.exists():
        return {"content": revelation_path.read_text(encoding="utf-8")}
    return {"content": ""}


@world_router.post("/world/revelation")
async def write_revelation(req: RevelationRequest):
    from datetime import datetime

    revelation_path = settings.workspace_root / "revelation.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"\n## [{timestamp}] 神之谕令\n{req.message}\n"

    if revelation_path.exists():
        revelation_path.write_text(
            revelation_path.read_text(encoding="utf-8") + content, encoding="utf-8"
        )
    else:
        revelation_path.write_text(f"# 💡 神谕 (Revelation)\n{content}", encoding="utf-8")

    return {"status": "ok", "message": "神谕已降临"}


@world_router.get("/agent/world-log")
async def world_log():
    world_log_path = settings.workspace_root / "world_log.md"
    events = []
    if world_log_path.exists():
        content = world_log_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        for line in lines:
            if line.strip() and not line.startswith("#"):
                events.append(
                    {"type": "info", "lineage_id": "system", "content": line, "timestamp": 0}
                )
    return {"events": events}
