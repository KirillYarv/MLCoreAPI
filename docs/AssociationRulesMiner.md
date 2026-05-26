# Class AssociationRulesMiner

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `arl_repo` | `ArlRepository` | public | Репозиторий для чтения транзакций из БД. |
| `cache_service` | `CacheServiceInterface` | public | Сервис кеширования для загрузки/сохранения JSON-данных. |
| `_pairs_arl` | `list` | private | In-memory кеш вычисленных ассоциативных пар. |
| `_cache_dir` | `str` | private | Префикс директории для кеш-файлов. |
| `_cache_prefix` | `str` | private | Префикс имени кеш-файлов ARL. |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `AssociationRulesMiner` | `__init__` | `arl_repo: ArlRepository`, `cache_service: CacheServiceInterface`, `cache_dir: str = ''`, `cache_prefix: str = 'data_for_arl'` | public | `None` | Инициализирует зависимости и настройки кеша. |
| `AssociationRulesMiner` | `get_pairs` | `Нет` | public | `list` | Возвращает пары из памяти/кеша, при отсутствии запускает вычисление Apriori. |
| `AssociationRulesMiner` | `_get_unique_products` | `pairs: list[tuple[str, str, float, float, float]]` | private | `list[tuple[str, str, float, float, float]]` | Убирает дубли пар по товарам с учетом перестановки (`A-B` == `B-A`). |
| `AssociationRulesMiner` | `_load_or_calculate` | `data_paths: list[str]` | private | `list` | Оркестрирует загрузку кеша и fallback на пересчет. |
| `AssociationRulesMiner` | `_get_results` | `transactions_postfix: str` | private | `tuple[float, float]` | Для одной партиции: загружает транзакции, запускает Apriori, сохраняет пары с метриками (`support`, `confidence`, `lift`). |
| `AssociationRulesMiner` | `_calculate_rules` | `Нет` | private | `list` | Параллельно обрабатывает партиции через `Pool`, логирует время, возвращает объединенный кеш. |
| `AssociationRulesMiner` | `_log_pairs_metrics` | `pairs: list[tuple[str, str, float, float, float]]` | private | `None` | Логирует итоговые метрики рекомендаций: число пар, число уникальных товаров, средние `support`, `confidence`, `lift`. |
