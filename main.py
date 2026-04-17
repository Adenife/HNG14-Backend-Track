from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.routers import (
    gender_classifier,
    profiles,
)


app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# Register slowapi rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


origins = [settings.CLIENT_ORIGIN]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mandatory for grading
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
