"""Tests for pyramid_sa.meta — Base, AuditMixin, event listeners."""

from tests.conftest import Item


class TestAuditMixin:
    def test_as_dict_returns_column_values(self, dbsession):
        item = Item(name="test-item")
        dbsession.add(item)
        dbsession.flush()

        result = item.as_dict()
        assert result["name"] == "test-item"

    def test_as_dict_hides_internal_id(self, dbsession):
        item = Item(name="test-item")
        dbsession.add(item)
        dbsession.flush()

        result = item.as_dict(hide_internal_fields=True)
        assert "id" in result
        assert result["id"] == item.uuid

    def test_as_dict_converts_to_camel_case(self, dbsession):
        item = Item(name="test-item")
        dbsession.add(item)
        dbsession.flush()

        result = item.as_dict(convert_to_camel=True)
        assert "createdAt" in result

    def test_as_dict_no_camel(self, dbsession):
        item = Item(name="test-item")
        dbsession.add(item)
        dbsession.flush()

        result = item.as_dict(convert_to_camel=False)
        assert "created_at" in result

    def test_as_dict_exclude(self, dbsession):
        item = Item(name="test-item")
        dbsession.add(item)
        dbsession.flush()

        result = item.as_dict(exclude=["name"])
        assert "name" not in result

    def test_copy_with(self, dbsession):
        item = Item(name="original")
        dbsession.add(item)
        dbsession.flush()

        copy = item.copy_with(name="copy")
        assert copy.name == "copy"
        assert copy.id is None
        assert isinstance(copy, Item)


class TestEventListeners:
    def test_before_insert_sets_created_by(self, session_factory, fake_request):
        session = session_factory(info={"request": fake_request})
        item = Item(name="audited-item")
        session.add(item)
        session.flush()

        assert item.created_by == "test-user"
        assert item.created_ip == "127.0.0.1"
        session.rollback()
        session.close()

    def test_before_update_sets_updated_by(self, session_factory, fake_request):
        session = session_factory(info={"request": fake_request})
        item = Item(name="audited-item")
        session.add(item)
        session.flush()

        item.name = "updated-name"
        session.flush()

        assert item.updated_by == "test-user"
        assert item.updated_ip == "127.0.0.1"
        session.rollback()
        session.close()

    def test_no_request_does_not_fail(self, dbsession):
        item = Item(name="no-request")
        dbsession.add(item)
        dbsession.flush()

        assert item.created_by is None
        assert item.created_ip is None
