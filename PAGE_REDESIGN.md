# Page redesign

Reorganise the evidence page so that one page serves the whole cycle of work.
Keep what exists and works (the three flow charts, the tests list, the cards
and panels, replay, review marks, structure map, definitions, operator tab,
compare tab). This file is about arrangement and a few additions, not a rewrite.

Never open or print `drafts.jsonl`. No new dependencies beyond Chart.js. Small
files. Light and dark mode. Old sessions open as far as their records allow;
missing data is shown as "not recorded".

## Who uses the page, and for what

A person (the operator, or a reader such as a supervisor) does three jobs:

1. **Set up and run**: write an assignment, start the AI on it, watch.
2. **Follow and verify**: see what the AI did and check it against the measurements.
3. **Compare and judge**: across sessions, how often and how well.

Each job gets a clear place. Nothing requires the older control page.

Do the parts in order. After each part, run its "Done when" checks and commit.
Report at the end and stop.

---

## Part A — Home

Shown when no session is selected (`/viewer/`).

- Three large actions: **New session**, **Open a session**, **Compare sessions**.
- **Results so far**, one line per brief, computed from the sessions and, where
  they exist, their scores. Example: "two-hosts-udp-demand: 9 sessions ·
  9 with a final report · 9 meet the brief's conditions · largest gap to the
  best 0.11%".
- **Sessions table**: id, brief, started, how it ended, simulations used,
  tests held / failed, review progress. Sortable and filterable. A switch
  "show operator columns" adds scheduling policy and gap to the best.
- A running session is marked and listed first.

**Done when:** the home page lists every session; sorting and the filter work;
the results line equals a count made directly from the session and score files.

---

## Part B — Set up and run

**New session** opens a panel:

1. Brief: choose one, or open the brief editor ("save as new brief"; an
   existing brief is never overwritten).
2. Scheduling policy: share, cap, or **random** (the harness chooses, records
   it under `checks/`, and the page reveals it only after the session is scored).
3. Settings: budget (from the brief), the flags, with their defaults.
4. **Start**. The page goes to the new session.

While a session runs:

- A banner on its page: "running · turn k · n simulations left", and **Stop**.
- The page refreshes by itself as records arrive; new items appear in place
  without losing what the reader has open.

On the Operator tab, next to the sweep map and the score:

- **Run one simulation** (operator run with chosen settings; result shown in
  the standard result panel; stored under `checks/`).
- **Run a sweep** (grid form, progress bar, Stop).

Keep the older control page working, but nothing should need it.

**Done when:** a session can be created, started, watched to its end and
stopped using only this page; a "random" session shows its policy only after
scoring; an operator simulation and a small sweep can be started from the
Operator tab.

---

## Part C — The session page

Top to bottom:

### C1. Header strip (always visible)
Brief · session id · model · how it ended · simulations used / allowed ·
tests held / failed · the recommendation in one line. With operator columns
on: scheduling policy and gap to the best.

### C2. Overview (the first thing a reader reads)
- The introduction strip (existing).
- **Research overview**, from the final report: the goal; the recommended
  settings; the expected result; the explanation in at most three lines with
  "more"; when it holds; when it breaks. Each claim is a chip (existing).
- If there is no report: "no final report", and why the session ended.

### C3. Highlights
Up to seven key moments, chosen by fixed rules from the records (no model is
asked), each one sentence built from the record's fields, each a link:

1. the first test that held;
2. every test that failed and from which a later hypothesis follows
   (`follows_from`) — "this changed the direction";
3. the tests cited by the report's first claim;
4. the simulation after which the best valid result no longer improved;
5. every refused answer or refused part;
6. any verdict that contradicts its check, and any number in the model's text
   that differs from the measurement;
7. the final report.

If more than seven qualify, keep them in this priority order and say how many
were left out. A reader should be able to follow the session from the
highlights alone.

### C4. Best so far
One chart. Horizontal: simulations in the order they ran (1 … n), with a thin
mark at each turn. Vertical: the brief's target measure.

- One dot per simulation: filled if it meets the brief's conditions, hollow
  if not.
- A step line: the best value so far among simulations meeting the conditions.
- A marker at the recommended settings.
- With operator columns on: a horizontal line at the best row of the sweep.
- For a brief whose goal is open: "not applicable: the goal is chosen by the
  model", and no chart.

### C5. The work, as tree and detail
Two panes.

- **Left: a tree.** turn → experiment → test → simulation. Refused items
  appear in place, in the warning colour. Each row shows its icon, id, a few
  words, and its state (held / failed, supported / refuted). Collapsible. The
  tree follows replay: items after the replay step are greyed.
- **Right: the detail** of whatever is selected: the work-log card for a turn,
  the test flow chart for a test (View 3), the result panel for a simulation,
  the experiment's chart for an experiment.
- Above the panes, three buttons switch the left side between **Tree**,
  **Session flow** (the lanes, View 1) and **Hypothesis map** (View 2).
  Selection is shared: choosing an item in one shows it selected in the others.

### C6. How to read this page
The structure map, the turn loop, the legend and the definitions, in one
collapsible section, open on a reader's first visit and closed afterwards.

**Done when:** for s006, the overview shows the report's fields; the
highlights list contains its first held test and its final report and every
link opens the right item; the best-so-far line ends at the value of the
recommended settings; selecting a test in the tree selects the same test in
the lanes and in the hypothesis map; replay greys later items in all three.

---

## Part D — Compare and judge

**Compare sessions** tab:

- The sessions table of one brief (as on Home), with a tick on each row.
- Ticking two or more shows, side by side:
  - their best-so-far lines on one chart (one colour per session);
  - a table: how it ended, simulations used, turns, hypotheses, tests held /
    failed, refused answers, recommendation (differences highlighted), and
    with operator columns on, policy and gap;
  - for each, the first test that held and its one-sentence highlight.
- With operator columns on: the sweep as a parallel-coordinates chart (one
  axis per knob, one for the target; rows failing the conditions greyed), with
  each ticked session's recommendation drawn as a bold line.

**Review queue** (on a session's page, as a tab beside the detail pane):

- The items a person should check, in this order: each claim of the final
  report with its evidence; verdicts contradicting a check; numbers differing
  from measurements; refused items; hypotheses that ended without a verdict;
  then every remaining test.
- Each item: open, tick, note (existing storage in `checks/reviews/`).
- Progress ("checked 7 of 31"), and **Sign off**: name and date, stored with
  the review; the session's row on Home then shows "reviewed by … on …".

**Done when:** two sessions of the same brief can be ticked and compared; the
parallel-coordinates chart draws the sweep with a ticked session's
recommendation; a sign-off survives a reload and shows on Home.

---

## Part E — Share

- **A link for every item**: `?session=<id>&item=<record id>` opens the page
  with that item selected and visible. The trail and every card have "copy
  link".
- **Export session**: one folder (or zip) holding this page and this session's
  files, which opens by double-clicking `index.html` with no server. It never
  contains drafts. A tick decides whether operator-only data (policy, score,
  review) is included; off by default.
- **Print**: the overview, highlights, best-so-far chart and tests list print
  cleanly on paper; the evidence sheet for one claim (existing).

**Done when:** a copied link reopens the same item; an exported folder of s006
opens offline in a browser and shows the overview, highlights, tree and one
test's flow chart; with the tick off, no file in it contains the policy.

---

## Words

Use the fixed definitions already on the page. "Work log" for the sequence of
the model's steps and its stated reasons. "Operator columns" for anything
operator-only. Do not introduce new terms.

## Final report to give

- Which parts are done and their "Done when" results.
- Line count of each viewer file.
- Anything left out and why.
