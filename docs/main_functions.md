# Функции `main.py`

| Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|
| `get_response` | `status: str`, `data: Any`, `message: str = 'OK'` | public | `dict[str, Any]` | Унифицированный формат ответа API (`status`, `message`, `data`). |
| `get_main` | `Нет` | public | `dict[str, Any]` | Endpoint `/`, возвращает статус сервиса и список основных маршрутов. |
| `get_pairs` | `Нет` | public | `dict[str, Any]` | Endpoint `/api/pairs`, возвращает только уникальные пары; в `message` пишет их количество (`unique_pairs`). |
| `get_pairs_by_name` | `product_name: str` | public | `dict[str, Any]` | Endpoint `/api/pairs/{product_name}`, возвращает связанные товары для указанного продукта. |
| `get_als_recommendations` | `user_id: str`, `top_k: int = 12` | public | `dict[str, Any]` | Endpoint `/api/als/recommendations/{user_id}`, загружает общий ALS-кеш, фильтрует по пользователю, возвращает `user_not_found`/`gpu_unavailable` при ошибках. |
| `refresh_als_recommendations` | `top_k: int = 12` | public | `dict[str, Any]` | Endpoint `POST /api/als/refresh`, принудительно удаляет ALS-кеш/артефакты и пересчитывает рекомендации. |
| `get_transactions` | `Нет` | public | `dict[str, Any]` | Endpoint `/db/transactions_2018_09`, возвращает выборку транзакций из одной партиции БД. |
| `is_connect` | `Нет` | public | `dict[str, Any]` | Endpoint `/db/isconnect`, проверяет доступность БД через `DbConnectionService`. |
