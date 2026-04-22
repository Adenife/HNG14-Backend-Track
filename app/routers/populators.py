from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.seeders import profile_seeder as seed_module


router = APIRouter()


@router.get("/seed-profiles", status_code=status.HTTP_200_OK)
async def populate_location(db: Session = Depends(get_db)):
    """
    Populates the profile database with data.

    This function is an asynchronous route handler for the "/seed-profiles" endpoint. It takes a database session as a dependency and uses it to populate the profile database with data.

    Parameters:
        - db (Session): The database session. Defaults to the result of the get_db function.

    Returns:
        - dict: A dictionary containing a status message indicating the success of the database seeding operation.
    """
    try:
        await seed_module.seed_profiles(db)
        return {"status": "Successfully seeded the database"}

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Seed file not found."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during seeding: {str(e)}",
        )
