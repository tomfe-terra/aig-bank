"""Health check endpoints."""

from fastapi import APIRouter, status

from ...core.constants import APP_NAME

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API is running and healthy.",
    responses={
        status.HTTP_200_OK: {
            "description": "Success",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "API is healthy",
                            "value": {
                                "status": "healthy",
                                "service": "AIG Bank API",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": APP_NAME,
    }
