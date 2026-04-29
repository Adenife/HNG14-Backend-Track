import os
import ijson
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

    # How many records to hold in memory before writing to disk
    BATCH_SIZE = 1000

    try:
        print("Starting streaming seed using CRUD function...")

        with open(full_path, "rb") as f:
            # Stream the 'profiles' array items
            profiles_stream = ijson.items(f, "profiles.item")

            count = 0
            for profile_data in profiles_stream:
                # Call your CRUD function (Now fast because it doesn't commit)
                await crud.seed_profile(db, profile_data)

                count += 1

                # Commit every 1000 records
                if count % BATCH_SIZE == 0:
                    db.commit()
                    # Optional: db.expunge_all()
                    # Use expunge_all if you have millions of rows to keep RAM low
                    print(f"Committed {count} profiles...")

            # Final commit for the remaining records
            db.commit()
            print(f"Success! Total seeded: {count}")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise e
