from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from todolist.models import Task, TaskStatusEnum
from todolist.repositories.base import TaskRepository


class SqlAlchemyTaskRepository(TaskRepository):
    """Task repository backed by a SQLAlchemy Session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: Task) -> Task:
        self._session.add(task)
        self._session.flush()
        return task

    def get(self, task_id: int) -> Task | None:
        return self._session.get(Task, task_id)

    def list_by_project(self, project_id: int) -> Sequence[Task]:
        stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.created_at)
        )
        return list(self._session.execute(stmt).scalars().all())

    def list_overdue(self, now: datetime) -> Sequence[Task]:
        """
        Overdue = has a deadline, deadline < now, and not done.
        """
        stmt = (
            select(Task)
            .where(
                and_(
                    Task.deadline.is_not(None),
                    Task.deadline < now,
                    Task.status != TaskStatusEnum.DONE,
                )
            )
            .order_by(Task.deadline)
        )
        return list(self._session.execute(stmt).scalars().all())

    def delete(self, task: Task) -> None:
        self._session.delete(task)
