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
