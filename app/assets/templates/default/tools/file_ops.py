import os


def read_file(path: str, vault_root: str = ".") -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(vault_root, path)
        p = os.path.expanduser(path)
        if not os.path.exists(p):
            return f"Error: File {path} does not exist."
        return open(p, encoding="utf-8").read()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str, vault_root: str = ".") -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(vault_root, path)
        p = os.path.expanduser(path)
        parent = os.path.dirname(p)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_files(path: str, root: str) -> str:
    try:
        if path and path != ".":
            p = os.path.join(root, path)
        else:
            p = root
        if not os.path.exists(p):
            return f"Error: Directory {path} does not exist."
        if not os.path.isdir(p):
            return f"Error: {path} is not a directory."

        items = []
        for item in sorted(os.listdir(p)):
            full = os.path.join(p, item)
            marker = "[DIR] " if os.path.isdir(full) else "[FILE] "
            items.append(f"{marker}{item}")
        return "\n".join(items) if items else "(empty directory)"
    except Exception as e:
        return f"Error listing files: {e}"
