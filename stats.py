"""Progress stats: completed tasks per week and walk streaks, computed from completion timestamps."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from pawpal_system import Task

WALK = re.compile(r"\bwalk(s|ed|ing)?\b", re.I)
MILESTONES = [
    (3, "🌱 Getting started"), (7, "🏅 One week strong"), (14, "🥈 Two weeks of walks"),
    (30, "🥇 A whole month"), (60, "🏆 Walking legend"), (100, "👑 Century club"),
]


@dataclass(frozen=True)
class Completion:
    description: str
    when: datetime
    pet_name: str = ""


def completions_from(tasks: list[Task]) -> list[Completion]:
    """Finished tasks that have a completion time (tasks finished before this was recorded are ignored)."""
    return [Completion(t.description, t.completed_at, t.pet_name) for t in tasks if t.completed and t.completed_at]


def week_start(day: date) -> date:
    """The Monday of the week containing `day`."""
    return day - timedelta(days=day.weekday())


def weekly_counts(done: list[Completion], today: date, weeks: int = 8) -> list[tuple[date, int]]:
    """(Monday, completed count) for the last `weeks` weeks, oldest first, including empty weeks."""
    first = week_start(today) - timedelta(weeks=weeks - 1)
    counts = {first + timedelta(weeks=i): 0 for i in range(weeks)}
    for c in done:
        monday = week_start(c.when.date())
        if monday in counts:
            counts[monday] += 1
    return list(counts.items())


def walk_days(done: list[Completion]) -> set[date]:
    """Days on which at least one walk was completed."""
    return {c.when.date() for c in done if WALK.search(c.description)}


def current_streak(days: set[date], today: date) -> int:
    """Consecutive walk days up to today. A streak is still alive if the last walk was yesterday."""
    day = today if today in days else today - timedelta(days=1)
    streak = 0
    while day in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def longest_streak(days: set[date]) -> int:
    best = run = 0
    previous = None
    for day in sorted(days):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    return best


def next_milestone(streak: int) -> tuple[int, str] | None:
    """The next streak target above the current streak, or None once every milestone is reached."""
    return next(((n, label) for n, label in MILESTONES if n > streak), None)


def reached_milestone(streak: int) -> str | None:
    """The best milestone label the streak has reached so far."""
    earned = [label for n, label in MILESTONES if streak >= n]
    return earned[-1] if earned else None


def sample_completions(today: date) -> list[Completion]:
    """Made-up history for the 'sample data' preview: eight weeks of care, a 9-day walk streak long ago and a
    5-day streak running now."""
    walk_offsets = set(range(0, 5)) | set(range(7, 16)) | {20, 21, 22, 30, 31, 40, 41, 42, 43}
    done = []
    for offset in range(56):
        day = today - timedelta(days=offset)
        at = lambda hour, minute=0: datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute)
        if offset in walk_offsets:
            done.append(Completion("Morning walk", at(8, 30), "Spot"))
        if offset % 7 != 3 and (offset < 28 or offset % 3 != 0):
            done.append(Completion("Morning feeding", at(7, 45), "Spot"))
        if offset < 40 and offset % 2 == 0:
            done.append(Completion("Evening feeding", at(17, 45), "Spot"))
        if offset % 7 == 2:
            done.append(Completion("Brush coat", at(19), "Spot"))
    return done
