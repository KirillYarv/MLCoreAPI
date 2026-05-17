import logging
from typing import Any, Dict

from fastapi import FastAPI

from src.repository.AlsRepository import AlsRepository
from src.repository.ArlRepository import ArlRepository
from src.repository.DbInfoRepository import DbInfoRepository
from src.service.ALS import AlternatingLeastSquaresService
from src.service.ARL import AssociationRulesMiner
from src.service.DbConnectionService import DbConnectionService

logging.basicConfig(
    level=logging.INFO,
    filename="py_log.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

miner = AssociationRulesMiner(arl_repo=ArlRepository())
als_service = AlternatingLeastSquaresService(als_repo=AlsRepository())
db_connection_service = DbConnectionService(db_info_repo=DbInfoRepository())

app = FastAPI()


def get_response(status: str, data: Any, message: str = "OK") -> Dict[str, Any]:
    """Build a unified successful API response payload.

    Args:
        status: Status of the response.
        data: Business payload to return to client.
        message: Human-readable status message.

    Returns:
        Dict[str, Any]: Standard API response envelope.
    """
    return {"status": status, "message": message, "data": data}


@app.get("/")
def get_main():
    logging.info("Catch /")
    return get_response(
        status="success",
        data={
            "service": "Market Basket Analysis API",
            "routes": [
                "/api/pairs",
                "/api/pairs/{product_name}",
                "/api/als/recommendations/{user_id}",
                "/db/isconnect",
            ],
        },
        message="Service is running",
    )


@app.get("/api/pairs")
def get_pairs():
    logging.info("Catch /api/pairs")
    pairs = miner.get_pairs()
    return get_response(
        status="success",
        data=pairs,
        message="Association pairs fetched",
    )


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

    return get_response(
        status="success",
        data=list(set(filtered_data)),
        message=f"Related products fetched for '{product_name}'",
    )


@app.get("/api/als/recommendations/{user_id}")
def get_als_recommendations(user_id: str, top_k: int = 12):
    """Return ALS recommendations for a specific user.

    Args:
        user_id: Target customer identifier.
        top_k: Number of recommended products per user.

    Returns:
        Dict[str, Any]: Unified API response with one user's recommendations.
    """
    logging.info("Catch /api/als/recommendations/%s", user_id)
    try:
        recommendations = als_service.get_recommendations(top_k=top_k)
    except RuntimeError as error:
        return get_response(
            status="error",
            data={"reason": "gpu_unavailable"},
            message=str(error),
        )

    user_recommendations = next(
        (
            recommendation
            for recommendation in recommendations
            if str(recommendation.get("customer_id")) == str(user_id)
        ),
        None,
    )

    if user_recommendations is None:
        return get_response(
            status="error",
            data={"reason": "user_not_found", "user_id": user_id},
            message=f"Recommendations for user '{user_id}' were not found",
        )

    return get_response(
        status="success",
        data=user_recommendations,
        message=f"ALS recommendations fetched for user '{user_id}'",
    )


@app.get("/db/transactions_2018_09")
def get_transactions():
    logging.info("Catch /db/transactions")
    get_transactions = ArlRepository()
    transactions = get_transactions.get_transactions("_2018_09")

    return get_response(
        status="success",
        data=transactions,
        message="Transactions fetched from database partition _2018_09",
    )


@app.get("/db/isconnect")
def is_connect():
    logging.info("Catch /db/isconnect")
    db_status = db_connection_service.check_connection()

    if not db_status["is_connected"]:
        return get_response(
            status="error",
            data=db_status,
            message="Database is not connected",
        )
    return get_response(
        status="success",
        data=db_status,
        message="Database connectivity check completed",
    )
