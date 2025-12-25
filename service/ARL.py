import json
import pandas as pd
from pathlib import Path
from apyori import apriori


class AssociationRulesMiner:
    def __init__(self, csv_path: str, json_cache_path: str):
        self.csv_path = Path(csv_path)
        self.json_cache_path = Path(json_cache_path)
        self._pairs_arl = []

    def get_pairs(self) -> list:
        """Публичный метод для получения ассоциативных пар."""
        if not self._pairs_arl:
            self._pairs_arl = self._load_or_calculate()
        return self._pairs_arl

    def _load_or_calculate(self) -> list:
        # 1. Попытка загрузить из кеша
        if self.json_cache_path.exists():
            try:
                with open(self.json_cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:
                        return data
            except json.JSONDecodeError:
                pass

        # 2. Расчет, если кеш пуст или отсутствует
        return self._calculate_rules()

    def _calculate_rules(self) -> list:
        if not self.csv_path.exists():
            return []

        # Загрузка и трансформация данных
        df = pd.read_csv(self.csv_path, delimiter=';')

        # Убираем колонку 'number', оставляем только товары (столбцы с 1 и 0)
        item_columns = [col for col in df.columns if col != 'number']

        # Оптимизированный сбор транзакций (быстрее чем iterrows)
        transactions = df[item_columns].apply(
            lambda x: x.index[x == 1].tolist(), axis=1
        ).tolist()

        # Запуск алгоритма Apriori
        # Исправлено: min_confidence (была опечатка)
        rules = apriori(
            transactions=transactions,
            min_support=0.0029,
            min_confidence=0.10,
            min_lift=3,
            min_length=3,
            max_length=3
        )

        # Извлекаем только списки товаров из объектов RelationRecord
        pairs = [list(rule.items) for rule in rules]

        # Сохраняем результат в кеш
        self._save_to_cache(pairs)

        return pairs

    def _save_to_cache(self, data: list):
        with open(self.json_cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
