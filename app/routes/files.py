from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from app.routes.shared import manager, settings

files_router = APIRouter(prefix="/agent", tags=["files"])


@files_router.get("/files/zones")
async def get_file_zones():
    zones = [
        {"id": "vault", "name": "Vault", "desc": "Agent 私有存储", "icon": "📦"},
        {"id": "academy", "name": "Academy", "desc": "族学区 - 公共知识", "icon": "📚"},
        {"id": "altar", "name": "Altar", "desc": "祭坛 - 实物交换", "icon": "🏛️"},
        {"id": "shrine", "name": "Shrine", "desc": "宗祠 - 归档区", "icon": "🪦"},
    ]

    result = []
    for zone in zones:
        zone_path = settings.workspace_root / zone["id"]
        files = []
        if zone_path.exists():
            for item in zone_path.rglob("*"):
                if item.is_file() and not item.name.startswith("."):
                    files.append(
                        {
                            "name": str(item.relative_to(zone_path)),
                            "size": item.stat().st_size,
                            "modified": int(item.stat().st_mtime * 1000),
                        }
                    )
        result.append({**zone, "files": files, "path": str(zone_path)})

    return {"zones": result}


@files_router.get("/files/{zone}")
async def get_zone_files(zone: str):
    zone_path = settings.workspace_root / zone

    if not zone_path.exists():
        raise HTTPException(status_code=404, detail="文件区不存在")

    files = []
    for item in zone_path.rglob("*"):
        if item.is_file() and not item.name.startswith("."):
            files.append(
                {
                    "name": str(item.relative_to(zone_path)),
                    "size": item.stat().st_size,
                    "modified": int(item.stat().st_mtime * 1000),
                }
            )

    return {"zone": zone, "path": str(zone_path), "files": files}


@files_router.get("/files/{zone}/{path:path}")
async def get_zone_file(zone: str, path: str):
    file_path = settings.workspace_root / zone / path

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    content = file_path.read_text(encoding="utf-8")
    return {"zone": zone, "path": path, "content": content}


@files_router.get("/files/{zone}/download/{path:path}")
async def download_zone_file(zone: str, path: str):
    file_path = settings.workspace_root / zone / path

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(path=file_path, filename=path, media_type="application/octet-stream")


@files_router.post("/files/altar/upload")
async def upload_to_altar(file: UploadFile = File(...)):
    altar_dir = settings.workspace_root / "altar"
    altar_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "unnamed_file"
    file_path = altar_dir / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "status": "ok",
        "message": f"文件 {filename} 已上传到祭坛",
        "path": str(file_path),
        "size": len(content),
    }


@files_router.post("/files/vault/{lineage_id}/upload")
async def upload_to_vault(lineage_id: str, file: UploadFile = File(...)):
    if not manager.exists(lineage_id):
        raise HTTPException(status_code=404, detail="Lineage 不存在")

    agent = manager.load(lineage_id)
    vault_dir = agent.vault_path
    vault_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "unnamed_file"
    file_path = vault_dir / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "status": "ok",
        "message": f"文件 {filename} 已上传到 {lineage_id} 的 Vault",
        "path": str(file_path),
        "size": len(content),
    }
