from sqlalchemy.orm import Session
from pydantic import EmailStr
from datetime import datetime
import json
import uuid
from typing import Optional
from sqlalchemy import desc, asc
from fastapi import HTTPException


from ...models import models
from ...models.schemas import profileSchema as schemas


async def seed_profile(db: Session, profile: dict):
    """
    Asynchronously creates a new profile in the database.

    Parameters:
    - db: A database session object.
    - profile: A dictionary containing the profile's data.

    Returns:
    - The created profile object.
    """

    validated_data = schemas.ProfileDataSchema(**profile)
    db_profile = models.Profile(**validated_data.model_dump())
    db.add(db_profile)
    return db_profile


async def create_profile(db: Session, profile: schemas.ProfileDataSchema):
    """
    Asynchronously creates a new user in the database.

    Parameters:
    - db: A database session object.
    - profile: A dictionary containing the user's data.

    Returns:
    - The created user object.
    """
    db_profile = models.Profile(**profile)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


async def delete_profile(db: Session, user_id: uuid.UUID):
    """
    An asynchronous function to delete a user from the database.

    Parameters:
    - db: A database session object.
    - user_id: A UUID representing the user's ID.

    Returns:
    - True if the user was successfully deleted, False otherwise.
    """
    db_user = db.query(models.Profile).filter(models.Profile.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    else:
        return False


async def get_profile(db: Session, user_id: uuid.UUID):
    """
    Asynchronously retrieves a user from the database based on the provided user_id.

    Parameters:
    - db: The database session
    - user_id: The unique identifier of the user (UUID)

    Returns:
    - The user object from the database, or None if not found
    """
    return db.query(models.Profile).filter(models.Profile.id == user_id).first()


async def get_profile_by_name(db: Session, name: str):
    """
    Asynchronously retrieves a user from the database based on the provided user_id.

    Parameters:
    - db: The database session
    - user_id: The unique identifier of the user (UUID)

    Returns:
    - The user object from the database, or None if not found
    """
    return db.query(models.Profile).filter(models.Profile.name == name.lower()).first()


async def get_profiles_old(
    db: Session,
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieves profiles from the database based on various filters.

    Args:
        db (Session): The database session.
        gender (str, optional): The gender filter. Defaults to None.
        country_id (str, optional): The country ID filter. Defaults to None.
        age_group (str, optional): The age group filter. Defaults to None.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to retrieve. Defaults to 10.

    Returns:
        List[Profile]: The list of profiles matching the filters.
    """
    query = db.query(models.Profile)
    if gender:
        query = query.filter(models.Profile.gender.ilike(gender))

    if country_id:
        query = query.filter(models.Profile.country_id.ilike(country_id))

    if age_group:
        query = query.filter(models.Profile.age_group.ilike(age_group))

    return query.offset(skip).limit(limit).all()
    # return db.query(models.Profile).offset(skip).limit(limit).all()


async def get_profiles(
    db: Session,
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_gender_probability: Optional[float] = None,
    min_country_probability: Optional[float] = None,
    sort_by: Optional[str] = "created_at",
    order_by: Optional[str] = "desc",
    skip: int = 0,
    limit: int = 10,
):
    """
    Retrieves profiles from the database based on various filters.

    Args:
        db (Session): The database session.
        gender (str, optional): The gender filter. Defaults to None.
        country_id (str, optional): The country ID filter. Defaults to None.
        age_group (str, optional): The age group filter. Defaults to None.
        min_age (int, optional): The minimum age filter. Defaults to None.
        max_age (int, optional): The maximum age filter. Defaults to None.
        min_gender_probability (float, optional): The minimum gender probability filter. Defaults to None.
        min_country_probability (float, optional): The minimum country probability filter. Defaults to None.
        sort_by (str, optional): The field to sort by. Defaults to "created_at".
        order_by (str, optional): The sort order. Defaults to "desc".
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to retrieve. Defaults to 10.

    Returns:
        List[Profile]: The list of profiles matching the filters.
    """
    ALLOWED_SORT_FIELDS = {
        "age",
        "created_at",
        "gender_probability",
        "country_probability",
    }

    query = db.query(models.Profile)

    if gender:
        query = query.filter(models.Profile.gender.ilike(gender))
    if country_id:
        query = query.filter(models.Profile.country_id.ilike(country_id))
    if age_group:
        query = query.filter(models.Profile.age_group.ilike(age_group))

    if min_age is not None:
        query = query.filter(models.Profile.age > min_age)
    if max_age is not None:
        query = query.filter(models.Profile.age < max_age)
    if min_gender_probability is not None:
        query = query.filter(
            models.Profile.gender_probability >= min_gender_probability
        )
    if min_country_probability is not None:
        query = query.filter(
            models.Profile.country_probability >= min_country_probability
        )

    if sort_by and sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field. Allowed fields are: {', '.join(ALLOWED_SORT_FIELDS)}",
        )

    # Now it's safe to use or default
    sort_field_name = sort_by or "created_at"
    sort_attr = getattr(models.Profile, sort_field_name)

    if order_by == "desc":
        query = query.order_by(desc(sort_attr))
    else:
        query = query.order_by(asc(sort_attr))

    total_count = query.count()
    result = query.offset(skip).limit(limit).all()

    return result, total_count
