# pyramid-sa

Pyramid SQLAlchemy Integration — a reusable library that wires SQLAlchemy into any Pyramid application.

## Installation

```bash
pip install pyramid-sa
```

For test fixtures (dev only):

```bash
pip install pyramid-sa-testing
```

## Usage

In your Pyramid app factory:

```python
from pyramid.config import Configurator


def create_app(global_config=None, dbengine=None, **settings):
    config = Configurator(settings=settings)

    if dbengine is not None:
        config.registry["dbengine"] = dbengine

    config.include("pyramid_sa")

    # Import your models so SQLAlchemy knows about them
    import myapp.models  # noqa: F401
    from sqlalchemy.orm import configure_mappers
    configure_mappers()

    config.scan(".views")
    return config.make_wsgi_app()
```

### What `config.include("pyramid_sa")` does

1. Includes `pyramid_tm` (transaction management)
2. Creates the SQLAlchemy engine from `sqlalchemy.url` in settings (or uses `config.registry["dbengine"]` if pre-set)
3. Registers a session factory and adds `request.dbsession` as a reified property
4. Adds an exception tween (`NoResultFound` → 404, `IntegrityError` → 409)
5. Configures a JSON renderer with adapters for `datetime`, `date`, and `UUID`

### Base model

All your models should inherit from `pyramid_sa.Base`:

```python
import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from pyramid_sa import Base, generate_uuid


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid.UUID] = mapped_column(default=generate_uuid, unique=True)
    name: Mapped[str] = mapped_column(String(255))
```

`Base` includes an `AuditMixin` that adds `created_at`, `updated_at`, `created_by`, `updated_by`, `created_ip`, `updated_ip` columns automatically.

### Alembic

Scaffold alembic in your project with a single command:

```bash
db init-alembic
```

This creates `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, and `alembic/versions/` in the current directory, pre-wired with pyramid-sa helpers. Then edit `alembic/env.py` to import your models:

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

Migration versions live in your app (`alembic/versions/`), never in the library.

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

Commands:
- `db init-alembic` — scaffold alembic in the current directory (`--force` to overwrite)
- `db drop` — drop all database tables
- `db initialize` — create schema (`--drop-before`, `--run-thru-alembic` flags)

## Test Fixtures

Install `pyramid-sa-testing` and the pytest plugin is auto-discovered. It provides:

| Fixture | Scope | Description |
|---|---|---|
| `pyramid_sa_engine` | session | SQLite in-memory engine (override for PostgreSQL) |
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

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run black .
```

## License

MIT
