"""Simple scheduler wrapper for periodic runs.

This is a tiny wrapper using the `schedule` library if available.
"""
import time
from typing import Callable


class Scheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, func: Callable, interval_minutes: int):
        try:
            import schedule
        except Exception:
            raise RuntimeError("schedule library not installed; pip install schedule")
        schedule.every(interval_minutes).minutes.do(func)
        self.jobs.append(func)

    def run_forever(self):
        import schedule
        while True:
            schedule.run_pending()
            time.sleep(1)

