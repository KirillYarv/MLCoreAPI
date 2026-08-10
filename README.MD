## Market Basket Analysis API
Market Basket Analysis API - это FastAPI-сервис, который сочетает в себе два типа рекомендаций:
- ARL (Apriori): поиск ассоциативных товарных пар 
- implicit ALS: персональные рекомендации для каждого пользователя на основе неявных факторов взаимодействия пользователей с товарами 

## API Endpoints
1) **Корневой endpoint**
- `GET /`
- Возвращает статус сервиса и список маршрутов

2) **ARL: все уникальные пары**
- `GET /api/pairs`
- Возвращает уникальные пары (`A-B` и `B-A` считаются одной парой)
- В `message` возвращается количество уникальных пар

3) **ARL: связанные товары по product_id**
- `GET /api/pairs/{product_id}`
- Возвращает связанные товары для переданного `product_id`

4) **ALS: рекомендации по пользователю**
- `GET /api/als/recommendations/{user_id}?top_k=12`
- `user_id` — id пользователя
- `top_k` — число рекомендаций (по умолчанию `12`)
- Ошибки:
  - `gpu_unavailable` — недоступна CUDA/GPU-конфигурация
  - `user_not_found` — пользователь отсутствует в рассчитанных рекомендациях

5) **ALS: принудительный refresh**
- `POST /api/als/refresh?top_k=12`
- Очищает артефакты/кеш и пересчитывает модель и рекомендации

## Запуск (Docker Compose)
### 1) Клонирование
```bash
git clone https://github.com/KirillYarv/MLCoreAPI.git
cd MLCoreAPI
```

### 2) Поднять сервисы
```bash
docker compose up --build
```

Фоновый режим:
```bash
docker compose up --build -d
```

Остановка сервисов:
```bash
docker compose down
```

### 3) Применить миграции
```bash
docker compose run --rm python_app alembic upgrade head
```
После запуска API доступно на `http://127.0.0.1:8001`.

### Требования для GPU (ALS)
- На хосте должен быть установлен NVIDIA Driver с поддержкой CUDA 12.2.
- Рекомендуемый минимум: драйвер ветки 535+ (например, 536.25 и выше).
- Установленный NVIDIA Container Toolkit

Проверка GPU внутри контейнера:

```bash
docker compose run --rm python_app python3 -c "from implicit import gpu; print(gpu.HAS_CUDA)"
```

## Инфраструктура в compose
- `python_app` — FastAPI backend
- `db` — Postgres 17
- `pgadmin` — UI для администрирования БД (`http://127.0.0.1:5050`)

Данные Postgres сохраняются в Docker volume `postgres_data`.

Важно: внутри контейнера приложение подключается к Postgres по хосту `host.docker.internal`.

## Документация API
- Swagger UI: `/docs`
