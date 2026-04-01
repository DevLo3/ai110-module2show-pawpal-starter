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
    min_interval: int = 0   # minimum minutes required between occurrences (0 = no constraint)
    is_complete: bool = False
    responsible_parents: list[Parent] = field(default_factory=list)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_complete = True

    def mark_incomplete(self) -> None:
        """Reset this task to incomplete."""
        self.is_complete = False

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
        """Store the pets, parents, tasks, and busy periods used to generate a schedule."""
        self.target_pets = target_pets
        self.parents = parents
        self.tasks = tasks
        self.busy_periods = busy_periods or []

    def generate_schedule(self) -> Schedule:
        """Build and return a Schedule by fitting prioritized tasks into free time windows."""

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

        def consume_slot(
            src_windows: list[tuple[int, int]], slot_start: int, duration: int
        ) -> list[tuple[int, int]]:
            """Remove a [slot_start, slot_start+duration] block from the window list."""
            slot_end = slot_start + duration
            result: list[tuple[int, int]] = []
            for w_start, w_end in src_windows:
                if w_end <= slot_start or w_start >= slot_end:
                    result.append((w_start, w_end))
                else:
                    if w_start < slot_start:
                        result.append((w_start, slot_start))
                    if w_end > slot_end:
                        result.append((slot_end, w_end))
            return result

        # 3. Sort tasks: high → medium → low, then shorter duration first as tiebreaker
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (_PRIORITY_ORDER.get(t.priority, 99), t.duration),
        )

        # 4. Greedily fit each task into the remaining free windows,
        #    respecting min_interval between occurrences of the same task.
        scheduled: list[Task] = []
        reasoning_lines: list[str] = []

        for task in sorted_tasks:
            slots_needed = task.daily_frequency
            placed_times: list[str] = []
            remaining = list(windows)
            last_placed_end: Optional[int] = None

            for _ in range(slots_needed):
                # The next occurrence can't start before this point
                earliest = (last_placed_end + task.min_interval) if last_placed_end is not None else 0
                placed = False

                for w_start, w_end in remaining:
                    slot_start = max(w_start, earliest)
                    if slot_start + task.duration <= w_end:
                        placed_times.append(time(slot_start // 60, slot_start % 60).strftime("%I:%M %p"))
                        last_placed_end = slot_start + task.duration
                        remaining = consume_slot(remaining, slot_start, task.duration)
                        placed = True
                        break

                if not placed:
                    break

            if len(placed_times) >= slots_needed:
                scheduled.append(task)
                windows = remaining
                interval_note = (
                    f", ≥{task.min_interval // 60}hr gap enforced" if task.min_interval > 0 else ""
                )
                reasoning_lines.append(
                    f"- '{task.name}' [{task.priority}]: scheduled {slots_needed}x "
                    f"at {', '.join(placed_times)} ({task.duration} min each{interval_note})"
                )
            else:
                reasoning_lines.append(
                    f"- '{task.name}' [{task.priority}]: skipped — could not fit {slots_needed} "
                    f"occurrence(s) with ≥{task.min_interval} min between each"
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
