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
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
