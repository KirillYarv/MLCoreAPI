import logging
import os
from time import perf_counter

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    filename="py_log.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class ArlRepository:
    def get_transactions(self, transactions_postfix: str, limit: int = -1):
        self.connection = psycopg2.connect(
            database=os.getenv("DB_DATABASE") or "",
            user=os.getenv("DB_USERNAME") or "",
            password=os.getenv("DB_PASSWORD") or "",
            host="host.docker.internal",
            port=int(os.getenv("DB_PORT") or 5432),
        )

        limit_str = ""
        if limit > 0:
            limit_str = f" limit {limit}"

        with self.connection.cursor() as cursor:
            start = perf_counter()

            cursor.execute(
                f"select \
               	    t_dat, \
                    customer_id, \
                    string_agg(prod_name, '$$ ') \
                from transactions{transactions_postfix} t \
                left join articles a \
                    on a.article_id = t.article_id \
                group by t_dat, customer_id{limit_str}"
            )
            transactions = cursor.fetchall()

            prod_names = []

            for t in transactions:
                if len(t[2].split("$$ ")) > 1:
                    prod_names.append(t[2].split("$$ "))

            end = perf_counter()
            logging.info(
                f"get_transactions{transactions_postfix} took {end - start} seconds"
            )

            return prod_names, end - start
