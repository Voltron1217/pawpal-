from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from uuid import uuid4

FREQUENCIES = {"once": None, "daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


@dataclass
class Task:
    description: str
    time: datetime
    frequency: str = "once"
    completed: bool = False
    pet_name: str = ""
    duration_minutes: int = 30
    id: str = field(default_factory=lambda: uuid4().hex, init=False, repr=False)

    def __post_init__(self) -> None:
        """Reject frequencies other than once, daily, or weekly."""
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    @property
    def end(self) -> datetime:
        """When this task finishes."""
        return self.time + timedelta(minutes=self.duration_minutes)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self, after: datetime | None = None) -> Task | None:
        """A fresh, incomplete copy of a recurring task, or None for one-off tasks.

        The new due date is the completion day (`after`, default: this task's own
        due time) plus one step, keeping the original time of day. It is never
        earlier than this task's due time plus one step, so completing a task
        early doesn't duplicate an upcoming occurrence.
        """
        step = FREQUENCIES[self.frequency]
        if step is None:
            return None
        base = after if after is not None else self.time
        nxt = max(
            datetime.combine(base.date() + step, self.time.time()),
            self.time + step,
        )
        return replace(self, time=nxt, completed=False)


@dataclass
class Pet:
    name: str
    age: int
    breed: str
    weight: float = 0.0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and record the pet's name on it."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's list."""
        self.tasks.remove(task)

    def pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    phone: str = ""
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pets."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name, or None if not found."""
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> list[Task]:
        """Every task from every pet, combined."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Organizes tasks across all of an owner's pets via Owner.get_all_tasks()."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that works on the given owner's pets."""
        self.owner = owner

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        return self.owner.get_all_tasks()

    def sorted_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return the given tasks (default: all) ordered by time."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: t.time)

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[Task]:
        """Return all tasks, optionally filtered by pet name and/or completion status."""
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def tasks_on(self, day: datetime) -> list[Task]:
        """Return tasks due on the given day, ordered by time."""
        due = [t for t in self.get_all_tasks() if t.time.date() == day.date()]
        return self.sorted_by_time(due)

    def find_conflicts(self) -> list[tuple[Task, Task]]:
        """Pairs of pending tasks whose time ranges overlap."""
        pending = self.sorted_by_time(self.filter_tasks(completed=False))
        conflicts = []
        for i, a in enumerate(pending):
            for b in pending[i + 1 :]:
                if b.time >= a.end:  # sorted, so nothing later can overlap a
                    break
                conflicts.append((a, b))
        return conflicts

    @staticmethod
    def _warning(a: Task, b: Task) -> str:
        """Human-readable description of two clashing tasks."""
        pa, pb = a.pet_name or "unassigned", b.pet_name or "unassigned"
        who = f"{pa}'s" if pa == pb else f"{pa}'s and {pb}'s"
        kind = "same pet" if pa == pb else "different pets"
        when = f"{a.time:%a %H:%M}" if a.time == b.time else f"{a.time:%a %H:%M}-{a.end:%H:%M} / {b.time:%H:%M}-{b.end:%H:%M}"
        return f"WARNING: {who} tasks '{a.description}' and '{b.description}' clash at {when} ({kind})"

    def conflict_warnings(self) -> list[str]:
        """One warning message per clashing pair; an empty list means no conflicts."""
        return [self._warning(a, b) for a, b in self.find_conflicts()]

    def warnings_for(self, task: Task) -> list[str]:
        """Warnings a task would cause if added now. Never raises, never modifies anything."""
        return [
            self._warning(task, other)
            for other in self.filter_tasks(completed=False)
            if other is not task and task.time < other.end and other.time < task.end
        ]

    def complete_task(self, task: Task, now: datetime | None = None) -> Task | None:
        """Mark a task done; if it recurs, add the next occurrence to its pet."""
        task.mark_complete()
        nxt = task.next_occurrence(after=now or datetime.now())
        pet = self.owner.get_pet(task.pet_name)
        if nxt is not None and pet is not None:
            pet.add_task(nxt)
        return nxt
