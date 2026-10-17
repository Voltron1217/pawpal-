from datetime import datetime

from pawpal_system import Owner, Pet, Scheduler, Task

owner = Owner("Alice")
fluffy = Pet("Fluffy", age=3, breed="Persian")
spot = Pet("Spot", age=5, breed="Beagle")
owner.add_pet(fluffy)
owner.add_pet(spot)

today = datetime.now().replace(minute=0, second=0, microsecond=0)

# Three tasks across two pets, at different times
fluffy.add_task(Task("Feed Fluffy", today.replace(hour=8), "daily"))
spot.add_task(Task("Walk Spot", today.replace(hour=9), "once"))
fluffy.add_task(Task("Vet appointment for Fluffy", today.replace(hour=10), "weekly"))

scheduler = Scheduler(owner)

print("Today's Schedule")
for task in scheduler.tasks_on(today):
    status = "x" if task.completed else " "
    print(f"[{status}] {task.time:%Y-%m-%d %H:%M}  {task.pet_name:<8} {task.description} ({task.frequency})")

conflicts = scheduler.find_conflicts()
if conflicts:
    print("\nIssues found:")
    for a, b in conflicts:
        print(f"  {a.description} <-> {b.description} at {a.time:%H:%M}")
else:
    print("\nNo Issues found.")
