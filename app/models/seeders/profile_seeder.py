import json
import os
from sqlalchemy.orm import Session
from ...models.cruds import profileCrud as crud


async def seed_profiles(db: Session, file_path: str = "seed_profiles.json"):
    """
    Asynchronously seeds the database with profile data from a JSON file.

    Parameters:
    - db: A database session object.
    - file_path: The string path to the JSON seed file.

    Returns:
    - None
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_path)

    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return

    with open(full_path, "r") as f:
        data = json.load(f)

    profiles_data = data.get("profiles", [])

    try:
        print(f"Seeding {len(profiles_data)} profiles...")

        for p in profiles_data:
            # Ensure the CRUD function name matches here
            await crud.seed_profile(db, p)

        print("Database seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise e
