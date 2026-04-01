from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
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


class Recurrence(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


# Maps each TimePreference to a concrete (start, end) time window for use by the Scheduler.
TIME_PREFERENCE_WINDOWS: dict[TimePreference, tuple[time, time]] = {
    TimePreference.MORNING: (time(6, 0),  time(12, 0)),
    TimePreference.MIDDAY:  (time(12, 0), time(15, 0)),
    TimePreference.EVENING: (time(15, 0), time(20, 0)),
    TimePreference.NIGHT:   (time(20, 0), time(23, 59)),
}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _to_min(t: time) -> int:
    """Convert a time object to total minutes since midnight."""
    return t.hour * 60 + t.minute


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

    def add_task(self, task: "Task") -> None:
        """Append a task to this pet's task list."""
        self.tasks = self.tasks + [task]

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
    task_type: str
    duration: int           # minutes per occurrence
    priority: str           # "low" | "medium" | "high"
    target_pet: Optional[Pet] = None
    daily_frequency: int = 1
    min_interval: int = 0       # minimum minutes required between occurrences (0 = no constraint)
    strict_interval: bool = False  # if True, min_interval is always honoured even when auto-spreading
    is_complete: bool = False
    recurrence: Optional[Recurrence] = None
    next_due: Optional[date] = None    # date the next occurrence is due (set on mark_complete)
    responsible_parents: list[Parent] = field(default_factory=list)
    scheduled_time: Optional[time] = None  # set by Scheduler on first placement; used for sorting

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as completed.

        For recurring tasks ('daily' or 'weekly') returns a fresh Task
        instance for the next occurrence with is_complete=False,
        scheduled_time cleared, and next_due advanced by 1 or 7 days.
        Returns None for non-recurring tasks.
        """
        self.is_complete = True
        if self.recurrence is None:
            return None
        days_ahead = 1 if self.recurrence == Recurrence.DAILY else 7
        return replace(
            self,
            is_complete=False,
            scheduled_time=None,
            next_due=date.today() + timedelta(days=days_ahead),
            responsible_parents=list(self.responsible_parents),
        )

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

    def __lt__(self, other: "Task") -> bool:
        """Enable sorting by scheduled_time; tasks without a time sort last."""
        if self.scheduled_time is None and other.scheduled_time is None:
            return False
        if self.scheduled_time is None:
            return False
        if other.scheduled_time is None:
            return True
        return self.scheduled_time < other.scheduled_time


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
    conflicts: list[str] = field(default_factory=list)

    def edit(self, **kwargs) -> None:
        """Update one or more schedule attributes by keyword."""
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Schedule has no attribute '{key}'")
            setattr(self, key, value)

    def delete(self) -> None:
        """Clear all scheduled tasks, reasoning, and conflicts from this schedule."""
        self.tasks_scheduled.clear()
        self.reasoning = ""
        self.conflicts.clear()

    def calculate_task_count(self) -> int:
        """Return the total number of tasks in this schedule."""
        return len(self.tasks_scheduled)

    def generate_reasoning_text(self) -> str:
        """Return the human-readable explanation produced during scheduling."""
        return self.reasoning

    def filter_tasks(
        self,
        *,
        is_complete: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list["Task"]:
        """Return scheduled tasks matching the given filters.

        Pass is_complete=True/False to filter by completion status.
        Pass pet_name to filter by the assigned pet's name.
        Either or both filters may be applied simultaneously.
        """
        result = self.tasks_scheduled
        if is_complete is not None:
            result = [t for t in result if t.is_complete == is_complete]
        if pet_name is not None:
            result = [t for t in result if t.target_pet is not None and t.target_pet.name == pet_name]
        return result


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

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    @staticmethod
    def _check_interval_conflicts(
        intervals: list[tuple["Task", int, int]],
    ) -> list[str]:
        """Return warning strings for every pair of overlapping (task, start_min, end_min) entries."""
        def fmt(m: int) -> str:
            return time(m // 60, m % 60).strftime("%I:%M %p")

        warnings: list[str] = []
        for i, (task_a, a_start, a_end) in enumerate(intervals):
            for task_b, b_start, b_end in intervals[i + 1:]:
                if a_start < b_end and b_start < a_end:   # standard interval-overlap test
                    pet_a = task_a.target_pet.name if task_a.target_pet else "?"
                    pet_b = task_b.target_pet.name if task_b.target_pet else "?"
                    warnings.append(
                        f"CONFLICT: '{task_a.name}' ({pet_a})"
                        f" {fmt(a_start)}–{fmt(a_end)}"
                        f" overlaps '{task_b.name}' ({pet_b})"
                        f" {fmt(b_start)}–{fmt(b_end)}"
                    )
        return warnings

    def detect_conflicts(self, tasks: list["Task"]) -> list[str]:
        """Check an arbitrary task list for time overlaps and return warning strings.

        Each task must have scheduled_time and duration set; tasks without a
        scheduled_time are silently skipped.  Useful for validating a completed
        schedule or catching conflicts introduced by manually pre-timed tasks.
        """
        intervals: list[tuple[Task, int, int]] = []
        for task in tasks:
            if task.scheduled_time is None:
                continue
            start = _to_min(task.scheduled_time)
            intervals.append((task, start, start + task.duration))
        return self._check_interval_conflicts(intervals)

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

        start_min = _to_min(sched_start)
        end_min   = _to_min(sched_end)

        day_busy: dict[str, list[tuple[int, int]]] = {day: [] for day in all_days}
        for bp in self.busy_periods:
            bp_start = _to_min(bp.start_time)
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

        # Cache free windows once per day — avoids calling free_windows_for() twice per day
        # (once for the existence check, once for the best-day max).
        day_free = {d: free_windows_for(d) for d in all_days}
        day_free_mins = {d: sum(e - s for s, e in wins) for d, wins in day_free.items()}

        effective_days = [d for d in all_days if day_free_mins[d] > 0]
        if not effective_days:
            effective_days = all_days

        best_day = max(effective_days, key=lambda d: day_free_mins[d])
        windows  = list(day_free[best_day])

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

        # 3. Sort tasks: cluster by pet, then high → medium → low, then shorter duration first.
        #    Skip tasks already marked complete — no need to re-schedule finished work.
        sorted_tasks = sorted(
            [t for t in self.tasks if not t.is_complete],
            key=lambda t: (
                t.target_pet.name if t.target_pet else "",
                PRIORITY_ORDER.get(t.priority, 99),
                t.duration,
            ),
        )

        # 4. Greedily fit each task into the remaining free windows,
        #    respecting min_interval between occurrences of the same task.
        scheduled: list[Task] = []
        reasoning_lines: list[str] = []
        placed_intervals: list[tuple[Task, int, int]] = []  # (task, start_min, end_min)

        for task in sorted_tasks:
            slots_needed = task.daily_frequency
            placed_times: list[str] = []
            remaining = list(windows)
            last_placed_end: Optional[int] = None

            # Spread recurring tasks evenly when no explicit interval is set.
            # For strict_interval tasks the caller-supplied min_interval is always honoured.
            if slots_needed > 1 and task.min_interval == 0 and not task.strict_interval:
                total_window = end_min - start_min
                spare_time = total_window - slots_needed * task.duration
                effective_interval = max(0, spare_time // (slots_needed - 1))
            else:
                effective_interval = task.min_interval

            for _ in range(slots_needed):
                earliest = (last_placed_end + effective_interval) if last_placed_end is not None else 0
                placed = False

                for w_start, w_end in remaining:
                    slot_start = max(w_start, earliest)
                    if slot_start + task.duration <= w_end:
                        t_obj = time(slot_start // 60, slot_start % 60)
                        placed_times.append(t_obj.strftime("%I:%M %p"))
                        if len(placed_times) == 1:
                            task.scheduled_time = t_obj  # first occurrence anchors sort key
                        last_placed_end = slot_start + task.duration
                        placed_intervals.append((task, slot_start, last_placed_end))
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
        conflicts = self._check_interval_conflicts(placed_intervals)

        return Schedule(
            is_24hr_format=False,
            effective_days=effective_days,
            start_time=sched_start,
            end_time=sched_end,
            tasks_scheduled=scheduled,
            reasoning=reasoning,
            conflicts=conflicts,
        )
