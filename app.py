import streamlit as st

from pawpal_system import BusyPeriod, Parent, Pet, Schedule, Scheduler, Task, TimePreference

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

if "pets" not in st.session_state:
    st.session_state.pets = []

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "schedule" not in st.session_state:
    st.session_state.schedule = None

# ---------------------------------------------------------------------------
# Section 1: Owner
# ---------------------------------------------------------------------------

st.subheader("Owner")

if st.session_state.owner is None:
    with st.form("owner_form"):
        owner_name = st.text_input("Name", value="Jordan")
        owner_email = st.text_input("Email", value="jordan@example.com")
        owner_location = st.text_input("Location", value="Portland, OR")
        pref_options = [p.value for p in TimePreference]
        selected_prefs = st.multiselect("Time preferences", pref_options, default=["morning", "evening"])
        submitted = st.form_submit_button("Save Owner")

    if submitted:
        prefs = [TimePreference(p) for p in selected_prefs]
        st.session_state.owner = Parent(
            name=owner_name,
            email=owner_email,
            location=owner_location,
            time_preferences=prefs,
        )
        st.rerun()
else:
    owner = st.session_state.owner
    st.success(f"Owner: **{owner.name}** — {owner.email} ({owner.location})")
    if st.button("Edit Owner"):
        st.session_state.owner = None
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Pets
# ---------------------------------------------------------------------------

st.subheader("Pets")

with st.form("pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    pet_breed = st.text_input("Breed", value="Shiba Inu")
    pet_weight = st.number_input("Weight (lbs)", min_value=0.1, max_value=300.0, value=20.5)
    add_pet = st.form_submit_button("Add Pet")

if add_pet:
    new_pet = Pet(name=pet_name, age=int(pet_age), breed=pet_breed, weight=float(pet_weight))
    st.session_state.pets = st.session_state.pets + [new_pet]
    if st.session_state.owner is not None:
        st.session_state.owner.pets = st.session_state.pets

if st.session_state.pets:
    for pet in st.session_state.pets:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{pet.name}** — {pet.breed}, {pet.age} yrs, {pet.weight} lbs")
        with col2:
            if st.button("Remove", key=f"remove_pet_{pet.name}"):
                pet.delete_pet()
                st.session_state.pets = [p for p in st.session_state.pets if p.name != pet.name]
                st.rerun()
else:
    st.info("No pets added yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Tasks
# ---------------------------------------------------------------------------

st.subheader("Tasks")

pet_names = [p.name for p in st.session_state.pets]

with st.form("task_form"):
    task_title = st.text_input("Task title", value="Morning walk")
    task_type = st.text_input("Task type", value="exercise")
    col1, col2, col3 = st.columns(3)
    with col1:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col2:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        daily_freq = st.number_input("Daily frequency", min_value=1, max_value=10, value=1)
    min_interval_hrs = st.number_input(
        "Min hours between occurrences (0 = no constraint)",
        min_value=0, max_value=24, value=0,
    )
    target_pet_name = st.selectbox("For pet", options=pet_names if pet_names else ["(add a pet first)"])
    add_task = st.form_submit_button("Add Task")

if add_task and pet_names:
    target_pet = next((p for p in st.session_state.pets if p.name == target_pet_name), None)
    new_task = Task(
        name=task_title,
        task_type=task_type,
        duration=int(duration),
        priority=priority,
        daily_frequency=int(daily_freq),
        min_interval=int(min_interval_hrs) * 60,
        target_pet=target_pet,
        responsible_parents=[st.session_state.owner] if st.session_state.owner else [],
    )
    if target_pet is not None:
        target_pet.tasks = target_pet.tasks + [new_task]
    st.session_state.tasks = st.session_state.tasks + [new_task]

if st.session_state.tasks:
    st.write("Current tasks:")
    for i, task in enumerate(st.session_state.tasks):
        col1, col2 = st.columns([5, 1])
        with col1:
            pet_label = task.target_pet.name if task.target_pet else "—"
            label = (
                f"{task.name} ({pet_label}) — {task.duration} min x{task.daily_frequency}"
                f" [{task.priority}]"
            )
            checked = st.checkbox(label, value=task.is_complete, key=f"task_{i}")
            if checked and not task.is_complete:
                task.mark_complete()
            elif not checked and task.is_complete:
                task.mark_incomplete()
        with col2:
            if st.button("Delete", key=f"delete_task_{i}"):
                task.delete()
                st.session_state.tasks = [t for t in st.session_state.tasks if t is not task]
                st.rerun()
else:
    st.info("No tasks added yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Generate Schedule
# ---------------------------------------------------------------------------

st.subheader("Generate Schedule")

if st.button("Generate Schedule"):
    if not st.session_state.owner:
        st.warning("Please add an owner before generating a schedule.")
    elif not st.session_state.pets:
        st.warning("Please add at least one pet before generating a schedule.")
    elif not st.session_state.tasks:
        st.warning("Please add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(
            target_pets=st.session_state.pets,
            parents=[st.session_state.owner],
            tasks=st.session_state.tasks,
        )
        st.session_state.schedule = scheduler.generate_schedule()

if st.session_state.schedule:
    schedule = st.session_state.schedule
    st.success(
        f"Schedule covers **{', '.join(schedule.effective_days)}** — "
        f"{schedule.start_time.strftime('%I:%M %p')} to {schedule.end_time.strftime('%I:%M %p')}"
    )
    st.markdown(f"**Tasks scheduled:** {schedule.calculate_task_count()} of {len(st.session_state.tasks)}")
    for task in schedule.tasks_scheduled:
        pet_label = task.target_pet.name if task.target_pet else "—"
        st.write(f"- **{task.name}** ({pet_label}) — {task.duration} min x{task.daily_frequency} [{task.priority}]")
    with st.expander("Scheduling reasoning"):
        st.text(schedule.generate_reasoning_text())
