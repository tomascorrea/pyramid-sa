# Database & Migrations

pyramid-sa provides CLI commands for database management and bundled Alembic templates for migration scaffolding.

## CLI commands

The `db` command group is a Click group that you compose into your app's CLI:

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

### `db init-alembic`

Scaffold Alembic in the current directory, pre-wired for pyramid-sa:

```bash
db init-alembic
```

This creates:

- `alembic.ini` — Alembic configuration
- `alembic/env.py` — migration environment, pre-wired with pyramid-sa helpers
- `alembic/script.py.mako` — migration script template
- `alembic/versions/` — directory for migration files

The command refuses to overwrite existing files unless `--force` is passed:

```bash
db init-alembic --force
```

### `db drop`

Drop all database tables:

```bash
db --config-uri production.ini drop
```

Uses `Base.metadata.drop_all()` on the engine bootstrapped from the Pyramid config.

### `db initialize`

Create the database schema:

```bash
db initialize
```

Options:

| Flag | Description |
|---|---|
| `--drop-before` | Drop all tables before creating the schema |
| `--run-thru-alembic` | Apply Alembic migrations (`alembic upgrade head`) instead of `metadata.create_all()` |

```bash
db initialize --drop-before --run-thru-alembic
```

## Alembic setup

After running `db init-alembic`, edit `alembic/env.py` to import your models so Alembic autogenerate can see them:

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

The migration helpers (`run_migrations_offline`, `run_migrations_online`) handle engine creation from `alembic.ini` and context configuration.

Migration versions live in your app (`alembic/versions/`), never in the library. This keeps library upgrades safe — your migration history is fully under your control.
