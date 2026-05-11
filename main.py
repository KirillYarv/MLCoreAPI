import logging
from typing import Any, Dict

from fastapi import FastAPI

from src.repository.ArlRepository import ArlRepository
from src.repository.DbInfoRepository import DbInfoRepository
from src.service.ARL import AssociationRulesMiner
from src.service.DbConnectionService import DbConnectionService

logging.basicConfig(level=logging.INFO, filename="py_log.log")

miner = AssociationRulesMiner(arl_repo=ArlRepository())
db_connection_service = DbConnectionService(db_info_repo=DbInfoRepository())

app = FastAPI()


def success_response(data: Any, message: str = "OK") -> Dict[str, Any]:
    """Build a unified successful API response payload.

    Args:
        data: Business payload to return to client.
        message: Human-readable status message.

    Returns:
        Dict[str, Any]: Standard API response envelope.
    """
    return {"status": "success", "message": message, "data": data}


@app.get("/")
def get_main():
    logging.info("Catch /")
    return success_response(
        data={
            "service": "Market Basket Analysis API",
            "routes": ["/api/pairs", "/api/pairs/{product_name}", "/db/isconnect"],
        },
        message="Service is running",
    )


@app.get("/api/pairs")
def get_pairs():
    logging.info("Catch /api/pairs")
    pairs = miner.get_pairs()
    return success_response(data=pairs, message="Association pairs fetched")


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

    return success_response(
        data=list(set(filtered_data)),
        message=f"Related products fetched for '{product_name}'",
    )


@app.get("/db/transactions_2018_09")
def get_transactions():
    logging.info("Catch /db/transactions")
    get_transactions = ArlRepository()
    transactions = get_transactions.get_transactions("_2018_09")

    return success_response(
        data=transactions,
        message="Transactions fetched from database partition _2018_09",
    )


@app.get("/db/isconnect")
def is_connect():
    logging.info("Catch /db/isconnect")
    db_status = db_connection_service.check_connection()
    return success_response(data=db_status, message="Database connectivity check completed")
