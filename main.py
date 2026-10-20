from datetime import datetime

from pawpal_system import Owner, Pet, Scheduler, Task

owner = Owner("Alice")
fluffy = Pet("Fluffy", age=3, breed="Persian")
spot = Pet("Spot", age=5, breed="Beagle")
owner.add_pet(fluffy)
owner.add_pet(spot)

today = datetime.now().replace(minute=0, second=0, microsecond=0)

# Tasks are added deliberately out of chronological order
fluffy.add_task(Task("Vet appointment for Fluffy", today.replace(hour=14), "weekly"))
spot.add_task(Task("Evening walk", today.replace(hour=18), "daily"))
fluffy.add_task(Task("Feed Fluffy", today.replace(hour=8), "daily"))
spot.add_task(Task("Give medication", today.replace(hour=12), "once"))
spot.add_task(Task("Walk Spot", today.replace(hour=9), "once"))
fluffy.add_task(Task("Brush Fluffy", today.replace(hour=12, minute=15), "once"))  # overlaps medication

# Two tasks at exactly the same time: same pet, and different pets
fluffy.add_task(Task("Grooming", today.replace(hour=16), "once"))
fluffy.add_task(Task("Give flea treatment", today.replace(hour=16), "once"))
spot.add_task(Task("Training class", today.replace(hour=16), "once"))

scheduler = Scheduler(owner)


def show(title: str, tasks: list[Task]) -> None:
    print(f"\n{title}")
    if not tasks:
        print("  (none)")
    for task in tasks:
        status = "x" if task.completed else " "
        print(f"  [{status}] {task.time:%H:%M}  {task.pet_name:<8} {task.description} ({task.frequency})")


show("Tasks in the order they were added", scheduler.get_all_tasks())
show("Sorted by time", scheduler.sorted_by_time())

# Complete a one-off and a recurring task so the status filters have something to show
by_name = {t.description: t for t in scheduler.get_all_tasks()}
scheduler.complete_task(by_name["Walk Spot"])
nxt = scheduler.complete_task(by_name["Feed Fluffy"])
print(f"\nCompleted 'Walk Spot' and 'Feed Fluffy'; next Feed Fluffy is {nxt.time:%Y-%m-%d %H:%M}")

show("Fluffy's tasks (sorted)", scheduler.sorted_by_time(scheduler.filter_tasks(pet_name="Fluffy")))
show("Spot's tasks (sorted)", scheduler.sorted_by_time(scheduler.filter_tasks(pet_name="Spot")))
show("Pending only", scheduler.sorted_by_time(scheduler.filter_tasks(completed=False)))
show("Completed only", scheduler.sorted_by_time(scheduler.filter_tasks(completed=True)))
show("Spot's pending tasks", scheduler.sorted_by_time(scheduler.filter_tasks(pet_name="Spot", completed=False)))

warnings = scheduler.conflict_warnings()
print()
if warnings:
    for w in warnings:
        print(w)
else:
    print("No conflicts found.")

# Check a task before adding it; the program keeps running either way
candidate = Task("Bath time", today.replace(hour=16), "once", pet_name="Spot")
print("\nChecking 'Bath time' at 16:00 before adding:")
for w in scheduler.warnings_for(candidate) or ["No conflicts."]:
    print(" ", w)
