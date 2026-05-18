"""create customers table

Revision ID: b5a5a3c173f9
Revises:
Create Date: 2026-05-18 03:47:03.060426

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5a5a3c173f9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        CREATE TABLE customers (
            customer_id VARCHAR(64) PRIMARY KEY,
            fn FLOAT,
            active FLOAT,
            club_member_status VARCHAR(20),
            fashion_news_frequency VARCHAR(20),
            age INT,
            postal_code VARCHAR(64)
        );
    """)
    )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS customers"))
