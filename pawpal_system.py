from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from uuid import uuid4

from pawpal_log import get_logger

log = get_logger("pawpal.system")

FREQUENCIES = {"once": None, "daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
MAX_DURATION_MINUTES = 24 * 60
MAX_PET_AGE = 50
MAX_NOTE_CHARS = 500
MAX_OWNER_NAME = 50
# species -> (label for young animals, age where "young" ends, age where "senior" starts), in years
LIFE_STAGES = {
    "Dog": ("puppy", 1, 7),
    "Cat": ("kitten", 1, 10),
    "Rabbit": ("young", 1, 6),
    "Hamster": ("young", 1, 2),
    "Guinea Pig": ("young", 1, 5),
}


@dataclass
class Task:
    description: str
    time: datetime
    frequency: str = "once"
    completed: bool = False
    pet_name: str = ""
    duration_minutes: int = 30
    completed_at: datetime | None = None
    id: str = field(default_factory=lambda: uuid4().hex, init=False, repr=False)

    def __post_init__(self) -> None:
        """Reject blank descriptions, bad times, unknown frequencies and impossible durations."""
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("task description is required")
        if not isinstance(self.time, datetime):
            raise ValueError("task time must be a datetime")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
        if not 0 < self.duration_minutes <= MAX_DURATION_MINUTES:
            raise ValueError(f"duration_minutes must be between 1 and {MAX_DURATION_MINUTES}")

    @property
    def end(self) -> datetime:
        """When this task finishes."""
        return self.time + timedelta(minutes=self.duration_minutes)

    def mark_complete(self, when: datetime | None = None) -> None:
        """Mark this task as completed, remembering when (default: now) for progress stats."""
        self.completed = True
        self.completed_at = when or datetime.now()

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
        nxt = self.time + step
        while nxt.date() <= base.date():
            nxt += step
        return replace(self, time=nxt, completed=False, completed_at=None)


@dataclass
class Pet:
    name: str
    age: int
    breed: str
    weight: float = 0.0
    tasks: list[Task] = field(default_factory=list)
    species: str = ""
    diet: str = ""
    medications: str = ""
    allergies: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def life_stage(self) -> str:
        """puppy/kitten/young, adult or senior, from species and age (birds and turtles are just 'adult')."""
        stages = LIFE_STAGES.get(self.species)
        if stages is None:
            return "adult"
        young_label, young_until, senior_from = stages
        if self.age < young_until:
            return young_label
        return "senior" if self.age >= senior_from else "adult"

    def add_note(self, text: str, when: datetime | None = None) -> str:
        """Save a dated free-text note about this pet and return the stored line."""
        text = " ".join((text or "").split())
        if not text:
            raise ValueError("note is empty")
        if len(text) > MAX_NOTE_CHARS:
            raise ValueError(f"note is too long ({len(text)} characters, max {MAX_NOTE_CHARS})")
        line = f"{(when or datetime.now()):%Y-%m-%d}: {text}"
        self.notes.append(line)
        log.info("note added for %s (%d chars)", self.name, len(text))
        return line

    def __post_init__(self) -> None:
        """Reject blank names and impossible ages or weights."""
        if not self.name or not self.name.strip():
            raise ValueError("pet name is required")
        if not 0 <= self.age <= MAX_PET_AGE:
            raise ValueError(f"pet age must be between 0 and {MAX_PET_AGE}")
        if self.weight < 0:
            raise ValueError("pet weight cannot be negative")

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and record the pet's name on it."""
        task.pet_name = self.name
        self.tasks.append(task)
        log.info("task added: %r for %s at %s (%s)", task.description, self.name, task.time.isoformat(), task.frequency)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's list; a task that isn't there is logged and ignored."""
        try:
            self.tasks.remove(task)
        except ValueError:
            log.warning("remove_task: %r is not on %s's list; nothing removed", task.description, self.name)
            return
        log.info("task removed: %r from %s", task.description, self.name)

    def pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    phone: str = ""
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pets; pet names must be unique."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"a pet named {pet.name!r} already exists")
        self.pets.append(pet)
        log.info("pet added: %s (%s, %s)", pet.name, pet.species or "unknown species", pet.breed)

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name, or None if not found."""
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> list[Task]:
        """Every task from every pet, combined."""
        return [task for pet in self.pets for task in pet.tasks]


class OwnerDirectory:
    """Several owners side by side. Each has their own pets and tasks, so pet names only need to be
    unique within one owner."""

    def __init__(self) -> None:
        self._owners: dict[str, Owner] = {}

    def add(self, name: str) -> Owner:
        """Create and register an owner; blank, over-long or duplicate (case-insensitive) names are rejected."""
        clean = " ".join((name or "").split())
        if not clean:
            raise ValueError("owner name is required")
        if len(clean) > MAX_OWNER_NAME:
            raise ValueError(f"owner name is too long (max {MAX_OWNER_NAME} characters)")
        if any(existing.lower() == clean.lower() for existing in self._owners):
            raise ValueError(f"an owner named {clean!r} already exists")
        owner = self._owners[clean] = Owner(clean)
        log.info("owner added: %s", clean)
        return owner

    def get(self, name: str | None) -> Owner | None:
        """The owner with exactly this name, or None."""
        return self._owners.get(name) if name is not None else None

    def names(self) -> list[str]:
        """Owner names in the order they were added."""
        return list(self._owners)

    def __len__(self) -> int:
        return len(self._owners)

    def __contains__(self, name: object) -> bool:
        return name in self._owners


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
        if conflicts:
            log.warning("%d scheduling conflict(s) among %d pending tasks", len(conflicts), len(pending))
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
        if task.completed:
            log.info("complete_task ignored: %r is already completed", task.description)
            return None
        moment = now or datetime.now()
        task.mark_complete(moment)
        nxt = task.next_occurrence(after=moment)
        pet = self.owner.get_pet(task.pet_name)
        if nxt is not None and pet is not None:
            pet.add_task(nxt)
        elif nxt is not None:
            log.warning("next occurrence of %r not saved: no pet named %r", task.description, task.pet_name)
        log.info("task completed: %r (%s); next=%s", task.description, task.pet_name or "no pet", nxt.time.isoformat() if nxt else None)
        return nxt
