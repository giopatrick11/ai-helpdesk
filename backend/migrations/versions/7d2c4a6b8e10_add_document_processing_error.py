"""add document processing error

Revision ID: 7d2c4a6b8e10
Revises: 3f4a9b7c2d10
Create Date: 2026-09-05 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d2c4a6b8e10"
down_revision: Union[str, Sequence[str], None] = "3f4a9b7c2d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("processing_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "processing_error")
