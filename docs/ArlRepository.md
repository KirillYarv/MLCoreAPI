# Class ArlRepository

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `database` | `str` | public | Имя базы данных Postgres. |
| `user` | `str` | public | Имя пользователя БД. |
| `password` | `str` | public | Пароль пользователя БД. |
| `host` | `str` | public | Хост БД (по умолчанию `host.docker.internal`). |
| `port` | `int` | public | Порт подключения к БД. |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `ArlRepository` | `__init__` | `database: str`, `user: str`, `password: str`, `host: str`, `port: int` | public | `None` | Инициализирует параметры подключения к Postgres. |
| `ArlRepository` | `get_transactions` | `transactions_postfix: str`, `limit: int = -1` | public | `tuple[list[list[str]], float]` | Потоково читает транзакции из партиции, группирует товары по дате+клиенту, фильтрует транзакции длиной > 1, возвращает подготовленные транзакции и время SQL-этапа. |
