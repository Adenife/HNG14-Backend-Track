import asyncio
import httpx
import re
from uuid6 import uuid7
from datetime import datetime, timezone
from typing import Optional, Dict, Union, Annotated
from fastapi import APIRouter, HTTPException, status, Depends

from ..core.config import settings
from ..core.logging import configure_logging, LogLevel
from ..models.schemas import profileSchema as schema

router = APIRouter()
logger = configure_logging(level=LogLevel.DEBUG)

# In-memory storage
profiles_db: Dict[str, dict] = {}


def get_age_group(age: int) -> str:
    """
    Returns an age group based on the given age.

    Age groups are as follows:
    * 0-12: child
    * 13-19: teenager
    * 20-59: adult
    * 60+: senior

    :param age: The age to determine the age group for
    :return: The age group as a string
    """
    if 0 <= age <= 12:
        return "child"
    if 13 <= age <= 19:
        return "teenager"
    if 20 <= age <= 59:
        return "adult"
    return "senior"


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
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Define the concurrent tasks
        tasks = [
            client.get(f"{settings.GENDER_BASE_URL}?name={name}"),
            client.get(f"{settings.AGIFY_BASE_URL}?name={name}"),
            client.get(f"{settings.NATIONALIZE_BASE_URL}?name={name}"),
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
            # logger.critical(f"Upstream Connection Error: {str(e)}")
            logger.critical(f"DEBUG: Error type: {type(e).__name__}, Message: {str(e)}")
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
            "country_probability": top_country["probability"],
        }


@router.post(
    "/profiles",
    status_code=status.HTTP_201_CREATED,
    response_model=Union[schema.ProfileResponse, schema.ProfileAlreadyExistsResponse],
)
async def create_profile(
    query_params: Annotated[schema.ProfileCreateRequest, Depends()],
):
    """
    Creates a new profile in the database.

    Args:
    payload (schema.ProfileCreateRequest): The name of the profile to be created.

    Returns:
    Union[schema.ProfileResponse, schema.ProfileAlreadyExistsResponse]: A dictionary containing the created profile data or an error message if the profile already exists.

    Raises:
    HTTPException: If the request is invalid or if an internal error occurs.
    """
    name = query_params.name
    logger.info(f"Profile creation request for name: {name}")

    try:
        if not name or name.strip() == "":
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Missing or empty name"},
            )

        if not re.match("^[a-zA-Z]+$", name):
            raise HTTPException(
                status_code=422, detail={"status": "error", "message": "Invalid type"}
            )

        processed_name = name.strip().lower()

        # Idempotency
        for profile in profiles_db.values():
            if profile["name"] == processed_name:
                return {
                    "status": "success",
                    "message": "Profile already exists",
                    "data": profile,
                }

        ext_data = await fetch_external_data(processed_name)

        new_id = str(uuid7())
        new_profile = {
            "id": new_id,
            "name": processed_name,
            "created_at": datetime.now(timezone.utc),
            **ext_data,
        }

        profiles_db[new_id] = new_profile
        return {"status": "success", "data": new_profile}

    except HTTPException as he:
        logger.critical(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Internal Server Error"},
        )


@router.get("/profiles", response_model=schema.ProfileListResponse)
async def get_all_profiles(
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
):
    """
    Retrieves all profiles from the database.

    Args:
        gender (Optional[str]): The gender to filter by.
        country_id (Optional[str]): The country_id to filter by.
        age_group (Optional[str]): The age group to filter by.

    Returns:
        schema.ProfileListResponse: A dictionary containing the filtered profile data.

    Raises:
        HTTPException: If the request is invalid or if an internal error occurs.
    """
    results = list(profiles_db.values())

    if gender:
        results = [p for p in results if p["gender"].lower() == gender.lower()]
    if country_id:
        results = [p for p in results if p["country_id"].upper() == country_id.upper()]
    if age_group:
        results = [p for p in results if p["age_group"].lower() == age_group.lower()]

    return {"status": "success", "count": len(results), "data": results}


@router.get("/profiles/{id}", response_model=schema.ProfileResponse)
async def get_single_profile(id: str):
    """
    Retrieves a single profile from the database.

    Args:
        id (str): The unique identifier of the profile to retrieve.

    Returns:
        schema.ProfileResponse: A dictionary containing the retrieved profile data.

    Raises:
        HTTPException: If the profile is not found.
    """
    profile = profiles_db.get(id)
    if not profile:
        err_msg = {"status": "error", "message": "Profile not found"}
        logger.critical(f"HTTPException: {err_msg}")
        raise HTTPException(status_code=404, detail=err_msg)
    return {"status": "success", "data": profile}


@router.delete("/profiles/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(id: str):
    """
    Deletes a single profile from the database.

    Args:
        id (str): The unique identifier of the profile to delete.

    Returns:
        None

    Raises:
        HTTPException: If the profile is not found.
    """
    if id not in profiles_db:
        err_msg = {"status": "error", "message": "Profile not found"}
        logger.critical(f"HTTPException: {err_msg}")
        raise HTTPException(status_code=404, detail=err_msg)

    del profiles_db[id]
    return None


# async def fetch_external_data(name: str):
#     """
#     Fetches external data from the Genderize, Agify and Nationalize APIs based on a given name.

#     :param name: The name to fetch data for
#     :return: A dictionary containing the fetched data
#     :raises HTTPException: If any of the external API calls fail
#     """
#     async with httpx.AsyncClient() as client:
#         tasks = [
#             client.get(f"{settings.GENDER_BASE_URL}?name={name}"),
#             client.get(f"{settings.AGIFY_BASE_URL}?name={name}"),
#             client.get(f"{settings.NATIONALIZE_BASE_URL}?name={name}"),
#         ]

#         try:
#             results = await asyncio.gather(*tasks)
#             g_res_raw, a_res_raw, n_res_raw = results

#             # Upstream status checks
#             if g_res_raw.status_code != 200:
#                 raise HTTPException(
#                     status_code=502,
#                     detail={
#                         "status": "error",
#                         "message": "Genderize returned an invalid response",
#                     },
#                 )
#             if a_res_raw.status_code != 200:
#                 raise HTTPException(
#                     status_code=502,
#                     detail={
#                         "status": "error",
#                         "message": "Agify returned an invalid response",
#                     },
#                 )
#             if n_res_raw.status_code != 200:
#                 raise HTTPException(
#                     status_code=502,
#                     detail={
#                         "status": "error",
#                         "message": "Nationalize returned an invalid response",
#                     },
#                 )

#             g_res, a_res, n_res = g_res_raw.json(), a_res_raw.json(), n_res_raw.json()
#         except HTTPException as he:
#             raise he
#         except Exception as e:
#             logger.critical(f"Upstream Connection Error: {str(e)}")
#             raise HTTPException(
#                 status_code=502,
#                 detail={"status": "error", "message": "External API error"},
#             )

#         if g_res.get("gender") is None or g_res.get("count", 0) == 0:
#             raise HTTPException(
#                 status_code=502,
#                 detail={
#                     "status": "error",
#                     "message": "Genderize returned an invalid response",
#                 },
#             )

#         if a_res.get("age") is None:
#             raise HTTPException(
#                 status_code=502,
#                 detail={
#                     "status": "error",
#                     "message": "Agify returned an invalid response",
#                 },
#             )

#         if not n_res.get("country"):
#             raise HTTPException(
#                 status_code=502,
#                 detail={
#                     "status": "error",
#                     "message": "Nationalize returned an invalid response",
#                 },
#             )

#         top_country = max(n_res["country"], key=lambda x: x["probability"])

#         return {
#             "gender": g_res["gender"],
#             "gender_probability": g_res["probability"],
#             "sample_size": g_res["count"],
#             "age": a_res["age"],
#             "age_group": get_age_group(a_res["age"]),
#             "country_id": top_country["country_id"],
#             "country_probability": top_country["probability"],
#         }
