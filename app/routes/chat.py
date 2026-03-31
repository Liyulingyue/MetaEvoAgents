from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.inner import InnerAgent

agents_router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    max_steps: int = 10


@agents_router.post("/chat")
async def chat(req: ChatRequest):
    agent = InnerAgent()
    result = agent.run(objective=req.message, max_steps=req.max_steps)
    return result.to_dict()


@agents_router.get("/health")
async def health():
    return {"status": "ok"}
