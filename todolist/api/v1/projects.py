# todolist/api/v1/projects.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from todolist.db.session import SessionLocal
from todolist.core.services import ProjectService
from todolist.core.errors import (
    ProjectNotFound,
    ProjectLimitReached,
    DuplicateProjectName,
    ValidationError,
)
from todolist.repositories.sqlalchemy_project import SqlAlchemyProjectRepository
from todolist.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


# ---------- Dependencies ----------

def get_db():
    """
    FastAPI dependency that yields a DB session and handles commit/rollback.
    (Same pattern as in tasks router.)
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


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    repo = SqlAlchemyProjectRepository(db)
    # no cascade_delete_tasks via API (DB already cascades tasks via ORM relationship)
    return ProjectService(repo=repo)

@router.get(
    "/",
    response_model=List[ProjectRead],
    summary="List all projects",
    description="Return all projects ordered by creation time.",
)
def list_projects(service: ProjectService = Depends(get_project_service)):
    core_projects = service.list_projects()
    return [
        ProjectRead(
            id=p.id,
            name=p.name,
            description=p.description or None,
            created_at=p.created_at,
        )
        for p in core_projects
    ]

@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a project with a unique name and optional description.",
)
def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
):
    try:
        core_project = service.create_project(
            name=payload.name,
            description=payload.description or "",
        )
    except ProjectLimitReached as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except DuplicateProjectName as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return ProjectRead(
        id=core_project.id,
        name=core_project.name,
        description=core_project.description or None,
        created_at=core_project.created_at,
    )

@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get a single project",
    description="Return a single project by its ID.",
)
def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
):
    try:
        core_project = service.get_project(project_id)
    except ProjectNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return ProjectRead(
        id=core_project.id,
        name=core_project.name,
        description=core_project.description or None,
        created_at=core_project.created_at,
    )

@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Update a project",
    description="Partially update a project's name and/or description.",
)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
):
    try:
        core_project = service.update_project(
            pid=project_id,
            name=payload.name,
            description=payload.description,
        )
    except ProjectNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DuplicateProjectName as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return ProjectRead(
        id=core_project.id,
        name=core_project.name,
        description=core_project.description or None,
        created_at=core_project.created_at,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Delete a project by ID. Tasks are cascade-deleted by the ORM.",
)
def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
):
    try:
        service.delete_project(project_id)
    except ProjectNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return None
