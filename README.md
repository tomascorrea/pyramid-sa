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

Full documentation is available at [tomascorrea.github.io/pyramid-sa](https://tomascorrea.github.io/pyramid-sa/).

- [Getting Started](docs/getting-started.md) — installation, app factory wiring, what `include` sets up
- [Models](docs/models.md) — `Base` vs `Model`, `as_dict()`, `copy_with()`, mixins
- [Database & Migrations](docs/database.md) — Alembic scaffold, CLI commands, `env.py` setup
- [Audit Trail](docs/audit.md) — `AuditMixin` columns and automatic field population
- [Soft Delete](docs/soft-delete.md) — `SoftDeleteMixin`, filtering, unique indexes, restore
- [Error Handling](docs/error-handling.md) — exception tween, custom error formatters
- [Testing](docs/testing.md) — pytest fixtures, transaction isolation, `conftest.py` setup
- [API Reference](docs/api.md) — full public API by module

## Installation

```bash
pip install pyramid-sa
```

For test fixtures (dev only):

```bash
pip install pyramid-sa-testing
```

## Quick Start

Wire `pyramid-sa` into your Pyramid app factory:

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

See [Getting Started](docs/getting-started.md) for a full walkthrough of what `config.include("pyramid_sa")` sets up, model definitions, and next steps.

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run black .
```

## License

MIT
