"""Tests for restore conflict detection on soft-delete models."""

import pytest

from pyramid_sa.models.soft_delete import RestoreConflictError
from tests.soft_delete.app.models import Article, ScopedArticle


def test_restore_raises_on_single_column_conflict(dbsession):
    """Restoring when an active row holds the same unique value raises."""
    original = Article(slug="taken", title="Original")
    dbsession.add(original)
    dbsession.flush()

    dbsession.delete(original)
    dbsession.flush()

    replacement = Article(slug="taken", title="Replacement")
    dbsession.add(replacement)
    dbsession.flush()

    deleted = (
        dbsession.execute(
            Article.__table__.select().where(Article.__table__.c.title == "Original")
        )
        .mappings()
        .one()
    )
    original_reloaded = dbsession.get(
        Article,
        deleted["id"],
        execution_options={"include_deleted": True},
    )

    with pytest.raises(RestoreConflictError, match="slug") as exc_info:
        original_reloaded.restore()

    assert ("slug",) in exc_info.value.conflicts
    assert exc_info.value.instance is original_reloaded


def test_restore_succeeds_when_no_conflict(dbsession):
    """Restoring a soft-deleted row works when no active row conflicts."""
    article = Article(slug="free-slug", title="Will restore")
    dbsession.add(article)
    dbsession.flush()

    dbsession.delete(article)
    dbsession.flush()

    deleted = dbsession.get(
        Article,
        article.id,
        execution_options={"include_deleted": True},
    )
    deleted.restore()
    dbsession.flush()

    assert not deleted.is_deleted
    assert deleted.deleted_by is None
    assert deleted.deleted_ip is None


def test_can_restore_returns_conflicts(dbsession):
    """can_restore() reports conflicting columns without modifying the instance."""
    a1 = Article(slug="conflict-check", title="First")
    dbsession.add(a1)
    dbsession.flush()

    dbsession.delete(a1)
    dbsession.flush()

    a2 = Article(slug="conflict-check", title="Second")
    dbsession.add(a2)
    dbsession.flush()

    stale = dbsession.get(
        Article,
        a1.id,
        execution_options={"include_deleted": True},
    )

    conflicts = stale.can_restore()

    assert ("slug",) in conflicts
    assert stale.is_deleted, "can_restore must not modify the instance"


def test_can_restore_returns_empty_when_safe(dbsession):
    """can_restore() returns an empty list when no conflicts exist."""
    article = Article(slug="safe-slug", title="Safe")
    dbsession.add(article)
    dbsession.flush()

    dbsession.delete(article)
    dbsession.flush()

    deleted = dbsession.get(
        Article,
        article.id,
        execution_options={"include_deleted": True},
    )

    assert deleted.can_restore() == []


def test_restore_conflict_on_multi_column_unique(dbsession):
    """Multi-column unique constraint conflicts are detected as a tuple."""
    sa1 = ScopedArticle(tenant_id="acme", slug="intro", title="Original")
    dbsession.add(sa1)
    dbsession.flush()

    dbsession.delete(sa1)
    dbsession.flush()

    sa2 = ScopedArticle(tenant_id="acme", slug="intro", title="Replacement")
    dbsession.add(sa2)
    dbsession.flush()

    deleted = dbsession.get(
        ScopedArticle,
        sa1.id,
        execution_options={"include_deleted": True},
    )

    with pytest.raises(RestoreConflictError) as exc_info:
        deleted.restore()

    assert ("tenant_id", "slug") in exc_info.value.conflicts


def test_multi_column_no_conflict_different_tenant(dbsession):
    """Same slug in a different tenant does not conflict."""
    sa1 = ScopedArticle(tenant_id="acme", slug="shared", title="Acme's")
    dbsession.add(sa1)
    dbsession.flush()

    dbsession.delete(sa1)
    dbsession.flush()

    sa2 = ScopedArticle(tenant_id="globex", slug="shared", title="Globex's")
    dbsession.add(sa2)
    dbsession.flush()

    deleted = dbsession.get(
        ScopedArticle,
        sa1.id,
        execution_options={"include_deleted": True},
    )

    deleted.restore()
    dbsession.flush()

    assert not deleted.is_deleted
