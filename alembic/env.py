from alembic import context
from app.db.connection import build_engine
from app.models import Base


def run_migrations_online():
    engine = build_engine()
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=Base.metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError('Use online migrations with configured PostgreSQL credentials.')
else:
    run_migrations_online()
