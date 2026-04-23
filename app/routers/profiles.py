import re
import uuid
from datetime import datetime, timezone
from typing import Optional, Union
from fastapi import APIRouter, HTTPException, status, Response, Request, Depends, Query
from sqlalchemy.orm import Session

from ..core.logging import configure_logging, LogLevel
from ..models.schemas import profileSchema as schema
from ..services.external_api import fetch_external_data
from ..core.limiter import limiter
from ..models.cruds import profileCrud as crud_profile
from ..core.database import get_db
from ..utils.helpers import parse_natural_query

router = APIRouter()
logger = configure_logging(level=LogLevel.DEBUG)


@router.post(
    "/profiles",
    status_code=status.HTTP_201_CREATED,
    response_model=schema.ProfileResponse,
    response_model_exclude_none=True,
)
@limiter.limit("10/minute")
async def create_profile(
    request: Request,
    payload: schema.ProfileCreateRequest,
    response: Response,
    db: Session = Depends(get_db),
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
        checker = await crud_profile.get_profile_by_name(db, name=processed_name)
        if checker:
            response.status_code = status.HTTP_200_OK
            return {
                "status": "success",
                "message": "Profile already exists",
                "data": checker,
            }

        ext_data = await fetch_external_data(processed_name)
        profile_data = {"name": processed_name, **ext_data}

        new_profile = await crud_profile.create_profile(db, profile_data)
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
    "/profiles/old",
    response_model=schema.ProfileListResponse_Old,
    status_code=status.HTTP_200_OK,
)
async def get_all_profiles_old(
    db: Session = Depends(get_db),
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
):
    """
    Retrieves all profiles from the database that match the specified filters.

    Parameters:
        - db (Session): The database session.
        - gender (Optional[str]): The gender of the profiles to retrieve. Defaults to None.
        - country_id (Optional[str]): The country ID of the profiles to retrieve. Defaults to None.
        - age_group (Optional[str]): The age group of the profiles to retrieve. Defaults to None.

    Returns:
        - schema.ProfileListResponse_Old: The response containing the list of profiles and the total count.
            - status (str): The status of the request.
            - count (int): The total count of profiles.
            - data (List[ProfileDataSchema]): The list of profile data.

    Raises:
        - HTTPException: If an HTTP exception occurs.
        - Exception: If any other exception occurs.
    """
    try:
        results = await crud_profile.get_profiles_old(
            db, gender=gender, country_id=country_id, age_group=age_group
        )

        if not results:
            return schema.ProfileListResponse_Old(status="success", count=0, data=[])

        return schema.ProfileListResponse_Old(
            status="success", count=len(results), data=results
        )

    except HTTPException as he:
        logger.warning(f"HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


@router.get(
    "/profiles",
    response_model=schema.ProfileListResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def get_all_profiles(
    db: Session = Depends(get_db),
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_gender_probability: Optional[float] = None,
    min_country_probability: Optional[float] = None,
    sort_by: Optional[str] = "created_at",
    order: Optional[str] = "desc",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Retrieves a paginated list of profiles from the database that match the specified filters.

    Parameters:
        - db (Session): The database session.
        - gender (Optional[str]): The gender of the profiles to retrieve. Defaults to None.
        - country_id (Optional[str]): The country ID of the profiles to retrieve. Defaults to None.
        - age_group (Optional[str]): The age group of the profiles to retrieve. Defaults to None.
        - min_age (Optional[int]): The minimum age of the profiles to retrieve. Defaults to None.
        - max_age (Optional[int]): The maximum age of the profiles to retrieve. Defaults to None.
        - min_gender_probability (Optional[float]): The minimum gender probability of the profiles to retrieve. Defaults to None.
        - min_country_probability (Optional[float]): The minimum country probability of the profiles to retrieve. Defaults to None.
        - sort_by (Optional[str]): The field to sort the profiles by. Defaults to "created_at".
        - order (Optional[str]): The order to sort the profiles by. Defaults to "desc".
        - page (int): The page number of the results to retrieve. Defaults to 1.
        - limit (int): The maximum number of profiles per page. Defaults to 10.

    Returns:
        - schema.ProfileListResponse: The response containing the list of profiles and the total count.
            - status (str): The status of the request.
            - page (int): The page number of the results.
            - limit (int): The maximum number of profiles per page.
            - total (int): The total count of profiles.
            - data (List[ProfileDataSchema]): The list of profile data.

    Raises:
        - HTTPException: If an HTTP exception occurs.
        - Exception: If any other exception occurs.
    """
    try:
        # Pagination math
        skip = (page - 1) * limit

        results, total_count = await crud_profile.get_profiles(
            db,
            gender=gender,
            country_id=country_id,
            age_group=age_group,
            min_age=min_age,
            max_age=max_age,
            min_gender_probability=min_gender_probability,
            min_country_probability=min_country_probability,
            sort_by=sort_by,
            order_by=order,
            skip=skip,
            limit=limit,
        )

        if not results:
            return schema.ProfileListResponse(
                status="success", page=page, limit=limit, total=total_count, data=[]
            )

        return schema.ProfileListResponse(
            status="success", page=page, limit=limit, total=total_count, data=results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        if "DataError" in str(type(e)) or "ProgrammingError" in str(type(e)):
            raise HTTPException(status_code=400, detail="Invalid query parameters")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get(
    "/profiles/search",
    response_model=schema.ProfileListResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def get_profile_natural_query(
    db: Session = Depends(get_db),
    search: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Retrieves a list of profiles based on a natural language query.

    This function takes a natural language query as input and returns a list of profiles that match the query.
    The query can include filters such as gender, country, age group, minimum age, maximum age, minimum gender probability, and minimum country probability.
    The results are paginated and can be sorted by age, creation date, gender probability, or country probability.
    The function also supports specifying the order of the results (ascending or descending).

    Parameters:
        db (Session): The database session.
        search (str): The natural language query.
        page (int): The page number of the results.
        limit (int): The number of profiles per page.

    Returns:
        ProfileListResponse: The response containing the status, page number, limit, total count, and the list of matching profiles.
    """
    try:
        filters = parse_natural_query(search)

        if filters.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": filters["message"]},
            )
        # Pagination math
        skip = (page - 1) * limit

        results, total_count = await crud_profile.get_profiles(
            db,
            gender=filters.get("gender"),
            country_id=filters.get("country_id"),
            age_group=filters.get("age_group"),
            min_age=filters.get("min_age"),
            max_age=filters.get("max_age"),
            skip=skip,
            limit=limit,
        )

        if not results:
            return schema.ProfileListResponse(
                status="success", page=page, limit=limit, total=total_count, data=[]
            )

        return schema.ProfileListResponse(
            status="success", page=page, limit=limit, total=total_count, data=results
        )

    except HTTPException as he:
        logger.warning(f"HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


@router.get(
    "/profiles/{id}",
    response_model=schema.ProfileResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def get_single_profile(
    id: uuid.UUID,
    db: Session = Depends(get_db),
):
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
        profile = await crud_profile.get_profile(db, user_id=id)
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
async def delete_profile(
    id: uuid.UUID,
    db: Session = Depends(get_db),
):
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
        profile = await crud_profile.get_profile(db, user_id=id)

        if not profile:
            err_msg = {"status": "error", "message": "Profile not found"}
            logger.warning(f"HTTPException: {err_msg}")
            raise HTTPException(status_code=404, detail=err_msg)

        # Remove from both structures to keep them in sync
        result = await crud_profile.delete_profile(db, user_id=id)
        if result:
            logger.info(f"Profile deleted successfully: {id}")
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            logger.error(f"Profile deletion failed: {id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to delete profile",
            )
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
