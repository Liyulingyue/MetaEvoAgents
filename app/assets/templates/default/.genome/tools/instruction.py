import os


def update_instruction(new_content: str, lineage_root: str) -> str:
    try:
        path = os.path.join(lineage_root, "instruction.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return "Instruction updated successfully."
    except Exception as e:
        return f"Error updating instruction: {e}"
