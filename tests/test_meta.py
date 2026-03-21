"""Tests for pyramid_sa.meta — Base, AuditMixin, event listeners."""

from tests.conftest import Item


def test_as_dict_returns_column_values(dbsession):
    """Verify as_dict includes all column values."""
    item = Item(name="test-item")
    dbsession.add(item)
    dbsession.flush()

    result = item.as_dict()
    assert result["name"] == "test-item"


def test_as_dict_hides_internal_id(dbsession):
    """Verify as_dict replaces the integer id with uuid when hiding internals."""
    item = Item(name="test-item")
    dbsession.add(item)
    dbsession.flush()

    result = item.as_dict(hide_internal_fields=True)
    assert "id" in result
    assert result["id"] == item.uuid


def test_as_dict_converts_to_camel_case(dbsession):
    """Verify as_dict converts snake_case keys to camelCase."""
    item = Item(name="test-item")
    dbsession.add(item)
    dbsession.flush()

    result = item.as_dict(convert_to_camel=True)
    assert "createdAt" in result


def test_as_dict_no_camel(dbsession):
    """Verify as_dict preserves snake_case keys when camel conversion is off."""
    item = Item(name="test-item")
    dbsession.add(item)
    dbsession.flush()

    result = item.as_dict(convert_to_camel=False)
    assert "created_at" in result


def test_as_dict_exclude(dbsession):
    """Verify as_dict omits excluded fields from the result."""
    item = Item(name="test-item")
    dbsession.add(item)
    dbsession.flush()

    result = item.as_dict(exclude=["name"])
    assert "name" not in result


def test_copy_with(dbsession):
    """Verify copy_with creates a detached copy with overridden attributes."""
    item = Item(name="original")
    dbsession.add(item)
    dbsession.flush()

    copy = item.copy_with(name="copy")
    assert copy.name == "copy"
    assert copy.id is None
    assert isinstance(copy, Item)


def test_before_insert_sets_created_by(request_dbsession):
    """Verify the before_insert listener populates created_by and created_ip."""
    item = Item(name="audited-item")
    request_dbsession.add(item)
    request_dbsession.flush()

    assert item.created_by == "test-user"
    assert item.created_ip == "127.0.0.1"


def test_before_update_sets_updated_by(request_dbsession):
    """Verify the before_update listener populates updated_by and updated_ip."""
    item = Item(name="audited-item")
    request_dbsession.add(item)
    request_dbsession.flush()

    item.name = "updated-name"
    request_dbsession.flush()

    assert item.updated_by == "test-user"
    assert item.updated_ip == "127.0.0.1"


def test_no_request_does_not_fail(dbsession):
    """Verify audit listeners gracefully handle sessions without a request."""
    item = Item(name="no-request")
    dbsession.add(item)
    dbsession.flush()

    assert item.created_by is None
    assert item.created_ip is None
