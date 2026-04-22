from uuid6 import uuid7
from ..core.database import Base
from ..core.config import settings
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    TIMESTAMP,
    Boolean,
    Numeric,
    Integer,
    Enum,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ARRAY
import datetime


def get_column_type(is_foreign_key=False, foreign_key_table=None):
    """
    Returns a column type based on the input parameters.

    Args:
        is_foreign_key (bool): Whether the column is a foreign key.
        foreign_key_table (str): The name of the table to which the foreign key is linked.

    Returns:
        Column: The column type based on the input parameters.
    """
    if is_foreign_key and foreign_key_table:
        return Column(
            UUID(as_uuid=True), ForeignKey(f"{foreign_key_table}.id"), nullable=False
        )
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid7)


def current_time():
    """
    Returns the current UTC time.

    This function uses the `datetime.datetime.utcnow()` method to get the current UTC time.

    Returns:
        datetime.datetime: The current UTC time.
    """
    return datetime.datetime.utcnow()


class Profile(Base):
    __tablename__ = "profile"
    id = get_column_type()
    name = Column(String(255), nullable=False)
    gender = Column(String(255), nullable=False)
    gender_probability = Column(Numeric(128), nullable=False)
    sample_size = Column(Integer, nullable=True)
    age = Column(Integer, nullable=False)
    age_group = Column(String(255), nullable=False)
    country_id = Column(String(255), nullable=False)
    country_name = Column(String(255), nullable=True)
    country_probability = Column(Numeric(128), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    # updatedat = Column(
    #     TIMESTAMP(timezone=True),
    #     nullable=False,
    #     default=current_time,
    #     onupdate=current_time,
    # )
