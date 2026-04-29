import csv
import io
import re
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..core.auth import get_current_user, require_admin
from ..core.database import get_db
from ..core.limiter import limiter
from ..core.logging import LogLevel, configure_logging
from ..models import models
from ..models.cruds import profileCrud as crud_profile
from ..models.schemas import profileSchema as schema
from ..services.external_api import fetch_external_data
from ..utils.helpers import parse_natural_query
from ..models.schemas.userSchema import WhoAmIResponse

router = APIRouter()
logger = configure_logging(level=LogLevel.DEBUG)

ALLOWED_SORT_FIELDS = {"age", "created_at", "gender_probability", "country_probability"}
ALLOWED_ORDER = {"asc", "desc"}

CSV_COLUMNS = [
    "id",
    "name",
    "gender",
    "gender_probability",
    "age",
    "age_group",
    "country_id",
    "country_name",
    "country_probability",
    "created_at",
]


def _build_links(
    base_path: str, page: int, limit: int, total: int
) -> schema.PaginationLinks:
    total_pages = max(1, -(-total // limit))  # ceiling division
    self_link = f"{base_path}?page={page}&limit={limit}"
    next_link = (
        f"{base_path}?page={page + 1}&limit={limit}" if page < total_pages else None
    )
    prev_link = f"{base_path}?page={page - 1}&limit={limit}" if page > 1 else None
    return schema.PaginationLinks(self=self_link, next=next_link, prev=prev_link)


@router.post(
    "/profiles",
    status_code=status.HTTP_201_CREATED,
    response_model=schema.ProfileResponse,
    response_model_exclude_none=True,
)
@limiter.limit("60/minute")
async def create_profile(
    request: Request,
    payload: schema.ProfileCreateRequest,
    response: Response,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    """
    Create a new profile (admin only).

    Args:
        request (Request): The incoming HTTP request.
        payload (schema.ProfileCreateRequest): The profile data to create.
        response (Response): The HTTP response object.
        db (Session): The database session dependency.
        _ (models.User): The authenticated admin user.

    Returns:
        schema.ProfileResponse: A dictionary containing the created profile data.

    Raises:
        HTTPException: If the name is missing, empty, or contains non-alphabetic characters.
        HTTPException: If the user is not an admin.
    """
    """Create a new profile (admin only). Calls external APIs for enrichment."""
    name = str(payload.name).strip()
    logger.info(f"Profile creation request for name: {name}")

    try:
        if not name:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Missing or empty name"},
            )

        if not re.match(r"^[a-zA-Z\s]+$", name):
            raise HTTPException(
                status_code=422,
                detail={"status": "error", "message": "Name must contain only letters"},
            )

        processed_name = name.lower()

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
        raise
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Internal Server Error"},
        )


@router.get(
    "/profiles",
    response_model=schema.ProfileListResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("60/minute")
async def get_all_profiles(
    request: Request,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
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
    List profiles with filtering, sorting, pagination, and navigation links.

    Args:
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.
        _ (models.User): The authenticated current user.
        gender (Optional[str]): Filter by gender.
        country_id (Optional[str]): Filter by country ID.
        age_group (Optional[str]): Filter by age group.
        min_age (Optional[int]): Minimum age filter.
        max_age (Optional[int]): Maximum age filter.
        min_gender_probability (Optional[float]): Minimum gender probability filter.
        min_country_probability (Optional[float]): Minimum country probability filter.
        sort_by (Optional[str]): Field to sort by (default: created_at).
        order (Optional[str]): Sort order (asc or desc).
        page (int): Page number (default: 1).
        limit (int): Items per page (default: 10, max: 50).

    Returns:
        schema.ProfileListResponse: A dictionary containing paginated profile data and links.

    Raises:
        HTTPException: If query parameters are invalid.
    """
    """List profiles with filtering, sorting, pagination, and navigation links."""
    try:
        if sort_by not in ALLOWED_SORT_FIELDS or order not in ALLOWED_ORDER:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Invalid Query Parameters"},
            )

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

        total_pages = max(1, -(-total_count // limit))
        links = _build_links("/api/profiles", page, limit, total_count)

        return schema.ProfileListResponse(
            status="success",
            page=page,
            limit=limit,
            total=total_count,
            total_pages=total_pages,
            links=links,
            data=results or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/profiles/export")
@limiter.limit("60/minute")
async def export_profiles(
    request: Request,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
    fmt: str = Query("csv", alias="format"),
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    sort_by: Optional[str] = "created_at",
    order: Optional[str] = "desc",
):
    """
    Export profiles as CSV with the same filter/sort support as GET /api/profiles.

    Args:
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.
        _ (models.User): The authenticated current user.
        fmt (str): Export format (only csv is supported).
        gender (Optional[str]): Filter by gender.
        country_id (Optional[str]): Filter by country ID.
        age_group (Optional[str]): Filter by age group.
        min_age (Optional[int]): Minimum age filter.
        max_age (Optional[int]): Maximum age filter.
        sort_by (Optional[str]): Field to sort by.
        order (Optional[str]): Sort order.

    Returns:
        StreamingResponse: A CSV file download.

    Raises:
        HTTPException: If format is not csv or query parameters are invalid.
    """
    """Export profiles as CSV with the same filter/sort support as GET /api/profiles."""
    if fmt.lower() != "csv":
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "Only format=csv is supported"},
        )

    if sort_by not in ALLOWED_SORT_FIELDS or order not in ALLOWED_ORDER:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "Invalid Query Parameters"},
        )

    results, _ = await crud_profile.get_profiles(
        db,
        gender=gender,
        country_id=country_id,
        age_group=age_group,
        min_age=min_age,
        max_age=max_age,
        sort_by=sort_by,
        order_by=order,
        skip=0,
        limit=100_000,  # Export all matching rows
    )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for profile in results:
        row = {col: getattr(profile, col, "") for col in CSV_COLUMNS}
        writer.writerow(row)

    output.seek(0)
    from datetime import datetime

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"profiles_{timestamp}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/profiles/search",
    response_model=schema.ProfileListResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("60/minute")
async def get_profile_natural_query(
    request: Request,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Search profiles using natural language (e.g. 'young males from nigeria').

    Args:
        request (Request): The incoming HTTP request.
        db (Session): The database session dependency.
        _ (models.User): The authenticated current user.
        q (str): Natural language search query.
        page (int): Page number (default: 1).
        limit (int): Items per page (default: 10, max: 50).

    Returns:
        schema.ProfileListResponse: A dictionary containing paginated profile data and links.

    Raises:
        HTTPException: If the query is invalid or parsing fails.
    """
    """Search profiles using natural language (e.g. 'young males from nigeria')."""
    try:
        filters = parse_natural_query(q)

        if filters.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": filters["message"]},
            )

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

        total_pages = max(1, -(-total_count // limit))
        links = _build_links("/api/profiles/search", page, limit, total_count)

        return schema.ProfileListResponse(
            status="success",
            page=page,
            limit=limit,
            total=total_count,
            total_pages=total_pages,
            links=links,
            data=results or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get(
    "/profiles/{id}",
    response_model=schema.ProfileResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("60/minute")
async def get_single_profile(
    request: Request,
    id: uuid.UUID,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """
    Retrieve a single profile by UUID.

    Args:
        request (Request): The incoming HTTP request.
        id (uuid.UUID): The unique identifier of the profile.
        db (Session): The database session dependency.
        _ (models.User): The authenticated current user.

    Returns:
        schema.ProfileResponse: A dictionary containing the profile data.

    Raises:
        HTTPException: If the profile is not found.
    """
    """Retrieve a single profile by UUID."""
    try:
        profile = await crud_profile.get_profile(db, user_id=id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={"status": "error", "message": "Profile not found"},
            )
        return {"status": "success", "data": profile}

    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Internal Server Error"},
        )


@router.delete(
    "/profiles/{id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("60/minute")
async def delete_profile(
    request: Request,
    id: uuid.UUID,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    """
    Delete a profile by UUID (admin only).

    Args:
        request (Request): The incoming HTTP request.
        id (uuid.UUID): The unique identifier of the profile to delete.
        db (Session): The database session dependency.
        _ (models.User): The authenticated admin user.

    Returns:
        Response: A 204 No Content response on success.

    Raises:
        HTTPException: If the profile is not found or user is not an admin.
    """
    """Delete a profile by UUID (admin only)."""
    try:
        profile = await crud_profile.get_profile(db, user_id=id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={"status": "error", "message": "Profile not found"},
            )

        result = await crud_profile.delete_profile(db, user_id=id)
        if result:
            logger.info(f"Profile deleted: {id}")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Unable to delete profile"},
        )

    except HTTPException:
        raise
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
    include_in_schema=False,
)
async def get_all_profiles_old(
    db: Session = Depends(get_db),
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
):
    """
    Legacy endpoint preserved from Stage 2.

    Args:
        db (Session): The database session dependency.
        gender (Optional[str]): Filter by gender.
        country_id (Optional[str]): Filter by country ID.
        age_group (Optional[str]): Filter by age group.

    Returns:
        schema.ProfileListResponse_Old: A dictionary containing profile data in old format.

    Raises:
        HTTPException: If an internal error occurs.
    """
    """Legacy endpoint preserved from Stage 2."""
    try:
        results = await crud_profile.get_profiles_old(
            db, gender=gender, country_id=country_id, age_group=age_group
        )
        return schema.ProfileListResponse_Old(
            status="success", count=len(results) if results else 0, data=results or []
        )
    except Exception as e:
        logger.critical(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/users/me", response_model=WhoAmIResponse)
@limiter.limit("10/minute")
async def whoami(
    request: Request,
    current_user: models.User = Depends(get_current_user),
):
    """
    Get the current authenticated user's information.

    Args:
        request (Request): The incoming HTTP request.
        current_user (models.User): The authenticated current user.

    Returns:
        WhoAmIResponse: A dictionary containing the current user's data.

    Raises:
        HTTPException: If the user is not authenticated.
    """

    return {"status": "success", "data": current_user}
