"""
Database engine and session factory.

This module is responsible for:
- loading DATABASE_URL from environment (.env)
- creating the SQLAlchemy engine
- providing a SessionLocal factory
- optional context manager for working with sessions
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# 1) Load environment variables from .env (if present)
load_dotenv()

# 2) Read the DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fail fast if not configured
    raise RuntimeError(
        "DATABASE_URL is not set. Did you create .env and run docker compose up?"
    )

# 3) Create the SQLAlchemy engine
# echo=True will log SQL queries; you can turn it on if you want to see SQL.
engine = create_engine(DATABASE_URL, echo=False, future=True)

# 4) Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.

    Usage:
        from todolist.db.session import session_scope

        with session_scope() as session:
            # use session here
            ...
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """
    Simple health-check: try `SELECT 1` against the DB.
    Returns True if OK, raises on failure.
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        value = result.scalar_one()
        return value == 1
