import json
import queue
import sys
import uuid
import subprocess
import threading
from pathlib import Path
from typing import Callable


class LineageAgent:
    _process: subprocess.Popen | None
    _reader_thread: threading.Thread | None
    _reader_ready: threading.Event | None
    _response_queue: queue.Queue[dict]
    _running_lock: threading.RLock
    _send_lock: threading.Lock

    def __init__(
        self, lineage_root: Path
    ):
        self.lineage_root = Path(lineage_root).resolve()
        self.lineage_id = self.lineage_root.name
        self.vault_path = self.lineage_root / "vault"

        self._process = None
        self._reader_thread = None
        self._reader_ready = None
        self._response_queue = queue.Queue()
        self._running_lock = threading.RLock()
        self._send_lock = threading.Lock()

    @property
    def metadata(self) -> dict:
        meta_path = self.lineage_root / ".metadata.json"
        if meta_path.exists():
            return json.loads(meta_path.read_text(encoding="utf-8"))
        return {}

    def _start_process(self):
        with self._running_lock:
            if self._process is not None and self._process.poll() is None:
                return
            self._response_queue = queue.Queue()
            self._reader_ready = threading.Event()
            
            engine_path = self.lineage_root / "engine.py"
            if not engine_path.exists():
                print(f"Error: Engine file not found at {engine_path}")
                return

            self._process = subprocess.Popen(
                [sys.executable, str(engine_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # 捕获 stderr 用于调试
                cwd=str(self.lineage_root),
            )
            
            # 开启 stderr 监听线程
            def listen_stderr():
                for line in self._process.stderr:
                    print(f"[{self.lineage_id} STDERR] {line.decode('utf-8').strip()}")
            
            threading.Thread(target=listen_stderr, daemon=True).start()

            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()
            self._reader_ready.wait(timeout=5)  # 增加点宽限时间

    def _read_loop(self):
        assert self._process is not None
        assert self._reader_ready is not None
        self._reader_ready.set()
        for line in self._process.stdout:  # type: ignore[union-attr]
            line = line.decode("utf-8").strip()
            if line:
                try:
                    msg = json.loads(line)
                    self._response_queue.put(msg)
                except json.JSONDecodeError:
                    pass

    def _get_response(self, timeout: float = 30) -> dict:
        try:
            return self._response_queue.get(timeout=timeout)
        except queue.Empty:
            return {"type": "error", "message": "Timeout waiting for kernel response"}

    def _send(self, msg: dict):
        self._start_process()
        with self._send_lock:
            assert self._process is not None and self._process.stdin is not None
            line = json.dumps(msg, ensure_ascii=False) + "\n"
            self._process.stdin.write(line.encode("utf-8"))  # type: ignore[union-attr]
            self._process.stdin.flush()  # type: ignore[union-attr]

    def run(self, objective: str, max_steps: int = 10, on_step: Callable | None = None, on_born: Callable | None = None):
        session_id = str(uuid.uuid4())[:8]
        self._send({"type": "run", "session_id": session_id, "objective": objective, "max_steps": max_steps})
        
        final_output = ""
        steps = []
        
        while True:
            msg = self._get_response(timeout=120)  # Long timeout for LLM
            if msg.get("type") == "error":
                return {"error": msg.get("message")}
            
            if msg.get("type") == "step":
                steps.append(msg)
                if on_step:
                    on_step(msg)
                continue
            
            if msg.get("type") == "born_notification":
                child_id = msg.get("child_id")
                if on_born:
                    on_born(child_id)
                continue
            
            if msg.get("type") == "result":
                final_output = msg.get("final_output", "")
                break
            
            if msg.get("type") == "shutdown_ok":
                break
        
        return {
            "session_id": session_id,
            "steps": steps,
            "final_output": final_output
        }

    def introspect(self) -> dict:
        self._send({"type": "introspect"})
        resp = self._get_response(timeout=5)
        return resp if resp.get("type") == "introspect_result" else {}

    def sync(self) -> bool:
        self._send({"type": "sync"})
        resp = self._get_response(timeout=5)
        return resp.get("type") == "sync_ok"

    def shutdown(self):
        with self._running_lock:
            if self._process is not None:
                try:
                    self._send({"type": "shutdown"})
                    self._get_response(timeout=2)
                except Exception:
                    pass
                self._process.terminate()
                self._process.wait(timeout=2)
                self._process = None
                self._reader_thread = None

    def __del__(self):
        self.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.shutdown()
