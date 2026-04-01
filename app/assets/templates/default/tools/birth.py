import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def birth(child_id: str, lineage_root: str) -> str:
    """
    Biological Inheritance (Physiological Birth).
    The agent replicates its '.genome' (germline) to a new lineage directory.
    
    :param child_id: The ID for the new-born child.
    :param lineage_root: The root path of the current (parent) lineage.
    """
    try:
        parent_path = Path(lineage_root).resolve()
        genome_path = parent_path / ".genome"
        workspace_root = parent_path.parent
        child_path = workspace_root / child_id
        
        if not genome_path.exists():
            return f"Error: No .genome directory found in parent {parent_path}. Birth failed."
            
        if child_path.exists():
            return f"Error: Child lineage directory {child_id} already exists."
            
        # 1. 物理分裂：从生殖细胞模板复制到新生命实体
        shutil.copytree(genome_path, child_path)
        
        # 2. 基因烙印：更新子代的元数据
        meta_path = child_path / ".metadata.json"
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except:
                pass
        
        meta.update({
            "uid": child_id, # 或者重新生成 UUID
            "parent_id": parent_path.name,
            "created_at": datetime.now().isoformat(),
            "generation": meta.get("generation", 0) + 1
        })
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # 3. 产生出生证明 (由 engine 处理发往网关)
        # 这里仅执行物理创建，返回成功信息
        return f"Birth Success: Child '{child_id}' born at {child_path}. Please notify registry."
        
    except Exception as e:
        return f"Birth Error: {str(e)}"
