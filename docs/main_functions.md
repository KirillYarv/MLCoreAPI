# Функции `main.py`

| Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|
| `get_response` | `status: str`, `data: Any`, `message: str = 'OK'` | public | `dict[str, Any]` | Унифицированный формат ответа API (`status`, `message`, `data`). |
| `get_main` | `Нет` | public | `dict[str, Any]` | Endpoint `/`, возвращает статус сервиса и список основных маршрутов. |
| `get_pairs` | `Нет` | public | `dict[str, Any]` | Endpoint `/api/pairs`, сначала проверяет Redis-ключ `pairs_result`, при miss вызывает ARL и сохраняет итоговые уникальные пары в Redis. ARL внутри использует `JsonFileCacheService` для файловых партиционных кешей. |
| `get_pairs_by_id` | `product_id: str` | public | `dict[str, Any]` | Endpoint `/api/pairs/{product_id}`, сначала проверяет Redis-ключ `pairs_result_{product_id}`, при miss фильтрует ARL-пары и кеширует результат в Redis. |
| `get_als_recommendations` | `user_id: str`, `top_k: int = 12` | public | `dict[str, Any]` | Endpoint `/api/als/recommendations/{user_id}`, сначала проверяет Redis-ключ `als_{user_id}`, при miss получает ALS-рекомендации, фильтрует по пользователю и возвращает `user_not_found`/`gpu_unavailable` при ошибках. |
| `refresh_als_recommendations` | `top_k: int = 12` | public | `dict[str, Any]` | Endpoint `POST /api/als/refresh`, удаляет файловые артефакты ALS-модели и пересчитывает рекомендации. |
| `is_connect` | `Нет` | public | `dict[str, Any]` | Endpoint `/db/isconnect`, проверяет доступность БД через `DbConnectionService`. |
