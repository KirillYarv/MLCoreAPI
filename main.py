import logging
from enum import unique
from time import perf_counter
from typing import Any, Dict

from fastapi import FastAPI

from src.repository.AlsRepository import AlsRepository
from src.repository.ArlRepository import ArlRepository
from src.repository.DbInfoRepository import DbInfoRepository
from src.service.ALS import AlternatingLeastSquaresService
from src.service.ARL import AssociationRulesMiner
from src.service.CacheService import JsonFileCacheService
from src.service.DbConnectionService import DbConnectionService

logging.basicConfig(
    level=logging.DEBUG,
    filename="py_log.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

cache_service = JsonFileCacheService()
miner = AssociationRulesMiner(arl_repo=ArlRepository(), cache_service=cache_service)
als_service = AlternatingLeastSquaresService(
    als_repo=AlsRepository(),
    cache_service=cache_service,
)
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
                "/api/pairs/{product_id}",
                "/api/als/recommendations/{user_id}",
                "/api/als/refresh",
                "/db/isconnect",
            ],
        },
        message="Service is running",
    )


@app.get("/api/pairs")
def get_pairs():
    logging.info("Catch /api/pairs")
    start = perf_counter()
    pairs = miner.get_pairs()
    end = perf_counter()
    logging.info(f"get_pairs took {end - start} seconds")

    return get_response(
        status="success",
        data=pairs,
        message=f"Association pairs fetched: unique_pairs={len(pairs)}",
    )


@app.get("/api/pairs/{product_id}")
def get_pairs_by_id(product_id: str):
    logging.info(f"Catch /api/pairs/{product_id}")
    start = perf_counter()

    data = miner.get_pairs()
    filtered_data = []
    for pair in data:
        if product_id in pair[0]:
            filtered_data.append(pair[1])
            continue
        if product_id in pair[1]:
            filtered_data.append(pair[0])

    end = perf_counter()
    logging.info(f"get_pairs_by_id took {end - start} seconds")

    return get_response(
        status="success",
        data=list(set(filtered_data)),
        message=f"Related products fetched for '{product_id}'",
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
    start = perf_counter()

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
    end = perf_counter()
    logging.info(f"get_als_recommendations_by_name took {end - start} seconds")
    return get_response(
        status="success",
        data=user_recommendations,
        message=f"ALS recommendations fetched for user '{user_id}'",
    )


@app.post("/api/als/refresh")
def refresh_als_recommendations(top_k: int = 12):
    """Force refresh of ALS model artifacts and recommendations.

    Args:
        top_k: Number of recommended products per user.

    Returns:
        Dict[str, Any]: Unified API response with refreshed recommendation payload.
    """
    logging.info("Catch /api/als/refresh")
    start = perf_counter()
    try:
        recommendation_count = als_service.refresh_recommendations(top_k=top_k)
    except RuntimeError as error:
        return get_response(
            status="error",
            data={"reason": "gpu_unavailable"},
            message=str(error),
        )
    end = perf_counter()
    logging.info(f"refresh_als_recommendations took {end - start} seconds")
    return get_response(
        status="success",
        data={"users_count": recommendation_count, "top_k": top_k},
        message="ALS recommendations were refreshed",
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
    start = perf_counter()
    db_status = db_connection_service.check_connection()

    if not db_status["is_connected"]:
        return get_response(
            status="error",
            data=db_status,
            message="Database is not connected",
        )
    end = perf_counter()
    logging.info(f"is_connect took {end - start} seconds")
    return get_response(
        status="success",
        data=db_status,
        message="Database connectivity check completed",
    )
