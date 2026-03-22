"""Tests for SoftDeleteMixin — columns, soft_delete(), restore(), is_deleted."""

from tests.soft_delete.app.models import Article


def test_soft_delete_columns_exist(dbsession):
    """Verify soft-delete columns are present on the model."""
    article = Article(slug="test-cols", title="Test")
    dbsession.add(article)
    dbsession.flush()

    assert article.deleted_at is None
    assert article.deleted_by is None
    assert article.deleted_ip is None


def test_is_deleted_false_by_default(dbsession):
    """Verify is_deleted is False for a new instance."""
    article = Article(slug="test-prop", title="Test")
    dbsession.add(article)
    dbsession.flush()

    assert article.is_deleted is False


def test_soft_delete_sets_deleted_at(dbsession):
    """Verify soft_delete() sets deleted_at to a non-None datetime."""
    article = Article(slug="test-sd", title="Test")
    dbsession.add(article)
    dbsession.flush()

    article.soft_delete()
    dbsession.flush()

    assert article.deleted_at is not None
    assert article.is_deleted is True


def test_restore_clears_deleted_fields(dbsession):
    """Verify restore() resets all deleted_* fields to None."""
    article = Article(slug="test-restore", title="Test")
    dbsession.add(article)
    dbsession.flush()

    article.soft_delete()
    dbsession.flush()
    assert article.is_deleted is True

    article.restore()
    dbsession.flush()

    assert article.deleted_at is None
    assert article.deleted_by is None
    assert article.deleted_ip is None
    assert article.is_deleted is False
