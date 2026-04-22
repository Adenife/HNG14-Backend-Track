import httpx
import asyncio
from fastapi import HTTPException

from ..core.config import settings
from ..core.database import external_api_cache
from ..core.logging import configure_logging, LogLevel
from ..utils.helpers import get_age_group

logger = configure_logging(level=LogLevel.DEBUG)


async def fetch_external_data(name: str):
    """
    Concurrently fetches external data from Genderize, Agify, and Nationalize APIs.

    Args:
        name (str): The name to query the APIs with.

    Returns:
        A dictionary containing the processed data.

    Raises:
        HTTPException (502): If any of the external APIs return an invalid response.
        HTTPException (502): If any of the external APIs fail to respond (e.g. timeout, DNS failure).
    """
    # Cache hit — return immediately without hitting external APIs
    if name in external_api_cache:
        logger.info(f"Cache hit for name: {name}")
        return external_api_cache[name]

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Define the concurrent tasks
        tasks = [
            client.get(settings.GENDER_BASE_URL, params={"name": name}),
            client.get(settings.AGIFY_BASE_URL, params={"name": name}),
            client.get(settings.NATIONALIZE_BASE_URL, params={"name": name}),
        ]

        try:
            # Execute all calls in parallel
            results = await asyncio.gather(*tasks)
            api_names = ["Genderize", "Agify", "Nationalize"]

            # 1. Validate HTTP status codes first
            for i, res in enumerate(results):
                if res.status_code != 200:
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "status": "error",
                            "message": f"{api_names[i]} returned an invalid response",
                        },
                    )

            # 2. Parse JSON only after confirming 200 OK
            g_res, a_res, n_res = [r.json() for r in results]

        except HTTPException as he:
            # Re-raise our specific 502s
            raise he
        except Exception as e:
            # Catch timeouts or DNS failures
            logger.critical(f"Error type: {type(e).__name__}, Message: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail={"status": "error", "message": "External API error"},
            )

        # 3. Apply Stage 1 Domain Validation (The "Edge Cases")
        if g_res.get("gender") is None or g_res.get("count", 0) == 0:
            raise HTTPException(
                status_code=502,
                detail={
                    "status": "error",
                    "message": "Genderize returned an invalid response",
                },
            )

        if a_res.get("age") is None:
            raise HTTPException(
                status_code=502,
                detail={
                    "status": "error",
                    "message": "Agify returned an invalid response",
                },
            )

        if not n_res.get("country"):
            raise HTTPException(
                status_code=502,
                detail={
                    "status": "error",
                    "message": "Nationalize returned an invalid response",
                },
            )

        # 4. Final Logic: Pick the highest probability country
        top_country = max(n_res["country"], key=lambda x: x["probability"])

        return {
            "gender": g_res["gender"],
            "gender_probability": g_res["probability"],
            "sample_size": g_res["count"],
            "age": a_res["age"],
            "age_group": get_age_group(a_res["age"]),
            "country_id": top_country["country_id"],
            "country_name": top_country["country_name"],
            "country_probability": top_country["probability"],
        }
