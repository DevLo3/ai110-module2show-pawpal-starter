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

## Smarter Scheduling

The scheduler has been extended with several features beyond the baseline:

**Priority-aware, pet-clustered ordering** — tasks are sorted high → medium → low priority, and tasks belonging to the same pet are grouped together so a pet owner's attention isn't split between animals mid-schedule.

**Even spacing for recurring tasks** — tasks with a `daily_frequency` greater than 1 (e.g. feeding twice a day) are automatically spread evenly across the available window rather than stacked at the earliest possible times.

**Recurrence** — tasks can be marked `daily` or `weekly`. Calling `mark_complete()` on a recurring task automatically returns a fresh instance for the next occurrence with `next_due` set forward by 1 or 7 days.

**Conflict detection** — `Scheduler.detect_conflicts(tasks)` checks any list of scheduled tasks for overlapping time intervals and returns human-readable warning strings. The same check runs automatically at the end of `generate_schedule()` and is stored on the returned `Schedule` object.

**Task filtering and sorting** — `Schedule.filter_tasks(is_complete=..., pet_name=...)` returns a filtered subset of scheduled tasks. Tasks are also sortable by scheduled time via the standard `sorted()` built-in (`Task` implements `__lt__`).

**Duplicate prevention** — the UI blocks adding a task with the same name and pet as one that already exists.

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
