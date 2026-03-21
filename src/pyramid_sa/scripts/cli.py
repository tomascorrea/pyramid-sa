"""Database management CLI commands."""

import click
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from pyramid.paster import bootstrap, setup_logging

from pyramid_sa.meta import Base


def _get_engine(config_uri: str):
    """Bootstrap Pyramid and return the SQLAlchemy engine."""
    setup_logging(config_uri)
    env = bootstrap(config_uri)
    try:
        engine = env["request"].dbsession.get_bind()
    finally:
        env["closer"]()
    return engine


@click.group()
def db():
    """Database management commands."""


@db.command()
@click.pass_context
def drop(ctx: click.Context):
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
def initialize(ctx: click.Context, drop_before: bool, run_thru_alembic: bool):
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
