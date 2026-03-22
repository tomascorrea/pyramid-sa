"""Tests for the db CLI commands."""

from pathlib import Path

import pytest
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from click.testing import CliRunner
from sqlalchemy import create_engine, inspect

from pyramid_sa.scripts.cli import db


@pytest.fixture()
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change into a temporary directory for each test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_init_alembic_creates_scaffold(work_dir: Path) -> None:
    """Happy path: all expected files and directories are created."""
    runner = CliRunner()
    result = runner.invoke(db, ["init-alembic"], catch_exceptions=False)

    assert result.exit_code == 0
    assert (work_dir / "alembic.ini").is_file()
    assert (work_dir / "alembic").is_dir()
    assert (work_dir / "alembic" / "env.py").is_file()
    assert (work_dir / "alembic" / "script.py.mako").is_file()
    assert (work_dir / "alembic" / "versions").is_dir()
    assert "created" in result.output
    assert "Alembic scaffold ready" in result.output


def test_init_alembic_env_py_contains_pyramid_sa_imports(work_dir: Path) -> None:
    """Generated env.py is pre-wired with pyramid-sa helpers."""
    runner = CliRunner()
    runner.invoke(db, ["init-alembic"], catch_exceptions=False)

    env_content = (work_dir / "alembic" / "env.py").read_text()
    assert "from pyramid_sa import Base" in env_content
    assert "from pyramid_sa.scripts.alembic import" in env_content
    assert "run_migrations_offline" in env_content
    assert "run_migrations_online" in env_content


def test_init_alembic_refuses_overwrite(work_dir: Path) -> None:
    """Aborts when alembic files already exist without --force."""
    runner = CliRunner()
    runner.invoke(db, ["init-alembic"], catch_exceptions=False)

    result = runner.invoke(db, ["init-alembic"])
    assert result.exit_code != 0
    assert "Already exists" in result.output


def test_init_alembic_force_overwrites(work_dir: Path) -> None:
    """--force allows overwriting existing files."""
    runner = CliRunner()
    runner.invoke(db, ["init-alembic"], catch_exceptions=False)

    ini_path = work_dir / "alembic.ini"
    ini_path.write_text("old content")

    result = runner.invoke(db, ["init-alembic", "--force"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "[alembic]" in ini_path.read_text()


def test_init_alembic_refuses_when_only_ini_exists(work_dir: Path) -> None:
    """Aborts when only alembic.ini exists."""
    (work_dir / "alembic.ini").write_text("old")

    runner = CliRunner()
    result = runner.invoke(db, ["init-alembic"])

    assert result.exit_code != 0
    assert "Already exists" in result.output


def test_init_alembic_refuses_when_only_dir_exists(work_dir: Path) -> None:
    """Aborts when only the alembic/ directory exists."""
    (work_dir / "alembic").mkdir()

    runner = CliRunner()
    result = runner.invoke(db, ["init-alembic"])

    assert result.exit_code != 0
    assert "Already exists" in result.output


def test_init_alembic_autogenerate_creates_migration(work_dir: Path) -> None:
    """Autogenerate detects the Item model and produces a valid migration."""
    runner = CliRunner()
    runner.invoke(db, ["init-alembic"], catch_exceptions=False)

    db_url = f"sqlite:///{work_dir}/test.db"
    cfg = AlembicConfig(str(work_dir / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", db_url)

    alembic_command.revision(cfg, autogenerate=True, message="init")

    versions_dir = work_dir / "alembic" / "versions"
    migration_files = [f for f in versions_dir.iterdir() if f.suffix == ".py"]
    assert len(migration_files) == 1

    migration_content = migration_files[0].read_text()
    assert "op.create_table('items'" in migration_content
    assert "'name'" in migration_content
    assert "'uuid'" in migration_content
    assert "'created_at'" in migration_content
    assert "'updated_at'" in migration_content
    assert "'created_by'" in migration_content

    alembic_command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    columns = {c["name"] for c in inspect(engine).get_columns("items")}
    engine.dispose()

    expected = {
        "id",
        "uuid",
        "name",
        "created_at",
        "updated_at",
        "created_ip",
        "updated_ip",
        "created_by",
        "updated_by",
    }
    assert expected == columns
