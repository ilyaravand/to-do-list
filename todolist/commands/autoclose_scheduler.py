from __future__ import annotations

import time

import schedule

from todolist.commands.autoclose_overdue import main as autoclose_once


def job() -> None:
    print("[info] Running auto-close-overdue job...")
    autoclose_once()


def main() -> None:
    # Example: run every 15 minutes
    schedule.every(15).minutes.do(job)
    # If you want: schedule.every().day.at("02:00").do(job)

    print("[info] Starting scheduler: auto-close overdue tasks every 15 minutes.")
    print("[info] Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[info] Scheduler stopped by user.")
