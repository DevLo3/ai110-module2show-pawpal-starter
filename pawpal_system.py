from __future__ import annotations

from dataclasses import dataclass, field
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

    def edit_pet(self, **kwargs) -> None:
        """Update one or more pet attributes."""
        pass

    def delete_pet(self) -> None:
        """Remove this pet from the system."""
        pass


@dataclass
class Parent:
    name: str
    email: str
    location: str
    time_preferences: list[TimePreference] = field(default_factory=list)
    # Tracks whether this parent is active; at least 1 must remain active at all times.
    active: bool = True

    def edit(self, **kwargs) -> None:
        """Update one or more parent attributes."""
        pass

    def deactivate(self) -> None:
        """
        Deactivate this parent.
        Must verify at least one other parent remains active before proceeding.
        """
        pass


@dataclass
class Task:
    name: str
    task_type: str          # 'type' is a Python builtin, so task_type is used here
    duration: int           # minutes
    priority: str           # e.g. "low" | "medium" | "high"
    target_pet: Optional[Pet] = None
    daily_frequency: int = 1

    def edit(self, **kwargs) -> None:
        """Update one or more task attributes."""
        pass

    def delete(self) -> None:
        """Remove this task from the system."""
        pass

    def duplicate(self) -> Task:
        """Return a new Task with the same attributes as this one."""
        pass


@dataclass
class BusyPeriod:
    """
    A time window when the owner(s) are unavailable for pet care.
    The Scheduler avoids placing tasks inside busy periods.
    """
    name: str
    start_time: time
    duration: int           # minutes
    weekly_frequency: int
    owners: list[Parent] = field(default_factory=list)

    def edit_busy_period(self, **kwargs) -> None:
        """Update one or more busy period attributes."""
        pass

    def delete_busy_period(self) -> None:
        """Remove this busy period from the system."""
        pass


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
        """Update one or more schedule attributes."""
        pass

    def delete(self) -> None:
        """Delete this schedule."""
        pass

    def calculate_task_count(self) -> int:
        """Return the total number of tasks in this schedule."""
        pass

    def generate_reasoning_text(self) -> str:
        """Return a human-readable explanation of why this schedule was produced."""
        pass


# ---------------------------------------------------------------------------
# Scheduler (logic engine)
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Accepts pets, parents, and busy periods as inputs and produces a Schedule.
    Keeps scheduling logic separate from the Schedule data object.
    """

    def __init__(
        self,
        target_pets: list[Pet],
        parents: list[Parent],
        busy_periods: Optional[list[BusyPeriod]] = None,
    ) -> None:
        self.target_pets = target_pets
        self.parents = parents
        self.busy_periods = busy_periods or []

    def generate_schedule(self) -> Schedule:
        """
        Build and return a Schedule by:
        1. Collecting all tasks across target pets.
        2. Identifying free windows (total day minus busy periods).
        3. Ordering tasks by priority and fitting them into free windows.
        4. Attaching reasoning text to the resulting Schedule.
        """
        pass
