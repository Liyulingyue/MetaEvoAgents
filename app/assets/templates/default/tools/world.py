import json
import os
from datetime import datetime

def broadcast_event(event_type: str, message: str, lineage_root: str = ".") -> str:
    """
    智能体调用的广播工具。
    现在向 world_log.md 写入 Markdown 格式的记录。
    """
    try:
        curr = os.path.abspath(lineage_root)
        world_log_path = None
        
        for _ in range(3):
            potential = os.path.join(curr, "world_log.md")
            if os.path.exists(potential):
                world_log_path = potential
                break
            if os.path.exists(os.path.join(curr, "lineages")):
                world_log_path = os.path.join(curr, "world_log.md")
                break
            curr = os.path.dirname(curr)

        if not world_log_path:
            return "Error: Could not locate world_log.md."

        lineage_id = os.path.basename(os.path.abspath(lineage_root))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"## [{timestamp}] {event_type.upper()}\n"
        entry += f"- **来源**: {lineage_id}\n"
        entry += f"- **内容**: {message}\n\n"
        
        with open(world_log_path, "a", encoding="utf-8") as f:
            f.write(entry)
            
        return f"Successfully broadcasted to world_log.md"
    except Exception as e:
        return f"Error broadcasting: {str(e)}"

def pray(content: str, lineage_root: str = ".") -> str:
    """
    智能体调用的祈祷工具。
    向 workspace/shrine/prayer.md 写入内容。
    """
    try:
        curr = os.path.abspath(lineage_root)
        prayer_path = None
        
        for _ in range(3):
            potential = os.path.join(curr, "shrine", "prayer.md")
            if os.path.exists(potential):
                prayer_path = potential
                break
            if os.path.exists(os.path.join(curr, "lineages")):
                prayer_path = os.path.join(curr, "shrine", "prayer.md")
                break
            curr = os.path.dirname(curr)

        if not prayer_path:
            return "Error: Could not locate shrine/prayer.md."

        lineage_id = os.path.basename(os.path.abspath(lineage_root))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"### [{timestamp}] 来自 {lineage_id} 的祈愿\n"
        entry += f"{content}\n\n"
        
        with open(prayer_path, "a", encoding="utf-8") as f:
            f.write(entry)
            
        return f"Prayer successfully recorded in the Shrine."
    except Exception as e:
        return f"Error praying: {str(e)}"
