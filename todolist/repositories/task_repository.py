# todolist/repositories/task_repository.py
from typing import List, Optional

from sqlalchemy.orm import Session

from todolist.models.task import Task  # <- import your real Task model


def get(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()


def list_all(db: Session) -> List[Task]:
    return db.query(Task).order_by(Task.created_at.desc()).all()


def create(
    db: Session,
    *,
    title: str,
    description: str | None,
    due_date,
) -> Task:
    task = Task(
        title=title,
        description=description,
        due_date=due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update(db: Session, task: Task, **fields) -> Task:
    for key, value in fields.items():
        if value is not None:
            setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
