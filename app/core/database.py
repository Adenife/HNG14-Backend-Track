from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings


environment = settings.ENVIRONMENT

if environment != "production":
    SQLALCHEMY_DATABASE_URL = (
        "postgresql://adenife:%40AdenifesimI@127.0.0.1:5432/hng14be"
    )

    # engine = create_engine(
    #     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    # )  # only needed for sqlite
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOSTNAME}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    A function that returns a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Primary storage: id -> profile data
profiles_db: Dict[str, dict] = {}

# Secondary index: name (lowercase) -> id
# Kept in sync with profiles_db for O(1) duplicate lookups
profiles_name_index: Dict[str, str] = {}

# External API result cache: name (lowercase) -> enrichment data
# Avoids redundant calls to Genderize/Agify/Nationalize for the same name
external_api_cache: Dict[str, dict] = {}
