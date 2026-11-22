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
