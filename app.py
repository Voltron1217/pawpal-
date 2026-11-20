import os
from datetime import datetime, timedelta

import streamlit as st

import actions
import rag
import routines
import widgets
from breeds import BREEDS, MIXED
from pawpal_log import get_logger
from walk_animation import STATUS_WIDGET_CSS, loading_html
from pawpal_system import FREQUENCIES, OwnerDirectory, Pet, Task, Scheduler

# Streamlit only loads secrets.toml lazily, so copy API keys into the environment for rag.py.
for _name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
    try:
        if _name in st.secrets and _name not in os.environ:
            os.environ[_name] = st.secrets[_name]
    except Exception:  # no secrets file
        pass

log = get_logger("pawpal.app")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.markdown(STATUS_WIDGET_CSS, unsafe_allow_html=True)

st.title("🐾 PawPal+")

PANEL_CSS = """
<style>
div[data-testid="stColumn"]:has(#ask-panel-marker),
div[data-testid="column"]:has(#ask-panel-marker) {
    position: sticky;
    top: 4rem;
    align-self: flex-start;
    max-height: calc(100vh - 5rem);
    overflow-y: auto;
    padding: 1rem;
    border: 1px solid rgba(128, 128, 128, 0.35);
    border-radius: 0.75rem;
}
@media (max-width: 900px) {
    div[data-testid="stColumn"]:has(#ask-panel-marker),
    div[data-testid="column"]:has(#ask-panel-marker) { position: static; max-height: none; }
}
</style>
<div id="ask-panel-marker"></div>
"""

left, right = st.columns([2, 1], gap="large")

with left:

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

    # Keep every owner (and their pets) alive across Streamlit reruns
    if "directory" not in st.session_state:
        st.session_state.directory = OwnerDirectory()
    directory = st.session_state.directory

    def clear_owner_state() -> None:
        """Drop anything half-finished that belonged to the previous owner."""
        for stale in ("pending_action", "ask_flash", "flash", "routine_pet_request"):
            st.session_state.pop(stale, None)
        st.session_state.ask_q = ""

    def on_owner_change() -> None:
        clear_owner_state()
        log.info("switched owner to %s", st.session_state.get("current_owner"))

    st.subheader("Owner")
    if "owner_request" in st.session_state:  # a newly added owner becomes the selected one
        st.session_state.current_owner = st.session_state.pop("owner_request")
    if directory.names():
        st.selectbox(
            "Who is using PawPal+?", directory.names(), key="current_owner", on_change=on_owner_change,
            help="Each owner has their own pets and tasks.",
        )
    with st.expander("Add a new owner", expanded=not directory.names()):
        with st.form("add_owner", clear_on_submit=True):
            new_owner_name = st.text_input("Owner name")
            if st.form_submit_button("Add owner"):
                try:
                    added = directory.add(new_owner_name)
                    st.session_state.owner_request = added.name
                    clear_owner_state()
                    st.rerun()
                except ValueError as exc:
                    log.warning("add owner rejected: %s", exc)
                    st.error(f"Could not add owner: {exc}")
    if not directory.names():
        st.info("Add an owner to get started. Each owner keeps their own pets and tasks.")
        st.stop()
    current = st.session_state.get("current_owner")
    if current not in directory:
        current = directory.names()[0]
        st.session_state.current_owner = current
    owner = directory.get(current)
    scheduler = Scheduler(owner)
    st.caption(f"Showing {owner.name}'s pets and tasks.")

    st.subheader("🔔 Reminders")
    widgets.render_reminders(owner.name)


    # step 3 
    st.subheader("add pet")
    # Species sits outside the form so the breed list below updates as soon as it changes.
    species = st.radio("Species", list(BREEDS), horizontal=True)
    with st.form("add_pet", clear_on_submit=True):
        c1, c2 = st.columns(2)
        pet_name = c1.text_input("Pet name")
        age = c2.number_input("Age", min_value=0, max_value=40, value=1)
        breed_choice = st.selectbox(
            f"{species} breed",
            BREEDS[species] + [MIXED],
            index=None,
            placeholder="Scroll or start typing to search breeds...",
        )
        other_breed = st.text_input("Breed not listed? Type it here (optional)")
        if st.form_submit_button("Add pet"):
            breed = other_breed.strip() or breed_choice or MIXED
            if not pet_name.strip():
                st.error("Pet name is required.")
            elif owner.get_pet(pet_name.strip()):
                st.error(f"{pet_name} already exists.")
            else:
                try:
                    owner.add_pet(Pet(pet_name.strip(), int(age), breed, species=species))
                    st.success(f"Added {pet_name.strip()} the {breed} ({species.lower()}).")
                except ValueError as exc:
                    log.warning("add pet rejected: %s", exc)
                    st.error(f"Could not add pet: {exc}")
                except Exception:
                    log.exception("add pet failed unexpectedly")
                    st.error("Something went wrong adding the pet. Please try again.")

    if owner.pets:
        st.write(f"{owner.name}'s pets: " + ", ".join(p.name for p in owner.pets))
    else:
        st.info("No pets yet. Add one above.")

    st.subheader("Pet profile and notes")
    st.caption("Anything you save here is used by Ask PawPal to answer questions about your specific pet.")
    if owner.pets:
        prof_name = st.selectbox("Pet", [p.name for p in owner.pets], key=f"prof_pet_{owner.name}")
        prof = owner.get_pet(prof_name)
        st.caption(f"{prof.name}: {prof.species or 'pet'}, {prof.breed}, {prof.age} yr, life stage: {prof.life_stage}")
        with st.form(f"profile_{prof.name}"):
            pc1, pc2 = st.columns(2)
            diet = pc1.text_input("Diet", value=prof.diet, placeholder="e.g. 1 cup kibble twice a day")
            weight = pc2.number_input("Weight", min_value=0.0, max_value=500.0, value=float(prof.weight), step=0.5)
            medications = st.text_input("Medications", value=prof.medications, placeholder="e.g. Heartworm pill monthly")
            allergies = st.text_input("Allergies", value=prof.allergies, placeholder="e.g. Chicken")
            if st.form_submit_button("Save profile"):
                prof.diet, prof.medications, prof.allergies = diet.strip(), medications.strip(), allergies.strip()
                prof.weight = float(weight)
                log.info("profile saved for %s", prof.name)
                st.success(f"Saved {prof.name}'s profile.")
        with st.form(f"note_{prof.name}", clear_on_submit=True):
            note_text = st.text_area("Add a note", placeholder="e.g. Scared of thunderstorms. Gets carsick.", max_chars=500)
            if st.form_submit_button("Add note"):
                try:
                    prof.add_note(note_text)
                    st.success("Note saved.")
                except ValueError as exc:
                    log.warning("note rejected: %s", exc)
                    st.error(f"Could not save note: {exc}")
        for saved in prof.notes:
            st.markdown(f"- {saved}")
    else:
        st.caption("Add a pet first.")

    st.subheader("Starter routine")
    st.caption("A suggested set of daily care tasks for the pet's species and age. Edit anything, untick what you don't want, then add.")
    if owner.pets:
        if "routine_pet_request" in st.session_state:  # set by Ask PawPal before this widget is created
            st.session_state[f"routine_pet_{owner.name}"] = st.session_state.pop("routine_pet_request")
        r_name = st.selectbox("Pet", [p.name for p in owner.pets], key=f"routine_pet_{owner.name}")
        r_pet = owner.get_pet(r_name)
        r_start = st.date_input("First day", value=datetime.now().date() + timedelta(days=1), key="routine_start")
        r_items = routines.starter_routine(r_pet)
        if not r_items:
            st.info(f"No starter routine for {r_pet.name} yet (species: {r_pet.species or 'unknown'}).")
        else:
            st.caption(f"Suggested for {r_pet.name}, a {r_pet.life_stage} {r_pet.species.lower()}.")
            r_rows = [
                {"Add": True, "Task": i.description, "Time": f"{i.clock:%H:%M}", "Repeats": i.frequency,
                 "Minutes": i.duration_minutes, "Day offset": i.day_offset}
                for i in r_items
            ]
            edited = st.data_editor(
                r_rows,
                key=f"routine_editor_{owner.name}_{r_pet.name}_{r_pet.life_stage}",
                hide_index=True,
                column_config={
                    "Add": st.column_config.CheckboxColumn("Add?"),
                    "Time": st.column_config.TextColumn("Time (HH:MM)"),
                    "Repeats": st.column_config.SelectboxColumn("Repeats", options=list(FREQUENCIES)),
                    "Minutes": st.column_config.NumberColumn("Minutes", min_value=1, max_value=1440, step=5),
                    "Day offset": st.column_config.NumberColumn("Starts +days"),
                },
                disabled=["Day offset"],
            )
            if routines.routine_note(r_pet):
                st.caption(routines.routine_note(r_pet))
            if st.button("Add selected tasks", key="routine_add"):
                try:
                    rows_now = edited if isinstance(edited, list) else edited.to_dict("records")
                    result = routines.add_routine(r_pet, scheduler, rows_now, r_start)
                    if result.added:
                        st.success(f"Added {len(result.added)} task(s) for {r_pet.name}, starting {r_start:%a %b %d}.")
                    for line in result.skipped:
                        st.caption(f"Skipped - {line}")
                    for message in result.warnings:
                        st.warning(message)
                except Exception:
                    log.exception("adding routine failed")
                    st.error("Something went wrong adding the routine. Please try again.")
    else:
        st.caption("Add a pet first.")

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
                try:
                    new_task = Task(description.strip(), datetime.combine(day, at), frequency, duration_minutes=int(duration))
                    new_task.pet_name = target
                    clashes = scheduler.warnings_for(new_task)  # check before adding
                    owner.get_pet(target).add_task(new_task)
                    st.success(f"Added '{new_task.description}' for {target} at {new_task.time:%a %H:%M}.")
                    for message in clashes:
                        st.warning(message)
                except ValueError as exc:
                    log.warning("add task rejected: %s", exc)
                    st.error(f"Could not add task: {exc}")
                except Exception:
                    log.exception("add task failed unexpectedly")
                    st.error("Something went wrong adding the task. Please try again.")
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
            try:
                nxt = scheduler.complete_task(task)
            except Exception:
                log.exception("mark done failed")
                st.error("Could not mark that task done. Please try again.")
                st.stop()
            if nxt:
                st.session_state.flash = f"Done! Next '{task.description}' is scheduled for {nxt.time:%a %Y-%m-%d %H:%M}."
            else:
                st.session_state.flash = f"Done! '{task.description}' completed."
            st.rerun()
    else:
        st.caption("Nothing pending.")

    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

    st.divider()
    widgets.render_progress(owner)


with right:
    st.markdown(PANEL_CSS, unsafe_allow_html=True)
    st.subheader("Ask PawPal")
    st.caption("Answers come from the pet-care guide in knowledge/, plus your pet's schedule.")

    EXAMPLES = {
        "Dog": [
            "How often should I walk my dog?",
            "How many times a day should I feed my dog?",
            "How often should I trim my dog's nails?",
            "When does my dog need a vet visit?",
            "Can I give medication at the same time as a walk?",
        ],
        "Cat": [
            "How often should I brush my cat?",
            "How many meals does a kitten need?",
            "How often should I scoop the litter box?",
            "How much should I play with my cat each day?",
            "How often should an older cat see the vet?",
        ],
        "Rabbit": [
            "How much hay should my rabbit eat?",
            "How long should my rabbit be out of its cage each day?",
            "What if my rabbit stops eating?",
        ],
        "Bird": [
            "How often should I clean my bird's cage?",
            "How much sleep does my bird need?",
            "What foods are toxic to birds?",
        ],
        "Hamster": [
            "When should I feed my hamster?",
            "How often should I clean my hamster's cage?",
        ],
        "Guinea Pig": [
            "Why does my guinea pig need vitamin C?",
            "How much floor time should my guinea pig get?",
        ],
        "Turtle": [
            "How long should my turtle's UVB light be on?",
            "How often should I feed my turtle?",
            "How often should I change my turtle's water?",
        ],
        "": [
            "What should I do if my pet is vomiting?",
            "How should I schedule medication?",
            "How do I care for a senior pet?",
        ],
    }


    def use_example(text: str) -> None:
        st.session_state.ask_q = text
        st.session_state.ask_now = True


    def confirm_action() -> None:
        """Add the proposed task, but only because the owner pressed Confirm."""
        proposal = st.session_state.pop("pending_action", None)
        if proposal is None:
            return
        try:
            current = st.session_state.directory.get(st.session_state.current_owner)
            task = proposal.to_task()
            clashes = Scheduler(current).warnings_for(task)
            current.get_pet(proposal.pet_name).add_task(task)
            log.info("action confirmed: %r for %s", proposal.description, proposal.pet_name)
            st.session_state.ask_flash = (f"Added {proposal.description} for {proposal.pet_name} at {task.time:%a %H:%M}.", clashes)
        except Exception:
            log.exception("confirming action failed")
            st.session_state.ask_flash = ("Sorry, I couldn't add that task. Please use the Add task form.", [])


    def cancel_action() -> None:
        st.session_state.pop("pending_action", None)
        log.info("action cancelled")


    if "ask_flash" in st.session_state:
        flash_text, flash_warnings = st.session_state.pop("ask_flash")
        st.success(flash_text)
        for flash_warning in flash_warnings:
            st.warning(flash_warning)


    if owner.pets:
        who = st.selectbox("About which pet?", [p.name for p in owner.pets], key=f"ask_pet_{owner.name}")
        chosen_pet = owner.get_pet(who)
        q_col, ask_col = st.columns([4, 1], vertical_alignment="bottom")
        q_col.text_input("Your question", key="ask_q", placeholder="Type a question or tap an example below")
        ask_clicked = ask_col.button("Ask", type="primary", use_container_width=True)
        answer_area = st.container()  # the answer renders here, right under the question box
        st.caption("Try one of these:")
        personal = [
            f"What medications is {chosen_pet.name} on?",
            f"Is {chosen_pet.name} allergic to anything?",
            f"Is {chosen_pet.name} a senior {chosen_pet.species.lower() or 'pet'}?",
        ]
        if chosen_pet.breed and chosen_pet.breed != MIXED:
            personal.insert(0, f"What should I know about caring for a {chosen_pet.breed}?")
        st.caption(f"About {chosen_pet.name}:")
        for example in personal:
            st.button(example, key=f"ex_{chosen_pet.name}_{example}", on_click=use_example, args=(example,))
        st.caption("Ask me to change the schedule (I'll ask you to confirm):")
        for example in (f"Add a 6pm walk for {chosen_pet.name} every day", f"Set up a starter routine for {chosen_pet.name}"):
            st.button(example, key=f"ex_{chosen_pet.name}_{example}", on_click=use_example, args=(example,))
        st.caption("General care:")
        for example in EXAMPLES.get(chosen_pet.species, []) + EXAMPLES[""]:
            st.button(example, key=f"ex_{example}", on_click=use_example, args=(example,))
        asked = ask_clicked or st.session_state.pop("ask_now", False)
        question = st.session_state.get("ask_q", "").strip()
        with answer_area:
            if asked and not question:
                st.warning("Please type a question first.")
            if asked and question:
                walking = st.empty()
                walking.markdown(loading_html(), unsafe_allow_html=True)
                try:
                    action = actions.interpret(question, owner, chosen_pet)
                    answered = None if action is not None else rag.answer(question, scheduler, chosen_pet)
                finally:
                    walking.empty()
                st.markdown(f"**Q:** {question}")
                if action is not None:
                    st.session_state.pop("pending_action", None)
                    if action.kind == "error":
                        st.warning(action.message)
                    elif action.kind == "routine":
                        st.session_state.routine_pet_request = action.pet.name
                        st.session_state.ask_flash = (
                            f"I opened a starter routine for {action.pet.name} in the 'Starter routine' section. "
                            "Review it, edit anything, and add the tasks you want.", [])
                        st.rerun()
                    else:
                        st.session_state.pending_action = action.proposal
                else:
                    text, sources, used_llm = answered
                    st.write(text)
                    st.caption("Sources: " + "; ".join(sources) if sources else "No matching guidance found.")
                    if not used_llm and sources:
                        st.info("Showing retrieved passages only. Set GEMINI_API_KEY (or ANTHROPIC_API_KEY) for written answers.")
            if "pending_action" in st.session_state:
                pending = st.session_state.pending_action
                with st.container(border=True):
                    st.markdown("**Add this to the schedule?**")
                    st.markdown(pending.summary())
                    if pending.is_in_past():
                        st.caption("That time has already passed, so the task will show as overdue.")
                    for clash in Scheduler(owner).warnings_for(pending.to_task()):
                        st.warning(clash)
                    confirm_col, cancel_col = st.columns(2)
                    confirm_col.button("Confirm", type="primary", on_click=confirm_action, key="confirm_action")
                    cancel_col.button("Cancel", on_click=cancel_action, key="cancel_action")
    else:
        st.caption("Add a pet first. Then you can ask questions like 'How often should I walk my dog?'")
