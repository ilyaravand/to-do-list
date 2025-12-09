# todolist/interface/cli.py
from __future__ import annotations
import sys
from typing import Callable
from ..config.settings import settings
# from ..core.repository import ProjectRepository, TaskRepository
from ..core.repository import InMemoryProjectRepository, InMemoryTaskRepository
from ..core.services import ProjectService, TaskService
from ..core.errors import (
    ProjectLimitReached, DuplicateProjectName, ValidationError, ProjectNotFound,
    TaskLimitReached, TaskNotFound
)

# _repo = ProjectRepository()
# _task_repo = TaskRepository()
_repo = InMemoryProjectRepository()
_task_repo = InMemoryTaskRepository()

_service = ProjectService(_repo, cascade_delete_tasks=_task_repo.delete_by_project)
_task_service = TaskService(project_repo=_repo, task_repo=_task_repo)


def _line(ch: str = "─", n: int = 50) -> str:
    return ch * n


def _pause(msg: str = "Press Enter to continue...") -> None:
    try:
        input(msg)
    except EOFError:
        pass


def action_create_project() -> None:
    print(_line())
    print("Create a new project")
    print(_line())
    name = input("Name (≤ 30 words): ").strip()
    desc = input("Description (≤ 150 words, optional): ").strip()
    try:
        p = _service.create_project(name, desc)
        print(f"\n[ok] Project created: id={p.id} name='{p.name}'")
    except (ProjectLimitReached, DuplicateProjectName, ValidationError) as e:
        print(f"\n[error] {e}")
    _pause()


def action_list_projects() -> None:
    print(_line())
    print("Projects")
    print(_line())
    if _repo.count() == 0:
        print("(no projects yet)")  # friendly empty message
    else:
        # sort by creation time, as required by the PDF
        for p in sorted(_repo.all(), key=lambda x: x.created_at):
            print(f"- #{p.id} | {p.name}  —  {p.description or '(no description)'}")
    _pause()


def action_info() -> None:
    print(_line())
    print("Info")
    print(_line())
    print(f"MAX_NUMBER_OF_PROJECT = {settings.MAX_NUMBER_OF_PROJECT}")
    print(f"Current count         = {_repo.count()}")
    _pause()


def action_exit() -> None:
    print("\nBye!")
    raise SystemExit(0)


def action_edit_project() -> None:
    print(_line())
    print("Edit a project")
    print(_line())
    pid_str = input("Project ID to edit: ").strip()
    if not pid_str.isdigit():
        print("\n[error] invalid id")
        return _pause()

    pid = int(pid_str)
    current = _repo.get_by_id(pid)
    if not current:
        print(f"\n[error] project #{pid} not found")
        return _pause()

    print(f"Current name: {current.name}")
    print(f"Current description: {current.description or '(none)'}")

    new_name = input("New name (blank to keep): ").strip()
    new_desc = input("New description (blank to keep): ").strip()

    if new_name == "": new_name = None
    if new_desc == "": new_desc = None

    try:
        p = _service.update_project(pid, name=new_name, description=new_desc)
        print(f"\n[ok] updated: id={p.id} name='{p.name}'")
    except (DuplicateProjectName, ValidationError, ProjectNotFound) as e:
        print(f"\n[error] {e}")
    _pause()

def action_add_task() -> None:
    print(_line())
    print("Add a task to a project")
    print(_line())

    pid_str = input("Project ID: ").strip()
    if not pid_str.isdigit():
        print("\n[error] invalid project id")
        return _pause()
    pid = int(pid_str)

    title = input("Title (≤ 30 words): ").strip()
    desc = input("Description (≤ 150 words, optional): ").strip()
    status = input("Status [todo|doing|done] (blank = todo): ").strip().lower()
    deadline = input("Deadline (YYYY-MM-DD, optional): ").strip()

    status = status or "todo"
    deadline = deadline or None

    try:
        t = _task_service.create_task(
            project_id=pid,
            title=title,
            description=desc,
            status=status,
            deadline=deadline,
        )
        shown_deadline = t.deadline.isoformat() if t.deadline else "—"
        print(f"\n[ok] Task created: id={t.id} project=#{t.project_id} status={t.status} deadline={shown_deadline}")
    except (ProjectNotFound, TaskLimitReached, ValidationError) as e:
        print(f"\n[error] {e}")
    _pause()


def action_delete_project() -> None:
    print(_line())
    print("Delete a project")
    print(_line())
    pid_str = input("Project ID to delete: ").strip()
    if not pid_str.isdigit():
        print("\n[error] invalid id")
        return _pause()

    pid = int(pid_str)
    confirm = input(
        f"Are you sure you want to delete project #{pid}? This will also delete its tasks. [y/N]: "
    ).strip().lower()
    if confirm not in {"y", "yes"}:
        print("\n[cancelled] no changes made.")
        return _pause()

    try:
        _service.delete_project(pid)
        print(f"\n[ok] deleted project #{pid}")
    except ProjectNotFound as e:
        print(f"\n[error] {e}")
    _pause()

def action_change_task_status() -> None:
    print(_line()); print("Change task status"); print(_line())
    tid_str = input("Task ID: ").strip()
    if not tid_str.isdigit():
        print("\n[error] invalid task id"); return _pause()
    tid = int(tid_str)
    status = input("New status [todo|doing|done]: ").strip().lower()
    try:
        t = _task_service.set_task_status(tid, status)
        print(f"\n[ok] task #{t.id} status → {t.status}")
    except (TaskNotFound, ValidationError) as e:
        print(f"\n[error] {e}")
    _pause()


def action_edit_task() -> None:
    print(_line()); print("Edit task"); print(_line())
    tid_str = input("Task ID to edit: ").strip()
    if not tid_str.isdigit():
        print("\n[error] invalid task id"); return _pause()
    tid = int(tid_str)

    # Optional: fetch current task to show values (nice UX)
    t = _task_repo.get_by_id(tid)
    if not t:
        print(f"\n[error] task #{tid} not found"); return _pause()
    print(f"Current title: {t.title}")
    print(f"Current description: {t.description or '(none)'}")
    print(f"Current status: {t.status}")
    print(f"Current deadline: {t.deadline or '(none)'}")

    title = input("New title (blank to keep): ").strip()
    desc = input("New description (blank to keep): ").strip()
    status = input("New status [todo|doing|done] (blank to keep): ").strip().lower()
    deadline = input("New deadline YYYY-MM-DD (blank to keep): ").strip()

    kwargs = {}
    if title != "": kwargs["title"] = title
    if desc != "": kwargs["description"] = desc
    if status != "": kwargs["status"] = status
    if deadline != "": kwargs["deadline"] = deadline

    try:
        t2 = _task_service.update_task(tid, **kwargs)
        d_show = t2.deadline.isoformat() if t2.deadline else "—"
        print(f"\n[ok] updated task #{t2.id}  status={t2.status}  deadline={d_show}")
    except (TaskNotFound, ValidationError) as e:
        print(f"\n[error] {e}")
    _pause()

def action_delete_task() -> None:
    print(_line()); print("Delete task"); print(_line())
    pid_str = input("Project ID: ").strip()
    tid_str = input("Task ID: ").strip()
    if not (pid_str.isdigit() and tid_str.isdigit()):
        print("\n[error] invalid ids"); return _pause()
    pid, tid = int(pid_str), int(tid_str)
    confirm = input(f"Delete task #{tid} in project #{pid}? [y/N]: ").strip().lower()
    if confirm not in {"y", "yes"}:
        print("\n[cancelled] no changes made."); return _pause()
    try:
        _task_service.delete_task(pid, tid)
        print(f"\n[ok] deleted task #{tid} from project #{pid}")
    except (TaskNotFound, ValidationError) as e:
        print(f"\n[error] {e}")
    _pause()

def action_list_project_tasks() -> None:
    print(_line())
    print("Tasks of a project")
    print(_line())
    pid_str = input("Project ID: ").strip()
    if not pid_str.isdigit():
        print("\n[error] invalid project id")
        return _pause()
    pid = int(pid_str)

    try:
        tasks = _task_service.list_tasks_for_project(pid)
    except ProjectNotFound as e:
        # suitable message if project does not exist
        print(f"\n[error] {e}")
        return _pause()

    if not tasks:
        # suitable message if project exists but has no tasks
        print(f"(no tasks for project #{pid})")
    else:
        # required fields per PDF: id, title, status, deadline
        for t in tasks:
            d = t.deadline.isoformat() if t.deadline else "—"
            print(f"- #{t.id} | [{t.status}] {t.title}  —  deadline: {d}")
    _pause()

def action_reset_memory() -> None:
    global _repo, _task_repo, _service, _task_service
    # reinitialize all in-memory stores
    # _repo = ProjectRepository()
    # _task_repo = TaskRepository()
    _repo = InMemoryProjectRepository()
    _task_repo = InMemoryTaskRepository()
    _service = ProjectService(_repo, cascade_delete_tasks=_task_repo.delete_by_project)
    _task_service = TaskService(project_repo=_repo, task_repo=_task_repo)
    print("\n[ok] in-memory state reset (projects & tasks cleared)")
    _pause()

# def main() -> None:
#     actions: dict[str, tuple[str, Callable[[], None]]] = {
#         "1": ("Create project", action_create_project),
#         "2": ("List projects", action_list_projects),
#         "3": ("Show info (limit & count)", action_info),
#         "4": ("Edit project", action_edit_project),
#         "5": ("Delete project", action_delete_project),
#         "6": ("Add task", action_add_task),
#         "7": ("Change task status", action_change_task_status),
#         "8": ("Edit task", action_edit_task),
#         "9": ("Delete task", action_delete_task),
#         "10": ("List tasks of a project", action_list_project_tasks),
#         "99": ("[DEV] Reset in-memory state", action_reset_memory),
#         "0": ("Exit", action_exit),
#     }
#
#     try:
#         while True:
#             print("\n" + _line())
#             print("To-Do CLI — Menu")
#             print(_line())
#             for key, (label, _) in actions.items():
#                 print(f" {key}) {label}")
#             choice = input("\nSelect an option: ").strip()
#             action = actions.get(choice)
#             if action:
#                 action[1]()  # call the function
#             else:
#                 print("[error] Invalid choice. Try again.")
#     except KeyboardInterrupt:
#         print("\n\nInterrupted. Exiting…")
#         sys.exit(130)

# todolist/interface/cli.py

def main() -> None:
    """
    Deprecated CLI entry point.

    Phase 3 requirement: the primary interface is now the HTTP API.
    """
    message = (
        "This CLI is deprecated and no longer supported.\n\n"
        "Please use the HTTP API instead:\n"
        "  poetry run uvicorn todolist.main:app --reload\n\n"
        "Then open the automatic documentation in your browser:\n"
        "  http://127.0.0.1:8000/docs\n"
    )
    print(message)


if __name__ == "__main__":
    main()
