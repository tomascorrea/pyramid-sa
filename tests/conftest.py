"""Shared test fixtures for pyramid-sa."""

from __future__ import annotations

import uuid  # noqa: TCH003 — needed at runtime for SQLAlchemy mapped annotations

import pytest
from sqlalchemy import String, create_engine
from sqlalchemy.orm import Mapped, mapped_column

from pyramid_sa import Base, generate_uuid, get_session_factory


class Item(Base):
    """Example model used by tests."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
    name: Mapped[str] = mapped_column(String(255))


class FakeRequest:
    """Minimal request-like object for audit event listener tests."""

    def __init__(self, userid="test-user", client_addr="127.0.0.1"):
        self.authenticated_userid = userid
        self.client_addr = client_addr


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(db_engine):
    return get_session_factory(db_engine)


@pytest.fixture()
def dbsession(session_factory):
    session = session_factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def fake_request():
    return FakeRequest()


@pytest.fixture()
def request_dbsession(session_factory, fake_request):
    """Session bound to a fake request — handles rollback and close automatically."""
    session = session_factory(info={"request": fake_request})
    yield session
    session.rollback()
    session.close()
