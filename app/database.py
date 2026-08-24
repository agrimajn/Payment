"""Database connection setup.

Defines the SQLAlchemy engine (the low-level connection to the SQLite
file), a session factory for talking to it, and the declarative base
that models.py builds table definitions from.
"""

from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL

# check_same_thread=False is required for SQLite specifically: SQLite
# normally restricts a connection to the thread that created it, but
# FastAPI may handle requests on different threads. This is safe here
# because each request gets its own session (see get_db below).
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class that all ORM models inherit from."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields one session per request.

    The `finally` block runs after the response is sent (or if an
    exception occurs), guaranteeing the session is always closed
    rather than left open indefinitely.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
