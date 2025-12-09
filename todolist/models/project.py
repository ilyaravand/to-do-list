from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from todolist.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Project name should be unique (one of the rules from phase 1)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Optional description
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationship to tasks (1 project → many tasks)
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id!r} name={self.name!r}>"
