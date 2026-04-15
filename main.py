from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.core.config import settings
from app.routers import (
    gender_classifier,
    profiles,
)


app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)


origins = [settings.CLIENT_ORIGIN]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(gender_classifier.router, tags=["Gender Classifier"], prefix="/api")
app.include_router(profiles.router, tags=["Profiles"], prefix="/api")


@app.get("/api/check")
async def check():
    """
    Check if the API is up and running.

    This endpoint returns a simple `{"status": "ok"}` response if the API is up and running.
    """
    return {"status": "ok"}
