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
    TaskNotFound,
)
from todolist.repositories.sqlalchemy_task import SqlAlchemyTaskRepository
from todolist.schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskStatusUpdate
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

@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update a task in a project",
    description="Partially update a task's title, description, status or deadline.",
)
def update_task_for_project(
    project_id: int,
    task_id: int,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
):
    """
    Update a task using TaskService.update_task.
    We also enforce that the task really belongs to the given project.
    """
    try:
        core_task = service.update_task(
            task_id=task_id,
            title=payload.title,
            description=payload.description,
            status=payload.status.value if payload.status is not None else None,
            deadline=payload.deadline,
        )
    except TaskNotFound as exc:
        # task does not exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValidationError as exc:
        # invalid title/description/status/deadline according to your business rules
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # extra safety: URL's project_id must match the task's project_id
    if core_task.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"task #{task_id} does not belong to project #{project_id}",
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
        closed_at=None,   # domain Task doesn’t track this; ok to expose as null
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task from a project",
    description="Delete a task by id within the given project.",
)
def delete_task_for_project(
    project_id: int,
    task_id: int,
    service: TaskService = Depends(get_task_service),
):
    """
    Delete a task using TaskService.delete_task(project_id, task_id).

    - If task doesn't exist -> TaskNotFound -> 404
    - If task belongs to another project -> ValidationError -> 400
    """
    try:
        service.delete_task(project_id=project_id, task_id=task_id)
    except TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValidationError as exc:
        # e.g. "task #X does not belong to project #Y"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 204: no body
    return None


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Get a single task in a project",
    description="Return one task by id, ensuring it belongs to the given project.",
)
def get_task_for_project(
    project_id: int,
    task_id: int,
    service: TaskService = Depends(get_task_service),
):
    """
    Fetch one task using TaskService.get_task_for_project(project_id, task_id)
    and map it to the TaskRead schema.
    """
    try:
        core_task = service.get_task_for_project(project_id=project_id, task_id=task_id)
    except TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValidationError as exc:
        # task exists but doesn't belong to this project
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return TaskRead(
        id=core_task.id,
        title=core_task.title,
        description=core_task.description,
        status=core_task.status,
        deadline=core_task.deadline,
        project_id=core_task.project_id,
        created_at=core_task.created_at,
        closed_at=None,  # domain Task doesn't track this; we expose null
    )

@router.patch(
    "/{task_id}/status",
    response_model=TaskRead,
    summary="Change status of a task",
    description="Change the status of a task to todo / doing / done.",
)
def set_task_status_for_project(
    project_id: int,
    task_id: int,
    payload: TaskStatusUpdate,
    service: TaskService = Depends(get_task_service),
):
    """
    Change the status of a task using TaskService.set_task_status.

    We first ensure the task belongs to the given project,
    then we call set_task_status for the actual update.
    """
    try:
        # ensure task exists and belongs to this project
        service.get_task_for_project(project_id=project_id, task_id=task_id)

        # now update the status
        core_task = service.set_task_status(
            task_id=task_id,
            status=payload.status.value,  # TaskStatusEnum -> "todo"/"doing"/"done"
        )
    except TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValidationError as exc:
        # invalid status or other business rule
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return TaskRead(
        id=core_task.id,
        title=core_task.title,
        description=core_task.description,
        status=core_task.status,
        deadline=core_task.deadline,
        project_id=core_task.project_id,
        created_at=core_task.created_at,
        closed_at=None,
    )
