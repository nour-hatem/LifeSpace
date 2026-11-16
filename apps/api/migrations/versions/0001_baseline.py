"""Empty baseline for the LifeSpace schema.

Revision ID: 0001
Revises:
Create Date: 2026-11-16 02:30:55.526436

This baseline contains no schema changes. It exists so every later revision
has a stable parent.
"""

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the empty baseline: no schema changes yet."""
    pass


def downgrade() -> None:
    """Revert the empty baseline: no schema changes yet."""
    pass
