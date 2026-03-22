"""Tests for the explicit soft-delete unique index APIs."""

import logging

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from pyramid_sa import Base, SoftDeleteUniqueIndex, soft_delete_mapped_column
from pyramid_sa.soft_delete import _ACTIVE_INDEX_SUFFIX
from tests.soft_delete.app.models import Article, ScopedArticle


def test_soft_delete_mapped_column_creates_partial_index(app):
    """soft_delete_mapped_column(unique=True) produces a partial unique index."""
    table = Article.__table__
    idx_name = f"uq_{table.name}_slug{_ACTIVE_INDEX_SUFFIX}"

    matching = [idx for idx in table.indexes if idx.name == idx_name]
    assert len(matching) == 1

    idx = matching[0]
    assert idx.unique is True
    assert [c.name for c in idx.columns] == ["slug"]
    assert idx.dialect_options["postgresql"]["where"] is not None
    assert idx.dialect_options["sqlite"]["where"] is not None


def test_soft_delete_unique_index_creates_partial_index(app):
    """SoftDeleteUniqueIndex in __table_args__ produces a partial unique index."""
    table = ScopedArticle.__table__
    idx_name = f"uq_{table.name}_tenant_id_slug{_ACTIVE_INDEX_SUFFIX}"

    matching = [idx for idx in table.indexes if idx.name == idx_name]
    assert len(matching) == 1

    idx = matching[0]
    assert idx.unique is True
    assert [c.name for c in idx.columns] == ["tenant_id", "slug"]
    assert idx.dialect_options["postgresql"]["where"] is not None
    assert idx.dialect_options["sqlite"]["where"] is not None


def test_plain_unique_stays_global(app):
    """mapped_column(unique=True) on a soft-delete model stays globally unique."""
    table = Article.__table__
    active_idx_names = {
        idx.name for idx in table.indexes if idx.name and idx.name.endswith("_active")
    }
    assert "uq_articles_uuid_active" not in active_idx_names


def test_plain_unique_constraint_warns(caplog):
    """A plain UniqueConstraint on a soft-delete model logs a warning."""
    from pyramid_sa.soft_delete import _warn_plain_unique_constraints

    with caplog.at_level(logging.WARNING, logger="pyramid_sa.soft_delete"):
        _warn_plain_unique_constraints(Article)

    assert any("uuid" in record.message for record in caplog.records)
    assert any("SoftDeleteUniqueIndex" in record.message for record in caplog.records)


def test_soft_delete_unique_index_on_non_soft_delete_model_raises():
    """SoftDeleteUniqueIndex on a model without SoftDeleteMixin raises TypeError."""
    with pytest.raises(TypeError, match="deleted_at"):

        class BadModel(Base):
            __tablename__ = "bad_model_no_soft_delete"
            __table_args__ = (SoftDeleteUniqueIndex("name"),)

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))


def test_soft_delete_mapped_column_without_unique_is_plain():
    """soft_delete_mapped_column without unique=True behaves like mapped_column."""
    col = soft_delete_mapped_column(String(100))
    assert not col.column.info.get("soft_delete_unique")


def test_soft_delete_mapped_column_preserves_info():
    """soft_delete_mapped_column merges with existing info dict."""
    col = soft_delete_mapped_column(String(100), unique=True, info={"custom": "value"})
    assert col.column.info["soft_delete_unique"] is True
    assert col.column.info["custom"] == "value"
