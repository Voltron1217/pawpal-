import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breeds import BREEDS
from pawpal_system import Owner, Pet, Scheduler
from routines import MAX_ROUTINE_TASKS, add_routine, routine_note, starter_routine

START = date(2026, 11, 19)


def rows_for(pet):
    return [
        {"Add": True, "Task": i.description, "Time": f"{i.clock:%H:%M}", "Repeats": i.frequency,
         "Minutes": i.duration_minutes, "Day offset": i.day_offset}
        for i in starter_routine(pet)
    ]


def setup(species="Dog", age=3, breed="Beagle"):
    owner = Owner("Alice")
    pet = Pet("Spot", age, breed, species=species)
    owner.add_pet(pet)
    return owner, pet, Scheduler(owner)


@pytest.mark.parametrize("species", list(BREEDS))
@pytest.mark.parametrize("age", [0, 3, 12])
def test_every_species_and_stage_has_a_routine_that_does_not_clash_with_itself(species, age):
    owner, pet, sched = setup(species, age, "Mixed")
    result = add_routine(pet, sched, rows_for(pet), START)
    assert result.added and not result.skipped
    assert sched.find_conflicts() == []


def test_unknown_species_has_no_routine():
    _, pet, _ = setup("", 3, "Mixed")
    assert starter_routine(pet) == []


def test_routine_depends_on_life_stage():
    puppy = [i.description for i in starter_routine(setup("Dog", 0)[1])]
    adult = [i.description for i in starter_routine(setup("Dog", 3)[1])]
    senior = [i.description for i in starter_routine(setup("Dog", 12)[1])]
    assert "Lunch" in puppy and "Lunch" not in adult
    assert any("senior" in d.lower() for d in senior) and any("wellness" in d.lower() for d in adult)


def test_high_energy_breed_gets_longer_walks_and_long_haired_cat_daily_brushing():
    beagle_walk = next(i for i in starter_routine(setup("Dog", 3, "Beagle")[1]) if i.description == "Morning walk")
    pug_walk = next(i for i in starter_routine(setup("Dog", 3, "Pug")[1]) if i.description == "Morning walk")
    assert beagle_walk.duration_minutes > pug_walk.duration_minutes
    persian = next(i for i in starter_routine(setup("Cat", 3, "Persian")[1]) if i.description == "Brush coat")
    siamese = next(i for i in starter_routine(setup("Cat", 3, "Siamese")[1]) if i.description == "Brush coat")
    assert (persian.frequency, siamese.frequency) == ("daily", "weekly")


def test_adult_turtle_note_explains_the_missing_feeding_task():
    _, adult, _ = setup("Turtle", 5, "Box Turtle")
    _, baby, _ = setup("Turtle", 1, "Box Turtle")
    assert routine_note(adult) and not routine_note(baby)
    assert not any("Feed" in i.description for i in starter_routine(adult))
    assert any("Feed" in i.description for i in starter_routine(baby))


def test_add_routine_sets_start_date_and_offsets_and_pet_name():
    _, pet, sched = setup()
    add_routine(pet, sched, rows_for(pet), START)
    by_name = {t.description: t for t in pet.tasks}
    assert by_name["Morning walk"].time.date() == START and by_name["Morning walk"].pet_name == "Spot"
    assert (by_name["Book yearly wellness exam"].time.date() - START).days == 7


def test_only_ticked_rows_are_added():
    _, pet, sched = setup()
    rows = rows_for(pet)
    for row in rows[1:]:
        row["Add"] = False
    result = add_routine(pet, sched, rows, START)
    assert len(result.added) == 1 and len(pet.tasks) == 1


def test_adding_twice_does_not_duplicate_tasks():
    _, pet, sched = setup()
    first = add_routine(pet, sched, rows_for(pet), START)
    second = add_routine(pet, sched, rows_for(pet), START)
    assert second.added == [] and len(second.skipped) == len(first.added)
    assert len(pet.tasks) == len(first.added)


def test_edited_rows_are_respected_and_bad_rows_are_skipped_and_reported():
    _, pet, sched = setup()
    rows = rows_for(pet)[:4]
    rows[0].update({"Task": "Breakfast kibble", "Time": "06:45", "Minutes": 20})
    rows[1]["Time"] = "8 o'clock"      # not HH:MM
    rows[2]["Repeats"] = "hourly"      # unsupported frequency
    rows[3]["Minutes"] = 0             # impossible duration
    result = add_routine(pet, sched, rows, START)
    assert [t.description for t in result.added] == ["Breakfast kibble"]
    assert result.added[0].time.hour == 6 and result.added[0].time.minute == 45
    assert len(result.skipped) == 3


def test_clashes_with_existing_tasks_are_reported_as_warnings():
    owner, pet, sched = setup()
    pet.add_task(__import__("pawpal_system").Task("Vet", __import__("datetime").datetime(2026, 11, 19, 8, 0)))
    result = add_routine(pet, sched, rows_for(pet), START)
    assert any("Vet" in w for w in result.warnings)


def test_routine_size_is_capped():
    _, pet, sched = setup()
    rows = rows_for(pet) * 10
    result = add_routine(pet, sched, rows, START)
    assert len(result.added) + len(result.skipped) <= MAX_ROUTINE_TASKS + 1
