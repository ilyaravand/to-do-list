# todolist/main.py
from fastapi import FastAPI

from todolist.api.v1.tasks import router as tasks_router
from todolist.api.v1.projects import router as projects_router

app = FastAPI(
    title="ToDoList API",
    version="1.0.0",
    description="API for managing projects and tasks (Phase 3).",
)

app.include_router(projects_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
