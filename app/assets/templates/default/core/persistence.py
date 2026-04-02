import json
from pathlib import Path

class Persistence:
    def __init__(self, history_path: Path, instruction_path: Path):
        self.history_path = history_path
        self.instruction_path = instruction_path

    def load_history(self) -> list:
        if self.history_path.exists():
            try:
                content = self.history_path.read_text(encoding="utf-8")
                return json.loads(content) if content.strip() else []
            except Exception:
                return []
        return []

    def save_history(self, history: list):
        serializable = []
        for m in history:
            if hasattr(m, "model_dump"):
                serializable.append(m.model_dump())
            else:
                serializable.append(m)
        self.history_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_instruction(self) -> str:
        if self.instruction_path.exists():
            return self.instruction_path.read_text(encoding="utf-8")
        return "You are an autonomous coding agent."
