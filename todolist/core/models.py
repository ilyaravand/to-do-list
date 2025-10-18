# todolist/core/models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import itertools

_id_counter = itertools.count(1)

@dataclass
class Project:
    name: str
    description: Optional[str] = ""
    id: int = field(default_factory=lambda: next(_id_counter))
    created_at: datetime = field(default_factory=datetime.utcnow)
