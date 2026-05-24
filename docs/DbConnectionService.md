# Class DbConnectionService

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `db_info_repo` | `DbInfoRepository` | public | Репозиторий для проверки доступности БД. |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `DbConnectionService` | `__init__` | `db_info_repo: DbInfoRepository` | public | `None` | Инициализирует сервис зависимостью репозитория DB health-check. |
| `DbConnectionService` | `check_connection` | `Нет` | public | `dict` | Возвращает API-совместимый словарь с полями `is_connected` и `message`. |
