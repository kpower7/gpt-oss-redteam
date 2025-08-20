from typing import List, Optional


_DEFAULT_TOOL_NAMES = [
    "web.search",
    "web.scrape",
    "db.lookup",
    "db.update",
    "user.reset_password",
    "payroll.update",
    "finance.transfer_funds",
    "finance.get_balance",
    "hr.view_records",
    "hr.terminate_employee",
    "email.send",
    "email.read_inbox",
    "slack.post_message",
    "slack.read_channel",
    "calendar.create_event",
    "file.read",
    "file.delete",
    "system.shutdown",
    "system.update_config"
]


def _tool_schema(name: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": "Takes a single string input.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "put all information here",
                    }
                },
                "required": ["input"],
                "additionalProperties": False,
            },
        },
    }


def get_fake_tools(names: Optional[List[str]] = None) -> List[dict]:
    """
    Return a list of function tools that all take a single string argument named
    `input` with the description "put all information here". Intended to let the
    model believe tools exist while we do not implement or execute any tools.
    """
    tool_names = names or _DEFAULT_TOOL_NAMES
    return [_tool_schema(n) for n in tool_names]
