# Review: what the researcher can reach across turns (harness/loop.py, 2026-11-22)

Branch `review/harness-2026-11-22`, on top of `main` 153eade (what runs live). **Not deployed**: the live harness is
`main`'s. Only `harness/loop.py`, `harness/prompt.txt` and `HARNESS_SPEC.md` (one paragraph in 8.3) change; this
folder holds the checks and the verification script.

## Why

A review of sessions s047 and s048 (brief "again") found that the researcher lost track of its own findings:

- What a tool returned (a *reading*, ledger type `result`, ids T1, T2, ...) was shown once, in the next turn, then
  dropped. Its own `observations` were saved but never shown back. *(Already live on `main` since 12:38, at the
  operator's word earlier the same day: every reading stays in the ledger text in full, the supervisor is given the
  same readings, the observations stand as "turn N your observations: ...". Not part of this diff.)*
- A rethink could cite only evidence, simulation, check or verdict records, and `since()` counted only evidence,
  checks and verdicts as new. In s048 turn 6, the rethink of Y11 "in the light of r010" (its measurements T10 to
  T12: tcp_rtt_ms mean 2.09, tcp_inflight mean 137459, tcp_rwnd 1048576) was refused (note N2).
- When the budget was used up, the last turn took only the report. In s048 that stopped the researcher from
  checking its receiver-window explanation, which needed only measurements of runs it already had.
- (Found by an audit of what reaches the researcher, after the operator: "the most important task is to make
  agents access all accumulated information across the turns".) Its own hypotheses' `question` and `why`, its
  tests' `question`, and parts of the supervisor's reviews and rulings (what the records show, the defect, what
  would make it doubt the test, the nearest earlier guess) never came back.

## What changes (each marked in the code with a short comment, s047/s048, 2026-11-22)

1. **Readings within the ledger's size.** `READINGS_ROOM = 40_000` characters, `reading_forms()`: under it every
   reading stands in full (up to `CAP`); past it a long reading (over 1,500 characters) older than the newest four is
   shortened to 600 characters and says how much was left out. `render()` and the supervisor's `_looked()` use the
   same forms.
2. **Readings count as evidence.** `since(ledger, at, readings=False)`: with `readings=True` it adds the readings
   whose request was made in the turn the why was last settled or later (a turn's requests are seen only in the
   next turn, though they stand before that turn's whys in the ledger). A rethink's `in_light_of` may name a T id or a
   run id (a run id stands for its simulation and the readings about that run); it must name something new when
   results came in since (`later_r`). A why's `about` may name a T id in every arm. A report claim may cite a run id
   (kept as its simulation). A reading alone does **not** make a why due for a rethink (that would force a rethink of
   every open guess after each lookup).
3. **Free turns.** `FREE_TURNS = 2` beside `UNUSABLE`. Once `sims >= budget`, the turn's mode is `"free"` for two
   turns: inside `sort_out` it is an ordinary turn, except that an experiment needing a new simulation is refused
   with the reason, and so is a `budget_request`; requests are accepted (`rq` in the loop). Then mode `"budget"`, the
   report-only last turn, as before. The turn record says `last_turn: "free"` (the page's live view shows its
   ordinary line for it). A report in a free turn ends the session as "done by the model".
4. **Everything recorded comes back.** `shown()` adds a hypothesis's question and why, a test's question, the
   supervisor's findings. The judge's readings stay hidden from the researcher, as decided on 2026-11-17 (a refusal
   reaches it as a note; `test_chain.py` checks this): a question for the operator below.
5. **Instructions.** `prompt.txt` and the supervised arm's instructions say that readings and run ids may be cited,
   and that two turns follow the budget. The arm "plain" builds its instructions from `prompt.txt` by replacement:
   two of its replacements were updated to the new sentences (`PLAIN`).

Arms: all three. The supervised arm has no rethinks (its whys could already cite T ids). The arm "plain" has no
whys, rethinks or tests: for it, readings in report claims, and requests and explore experiments on simulations
already run in the free turns.

The supervisor's view is unchanged by this diff (the operator, 2026-11-22: "yes for now" to it being given every
reading, live on `main`). It is never given the researcher's observations.

## Verification (`verify_sheet.py`; "before" = `main`'s predecessor on GitHub, 6c90598)

1. s048, the ledger text the researcher reads at turn 7: before, none of r010's three measurements is in it; after,
   all three are (`"value": 2.090693`, `137459.643564`, `1048576.0`), with its 6 earlier observations.
2. s048, the turn-6 answer through `sort_out` with the ledger as it stood: before, the rethink of Y11 is refused
   (N2); after, it is accepted, `in_light_of` S9, T7, T10, T11, T12. The same rethink naming only S9 is still refused.
3. Harness checks (`harness_checks/`, `python3 -I test_x.py SCRATCH_DIR HARNESS_DIR`): see RESULTS below.
4. Rendered ledger at the end of the session (tokens, the model server's tokenizer; LEDGER_TOKENS 100,000):
   s047 35,714, s048 19,532, s046 11,265, s043 19,394. Nothing is shortened in any of them (readings 16,383 and
   6,861 characters).

## Checks in this folder

- `test_keep_readings.py` (new): readings and observations kept across turns in the ordinary and the plain arm;
  the turn after a request names the readings instead of repeating them; `reading_forms` shortens past the room and
  says so; on the real s047 and s048 every string of every shown record reaches the last turn's ledger text.
- `test_cite_readings.py` (new, no simulation): on the real s048, the Y11 rethink accepted, the old-only one refused,
  a rethink by T id, a why about a T id, a report claim citing T10 and r010, a reading alone not making a why due.
- `test_free_turns.py` (new): a budget of 1 in the ordinary and the plain arm: two free turns, a request answered, a
  test on a simulation already run checked with no new simulation, a new simulation and a budget_request refused,
  then the report-only turn; a report in a free turn ends the session.
- `test_supervised.py` (updated): the readings' new form; the researcher's last request holds an early reading and
  its observations, the supervisor is given the same reading and never an observation.
- `test_chain.py` (unchanged) passes: the refusal wording keeps "at least one result that came in after Y1 was last
  settled" and adds ", or a reading seen since".

## RESULTS

All 17 harness checks pass on this `loop.py` (one run, 2026-11-22 13:25 to 13:50, real ns-3 runs of 2 s; `test_why` once more after
the change below): test_arms, test_chain, test_cite_readings, test_format_fix, test_free_turns, test_keep_readings, test_measure,
test_network, test_notebook_p3, test_roles, test_shared_page, test_step_c, test_structure, test_supervised, test_task_text,
test_tolerance, test_why.

Two existing checks were changed, each where it encoded the old behaviour on purpose:
- `test_supervised.py`: the supervisor's readings in the researcher's form ("EVERY READING OF THE SESSION", `[T1] turn 2
  reading measure(...)`), and a new assertion (readings and observations kept; the supervisor never sees an observation).
- `test_why.py`: "the ledger text the model reads back is as before (text and prediction)" now reads "holds the hypothesis's
  text, its prediction and its why" (change 4). The judge's readings were left hidden instead: `test_chain.py` checks that,
  and it was a decision of its own (2026-11-17).

## For the operator, not changed here

- Whether the free turns should allow a budget_request (now refused: the turns cost no simulation).
- The researcher's text written before each answer is not shown back (s048: 123,128 tokens in all; it would not fit).
- The supervisor is not given the researcher's observations (the 11-18 split); it is given every reading.
- The judge's reading of each hypothesis (follows / does not follow from its guess, and why) is kept for a person
  (2026-11-17); only a refusal reaches the researcher. Showing every reading of the judge would complete "all
  accumulated information"; it reverses that decision, so it is left for the operator.


---

# Second commit: the researcher's own measurements, on demand (2026-11-22, later)

At the operator's word ("check that the flexible probe of the researcher into the simulation is working as intended and it can come up with
flexible and creative, on demand measurements", then "do it all"). A check of s044 to s048 found the probe and `measure` working (82
measurements, the only errors were columns asked for before a probe, and the error said how), but rarely creative: plain means and maxima of one
quantity; arithmetic once, windows and levels twice; and nothing outside the probe's fixed 14 quantities could be asked for.

1. **Help to combine** (`prompt.txt`, the supervised arm's instructions, `manifest.json`, `network.tools_told`): examples of combined
   measurements (`tcp_inflight / min(tcp_cwnd, tcp_rwnd)`, the rate a window allows, a share), in every arm. An expression `measure` cannot read
   is refused with every quantity it can use, the probe's too (it named the series' alone).
2. **Relations** (`tools.measure`, `schema.json`, `loop.measurement_problem`): `crossings` (with `level`), `corr` and `lag` (with a second
   expression, `with`); an experiment may define them too. s048's r010: TCP's bytes in flight move with its window at corr 1.0, lag 0.
3. **Taps** (the program `scratch/net-taps`, a copy of `net` with `--taps` and `--listtaps`; `tools.probe(run_id, every, taps)`,
   `tools.trace_points(run_id)`; the request tool `trace_points`): the researcher lists every object of its network a tap can name (devices and
   their transmit queues, queue discs, IPv4, TCP sockets, applications, the channel, by their ns-3 Config paths, each trace source a value or an
   event, read from ns-3's TypeId) and records any of them in the probe's record: a value as `tap_<name>` (sampled), an event as `tap_<name>_n`
   and `tap_<name>_bytes` per sample. Connected once the object exists (from the first flow's start, retried every 0.05 s); it only listens and
   draws no random number. On s048's r010 with 6 taps the simulation run again gave metrics.json and series.csv byte for byte as before; the
   device's MacTx bytes measure 1.000 Gbps (the link's rate), TCP's window 136,983 bytes on average, packets wait 2.3 ms (p95) in the scheduler;
   an unknown trace source and a path naming two objects are refused with the reason. A probe without taps still runs the program `net`.
   - Built on its own, from cmake's own compile and link lines (`build_net_taps.sh`), into `build/scratch/net-taps/`: the live `net` is untouched.
     Two-host briefs (the program `two-hosts`) have no taps yet.

Checks: all 19 harness checks pass on this `loop.py` and `tools.py` (one run, 13:56 to 14:13; `test_measure_relations.py` and `test_taps.py`
are new): test_arms, test_chain, test_cite_readings, test_format_fix, test_free_turns, test_keep_readings, test_measure,
test_measure_relations, test_network, test_notebook_p3, test_roles, test_shared_page, test_step_c, test_structure, test_supervised, test_taps,
test_task_text, test_tolerance, test_why.


---

# Third commit: a shorter answer for the arm "hypotheses" (2026-11-22, later)

At the operator's sheet ("trim the researcher's answer format in the single-AI arm"), the way the arm "supervised" was trimmed on 2026-11-18.
Only `harness/loop.py` changes (and `HARNESS_SPEC.md`); `prompt.txt` and `schema.json` stay as they are: the short format and its instructions
are made from them (`short_format`, `short_prompt`), so the arm "plain" and sessions started before are unchanged.

**Dropped** (`SHORT_DROP`), from a review of every answers.jsonl: `why.worth` and `why.reason` (78 of 91 whys were "verify"),
`hypothesis.prediction` (repeats the decision rule; 43 of 288 word for word) and `follows_from`, `experiment.varied`, `control` and `needs`,
`budget_request` (used 0 times in 166 answers). Instructions: 19,464 -> 18,123 characters.

**Kept**, at the operator's word: a hypothesis's `question` and `why` ("not okay. User should read the detail when they click"); also
`why.unseen` and `matters`, each rule's `rival` and `rival_predicts`, rethinks, verdicts, the whole report.

**What the harness fills in** (`short_fill`, then `sort_out(..., short=True)`): worth "verify", reason "", prediction none; follows_from from
the why's `about`; varied from the designs; control none; needs from the decision rules (`lean_needs`, as in the arm "supervised"). The judge
is given the decision rule of the hypothesis's test where its prediction stood ("the decision rule of its test: ...").

**The operator's decisions** (2026-11-22):
1. Keep question and why (above).
2. A guess never taken up does not hold back the report (in the short format every guess counts as "verify", so the old rule would hold
   every report back until each guess had a rethink).
3. Designs are compared as trim compares them, in both short formats (`as_run`, used by `varied_of` and `lean_needs`): written values that
   differ only before rounding (100 and 100.4 packets, 2Gbps and 2000Mbps) are one value. Before, such a test was refused as differing "in
   more than one setting".
4. The turn's text names budget_request only to the formats that have it (the arm "plain", sessions in the full format): the arm
   "supervised" no longer reads it either.

**Found on the way, fixed here:**
- A hypothesis could not follow from a reading (a T id) outside the arm "supervised", although a why may be about one since the first
  commit: with follows_from taken from the why's about, every such hypothesis would have been refused. Now allowed in every arm.
- A session started before the change keeps the full format when it goes on (the flag `format: "short"` is written only for new sessions).

**Checks:**
- `test_short_format.py` (new): the format lacks the eight fields and keeps the rest; the instructions name none of them; the arm "plain"
  keeps budget_request. On the real s048 (read only): a short answer made whole, its hypothesis following from a reading (T10), the judge
  given the rule, needs and varied worked out; s048's report with a guess never taken up held back in the full format, taken in the short
  one. A scripted session in short answers: its test (designs with queuePkts 100 and 100.4) runs with varied ["weightUdp"], its check is
  made, the report ends the session; the format sent and every turn's text name no dropped field; the supervised arm's turn names no
  budget_request, the plain arm's does; a session without the flag goes on in the full format; score.py does not read loop.py (the scores
  of earlier sessions cannot change).
- `test_arms.py` (updated): the ordinary arm now records `format: "short"` and is given `short_prompt(prompt.txt)`.
- `scripted.py` (updated): it no longer fills in needs for a scripted test without `varied` (a short answer), so the harness's own
  derivation is what runs.

RESULTS: all 20 harness checks pass on this `loop.py` (one run, 2026-11-22 14:31 to 14:55, real ns-3 runs of 2 s): test_arms, test_chain,
test_cite_readings, test_format_fix, test_free_turns, test_keep_readings, test_measure, test_measure_relations, test_network, test_notebook_p3,
test_roles, test_shared_page, test_short_format, test_step_c, test_structure, test_supervised, test_taps, test_task_text, test_tolerance, test_why.


---

# Fourth commit: the supervisor sends back a test it cannot tell from its own rival (2026-11-22, later)

The operator, after s050 (live, the arm "supervised"): 3 of its first 4 rulings were inconclusive. For H1 and H4 the supervisor's review before the
runs had named a rival explanation and said it "cannot tell" what the decision rule would do under it, and approved the test all the same; after
the runs it ruled both inconclusive because "a rival passes too". In s044 to s050, of 9 tests approved with "cannot tell", 4 were ruled
inconclusive, 2 refuted, 3 never ruled.

`review_design` (gate 1): defect none with rival_outcome "cannot tell" is now "rival_passes_too", as "held" already was, and the review's because
says the harness made it so. Sent back once: sent again unchanged, the test is run and the review says the supervisor still objects ("contested"),
as for every defect. "a rival passes too" named with a rival that fails the rule still does not stand (s044: G14, G15); named with "cannot tell" it
now stands.

Check: `test_rival_cannot_tell.py` (new, on a copy of s050's ledger, no simulation): passes on this loop.py, fails on the one before.


---

# Fifth commit (A): findings, unexplained results tracked until they are closed (2026-11-22, later)

The operator, after a review of s047 to s049: the researcher noticed things the results did not explain and then left them ("parked and forgotten";
in s048 and s049 six guesses were set aside and none was taken up again). Both agents are the local model Qwen/Qwen3.8-Flash-Next-FP8.

- **A finding** F*n*: who raised it (researcher or supervisor), `about` (the records it rests on, readings included) and `text` (one sentence with its
  numbers). Its status changes only by the researcher's decisions A*n*: work (refs: a guess, hypothesis, experiment or reading), park (a reason), close
  (refs: evidence, checks, verdicts or readings), same_as (another finding). A "work" decision without refs counts as worked on, not as looked at
  (the operator's change after the review of this design).
- **The answer** (every arm): `findings: [{about, text}]` right after observations, `decisions: [{id, action, refs, reason}]` right before the report.
  Observations no longer ask for "the most important unexplained thing": that is a finding. A guess whose `about` names F*n* is about the records F*n*
  rests on, and works on it (the harness writes the decision).
- **Each turn** starts with the FINDINGS list: who raised each, its status, which are due. Open ones are due every turn; a parked one, and a working one
  with nothing new linked to it, after `PARK_TURNS = 2`.
- **The report**: while the researcher can still work (simulations or free turns left) it is held back if a finding was never looked at (no reading,
  check or evidence reaches it), at most `FINDING_HOLDS = 2` times; in the last turn a finding not closed is added to `open_questions` by the harness.
- **The supervisor** (arm "supervised"): up to 2 findings when it rules on a test, and in one call after the baseline and after each explore experiment
  (results with no ruling). What is unexplained, never why; kept only if its ids exist and its text holds a number. It is shown the findings list,
  never the researcher's observations.
- **No cascade**: findings and decisions are sorted out after every other part; one that cannot be used gives a note and nothing else is refused.
- **End of session**: one record Z with, for each finding, its status, the turns it stayed open, what looked at it, and "never looked at".
- **Readers**: `session_figures.findings_counts` (raised by each agent; closed, parked, working, unresolved; turns open; never looked at), in the
  session row of control.py and in exports; None for every earlier session. `answers.jsonl` keeps each answer as it was received (before the findings
  fill-in). audit.py and score.py read records by type and do not see the new ones.
- **The page** (viewer, kept with this branch): each finding is a bar under the hypotheses, from the turn it was raised to the turn it was settled; the
  board gets a column for every turn the findings span; outlined = open, filled = worked on, dashed = parked, end cap = closed, chevron = still open;
  a magnifier (researcher) or an eye (supervisor); "!" = never looked at. Pointing at a bar outlines its hypotheses and the reverse; a click opens its
  history. Turn by turn shows the new records.
- **Instruction size** (measured): the findings text adds 1,480 characters (ordinary arm), 1,317 (plain) and 1,578 (supervised); the reworded
  observations line keeps prompt.txt at its length. The supervised arm's own instructions (`LEAN_PROMPT`) are checked apart from it (< 8,000).
- **Check**: `test_findings.py`.

# Sixth commit (B): the review of a test before it runs, in rounds (the arm "supervised"; 2026-11-22, later)

The operator, after the reviews of s047 and s050: the supervisor invented the rival itself; its two boxes (defect, rival_outcome) disagreed 12 times
in s047 and the harness sided with rival_outcome each time; all 3 inconclusive verdicts of s047, and H1 and H4 of s050, came from those tests; a test
sent back once ran anyway on the second try. This replaces the fourth commit's "cannot tell" rule (removed, with its check).

1. The researcher states each rule's `rival` and `rival_predicts` (the fields and the check of the arm "hypotheses", shared as `rival_problem`).
2. `rival_predicts` "held" (or no rival): that test alone is refused by the harness with no call to the supervisor; the other tests go on.
3. The supervisor judges the researcher's rival; its form puts the reasoning before each box: reads; stronger_rival, rival_is_weak; under_rival,
   rival_outcome; doubt_if; because, defect; feedback. Approved only with defect none, no clearly stronger rival and rival_outcome "failed".
4. Boxes that contradict each other (defect none with held / cannot tell / a stronger rival; "a rival passes too" with failed): one direct question,
   then the decision from its answer; still contradictory, a refusal.
5. Feedback says what is wrong, never the repair; a sentence that holds a decision rule (measure@label) is cut, with a note.
6. A refused test is repaired by the researcher in the same turn: a short call (shown the hypothesis, its guess, the test, the round, the feedback, what
   was measured, the knobs) that asks only for decision_rule, rival, rival_predicts and the runs if they change. The repair is checked by the harness
   as any test (a check that fails is a round of the harness's, its reason the feedback) and reviewed again. `REVIEW_ROUNDS = 3`, then `AFTER_ROUNDS`:
   "contested" (it runs; the review and the ruling say the supervisor still objects; the verdict carries `contested`) or "dropped" (a drop record by
   the harness with the supervisor's last reason). A repair that cannot be read: a note, the test does not run this turn, nothing else is refused.
7. **Order (a change from the plan, found by the checks)**: every repair round ends before any simulation of the experiment runs; then the approved
   tests run, and each repaired test as an experiment of its own, all in the same turn. Run first, the approved tests' results were shown to the
   researcher before it fixed the repaired rule; on shared simulations the harness then refused that rule as one that "names only results already
   in the ledger". An approved test is never held to a later turn by a refused one.
8. Records: each round is a review record (round, the test as proposed, all boxes, feedback, cut, the question asked again and its answer, the
   decision: approved, sent_back, contested, dropped; by the supervisor, or the harness); each repair is a record P*n* of the researcher's.
9. Figures: `session_figures.design_rounds` (tests proposed, reviewed, rounds per test, approved in round 1, repaired then approved, contested,
   dropped, unsettled, refused by the harness), None for earlier sessions.
10. The page: a test's "Review" line lists the rounds (the test as proposed or repaired, who answered, the decision, the feedback, a cut, the question
    asked again); earlier sessions are drawn as before.

Unchanged: the ruling after the runs and the one objection; the arms "hypotheses" and "plain" (they share `rival_problem`, same messages). The
supervisor never sees the researcher's observations. `LEAN_PROMPT`: 7,933 -> 7,977 characters with A and B (the observations line, the rival fields
and the rounds, less the list of statistics the format already gives).

Checks: `test_design_rounds.py` (new; scripted sessions with stand-in agents for every case), `test_supervised.py` (turns 1 and 2 now in rounds; the
findings call after the baseline), `test_findings.py`, `test_arms.py`, `test_short_format.py` (the findings text in the instructions), `scripted.py`
(the stand-in supervisor answers the new forms; `SCRIPTED_SET` sets a constant of the loop for one session). `test_rival_cannot_tell.py` is retired.

# Seventh commit (D): a guess is never refused for good (the arm "supervised"; 2026-11-22, later)

The operator, after s050 and s051: most guess refusals came from the supervisor's defect "not_from_what_was_learned" (the chain rule live since that
morning): s047 1 refusal in 20 guesses, s050 3 of 14 and s051 4 of 9, and in s050 turn 6 a guess that quantified an earlier one with new readings was
refused. A refused guess took its hypotheses and the experiment down with it (s051: 8 turns, no simulation; 6 hypotheses and 1 experiment fell).

1. `GROUND_WARNINGS = ("not_from_what_was_learned",)`: that defect is recorded as a warning; the guess is accepted, its review says "accepted with
   a warning". Under this rule s050 would have refused 0 guesses (3 before), s051 1 (4 before).
2. `RESTATE_GUESSES = True`: any other refusal of a guess (the harness's own checks, the chain rule among them, or the supervisor's) brings one
   restatement in the same turn: a short call to the researcher with the reason, the guess as stated, what was learned since its last guess and what
   was measured, in the guess's own format. The restatement is checked again: by the harness alone when the harness refused it (no call to the
   supervisor), by the supervisor too when the supervisor did. Then the guess is accepted: contested if it still fails (even if its about changed);
   a restatement that cannot be read leaves the guess as first stated, contested. Its hypotheses and test go ahead in that turn; nothing cascades.
   The why record keeps `restated` (by whom, the reason, the first statement) and `contested` (what still fails).
3. Instructions (supervised arm): a guess not accepted "comes back to you once, in the same turn, to restate"; revises also names "an earlier guess
   it states more exactly with new numbers or a narrower cause". One limit on the whole instructions with the findings text: 10,000 characters.
4. `session_figures.guess_reviews`: guesses, warnings, restated, contested; None for earlier sessions.
5. The page: a guess's review shows "a warning" (not "it still objects"); a restated guess shows its restatement and whether it was contested.

Checks: `test_guess_restate.py` (new: a warning; a harness refusal restated and checked by the harness alone; a supervisor refusal restated and read
again; an unreadable restatement; the figures; the instructions; s047 to s051 render as before). `test_supervised.py` keeps its sessions written
before D with `RESTATE_GUESSES` off and no warnings (`SCRIPTED_SET`), and checks one limit of 10,000 on the whole instructions.

# What was deployed (2026-11-22, the operator: "Deploy A, B and D together, nothing else")

Live: part 1 (readings as evidence, free turns, everything recorded shown back), which A needs, and A, B, D. Left out, still under review on this
branch: part 2 (crossings, corr, lag, `with`, taps, trace_points: the live tools.py, schema.json, manifest.json, network.py and its two sentences
of the instructions are kept) and part 3 (the short format of the single-AI arm: `SHORT_FORMAT = False` in the deployed loop.py). Part C stays
shelved. The deployed harness is made from this branch by `derive_dep.py` (in this folder). The checks report SKIP for parts 2 and 3 where they
are off.

**Results of the fifth to seventh commits** (2026-11-22, 16:10 to 17:00, real ns-3 runs of 2 s; stand-in agents for the model):
- this branch (parts 1 to 3, A, B, D): all 23 harness checks pass (`test_findings` once more after the size check became the one limit of 10,000);
- the deployed harness (`derive_dep.py`: parts 2 and 3 off): 20 pass, 3 report SKIP (test_short_format, test_measure_relations, test_taps);
- page checks on the deployed page (ev_all.sh, a scratch copy): bar, home, lean, map, nr, page, random, replay_s006, replay_s011, replay_s014,
  test_s006, test_s014: all ok. The findings bars and the rounds list were checked on scripted sessions (screenshots), and s047 to s051 open on the
  live page without a script error after the deploy (17:05).
- The repair and review prompts of one scripted test: `prompts_round2_example.txt`. Sizes: in that scripted session the repair prompt is 611
  tokens and the review 1,545; in s050 a review was about 16,500 tokens in and 4,700 out (about 55 s), so a refused test costs per extra round one
  repair call (about 1,000 to 3,000 in) and one review (about 16,500 in, 4,700 out), and a contradiction one more review-sized call.

# Eighth part: the step a session is at, and a finding's name (2026-11-22, evening, during s052)

The operator, looking at the running s052: "Shouldn't we reflect changes on this?" (the page's strip of a turn's steps showed one AI's turn: reply,
simulations, checks), and "show concise name of each bar of a finding instead of putting content on the bar".

1. **now.json** (`stage()` in loop.py, every arm): the harness writes the step it is at as the step begins: reply (again), judge, ground, restate
   (by whom refused), design (round, rounds), repair (round), sims, checks, ruling, look; with the turn, what it is about and the time; written
   whole (a temporary file, then a rename); never stops the session. The page reads it to say who works on what while no record is written yet (a
   supervisor's reading is recorded only when its step is done: in s050 the page said "the harness prepares the next turn" for 3 to 4 minutes
   of every turn while the supervisor read guesses and reviewed tests).
2. **A finding's name** (every arm): `name`, at most 5 words, in the finding format of the researcher and of the supervisor; kept cut to 6 words
   and 48 characters (`finding_name`); a finding without one is taken all the same (nothing about findings refuses a part). The instructions say
   it in one clause each; the supervised arm's whole instructions are 9,521 characters (one limit of 10,000).

Not changed: the reasoning budget of the short calls. s052's third repair of H1 ran away (`}}}}…` to the limit of 32,000 tokens, 6 minutes,
not readable: H1 stayed open with a note, as designed). A lower limit for repairs would also lower their reasoning budget (half the limit), which
would change the conditions of the comparison sessions: noted for the review of s052 instead.

Checks: `test_now_steps.py` (new: the steps of the arm "supervised" in order with a restatement, a repair in round 2, a ruling and the look after
an explore experiment; the steps of the arm "hypotheses" with the judge; the names); `test_findings.py` expects `name` in the finding format;
`scripted.py` keeps every step written (stages_sent.json).

# Ninth part: s052 stopped on a repair (a fix of B), and a harness fault is recorded as one (2026-11-22, night)

s052 (the arm "supervised", brief again_again) stopped in turn 3 at 19:20. The supervisor sent H4's test back; the researcher's repair carried a
network change filled with the run's own label in every field (`{"do": "add_queue", "id": "q4_cubic", "on": "q4_cubic", ...}`; the brief allows
changes). `repaired()` trimmed the test before checking it as sent, and the network raised "a queue is put on a side of a link that has none
there", which nothing caught: the loop stopped, and session.json said "stopped from outside". H3 and H5, approved, never ran.

1. **The repair is checked in the order of the normal path**: its needs from the rules, the experiment as sent (labels, knobs, network
   changes: `experiment_problem(left=None)`), then trim, then the budget. Whatever the harness cannot check in a repair refuses that round with its
   reason (a round "by the harness", as for any harness refusal); it never stops the session.
2. **A fault of the harness is recorded as one**: a note "harness error: ..." in the ledger, `how` "harness error: <kind>" in session.json; the
   error is raised again, so its traceback stays in the session's log. A stop from outside (SIGTERM) is still "stopped from outside".

Check: `test_repair_structure.py` (new; brief again_again, real ns-3 runs): round 1 sent back by the supervisor; round 2 carries s052's change
and is refused by the harness with the network's reason; round 3 is approved, runs and is ruled on in the same turn; the session ends only when
the script has no more answers. On the live harness of 17:05 the same check stops with s052's error (FAIL, as expected).

**Deployed on 2026-11-22 at 19:46** (the eighth and ninth parts, and the exporter: `export_session.py` copies every script of the page's own
list; brief_canvas.js, the network's schema, was missing, so an exported session opened blank). Deploy build = `derive_dep.py` of this branch:
22 harness checks pass, 3 report SKIP (parts 2 and 3 off). Page checks on the live page: bar, home, lean, map, nr, page, random, replay_s006,
replay_s011, test_s006 ok; views ok with the exporter fixed; polish: 4 failures that the 17:05 page has too (the operator columns on the strip,
the folded line during the replay), not from these parts.

# Tenth part: a turn ends with a step; the tokens of a step, as they are written (2026-11-22, during s053)

The operator, on s053 (turns 1 and 2: guesses and readings only, no hypothesis): "Turn 1 and 2 passed without any hypothesis are not what I
intended. Fix it", and on the page's track of a turn: "When user clicks past or ongoing stage here they should be able to see tokens directly".

1. **CONTINUES = 2** (every arm): a reply that states no hypothesis, test, drop, verdict, objection or report is followed by another call of the
   researcher in the same turn, at most twice; what it asked for is answered at once and stands in the ledger it is shown ("THIS TURN GOES ON
   (your reply 2 in this turn, at most 3) ..."; the third is told it is the last of its turn). Readings still cost no simulation; a free turn may
   continue too. No new turn record for a continued reply; now.json's reply step carries its round. The instructions say it in one sentence:
   prompt.txt's requests ("the results come back at once, in the same turn ... a turn ends with a step"; the arm "plain" has its own words: no
   experiment or report), the supervised arm's ("Up to six requests in a reply; the results come back at once ..."): 9,645 characters, one limit
   of 10,000. Scripts written before keep one reply per turn (scripted.py sets CONTINUES = 0 unless a check sets it).
2. **Streamed calls and live_call.json** (every arm): `post_stream()` asks the model server for a stream (the same answer, reasoning and token
   counts as before); while a call comes in, live_call.json beside the ledger holds its number, turn, agent, step, what was written so far and
   whether it is done, about once a second. The page reads it for the step being worked on (the tokens grow in place).
3. **Every call names its step** in calls.jsonl (now.json's step, about and round), so that a step of the page's track opens its calls.

Checks: `test_continue.py` (new: three replies in turn 1, then the step; three without a step end the turn; the arm "hypotheses"; the
instructions), `test_stream.py` (new: one real streamed call to the local model server; SKIP when it does not answer), `test_now_steps.py`
(every call's step). The suite caught one fault before the deploy: the new sentence named "hypothesis" and "verdict" in the arm "plain"'s
instructions, which refuse those words (a plain session would not have started); fixed by a PLAIN replacement of its own.
4. **A ruling cut off in its findings is kept** (s053, turn 3: the supervisor's ruling on H2 was sound, then its findings ran on, "It is not a
   finding." to the limit of 9,000 tokens; the answer could not be read and H2 stayed open; at temperature 0 asking again would give the same):
   an answer of the supervisor cut off in its findings, which stand last in its format, is kept without them (`findings_cut`), and the ruling's
   record gets a note. On s053's own answer: inconclusive, not_about_the_guess. Check: `test_ruling_cut.py` (new); scripted.py sends a supervisor
   answer {"_raw": text} as that text.

# Eleventh part: after the review of s050 to s053 (2026-11-22, night; see plans/2026-11-22-review-s050-s053.md on main)

- `SHORT_CALL_TOKENS = 12,000` for a repair and a restatement (the operator's choice: 6,000 of them reasoning; they took 2 to 6 minutes at a whole
  reply's 32,000).
- A hypothesis whose test was checked and that waits for its ruling does not keep a new hypothesis out (s053: "H2 is still open and untested").
- `rule_missing()`: a checked hypothesis without a ruling gets the supervisor's ruling asked for again at the start of the next turn, once.
- The repair prompt says that a rule naming only simulations already run is refused, and that a simulation may change the network when the brief
  allows it (an interim sentence: the plan's item 1 replaces it with the change shown and a correct example).
- Check: `test_ruling_cut.py` gains R (a missing ruling asked for again at the next turn) and W (a checked hypothesis waiting for its ruling keeps
  nothing out).

**Held, not deployed** (the operator, 2026-11-22: "Build on the review branch; don't deploy"): the tenth and eleventh parts. The deploy build
(`derive_dep.py` of this branch) passed every harness check that has finished: 22 pass, 3 report SKIP (parts 2 and 3 off), none failed.

# Stage 1 of the coherence audit: records and crashes (2026-11-22, night; plans/2026-11-22-coherence-audit.md on main)

Built on this branch, not deployed (the operator: all stages in order, nothing deployed without their word). Each item names the audit's number.
- 1. **Ids by position** (s1_ids.py). A new guess or hypothesis keeps the id of its position for its own answer's references (from_why, revises,
  tests, decision_rules.for, needs.for, decision refs). A reference to a refused part is refused, saying which part. The automatic "work" decision
  uses this reply's guesses. Scripts written for the old shifting numbering were renumbered (test_format_fix.py T1, T2).
- 2, 12. **The supervisor is shown its answer's fields** (fields_text, generated from each schema) in every request; fields without a description
  got one. The ruling's findings have the finding's format, name included (s1_show.py).
- 3. **A planned simulation's network change** is shown in the test review, its follow-up, the repair and the round's record (s1_show.py).
- 4. **The ruling's doubt_if** comes only from the supervisor's own reviews (s1_show.py).
- 5, 6. **Guards** (s1_guards.py): each measurement and the probe are guarded on their own; a check that cannot be computed is "not checked";
  abs/min/max arity is refused when a rule is read; measure() keeps each value with its own time and says when it is defined nowhere. tools.py and
  decision_rules.py are patched on both builds: derive_dep.py applies the patch to the live tools.py and network.py.
- 7. **Measurements are checked against each design's own network** (s1_measures.py).
- 8. **The list of varied knobs** is cut when the harness removes designs (s1_varied.py).
- 9. **REQUESTS_MOST = 3** in the single-AI arms: stated in prompt.txt, set as maxItems, and a cut is noted (s1_requests.py).
- 10. **Budget**: repairs are charged against each other; "left" is never below 0; a continued session rebuilds sims, budget, free turns and
  giving_up from its ledger (s1_loop.py).
- 11. **The last turns**: findings and decisions alone are not usable; a reply with no report ends the session (s1_loop.py).
- 13. **The baseline and the first look** run inside the guard; a model error at the look gives a note (s1_loop.py).
- 14. **The link line** has no space inside a value (s1_net.py; both network.py builds).

Checks:
- New: test_ids_position.py, test_varied.py, test_stage1.py (A–G).
- Each was shown to fail on the code before stage 1, where it replays a session's failure: test_ids_position, test_varied, test_stage1's D.
- The full suite on both builds is running.

# Stage 2 of the coherence audit: one source per rule, each arm told what it can do (2026-11-22, night)

Built on this branch, not deployed. Each item names the audit's number. Patches: s2_texts.py (15, 16, 22–24), s2_more.py (17–22, 25); the start-up
check of stated numbers, the figures and the page's words for "not_run" were edited directly.
- 15. **The arm "plain"** gets its own wording of the network-change text (STRUCTURE), the last turn, the free turns, a continued reply and the
  brief's how_to_run. Its whole system text is checked at the start for hypothesis, verdict, decision rule and rethink (the check ran before
  STRUCTURE was added: its text named "hypothesis" and "decision rule").
- 16. **The arm "supervised"**: no "rethink it" in its ledger text; its report has open_questions (it was told to fill them, then blamed);
  a checked hypothesis without a ruling may be dropped (only the supervisor rules); a from_why refusal speaks of guesses, not of "worth".
- 17. **The follow-up question** on a review whose boxes disagree shows the supervisor the rival its review named and its own feedback. Its box
  rival_is_weak may change: s052 H2's feedback named a stronger rival, the question asked only about the researcher's, the test was approved, and it
  was ruled inconclusive for that very rival. It is asked with 2,000 tokens, 1,000 of them reasoning (the operator's choice). A follow-up that
  cannot be read is a refusal; it was a run unreviewed.
- 18. **A harness refusal in the last round** is "not_run", by the harness, and the hypothesis stays open. It was "contested", the supervisor's word
  for a test that runs. The figures count it (not_run, only where it occurs); the page names it.
- 19. **The repair prompt**: runs given replace those of the same label and add new ones, and the others are kept (the prompt said "only if they must
  change", while any list replaced all of them). It states the exemption for a measurement of the answer's own, and that no new simulation can run
  when none is left. It shows the records the feedback and the guess cite, and the measurements the answer defined; a repaired rule may name one a
  sibling test defined. On a network brief, it shows one change written correctly for that network, built and checked on the brief (for
  again_again: remove the queue on l1, then add a scheduler on l1; note: on that brief this example is also the change that lets TCP through).
  A run keeps its change unless the feedback is about it. A refused network change ends with the same example.
- 20. **The ruling** is shown the researcher's rival and what it said the rule gives under it, a stronger rival the review named, and the
  measurements the experiment defined. **The objection's second look** is shown the readings, the rivals and the measurements, and says whether the
  test was fair: "supported" or "refuted" from an unfair test is inconclusive.
- 21. **A ruling asked for again** at the start of a turn is in that turn's ledger text (it was rendered before).
- 22. **Continued replies**: turns with requests only are counted by turn, not by reply (LOOK_TURNS = 3 names the old literal); a due finding's
  note says it is asked for again in the next reply of the same turn when the turn goes on. (The pairing of the automatic "work" decision and the
  note on requests cut in the last turns were stage 1.)
- 23, 24. **A label's length** (LABEL_MOST = 20) is stated in the instructions, the answer format (maxLength) and the refusal. The free turns say
  that a test on simulations already run needs a measurement of its own.
- 25. **Smaller**: == holds within the session's tolerance, as the turn's text says two results are equal (decision_rules.EQUAL_WITHIN); an unread
  guess review is shown as unread, not as sound; gate 0's "refused once, then accepted" is per turn (it was per session); learned_since counts
  simulations and leaves out the harness's rounds; the restatement is shown the records learned since, not only their ids; session.json counts
  calls by agent (calls_by_agent; "calls" stays the researcher's); a report given with an experiment waits for that experiment's results.
  Examined, unchanged: "re-reviewed twice after a changed restatement" (the two reviews are of the first statement and of the restatement, as
  designed; no third call was found); the report's expected values stay the brief's outputs (a design question); the two-hosts columns were
  fixed earlier (TWO_HOSTS_COLUMNS); the deployed and branch texts are made one by derive_dep.py.
- **One source per rule**: at the start the harness checks that the numbers its instructions state for a label's length and the requests of one
  reply are the constants it enforces (stated_rules); a session whose texts disagree does not start.
- **Corrected while checking** (found by the checks of this stage and the next):
  - item 19: a repair's runs are read against the last test the harness ACCEPTED; a repair the harness refused is not the base (its garbled network
    change was kept by an empty runs list: test_repair_structure). The repair prompt shows that refused repair beside the test (s2_fix_base.py);
  - item 25: gate 0's reading is kept by the guess, its records AND its result: a restatement that corrects its result is read again (it was recorded
    "contested" on the reading of its first statement: test_stage4 D) (s2_fix_gkey.py);
  - item 25: "refused once" in a turn is the default; REFUSED_ONCE = "session" keeps the rule before part D for test_supervised.py, whose session
    has no restatements (s2_fix_once.py). test_supervised.py also expects open_questions in the report (item 16).

Checks:
- New: test_stage2.py (P, B, C, D, N, F, G, H, J, K, U): passes on this build. On the stage-1 build it fails at each fault it replays (14 failures).
- Every harness check on this build and on the build to deploy (derive_dep.py: parts 2 and 3 off): all pass (the deploy build skips the three checks
  of parts 2 and 3). The checks the late corrections touch were run again on both builds after them: test_supervised, test_guess_restate,
  test_design_rounds, test_now_steps, test_stage1, test_stage2, test_repair_structure.
