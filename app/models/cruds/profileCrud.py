from sqlalchemy.orm import Session
from pydantic import EmailStr
from datetime import datetime
import json
import uuid
from typing import Optional
from sqlalchemy import desc, asc


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
    # 1. Validate the dictionary using your schema
    validated_data = schemas.ProfileDataSchema(**profile)

    # 2. Convert the validated schema to a SQLAlchemy model
    # .model_dump() (Pydantic v2) or .dict() (Pydantic v1)
    db_profile = models.Profile(**validated_data.model_dump())

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
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
    Asynchronous function to retrieve users from the database.

    Args:
        db (Session): The database session.
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to retrieve. Defaults to 100.

    Returns:
        List[User]: List of user objects retrieved from the database.
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
        query = query.filter(models.Profile.age >= min_age)
    if max_age is not None:
        query = query.filter(models.Profile.age <= max_age)
    if min_gender_probability is not None:
        query = query.filter(
            models.Profile.gender_probability >= min_gender_probability
        )
    if min_country_probability is not None:
        query = query.filter(
            models.Profile.country_probability >= min_country_probability
        )

    if not sort_by or sort_by not in ALLOWED_SORT_FIELDS:
        sort_attr = models.Profile.created_at
    else:
        # Now the IDE knows sort_by is definitely a valid string
        sort_attr = getattr(models.Profile, sort_by)

    if order_by == "desc":
        query = query.order_by(desc(sort_attr))
    else:
        query = query.order_by(asc(sort_attr))

    total_count = query.count()
    result = query.offset(skip).limit(limit).all()

    return result, total_count
