from fastapi import HTTPException, status, APIRouter, Depends
from typing import Annotated
import re
import httpx
from datetime import datetime, timezone


from ..core.config import settings
from ..core.logging import configure_logging
from ..core.logging import LogLevel
from ..models.schemas import genderClassifierSchema as schema


router = APIRouter()
logger = configure_logging(level=LogLevel.DEBUG)


@router.get(
    "/classify",
    status_code=status.HTTP_200_OK,
    response_model=schema.GenderResponseSchema,
)
async def classify_name(
    query_params: Annotated[schema.GenderBaseSchema, Depends()],
):
    """
    Classify a name based on its gender.

    Args:
        query_params (GenderBaseSchema): The name to classify.

    Returns:
        GenderResponseSchema: A dictionary containing the classification result.

    Raises:
        HTTPException: If the name is missing or empty, or if the name contains non-alphabetic characters.
        HTTPException: If the external API returns an error.
    """
    name = query_params.name

    logger.info(f"Request received for name: {name}")

    try:
        if not name or name.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Missing or empty name"
            )

        if not re.match("^[a-zA-Z]+$", name):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Non-string name: Name must contain only alphabetic characters",
            )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{settings.GENDER_BASE_URL}/?name={name}")
                api_data = response.json()
            except Exception:
                raise HTTPException(status_code=502, detail="External API error")

        if api_data.get("gender") is None or api_data.get("count") == 0:
            return {
                "status": "error",
                "message": "No prediction available for the provided name",
            }

        prob = api_data.get("probability", 0)
        count = api_data.get("count", 0)
        is_confident = prob >= 0.7 and count >= 100

        return {
            "status": "success",
            "data": {
                "name": name,
                "gender": api_data.get("gender"),
                "probability": prob,
                "sample_size": count,
                "is_confident": is_confident,
                "processed_at": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            },
        }

    except HTTPException as he:
        logger.critical(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
