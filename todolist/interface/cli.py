# todolist/interface/cli.py
from __future__ import annotations



import sys
from typing import Callable
from ..core.repository import ProjectRepository
from ..core.services import ProjectService
from ..config.settings import settings
from ..core.errors import (
    ProjectLimitReached, DuplicateProjectName, ValidationError, ProjectNotFound
)

_repo = ProjectRepository()
_service = ProjectService(_repo)


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
        print("(no projects yet)")
    else:
        for p in sorted(_repo.all(), key=lambda x: x.id):
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

def main() -> None:
    actions: dict[str, tuple[str, Callable[[], None]]] = {
        "1": ("Create project", action_create_project),
        "2": ("List projects", action_list_projects),
        "3": ("Show info (limit & count)", action_info),
        "4": ("Edit project", action_edit_project),
        "5": ("Delete project", action_delete_project),
        "0": ("Exit", action_exit),
    }

    try:
        while True:
            print("\n" + _line())
            print("To-Do CLI — Menu")
            print(_line())
            for key, (label, _) in actions.items():
                print(f" {key}) {label}")
            choice = input("\nSelect an option: ").strip()
            action = actions.get(choice)
            if action:
                action[1]()  # call the function
            else:
                print("[error] Invalid choice. Try again.")
    except KeyboardInterrupt:
        print("\n\nInterrupted. Exiting…")
        sys.exit(130)


if __name__ == "__main__":
    main()
