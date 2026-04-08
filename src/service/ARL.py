import json
from pathlib import Path

from apyori import apriori

from ..repository.ArlRepository import ArlRepository


class AssociationRulesMiner:
    def __init__(self, json_cache_path: str, arl_repo: ArlRepository):
        self.arl_repo = arl_repo
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
                with open(self.json_cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data:
                        return data
            except json.JSONDecodeError:
                pass

        # 2. Расчет, если кеш пуст или отсутствует
        return self._calculate_rules()

    def _calculate_rules(self) -> list:
        transactions = self.arl_repo.get_transactions(limit=-1)
        # Запуск алгоритма Apriori
        rules = apriori(
            transactions=transactions,
            min_support=0.0005,
            min_confidence=0.09,
            min_lift=2.5,
            min_length=2,
            max_length=2,
        )

        # Извлекаем только списки товаров из объектов RelationRecord
        pairs = [list(rule.items) for rule in rules]

        # Сохраняем результат в кеш
        self._save_to_cache(pairs)

        return pairs

    def _save_to_cache(self, data: list):
        with open(self.json_cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
