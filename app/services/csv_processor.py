import csv
import io
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..models import models
from ..models.cruds import profileCrud as crud_profile
from ..utils.helpers import get_age_group
import logging

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["name", "gender", "age", "country_id"]
RECOGNIZED_GENDERS = ["male", "female"]


async def process_csv(db: Session, file_content: bytes) -> Dict[str, Any]:
    """
    Processes a CSV file for profile ingestion.
    Uses streaming/chunked processing to handle large files efficiently.
    """
    stream = io.StringIO(file_content.decode("utf-8"))
    reader = csv.DictReader(stream)

    summary = {
        "status": "success",
        "total_rows": 0,
        "inserted": 0,
        "skipped": 0,
        "reasons": {
            "duplicate_name": 0,
            "invalid_age": 0,
            "unrecognized_gender": 0,
            "missing_fields": 0,
            "malformed_row": 0,
        },
    }

    # To optimize name checks, we can fetch existing names in batches if needed
    # But for simplicity and correctness with concurrent uploads, we'll check each row
    # or use a local cache for the current session.

    batch_size = 1000
    # current_batch = []

    for row in reader:
        summary["total_rows"] += 1

        try:
            # 1. Check for missing fields
            if not all(row.get(field) for field in REQUIRED_FIELDS):
                summary["skipped"] += 1
                summary["reasons"]["missing_fields"] += 1
                continue

            # 2. Validate Gender
            gender = row["gender"].lower().strip()
            if gender not in RECOGNIZED_GENDERS:
                summary["skipped"] += 1
                summary["reasons"]["unrecognized_gender"] += 1
                continue

            # 3. Validate Age
            try:
                age = int(row["age"])
                if age < 0:
                    raise ValueError
            except (ValueError, TypeError):
                summary["skipped"] += 1
                summary["reasons"]["invalid_age"] += 1
                continue

            # 4. Check for duplicate name in DB
            name = row["name"].lower().strip()
            existing = await crud_profile.get_profile_by_name(db, name)
            if existing:
                summary["skipped"] += 1
                summary["reasons"]["duplicate_name"] += 1
                continue

            # 5. Prepare data
            profile_data = {
                "name": name,
                "gender": gender,
                "age": age,
                "age_group": get_age_group(age),
                "country_id": row["country_id"].upper().strip(),
                "gender_probability": float(row.get("gender_probability", 1.0)),
                "country_probability": float(row.get("country_probability", 1.0)),
                "country_name": row.get("country_name"),
                "sample_size": (
                    int(row.get("sample_size", 0)) if row.get("sample_size") else 0
                ),
            }

            # Create the profile object
            db_profile = models.Profile(**profile_data)
            db.add(db_profile)
            summary["inserted"] += 1

            # Commit in batches to keep memory low and improve performance
            if summary["inserted"] % batch_size == 0:
                db.commit()

        except Exception as e:
            logger.error(f"Error processing row: {e}")
            summary["skipped"] += 1
            summary["reasons"]["malformed_row"] += 1
            continue

    # Final commit for the last batch
    db.commit()

    return summary
