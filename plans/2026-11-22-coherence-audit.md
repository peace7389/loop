# Coherence audit of the harness and the page, and the plan — 2026-11-22, night

The operator: "Since all errors have been occurring due to inconsistent and incomplete overall structure, examine every element and detail to each
line of code as thoroughly as you can, to make everything work coherently together as intended." Five independent line-by-line audits ran:
- the turn loop and states;
- the supervisor's gates;
- what the agents are told versus what the harness enforces;
- the page and server versus the records;
- simulations, readings and decision rules.

They were set beside my own examination of the competitor design ("Next change for the arm 'supervised'"). Evidence comes from sessions
s041–s053. Every item below was checked against the code, and most against a session record; where a problem was found by reading the code
alone, it says so. Nothing has been edited or deployed. The code examined is the review branch (976cae4); "live" means the problem is also in
the harness deployed at 19:46.

## Six root causes

All of today's failures, and most of what the audits found, come from six patterns:

| | Root cause | Examples |
|---|---|---|
| R1 | **One rule, several copies that drift.** A limit or rule written separately in the code, the instructions, the refusal texts, the page and the exporter. | rounds, requests per turn, label length, rethink, open_questions, the plain arm's words, the exporter's file list |
| R2 | **One action, several paths with different checks.** | an experiment handled as a normal turn, a repair, a free turn, a continued reply or a resumed session; a review and its follow-up question |
| R3 | **An agent is not shown what it is asked to judge.** | the supervisor never sees its answer fields; the test reviewer never sees a network change; the ruling never sees the rival; repairs and restatements do not see the records they are told to use |
| R4 | **References by a number that is not reserved.** | a refused part shifts the ids of everything after it in the same answer |
| R5 | **States without an exit, and errors that escape.** | a checked hypothesis without a ruling; errors in a measurement, a ruling or the session start that stop the session |
| R6 | **The page assumes older shapes of the records.** | one experiment per turn, every note a refusal, every review the supervisor's |

The plan fixes the causes, not only the instances:
- every rule is stated from the same constant that enforces it;
- every model call is shown its answer fields, generated from its schema;
- one validation function serves every path an experiment can take;
- ids are reserved by position;
- every state has an exit, and every model call or tool error is caught where it happens;
- the page reads the records' current shapes and the old ones.

## Problems, most severe first

### A. Stops a session, loses work, or corrupts the record

1. **Ids shift after a refused part (R4, live).** Only accepted guesses and hypotheses get ids, but the researcher refers to new ones by "the id it
   will get". One refusal shifts every later guess, hypothesis and test in that answer:
   - s050 t4: H5 and H6, written from "equal bandwidth", were recorded under the fair-share guess, and the q4-vs-q1000 rule landed on the
     NewReno hypothesis;
   - s051 t4 H1, s051 t8 H3, s041 t2 H2: hypotheses recorded under the wrong guess;
   - also s044 t2 and s046 t3.
2. **The supervisor is never shown its answer fields (R3, live since 11-18).** The schema reaches the model server only as a constraint. The field
   names (records_show, stronger_rival, rival_is_weak, doubt_if, shows, retest, …) and their meanings are not in any supervisor prompt. Its reasoning
   says so: "Need infer exact JSON schema? … no explicit schema in user message". Consequences:
   - "shows" holds the verdict word in 16 of 17 rulings;
   - 5 of 17 rulings say fair and name a defect;
   - 60 of 77 supervisor calls ran to their reasoning limit.
3. **The test review, its follow-up question and the repair never show a simulation's network change (R3, live).** s053 H1's scheduler test was
   sent back as "unchanged from the default". Every later failure of H1 followed, and the ruling then said "a fair test would compare an actual
   scheduler", which was the original test.
4. **A ruling crashes when the newest review of a test is the harness's (R5, live).** It reads doubt_if, which harness reviews do not have, outside
   the try. The trigger: a harness-refused round, then an unreadable supervisor review.
5. **An experiment's own measurement can stop the session after its simulations ran (R5, live).**
   - A ratio over a flow that is at zero divides by zero. TCP is at 0 throughout 15 of the 51 runs of s047–s053.
   - A one-argument min/max raises an error.
   - A probe error raises one too.
6. **measure() pairs values with the wrong times when the expression is undefined at some samples (live).** On s048 r002: first_time_above 2.0 s
   (true 10.01 s); rate and slope off by a factor of 5 to 10000.
7. **Measurements are validated against the brief's network, not the network each design runs on (R2, live).**
   - Whole experiments were refused: s048 t4, s050 t5, s050 t6.
   - The reverse case passes validation, then the measurement is silently not computed.
8. **The harness's own "varied" list goes stale and refuses the whole experiment (R2, live).** s050 t1 lost H1–H3's tests; s051 t4 the same.
9. **Readings beyond 3 are dropped silently in the single-AI and plain arms (R1, live).** In s048, 12 asked-for readings were never run.
10. **Budget (R2).**
    - Repairs are not charged against each other: with 3 left, three repaired tests can run 6.
    - A continued session gets its whole budget back.
    - A negative "left" refuses every experiment in the free turns.
11. **The last turn can repeat without end** when a refused report comes with a finding decision; it also disables the 3-unusable-turns stop.
12. **The ruling asks for a finding's name that its own schema forbids (R1, live).** Its findings are nameless. This plausibly set off s053's runaway
    ruling ("It is not a finding." to the limit), which lost H2's ruling and stalled the session.
13. **The session start (baseline, the supervisor's first look) is outside the try:** an error there leaves no record of how the session ended.
14. **A link rate written with a space ("1 Gbps") passes the brief check**, and then every simulation fails.

### B. Wrong or misleading text (wastes turns, confounds comparisons)

15. **The plain arm is told about hypotheses and decision rules (R1, live):**
    - STRUCTURE is added after its word check;
    - the manifest's how_to_run;
    - the continued-turn, last-turn and free-turn texts.
    This confounds the comparison of the arms.
16. **The supervised arm is told things it cannot do (R1):**
    - to rethink guesses ("rethink it before…");
    - to use open_questions, which its report does not have, and is then blamed ("the report did not name it");
    - a drop of a checked hypothesis is refused with "it needs a verdict", but verdicts are the supervisor's;
    - "a why whose worth is verify", a field this arm does not have.
17. **The follow-up question turns a real objection into an approval.** s052 H2: the review named a stronger rival (rival_passes_too); the
    follow-up asked only about the researcher's rival; the test was approved and run, then ruled inconclusive for exactly that rival.
18. **A harness refusal in the last round is recorded as "contested: the supervisor still objects"**, although the test does not run. The page and
    the figures count it as the supervisor's.
19. **The repair prompt (R1, R3):**
    - "runs only if they must change", yet any list replaces all runs;
    - "name a simulation not yet run", which leaves out the exemption for a rule on a measurement of its own, and cannot be met in a free turn;
    - the records it is told to use are not shown;
    - its measurements are lost: a rule on a sibling test's measurement is never computed.
20. **The ruling does not see the rival judged at the review, nor the measurement definitions.** The objection's second look gets neither the
    readings nor a fairness question.
21. **A re-asked ruling (rule_missing, held build) is invisible in that turn's ledger text,** which was rendered before it.
22. **Continued replies (CONTINUES, held build):**
    - the automatic "work" decision names the wrong guess;
    - "requests only" counts replies, not turns;
    - notes say "asked again in the next turn" within the same turn;
    - requests in the last turns are dropped silently.
23. **A label over 20 characters refuses the whole experiment,** and this is never told.
24. **The free turns invite tests that trim refuses.**
25. **Smaller:**
    - `==` gets no tolerance;
    - the report's expected values are limited to the brief's outputs;
    - a guess is re-reviewed twice after a changed restatement;
    - refused_about is session-wide;
    - an unread guess is shown as sound;
    - harness reviews count as learned, and simulations do not;
    - the restatement is shown ids only;
    - the call counts undercount;
    - the two-hosts example names columns it does not record;
    - the deployed and branch texts disagree;
    - a report together with an experiment is accepted before the experiment's checks (single-AI).

### C. The page and server

26. **One experiment per turn:** s053 turn 3 shows X1 and not X2 or its check C2 (live).
27. **Notes that are not refusals are drawn as refusals** ("report refused" next to "report accepted").
28. **The calls cards never refresh with the deployed harness.**
29. **The harness's review rounds are drawn as the supervisor's** (s052 G7, s053 G8/G10).
30. **Old supervised sessions miss their test reviews** in a hypothesis's course (s047, s050, s051: no `gate` field).
31. **A link to a finding opens a turn log** ("copy link" and reload go elsewhere).
32. **The banner and the "Now" card assume the single-AI arm** ("It may judge earlier tests", "not judged by the AI yet").
33. **Continued replies and re-asked rulings (held build):** the live view says "preparing the next turn" during a reply, and later replies'
    observations are dropped.
34. **live_call.json and calls.jsonl store the step in different shapes;** the objection call has no step.
35. **An export lacks supervisor.jsonl,** and keeps dead links to the agents page.
36. **A note's hover box names the harness for the researcher's own notes;** the agents page mislabels a new running session.

All 53 sessions s001–s053 load on the live page without a script error (checked one by one, with every item and hover box).

## Plan (review branch; nothing deployed until the operator decides)

Each stage ends with every harness check passing, new scripted checks for each item, the page checks passing, and s047–s053 rendering and scoring
as before.

**Stage 1. Records and crashes:** items 1–14, plus the root-cause helpers.
- ids reserved by position, and a reference to a refused part refused with that reason;
- one schema-to-text function, so that every model call lists its answer fields with their descriptions;
- network changes shown wherever a simulation is described;
- guards on measurement, probe, check and the session start;
- measure() fixed for undefined samples, and min/max/abs checked for their number of arguments;
- per-design measurement validation;
- varied recomputed after every removal;
- budget accounting: repairs reserved, a continued session rebuilt from its ledger, a negative "left" read as 0;
- the last-turn loop closed;
- finding names in rulings;
- the requests cap stated, in the schema, and noted when it cuts;
- link values with spaces normalised.

**Stage 2. One source per rule:** items 15–25.
- Each rule's statement is generated from the constant that enforces it.
- Every turn text and refusal is worded per arm; the plain arm's word check covers the whole text.
- The supervised arm:
  - no rethink;
  - open_questions;
  - a checked hypothesis without a ruling may be dropped.
- The follow-up question may change its stronger-rival box, and a failed follow-up refuses.
- "Not run" for a harness refusal in the last round.
- The repair prompt:
  - the full list of runs;
  - the exemption;
  - the cited readings;
  - the test's measurements;
  - the network change format, with an example from the brief.
- The ruling and the objection's second look see the rival and the measurement definitions, and the second look is asked about fairness.
- rule_missing runs before the ledger text is rendered.
- CONTINUES: fixed pairing, counters and notes.
- The label limit is stated, and the free-turn text corrected.

**Stage 3. The page:** items 26–36.

**Stage 4. The rest of "Fixes from s052 and s053":**
- feedback that names one problem;
- at most 3 comparisons in a decision rule;
- speed: one batched first review per turn, and no supervisor call after a harness refusal;
- units on the page.

**Stage 5. The competitor design, with these corrections:**
- **"Live"** means not revised and not refuted by a standing ruling. "Set aside" does not occur in this arm.
- **Correct:** pass requires exactly (the tested guess gives held, the competitor gives failed). Any other pair with pass is a contradiction, which
  gets one follow-up question.
- **Fits:** the boxes are checked against the check and the two predictions. The supervisor still judges; the harness asks once on a
  contradiction and never picks.
- **Refutation follows the standing ruling,** so an objection can undo it. Its consequences:
  - the researcher sees "refuted by Vn" in its ledger text;
  - a new hypothesis from a refuted guess is refused, and a new guess may revise it;
  - open hypotheses of the refuted guess stay.
- **A missing competitor:** the review has a field naming the missing cause. The test is then held with no repair call, and the next guess
  declaring `competes_with` is recorded "from feedback".
- **"No effect" with a cause** is checked by a guess-review defect, no_cause, and by the Consistent question.
- **A declared competitor:** the guess review is told it competes with Yn, so a "repeat" means the same cause.
- **"Contested only if it still tests its hypothesis"** is the Consistent question: after the last round the test runs only if Consistent passed.
- **foreseeable** is a field of the ruling's three questions; it costs no extra call.
- **Instruction size:** 9,645 of 10,000 now. About 400 characters must go elsewhere; exact sizes before and after will be reported.
- **Extra calls per turn:** one guess review per new competitor guess (about 48 s), unless the first review is batched (stage 4). A held test
  saves a repair and a review.
- **Single-AI arm unchanged.** Applying it there later would need `competes_with` in its rethinks and its own verdicts.

## Decisions for the operator
1. Start building stage 1 now? It is the first deploy candidate, alone or with stage 2.
2. The limit of 3 comparisons: the supervised arm only (as the sheet's heading says), or every arm?
3. The supervisor's follow-up question: thinking off, or a thinking budget of 1,000?
4. The competitor design: are the corrections above acceptable (especially: a refuted guess gets no new hypotheses)?

## Status (2026-11-22, night): all five stages built on the review branch, nothing deployed

Branch `review/harness-2026-11-22`; what each stage did, its checks and what was corrected while checking stand in
`review/harness-2026-11-22/REVIEW.md` there (its sections "Stage 1" to "Stage 5").
- Stage 1 (records and crashes): commit 60b000d.
- Stage 2 (one source per rule): commit 44cd3c3. Then the branch's page was brought up to main's (cc48ea5): every page change since 17:06 had
  gone to main only.
- Stage 3 (the page): ec9be26. Stage 4 (the rest of "Fixes from s052 and s053", with the batched first review): c135505. Stage 5 (competitors
  are guesses, three questions): 13992f1.
- Every harness check was run on each stage's build and on the build to deploy (derive_dep.py): all pass (the deploy build skips the 3 checks of
  parts 2 and 3). The researcher's ledger text of s047 to s053 is unchanged. The page draws every session as before except the intended fixes:
  s052 and s053 show the harness's own review rounds as the harness's, s053's turn 3 shows its second experiment X2, and turns of s041 to s047 show
  the observations the page used to drop. The page checks on the final page are running against main's page as the baseline.
- Decisions for the operator: whether to deploy, and which stages. The arm "supervised" sessions started after a deploy of stage 5 would work with
  competitors (COMPETITORS); a session keeps what it started with.
