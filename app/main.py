from fastapi import FastAPI
from app.routes.chat import agents_router

app = FastAPI(title="MetaEvoAgents - 演化智能体引擎", version="0.1.0")

app.include_router(agents_router)


@app.get("/")
async def root():
    return {"message": "MetaEvoAgents 引擎运行中", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
