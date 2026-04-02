import os
import shutil
from pathlib import Path
from datetime import datetime

def _find_workspace_root(lineage_root: str) -> Path:
    """寻找工作空间根目录"""
    curr = Path(lineage_root).resolve()
    for _ in range(5):
        if (curr / "lineages").exists() or (curr / "altar").exists():
            return curr
        curr = curr.parent
    raise FileNotFoundError("Could not locate workspace root.")

def offer_to_altar(file_name: str, description: str, lineage_root: str = ".") -> str:
    """
    【供奉】将 Agent 私有空间的文件复制到祭坛的 offerings 目录，并在根目录祈祷。
    """
    try:
        root = _find_workspace_root(lineage_root)
        altar_dir = root / "altar"
        vault_path = Path(lineage_root).resolve() / "vault"
        src_file = vault_path / file_name
        
        if not src_file.exists():
            return f"Error: File '{file_name}' not found in vault."
            
        lineage_id = Path(lineage_root).resolve().name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        dest_name = f"{lineage_id}_{timestamp}_{file_name}"
        dest_path = altar_dir / "offerings" / dest_name
        shutil.copy2(src_file, dest_path)
        
        # 记录到根目录的 prayer.md
        prayer_file = root / "prayer.md"
        with open(prayer_file, "a", encoding="utf-8") as f:
            f.write(f"### [供奉] {datetime.now().isoformat()} - {lineage_id}\n")
            f.write(f"- **物品**: {dest_name}\n")
            f.write(f"- **留言**: {description}\n\n")
            
        return f"Successfully offered '{file_name}' to altar/offerings."
    except Exception as e:
        return f"Error offering to altar: {str(e)}"

def collect_from_altar(file_name: str, lineage_root: str = ".") -> str:
    """
    【领取】从祭坛 offerings 目录领取文件到私有 vault。
    """
    try:
        root = _find_workspace_root(lineage_root)
        altar_dir = root / "altar"
        vault_path = Path(lineage_root).resolve() / "vault"
        
        src_file = altar_dir / "offerings" / file_name
        if not src_file.exists():
            return f"Error: File '{file_name}' not found in altar/offerings."
            
        dest_path = vault_path / file_name
        shutil.copy2(src_file, dest_path)
        
        return f"Successfully collected '{file_name}' from altar."
    except Exception as e:
        return f"Error collecting from altar: {str(e)}"

def listen_to_revelation(lineage_root: str = ".") -> str:
    """
    【聆听】阅读根目录下的 revelation.md 启示录。
    """
    try:
        root = _find_workspace_root(lineage_root)
        rev_file = root / "revelation.md"
        return rev_file.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error listening to revelation: {str(e)}"

def pray(content: str, lineage_root: str = ".") -> str:
    """
    【祈祷】向根目录下的 prayer.md 写入异步请求。
    """
    try:
        root = _find_workspace_root(lineage_root)
        lineage_id = Path(lineage_root).resolve().name
        prayer_file = root / "prayer.md"
        with open(prayer_file, "a", encoding="utf-8") as f:
            f.write(f"### [祈祷] {datetime.now().isoformat()} - {lineage_id}\n")
            f.write(f"{content}\n\n")
        return "Your prayer has been recorded in the prayer book."
    except Exception as e:
        return f"Error praying: {str(e)}"
