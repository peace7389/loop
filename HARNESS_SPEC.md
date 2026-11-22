# Specification: AI hypothesis-loop harness over ns-3

This document describes the system as it is on 2026-11-12. It was rewritten as
a whole on that day (stage 7 of `RESTRUCTURE_PLAN.md`); the earlier text, a
build specification with dated revision blocks, is in the repository's history
(the version of commit `88147b2`). Section 16 gives the history in short.

Items marked **DECISION** were decided by the operator and are not revisited
without them. Items marked **VERIFIED** were checked against the ns-3.49 source
or by a run on this machine, on the date given.

The working folder is `~/project` on the research server. This file's real
location is `~/ADRS/openevolve/HARNESS_SPEC.md`; `snapshot.sh` copies it into
the repository (section 13).

## 1. Purpose

**What the model is told** (the brief): two computers are connected by a single
wire. One sends, one receives. The sender uses UDP and TCP at the same time. A
scheduler on the sender splits the link between them by a configurable ratio.
Find the best settings and explain why they are best.

**What the harness is for**: to observe whether a local language model can read
the state of a system it cannot see inside, form a hypothesis, design an
experiment with a decision rule stated before the simulations run, have it run,
judge the result against that rule, and choose the next step, repeatedly, and
end with a report whose every claim cites its evidence. The settings it finds
are not the point; the chain of reasoning is. The harness makes that chain an
official, inspectable record, and the viewer lets a person verify it against
the measurements.

**What the model is not told** (never put this in a brief, the prompt or a tool
description; the model is supposed to find it out):

- How the scheduler behaves when one flow has less to send than its part
  allows. There are two scheduling policies behind the same ratio knob
  (section 6.2). Under `share` the unused part goes to the other flow and the
  link stays full; under `cap` it is wasted and link use drops. The operator
  chooses the policy per session; the model never sees it.
- UDP has no congestion control and TCP backs off on loss. In ns-3 the UDP
  application pushes packets into the stack regardless, and what does not fit
  is dropped at the scheduler's queue, so UDP loss at the sender follows
  directly from the configured part and the queue length.
- With both flows saturating the link the total is pinned at the link rate, so
  "best ratio" has no answer without a stated goal. A good reasoner notices
  this (brief `two-hosts-open`).

## 2. Vocabulary

Use these words, and only these, in code, files, the prompt, the viewer and
reports. The sentences are the viewer's definitions, word for word
(`EV_DEF` in `viewer/evidence_data.js`).

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

Also fixed:

- **Draft**: the text the model writes before its JSON answer (the server's
  reasoning field). Ledger type `draft`; the text itself is in `drafts.jsonl`.
- **Work log**: the sequence of the model's steps and its stated reasons, as
  the viewer shows it.
- **Operator-only**: stored under `checks/` and not reachable through any
  function of `harness/tools.py`. **Operator columns**: the viewer's switch
  that shows operator-only values.
- **Knob**: a setting the model may change. **System setting**: one the brief
  fixes.
- Earlier names, still read in old records but not written: `mode` (now
  scheduling policy, `policy`), `rule` / `rules` / `pass_if` (now decision
  rule), `scratch` (now draft), "run" for a simulation.

## 3. Principles

**DECISION: the model never produces a result.** Simulation, evidence and check
records are written by the harness from files the simulator produced. The model
proposes and interprets; it never writes a number into the record as measured.

**DECISION: the decision rule comes first.** An experiment that tests a
hypothesis is accepted only with a decision rule for it, stated before the
simulations run, in a form the harness can evaluate itself. The harness, not
the model, says whether it held.

**DECISION: the ledger is the only memory.** Each turn's prompt is rebuilt from
`ledger.jsonl`. The model has no other state. The loop only appends; it never
edits or deletes a line.

**DECISION: strict write ownership.**

- The simulator writes only inside the output folder it is given.
- `loop.py` writes only its own session's folder, `sessions/<id>/`, and appends
  one line per simulation to `checks/operator.jsonl`.
- `control.py` writes only under `checks/`, and new files in `briefs/`.
- `tools.py` (apart from running simulations into the session's `runs/`) and
  the viewer write nothing. The page's only writes go through `control.py`'s
  POST endpoints.
- The model writes nothing. It returns JSON to `loop.py`, which decides what
  to append.

**DECISION: the model's discretion is which tool to ask and which experiment to
design.** No shell, no file access, no paths; settings are forced into the
brief's ranges; a simulation budget per session.

**DECISION: sessions know nothing about each other.** Every path a tool reads
is inside the current session's folder, and a run id is accepted only if that
session's own index lists it.

**DECISION: the operator's side is out of the model's reach.** The scheduling
policy, operator simulations, sweeps, answer keys, scores and reviews live
under `checks/`. The policy reaches a simulation only as an environment
variable.

**DECISION: nothing is filled in.** Where a session did not record a field the
viewer says "not recorded". The harness records no score of its own; a score
exists only where the operator has made a sweep and scored the session.

**DECISION: small and plain.** Python standard library plus `requests`
(`control.py` and the operator tools: standard library only). No frameworks, no
agent libraries, no database. The viewer is static files, plain JavaScript,
with Chart.js from a CDN as the only library; viewer files are kept small
(each `evidence_*.js` is under about 170 lines).

**DECISION: draft text is not shown**, except on the owner's own page (revised
2026-11-22, the operator: "a separate page for me to see the tokens generated by
the local AI agents"). `drafts.jsonl` and `calls.jsonl` are never opened by the
session's page, the export, or anyone reporting on a session, and are given to
nobody as files over HTTP; the ledger keeps only a draft's length and token
count. `viewer/agents.html` shows them, through `GET /api/agents`; since 2026-11-22, later (the operator:
"everyone who sees the page"), to everyone who can open the session's page, view-only visitors included (10.1).

## 4. Environment

- Host `ece-silbmark2`, Ubuntu 24.04, 256 cores, shared with other users. No
  sudo, no system packages. Home is on Lustre and nearly full: per-simulation
  output is kept small, and **pcap is off by default**.
- ns-3: `~/project/ns-3.49`, built with `--build-profile=optimized
  --enable-examples` (logging and asserts compiled out). Only
  `scratch/two-hosts/` is ours. The harness starts the built program directly:
  `ns-3.49/build/scratch/two-hosts/ns3.49-two-hosts-optimized`, with
  `LD_LIBRARY_PATH=ns-3.49/build/lib`. Rebuild after a scenario change with
  `./ns3 build` in the ns-3 tree.
- Python: `/home/chunguck.kim/miniforge3/bin/python3` (3.14.7, has `requests`).
- Model server: vLLM, OpenAI-compatible, `http://127.0.0.1:18000/v1`, on GPUs 6
  and 7. `loop.py` takes the model id from the first entry of `GET /v1/models`
  (now `Qwen/Qwen3.8-Flash-Next-FP8`); it is not hardcoded. The server runs the
  qwen3 reasoning parser, so the reply has the draft in `reasoning` and the
  JSON answer in `content`. Context length 131,072 tokens.
- Control server and page: port 8600, bound to 127.0.0.1, in tmux `control`:
  `tmux new-session -d -s control -c ~/project "/home/chunguck.kim/miniforge3/bin/python3 harness/control.py"`.
  Restart it after editing `control.py`, `tools.py` or `export_session.py`.
  From the operator's laptop it is `http://127.0.0.1:48600/viewer/`.
- ADRS (`~/ADRS`, ports 8766-8768) is a separate system. The harness imports
  nothing from it. The one link is the other way: the ADRS main viewer loads
  `viewer/adrs_view.py` to show this project as a task (section 12.3).
- A session of 40 simulations has taken 20 to 50 minutes when six ran side by
  side (the longest, 94 minutes); up to six run side by side.

## 5. Layout

```
~/project/
├── HARNESS_SPEC.md               this file (a copy; see section 13)
├── EVIDENCE_VIEW.md, PAGE_REDESIGN.md   the operator's plans for the page (section 12)
├── briefs/<id>.json              the assignments (section 7)
├── harness/
│   ├── loop.py                   the loop: one session (section 8)
│   ├── decision_rules.py         reads and checks decision rules (8.4)
│   ├── tools.py                  all the model can reach, and the brief check (section 9)
│   ├── manifest.json             what is the same for every brief: outputs, tools
│   ├── schema.json               the answer format, enforced by the model server; its params object is built from the brief (8.3)
│   ├── prompt.txt                the system prompt
│   ├── control.py                the operator's server, port 8600 (section 10)
│   ├── session_figures.py        figures counted from a session's records, for control.py's session rows (12.1); finds the void checks
│   ├── audit.py                  operator: what a session's records are worth as tests (10.8)
│   ├── score.py                  operator: score a session against a sweep (10.4)
│   ├── export_session.py         operator: a session as a folder that opens offline (10.6)
│   ├── make_trace.py             operator: packet-event recordings (10.7)
│   ├── check_objects.py          operator: the picture of the system against the scenario source (6.4)
│   └── move_drafts.py            operator, used once: draft text out of old ledgers
├── sessions/<id>/                one session; ids s001, s002, ...
│   ├── session.json              what it was given, the flags, how it ended (8.8)
│   ├── ledger.jsonl              the record, append-only, written only by loop.py (8.7)
│   ├── drafts.jsonl              the text of each draft; read only for the owner's page (agents.html)
│   ├── calls.jsonl               every call of the model: agent, messages, what it wrote, tokens (8.7); owner's page only
│   ├── answers.jsonl             each turn's accepted answer as it was received (8.3); no tool reads it
│   ├── report.json               the final report as accepted
│   └── runs/
│       ├── index.json            this session's simulations: {id, params, metrics}, one per line
│       └── <run>/                params.json, metrics.json, series.csv, flowmon.xml (ids r001, ...)
├── checks/                       operator-only: no function of tools.py reads here
│   ├── operator.jsonl            {session, id, policy, seconds} per simulation, appended by loop.py
│   ├── build1/ ... build5/       the operator's checks of the simulator, by build (6.4)
│   ├── op-<time>/, control.jsonl operator simulations started from the page
│   ├── sessions/<id>.log         terminal output of a session started by control.py
│   ├── sweeps/<id>/              table.csv, status.json (10.2)
│   ├── keys/<brief>.json         answer key (10.3)
│   ├── scores/<session>.json     score; <session>.recommendation/ holds its one simulation (10.4)
│   ├── reviews/<session>.json    the reviewer's ticks, notes and sign-off (10.5)
│   ├── audit/<session>.json      the audit of a session's checks, verdicts, experiments and designs (10.8)
│   ├── random.json               sessions whose policy the server chose (10.1)
│   └── exports/                  exported sessions (not in the repository)
├── trace/                        packet-event recordings, operator-only (10.7)
├── viewer/                       the page (section 12)
├── scratch/two-hosts/            a copy of the scenario, for the repository
├── snapshot.sh, README.md, .gitignore
└── ns-3.49/                      upstream ns-3; touch only scratch/two-hosts/ (not in the repository)
    └── scratch/two-hosts/        two-hosts.cc, link-queue-disc.h, link-queue-disc.cc
```

## 6. The simulator

### 6.1 The scenario: `two-hosts.cc`

Two nodes on one point-to-point link. Node 0 sends, node 1 receives.

- UDP: `OnOffApplication`, constant rate `--udpRate`, 1400-byte packets, TOS
  0x10, which maps to socket priority 6. Port 9.
- TCP: `BulkSendApplication`, always has data, TOS 0 (priority 0). Port 10.
  Congestion control is `--tcpVariant`. Segment size is `mtu - 52` (20 IP + 20
  TCP + 12 timestamp option), so a full segment is exactly one MTU-sized
  packet. Send and receive buffers are 1 MB unless `--tcpBufBytes` is given;
  TCP's first window is ns-3's own, 10 segments, unless `--tcpInitCwnd` is
  given.
- On node 0's device the root queue disc is `ns3::LinkQueueDisc` (6.2) with two
  child `FifoQueueDisc`s, each of `--queuePkts` packets unless its own length
  is given (`--queuePktsUdp`, `--queuePktsTcp`). The device's own queue
  is a drop-tail of 10 packets unless `--devQueuePkts` is given (both
  devices); it never drops, because a full device queue stops the scheduler,
  so queueing and drops happen in the queue disc, per band, where they are
  counted.
- Timing: traffic starts at t = 1 s. Each sender starts up to 10 ms later; the
  two offsets come from one `UniformRandomVariable`, so `--seed` (the run
  number) changes the simulation. Traffic runs for `warmup + duration` seconds.
  The first `warmup` seconds (1 s) are not measured: every counter is read at
  t = 1 + warmup and again at the stop, and `metrics.json` holds the
  differences. `series.csv` covers the whole run.
- `--out` must be an absolute path.

Options and defaults:

| Option | Default | Who may set it |
|---|---|---|
| `linkRate` | 1Gbps | a brief, as a fixed setting only |
| `linkDelay` | 50us | a brief, as a fixed setting only |
| `mtu` | 1500 | a brief, as a fixed setting only |
| `weightUdp` | 0.5 (0.05 to 0.95) | a brief: fixed or knob |
| `udpRate` | 2Gbps | a brief: fixed or knob |
| `queuePkts` | 100 | a brief: fixed or knob |
| `tcpVariant` | TcpCubic | a brief: fixed or knob |
| `duration` | 10 | a brief: fixed or knob |
| `seed` | 1 | a brief: fixed or knob |
| `queuePktsUdp`, `queuePktsTcp` | 0: as long as `queuePkts` says | a brief: left out, fixed or knob (a whole number of at least 1) |
| `tcpInitCwnd` | 0: ns-3's own first window, 10 segments | a brief: left out, fixed or knob (a whole number of at least 1) |
| `tcpBufBytes` | 0: 1 MB each | a brief: left out, fixed or knob (a whole number of at least 4096) |
| `devQueuePkts` | 0: 10 packets | a brief: left out, fixed or knob (a whole number of at least 1) |
| `out` | (required) | the harness |
| `warmup` (1), `tcp` (on), `udpTos` (0x10), `pcap` (off), `events` (0), `eventsAt` (0) | | the operator only, by starting the program directly |

**Settings added after build 4** (`NOTEBOOK_VIEW.md`, Part 3, Step C; one at
a time, each with an operator check that predicts a number, 6.4). The rule for
each: at its default the program does what it did before the setting existed
and writes the same files, byte for byte; `params.json` states such a setting
only when it was given. So far: `queuePktsUdp` and `queuePktsTcp`, each queue's
own length (build 5). A queue without its own length has the common
`queuePkts`; once both are given, `queuePkts` has no effect. Then, at the
operator's word that values the scenario fixed should be settings where an
experiment may turn on them (2026-11-15): `tcpInitCwnd`, TCP's first window in
segments, and `tcpBufBytes`, the size in bytes of TCP's send buffer and of its
receive buffer on both hosts (build 6); `devQueuePkts`, the length of each
device's transmit queue: the packets that wait there after the scheduler has
chosen them (build 7).

`--udpRate=0bps` leaves the UDP sender out and `--tcp=0` the TCP sender.
`--events=MS` writes every packet-level event of a window of MS milliseconds to
`events.csv` (10.7); with it off the other outputs are byte-identical.

**Rule: the scenario file says nothing about the policy.**
`grep -n -i -w -E "mode|share|shared|cap|wrr|weighted|token|bucket|deficit" two-hosts.cc`
must print nothing (it does, 2026-11-12), and the same holds for
`two-hosts --PrintHelp`. The model cannot read the file, but its words appear
in error texts and in the public repository.

**VERIFIED (2026-11-09):** all files in `scratch/two-hosts/` build as one
program, named after the one file that contains `main`. The configure step
fails if more than one file matches the regex `main[(| (]`, which has no word
boundary, so no other file there may contain `main(` or `main (`, even in a
comment.

### 6.2 The scheduler: `LinkQueueDisc`

`link-queue-disc.{h,cc}`. A two-band root queue disc. Band 0 takes packets
with socket priority 6 (UDP here); band 1 takes everything else. Attributes:
`WeightUdp` (0.05 to 0.95, default 0.5) and `Quantum` (bytes, default 3000).
Drops happen in the child FIFOs and are counted per band.

The scheduling policy comes from the environment variable `TWOHOSTS_SCHED`
(`share` or `cap`; unset means `share`; any other value aborts before a file is
written). It is not a command-line option and not an attribute.

- **share**: deficit round robin over the two bands with weights `WeightUdp`
  and `1 - WeightUdp`. An empty band's deficit is reset and its turn passes to
  the other band, so the link is never idle while a packet waits: the
  configured part is a floor, not a ceiling.
- **cap**: each band has its own token bucket, band 0 at `WeightUdp` x link
  rate and band 1 at the rest, burst `Quantum` bytes. A band without tokens
  waits even if the other is empty; the queue disc schedules its own wake-up.
  Each flow is held to its part. The link rate is read from the `DataRate` of
  the device the queue disc is installed on.

The two fingerprints, same settings (`weightUdp` 0.5, `udpRate` 200Mbps):
under share TCP gets 0.767 Gbps and link use is 1.00; under cap TCP gets
0.483 Gbps and link use is 0.705.

**DECISION (2026-11-09): both bands are capped under `cap`.** With only UDP
capped the two policies give the same numbers.

**VERIFIED (2026-11-09):** `TbfQueueDisc` cannot be used as a child for this:
it schedules `Run` on itself and as a child has no send callback; with asserts
compiled out it fails silently. That is why the cap is built into the root.

The scheduler's own source still says "mode" inside. It was left so because
`RESTRUCTURE_PLAN.md` forbids changing the scenario; outside it the word is
"scheduling policy".

### 6.3 Outputs (fixed; the tools, the ledger and the viewer read these)

`params.json`: the nine brief options as the program used them, then each
setting added after build 4 that was given (6.1), and no others.

`metrics.json`, flat, the measured `duration` seconds only:

| Key | Meaning |
|---|---|
| `udp_goodput_bps` | payload bits per second delivered to the UDP receiver |
| `tcp_goodput_bps` | payload bits per second delivered to the TCP receiver |
| `udp_loss_frac` | of the UDP packets sent inside the measured seconds, the fraction that never arrived (counted by packet uid, so it cannot be negative) |
| `drops_band0`, `drops_band1` | packets dropped from the scheduler's UDP and TCP queue |
| `tcp_retrans` | TCP segments the sender sent again |
| `link_util` | bits transmitted on the wire divided by link capacity |
| `link_rate_bps`, `weight_udp` | the link capacity and the ratio knob as used |

`series.csv`, a sample every 0.1 s over the whole run (the measured seconds
begin at t = 2). Since build 7 each sample is in the file as soon as it is
taken (a flush after each row; the bytes are the same), so a run can be
watched while it runs (12.1, the tiles); `metrics.json` and `params.json` are
written when the simulation has ended:

```
t,udp_bps,tcp_bps,cwnd,drops_band0,drops_band1,q_band0,q_band1,qmin_band0,qmin_band1
```

Drops there are totals since traffic began; `q_*` is the packets waiting in
each band at the sample time, `qmin_*` the fewest waiting since the previous
sample.

`flowmon.xml`: FlowMonitor output, kept for the `grep_trace` tool (not in the
repository).

`events.csv` (only with `--events`): `t_ns,ev,kind,obj,flow,key,size,info`.

### 6.4 Builds and the operator's checks of the simulator

A failed check is a simulation matter, not a model finding. Checks are run by
starting the built program directly into `checks/<build>/`, never through
`tools.run`.

| Build | Date | What changed | Checks |
|---|---|---|---|
| 1 | 11-09 | First scenario and scheduler (then `WrrQueueDisc`, policy as `--mode`) | `checks/build1/`: `sanity-*`, `share-*`, `cap-*` |
| 2 | 11-10 | Segment size `mtu - 52` (before, every segment left as a 1500-byte packet plus a 32-byte tail); warm-up; the seed now matters; `tcp_retrans`; queue-occupancy columns; `--tcp`, `--udpTos`, `--warmup` | `checks/build2/`: checks 1 to 4 pass |
| 3 | 11-11 | Scheduler renamed `LinkQueueDisc`; policy from `TWOHOSTS_SCHED`; link rate read from the device | `checks/build3/results.json`: checks 1 to 4 byte-identical to build 2; checks 5 to 11 pass |
| 4 | 11-11 | `udp_loss_frac` counted by packet uid (it could be slightly negative before) | `checks/build4/results.json`: checks 1 to 4 give the same value for every other metric; largest change of `udp_loss_frac` 0.000006 |

| 5 | 11-14 | Each queue may have its own length: `--queuePktsUdp`, `--queuePktsTcp` (Step C, first setting) | `checks/build5/results.json`: with the new options left out, every run of checks 1 to 11 (17 runs; `metrics.json`, `series.csv`, `params.json`, `flowmon.xml`: 68 files) is byte-identical to the build-4 program run just before the change, and checks 1 to 4 to the files in `checks/build4/`; check 12 passes |
| 6 | 11-15 | TCP's first window and TCP's buffers may be set: `--tcpInitCwnd`, `--tcpBufBytes` | `checks/build6/results.json`: with the new options left out, every run of checks 1 to 12 (26 runs; 104 files) is byte-identical to build 5; checks 13 and 14 pass |
| 7 | 11-15 | The device's transmit queue may be set: `--devQueuePkts`; `series.csv` is written sample by sample | `checks/build7/results.json`: with the new option left out, every run of checks 1 to 14 (38 runs; 152 files) is byte-identical to build 6; checks 15 and 16 pass |

Build 7 is the current one. Both sweep tables (10.2) were made with build 4;
builds 5, 6 and 7 write the same files for settings that leave the new
options out. The scripts that ran and compared the checks of a build are kept
in its folder (`run_checks.py`, `compare.py`, `check12.py`, `check13_14.py`,
`check15_16.py`). The packet-event recordings of check 15 (2 MB each) are not
kept; each run's `command.txt` makes them again.

The sixteen checks; 1 to 11 as measured with build 3, 12 with build 5, 13 and
14 with build 6, 15 and 16 with build 7:

| # | Settings | Measured | Result |
|---|---|---|---|
| 1 | UDP alone (`tcp=0`, weightUdp 0.95, udpRate 2Gbps) | UDP 0.9790 Gbps (= 1400/1430), link use 1.00 | pass |
| 2 | TCP alone (`udpRate=0bps`) | TCP 0.9640 Gbps, largest packet 1500 bytes, no 32-byte tails | pass |
| 3 | share, weightUdp 0.2 / 0.5 / 0.8, both saturating | UDP/link 0.1958 / 0.4895 / 0.7835, link use 1.00 | pass |
| 4 | share, weightUdp 0.5, udpRate 200Mbps | UDP 0.2000, no UDP drops, TCP 0.7671 Gbps, link use 1.00 | pass |
| 5a | queuePkts 4, TcpNewReno | UDP/link 0.5764, link use 1.00 | pass |
| 5b | queuePkts 4, TcpCubic | UDP/link 0.5079, link use 1.00 | pass |
| 6 | cap, udpRate 200Mbps | UDP 0.2000, no drops, TCP 0.4827 Gbps, link use 0.7050 | pass |
| 7 | cap, all defaults | within 0.14% of share | pass |
| 8 | UDP sent with the default TOS (`udpTos=0`) | both flows in the TCP queue: TCP 0, UDP 0.9790 Gbps | pass |
| 9 | packet count, defaults | UDP sent = received + dropped, to 0.0001% | pass |
| 10 | seed 1 twice, then seed 2 | seed 1 byte-identical; seed 2 differs in `series.csv`, metrics within 0.0002% | pass |
| 11 | duration 2 and 30 against 10 | rates within 0.001%; counts under 50 events are exempt | pass (**DECISION 2026-11-11**: the exemption) |
| 12 | separate queue lengths, predicted before the run: with queuePktsUdp 20 and queuePktsTcp 200 (and swapped; and under cap) no queue ever holds more than its own length and every drop happens with exactly that many waiting; both given as 100 is the default; `queuePkts` 37 is `queuePkts` 999 with both own lengths 37; one own length alone leaves the other queue at `queuePkts` | most waiting 20 and 200 (swapped: 200 and 20); in two recorded seconds 269,728 UDP drops all at 20 waiting and 4 TCP drops all at 200 (swapped: all at 200, 185 at 20; cap: 269,847 at 20, 4 at 200); the three pairs byte-identical in `metrics.json`, `series.csv`, `flowmon.xml` | pass |
| 13 | TCP's first window, predicted before the run: with `tcpInitCwnd` 1, 4 and 40 (TCP alone, link delay 200 ms) the first congestion window recorded and the first burst that arrives are N x 1448 bytes; not given, the same with N = 10; given as 10 is the default; over 10 measured seconds it changes the goodput by less than 1 % | 1,448, 5,792 and 57,920 bytes, window and burst alike; not given 14,480; given as 10 byte-identical in `metrics.json`, `series.csv`, `flowmon.xml`; goodput with 1 against 40 segments differs by 0.0001 % | pass |
| 14 | TCP's buffers, predicted before the run: with `tcpBufBytes` 65,536 and a round trip of 20 ms (TCP alone) the window cannot exceed the buffer, so goodput is at most 26.2 Mbps and at least 40 % of that; with 262,144 at most 104.9 Mbps and 3 to 4.5 times the first; given as 1,048,576 is the default | 26.16 Mbps (99.8 % of the bound); 104.65 Mbps (99.8 %; 4.0 times); given as 1,048,576 byte-identical in the three files | pass |
| 15 | the device's transmit queue, predicted before the run: with the scheduler never empty (UDP offers 2 Gbps on the 1 Gbps link) the packets waiting in the sender's device queue number at most N and reach N, for `devQueuePkts` 1, 50, 200 and for 10 when it is not given; a packet waits there for the transmissions of the N packets before it, between N x 11.44 and N x 12.02 microseconds; given as 10 is the default | most waiting 1, 10, 50, 200; waits 11.44 to 12.02, 116.7 to 117.3, 585.8 to 586.4 and 2,343.9 to 2,344.4 microseconds (about 2,500 packets timed in each run, from 40 ms of packet events); given as 10 byte-identical in `metrics.json`, `series.csv`, `flowmon.xml`; `params.json` states it only when given | pass |
| 16 | `series.csv` sample by sample, predicted before the run: 6 s after a run of 10 measured seconds was started (it takes about 25 s) its `series.csv` holds at least 5 samples and its `metrics.json` does not exist yet; the finished file is byte-identical to build 6's | 25 samples after 6 s, no `metrics.json`, the program still running; the finished file byte-identical to `checks/build6/c13c-defaults/series.csv` | pass |

`harness/check_objects.py` is run with them after a change of the
scenario. The viewer's picture of the system (12.1) states values that the
scenario fixes in its source: the UDP packet size, the ports, the device's
queue, the TCP buffers, the scheduler's quantum, the start times. Nothing
updates them when the scenario changes. The check reads `two-hosts.cc` and
`link-queue-disc.cc` and compares them, value by value, with
`viewer/objects.json` and with the picture's script; it writes nothing and ends
with status 1 if a value differs or can no longer be read. For a setting added
after build 4 it checks that the scenario has the option, that the object it
belongs to is given it, and that the object's row in `objects.json` names it.
On 2026-11-15, with build 7: 50 values compared, 50 ok.

What checks 5a and 5b show: with short queues TCP's queue empties after a
loss, and under share UDP then gets more than its configured part. With Cubic
and queues of 8 or more this does not happen on a 50 us link, because Cubic
keeps 70% of its window after a loss.

### 6.5 A network from a description: `net.cc` and `FlowQueueDisc`

A brief that has a `"topology"` (section 7, at its end) is run by a second
program, `ns-3.49/scratch/net` (`net.cc`, `flow-queue-disc.{h,cc}`; copied to
`scratch/net/` of the repository), built by hand like `two-hosts`. It reads one
file, `network.txt`, which `harness/network.py` (`text`) writes for each
simulation, and builds what the file says with ns-3's own objects: a Node for
each host, a point-to-point channel and two devices for each link, the
internet stack, UDP and TCP applications, and in front of a device the queue
the file describes. One line per object:

    host <id>
    link <id> <host> <host> rate=<rate> delay=<time> mtu=<bytes> devq=<packets>
    dev <link> <host> [rate=<rate>] [devq=<packets>]
    queue <link> <host> kind=fifo|scheduler length=<packets> [parts=<name>:<n>,...] [largest=<name>:<rate>,...] [classes=<name>:<flow>+<flow>,...]
    flow <id> udp <from> <to> rate=<rate> packet=<bytes>
    flow <id> tcp <from> <to> type=<TcpCubic|...>
    tcp [initcwnd=<segments>] [buf=<bytes>]
    run duration=<s> seed=<n>

A **link is a channel and two devices**, as in ns-3. The `link` line gives
what the two devices have in common; a `dev` line gives one device a rate or a
transmit queue of its own (second build, 2026-11-17). A **queue** stands on
one sending side of a link, and a link may have one on each side. Where none
is described, packets wait in a plain queue of 100 packets. A **scheduler**
has one queue for each of its parts. A part is named after one flow, which
then has the queue to itself, or after a class: `classes=udp:u1+u2` puts the
flows u1 and u2 into one queue, and they share its part of the link. How a
scheduler divides the link (share, cap, prio) is the session's policy, given
on the command line and never written into the brief.

The measures are named from the network: per flow `<flow>_goodput_bps`, and
`<flow>_loss_frac` (UDP) or `<flow>_retrans` (TCP); per link `<link>_util`
and `<link>_util_back` (bits sent each way, divided by the rate of the device
that sends them); per queue the drops: `<link>_drops_<part>` for each part of
a scheduler, `<link>_drops` for a plain queue, `<link>_drops_back` for the
plain queue of the other side (where both sides have a described plain queue,
for the side of the link's second host). The series over time carries a
column for each flow's rate, each TCP flow's window, and each queue's drops
and length.

The operator's checks, each a prediction worked out beforehand and a
simulation: `checks/net1/` (the first build: the default network gives the
measures of `two-hosts`; largest rates; prio; a dumbbell of three hosts with
parts 0.25 and 0.75; ten networks) and `checks/net2/` (the second build: a
device at 200 Mbps on a 1 Gbps link gives 192.8 Mbps of TCP goodput, 193.07
predicted; a scheduler on each side of one link; two described plain queues
told apart as `_drops` and `_drops_back`; two UDP flows in one queue of a
scheduler held to 50 Mbps give 49.02 Mbps together; in the dumbbell, two TCP
flows in one queue with the part 0.25 get together what one had alone, 24.1
Mbps, and the third flow 72.3 Mbps). All met. The ten networks of `net1` give
byte-identical output on the second build.

## 7. Briefs

A session is started with a brief, `briefs/<id>.json`. It is the model's only
account of the system.

```
{ "id":          equals the file name
  "task":        optional, and absent from every brief made since 2026-11-17: the harness writes it (below)
  "description": the system in plain words; {name} is filled with a fixed setting's value, or reads "the knob <name>" for a knob
  "system":      { setting: value }                      fixed for this brief
  "knobs":       { setting: {min, max, default, step?, meaning} | {choices, default, meaning} }
  "goal":        {"kind": "open"}
               | {"kind": "given", "target": {"measure", "direction": "max"|"min"}, "conditions": ["udp_loss_frac <= 0.01", ...], "tolerance"?: per cent}
  "limits":      {"simulations": 40, "simulations_per_experiment": 12} }
```

**The task is written by the harness** (**DECISION 2026-11-17**; the operator, reading the brief `trap` on the page:
"Is it okay that the task the AI is given stays the same regardless of settings?"). It was not. The task was a text
typed into the brief, and a brief made from another one on the set-up page kept the other's text. `trap` told the model
"both at maximum rate" while its UDP rate was fixed at 300 Mbps, "find the best ratio" while five settings were open,
and "say what 'performance' you chose to mean" while its aim was given; session s031 ran on that. Now
`tools.task_text(brief)` writes the task from the brief's aim and the settings it leaves open, and `check_brief` puts
it into every brief that states none:

- given aim: "Find the settings that give the largest tcp_goodput_bps, while udp_loss_frac <= 0.01. You may change 4
  settings (weightUdp, queuePkts, tcpVariant, duration); every other setting is fixed. Explain why they are best."
- open aim: "No aim is given. Choose what 'performance' should mean for this system and say why; then find the
  settings that are best for it. You may change ... Explain why they are best."

The system itself is told in the description, a measure's meaning in the list of outputs. A brief that still states a
task of its own keeps it, and so do its sessions (every brief made before, among them `two-hosts-open`,
`two-hosts-udp-demand`, `trap`). The set-up page has no task field: it shows the sentence as the form changes
(`EV.taskText`, the same words; `ev_usable.py task` compares the two) and saves a brief without a task. A `task` that
is there but empty is refused.

**A name in braces in the description** stands for a fixed setting's value or, where the setting is a knob, for "the
knob <name>", so that one description stays true whoever decides the setting ("at a constant rate ({udpRate})" reads
"(300Mbps)" or "(the knob udpRate)"). A name that is no setting of the brief is refused. Until 2026-11-17 only a fixed
setting could be named, and a description copied into a brief that fixed a knob went on saying "the setting udpRate".

**Three briefs made on 2026-11-17** this way, each from the brief it is named after, with the seed fixed at 1 (the
operator's decision: in 53 settings run under several seeds TCP goodput differed by at most 0.17 %, and 11 % of all
simulations had been spent on other seeds): `two-hosts-open-2`, `two-hosts-udp-demand-2`, `trap-2`. They state no
task and name udpRate in braces. The answer key of `two-hosts-udp-demand` serves `two-hosts-udp-demand-2` as well (its
sweeps were made with seed 1): `checks/keys/two-hosts-udp-demand-2.json`.

`tools.check_brief` is the one check, used by `loop.py` and `control.py`:

- every program option of the first nine rows of 6.1 is either fixed or a
  knob, never both;
- **a setting added after build 4** (6.1: `queuePktsUdp`, `queuePktsTcp`,
  `tcpInitCwnd`, `tcpBufBytes`, `devQueuePkts`) may
  be left out, fixed or made a knob. Left out, it is in neither the brief nor
  the program's command line, so the briefs written before it and their
  sessions and sweeps are as they were. Refused: `queuePkts` as a knob while
  both queues have their own length (it would change nothing, and a test on it
  would test nothing);
- any of the nine can be a knob (**DECISION 2026-11-13**, `NOTEBOOK_VIEW.md`,
  Part 3, Step B: since the answer format is built from the brief, link rate,
  link delay and MTU can be opened to the model too; no brief in the
  repository does so yet);
- values the program accepts; `min < max` with the default between; a meaning
  for every knob;
- **a step** (optional, for a numeric knob: weightUdp, queuePkts, duration,
  seed, mtu, queuePktsUdp, queuePktsTcp, tcpInitCwnd, tcpBufBytes, devQueuePkts; a whole number where the knob is one; above 0 and at most
  `max - min`): the model's values are rounded to it, counted from the knob's
  `min`, and the rounding is recorded as a clamp (asked, used). The model
  reads it in the brief with the knob's range. Two designs that round to the
  same value are one simulation (8.5);
- a given goal needs a target that is one of the outputs and a list of
  conditions (it may be empty);
- **a tolerance** (optional, in a given goal: a number of per cent above 0
  and below 100): two results closer than this count as equal. The model
  reads it in the brief; `score.py` uses it (10.4); the page states it beside
  the goal;
- a `{name}` in the description must be one of the brief's fixed settings;
- `udpPacketBytes` may be stated under `system` but only as 1400 (the scenario
  fixes it).

The scheduling policy is not part of a brief.

Two briefs exist:

| Brief | Fixed | Knobs | Goal |
|---|---|---|---|
| `two-hosts-open` | linkRate 1Gbps, linkDelay 50us, mtu 1500 | weightUdp, udpRate (100Mbps to 3Gbps, default 2Gbps), queuePkts (4 to 1000), tcpVariant (6 choices), duration (2 to 30), seed (1 to 1000) | open: the model states and justifies its own |
| `two-hosts-udp-demand` | the same, and udpRate 300Mbps | the others | given: largest `tcp_goodput_bps` while `udp_loss_frac <= 0.01` |

Both have limits of 40 simulations and 12 per experiment. Both descriptions say
that how the scheduler behaves when a queue has less to send than its part
allows is not described and is part of the work.

A brief is never overwritten: the page's editor saves under a new id only
(`POST /api/brief`).

**The set-up page, "New session"** (`viewer/brief_editor.js`, address
`?tab=new`; **DECISION 2026-11-14**, the operator's `READABLE_PAGE.md`, Part 3)
is where a brief is written and a session started. It has the seven blocks of
a session's "The setting" (12.1), in the same order, built from the same
pieces; here each block is a form: the network (the picture of the system and,
under it, one card per part with every value it has; see below), who decides
what (each setting "fixed by the operator" with a value, or "the AI may change
it" with a range, a default and an optional step; a setting a brief may leave
out has a third state, "not set"; a numeric setting also has a bar), the aim (a ready-made aim, a target with conditions and a tolerance, or
"open: the AI chooses"), what the AI is told, is not told and can do (the task
and the description to write, the three lists, which follow the form, and
"the exact text the AI will be given"), the limits, kept from the AI (the
scheduling policy: share, cap or random), how the AI runs (the flags, each
beside its default). Every block says in one sentence what it is for. A value
that cannot be used is refused as it is typed, with the reason beside it
(`BRIEF_EDITOR.problems`: the rules of `tools.check_brief` and of
`control.py`'s start, said first by the page; the server checks again). Above
Start stands the header strip the session's page will have.

**A part is configured in its own card** (**DECISION 2026-11-15**, the
operator: "I still cannot configure the scheduler and the rest on the new
session page"; the values could be set, but only in block 2 and block 6, far
from the part they belong to). In the cards under the picture every value
that comes from a setting is a field (`BRIEF_EDITOR.confField`): the UDP
rate in the UDP source's card, the ratio in the scheduler's, each queue's
length in its queue's, the link's rate and largest packet in the devices',
the delay in the link's, TCP's type, first window and buffers in the TCP
socket's. The scheduler's card also chooses the scheduling policy (share,
cap, random): the same choice as block 6, each following the other. Under
that choice a note says what the policy does with the form's numbers
(`BRIEF_EDITOR.policyEffect`; the operator asked whether "cap" needed more
to be set: it does not, its two limits are the ratio times the link rate):
"UDP at most 450 Mbps, TCP at most 550 Mbps, even when the other sends less"
for cap, "both sending: UDP 450 Mbps, TCP 550 Mbps; what one leaves unused
goes to the other" for share; and under cap the row of the 3,000 bytes says
they are the most a flow may send in one go. Under the TCP type chosen in the
TCP socket's card a note gives that type's plain line (below). A note is not
a value: it stands under its row over the card's whole width, on a tinted
ground, with an "i" before it (the operator: an explanation must not look
like a set value). A field
is the same value as in block 2 (typing in one writes the other); block 2
keeps the ranges and the steps. The mark before a field says who decides and
a click on it switches that: ✦ the AI may change it (the field is then the
value it starts from), ✧ fixed by the operator; the value in the field stays
the value. A setting a brief may leave out has an empty field that shows
what the program does without it; a value typed there sets it (fixed), and
emptying it leaves it out again. A queue's field sets that queue's own
length. A row that only repeats or follows from a value set in another card
(the scheduler's link rate, the link's capacity, TCP's segment payload) is
shown, not set. A value that cannot be used is marked in its card with the
reason on the field. While a field is typed in, its row is not written again
(the cursor stays); what follows from it (TCP's share beside the ratio, the
picture) follows. Values the scenario fixes (the packet's payload, the start
times, the turn size, TCP's options and timers, UDP's receive buffer) are
text: they are not options of the program.

**A bar beside each numeric setting** (**DECISION 2026-11-15**, the operator:
"set variables using a visual bar along with directly entering the value").
In block 2 every numeric setting that is set has a bar between its switch
and its fields (`BRIEF_EDITOR.bar`): one handle for a fixed value; for a
setting the AI may change, the lowest and the highest value (two short
strokes, the range shaded between them) and the value it starts from (a
dot). The bar and the fields are the same values: dragging a handle (or the
arrow keys) writes the field as if typed, typing moves the handle. The ends
of a range cannot pass each other, and the starting value stays between
them. A bar's span is the range worth dragging over (`BRIEF_EDITOR.BAR`); a
rate, a delay, a count of packets and a buffer run in equal ratios (10 to
100 takes as much room as 100 to 1,000), the ratio, the largest packet, the
measured time and the seed evenly. A handle writes a round value (two digits
of a rate or a delay, in whole Mbps, Gbps, us or ms as the harness writes
them; a whole number of packets; a ratio in hundredths; a buffer of 1 or 1.5
times a power of two). A value beyond the span can still be typed: the
handle then stands at the end. A fixed bar has the operator's tone, a range
the AI's. The TCP type (a list) and a setting that is not set have no bar.
Check of both: `ev_usable.py cards bars`.

**An empty set-up** (**DECISION 2026-11-15**, the operator: "Why I can't
disenable this?", then "Show empty setup as a seperate check box because it is
special choice"). The list "Start from a saved brief" always held a saved
brief. Under it now stands a box of its own, "or start from an empty set-up"
(`#be-none`, `BRIEF_EDITOR.blank`): ticked, the task and the description are
empty, the aim is open, nothing is left to the AI, and every setting stands
fixed at the value the brief `two-hosts-open` gives it (its fixed settings,
its knobs' defaults, its limits), so that only the two texts and a name are
missing before a session can start; the list is off and says "not used: the
set-up starts empty"; the line under the form says that the form started empty
and how many values were filled in since. Unticked, the form is filled again
from the brief it held before. (For an hour the empty set-up was the first
entry of the list.) Check: `ev_usable.py none`.

A form that differs from every saved brief is saved under a new name before
its session starts; a brief is never overwritten. "Start a new session from
this setup" on a session's page opens the set-up page with every value of that
session (what it was given, its flags, its policy), each changed value marked;
saved unchanged it gives a brief equal to the session's, its settings in the
same order. The roomy form, one row per setting with the line the AI reads
about it, stays reachable as "all settings as a list". Three ready-made
**variations** of the opened brief make one change and propose a name: "no
loss allowed", "coarse ratio (steps of 0.01)", "small budget (15
simulations)". The editor of the older control page (`index_full.html`) is
`brief_editor_old.js`.

**A brief with a network** (`"topology"`; `harness/network.py`). Instead of
the fixed two-host system a brief can carry the network as data:

    {"hosts": [{"id": "a"}, {"id": "r"}, {"id": "c"}],
     "links": [{"id": "lc", "between": ["r", "c"], "rate": "100Mbps", "delay": "1ms", "mtu": 1500, "device_queue": 10,
                "queue": {"on": "r", "kind": "scheduler", "length": 100, "parts": {"one": 0.25, "fb": 0.75},
                          "largest_rate": {}, "classes": {"one": ["fa", "fd"]}},
                "ends": {"c": {"rate": "50Mbps", "queue": {"kind": "fifo", "length": 50}}}}, ...],
     "flows": [{"id": "fa", "kind": "tcp", "from": "a", "to": "c", "type": "TcpCubic"},
               {"id": "ub", "kind": "udp", "from": "c", "to": "a", "rate": "80Mbps", "packet_bytes": 1400}]}

At most 8 hosts, 12 links and 8 flows; one link between two hosts; a flow
takes the shortest way in links, and a network in which a flow has two
equally short ways is refused. A link's line gives what its two devices have
in common. `"queue"` with `"on"` describes the queue of one sending side (the
form of every brief before 2026-11-17, read as before). `"ends"` says, by
host, what one end has of its own: `rate`, `device_queue`, and `queue` (the
queue of that side, so that a link can have one on each side; a side has at
most one). A scheduler's `classes` name groups of flows that share one of
its queues: a name of its own (not a flow's, not used on the link's other
side) that has a part, and the flows in it; every flow that passes the
scheduler waits in exactly one of its queues.

A flow is an ns-3 application and the socket it opens, and the two are
separate choices (2026-11-18, at the operator's word that the page must match
ns-3). `"kind"` is the socket, ns-3's `Protocol` of the application: `udp` or
`tcp`. `"app"` is the application that sends: `onoff` (`OnOffApplication`,
always on: `packet_bytes` at a time at the constant `rate`) or `bulk`
(`BulkSendApplication`: as fast as the socket accepts). Left out, a `udp`
flow is `onoff` and a `tcp` flow is `bulk`, which is every flow written
before, and such a flow is still written without `app` (in the brief and in
`network.txt`). So a TCP flow can send at a constant rate:
`{"id": "t1", "kind": "tcp", "app": "onoff", "rate": "200Mbps",
"packet_bytes": 1400, "type": "TcpCubic", ...}`; it has the settings
`t1.rate`, `t1.packet_bytes` and `t1.type` and the measures of a TCP flow
(goodput, segments sent again). `bulk` over `udp` is refused, by the harness
and by the program, as ns-3 refuses it. The receiver of every flow is a
`PacketSink`. The program's third build reads `app=onoff|bulk` on a flow's
line; `checks/net3` holds its five predictions, all met (OnOff over TCP at
200 Mbps alone delivers 200.0 Mbps; at 2 Gbps on a 1 Gbps link it delivers
what BulkSend delivers; beside a 2 Gbps UDP flow under share it gets its
100 Mbps and UDP the rest, 877.3 Mbps), and the 15 networks of `checks/net1`
and `checks/net2` give byte-identical output.

The same day, the rest of what ns-3 has for these objects and the builder
could not say (the program's fourth build; `checks/net4`, nine predictions,
all met; the 20 networks of `checks/net1` to `net3` byte-identical). Each is
optional, and a brief that states none of them is written and run as before.

- **An application's times.** A flow may state `start` and `stop`
  (`StartTime`, `StopTime`: seconds of the simulation; left out, 1 s and the
  end; the measured seconds begin at 2 s), for OnOff `on_time` and `off_time`
  (the lengths of its on and off periods, together; left out, always on) and
  `max_bytes` (`MaxBytes`). Each stated one is a setting (`udp.start`, ...)
  and can be a knob. On a quarter of the time a 100 Mbps flow delivers
  25.0 Mbps; BulkSend with on and off periods is refused.
- **A device's own largest packet and its loss.** An end of a link may state
  `mtu` and `loss`: the part of the packets arriving at that device that it
  receives in error and drops (a `RateErrorModel` as the device's
  `ReceiveErrorModel`). A device with a loss gives the measure
  `<link>_lost_<host>`. A loss of 0.1 measures 0.0999.
- **TCP's options.** `tcpSack`, `tcpTimestamps` (1 or 0) and `tcpDelAck`
  beside `tcpInitCwnd` and `tcpBufBytes`: settings of the whole simulation,
  because in ns-3 they are attributes of every TCP socket with one default.
  Only the congestion control is the host's own (`TcpL4Protocol`'s
  `SocketType`); the program sets it for each flow just before the flow's
  socket is made. Without timestamps a segment carries 1460 bytes.
- **ns-3's queue discs.** A queue's `kind` is the queue disc of its device:
  `fifo`, `pfifofast`, `codel`, `fqcodel`, `red`, `pie` (`network.QUEUE_DISCS`,
  each with ns-3's own settings and `length` as its `MaxSize`) or `scheduler`,
  the project's `FlowQueueDisc`. Beside 2 Gbps of UDP, FqCoDel leaves a TCP
  flow 482 Mbps where the five single-line discs leave it nothing. A side
  with no described queue still gets a `FifoQueueDisc` of 100 packets, not
  ns-3's own default (FqCoDel); the page says so.
- **The AI's own change of structure** states a ninth field, `app`: with
  `onoff` and `kind` `tcp` it adds a TCP flow at a constant rate; `add_queue`
  takes any of the queue discs.
- **Who decides a setting** is said in words (the operator, 2026-11-18: a small sign said it too vaguely): beside
  each setting of the builder a switch of two halves, "fixed" with the operator's mark and "AI may change" with
  the AI's; the half that holds is filled, a click on the other switches, and the row of a setting the AI may
  change is tinted and shows its lowest, highest and starting value under their names (`BRIEF_NET.whoSeg`).
- **The conditions of a given aim are rows filled by choosing** (the operator, 2026-11-18): a measure by its plain
  name, a comparison in words (at most, at least, below, above), a number in the unit a person uses (Mbps for
  bits per second, per cent for a loss or a use), with a button to add a row and one to remove it. Each row says
  how it reads and the line the harness checks (`fb_loss_frac <= 0.05`); the brief holds those lines as before. A
  line of another shape in a saved brief stays a text field. A given aim always has a target the network
  measures (the form showed the first measure while holding none: the page said "Ready" and the brief was
  refused).
- **Nothing has to be typed but a name**: "Start from" is marked optional (the builder opens on the two-host
  network, ready to build on and to start), and the description writes itself from the network until the
  operator types one of their own (`descAuto`).
- **The page** shows beside each setting the ns-3 attribute it is
  (`EV.NET_ATTR`: `DataRate`, `Mtu`, `TxQueue · MaxSize`, `StartTime`, ...).
- A knob of a network is a whole number by its setting's kind
  (`network.kind`), not by how its lowest value is written: a loss or a time
  whose range begins at 0 was rounded to whole numbers before.

Not built: the ready-made two-host system still has its own program and its
own names (`weightUdp`, `udpRate`, `queuePkts`), because its answer keys and
the comparison arms rest on them; a route that can be chosen; on and off
periods drawn from a random variable; TCP options per socket.

Every setting has an **address**, object.property: `lc.rate`, `lc.delay`,
`lc.mtu`, `lc.device_queue`, `lc.queue.length`, `lc.queue.parts.one`,
`lc.queue.largest_rate.fb`, `fa.type`, `ub.rate`, `ub.packet_bytes`; of an
end, `lc.c.rate`, `lc.c.device_queue`, `lc.c.queue.length`,
`lc.c.queue.parts.<name>`. The brief fixes a setting (its value in the
network) or makes it a knob (an entry of `knobs` under its address). No
object may be named like a word of an address (`network.KEPT`). The measures
are those of section 6.5 (`network.outputs`), and the goal, the conditions
and the report's expected values name them. `network.problems` gives every
reason a network cannot be built, in words; `tools.check_brief` refuses the
brief with them.

With `"structure": {"may_change": true, "most": {...}, "locked": [...]}` the
AI may change the network in the simulations it asks for (`network.apply`:
add_host, add_link, add_flow, add_queue, remove). The first queue of a link
is written the older way and a second one into `ends`, so that the first
keeps its addresses; removing a queue of a link that has two names its side
(`on`). After every change `network.sync` keeps each scheduler's parts in
step with the flows that pass it: a new flow gets a queue of its own, and a
class that holds no flow any more goes with its part.

## 8. The session: `loop.py`

```
loop.py [--session ID] [--brief ID] [--budget N] [--draft on|off] [--max-tokens N]
        [--policy share|cap] [--temperature T] [--baseline on|off]
```

| Flag | Default | Meaning |
|---|---|---|
| `--session` | the next free `sNNN` | an existing id continues that session |
| `--brief` | `two-hosts-open` | the brief of a new session; a continued one keeps its own |
| `--budget` | the brief's `limits.simulations` | simulations granted at the start; never more than that limit |
| `--draft` | `on` | the model may write a draft before its answer |
| `--max-tokens` | 32000 with the draft, 3000 without | most tokens of one answer, draft included |
| `--policy` | `share` | the scheduling policy (`--mode` is still accepted) |
| `--temperature` | 0.3 | |
| `--baseline` | `on` | on an empty ledger, first run the harness's own experiment X0 |

**DECISION (2026-11-11): the defaults are `--draft on --max-tokens 32000`.**
With 8,000 and 16,000 tokens answers were cut off (s001, s003).

### 8.1 Start

The session folder is created only after the model server has answered.
`session.json` is written with what the session was given (8.8). On an empty
ledger the harness runs its own first experiment: `X0` (explore, by the
harness), one simulation `S0` with every setting at its default, evidence `E0`.
It is turn 0 and is not counted in the budget, so the model's first turn starts
from an observed record.

A session that ended with its report cannot be continued. `s001` (made before
briefs) cannot be continued either.

**The comparison arm "plain"** (`loop.py --arm plain`, 2026-11-17; for the open question "does the hypothesis format
help at all?", 15 item B1 of `HISTORY.md`). The same loop, model, brief, budget, tolerance and final report, without
the hypothesis format: the answer has no `hypotheses`, `drop` or `verdicts`, and an experiment only explores (no
`tests`, no `decision_rules`), so the ledger of such a session holds no hypothesis, check or verdict record.
`loop.plain_format` cuts those parts out of the answer format; `loop.plain_prompt` makes the instructions from
`prompt.txt` each time a session starts: the lines on hypotheses, decision rules and verdicts are left out, five
sentences that name them are reworded, and every other paragraph is the same word for word (the purpose, "ask why
before you ask which", "tell a meaningful difference from a marginal one", the parts of the report). It stops if
`prompt.txt` has changed so that one of those lines is not found, or if the result still names a hypothesis, a
decision rule or a verdict. `session.json` records `flags.arm` ("plain"; the ordinary arm records nothing) and the
instructions as given; an existing session keeps its arm. Test: `harness_checks/test_arms.py`. The page has no view
made for such a session: it shows it as a session without hypotheses.

**The arm "supervised": a researcher and a supervisor** (`loop.py --arm supervised`, 2026-11-18, the operator's
decision). A review of the loop's objects over the 43 sessions had shown that the links around the harness's check
were nominal: no verdict ever contradicted its check (378 of 474 repeat it), the judge found 20 of 20 hypotheses to
follow from their guesses, a rethink could call a guess supported after its only hypothesis was refuted, and the
full format scored exactly as the plain arm did. The operator's requirements: two agents with distinct roles,
independent as far as one model allows; every transition of the chain checked by the supervisor and by the
harness's rules; a hypothesis said to come from earlier results must be their fruit; everything shown on the page,
what one did on what ground and what the other said to it.

- **The researcher** proposes: guesses of why, hypotheses, decision rules, experiments, the report. It does not rule
  on its own tests. Its answer has no `verdicts` and no `rethink`; in their place `objections`
  (`loop.supervised_format`), and its instructions are made from `prompt.txt` each time (`loop.supervised_prompt`:
  the lines on rethinking and on verdicts are replaced by what the supervisor does). There is no judge.
- **The supervisor** proposes nothing. It is asked in a request of its own (`loop.supervise`): its own instructions
  (`loop.SUPERVISOR`), nothing of the researcher's conversation, temperature 0. It is shown the brief's description,
  the guess (its result, the guess, what would make it so), the hypothesis, the decision rules, the planned
  simulations and the measured numbers; never the researcher's observations, its reasons for a guess, or a
  hypothesis's question and why. It acts at three places:
  - **Gate 0, a new guess** (`ground_of`): it is shown the records the guess cites as the ledger holds them, and the
    session's earlier guesses, hypotheses and rulings. It says what those records show, names the nearest earlier
    guess or hypothesis, and names a defect or none (`GROUNDS`: the result is not in the records; it repeats an
    earlier one; it ignores a ruling). A guess with a defect is refused, and no hypothesis can come from it. A guess
    about the same records stated after that is accepted whatever the supervisor finds, and its record says that it
    still objects: the supervisor can be wrong and must not be able to stop the work.
  - **Gate 1, a test before any simulation** (`review_design`): for each tested hypothesis it first names the
    strongest rival explanation and what the decision rule would do under it, then what would make it doubt the
    test even if it comes out as predicted, then a defect or none (`DEFECTS`: not about the guess; a rival passes
    too; already answered by the records; confounded; the threshold decides nothing). A rival under which the rule
    would hold is the defect "a rival passes too", whatever it called it. A test with a defect is sent back: no
    simulation is run or counted. Sent again it is run, and its review says "contested" if the supervisor still
    objects.
  - **Gate 2, after the checks** (`rule_on`): the harness has checked the rules; the supervisor says what the check
    means: supported (every check held in a fair test), refuted (a check failed in a fair test) or inconclusive
    (not a fair test: the defect, and what a fair test would compare). It is reminded of what it wrote at gate 1.
    Its ruling is the hypothesis's verdict record, `by` "supervisor". The checks are facts: a ruling that does not
    fit them (supported although a check failed) is recorded as inconclusive, with `changed_by_harness`.
  - **An objection** of the researcher to a ruling (`answer_objection`), at most one for a ruling: the supervisor
    looks at the records again, and its second ruling stands.
- **The harness** keeps what it had: it runs, measures, checks the rules, and refuses what its own rules refuse (a
  rule over known results, a simulation no need names, an id that does not exist). A guess all of whose hypotheses
  were ruled refuted counts as refuted. Nothing is owed by the researcher before the report.
- **Records**: `review` (ids G, `by` supervisor; `gate` "ground" for a guess), `verdict` by the supervisor,
  `objection` (ids O, by the model); a guess keeps the supervisor's reading in `ground`. Beside the ledger,
  `supervisor.jsonl` holds, for each record of the supervisor, what it was shown and what it answered.
  `session.json` records `flags.arm` and `flags.supervisor`.
- **The page** (12.1): a source of its own, "supervisor", with its mark and colour; on a test's card "Its ground"
  (the guess read against its records), "Review" (the test before the simulations: sent back, approved, run
  although it still objects; its rival; what would make it doubt the test), "Ruling" (with a researcher's objection
  and the second look) and "So next"; in the turn's record a part "What the supervisor said, and on what ground"
  with, for each of its records, what it was shown; a lane of its own in the session flow; in "From one hypothesis
  to the next" the column of the judge is the supervisor's. Started from the set-up page ("who rules on the tests")
  or with `POST /api/session {"arm": "supervised"}`.
- **"Two agents"** (`EV.agentsCard`, the operator: show that there are two independent agents and what they do
  differently; not drawn since 2026-11-22, its code kept): on a supervised session's page, before the work itself, three lanes side by side (the researcher
  proposes; the harness measures: the facts; the supervisor checks each step), each with what it is shown, what
  it writes and what it may not do, and under them the nine steps of the work in order with who acts at each and
  what was done in this session by the replay's step, counted from the records (looks and measurements of its
  own; guesses accepted; guesses sound, not accepted, accepted with the objection standing; tests approved, sent
  back, run with the objection standing; simulations and checks; rulings; objections; the report).
- **Test**: `harness_checks/test_supervised.py` (a scripted researcher and a scripted supervisor: each gate, the
  objection, what the supervisor was shown, looking, the other arms unchanged). Not yet measured: whether the
  supervisor, being the same model, objects where it should; a session on `trap-2` and seeded known-bad designs
  are the next step. Not built: the supervisor's reading of the report's claims (gate 3).
- **The first real session, s044 on `trap-2`** (stopped after 7 turns and 27 minutes at the operator's word, no
  simulation run): the researcher looked first (24 tool requests, 19 of them measurements of its own) and the
  supervisor was no rubber stamp (of 14 guesses 5 sound, 1 refused, 8 accepted with its objection standing; all 5
  tests sent back). But 8 of its 9 objections to guesses were unfair, by a fault of the design: it was shown the
  simulation's summary and not what the tools had returned, and the guesses rested on a series and on
  measurements. Two of the five send-backs named "a rival passes too" while its own rival would have failed the
  rule; one argued itself out of the defect in the field after it. Repaired the same evening: the supervisor is
  shown what the tools returned about the simulations (`loop._looked`; since 2026-11-22 every reading of the
  session, as the researcher's ledger holds them); in each of its answers the reasoning is
  written before the decision; "a rival passes too" stands only when its own rival would pass the rule; it
  reasons before it answers (the model's reasoning step is on for its requests; that text is not kept); a guess
  that was set aside is taken up by a new guess that names it in `revises`. Counted with
  `harness_checks/supervisor_figures.py`.
- **The second real session, s046 on `trap-2`** (with the repaired supervisor, the probe and measurements in
  rules; stopped at the operator's word after 5 turns and 40 minutes, no simulation run). What it showed: the
  supervisor judged fairly (6 guesses accepted; 2 refused, one a repetition, one for a number that is not in
  the records). The researcher asked for the probe of the baseline in its first turn and measured, of its own
  accord, what `trap-2` hides: the receiver's window 1,048,576 bytes, the bytes in flight at 72 % of it, a round
  trip of 20.03 ms, no waiting in the TCP queue; its hypotheses were about exactly that. What it did not show:
  a test. Two experiments were refused by the harness's own rules (a rule on a measurement of its own while the
  need still named an output: the instructions said "the output that decides it", corrected; a hypothesis
  from a guess it had itself set aside), and 3 of the researcher's 6 replies were cut off at 32,000 tokens. A
  turn took 6 to 13 minutes, the supervisor's reasoning included. So the chain to a checked finding is not yet
  demonstrated with the real model: the researcher's answer asks too much of it in one reply.
- **Looking before simulating** (the operator: the researcher observes the system whenever it wants, and is no
  optimiser). In this arm a turn takes up to six requests (`loop.LOOKS`; three in the other arms), six turns in a
  row may only look, and the instructions of item 8 say: look before you simulate, a test whose answer the ledger
  holds is sent back, stop when you can say what makes the system behave as it does.
- **Measurements the researcher defines, produced by the simulator without changing any result** (the operator,
  2026-11-18: it may come up with the measurements it needs, and may not change what a simulation gives; in every
  arm).
  - *The probe.* Both programs take `--probe=<seconds>` and then write `probe.csv`, a finer record made by trace
    sinks only and a sampler of its own: TCP's round-trip time (`rtt_ms`), its retransmission timeout (`rto_ms`),
    the bytes sent and not yet acknowledged (`inflight`), the slow-start threshold (`ssthresh`), the receiver's
    window as the sender knows it (`rwnd`), the longest time a packet waited in each queue (`wait_..._ms`), the
    packets in the device's transmit queue (`devq`), with the throughputs, the window and the queue lengths at the
    same instants. In `net` the columns carry the flow's and the link's names (`network.record_columns`). Nothing
    that sends, queues, drops or times a packet is added, and no random number is drawn. Proof, in
    `checks/probe1`: 60 recorded simulations of four sessions and the 35 recorded networks, each run again
    without the probe and with it, give `metrics.json` and `series.csv` byte for byte as recorded (0 of 190 runs
    differ).
  - *Looking.* `measure(run_id, of, stat, t_from, t_to, level)` computes a statistic over a column, or over
    arithmetic over columns, of what a simulation recorded (`tools.MEASURE_STATS`: mean, min, max, std, first,
    last, p05, p50, p95, slope, rate, time above or below a level, the first time above or below it).
    `probe(run_id, every)` runs a simulation that already ran again with the probe, same settings, seed and
    scheduling policy, and keeps its record only if `metrics.json` and `series.csv` of that second run equal the
    first's (logged in the session's `probes.jsonl`); `measure` then reads its columns, and
    `series(run_id, every_n, probe=true)` its rows. Neither costs a simulation.
  - *Testing.* An experiment may define `measurements` of its own (a name, `of`, `stat`, a window, a level;
    `loop.measurement_problem` refuses one that names no recorded column, with the columns there are). Its
    simulations are run with the probe; the first is also run without it, beside it, and the two are compared
    (`probe_same`). The harness computes each measurement for each simulation, keeps it with the simulation's
    measures (`own` names them) and in its evidence line, and a decision rule or a need names it like an output
    (`rwnd_max@a >= 1000000`): the check is the harness's, as for any measure. A rule on such a measurement may
    be about simulations that already ran: the measurement is new, so the rule can fail, nothing is simulated
    and nothing is counted; the harness makes that earlier simulation's finer record itself.
  - The supervisor is shown the definitions with the test and the values with the results. The page shows them on
    the test's card ("Measures": what each is, its value in each simulation).
  - Test: `harness_checks/test_measure.py` (the probe kept because the result was the same; a rule on
    `rwnd_max` checked; a rule on a new measurement of an earlier simulation at no cost; a measurement of no
    recorded column refused; the same on a network: a flow's packets wait 65 ms with a small part and 15 ms with a
    large one). Not yet shown: that the model, in a real session, reaches a cause through measurements of its
    own. Not built: a tap the program does not have (the delay of single packets end to end, the instants of
    acknowledgements); a tap is a change to the program and needs the same proof.
- **The researcher's short reply** (2026-11-18, the operator's "ok do it"). In this arm the researcher states only
  what nobody else can state; the harness derives the rest and the supervisor does what the dropped fields were
  for. The reply has: `observations` (one or two sentences), `requests`, `whys` (`about`, `result`, `guess`,
  `revises`), `hypotheses` (`from_why`, `text`), `drop`, `experiment` (`kind`, `tests`, `question`, `runs`,
  `measurements`, `decision_rules` with `for` and `decision_rule`), `objections`, `report` (`goal`,
  `recommendation`, `limit`, `explanation`, `claims` with `text` and `evidence`). Not asked any more: a why's
  `unseen`, `matters`, `worth`, `reason`; a hypothesis's `question`, `why`, `prediction`, `follows_from`; an
  experiment's `needs`, `varied`, `control`; a rule's `rival` and `rival_predicts` (the supervisor names the rival
  at gate 1); the report's `expected`, `no_difference`, `holds_when`, `breaks_when`, `open_questions`; `verdicts`,
  `rethink`, `budget_request`, `done` (a report ends the session). `supervised_format()` makes the format,
  `LEAN_PROMPT` is the instructions (6,348 characters; `prompt.txt` is not used in this arm), `lean_fill()` puts
  the dropped fields back empty so that the ledger keeps one shape, `lean_needs()` derives each test's needs from
  its rules (the simulations a rule names, the one setting in which they differ, the first measure it names; marked
  `derived`). A rule whose simulations differ in more than one setting is refused; a simulation no rule names is
  left out and noted. The page hides the empty rows and writes "Compares" (by the harness) for a derived need.
  Test: `harness_checks/test_supervised.py`. One reply of the real model to the first turn on `trap-2` (no
  session): 3,099 characters, 6 requests, 3 guesses, 3 hypotheses, every part accepted. Not yet shown: a whole
  session in this form.

**The draft has a limit of its own** (all arms, 2026-11-18). The model reasons before it answers (its draft), and
`--max-tokens` (32,000) counted draft and answer together. In s045 and s046, 5 of 11 answers were empty with
`finish_reason=length`: the draft alone had used all 32,000 tokens, six minutes each, and no answer was written.
The length of the answer was not the cause (a whole answer is about 6,000 characters). `ask()` now sends
`thinking_token_budget = draft_tokens(max_tokens)`, half of the limit (16,000 for the researcher, 4,500 for the
supervisor): the model server (vLLM 0.32, `--reasoning-parser qwen3`) ends the draft there and the model writes
its answer. Measured on the server with a puzzle and a limit of 6,000: without the budget 6,000 draft tokens and
no answer; with a budget of 300 or 1,500 the draft stops at 299 or 1,499 tokens and a valid answer follows. A
server that refuses the field is asked once more without it, and not again. `session.json` states `draft_tokens`.
Not changed, and to be decided by the operator: the model's card advises temperature 1.0, top_p 0.95, top_k 20
when it reasons (the harness uses 0.3, and 0 for the supervisor), and the model reasons at its highest effort
(`reasoning_effort` xhigh, the template's default; medium and low exist).

### 8.2 A turn

1. The ledger is rendered as text (8.7). If it is over 100,000 tokens, counted
   by the server's tokenizer, the session ends ("ledger too large").
2. A `turn` record is appended: simulations left, open hypotheses, the ids
   added since the previous turn, and whether this is a last turn.
3. The model is asked once. System message: `prompt.txt`. User message: the
   brief as JSON (with the descriptions of the outputs and the tools), the
   budget line, the ledger text, and the results of the tools it asked for in
   its previous answer. The answer format (8.3) is passed as `response_format`
   (`json_schema`), so the reply is one JSON object of that format.
4. If the reply is empty, cut off (`finish_reason` "length"), not JSON, or
   holds nothing usable, the model is asked a second time. Each attempt's draft
   is recorded.
5. What can be used of the answer is used (8.3); what cannot is refused, part
   by part.

### 8.3 The answer, part by part

The answer format (`schema.json`; every field is required, the optional ones
may be null or empty):

```
{ "observations":   text
  "rethink":        [ {id: Y id, in_light_of: [ids], now: "verify"|"set_aside"|"refuted", because} ]
  "whys":           [ {about: [ids | run id | "brief"], result, guess, unseen, matters, worth: "verify"|"set_aside", reason, revises: Y id | null} ]
  "hypotheses":     [ {from_why: Y id, text, question, why, prediction, follows_from: [ids | "brief"] (optional)} ]
  "drop":           [ {id, why} ]
  "experiment":     { kind: "test"|"explore", tests: [H ids], question,
                      needs: [ {for: H id, to_know, varies: knob|"none"|"structure", measure, simulations: [labels]} ],
                      varied: [knobs], control: label|null,
                      runs: [ {label, params: {every knob of the brief: value}} ],
                      decision_rules: [ {for, decision_rule, rival, rival_predicts: "held"|"failed"} ] } | null
  "verdicts":       [ {for, result: "supported"|"refuted"|"inconclusive", because, next} ]
  "report":         { ... 8.6 ... } | null
  "requests":       [ {tool, args} ]
  "budget_request": {simulations, why} | null
  "done":           true | false }
```

**The chain of reasoning is fixed by the format** (**DECISION 2026-11-17**, the
operator: "after the AI formed a hypothesis, it clearly chooses what it needs
to know and subsequently forms simulations"; "its main role is not to try many
less informed fixes ... but actually looking into the system and form 'why'").
Measured on eight sessions before the change: of 101 decision rules 70 compared
simulations that differ in one setting, 14 in several, 17 judged one simulation
against a number; 28 of 228 test simulations were named by no rule; 12 of 39
sessions ended with the budget used up (typical spending 12, 12, 12, 3, 1). The
chain, link by link, each a part of the answer in this order:

1. a result (records of the ledger);
2. `whys`: informed guesses of why that result came out so. `about` the
   records; `result` in one sentence; the `guess`; `unseen`: what in the system,
   not directly visible in the measures, would make it so; `matters`: what it
   would mean for the goal; `worth`: verify or set_aside, with the `reason`.
   Ledger type `why`, ids `Y<n>`. A why that was set aside stays in the ledger;
3. `hypotheses`: each from a why whose worth is verify (`from_why`; one in the
   ledger or one of the same answer). `follows_from` may be left out: the
   harness takes it from the why's `about`;
4. `needs`, in a test experiment, before its simulations: one for each tested
   hypothesis: what must be known to decide it, the one knob that differs
   between its simulations (`none`: one simulation against a stated number;
   `structure` where the brief lets the structure change), the measure that
   decides it, and the simulations made for it;
5. the simulations: only those a need lists.

**A guess is not fixed by how it was first stated** (**DECISION 2026-11-17**, the
operator: "strong and grounded by whys, but not fixed by the initially formed
whys"). A why has a standing that can change (`loop.why_states`): `rethink`
looks at an earlier why again in the light of results that came in after it
(now verify, set_aside or refuted; ledger type `rethink`, ids `K<n>`); a new why
may name the one it replaces (`revises`; the old one then counts as revised).
No new hypothesis may come from a why that was stated, or last rethought,
before the latest results: it must be rethought first, naming one of them. A
why that was set aside is taken up the same way. The ledger text shows each
why with its standing now and marks one that is stale.

**The step from one hypothesis to the next is reviewed, and the review comes first** (**DECISION 2026-11-17**, the
operator: "the most significant upgrade is making the AI review the transition between hypotheses; make sure it is
correctly implemented"). `loop.tested_whys`: a why that is still marked verify and of which a hypothesis was checked
since it was last settled is due. While a why is due, the answer's new hypotheses and its experiment are refused
("first look again at the guesses that were just tested: Y4 (H4: C4 held; H5: C5 failed) ..."), and so is the report;
a rethink of each in the same answer (or a new why that replaces it) lifts that. The turn's text says it first ("LOOK
AGAIN FIRST: ..."). Found on s042: in turn 3 the model's three rethinks named K4, K5, K6 (the numbers of rethinks)
instead of the whys, were refused, and it went on to new hypotheses unreviewed. In the answer format the id of a why
can now only be written as Y and a number (`pattern` on `rethink.id`, `hypotheses.from_why`, `whys.revises`; the
model server enforces it). A rethink's `now` may also be `supported`.

**Choosing which guesses to verify is closed like a verdict** (**DECISION
2026-11-17**; s041 marked all 11 whys "verify", set none aside, and never took
up two of them, one the true cause). Before the report is accepted, every why
whose standing is verify has led to a hypothesis or been settled by a rethink;
otherwise the report is refused once (`loop.WAIT`), naming them, and the next
answer is taken as it comes.

**The judge** (**DECISION 2026-11-17**, the operator; `loop.judge_link`, flag
`--judge on|off`, default on; not in the arm `plain`). The harness could only
check that the why a hypothesis names exists (s041: H2 named a why about the
1 MB / 20 ms cap and was about measuring 30 s instead of 10 s). A second model
call (the session's own model, no draft, temperature 0, 400 tokens) is given
the system's description, the knobs, the why (result, guess, unseen) and the
hypothesis (text, prediction), and answers `{follows, because}`: would testing
the hypothesis tell whether the guess is true? A hypothesis it finds unconnected
is refused with its reason, but only when a second reading agrees (the judge is
not steady on a pair at the border: on s041's nine pairs it said no to H2 in 3
of 3 rounds and to H3 in 1 of 3). Each reading is kept: with the hypothesis
(`judge`), and in a ledger record of type `judge` (`J<n>`, by the harness, not
shown to the model). When the judge cannot be asked the hypothesis is accepted
unjudged and says so. About 0.7 s a call.

`prompt.txt` opens with the role in these words' sense: not to try many
settings and keep whichever comes out slightly ahead, but to look into the
system, ask why a result came out so, and infer what is not directly visible.
The arm `plain` (10.9) has none of this: no whys, no needs.

**The params object comes from the brief; every design states every knob**
(**DECISION 2026-11-13**, the operator's `FORMAT_FIX.md`, Part 1). At the start
of a session `loop.answer_format` puts into `schema.json` what depends on the
brief: `params` gets one property per knob, in the brief's order, **all
required**, each with its type (`tools.KNOB_TYPES`) and, for a knob with
choices, its `enum`; a setting the brief fixes is not a property. `varied`
lists the same knobs, and `runs` holds at most the brief's simulations per
experiment. For `two-hosts-udp-demand` the format has no `udpRate`.

Why: the model server enforces the **order** of a schema's properties. Until
2026-11-13 `params` was one fixed object with every key optional and
`weightUdp` first, so a design that began with another key could no longer
state `weightUdp` at all, and it ran at the default 0.5. Confirmed with two
requests to the server on 2026-11-13 ("Give one design with udpRate 400Mbps
and weightUdp 0.8, stating udpRate first"): under that order the answers
began `{"udpRate": "400Mbps", ...` and none of three stated `weightUdp`; with
the properties listed in the opposite order all three were
`{"udpRate": "400Mbps", "weightUdp": 0.8}`. With every knob required the same
request gives all six knobs, `weightUdp` 0.8 among them. What this did to the
earlier sessions is in section 11 and in section 15, item 9.

**A hypothesis is also put as a question** (`question`, required): the
hypothesis as one plain question, for a reader who is not a specialist. The
harness requires only that it is not empty; "at most 20 words" is guidance in
the prompt and in the format's description.

**A hypothesis also says why it is asked** (`why`, required since 2026-11-14;
**DECISION**, the operator: the page should show why the AI needed a question
for the aim, and the records held nothing of the kind): one plain sentence
saying how answering the question helps reach the goal. The harness requires
only that it is not empty ("at most 25 words" is guidance); a hypothesis
without one is a refused part ("a hypothesis needs a why: ..."), and the rest
of the answer is used. It is not part of the ledger text the model reads
back. Sessions before this date have none, and the page then shows none.

**Each turn's accepted answer is kept as it was received**, before any part
was refused or cut, in `sessions/<id>/answers.jsonl` (`{turn, answer}`, one
line per turn that had something usable), so that what was asked can be
compared with what was run. No tool reads the file.

`loop.sort_out` accepts or refuses each part on its own, in this order, and
the parts accepted earlier count for the later ones:

| Part | Accepted when |
|---|---|
| verdict | the hypothesis is open and one of its decision rules has been checked; it has a result and a because. It closes the hypothesis. |
| drop | the hypothesis is open, none of its decision rules has been checked, and there is a reason. A tested hypothesis cannot be dropped: it needs a verdict. |
| new why | `result`, `guess`, `unseen`, `matters` and `reason` are not empty; `worth` is verify or set_aside; `about` lists records that are in the ledger (evidence tables, simulations, checks, verdicts; a verdict of the same answer counts) or the word `brief`. It gets the next id `Y<n>`, usable in the same answer. |
| new hypothesis | `from_why` names a why whose worth is verify (in the ledger or accepted from this same answer); it has a text, a question (not empty), a why (not empty) and `follows_from` (taken from the why's `about` when left out): ids of verdicts, checks, evidence tables or simulations that are in the ledger (a verdict accepted from this same answer counts, by the id it is about to get), or the word `brief`. It gets the next id `H<n>`, usable in the same answer. |
| experiment | see 8.5. At most one per turn. It is itself taken part by part: a design or a decision rule can be refused and the rest run. |
| budget request | a whole number of at least 1 and a reason. Granted up to the brief's limit, before this turn's experiment is counted. |
| report | see 8.6. Only together with `done`, and `done` only with a report. |

A refused part becomes a `note` by the harness ("refused part of the answer:
... Reason: ..."), with `part` and `reason` as fields, which the next turn's
ledger text shows; the rest of the answer is used. The whole answer is refused
(a `malformed` record, with `refused`: [{part, reason}] and the first 2,000
characters of the content) only when nothing in it can be used.

`observations` is kept once, in the first record the turn adds (an answer none of whose parts made a record keeps
them in a `note` by the model). Since 2026-11-22 (the operator: "I want the researcher to see all lookup results and its own
observations previously accumulated all the time") the ledger text the researcher reads shows every turn's observations in their
place, as "turn N your observations: ...", and a turn of requests only as "a turn of requests only: tool(args); ..."; until then a
turn's observations were shown only for a turn of requests only (as the record's JSON). The supervisor is never given them.

Tool requests: at most 3 per turn. Each is a `request` record and what came
back a `result` record (a reading, T1, T2, ...). Since 2026-11-22 (the operator:
"I want the researcher to remember everything it found across all turns ... keep
every lookup result in the notebook, so both agents see the same thing") every
reading stays in the ledger text of every later turn, in its place, in full up to
6,000 characters with its line breaks (`loop.reading`), and the supervisor is
given the same readings the same way at each of its gates (`loop._looked`); the
next turn's "TOOL RESULTS" line names the new readings' ids instead of giving
them a second time. Until then the results were given once, in the next turn
(the arm "supervised": then one line of 260 characters), and the supervisor a
selection of its own (the simulations at hand, newest first, 5,000 to 9,000
characters). A turn with requests only is a "tool-only" turn (a `note` by the
model); after more than 3 of them in a row the model is told to decide (its
readings are no longer withheld).

*Under review (branch review/harness-2026-11-22, not deployed): what the researcher can reach across turns,
from a review of s047 and s048.*
- Within LEDGER_TOKENS (READINGS_ROOM = 40,000 characters): while the readings together are under it, each stands
  in full; past it, a long reading (over 1,500 characters) older than the newest four is shortened to its first 600
  characters and says how much was left out ("ask again with the same request for the whole of it"); the
  supervisor is given the same forms (`loop.reading_forms`). s047: 35,714 tokens, s048: 19,532 (of 100,000).
- Readings count as evidence: a why's `about`, a rethink's `in_light_of` and a report claim's `evidence` may name
  a reading by its T id, or a run by its id (r010: that run's simulation and what the tools returned about it; in
  a claim, the simulation). For a rethink, a reading counts as new to a why when its request was made in the turn
  the why was last settled or later (`since(..., readings=True)`): what a turn's requests return is seen only in
  the next turn, though it stands before that turn's whys in the ledger (s048: T10 to T12, asked for with Y11 in
  turn 5, seen in turn 6). A reading alone does not make a why due for a rethink. The turn-6 rethink of Y11 in s048
  ("in the light of r010", refused, note N2) is accepted.
- Free turns: once the budget is used up, FREE_TURNS = 2 more turns (`last_turn: "free"` in the turn record) in
  which requests, whys, rethinks, hypotheses and tests are accepted if no new simulation is needed (every
  simulation of the experiment already ran: its result is returned, a measurement of its own is computed from what
  it recorded); an experiment that needs one, and a budget_request, are refused with the reason. A report in a
  free turn ends the session ("done by the model"); after the free turns, the report-only last turn as before.
- Everything recorded comes back to the researcher: a hypothesis's question and why, a test's question, and what
  the supervisor's reviews and rulings found (what the records show, the defect, what would make it doubt the test,
  the nearest earlier guess). The judge's readings stay kept for a person (2026-11-17).
- All three arms; the arm "plain" has no whys, rethinks or tests (for it: readings in claims, and requests and
  explore experiments on simulations already run in the free turns); the supervised arm has no rethinks.
- The researcher's own measurements: measure has crossings (with level), corr and lag (with a second expression, `with`), also in
  an experiment's measurements; the instructions give examples of combined measurements; on a network, trace_points(run_id) lists every object
  a tap can name and probe(run_id, every, taps={name: ns-3 Config path}) records them (tap_<name>, tap_<name>_n, tap_<name>_bytes) with the
  program net-taps (a copy of net, built on its own); the result run again is byte for byte the same.
- The short answer format of the arm "hypotheses" (a new session, flag `format: "short"`; a session started before keeps the full one):
  no why.worth or reason, no hypothesis.prediction or follows_from, no experiment.varied, control or needs, no budget_request
  (`loop.SHORT_DROP`, `short_format`, `short_prompt`, `short_fill`). The harness fills them in: worth "verify", follows_from from the
  why's about (a reading too, in every arm), varied from the designs, needs from the decision rules (`lean_needs`), the judge given
  the rule of the hypothesis's test where its prediction stood. A guess never taken up does not hold back the report. Kept: a
  hypothesis's question and why, why.unseen and matters, each rule's rival, rethinks, verdicts, the whole report. In both short
  formats designs are compared as trim compares them (`as_run`: 100 and 100.4 packets are one value), and the turn's text names
  budget_request only to the formats that have it (the arm "plain", sessions in the full format).
- Findings (every arm): a finding F*n* is one thing the results do not explain (about: the records it rests on; text: one sentence with its
  numbers), raised by the researcher (`findings` in its answer) or, in the arm "supervised", by the supervisor (in its ruling, and in one call after
  the baseline and each explore experiment: what is unexplained, never why; kept only with ids that exist and a number). Its status changes only by
  the researcher's decisions A*n* (`decisions`: work with refs, park with a reason, close with evidence, same_as); a work decision without refs counts
  as worked on, not as looked at; a guess whose about names F*n* works on it. Every turn begins with the FINDINGS list; open findings are due each
  turn, parked and idle working ones after PARK_TURNS = 2. A report offered while the researcher can still work is held while a finding was never
  looked at (at most FINDING_HOLDS = 2 times); in the last turn the harness adds every finding not closed to open_questions. A record Z at the end
  tallies each finding. Nothing about findings refuses another part. `session_figures.findings_counts`; the page draws a bar per finding under
  the hypotheses.
- The review of a test before it runs, in rounds (gate 1, the arm "supervised"; it replaces the "cannot tell" rule of the fourth commit): the
  researcher states each rule's rival and rival_predicts (`rival_problem`, shared with the arm "hypotheses"; "held" is refused before any call);
  the supervisor judges that rival (each box after its reasoning: stronger_rival, rival_is_weak; under_rival, rival_outcome; because, defect;
  feedback), approved only with no defect, no stronger rival and rival_outcome "failed"; contradicting boxes get one direct question, a second
  contradiction is a refusal; feedback never holds a decision rule (cut, with a note). A refused test is repaired by the researcher in the same
  turn (a short call: the test only), re-checked by the harness and reviewed again, REVIEW_ROUNDS = 3, then AFTER_ROUNDS ("contested": it runs and
  the ruling knows; "dropped"). Every round ends before any simulation of the experiment runs; then the approved tests run, each repaired one as an
  experiment of its own, in the same turn. Each round is a review record, each repair a record P*n*. `session_figures.design_rounds`.
- Guesses (the arm "supervised"; part D): the supervisor's "not_from_what_was_learned" is a recorded warning (the guess is accepted); any other
  refusal of a guess (the harness's chain rule among them, or the supervisor's) brings one restatement in the same turn, checked again (by the
  harness alone when the harness refused it), then the guess is accepted, contested if it still fails: its hypotheses and test go ahead.
  `session_figures.guess_reviews`. One limit on the supervised arm's whole instructions (findings text included): 10,000 characters.
- Deployed on 2026-11-22 (the operator: A, B and D, nothing else): part 1 (which A needs), A, B and D; parts 2 and 3 stay here
  (`derive_dep.py` makes the deployed harness: the live tools.py, schema.json, manifest.json, network.py; `SHORT_FORMAT = False`).
- Checks: harness_checks/test_keep_readings.py, test_cite_readings.py, test_free_turns.py, test_measure_relations.py, test_taps.py, test_short_format.py, test_findings.py, test_design_rounds.py, test_guess_restate.py (new);
  test_supervised.py (the readings' new form; readings and observations kept, the supervisor never sees an
  observation). In a last turn (8.8) requests are
not taken.

*Deployed on 2026-11-22 at 17:05 (the operator: "Deploy A, B and D together, nothing else"; built on branch review/harness-2026-11-22,
whose REVIEW.md has the reasons, the checks and the results):*
- **Readings as evidence** (part 1, which A needs): a why's `about`, a rethink's `in_light_of` and a report claim's `evidence` may name a reading
  (T*n*) or a run id (its simulation and its readings); a reading seen since a why was settled counts as new for its rethink (`since(...,
  readings=True)`), but a reading alone does not make a why due. Within READINGS_ROOM = 40,000 characters every reading stands in full. Once the
  budget is used up, FREE_TURNS = 2 more turns to look and to test on simulations already run, then the report-only turn. Everything recorded comes
  back to the researcher (a hypothesis's question and why, a test's question, the supervisor's findings); the judge's readings stay a person's.
- **Findings** (A, every arm): a finding F*n* is one thing the results do not explain (about: the records it rests on; text: one sentence with its
  numbers), raised by the researcher (`findings` in its answer) or, in the arm "supervised", by the supervisor (in its ruling, and in one call after
  the baseline and each explore experiment; what is unexplained, never why; kept only with ids that exist and a number). Its status changes only by
  the researcher's decisions A*n* (`decisions`: work with refs, park with a reason, close with evidence, same_as); a work decision without refs counts
  as worked on, not as looked at; a guess whose about names F*n* works on it. Every turn begins with the FINDINGS list; open findings are due each
  turn, parked and idle working ones after PARK_TURNS = 2. A report offered while the researcher can still work is held while a finding was never
  looked at (at most FINDING_HOLDS = 2 times); in the last turn the harness adds each finding not closed to open_questions. A record Z at the end
  tallies each finding. Nothing about findings refuses another part. `session_figures.findings_counts`; the page draws a bar per finding under the
  hypotheses (pointing links a bar and its hypotheses; a click opens its history).
- **The review of a test in rounds** (B, the arm "supervised"): the researcher states each rule's rival and rival_predicts (`rival_problem`, as in
  the single-AI arm; "held" is refused before any call); the supervisor judges that rival (each box after its reasoning), approved only with no
  defect, no stronger rival and rival_outcome "failed"; contradicting boxes get one direct question, a second contradiction is a refusal; feedback
  never holds a decision rule (cut, with a note). A refused test is repaired by the researcher in the same turn (a short call: the test only),
  re-checked and reviewed again, REVIEW_ROUNDS = 3, then AFTER_ROUNDS = "contested" (it runs; the ruling knows). Every round ends before any
  simulation of the experiment runs; then the approved tests run, a repaired one as an experiment of its own, in the same turn. Each round is a
  review record, each repair a record P*n*. `session_figures.design_rounds`; a test's detail lists its rounds.
- **Guesses** (D, the arm "supervised"): the supervisor's "not_from_what_was_learned" is a warning (the guess is accepted, its review says so);
  any other refusal of a guess (the harness's chain rule among them, or the supervisor's) brings one restatement in the same turn, checked again
  (by the harness alone when the harness refused it), then the guess is accepted, contested if it still fails: its hypotheses and test go ahead.
  `session_figures.guess_reviews`. The supervised arm's whole instructions (with the findings text) are kept under 10,000 characters.
- **Not deployed** (still under review on the branch): part 2 (the statistics crossings, corr and lag, `with`, taps on trace sources,
  trace_points: the live tools.py, schema.json, manifest.json and network.py stay), part 3 (the short answer format of the single-AI arm:
  `SHORT_FORMAT = False`), and part C (follow-through on findings, shelved).

### 8.4 Decision rules: `decision_rules.py`

A decision rule is a comparison the harness can evaluate itself. Grammar:

- numbers;
- `measure@label`: the value of an output in the simulation with that label
  (`@label` may be left out when the experiment has one simulation);
- `+ - * /` and parentheses; `abs()`, `min()`, `max()`;
- exactly one of `< <= > >= ==` per comparison;
- comparisons joined by `AND` and `OR` (`AND` first), grouped with parentheses.

It is read by a small recursive-descent parser, never by `eval`. Every
comparison is evaluated, so a simulation that gave no value is always noticed.

Each decision rule comes with a **rival**, a competing explanation of how the
system behaves, and `rival_predicts`: what the rule would give if the rival
were true. A rule with `rival_predicts: "held"` is refused: it would hold under
the rival too and cannot tell the two explanations apart.

### 8.5 An experiment

Readable as it was sent (`loop.experiment_problem`) when:

- it has 1 to `simulations_per_experiment` simulations, each with its own
  label (letters, digits and `_`, at most 20 characters);
- every `params` key is a setting of the brief;
- `control` is one of the labels or null, and `varied` names knobs;
- kind `test`: `tests` lists open hypotheses, with at least one decision rule
  for each and none for any other; every rule is readable and has its rival;
  `needs` has one readable entry for each tested hypothesis;
- kind `explore`: a question, no tests, no needs and no decision rules.

**Needs tie each simulation to a hypothesis** (`loop.needs_problem`;
**DECISION 2026-11-17**). Judged on what `loop.trim` leaves, like the budget;
the experiment is refused, with the reason, when: the simulations of a need
differ in anything but the knob it names (or do not differ in it); a need that
says nothing varies lists more than one simulation; a decision rule of the
hypothesis names a simulation its need does not list, or does not name the
need's measure; a simulation is listed by no need ("made for no hypothesis").
The experiment record keeps `needs` (what is left of them after `trim`).

**A decision rule must be able to fail** (`loop.trim`; **DECISION 2026-11-17**).
A rule all of whose simulations equal ones already run in the session names
only known results: it is refused as no test ("what the known results show
belongs in a why or in observations"). Found by reading s041 and s033: both
"tested" the limit they had already measured (H5, H14), the check could only
hold, and the report cited it. In s026 to s041 there are 12 such rules, all
held, all cited by a final report. A design that equals an earlier simulation
may still be the control of a rule that also names a new one.

**One experiment may use at most half of the simulations that are left**
(`loop.spend_cap(left, per) = max(1, min(per, (left + 1) // 2))`; **DECISION
2026-11-17**, the operator: sessions spent the budget in three experiments of
12 and had nothing left for what the results raised). The turn's text states
the number ("This turn's experiment may run at most N new simulations");
a larger experiment is refused with it.

**A plan that cannot test anything is cut back before anything is run**
(`loop.trim`; **DECISION 2026-11-13**, `FORMAT_FIX.md`, Parts 1 and 2). Each cut
is a refused part with its own note, and the rest of the answer is kept:

| What | Refused | The note says |
|---|---|---|
| a design that does not state every knob (the guard behind the answer format: `tools.clamp(design=label)`) | that design | "design `<label>` does not state `<knob>`" |
| a knob listed in `varied` that has one value in every design | the whole experiment | "`<knob>` is listed as varied but has the single value `<v>` in every design" |
| a decision rule that names two or more labels of which two are the same simulation (same settings and seed, also when both are returned from the same earlier simulation) | that decision rule | "this decision rule compares `<a>` with `<b>`, which are the same simulation (same settings and seed), so it cannot hold or fail for a reason; change the designs or the rule" |
| two designs of one experiment with the same settings and seed | the later design | "design `<b>` has the same settings and seed as `<a>`; give it different settings or remove it" |
| a decision rule that names a refused design | that decision rule | "this decision rule names `<b>`, a design that was refused; change the designs or the rule" |
| a design that only refused decision rules name | that design: nothing is run for a refused rule's hypothesis | "design `<a>` is named only by a decision rule that was refused, so it is not run" |

A tested hypothesis left without a decision rule is no longer tested by the
experiment; when no decision rule or no design is left, the experiment is
refused. None of these notes says anything about the system: each speaks only
of the model's own plan. What is left is then counted against the budget: the
new simulations it needs must fit in what is left.

In s002 to s019, recorded before this, the same rules would have refused 198
repeated designs in 32 experiments, 107 decision rules, and 29 experiments for
a varied knob of one value.

What the harness then does (`loop.experiment`):

1. Appends the `experiment` record: the design and the decision rules as
   stated, and for each simulation the settings actually used. A value outside
   its range is forced into it, and a setting the brief fixes takes the brief's
   value; both are recorded as `clamped` (asked, used).
2. Runs all its new simulations at once (`tools.run_many`: one process each),
   and writes the operator's line for each to `checks/operator.jsonl`.
3. Appends one `simulation` record each (label, run id, settings used, metrics
   or error).
4. Appends one `evidence` record: one text line per simulation (label, run id,
   settings changed from the defaults, the measured values).
5. Evaluates every decision rule and appends one `check` record each: the
   rule, the rule with the measured numbers written in, and `held`, `failed`,
   or `not checked` (a simulation it names gave no value).

**A simulation is not run twice.** One with the same settings and seed as a
simulation of an earlier experiment of the session (compared on every program
option, rates by value) is not run again: its record carries the earlier
result and `same_as`, a note says so, and it is not counted against the
budget. Within one experiment a repeated design is refused (above); sessions
before s020 hold such repeats, returned under `same_as` as well.

The budget counts simulations actually run.

### 8.6 The final report

```
{ "goal":           the goal the answer is best for (open brief: the one the model chose, and why)
  "recommendation": {knob: value}
  "expected":       {output: number}
  "no_difference":  [knobs]   since 2026-11-15: the knobs whose tested values made no meaningful difference to the goal
  "limit":          text      since 2026-11-15: what limits the result at the recommendation, and the ledger ids that show it
  "explanation", "holds_when", "breaks_when": texts
  "claims":         [ {text, role: supports | background | limits, evidence: [ledger ids]} ]
  "open_questions": [texts] }
```

**The recommendation states every knob of the brief** (**DECISION
2026-11-15**, a repair: the operator asked whether a claim of s030 was shown
"without simulation"; the claim was sound, the recommendation beside it was
not). Until then the recommendation had a fixed list of six knobs, all
optional, and the model server writes an object's properties in the format's
order (8.3): a report that had passed over a knob could not name it any more,
and a knob outside the list (`tcpBufBytes`) could not be recommended at all.
s030's report names ratio 0.493 with BBR, UDP at 3 Gbps, queues of 500 and
16 MB buffers in its claim and took its expected values from that simulation,
but its recorded recommendation holds only the ratio, the TCP type, the
measured time and the seed. Now `loop.answer_format` builds the
recommendation from the brief like a design (one property per knob, all
required), `check_report` refuses one that leaves a knob out (the guard), and
the prompt says that a value is stated for every knob and that the expected
values and the supporting claims are read against exactly these settings.

`loop.check_report` refuses a report whose recommendation names a fixed setting
or something that is not a knob, leaves a knob of the brief out, or has a value outside its range; whose
`expected` is not numbers by output names; or whose claims cite an id that is
not in the ledger.

If a hypothesis with a checked decision rule still has no verdict, the report
is refused once, with the list, and the verdicts are asked for together with
the report; the second time it is accepted as it comes.

**What limits the result, and what made no difference** (**DECISION 2026-11-15**, the operator: "The AI should not
just optimize settings from simulations but ask why ... If any setting doesnt make meaningful improvement it should ask
why rather than improving a marginal amount and present it as the best one"; s031 had recommended a TCP type and a
seed for differences of 0.02 % and never asked what held TCP at its limit). The report has two required parts before
its explanation: `no_difference`, a list of knob names (it may be empty; the answer format allows only the brief's
knobs), and `limit`, a text. `check_report` refuses a report without a `limit`, one whose `no_difference` names
something that is not a knob, and one that names a knob the session never varied (fewer than two values of it among
its simulations): a setting that was not tested cannot be said to make no difference. Reports recorded before have
neither part. Test: `harness_checks/test_tolerance.py` (the session `lim1`). The page shows both as the part "What
limits the result" (12.1).

An accepted report is a `report` record (`R1`) and `sessions/<id>/report.json`,
and the session is over.

Each claim has a **role** (**DECISION 2026-11-14**, `READABLE_PAGE.md`, Part
5): `supports` (a reason for the recommendation), `background` (how the system
behaves) or `limits` (when the recommendation would change). The answer format
requires it, between the claim's text and its evidence; `prompt.txt` says it
in one sentence; `check_report` refuses a report in which a claim has no role
or a word that is not one, as a refused part ("report.claims: claim 1 has no
role: ..."). The page orders the report by it (12.1). Reports recorded before
this have no roles and are shown with their claims in one list.

### 8.7 The ledger

One JSON object per line: `{id, turn, type, by, parent, body, ts}`. `by` says
who produced the content and is written by the harness, never taken from the
model's answer.

| Type | Id | By | Body | In the prompt |
|---|---|---|---|---|
| why | Y | model | about, result, guess, unseen, matters, worth, reason, revises (since 2026-11-17) | yes, with its standing now |
| rethink | K | model | for, in_light_of, now, because | yes |
| judge | J | harness | guess, hypothesis, follows, because: one reading of the judge | no |
| hypothesis | H | model | from_why (since 2026-11-17), text, question, why, prediction, follows_from | yes, with its current state and the why it comes from (the question and the why are not shown) |
| drop | W | model | for, why | yes |
| experiment | X | model (X0: harness) | kind, tests, question, varied, control, runs [{label, params, clamped}], decision_rules: what is left after `loop.trim`; `params` holds every knob of the brief (X0's is empty) | yes |
| simulation | S | simulator | label, run_id, params, metrics or error, same_as | no (the evidence has its line) |
| evidence | E | harness | experiment, lines | yes |
| check | C | harness | for, experiment, decision_rule, rival, rival_predicts, with_numbers, result; since 2026-11-15, when a comparison of the rule was decided by less than the tolerance: tolerance (per cent) and within_tolerance [{left, op, right, percent}] | yes |
| verdict | V | model | for, result, because, next | yes |
| report | R | model | the report | yes |
| note | N | harness (tool-only turn: model) | text, and fields of its kind | yes |
| malformed | M | harness | error, refused, content | yes, the reason only |
| turn | U | harness | simulations_left, open_hypotheses, added, last_turn | no |
| request / result | Q / T | model / harness | tool, args / tool, result | request: no; result: yes, in full with its id (since 2026-11-22) |
| draft | D | model | chars, tokens, model, finish_reason | no |

Ids count up per type. The prompt shows one line per record, each cut at 6,000
characters. No record type is the operator's: the brief and the scheduling
policy are theirs, and they are not ledger records.

Old formats, read but not written: `s001` has one simulation per experiment,
`pass_if` instead of decision rules, `scratch` records and no `by`; `s002` and
`s003` say `rules` / `rule`; sessions before `s008` have no `follows_from`, no
`turn` records and no structured refusals; sessions before `s020` have no
`question`, no `answers.jsonl`, and designs whose `params` hold only the knobs
the model stated (the others ran at the brief's default); sessions before
`s028` have no `why` on their hypotheses.

*Every call of the model: `calls.jsonl`* (since 2026-11-22, the operator: to look into how the agents work and
what they see). Beside the ledger, one line per call of the local model, by the researcher, the judge or the
supervisor (`loop.called`, through which the three go): `n`, `turn`, `agent`, `at`, `seconds`, `model`, `draft`,
`temperature`, `max_tokens`, `system` and `user` (the two messages it was given), `reasoning` (what it wrote before
its answer), `answer`, `finish_reason`, `usage` (the model server's counts). No tool and no model reads it; a
scripted session (harness_checks) writes it too. Only the owner's page shows it (10.1, 12).

### 8.8 How a session ends, and `session.json`

| `how` | When |
|---|---|
| done by the model | the model set `done` with an accepted report |
| all simulations used, report given in the last turn | the budget was used up; one last turn follows in which no experiment is accepted and the report is required; the report was accepted. Sessions before 2026-11-17 say "simulation limit reached", which read like an error |
| all simulations used, no usable report | that last turn brought none (before 2026-11-17: "simulation limit reached, no usable report") |
| 3 turns in a row without a usable answer, report given in the last turn | after 3 unusable turns one last turn accepts only the report |
| 3 turns in a row without a usable answer | that turn brought none either |
| ledger too large | the rendered ledger passed 100,000 tokens |
| model server error | the server failed or answered with an error; a note carries it |
| stopped from outside | SIGTERM or SIGHUP |

`session.json`:

- written at the start: `id`, `brief`, `model`, `started`, `flags` (budget,
  draft, max_tokens, temperature, baseline), `given` (the brief with its
  description filled in, plus the manifest: exactly what the model is shown),
  `prompt` (the text of `prompt.txt`);
- added at the end: `ended`, `how`, `report` (its ledger id or null),
  `left_open` (hypotheses still open), `without_verdict` (tested but not
  judged), `turns`, `simulations`, `calls` (requests the model server
  answered), `cut_off` (how many ended with `finish_reason` "length").

The scheduling policy is not in it. A session can be reported from
`session.json` and `report.json` alone, without opening its ledger.

### 8.9 `prompt.txt`

Plain text. It says: the system cannot be seen inside and is reached only
through the tools and experiments; the ledger is the only memory; then the
parts of the answer one by one, with the rules of 8.3 to 8.6 in the model's
terms; that a refused part is left out and named in a note; "Be concrete and
quantitative. Prefer experiments that distinguish between explanations."

Since 2026-11-13 it also says that every design states a value for every knob
of the brief (a knob left as it was is stated with the value it had), and that
each new hypothesis is also given as one plain question of at most 20 words,
for a reader who is not a specialist (and, since 2026-11-14, with why: one
plain sentence of at most 25 words saying how answering it helps reach the
goal); that a knob which has a step in the
brief is rounded to it; and that a goal's tolerance makes two results closer
than that many per cent count as equal.

**Since 2026-11-15 the last turn names the hypotheses that still need a
verdict** (the operator, on seventeen refusals in the last turn of s030: "Why
did these errors happen?"). The prompt said "give a verdict on every hypothesis
that has a checked decision rule", and the last turn's message "give your
verdicts on hypotheses whose decision rules have been checked": the model
judged all seventeen again, and each second verdict was refused ("H1 is not an
open hypothesis"). The prompt now says "…and no verdict yet", and that a
hypothesis with a verdict is closed and a second verdict is refused; the last
turn's message (`loop.py`, mode "budget") lists the open hypotheses with a
checked rule by name, or says that every one already has its verdict. Scripted
tests `test_roles`, `test_format_fix`, `test_why`, `test_notebook_p3`: PASS
(`test_step_c` fails two lines that assume the six briefs on disk are the old
ones; four of them are now the operator's own).

**Since 2026-11-15 it tells the model to plan for the limit on simulations**
(the operator, after a session that used 12, 12, 11, 4 and 1 simulations and
wrote in its report that its optimum "was not finely swept": "we should make
the AI understand there is a limit on the number of simulations and account
for it"). The limit was already given (the brief's `limits`, and
`simulations_left` in every turn record); the prompt now also says, under the
budget: plan for it from the first turn, decide what you most need to learn,
do not spend simulations on what a result you already have answers, keep
enough for the comparison that decides your answer, and do not leave the
decisive test for later than you can afford, because when the simulations run
out there is one last turn for the report and no further experiment. A
general rule: it names nothing of this system. Sessions before and after it
differ in this; each session's `session.json` keeps the prompt it ran with.

**Since 2026-11-15 it says that a failed check is not yet a refutation** (the
operator: "If checks fail, does AI try again?", then "Do you understand that
hypothesis that is failed in check just proceed to verdict is not good?"). The
harness never repeats a test, and it has always let an open hypothesis be
tested again (an experiment's `tests` must be open hypotheses; a hypothesis is
open until its verdict). The model rarely used that. Of the 174 failed checks
in sessions s001 to s030, 130 were followed by a verdict with no further check
of that hypothesis (58 refuted, 72 inconclusive). In s030, H1 ("The scheduler
is work-conserving …") was judged refuted on a failed check while the verdict's
own next step named another cause to test; the session found that cause, and
the first claim of its final report says what H1 said. H1 stays "refuted" in
the record, because a verdict closes a hypothesis. The prompt, under verdicts,
now says: a failed check says that the prediction was not measured in that
test, which the test itself may explain (another setting limited the result,
a badly chosen threshold, simulations that differ in more than the one thing
tested); so the model is not to go from a failed check straight to refuted,
but to say in `because` why the check failed; if the test was a fair one, the
verdict is refuted; if the test may be the reason, it gives no verdict yet and
tests the hypothesis again with a design that removes that reason (the failed
check stays in the ledger and the later verdict cites both), or, if it cannot
test again, says inconclusive and what would settle it; and a check that held
supports the hypothesis only if the rival would have failed it. This is
guidance in the prompt: nothing in the harness enforces it, the answer format
is unchanged, and no real session has run with it yet. Two things it does not
settle, for the operator: whether the harness should refuse "refuted" when
`because` does not say why the test was fair; and the line "Accepts a result
against its expectation" of the researcher card, which counts a failed test
judged inconclusive as not accepted.

**Since 2026-11-15 a check's line, as the model reads it, carries the rival**
(`loop.shown`; from a reading of s031 by Claude chat that the operator passed
on: "when the test does fail, the AI is shown only FAILED, not that second
explanation"). The rival explanation of a decision rule stood only in the
experiment's line, some records before the check. The check's line now ends
"[this is what the rival explanation predicted: …]" when the result is what
the rival predicted, and "[the rival explanation predicted FAILED and does
not fit this result: …]" when it is not. In s031 the rival of H2, which
failed in turn 1, read "All TCP variants are capped by the same scheduler
share or buffer limit": the limit the session then spent its simulations
around without naming it. Only the text given to the model changes; the
records are as they were, and a check recorded without a rival reads as
before.

**Since 2026-11-15: why before which, and a meaningful difference told from a
marginal one** (**DECISION 2026-11-15**, the operator: "The AI should not just
optimize settings from simulations but ask why. that is the whole point of
this project. And especially it should be able to tell apart meaningful
difference and marginal tiny one. If any setting doesnt make meaningful
improvement it should ask why rather than improving a marginal amount and
present it as the best one"; then "Do what you are confident to be necessary
changes"). What led to it: in s031 (brief `trap`: a link of 10 ms, UDP offered
300 Mbps) every TCP type ends at the same 419 Mbps, which is the 1 MB buffer
over the 20 ms round trip, and the ratio and the queue change nothing. The
model saw that by turn 3 and wrote it in its report; it never asked why 419
when 700 Mbps of the link were free, spent 13 of its 20 simulations on
differences of 0.02 % between two TCP types and between seeds, and recommended
"TcpBic" and "seed 3" for them. Over all sessions s001 to s031, 112 of 459
checks rested on a comparison of two results less than 1 % apart: 37 of them
compared a simulation with itself (the fault of section 15 item 9, shown as
void), 75 (16 %) two different simulations. Three
things were changed, all general (nothing names this system):

1. **A tolerance always holds** (`loop.TOLERANCE`): the brief's
   `goal.tolerance`, or 1 % when the brief states none (`DEFAULT_TOLERANCE`).
   Every turn's message states it ("TOLERANCE: two results that differ by less
   than 1 % count as equal …").
2. **The harness marks a check that was decided by less than the tolerance**
   (`loop.decided_by_little`, `decision_rules.comparisons`). For every
   comparison of the rule whose two sides are results (both measured, or one
   measured and the other a number that is an earlier result of the session
   written out, which the model often does) and differ by less than the
   tolerance, the check's record says so (`tolerance`, `within_tolerance`),
   and the line the model reads ends "[NOTE: … the two sides differ by 0.0196
   %, less than the tolerance of 1 %. They count as equal: this comparison is
   decided by a difference that does not matter, so it is no evidence of a
   difference.]". The result the rule gives (held, failed) is kept. A number
   the rule states of its own (a limit of the brief, a margin) is not a
   result and is never marked. In s031 it marks H11, H12 and H16 and no other.
3. **The prompt**: its second paragraph says that the purpose is to understand
   why the system behaves as it does, and that a session which names a best
   setting and cannot say why, or what stops the result from being better, has
   not done the work. `observations` now asks, each turn, for what the results
   do not yet explain (a result that does not change when a setting changes,
   one that stays below what the settings would allow, results equal to the
   last digit, one against expectation), the most important of which the next
   hypothesis is about. Two paragraphs before the last line: "Ask why before
   you ask which" (a setting that does not matter is a finding, and the next
   question is what does limit the result; the detailed record of a
   simulation and what the brief says are there to reason from) and "Tell a
   meaningful difference from a marginal one" (no rule that a difference
   inside the tolerance can decide, no hypothesis built on one, no further
   simulations for one, no recommendation because of one; when nothing makes a
   meaningful difference, say they are equal, keep the simplest, and say what
   limits the result). The report's `explanation` is to say what limits the
   result at the recommendation. A seed, where the brief leaves one to the
   model, is said to be for repeating a simulation, not a setting to tune
   (measured: 53 settings run under two or more seeds differed by a median of
   0.0002 % in TCP goodput, at most 0.17 %; 113 of 989 simulations were spent
   on other seeds).

The page shows the same to a reader, for every session, old ones too
(`EV.closeCalls`, `EV.closeNote`, by the harness's rule): in a test's detail,
under the result, "Decided by less than the tolerance. 418.957 Mbps against
418.875 Mbps: a difference of 0.02 %. Two results closer than the tolerance
of 1 % count as equal, so this result shows no meaningful difference,
whichever way the rule came out"; on its notebook card "decided by 0.02 % ·
inside the tolerance of 1 %: no meaningful difference". Both carry the sign
of what needs a look, whose box now names four things. A void check is shown
as void, not as close. Check: `ev_usable.py close` (which tests and by how
much, worked out again with `decision_rules.py` from the records: s013, s014,
s016, s024, s030, s031).

Harness test: `harness_checks/test_tolerance.py` (the kinds of a comparison's
sides; s031's checks worked out again; a scripted session on a brief without
a tolerance and one on a brief that states 5 %; what each turn was told; the
prompt's lines). Not done, for the operator: a report field of its own for
"what limits the result" and for the settings that made no difference (the
prompt asks for both in `explanation`); the seed is still a knob in the two
base briefs; no real session has run with these instructions when this was
written.

It must not describe the scheduling policy, how the scheduler works, TCP
backoff, or any expected result. For that reason the prompt and the format
give no example of a question about this system: the example of the
operator's sheet ("Does the scheduler pass UDP's unused part of the link to
TCP?") names the very behaviour the model is to find out (section 1).

## 9. What the model can reach: `tools.py`

`open_session(id, brief)` makes one session's folder the only place the tools
can reach. The model can ask for:

| Tool | Returns |
|---|---|
| `describe_system()` | the brief, with the descriptions of the outputs and the tools |
| `metrics(run_id)` | a simulation's `metrics.json` |
| `series(run_id, every_n)` | `series.csv`, thinned to at most 100 rows |
| `grep_trace(run_id, pattern, limit)` | lines of `flowmon.xml` matching a regular expression, at most 50 |
| `list_runs()` | id, params and metrics of every simulation of this session |

No tool takes a path. A run id is accepted only if this session's
`runs/index.json` lists it, so no name can reach another session or `checks/`.
There is no tool that reads source code (**DECISION 2026-11-11**: `read_source`
was removed after s001, where the model read the policy's name in the scenario
file and never had to test for it).

Simulations are run only by the harness, for an accepted experiment:
`run_many` forces each setting into the brief's ranges (`clamp`; with
`design=<label>` it also refuses a design that does not state every knob,
8.5), starts the
built program with every option explicit (`options`: the fixed settings, the
knobs' defaults, then the chosen values; a setting the brief leaves out,
`tools.EXTRA`, is not passed) and `TWOHOSTS_SCHED` in its
environment, waits up to 600 s, and appends `{id, params, metrics}` to the
session's `runs/index.json`.

`manifest.json` holds what is the same for every brief: the outputs and the
tools with one-line meanings, how an experiment is run, how the budget counts.

## 10. The operator's side

### 10.1 `control.py` (port 8600)

Serves the project's files read-only and a few endpoints. Standard library
only.

| Endpoint | What it does |
|---|---|
| `GET /api/status` | what is running, the briefs, the sweeps, and `sessions`: one row per session (brief, counts, checks held and failed, how it ended, policy, running, the figures of `session_figures.py` (held and failed are counted without the void checks; `void` is [void checks, all checks]), and from `checks/` the score in short and the review) |
| `GET /api/sessions` | that list alone |
| `POST /api/session` | starts `loop.py` with the chosen flags: a new session, or with `session` a continued one. One session runs at a time (below) |
| `POST /api/stop` | `{session}`: stops a session started here; only for the account that started it, or the owner |
| `POST /api/run` | `{params, policy, brief}`: one operator simulation into `checks/op-<time>/`, listed in `checks/control.jsonl` |
| `POST /api/sweep`, `GET /api/sweep/<id>`, `POST /api/sweep/<id>/stop` | 10.2 |
| `POST /api/judge` | 10.4 |
| `POST /api/review` | 10.5 |
| `POST /api/export` | 10.6 |
| `POST /api/brief` | saves a new brief after `tools.check_brief`; an existing id is refused |

**Policy "random".** `POST /api/session` with `policy: "random"`: the server
chooses share or cap, lists the session in `checks/random.json`, and leaves its
policy out of `/api/status` until the session has a score. The page takes the
policy only from `/api/status`.

**Who may call it: the page is shared** (**DECISION 2026-11-17**, the operator: "I want everybody to be able to use
it as much as I am without too much works", and, asked which accounts: every account of this server; then "I want to
make the least safety measure. I want the viewer to show who is running the ongoing session if any, and not allowing
running new session during that to avoid conflicts"). The server still listens on 127.0.0.1 only, so it is reached
from this machine alone: by a browser here, or through an SSH tunnel of somebody who has an account here
(`ssh -N -L 48600:127.0.0.1:8600 <account>@<server>`, then `http://127.0.0.1:48600/viewer/`; the foot of every view
shows that line with the server's name). Until 2026-11-17 a POST was accepted from the owner's account alone. Now:

- **Every account may use the page as the owner does.** A POST is accepted from any account of the machine, as
  `application/json` and from the server's own page only. The account is read from the connection
  (`/proc/net/tcp`; a tunnel is opened by its user's own sshd process); a connection whose account cannot be found is
  refused.
- **One session at a time** (`MAX_LOOPS = 1`; six ran side by side before). While a session is running, wherever it
  was started, `POST /api/session` is refused with "session s032 is running, started by <account>: one session runs
  at a time. A new one can start when it has ended". A loop started from a terminal counts, as the owner's. The rule
  is the server's, for starts through the page: the owner can still start loops from a terminal.
- **A running session is stopped by the account that started it, or by the owner** (the account that runs the
  server); anybody else is refused.
- **Every POST that was carried out is noted** in `checks/people.jsonl`: time, account, endpoint, the id it
  concerned. The file holds account names, so it is in `.gitignore` and in no export.
- `GET /api/status` also gives `you` (the account that asks), `owner`, `running_now` (`[{id, by}]`),
  `one_at_a_time` and `share` (`{host, port}`); a session's row has `by` (who started it through the page; a running
  session nobody started there is the owner's) and `can_stop` (for the one who asks).
- `drafts.jsonl` and `calls.jsonl` are given to nobody as files over HTTP, the owner included (GET and HEAD, also
  with the name written in capitals or with `%2E`). `GET /api/agents?session=<id>` (since 2026-11-22) gives what
  the local model was given and wrote in that session (`calls.jsonl`; for an older session its drafts, its accepted
  answers, the supervisor's records and each draft's counts) to everyone who can read the page (first the owner
  only; opened the same day at the operator's word), view-only visitors from the network included. Everything else under the project folder is readable by every account, as before: the
  answer keys and sweeps under `checks/` too, so "operator-only" now means "not reachable by the model", not "hidden
  from the people who use the page".

**Looking from the network** (**DECISION 2026-11-17**, the operator: "Important : I want my professor to be able to
view it on webbrowser on computer or mobile. Consider him has technion VPN"). A phone cannot hold an SSH tunnel, so
the real server is started with `--network on` and then also answers on the machine's network address:
`http://<server>:8600/viewer/`, for any browser on the campus network or its VPN. A visitor who comes that way (any
address but 127.0.0.1) can only look: every POST is refused with "view only: ..."; only the page's own material is
given (`viewer/`, `sessions/` without `drafts.jsonl`, `briefs/`, `trace/`, `checks/` without `people.jsonl` and
`exports/`, `harness/manifest.json`, and the three GET endpoints), nothing else of the project folder and no listing
of a folder; `/api/status` says `view_only` and names nobody as `you`. What such a visitor can read is what the
public repository already holds, plus the sessions of the moment. The page then shows "view only" in the bar, its
Start button is off with the reason, and its foot says how to use the page fully; for a user of this machine the foot
gives the address to look from the network. At 700 px and under (a phone) a card that holds something wider than the
screen scrolls sideways inside itself, so the page as a whole does not. Without `--network on` (the scratch copies
of the checks) the server listens on 127.0.0.1 alone, as before. Tests: `test_shared_page.py` (a request through the
machine's own network address), `ev_usable.py network`. Whether the server's firewall lets port 8600 through from
the VPN has not been seen from outside.

**A personal link** (**DECISION 2026-11-17**; the operator, having opened the page from a phone: "I want my professor
to be able to run new session and do everything as me"). Opening POST to every visitor from the network was not
done: the address answers to anybody who can reach it, and each of them could then start and stop sessions under
the owner's account. Instead `python3 harness/invite.py NAME` writes a long random key into `checks/access.json`
(`{key: name}`, mode 600, in `.gitignore`, in no export, given to nobody over HTTP) and prints the page's address
with `?key=...`. A request from the network that shows the key (in its address the first time; the server then sets
the cookie `th_key`, HttpOnly, and redirects to the address without it) is that person: `/api/status` says `you`
"NAME (by link)", `view_only` false and `by_link` true; POSTs are carried out and noted under that name; such a
person may stop any session started here, as the owner may (the links are the owner's own choice of people). One
session at a time holds for them as for everybody. The file is read at each request, so `invite.py --remove NAME`
ends a link at once; `invite.py --list` names who has one. The key travels over plain HTTP: it is as safe as the
network between the browser and the server. Test: `test_shared_page.py` (its last part).

Sessions started through the page run under the owner's account and use its model server. Reviews and checklist
judgements are one set per session, without the reviewer's account: two people who review the same session write
into the same marks. Test: `harness_checks/test_shared_page.py` (the server run inside the test, with the account of
each request chosen by the test); the page: `ev_usable.py shared`. A lab member's own tunnel has not been tried by
anybody but the owner yet.

An operator simulation is made by the built program directly, never by
`tools.run`, so it never reaches a session's folder.

### 10.2 Sweeps

`POST /api/sweep {brief, policy, grid: {knob: [values]}}` runs every
combination of the grid, at most 64 at a time, one sweep at a time, at most
5,000 simulations. `checks/sweeps/<id>/table.csv` has one row per simulation
(its number, the nine options, a column for each setting of `tools.EXTRA` the
brief sets, the outputs, seconds, error); `status.json` the
progress. A simulation's own folder is removed once its row is written.

`{add_to: <sweep id>, grid}` adds the combinations the table does not have yet;
with `rerun: true` every earlier combination is run again too, so the whole
table comes from one build. The table as it was is kept beside the new one.

Sweeps made, both for `two-hosts-udp-demand` with build 4: `sw-20261111-190100`
(share) and `sw-20261111-190604` (cap). Each has 2,190 simulations: 73 values
of weightUdp (0.05 to 0.95; every 0.01 from 0.26 to 0.36; every 0.0002 from
0.300 to 0.310) x 5 queue lengths x 6 TCP variants, duration 10, seed 1.

### 10.3 Answer keys

`checks/keys/<brief>.json`: `{brief, about, per_scheduling_policy: {share|cap:
{sweep, notes}}, checklist}`. The notes are the operator's reading of the
sweep; the checklist is what a session is judged by. One key exists, for
`two-hosts-udp-demand`. Its checklist:

1. States the goal it optimises
2. Finds that the setting only matters under contention / when the UDP flow
   uses less than its part
3. Finds the effect of a short queue with a hard-backing-off TCP variant
4. Does not spend simulations on differences smaller than run-to-run variation

What the two sweeps show: under both policies UDP stops losing at about
weightUdp 0.303, and the best TCP goodput (about 671.5 Mbps) sits just below
that weight, where UDP gives up a little under 1% of its packets. Above it,
under share TCP stays at 668.6 Mbps at every weight; under cap it falls as the
weight rises (482.7 Mbps at 0.5).

### 10.4 Score: `score.py`

```
score.py SESSION [--target M --direction max|min --condition "..."] [--judge N=yes|no|unjudged]
```

Only a session that ended with its report can be scored. It reads the
session's `session.json` and `report.json`, its policy, the answer key and the
sweep's table, and writes `checks/scores/<session>.json`:

- the best row of the sweep for the goal: the target, among the rows where
  every condition holds;
- one operator simulation at exactly the recommended settings (always; a
  nearby grid row is not used, because it can sit on the other side of a
  threshold), in `checks/scores/<session>.recommendation/`;
- the gap on the target: best row minus the recommendation (negative when the
  recommendation is better than every row of the sweep), and whether the
  conditions hold at the recommendation;
- simulations used, and the size of the sweep;
- the checklist, each item `yes`, `no` or `unjudged`, with a note where the
  operator wrote one. The operator judges on the command line (`--judge
  2=yes`) or on the Operator tab, which sends `POST /api/judge {session, n,
  judgement, note}`: `control.py` writes the judgement and the note into the
  same file, only for a session that has a score. Judgements and notes are
  kept when the score is written again.

For a brief with an open goal the operator enters the goal the report states
(`--target`, `--direction`, `--condition`). There is no answer key or sweep for
`two-hosts-open` yet, so its sessions cannot be scored.

**The tolerance** (**DECISION 2026-11-13**). When the goal of the session's
brief gives a tolerance, or the operator enters one (`--tolerance PER_CENT`),
the score also says whether the recommendation is "at the best, within the
tolerance": the conditions hold at it and the gap is at most that many per
cent of the best row's value (a recommendation better than every row always
is). The score file gets `tolerance_per_cent`, `tolerance_from` ("the brief"
or "entered by the operator"), `within_the_tolerance` and `against_the_best`;
the Operator tab and the gap in the header strip show it. With a tolerance of
1%, s006 is at the best, within the tolerance.

### 10.5 Review

`POST /api/review {session, item, tick, note}` keeps the reviewer's tick and
note for one item of a session's page in `checks/reviews/<session>.json`. The
item `signoff` holds the sign-off: a name, and the date the server adds. No
review has been made yet.

### 10.6 Export: `export_session.py`

`POST /api/export {session, operator}` makes
`checks/exports/<session>-<time>[-operator]/` and a zip: the page and one file
with this session's files as text (its ledger without the draft records,
`session.json`, `report.json`, `runs/index.json`, every `series.csv`) and
`viewer/objects.json`, which holds no operator-only value. It opens
by double-clicking `index.html`, with no server. `drafts.jsonl` is never read.
Operator-only data (policy, score, review, answer key, sweep table) goes in
only with `operator: true`. A running session cannot be exported.

### 10.7 Packet-event recordings: `make_trace.py`

`make_trace.py NAME "TITLE" "NOTE" [--setting=value ...] [--policy=share|cap]`
runs the built program with `--events` into `trace/NAME/` and lists it in
`trace/index.json`. No tool reads `trace/`. Four recordings exist (`default`,
`queue4`, `share-udp200m`, `cap-udp200m`); the earlier six-page viewer shows
them. After a simulator change they must be made again.

### 10.8 Audit: `audit.py`

`audit.py <session> [...]` writes `checks/audit/<session>.json` from the
session's ledger and `session.json` alone (**DECISION 2026-11-13**,
`FORMAT_FIX.md`, Part 3). Existing sessions are not rewritten; the audit says
what their records are worth as tests:

- **checks**: for each check, the labels its decision rule names and the run
  behind each. `void`: the rule names two or more labels and at least two are
  the same simulation (the same run in that experiment), so it compared a
  simulation with itself. `one_simulation`: the stricter case, every label it
  names is one simulation.
- **verdicts**: the checks of the verdict's hypothesis in the last experiment
  that tested it before the verdict, and whether it rests only on void checks.
- **experiments**: the knobs listed as varied that have one value in all the
  experiment's simulations.
- **designs**: the knobs of the brief a design does not state, and whether
  its label names a weight (`w` and a digit) while it states no `weightUdp`.
- the counts of each.

The page marks the same void checks from the ledger itself (12.1), so an
exported session shows them without `checks/`; `session_figures.void_checks`
is the one definition both `audit.py` and `control.py`'s rows use.

### 10.9 The comparison arm "random": `random_search.py`

`python3 harness/random_search.py --brief ID --policy share|cap --n N --seed K`: no model. N settings are drawn at
random from the brief's own ranges (each knob on its own, evenly: a number between min and max, whole where the knob
is, rounded to its step where it has one; a rate between its two rates; one of the choices), each is simulated once by
the built program directly (as a sweep does, at most 64 at a time), and the best of them, the goal's target among the
rows where every condition holds, stands for the "recommendation". The draw depends only on `--seed`. Written to
`checks/random/<name>/`: `table.csv` and `result.json`. The brief's goal must be given. It answers what a session's
budget buys without any thinking, drawn from the brief's whole ranges and not from a sweep's grid (the sweeps of
`two-hosts-udp-demand` are dense near the optimum, so a draw from their rows is not a fair baseline: `HISTORY.md` B2).

## 11. Results so far

25 sessions, all with the same model. `s001` is from 2026-11-09, `s002` to
`s019` from 2026-11-11 (the table below), `s020` to `s025` from 2026-11-13
(after the repair of the answer format; their table is further down). "Gap" is the best row of the sweep minus the recommendation,
on TCP goodput; at every scored recommendation the brief's condition holds.

| Session | Brief | Policy | Draft | How it ended | Turns | Simulations | Gap (Mbps) |
|---|---|---|---|---|---|---|---|
| s001 | (before briefs) | share | on | old format, no report | 12 | 5 | |
| s002 | two-hosts-open | share | on | stopped (before reports existed) | | | |
| s003 | two-hosts-udp-demand | share | on | stopped from outside (answers cut off at 16,000 tokens) | | | |
| s004 | two-hosts-udp-demand | share | off | done by the model | 14 | 36 | 0.075 |
| s005 | two-hosts-udp-demand | share | on | done by the model | 5 | 40 | 0.075 |
| s006 | two-hosts-udp-demand | cap | on | done by the model | 5 | 40 | -0.047 |
| s007 | two-hosts-udp-demand | cap | off | 3 turns in a row without a usable answer | 7 | 20 | not scored: no report |
| s008 | two-hosts-udp-demand | share | on | simulation limit reached | 5 | 40 | 0.622 |
| s009 | two-hosts-udp-demand | share | on | simulation limit reached | 7 | 40 | 0.075 |
| s010 | two-hosts-udp-demand | share | on | simulation limit reached | 6 | 40 | 0.741 |
| s011 | two-hosts-udp-demand | cap | on | done by the model | 5 | 39 | 0.000 |
| s012 | two-hosts-udp-demand | cap | on | simulation limit reached | 8 | 40 | -0.096 |
| s013 | two-hosts-udp-demand | cap | on | simulation limit reached | 7 | 40 | -0.338 |
| s014 | two-hosts-open | share | on | done by the model | 14 | 26 | not scored |
| s015 | two-hosts-open | share | on | done by the model | 5 | 28 | not scored |
| s016 | two-hosts-open | share | on | simulation limit reached | 12 | 40 | not scored |
| s017 | two-hosts-open | cap | on | simulation limit reached | 19 | 40 | not scored |
| s018 | two-hosts-open | cap | on | done by the model | 6 | 36 | not scored |
| s019 | two-hosts-open | cap | on | done by the model | 11 | 30 | not scored |

Verdicts against checks, s001 to s019 (251 verdicts). The row is the checks
of the verdict's hypothesis in the last experiment that tested it before the
verdict; "no verdict" is a hypothesis that was checked and never judged. A
**void** check is one whose decision rule compared a simulation with itself
(10.8); it is left out of a row, and a verdict whose checks were all void
stands in the row "void".

| Brief | Checks | supported | inconclusive | refuted | no verdict |
|---|---|---|---|---|---|
| two-hosts-udp-demand | held | 63 | 0 | 0 | 7 |
| | failed | 0 | 0 | 39 | 9 |
| | void | 1 | 0 | 0 | 0 |
| two-hosts-open | held | 59 | 5 | 0 | 3 |
| | mixed | 0 | 7 | 0 | 0 |
| | failed | 0 | 3 | 4 | 0 |
| | void | 0 | 67 | 0 | 0 |
| (s001, before briefs) | no check | 3 | 0 | 0 | 0 |

**107 of the 337 checks of s002 to s019 are void**: 106 in `two-hosts-open`
(s014: 44 of 91, s017: 34 of 49, s019: 15 of 28, s016: 13 of 24) and 1 in
`two-hosts-udp-demand` (s004, C6); 96 of them name one simulation only. The
cause is in 8.3: in s014 (97 designs) and s017 (107), simulations whose label
names a weight, such as `u400_w80`, state no `weightUdp`, ran at the default
0.5, and were therefore one simulation under several labels.

This replaces what this section said before ("with an open goal it called 63
of 67 failed checks inconclusive"). Split by void and distinct checks, the 82
"inconclusive" verdicts of `two-hosts-open` are: 67 on checks that were all
void, 7 on mixed checks, 5 on held checks and 3 on failed ones. On distinct
checks the model called 4 of 7 failures a refutation; what it called
inconclusive was, almost always, a comparison of a simulation with itself,
and in s014 its own answer of turn 5 says so ("the simulations omitted the
weightUdp parameter"). The two briefs are still never added together.

**Whose conclusions are affected.** s014, s016, s017 and s019: 67 of their
122 verdicts rest only on void checks, and most of their budget went to
simulations that were returned, not run (s014: 91 of 118; s017: 112 of 153).
No claim of their final reports cites a void check, but what they could
conclude about a setting other than the weight at its default rests on few
distinct simulations. They are kept as records of the defect, not as results
(section 15, item 9). s004: one verdict ("supported", on C6) rests on a void
check; its recommendation and score are not affected. s015 and s018, and
every other session of `two-hosts-udp-demand`, have no void check.

**After the repair: s020 to s025** (2026-11-13; brief `two-hosts-open`, three
under each scheduling policy, default settings, the brief's own budget; the
first sessions in which every design states every knob and every hypothesis
has a question). `audit.py` on each:

| Session | Policy | How it ended | Turns | Simulations | The goal the model chose | Recommendation | Void checks | Designs stating every knob |
|---|---|---|---|---|---|---|---|---|
| s020 | share | done by the model | 6 | 39 | largest sum of UDP and TCP goodput | weightUdp 0.95 (udpRate 2Gbps, the rest at the defaults) | 0 of 11 | 44 of 44 |
| s021 | share | done by the model | 6 | 39 | largest of the smaller of the two goodputs | weightUdp 0.5 | 0 of 16 | 45 of 45 |
| s022 | share | done by the model | 3 | 23 | largest sum of UDP and TCP goodput | weightUdp 0.95 (duration 5, the rest at the defaults) | 0 of 8 | 24 of 24 |
| s023 | cap | done by the model | 5 | 22 | largest of the smaller of the two goodputs, UDP offered at 3 Gbps | weightUdp 0.496, udpRate 3Gbps | 0 of 10 | 24 of 24 |
| s024 | cap | done by the model | 5 | 31 | largest of the smaller of the two goodputs, UDP offered at 2 Gbps | weightUdp 0.497 | 0 of 9 | 36 of 36 |
| s025 | cap | done by the model | 5 | 38 | largest sum of UDP and TCP goodput, UDP offered at 3 Gbps | weightUdp 0.95, udpRate 3Gbps | 0 of 9 | 42 of 42 |

No check is void, no design lacks a knob, and none of the three new refusals
of 8.5 was needed. 23 of 221 simulations were returned from an earlier one
(in s014 to s019: 294 of 500). 57 of the 63 checks held and 6 failed; the 63
verdicts are 52 supported, 6 refuted and 5 inconclusive (all five in s022,
on checks that held). These sessions are not scored: `two-hosts-open` has no
answer key (section 15, item 2).

The best row is 671.585 Mbps under share and 671.533 Mbps under cap, so the
largest gap is 0.11% of the best. These figures say how close the
recommendation is. They do not say whether the reasoning was sound: every
checklist item of every score is still `unjudged`, and no report has been
reviewed by a person.

## 12. The viewer

### 12.1 The evidence page: `viewer/index.html`

One page for the whole cycle of work, at `http://127.0.0.1:8600/viewer/`. It
was built from the operator's `EVIDENCE_VIEW.md` and `PAGE_REDESIGN.md`, which
remain the description of what each part must show. Its goal: a person can
see, for any session, what was done step by step, who did each step, why the
model said it took it, and what the simulations showed, and can verify any
claim of the final report against the measurements.

Address: `?session=<id>` opens a session; `&tab=session|operator|compare`;
`&item=<record id>` opens the page with that item selected. Without a session
it is Home.

**The session page since `READABLE_PAGE.md`** (**DECISION 2026-11-14**, the
operator's sheet, parts 1 to 8; it replaces the design rules of the earlier
sheets, and where a paragraph further down describes the Overview band, the
card "The final report", the card "The system", "Highlights", the New session
panel or the switch "as a list / as a tree", this block decides: those parts
are gone or moved as said here, and the paragraphs remain as the record of
what each kept piece shows and how it follows the replay).

*What the page must achieve.* A person who has never seen it can say, in ten
minutes: what the network is, what the AI was asked and what it could see;
which questions it set itself, how it tested each, what it learned; what it
proposes, on what evidence, and where that stops being true; in what ways its
work was the work of a researcher; and, with operator columns on, whether it
was right.

*The lean page (since 2026-11-22, the operator: "a more lean viewer with only 3 parts").* A session's page is
three parts: 1 the setting, as before; 2 what it needed to find out: the board, the parts of a running session,
and "Turn by turn: who did what" folded at its end; 3 beside it, the detail pane: whatever is clicked (a
hypothesis's test, a record, the final report through the box of the answer; the session's summary when nothing
is). The pane stays in the window when the page scrolls; the board's column is at least as tall as the pane, so
what the pane shows never changes the page's height. A board wider than its column is drawn down to 85 % and then
scrolls sideways inside its card, with one line that says so. Not drawn, code kept (`EV.LEAN` in
`evidence_page.js`): the notebook, "What it proposes", "How it worked as a researcher", "Looking closer", "How to
read this page", "From one hypothesis to the next", the table "The same, test by test", the walk. `?page=full` in
the address draws the page described below. Check: `ev_lean.py`; the older page checks run on a scratch copy whose
page is full by default (`ev_all.sh`). While "Turn by turn" is open, the board stays in the window under the header
strip and only the turns move under it (the operator, 2026-11-22: the big picture stays in view while the details are
searched): `#s-map` holds the board alone (its key and the path button stand under it, `#s-map-under`), `EV.pinFit`
measures it after each drawing and when the fold opens or closes (turn by turn's column heads stand under it), and a
board taller than 45 % of the window is not held. A click on a held box opens it beside, and the page does not move.
What the agents exchanged (the operator, 2026-11-22, of three ways the first): in Turn by turn each record says what it answers ("← answers Q5 ·
Researcher") and what answered it ("→ Harness: T5, T6"), from the records' own parent ids, between different entities, the turn records left out;
pointing at a box outlines its partners and draws an arrow to each (asker to answer; nothing moves); an agent's first box of a turn links to that turn
in Agent transcripts (agents.html opens at #turn-N). `evidence_exch.js`.
The measurements the researcher made up (the operator, 2026-11-22): a small ruler mark astride the lower right corner of a box of the board (a
hypothesis, an exploration, the aim for the baseline) says how many belong to it (a reading of measure or probe that its guess, rethink or record
cites, else one of a run its test made; a measurement its experiment defines); a click opens them in the detail pane by turn (definition, run,
value; a probe's quantities). `evidence_meas.js`. "Agent transcripts" stands beside Brief | Full in the header strip.
The turns stand in a box of their own (`#tn-scroll`), as tall as the window leaves under the held board (the operator, 2026-11-22:
"user should be able to switch to whole page scrolling when they click outside of the detail section"): after a click inside it
(or opening the fold) the wheel scrolls the turns alone and the page stays; after a click anywhere outside it, or Esc, the wheel
scrolls the page (the box no longer scrolls), so the page is short and the rest of it is reached at once. A line above the box
says which, and the box keeps its place in the turns when the page is drawn again. A board wider than its column scrolls
sideways inside its card (`.ev .ev-lean #s-find .ev-map`; from the morning of 2026-11-22 until then an older rule let it spill
over the detail pane). The aim stands right under the heading of the setting, in the aim's own box (as in the brief's card),
before the network (the operator, 2026-11-22: "show the aim clearly on the setting section for users to see what this session
is about"); the block "The aim" is then not among the rest (the full page keeps its seven blocks).

*The agents' page, `viewer/agents.html`*, opened by the menu's button "Agent transcripts" (for the
session chosen in the menu, in a new tab) and readable by everyone who sees the page (2026-11-22, the operator: "a separate page for me to see tokens generated
by the local AI agents", to look into how the agents work and what they see). For one session, every call of the
local model in order, by turn: the agent (researcher, judge, supervisor), its tokens given and written, why it
stopped, how long it took; folded under each, the system message (said once, then "the same as call n") and the
user message it was given, what it wrote before its answer, and its answer. Buttons: one agent or every agent; open
or fold one part in every call. A session from before `calls.jsonl` shows what was kept of it (the drafts with the
ledger's counts, the accepted answers, the supervisor's records). While a session runs, a call is added at the end
when it returns and the page does not move. Its data comes only from `GET /api/agents` (10.1).

*Three levels of detail.* Level 1, at a glance, open at the top at full
width: the header strip, the setting, what it needed to find out (with its
detail, "Turn by turn: who did what", folded at its end; "The session at a
glance" and "Two agents" are not drawn since 2026-11-22). Level 2, read, below it in the left column: the notebook, what it
proposes, how it worked as a researcher. Level 3, inspect: the detail pane,
opened by a click (a test's flow chart, the exact decision rule and numbers, a
simulation's settings and charts, the review queue). Nothing of level 3 stands
at level 1 or 2 except as something to click. The switch **Brief / Full** in
the header strip opens every folded part; the browser remembers it
(`ev-full`).

*The sections, in order,* each with its heading and under it the reader's
question:

| # | Heading | Question | File |
|---|---|---|---|
| 0 | (header strip) | | brief, session, how it ended, simulations used, the recommendation in one line; Brief / Full; "Walk me through this session" |
| | (legend) | | the page's one legend of its three colour meanings (`EV.legendBar`) |
| 1 | The setting | What is this network, what was the AI asked, and what could it see? | `evidence_setting.js` |
| 2 | The session at a glance | What happened overall? | `evidence_glance.js`; not drawn since 2026-11-22 (the operator: the page showed too much), its code kept |
| 3 | What it needed to find out | Which questions did it set itself, and what did it learn? | `evidence_find.js`; folded at its end, "The same, test by test" and "Turn by turn: who did what" (`evidence_turns.js`): closed on a first visit, open in Full, the browser remembers each (`ev-find`, `ev-turns`) |
| 4 | The work, step by step | How did it test each? | `evidence_notebook.js` |
| 5 | What it proposes | What does it recommend, on what evidence, and where does that stop being true? | `evidence_page.js` |
| 6 | How it worked as a researcher | Did it work the way a researcher does? | `evidence_research.js` |
| 7 | Looking closer | How did the search go? | `evidence_closer.js` |
| 8 | How to read this page | What is a turn, a test, a check? | `evidence_page.js`, `evidence_top.js` |

*1 The setting* has seven blocks; the set-up page (section 7) has the same
seven as forms. The network (the picture; a click on a part shows its values,
and no part is chosen until then; for a brief with a network, since 2026-11-22, a schema of its ns-3 objects (the
operator: "a schema of more quality, to see what object types are involved"): each host drawn as the network
builder draws it in full, its Node with its applications, sockets, IPv4 and traffic control; on each end of a link
its device (PointToPointNetDevice), between the two its channel (PointToPointChannel); each flow in its colour from
its application to the other end; under it "Made of", each kind of ns-3 object with how many and its class (hover:
what it is); the flows and the links in words folded under that. A network wider than 1,700 px draws each host as
its sign and marks. A click on a part (a host, an application with its socket, a sink, a queue, a device, a link) opens
its card beside the schema (the operator: "I want users to see the detail of clicked object on the right side"): its name
and ns-3 class, where it is, each setting with its value, its ns-3 attribute and who decides it (the AI within a range,
with the values this session tried, or the operator), and what is measured there (with a simulation open, its values).
`EV.netCard`, `EV.netParts`; a second click on the same part closes the card. "Made of" is the schema's legend at the head of the column beside it (an open card covers it); a click on any blank
place of the network's part closes the card and "Made of" stands again. The link's words stand in a bordered label above its line. The schema's column is as wide as the
schema; the card takes the rest of the row, at least 340 px (the operator: "the box for detail could be horizontally larger"),
and its rows wrap rather than being cut. `EV.netSvg`, `EV.netKinds`, `EV.netWords` in `evidence_net.js` with `NETC.hostSvg` of
`brief_canvas.js`; check `ev_net.py`); who decides what (the settings by who
decides them, in the two colours); the aim, and who set it; what the AI is
told, is not told and can do (three lists built from the session's `given`
and the tools the harness offers, and, folded, the exact text the AI was
given: what `describe_system()` returns, word for word); the limits and how
many simulations were used; kept from the AI (the scheduling policy: only
with the operator columns on; with them off its name stands nowhere on the
Session tab, and the scheduler in the picture carries the mark "policy not
told to the AI"); how the AI runs (the model and the flags). Blocks 5 to 7 are
one line each in Brief.

*2 The session at a glance* is the card "What this session is made of" under
its new heading, with the tally of the checks. A turn's name opens its work
log and brings the notebook to that turn. Where the turns do not fit the
width, the table continues on further bands of the same rows: nothing scrolls
sideways.

*3 What it needed to find out:* first the board (`EV.viewMap` in
`evidence_views.js`; **DECISION 2026-11-14**, the operator: show on a board
which hypothesis led to which, with a line coloured by supported or refuted,
time on the x axis, the hypotheses of one time one under the other). One box
per hypothesis in the column of the turn it was stated in, tinted by how it
ended; a box opens its test. An arrow leads to each hypothesis that names a
result of the earlier one in what it follows from: in the colour of "held"
where that result is a verdict "supported" or a check that held, in the
colour of "failed" where it is "refuted" or a check that failed, dark for
both, dashed for "inconclusive" or a void check; the result's sign stands
just before the box. A dotted arrow is the weak link: the later hypothesis
names only the result table of the experiment that tested the earlier one.
Where the page is too narrow for boxes of 132 px (many turns), the boxes are
small and hold the hypothesis's id and the sign of how it ended. In a running
session the turn being written has one empty box. "Show the path to the
answer" marks the hypotheses the final report's claims rest on and what they
follow from. The board replaces the folded "Hypothesis map". Under it, folded
("The same, test by test"; open in Full; the browser remembers it,
`ev-find`), the table: one row per test in the order stated: the
question (the hypothesis's `question`; else its text, cut to two lines), the
outcome (the verdict; "void" where the check compared a simulation with
itself), what was measured (the check's numbers in words: "483 Mbps, not over
700 Mbps"), what it led to (a mark for each later hypothesis that follows,
going to that row). A row opens its notebook card and brings it into view.
Nine rows at most, then "n more". A failed check has no warning colour. The
replay greys later rows and counts only what is recorded.

*4 The work, step by step* is the notebook; the replay's buttons stand in its
heading; a refused answer or part is a line under its turn's heading. The key
moments that were the card "Highlights" are marks on its cards and headings
(`EV.moments`): first test that held, changed course here, cited by claim 1,
best result.

*5 What it proposes* reads as one argument: the aim and who set it; the
proposed adjustment (each recommended setting beside the value the session
started from, "ratio 0.5 → 0.497", and one line "everything else unchanged");
the expected result in short; because (the claims whose `role` is `supports`,
then `background`); but (the claims whose role is `limits`, then "holds when"
and "breaks when"); the explanation, folded. The role of a claim is required
by the answer format and checked by the harness (8.6); a report recorded
without roles shows its claims in one list. The counts of claims are worded
neutrally ("cite only checks that held", ..., "cite nothing") and none is in
the warning colour. A session without a final report says "No final report"
here, with how it ended.

A report that says what limits its result (8.6) has a fourth part, **"What limits the result"**, after the expected
result: the report's `limit` in the AI's words and, from its `no_difference`, "Made no meaningful difference, by its
own list: seed" (or that the list is empty). The full report in the pane has the same part. A report recorded before
has no such part and the numbering has no gap; in the replay the part is absent until the report is recorded; a
running session whose instructions ask for it has a seventh empty place. Check: `ev_usable.py limit` (the scripted
session `lim1`). The claims of the full report are plain boxes: their violet left edge, a leftover of the time when
violet meant "written by the AI" (the operator, 2026-11-17: "Is purple color applied here a remnant ...?"), is gone,
and `ev_usable.py plain` finds no violet on a session's page but the small icons.

**The shared page** (10.1, 2026-11-17). Home's title line says "s032 running now, started by <account>" and the
running row "running now · <account>"; the set-up page's heading says the same, its Start button is off while a
session runs and says why on the button and under it ("Session s032 is running now, started by … One session runs at
a time …"), and it comes on again by itself when the session has ended; the running session's banner has the Stop button alone for the one who started it (its box: "You started this
session"), "started by <account>" and the Stop button for the owner, "started by <account>" and no button for
anybody else (its box: "Only <account> or <owner> can stop it"), and for a session started with a command in a
terminal "started from a terminal by <account> · this page cannot stop it" (the operator, 2026-11-17, of the earlier
wording: "What does 'it is stopped there' mean?"; the box says that the page can stop only the sessions it started).
The banner's line of text never wraps: what does not fit is cut with an ellipsis and a note of what just arrived
stands whole in its box. Until 2026-11-17 a note could make the banner wrap to a second line, which moved the page by
20 px; the live view's check found it once the banner's end had become shorter (`HISTORY.md` C5). The foot of every view gives the one command that brings
the page to somebody else's computer. With a server that says nothing of accounts (an exported page) all of this is
absent. Check: `ev_usable.py shared`, which changes the server's answers on their way to the page (a pretended
running session, two pretended accounts) and starts nothing.

**The task on the page** (section 7, 2026-11-17). The set-up page's fourth block shows the task as the harness writes
it from the form, in a dashed box, not a field; while the form is still a saved brief that states a task of its own,
that text stands under it with a warning that a session started on the brief as it is gets it. The brief in the
detail pane says under "The task, as the AI was given it" whether it was "written by the harness from the aim and the
settings the AI may change" or "written by hand in the brief". Check: `ev_usable.py task`.

*6 How it worked as a researcher:* nine lines, each a count the page makes
from the records by a fixed rule shown on hover, with a word (present, partly,
absent; "not recorded" for a session recorded before the field existed; "not
applicable" with the reason) and links to its evidence: asks a question
before testing; commits to a prediction first (a decision rule recorded before
every simulation it names first ran; a simulation returned from an earlier one
first ran when that one did); makes predictions that could fail; accepts a
result against its expectation; changes course because of evidence; looks
beyond the obvious setting; does not repeat itself; states the limits of its
answer; supports each claim. With the operator columns on, two more: the
scheduling policy beside the first judged hypothesis that names the scheduler,
and the sentence about choosing at random. A reviewer's tick and note stand
beside each line (review item `rs:<line>`). The page states no overall
verdict. The same lines are columns of the Compare tab. A separate script,
`research_recount.py`, recounts them from the ledger.

*7 Looking closer:* the analysis views, each folded to one line that says
what it holds, opened by one click (the browser remembers which, `ev-closer`):
best so far, the simulations of each turn along one setting, the target where
one setting alone differs, verdicts against checks, the tests as a list with
margins, session flow, the tree (the hypothesis map is the board of section
3).

*A guided walk* (`evidence_walk.js`): "Walk me through this session" shows one
sentence per section 1 to 6 (five without a final report), built from the
records by a fixed rule, at the head of its section, with back, next and
leave; leaving it puts the page back as it was.

*A running session, shown as it is made* (`evidence_live.js`; **DECISION
2026-11-14**, the operator: show the evidence as it is generated, as a
skeleton of the steps whose places fill in, with the content of each place to
read and with where the work is). No new section: the sections above are the
skeleton. A place whose record is not there is drawn empty (a dashed square
in section 2; the word "empty" elsewhere) and fills when its record arrives:
a check or a verdict a test does not have yet, the simulations an experiment
waits for, the final report (its six parts in section 5), and, while a reply
is written, one empty row in section 3 and one empty card of six lines in
the notebook. A place that is never filled stays drawn empty after the end
("No verdict was given", "No final report was given"). Where the work is, is
read from the records alone: no record, the harness is preparing the session;
an experiment without its results, ns-3 is working on its
simulations; the newest record is a turn's first, the AI is writing its
reply; anything else, the harness is preparing the next turn. The banner,
which stays under the header strip, says it in one sentence with how long the
newest record has been the newest (the server's `Date` against the ledger's
`Last-Modified`), what arrived at the last reading, and Stop. **The page
never moves by itself** (**DECISION 2026-11-15**, the operator: "I don't want
you to kidnap users to the place on the page ... just show a little popup";
the switch "follow the work" is gone). When a new turn begins, and when an
experiment's simulations start, a small note appears under the banner at the
right for a quarter of a minute (`EV.liveNote`): "Turn 6 has started" with
"show it", "ns-3 is running the 5 simulations of X5" with "watch them"; the
button takes the reader there at the reader's own click, the cross closes
the note. And the reader's place is kept: when records arrive the page is
drawn again and parts above may have grown, so the part that stood at the top
of the window is put back where it stood (`EV.liveAnchor`; a part that stays
in the window, like the banner or the detail pane, is not used for this). The AI's reply arrives whole, so while it is written the mark stands
on every place that reply may fill, and the sentence says so; a draft is never
read (of a draft record only its type, to say that a reply was asked for
again). New records are marked for half a minute. Every two seconds the page
asks for the ledger's size (a HEAD request) and reads the session again only
when it has grown. While an experiment's simulations run, the sentence also
says how many of them the harness has collected so far: the runs its index
(`runs/index.json`) lists that no record holds yet (the harness reads its
simulations in the order it started them).

*The simulations as they run* (`evidence_tiles.js`; at the operator's word,
2026-11-15: "show how it's going"; check `ev_live.py tiles`, and `real` on a
session of the local model). While an experiment's simulations run, "What it
needed to find out" holds, under the strip of the stage, one tile per
simulation the simulator has to run. A tile shows the design's label and its
run, the settings in which the design differs from the brief's defaults, how
far the measured time has got, the goodput of the two flows over that time
(two lines in the flows' colours, from 0 to the link's rate, over the measured
seconds; the newest sample's values beside them; pointing at the picture reads
the sample under the pointer in words) and, once the simulation has ended,
the measures of its `metrics.json` (UDP goodput, TCP goodput, UDP loss), then
that the harness has collected it. Every two seconds the page reads each
running simulation's own `series.csv` again: the curve is that file and
nothing else, and it grows because the simulator writes each sample as it is
taken (build 7, 6.3). Which run is whose the page recounts by the harness's
own rule (8.5: in the order of the design, every simulation whose settings and
seed no earlier simulation of the session had, numbered on from the last run;
the designs that are not run again are named in a line). The recount is
checked: when a simulation has ended its own `params.json` says what it ran
with, and a tile whose file names other settings than the design expected is
named by its run and shows the file's settings; if more runs exist than the
recount expects, every tile is named by its run alone. On two recorded
sessions the recount equals the records at each of their 9 experiments (73
simulations). **The tiles stay when the experiment's records have arrived**
(**DECISION 2026-11-15**, the operator asked whether showing the state of the
running simulations had been judged inappropriate: it was shown, but for the
7 to 30 seconds an experiment's simulations take, against the minutes of the
reply that follows, and in another part of the page than the notebook, so it
was hardly ever seen). Until the next experiment starts the tiles show the
simulations of the newest experiment as they ended ("as ns-3 ran them"),
from the records (which run each simulation got) and the same files, each
with its whole curve and its measures. While simulations run, the notebook's
line "ns-3 is working on its simulations" says how many have ended and links
to the tiles, and the note under the banner (above) says that they started.
The tiles go when the session ends: from then on its simulations are in the
notebook and the tables. Nothing on a tile is written by a model.
**Running or ended, at a glance** (the operator): a badge at the right of a
tile's name (the accent colour with a moving dot while it runs, a grey
"ended" once it has), a strip that fills as the measured time passes, and the
tile itself (a heavy accent edge on a bright ground while it runs, quiet once
ended, a dashed edge while it waits); the heading says "running now" or "all
ended" and the count line how many run and wait. No line repeats that a
simulation ended. **What was set and what was measured stand apart** (the
operator): above the picture, behind the label "set", the settings in which
the simulation differs from the brief's defaults; under it, behind "measured"
("now" while it runs), each measure as a small name over its value.
**Why a simulation has its name** (the operator): pointing at a name (on a
tile, or beside a simulation in a rule) opens a box that reads the AI's label
against the experiment's designs (`EV.namePop`): for each part of the name
between "_", the settings on which every simulation carrying that part
agrees while another differs ("bbr": TCP type Bbr; "w05": ratio 0.05), how
many carry it, and that a part which sets nothing apart is the AI's own
word. The box says that this is the page's reading of the recorded designs,
not the AI's statement.

The simulator itself prints nothing
while it runs, and ns-3's logging is not in the optimized build; a
simulation's detail shows instead how the simulator was started: the
program's name (kept in `objects.json` as `program`, which `check_objects.py`
compares with `BIN` of `tools.py`) with the options that run recorded, and
that the scheduling policy does not reach the program through its options. In section 3 a strip shows the steps of a turn (the AI writes its reply, the
simulator runs its simulations, the harness checks each decision rule, the
next turn), the one being worked on with its moving icon and the time; before
the first hypothesis the section shows that strip alone. Section 6 says "not
yet" where there is nothing to count.
Under each result the notebook says how long before its simulations came
back the decision rule was stated, or that the rule names a simulation that
had already run. The key of section 2 says whose form it is: the rows are the
harness's form of a turn, told to the AI in its prompt; what fills them, how
many turns there are and when it stops are the AI's. `ev_live.py` checks it:
two recorded sessions played back record by record as if running, each stage
against a recount of those records, and one real session followed from the
set-up page.

*The words that need explaining* (`evidence_words.js`; **DECISION 2026-11-14**,
the operator: emphasise the important words and explain them on hover). A
setting, a measure or a part of the network has a dotted line under it
wherever it stands on a session's page (in the AI's own words, in the page's
lines, in a table), and its first occurrence in a card, a row or a claim is
set a little heavier. Pointing at it, or reaching it with the Tab key, opens
a small box beside it; the page does not move, and the text itself is never
changed. A word is found by a fixed list: a setting by its field name
(`weightUdp`) and by its plain name where that is more than one word; a
measure by its field name and its plain name ("UDP loss"); a part by the name
of a picture's object that is one of a kind (UDP queue, TCP queue, scheduler,
UDP source, TCP source). What the box says is taken from what is recorded: for
a setting the brief's own line about it, its range and where the session
started (or that the operator fixed it, and at what) and the values the
session's own simulations tried; for a measure the harness's line about it,
its unit, its value in the baseline and what the brief's goal says about it;
for a part its card from "The setting", where the scheduling policy stays
operator-only. The labels and terms the page already explained on hover open
the same box. At an earlier step of the replay a box shows nothing recorded
later. The picture and the words belong together: pointing at a part of the
picture sets off, everywhere on the page, the settings that part is set by
and the measures taken there (the link: link rate, link delay, link use), as
`objects.json` records them for that part; pointing at a marked word sets off
the parts of the picture where it is set or measured. `ev_words.py` checks
it.

*Readability, 2026-11-14 and 15* (**DECISIONS**, each at the operator's word;
checks `ev_design.py`, `ev_board.py`, `ev_glance.py`).
- *One kind of box.* Pointing at a hypothesis's box on the board (or at its
  name in the table) opens its card: the name and how it ended, the question,
  then six lines in a fixed order (why, follows from, expected,
  result, conclusion, led to). Pointing at an arrow or at its sign opens the
  arrow's card: the result the later hypothesis names, with what was measured,
  how it was judged and the AI's next step; a click opens the earlier test. An
  arrow that passes over a column runs in the gap between two rows of boxes. A
  brief's name has a box too: what it asks, built from its goal, the task in
  the operator's words, the counts of its settings; the same words stand
  beside the name on Home and in the lists of briefs.
- *Grouping.* What belongs together stands in one region with an edge and a
  ground of its own, with more space between two regions than inside one: the
  seven blocks of "The setting" and of the set-up page, and each turn of the
  notebook with its heading and all of its cards.
- *Nothing changes size on a click.* The settings of the part chosen in the
  picture stand in a card beside it that lies over what is below when it is
  taller than the picture. On the set-up page every part stands at once in a
  card under the picture, with its values as fields (section 7); pointing at a
  part sets off its card and its rows of block 2, and the other way round.
- *A test in full* (the detail pane): the headings of its notebook card
  (Hypothesis, Why, Plan, Expected, Result, Conclusion, So next), each said once
  and never cut; then its chart; folded, "The exact records" (the rule as
  written, the check's raw numbers, the times); last the same test as one
  picture. A simulation chosen inside an open test opens within it (an inset),
  so the test stays in view; elsewhere a click opens its item in the pane.
- *Section 2 in names and words.* "The session at a glance" has no shapes to
  decode: a hypothesis is its name on a chip, tinted by how it ended as its box
  on the board; a test is "H1 held" or "H1 failed"; the simulations of a turn
  are "X1 · 5 simulations", with "2 not run again" under it where designs had
  the settings and seed of earlier ones (**DECISION 2026-11-15**, the
  operator: a bare number after the experiment could not be read), and
  pointing at it opens the experiment's box (`EV.expPop`: the hypotheses it
  tests with how each check ended, or the question it explores, its
  simulations in words built from their settings, how many were not run
  again, how long they took); a verdict stands in the turn it was given; the final report is
  the word "written". There is no row of decision rules: a rule stands with its
  test. An empty place is the word "empty", "not checked", "not judged" or
  "n running".
- The brief's detail card names each setting by its plain label, with each
  knob's range in words and where the session starts; a setting's meaning is in
  the label's box and is not repeated.

- *Rule against outcome, as a bar.* Where a decision rule compares measures
  with numbers, the test's detail and its notebook card draw one horizontal
  bar per comparison (`EV.ruleBars`): the scale runs over the values involved,
  the region the rule allows is marked, and a mark stands where the simulation
  came out; beside it the same in words. A rule the page cannot place on a
  scale (not a comparison with a number) has no bar and stays in words.
  Pointing at the dot or at the threshold opens a small box at once
  (**DECISION 2026-11-15**, the operator, who twice asked for it "more
  concise and understandable"): three short lines. The dot: the value, large,
  with what it is ("865.6 Mbps  TCP goodput"); the simulation, by its
  settings ("at UDP rate 100 Mbps"); and, with the sign of held or failed,
  "rule: over 800 Mbps". The threshold: "800 Mbps  threshold"; "rule: TCP
  goodput over 800 Mbps"; "measured: 865.6 Mbps". A side of a comparison is
  never called "the left side": it is said by what it is (`EV.exprSays`):
  "UDP goodput + TCP goodput", "the smaller of UDP goodput and TCP goodput"
  (min), "the gap between … and …" (abs of a difference), "the smallest TCP
  goodput of 6 simulations"; where its measures come from several
  simulations, each is followed by the settings in which those simulations
  differ. Each mark has a wider place to point at.
  **One measure held between two numbers is one bar** (the operator: "both
  are about the same variable"): "… >= 200 Mbps and … <= 300 Mbps" is drawn
  as one band between two ticks, with one dot, and reads "must be within 200
  Mbps to 300 Mbps" (in a rule joined by "and" throughout). The bars also
  stand in "The decision rule, in full" of a test's detail (the operator);
  before the rule's check is recorded they show what the rule allows, without
  a dot, and a comparison with a measured right side is then in words.
- *A box's parts each have a look* (**DECISION 2026-11-15**, the operator:
  "different formats are not distinct enough to tell apart what is what",
  then "content and design both are not easy to read"). The box of a setting
  or a measure reads from top to bottom: its name with its kind on a chip
  ("measure", "setting"); one or two plain sentences that say what it is, in
  the page's words (`EV.MEASURE_SAYS`, `EV.SET_SAYS`: "How much UDP data
  reaches the receiver each second. Lost packets do not count."); the facts
  as small grey labels with their values on a tinted ground (in the baseline,
  measured at, the brief's target or condition; decided by, range, started
  from, tried here); then, smaller and behind a bar, the line the AI was
  given, with whose line it is; last, under a rule, its name in the records.
  A box too tall to stand under or over its word stands beside it.
- *One word for one thing* (**DECISION 2026-11-15**, the operator: "if
  question and hypothesis refer to the same thing, shouldn't we merge it into
  hypothesis?"). The page calls a hypothesis a hypothesis everywhere: the
  first line of a notebook card and of a test's detail is "Hypothesis"
  (until then "Question"), the table and the board speak of hypotheses, a
  running session's empty place is "the next hypothesis". What is shown
  there is still the hypothesis in its plain wording, the record's field
  `question`, whose name does not change. An exploration still explores a
  question: it has no hypothesis.
- *A brief's box* has the same looks: its name with "brief" on a chip; the
  facts (the aim; where the aim is open and the final report is recorded, the
  aim the AI chose, in its words, with where it was stated; how many settings
  the AI may change, how many are fixed, the limit); then, behind a bar, the
  task as the AI was given it.
- *Where the work is, on the board* (the operator): in a running session the
  whole column of the turn being worked on stands on a ground of the accent
  colour, with "turn 3 · now" in that colour; the notebook's group of that
  turn has the same edge and a light tint. *Every turn has its column*, also
  one that stated no hypothesis (the operator: "why no information beyond
  turn 4?"): a turn that only explored shows its exploration (the experiment
  and what it wanted to find out, with a dashed edge; its box is the
  experiment's), and a running session's last turn says that only the final
  report is accepted. *A result before its verdict* (the operator: "why are
  turn 1's results not shown by colours?"): the harness checks a rule as soon
  as its simulations are back, the AI judges only in its next reply; until
  then the hypothesis's box says "check held" or "check failed" with its sign
  and has an edge in that colour, the fill being kept for the verdict.
- *Cards on the glance* (the operator): pointing at a hypothesis's chip
  opens the hypothesis's card; at a test's chip ("H1 failed"), a test card
  (`EV.testPop`: the check's outcome on a badge, expected against found with
  one line and one sign per comparison, the simulations in words, the rival,
  the verdict); at a verdict's chip ("H1 refuted"), a verdict card
  (`EV.verdictPop`: the judgement on a badge, the AI's reason in its words,
  the check it rests on, marked where the two disagree, and what it decided
  to do next).
- *A notebook card is three parts, each in a border of its own* (the
  operator: "too much content in one border"): the hypothesis and why; the
  test, on a tinted ground (the plan; Expected as one line per comparison,
  `EV.ruleList`, where both sides are the same measure the second reads "the
  same at ratio 0.2"; Result as the check's word on a badge and one bar per
  comparison whose caption is the two numbers alone, in the order of the
  lines above); the conclusion and what came next. The sentence with all the
  numbers is kept only where no bar can be drawn. A measured number that is
  one measure of one simulation still opens that simulation.
- *A test's detail says each thing once* (the operator: "better format and,
  when necessary, reducing content"): its head carries the check's outcome
  and the verdict on badges; the hypothesis stands by its plain wording, its
  full statement, prediction and what it follows from one click away
  (folded); in Plan the settings that are the same in all simulations are
  folded behind "only ratio differs between them"; Result is the check's
  word on a badge and the bars, without the sentence that repeats them.
- *Who decides what, on a session's page*: a setting the AI may change has
  its lowest and highest value and the value the session starts at in three
  columns under those names (the operator: "this from ~ to ~ structure is
  difficult to understand"); a setting chosen from a list has the list in
  the place of the first two.
- *How a session ended, said plainly*: for "simulation limit reached" the
  banner adds that it used all the simulations the brief allows and that the
  harness then gave it one last turn for its final report; the sentence
  about places never filled stands only where one is empty.
- *The diagnosis* (**DECISION 2026-11-15**, the operator asked for an
  objective view of renaming "claim" to "diagnosis"; the word fits one of the
  three roles, so only that one carries it). A claim keeps its name: a
  statement the final report rests on, with the records it cites, the
  model's own and not yet judged by a person (the word has that box wherever
  it is marked). The claims whose role is "background" (how the system
  behaves) are shown as "Its diagnosis": a part of its own in "What it
  proposes", before "Because" (now the reasons alone) and "But", and a line
  "Diagnosis" on the answer's card. The word is the page's: the record's role
  stays `background`, and the model is still told "background".
- *The answer's box* on the board has a ground and an edge in the AI's own
  toned colour (the operator: "an appropriate colour"): it is what the AI
  concluded; green and red stay the outcome of a test. An exploration that
  the report's claims cite has its quiet line to the answer like a cited
  hypothesis, and its box says what an exploration is, what its simulations
  measured, and which claim cites it. A claim that cites no check but an
  experiment's results says so ("no check cited · it cites the measured
  results of X5"), so that "no check" is not read as "no evidence".
- *The legend's items* each stand in a border of their own inside the border
  of their group (the operator), so that "AI", "harness", "ns-3", "operator"
  read as four things.
- *A hypothesis's card* (the operator: "more design for readability") has the
  name, how it ended on a tinted badge, and the turn at the right; the
  question; why it was asked and what it follows from; then the test on a
  tinted ground: Expected as one short line per comparison of the rule (each
  side in words, the first three), Result as the check's word and one line
  per comparison with its own sign ("482 Mbps over 433.8 Mbps", "190.1 Mbps
  not over 433.8 Mbps"); then the verdict on its badge with its first
  sentence, and the hypotheses it led to as chips.
- *A part's card* (the operator: "the name of the item and its value should
  be distinct"): the part's name with its ns-3 class on a chip; each row's
  name small and grey on a shaded ground, its value dark and heavy beside it,
  a note about the value (who decides it, its range) small after it; what is
  measured there as a note under the rows. The card keeps one height.
- *The TCP types in plain words* (the operator: "simple and easy to read
  explanation on chosen congestion control algorithms where appropriate").
  Each type has one line of at most 22 words (`EV.TCP_SAYS`): what it reacts
  to (loss, delay, or what it measures of the path) and what it does. The
  lines stand under the type chosen on the set-up page, in the box of the
  setting "TCP type" (one line for each type the brief offers or fixes), and
  the type named in the TCP socket's card opens that box. They are the page's
  words for the reader; the AI's brief names the types only.
- *The board opens with the aim and closes with the answer.* Its first box is
  the aim (the brief's goal with its conditions). Where the brief leaves the
  aim open, the box says the aim the AI chose (**DECISION 2026-11-15**, the
  operator): the goal of its final report, in its own words, cut by the
  browser at a whole line, with "stated in its final report"; the whole text
  is on the box's card. The AI states its aim nowhere before that report, so
  until the report is recorded (a running session, an earlier step of the
  replay) the box says only that the aim is open. Its last box is the answer: what
  the final report proposes and, after "because", its first reason in the
  AI's words (the first claim whose role is "supports"; in a report without
  roles its first claim). Lines run from the hypotheses the report's claims
  cite to the answer. Pointing at the answer opens its card: Proposes,
  Expects, then the report's claims word for word, sorted by the role the AI
  gave them ("Because": supports, then background; "But": limits, with
  "breaks when"); a report recorded without roles lists them as "Its claims"
  and the page assigns none. On a board with many turns the last box says
  only "answer"; the card is the same. Without a final report the box says
  so and has no card.
- *The set-up page shows the whole configuration at once.* Under the picture
  of block 1 stands every part with all its settings (`#be-conf`), leaving out
  what no experiment turns on (ports, addresses, counters); pointing at a part
  sets off its settings there. The scheduling policy is shown there as chosen
  in block 6. The two settings of build 6 (6.1) stand in block 2 and in the
  list of all settings with three states, as each queue's own length does:
  not set (the line says what the program then does: ns-3's first window of
  10 segments, buffers of 1 MB each), fixed by the operator, or left to the
  AI within a range. The picture's TCP socket shows them (first window, send
  and receive buffer), at the program's own values when the brief leaves them
  out. The setting of build 7, the device's transmit queue, is there in the
  same way (not set: 10 packets); both devices' cards and the device's box in
  the picture show its length.
- *Conditions are chosen, not typed.* A condition of a given goal is three
  lists (the measure, by its plain name; the comparison; the value with the
  measure's unit), with as many conditions as wanted; the brief stores the
  same text as before.
- *Colour, sparingly.* Who produced an item is its icon in a toned-down
  colour of its own (`--bt-*`); one accent (`--live`, a quiet teal) marks what
  is happening now in a running session. A name and its value differ in
  weight. A buffer's size is written as a person says it (64 kB, 1 MB).

*Clicks that move the page* are stated in "How to read this page": a turn's
name in section 2, a row of section 3, a box of the structure map, a line of
section 6 that names a section, and the walk. No other click does.

*Design rules, for the session page and the set-up page.* Labels are plain
words ("ratio", "UDP rate", "queue length", "TCP type"); the field name is on
hover. A text the page did not write (the model's, the harness's, the
operator's recorded words) is marked `data-own`. A measured number at levels 1
and 2 has at most four significant digits and its unit (rates in Mbps or
Gbps, fractions in per cent, counts whole; `EV.v4`); a setting's value is
shown as recorded (`data-exact`); the exact value is on hover and at level 3.
Who produced an item is said by a small icon in the neutral colour, not by a
colour (**DECISION 2026-11-14**, the operator: a colour has no meaning of its
own and has to be memorised): a spark for the AI, a gear for the harness, two
computers and their link for the simulator, a person for the operator; each
is named once in the legend under the header strip. In the picture of "The
setting" a value the AI may change has ✦ before it and is set heavier; every
other value is fixed by the operator. Colour has two meanings, named in the
same legend: the outcome of a test (held, failed, and the warning mark, kept
for a refused answer, a verdict against its check and a number that differs
from its measurement), and the flow (UDP, TCP). Selection is drawn in the neutral colour. The text is 14 px,
small text 12 px or more, a paragraph at most about 80 characters wide.
Nothing scrolls sideways from 900 to 1,800 px. `ev_readable.py` (parts 1 to 8)
checks all of this.

**The top bar is the same in every view** (**DECISION 2026-11-12**, after the
operator found that it changed when a session was chosen and repeated what
Home offered). It has two groups, always with all of their items, each at its
own place:

- **All sessions**: Home, Compare sessions, New session (in the bar of every
  view since 2026-11-15, at the operator's word: a session can be set up from
  wherever one is; Home no longer has a button of its own for it).
- **One session**: the list of sessions, then that session's two pages,
  Session and Operator. The two wait, greyed, until a session is chosen.

On the right is the switch "show operator columns". A chosen session stays
chosen on Home and on Compare. Every destination has one place: nothing the
bar offers is repeated as a button in a page. The earlier pages are one quiet
line at the foot of every view.

| Place | What is there |
|---|---|
| Home | A title line with the one action that belongs there, New session; the results so far as a table, one row per brief (sessions, with a final report, meet the brief's conditions, largest gap to the best, not scored; a cell with nothing to count says "not scored"); the table of every session, sortable and filterable, a running one first, where a row opens its session and shows, on one line, its checks in order followed by the counts of held and failed, how many of its simulations were returned from an earlier one ("returned"), and how many no decision rule names ("not named by a rule") |
| New session | The set-up page (`?tab=new`): the seven blocks of "The setting" as forms, the strip of the session to be, Start (section 7). While a session runs: the banner of the live view (above): where the work is, what just arrived, "follow the work" and Stop; the page reads new records by itself |
| A session | Header strip (always visible, labelled fields on one line); the Overview, first and at full width, one band that holds only the answer; "The system"; "What this session is made of"; then, in the left column beside the detail pane, "The final report" (the model's own words: its claims as rows of full sentences, its explanation); the notebook, one card per test, and under it, closed by default, the same tests as a list or as a tree; highlights; best so far; the work; "How to read this page" |
| The work | Session flow (three lanes: model, harness, simulator) or Hypothesis map (arrows from `follows_from`). The tree (turn, experiment, test, simulation; each row names its kind in words: "experiment X1", "test of H1", "simulation S2") is behind the notebook's switch. One selection is shared by the notebook, the tree, the flow and the map. Replay greys everything after the chosen step in all of them |
| Detail pane | On the right, beside all of the above: the work-log card of a turn, the flow chart of one test, the result panel of a simulation, the chart of an experiment. A second tab holds the review queue and the sign-off |
| Operator tab | From `checks/` only: the policy, the sweep as a heat map with the session's simulations on it, the score with the knobs that differ from the sweep's best row marked, the checklist with the operator's judgement and note for each item; "Run one simulation" and "Run a sweep" |
| Compare tab | Sessions of one brief with a tick each; two or more ticked are shown side by side: their best-so-far lines, a table, the first test that held; with operator columns on, the sweep as a parallel-coordinates chart with each recommendation as a bold line |
| Share | "Copy link" on every item; export; print (overview, the final report, highlights, best so far, tests list; or the evidence sheet of one claim) |

**The top of a session's page** (`evidence_page.js`; **DECISIONS 2026-11-12**:
the overview first, and the comparison with the brief's defaults; **DECISION
2026-11-13**, the operator's `OVERVIEW_REDESIGN.md`: the Overview is one band,
and the model's own words are a card beside the detail pane).

- **The header strip** stays in view: labelled fields on one line, each a
  small label above its value: Brief, Session, How it ended, Simulations (used
  of allowed), Checks (held and failed, as marks with their counts), Model,
  Recommends; with the operator columns on, also the scheduling policy and the
  gap to the best.
- **The Overview comes first, at full width, and is one band** that holds
  only the answer, so that a reader meets the conclusion first and "The
  system" and the top of "What this session is made of" are still on the
  first screen (measured on s012 in a 1500 by 1000 px window: 291 px tall;
  before, 955). The introduction with its "dismiss" button, then four columns
  side by side (two by two in a window under 900 px):
  1. the goal, cut to four lines when longer (an open-goal session states a
     long one);
  2. the recommended settings, as described below;
  3. the expected result in short (`ov-exp-top`): the row of the goal's
     target measure and the rows of the measures the brief's conditions name,
     each with its condition ("the brief allows udp_loss_frac <= 0.01");
     where the brief gives no goal, the first three rows the report lists;
     then "n more in the final report" when rows are left out;
  4. its claims, in numbers only (`ov-claims`), one count per line (claims;
     cite held checks only; held and failed; failed only; no check; no
     evidence), and under them, as plain text, where the claims are.
  Then the share bar.
- **"The final report"** (`s-report`) is the first card of the left column,
  before the highlights, so that it stands beside the detail pane: a click on
  a claim opens the claim's test in the pane, in view, and the page does not
  move. It holds the model's own words and has the model's colour on its left
  edge: its claims as rows of full sentences with the checks each cites, the
  counts line and "print evidence sheet"; the explanation (six lines, then
  "more" and "less"); the expected result as the full table (`ov-exp`), an
  output's name on the left and its value on the right, without the outputs
  that only repeat a setting (`link_rate_bps`, `weight_udp`; the full final
  report in the detail pane shows them); when it holds; when it breaks; and
  the line that opens the full final report, the brief and the session's
  summary on the right.
- A selected claim keeps its dark ground while the pointer is on it, so its
  text can be read right after the click (contrast 19.17; before, 1.07).
- **The recommendation against the brief's defaults.** Both are recorded; the
  comparison is the page's. The knobs that differ are set large; the others
  follow in one line, "at the brief's default: …"; a knob of the brief that the
  report does not name is listed as "not named in the report". The strip's
  "Recommends" names only the knobs that differ. The recommendation is stated
  in these two places and nowhere else on the first screen.
- A session without a final report says "No final report" and how it ended,
  and has no card "The final report"; the line that opens the brief and the
  session's summary then stays in the Overview.
- In the replay the report is absent before its step, not greyed: the Overview
  says "No final report by this step" and shows no goal, setting, expected
  value or count of claims, the card "The final report" is not there, the
  strip says "no recommendation yet" and counts only the records by that step.
- Print: the Overview and "The final report" are both printed, with the goal
  and the explanation in full.
- **The session's summary** in the detail pane keeps the flags, the start, the
  duration, the turns, the model calls, the checks in order and the verdicts
  against checks. It does not repeat the strip (model, simulations used, how
  it ended). In the replay it shows only what is recorded by the step; the
  figures written at the session's end are absent.

**The detail pane fits its width.** Nothing in it is wider than the pane, and
nothing in it scrolls sideways.

- The flow chart of one test (`evidence_flow.js`) is drawn to the width it
  has, after the page is in place: hypothesis, decision rule, the simulations
  the rule names, "did the rule hold?", verdict, next, and the hypotheses that
  followed. In a pane of 700 px or more the first five share one row and the
  last two stand on a second; in a pane wide enough all seven stand in one
  row; in a narrower one the chart continues over as many rows as it needs,
  with an arrow from the end of a row to the start of the next. No box is cut
  off.
- The hypothesis box shows the id and the state; the hypothesis's text stands
  above the chart. The decision-rule box shows two lines of the rule; the rule
  in full stays below. A longer text in a box ends after its lines with "…".
- The table "the simulations this rule names" has one row per simulation and
  one column per setting that differs between them (in bold) and per measure
  the rule judges, so it grows downward, not sideways. It stands under the
  chart of the judged measure, at the pane's width.

**The sweep on the Operator tab** (`evidence_heat.js`): a heat map over two
chosen knobs; each cell holds the best value of the target among the sweep's
rows that meet the conditions.

- **One colour scale at a time**, chosen by a switch above the map: over all
  cells, or "within 1% of the best", where the scale runs from 99% of the best
  value to the best and every cell below that is drawn in the palest step; the
  key says so and gives their number. The darkest step is the best.
- **Across**, the values stand in the order of size. Where the step between
  neighbours changes there is a small gap and the value is printed; under the
  axis each stretch is bracketed, and a sentence names every stretch with its
  step, worked out from the values ("0.05 to 0.25 by 0.05 · to 0.3 by 0.01 ·
  to 0.31 by 0.0002 · …").
- **Marks**: the session's simulations are numbered circles, in their order.
  Circles that would overlap are one dark mark with their count; a click on it
  lists them under the map, and each line opens that simulation in the
  session. The label of the best cell stands above the map, joined to its cell
  by a line, so it covers no number.
- **The score**: in the two tables (the sweep's best row; the recommendation,
  simulated) a knob whose values differ is in bold with "≠".
- **The checklist**: each item has yes, no or unjudged and a note; a change is
  saved at once (10.4) and the row is brought up to date in place.

**"The system"** (`evidence_system.js`) is the card under the overview: the
two computers of the brief, each an outline that
holds its ns-3 objects in the order a packet passes them (applications,
internet stack, traffic control, net device), and the link between them.

- The objects and what the scenario fixes about them come from
  `viewer/objects.json` (hand-kept; `harness/check_objects.py` compares it with
  the scenario source, 6.4). The values come from the session: its brief's
  fixed settings and each knob's default, or the settings of the simulation
  the reader opened last; "show the brief's defaults" brings the defaults back.
  Each queue shows its own length; where the brief does not give it one, the
  common queue length, in the colour and with the label of that setting
  (`EV.SYS_OWN`, `EV.sysOwn`).
- **Two colours, one legend**: a setting the brief opens to the model is
  written in the model's colour, a setting the brief fixes in the operator's;
  the legend under the picture names both. The same picture (`EV.sysSvg`) is
  the form of the brief editor (section 7).
- A click on an object shows it beside the picture, inside the card: its
  settings, each with its value and its label, "the model may change it" (with
  its range, its step where it has one, and the values this session tried) or
  "fixed by the operator"; and what
  is measured there, with the opened simulation's values. The object chosen is
  not the session's selection: the item open in the detail pane stays open, and
  the page does not move.
- The scheduling policy is shown only with the operator columns on.
- The card grows to hold the chosen object's settings: nothing scrolls inside
  it.
- The card folds, and the browser remembers it; folded, its heading still says
  which settings it shows. It is not printed. During the replay it shows
  nothing recorded after the chosen step.

**"What this session is made of"** (`evidence_glance.js`) is the card after
it: the whole session as one picture.

- A column per turn (and "start" for the harness's baseline); a row per kind
  of item: hypotheses, decision rules, simulations (under the name of their
  experiment), checks, verdicts, the final report. One mark per item, and each
  row's title gives the number of items.
- Down a column stand a hypothesis, its decision rule, the simulations of the
  turn's experiment, the check and the verdict: together one test.
- The marks are drawn shapes, not characters of a font, so that they have one
  weight and one size everywhere: one small shape per kind (hypothesis,
  decision rule, simulation, held, failed, supported, refuted, inconclusive,
  dropped, a simulation returned from an earlier one, the final report), in the
  colour of its state. A mark's kind is also in its `data-m`, for the page
  checks.
- A hypothesis that stands a second time (tested in a later turn, or put to
  another decision rule) and a verdict that stands under a second decision
  rule are drawn small and faint, not hollow, and counted once.
- The refusals of a turn (refused answers or parts) are a count beside the
  turn's name.
- A mark opens its item in the detail pane, and the page does not move.
  Pointing at a mark marks what belongs with it, and a sentence under the
  table says what it is.
- The marks shrink and wrap so that every turn fits the width of the page; a
  session with too many turns for that scrolls sideways inside the card, and
  the card says so.
- During the replay an item recorded after the chosen step is an empty dot,
  with no text, state or title; the key and the sentence under the table name
  only what is recorded by then.
- The card folds like "The system": a "fold" button in its heading. Unlike
  "The system" the browser does not remember it: the card is unfolded whenever
  the page is loaded, and a fold holds only while that page stays open (the
  operator's word, 2026-11-18). Folded, its line carries its content: the counts from
  the records by the replay's step ("5 turns · 12 hypotheses · 12 checks, 10
  held and 2 failed as marks · 44 simulations"). It is not printed.

**The notebook is the main view of a session's work** (`evidence_notebook.js`;
**DECISION 2026-11-13**, the operator's `NOTEBOOK_VIEW.md`, Part 1). It is the
first thing in the left column under "The final report". One card per test,
under a light heading per turn ("Turn 2 · 28 simulations left", with what the
turn did); an exploration is a heading with its question and its simulations,
without a card; the harness's baseline is the heading "Start". Every card has
the same six lines, always in this order, each a recorded text or a measured
number, with the small icon of who produced it:

| Line | Taken from | Produced by |
|---|---|---|
| Hypothesis | the hypothesis's plain wording (its field `question`); a session that recorded none: the hypothesis text | model |
| Why | the hypothesis's `why`: why answering it helps reach the goal. Only where it is recorded; the line is absent otherwise | model |
| Plan | what differs between the simulations the decision rule names, in words built from their settings ("2 simulations: UDP share of the link 0.2, 0.8 at Measured time 5"), then what they share that is not the brief's default | model's design |
| Expected | the decision rule for reading, and its rival in one line | model |
| Result | the same rule with the measured numbers, and held or failed; a number opens its simulation | simulator and harness |
| Conclusion | the verdict and the first sentence of its "because"; "more" shows the rest | model |
| So next | the verdict's "next", and a link to each hypothesis that follows from this test | model |

- The left edge says the outcome: expected and found (held, the colour of the
  held sign), expected and not found (failed, the colour of the failed sign). A
  failed check is a result, not a warning. A void check reads "void: compared
  a simulation with itself" in Result and has a neutral edge.
- "changed course here": the check failed and a later hypothesis follows from
  the test (it names its check, its verdict or its simulations, or the table
  of its experiment).
- A test whose verdict has not come yet shows its last two lines as "not
  yet"; in a session that ended without one, "no verdict".
- A click on a card opens the test in the detail pane, as a row of the tests
  list does. In the replay a card can be read from the step of its experiment,
  its Result from the step of its check, its last two lines from the step of
  its verdict.
- **A turn folds at a click on its heading** (**DECISION 2026-11-15**, the
  operator). The heading then stands alone and names the hypotheses the turn
  tested with how each stands; a second click opens it. Nothing else is drawn
  again, so nothing above moves; "fold every turn" and "open every turn"
  stand above the first turn. What a click on the heading did before (the
  turn's own record in the pane) is the link "the turn's record" at the
  heading's right end. Folding is kept while the page is open and is not
  printed (a printed notebook is open).
- **Under it, one switch, closed by default**: the same tests "as a list" (the
  tests list) or "as a tree" (the tree); one of the two at a time; the choice
  is kept over a reload. The notebook is printed; the switch is not.

**Numbers written for reading** (`evidence_read.js`). Wherever a decision rule
or a check is shown for reading (the notebook, the boxes of a test's flow
chart, the work-log card, an evidence item, the highlights), the outputs stand
by their plain names and the numbers in the units of the page:
`tcp_goodput_bps@low_w50 > 800000000` as "TCP goodput at UDP rate 100 Mbps
(low_w50) > 800 Mbps", its check as "483 Mbps > 800 Mbps: failed". **A
simulation is said by its settings** (**DECISION 2026-11-15**, the operator:
"what are these w025b things? could users understand them?"): a rule names a
simulation by the label the AI gave it, which says little, so the page puts
before it what that simulation is (`EV.simSays`): the settings in which the
simulations the test's rule names differ from each other ("ratio 0.25");
for a single simulation, the settings that are not the brief's defaults.
They come from the experiment's own designs, which are recorded with the
rule. The AI's label stays beside it, in grey and marked as the AI's, so that
the exact text and the tables can still be matched. Two comparisons that hold
one measure between two numbers read as one phrase: "UDP goodput at ratio
0.25 within 200 Mbps to 300 Mbps", and with the numbers "245 Mbps within 200
Mbps to 300 Mbps" (strict comparisons: "between … and …"). A measured number is the value of
that output in the simulation the rule names (the harness's check holds the
same value) and is shown with as many digits as it takes to tell the two
sides of its comparison apart; a number written in the rule keeps every digit.
The exact text is on hover, and the test's panel keeps the exact rule and the
exact check. The grammar read is the harness's (8.4); a text that cannot be
read is shown as it is.

**Best so far, against choosing at random** (`evidence_random.js`; operator
columns only, and only for a brief with a given goal whose session is scored;
**DECISION 2026-11-13**, `NOTEBOOK_VIEW.md`, Part 2). Behind the session's line
the best-so-far chart draws a grey band and a dashed line: what a method
without any reasoning gives.

- **The random method.** N draws, N = the simulations the session used. Each
  draw takes every knob evenly, and apart from the others, from the values of
  the sweep's **first grid** (`status.json`, `grid`), not from the rows added
  later around the best point, which would favour it; its result is the sweep
  row with those values. After k draws the method's result is the best value
  of the target among the draws that meet the brief's conditions; before any
  draw meets them it has no value. Repeated 2,000 times with a fixed seed
  (mulberry32, seed 20261113).
- **On the chart**: the band is the 10th to the 90th percentile of those
  results at each k (a repetition without a value counts as the worst), the
  dashed line the median. The first draw stands at the session's first own
  simulation, after the harness's baseline. The sweep's best row stays as the
  horizontal line.
- **One sentence under the chart**, computed: "Within 0.5% of the sweep's best
  (…): this session after k simulations; random choice after m in the median
  (never within N in p% of repetitions)", with "not reached" where it applies,
  and "at the harness's baseline" when the default settings are already
  within.
- The legend says what the band is and from which rows it is drawn. Compare
  draws one band for each scheduling policy among the ticked sessions.
- `~/research/tools/evidence_checks/random_recount.py` counts the same from
  the sweep table with its own code; the page's band and the sentence's
  numbers equal it draw by draw.

What it shows for the two sweeps of `two-hosts-udp-demand` (40 draws): under
**cap** random choice never comes within 0.5% of the best (median after 40
draws 658.8 Mbps against a best of 671.5), while s006 was within after 2
simulations and s012 after 10; under **share** the harness's baseline is
already within (668.6 against 671.6 Mbps: once UDP loses nothing the weight
no longer matters), and random choice is within after 2 draws in the median.
The first grid is itself not evenly spaced: 11 of its 24 values of weightUdp
lie between 0.26 and 0.36, so even this band favours random choice somewhat.

**A hypothesis's question** (`EV.hshort`, `EV.question` in
`evidence_marks.js`). Where a hypothesis stands in short, the page shows its
question when the session recorded one: the first line of a test in the tests
list (its first 30 words, then "more" and "less"; the click moves nothing), a
line above the hypothesis text in the test's panel and the hypothesis's card,
the tree's row, the hypothesis map's node, the work-log card ("its
question: ..."), the highlights and the hover texts. A session that recorded
no question (before s020) shows the hypothesis text in its place.

**Void checks** (**DECISION 2026-11-13**, `FORMAT_FIX.md`, Part 3).
`EV_DATA.build` finds them from the ledger as `audit.py` does (10.8) and gives
such a check the result "void", keeping what the harness recorded as
`recorded`. A void check counts neither as held nor as failed in any count or
chart of the page, and it is marked wherever a check is shown, with the drawn
sign of a struck circle and the words "void: this decision rule compared a
simulation with itself":

- the header strip counts held, failed and void; the introduction says
  "33 of 47 decision rules held; 44 more were void (each compared a simulation
  with itself)";
- the tests list: "check void", the sentence in place of the margin (a void
  check has none), on a row that may wrap;
- the test's panel: the diamond of the flow chart says "void", the sentence
  stands under it, and a note below names the labels that are one simulation,
  their run, and what the harness had recorded;
- the tree's rows and each experiment's counts; "What this session is made
  of" (its own sign, named in the key); the session flow's box of checks;
- the session's summary: the checks in order with the void ones, a line
  "44 void: ...", and in "Verdicts against checks" the row "void";
- Home: the checks in order, held and failed without the void ones, and the
  column **void checks** ("44 of 91", sortable); Compare the same.

**A verdict that rests only on void checks** (the checks of its hypothesis in
the last experiment that tested it before the verdict were all void) is
marked "rests on void checks": in the tests list, the flow chart, the test's
panel, the work-log card, and as the sign alone in the tree. A verdict cannot
"disagree" with a void check. A claim of the final report that cites a void
check shows it with the void sign; the five kinds of claims are counted from
the checks that are not void.

In the replay all of this appears at the step of the check, or of the
verdict, never before. s006 and s011 have no void check and their pages are
as before.

**The tests list** (`evidence_more.js`) gives each test two lines: first the
hypothesis's id and its question (or, without one, its text cut after two
lines), across the card's width; under
it what was compared (ended with "…" where it is long, in full on hover), the
check, the margin and the verdict. The margin's bar has a tick at zero, and a
bar that is not zero is at least 2 px wide.

**The tests list follows the replay as the tree does.** A group heading and a
test's row can be read from the step at which their experiment is recorded; a
test's check and its margin from the step of the check; its verdict from the
step of the verdict. "no verdict" and "not checked" can be read only at the
last step, because only then is it known. A row that is not recorded yet stays
as a grey bar with nothing to read in it.

**The claims of the final report** are rows of full sentences. A claim has no
stripe coloured by held or failed, because a claim can rest on a refutation
(s011, claim 5, cites the failed check C5 as its evidence). It shows the checks
it cites itself as marks, in the order cited ("held C4, failed C7, held C8"); a
claim that cites only evidence tables, simulations or verdicts says "no check
cited" in the ordinary text colour; a claim with no evidence at all says "no
evidence" in the warning colour. The line under the claims counts the five
kinds: cite held checks only, cite held and failed checks, cite failed checks
only, cite no check, with no evidence. Over the 15 sessions with a final
report: 81 claims; 52, 11, 10, 8 and 0.

The **test** is the unit of evidence: one hypothesis put to one decision rule.
The experiment is only the batch it was run in. Nothing in `loop.py` records a
test; `evidence_data.js` derives it: a test's simulations are the labels after
`@` in its decision rule.

**Highlights** are up to seven key moments chosen by fixed rules from the
records (no model is asked): the first test that held; failed tests from which
a later hypothesis follows; the tests cited by the report's first claim; the
simulation after which the best valid result no longer improved; refusals; a
verdict that contradicts its check or a number in the model's text that
differs from the measurement; the final report.

**Views counted from the records.** These were decided in the operator's
`~/VIEWS_DECISIONS.md` (2026-11-12). Rules for all of them: in the replay a
view shows what the records by the chosen step give and nothing later; none is
printed; nothing is filled in; a click never moves the page.

- **Verdicts against checks** (`evidence_verdicts.js`): a table of counts, one
  verdict each. Row: the checks of the verdict's hypothesis in the last
  experiment that tested it before the verdict: held (all held), failed (all
  failed), mixed, or no check (the first format). Column: supported,
  inconclusive, refuted, and "no verdict" for a hypothesis that was checked and
  never judged. It stands in a session's summary in the detail pane (that
  session alone, counted by the page from the session's records) and on the
  Compare tab (the sessions of the chosen brief, from the counts in
  `control.py`'s session rows; with the operator columns on, also one table per
  scheduling policy). **Sessions of different briefs are never added
  together.**
- **The simulations of each turn, along one knob** (`evidence_knob.js`), on
  the session page under "Best so far": one horizontal axis per turn, one dot
  per simulation at the value it used. Each axis spans that turn's own
  smallest to largest value, with both ends printed with as many decimals as
  the finest value of that turn ("0.300" and "0.310"), and a shape joins it
  to the part of the previous axis it covers: filled lightly in the grid
  colour, its two lines in the muted text colour, so the narrowing can be
  seen. A turn with one value keeps the
  previous axis and says what it varied instead; the first axis of all is then
  the brief's range. A knob with choices keeps the brief's order. Simulations
  at the same value are stacked. A dot is a simulation, not a flow: it is drawn in the text colour,
  never in the colour of UDP or TCP. It is filled if the simulation meets the
  brief's conditions, as in "Best so far"; with an open goal there is one kind
  of dot. A simulation returned from an earlier one carries the mark of that
  kind beside its dot, at the size of a dot. The knob shown at first is the one that most experiments vary. With
  the operator columns on, a line marks the value of the best row of the
  sweep. A click on a dot opens that simulation.
- **The checks of each session, in order**: on Home, in each session's row,
  the session's checks in the order they were made, as ✓ and ✗, with a small
  gap between turns. At most 40 are drawn, then "+ n more"; a session in the
  first format says "not recorded". The sequence comes from `control.py`'s
  session row. After it stand the counts of held and failed, as marks with
  their numbers; there is no separate column of counts. The column is as wide
  as the widest sequence and no wider. The open session's summary shows the same sequence, counted
  from its own records, so an exported copy shows it too.
- **How far each check was from its decision rule** (`evidence_margin.js`):
  the margin, in each test's second line of the tests list. It is read from the check's rule with its
  numbers written in: for `a > b` or `a >= b` it is (a - b) / |b|; for `a < b`
  or `a <= b` it is (b - a) / |b|; comparisons joined by AND give the
  smallest, by OR the largest. A right side of 0, or `==`, has no margin: "not
  applicable" (none of the 337 checks so far). Held or failed is taken from
  the check, never from the sign. It is shown as a number with a short bar,
  cut at ±100% and marked when cut. The column's note, word for word: "By how
  much of the rule's right side the measured side cleared it. It depends on how
  the rule was written, so it compares checks of the same kind only; it does
  not say whether a prediction was bold." The tests list is printed without
  the margin.
- **The target measure where one knob alone differs** (in `evidence_knob.js`),
  on the session page under the chart of the turns: a table, one row per knob.
  A group is a set of simulations that differ in that knob only (a simulation
  returned from an earlier one counts once). Columns: the number of groups;
  the values the session used; the largest range of the target measure over
  its groups; the same among simulations that meet the brief's conditions. A
  knob with no group says "not varied alone"; the seed's row is named
  "run-to-run variation"; with an open goal the table is one line, "not
  applicable: the goal is chosen by the model". Its note, word for word: "A
  range shows how far the model moved a knob, not how much the knob matters."
- **Simulations left at each turn**: no chart (**DECISION**: "an even pace" has
  no definition, because the number of turns is not known in advance, and the
  count stays flat while a session tests on simulations it already has).
  Instead, in the card "What this session is made of", each turn's header says
  how many simulations were left at its start ("30 left"). A session with no
  turn records (those before s008) says "not recorded" once, in the card's
  key, and not under every turn.
- **Two figures on Home**, as two columns of the sessions table, from
  `control.py`'s session row: the simulations returned from an earlier one, of
  all simulations (s014: 91 of 118; s017: 112 of 153); and the simulations that
  no decision rule names, of the simulations of the experiments that test
  (s011: 14 of 43). The first format says "not recorded".

**The model's numbers against the measurements.** Where the model's text names
a measure with a number, or gives a number that equals a measured value of the
same experiment, the page shows both and marks agrees or differs.

Rules of the page:

- **A click never moves the page.** Whatever is chosen opens in the pane
  beside it. The one exception is the structure map's boxes, which scroll.
- The four producers are named AI, harness, ns-3, operator (**DECISION
  2026-11-15**, the operator: "ns-3", not "simulator", in the legend, the
  icons' notes and the sentences of a running session; the records' field
  stays `simulator`).
- One fixed icon per producer, in the neutral colour (until 2026-11-14 one
  fixed colour: model violet, harness magenta, simulator green, operator
  yellow). UDP is blue and TCP orange in every chart. Never two
  scales in one chart, with one exception (**DECISION 2026-11-12**): in "The
  simulations of each turn, along one knob" every turn has its own axis, with
  both ends printed and lines joining it to the previous one.
- **A sign is a drawn mark, not a character of a font** (`evidence_marks.js`):
  held, failed, not checked, supported, refuted, inconclusive, a hypothesis, a
  dropped one, a decision rule, a simulation, one returned from an earlier one,
  the final report, and a warning. Each has one shape, one weight and one size
  wherever it stands, and its kind is in `data-m` for the page checks.
- **The colour of held and failed is on the sign only** (**DECISION
  2026-11-12**): the green of held and supported and the red of failed and
  refuted are on the mark; the word beside it is in the ordinary text colour
  and weight.
- **A failed check is a result, not a warning.** The warning colour is kept
  for: a claim with no evidence; a verdict that contradicts its check; a
  number in the model's text that differs from the measurement; a refused
  answer or part; a session that ended without a final report.
- **Five type sizes**, named once in `index.html` (`--f-note` 11 px: notes,
  chart axes, labels inside pictures; `--f-sec` 12 px: secondary text;
  `--f-text` 13 px: the text; `--f-card` 15 px: a card's title; `--f-page`
  20 px: the page's title, and the recommended value in the overview). No
  other size is set anywhere, in a style or in a script, and no text is smaller
  than 11 px, a picture's text included: where a picture has no room for a
  label at 11 px the label is shortened, not shrunk. The canvas charts take
  their sizes from the same names.
- **A picture is drawn at its own size** where the page has the room, so that
  11 px is 11 px on the screen: the flow chart of a test, "Best so far" and
  the simulations of each turn are drawn to the width they have and drawn
  again when the window changes; the picture of the system and the structure
  map have columns as wide as they are. Below a window of about 1,340 px
  those two are scaled down (15, known limits).
- **Labels are in sentence case**, small and muted. No style sets capitals or
  letter spacing.
- Numbers stand in tabular figures everywhere on the page.
- **A defined term** shows its definition on hover wherever it stands. The
  dotted underline stands only where the term is a label: a card's heading, a
  column title, a field's or a box's label. Inside a sentence it has none.
- **The grey line beside a heading says what the card holds.** How to operate
  a card ("click …", "point at …") is said once, under "Using the page" in
  "How to read this page". What can be clicked shows it by the pointer and a
  change of background under it.
- **A row of Home and of Compare is one line high.** A brief, a start and an
  ending never break inside a word or a date; a text too long for its column
  ends in "…" and is given in full on hover. The review cell says "n to
  check" until the review has its first tick, then the progress; "not
  started" is not printed.
- Missing data is shown as "not recorded". Old sessions open as far as their
  records allow.
- The page reads a ledger without its draft records and never requests
  `drafts.jsonl`.
- The frame (title, tabs) is the same on every view.
- Light and dark mode. Flow charts are plain SVG drawn by the page's own
  script; Chart.js is used for the time charts only.
- A redraw keeps what the reader has open and the scroll of inner lists; form
  fields update in place.

The page's checks are kept outside the repository, in
`~/research/tools/evidence_checks/` (`ev.sh` and Playwright scripts: click
everything, the "Done when" checks of both plans, the replay leak test, 
`ev_bar.py`: the top bar has the same items at the same places in every view,
and `ev_glance.py`: in the card "What this session is made of" each number
equals the marks drawn, the replay shows nothing recorded later, and a click
opens the item without moving the page; in the card "The system" every object
is drawn and opens beside the picture, the values are the brief's or the
opened simulation's, and the scheduling policy stays operator-only);
`ev_views.py`: every view of `VIEWS_DECISIONS.md` against a count made from
the ledgers, against the figures of that sheet, and in the replay;
`ev_polish.py`: the "Done when" checks of `PAGE_POLISH.md`, and that no sign
is a character and no result word is green or red). `ev_all.sh` runs every
check on a fresh scratch copy.
`ev_replay.py` does not count an id that stands in words the model itself had
written by that step, such as "next: run X4". It reads the tests list row by
row (what can be read is exactly what is recorded by the step), and it stops
for a moment every 20 drawings: drawing the page thousands of times without a
pause made the browser hold 14 GB and stall on the longest session.
Anything that starts, stops or writes is tried on a scratch copy of the project
on port 8611, never on the real sessions.

**Readability, the afternoon and evening of 2026-11-15** (**DECISION
2026-11-15**, each at the operator's word while reading sessions s029 and
s030; the files are `evidence_more.js`, `evidence_cards.js`,
`evidence_find.js`, `evidence_views.js`, `evidence_words.js`,
`evidence_top.js`, `evidence_marks.js`, `evidence_setting.js`,
`evidence_glance.js`, `evidence.js` and the styles in `index.html`):

- *One word for one thing, again.* The row labels of "The session at a glance"
  are the things they hold, by the word their box defines: **Hypotheses,
  Checks, Simulations, Verdicts, Final report** (they were "Stated", "Tested",
  "Judged"). The line that holds a verdict is called **Verdict** everywhere:
  in the notebook card, the test's detail and the hypothesis's box (it was
  "Conclusion"; on an arrow's box "Judged"; a test's box said "Found" where
  the others say "Result"). The keys in the page (`data-l`, `data-td`,
  `data-hp` = `conclusion`) keep their names.
- *The final report's detail pane* (`reportBody`) has the parts of "What it
  proposes", in the same order and under the same names, each in a numbered
  box: the aim; the proposed adjustment (a table: setting, at the start, what
  it recommends; a changed value is set off, "unchanged" and "not named" are
  light); the expected result (a table, values as everywhere else: "83.81 %",
  "485.9 Mbps"; the two measures that only repeat a setting stand last,
  lighter); its diagnosis, because, but (a claim is a card: number, the marks
  of what it cites, its sentence with its terms set off, then one row per
  cited record: the link, what it is, its result, "Rule" and "Measured" or
  "Because" as labelled lines, and the reviewer's tick and note at the right);
  "holds when" and "breaks when" side by side; the explanation, one sentence a
  line (`repLines`: the words and their order are the AI's); open questions;
  its numbers against the measurements. The line under the title counts the
  settings changed, the measures expected and the claims by what they cite.
- *The aim has a colour and a sign of its own* (a clear blue, `--aim`, and a
  flag on a summit, `EV.flag()`), as the answer has its gold and its bulb. An
  aim the AI chose is **stated at the end**: the harness asks for the aim only
  in the final report. The board's first box therefore says "chosen by the AI
  at the end", and so do the box's card, the setting's block 3 ("At the end,
  in its final report, it chose: …"), "What it proposes" and the report's
  pane, so that nobody reads the hypotheses as written against an aim that was
  already on record. A click on the aim's box opens the brief's card, which
  now begins with the aim in a box of that colour: the brief's line, then (an
  open aim) the aim the AI chose, uncut, with the turn it was stated in and a
  link to the report. The cards of one row of "The setting" are equally tall,
  and the aim's card shows the chosen aim in as many whole lines as it has room
  for (`aimFit`).
- *The board's key is a small table* (it was two lines of sentences, then, for
  an afternoon, bordered items in two bordered groups; the operator: "more
  neatly and minimally"). One bordered box, two rows and one line: **A box** "is
  a hypothesis, as the AI judged it", then its looks (supported, refuted,
  inconclusive, dropped, never judged; "checked, not judged yet"; the ring,
  "cited by the final report"); **An arrow** "leads to a hypothesis that
  follows from", then what it follows from (one that was supported, one that
  was refuted, results of both kinds, an inconclusive result, an experiment's
  result table, the brief or the baseline); the last line says that pointing
  reads and a click opens. A look is its mark and two or three words, without
  a border of its own; its whole sentence is in the box that opens when it is
  pointed at (`data-wd="l:key-…"`, in `LEGEND_SAYS` beside the legend's). Only
  the looks the board has are listed, as before.
- *A light rule between the turns.* A dashed 1 px line stands between each two
  columns of the board (`line.map-sep`), through no box. (The operator asked
  for "light horizontal borders between turns"; the turns are columns, so the
  rules are upright. Reported, to be changed if something else was meant.)
- *An exploration's box* holds its question in two lines, however the words
  break (a long word had taken a line and the third was cut through).
- *The table under the board has a button* ("open" / "fold", at the right of
  its line). Brief keeps what the browser remembers (`ev-find`); Full opens it;
  folding or opening it by hand holds through every redraw until the next
  switch between Brief and Full (`EV.s.findOpen`, cleared by `EV.act.level`).
- *A rule's bar is at most 300 px long* (it ran the width of its line: 424 px
  on a notebook card, 627 px in a test's detail), so that the threshold and
  the dot are a short reach apart (the operator: "users have to move mouse
  more"). Positions on a bar are per cent, so nothing else changes.
- *A click on a step of the stage strip* (the operator: "When I click 'the AI
  writes its reply', what would be good information to show?"). The steps of a
  running session's strip are buttons where they have something to show; the
  page does not move. "The AI writes its reply" opens the turn's work log
  beside the page, which now begins with a block **Now** (`EV.liveNowCard`,
  `#lg-now`), with the time running: what the AI was given (the brief, its
  record so far with the count of records, and what is new to it since its
  last reply: the result tables, the checks with how many held, failed and
  are void, the answers to what it asked for, the harness's notes); which
  hypotheses wait for its verdict (checked, not judged); what this reply may
  bring; the simulations left and the most one experiment may hold; how long
  its earlier replies of this session took (from the records' times: a turn's
  first record to the first record of its reply); and that nothing of the
  reply can be shown while it is written, because it arrives whole. Until the
  reply is there, "What it decided" and "Why, in its own words" say "not there
  yet: the reply is being written" (they said "nothing usable" and
  "observations: not recorded"). The steps of the simulations and of the
  checks open the turn's experiment once it is recorded; then the work log's
  Now block names the experiment and how many simulations are collected.
  Nothing in the block is the AI's text and no draft is read. Check:
  `ev_live.py now` (every moment of a recorded session at which a reply was
  being written, each figure counted again from the records).
- *The turn being worked on stands out in the glance as on the board* (the
  operator: "Emphasize ongoing turn in the similar manner with one in 'What it
  needed to find out' for consistency"). The six cells of its column in "The
  session at a glance", from the turn's name to the final report, have the
  tinted ground and the edge of the board's band (`td.gl-nowc`, the colour
  `--live`), round at the top and at the foot by the band's radius of 10 px
  (the operator, a little later: "highlight with round edge … for
  consistency"), and its name says "· now". While its reply is being written the
  sentence under the glance says "the AI is writing its reply" (it said
  "nothing the harness could use", which is true only of a turn that is over).
  Check: `ev_live.py now`.
- *"Not accepted" beside a turn's name* (the operator read "1 refused" on
  turn 6 as "1 refuted" and asked why turn 2, which has a refuted hypothesis,
  had no such mark). The count of answers or parts of an answer that the
  harness did not accept in a turn says "n not accepted" in the glance, with a
  box that says it is about the form of the answer and not a verdict, and "n
  parts of its answer not accepted" in the notebook's heading of the turn.
  The lines that list them still begin "refused part …", in the harness's
  own word; whether the page should say "not accepted" everywhere is open
  (section 15).
- *A test's detail, cut to what it is for* (the operator asked for a neutral
  estimate of how much of the pane is useful; measured on the test of H10 of
  s031: 4,327 characters over 2,046 px, a third of them the chain of boxes,
  which repeats the sections under it, and the rule shown four times; the
  operator: "Lets go"). (1) **A rule with an "or" in it is shown as either-or
  lines, not as bars** (`EV.ruleGroups`, `EV.ruleAlts`). A bar says of its
  comparison that it "must" hold, which is not so for one side of an
  either-or: under a rule that held, half of the lines said "does not hold".
  The rule is read as groups joined by "and"; a group is one comparison or
  several alternatives; an alternative is one comparison or several joined by
  "and". A group whose comparisons are all about one simulation is headed by
  that simulation and stands in one line ("either UDP loss 0 % not over 1 %
  or ✓ TCP goodput 327.8 Mbps at most 419.9 Mbps", then "holds"); otherwise
  each alternative has a line. The alternative that is met has the sign, the
  other is grey and says "not …": it is not a failure. A right side that is a
  sum of numbers is shown as its value (the rule's own writing in its box). A
  rule nested deeper than that stays a sentence. The same lines, without
  numbers, are the rule under "Expected", on a notebook card and in the
  rule's inset. (2) **"Expected" shows the rule as a short list** (one line a
  comparison, or the either-or groups) in place of the one long sentence; the
  sentence as it was written is in "The exact records". (3) **The chain of
  boxes is folded** ("the test as a chain of boxes", `#td-chain`); a click
  opens it and draws it to the pane's width, and the browser remembers it
  (`ev-chain`). (4) A number added to or taken from a measure is in that
  measure's unit ("TCP goodput + 5 Mbps"; it read "+ 5,000,000"). (5) The
  line of the number check says "the n numbers in this text match the
  measurements" (it read "1 number agree"). The pane of that test is now
  1,661 px and 2,595 characters. The chart at its foot, with its PNG and CSV
  buttons, stays. Check: `ev_usable.py either` (every comparison, alternative
  and group worked out again from the page's two numbers, and the groups
  together against the harness's recorded result: 15 rules, 117 comparisons,
  in s008, s009, s010, s012 and s031).
- *Four faults left by the interrupted session, found by the full run* (they
  had failed in its last full run too, unread). (1) While a reply is written
  after an experiment, "What it needed to find out" scrolled sideways below
  1,440 px: the three measured values of a simulation's tile ran out of the
  tile. They wrap inside it now, and a tile has its three places from the
  start (a value not known yet is a dash with the reason in its box), so that
  a tile keeps its height from waiting to ended. (2) The first row of "The
  setting" was 18 px taller (the columns lowest, highest, starts at, and a
  list of six TCP types on three lines), which pushed "The session at a
  glance" off the first screen at 1,500 x 1,000: a list of choices holds two
  lines in that block, the whole list being in its box, in the setting's
  box and in block 4. (3) `ev_readable.py` part 3 still expected "0.05 to
  0.95 … from 0.5" where the three columns stand: the check was brought up to
  the page. (4) The line that sums up refusals of one kind showed a field's
  name (`follows_from`) as if it were the page's word: the part and the
  reason, the harness's own words, are marked as such (`data-own`).
- *Why a check came out as it did, on the box* (the operator: "Shouldn't we
  show reason for failed check?"). A hypothesis that has its check and not yet
  its verdict says, under "check failed" or "check held" and its question
  (then one line), what was measured against the rule, in the words of the
  table under the board ("46.7 %, not at least 98 %"; `.bx-why`); the whole is
  in the hypothesis's card. With the verdict the line goes, as the edge does.
  Check: `ev_usable.py checked`.
- *The words of "How it worked as a researcher"* (the operator: "We should
  make 'present', 'partly', 'not yet' more visible and distinct because they
  are important"). Each word has a look of its own and one width (100 px),
  in 14 px bold type: **present** a filled pill with ●, **partly** a pale pill
  with a dark edge and ◐, **absent** an outlined pill with ○, **not yet** a
  dotted pill with ◌; "not recorded" and "not applicable" stay light. They
  differ by fill, edge and sign, not by a colour of good and bad: they are
  findings, not errors. The same looks stand in Compare and in the card's
  last line. Check: `ev_usable.py marks`.
- *The key of "The session at a glance"* has a border around each item that
  explains a mark (the operator: "Give border to each"), as the page's legend
  has. Its two sentences about the card as a whole ("click a name to open it
  beside the page", "the rows are the harness's form of a turn …") have none
  and stand on a line of their own under the items (the operator: "Dont give
  the same border to these. Dont you think they are different?"). Check:
  `ev_usable.py marks`.
- *Home with a session running.* The table was 22 px wider than a 1,440 px
  window as soon as a session ran (the pill "running" beside the session's
  name; found while reading the polish check, and on the live page with s031
  running). The running session now has the moving dot beside its name (two
  columns on stands "running now", as before), and a session's start is said
  as month-day hour:minute, with the whole time in the cell's box (Home and
  Compare). The table's least width at 1,440 px is now 1,340 px. Check:
  `ev_usable.py home` (a running session on a brief with a name of 42
  characters).
- *Checks of this section's later changes*, which had first only been tried
  by hand: `ev_usable.py key` (the key's two rows, exactly the looks the
  board has, a box for each look, no sideways scrolling from 900 to 1,800 px),
  `board` (the rules between the turns, the aim's box opening the aim whole,
  the table's button in Brief and Full), `short` (the bars' length) and
  `legend` (a box for each item of the legend, which stays 25 px high).
- *The legend's items have boxes* (`data-wd="l:…"`, `LEGEND_SAYS`): the name,
  its group on a chip, one or two sentences, and where it is seen. No `title`
  is left on them.
- *A record's name says what it is.* "N3", "E2", "Q1" carry a box
  (`data-wd="r:…"`, `ID_SAYS`): what the letter stands for (H hypothesis, X
  experiment, S simulation, E result table, C check, V verdict, N note of the
  harness, Q request, T tool result, U turn record, R final report), who wrote
  the record, in which turn, and what it says. "How to read this page" lists
  the letters.
- *Refusals that say one thing are one line, in the work log too.* An answer
  that judges again what was judged gets one refusal for each hypothesis ("H1
  is not an open hypothesis", seventeen times in s030). The work log now shows
  them as the notebook does: one line that says how many, what and why, and
  that this is not an error of the system; each note is under it, at a click.
- *A hypothesis's box* has "Expected" and "Result" each in a box of its own.
- *The top bar* has no captions ("All sessions", "One session"): they read as
  titles. The two groups stay apart by the rule between them.

Still without their own lines in this section, from earlier the same day (the
code and the checks are the record): the "New session" pill in the top bar of
every view, the answer's gold ground and bulb, the answer card in chips and
rows, "Measured here" as a row of an object's card, the unit in a measure's
box, a claim's click that keeps its place and claims of equal size, a value's
box as named rows.

**The network builder** (`viewer/brief_net.js`, `brief_canvas.js`,
`evidence_net.js`; the set-up page, "A network I build"). The operator builds
the `"topology"` of a brief (section 7) by hand: a palette of tools in four
groups (nodes, connections, applications, traffic control) dragged onto a
picture drawn with JointJS (`viewer/vendor`, carried by the page). A host is
drawn simply (its sign and one mark for each application and queue) or in
full (applications, internet stack, traffic control, as in the two-host
picture); hosts are moved and resized freely, the picture is moved and
zoomed, F fits it, the left and right arrows undo and redo. The chosen
object's card stands beside the picture, and under it one card for each part
of the network with every setting it has and what the program fixes; a
setting is fixed by the operator (✧) or left to the AI (✦) by a click on its
mark. Since 2026-11-17 the builder follows ns-3's own parts (section 6.5):
- a link's card names its two devices, and each can be given a rate and a
  transmit queue of its own ("set separately", and "same as the link again");
- a shared queue or a scheduler can be put on either sending side of a link,
  and on both; the first keeps the addresses `<link>.queue.…`, the second is
  `<link>.<host>.queue.…`, as `network.apply` does it;
- a scheduler's card asks, for each flow that passes, in which queue it
  waits: one of its own, a shared queue that stands, or a new shared queue.
  Flows in one queue share its part; the picture draws them into one box.
`EV.netEnds`, `EV.netQueues`, `EV.netSettings` and `EV.netOutNames` mirror
`network.ends`, `queues`, `settings` and `outputs`; the check `ev_build.py`
(part `ends`) compares the two on every step, saves the network and starts a
session on it. A session's page draws a mark for each described queue and
says a device's own values and a shared queue in words.

### 12.2 Earlier pages, kept working

| File | What it is |
|---|---|
| `index_runs.html` + `adrs_view.js` | the streamlined run page of 2026-11-11 morning: every simulation, one chosen simulation, two on the same axes |
| `index_full.html` + `adrs_view_full.js` | the six-page viewer of 2026-11-10: overview, system objects (`objects.json`), experiments, packet events, runs, control (with the brief editor, `brief_editor.js`) |
| `index_old.html` | the first page of 2026-11-09 |

Nothing needs them any more except the packet-event recordings, which only
`index_full.html` shows.

### 12.3 In the ADRS main viewer

`viewer/adrs_view.py` is loaded by file path by the ADRS viewer
(`viewer_new.py`, port 8767) and shows the project as task `twohosts`: each
session is a run, plus `operator_checks`. It is read-only and passes the raw
records to `adrs_view.js`, which draws the run page there. The task has no
score, so the main viewer hides its score sections. It shows the earlier run
page, not the evidence page.

## 13. Repository

`~/project` is a git repository (branch `main`), pushed to the public
repository `github.com/peace7389/loop` so that the work can be read from
outside. Routine: `./snapshot.sh` (copies the scenario from the ns-3 tree and
this file from `~/ADRS/openevolve/`, then stages everything), commit, push, at
the end of each stage.

Not in the repository: `ns-3.49/` and its tarball, `flowmon.xml`, pcap files,
`checks/exports/`. The operator's own notes and patches in the folder stay
untracked until they say otherwise.

## 14. Things not to do

- Do not let the model see the scheduling policy, the scheduler's source, a
  file path, or anything under `checks/`.
- Do not put explanations of the expected behaviour in a brief, the prompt or
  the manifest.
- Do not let the model write files, run a shell, or edit the ledger.
- Do not run an operator simulation through `tools.run`.
- Do not test anything that starts, stops or writes against the real sessions.
- Do not open, print or show `drafts.jsonl` or `calls.jsonl`, except on the page `viewer/agents.html`.
- Do not invent a value for something that was not recorded.
- Do not overwrite a brief, rewrite an old session, or edit a ledger line.
- Do not change the ns-3 scenario without the operator's word; after a change,
  run the checks of 6.4 and `check_objects.py` again, bring
  `viewer/objects.json` up to date, and make the sweeps and recordings again.
- Do not write into `viewer/objects.json` how the scheduling policy is set: the
  file goes into exported sessions.
- Do not modify anything under `ns-3.49/` except `scratch/two-hosts/`; no
  `main(` in any file there other than `two-hosts.cc`.
- Do not install system packages or Python packages; do not add a framework,
  a database or a build step.
- Do not enable pcap by default.

## 15. Open items and known limits

1. **Nothing has been judged.** Every checklist item is `unjudged` and no
   session has a review or a sign-off.
2. **The open-goal sessions (s014 to s019) are unscored**, at the operator's
   word. Scoring them would also need an answer key and sweeps for
   `two-hosts-open`, which has one more knob (`udpRate`).
3. **The file server serves every file of the project**, read-only, on
   127.0.0.1, including `checks/` and `drafts.jsonl`. That a "random" session's
   policy stays hidden until it is scored, and that drafts are not shown, is
   kept by `/api/status` and by the page not asking for those files, not by the
   server refusing them.
4. The scheduler's source and the titles of two recordings in `trace/` still
   say "mode".
5. The ADRS main viewer shows the earlier run page, not the evidence page.
6. Old-format sessions (`s001` to `s007`) lack some records (8.7); the page
   shows "not recorded" there.
7. All sessions used one model, temperature 0.3, seed 1 for the simulations
   unless the model chose otherwise. Nothing here says how the results vary
   with another model.
8. **Two pictures are scaled down in a narrow window.** The picture of the
   system and the structure map of "How to read this page" have a fixed
   drawing width (1,000 and about 940 px); in a window narrower than about
   1,340 px (and wider than 1,100, where the page becomes one column) they are
   scaled to fit, and their text is then smaller than 11 px.
9. **Designs that lost a setting, and decision rules that compared a
   simulation with itself** (found 2026-11-13). Until s019 the answer format
   let a design leave knobs out, and the model server's enforcement of the
   order of the format's properties meant a design that began with another
   key could not state `weightUdp` (8.3, confirmed by two requests to the
   server). 107 of 337 checks are void for it (section 11). The format, the
   harness (8.5) and the page (12.1) are repaired; **s014, s016, s017 and s019
   are kept as records of the defect, not as results**, and one verdict of
   s004 rests on a void check. Until 2026-11-15 the recommendation object of the final report
    had every knob optional in a fixed order (weightUdp first), and reports
    could lose knobs the same way: **s030's recorded recommendation lacks its
    UDP rate, queue length and TCP buffers** (8.6, repaired from the next
    session on). In the reports of the earlier sessions a knob that is not
    named may have been meant at another value than its default; the records
    cannot show it, and a score (10.4) measures the recommendation as
    recorded, the others at their defaults.

10. **Left as it is after `READABLE_PAGE.md`** (2026-11-14). The picture of the
    system is still scaled down in a window narrower than about 1,340 px, so
    its labels are then smaller than 12 px (item 8). "The simulations of each
    turn, along one setting" keeps one axis per turn (the exception decided on
    2026-11-12), though the sheet's design rules say "never two scales". The
    sheet's own example of the adjustment line shows a setting with five
    digits and no unit ("ratio 0.5 → 0.30295"): a setting's value is shown as
    recorded, and the rule of four digits and a unit is applied to measured
    numbers. A line of "How it worked as a researcher" that names a section
    goes to that section, a fifth click that moves the page beside the four
    the sheet lists. "Commits to a prediction first" counts a decision rule as
    late when it names a simulation returned from an earlier one (the
    baseline, most often); whether that is the right reading is for the
    operator to say.

11. **Open after the evening of 2026-11-15**, each for the operator to decide.
    (a) "Refused" and "refuted" differ by one letter: the count beside a
    turn's name now says "not accepted"; the lines that list what was refused,
    the legend and the work log still say "refused". (b) A failed check is
    not yet a refutation: the prompt says so (8.9), nothing in the harness
    enforces it, and no real session has run with it; the researcher card's
    line "Accepts a result against its expectation" still counts a failed
    test judged inconclusive as not accepted. (c) How a hypothesis and the
    simulations of its test belong together is shown only in the test's
    detail (its plan) and by pointing at a name in the glance; the tiles of a
    running experiment do not say which hypothesis a simulation serves.
    (d) The rules between the turns of the board are upright, the turns being
    columns; the operator's words were "horizontal borders".
12. **Open after 2026-11-17.** (a) The shared page (10.1) has been tried by the owner alone: no other account has
    opened a tunnel yet. Reviews and checklist judgements carry no account, so two reviewers of one session overwrite
    each other. Every account of the machine can read `checks/` (answer keys, sweeps, `people.jsonl`).
    (b) Sessions on the briefs made before 2026-11-17 still get those briefs' hand-written task; `trap` contradicts
    its own aim and settings and is kept only as the record of s031. (c) The page has no view for a session of the
    arm "plain" or for a random search: they are compared by their figures (section 11), not on the page.

## 16. History in short

| Date | What |
|---|---|
| 2026-11-09 | First build in five stages: scenario with the stock priority scheduler, the weighted scheduler with two behaviours, tools, the loop, a first viewer. Session s001: 12 turns, 5 experiments; 40% of the model's answers were cut off at 8,000 tokens. |
| 2026-11-10 | Simulator revised (build 2) after a review found TCP segments split in two and the seed without effect. Operator checks 1 to 4. The viewer grew to six pages; the control server replaced the plain file server; the project became a task of the ADRS main viewer. |
| 2026-11-11 | Scheduler renamed and the policy moved to an environment variable (build 3), after s001 showed the model reading the policy's name in the source. `RESTRUCTURE_PLAN.md` stages 1 to 5: sessions in their own folders; briefs; experiments of several simulations with decision rules checked by the harness; the final report; sweep, answer key and score. `CHECKS_AND_REPAIRS.md`: checks 5 to 11, and repairs B1 (loss cannot be negative, build 4), B2 (a tested hypothesis needs a verdict), B3 (draft text in its own file). Terms fixed: decision rule, scheduling policy. Rivals; simulations not run twice; answers taken part by part. `EVIDENCE_VIEW.md` and `PAGE_REDESIGN.md`: the evidence page (replacing stage 6). Sessions s002 to s019. The project became a public git repository. |
| 2026-11-12 | Stage 7: this document rewritten as a whole. The top bar made the same in every view. Two cards at the top of a session's page: "The system" and "What this session is made of". `check_objects.py`. |
| 2026-11-13 | `OVERVIEW_REDESIGN.md`: the Overview as one band, the model's own words as the card "The final report". `FORMAT_FIX.md`: the cause of designs without `weightUdp` confirmed at the model server; the params object built from the brief with every knob required; a question with each hypothesis; `answers.jsonl`; a plan that cannot test anything is refused part by part; `audit.py` and the void marks on the page; six new sessions on `two-hosts-open` (s020 to s025). |
| 2026-11-14 | `NOTEBOOK_VIEW.md`, Part 3, Step C, begun at the operator's word: new settings of the simulator, one at a time, each with an operator check that predicts a number, and with the earlier checks byte-identical at the defaults. First setting (build 5): each queue's own length, `queuePktsUdp` and `queuePktsTcp`; check 12; a brief may leave them out, fix them or open them to the model; the picture and the brief editor show and set them. Still to do, each waiting for the operator's word: the TCP initial window, a maximum rate per flow, strict priority as a third scheduling policy. |
| 2026-11-14 | `READABLE_PAGE.md`, parts 1 to 8: the session page in three levels of detail and in the order of a reader's questions; the setting and the set-up page as one design of seven blocks; "What it needed to find out"; the final report as one argument, with a required role for each claim; "How it worked as a researcher"; design rules checked by a script; a guided walk. |
| 2026-11-14 | The live view of a running session, at the operator's word: the page's sections as a skeleton whose empty places fill as records arrive, one sentence that says where the work is, and the time between a decision rule and its result under each result. No change to the harness: everything is read from the ledger. |
| 2026-11-14 | The words that need explaining, at the operator's word: settings, measures and parts of the network are marked wherever they stand, and a small box says what each is, from the brief, the harness's list and the picture's objects. |
| 2026-11-14 | Who produced an item is said by an icon, at the operator's word; colour is kept for the outcome of a test and for the two flows. |
| 2026-11-14 | The picture and the words set each other off on hover, at the operator's word. |
| 2026-11-14 | The board of "What it needed to find out", at the operator's word: the hypothesis map moved up, with arrows in the colour of the result that led onward; the table of the tests folded under it. |
| 2026-11-14 | The live banner says how many simulations of the running experiment the harness has collected; a simulation's detail shows how the simulator was started. |
| 2026-11-14 | Every new hypothesis says why it is asked (`why`, required), at the operator's word; the page shows it beside the question, and nothing where it was not recorded. |
| 2026-11-15 | Readability, at the operator's word: cards for a hypothesis and for an arrow of the board, what a brief asks beside its name, grouping by regions, nothing changing size on a click, a test's detail in full under the headings of its card, a simulation opening inside its test, the glance in names and words, a bar for each rule against its outcome, the aim and the answer (with its reasons) on the board, the whole configuration and chosen conditions on the set-up page, toned colours with one accent for what is happening now. |
| 2026-11-15 | Simulator build 6, at the operator's word that fixed values should be settings: TCP's first window (`tcpInitCwnd`) and TCP's buffers (`tcpBufBytes`), each left out, fixed or a knob of a brief; checks 13 and 14; the earlier checks byte-identical. |
| 2026-11-15 | Usability, each at the operator's word in one morning: a part is configured in its own card on the set-up page (fields, the mark of who decides, the scheduling policy on the scheduler's card) and numeric settings have bars; the board's first box says the aim the AI chose; "ns-3" names the source; pointing at a rule bar's dot or threshold opens its value; a turn of the notebook folds at its heading; the page never moves by itself (a note says that a turn or an experiment's simulations started; the reader's place is kept) and the tiles of the newest simulations stay; a simulation in a rule is said by its settings; the glance says "5 simulations" and an experiment has a box; then, the same day: the boxes of words, hypotheses, parts and bar marks redesigned so that a name, a value, a quotation and a note each look different and say less; a side of a comparison said by what it is; one bar and one phrase for a measure held between two numbers; the bars in "The decision rule, in full"; one plain line per TCP type; a note under the scheduling policy that says what it does with the form's numbers. Check `ev_usable.py`. |
| 2026-11-15 | The same afternoon, each at the operator's word: running and ended simulations told apart on their tiles, what was set apart from what was measured, and a box that reads a simulation's name; the turn being worked on highlighted, every turn with a column on the board, a check's result on a box before its verdict; cards for the glance's tests and verdicts; a notebook card in three bordered parts and a test's detail that says each thing once; lowest, highest and start in columns; the ending said plainly. The prompt tells the model to plan for the limit on simulations (8.9). |
| 2026-11-15 | Simulator build 7, at the operator's word: the device's transmit queue as a setting (`devQueuePkts`; check 15), and `series.csv` written sample by sample (check 16), so that the page can show each simulation of a running experiment on a tile of its own, its curve growing as the simulator works. |
| 2026-11-15 | The evening, each at the operator's word: one word for one thing (Hypotheses, Checks, Verdicts; "Verdict" for "Conclusion"), the final report's pane in numbered boxes with tables and claim cards, the aim in its own colour with a flag and "chosen by the AI at the end", borders in the board's key, boxes on the legend's items and on record names (N3, E2), repeated refusals as one line in the work log, no captions in the top bar; the last turn names the hypotheses that still need a verdict |
| 2026-11-15 | Completion of that evening after an interrupted session, and three more at the operator's word: the board's key as a small table of two rows with each look's sentence in a box; a light rule between the turns; a button on the table under the board, whose folding holds in Full; an exploration's box in two lines; a rule's bar at most 300 px long; an empty set-up on the set-up page. Checks for what had only been tried by hand: `ev_usable.py key board short none legend`; `test_step_c.py` counts only the briefs that state none of the later settings |
| 2026-11-15 | The same evening, each at the operator's word: a click on a step of a running session's strip opens what is happening (the turn's work log begins with "Now": what the AI was given, which hypotheses wait for its verdict, how long its earlier replies took); the reason of a check on an unjudged box of the board; the empty set-up as a box of its own under the list of saved briefs; present, partly, absent and not yet each with a look of its own; borders in the glance's key; Home no longer wider than the window while a session runs. The prompt says that a failed check is not yet a refutation (8.9) |
| 2026-11-15 | A test's detail cut to what it is for, at the operator's word after a measured estimate: a rule with an "or" as either-or lines in place of bars that said "does not hold" under a rule that held; the rule under "Expected" as a short list; the chain of boxes folded. Four faults of the interrupted session that its last full run had reported and nobody had read: tiles' values running out of their tiles, the first screen 18 px too tall, a stale expectation of a check, a field name in a summed-up refusal. "Not accepted" beside a turn's name, where "refused" read like "refuted" |
| 2026-11-17 | The page shared with the lab, at the operator's word: every account of the server may use it through its own SSH tunnel; one session at a time, and the page says which is running and who started it; only that account or the owner stops it; every start, stop and saved brief noted with its account (`checks/people.jsonl`, not in git); `drafts.jsonl` given to nobody. |
| 2026-11-17 | The task is written by the harness from the aim and the open settings, after the operator found that `trap`'s task contradicted both; a name in braces in the description may be a knob; three briefs with the seed fixed (`two-hosts-open-2`, `two-hosts-udp-demand-2`, `trap-2`). |
| 2026-11-17 | The final report says what limits the result and which settings made no difference (the harness part was written on 2026-11-15 and finished now), shown on the page as "What limits the result"; the last violet edge is gone. |
| 2026-11-17 | Two comparison arms for the question "does the hypothesis format help?": `loop.py --arm plain` (the same loop without hypotheses, decision rules and verdicts) and `random_search.py` (no model). |
| 2026-11-17, late | The network follows ns-3's own parts (`TOPOLOGY.md`, stages N1 and N2): a link is a channel and two devices, each of which can have its own rate and transmit queue; a queue on either sending side of a link, or on both; several flows in one queue of a scheduler (a class). Second build of `net`, five predictions met (`checks/net2`), the ten earlier networks byte-identical. `network.py`, the builder and a session's page read all three; older briefs are read as before. In a hypothesis, `follows_from` may name a run id (found in s043). Session s043, the first under the mandatory look-again: a review after every tested hypothesis (9 in 6 turns). |
| 2026-11-18 | The builder names ns-3's objects: a flow's application (OnOff, BulkSend) and its socket (UDP, TCP) are two choices of its card, so TCP can send at a constant rate (third build of `net`, `checks/net3`); the Link tool says that it brings a net device (NIC) at each end, the queue tools name their queue disc; a scheduler with a single queue is described as that. The brief `two-hosts-one-queue`. "The session at a glance" is unfolded whenever the page is loaded. |
| 2026-11-18, late | What else ns-3 has for the builder's objects ("Do it", the operator's list of six): an application's times, a device's own largest packet and loss, TCP's options, ns-3's queue discs beside the project's scheduler, the ns-3 attribute beside every setting; the AI's own change of structure can add OnOff over TCP (fourth build of `net`, `checks/net4`). Not done: one vocabulary with the ready-made two-host system. |
| 2026-11-18, night | The arm "supervised": a researcher that proposes and a supervisor, asked apart from it, that reads each new guess against its records, reviews each test before its simulations and rules on what the checks mean; objections; everything of the supervisor on the page with its ground and what it was shown. After a review of the loop's objects: the verdict had repeated the check, the judge had never refused. |
| 2026-11-18, night | Measurements the researcher defines: both programs get a probe that only listens (0 of 190 re-runs of recorded simulations differ), the tools `measure` and `probe`, and measurements an experiment defines and its decision rules name. The first real supervised session (s044) showed the supervisor refusing guesses it could not check, because it was not shown the tool results: repaired. The builder says who decides a setting in words, takes the aim's conditions as rows, and needs nothing typed but a name; the page's card "Two agents". |
| 2026-11-18, late | The researcher's short reply in the arm "supervised" (the harness derives a test's needs from its rules); a limit on the draft, half of the answer's tokens, in all arms, because empty answers came from drafts that used the whole limit; the builder's row "simulation time, s". |
| 2026-11-18, late | The card "Turn by turn: who did what" (the operator's proposal): one column for each entity (Researcher; Supervisor in a two-agent session, Judge in a session with judge records; Harness; ns-3), one band for each turn, time runs down, every ledger record a box in the column of whoever made it (simulations, requests, tool results and notes that follow each other share a box); a box's id opens the record, a turn folds, the replay hides what came later. `viewer/evidence_turns.js`; check `evidence_checks/ev_turns.py`. The older "Session flow" under "Looking closer" is unchanged. |
| 2026-11-22 | The page shows less (the operator: "too complex and obscure with too many information shown"): "Turn by turn: who did what" is no longer a card but the folded detail at the end of "What it needed to find out" (closed on a first visit, open in Full, remembered as `ev-turns`; the box "Session" of "How a session is built" opens it); "Two agents" and "The session at a glance" are not drawn for now (their code stays; the guided walk has no step for them; the page checks that read them run only where they are drawn). Repaired the same day: a network whose flows are named udp and tcp writes `udp_bps` and `tcp_bps` like the two-host program, was taken for it, and three of a simulation's four charts over time stayed empty with a script error (s045, s047, s048) |
| 2026-11-22, later | At the operator's word: the board stays in view while turn by turn is read; the network drawn as a schema of its ns-3 objects with a "Made of" line; every call of the local model kept (`calls.jsonl`) and shown on the owner's page `agents.html` (`/api/agents`, the owner only); every reading of the tools stays in the researcher's ledger text and the supervisor is given the same readings. Also: the 11-18 harness fix of the supervised arm deployed. |
| 2026-11-22 | The lean page, three parts (the operator): the setting; what it needed to find out (the board, turn by turn folded); the detail of what is clicked, beside it and always in the window. Every other section is kept but not drawn (`EV.LEAN`; `?page=full` draws the page as it was). A long board stays readable (85 % at least, then it scrolls sideways in its card and says so); turn by turn in the narrower column puts a label above its value. Found and repaired while building it: a shorter detail made the page jump (95 px on s046) when the pane was taller than the board's column |
| 2026-11-22, evening | Deployed at 17:05 (the operator: "A, B and D, nothing else"): readings as evidence and two free turns (part 1); findings (A); the review of a test in rounds with the researcher's own rival (B); a guess restated once and then accepted, "not from what was learned" a warning (D). Not deployed: part 2 (measurement statistics, taps), part 3 (the short answer format), part C (shelved). See 8.3, and the branch review/harness-2026-11-22. |

The operator's plans, in the order they were followed: `~/RESTRUCTURE_PLAN.md`,
`~/CHECKS_AND_REPAIRS.md`, `EVIDENCE_VIEW.md`, `PAGE_REDESIGN.md` (these two
are in the repository), `~/VIEWS_DECISIONS.md`, `~/PAGE_POLISH.md`,
`OVERVIEW_REDESIGN.md`, `FORMAT_FIX.md`, `NOTEBOOK_VIEW.md`, `READABLE_PAGE.md` (the last four
beside this file in `~/project`, not in the repository).

## 17. Source files

Line counts on 2026-11-15. Many lines are long, in the viewer's JavaScript
above all, so the counts understate the size.

**Scenario (`ns-3.49/scratch/two-hosts/`, copied to `scratch/two-hosts/`)**

| File | Lines | What it is |
|---|---|---|
| `two-hosts.cc` | 501 | the scenario and its outputs |
| `link-queue-disc.cc` | 171 | the scheduler, both policies |
| `link-queue-disc.h` | 45 | its header |

**Harness (`harness/`)**

| File | Lines | What it is |
|---|---|---|
| `loop.py` | 624 | the loop: one session; the answer format from the brief; `trim` |
| `tools.py` | 260 | all the model can reach; the brief check; running simulations |
| `decision_rules.py` | 163 | reads and checks decision rules |
| `schema.json` | 423 | the answer format (its params object is put in by loop.py) |
| `prompt.txt` | 31 | the system prompt |
| `manifest.json` | 22 | outputs and tools, described |
| `control.py` | 565 | the operator's server |
| `session_figures.py` | 123 | figures counted from a session's records, for control.py's session rows; the void checks |
| `audit.py` | 88 | operator: the audit of a session's checks, verdicts, experiments and designs |
| `score.py` | 137 | operator: score a session |
| `export_session.py` | 70 | operator: export a session |
| `check_objects.py` | 207 | operator: the picture of the system against the scenario source |
| `make_trace.py` | 38 | operator: packet-event recordings |
| `move_drafts.py` | 33 | operator, used once: draft text out of old ledgers |

**Briefs (`briefs/`)**

| File | Lines | What it is |
|---|---|---|
| `two-hosts-open.json` | 26 | every knob, open goal |
| `two-hosts-udp-demand.json` | 33 | UDP rate fixed, given goal |

**The evidence page (`viewer/`)**

| File | Lines | What it is |
|---|---|---|
| `index.html` | 387 | the shell: colours, styles, the list of scripts |
| `evidence.js` | 188 | the address, loading, the top bar, clicks, replay, review marks |
| `evidence_data.js` | 179 | a session's files read into what the page draws; the definitions; derives the tests |
| `evidence_marks.js` | 61 | the drawn marks used all over the page; a result as its sign and its word; a claim's cited checks |
| `evidence_read.js` | 192 | decision rules and checks written for reading: plain names, the page's units, the exact text on hover |
| `evidence_notebook.js` | 121 | the notebook: one card of six lines per test under a heading per turn; the switch to the same tests as a list or as a tree |
| `evidence_home.js` | 70 | Home |
| `evidence_run.js` | 49 | the New session panel |
| `evidence_live.js` | 159 | a running session shown as it is made: the empty places, where the work is, the time, what just arrived, the quick reading; the note of a new turn; the reader's place |
| `evidence_tiles.js` | 121 | the simulations of the experiment being run (and of the newest one that ended), one tile each, read from the simulator's own files |
| `evidence_words.js` | 194 | the words that need explaining: their marks, and the box that opens beside them |
| `evidence_system.js` | 114 | "The system": the two computers with their ns-3 objects, and a card for the chosen object |
| `evidence_glance.js` | 125 | "What this session is made of": a column per turn, a row per kind of item, one mark per item |
| `evidence_page.js` | 134 | a session's page, top to bottom: the header strip, the Overview band, the card "The final report", the work |
| `evidence_high.js` | 62 | the key moments of a session, by fixed rules: marks on the notebook (once the card “Highlights”) |
| `evidence_best.js` | 82 | best so far |
| `evidence_random.js` | 74 | best so far against choosing at random from the sweep's first grid: the band, the sentence, the legend (operator columns) |
| `evidence_knob.js` | 96 | the simulations of each turn along one knob, one axis per turn; the target measure where one knob alone differs |
| `evidence_tree.js` | 55 | the work as a tree; the shared selection |
| `evidence_views.js` | 171 | View 1 (session flow) and View 2 (the board of "What it needed to find out": the hypotheses by turn and what each follows from) |
| `evidence_flow.js` | 109 | View 3 (one test as a flow chart) and its chart |
| `evidence_cards.js` | 126 | the trail, the work-log card, the brief; the model's numbers against the measurements |
| `evidence_test.js` | 73 | the test panel |
| `evidence_panels.js` | 102 | the experiment panel; the result panel of a simulation |
| `evidence_more.js` | 125 | summary, the tests list, the final report in full, the evidence sheet |
| `evidence_top.js` | 91 | the drawings of "How to read this page" |
| `evidence_verdicts.js` | 71 | verdicts against checks: the table of counts, in a session's summary and on Compare |
| `evidence_margin.js` | 39 | the margin of a check: how far it was from its decision rule; a part of each test's line in the tests list |
| `evidence_review.js` | 48 | the review queue and the sign-off |
| `evidence_operator.js` | 53 | the Operator tab: the score, the checklist and its judgements |
| `evidence_heat.js` | 64 | the sweep as a heat map: the colour range, the stretches of the axis, the session's simulations as marks |
| `evidence_oprun.js` | 78 | the operator's own simulation and sweep |
| `evidence_compare.js` | 67 | the Compare tab |
| `evidence_parallel.js` | 47 | the sweep as a parallel-coordinates chart |
| `evidence_share.js` | 56 | links, export, print |
| `objects.json` | 78 | the ns-3 objects of "The system" and what the scenario fixes about them (hand-kept; `check_objects.py` compares it with the scenario) |
| `brief_editor.js` | 562 | the set-up page, “New session”: the seven blocks as forms; a part's values as fields in its card; the bars of block 2 |
| `evidence_walk.js` | 61 | the guided walk: one sentence per section, from the records |
| `brief_editor_old.js` | 237 | the brief editor of the older control page (index_full.html) |

**Earlier pages and the ADRS adapter (`viewer/`)**

| File | Lines | What it is |
|---|---|---|
| `adrs_view.js` | 802 | the run page and the drawing of one simulation; also loaded by the evidence page and by the ADRS main viewer |
| `adrs_view.py` | 526 | the project as a task of the ADRS main viewer |
| `index_runs.html` | 114 | shell of the run page |
| `index_full.html` | 516 | the six-page viewer |
| `adrs_view_full.js` | 988 | its content |
| `index_old.html` | 99 | the first page |

**Other**

| File | Lines | What it is |
|---|---|---|
| `snapshot.sh` | 13 | refresh the copies and stage everything |
| `README.md` | 52 | what is where, for a reader of the repository |

57 files, 8,919 lines in all.
