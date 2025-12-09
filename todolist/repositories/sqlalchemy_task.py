from __future__ import annotations

from datetime import datetime, date
from typing import Iterable, Optional

from sqlalchemy import and_, select, func
from sqlalchemy.orm import Session

# Core/domain models
from todolist.core.models import Task as CoreTask
from todolist.core.repository import TaskRepository

# ORM/DB models
from todolist.models import Task as ORMTask, TaskStatusEnum


class SqlAlchemyTaskRepository(TaskRepository):
    """Task repository backed by a SQLAlchemy Session.

    Converts between core Task dataclasses and ORM Task rows.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ---------- helper mappers ----------

    @staticmethod
    def _to_core(orm: ORMTask) -> CoreTask:
        """Convert ORM Task -> core Task."""
        # deadline in core is Optional[date]; ORM may use date or datetime
        deadline = orm.deadline
        if isinstance(deadline, datetime):
            deadline = deadline.date()
        return CoreTask(
            project_id=orm.project_id,
            title=orm.title,
            description=orm.description or "",
            status=orm.status,
            deadline=deadline,
            id=orm.id,
            created_at=orm.created_at,
        )

    # ---------- TaskRepository API ----------

    def add(self, t: CoreTask) -> CoreTask:
        """Persist a new task and sync id/created_at back to the core object."""
        orm = ORMTask(
            project_id=t.project_id,
            title=t.title,
            description=t.description or "",
            status=t.status,
            deadline=t.deadline,
        )
        self._session.add(orm)
        self._session.flush()

        t.id = orm.id
        t.created_at = orm.created_at
        return t

    def get_by_id(self, tid: int) -> Optional[CoreTask]:
        orm = self._session.get(ORMTask, tid)
        if orm is None:
            return None
        return self._to_core(orm)

    def all_for_project(self, project_id: int) -> Iterable[CoreTask]:
        stmt = (
            select(ORMTask)
            .where(ORMTask.project_id == project_id)
            .order_by(ORMTask.created_at)
        )
        return [self._to_core(orm) for orm in self._session.scalars(stmt).all()]

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(ORMTask)) or 0

    def delete_by_project(self, project_id: int) -> int:
        stmt = select(ORMTask).where(ORMTask.project_id == project_id)
        tasks = self._session.scalars(stmt).all()
        deleted = len(tasks)
        for orm in tasks:
            self._session.delete(orm)
        self._session.flush()
        return deleted

    def update(
        self,
        t: CoreTask,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        deadline: Optional[date] = None,
    ) -> CoreTask:
        """Update task in DB and in the core object."""
        orm = self._session.get(ORMTask, t.id)
        if orm is None:
            return t

        if title is not None:
            orm.title = title
            t.title = title
        if description is not None:
            orm.description = description
            t.description = description
        if status is not None:
            orm.status = status
            t.status = status
        if deadline is not None:
            orm.deadline = deadline
            t.deadline = deadline

        self._session.flush()
        return t

    def delete(self, task_id: int) -> bool:
        orm = self._session.get(ORMTask, task_id)
        if orm is None:
            return False
        self._session.delete(orm)
        self._session.flush()
        return True

    # ---------- Extra helper for auto-close overdue ----------

    def list_overdue(self, now: datetime) -> Iterable[CoreTask]:
        """
        Overdue = has a deadline, deadline < now (date-level), and not done.
        Returns core Task objects.
        """
        stmt = (
            select(ORMTask)
            .where(
                and_(
                    ORMTask.deadline.is_not(None),
                    ORMTask.deadline < now,
                    ORMTask.status != TaskStatusEnum.DONE.value,
                )
            )
            .order_by(ORMTask.deadline)
        )
        return [self._to_core(orm) for orm in self._session.scalars(stmt).all()]
