"""create articles table

Revision ID: 40f44614cd76
Revises: b5a5a3c173f9
Create Date: 2026-05-18 03:47:43.696631

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "40f44614cd76"
down_revision: Union[str, Sequence[str], None] = "b5a5a3c173f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            CREATE TABLE articles (
                article_id integer PRIMARY KEY,
                product_code VARCHAR(20),
                prod_name VARCHAR(255),
                product_type_no integer,
                product_type_name VARCHAR(100),
                product_group_name VARCHAR(100),
                graphical_appearance_no integer,
                graphical_appearance_name VARCHAR(100),
                colour_group_code VARCHAR(10),
                colour_group_name VARCHAR(50),
                perceived_colour_value_id integer,
                perceived_colour_value_name VARCHAR(50),
                perceived_colour_master_id integer,
                perceived_colour_master_name VARCHAR(50),
                department_no integer,
                department_name VARCHAR(100),
                index_code CHAR(1),
                index_name VARCHAR(100),
                index_group_no integer,
                index_group_name VARCHAR(100),
                section_no integer,
                section_name VARCHAR(100),
                garment_group_no integer,
                garment_group_name VARCHAR(100),
                detail_desc TEXT
            );
    """)
    )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS articles"))
