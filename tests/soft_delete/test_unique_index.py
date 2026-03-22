"""Tests for automatic unique index transformation on soft-delete models."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from tests.soft_delete.app.models import Article


def test_unique_conflict_on_active_rows(dbsession):
    """Verify two active rows with the same unique slug still conflict."""
    a1 = Article(slug="dupe", title="First")
    dbsession.add(a1)
    dbsession.flush()

    a2 = Article(slug="dupe", title="Second")
    dbsession.add(a2)

    with pytest.raises(IntegrityError):
        dbsession.flush()

    dbsession.rollback()


def test_soft_deleted_unique_allows_reuse(dbsession):
    """Verify a soft-deleted row's unique value can be reused by a new active row."""
    a1 = Article(slug="reusable", title="Original")
    dbsession.add(a1)
    dbsession.flush()

    dbsession.delete(a1)
    dbsession.flush()

    a2 = Article(slug="reusable", title="Replacement")
    dbsession.add(a2)
    dbsession.flush()

    active = dbsession.execute(
        select(Article).where(Article.slug == "reusable")
    ).scalar_one()
    assert active.title == "Replacement"

    all_rows = (
        dbsession.execute(
            select(Article)
            .where(Article.slug == "reusable")
            .execution_options(include_deleted=True)
        )
        .scalars()
        .all()
    )
    assert len(all_rows) == 2
