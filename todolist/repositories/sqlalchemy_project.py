from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from todolist.models import Project
from todolist.repositories.base import ProjectRepository


class SqlAlchemyProjectRepository(ProjectRepository):
    """Project repository backed by a SQLAlchemy Session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> Project:
        self._session.add(project)
        # Flush so project.id is populated from the DB
        self._session.flush()
        return project

    def get(self, project_id: int) -> Project | None:
        return self._session.get(Project, project_id)

    def get_by_name(self, name: str) -> Project | None:
        stmt = select(Project).where(Project.name == name)
        return self._session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> Sequence[Project]:
        stmt = select(Project).order_by(Project.created_at)
        return list(self._session.execute(stmt).scalars().all())

    def delete(self, project: Project) -> None:
        self._session.delete(project)
