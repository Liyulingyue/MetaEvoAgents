from fastapi import APIRouter, HTTPException
from datetime import datetime
from pathlib import Path
import shutil
import json as _json

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


@lineage_router.get("/history/{lineage_id}")
async def get_history(lineage_id: str):
    if not manager.exists(lineage_id):
        raise HTTPException(status_code=404, detail="Lineage not found")

    lineage_path = settings.workspace_root / "lineages" / lineage_id
    history_path = lineage_path / "history.json"

    if history_path.exists():
        import json as _json

        try:
            history = _json.loads(history_path.read_text(encoding="utf-8"))
            return {"lineage_id": lineage_id, "history": history}
        except Exception:
            return {"lineage_id": lineage_id, "history": []}

    return {"lineage_id": lineage_id, "history": []}


@lineage_router.get("/templates")
async def get_templates():
    templates_dir = Path(__file__).parent.parent / "assets" / "templates"
    templates = []
    if templates_dir.exists():
        for item in templates_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                instruction_path = item / "instruction.md"
                desc = ""
                if instruction_path.exists():
                    content = instruction_path.read_text(encoding="utf-8")
                    lines = content.strip().split("\n")
                    for line in lines[1:]:
                        if line.strip() and not line.startswith("#"):
                            desc = line.strip()[:50]
                            break
                templates.append(
                    {
                        "id": item.name,
                        "name": item.name,
                        "desc": desc or "标准智能体",
                    }
                )
    if not templates:
        templates.append({"id": "default", "name": "default", "desc": "标准智能体"})
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
        _bootstrap_lineage(lineage_id, lineage_path, template)
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


@lineage_router.get("/lineages/{lineage_id}/files")
async def get_lineage_files(lineage_id: str):
    """获取 Lineage 的所有文件"""
    lineage_path = settings.workspace_root / "lineages" / lineage_id

    if not lineage_path.exists():
        raise HTTPException(status_code=404, detail=f"Lineage '{lineage_id}' 不存在")

    files = []
    for item in lineage_path.rglob("*"):
        if item.is_file() and not item.name.startswith("."):
            rel_path = str(item.relative_to(lineage_path))
            files.append(
                {
                    "name": rel_path,
                    "size": item.stat().st_size,
                    "modified": int(item.stat().st_mtime * 1000),
                }
            )

    return {"lineage_id": lineage_id, "path": str(lineage_path), "files": files}


@lineage_router.get("/lineages/{lineage_id}/files/{path:path}")
async def get_lineage_file(lineage_id: str, path: str):
    """读取 Lineage 的文件内容"""
    lineage_path = settings.workspace_root / "lineages" / lineage_id
    file_path = lineage_path / path

    if not lineage_path.exists():
        raise HTTPException(status_code=404, detail=f"Lineage '{lineage_id}' 不存在")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        content = file_path.read_text(encoding="utf-8")
        return {"lineage_id": lineage_id, "path": path, "content": content}
    except Exception:
        return {
            "lineage_id": lineage_id,
            "path": path,
            "content": "(二进制文件或无法读取)",
            "binary": True,
        }


@lineage_router.get("/chat-session")
async def get_chat_session():
    session_file = settings.workspace_root / "chat_session.json"
    if session_file.exists():
        return {"messages": _json.loads(session_file.read_text(encoding="utf-8"))}
    return {"messages": []}


@lineage_router.post("/chat-session")
async def save_chat_session(request: dict):
    session_file = settings.workspace_root / "chat_session.json"
    session_file.write_text(
        _json.dumps(request.get("messages", []), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"status": "ok"}
