# Architectural Decisions

Record of key technical and architectural decisions for this project.

## Template

Use this format when adding a new decision:

### YYYY-MM-DD — Decision Title

**Status**: Accepted | Superseded | Deprecated

**Context**: What is the issue or situation that motivates this decision?

**Decision**: What is the change that we're proposing or have agreed to?

**Consequences**: What are the trade-offs and results of this decision?

---

## Decisions

### 2026-03-21 — Initial project setup

**Status**: Accepted

**Context**: Starting a reusable Pyramid+SQLAlchemy integration library extracted from production patterns.

**Decision**: Using uv with src layout, ruff + black for linting/formatting, pytest for testing, and MkDocs for documentation.

**Consequences**: Consistent project structure that follows Python best practices. All team members and AI assistants can rely on the same conventions.

### 2026-03-21 — Alembic scaffold owned by consuming app

**Status**: Accepted

**Context**: Alembic migration versions must live in the consuming application, not in the library. The library provides migration runner helpers but had no way to bootstrap the alembic directory structure.

**Decision**: Bundle alembic template files under `pyramid_sa/templates/alembic/` and provide a `db init-alembic` CLI command that copies them into the consuming app's working directory. Templates are read via `importlib.resources`. The command refuses to overwrite unless `--force` is passed.

**Consequences**: Consuming apps get a one-command setup for alembic, pre-wired with pyramid-sa helpers. Migration versions stay in the app, never in the library. The templates directory uses a distinct name (`templates/`) to avoid confusion with actual alembic migration data.

### 2026-03-21 — Separate testing package

**Status**: Accepted

**Context**: Test fixtures (pytest plugin) depend on webtest and transaction, which should not ship in production.

**Decision**: Split into two packages in one repo: `pyramid-sa` (main library) and `pyramid-sa-testing` (pytest plugin). The testing package has its own pyproject.toml under `testing/`.

**Consequences**: Production installs carry zero test code or test dependencies. Consuming apps add `pyramid-sa-testing` to dev dependencies only.
