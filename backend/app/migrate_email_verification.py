
"""Safely add email-validation fields to SQLite or PostgreSQL."""
from sqlalchemy import inspect, text

from .database import Base, engine
from . import models  # Register database models with SQLAlchemy


def migrate() -> None:
    # Create any missing tables; existing tables and data are preserved.
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        raise RuntimeError("Users table not found.")

    existing_columns = {
        column["name"] for column in inspector.get_columns("users")
    }

    is_postgres = engine.dialect.name == "postgresql"

    additions = {
        "email_verified": "BOOLEAN NOT NULL DEFAULT TRUE",
        "email_verification_token_hash": "VARCHAR(64)",
        "email_verification_expires_at": (
            "TIMESTAMP WITH TIME ZONE" if is_postgres else "DATETIME"
        ),
    }

    with engine.begin() as connection:
        for name, column_type in additions.items():
            if name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE users ADD COLUMN {name} {column_type}")
                )
                print(f"Added: {name}")
            else:
                print(f"Already exists: {name}")

        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_users_email_verification_token_hash "
                "ON users (email_verification_token_hash)"
            )
        )

        total = connection.execute(
            text("SELECT COUNT(*) FROM users")
        ).scalar_one()

        verified = connection.execute(
            text("SELECT COUNT(*) FROM users WHERE email_verified = TRUE")
        ).scalar_one()


    print("Migration completed successfully.")
    print(f"Existing accounts: {total}")
    print(f"Verified accounts: {verified}")


if __name__ == "__main__":
    migrate()
