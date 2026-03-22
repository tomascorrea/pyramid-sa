"""Tests for soft-delete audit fields (deleted_by, deleted_ip)."""

from tests.soft_delete.conftest import Article


def test_soft_delete_populates_audit_from_request(authenticated_request):
    """Verify soft_delete() sets deleted_by and deleted_ip from the request."""
    dbsession = authenticated_request.dbsession
    article = Article(slug="audit-sd", title="Audited")
    dbsession.add(article)
    dbsession.flush()

    article.soft_delete()
    dbsession.flush()

    assert article.deleted_by == "test-user"
    assert article.deleted_ip == "127.0.0.1"


def test_session_delete_populates_audit_from_request(authenticated_request):
    """Verify session.delete() also populates deleted_by and deleted_ip."""
    dbsession = authenticated_request.dbsession
    article = Article(slug="audit-sess", title="Via Session")
    dbsession.add(article)
    dbsession.flush()

    dbsession.delete(article)
    dbsession.flush()

    assert article.deleted_by == "test-user"
    assert article.deleted_ip == "127.0.0.1"


def test_soft_delete_without_request_leaves_audit_none(dbsession):
    """Verify audit fields are None when no request is available."""
    article = Article(slug="no-req", title="No Request")
    dbsession.add(article)
    dbsession.flush()

    article.soft_delete()
    dbsession.flush()

    assert article.deleted_by is None
    assert article.deleted_ip is None
