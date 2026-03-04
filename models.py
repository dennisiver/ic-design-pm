"""資料模型定義"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Project:
    id: int = 0
    name: str = ""
    description: str = ""
    color: str = "#4A90D9"
    sort_order: int = 0
    is_archived: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Task:
    id: int = 0
    project_id: int = 0
    title: str = ""
    description: str = ""
    status: str = "待辦"
    priority: str = "中"
    category: str = ""
    assignee: str = ""
    due_date: Optional[str] = None
    sort_order: int = 0
    created_at: str = ""
    updated_at: str = ""
    tags: list = field(default_factory=list)
