"""
Shared SQLAlchemy declarative base for all ORM models.
Any ORM model (Project, Task, etc.) should inherit from Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass
