from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routes.agent import chat_router
from app.routes.lineage import lineage_router
from app.routes.vault import vault_router
from app.routes.files import files_router
from app.routes.world import world_router
from app.routes.events import events_router
from app.routes.system import system_router
from app.routes.shared import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager.startup_all()
    yield
    manager.shutdown_all()


app = FastAPI(title="MetaEvoAgents - 演化智能体引擎", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(lineage_router)
app.include_router(vault_router)
app.include_router(files_router)
app.include_router(world_router)
app.include_router(events_router)
app.include_router(system_router)


@app.get("/")
async def root():
    return {"message": "MetaEvoAgents 引擎运行中", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
