import os
import subprocess


def execute_bash(command: str, cwd: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        output = result.stdout + result.stderr
        return output if output else "(empty output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {e}"


def get_vault_path(lineage_root: str) -> str:
    return os.path.join(lineage_root, "vault")
