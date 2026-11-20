"""Reminders: which pending tasks are due soon or overdue right now."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from pawpal_system import Task

LEAD_OPTIONS = [5, 10, 15, 30, 60]
SNOOZE_MINUTES = 10
OVERDUE_HOURS = 24  # older misses are not nagged about, so stale data doesn't flood the screen


@dataclass(frozen=True)
class Reminder:
    task: Task
    status: str  # "overdue" or "soon"
    minutes: int  # minutes overdue, or minutes until it starts

    def message(self) -> str:
        who = f"{self.task.pet_name}: " if self.task.pet_name else ""
        if self.status == "overdue":
            return f"{who}{self.task.description} was due at {self.task.time:%H:%M} ({_ago(self.minutes)} overdue)"
        when = "now" if self.minutes <= 0 else f"in {self.minutes} min"
        return f"{who}{self.task.description} starts {when} ({self.task.time:%H:%M})"


def _ago(minutes: int) -> str:
    return f"{minutes} min" if minutes < 60 else f"{minutes // 60} h {minutes % 60} min"


def due_reminders(
    tasks: list[Task],
    now: datetime,
    lead_minutes: int = 15,
    snoozed: dict[str, datetime] | None = None,
) -> list[Reminder]:
    """Pending tasks that start within `lead_minutes` or were due in the last 24 hours, most urgent first.

    Completed tasks and tasks snoozed until later than `now` are skipped.
    """
    snoozed = snoozed or {}
    found = []
    for task in tasks:
        if task.completed or snoozed.get(task.id, now) > now:
            continue
        if task.time < now:
            if now - task.time <= timedelta(hours=OVERDUE_HOURS):
                found.append(Reminder(task, "overdue", int((now - task.time).total_seconds() // 60)))
        elif task.time <= now + timedelta(minutes=lead_minutes):
            found.append(Reminder(task, "soon", int((task.time - now).total_seconds() // 60)))
    return sorted(found, key=lambda r: (r.status != "overdue", r.task.time))


def snooze_until(now: datetime, minutes: int = SNOOZE_MINUTES) -> datetime:
    return now + timedelta(minutes=minutes)
