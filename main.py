from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.limiter import limiter
from app.routers import (
    gender_classifier,
    profiles,
    populators,
)
from app.models import models
from app.core.database import engine


app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
models.Base.metadata.create_all(bind=engine)

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
app.include_router(populators.router, tags=["Populators"], prefix="/api")


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # Check if the detail is already our custom error dict
    if isinstance(exc.detail, dict) and "status" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )
    # Fallback for standard string errors
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": str(exc.detail)},
    )


@app.get("/api/check")
async def check():
    """
    Check if the API is up and running.

    This endpoint returns a simple `{"status": "ok"}` response if the API is up and running.
    """
    return {"status": "ok"}
