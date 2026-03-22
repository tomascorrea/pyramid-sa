"""Tests verifying behavior when sa_enable_soft_delete() is NOT called."""

from sqlalchemy import select
from tests.no_soft_delete.app.models import Task


def test_delete_hard_deletes_without_directive(dbsession):
    """Without the directive, session.delete() performs a hard delete."""
    task = Task(title="ephemeral")
    dbsession.add(task)
    dbsession.flush()
    task_id = task.id

    dbsession.delete(task)
    dbsession.flush()

    row = dbsession.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()

    assert row is None


def test_query_returns_all_without_directive(dbsession):
    """Without the directive, soft-deleted rows still appear in queries."""
    task = Task(title="manual-sd")
    dbsession.add(task)
    dbsession.flush()

    task.soft_delete()
    dbsession.flush()

    results = dbsession.execute(select(Task)).scalars().all()
    titles = {t.title for t in results}

    assert "manual-sd" in titles
