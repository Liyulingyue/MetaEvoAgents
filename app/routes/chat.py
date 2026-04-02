from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.lineage.manager import LineageManager

agents_router = APIRouter(prefix="/agent", tags=["agent"])
manager = LineageManager()

class ChatRequest(BaseModel):
    message: str
    lineage_id: str = "default"
    max_steps: int = 10
    mode: str = "direct"  # direct: 指定 ID, dispatch: 自动分发


@agents_router.post("/chat")
async def chat(req: ChatRequest):
    # 指令模式：自动寻找空闲 Agent
    if req.mode == "dispatch":
        result = manager.dispatch_task(req.message, req.max_steps)
        if "error" in result:
             raise HTTPException(status_code=503, detail=result["error"])
        return result

    # 默认模式：直接指定 ID
    # Ensure lineage exists or create it
    agent = manager.create(req.lineage_id)
    
    # Run the agent in its own process
    # Register the newborn when born_notification is received
    result = agent.run(
        objective=req.message, 
        max_steps=req.max_steps,
        on_born=lambda child_id: manager.register_newborn(child_id)
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result


@agents_router.get("/introspect/{lineage_id}")
async def introspect(lineage_id: str):
    if not manager.exists(lineage_id):
        raise HTTPException(status_code=404, detail="Lineage not found")
    agent = manager.load(lineage_id)
    return agent.introspect()
