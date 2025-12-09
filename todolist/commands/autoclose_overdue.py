from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import and_, select

from todolist.db.session import session_scope
from todolist.models import Task, TaskStatusEnum


def main() -> None:
    """Auto-close all overdue tasks.

    Overdue is defined as:
    - deadline is not NULL, and
    - deadline < today (date comparison only), and
    - status is not DONE.
    """

    today = date.today()
    now = datetime.now(UTC)

    # We define "before today" by comparing to today's midnight in UTC.
    today_start_utc = datetime.combine(today, datetime.min.time(), tzinfo=UTC)

    with session_scope() as session:
        stmt = select(Task).where(
            and_(
                Task.deadline.is_not(None),
                Task.deadline < today_start_utc,
                Task.status != TaskStatusEnum.DONE.value,
            )
        )

        overdue_tasks = list(session.scalars(stmt))

        for task in overdue_tasks:
            task.status = TaskStatusEnum.DONE.value
            task.closed_at = now

        updated_count = len(overdue_tasks)
        # session_scope will commit on successful exit

    if updated_count:
        print(f"[ok] Auto-closed {updated_count} overdue task(s).")
    else:
        print("[ok] No overdue tasks found.")
