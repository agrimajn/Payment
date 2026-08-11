"""Database connection setup.

Defines the SQLAlchemy engine (the low-level connection to the SQLite
file), a session factory for talking to it, and the declarative base
that models.py builds table definitions from.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

# check_same_thread=False is required for SQLite specifically: SQLite
# normally restricts a connection to the thread that created it, but
# FastAPI may handle requests on different threads. This is safe here
# because each request gets its own session (see get_db in routes.py).
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class that all ORM models inherit from."""
