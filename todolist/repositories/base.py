from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence

from todolist.models import Project, Task


class ProjectRepository(ABC):
    """Abstract interface for project persistence."""

    @abstractmethod
    def add(self, project: Project) -> Project:
        """Persist a new project."""
        raise NotImplementedError

    @abstractmethod
    def get(self, project_id: int) -> Project | None:
        """Return project by id, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str) -> Project | None:
        """Return project by name, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Sequence[Project]:
        """Return all projects."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, project: Project) -> None:
        """Delete the given project."""
        raise NotImplementedError


class TaskRepository(ABC):
    """Abstract interface for task persistence."""

    @abstractmethod
    def add(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    def get(self, task_id: int) -> Task | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_project(self, project_id: int) -> Sequence[Task]:
        """All tasks for a project, ordered by creation or deadline."""
        raise NotImplementedError

    @abstractmethod
    def list_overdue(self, now: datetime) -> Sequence[Task]:
        """Tasks whose deadline < now and status != done."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, task: Task) -> None:
        raise NotImplementedError
