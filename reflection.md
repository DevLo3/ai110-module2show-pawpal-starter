# PawPal+ Project Reflection

## 1. System Design

   The PawPal+ app should enable users to complete 3 core actions:
        1. Add their pet to the app (with relevant pet attributes and a pet picture)
        2. Create, edit, and delete tasks related to their pet (e.g. taking a walk, feeding, grooming, etc.)
        3. Generate a daily plan to accomplish tasks for their pet (based on user requirements and constraints)

**a. Initial design**

- Briefly describe your initial UML design.
    My initial design used five classes connected around a central `Scheduler` that takes pets, parents, and busy periods as inputs and produces a `Schedule` as output. 
- What classes did you include, and what responsibilities did you assign to each?
    I included `Pet` (stores pet profile data), `Parent` (stores owner info and time preferences), `Task` (represents a care action tied to a specific pet), `Block` (marks when owners are unavailable), and `Schedule` (contains the logic to generate a plan and creates the output object that holds the resulting task list and reasoning). I also added a `TimePreference` enum to cleanly represent when parents are available throughout the day.


**b. Design changes**

- Did your design change during implementation?
    Yes
- If yes, describe at least one change and why you made it.
    I made the scheduling logic separate from the Schedule data objects, via a separate Scheduler class, to make the system easier to reason about and extend. Additionally I changed the name of my `Block` class to `busyPeriod`as Claude initially misinterpreted the term Block to refer to a block of tasks, instead of interpreting it as a period of time where tasks shouldn't be scheduled, which is what I meant. To prevent further confusion, I decided to change the class's name to one suggested by Claude (busyPeriod). Finally, I added tasks: list[Task] to `Pet` and added pets: list[Pet] to `Parent`, after Claude identified these as missing relationships. With that change, Pets now own their tasks directly and tasks know whos' doing them.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    The scheduler considers parent `TimePreference` (morning, midday, evening, night — each mapped to a concrete time window), `BusyPeriod` blocks that carve unavailable time out of that window, task `priority` (high → medium → low), task `duration`, `daily_frequency`, and `min_interval` (a required gap between occurrences of the same task). It also respects `is_complete` status, skipping already-finished tasks entirely.

- How did you decide which constraints mattered most?
    Priority was chosen as the primary sort key because missing a high-priority task (like medication) has real consequences for a pet's health, while a lower-priority task (like grooming) can flex. Pet clustering was added as a secondary sort criterion so all of one pet's tasks land together in the day, reducing the mental overhead of switching between animals mid-schedule.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    The scheduler uses a greedy first-fit algorithm: it places each task into the earliest available slot and never backtracks. This means a high-priority long task placed early can block several shorter lower-priority tasks from fitting later, even though a different ordering would have accommodated everyone.

- Why is that tradeoff reasonable for this scenario?
    For a typical household with a small number of tasks (under ~20), the greedy approach produces a usable schedule in effectively zero time and is easy to reason about — the reasoning text it generates maps directly to the order decisions were made. A globally optimal solver would be harder to explain to a pet owner and would add complexity that isn't warranted at this scale.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    I used AI throughout every phase: drafting the initial UML, stubbing out class skeletons, implementing the scheduling logic incrementally, refactoring for code quality (e.g. replacing stringly-typed recurrence strings with a `Recurrence` enum), writing the automated test suite, and updating documentation. It was especially useful for keeping multiple files in sync — when I added a new field to `Task`, the AI could update the constructor calls in `app.py`, `main.py`, and the tests in one pass rather than me hunting for every usage manually.

- What kinds of prompts or questions were most helpful?
    The most productive prompts were ones that gave context about *intent*, not just what code to write — for example, "add logic so that when a recurring task is marked complete, a new instance is automatically created for the next occurrence" led to a cleaner design than asking it to "add a `next_due` field." Asking it to explain tradeoffs before implementing (like greedy vs. optimal scheduling) also helped me make more informed decisions rather than just accepting whatever it first produced.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    When Claude first suggested naming the unavailability class `BusyPeriod`, I pushed back and kept my original name `Block` — but after seeing it misinterpret the word "Block" as a block of tasks rather than a time block in several follow-up responses, I decided the rename was actually the right call. That experience showed me that class names don't just matter for my own readability; they shape how the AI reasons about the design in every subsequent prompt.

- How did you evaluate or verify what the AI suggested?
    My main verification method was running `main.py` after each significant change and reading the printed output to confirm the behavior matched what I described in the prompt. For the scheduler specifically, I traced through the reasoning text it generated — if the reasoning said a task was placed at a time that didn't make sense given the busy periods or priority order, I knew the logic was wrong and would ask the AI to explain its approach before accepting any fix.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    I tested three behavioral areas: chronological task sorting (including the edge case where tasks without a scheduled time sort last and two untimed tasks are unordered relative to each other), recurrence spawning (verifying that `mark_complete` on a daily task returns a new task due tomorrow, a weekly task returns one due in 7 days, the spawned task starts incomplete with no scheduled time, and non-recurring tasks return `None`), and conflict detection (overlapping, back-to-back, non-overlapping, cross-pet, and missing-time cases).

- Why were these tests important?
    These three behaviors are the most likely sources of silent bugs — sorting failures produce a visually wrong schedule without raising an exception, a broken recurrence silently drops tasks the owner expects to see tomorrow, and an undetected conflict could cause two real-world care activities to be attempted simultaneously. Testing them explicitly gave me confidence that the core logic holds before I wired it into the UI, where bugs become much harder to reproduce and isolate.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    I would rate my confidence at 4 out of 5 stars. The core scheduling logic, recurrence, sorting, and conflict detection are all covered by 23 passing tests, and I manually verified the output of `main.py` after each significant change. The main gap is the Streamlit UI layer, which is not covered by automated tests — session state transitions, form resubmission, and `st.rerun()` behavior can only be verified by clicking through the app manually.

- What edge cases would you test next if you had more time?
    I would test what happens when the entire available window is consumed by high-priority tasks and lower-priority tasks are left unscheduled, and verify that the reasoning text accurately reflects the skip decision. I would also test the even-spacing formula edge case where a recurring task has a `daily_frequency` greater than the number of available free windows, and confirm that a `BusyPeriod` that exactly spans the entire scheduling window results in zero placed tasks rather than an error.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    I am most satisfied with the recurrence design. Making `mark_complete()` return an `Optional[Task]` — rather than mutating global state or requiring the scheduler to poll for due tasks — kept the `Task` class self-contained and made the UI integration straightforward: the caller checks the return value and decides where to register the new instance. It was a small API surface decision that made every other layer cleaner, and seeing it hold up across the test suite and the Streamlit UI without any special cases felt like a sign that the abstraction was right.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    I would redesign the scheduling window model. Right now the scheduler derives a single contiguous window from the owner's `TimePreference` values and subtracts `BusyPeriod` blocks, but the result is still one flat list of free minutes per day. A richer model would represent free windows as a sorted list of `(start, end)` intervals from the start, which would make it easier to place tasks that span a gap (e.g., a lunch-break walk between two busy periods) and would eliminate the need to re-derive available time inside the greedy loop. I would also add UI tests — even a small Playwright or Selenium suite covering the happy path would catch the session-state bugs that are currently only found by manual clicking.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    The most important thing I learned is that naming is load-bearing when working with AI. Renaming `Block` to `BusyPeriod` changed how the model reasoned about the class in every subsequent prompt — it stopped suggesting that the class manage collections of tasks and started suggesting that it carve out unavailable time windows, which is exactly what I needed. More broadly, I learned that the best way to use an AI collaborator is to front-load intent and context in each prompt rather than just asking for code: when I explained *why* I wanted a certain design, the suggestions fit the system; when I only described *what* to write, I often got something technically correct but architecturally at odds with the rest of the codebase.
