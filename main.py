"""PawPal+ demo script: builds a sample owner, pets, tasks, and prints today's schedule.

Also demonstrates Task sorting by scheduled_time and filtering by pet/completion status.
"""

from datetime import date, time

from pawpal_system import (
    BusyPeriod,
    Parent,
    Pet,
    Recurrence,
    Schedule,
    Scheduler,
    Task,
    TimePreference,
)

# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

jordan = Parent(
    name="Jordan",
    email="jordan@example.com",
    location="Portland, OR",
    time_preferences=[TimePreference.MORNING, TimePreference.EVENING],
)

# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------

mochi = Pet(
    name="Mochi",
    age=3,
    breed="Shiba Inu",
    weight=20.5,
    birthday=date(2022, 4, 10),
)

biscuit = Pet(
    name="Biscuit",
    age=7,
    breed="Tabby Cat",
    weight=9.2,
    birthday=date(2018, 11, 2),
)

jordan.pets = [mochi, biscuit]

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

morning_walk = Task(
    name="Morning Walk",
    task_type="exercise",
    duration=30,
    priority="high",
    target_pet=mochi,
    daily_frequency=1,
    responsible_parents=[jordan],
)

feeding = Task(
    name="Feeding",
    task_type="nutrition",
    duration=10,
    priority="high",
    target_pet=mochi,
    daily_frequency=2,
    min_interval=480,   # at least 8 hours between feedings
    recurrence=Recurrence.DAILY,
    responsible_parents=[jordan],
)

grooming = Task(
    name="Grooming",
    task_type="hygiene",
    duration=20,
    priority="medium",
    target_pet=mochi,
    daily_frequency=1,
    responsible_parents=[jordan],
)

litter_box = Task(
    name="Litter Box Cleaning",
    task_type="hygiene",
    duration=10,
    priority="high",
    target_pet=biscuit,
    daily_frequency=1,
    responsible_parents=[jordan],
)

playtime = Task(
    name="Playtime",
    task_type="enrichment",
    duration=25,
    priority="medium",
    target_pet=biscuit,
    daily_frequency=1,
    responsible_parents=[jordan],
)

vet_meds = Task(
    name="Vet Medication",
    task_type="health",
    duration=5,
    priority="high",
    target_pet=biscuit,
    daily_frequency=2,
    min_interval=720,   # at least 12 hours between doses
    recurrence=Recurrence.DAILY,
    responsible_parents=[jordan],
)

mochi.tasks   = [morning_walk, feeding, grooming]
biscuit.tasks = [litter_box, playtime, vet_meds]

# Tasks added out of order (low → medium → high, mixed pets) to show that the
# Scheduler reorders them correctly and scheduled_time sorting works end-to-end.
all_tasks = [grooming, playtime, litter_box, feeding, morning_walk, vet_meds]

# ---------------------------------------------------------------------------
# Busy periods
# ---------------------------------------------------------------------------

work_hours = BusyPeriod(
    name="Work",
    start_time=time(9, 0),
    duration=240,  # 9am–1pm
    effective_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    owners=[jordan],
)

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

scheduler = Scheduler(
    target_pets=[mochi, biscuit],
    parents=[jordan],
    tasks=all_tasks,
    busy_periods=[work_hours],
)

schedule: Schedule = scheduler.generate_schedule()

# ---------------------------------------------------------------------------
# Print Today's Schedule
# ---------------------------------------------------------------------------

print("=" * 50)
print("          PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 50)
print(f"Owner  : {jordan.name}")
print(f"Pets   : {', '.join(p.name for p in jordan.pets)}")
window_start = schedule.start_time.strftime("%I:%M %p")
window_end = schedule.end_time.strftime("%I:%M %p")
print(f"Window : {window_start} – {window_end}")
print(f"Days   : {', '.join(schedule.effective_days)}")
print()
print(f"Tasks Scheduled ({schedule.calculate_task_count()} of {len(all_tasks)} total):")
print("-" * 50)
for task in schedule.tasks_scheduled:
    pet_label = task.target_pet.name if task.target_pet else "N/A"
    print(
        f"  {'[DONE]' if task.is_complete else '[    ]'} [{task.priority.upper():6}]"
        f"  {task.name} ({pet_label})"
        f" — {task.duration} min x{task.daily_frequency}"
        f"{f' [{task.recurrence.value}]' if task.recurrence else ''}"
    )
print()
print(schedule.generate_reasoning_text())
print("=" * 50)

# ---------------------------------------------------------------------------
# Demo: sort scheduled tasks by scheduled_time (uses Task.__lt__)
# ---------------------------------------------------------------------------

print()
print("=" * 50)
print("  SORTED BY SCHEDULED TIME (Task.__lt__)")
print("=" * 50)
for task in sorted(schedule.tasks_scheduled):
    pet_label = task.target_pet.name if task.target_pet else "N/A"
    time_label = (
        task.scheduled_time.strftime("%I:%M %p")
        if task.scheduled_time else "unscheduled"
    )
    print(f"  {time_label}  [{task.priority.upper():6}]  {task.name} ({pet_label})")

# ---------------------------------------------------------------------------
# Demo: recurrence — mark_complete() on a recurring task spawns the next one
# ---------------------------------------------------------------------------

print()
print("=" * 50)
print("  RECURRENCE DEMO")
print("=" * 50)

spawned: list[Task] = []
for task in schedule.tasks_scheduled:
    next_occ = task.mark_complete()
    if next_occ is not None:
        spawned.append(next_occ)
        if next_occ.target_pet is not None:
            next_occ.target_pet.tasks = next_occ.target_pet.tasks + [next_occ]

print(f"Marked all {schedule.calculate_task_count()} tasks complete.")
print(f"Spawned {len(spawned)} next-occurrence task(s):\n")
for task in spawned:
    pet_label = task.target_pet.name if task.target_pet else "N/A"
    print(
        f"  [ ] [{task.priority.upper():6}]  {task.name} ({pet_label})"
        f" — {task.recurrence.value}, next due {task.next_due}"
    )

# ---------------------------------------------------------------------------
# Demo: filter_tasks — by pet name and by completion status
# ---------------------------------------------------------------------------

print()
print("=" * 50)
print("  FILTER: pet_name='Mochi'")
print("=" * 50)
for task in schedule.filter_tasks(pet_name="Mochi"):
    print(
        f"  {'[DONE]' if task.is_complete else '[    ]'}"
        f"  {task.name} — {task.duration} min [{task.priority}]"
    )

print()
print("=" * 50)
print("  FILTER: is_complete=False  (pending tasks only)")
print("=" * 50)
for task in schedule.filter_tasks(is_complete=False):
    pet_label = task.target_pet.name if task.target_pet else "N/A"
    print(f"  [    ]  {task.name} ({pet_label}) — {task.duration} min [{task.priority}]")

print()
print("=" * 50)
print("  FILTER: pet_name='Biscuit' AND is_complete=False")
print("=" * 50)
for task in schedule.filter_tasks(is_complete=False, pet_name="Biscuit"):
    print(f"  [    ]  {task.name} — {task.duration} min [{task.priority}]")
print("=" * 50)

# ---------------------------------------------------------------------------
# Demo: conflict detection
# Two tasks are manually pre-timed so they overlap with already-placed slots.
#
#   bath_time  : 06:45 AM for 30 min  → ends 07:15 AM
#                conflicts Morning Walk (06:50 AM – 07:20 AM)
#
#   extra_meds : 06:00 AM for 20 min  → ends 06:20 AM
#                conflicts Vet Medication (06:00 AM – 06:05 AM) AND
#                          Litter Box Cleaning (06:05 AM – 06:15 AM)
# ---------------------------------------------------------------------------

bath_time = Task(
    name="Bath Time",
    task_type="hygiene",
    duration=30,
    priority="medium",
    target_pet=mochi,
    daily_frequency=1,
    responsible_parents=[jordan],
    scheduled_time=time(6, 45),
)

extra_meds = Task(
    name="Extra Medication",
    task_type="health",
    duration=20,
    priority="high",
    target_pet=biscuit,
    daily_frequency=1,
    responsible_parents=[jordan],
    scheduled_time=time(6, 0),
)

conflict_warnings = scheduler.detect_conflicts(
    schedule.tasks_scheduled + [bath_time, extra_meds]
)

print()
print("=" * 50)
print("  CONFLICT DETECTION")
print("=" * 50)
if conflict_warnings:
    for warning in conflict_warnings:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")
print("=" * 50)
