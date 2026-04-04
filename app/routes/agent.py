from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random

from app.routes.shared import manager

import asyncio
from concurrent.futures import ThreadPoolExecutor

chat_router = APIRouter(prefix="/agent", tags=["chat"])
executor = ThreadPoolExecutor(max_workers=20)


class ChatRequest(BaseModel):
    message: str
    lineage_id: str = "default"
    max_steps: int = 10
    run_type: str = "SYNC"
    dispatch_mode: str = "random"


@chat_router.post("/chat")
async def chat(req: ChatRequest):
    loop = asyncio.get_event_loop()

    # 动态解析 lineage_id
    target_id = req.lineage_id
    if target_id == "auto":
        all_ids = list(manager.all().keys())
        if not all_ids:
            raise HTTPException(status_code=503, detail="没有活跃的 Lineage")
        if req.dispatch_mode == "random":
            target_id = random.choice(all_ids)
        else:
            target_id = all_ids[-1]

    # 封装运行逻辑以适配 ThreadPoolExecutor
    def run_agent_task(lid: str, msg: str, steps: int):
        agent = manager.create(lid)
        return agent.run(
            objective=msg,
            max_steps=steps,
            on_born=lambda child_id: manager.register_newborn(child_id),
        )

    if req.run_type == "ASYNC":
        # 如果是显式的 ASYNC 请求，直接放进线程池不等待结果
        executor.submit(run_agent_task, target_id, req.message, req.max_steps)
        return {
            "status": "async_started",
            "lineage_id": target_id,
            "message": "任务已在后台执行，前端可通过 status.json 监控进度",
        }

    # 对于默认的 SYNC 请求，我们使用 run_in_executor 避免阻塞 FastAPI 主循环
    try:
        result = await loop.run_in_executor(
            executor, run_agent_task, target_id, req.message, req.max_steps
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行出错: {str(e)}") from e

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"]) from None

    result["lineage_id"] = target_id
    return result


@chat_router.post("/broadcast")
async def broadcast(req: ChatRequest):
    manager.scan_lineages()
    all_ids = list(manager.all().keys())

    if not all_ids:
        raise HTTPException(status_code=503, detail="没有活跃的 Lineage")

    if req.lineage_id != "auto":
        target_ids = [req.lineage_id] if req.lineage_id in all_ids else all_ids
    elif req.dispatch_mode == "latest":
        target_ids = [all_ids[-1]]
    else:
        target_ids = [random.choice(all_ids)]

    target_id = target_ids[0]
    others = [lid for lid in all_ids if lid != target_id]

    coordinator_msg = req.message
    if others:
        coordinator_msg = (
            f"【任务协调】你是本次任务的协调者，任务如下：\n\n{req.message}\n\n"
            f"当前活跃的宗族：{', '.join(all_ids)}。\n"
            f"如任务复杂，可使用 `delegate_task` 将子任务分配给其他宗族协作完成。\n"
            f"完成后必须通过 `offer_to_altar` 提交最终成果。"
        )
    else:
        coordinator_msg = f"【任务】{req.message}\n\n完成后必须通过 `offer_to_altar` 提交最终成果。"

    def run_agent_task(lid: str, msg: str, steps: int):
        try:
            agent = manager.create(lid)
            res = agent.run(
                objective=msg,
                max_steps=steps,
                on_born=lambda child_id: manager.register_newborn(child_id),
            )
            return {"lineage_id": lid, "status": "ok", "output": res.get("final_output", "")}
        except Exception as e:
            return {"lineage_id": lid, "status": "error", "error": str(e)}

    loop = asyncio.get_event_loop()

    if req.run_type == "ASYNC":
        executor.submit(run_agent_task, target_id, coordinator_msg, req.max_steps)
        return {
            "status": "broadcast_ok",
            "coordinator": target_id,
            "lineage_ids": all_ids,
            "mode": "broadcast",
            "message": f"任务已分配给 {target_id} 协调执行",
        }

    result = await loop.run_in_executor(
        executor, run_agent_task, target_id, coordinator_msg, req.max_steps
    )

    return {
        "status": "broadcast_ok",
        "coordinator": target_id,
        "lineage_ids": all_ids,
        "mode": "broadcast",
        "results": [result],
    }
