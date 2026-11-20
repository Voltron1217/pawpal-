"""Streamlit pieces for progress stats and reminders (the logic lives in stats.py and reminders.py)."""
from __future__ import annotations

from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st

import reminders
import stats
from pawpal_log import get_logger
from pawpal_system import Owner, Scheduler

log = get_logger("pawpal.ui")


def render_progress(owner: Owner, today: date | None = None, sample_default: bool = False) -> None:
    """Completed tasks per week, walk streaks and streak milestones for one pet or all of an owner's pets."""
    today = today or date.today()
    st.subheader("Progress stats")
    pick_col, sample_col = st.columns([2, 1])
    who = pick_col.selectbox("Show stats for", ["All pets"] + [p.name for p in owner.pets], key=f"stats_pet_{owner.name}")
    sample = sample_col.toggle(
        "Sample data", value=sample_default, key=f"stats_sample_{owner.name}",
        help="Preview with made-up history. Your real data is not touched.",
    )
    if sample:
        st.caption("Showing made-up history so you can see what this looks like.")
        done = stats.sample_completions(today)
    else:
        pets = owner.pets if who == "All pets" else [p for p in owner.pets if p.name == who]
        done = stats.completions_from([t for p in pets for t in p.tasks])

    weekly = stats.weekly_counts(done, today)
    this_week, last_week = weekly[-1][1], weekly[-2][1]
    days = stats.walk_days(done)
    streak, best = stats.current_streak(days, today), stats.longest_streak(days)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Done this week", this_week, delta=(this_week - last_week) if (this_week or last_week) else None,
              help="Compared with last week (this week is not over yet)")
    m2.metric("🔥 Walk streak", f"{streak} day{'s' if streak != 1 else ''}", help="Days in a row with a completed walk")
    m3.metric("Best streak", f"{best} day{'s' if best != 1 else ''}")
    m4.metric("All-time done", len(done))

    st.caption("Completed tasks per week (last 8 weeks)")
    frame = pd.DataFrame({"Week of": [f"{d:%b %d}" for d, _ in weekly], "Completed": [n for _, n in weekly]})
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#ff6b6b")
        .encode(
            x=alt.X("Week of:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)),  # sort=None keeps weeks in order
            y=alt.Y("Completed:Q", axis=alt.Axis(tickMinStep=1, title=None)),
            tooltip=["Week of", "Completed"],
        )
        .properties(height=220)
    )
    st.altair_chart(chart, use_container_width=True)

    badge, upcoming = stats.reached_milestone(streak), stats.next_milestone(streak)
    if badge:
        st.success(f"{badge}: {streak}-day walk streak!")
    if upcoming:
        target, label = upcoming
        remaining = target - streak
        st.progress(min(streak / target, 1.0), text=f"{remaining} more day{'s' if remaining != 1 else ''} of walks to reach {label}")
    if streak and today not in days:
        st.warning("🐕 No walk logged today yet. Complete one to keep your streak alive!")
    elif not days:
        st.info("Complete a task with 'walk' in its name to start a streak. Mark tasks done above and your progress shows up here.")
    elif not done:
        st.info("No completed tasks yet.")


def render_reminders(owner_name: str) -> None:
    """Reminder settings plus the live reminder panel, which refreshes itself every 30 seconds."""
    st.session_state.setdefault("snoozed", {})
    st.session_state.setdefault("notified", set())
    with st.expander("Reminder settings"):
        st.select_slider(
            "Remind me this long before a task starts", options=reminders.LEAD_OPTIONS, value=15,
            format_func=lambda minutes: f"{minutes} min", key="reminder_lead",
        )
        st.toggle("Pop-up alerts", value=True, key="reminder_toasts", help="Show a pop-up when a task becomes due")
        st.caption("Reminders appear while PawPal+ is open in your browser; the panel checks the time every 30 seconds.")
    _reminder_panel(owner_name)


@st.fragment(run_every="30s")
def _reminder_panel(owner_name: str) -> None:
    owner = st.session_state.directory.get(owner_name)
    if owner is None:
        return
    scheduler = Scheduler(owner)
    now = datetime.now()
    items = reminders.due_reminders(
        scheduler.get_all_tasks(), now, st.session_state.get("reminder_lead", 15), st.session_state.snoozed
    )
    if not items:
        st.caption(f"✅ Nothing due soon. Checked at {now:%H:%M}.")
        return
    for item in items:
        text_col, done_col, snooze_col = st.columns([5, 1.4, 2])
        text_col.markdown(f"{'⏰' if item.status == 'overdue' else '🔔'} **{item.message()}**")
        if done_col.button("Done", key=f"rem_done_{item.task.id}"):
            scheduler.complete_task(item.task)
            log.info("reminder: %r marked done", item.task.description)
            st.rerun()  # refresh the whole page so the schedule and stats update
        if snooze_col.button(f"Snooze {reminders.SNOOZE_MINUTES} min", key=f"rem_snooze_{item.task.id}"):
            st.session_state.snoozed[item.task.id] = reminders.snooze_until(now)
            log.info("reminder: %r snoozed", item.task.description)
            try:
                st.rerun(scope="fragment")  # only the reminder panel needs to refresh
            except Exception:  # not inside a fragment rerun (e.g. a full-page run): refresh the page instead
                st.rerun()
    if st.session_state.get("reminder_toasts", True):
        for item in items:
            if item.task.id not in st.session_state.notified:
                st.session_state.notified.add(item.task.id)
                st.toast(item.message(), icon="⏰" if item.status == "overdue" else "🔔")
