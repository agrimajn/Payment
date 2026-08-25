"""Shared pytest fixtures.

Every test gets a fresh, isolated in-memory SQLite database -- never
the real tokenizer.db -- so tests can't pollute real data or leak
state between each other.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import API_KEY
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    """A fresh in-memory database, created and torn down per test.

    StaticPool makes SQLAlchemy reuse a single connection for the
    whole engine -- without it, an in-memory SQLite database would
    vanish between queries, since each new connection normally gets
    its own separate (and separately empty) in-memory database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """A TestClient whose requests use db_session instead of the real database."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Headers carrying the real API key, for hitting protected endpoints."""
    return {"X-API-Key": API_KEY}


@pytest.fixture()
def valid_card_payload() -> dict[str, object]:
    """A Luhn-valid card payload reusable across multiple tests."""
    return {
        "card_number": "4111111111111111",
        "expiration_month": 12,
        "expiration_year": 2030,
        "cvv": "123",
    }
