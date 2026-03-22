"""Tests for automatic soft-delete query filtering."""

from sqlalchemy import select

from tests.soft_delete.app.models import Article


def test_soft_deleted_rows_excluded_from_query(dbsession):
    """Verify soft-deleted rows are automatically excluded from SELECT queries."""
    a1 = Article(slug="visible", title="Visible")
    a2 = Article(slug="hidden", title="Hidden")
    dbsession.add_all([a1, a2])
    dbsession.flush()

    a2.soft_delete()
    dbsession.flush()

    results = dbsession.execute(select(Article)).scalars().all()
    slugs = {a.slug for a in results}

    assert "visible" in slugs
    assert "hidden" not in slugs


def test_include_deleted_bypasses_filter(dbsession):
    """Verify execution_options(include_deleted=True) returns soft-deleted rows."""
    a1 = Article(slug="alive", title="Alive")
    a2 = Article(slug="dead", title="Dead")
    dbsession.add_all([a1, a2])
    dbsession.flush()

    a2.soft_delete()
    dbsession.flush()

    results = (
        dbsession.execute(select(Article).execution_options(include_deleted=True))
        .scalars()
        .all()
    )
    slugs = {a.slug for a in results}

    assert "alive" in slugs
    assert "dead" in slugs


def test_restored_rows_reappear_in_query(dbsession):
    """Verify restored rows are visible again in normal queries."""
    article = Article(slug="comeback", title="Comeback")
    dbsession.add(article)
    dbsession.flush()

    article.soft_delete()
    dbsession.flush()

    results = dbsession.execute(select(Article)).scalars().all()
    assert not any(a.slug == "comeback" for a in results)

    article.restore()
    dbsession.flush()

    results = dbsession.execute(select(Article)).scalars().all()
    assert any(a.slug == "comeback" for a in results)
