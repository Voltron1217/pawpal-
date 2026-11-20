import os
import sys
from datetime import date, datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stats
from pawpal_system import Owner, Pet, Scheduler, Task
from stats import Completion

TODAY = date(2026, 11, 18)  # a Wednesday


def done_on(offset, description="Morning walk"):
    day = TODAY - timedelta(days=offset)
    return Completion(description, datetime.combine(day, datetime.min.time()).replace(hour=8))


# --- completion timestamps -------------------------------------------------------------
def test_completing_a_task_records_when():
    owner = Owner("A")
    pet = Pet("Spot", 3, "Beagle")
    owner.add_pet(pet)
    task = Task("Walk Spot", datetime(2026, 11, 18, 8, 0), "daily")
    pet.add_task(task)

    nxt = Scheduler(owner).complete_task(task, now=datetime(2026, 11, 18, 8, 30))

    assert task.completed_at == datetime(2026, 11, 18, 8, 30)
    assert nxt.completed_at is None and not nxt.completed  # the next occurrence starts fresh


def test_double_completion_keeps_the_first_timestamp():
    owner = Owner("A")
    pet = Pet("Spot", 3, "Beagle")
    owner.add_pet(pet)
    task = Task("Feed", datetime(2026, 11, 18, 8, 0))
    pet.add_task(task)
    sched = Scheduler(owner)
    sched.complete_task(task, now=datetime(2026, 11, 18, 8, 5))
    sched.complete_task(task, now=datetime(2026, 11, 18, 20, 0))
    assert task.completed_at == datetime(2026, 11, 18, 8, 5)


def test_completions_ignore_pending_tasks_and_tasks_without_a_timestamp():
    pending = Task("a", datetime(2026, 11, 18, 8, 0))
    legacy = Task("b", datetime(2026, 11, 18, 8, 0), completed=True)  # finished before timestamps existed
    finished = Task("c", datetime(2026, 11, 18, 8, 0))
    finished.mark_complete(datetime(2026, 11, 18, 9, 0))
    assert [c.description for c in stats.completions_from([pending, legacy, finished])] == ["c"]


# --- weekly counts ------------------------------------------------------------------------
def test_week_starts_on_monday():
    assert stats.week_start(date(2026, 11, 18)) == date(2026, 11, 16)
    assert stats.week_start(date(2026, 11, 22)) == date(2026, 11, 16)  # Sunday
    assert stats.week_start(date(2026, 11, 23)) == date(2026, 11, 23)  # next Monday


def test_weekly_counts_cover_eight_weeks_oldest_first_with_empty_weeks():
    done = [done_on(0), done_on(1), done_on(2), done_on(9)]  # Wed, Tue, Mon this week; Mon of last week
    weekly = stats.weekly_counts(done, TODAY)
    assert len(weekly) == 8 and weekly[-1][0] == date(2026, 11, 16)
    assert [n for _, n in weekly] == [0, 0, 0, 0, 0, 0, 1, 3]
    assert [d for d, _ in weekly] == sorted(d for d, _ in weekly)


def test_completions_older_than_the_window_are_not_counted():
    assert sum(n for _, n in stats.weekly_counts([done_on(200)], TODAY)) == 0


def test_sunday_night_and_monday_morning_fall_in_different_weeks():
    sunday = Completion("x", datetime(2026, 11, 15, 23, 59))
    monday = Completion("x", datetime(2026, 11, 16, 0, 1))
    weekly = dict(stats.weekly_counts([sunday, monday], TODAY))
    assert weekly[date(2026, 11, 9)] == 1 and weekly[date(2026, 11, 16)] == 1


# --- walk streaks -------------------------------------------------------------------------
@pytest.mark.parametrize("text", ["Morning walk", "Walk Spot", "Short walk", "evening WALK", "Walking the dog", "Walks"])
def test_walk_descriptions_are_recognised(text):
    assert stats.walk_days([done_on(0, text)]) == {TODAY}


@pytest.mark.parametrize("text", ["Feed Spot", "Sidewalk chalk", "Brush coat", "Walker visit"])
def test_non_walk_tasks_do_not_count(text):
    assert stats.walk_days([done_on(0, text)]) == set()


def test_several_walks_on_one_day_count_once():
    assert stats.walk_days([done_on(0), done_on(0, "Evening walk")]) == {TODAY}


def test_current_streak_counts_back_from_today():
    days = {TODAY - timedelta(days=i) for i in (0, 1, 2, 4, 5)}  # gap on day 3
    assert stats.current_streak(days, TODAY) == 3


def test_streak_is_still_alive_if_the_last_walk_was_yesterday():
    days = {TODAY - timedelta(days=i) for i in (1, 2, 3)}
    assert stats.current_streak(days, TODAY) == 3


def test_streak_is_broken_after_a_missed_day():
    days = {TODAY - timedelta(days=i) for i in (2, 3, 4)}
    assert stats.current_streak(days, TODAY) == 0


def test_no_walks_means_no_streak():
    assert stats.current_streak(set(), TODAY) == 0 and stats.longest_streak(set()) == 0


def test_longest_streak_finds_the_best_run():
    days = {TODAY - timedelta(days=i) for i in (0, 1, 5, 6, 7, 8, 9, 20)}
    assert stats.longest_streak(days) == 5
    assert stats.longest_streak({TODAY}) == 1


def test_milestones():
    assert stats.next_milestone(0)[0] == 3 and stats.next_milestone(3)[0] == 7 and stats.next_milestone(100) is None
    assert stats.reached_milestone(2) is None and "One week" in stats.reached_milestone(9)


def test_sample_data_shows_a_live_streak_and_a_longer_past_one():
    done = stats.sample_completions(TODAY)
    days = stats.walk_days(done)
    assert stats.current_streak(days, TODAY) == 5 and stats.longest_streak(days) == 9
    assert sum(n for _, n in stats.weekly_counts(done, TODAY)) > 40
