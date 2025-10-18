# todolist/core/models.py
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import itertools

_id_counter = itertools.count(1)
_task_id_counter = itertools.count(1)

@dataclass
class Project:
    name: str
    description: Optional[str] = ""
    id: int = field(default_factory=lambda: next(_id_counter))
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Task:
    project_id: int
    title: str
    description: str = ""
    status: str = "todo"          # todo | doing | done
    deadline: Optional[date] = None
    id: int = field(default_factory=lambda: next(_task_id_counter))
    created_at: datetime = field(default_factory=datetime.utcnow)