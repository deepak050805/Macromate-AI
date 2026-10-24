from alembic import context
from flask import current_app

config = context.config
db = current_app.extensions["migrate"].db


def run_migrations_online():
    with db.engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=db.metadata,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=db.engine.url.render_as_string(hide_password=False),
        target_metadata=db.metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
