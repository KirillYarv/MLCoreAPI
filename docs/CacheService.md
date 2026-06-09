# Class CacheServiceInterface

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `Нет` | `-` | `-` | Интерфейс не хранит состояние. |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `CacheServiceInterface` | `load_many` | `cache_paths: list[str]` | public | `list[Any]` | Контракт загрузки и объединения данных из нескольких кеш-ключей/файлов. |
| `CacheServiceInterface` | `save` | `data: Any`, `cache_name: str`, `time_to_expire_s: int = 0` | public | `None` | Контракт сохранения JSON-совместимых данных в кеш. |
| `CacheServiceInterface` | `load` | `cache_name: str` | public | `Any` | Контракт загрузки одного значения из кеша. |

# Class JsonFileCacheService

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `Нет` | `-` | `-` | Реализация не хранит состояние между вызовами. |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `JsonFileCacheService` | `load_many` | `cache_paths: list[str]` | public | `list[Any]` | Читает все существующие файлы из списка, объединяет данные; `list`-payload расширяет, одиночный объект добавляет как элемент. |
| `JsonFileCacheService` | `save` | `data: list[Any]`, `cache_name: str`, `time_to_expire_s: int = 0` | public | `None` | Сохраняет данные в JSON-файл (`default=str`); TTL игнорируется файловой реализацией. |
| `JsonFileCacheService` | `load` | `cache_name: str` | public | `Any` | Не реализован для одиночного чтения; используется `load_many`. |

# Class RedisCacheService

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `redis_service` | `redis.Redis` | public | Клиент Redis для runtime-кеша API. |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `RedisCacheService` | `__init__` | `host: str = os.getenv('DEFAULT_URI') or ''`, `port: int = int(os.getenv('REDIS_PORT') or 6379)` | public | `None` | Инициализирует Redis-клиент с DB `0`. |
| `RedisCacheService` | `load_many` | `cache_paths: list[str]` | public | `list[Any]` | Загружает JSON-значения из Redis по списку ключей и добавляет каждое значение как отдельный элемент. |
| `RedisCacheService` | `save` | `data: list[Any]`, `cache_name: str`, `time_to_expire_s: int = 180` | public | `None` | Сохраняет JSON-значение в Redis с TTL по умолчанию 180 секунд. |
| `RedisCacheService` | `load` | `cache_name: str` | public | `Any` | Возвращает сырое значение Redis по ключу или `None`. |
