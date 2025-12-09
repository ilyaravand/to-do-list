# todolist/main.py
from fastapi import FastAPI

from todolist.api.v1.tasks import router as tasks_router

app = FastAPI(
    title="ToDoList API",
    version="1.0.0",
    description="API for managing tasks (Phase 3)",
)

# Versioned API
app.include_router(tasks_router, prefix="/api/v1")
