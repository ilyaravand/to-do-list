# todolist/api/v1/tasks.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from todolist.db.session import SessionLocal
from todolist.core.services import TaskService
from todolist.core.errors import (
    ProjectNotFound,
    TaskLimitReached,
    ValidationError,
)
from todolist.repositories.sqlalchemy_task import SqlAlchemyTaskRepository
from todolist.schemas.task import TaskCreate, TaskRead, TaskUpdate  # TaskUpdate for later
from todolist.repositories.sqlalchemy_project import SqlAlchemyProjectRepository


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


@router.post(
    "/",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task in a project",
    description="Create a task inside the given project with title, optional description, status and deadline.",
)
def create_task_for_project(
    project_id: int,
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
):
    """
    Create a task using the existing TaskService.create_task business logic.
    """
    try:
        core_task = service.create_task(
            project_id=project_id,
            title=payload.title,
            description=payload.description or "",
            status=payload.status.value if payload.status is not None else None,
            deadline=payload.deadline,  # TaskService can handle date or str
        )
    except ProjectNotFound as exc:
        # project does not exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except TaskLimitReached as exc:
        # reached MAX_NUMBER_OF_TASK
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except ValidationError as exc:
        # invalid status, title too long, description too long, bad deadline, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Map core Task -> TaskRead
    return TaskRead(
        id=core_task.id,
        title=core_task.title,
        description=core_task.description,
        status=core_task.status,
        deadline=core_task.deadline,
        project_id=core_task.project_id,
        created_at=core_task.created_at,
        closed_at=None,  # core Task doesn't track this; fine to expose as null
    )
