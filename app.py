from datetime import datetime

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )


st.divider()

# Keep one Owner alive across Streamlit reruns
if "owner" not in st.session_state:
    st.session_state.owner = Owner("")
owner = st.session_state.owner
scheduler = Scheduler(owner)

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)


# step 3 
st.subheader("add pet")
with st.form("add_pet", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    pet_name = c1.text_input("Pet name")
    age = c2.number_input("Age", min_value=0, max_value=40, value=1)
    breed = c3.text_input("Breed")
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Pet name is required.")
        elif owner.get_pet(pet_name.strip()):
            st.error(f"{pet_name} already exists.")
        else:
            owner.add_pet(Pet(pet_name.strip(), int(age), breed.strip()))

if owner.pets:
    st.write("Pets: " + ", ".join(p.name for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.subheader("add task")
if owner.pets:
    with st.form("add_task", clear_on_submit=True):
        target = st.selectbox("Pet", [p.name for p in owner.pets])
        description = st.text_input("Task", value="Morning walk")
        c1, c2, c3 = st.columns(3)
        day = c1.date_input("Date", value=datetime.now().date())
        at = c2.time_input("Time", value=datetime.now().replace(minute=0).time())
        frequency = c3.selectbox("Frequency", ["once", "daily", "weekly"])
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=480, value=30, step=5)
        if st.form_submit_button("Add task"):
            new_task = Task(description, datetime.combine(day, at), frequency, duration_minutes=int(duration))
            new_task.pet_name = target
            clashes = scheduler.warnings_for(new_task)  # check before adding
            owner.get_pet(target).add_task(new_task)
            st.success(f"Added '{description}' for {target} at {new_task.time:%a %H:%M}.")
            for message in clashes:
                st.warning(message)
else:
    st.caption("Add a pet first.")

st.divider()

st.subheader("Schedule")
f1, f2 = st.columns(2)
pet_filter = f1.selectbox("Pet", ["All"] + [p.name for p in owner.pets])
status_filter = f2.selectbox("Status", ["All", "Pending", "Completed"])
tasks = scheduler.sorted_by_time(
    scheduler.filter_tasks(
        pet_name=None if pet_filter == "All" else pet_filter,
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
    )
)

warnings = scheduler.conflict_warnings()
if warnings:
    st.warning(f"{len(warnings)} scheduling conflict(s) found. Review them below the table.")
elif scheduler.get_all_tasks():
    st.success("No scheduling conflicts.")

if tasks:
    st.table(
        [
            {
                "Status": "Done" if t.completed else "Pending",
                "Date": f"{t.time:%Y-%m-%d}",
                "Start": f"{t.time:%H:%M}",
                "End": f"{t.end:%H:%M}",
                "Pet": t.pet_name,
                "Task": t.description,
                "Repeats": t.frequency,
            }
            for t in tasks
        ]
    )
else:
    st.info("No matching tasks.")

for message in warnings:
    st.warning(message)

st.subheader("Mark task done")
pending = scheduler.sorted_by_time(scheduler.filter_tasks(completed=False))
if pending:
    labels = {t.id: f"{t.time:%Y-%m-%d %H:%M} - {t.pet_name}: {t.description}" for t in pending}
    chosen = st.selectbox("Pending task", list(labels), format_func=labels.get)
    if st.button("Mark done"):
        task = next(t for t in pending if t.id == chosen)
        nxt = scheduler.complete_task(task)
        if nxt:
            st.session_state.flash = f"Done! Next '{task.description}' is scheduled for {nxt.time:%a %Y-%m-%d %H:%M}."
        else:
            st.session_state.flash = f"Done! '{task.description}' completed."
        st.rerun()
else:
    st.caption("Nothing pending.")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))
