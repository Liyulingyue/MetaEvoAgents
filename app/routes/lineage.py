from fastapi import APIRouter, HTTPException
from datetime import datetime
import shutil

from app.agents.lineage.manager import LineageManager
from app.routes.shared import manager, settings

lineage_router = APIRouter(prefix="/agent", tags=["lineage"])


@lineage_router.get("/lineages")
async def get_lineages():
    manager.scan_lineages()
    lineages_dir = settings.workspace_root / "lineages"
    result = []
    if lineages_dir.exists():
        for item in lineages_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                meta_path = item / ".metadata.json"
                meta = {}
                if meta_path.exists():
                    import json as _json

                    meta = _json.loads(meta_path.read_text(encoding="utf-8"))

                created_at = 0
                if "created_at" in meta:
                    created_at = int(datetime.fromisoformat(meta["created_at"]).timestamp() * 1000)

                vault_path = item / "vault"
                vault_contents = []
                if vault_path.exists():
                    vault_contents = [f.name for f in vault_path.iterdir()]

                result.append(
                    {
                        "id": item.name,
                        "name": item.name,
                        "status": "idle",
                        "created_at": created_at,
                        "metadata": {
                            "uid": meta.get("uid"),
                            "generation": meta.get("generation", 1),
                            "parent_lineage_id": meta.get("parent_lineage_id"),
                        },
                        "vault_contents": vault_contents,
                    }
                )
    return result


@lineage_router.get("/introspect/{lineage_id}")
async def introspect(lineage_id: str):
    if not manager.exists(lineage_id):
        raise HTTPException(status_code=404, detail="Lineage not found")
    agent = manager.load(lineage_id)
    return agent.introspect()


@lineage_router.get("/templates")
async def get_templates():
    templates = [
        {"id": "default", "name": "默认模板", "desc": "标准智能体"},
        {"id": "explorer", "name": "探索者", "desc": "擅长探索和发现"},
        {"id": "builder", "name": "建造者", "desc": "擅长构建和创造"},
        {"id": "researcher", "name": "研究者", "desc": "擅长研究和分析"},
    ]
    return {"templates": templates}


@lineage_router.post("/lineages")
async def create_lineage(request: dict):
    import uuid
    from app.agents.lineage.manager import _bootstrap_lineage

    name = request.get("name", "")
    template = request.get("template", "default")

    lineage_id = name if name else f"Lineage-{uuid.uuid4().hex[:8]}"
    lineage_path = settings.workspace_root / "lineages" / lineage_id

    if lineage_path.exists():
        raise HTTPException(status_code=400, detail=f"Lineage '{lineage_id}' 已存在")

    try:
        _bootstrap_lineage(lineage_id, lineage_path)
        return {"status": "ok", "id": lineage_id, "message": f"Lineage '{lineage_id}' 创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@lineage_router.delete("/lineages/{lineage_id}")
async def delete_lineage(lineage_id: str):
    lineage_path = settings.workspace_root / "lineages" / lineage_id

    if not lineage_path.exists():
        raise HTTPException(status_code=404, detail=f"Lineage '{lineage_id}' 不存在")

    try:
        shutil.rmtree(lineage_path)
        if lineage_id in manager.lineages:
            del manager.lineages[lineage_id]
        return {"status": "ok", "message": f"Lineage '{lineage_id}' 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
