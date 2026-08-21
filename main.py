import json
import logging
from time import perf_counter
from typing import Any, Dict

from fastapi import FastAPI

from src.repository.AlsRepository import AlsRepository
from src.repository.ArlRepository import ArlRepository
from src.service.ALS import AlternatingLeastSquaresService
from src.service.ARL import AssociationRulesMiner
from src.service.CacheService import JsonFileCacheService, RedisCacheService

logging.basicConfig(
    level=logging.DEBUG,
    filename="py_log.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

cache_service = RedisCacheService()
json_cache_service = JsonFileCacheService()

miner = AssociationRulesMiner(
    arl_repo=ArlRepository(), cache_service=json_cache_service
)
als_service = AlternatingLeastSquaresService(
    als_repo=AlsRepository(),
)

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
    user_cache = cache_service.load("pairs_result")
    if user_cache:
        pairs = json.loads(user_cache)

        return get_response(
            status="success",
            data=pairs,
            message=f"Association pairs fetched: unique_pairs={len(pairs)}",
        )
    pairs = miner.get_pairs()

    cache_service.save(pairs, "pairs_result")

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
    user_cache = cache_service.load(f"pairs_result_{product_id}")
    if user_cache:
        pairs = json.loads(user_cache)
        return get_response(
            status="success",
            data=pairs,
            message=f"Association pairs fetched: unique_pairs={len(pairs)}",
        )

    data = miner.get_pairs()
    filtered_data: list[str] = []
    for pair in data:
        if product_id in pair[0]:
            filtered_data.append(pair[1])
            continue
        if product_id in pair[1]:
            filtered_data.append(pair[0])

    filtered_data = list(set(filtered_data))
    cache_service.save(filtered_data, f"pairs_result_{product_id}")

    end = perf_counter()
    logging.info(f"get_pairs_by_id took {end - start} seconds")

    return get_response(
        status="success",
        data=filtered_data,
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

    user_cache = cache_service.load(f"als_{user_id}")
    if user_cache:
        return get_response(
            status="success",
            data=json.loads(user_cache),
            message=f"ALS recommendations fetched for user '{user_id}'",
        )

    try:
        recommendations = als_service.get_recommendations(top_k=top_k)
    except RuntimeError as error:
        return get_response(
            status="error",
            data={"reason": "gpu_unavailable"},
            message=str(error),
        )

    user_recommendations: list[Dict[str, Any]] = []
    for recommendation in recommendations:
        if str(recommendation.get("customer_id")) == str(user_id):
            user_recommendations.append(recommendation)

    if not user_recommendations:
        return get_response(
            status="error",
            data={"reason": "user_not_found", "user_id": user_id},
            message=f"Recommendations for user '{user_id}' were not found",
        )

    cache_service.save(user_recommendations, f"als_{user_id}")

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
