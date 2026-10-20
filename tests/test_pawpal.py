import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    task = Task("Feed Fluffy", datetime(2024, 6, 1, 8, 0))
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Fluffy", age=3, breed="Persian")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feed Fluffy", datetime(2024, 6, 1, 8, 0)))

    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Helpers for the scheduler tests below
# ---------------------------------------------------------------------------
from datetime import timedelta

import pytest

from pawpal_system import Owner, Scheduler

DAY = datetime(2024, 6, 3, 0, 0)  # a Monday


def at(hour, minute=0, day_offset=0):
    return DAY.replace(hour=hour, minute=minute) + timedelta(days=day_offset)


@pytest.fixture
def setup():
    owner = Owner("Alice")
    fluffy = Pet("Fluffy", age=3, breed="Persian")
    spot = Pet("Spot", age=5, breed="Beagle")
    owner.add_pet(fluffy)
    owner.add_pet(spot)
    return owner, fluffy, spot, Scheduler(owner)


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------
def test_sorted_by_time_orders_tasks_added_out_of_order(setup):
    _, fluffy, spot, sched = setup
    fluffy.add_task(Task("late", at(18)))
    spot.add_task(Task("early", at(8)))
    fluffy.add_task(Task("mid", at(12)))

    assert [t.description for t in sched.sorted_by_time()] == ["early", "mid", "late"]


def test_sorted_by_time_orders_across_days_not_just_time_of_day(setup):
    _, fluffy, _, sched = setup
    fluffy.add_task(Task("tomorrow 7am", at(7, day_offset=1)))
    fluffy.add_task(Task("today 9pm", at(21)))

    assert [t.description for t in sched.sorted_by_time()] == ["today 9pm", "tomorrow 7am"]


def test_sorted_by_time_is_stable_for_identical_times(setup):
    _, fluffy, spot, sched = setup
    fluffy.add_task(Task("first", at(9)))
    spot.add_task(Task("second", at(9)))
    fluffy.add_task(Task("third", at(9)))

    # Ties keep get_all_tasks() order: pet by pet, then insertion order within a pet.
    assert [t.description for t in sched.sorted_by_time()] == ["first", "third", "second"]


def test_filter_by_pet_and_status_then_sort(setup):
    _, fluffy, spot, sched = setup
    done = Task("done", at(7))
    fluffy.add_task(Task("pending late", at(15)))
    fluffy.add_task(done)
    fluffy.add_task(Task("pending early", at(9)))
    spot.add_task(Task("spot task", at(8)))
    done.mark_complete()

    result = sched.sorted_by_time(sched.filter_tasks(pet_name="Fluffy", completed=False))

    assert [t.description for t in result] == ["pending early", "pending late"]


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------
def test_once_task_has_no_next_occurrence():
    assert Task("bath", at(9), "once").next_occurrence() is None


def test_completing_daily_task_creates_next_day_occurrence(setup):
    _, fluffy, _, sched = setup
    task = Task("feed", at(8), "daily")
    fluffy.add_task(task)

    nxt = sched.complete_task(task, now=at(8, 5))

    assert task.completed is True
    assert nxt is not None and nxt.completed is False
    assert nxt.time == at(8, day_offset=1)
    assert nxt in fluffy.tasks and nxt is not task


def test_completing_weekly_task_creates_occurrence_seven_days_later(setup):
    _, fluffy, _, sched = setup
    task = Task("vet", at(14), "weekly")
    fluffy.add_task(task)

    nxt = sched.complete_task(task, now=at(14, 10))

    assert nxt.time == at(14, day_offset=7)


def test_next_occurrence_keeps_original_time_of_day_when_completed_late(setup):
    # Task due 08:00, finished at 21:45: the next one must still be 08:00 tomorrow.
    _, fluffy, _, sched = setup
    task = Task("feed", at(8), "daily")
    fluffy.add_task(task)

    nxt = sched.complete_task(task, now=at(21, 45))

    assert nxt.time == at(8, day_offset=1)


def test_completing_early_does_not_duplicate_an_upcoming_occurrence(setup):
    # Due in 5 days but completed today: next must be due date + 1 step, not today + 1.
    _, fluffy, _, sched = setup
    task = Task("feed", at(8, day_offset=5), "daily")
    fluffy.add_task(task)

    nxt = sched.complete_task(task, now=at(9))

    assert nxt.time == at(8, day_offset=6)


def test_completing_same_recurring_task_twice_does_not_spawn_duplicates(setup):
    # BUG: complete_task has no guard, so a double-click on "Done"
    # (or a Streamlit rerun) adds a second identical next occurrence.
    _, fluffy, _, sched = setup
    task = Task("feed", at(8), "daily")
    fluffy.add_task(task)

    sched.complete_task(task, now=at(8))
    sched.complete_task(task, now=at(8))

    assert len(fluffy.tasks) == 2


def test_weekly_task_completed_late_keeps_its_weekday(setup):
    # Due Monday Jun 3; finished Wednesday Jun 5 -> expect next Monday Jun 10.
    _, fluffy, _, sched = setup
    task = Task("vet", at(14), "weekly")
    fluffy.add_task(task)

    nxt = sched.complete_task(task, now=at(15, day_offset=2))

    assert nxt.time.weekday() == task.time.weekday()


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------
def test_same_start_time_same_pet_is_a_conflict(setup):
    _, fluffy, _, sched = setup
    fluffy.add_task(Task("groom", at(16)))
    fluffy.add_task(Task("flea treatment", at(16)))

    assert len(sched.find_conflicts()) == 1
    assert "same pet" in sched.conflict_warnings()[0]


def test_partial_overlap_is_a_conflict(setup):
    _, fluffy, spot, sched = setup
    fluffy.add_task(Task("meds", at(12), duration_minutes=30))
    spot.add_task(Task("brush", at(12, 15), duration_minutes=30))

    assert len(sched.find_conflicts()) == 1


def test_back_to_back_tasks_do_not_conflict(setup):
    # 12:00-12:30 then 12:30-13:00 touch but do not overlap.
    _, fluffy, _, sched = setup
    fluffy.add_task(Task("a", at(12), duration_minutes=30))
    fluffy.add_task(Task("b", at(12, 30), duration_minutes=30))

    assert sched.find_conflicts() == []


def test_long_task_containing_several_short_ones_conflicts_with_each(setup):
    # The early `break` in find_conflicts must not skip later overlaps.
    _, fluffy, spot, sched = setup
    fluffy.add_task(Task("long", at(8), duration_minutes=120))
    spot.add_task(Task("short1", at(8, 30), duration_minutes=15))
    spot.add_task(Task("short2", at(9), duration_minutes=30))

    pairs = {(a.description, b.description) for a, b in sched.find_conflicts()}

    assert pairs == {("long", "short1"), ("long", "short2")}  # shorts don't clash with each other


def test_completed_tasks_are_ignored_in_conflicts(setup):
    _, fluffy, spot, sched = setup
    done = Task("done", at(9))
    fluffy.add_task(done)
    spot.add_task(Task("pending", at(9)))
    done.mark_complete()

    assert sched.find_conflicts() == []


def test_warnings_for_flags_overlap_without_modifying_schedule(setup):
    _, fluffy, spot, sched = setup
    fluffy.add_task(Task("groom", at(16)))
    candidate = Task("bath", at(16, 10), pet_name="Spot")

    warnings = sched.warnings_for(candidate)

    assert len(warnings) == 1
    assert len(fluffy.tasks) == 1 and spot.tasks == []
