# Class AlternatingLeastSquaresService

## Поля класса
| Поле класса | Тип | Видимость | Описание |
|---|---|---|---|
| `als_repo` | `AlsRepository` | public | Репозиторий для чтения интеракций ALS из БД. |
| `cache_service` | `CacheServiceInterface` | public | Сервис кеширования для загрузки/сохранения JSON-данных. |
| `cache_dir` | `str` | public | Каталог/префикс для кеш-файлов ALS. |
| `cache_prefix` | `str` | public | Префикс кеша ALS (`data_for_als` по умолчанию). |
| `factors` | `int` | public | Число латентных факторов ALS. |
| `regularization` | `float` | public | Коэффициент L2-регуляризации. |
| `iterations` | `int` | public | Число итераций ALS. |
| `pool_processes` | `int` | public | Количество процессов на этап параллельной загрузки партиций. |
| `use_gpu` | `bool` | public | Флаг обязательного использования GPU backend. |
| `_cached_recommendations` | `list[dict[str, Any]]` | private | In-memory кеш рассчитанных рекомендаций. |
| `_cached_top_k` | `int \| None` | private | Значение `top_k`, соответствующее in-memory кешу рекомендаций. |
| `all_users_count` | `int` | public | Число уникальных пользователей (размерность матрицы по строкам). |
| `all_items_count` | `int` | public | Число уникальных товаров (размерность матрицы по столбцам). |

## Методы класса
| Принадлежность классу | Название | Аргументы | Видимость | Тип возвращаемого результата | Комментарии |
|---|---|---|---|---|---|
| `AlternatingLeastSquaresService` | `__init__` | `als_repo: AlsRepository`, `cache_service: CacheServiceInterface`, `cache_dir: str = ''`, `cache_prefix: str = 'data_for_als'`, `factors: int = 20`, `regularization: float = 0.01`, `iterations: int = 20`, `pool_processes: int = 3`, `use_gpu: bool = True` | public | `None` | Инициализирует параметры ALS, кеш и размеры матрицы на основе БД. |
| `AlternatingLeastSquaresService` | `get_recommendations` | `top_k: int = 12` | public | `list[dict[str, Any]]` | Возвращает рекомендации из кеша или запускает полный pipeline расчета. |
| `AlternatingLeastSquaresService` | `refresh_recommendations` | `top_k: int = 12` | public | `int` | Принудительно удаляет артефакты/кеш и пересчитывает модель и рекомендации заново; возвращает количество записей. |
| `AlternatingLeastSquaresService` | `_load_or_calculate` | `cache_paths: list[str]`, `top_k: int` | private | `list[dict[str, Any]]` | Загружает кеш рекомендаций или запускает пересчет. |
| `AlternatingLeastSquaresService` | `_artifact_paths` | `Нет` | private | `dict[str, Path]` | Возвращает пути к артефактам модели (model, mappings, user_items). |
| `AlternatingLeastSquaresService` | `_has_model_artifacts` | `Нет` | private | `bool` | Проверяет наличие полного набора артефактов модели в кеше. |
| `AlternatingLeastSquaresService` | `_save_model_artifacts` | `model: AlternatingLeastSquares`, `user_dict: dict[int, Any]`, `item_dict: dict[int, Any]`, `user_items_matrix: csr_matrix` | private | `None` | Сохраняет модель ALS, маппинги индексов и sparse-матрицу взаимодействий. |
| `AlternatingLeastSquaresService` | `_load_model_artifacts` | `Нет` | private | `tuple[AlternatingLeastSquares, dict[int, Any], dict[int, Any], csr_matrix]` | Загружает модель, маппинги и матрицу взаимодействий из артефактов. |
| `AlternatingLeastSquaresService` | `_generate_recommendations_from_artifacts` | `top_k: int` | private | `list[dict[str, Any]]` | Строит рекомендации из сохраненной модели без этапов БД и переобучения. |
| `AlternatingLeastSquaresService` | `_get_repository_data` | `transactions_postfix: str` | private | `None` | Загружает данные одной партиции из БД и сохраняет в кеш-файл партиции. |
| `AlternatingLeastSquaresService` | `_calculate_recommendations` | `top_k: int` | private | `list[dict[str, Any]]` | Параллельно подготавливает данные по партициям, собирает единый DataFrame, фильтрует данные, обучает ALS, сохраняет общий кеш. |
| `AlternatingLeastSquaresService` | `_build_interactions_dataframe_from_cache` | `table_postfixes: list[str]` | private | `pd.DataFrame` | Читает кеши партиций и собирает единый DataFrame интеракций (`t_dat`, `customer_id`, `article_id`). |
| `AlternatingLeastSquaresService` | `_filter_data` | `df: pd.DataFrame`, `user_count=10`, `item_count=20` | private | `pd.DataFrame` | Отбрасывает редких пользователей и товары ниже заданных порогов активности. |
| `AlternatingLeastSquaresService` | `_train_single_model` | `interactions_df: pd.DataFrame`, `top_k: int` | private | `list[dict[str, Any]]` | Кодирует пользователей/товары в индексы, обучает ALS, строит top-k рекомендации и возвращает их по пользователям. |
| `AlternatingLeastSquaresService` | `_build_recommendations` | `model: AlternatingLeastSquares`, `user_items_matrix: csr_matrix`, `user_dict: dict[int, Any]`, `item_dict: dict[int, Any]`, `top_k: int` | private | `list[dict[str, Any]]` | Формирует итоговые рекомендации для всех пользователей с историей взаимодействий. |
| `AlternatingLeastSquaresService` | `_evaluate_metrics` | `model: AlternatingLeastSquares`, `interactions_df: pd.DataFrame`, `k: int` | private | `tuple[float, float, float]` | Считает MAP@K, NDCG@K и Precision@K через временной split (`train/test`). |
| `AlternatingLeastSquaresService` | `_to_user_item_coo` | `df: pd.DataFrame` | private | `coo_matrix` | Преобразует DataFrame интеракций в sparse COO матрицу user-item. |
| `AlternatingLeastSquaresService` | `_train_test_split_over` | `clickstream_df: pd.DataFrame`, `test_quantile: float = 0.8` | private | `tuple[pd.DataFrame, pd.DataFrame]` | Делит данные на train/test по времени (`t_dat`) с фильтрацией cold-start в test. |
| `AlternatingLeastSquaresService` | `_validate_gpu_configuration` | `Нет` | private | `None` | Проверяет доступность CUDA backend в `implicit`, при отсутствии бросает `RuntimeError`. |
