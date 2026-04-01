from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, time
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------

class TimePreference(Enum):
    MORNING = "morning"
    MIDDAY = "midday"
    EVENING = "evening"
    NIGHT = "night"


# Maps each TimePreference to a concrete (start, end) time window for use by the Scheduler.
TIME_PREFERENCE_WINDOWS: dict[TimePreference, tuple[time, time]] = {
    TimePreference.MORNING: (time(6, 0),  time(12, 0)),
    TimePreference.MIDDAY:  (time(12, 0), time(15, 0)),
    TimePreference.EVENING: (time(15, 0), time(20, 0)),
    TimePreference.NIGHT:   (time(20, 0), time(23, 59)),
}

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Core data classes
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    age: int
    breed: str
    weight: float
    picture: Optional[str] = None
    birthday: Optional[date] = None
    tasks: list[Task] = field(default_factory=list)

    def edit_pet(self, **kwargs) -> None:
        """Update one or more pet attributes by keyword."""
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Pet has no attribute '{key}'")
            setattr(self, key, value)

    def delete_pet(self) -> None:
        """Detach all tasks from this pet and clear the task list."""
        for task in self.tasks:
            task.target_pet = None
        self.tasks.clear()


@dataclass
class Parent:
    name: str
    email: str
    location: str
    time_preferences: list[TimePreference] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)
    # At least one parent must remain active at all times.
    active: bool = True

    def edit(self, **kwargs) -> None:
        """Update one or more parent attributes by keyword."""
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Parent has no attribute '{key}'")
            setattr(self, key, value)

    def deactivate(self) -> None:
        """Mark this parent as inactive."""
        self.active = False


@dataclass
class Task:
    name: str
    task_type: str          # 'type' is a Python builtin, so task_type is used here
    duration: int           # minutes per occurrence
    priority: str           # "low" | "medium" | "high"
    target_pet: Optional[Pet] = None
    daily_frequency: int = 1
    responsible_parents: list[Parent] = field(default_factory=list)

    def edit(self, **kwargs) -> None:
        """Update one or more task attributes by keyword."""
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Task has no attribute '{key}'")
            setattr(self, key, value)

    def delete(self) -> None:
        """Remove this task from its pet's task list and clear parent assignments."""
        if self.target_pet is not None and self in self.target_pet.tasks:
            self.target_pet.tasks.remove(self)
            self.target_pet = None
        self.responsible_parents.clear()

    def duplicate(self) -> Task:
        """Return a new Task with the same attributes (shallow-copies the parents list)."""
        return replace(self, responsible_parents=list(self.responsible_parents))


@dataclass
class BusyPeriod:
    """
    A time window when the owner(s) are unavailable for pet care.
    The Scheduler avoids placing tasks inside busy periods.
    """
    name: str
    start_time: time
    duration: int           # minutes
    effective_days: list[str]   # e.g. ["Monday", "Wednesday"]
    owners: list[Parent] = field(default_factory=list)

    def edit_busy_period(self, **kwargs) -> None:
        """Update one or more busy period attributes by keyword."""
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"BusyPeriod has no attribute '{key}'")
            setattr(self, key, value)

    def delete_busy_period(self) -> None:
        """Clear owner assignments from this busy period."""
        self.owners.clear()


# ---------------------------------------------------------------------------
# Schedule (output data object)
# ---------------------------------------------------------------------------

@dataclass
class Schedule:
    is_24hr_format: bool
    effective_days: list[str]   # e.g. ["Monday", "Wednesday", "Friday"]
    start_time: time
    end_time: time
    tasks_scheduled: list[Task] = field(default_factory=list)
    reasoning: str = ""

    def edit(self, **kwargs) -> None:
        """Update one or more schedule attributes by keyword."""
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Schedule has no attribute '{key}'")
            setattr(self, key, value)

    def delete(self) -> None:
        """Clear all scheduled tasks and reasoning from this schedule."""
        self.tasks_scheduled.clear()
        self.reasoning = ""

    def calculate_task_count(self) -> int:
        """Return the total number of tasks in this schedule."""
        return len(self.tasks_scheduled)

    def generate_reasoning_text(self) -> str:
        """Return the human-readable explanation produced during scheduling."""
        return self.reasoning


# ---------------------------------------------------------------------------
# Scheduler (logic engine)
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Accepts pets, parents, tasks, and busy periods as inputs and produces a Schedule.
    Keeps scheduling logic separate from the Schedule data object.
    """

    def __init__(
        self,
        target_pets: list[Pet],
        parents: list[Parent],
        tasks: list[Task],
        busy_periods: Optional[list[BusyPeriod]] = None,
    ) -> None:
        self.target_pets = target_pets
        self.parents = parents
        self.tasks = tasks
        self.busy_periods = busy_periods or []

    def generate_schedule(self) -> Schedule:
        """
        Build and return a Schedule by:
        1. Deriving the time window from parent preferences (or defaulting to 8am–8pm).
        2. Computing free windows per day by subtracting busy periods.
        3. Sorting tasks by priority (high → medium → low) and fitting them greedily.
        4. Attaching reasoning text that explains each scheduling decision.
        """

        # 1. Derive time window from parent preferences
        all_preferences = [p for parent in self.parents for p in parent.time_preferences]
        if all_preferences:
            preference_windows = [TIME_PREFERENCE_WINDOWS[p] for p in all_preferences]
            sched_start = min(w[0] for w in preference_windows)
            sched_end   = max(w[1] for w in preference_windows)
        else:
            sched_start = time(8, 0)
            sched_end   = time(20, 0)

        # 2. Build busy blocks per day as (start_min, end_min) tuples
        all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        def to_min(t: time) -> int:
            return t.hour * 60 + t.minute

        start_min = to_min(sched_start)
        end_min   = to_min(sched_end)

        day_busy: dict[str, list[tuple[int, int]]] = {day: [] for day in all_days}
        for bp in self.busy_periods:
            bp_start = to_min(bp.start_time)
            bp_end   = bp_start + bp.duration
            for day in bp.effective_days:
                if day in day_busy:
                    day_busy[day].append((bp_start, bp_end))

        def free_windows_for(day: str) -> list[tuple[int, int]]:
            """Return the free (start_min, end_min) windows within the schedule window for a day."""
            result: list[tuple[int, int]] = []
            cursor = start_min
            for b_start, b_end in sorted(day_busy[day]):
                b_start = max(b_start, start_min)
                b_end   = min(b_end, end_min)
                if b_start > cursor:
                    result.append((cursor, b_start))
                cursor = max(cursor, b_end)
            if cursor < end_min:
                result.append((cursor, end_min))
            return result

        # Determine which days have usable free time
        effective_days = [d for d in all_days if sum(e - s for s, e in free_windows_for(d)) > 0]
        if not effective_days:
            effective_days = all_days

        # Use the most-available day as the reference for task fitting
        best_day = max(effective_days, key=lambda d: sum(e - s for s, e in free_windows_for(d)))
        windows  = list(free_windows_for(best_day))

        # 3. Sort tasks: high → medium → low, then shorter duration first as tiebreaker
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (_PRIORITY_ORDER.get(t.priority, 99), t.duration),
        )

        # 4. Greedily fit each task into the remaining free windows
        scheduled: list[Task] = []
        reasoning_lines: list[str] = []

        for task in sorted_tasks:
            slots_needed = task.daily_frequency
            placed_times: list[str] = []
            next_windows: list[tuple[int, int]] = []

            for w_start, w_end in windows:
                while len(placed_times) < slots_needed and (w_end - w_start) >= task.duration:
                    slot = time(w_start // 60, w_start % 60)
                    placed_times.append(slot.strftime("%I:%M %p"))
                    w_start += task.duration
                if w_end > w_start:
                    next_windows.append((w_start, w_end))

            if len(placed_times) >= slots_needed:
                scheduled.append(task)
                windows = next_windows
                reasoning_lines.append(
                    f"- '{task.name}' [{task.priority}]: scheduled {slots_needed}x "
                    f"at {', '.join(placed_times)} ({task.duration} min each)"
                )
            else:
                reasoning_lines.append(
                    f"- '{task.name}' [{task.priority}]: skipped — not enough free time "
                    f"(needs {task.duration * slots_needed} min total)"
                )

        reasoning = "Schedule reasoning:\n" + "\n".join(reasoning_lines)

        return Schedule(
            is_24hr_format=False,
            effective_days=effective_days,
            start_time=sched_start,
            end_time=sched_end,
            tasks_scheduled=scheduled,
            reasoning=reasoning,
        )
