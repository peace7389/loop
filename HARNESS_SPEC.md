# Build specification: AI hypothesis-loop harness over ns-3

You are building a small research harness. Read this whole document before
writing anything. Every item marked **DECISION** is final; do not revisit it.
Items marked **VERIFY** must be checked against the actual ns-3 source on this
machine before use, because the API shifts between releases. Verification
pass of 2026-11-09 (ns-3.49 source, vLLM 0.32.0 live): every VERIFY item below
is resolved and marked **VERIFIED**; decisions taken from that pass are marked
**DECISION (2026-11-09)**.

## 1. Purpose

**Nominal task** (what the local LLM is told): two computers connected by a
single wire. One sends, one receives. The sender uses UDP and TCP at the same
time, both at maximum rate. A scheduler on the sender splits the link between
them by a configurable ratio. Find the best ratio for performance.

**Real purpose** (what the harness is for): to observe whether a local LLM can
read the state of a system, form a hypothesis, design an experiment with
pre-stated pass/fail criteria, run it, judge the result against those criteria,
and choose the next step accordingly, repeatedly. The ratio itself is not the
point; the chain of reasoning is. The harness must make that chain an
official, inspectable record.

**Background the harness designer relies on** (do not put this in the LLM's
prompt; the LLM is supposed to discover it):
- UDP has no congestion control; it sends whatever it is allowed. TCP backs
  off on loss. Under a work-conserving weighted scheduler, every TCP backoff
  momentarily empties the TCP queue and the scheduler gives that slot to UDP,
  so the measured split skews toward UDP above its configured weight while
  link utilisation stays near 100%. Under a true rate limiter the slot is
  wasted and utilisation drops. Same configured number, two fingerprints.
- With both flows saturating the link, the aggregate throughput is pinned at
  line rate, so "best ratio" has no answer without a stated objective. A good
  reasoner notices this.
- In ns-3 there is no socket backpressure for UDP: the application pushes
  packets into the stack and excess is dropped at the queue disc. So UDP loss
  at the sender is always "self-inflicted" by the configured weight and queue
  size. This is a simulator property, not a Linux one.

## 2. Non-negotiable principles

**DECISION: minimal code.** Every file has a size budget (section 5). If a file
grows past it, something is in the wrong place. No frameworks, no agent
libraries, no ORM, no web backend. Dependencies: Python standard library plus
`requests`. Nothing else.

**DECISION: strict write ownership.**
- ns-3 writes only inside `runs/<id>/`.
- `harness/loop.py` writes only `ledger.jsonl` and `runs/index.json`.
- `harness/tools.py` and `viewer/` write nothing.
- The LLM writes nothing. It returns JSON to `loop.py`, which decides what to
  append.

**DECISION: the LLM never produces a result.** Evidence records are written by
the harness from files ns-3 produced. The LLM may only propose experiments and
interpret evidence the harness attached.

**DECISION: pre-registration.** An experiment is accepted only if it carries
pass/fail criteria stated before it runs. The schema rejects experiments
without `pass_if`.

**DECISION: the ledger is the only memory.** Each turn's prompt is rebuilt from
`ledger.jsonl`. The LLM has no other state. This makes the reasoning auditable
and prevents drift.

**DECISION: LLM discretion is "which tool to call and which experiment to
design", nothing else.** No shell, no file writes, parameters clamped to
ranges in `manifest.json`, a run budget per session.

## 3. Environment facts (from the machine report; do not re-derive)

- Host: `ece-silbmark2`, Ubuntu 24.04.4, kernel 6.8, 256 cores, ~2 TB RAM.
- Home is Lustre, 95% full. Keep per-run output small. **DECISION: pcap off
  by default**; a flag may enable it for one run.
- No sudo. No system package installs. ninja is absent; cmake's default
  generator is already working. Do not try to install ninja.
- ns-3: `~/project/ns-3.49`, built with `--build-profile=optimized
  --enable-examples`. Logging and asserts are compiled out; `./ns3 run first`
  exits 0 with no output, which is correct.
- ns-3.49 API facts already verified: the `Tos` attribute lives in
  `SourceApplication` and is inherited by `OnOffApplication` and
  `BulkSendApplication`; `Priomap` has `ATTRIBUTE_HELPER_CPP`, so a
  space-separated string value parses; `Socket::IpTos2Priority` is in
  `src/network/model/socket.cc`; schedulers present are fifo, pfifo-fast,
  prio, tbf; **no DRR or WRR exists in this version**.
- Python for the harness: conda base, `/home/chunguck.kim/miniforge3/bin/python3`,
  Python 3.14.7, has `requests`. **DECISION: use this interpreter; add nothing.**
- Model server: vLLM 0.32.0 already running, OpenAI-compatible, at
  `http://127.0.0.1:18000`, pinned to GPUs 6 and 7, serving a Qwen model.
  **DECISION: use this endpoint. Do not install or start Ollama.** Get the
  exact model id from `GET /v1/models` at startup and use it verbatim: take
  the FIRST entry of `data` (currently `Qwen/Qwen3.8-Flash-Next-FP8`; the
  second entry is an alias). Do not hardcode it. The server runs with the
  qwen3 reasoning parser, so thinking is ON by default; see 7.4.
- Ports in use: 8000, 8080, 8766-8768, 8899, 9401, 9405, 18000, 18099.
  **DECISION: viewer port is 8600**, served with
  `python3 -m http.server 8600 --directory ~/project`, reached via
  `ssh -L 8600:localhost:8600`.
- An unrelated system called ADRS exists on this machine (ports 8766-8768,
  `~/ADRS/.venv`). **DECISION: this harness is separate from ADRS.** Do not
  import from it, do not write into it, do not share its ports.

## 4. Directory layout

**REVISED 2026-11-11 (operator; stage 1 of `~/RESTRUCTURE_PLAN.md`): one folder per
session.** This block replaces `ledger.jsonl`, `runs/` and `runs/operator.jsonl`
in the layout below and wherever sections 2, 7 and 8 name them.
```
~/project/
├── sessions/<id>/                 # one session; ids s001, s002, ...; nothing is shared between sessions
│   ├── ledger.jsonl               # append-only, written only by loop.py
│   ├── runs/index.json            # this session's simulations only
│   ├── runs/<run>/                # params.json, metrics.json, series.csv, flowmon.xml (run ids r001, ... per session)
│   └── two-hosts.cc               # the scenario source as copied when the session was created; what read_source returns
└── checks/                        # operator-only: no function of tools.py reads here
    ├── operator.jsonl             # {session, id, mode, seconds} per simulation, appended by loop.py
    ├── build1/                    # the stage 1-2 runs sanity-*, share-*, cap-* and their index.json
    ├── build2/, build3/           # the operator checks of the revised simulator
    ├── op-<time>/, control.jsonl  # operator runs started from the viewer
    └── sessions/<id>.log          # terminal output of a session started by control.py
```
- `loop.py --session <id>`: default a new id (the next free `sNNN`); an existing
  id continues that session (no second baseline). The session folder is created
  after the model server has answered.
- `tools.py`: `open_session(id)` sets the one folder the tools can reach.
  `list_runs` reads that session's `runs/index.json`; `metrics`, `series` and
  `grep_trace` refuse (`unknown run`) any id that index does not list, so no
  name or path can reach another session or `checks/`. `run` returns the run
  time; it no longer writes the operator's line (loop.py does).
- `control.py`: `GET /api/status` carries `sessions` (id, records, experiments,
  first and last time, mode, model, running); `GET /api/sessions` is that list
  alone; `POST /api/session` starts a new session, or continues one when given
  `"session": "<id>"`.
- Viewer: the page lists the sessions (newest first) and "Operator checks of the
  simulator" in one selector, `?session=<id>`; in the ADRS main viewer each
  session is a run of the task (`run=loop` = the newest).
- Migration: the first session's ledger and runs `r001`-`r006` are
  `sessions/s001/` (`r001` is the stage-3 `tools.run` test, kept with it as the
  operator asked). Its lines in `operator.jsonl` gained `"session": "s001"`.
  `s001` has no `two-hosts.cc` copy: the file it read was not kept.
- Verified: in a fresh session `list_runs()` is `[]` and `metrics("cap-200m")`,
  `metrics("r002")` are refused; the page content built for `s001` is identical,
  character for character, to what the old single ledger gave.

```
~/project/
├── ns-3.49/                       # upstream; touch only scratch/
│   └── scratch/two-hosts/
│       ├── two-hosts.cc           # scenario (provided; see 6.1)
│       ├── wrr-queue-disc.h       # weighted scheduler (to write; see 6.2)
│       └── wrr-queue-disc.cc
├── harness/
│   ├── loop.py                    # the only control flow        <= 150 lines
│   ├── tools.py                   # read-only functions          <= 100 lines
│   ├── schema.json                # LLM turn format, enforced by vLLM
│   ├── manifest.json              # what the LLM is told about the system
│   └── prompt.txt                 # fixed system prompt, plain text
├── viewer/
│   └── index.html                 # static, vanilla JS + Chart.js CDN <= 250 lines
├── runs/
│   ├── index.json                 # one line per run: {id, params, metrics}
│   └── <id>/                      # metrics.json, series.csv, flowmon.xml
└── ledger.jsonl                   # append-only
```

All files in `scratch/two-hosts/` build as one program. **VERIFIED:** ns-3
names it after the one source file that contains `main`, prefixed by the
directory, so with `two-hosts/two-hosts.cc` the program is `two-hosts` and
`./ns3 run two-hosts` works. The configure step fails if more than one file in
the directory matches the regex `main[(| (]` (no word boundary: a comment or
identifier containing `main(` or `main (` counts). Only `two-hosts.cc` may
contain that text; see section 9.

## 5. Build order and acceptance tests

Build in this order. Do not start a stage until the previous one passes.

### Stage 1: scenario with the stock strict-priority scheduler
Place the provided `two-hosts.cc` (section 6.1) in `scratch/two-hosts/`,
build, and run two sanity cases:

```
./ns3 run "two-hosts --udpRate=2Gbps  --out=$HOME/project/runs/sanity-2g"
./ns3 run "two-hosts --udpRate=400Mbps --out=$HOME/project/runs/sanity-400m"
```

Pass criteria (1 Gbps link, 10 s):
- 2 Gbps case: `udp_goodput_bps` ≈ 0.9-0.97e9, `tcp_goodput_bps` near 0,
  `drops_band0` large (hundreds of thousands), `link_util` ≈ 1.
- 400 Mbps case: `udp_goodput_bps` ≈ 0.4e9, `tcp_goodput_bps` ≈ 0.5-0.6e9,
  `drops_band0` = 0.
- `series.csv` has ~100 rows with the header in section 6.3.
If both flows share the link roughly equally in the 2 Gbps case, the
priority mapping is broken; suspect the `Priomap` string or the `Tos` value.

**Status (2026-11-09): stage 1 PASSED.** No provided `two-hosts.cc` existed on
the machine, so it was written to 6.1 (170 lines, stock `PrioQueueDisc`,
2-band `Priomap` "1 1 1 1 1 1 0 0 1 1 1 1 1 1 1 1", TCP buffers 1 MB, segment
size mtu-40; `link_util` measured from the device's PhyTxEnd bytes over
exactly [1 s, duration+1 s]). Results: 2 Gbps -> udp 0.979e9, tcp 0.84e6,
drops_band0 911478, drops_band1 0, link_util 1.000; 400 Mbps -> udp 0.400e9,
tcp 0.563e9, drops_band0 0, drops_band1 170, link_util 1.000; series.csv 100
rows + header; each run folder 5.5 KB (pcap off). The UDP goodput at 2 Gbps is
0.979e9, just above the 0.9-0.97e9 written above: 1400-byte payloads carry 30
bytes of UDP/IP/PPP headers, so 1400/1430 = 0.979 is the ceiling. Stage 2
may start.

### Stage 2: weighted scheduler
Write `wrr-queue-disc.{h,cc}` per section 6.2, switch `two-hosts.cc` to use
it, rebuild, and run the ratio sweep:

```
for w in 0.2 0.5 0.8; do ./ns3 run "two-hosts --weightUdp=$w --out=.../w$w"; done
```

Pass criteria: `udp_goodput_bps / link_rate_bps` within roughly ±10% of
`weightUdp`, and `link_util` ≈ 1 in all three. (The original criterion also
asked for the share to sit consistently above the weight, the TCP-backoff
skew; measured 2026-11-09 it sits exactly at the weight in wire bytes because
the TCP band never empties at `queuePkts=100`. **DECISION (operator,
2026-11-09): the ±10% criterion alone; queue depth unchanged.**) Then run `--weightUdp=0.5 --udpRate=200Mbps`
(default mode `share`): UDP ≈ 0.2e9, TCP ≈ 0.75e9, `drops_band0` = 0. That
run proves the scheduler is work-conserving (a floor, not a cap). If TCP
stays near 0.5e9 in `share` mode, the scheduler is behaving like a rate
limiter and is wrong.

Then the same run with `--mode=cap --weightUdp=0.5 --udpRate=200Mbps`: UDP
≈ 0.2e9 and **TCP ≈ 0.5e9, not 0.75e9**, the opposite of the `share` result.
That difference is the whole point of having two modes; stage 2 passes only
when both fingerprints are reproduced. Also run `--mode=cap --weightUdp=0.5`
with the default 2 Gbps UDP: UDP ≈ 0.5e9 (capped), TCP takes the rest.

**Status (2026-11-09): stage 2 PASSED (operator confirmed both open points, see
section 10).** `wrr-queue-disc.h` 45 lines, `.cc` 158 lines; `two-hosts.cc` now
installs `ns3::WrrQueueDisc` (WeightUdp, Mode, LinkRate) and also writes
`params.json` per run for the run index. Results (1 Gbps link, 10 s):

| run | udp/link | tcp | link_util | drops0 | drops1 |
|---|---|---|---|---|---|
| share w=0.2 | 0.196 | 0.761e9 | 1.000 | 1,610,938 | 464 |
| share w=0.5 | 0.489 | 0.476e9 | 1.000 | 1,348,803 | 230 |
| share w=0.8 | 0.783 | 0.191e9 | 1.000 | 1,086,239 | 224 |
| share w=0.5, udp 200 Mbps | 0.200 | 0.756e9 | 1.000 | 0 | 369 |
| cap w=0.5, udp 200 Mbps | 0.200 | **0.477e9** | **0.706** | 0 | 542 |
| cap w=0.5 | 0.490 | 0.475e9 | 1.000 | 1,347,938 | 256 |
| cap w=0.2 / 0.8 | 0.196 / 0.783 | 0.761 / 0.191e9 | 1.000 | | |

Met: ±10% of the weight; `link_util` ≈ 1 in share mode; share floor (TCP
0.756e9 at 200 Mbps UDP); cap fingerprint (TCP 0.477e9, utilisation 0.71).
NOT met: "consistently above the weight". UDP's share is exactly the weight
in wire bytes (0.979 × weight in goodput, the 30-byte header overhead), i.e.
no TCP-backoff skew: with CUBIC, a 100-packet band queue and 1 MB buffers the
TCP band is practically never empty (230-464 TCP drops in 10 s), so DRR has no
idle TCP slot to hand to UDP. The skew would need a shallower queue or more
loss. Left as measured, not tuned; operator to decide (section 10).

### Stage 3: harness without the LLM
Write `tools.py`, `manifest.json`, `schema.json`. Test `tools.run()` from a
Python shell: it must clamp out-of-range params, create `runs/<id>/`, invoke
ns-3, parse `metrics.json`, and append to `runs/index.json`. Test the model
endpoint with one hand-written request using `schema.json` as
`response_format`; the reply must parse as JSON that validates.

**Status (2026-11-09): stage 3 PASSED.** `tools.py` 93 lines, `manifest.json`,
`schema.json`. `tools.run()` clamped weightUdp 2.0 -> 0.95, udpRate 5Gbps ->
3000Mbps, queuePkts 5 -> 10, TcpBogus -> TcpCubic, dropped an unknown key,
created `runs/r001/`, ran ns-3 without rebuilding (4 s for a 2 s run), parsed
`metrics.json`, appended to `runs/index.json` and `runs/operator.jsonl`;
`metrics/series/grep_trace/list_runs` work; `read_source("wrr-queue-disc.cc")`
= "not available"; `metrics("../harness")` rejected. Endpoint test with the
real schema: valid JSON with thinking off (834 tokens) and on (5156 tokens,
4430 reasoning).

### Stage 4: the loop
Write `loop.py` and `prompt.txt`. Run with a budget of 5 experiments. Pass
criteria: `ledger.jsonl` contains at least one hypothesis, one experiment with
`pass_if`, one evidence record written by the harness, and one verdict that
references the evidence id. Inspect the ledger by hand; the records must be
coherent.

**Status (2026-11-09): stage 4 PASSED.** `loop.py` 129 lines, `prompt.txt`.
`--budget 5 --thinking on --mode share`: 12 turns, 25 min, 37 ledger records
(15 scratch, 5 hypothesis, 5 experiment with pass_if, 5 evidence from the
harness, 3 verdicts citing E ids, 1 tool-only note, 3 malformed). Chain is
coherent: H1 (work-conserving 50/50) -> X1/E1 -> V1 supported -> H2 (w=0.95)
-> V2 -> H3 (w=0.05) -> V3 -> H4/H5 (w=0.49, 0.493 for a max-min goodput
objective the model chose itself). Finding: 6 of 15 model calls (40%) hit
`max_tokens` 8000 inside the reasoning (25-28k chars) and returned empty
content -> malformed; the successful calls used 4.8k-7.7k tokens. Operator
decision pending: raise the thinking budget (12-16k) or run with
`--thinking off`.

### Stage 5: viewer
Write `index.html`. Serve on 8600. It must render an existing ledger and runs
directory without any change to the harness.

**Status (2026-11-09): stage 5 PASSED.** `viewer/index.html` 98 lines (built
early, after stage 2, at the operator's request). Reasoning trail with folded
scratch records, run detail with the two charts, across-runs scatter and run
table (operator mode column from `runs/operator.jsonl`). Served by
`python3 -m http.server 8600 --directory ~/project --bind 127.0.0.1` in tmux
`harness_viewer`; reached from the Mac through `LocalForward
127.0.0.1:48600 127.0.0.1:8600` (8600 and 18600 were taken by VS Code's auto
forwarding there).

### Operator checks of the revised simulator (2026-11-10)
Eleven checks written by the operator, run in order by calling the built
program directly (outputs in `~/project/checks/build2/`, never in
`runs/index.json`), stopping at the first failure. Rule: a failure is a
simulation matter, not a model finding.

| # | Settings | Predicted | Measured | Result |
|---|---|---|---|---|
| 1 | UDP alone: weightUdp 0.95, udpRate 2Gbps, tcp=0 | UDP 0.979 Gbps, TCP 0, link use 1.00 | UDP 0.9790, TCP 0, use 1.0000 | pass |
| 2 | TCP alone: udpRate 0 | TCP about 0.965 Gbps, few retransmissions, no packet over 1500 bytes, no 32-byte tails | TCP 0.9640; 120 retransmissions in 10 s (0.013% of data packets); largest packet 1500 bytes; no 32-byte packets; no fragments | pass |
| 3 | share, weightUdp 0.2 / 0.5 / 0.8, both saturating | UDP/link = weight x 0.979 within 3%; use 1.00; drops in both bands | 0.1958 / 0.4895 / 0.7835 (all within 0.03%); use 1.0000; drops in both bands | pass |
| 4 | share, weightUdp 0.5, udpRate 200Mbps | UDP about 0.196, drops_band0 0, TCP about 0.76, use 1.00 | UDP 0.2000 (udpRate is the payload rate), drops_band0 0, TCP 0.7671, use 1.0000 | pass |
| 5 | share, weightUdp 0.5, queuePkts 8 | UDP/link 0.52-0.60, use 1.00, more retransmissions than check 3, TCP band empties periodically | UDP/link 0.4895 (no rise), use 1.0000, retransmissions 2295 (check 3: 71), TCP band never empty (lowest occupancy 2 packets) | **FAIL** |
| 6-11 | | | not run (stop rule) | |

Diagnosis of check 5 (same settings, one thing changed; the occupancy
instrument was confirmed on check 4, where the UDP band is seen empty in every
interval): the effect exists in the simulator but not at queue 8 with Cubic on
a 50 us link, because Cubic keeps 70% of its window after a loss and that is
still more than the link holds.

| Change from check 5 | UDP/link | TCP band emptied |
|---|---|---|
| queuePkts 4 (Cubic) | 0.5079 | every interval |
| TcpNewReno (queuePkts 8) | 0.5157 | every interval |
| TcpNewReno, queuePkts 4 | 0.5764 | every interval |
| linkDelay 5 ms (queuePkts 8, Cubic; not a manifest parameter) | 0.6810 | every interval |

Open decision for the operator: accept that the effect is reachable only with
queuePkts 4-7 or a non-Cubic variant, or change the scenario (a longer link
delay) so that it appears at the settings of check 5.

## 6. Simulator specification

### 6.1 `two-hosts.cc` (provided separately; do not rewrite from scratch)
Two nodes, one `PointToPoint` link. Node 0 sends, node 1 receives. UDP via
`OnOffApplication` at `--udpRate` with 1400-byte packets, `Tos=0x10` (maps to
socket priority 6). TCP via `BulkSendApplication`, `MaxBytes=0`, `Tos=0`
(priority 0). Sinks on node 1, UDP port 9, TCP port 10. Apps run from t=1 s to
t=duration+1. Device FIFO is set to 10 packets so queueing and drops happen in
the queue disc, per band, where they are countable. A sampler every 100 ms
writes `series.csv`. At the end it writes `metrics.json` and `flowmon.xml`.

**REVISED 2026-11-10 (operator: "go ahead with all six changes"), after the
review found that TCP segments were split in two on the wire and that the seed
had no effect:**
1. TCP segment size is `mtu - 52` (20 IP + 20 TCP + 12 timestamp option), so a
   full segment is exactly one 1500-byte packet. With `mtu - 40` every segment
   left as a 1500-byte packet plus a 32-byte fragment.
2. `--tcp=0` leaves the TCP sender out; `--udpRate=0bps` leaves the UDP sender
   out. Operator only: the manifest still starts `udpRate` at 100Mbps and has
   no `tcp` parameter.
3. `--udpTos=N` sets the UDP sender's TOS byte (default 0x10). Operator only.
4. `metrics.json` gains `tcp_retrans` (the sender's `Retransmission` trace);
   `series.csv` gains `q_band0,q_band1` (packets waiting in each band at the
   sample time) and `qmin_band0,qmin_band1` (the fewest waiting since the
   previous sample, from each band's `PacketsInQueue` trace).
5. Warm-up: traffic runs for `warmup + duration` seconds (`--warmup`, default
   1 s, operator only). `metrics.json` covers the last `duration` seconds only:
   every counter is read at t = 1 + warmup and again at the stop, and the
   metrics are the differences. `series.csv` still covers the whole run, and
   its drop columns are totals since traffic began.
6. Each sender starts up to 10 ms after t = 1 s; the two offsets come from one
   `UniformRandomVariable`, so `--seed` now changes the run.
The scenario file's comments stay neutral (the model can read it).

**DECISION: `--out` must be an absolute path.** `./ns3 run` changes working
directory before launching the program.

**DECISION: default parameters.** `linkRate=1Gbps`, `linkDelay=50us`,
`udpRate=2Gbps`, `tcpVariant=TcpCubic`, `mtu=1500`, `queuePkts=100`,
`duration=10`, `seed=1`, `weightUdp=0.5`, `mode=share`. The `--mode` value is
passed straight through to the scheduler's `Mode` attribute (or set with
`Config::SetDefault("ns3::WrrQueueDisc::Mode", ...)`); the scenario file
carries no comment near it that explains what it does. There is no
`--policy` flag and no TBF anywhere in the scenario.

### 6.2 `WrrQueueDisc` (to write)

**REVISED 2026-11-11 (operator, after session 1: the model read `Mode="share"`
and the class name `WrrQueueDisc` in `two-hosts.cc` and so never had to test
which behaviour it faced). This block replaces every mention below and in
sections 4, 6.1, 7.3 and 9 of the old names, of `--mode` and of the `Mode` /
`LinkRate` attributes:**
- The class is `ns3::LinkQueueDisc` in `link-queue-disc.{h,cc}` (still not
  readable by the model). Its attributes are `WeightUdp` and `Quantum` only.
- `two-hosts.cc` has no `--mode` option and passes only `WeightUdp` and the
  queue size. Its comments and help strings are reworded so that
  `grep -n -i -w -E "mode|share|shared|cap|wrr|weighted|token|bucket|deficit" two-hosts.cc`
  prints nothing (the same holds for `two-hosts --PrintHelp`).
- The mode comes from the environment variable `TWOHOSTS_SCHED` (`share` |
  `cap`; unset = `share`; any other value aborts the run before it writes a
  file). The link rate used in `cap` mode is read from the `DataRate` attribute
  of the device the queue disc is installed on.
- `tools.run`, `control.py` and `make_trace.py` set `TWOHOSTS_SCHED` in the
  child process's environment. `runs/operator.jsonl` records the mode as before;
  `make_trace.py --mode=cap` is still how the operator asks for it there.
- Verified: operator checks 1-4 re-run with this build
  (`checks/build3/results.json`) give `metrics.json`, `series.csv` and
  `params.json` byte-identical to `checks/build2/`; a `cap` and a `share`
  recording (`udpRate=200Mbps`) are byte-identical to the build-2 recordings in
  `trace/`.
- Still open: `list_runs` returns every run in `runs/index.json`, including the
  operator's stage-2 runs whose folder names contain `share` / `cap`.
A two-band, work-conserving, byte-based weighted scheduler, i.e. deficit
round robin. Specification:

- Subclass `ns3::QueueDisc`. Register with `NS_OBJECT_ENSURE_REGISTERED` and a
  `GetTypeId` with attributes `WeightUdp` (double, 0.05-0.95, default 0.5),
  `Quantum` (uint32, bytes, default 2 × MTU = 3000), `Mode` (enum `share` |
  `cap`, default `share`) and `LinkRate` (DataRate, set by `two-hosts.cc` to
  the link rate; used only in `cap` mode). **VERIFIED** in ns-3.49
  `queue-disc.h`: pure virtuals `bool DoEnqueue(Ptr<QueueDiscItem>)`,
  `Ptr<QueueDiscItem> DoDequeue()`, `bool CheckConfig()`,
  `void InitializeParams()`; optional `Ptr<const QueueDiscItem> DoPeek()`;
  accessors `AddQueueDiscClass`, `GetQueueDiscClass(i)`,
  `GetNQueueDiscClasses()`, `QueueDiscClass::GetQueueDisc()`; drop helpers
  `DropBeforeEnqueue(item, reason)` / `DropAfterDequeue(item, reason)`;
  `GetStats()` has `nTotalDroppedPackets` (plus BeforeEnqueue / AfterDequeue
  splits). `CheckConfig` must reject internal queues and packet filters and
  require exactly 2 classes (Prio does the same; it also creates 2 Fifo
  children when none are given, which this class may copy).
- Two child queue discs attached as `QueueDiscClass` 0 and 1, each a
  `FifoQueueDisc` of `--queuePkts` packets, installed through
  `TrafficControlHelper::AddQueueDiscClasses` + `AddChildQueueDisc` exactly as
  the Prio version does, so `two-hosts.cc` changes by one line.
- Classification in `DoEnqueue`: read the `SocketPriorityTag`; priority 6 goes
  to band 0 (UDP), everything else to band 1 (TCP). No packet filters.
- `DoDequeue` in `share` mode implements DRR: keep a deficit counter per band and a current
  band index. Loop over bands starting from current: if the band is empty,
  reset its deficit to 0 and advance; otherwise, if its deficit is smaller
  than the head packet's size, add `Quantum × weight_band` to the deficit and
  advance; otherwise dequeue the head, subtract its size from the deficit, and
  return it. Band weights are `WeightUdp` and `1 - WeightUdp`. Return null
  only when both bands are empty. This is work-conserving by construction.
- `DoDequeue` in `cap` mode (**DECISION (2026-11-09)**, replaces the TBF idea):
  each band has its own token bucket, band 0 at `WeightUdp × LinkRate`, band 1
  at `(1 - WeightUdp) × LinkRate`, burst `Quantum` bytes each: two fixed pipes.
  Serve the first band (alternating start) that has a packet and enough
  tokens. When packets wait but no band has tokens, return null and
  `Simulator::Schedule(time until the earliest band has enough tokens,
  &QueueDisc::Run, this)`. (Built 2026-11-09 with BOTH bands capped: the
  decision text said "TCP band uncapped", but then TCP takes every slot UDP
  leaves and the cap run gives TCP 0.756e9 and link_util 1.0, identical to
  share; the stage-2 acceptance (TCP ≈ 0.5e9) and the "utilisation drops"
  fingerprint in section 1 both require the TCP pipe to be capped too. See
  section 10.) This
  is safe because this class is the ROOT queue disc: a root has the device
  queue interface and the send callback. (**VERIFIED** why TBF was dropped:
  `TbfQueueDisc` schedules `Run` on itself the same way, and as a CHILD of
  `PrioQueueDisc` it has no send callback, so the wake-up ends in a null
  callback; asserts are compiled out in the optimized profile, so it would
  fail silently. ns-3 documents TBF only as a root.)
- Drops happen in the child FIFOs; per-band drop counts are read from
  `GetQueueDiscClass(i)->GetQueueDisc()->GetStats().nTotalDroppedPackets`.
- Size budget: header ≤ 40 lines, source ≤ 120 lines.

**DECISION (2026-11-09): hidden mode switch, no TBF, no `--policy`.** The two
behaviours live in one class as `Mode = share | cap`: `share` is the
work-conserving DRR (a floor), `cap` is a rate limiter wearing the same ratio
knob. The operator selects the mode with `Config::SetDefault(
"ns3::WrrQueueDisc::Mode", StringValue("cap"))` or the `--mode` flag that
`two-hosts.cc` passes straight through without comment. **`mode` is not in
`manifest.json` and the LLM is not told it exists.** The LLM's job can then
include discovering which behaviour it is facing. Default mode is `share`.

### 6.3 Output contract (fixed; the viewer, tools, and ledger all read these)
`metrics.json`, flat, exactly these keys (`tcp_retrans` added 2026-11-10; all
values cover the measured seconds only, see 6.1 revision 5):
```
udp_goodput_bps, tcp_goodput_bps, udp_loss_frac,
drops_band0, drops_band1, tcp_retrans, link_util, link_rate_bps, weight_udp
```
`series.csv` header, exactly (the last four columns added 2026-11-10, at the
end, so readers of the first six are unaffected):
```
t,udp_bps,tcp_bps,cwnd,drops_band0,drops_band1,q_band0,q_band1,qmin_band0,qmin_band1
```
`flowmon.xml`: FlowMonitor output, kept for the LLM's `grep_trace` tool.

## 7. Harness specification

### 7.1 `manifest.json`

**REVISED 2026-11-11 (operator; stage 2 of `~/RESTRUCTURE_PLAN.md`): briefs.** This
block replaces what 7.1, 7.3 and 7.5 say about the task, the parameters, the
fixed settings and `read_source`.
- A session is started with a brief, `briefs/<id>.json`: `id`, `task`,
  `description`, `system` (fixed settings), `knobs` (min/max or choices, default,
  meaning), `goal` (`{"kind": "open"}` or `{"kind": "given", "target": {measure,
  direction}, "conditions": [...]}`) and `limits` (`simulations`,
  `simulations_per_experiment`). `loop.py --brief <id>`, default `two-hosts-open`.
  Two briefs exist: `two-hosts-open` (the earlier task, every knob) and
  `two-hosts-udp-demand` (`udpRate` fixed at 300Mbps; maximise `tcp_goodput_bps`
  while `udp_loss_frac <= 0.01`).
- `description` is the operator's plain-language text of the system. `{name}`
  in it is filled from the brief's own `system` settings; a name that is not a
  system setting makes the brief invalid. It is the model's only account of the
  system: **`read_source` is removed** and sessions keep no copy of
  `two-hosts.cc` (operator, 2026-11-11).
- `manifest.json` keeps what is the same for every brief: `outputs`, `tools`,
  `how_to_run`, `budget`. `describe_system()` returns the brief (description
  filled in) followed by those.
- `tools.clamp`: a setting under `system` is not the model's to change; an
  experiment that sets it gets the brief's value, recorded in the experiment's
  `clamped` like any other clamp. `tools.options` starts the program with every
  option explicit: the system settings, the knobs' defaults, then the chosen
  values. `udpPacketBytes` is descriptive (the scenario fixes it at 1400).
- The starting budget is the brief's `limits.simulations` (`--budget` overrides
  it); `simulations_per_experiment` is not used until experiments hold several
  simulations (stage 3).
- `sessions/<id>/session.json`, written by `loop.py` when the session is
  created: `id`, `brief`, `model`, `started`, `flags` (budget, draft,
  temperature, baseline) and `given` (exactly what `describe_system()` returns).
  A continued session uses `given`, not the brief file, and refuses another
  brief. The scheduler mode is not in it (it stays in `checks/operator.jsonl`).
  `s001` has no `session.json` and cannot be continued.
- `prompt.txt` says "brief" where it said "manifest", names the brief's parts,
  and tells the model what `done` means for an open and for a given goal.
- `control.py`: `/api/status` lists `briefs`; `/api/session` and `/api/run` take
  `brief`.
- Brief editor (operator, 2026-11-11): `viewer/brief_editor.js`, section 3 of the
  Control page of `index_full.html` (there is no separate operator tab yet). A
  form with the task, the description (with a preview as the model will read
  it), every setting with a Fixed / Knob switch, the goal and the limits. "Save
  as new brief" calls `POST /api/brief`, which runs `tools.check_brief` (the one
  check `loop.py` also uses through `open_session`) and writes
  `briefs/<id>.json` only if no file of that id exists; "Start session with this
  brief" is enabled when the form equals a saved brief. `check_brief` also
  requires: every program option either fixed or a knob; only the six settings
  of `schema.json` as knobs (`linkRate`, `linkDelay`, `mtu` are fixed only);
  values the program accepts; min < max with the default between; a meaning for
  every knob.
- Verified: both briefs give the expected `describe_system()`; in
  `two-hosts-udp-demand` an experiment asking `udpRate=1Gbps` ran at 300Mbps with
  `clamped: {"udpRate": ["1Gbps", "300Mbps"]}`; the default run of
  `two-hosts-open` is byte-identical in its metrics to operator check 3.
What the LLM is told. Contains: the nominal task sentence; the list of
parameters with min, max, default and one-line meaning (`weightUdp 0.05-0.95`,
`udpRate 100Mbps-3Gbps`, `linkRate` fixed at 1Gbps unless you decide to
expose it, `queuePkts 4-1000` (minimum lowered from 10 by the operator,
2026-11-10), `tcpVariant` from an enumerated list,
`duration 2-30`, `seed 1-1000`); the output keys from 6.3 with one-line
meanings; the tool list from 7.3; the run budget. **It must not mention
`mode`, ETS, DRR, TBF, work-conserving, or any explanation of what the
ratio does.**

### 7.2 `schema.json`
The LLM's whole output each turn. Enforced by passing it to vLLM as
`response_format: {"type": "json_schema", "json_schema": {"name": ..., "schema": {...}}}`.
**VERIFIED** on vLLM 0.32.0 (2026-11-09): this form works, including `anyOf`
unions with `null` and string `enum`s, and the reply validated. Use it alone;
there is no guided_json fallback.

```
{
  "observations": string,            // what it read in the ledger / tool results
  "hypothesis":   string | null,     // new hypothesis, or null when giving a verdict
  "prediction":   string | null,     // a number, range or direction, falsifiable
  "experiment": {                    // present XOR verdict
      "params":  { <subset of manifest params> },
      "metrics": [ <subset of output keys> ],
      "pass_if": string              // criterion in terms of the listed metrics
  } | null,
  "verdict": {
      "for":     string,             // ledger id of the hypothesis
      "result":  "supported" | "refuted" | "inconclusive",
      "because": string,             // must cite evidence ids
      "next":    string              // what to do next and why
  } | null,
  "requests": [ { "tool": string, "args": object } ],   // may be empty
  "done": boolean
}
```
Validation in `loop.py` beyond the schema: exactly one of `experiment` /
`verdict` is non-null unless `requests` is non-empty (a tool-only turn);
`experiment.params` keys ⊂ manifest; values clamped and the clamp is recorded
in the ledger; `pass_if` non-empty.

### 7.3 `tools.py` (read-only, bounded)
- `describe_system()` returns `manifest.json`.
- The operator's mode is `loop.py --mode share|cap` (default `share`); it goes
  to `tools.MODE`, onto the ns-3 command line, and into `runs/operator.jsonl`
  (`{id, mode, seconds}`), which no tool reads and the viewer shows. It is not
  in `runs/index.json`. Run ids are `r001`, `r002`, ...
- `run(params)` validates/clamps, allocates the next `runs/<id>/`, invokes
  `./ns3 run "two-hosts ..." --no-build` (**VERIFIED**: the flag exists and
  short program names resolve for scratch subdirectories; do not rebuild per
  run), parses
  `metrics.json`, appends `{id, params, metrics}` to `runs/index.json`,
  returns the id and metrics.
- `metrics(run_id)` returns the parsed `metrics.json`.
- `series(run_id, every_n)` returns a thinned `series.csv` (cap at 100 rows).
- `grep_trace(run_id, pattern, limit)` greps `flowmon.xml`, cap 50 lines.
- `list_runs()` returns `runs/index.json`.
- `read_source(name)`: **DECISION:** `two-hosts.cc` is readable;
  `wrr-queue-disc.*` is not, and the tool returns "not available" for it
  without saying why. The scenario file passes `--mode` straight through
  with no comment that reveals the mechanism; keep comments there neutral.
- All tool outputs are truncated to a fixed character cap (6,000) before being
  put in the prompt, except `read_source`, whose result is given whole
  (operator, 2026-11-11: the cap had cut `two-hosts.cc`, about 19,000
  characters, to its first third).
- No tool takes a path argument; only ids and names from a fixed set.

### 7.4 `loop.py`
```
load manifest, schema, prompt.txt; model_id = GET /v1/models
if the ledger is empty: tools.run({}) -> append evidence record E0 (turn 0, no parent)
loop until done or budget exhausted:
    prompt = system prompt + manifest + ledger rendered as text (+ pending tool results)
    turn   = POST /v1/chat/completions (response_format = schema, temperature 0.3;
             --thinking on  (default): max_tokens 8000, enable_thinking left at the vLLM default,
                                       the reply's `reasoning` field -> ledger record type "scratch"
             --thinking off:           max_tokens 1500, chat_template_kwargs = {"enable_thinking": false})
    parse; empty content, finish_reason == "length" or invalid JSON -> retry once,
           then record a "malformed" ledger entry and continue (the scratch record is still written)
    if requests: run tools, attach results, re-ask (count as half a turn; cap 3 per turn)
    if experiment: append experiment record -> tools.run -> append evidence record
    if verdict:    append verdict record (+ hypothesis record if hypothesis present)
    if hypothesis with experiment: append hypothesis record before the experiment
```
Ledger record: one JSON object per line,
`{id, turn, type, parent, body, ts}` with `type` in
`hypothesis | experiment | evidence | verdict | malformed | note | scratch`.
A `scratch` record holds the model's reasoning text for one turn (`body =
{reasoning, model, finish_reason, tokens}`), written before that turn's other
records, with `parent` = the previous record of the turn's chain. Evidence
`body` is the full `metrics.json` plus `run_id` and the experiment's
`pass_if` copied in. Ids are sequential (`H1`, `E1`, `V1`, ...). The loop
never edits or deletes a line.

**DECISION (operator, 2026-11-10): baseline evidence E0.** Before turn 1 of a
new ledger the harness runs the default experiment once (every parameter at
its default, the operator's `--mode`) and writes it as evidence `E0`: turn 0,
`parent` null, `body` = the metrics plus `run_id`, `pass_if` null and a note
saying the harness ran it. The model's first turn therefore starts from an
observed record. E0 is not counted in the run budget, and it is written only
when the ledger is empty (a resumed ledger gets no second baseline). Evidence
from the model's experiments is still numbered `E1`, `E2`, ...

**DECISION: run budget default 30; cap on consecutive tool-only turns 3;
model temperature 0.3; max tokens 1500.**

**DECISION (2026-11-09, revised): thinking is a flag, `--thinking on|off`,
default `on`.** The server runs the qwen3 reasoning parser, so with thinking on
the reply carries the model's reasoning in a separate `reasoning` field and
the JSON answer in `content`. With `on`: `max_tokens` 8000, `enable_thinking`
left at the vLLM default, and the `reasoning` field is written to
`ledger.jsonl` as a record of type `scratch` for that turn, so the ledger stays
the complete record of the model's reasoning. Scratch records are kept for the
audit and the viewer; they are NOT replayed into later prompts (the model's
conclusions are, through the other record types), so the prompt does not grow
by thousands of tokens per turn. With `off`: `max_tokens` 1500
and `chat_template_kwargs: {"enable_thinking": false}`. In both modes an empty
`content` or `finish_reason == "length"` is malformed and recorded like invalid
JSON. (**VERIFIED** 2026-11-09: with thinking on and only 300 tokens, the whole
budget went to reasoning and `content` came back empty with `finish_reason:
"length"`, which is why the budget is 8000 when thinking is on.)

### 7.5 `prompt.txt`
Plain text. States: the nominal task; that the system is a black box reachable
only through the listed tools; that every experiment must carry `pass_if`
before it runs and the verdict must be judged against it; that predictions
must be falsifiable numbers or directions; that it must cite evidence ids;
that it may ask for information it thinks it needs via tools; that it should
set `done=true` when it believes it has an answer and has stated the
objective that answer is best *for*. It must not describe ETS, DRR, TBF,
work-conservation, TCP backoff dynamics, or expected results.

## 8. Viewer specification (`viewer/index.html`)
**REVISED 2026-11-10 (operator: "systemic and logical ... natural and inevitable
order", "very readable", then "I want to see that on http://127.0.0.1:48600/viewer/").**
Still a static page with no backend and no build step; Chart.js is no longer
used (charts are drawn as SVG). `viewer/index.html` is a thin shell: colour
tokens, a two-button run switch (the AI session / operator checks), and a
5-second loader that reads `../ledger.jsonl`, `../runs/index.json`,
`../runs/operator.jsonl`, `../harness/manifest.json` and each
`../runs/<id>/series.csv`, and redraws only when something changed. Content and
layout live in `viewer/adrs_view.js`: `TH_DATA.build(raw, run)` turns the raw
records into the page's content, `TASK_VIEW.page` draws it. The same file draws
this task inside the ADRS main viewer (`/?task=twohosts`, fed the same raw
records by `viewer/adrs_view.py`), so both addresses show one page. Order, top
to bottom: name, question, state and six key facts; 1 the system under test
(network diagram, what the AI may change, what is measured); 2 where it stands;
3 what each experiment measured (chart of UDP/TCP goodput against the UDP share,
close-up, table); 4 how the AI got there (turn strip, hypothesis rows); 5 one
experiment in detail (settings with changes, pass rule as rows, verdict, time
charts, thinking folded). Pass rules are checked in the browser from the
recorded numbers (comparisons joined by AND; numbers, metric names, + - * /,
abs/min/max; anything else is shown as "not checked") and shown beside the
model's own verdict.

**Three pages (operator, 2026-11-10: "not put everything on the same page but
split pages to 2 ~ 3 according to purposes"; "adopt the schema of the image"
= `openevolve/lookthis.webp`, a computer whose screen shows "NS-3 Simulation"
with Node 0 and Node 1 as coloured stacks of layers).** The address after `#`
chooses the page; a tab bar under the title switches; the name of the task is
on every page.
1. `#overview`: question, state, six key facts; the system at a glance (the
   left-to-right packet-path picture, with a link to System); where it stands;
   what each experiment measured (chart + table). Clicking an experiment opens
   it on Experiments.
2. `#system`: the simulated network object by object, drawn as in the image:
   an "NS-3 Simulation" frame (the image's monitor and "one computer" label were
   dropped at the operator's word: "you dont have to copy the schema to include
   monitor or one computer thing") > Node 0 (sender, blue
   tint) and Node 1 (receiver, rose tint), each a stack of layer boxes
   (Applications, Internet Stack, Traffic Control, Net Device) holding one card
   per ns-3 object with all its settings; double arrows down to the channel box;
   then "Around the network" and the tables of adjustable settings and
   measured outputs.
   REVISED the same evening (operator: "Make each node and objects inside it
   smaller, and represent link as a line between them. Separate configuration
   values showing with the schema"): the System page now has (1) a small schema
   with names only: Node 0 and Node 1 as compact stacks of layer boxes, each
   object a small labelled box, and the link drawn as a double-headed line
   between the two Net Device boxes; (2) "Configuration of every object": tables
   per node (layer, object with its ns-3 class, setting, value), then the link;
   (3) "Around the network" as three small tables; (4) adjustable settings and
   measured outputs. Clicking an object in the schema scrolls to its rows.
   REVISED again (operator: "schema and configuration detail sections located
   side by side so that users can see directly for the object they choose";
   "no abrupt and coercive page position movement"): section 1 of System is the
   schema on the left and, beside it, the settings of the chosen object (the
   Scheduler at first); clicking an object or the link swaps that panel in
   place. "All settings in one list" follows, with the chosen object shaded.
   RULE FOR THE WHOLE VIEWER: a click never scrolls the page. Choosing an
   experiment on the Overview marks it and shows a short summary beside the
   chart, with a link to open it on Experiments; Experiments is a list on the
   left (sticky) with the chosen experiment beside it. The only position change
   is when another page is opened from far down: that page starts at its top.
   FURTHER REVISIONS (operator, 2026-11-10 late):
   - "I hate to see structure abruptly changes when I click page menus": the
     frame is identical on every page: one title line (name, run, state), then
     the tab bar, always at the same position; the question and the six facts
     are the Overview's first section.
   - "visualize these more structured way and more logically. It is the core of
     this whole project": on Experiments the chosen experiment is a numbered
     chain in three phases, with the actor named at each step. Before the run
     (the AI): 1 Hypothesis, 2 Prediction (the pass rule as rows). The run (the
     harness): 3 Experiment (what changed, what was kept), 4 Result. After the
     run: 5 Check (by the page: every criterion with its allowed range and the
     measured value as a picture), 6 Verdict (the AI's; flagged if it
     contradicts the check), 7 Next step (with a button to the next hypothesis).
   - "a visualization for providing time taken for each events with cause and
     effects among events": a fourth page, `#events`. `two-hosts.cc` gained
     `--events=MS` (default 0 = off; with it off the outputs are byte-identical)
     and `--eventsAt=S`: every packet-level event of a window is written to
     `<out>/events.csv` (`t_ns, ev, kind, obj, flow, key, size, info`; `ev` is
     the number of the simulator event it happened in; `key` follows one packet:
     u<uid>, t<TCP sequence number> because TCP segments cut from one write
     share a uid, a<uid> for ACKs). `harness/make_trace.py NAME TITLE NOTE
     [--setting=value]` (operator only) runs the built program into
     `~/project/trace/NAME/` and lists it in `trace/index.json`; no harness tool
     reads `trace/`. The page shows: the recordings to choose from; "How long
     each step takes" (typical / shortest / longest time between consecutive
     events of a packet's life, per flow); and a timeline (lanes from the
     sender's applications to the receiver, queue occupancy, drops, one bar per
     transmission, packets in flight) beside the chosen packet's life, each step
     with the time since the previous step, its cause ("because") and its
     effect ("so"), with links to the packets involved.
3. `#experiments`: how the AI got there (turn strip, hypothesis rows; for the
   operator checks a table of runs), then one experiment in detail.
The earlier single-page description of section 1 follows. Section 1 drew the network the ns-3 way (operator,
2026-11-10: "all objects to be visible on viewer with all configuration
values"): each host is a stack of layers (applications, internet stack, traffic
control, net device) standing on the channel, and every ns-3 object the scenario
creates is one card with all its settings, plus the objects around the network
(random numbers, clock, measurement). The object list is `viewer/objects.json`,
a viewer-only file (no harness tool reads it, so the model never sees it); its
`{values}` are filled from the manifest's defaults, and it must be updated
together with `two-hosts.cc`. "Running" on the static page means the ledger file was
written in the last 3 minutes. The first page is kept as `viewer/index_old.html`;
its description follows.

Static file, vanilla JS, Chart.js from a CDN, no build step, no backend.
Fetches `../ledger.jsonl` and `../runs/index.json` every 5 s. Three panels:
1. **Reasoning trail**: ledger as a tree hypothesis → experiment (showing
   `pass_if`) → evidence → verdict (colored supported/refuted/inconclusive)
   → next. `scratch` records (the model's reasoning for a turn) appear in the
   trail at their turn, folded by default, expandable. Clicking evidence
   selects its run.
2. **Run detail**: params table, metrics table, and two charts from
   `runs/<id>/series.csv`: throughput per flow over time with a horizontal
   line at `weight_udp × link_rate_bps`, and cwnd with band drops overlaid.
3. **Across runs**: scatter of `weight_udp` (x) vs
   `udp_goodput_bps / link_rate_bps` (y) with the diagonal drawn; points
   colored by whether `udp_loss_frac` is zero.
Works in light and dark mode. Writes nothing.

## 9. Things not to do
- Do not install system packages, ninja, Ollama, or any Python package.
- Do not modify anything under `ns-3.49/` except `scratch/two-hosts/`.
- Do not enable pcap by default.
- Do not let the LLM see `mode`, the scheduler source, or any file path.
- Do not use `TbfQueueDisc` or any `--policy` flag; the rate limiter is
  `WrrQueueDisc` in `cap` mode (6.2).
- No occurrence of `main(` or `main (` in any file of `scratch/two-hosts/`
  other than `two-hosts.cc`, including comments and identifiers (the scratch
  build regex has no word boundary).
- Do not let the LLM write files, run shell, or edit the ledger.
- Do not add a database, a web framework, or an agent framework.
- Do not put explanations of the expected physics in the prompt or manifest.
- Do not reuse ADRS code, venvs, or ports.

## 10. Open items to confirm with the operator before stage 3
- The model id: the first entry of `/v1/models` `data`, currently
  `Qwen/Qwen3.8-Flash-Next-FP8`. Read it at startup; do not hardcode.
- Whether `linkRate` should be a tunable the LLM can vary or fixed at 1 Gbps
  (default: fixed).
- Default `--mode` for the first LLM session (default: `share`).
- Stage 2 (2026-11-09), RESOLVED by the operator ("Confirm both"): (a) `cap` =
  both bands capped, as built; (b) share-mode criterion = within ±10% of the
  weight; default queue depth stays 100.
