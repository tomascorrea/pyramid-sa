# pyramid-sa

Pyramid SQLAlchemy Integration — a reusable library that wires SQLAlchemy into any Pyramid application.

## Features

- **Session management** — engine, transaction-managed sessions, `request.dbsession`
- **Declarative base** — `Base` with naming conventions and utility methods (`as_dict`, `copy_with`)
- **Audit trail** — opt-in `AuditMixin` tracking created/updated by whom and when
- **Soft delete** — opt-in `SoftDeleteMixin` with query filtering, unique indexes, and safe restore
- **Error mapping** — `NoResultFound` → 404, `IntegrityError` → 409, with customizable bodies
- **JSON rendering** — `datetime`, `date`, `UUID` adapters out of the box
- **Alembic scaffold** — `db init-alembic` for pre-wired migration setup
- **CLI commands** — `db drop`, `db initialize` for schema management
- **Test fixtures** — companion `pyramid-sa-testing` package with PostgreSQL-backed pytest plugin

## Documentation

Full documentation is available at the [docs site](docs/index.md), covering all features in detail.

## Installation

```bash
pip install pyramid-sa
```

For test fixtures (dev only):

```bash
pip install pyramid-sa-testing
```

## Quick start

In your Pyramid app factory:

```python
from pyramid.config import Configurator


def create_app(global_config=None, dbengine=None, **settings):
    config = Configurator(settings=settings)

    if dbengine is not None:
        config.registry["dbengine"] = dbengine

    config.include("pyramid_sa")
    config.sa_enable_audit()          # optional: auto-populate audit fields
    config.sa_enable_soft_delete()    # optional: soft-delete behavior
    config.sa_scan_models("myapp.models")

    config.scan(".views")
    return config.make_wsgi_app()
```

### What `config.include("pyramid_sa")` does

1. Includes `pyramid_tm` (transaction management)
2. Creates the SQLAlchemy engine from `sqlalchemy.url` in settings (or uses `config.registry["dbengine"]` if pre-set)
3. Registers a session factory and adds `request.dbsession` as a reified property
4. Adds an exception tween (`NoResultFound` → 404, `IntegrityError` → 409)
5. Configures a JSON renderer with adapters for `datetime`, `date`, and `UUID`
6. Registers directives: `sa_scan_models`, `sa_enable_audit`, `sa_enable_soft_delete`, `sa_error_formatter`

### Base vs Model

Use `Base` for plain models. Use `Model` for models that need both audit columns and soft-delete:

```python
from pyramid_sa import Base, Model, generate_uuid


class Item(Base):
    """Plain model — no audit or soft-delete columns."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
    name: Mapped[str] = mapped_column(String(255))


class Article(Model):
    """Audited + soft-deletable model."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
```

See the [Models docs](docs/models.md) for `as_dict()`, `copy_with()`, and selective mixin usage.

### Alembic

Scaffold alembic in your project:

```bash
db init-alembic
```

Then edit `alembic/env.py` to import your models:

```python
from alembic import context

from pyramid_sa import Base
from pyramid_sa.scripts.alembic import run_migrations_offline, run_migrations_online

import myapp.models  # noqa: F401

target_metadata = Base.metadata

if context.is_offline_mode():
    run_migrations_offline(target_metadata)
else:
    run_migrations_online(target_metadata)
```

### CLI

Compose the `db` commands into your app's CLI:

```python
import click
from pyramid_sa.scripts.cli import db


@click.group()
@click.option("--config-uri", default="development.ini", show_default=True)
@click.pass_context
def cli(ctx, config_uri):
    ctx.ensure_object(dict)
    ctx.obj["config_uri"] = config_uri


cli.add_command(db)
```

Commands: `db init-alembic`, `db drop`, `db initialize` (`--drop-before`, `--run-thru-alembic`).

## Test Fixtures

Install `pyramid-sa-testing` and the pytest plugin is auto-discovered:

| Fixture | Scope | Description |
|---|---|---|
| `pyramid_sa_engine` | session | PostgreSQL engine via pytest-postgresql |
| `pyramid_sa_tm` | function | Doomed transaction manager — auto-rollback after each test |
| `pyramid_sa_dbsession` | function | DB session bound to the test transaction |
| `pyramid_sa_testapp` | function | WebTest TestApp with session injected |
| `pyramid_sa_app_request` | function | Real Pyramid request for service-layer testing |

Your `conftest.py` must provide an `app` fixture:

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

See the [Testing docs](docs/testing.md) for examples and advanced usage.

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run black .
```

## License

MIT
