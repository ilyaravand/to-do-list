# todolist/core/services.py
from .models import Project
from .repository import ProjectRepository
from .errors import ProjectLimitReached, DuplicateProjectName, ValidationError
from .utils import word_count
from ..config.settings import settings

NAME_MAX_WORDS = 30
DESC_MAX_WORDS = 150

class ProjectService:
    def __init__(self, repo: ProjectRepository) -> None:
        self.repo = repo

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
