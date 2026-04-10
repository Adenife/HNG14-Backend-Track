from fastapi import FastAPI, Query, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime, timezone
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles RequestValidationError exceptions.

    Returns a JSONResponse with a status code of 422 and a message indicating that the name must be a valid string containing only letters.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Unprocessable Entity: Name must be a valid string containing only letters",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handles HTTPException exceptions.

    Returns a JSONResponse with the status code and detail from the exception.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )


@app.get("/api/classify")
async def classify_name(
    name: str = Query(None),
):
    """
    Classify a name based on its gender.

    Args:
        name (str): The name to classify. Defaults to None.

    Returns:
        dict: A dictionary containing the classification result.

    Raises:
        HTTPException: If the name is missing or empty, or if the name contains non-alphabetic characters.
        HTTPException: If the external API returns an error.
    """
    if name is None or name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing or empty name"
        )

    if not re.match("^[a-zA-Z]+$", name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Non-string name: Name must contain only alphabetic characters",
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"https://api.genderize.io/?name={name}")
            data = response.json()
        except Exception:
            raise HTTPException(status_code=502, detail="External API error")

    if data.get("gender") is None or data.get("count") == 0:
        return {
            "status": "error",
            "message": "No prediction available for the provided name",
        }

    prob = data.get("probability", 0)
    count = data.get("count", 0)
    is_confident = prob >= 0.7 and count >= 100

    return {
        "status": "success",
        "data": {
            "name": name,
            "gender": data.get("gender"),
            "probability": prob,
            "sample_size": count,
            "is_confident": is_confident,
            "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
