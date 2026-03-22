"""Tests for session.delete() interception and session.hard_delete()."""

from sqlalchemy import select

from tests.soft_delete.app.models import Article, Tag


def test_session_delete_soft_deletes(dbsession):
    """Verify session.delete() performs a soft delete on SoftDeleteMixin models."""
    article = Article(slug="del-soft", title="Soft")
    dbsession.add(article)
    dbsession.flush()
    article_id = article.id

    dbsession.delete(article)
    dbsession.flush()

    row = dbsession.execute(
        select(Article)
        .where(Article.id == article_id)
        .execution_options(include_deleted=True)
    ).scalar_one()

    assert row.deleted_at is not None
    assert row.is_deleted is True


def test_session_hard_delete_removes_row(dbsession):
    """Verify session.hard_delete() issues a real SQL DELETE."""
    article = Article(slug="del-hard", title="Hard")
    dbsession.add(article)
    dbsession.flush()
    article_id = article.id

    dbsession.hard_delete(article)
    dbsession.flush()

    row = dbsession.execute(
        select(Article)
        .where(Article.id == article_id)
        .execution_options(include_deleted=True)
    ).scalar_one_or_none()

    assert row is None


def test_session_delete_on_non_soft_model_hard_deletes(dbsession):
    """Verify session.delete() on a normal model still performs a hard delete."""
    tag = Tag(name="ephemeral")
    dbsession.add(tag)
    dbsession.flush()
    tag_id = tag.id

    dbsession.delete(tag)
    dbsession.flush()

    row = dbsession.execute(select(Tag).where(Tag.id == tag_id)).scalar_one_or_none()

    assert row is None
