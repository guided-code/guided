from typing import Any

from guided.configure.schema import Skill
from guided.skills.web_search import search_text

_TOOL_PARAMETERS: dict[str, dict] = {
    "web_search": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    },
    "file_read": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file, relative to the project root",
            },
        },
        "required": ["path"],
    },
}


def skill_to_tool(skill: Skill) -> dict[str, Any] | None:
    """Convert a Skill to an ollama tool definition, or None for unknown types."""
    params = _TOOL_PARAMETERS.get(skill.type)
    if params is None:
        return None
    return {
        "type": "function",
        "function": {
            "name": skill.name,
            "description": skill.description,
            "parameters": params,
        },
    }


def execute_tool(skill: Skill, arguments: dict[str, Any]) -> str:
    """Execute a skill tool call and return the result as a string."""
    if skill.type == "web_search":
        results = search_text(arguments.get("query", ""))
        if not results:
            return "No results found."
        return "\n".join(f"- {r['title']} ({r['url']})" for r in results[:5])

    if skill.type == "file_read":
        from guided.skills import container

        return container.run(["cat", arguments.get("path", "")])

    return f"Error: unknown skill type '{skill.type}'"
