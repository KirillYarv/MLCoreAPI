# AGENTS.md

## Scope
- Single FastAPI service (no monorepo, no workspace tooling).
- Runtime entrypoint is `main.py` (`app = FastAPI()`), served as `main:app`.

## Run Commands (source of truth)
- Local dev server: `uvicorn main:app --reload` (README)
- Docker run command in image: `uvicorn main:app --host 0.0.0.0 --port 8001 --reload` (`Dockerfile`)
- Docker Compose (primary): `docker compose up --build`
- Docker Compose in background: `docker compose up --build -d`
- Stop Compose stack: `docker compose down`
- GPU check in container: `docker compose run --rm python_app python3 -c "from implicit import gpu; print(gpu.HAS_CUDA)"`

## API Reality Check
- Implemented endpoints in `main.py`: `/`, `/api/pairs`, `/api/pairs/{product_name}`, `/api/als/recommendations/{user_id}`, `POST /api/als/refresh`, `/db/transactions_2018_09`, `/db/isconnect`.
- `/api/als/recommendations/{user_id}` computes/loads shared ALS recommendations (`top_k` query param), then filters by `user_id`; returns error payload with `reason=user_not_found` when missing.
- `/api/pairs` returns deduplicated unique pairs (`A-B` and `B-A` treated as one pair) and reports unique pair count in response message.

## Data/Infra Dependencies
- Repositories connect to Postgres via `psycopg2`; `AlsRepository` uses env vars (`DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD`, `DB_PORT`) and host `host.docker.internal` by default.
- API calls that touch repository methods require reachable external DB `Recommendation` with expected tables (`transactions_YYYY_MM`, `articles`, plus `customers` for ALS sizing logic).
- ALS GPU path requires NVIDIA driver compatible with CUDA 12.2 and Docker GPU runtime (`--gpus all`).

## ARL Execution Flow
- `/api/pairs` calls `AssociationRulesMiner.get_pairs()` in `src/service/ARL.py`.
- First call computes rules across fixed postfix list (`_2018_09` ... `_2020_05`) via `multiprocessing.Pool(processes=10)` and caches results to `data*.json` in repo root.
- Subsequent calls reuse in-memory cache (`self._pairs_arl`) and/or `data_*.json` files if present.

## ALS Execution Flow
- `/api/als/recommendations/{user_id}` calls `AlternatingLeastSquaresService.get_recommendations()` in `src/service/ALS.py`.
- Cache read/write in ALS and ARL is delegated to `JsonFileCacheService` (`src/service/CacheService.py`) via `CacheServiceInterface`.
- Data fetch stage is partition-based (`multiprocessing.Pool`) and produces one unified DataFrame in memory before training.
- Training/recommendation stage is single-process ALS (GPU-checked before run).
- Model artifacts are persisted and reused to skip DB/training on subsequent runs: `{cache_prefix}_model.npz`, `{cache_prefix}_mappings.json`, `{cache_prefix}_user_items.npz`.
- `POST /api/als/refresh` clears artifacts/results and forces full recomputation.

## Repo Quirks That Affect Edits
- `.gitignore` ignores `*.json`, `*.csv`, `*.log`; generated cache files and logs are normally untracked.
- `src/service/ALS.py` is actively evolving and may contain temporary debug logging/commented blocks; prefer preserving working runtime behavior when refactoring.
- No test/lint/typecheck config is present (`pytest.ini`, `pyproject.toml`, `tox.ini`, `Makefile` absent); do not claim checks were run unless you add and run them explicitly.
