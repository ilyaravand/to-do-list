# todolist/schemas/task.py
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field, constr

from todolist.models.task import TaskStatusEnum


# ---------- Shared base fields ----------
class TaskBase(BaseModel):
    title: constr(min_length=1, max_length=255) = Field(
        ...,
        description="Short title of the task.",
        example="Finish Phase 3 of software project",
    )
    description: Optional[constr(max_length=4000)] = Field(
        default=None,
        description="Detailed description of the task (optional).",
        example="Implement FastAPI controllers and Pydantic validation.",
    )
    status: TaskStatusEnum = Field(
        default=TaskStatusEnum.TODO,
        description="Current status of the task: todo / doing / done.",
        example="todo",
    )
    deadline: Optional[datetime] = Field(
        default=None,
        description="Optional deadline for the task (YYYY-MM-DD).",
        example="2025-12-31",
    )


# ---------- Create ----------
class TaskCreate(TaskBase):
    """
    Fields required from the client to create a new task.

    We *do not* allow the client to set created_at/closed_at here;
    those are controlled by the server / business logic.
    """
    pass


# ---------- Update (PATCH-style, all optional) ----------
class TaskUpdate(BaseModel):
    """
    Fields that the client is allowed to update for an existing task.

    All fields are optional because this will be used with PATCH semantics.
    """
    title: Optional[constr(min_length=1, max_length=255)] = None
    description: Optional[constr(max_length=4000)] = None
    status: Optional[TaskStatusEnum] = None
    deadline: Optional[datetime] = None


# ---------- Read / Response ----------
class TaskRead(TaskBase):
    """
    How a task is returned from the API.
    Includes read-only fields like id, project_id, created_at, closed_at.
    """
    id: int = Field(..., description="Primary key of the task.")
    project_id: int = Field(
        ...,
        description="ID of the project this task belongs to.",
        example=1,
        ge=1,
    )
    created_at: datetime = Field(
        ...,
        description="When the task was created (server timestamp).",
    )
    closed_at: Optional[datetime] = Field(
        default=None,
        description="When the task was actually closed (if any).",
    )

    class Config:
        from_attributes = True
        # For Pydantic v1:
        # orm_mode = True
        # For Pydantic v2 you can also use:
        # from_attributes = True
