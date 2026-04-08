import logging
import time

import psycopg2


class ArlRepository:
    def __init__(self) -> None:
        self.connection = psycopg2.connect(
            database="Recommendation",
            user="postgres",
            password="000000",
            host="localhost",
            port=5432,
        )

    def get_transactions(self, limit: int = -1):
        limit_str = ""
        if limit > 0:
            limit_str = f" limit {limit}"

        with self.connection.cursor() as cursor:
            start = time.time()

            cursor.execute(
                f"select \
               	    t_dat, \
                    customer_id, \
                    string_agg(prod_name, '$$ ') \
                from transactions_2018_09 t \
                left join articles a \
                    on a.article_id = t.article_id \
                group by t_dat, customer_id{limit_str}"
            )
            transactions = cursor.fetchall()

            prod_names = []

            for t in transactions:
                if len(t[2].split("$$ ")) > 1:
                    prod_names.append(t[2].split("$$ "))

            end = time.time()
            logging.info(f"get_transactions took {end - start} seconds")

            return prod_names
