TOOL_DEFINITIONS = {
    "execute_bash": {
        "name": "execute_bash",
        "description": "Execute a bash command in the vault directory.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "The command to run."}},
            "required": ["command"],
        },
        "module": "bash",
    },
    "read_file": {
        "name": "read_file",
        "description": "Read the content of a file from the vault.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the file."}},
            "required": ["path"],
        },
        "module": "file_ops",
    },
    "write_file": {
        "name": "write_file",
        "description": "Write or overwrite a file with the provided content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "content": {"type": "string", "description": "The content to write."},
            },
            "required": ["path", "content"],
        },
        "module": "file_ops",
    },
    "list_files": {
        "name": "list_files",
        "description": "List files and directories in a given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path (defaults to vault root).",
                }
            },
        },
        "module": "file_ops",
    },
    "search_files": {
        "name": "search_files",
        "description": "Search for a specific string in files within a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The text to search for."},
                "path": {
                    "type": "string",
                    "description": "The directory path to search in (defaults to current).",
                },
            },
            "required": ["query"],
        },
        "module": "search",
    },
    "update_instruction": {
        "name": "update_instruction",
        "description": "Update the agent's own instruction.md (its personality and goals). Use this when you want to evolve or refine your identity.",
        "parameters": {
            "type": "object",
            "properties": {
                "new_content": {
                    "type": "string",
                    "description": "The new instruction content to write.",
                }
            },
            "required": ["new_content"],
        },
        "module": "instruction",
    },
}


def get_tool_schemas():
    return [
        {
            "type": "function",
            "function": {
                "name": td["name"],
                "description": td["description"],
                "parameters": td["parameters"],
            },
        }
        for td in TOOL_DEFINITIONS.values()
    ]


def get_tool_definitions():
    return dict(TOOL_DEFINITIONS)
