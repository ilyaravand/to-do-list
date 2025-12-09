# todolist/api/v1/tasks.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from todolist.db.session import SessionLocal
from todolist.core.services import TaskService
from todolist.core.errors import ProjectNotFound
from todolist.repositories.sqlalchemy_task import SqlAlchemyTaskRepository
from todolist.schemas.task import TaskRead



router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["tasks"],
)


# ---------- Dependencies ----------

def get_db():
    """
    FastAPI dependency that yields a DB session and takes care of closing it.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """
    FastAPI dependency that wires SQLAlchemy repository -> TaskService.
    We reuse your existing TaskService + SqlAlchemyTaskRepository.
    """
    from todolist.repositories.sqlalchemy_project import SqlAlchemyProjectRepository

    project_repo = SqlAlchemyProjectRepository(db)
    task_repo = SqlAlchemyTaskRepository(db)
    return TaskService(project_repo=project_repo, task_repo=task_repo)


@router.get("/ping", summary="Ping endpoint for tasks")
def ping_tasks(project_id: int):
    """
    Simple test endpoint to verify that the API wiring works.
    """
    return {"message": f"tasks endpoint is alive for project {project_id}"}


@router.get(
    "/",
    response_model=List[TaskRead],
    summary="List tasks for a project",
    description="Return all tasks of the given project, sorted by creation time.",
)
def list_tasks_for_project(
    project_id: int,
    service: TaskService = Depends(get_task_service),
):
    """
    Controller -> Service -> Repository flow:

    - Controller receives HTTP request
    - Calls TaskService.list_tasks_for_project(project_id)
    - Service uses TaskRepository (SQLAlchemy) to fetch core Task objects
    - We map those core Task objects into Pydantic TaskRead models for the API response
    """
    try:
        core_tasks = service.list_tasks_for_project(project_id)
    except ProjectNotFound as exc:
        # Translate domain-level error to HTTP 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    # Map from core Task (domain) -> Pydantic TaskRead (API schema)
    result: List[TaskRead] = []
    for t in core_tasks:
        result.append(
            TaskRead(
                id=t.id,
                title=t.title,
                description=t.description,
                status=t.status,
                deadline=t.deadline,
                project_id=t.project_id,
                created_at=t.created_at,
                closed_at=getattr(t, "closed_at", None),  # safe in case domain Task lacks this
            )
        )
    return result
