"""Tests for pyramid_sa_testing — pytest plugin fixtures."""

from __future__ import annotations

import uuid  # noqa: TCH003 — needed at runtime for SQLAlchemy mapped annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from pyramid_sa import Base, generate_uuid


class Widget(Base):
    """Test-only model for verifying plugin fixtures."""

    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
    label: Mapped[str] = mapped_column(String(100))


def test_tm_is_doomed(pyramid_sa_tm):
    """Verify the transaction manager starts in a doomed state."""
    assert pyramid_sa_tm.isDoomed()


def test_dbsession_works(pyramid_sa_dbsession):
    """Verify the plugin dbsession can persist and flush objects."""
    widget = Widget(label="test-widget")
    pyramid_sa_dbsession.add(widget)
    pyramid_sa_dbsession.flush()

    assert widget.id is not None
    assert widget.label == "test-widget"


def test_testapp_makes_requests(pyramid_sa_testapp):
    """Verify the plugin testapp can send HTTP requests."""
    response = pyramid_sa_testapp.get("/health", status=200)
    assert response.json["status"] == "ok"


def test_app_request_has_dbsession(pyramid_sa_app_request):
    """Verify the app request object has a dbsession attribute."""
    assert pyramid_sa_app_request.dbsession is not None


def test_dbsession_rolls_back_between_tests(pyramid_sa_dbsession):
    """This test runs after test_dbsession_works — the widget should not exist."""
    count = pyramid_sa_dbsession.query(Widget).count()
    assert count == 0
