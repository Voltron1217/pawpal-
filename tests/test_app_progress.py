import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Scheduler, Task

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def _app_with_pet():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(APP, default_timeout=60).run()
    [t for t in at.text_input if t.label == "Owner name"][0].set_value("Alice")
    [b for b in at.button if b.label == "Add owner"][0].click().run()
    pet = Pet("Spot", 3, "Beagle", species="Dog")
    at.session_state.directory.get("Alice").add_pet(pet)
    return at, pet


def test_progress_section_renders_with_empty_state():
    at, _ = _app_with_pet()
    at.run()
    assert not at.exception
    assert [m.label for m in at.metric] == ["Done this week", "🔥 Walk streak", "Best streak", "All-time done"]
    assert any("start a streak" in i.value for i in at.info)


def test_completed_walks_show_up_in_the_stats():
    at, pet = _app_with_pet()
    now = datetime.now()
    sched = Scheduler(at.session_state.directory.get("Alice"))
    for days_ago in (0, 1, 2):
        task = Task("Morning walk", now - timedelta(days=days_ago, hours=1))
        pet.add_task(task)
        sched.complete_task(task, now=now - timedelta(days=days_ago))
    at.run()
    values = {m.label: m.value for m in at.metric}
    assert values["🔥 Walk streak"] == "3 days" and values["All-time done"] == "3" and not at.exception
    assert any("Getting started" in s.value for s in at.success)


def test_sample_data_toggle_shows_made_up_history():
    at, _ = _app_with_pet()
    at.run()
    [t for t in at.toggle if t.label == "Sample data"][0].set_value(True).run()
    values = {m.label: m.value for m in at.metric}
    assert values["🔥 Walk streak"] == "5 days" and values["Best streak"] == "9 days" and not at.exception


def test_overdue_task_appears_in_reminders_and_done_completes_it():
    at, pet = _app_with_pet()
    pet.add_task(Task("Give medication", datetime.now() - timedelta(minutes=20)))
    at.run()
    assert any("Give medication" in m.value and "overdue" in m.value for m in at.markdown)

    [b for b in at.button if b.label == "Done" and (b.key or "").startswith("rem_done_")][0].click().run()
    assert pet.tasks[0].completed and pet.tasks[0].completed_at is not None
    assert not any("Give medication" in m.value and "overdue" in m.value for m in at.markdown)


def test_snooze_hides_the_reminder():
    at, pet = _app_with_pet()
    pet.add_task(Task("Give medication", datetime.now() + timedelta(minutes=5)))
    at.run()
    assert any("Give medication" in m.value for m in at.markdown)
    [b for b in at.button if (b.key or "").startswith("rem_snooze_")][0].click().run()
    assert not any("starts in" in m.value for m in at.markdown)
    assert not pet.tasks[0].completed
