from typing import Dict, Iterable, Optional, Set
from .models import Project, Task

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

class TaskRepository:
    def __init__(self) -> None:
        self._by_id: Dict[int, Task] = {}
        self._by_project: Dict[int, Set[int]] = {}

    def add(self, t: Task) -> Task:
        self._by_id[t.id] = t
        self._by_project.setdefault(t.project_id, set()).add(t.id)
        return t

    def get_by_id(self, tid: int) -> Optional[Task]:
        return self._by_id.get(tid)

    def all_for_project(self, project_id: int) -> Iterable[Task]:
        ids = self._by_project.get(project_id, set())
        for tid in sorted(ids):
            yield self._by_id[tid]

    def count(self) -> int:
        return len(self._by_id)

    # used by Project cascade-delete
    def delete_by_project(self, project_id: int) -> int:
        ids = list(self._by_project.pop(project_id, []))
        for tid in ids:
            self._by_id.pop(tid, None)
        return len(ids)

    def update(self, t: Task, *, title=None, description=None, status=None, deadline=None) -> Task:
        if title is not None:
            t.title = title
        if description is not None:
            t.description = description
        if status is not None:
            t.status = status
        if deadline is not None:
            t.deadline = deadline
        return t

    def delete(self, task_id: int) -> bool:
        t = self._by_id.pop(task_id, None)
        if not t:
            return False
        # remove from project index set
        ids = self._by_project.get(t.project_id)
        if ids:
            ids.discard(task_id)
            if not ids:
                self._by_project.pop(t.project_id, None)
        return True

