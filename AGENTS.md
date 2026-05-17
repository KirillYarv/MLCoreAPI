# AGENTS.md

## Scope
- Single FastAPI service (no monorepo, no workspace tooling).
- Runtime entrypoint is `main.py` (`app = FastAPI()`), served as `main:app`.

## Run Commands (source of truth)
- Install deps: `pip install -r requirements.txt`
- Local dev server: `uvicorn main:app --reload` (README)
- Docker run command in image: `uvicorn main:app --host 0.0.0.0 --port 8001 --reload` (`Dockerfile`)
- GPU run for ALS in Docker: `docker run --rm --gpus all -p 8001:8001 mlcoreapi`

## API Reality Check
- Implemented endpoints in `main.py`: `/`, `/api/pairs`, `/api/pairs/{product_name}`, `/api/als/recommendations/{user_id}`, `/db/transactions_2018_09`, `/db/isconnect`.
- `/api/als/recommendations/{user_id}` computes/loads shared ALS recommendations (`top_k` query param), then filters by `user_id`; returns error payload with `reason=user_not_found` when missing.

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
- Data fetch stage is partition-based and cache-driven (`data_{postfix}.json`); unified DataFrame is rebuilt from cache files before training.
- Training/recommendation stage is single-process ALS (GPU-checked before run), and outputs cache `als_recs_all.json`.

## Repo Quirks That Affect Edits
- `.gitignore` ignores `*.json`, `*.csv`, `*.log`; generated cache files and logs are normally untracked.
- `src/service/ALS.py` is actively evolving and may contain temporary debug logging/commented blocks; prefer preserving working runtime behavior when refactoring.
- No test/lint/typecheck config is present (`pytest.ini`, `pyproject.toml`, `tox.ini`, `Makefile` absent); do not claim checks were run unless you add and run them explicitly.
