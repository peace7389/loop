# Two hosts, one link: an AI hypothesis loop over an ns-3 simulation

A local language model is asked a networking question about a simulated system it cannot see inside. It works only
through a ledger: hypothesis -> prediction -> experiment (with a decision rule stated first) -> evidence from the
simulator -> verdict. The harness runs the experiments; a viewer shows what the numbers did and why the model chose
each run. This repository is a snapshot of the working folder (`~/project` on the research server).

## What is where

| Path | What it is |
|---|---|
| `HARNESS_SPEC.md` | The build specification: purpose, decisions, what was verified against ns-3 |
| `scratch/two-hosts/` | The ns-3 scenario: `two-hosts.cc` and the scheduler `link-queue-disc.{h,cc}` (a copy; it is built inside an ns-3.49 tree) |
| `briefs/<id>.json` | A brief: the assignment a person writes before a session. Task, a plain-language description of the system, the fixed settings (`system`), the settings the model may change (`knobs`), the goal (open, or a target with conditions) and the limits |
| `harness/loop.py` | The loop: builds the prompt from the ledger, asks the model once per turn, does what its answer asks. A turn may state hypotheses, drop them, give verdicts and design one experiment of several simulations, run at once. `--brief <id>` chooses the brief of a new session, `--session <id>` the session (default: a new id `sNNN`) |
| `harness/decision_rules.py` | The decision rules of a test experiment: comparisons the model states before the simulations run (`measure@label > 1.1 * measure@other AND ...`), read and checked by the harness itself. Each comes with a rival explanation under which it would fail; one that would hold under the rival too is refused |
| `harness/tools.py` | Everything the model can reach: read-only tools and `run()`. Every path is inside the current session's folder; a run id is accepted only if that session's own index lists it |
| `harness/manifest.json`, `prompt.txt`, `schema.json` | What is the same for every brief (the outputs and the tools, described), the prompt, the answer format |
| `harness/score.py` | Operator tool: `score.py <session>` scores a finished session against the sweep of its brief and scheduling policy |
| `harness/control.py` | The operator's small server for the viewer (port 8600): lists sessions and briefs, starts sessions, operator runs and sweeps, saves new briefs; `make_trace.py` records packet events |
| `sessions/<id>/` | One session = one complete attempt by the model, in its own folder; sessions know nothing about each other. `s001` is the first session (2026-11-09) |
| `sessions/<id>/ledger.jsonl` | The session's record: draft (what the model wrote before its answer), hypothesis, drop, experiment, simulation, evidence (one line per simulation), check (a decision rule with the measured numbers, held or failed), verdict, request and result (a tool request and what came back), note, malformed. Each record has `by`: who produced it (`model`, `harness`, `simulator` or `operator`), written by the harness. `s001` is in the earlier format: one simulation per experiment, no checks |
| `sessions/<id>/runs/index.json` | The session's own simulations, the only ones its tools can see: id, params, metrics |
| `sessions/<id>/runs/<run>/` | One simulation: `params.json`, `metrics.json`, `series.csv` (a sample every 0.1 s) |
| `sessions/<id>/session.json` | What the session was given (`given`: its brief with the description filled in, plus the output and tool descriptions), the model, the start time and the flags; at the end: when and how it ended (`how`), the report's ledger id, and the hypotheses left open. `s001` was made before briefs and has none |
| `sessions/<id>/report.json` | The model's final report, as accepted by the harness: goal, recommendation, expected values, explanation, when it holds and breaks, claims with the ledger ids that support them, open questions |
| `checks/` | Operator-only: nothing here is reachable through `harness/tools.py` |
| `checks/operator.jsonl` | The scheduling policy (how the scheduler divides the link: share or cap) and the run time of every simulation, by session and run. The policy reaches the simulation as the environment variable `TWOHOSTS_SCHED`, not as an option. Lines written before 2026-11-11 call it `mode` |
| `checks/build1/` | The operator's first checks of both scheduling policies (`sanity-*`, `share-*`, `cap-*`), with their `index.json` |
| `checks/build2/`, `checks/build3/` | Operator checks of the revised simulator, with the command of each and `results.json` (checks 1 to 11 in `build3`) |
| `checks/sweeps/<id>/` | A sweep: every combination of a grid of knob values for one brief and one scheduling policy, run by the control server (`POST /api/sweep`). `table.csv` has one row per simulation, `status.json` the progress |
| `checks/keys/<brief>.json` | The answer key of a brief: which sweep belongs to which scheduling policy, notes, and the checklist a session is judged by |
| `checks/scores/<session>.json` | The score of a finished session, written by `harness/score.py`: best row of the sweep for the goal, the model's recommendation against it, simulations used, the checklist with the operator's judgements |
| `trace/` | Short packet-level event recordings made by the operator |
| `viewer/` | The viewer: `index.html` + `adrs_view.js` (one page); `index_full.html` + `adrs_view_full.js` is the earlier six-page version, whose Control page holds the operator's forms, including the brief editor (`brief_editor.js`) |

## Not in the repository

The ns-3.49 source tree and its build, the per-run `flowmon.xml` files, packet captures. The harness expects the
project at `~/project` with ns-3 built in `~/project/ns-3.49`, and a model served at `http://127.0.0.1:18000/v1`,
so the Python parts read here but do not run without those.

## Updating

`./snapshot.sh` re-copies the scenario and the specification and stages everything; then commit and push.
