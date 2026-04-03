from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.routes.shared import manager, settings

vault_router = APIRouter(prefix="/agent", tags=["vault"])


@vault_router.get("/vault/{lineage_id}")
async def get_vault(lineage_id: str):
    if not manager.exists(lineage_id):
        raise HTTPException(status_code=404, detail="Lineage not found")
    agent = manager.load(lineage_id)
    vault_path = agent.vault_path

    files = []
    if vault_path.exists():
        for item in vault_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(vault_path)
                files.append(
                    {
                        "name": str(rel_path),
                        "size": item.stat().st_size,
                        "modified": int(item.stat().st_mtime * 1000),
                    }
                )

    return {"lineage_id": lineage_id, "path": str(vault_path), "files": files}


@vault_router.get("/vault/{lineage_id}/{path:path}")
async def get_vault_file(lineage_id: str, path: str):
    if not manager.exists(lineage_id):
        raise HTTPException(status_code=404, detail="Lineage not found")
    agent = manager.load(lineage_id)
    file_path = agent.vault_path / path

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    content = file_path.read_text(encoding="utf-8")
    return {"lineage_id": lineage_id, "path": path, "content": content}


@vault_router.get("/vault/{lineage_id}/download/{path:path}")
async def download_vault_file(lineage_id: str, path: str):
    if not manager.exists(lineage_id):
        raise HTTPException(status_code=404, detail="Lineage not found")
    agent = manager.load(lineage_id)
    file_path = agent.vault_path / path

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=file_path, filename=path, media_type="application/octet-stream")
