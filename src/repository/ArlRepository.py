import logging
import os
from time import perf_counter
from typing import List, Tuple
from uuid import uuid4

import psycopg2

logging.basicConfig(
    level=logging.DEBUG,
    filename="py_log.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class ArlRepository:
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

    def get_transactions(self, transactions_postfix: str, limit: int = -1):
        connection = psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )

        limit_str = ""
        if limit > 0:
            limit_str = f" limit {limit}"

        query: str = f"select \
                   	    t_dat, \
                        customer_id, \
                        string_agg(prod_name, '$$ ') \
                    from transactions{transactions_postfix} t \
                    left join articles a \
                        on a.article_id = t.article_id \
                    group by t_dat, customer_id{limit_str}"

        cursor_name = f"arl_stream_{transactions_postfix.strip('_')}_{uuid4()}"

        with connection.cursor(name=cursor_name) as cursor:
            cursor.itersize = 20_000
            start = perf_counter()

            cursor.execute(query)
            transactions: List[Tuple[str, str, str]] = []
            while True:
                rows = cursor.fetchmany(20_000)
                if not rows:
                    break
                transactions.extend(rows)

            prod_names = []

            for t in transactions:
                if len(t[2].split("$$ ")) > 1:
                    prod_names.append(t[2].split("$$ "))

            end = perf_counter()
            logging.info(
                f"get_transactions{transactions_postfix} took {end - start} seconds"
            )

            return prod_names, end - start
