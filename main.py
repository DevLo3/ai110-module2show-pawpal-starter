"""PawPal+ demo script: builds a sample owner, pets, tasks, and prints today's schedule."""

from datetime import date, time

from pawpal_system import (
    BusyPeriod,
    Parent,
    Pet,
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
    responsible_parents=[jordan],
)

mochi.tasks   = [morning_walk, feeding, grooming]
biscuit.tasks = [litter_box, playtime, vet_meds]

all_tasks = mochi.tasks + biscuit.tasks

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
    pet_name = task.target_pet.name if task.target_pet else "N/A"
    status = "[DONE]" if task.is_complete else "[ ]"
    print(f"  {status} [{task.priority.upper():6}]  {task.name} ({pet_name}) — {task.duration} min x{task.daily_frequency}")
print()
print(schedule.generate_reasoning_text())
print("=" * 50)
