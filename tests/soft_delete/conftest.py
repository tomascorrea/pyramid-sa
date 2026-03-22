"""Fixtures for soft delete tests."""

from __future__ import annotations

import uuid  # noqa: TCH003 — needed at runtime for SQLAlchemy mapped annotations
from typing import TYPE_CHECKING

import pytest
from pyramid.config import Configurator
from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pyramid_sa import AuditMixin, Base, SoftDeleteMixin, generate_uuid, get_tm_session
from tests.conftest import TestSecurityPolicy

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyramid.router import Router


class Article(AuditMixin, SoftDeleteMixin, Base):
    """Soft-deletable model with a unique constraint for testing."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    comments: Mapped[list[Comment]] = relationship(back_populates="article")


class Comment(SoftDeleteMixin, Base):
    """Soft-deletable child model for relationship filtering tests."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(String(500))
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    article: Mapped[Article] = relationship(back_populates="comments")


class Tag(Base):
    """Non-soft-deletable model for comparison tests."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class Task(SoftDeleteMixin, Base):
    """Model with SoftDeleteMixin used against an app without the directive."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))


@pytest.fixture(scope="session")
def db_engine():
    """Engine WITHOUT upfront create_all.

    Tables are created by the ``app`` fixture after the soft-delete directive
    has transformed unique constraints into filtered partial indexes.
    """
    engine = create_engine("sqlite://")
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def build_app(db_engine):
    """App factory with audit AND soft delete enabled."""

    def _build(configure: Callable[[Configurator], None] | None = None) -> Router:
        config = Configurator(settings={})
        config.registry["dbengine"] = db_engine
        config.include("pyramid_sa")
        config.sa_enable_audit()
        config.sa_enable_soft_delete()
        config.set_security_policy(TestSecurityPolicy())
        if configure is not None:
            configure(config)
        return config.make_wsgi_app()

    return _build


@pytest.fixture(scope="session")
def app(build_app, db_engine):
    """WSGI app with soft delete enabled.

    Tables are created AFTER the app is configured so that the
    unique-index transformation has already been applied to the metadata.
    """
    application = build_app()
    Base.metadata.create_all(db_engine)
    return application


@pytest.fixture(scope="session")
def no_sd_app(db_engine):
    """WSGI app with audit only — soft delete NOT enabled."""
    config = Configurator(settings={})
    config.registry["dbengine"] = db_engine
    config.include("pyramid_sa")
    config.sa_enable_audit()
    config.set_security_policy(TestSecurityPolicy())
    return config.make_wsgi_app()


@pytest.fixture()
def no_sd_dbsession(no_sd_app, tm):
    """Session from the app without soft delete."""
    session_factory = no_sd_app.registry["dbsession_factory"]
    return get_tm_session(session_factory, tm)
