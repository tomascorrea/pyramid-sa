# Architecture

## Overview

pyramid-sa is a Pyramid integration library that provides SQLAlchemy session management, a declarative base with audit columns, exception-to-HTTP mapping, JSON rendering, Alembic migration helpers, and CLI commands. A companion package (pyramid-sa-testing) ships a pytest plugin with database test fixtures.

## Components

- **session.py** — Engine creation, session factory, transaction-managed sessions via pyramid_tm + zope.sqlalchemy
- **meta.py** — `Base` (DeclarativeBase + AuditMixin), naming conventions, SQLAlchemy event listeners for audit fields
- **tween.py** — Exception tween translating `NoResultFound` → 404 and `IntegrityError` → 409
- **renderer.py** — JSON renderer with adapters for datetime, date, UUID
- **scripts/alembic.py** — Offline/online migration runner helpers
- **scripts/cli.py** — Click `db` command group (init-alembic, drop, initialize)
- **templates/alembic/** — Bundled alembic scaffold templates (alembic.ini, env.py, script.py.mako) copied into consuming apps by `db init-alembic`
- **pyramid_sa_testing** (separate package) — Pytest plugin providing engine, session, transaction, and WebTest fixtures

## Data Flow

1. Consuming app calls `config.include("pyramid_sa")`
2. `includeme` wires pyramid_tm, engine, session factory, tween, and renderer
3. Each request gets a `request.dbsession` (reified, transaction-managed)
4. Audit event listeners populate created_by/updated_by from the request
5. On exceptions, the tween maps SA errors to HTTP responses

## External Dependencies

pyramid, sqlalchemy, alembic, pyramid-tm, zope-sqlalchemy, click, camel-converter
