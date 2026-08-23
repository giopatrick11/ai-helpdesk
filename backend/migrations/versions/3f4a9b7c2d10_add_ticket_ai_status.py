"""add ticket ai status

Revision ID: 3f4a9b7c2d10
Revises: eb17239a8f2a
Create Date: 2026-08-23 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f4a9b7c2d10"
down_revision: Union[str, Sequence[str], None] = "eb17239a8f2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tickets",
        sa.Column(
            "ai_status",
            sa.String(length=50),
            server_default="processing",
            nullable=False,
        ),
    )
    op.add_column(
        "tickets",
        sa.Column("ai_error", sa.Text(), nullable=True),
    )

    op.execute(
        """
        UPDATE tickets
        SET ai_status = CASE
            WHEN category IS NOT NULL AND ai_summary IS NOT NULL
                THEN 'completed'
            ELSE 'failed'
        END,
        ai_error = CASE
            WHEN category IS NOT NULL AND ai_summary IS NOT NULL
                THEN NULL
            ELSE 'Ticket AI analysis status was unknown before migration.'
        END
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tickets", "ai_error")
    op.drop_column("tickets", "ai_status")
