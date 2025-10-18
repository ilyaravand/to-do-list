# todolist/core/services.py
from typing import Optional
from .models import Project
from .repository import ProjectRepository
from .errors import (
    ProjectLimitReached, DuplicateProjectName, ValidationError, ProjectNotFound
)
from .utils import word_count
from ..config.settings import settings

NAME_MAX_WORDS = 30
DESC_MAX_WORDS = 150

class ProjectService:
    def __init__(self, repo: ProjectRepository, cascade_delete_tasks=None) -> None:
        """
        :param repo: ProjectRepository instance
        :param cascade_delete_tasks: optional callable(project_id:int) to cascade-delete tasks
        """
        self.repo = repo
        self._cascade_delete_tasks = cascade_delete_tasks

    def create_project(self, name: str, description: str = "") -> Project:
        # Validate counts
        if word_count(name) > NAME_MAX_WORDS:
            raise ValidationError(f"name must be ≤ {NAME_MAX_WORDS} words")
        if word_count(description) > DESC_MAX_WORDS:
            raise ValidationError(f"description must be ≤ {DESC_MAX_WORDS} words")

        # Limit
        if self.repo.count() >= settings.MAX_NUMBER_OF_PROJECT:
            raise ProjectLimitReached(
                f"MAX_NUMBER_OF_PROJECT={settings.MAX_NUMBER_OF_PROJECT} reached"
            )

        # Uniqueness
        if self.repo.get_by_name(name) is not None:
            raise DuplicateProjectName("project name must be unique")

        return self.repo.add(Project(name=name, description=description))

    def update_project(
        self,
        pid: int,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        if name is None and description is None:
            raise ValidationError("nothing to update; provide name and/or description")

        p = self.repo.get_by_id(pid)
        if not p:
            raise ProjectNotFound(f"project id {pid} not found")

        # validate name if provided
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("name cannot be empty")
            if word_count(name) > NAME_MAX_WORDS:
                raise ValidationError(f"name must be ≤ {NAME_MAX_WORDS} words")

            existing = self.repo.get_by_name(name)
            if existing and existing.id != pid:
                raise DuplicateProjectName("project name must be unique")

        # validate description if provided
        if description is not None and word_count(description) > DESC_MAX_WORDS:
            raise ValidationError(f"description must be ≤ {DESC_MAX_WORDS} words")

        return self.repo.update(
            p,
            name=name if name is not None else None,
            description=description if description is not None else None,
        )

    def delete_project(self, pid: int) -> None:
        """
        Delete a project by id.
        Also cascade-delete its tasks if a cascade hook is provided.
        """
        p = self.repo.get_by_id(pid)
        if not p:
            raise ProjectNotFound(f"project id {pid} not found")

        # Cascade delete tasks (if a hook is provided)
        if callable(self._cascade_delete_tasks):
            self._cascade_delete_tasks(pid)

        # Finally delete the project itself
        self.repo.delete(pid)