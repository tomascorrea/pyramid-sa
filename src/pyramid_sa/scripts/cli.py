"""Database management CLI commands."""

import importlib.resources
from pathlib import Path

import click
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from pyramid.paster import bootstrap, setup_logging

from pyramid_sa.meta import Base

_TEMPLATE_PACKAGE = "pyramid_sa.templates.alembic"


def _get_engine(config_uri: str):
    """Bootstrap Pyramid and return the SQLAlchemy engine."""
    setup_logging(config_uri)
    env = bootstrap(config_uri)
    try:
        engine = env["request"].dbsession.get_bind()
    finally:
        env["closer"]()
    return engine


def _scaffold_alembic(target: Path, *, force: bool) -> list[str]:
    """Copy alembic templates into *target* and return the list of created paths."""
    alembic_dir = target / "alembic"
    ini_file = target / "alembic.ini"
    versions_dir = alembic_dir / "versions"

    if not force:
        conflicts = []
        if ini_file.exists():
            conflicts.append(str(ini_file))
        if alembic_dir.exists():
            conflicts.append(str(alembic_dir))
        if conflicts:
            raise FileExistsError(
                f"Already exists: {', '.join(conflicts)}. Use --force to overwrite."
            )

    alembic_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(exist_ok=True)

    created: list[str] = []
    templates = importlib.resources.files(_TEMPLATE_PACKAGE)

    for name in ("alembic.ini",):
        dest = target / name
        dest.write_text((templates / name).read_text())
        created.append(str(dest))

    for name in ("env.py", "script.py.mako"):
        dest = alembic_dir / name
        dest.write_text((templates / name).read_text())
        created.append(str(dest))

    created.append(str(versions_dir))
    return created


@click.group()
def db():
    """Database management commands."""


@db.command("init-alembic")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing alembic files.",
)
def init_alembic(force: bool) -> None:
    """Scaffold Alembic in the current directory, pre-wired for pyramid-sa."""
    target = Path.cwd()
    try:
        created = _scaffold_alembic(target, force=force)
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from None
    for path in created:
        click.echo(f"  created {path}")
    click.echo("Alembic scaffold ready. Edit alembic/env.py to import your models.")


@db.command()
@click.pass_context
def drop(ctx: click.Context) -> None:
    """Drop all database tables."""
    engine = _get_engine(ctx.obj["config_uri"])
    Base.metadata.drop_all(bind=engine)
    click.echo("All tables dropped.")


@db.command()
@click.option(
    "--drop-before",
    is_flag=True,
    default=False,
    help="Drop all tables before initializing.",
)
@click.option(
    "--run-thru-alembic",
    is_flag=True,
    default=False,
    help="Apply Alembic migrations instead of metadata.create_all().",
)
@click.pass_context
def initialize(ctx: click.Context, drop_before: bool, run_thru_alembic: bool) -> None:
    """Initialize the database schema."""
    engine = _get_engine(ctx.obj["config_uri"])

    if drop_before:
        Base.metadata.drop_all(bind=engine)
        click.echo("All tables dropped.")

    if run_thru_alembic:
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
        alembic_command.upgrade(alembic_cfg, "head")
        click.echo("Alembic migrations applied.")
    else:
        Base.metadata.create_all(bind=engine)
        click.echo("All tables created.")
