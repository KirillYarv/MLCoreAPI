import glob
import json
import logging
from multiprocessing import Pool
from pathlib import Path
from time import perf_counter

from apyori import apriori

from ..repository.ArlRepository import ArlRepository

logging.basicConfig(
    level=logging.INFO,
    filename="py_log.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class AssociationRulesMiner:
    def __init__(
        self,
        arl_repo: ArlRepository,
        cache_dir: str = "",
        cache_prefix: str = "data_for_arl",
    ):
        self.arl_repo = arl_repo
        self._pairs_arl = []
        self._cache_dir = cache_dir
        self._cache_prefix = cache_prefix

    def get_pairs(self) -> list:
        """Публичный метод для получения ассоциативных пар."""
        data_paths = list(glob.glob(f"{self._cache_dir}{self._cache_prefix}*.json"))
        logging.info("Getting pairs from cache")
        if not self._pairs_arl:
            self._pairs_arl = self._load_or_calculate(data_paths)
        return self._pairs_arl

    def _load_or_calculate(self, data_paths: list[str]) -> list:
        # 1. Попытка загрузить из кеша

        logging.info(f"Loading cached data from {data_paths}")
        data = self._load_cached_data(data_paths)

        # 2. Расчет, если кеш пуст или отсутствует
        if not data:
            logging.info("Cache is empty or missing, calculating rules")
            data = self._calculate_rules()

        return data

    def _load_cached_data(self, data_paths: list[str]) -> list:
        data = []
        for path in data_paths:
            path = Path(path)
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data.extend(json.load(f))
                except json.JSONDecodeError:
                    pass
        return data

    def _get_results(self, transactions_postfix: str) -> tuple[float, float]:
        print(transactions_postfix)
        # получение транзакций из одной партицы
        transactions, time = self.arl_repo.get_transactions(transactions_postfix)

        # Запуск алгоритма Apriori
        start = perf_counter()
        rules = apriori(
            transactions=transactions,
            min_support=0.0008,
            min_confidence=0.09,
            min_lift=2.5,
            min_length=2,
            max_length=2,
        )
        end = perf_counter()

        apriori_time = end - start

        logging.info(
            f"Calculation apriori{transactions_postfix} time: {apriori_time} seconds\n"
        )

        # Извлекаем только списки товаров из объектов RelationRecord
        pairs = [list(rule.items) for rule in rules]

        # Сохраняем результат в кеш
        self._save_to_cache(pairs, f"{self._cache_prefix}{transactions_postfix}.json")

        return time, apriori_time

    def _calculate_rules(self) -> list:
        query_time = 0
        apriori_time = 0
        transactions_postfixes = [
            "_2018_09",
            "_2019_03",
            "_2019_05",
            "_2019_09",
            "_2019_11",
            "_2020_03",
            "_2020_05",
        ]
        with Pool(processes=10) as pool:
            start = perf_counter()

            r = pool.map(self._get_results, transactions_postfixes)
            for result in r:
                query_time += result[0]
                apriori_time += result[1]

            end = perf_counter()

        logging.info(f"sql_query took {query_time} seconds")
        logging.info(f"apriopi multythread took {apriori_time} seconds")
        logging.info(f"Total time: {end - start} seconds")

        data_paths = []
        for i in transactions_postfixes:
            data_paths.append(f"{self._cache_dir}{self._cache_prefix}{i}.json")

        return self._load_cached_data(data_paths)

    def _save_to_cache(self, data: list, path_str: str):
        with open(Path(path_str), "w", encoding="utf-8") as f:
            json.dump(data, f)
