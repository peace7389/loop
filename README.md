# Two hosts, one link: an AI hypothesis loop over an ns-3 simulation

A local language model is asked a networking question about a simulated system it cannot see inside. It works only
through a ledger: hypothesis -> prediction -> experiment (with a pass rule written first) -> evidence from the
simulator -> verdict. The harness runs the experiments; a viewer shows what the numbers did and why the model chose
each run. This repository is a snapshot of the working folder (`~/project` on the research server).

## What is where

| Path | What it is |
|---|---|
| `HARNESS_SPEC.md` | The build specification: purpose, decisions, what was verified against ns-3 |
| `scratch/two-hosts/` | The ns-3 scenario: `two-hosts.cc` and the scheduler `link-queue-disc.{h,cc}` (a copy; it is built inside an ns-3.49 tree) |
| `harness/loop.py` | The loop: builds the prompt from the ledger, asks the model once per turn, runs what it asked. `--session <id>` chooses the session (default: a new id `sNNN`) |
| `harness/tools.py` | Everything the model can reach: read-only tools and `run()`. Every path is inside the current session's folder; a run id is accepted only if that session's own index lists it |
| `harness/manifest.json`, `prompt.txt`, `schema.json` | The task as the model sees it, the prompt, the answer format |
| `harness/control.py` | The operator's small server for the viewer (port 8600); `make_trace.py` records packet events |
| `sessions/<id>/` | One session = one complete attempt by the model, in its own folder; sessions know nothing about each other. `s001` is the first session (2026-11-09) |
| `sessions/<id>/ledger.jsonl` | The session's record: draft (what the model wrote before its answer), hypothesis, experiment, evidence, verdict, note, malformed |
| `sessions/<id>/runs/index.json` | The session's own simulations, the only ones its tools can see: id, params, metrics |
| `sessions/<id>/runs/<run>/` | One simulation: `params.json`, `metrics.json`, `series.csv` (a sample every 0.1 s) |
| `sessions/<id>/two-hosts.cc` | The scenario source as that session could read it (sessions made since 2026-11-11) |
| `checks/` | Operator-only: nothing here is reachable through `harness/tools.py` |
| `checks/operator.jsonl` | The scheduler mode and run time of every simulation, by session and run (the mode reaches the simulation as the environment variable `TWOHOSTS_SCHED`, not as an option) |
| `checks/build1/` | The operator's first checks of both scheduler modes (`sanity-*`, `share-*`, `cap-*`), with their `index.json` |
| `checks/build2/`, `checks/build3/` | Operator checks of the revised simulator, with the command of each and `results.json` |
| `trace/` | Short packet-level event recordings made by the operator |
| `viewer/` | The viewer: `index.html` + `adrs_view.js` (one page); `index_full.html` + `adrs_view_full.js` is the earlier six-page version |

## Not in the repository

The ns-3.49 source tree and its build, the per-run `flowmon.xml` files, packet captures. The harness expects the
project at `~/project` with ns-3 built in `~/project/ns-3.49`, and a model served at `http://127.0.0.1:18000/v1`,
so the Python parts read here but do not run without those.

## Updating

`./snapshot.sh` re-copies the scenario and the specification and stages everything; then commit and push.
