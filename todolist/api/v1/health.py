# todolist/api/v1/health.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "",
    summary="Health check",
    description="Simple health check endpoint to verify that the API is running.",
)
async def health_check():
    return {"status": "ok"}
