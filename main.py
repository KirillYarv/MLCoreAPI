import json
import logging
from pathlib import Path

from fastapi import FastAPI

from src.repository.ArlRepository import ArlRepository
from src.service.ARL import AssociationRulesMiner

logging.basicConfig(level=logging.INFO, filename="py_log.log")

miner = AssociationRulesMiner(arl_repo=ArlRepository())

app = FastAPI()


@app.get("/")
def get_main():
    logging.info("Catch /")
    return f"It`s root dir.         /api/ARLs - the ARL results data"


@app.get("/api/pairs")
def get_pairs():
    logging.info("Catch /api/pairs")

    return miner.get_pairs()


@app.get("/api/pairs/{product_name}")
def get_pairs_by_name(product_name: str):
    logging.info(f"Catch /api/pairs/{product_name}")

    data = miner.get_pairs()
    filtered_data = []
    for pair in data:
        if product_name in pair[0]:
            filtered_data.append(pair[1])
            continue
        if product_name in pair[1]:
            filtered_data.append(pair[0])

    return set(filtered_data)


@app.get("/db/transactions_2018_09")
def get_transactions():
    logging.info("Catch /db/transactions")
    get_transactions = ArlRepository()
    transactions = get_transactions.get_transactions("_2018_09")

    return f"Data from Database: - {transactions}"


# python3.10-venv
