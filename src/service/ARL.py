import glob
import json
import logging
from ast import Tuple
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
        """public method for getting pairs."""
        data_paths = list(glob.glob(f"{self._cache_dir}{self._cache_prefix}*.json"))
        logging.info("Getting pairs from cache")
        if not self._pairs_arl:
            self._pairs_arl = self._load_or_calculate(data_paths)

        self._log_pairs_metrics(self._pairs_arl)
        return self._pairs_arl

    def _get_unique_products(
        self, pairs: list[tuple[str, str, float, float, float]]
    ) -> list[tuple[str, str, float, float, float]]:
        """get unique products from pairs."""
        unique_pairs_map = {}

        for pair in pairs:
            if len(pair) != 5:
                continue
            pair_key = tuple(sorted([str(pair[0]), str(pair[1])]))
            if pair_key not in unique_pairs_map:
                unique_pairs_map[pair_key] = [
                    pair_key[0],
                    pair_key[1],
                    pair[2],
                    pair[3],
                    pair[4],
                ]
        unique_pairs = list(unique_pairs_map.values())

        return unique_pairs

    def _load_or_calculate(self, data_paths: list[str]) -> list:
        # 1. Попытка загрузить из кеша

        logging.info(f"Loading cached data from {data_paths}")
        data = self._load_cached_data(data_paths)

        # 2. Расчет, если кеш пуст или отсутствует
        if not data:
            logging.info("Cache is empty or missing, calculating rules")
            data = self._calculate_rules()

        data = self._get_unique_products(data)

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
            min_support=0.0004,
            min_confidence=0.02,
            min_lift=3,
            min_length=2,
            max_length=2,
        )
        end = perf_counter()

        apriori_time = end - start

        logging.info(
            f"Calculation apriori{transactions_postfix} time: {apriori_time} seconds\n"
        )

        rules_list = list(rules)

        # Извлекаем только списки товаров из объектов RelationRecord
        pairs: list[tuple[str, str, float, float, float]] = []
        for rule in rules_list:
            pairs.append(
                (
                    str(rule.items[0]),
                    str(rule.items[1]),
                    float(rule.support),
                    max(float(stat.confidence) for stat in rule.ordered_statistics),
                    max(float(stat.lift) for stat in rule.ordered_statistics),
                )
            )

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

    def _save_to_cache(
        self, data: list[tuple[str, str, float, float, float]], path_str: str
    ):
        with open(Path(path_str), "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _log_pairs_metrics(
        self, pairs: list[tuple[str, str, float, float, float]]
    ) -> None:
        """Log aggregate ARL recommendation metrics for final pair list.

        Args:
            pairs: Final ARL pairs list where each item is expected to contain
                two associated products.
        """
        total_pairs = len(pairs)
        unique_products = set()
        support_values: list[float] = []
        confidence_values: list[float] = []
        lift_values: list[float] = []

        for pair in pairs:
            if not isinstance(pair, (list, tuple)):
                continue
            if len(pair) >= 2:
                unique_products.add(str(pair[0]))
                unique_products.add(str(pair[1]))
            if len(pair) >= 5:
                try:
                    support_values.append(float(pair[2]))
                    confidence_values.append(float(pair[3]))
                    lift_values.append(float(pair[4]))
                except (TypeError, ValueError):
                    continue

        avg_support = (
            sum(support_values) / len(support_values) if support_values else 0.0
        )
        avg_confidence = (
            sum(confidence_values) / len(confidence_values)
            if confidence_values
            else 0.0
        )
        avg_lift = sum(lift_values) / len(lift_values) if lift_values else 0.0

        logging.info(
            "ARL pairs summary | total_pairs=%d | unique_products=%d | support=%f | confidence=%f | lift=%f",
            total_pairs,
            len(unique_products),
            avg_support,
            avg_confidence,
            avg_lift,
        )
