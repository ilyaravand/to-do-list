# todolist/schemas/project.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr


class ProjectBase(BaseModel):
    name: constr(min_length=1, max_length=255) = Field(
        ...,
        description="Project name (must be unique).",
        example="My First Project",
    )
    description: Optional[constr(max_length=4000)] = Field(
        default=None,
        description="Optional project description.",
        example="This project is used to test the Phase 3 API.",
    )


class ProjectCreate(ProjectBase):
    """Input model for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Input model for partially updating a project."""
    name: Optional[constr(min_length=1, max_length=255)] = None
    description: Optional[constr(max_length=4000)] = None


class ProjectRead(ProjectBase):
    """Output model for returning projects from the API."""
    id: int = Field(..., description="Project ID.")
    created_at: datetime = Field(
        ...,
        description="When the project was created (server timestamp).",
    )

    class Config:
        from_attributes = True  # Pydantic v2
