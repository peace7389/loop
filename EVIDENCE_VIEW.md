# Evidence view (replaces EVIDENCE_TRAIL.md)

Goal: a person can see, for any session, what was done step by step, who did
each step, why the model said it took it, and what the simulations showed —
and can verify any claim in the final report against the measurements.

This is built together with stage 6 of `RESTRUCTURE_PLAN.md` (brief selector,
session list, operator tab with scheduling policy, sweep map and score,
compare-sessions table). Where the two overlap, this file decides.

## Order of work

1. Part 1 (what the harness records). Test with a scripted session. Commit.
2. Start six real sessions in the background on brief `two-hosts-udp-demand`,
   three under each scheduling policy, default settings, the brief's budget.
3. While they run: Part 2 and Part 3 (the page), and stage 6 of the main plan.
4. When the sessions end: score each, commit, push, and report one table
   (session, policy, how it ended, simulations used, gap to the best).

Run the "Done when" checks, report, and stop.

Never open or print `drafts.jsonl`. The page does not show draft text.

Words to use on the page: "work log" for the sequence of the model's steps and
its stated reasons; "simulation" for one ns-3 run; "experiment" for the batch
of simulations planned in one turn; "test" for one hypothesis put to one
decision rule; "decision rule"; "scheduling policy".

## Experiment and test (read this first)

The model sends one **experiment** per turn: a batch of simulations. Inside it
there are usually several **tests**. A test is one hypothesis, its decision
rule (with its rival), the simulations that rule names, the check, and the
verdict. The test is the unit of evidence and the thing a reader examines; the
experiment is only the container the tests were run in.

- Nothing changes in the answer format or in `loop.py`: still one experiment
  per turn, one decision rule per tested hypothesis.
- The page derives each test from the records: the simulations of a test are
  the labels that appear after `@` in its decision rule. Among them, the
  experiment's control (if named in the rule) is marked as the test's control.
- An "explore" experiment has no tests; it is shown as a batch with its
  question and its simulations.

---

## Part 1 — What the harness must record

1. **What a hypothesis follows from.** In the answer format, each new
   hypothesis gains a required field `follows_from`: a list of ids of earlier
   records (a verdict, a check, an evidence table, a simulation) or the word
   `brief`. `loop.py` refuses ids that do not exist. Add one sentence to the
   prompt.
2. **State at each turn.** At the start of every turn the harness appends a
   short `turn` record: turn number, simulations left, number of open
   hypotheses, ids of the records added since the previous turn.
3. **Refusals stay visible.** A wholly refused answer is a `malformed` record;
   a partly refused answer leaves a harness `note` ("refused part of the
   answer: …"). Both must hold the reason and which part was refused, in
   fields the page can read without parsing prose.
4. **Timestamps.** Every record has one.

Existing sessions are not rewritten; the page shows "not recorded" where a
field is missing.

---

## Part 2 — The three flow charts

Draw them as plain SVG built by the page's own script; no graph library.
Colours for who produced an item are the existing four (operator, model,
harness, simulator), with one legend.

### View 1 — Session flow (lanes)

- Three vertical lanes: the model, the harness, the simulator. Time runs down.
- One box per step, in the lane of whoever did it, joined by arrows in time
  order:
  - harness: "brief and baseline shown"; "plan accepted"; "refused: reason"
    (whole or part); "N checks: a held, b failed"; "report accepted" or
    "report refused: reason"
  - model: "turn k: verdicts …, new hypotheses …, experiment Xn (m simulations,
    r tests)"; "final report"
  - simulator: "m simulations" with a strip of dots, one per simulation;
    a simulation returned from an earlier one (not run again) is drawn hollow
- A thin band across the lanes marks each turn, with the turn number and
  simulations left.
- Refused steps are drawn in the warning colour and stay in the chart.
- Clicking a box opens it (work-log card, experiment flow, or result panel).
- Long sessions can collapse turns.

### View 2 — Hypothesis map

- One node per hypothesis, left to right by the turn in which it was stated,
  top to bottom in order.
- Node colour by state: open, supported, refuted, inconclusive, dropped,
  ended without a verdict.
- Arrows from `follows_from`: from the earlier record's hypothesis (or from a
  "brief" node) to the new hypothesis, labelled with the kind of record it
  came from ("refuted", "supported", "observation").
- Hypotheses cited by the final report's claims get a ring; "show the path to
  the answer" highlights the path from the first node to those.
- Clicking a node opens View 3 for the test of that hypothesis.

### View 3 — One test as a flow chart

Left to right:

hypothesis → decision rule (with its rival and what the rival would give)
→ the simulations this rule names → diamond "did the rule hold?" → verdict
→ "next" (the model's stated next step) → arrow to the hypothesis that
followed.

- Under the decision-rule box: "written hh:mm:ss · simulations finished
  hh:mm:ss ✓ written first" (warning colour if not).
- Under the diamond: the rule with the measured numbers filled in.
- If a verdict disagrees with its check (supported after failed, or refuted
  after held), mark it.
- Only the simulations named in this test's decision rule are shown, with the
  settings that differ between them highlighted. A line beneath says "run in
  experiment Xn (turn k) together with tests of H…, H…", each a link.
- A list "Tests" replaces any list of experiments as the main list of a
  session: one row per test (hypothesis, what was compared, held or failed,
  verdict), grouped under a light heading per experiment ("experiment X1 ·
  turn 1 · 12 simulations · 5 tests").

### The work-log card (opens from any model box)

Always the same three parts, built only from the model's recorded answer and
the `turn` record:

1. **What it had**: simulations left, open hypotheses, the records added since
   its previous turn (as links), any refusal notes it was shown.
2. **What it decided**: verdicts, new hypotheses with `follows_from`, the
   experiment (its simulations) and the tests in it (decision rule and rival
   for each).
3. **Why, in its own words**: its observations, each verdict's "because", its
   "next".

Where the model's text contains a number that also exists as a measurement in
the same experiment, show both and mark a mismatch (already done for verdicts;
extend to observations and the report).

### The result panel (opens from any simulation)

Always the same layout:

- settings that differ from the experiment's control, highlighted
- the measurements, with the difference from the control beside each
- the charts over time (existing), with the shared time marker
- PNG / CSV export

For a test: the measure its decision rule judges, one point per simulation it
names, control marked, the rule's threshold drawn as a line, clickable. For a
whole experiment: the same chart over all its simulations, on request.

### Kept from the earlier plan

- Claim chips for the final report with a coverage line ("N claims · A backed
  by held checks · B by a failed check · C with no evidence"). Clicking a chip
  highlights its evidence in View 1 and View 2 and opens View 3.
- Replay: first / previous / next / last and arrow keys; at step k everything
  later is greyed in all three views.
- Reviewer ticks and notes on every box, stored through `POST /api/review` in
  `checks/reviews/<session-id>.json`; a progress bar; "print evidence sheet"
  for one claim.

---

## Part 3 — Making the structure understandable at a glance

- **Structure map** at the top of every session page: the diagram
  brief → session → hypotheses / experiments / final report; experiment →
  tests; test → decision rule, simulations → check → verdict; drawn small, each box showing this session's
  count and coloured by who produces it. Clicking a box scrolls to that part.
- **Turn loop**: a small cycle "decide → run → check → look again" with the
  number of turns.
- **Definitions**: the sentences below, kept in one list and shown on hover
  wherever the term appears. Use them word for word.
- **Trail**: "Brief › Session › Turn › Experiment › Test › Simulation" above any
  opened item, each part clickable.
- **Icons**: one fixed symbol per record type, used in every list and chart.
- **Introduction strip**: three or four plain sentences describing this
  session, generated from its own counts, dismissible. Pattern: "A person
  wrote an assignment. The AI made one attempt, in N turns. Each turn it
  stated what it expected, ran simulations, and the harness checked whether it
  was right: A of B decision rules held. It ended with this recommendation: …"

### Definitions (word for word)

| Term | Sentence |
|---|---|
| Brief | The assignment a person writes before a session: fixed settings, knobs, goal and limits. |
| Session | One complete attempt by the model at one brief, from an empty record to its final report. |
| Turn | One exchange: the harness shows the record so far, and the model answers. |
| Hypothesis | The model's claim about how the system behaves. |
| Experiment | The batch of simulations the model plans in one turn, to test hypotheses or to explore a question. |
| Test | One hypothesis put to one decision rule, using some of an experiment's simulations. |
| Decision rule | The numeric condition, stated before the simulations, that decides whether a hypothesis is accepted or rejected. |
| Rival | A competing explanation that the decision rule would rule out. |
| Simulation | One run of the network simulator with one set of knob values. |
| Check | The harness applying a decision rule to the measured numbers: held or failed. |
| Verdict | The model's judgment of a hypothesis after its check: supported, refuted or inconclusive. |
| Final report | The model's answer: recommended settings, expected result, explanation, when it holds, when it breaks, and evidence for each claim. |
| Operator | The person running the project; operator-only items are never shown to the model. |
| Scheduling policy | How the sender's scheduler divides the link between the two flows; chosen by the operator and not told to the model. |

---

## Rules

- No new dependencies beyond Chart.js. Light and dark mode.
- UDP and TCP keep their existing colours. Never two scales in one chart.
- Missing data is shown as "not recorded"; nothing is filled in.
- Old sessions open as far as their records allow.

---

## Done when

- s005 opens in all three views; every box opens its card or panel.
- In View 2, every hypothesis of a session recorded after Part 1 has at least
  one incoming arrow, and "show the path to the answer" highlights a connected
  path.
- In View 3, every test of s005 and s006 shows exactly the simulations named
  in its decision rule; the order line is correct; and a scripted verdict that
  contradicts its check is marked.
- The "Tests" list of s006 has 18 rows grouped under its experiments.
- Replay at step k shows nothing recorded after k in any view.
- A reviewer tick and note survive a reload and are in `checks/reviews/`.
- The structure map's counts equal the counts in the session's ledger; each
  definition appears on hover; the trail is correct for an opened simulation.
- The six-session table is reported.
- Report the line count of each viewer file and list every place that shows
  "not recorded".
