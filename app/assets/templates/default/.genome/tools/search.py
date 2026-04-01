import subprocess


def search_files(query: str, path: str = ".") -> str:
    try:
        result = subprocess.run(
            f"grep -ril {repr(query)} {path}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        return output if output else "No matches found."
    except Exception as e:
        return f"Error searching files: {e}"
