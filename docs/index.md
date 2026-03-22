# pyramid-sa

Pyramid SQLAlchemy Integration — a reusable library that wires SQLAlchemy into any Pyramid application via `config.include("pyramid_sa")`.

## Features

- **Session management** — engine creation, transaction-managed sessions via pyramid_tm + zope.sqlalchemy, `request.dbsession` as a reified property
- **Declarative base** — `Base` with consistent naming conventions and utility methods (`as_dict`, `copy_with`) on every model
- **Audit trail** — opt-in `AuditMixin` that tracks `created_at`, `updated_at`, `created_by`, `updated_by`, `created_ip`, `updated_ip`
- **Soft delete** — opt-in `SoftDeleteMixin` with automatic query filtering, delete interception, partial unique indexes, and safe restore
- **Error mapping** — exception tween that translates `NoResultFound` to 404 and `IntegrityError` to 409, with customizable error bodies
- **JSON rendering** — adapters for `datetime`, `date`, and `UUID` out of the box
- **Alembic scaffold** — `db init-alembic` command copies pre-wired templates into your project
- **CLI commands** — `db drop` and `db initialize` for schema management
- **Test fixtures** — companion `pyramid-sa-testing` package with a pytest plugin for PostgreSQL-backed test sessions

## Quick install

```bash
pip install pyramid-sa
```

For test fixtures (dev only):

```bash
pip install pyramid-sa-testing
```

## Where to go next

- [Getting Started](getting-started.md) — installation, app factory, first model
- [Base & Models](models.md) — `Base`, `Model`, `ORMClass` utilities
- [Audit Trail](audit.md) — automatic created/updated tracking
- [Soft Delete](soft-delete.md) — soft-delete behavior, unique indexes, restore
- [Error Handling](error-handling.md) — exception tween and custom formatters
- [Database & Migrations](database.md) — Alembic scaffold and CLI commands
- [Testing](testing.md) — pytest fixtures for database testing
- [API Reference](api.md) — complete public API
