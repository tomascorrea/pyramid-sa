# Testing

The `pyramid-sa-testing` companion package provides a pytest plugin with fixtures for database-backed tests. It is auto-discovered via the `pytest11` entry point — no manual registration needed.

## Installation

```bash
pip install pyramid-sa-testing
```

This is a dev-only dependency. It pulls in `webtest`, `transaction`, `pytest-postgresql`, and `psycopg`.

## Fixtures

| Fixture | Scope | Description |
|---|---|---|
| `pyramid_sa_engine` | session | PostgreSQL engine via pytest-postgresql. Starts a temporary PostgreSQL process on a random port. |
| `pyramid_sa_tm` | function | Doomed transaction manager — auto-rollback after each test |
| `pyramid_sa_dbsession` | function | Database session bound to the test transaction |
| `pyramid_sa_testapp` | function | WebTest `TestApp` with the test session injected |
| `pyramid_sa_app_request` | function | Real Pyramid request (via `pyramid.scripting.prepare`) for service-layer testing |

## Required `app` fixture

Your `conftest.py` must provide a session-scoped `app` fixture that creates your Pyramid WSGI application and initializes the schema:

```python
import pytest
from pyramid_sa import Base


@pytest.fixture(scope="session")
def app(pyramid_sa_engine):
    from myapp.app import create_app

    wsgi_app = create_app(dbengine=pyramid_sa_engine)
    Base.metadata.create_all(pyramid_sa_engine)
    return wsgi_app
```

The plugin fixtures depend on `app` to access `app.registry["dbsession_factory"]`.

## Test isolation

Each test runs inside a doomed transaction. The `pyramid_sa_tm` fixture:

1. Begins a new transaction
2. Immediately dooms it (marks for rollback)
3. Yields the transaction manager to the test
4. Aborts the transaction after the test completes

This means every database change made during a test is rolled back automatically — no cleanup needed.

## Usage examples

### Testing views with `pyramid_sa_testapp`

```python
def test_list_items(pyramid_sa_testapp, pyramid_sa_dbsession):
    pyramid_sa_dbsession.add(Item(name="Widget"))
    pyramid_sa_dbsession.flush()

    response = pyramid_sa_testapp.get("/items", status=200)
    assert len(response.json) == 1
```

### Testing services with `pyramid_sa_app_request`

```python
def test_create_item(pyramid_sa_app_request, pyramid_sa_dbsession):
    request = pyramid_sa_app_request
    request.dbsession = pyramid_sa_dbsession

    item = create_item(request, name="Widget")
    assert item.name == "Widget"
    assert item.created_by is not None
```

### Testing with `pyramid_sa_dbsession` directly

```python
def test_soft_delete(pyramid_sa_dbsession):
    item = Item(name="Widget")
    pyramid_sa_dbsession.add(item)
    pyramid_sa_dbsession.flush()

    pyramid_sa_dbsession.delete(item)
    pyramid_sa_dbsession.flush()

    assert item.is_deleted
```

## PostgreSQL by default

`pyramid_sa_engine` uses pytest-postgresql to start a temporary PostgreSQL server. This ensures tests run against real PostgreSQL behavior (partial indexes, constraint semantics, etc.).

The devcontainer includes PostgreSQL server binaries so `postgresql_proc` can start its own instance. For CI environments, ensure PostgreSQL is available or override `pyramid_sa_engine` to use a different backend.

### Overriding the engine

To use a different database for tests, override `pyramid_sa_engine` in your `conftest.py`:

```python
@pytest.fixture(scope="session")
def pyramid_sa_engine():
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()
```
