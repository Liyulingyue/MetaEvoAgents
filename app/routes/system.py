from fastapi import APIRouter

from app.routes.shared import manager

system_router = APIRouter(prefix="/agent", tags=["system"])


@system_router.get("/tasks")
async def get_tasks():
    return {"status": "ok", "tasks": [], "message": "任务追踪功能开发中"}


@system_router.post("/reset")
async def reset_workspace():
    manager.reset()
    return {"status": "ok", "message": "Workspace 已重置"}


@system_router.post("/clear")
async def clear_workspace():
    manager.clear()
    return {"status": "ok", "message": "Workspace 已清空"}
