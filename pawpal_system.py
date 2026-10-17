from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

FREQUENCIES = {"once": None, "daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


@dataclass
class Task:
    description: str
    time: datetime
    frequency: str = "once"
    completed: bool = False
    pet_name: str = ""

    def __post_init__(self) -> None:
        """Reject frequencies other than once, daily, or weekly."""
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """A fresh, incomplete copy of a recurring task, or None for one-off tasks."""
        step = FREQUENCIES[self.frequency]
        if step is None:
            return None
        return replace(self, time=self.time + step, completed=False)


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
        """Pairs of pending tasks scheduled for the same time."""
        pending = self.sorted_by_time(self.filter_tasks(completed=False))
        return [
            (a, b)
            for i, a in enumerate(pending)
            for b in pending[i + 1 :]
            if a.time == b.time
        ]

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task done; if it recurs, add the next occurrence to its pet."""
        task.mark_complete()
        nxt = task.next_occurrence()
        pet = self.owner.get_pet(task.pet_name)
        if nxt is not None and pet is not None:
            pet.add_task(nxt)
        return nxt
