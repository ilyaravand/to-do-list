from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

# Core/domain models
from todolist.core.models import Project as CoreProject
from todolist.core.repository import ProjectRepository

# ORM/DB models
from todolist.models import Project as ORMProject


class SqlAlchemyProjectRepository(ProjectRepository):
    """Project repository backed by a SQLAlchemy Session.

    Converts between core Project dataclasses and ORM Project rows.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ---------- helper mappers ----------

    @staticmethod
    def _to_core(orm: ORMProject) -> CoreProject:
        """Convert ORM Project -> core Project."""
        return CoreProject(
            name=orm.name,
            description=orm.description or "",
            id=orm.id,
            created_at=orm.created_at,
        )

    # ---------- ProjectRepository API ----------

    def add(self, p: CoreProject) -> CoreProject:
        """Persist a new project and sync its id/created_at back to the core object."""
        orm = ORMProject(
            name=p.name,
            description=p.description or "",
        )
        self._session.add(orm)
        self._session.flush()  # orm.id & orm.created_at are now set

        # sync back to the core object
        p.id = orm.id
        p.created_at = orm.created_at
        return p

    def get_by_name(self, name: str) -> Optional[CoreProject]:
        stmt = select(ORMProject).where(ORMProject.name == name)
        orm = self._session.execute(stmt).scalar_one_or_none()
        if orm is None:
            return None
        return self._to_core(orm)

    def get_by_id(self, pid: int) -> Optional[CoreProject]:
        orm = self._session.get(ORMProject, pid)
        if orm is None:
            return None
        return self._to_core(orm)

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(ORMProject)) or 0

    def all(self) -> Iterable[CoreProject]:
        """Return all projects ordered by creation time (as core models)."""
        stmt = select(ORMProject).order_by(ORMProject.created_at)
        return [self._to_core(orm) for orm in self._session.scalars(stmt).all()]

    def update(
        self,
        p: CoreProject,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CoreProject:
        """Update project in DB and in the core object."""
        orm = self._session.get(ORMProject, p.id)
        if orm is None:
            # Services normally ensure existence before calling update,
            # so we just return p unchanged here.
            return p

        if name is not None:
            orm.name = name
            p.name = name
        if description is not None:
            orm.description = description
            p.description = description

        self._session.flush()
        return p

    def delete(self, pid: int) -> bool:
        orm = self._session.get(ORMProject, pid)
        if orm is None:
            return False
        self._session.delete(orm)
        self._session.flush()
        return True
