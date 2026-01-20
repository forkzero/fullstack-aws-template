"""Health check endpoint."""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint with build info."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "git_sha": settings.GIT_SHA,
        "build_timestamp": settings.BUILD_TIMESTAMP,
    }
