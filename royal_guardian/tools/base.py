from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class Risk(str, Enum):
    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    description: str
    risk: Risk
    approval_required: bool
    executor: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.id in self._tools:
            raise ValueError(f"Duplicate tool id: {tool.id}")
        self._tools[tool.id] = tool

    def describe(self) -> list[dict[str, Any]]:
        return [
            {"id": t.id, "description": t.description, "risk": t.risk.value, "approval_required": t.approval_required}
            for t in self._tools.values()
        ]

    def get(self, tool_id: str) -> ToolDefinition:
        if tool_id not in self._tools:
            raise KeyError(f"Unknown or unauthorized tool: {tool_id}")
        return self._tools[tool_id]

    def execute(self, tool_id: str, parameters: dict[str, Any], *, approved: bool = False) -> dict[str, Any]:
        tool = self.get(tool_id)
        if tool.risk is Risk.PROHIBITED:
            return {"ok": False, "error": "Action is prohibited"}
        if tool.approval_required and not approved:
            return {"ok": False, "error": "Approval required", "approval_required": True}
        return tool.executor(parameters)
