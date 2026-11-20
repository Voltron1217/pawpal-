"""Starter care routines: a sensible set of recurring tasks for a pet's species and life stage.

The suggestions follow the guides in knowledge/. They are only a starting point: the owner reviews,
edits and chooses which tasks to add (see add_routine), and nothing is scheduled automatically.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from pawpal_log import get_logger
from pawpal_system import FREQUENCIES, Pet, Scheduler, Task

log = get_logger("pawpal.routines")

MAX_ROUTINE_TASKS = 30
HIGH_ENERGY_DOGS = {
    "Beagle", "Labrador Retriever", "Golden Retriever", "German Shepherd", "Border Collie", "Husky (Siberian)",
    "Boxer", "Australian Shepherd", "Australian Cattle Dog",
}
LONG_HAIRED_CATS = {"Persian", "Maine Coon", "Ragdoll", "Himalayan", "Norwegian Forest Cat", "Siberian"}


@dataclass
class RoutineItem:
    description: str
    clock: time
    frequency: str = "daily"
    duration_minutes: int = 15
    day_offset: int = 0  # days after the chosen start date for the first occurrence


def _t(hhmm: str) -> time:
    return datetime.strptime(hhmm, "%H:%M").time()


def _item(description: str, hhmm: str, frequency: str = "daily", minutes: int = 15, offset: int = 0) -> RoutineItem:
    return RoutineItem(description, _t(hhmm), frequency, minutes, offset)


def starter_routine(pet: Pet) -> list[RoutineItem]:
    """Suggested tasks for this pet, or an empty list when its species is unknown."""
    stage, species = pet.life_stage, pet.species
    if species == "Dog":
        walk = 45 if pet.breed in HIGH_ENERGY_DOGS and stage == "adult" else 30
        if stage == "puppy":
            return [
                _item("Breakfast", "07:30"), _item("Short walk", "08:00", minutes=20),
                _item("Lunch", "12:00"), _item("Short walk", "12:30", minutes=20),
                _item("Dinner", "17:30"), _item("Short walk", "18:00", minutes=20),
                _item("Brush coat and check ears", "19:00", "weekly"),
                _item("Book puppy vaccine visit", "10:00", "once", offset=3),
            ]
        if stage == "senior":
            walk = 20
        return [
            _item("Morning feeding", "07:30"), _item("Morning walk", "08:00", minutes=walk),
            _item("Evening feeding", "17:30"), _item("Evening walk", "18:00", minutes=walk),
            _item("Brush coat and check ears", "19:00", "weekly"),
            _item("Book senior check-up (every 6 months)" if stage == "senior" else "Book yearly wellness exam",
                  "10:00", "once", offset=7),
        ]
    if species == "Cat":
        brush = _item("Brush coat", "19:00", "daily" if pet.breed in LONG_HAIRED_CATS else "weekly", 10)
        vet = _item("Book senior check-up (every 6 months)" if stage == "senior" else "Book yearly wellness exam",
                    "10:00", "once", offset=7)
        if stage == "kitten":
            return [
                _item("Kitten meal", "07:30", minutes=10), _item("Scoop litter box", "08:00", minutes=10),
                _item("Play session", "09:00"), _item("Kitten meal", "12:00", minutes=10),
                _item("Play session", "15:00"), _item("Kitten meal", "17:00", minutes=10),
                _item("Play session", "19:30"), _item("Kitten meal", "21:00", minutes=10), brush,
                _item("Book kitten vaccine visit", "10:00", "once", offset=3),
            ]
        return [
            _item("Morning feeding", "08:00", minutes=10), _item("Scoop litter box", "08:15", minutes=10),
            _item("Play session", "17:30"), _item("Evening feeding", "18:00", minutes=10),
            brush, _item("Change litter completely", "19:30", "weekly", 20), _item("Play session", "20:30"), vet,
        ]
    if species == "Rabbit":
        return [
            _item("Refresh hay, water and greens", "08:00"), _item("Out-of-cage exercise", "08:30", minutes=90),
            _item("Pellets and fresh greens", "18:00"), _item("Out-of-cage exercise", "18:30", minutes=90),
            _item("Brush rabbit", "20:15", "weekly", 10), _item("Deep clean enclosure", "20:30", "weekly", 30),
            _item("Book yearly rabbit check-up", "10:00", "once", offset=14),
        ]
    if species == "Bird":
        return [
            _item("Fresh food and water", "08:00"), _item("Replace cage liner", "08:15", minutes=10),
            _item("Out-of-cage time", "17:00", minutes=90), _item("Cover cage for sleep", "20:00", minutes=5),
            _item("Deep clean cage and perches", "10:00", "weekly", 30),
            _item("Book yearly avian vet check-up", "10:00", "once", offset=14),
        ]
    if species == "Hamster":
        return [
            _item("Evening feeding", "19:00", minutes=10), _item("Spot clean cage", "19:15", minutes=10),
            _item("Gentle handling and play", "19:30"), _item("Full cage clean", "11:00", "weekly", 30),
        ]
    if species == "Guinea Pig":
        return [
            _item("Hay, vegetables and vitamin C", "08:00"), _item("Spot clean cage", "08:15", minutes=10),
            _item("Floor time", "17:00", minutes=60), _item("Full cage clean", "11:00", "weekly", 30),
            _item("Book yearly vet check-up", "10:00", "once", offset=14),
        ]
    if species == "Turtle":
        items = [_item("Check water, basking spot and UVB light", "08:00", minutes=10)]
        if pet.age <= 2:
            items.append(_item("Feed turtle", "08:15", minutes=10))
        items += [
            _item("Partial water change and filter check", "11:00", "weekly", 30),
            _item("Book yearly reptile vet check-up", "10:00", "once", offset=14),
        ]
        return items
    return []


def routine_note(pet: Pet) -> str:
    """A caveat shown under the suggestions when the routine can't express something."""
    if pet.species == "Turtle" and pet.age > 2:
        return "Adult turtles are fed every 2 to 3 days, which PawPal can't schedule yet. Add feeding days yourself."
    return ""


def _default(value, fallback):
    """The value, or the fallback only when it is missing or blank (so a 0 is still seen as 0)."""
    return fallback if value is None or value == "" else value


@dataclass
class RoutineResult:
    added: list[Task]
    skipped: list[str]
    warnings: list[str]


def add_routine(pet: Pet, scheduler: Scheduler, rows: list[dict], start: date) -> RoutineResult:
    """Add the rows the owner kept (their 'Add' box ticked) as tasks for the pet, starting on `start`.

    Each row: {"Add", "Task", "Time" (HH:MM), "Repeats", "Minutes", "Day offset"}. Bad rows are skipped and
    reported, tasks already on the schedule are not duplicated, and clashes are returned as warnings.
    """
    added: list[Task] = []
    skipped: list[str] = []
    warnings: list[str] = []
    chosen = [r for r in rows if r.get("Add")]
    if len(chosen) > MAX_ROUTINE_TASKS:
        skipped.append(f"Only the first {MAX_ROUTINE_TASKS} tasks were considered.")
        chosen = chosen[:MAX_ROUTINE_TASKS]
    for row in chosen:
        name = str(row.get("Task") or "").strip()
        try:
            clock = datetime.strptime(str(row.get("Time", "")).strip(), "%H:%M").time()
            offset = int(_default(row.get("Day offset"), 0))
            when = datetime.combine(start + timedelta(days=offset), clock)
            task = Task(name, when, str(_default(row.get("Repeats"), "daily")),
                        duration_minutes=int(_default(row.get("Minutes"), 15)))
        except (ValueError, TypeError) as exc:
            skipped.append(f"{name or 'Unnamed task'}: {exc}")
            continue
        if any(t.description == task.description and t.time.time() == task.time.time()
               and t.frequency == task.frequency and not t.completed for t in pet.tasks):
            skipped.append(f"{name}: already scheduled")
            continue
        task.pet_name = pet.name
        warnings += scheduler.warnings_for(task)  # checked against everything added so far
        pet.add_task(task)
        added.append(task)
    log.info("routine added for %s: %d added, %d skipped", pet.name, len(added), len(skipped))
    return RoutineResult(added, skipped, warnings)


assert set(FREQUENCIES) >= {"once", "daily", "weekly"}  # routines only use frequencies the scheduler supports
