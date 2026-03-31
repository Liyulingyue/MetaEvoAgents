import importlib.util
import json
import shutil
import sys
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from app.agents.result import AgentResult
from app.core.config import settings


class LineageAgent:
    lineage_root: Path
    lineage_id: str
    vault_path: Path
    logs_path: Path
    kernel_path: Path
    metadata: dict
    instruction: str
    system_prompt: str
    assets: str

    def __init__(self, lineage_root: Path):
        self.lineage_root = Path(lineage_root).resolve()
        self.lineage_id = self.lineage_root.name
        self.vault_path = self.lineage_root / "vault"
        self.logs_path = self.lineage_root / "logs"
        self.kernel_path = self.lineage_root / "kernel.py"

        if not self.lineage_root.exists():
            self._bootstrap_from_template()

        self._load_identity()
        self._introspect()

    def _bootstrap_from_template(self):
        templates_root = settings.templates_root
        shutil.copytree(templates_root, self.lineage_root, dirs_exist_ok=True)
        self._record_birth()

    def _record_birth(self):
        metadata = self._read_metadata()
        metadata["uid"] = str(uuid.uuid4())[:8]
        metadata["created_at"] = datetime.now().isoformat()
        self._write_metadata(metadata)

        with self.lineage_root.joinpath("memory.log").open("a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().isoformat()}] LINEAGE BORN\n"
                f"  UID: {metadata['uid']}\n"
                f"  Template: {metadata.get('template', 'default')}\n"
                f"  Lineage ID: {self.lineage_id}\n"
            )

    def _load_identity(self):
        self.metadata = self._read_metadata()
        self.instruction = self.lineage_root.joinpath("instruction.md").read_text(encoding="utf-8")
        self.system_prompt = self.instruction

    def _introspect(self):
        vault_contents = list(self.vault_path.iterdir()) if self.vault_path.exists() else []
        self.assets = [x.name for x in vault_contents]
        self._append_memory(
            f"[{datetime.now().isoformat()}] INTROSPECTION\n  Vault contents: {self.assets}\n"
        )

    def _read_metadata(self) -> dict:
        return json.loads(self.lineage_root.joinpath(".metadata.json").read_text(encoding="utf-8"))

    def _write_metadata(self, data: dict):
        self.lineage_root.joinpath(".metadata.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _append_memory(self, entry: str):
        with self.lineage_root.joinpath("memory.log").open("a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def _load_kernel(self):
        spec = importlib.util.spec_from_file_location("_kernel", str(self.kernel_path))
        if not spec or not spec.loader:
            raise RuntimeError(f"Cannot load kernel from {self.kernel_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["_kernel"] = module
        spec.loader.exec_module(module)
        return module.Kernel(str(self.lineage_root))

    def sync_to_disk(self):
        self._write_metadata(self.metadata)

    def run(
        self,
        objective: str,
        max_steps: int = 10,
        streaming: bool = False,
        on_step: Callable | None = None,
    ):
        self._append_memory(
            f"[{datetime.now().isoformat()}] SESSION START\n"
            f"  Session ID: (delegated to kernel)\n"
            f"  Objective: {objective}\n"
        )

        kernel = self._load_kernel()

        session_id = str(uuid.uuid4())[:8]
        steps = []

        if streaming:
            self._log_session(session_id, {"status": "delegated_to_kernel", "objective": objective})
            print(f"\n{'=' * 50}")
            print(
                f"[Kernel] Delegated to workspace kernel, tools: {list(kernel.vault.definitions.keys())}"
            )
            print(f"[Kernel] Running objective: {objective}")

        final_output = kernel.run(objective, max_steps=max_steps)

        steps.append(
            {
                "step": 0,
                "message": final_output,
                "done": True,
            }
        )

        self._log_session(
            session_id,
            {
                "session_id": session_id,
                "steps": len(steps),
                "timestamp": datetime.now().isoformat(),
                "vault": str(self.vault_path),
                "lineage_id": self.lineage_id,
            },
        )

        if streaming:
            print(f"\n{'=' * 50}")
            print(f"Result: {final_output}")

        return AgentResult(session_id=session_id, steps=steps, final_output=final_output)

    def _log_session(self, session_id: str, data: dict):
        self.logs_path.mkdir(exist_ok=True)
        self.logs_path.joinpath(f"{session_id}.log").write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
