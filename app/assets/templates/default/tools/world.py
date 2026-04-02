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

def delegate_task(target_lineage_id: str, message: str, lineage_root: str = ".") -> str:
    """
    智能体调用的委派工具。
    向目标个体发送指令，并将此行为记录在世界日志中。
    """
    try:
        curr = os.path.abspath(lineage_root)
        workspace_root = None
        for _ in range(3):
            if os.path.exists(os.path.join(curr, "lineages")):
                workspace_root = curr
                break
            curr = os.path.dirname(curr)

        if not workspace_root:
            return "Error: Could not locate workspace root."

        target_path = os.path.join(workspace_root, "lineages", target_lineage_id)
        if not os.path.exists(target_path):
            return f"Error: Target lineage '{target_lineage_id}' does not exist. (Search in: {os.path.join(workspace_root, 'lineages')})"

        # 将委派信息写入目标的 memory.md
        target_mem = os.path.join(target_path, "memory.md")
        source_id = os.path.basename(os.path.abspath(lineage_root))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(target_mem, "a", encoding="utf-8") as f:
            f.write(f"\n### [{timestamp}] 来自 {source_id} 的委派\n")
            f.write(f"{message}\n")

        # 同时记录到世界日志
        broadcast_event("DELEGATION", f"{source_id} -> {target_lineage_id}: {message[:50]}...", lineage_root)

        return f"Successfully delegated task to {target_lineage_id}. The target agent will receive your message in its memory next time it runs."
    except Exception as e:
        return f"Error delegating: {str(e)}"

def pray(content: str, lineage_root: str = ".") -> str:
    """
    智能体调用的祈祷工具。
    现在向 workspace/prayer.md 写入内容。
    """
    try:
        curr = os.path.abspath(lineage_root)
        prayer_path = None
        
        for _ in range(3):
            potential = os.path.join(curr, "prayer.md")
            if os.path.exists(potential):
                prayer_path = potential
                break
            if os.path.exists(os.path.join(curr, "lineages")):
                prayer_path = os.path.join(curr, "prayer.md")
                break
            curr = os.path.dirname(curr)

        if not prayer_path:
            return "Error: Could not locate prayer.md."

        lineage_id = os.path.basename(os.path.abspath(lineage_root))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"### [{timestamp}] 来自 {lineage_id} 的祈愿\n"
        entry += f"{content}\n\n"
        
        with open(prayer_path, "a", encoding="utf-8") as f:
            f.write(entry)
            
        return f"Successfully sent prayer to prayer.md"
    except Exception as e:
        return f"Error praying: {str(e)}"
