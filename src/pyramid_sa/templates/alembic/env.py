from alembic import context

from pyramid_sa import Base
from pyramid_sa.scripts.alembic import run_migrations_offline, run_migrations_online

# Import your app's models here so Base.metadata is populated
# import myapp.models  # noqa: F401

target_metadata = Base.metadata

if context.is_offline_mode():
    run_migrations_offline(target_metadata)
else:
    run_migrations_online(target_metadata)
