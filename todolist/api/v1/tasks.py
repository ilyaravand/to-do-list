# todolist/api/v1/tasks.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.get("/ping", summary="Ping endpoint for tasks")
def ping_tasks():
    """
    Simple test endpoint just to verify that the API is wired correctly.
    """
    return {"message": "tasks endpoint is alive"}
