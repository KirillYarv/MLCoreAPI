"""create transactions table

Revision ID: 44c286a5f49f
Revises: 40f44614cd76
Create Date: 2026-05-18 03:48:09.261146

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "44c286a5f49f"
down_revision: Union[str, Sequence[str], None] = "40f44614cd76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            CREATE TABLE IF NOT EXISTS transactions
            (
                t_dat date,
                customer_id VARCHAR(64) COLLATE pg_catalog."default",
                article_id integer,
                price double precision,
                sales_channel_id integer,
                CONSTRAINT article FOREIGN KEY (article_id)
                    REFERENCES articles (article_id) MATCH SIMPLE
                    ON UPDATE NO ACTION
                    ON DELETE NO ACTION,
                CONSTRAINT customer FOREIGN KEY (customer_id)
                    REFERENCES customers (customer_id) MATCH SIMPLE
                    ON UPDATE NO ACTION
                    ON DELETE NO ACTION
            ) partition by range (t_dat);
    """)
    )

    conn.execute(
        sa.text("""
        CREATE TABLE transactions_2018_09 PARTITION OF transactions
            FOR VALUES FROM ('2018-09-19') TO ('2019-03-15');

        CREATE TABLE transactions_2019_03 PARTITION OF transactions
            FOR VALUES FROM ('2019-03-15') TO ('2019-05-15');

        CREATE TABLE transactions_2019_05 PARTITION OF transactions
            FOR VALUES FROM ('2019-05-15') TO ('2019-09-25');

        CREATE TABLE transactions_2019_09 PARTITION OF transactions
            FOR VALUES FROM ('2019-09-25') TO ('2019-11-10');

        CREATE TABLE transactions_2019_11 PARTITION OF transactions
            FOR VALUES FROM ('2019-11-10') TO ('2020-03-22');

        CREATE TABLE transactions_2020_03 PARTITION OF transactions
            FOR VALUES FROM ('2020-03-22') TO ('2020-05-15');

        CREATE TABLE transactions_2020_05 PARTITION OF transactions
            FOR VALUES FROM ('2020-05-15') TO ('2020-09-23');
    """)
    )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS transactions"))
