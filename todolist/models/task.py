from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from todolist.db.base import Base


class TaskStatusEnum(str, Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Basic fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    # Status: todo / doing / done
    status: Mapped[str] = mapped_column(
        SAEnum(
            TaskStatusEnum.TODO,
            TaskStatusEnum.DOING,
            TaskStatusEnum.DONE,
            name="task_status_enum",
        ),
        default=TaskStatusEnum.TODO,
        nullable=False,
    )

    # Deadlines & timestamps
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # When the task was actually closed (for the auto-close feature in phase 2)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Foreign key to projects.id
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationship back to Project
    project: Mapped["Project"] = relationship(
        back_populates="tasks",
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id!r} title={self.title!r} status={self.status!r}>"
