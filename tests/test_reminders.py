import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import reminders
from pawpal_system import Task

NOW = datetime(2026, 11, 18, 10, 0)


def task(minutes_from_now, description="Walk", pet="Spot"):
    t = Task(description, NOW + timedelta(minutes=minutes_from_now))
    t.pet_name = pet
    return t


def test_task_starting_within_the_lead_time_is_a_soon_reminder():
    r = reminders.due_reminders([task(10)], NOW, lead_minutes=15)[0]
    assert (r.status, r.minutes) == ("soon", 10) and "in 10 min" in r.message()


def test_task_further_away_than_the_lead_time_is_not_a_reminder():
    assert reminders.due_reminders([task(16)], NOW, lead_minutes=15) == []
    assert len(reminders.due_reminders([task(16)], NOW, lead_minutes=30)) == 1


def test_task_starting_right_now_says_now():
    assert "starts now" in reminders.due_reminders([task(0)], NOW)[0].message()


def test_past_task_is_overdue_with_how_long_ago():
    r = reminders.due_reminders([task(-45)], NOW)[0]
    assert (r.status, r.minutes) == ("overdue", 45) and "45 min overdue" in r.message()
    assert "1 h 30 min overdue" in reminders.due_reminders([task(-90)], NOW)[0].message()


def test_very_old_misses_are_not_nagged_about():
    assert reminders.due_reminders([task(-25 * 60)], NOW) == []
    assert len(reminders.due_reminders([task(-23 * 60)], NOW)) == 1


def test_completed_tasks_never_remind():
    t = task(5)
    t.mark_complete(NOW)
    assert reminders.due_reminders([t], NOW) == []


def test_overdue_come_first_then_soonest():
    items = reminders.due_reminders([task(10, "late-soon"), task(3, "early-soon"), task(-5, "overdue")], NOW)
    assert [r.task.description for r in items] == ["overdue", "early-soon", "late-soon"]


def test_snoozed_task_is_hidden_until_the_snooze_ends():
    t = task(5)
    snoozed = {t.id: reminders.snooze_until(NOW, 10)}
    assert reminders.due_reminders([t], NOW, snoozed=snoozed) == []
    assert len(reminders.due_reminders([t], NOW + timedelta(minutes=11), snoozed=snoozed)) == 1


@pytest.mark.parametrize("lead", reminders.LEAD_OPTIONS)
def test_every_lead_option_works(lead):
    assert len(reminders.due_reminders([task(lead)], NOW, lead_minutes=lead)) == 1
