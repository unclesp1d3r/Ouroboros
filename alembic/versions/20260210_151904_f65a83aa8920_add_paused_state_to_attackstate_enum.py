"""add_paused_state_to_attackstate_enum

Revision ID: f65a83aa8920
Revises: 1587d62b626a
Create Date: 2026-02-10 15:19:04.295213+00:00

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f65a83aa8920"
down_revision: str | None = "1587d62b626a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add 'PAUSED' value to attackstate enum.

    PostgreSQL enums are immutable, so we use ALTER TYPE to add a new value.
    The 'PAUSED' state is inserted after 'RUNNING' to maintain logical ordering.
    Note: The database stores enum names (PAUSED) not values (paused).
    """
    op.execute("ALTER TYPE attackstate ADD VALUE IF NOT EXISTS 'PAUSED' AFTER 'RUNNING'")


def downgrade() -> None:
    """Remove 'PAUSED' value from attackstate enum.

    Note: PostgreSQL does not support removing enum values directly.
    This downgrade recreates the enum without the 'PAUSED' value, which requires:
    1. Creating a new enum type without 'PAUSED'
    2. Updating the column to use the new type
    3. Dropping the old type
    4. Renaming the new type

    WARNING: This will fail if any rows contain 'PAUSED' as their state value.
    Those rows must be updated to a different state before downgrading.
    """
    # Create new enum without 'PAUSED'
    op.execute("""
        CREATE TYPE attackstate_new AS ENUM (
            'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'ABANDONED'
        )
    """)

    # Update column to use new type (this will fail if any rows have 'PAUSED' state)
    op.execute("""
        ALTER TABLE attacks
        ALTER COLUMN state TYPE attackstate_new
        USING state::text::attackstate_new
    """)

    # Drop old enum and rename new one
    op.execute("DROP TYPE attackstate")
    op.execute("ALTER TYPE attackstate_new RENAME TO attackstate")
