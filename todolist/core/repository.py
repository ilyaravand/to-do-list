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

    def get_by_id(self, pid: int) -> Optional[Project]:
        return self._by_id.get(pid)

    def count(self) -> int:
        return len(self._by_id)

    def all(self) -> Iterable[Project]:
        return self._by_id.values()

    def update(self, p: Project, *, name: Optional[str] = None,
               description: Optional[str] = None) -> Project:
        if name is not None and name.lower() != p.name.lower():
            # update name index
            self._by_name.pop(p.name.lower(), None)
            p.name = name
            self._by_name[p.name.lower()] = p.id
        if description is not None:
            p.description = description
        return p

    def delete(self, pid: int) -> bool:
        """
        Delete a project by id. Returns True if deleted, False if not found.
        Also updates the name index.
        """
        p = self._by_id.pop(pid, None)
        if not p:
            return False
        self._by_name.pop(p.name.lower(), None)
        return True