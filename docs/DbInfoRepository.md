# Class DbInfoRepository

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `database` | `str` | public | Имя целевой БД. |
| `user` | `str` | public | Пользователь БД. |
| `password` | `str` | public | Пароль БД. |
| `host` | `str` | public | Хост БД. |
| `port` | `int` | public | Порт БД. |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `DbInfoRepository` | `__init__` | `database: str`, `user: str`, `password: str`, `host: str`, `port: int` | public | `None` | Сохраняет параметры подключения к БД для health-check сценария. |
| `DbInfoRepository` | `is_connected` | `Нет` | public | `tuple[bool, str]` | Проверяет соединение с Postgres и возвращает флаг доступности и сообщение/текст ошибки. |
