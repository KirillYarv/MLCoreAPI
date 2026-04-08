from fastapi import FastAPI

from src.repository.ArlRepository import ArlRepository
from src.service.ARL import AssociationRulesMiner

miner = AssociationRulesMiner(json_cache_path="data.json", arl_repo=ArlRepository())

app = FastAPI()


@app.get("/")
def get_main():
    return f"It`s root dir.         /api/ARLs - the ARL results data"


@app.get("/api/pairs")
def get_pairs():
    return miner.get_pairs()


@app.get("/db/transactions")
def get_transactions():
    get_transactions = ArlRepository()
    transactions = get_transactions.get_transactions(limit=10000)

    return f"Data from Database: - {transactions}"


# python3.10-venv
