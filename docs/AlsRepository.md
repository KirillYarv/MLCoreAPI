# Class AlsRepository

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `database` | `str` | public | Имя БД (из `DB_DATABASE`). |
| `user` | `str` | public | Пользователь БД (из `DB_USERNAME`). |
| `password` | `str` | public | Пароль БД (из `DB_PASSWORD`). |
| `host` | `str` | public | Хост БД (по умолчанию `host.docker.internal`). |
| `port` | `int` | public | Порт БД (из `DB_PORT`). |
| `dsn` | `str` | public | DSN-строка подключения (из `DATABASE_URL`). |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `AlsRepository` | `__init__` | `database: str`, `user: str`, `password: str`, `host: str`, `port: int`, `dsn: str` | public | `None` | Инициализирует параметры подключения к Postgres. |
| `AlsRepository` | `get_user_item_interactions` | `transactions_postfix: str` | public | `list[tuple[str, str, int]]` | Потоково читает одну партицию для ALS (`t_dat`, `customer_id`, `article_id`, `interaction_weight`) и возвращает данные чанками, собранными в список. |
| `AlsRepository` | `get_count` | `table_name: str`, `column_name: str` | public | `int` | Возвращает количество уникальных значений в колонке (используется для размера sparse-матрицы ALS). |
