from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
from datetime import datetime

from app.agents.lineage.manager import LineageManager
from app.routes.shared import manager

chat_router = APIRouter(prefix="/agent", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    lineage_id: str = "default"
    max_steps: int = 10
    run_type: str = "SYNC"
    dispatch_mode: str = "random"


@chat_router.post("/chat")
async def chat(req: ChatRequest):
    if req.run_type == "ASYNC":
        import threading

        lineage_id = req.lineage_id

        if lineage_id == "auto":
            all_ids = list(manager.all().keys())
            if not all_ids:
                raise HTTPException(status_code=503, detail="没有活跃的 Lineage")
            if req.dispatch_mode == "random":
                lineage_id = random.choice(all_ids)
            else:
                lineage_id = all_ids[-1]

        def run_task():
            agent = manager.create(lineage_id)
            result = agent.run(
                objective=req.message,
                max_steps=req.max_steps,
                on_born=lambda child_id: manager.register_newborn(child_id),
            )

        thread = threading.Thread(
            target=run_task, name=f"Task-{lineage_id}-{datetime.now().strftime('%H%M%S')}"
        )
        thread.start()
        return {
            "status": "async_started",
            "thread_name": thread.name,
            "lineage_id": lineage_id,
            "message": "任务已在后台异步执行",
        }

    if req.lineage_id == "auto":
        all_ids = list(manager.all().keys())
        if not all_ids:
            raise HTTPException(status_code=503, detail="没有活跃的 Lineage")
        if req.dispatch_mode == "random":
            lineage_id = random.choice(all_ids)
        else:
            lineage_id = all_ids[-1]
    else:
        lineage_id = req.lineage_id

    agent = manager.create(lineage_id)
    result = agent.run(
        objective=req.message,
        max_steps=req.max_steps,
        on_born=lambda child_id: manager.register_newborn(child_id),
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    result["lineage_id"] = lineage_id
    return result


@chat_router.post("/broadcast")
async def broadcast(req: ChatRequest):
    manager.scan_lineages()
    all_ids = list(manager.all().keys())

    if not all_ids:
        raise HTTPException(status_code=503, detail="没有活跃的 Lineage")

    results = []
    for lineage_id in all_ids:
        try:
            agent = manager.create(lineage_id)
            result = agent.run(
                objective=req.message,
                max_steps=req.max_steps,
                on_born=lambda child_id: manager.register_newborn(child_id),
            )
            results.append(
                {"lineage_id": lineage_id, "status": "ok", "output": result.get("final_output", "")}
            )
        except Exception as e:
            results.append({"lineage_id": lineage_id, "status": "error", "error": str(e)})

    return {
        "status": "broadcast_ok",
        "lineage_ids": all_ids,
        "mode": "broadcast",
        "results": results,
    }
