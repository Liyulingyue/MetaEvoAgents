from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routes.chat import agents_router, manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：唤醒所有守护进程
    manager.startup_all()
    yield
    # 关闭时：停止所有守护进程
    manager.shutdown_all()

app = FastAPI(
    title="MetaEvoAgents - 演化智能体引擎", 
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(agents_router)


@app.get("/")
async def root():
    return {"message": "MetaEvoAgents 引擎运行中", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
