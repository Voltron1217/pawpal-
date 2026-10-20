# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Today's Schedule
[ ] 2026-10-17 08:00  Fluffy   Feed Fluffy (daily)
[ ] 2026-10-17 09:00  Spot     Walk Spot (once)
[ ] 2026-10-17 10:00  Fluffy   Vet appointment for Fluffy (weekly)

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```


## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

python -m pytest

# Run with coverage:
pytest --cov
```

Sample test output:

I give it a 4 out of 5 stars of my confidents level. 

```
platform darwin -- Python 3.12.7, pytest-7.4.4, pluggy-1.0.0
rootdir: /Users/voltron1217/pawpal-
plugins: anyio-4.2.0
collected 19 items                                                             

tests/test_pawpal.py ...................                                 [100%]

============================== 19 passed in 0.02s ==============================

```


## 📐 Smarter Scheduling

All of the scheduling logic lives in `Scheduler` and `Task` in [pawpal_system.py](pawpal_system.py). Run `python main.py` to see each feature in the terminal.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | Scheduler.sorted_by_time() | Orders tasks from every pet by their datetime using sorted(..., key=lambda t: t.time).
| Filtering | Scheduler.filter_tasks(pet_name, completed) | Filter by pet name, completion status, or both. Passing None skips that filter. The Streamlit app exposes it as Pet and Status dropdowns. |
| Recurring tasks | Task.next_occurrence(after), Scheduler.complete_task(task, now) | Completing between daily or weekly task adds a fresh copy to the same pet. The new due date is the completion day plus one `timedelta` step, keeping the original time of day.
| Conflict warnings | Scheduler.conflict_warnings(), Scheduler.warnings_for(task)` | Lightweight: returns warning strings instead of raising, and an empty list means no conflicts. conflict_warnings()covers the whole schedule. warnings_for() checks a task before it is added. |

### Tradeoff

Conflicts are reported but never resolved. The scheduler does not move, reject, or reprioritize tasks, because the owner knows context it cannot, and a warning can never crash the app or lose data.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
