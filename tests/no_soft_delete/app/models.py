"""Models for the no-soft-delete test app."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from pyramid_sa import Base, SoftDeleteMixin


class Task(SoftDeleteMixin, Base):
    """Has SoftDeleteMixin columns but the app never enables the directive."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
