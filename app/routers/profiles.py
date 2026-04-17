import re
from uuid6 import uuid7
from datetime import datetime, timezone
from typing import Optional, Dict, Union
from fastapi import APIRouter, HTTPException, status, Response

from ..core.logging import configure_logging, LogLevel
from ..core.database import profiles_db, profiles_name_index
from ..models.schemas import profileSchema as schema
from ..services.external_api import fetch_external_data

router = APIRouter()
logger = configure_logging(level=LogLevel.DEBUG)


@router.post(
    "/profiles",
    status_code=status.HTTP_201_CREATED,
    response_model=Union[schema.ProfileResponse, schema.ProfileAlreadyExistsResponse],
)
async def create_profile(payload: schema.ProfileCreateRequest, response: Response):
    """
    Creates a new profile in the database.

    Args:
    payload (schema.ProfileCreateRequest): The name of the profile to be created.

    Returns:
    Union[schema.ProfileResponse, schema.ProfileAlreadyExistsResponse]: A dictionary containing the created profile data or an error message if the profile already exists.

    Raises:
    HTTPException: If the request is invalid or if an internal error occurs.
    """
    name = str(payload.name).strip()
    logger.info(f"Profile creation request for name: {name}")

    try:
        if not name or name == "":
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Missing or empty name"},
            )

        if not re.match("^[a-zA-Z]+$", name):
            raise HTTPException(
                status_code=422, detail={"status": "error", "message": "Invalid type"}
            )

        processed_name = name.lower()

        # Idempotency — O(1) lookup via name index
        if processed_name in profiles_name_index:
            existing_id = profiles_name_index[processed_name]
            response.status_code = status.HTTP_200_OK
            return {
                "status": "success",
                "message": "Profile already exists",
                "data": profiles_db[existing_id],
            }

        ext_data = await fetch_external_data(processed_name)

        new_id = str(uuid7())
        new_profile = {
            "id": new_id,
            "name": processed_name,
            "created_at": datetime.now(timezone.utc),
            **ext_data,
        }

        # Keep both structures in sync
        profiles_db[new_id] = new_profile
        profiles_name_index[processed_name] = new_id
        return {"status": "success", "data": new_profile}

    except HTTPException as he:
        logger.warning(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Internal Server Error"},
        )


@router.get(
    "/profiles",
    response_model=schema.ProfileListResponse,
    status_code=status.HTTP_200_OK,
)
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
    try:
        results = list(profiles_db.values())

        if gender:
            results = [p for p in results if p["gender"].lower() == gender.lower()]
        if country_id:
            results = [
                p for p in results if p["country_id"].upper() == country_id.upper()
            ]
        if age_group:
            results = [
                p for p in results if p["age_group"].lower() == age_group.lower()
            ]

        return {"status": "success", "count": len(results), "data": results}

    except HTTPException as he:
        logger.warning(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Internal Server Error"},
        )


@router.get(
    "/profiles/{id}",
    response_model=schema.ProfileResponse,
    status_code=status.HTTP_200_OK,
)
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
    try:
        profile = profiles_db.get(id)
        if not profile:
            err_msg = {"status": "error", "message": "Profile not found"}
            logger.warning(f"HTTPException: {err_msg}")
            raise HTTPException(status_code=404, detail=err_msg)
        return {"status": "success", "data": profile}

    except HTTPException as he:
        logger.warning(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Internal Server Error"},
        )


@router.delete(
    "/profiles/{id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT
)
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
    try:
        if id not in profiles_db:
            err_msg = {"status": "error", "message": "Profile not found"}
            logger.warning(f"HTTPException: {err_msg}")
            raise HTTPException(status_code=404, detail=err_msg)

        # Remove from both structures to keep them in sync
        deleted_name = profiles_db[id]["name"]
        del profiles_db[id]
        profiles_name_index.pop(deleted_name, None)
        return None

    except HTTPException as he:
        logger.warning(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Internal Server Error"},
        )
