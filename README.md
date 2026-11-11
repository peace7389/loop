# Two hosts, one link: an AI hypothesis loop over an ns-3 simulation

A local language model is asked a networking question about a simulated system it cannot see inside. It works only
through a ledger: hypothesis -> prediction -> experiment (with a pass rule written first) -> evidence from the
simulator -> verdict. The harness runs the experiments; a viewer shows what the numbers did and why the model chose
each run. This repository is a snapshot of the working folder (`~/project` on the research server).

## What is where

| Path | What it is |
|---|---|
| `HARNESS_SPEC.md` | The build specification: purpose, decisions, what was verified against ns-3 |
| `scratch/two-hosts/` | The ns-3 scenario: `two-hosts.cc` and the weighted scheduler `wrr-queue-disc.{h,cc}` (a copy; it is built inside an ns-3.49 tree) |
| `harness/loop.py` | The loop: builds the prompt from the ledger, asks the model once per turn, runs what it asked |
| `harness/tools.py` | Everything the model can reach: read-only tools and `run()` |
| `harness/manifest.json`, `prompt.txt`, `schema.json` | The task as the model sees it, the prompt, the answer format |
| `harness/control.py` | The operator's small server for the viewer (port 8600); `make_trace.py` records packet events |
| `ledger.jsonl` | The AI session's record: scratch (reasoning), hypothesis, experiment, evidence, verdict, note, malformed |
| `runs/index.json` | Every run the model can see: id, params, metrics. `runs/operator.jsonl`: the scheduler mode of each (hidden from the model) |
| `runs/<id>/` | One simulation: `params.json`, `metrics.json`, `series.csv` (a sample every 0.1 s) |
| `checks/` | Operator checks of the simulator itself (no AI), with the command of each |
| `trace/` | Short packet-level event recordings made by the operator |
| `viewer/` | The viewer: `index.html` + `adrs_view.js` (one page); `index_full.html` + `adrs_view_full.js` is the earlier six-page version |

## Not in the repository

The ns-3.49 source tree and its build, the per-run `flowmon.xml` files, packet captures. The harness expects the
project at `~/project` with ns-3 built in `~/project/ns-3.49`, and a model served at `http://127.0.0.1:18000/v1`,
so the Python parts read here but do not run without those.

## Updating

`./snapshot.sh` re-copies the scenario and the specification and stages everything; then commit and push.
