from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.lineage.manager import LineageManager

agents_router = APIRouter(prefix="/agent", tags=["agent"])
manager = LineageManager()

class ChatRequest(BaseModel):
    message: str
    lineage_id: str = "default"
    max_steps: int = 10


@agents_router.post("/chat")
async def chat(req: ChatRequest):
    # Ensure lineage exists or create it
    agent = manager.create(req.lineage_id)
    
    # Run the agent in its own process
    result = agent.run(objective=req.message, max_steps=req.max_steps)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result


@agents_router.get("/introspect/{lineage_id}")
async def introspect(lineage_id: str):
    if not manager.exists(lineage_id):
        raise HTTPException(status_code=404, detail="Lineage not found")
    agent = manager.load(lineage_id)
    return agent.introspect()
