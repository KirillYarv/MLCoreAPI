import logging
import os
from time import perf_counter
from typing import List, Tuple
from uuid import uuid4

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    filename="py_log.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class AlsRepository:
    """Repository for loading user-item interactions for ALS pipeline."""

    def __init__(
        self,
        database: str = os.getenv("DB_DATABASE") or "",
        user: str = os.getenv("DB_USERNAME") or "",
        password: str = os.getenv("DB_PASSWORD") or "",
        host: str = "host.docker.internal",
        port: int = int(os.getenv("DB_PORT") or 5432),
    ) -> None:
        """Initialize repository with PostgreSQL connection settings."""
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    def get_user_item_interactions(
        self, transactions_postfix: str
    ) -> List[Tuple[str, str, int]]:
        """Load aggregated implicit interactions from one transactions partition.

        Args:
            transactions_postfix: Suffix for partition table name, e.g. ``_2019_03``.

        Returns:
            List[Tuple[str, str, int]]: Sequence of
                ``(t_dat, customer_id, article_id)`` rows.
        """
        """Load aggregated implicit interactions from one transactions partition.

        Data is read in chunks to avoid large memory spikes while fetching.
        """
        query = f"""
            select
                t_dat,
                customer_id,
                article_id
            from transactions{transactions_postfix}
        """
        start = perf_counter()

        connection = psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )
        cursor_name = f"als_stream_{transactions_postfix.strip('_')}_{uuid4().hex[:8]}"

        try:
            with connection.cursor(name=cursor_name) as cursor:
                cursor.itersize = 20_000
                cursor.execute(query)

                result: List[Tuple[str, str, int]] = []
                while True:
                    rows = cursor.fetchmany(20_000)
                    if not rows:
                        break
                    result.extend(rows)

                end = perf_counter()
                logging.info(
                    "data transactions%s for als took %.3f seconds",
                    transactions_postfix,
                    end - start,
                )
                return result
        finally:
            connection.close()

    def get_count(self, table_name: str, column_name: str) -> int:
        """Return the total number of unique users in the transactions data."""
        query = f"""
            select
                count(distinct {column_name})
            from {table_name}
        """
        start = perf_counter()

        connection = psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )

        with connection.cursor() as cursor:
            cursor.execute(query)

            result = cursor.fetchone()[0]
            end = perf_counter()

            logging.info(f"get_count took {end - start} seconds for {table_name}")

            return result
