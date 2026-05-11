# AGENTS.md

## Scope
- Single FastAPI service (no monorepo, no workspace tooling).
- Runtime entrypoint is `main.py` (`app = FastAPI()`), served as `main:app`.

## Run Commands (source of truth)
- Install deps: `pip install -r requirements.txt`
- Local dev server: `uvicorn main:app --reload` (README)
- Docker run command in image: `uvicorn main:app --host 0.0.0.0 --port 8001 --reload` (`Dockerfile`)

## API Reality Check
- Implemented endpoints in `main.py` are `/`, `/api/pairs`, `/api/pairs/{product_name}`, `/db/transactions_2018_09`.
- README still mentions `/pairs`; prefer code over docs when updating behavior.

## Data/Infra Dependencies
- `ArlRepository` connects directly to Postgres via `psycopg2` using hardcoded connection values in `src/repository/ArlRepository.py`.
- Host is `host.docker.internal`; API calls that touch repository methods require reachable external DB `Recommendation` with expected tables (`transactions_YYYY_MM`, `articles`).

## ARL Execution Flow
- `/api/pairs` calls `AssociationRulesMiner.get_pairs()` in `src/service/ARL.py`.
- First call computes rules across fixed postfix list (`_2018_09` ... `_2020_05`) via `multiprocessing.Pool(processes=10)` and caches results to `data*.json` in repo root.
- Subsequent calls reuse in-memory cache (`self._pairs_arl`) and/or `data_*.json` files if present.

## Repo Quirks That Affect Edits
- `.gitignore` ignores `*.json`, `*.csv`, `*.log`; generated cache files and logs are normally untracked.
- There is a duplicate repository file `src/repository/AlsRepository.py` that currently mirrors `ArlRepository.py`; production imports use `ArlRepository.py`.
- No test/lint/typecheck config is present (`pytest.ini`, `pyproject.toml`, `tox.ini`, `Makefile` absent); do not claim checks were run unless you add and run them explicitly.
