"""Models for the soft-delete test app."""

from __future__ import annotations

import uuid  # noqa: TCH003 — needed at runtime for SQLAlchemy mapped annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pyramid_sa import Base, Model, SoftDeleteMixin, generate_uuid


class Article(Model):
    """Soft-deletable model with a unique constraint."""

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
