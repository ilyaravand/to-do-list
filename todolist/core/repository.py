# todolist/core/repository.py
from typing import Dict, Iterable, Optional
from .models import Project

class ProjectRepository:
    def __init__(self) -> None:
        self._by_id: Dict[int, Project] = {}
        self._by_name: Dict[str, int] = {}

    def add(self, p: Project) -> Project:
        self._by_id[p.id] = p
        self._by_name[p.name.lower()] = p.id
        return p

    def get_by_name(self, name: str) -> Optional[Project]:
        pid = self._by_name.get(name.lower())
        return self._by_id.get(pid) if pid else None

    def count(self) -> int:
        return len(self._by_id)

    def all(self) -> Iterable[Project]:
        return self._by_id.values()
