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

**DECISION: draft text is not shown.** `drafts.jsonl` is never opened by the
viewer, the export, or anyone reporting on a session; the ledger keeps only a
draft's length and token count.

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
│   ├── schema.json               the answer format, enforced by the model server
│   ├── prompt.txt                the system prompt
│   ├── control.py                the operator's server, port 8600 (section 10)
│   ├── score.py                  operator: score a session against a sweep (10.4)
│   ├── export_session.py         operator: a session as a folder that opens offline (10.6)
│   ├── make_trace.py             operator: packet-event recordings (10.7)
│   ├── check_objects.py          operator: the picture of the system against the scenario source (6.4)
│   └── move_drafts.py            operator, used once: draft text out of old ledgers
├── sessions/<id>/                one session; ids s001, s002, ...
│   ├── session.json              what it was given, the flags, how it ended (8.8)
│   ├── ledger.jsonl              the record, append-only, written only by loop.py (8.7)
│   ├── drafts.jsonl              the text of each draft; never opened
│   ├── report.json               the final report as accepted
│   └── runs/
│       ├── index.json            this session's simulations: {id, params, metrics}, one per line
│       └── <run>/                params.json, metrics.json, series.csv, flowmon.xml (ids r001, ...)
├── checks/                       operator-only: no function of tools.py reads here
│   ├── operator.jsonl            {session, id, policy, seconds} per simulation, appended by loop.py
│   ├── build1/ ... build4/       the operator's checks of the simulator, by build (6.4)
│   ├── op-<time>/, control.jsonl operator simulations started from the page
│   ├── sessions/<id>.log         terminal output of a session started by control.py
│   ├── sweeps/<id>/              table.csv, status.json (10.2)
│   ├── keys/<brief>.json         answer key (10.3)
│   ├── scores/<session>.json     score; <session>.recommendation/ holds its one simulation (10.4)
│   ├── reviews/<session>.json    the reviewer's ticks, notes and sign-off (10.5)
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
  packet. Send and receive buffers are 1 MB.
- On node 0's device the root queue disc is `ns3::LinkQueueDisc` (6.2) with two
  child `FifoQueueDisc`s of `--queuePkts` packets each. The device's own queue
  is a 10-packet drop-tail, so queueing and drops happen in the queue disc,
  per band, where they are counted.
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
| `out` | (required) | the harness |
| `warmup` (1), `tcp` (on), `udpTos` (0x10), `pcap` (off), `events` (0), `eventsAt` (0) | | the operator only, by starting the program directly |

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

`params.json`: the nine brief options as the program used them.

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
begin at t = 2):

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

Build 4 is the current one. Both sweep tables (10.2) were made with it.

The eleven checks, as measured with build 3:

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

`harness/check_objects.py` is the twelfth thing to run after a change of the
scenario. The viewer's picture of the system (12.1) states values that the
scenario fixes in its source: the UDP packet size, the ports, the device's
queue, the TCP buffers, the scheduler's quantum, the start times. Nothing
updates them when the scenario changes. The check reads `two-hosts.cc` and
`link-queue-disc.cc` and compares them, value by value, with
`viewer/objects.json` and with the picture's script; it writes nothing and ends
with status 1 if a value differs or can no longer be read. On 2026-11-12: 42
values compared, 42 ok.

What checks 5a and 5b show: with short queues TCP's queue empties after a
loss, and under share UDP then gets more than its configured part. With Cubic
and queues of 8 or more this does not happen on a 50 us link, because Cubic
keeps 70% of its window after a loss.

## 7. Briefs

A session is started with a brief, `briefs/<id>.json`. It is the model's only
account of the system.

```
{ "id":          equals the file name
  "task":        the task text
  "description": the system in plain words; {name} is filled from "system"
  "system":      { setting: value }                      fixed for this brief
  "knobs":       { setting: {min, max, default, meaning} | {choices, default, meaning} }
  "goal":        {"kind": "open"}
               | {"kind": "given", "target": {"measure", "direction": "max"|"min"}, "conditions": ["udp_loss_frac <= 0.01", ...]}
  "limits":      {"simulations": 40, "simulations_per_experiment": 12} }
```

`tools.check_brief` is the one check, used by `loop.py` and `control.py`:

- every program option of the first nine rows of 6.1 is either fixed or a
  knob, never both;
- only `weightUdp`, `udpRate`, `queuePkts`, `tcpVariant`, `duration`, `seed`
  can be knobs (the answer format has no field for the others);
- values the program accepts; `min < max` with the default between; a meaning
  for every knob;
- a given goal needs a target that is one of the outputs and a list of
  conditions (it may be empty);
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

### 8.2 A turn

1. The ledger is rendered as text (8.7). If it is over 100,000 tokens, counted
   by the server's tokenizer, the session ends ("ledger too large").
2. A `turn` record is appended: simulations left, open hypotheses, the ids
   added since the previous turn, and whether this is a last turn.
3. The model is asked once. System message: `prompt.txt`. User message: the
   brief as JSON (with the descriptions of the outputs and the tools), the
   budget line, the ledger text, and the results of the tools it asked for in
   its previous answer. `schema.json` is passed as `response_format`
   (`json_schema`), so the reply is one JSON object of the answer format.
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
  "hypotheses":     [ {text, prediction, follows_from: [ids | "brief"]} ]
  "drop":           [ {id, why} ]
  "experiment":     { kind: "test"|"explore", tests: [H ids], question, varied: [knobs], control: label|null,
                      runs: [ {label, params: {knob: value}} ],
                      decision_rules: [ {for, decision_rule, rival, rival_predicts: "held"|"failed"} ] } | null
  "verdicts":       [ {for, result: "supported"|"refuted"|"inconclusive", because, next} ]
  "report":         { ... 8.6 ... } | null
  "requests":       [ {tool, args} ]
  "budget_request": {simulations, why} | null
  "done":           true | false }
```

`loop.sort_out` accepts or refuses each part on its own, in this order, and
the parts accepted earlier count for the later ones:

| Part | Accepted when |
|---|---|
| verdict | the hypothesis is open and one of its decision rules has been checked; it has a result and a because. It closes the hypothesis. |
| drop | the hypothesis is open, none of its decision rules has been checked, and there is a reason. A tested hypothesis cannot be dropped: it needs a verdict. |
| new hypothesis | it has a text and `follows_from`: ids of verdicts, checks, evidence tables or simulations that are in the ledger (a verdict accepted from this same answer counts, by the id it is about to get), or the word `brief`. It gets the next id `H<n>`, usable in the same answer. |
| experiment | see 8.5. At most one per turn. |
| budget request | a whole number of at least 1 and a reason. Granted up to the brief's limit, before this turn's experiment is counted. |
| report | see 8.6. Only together with `done`, and `done` only with a report. |

A refused part becomes a `note` by the harness ("refused part of the answer:
... Reason: ..."), with `part` and `reason` as fields, which the next turn's
ledger text shows; the rest of the answer is used. The whole answer is refused
(a `malformed` record, with `refused`: [{part, reason}] and the first 2,000
characters of the content) only when nothing in it can be used.

`observations` is kept once, in the first record the turn adds.

Tool requests: at most 3 per turn. Each is a `request` record and what came
back a `result` record; the model gets the results once, in the next turn, each
cut at 6,000 characters. A turn with requests only is a "tool-only" turn (a
`note` by the model); after more than 3 of them in a row the results are
withheld and the model is told to decide. In a last turn (8.8) requests are
not taken.

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

Accepted (`loop.experiment_problem`) when:

- it has 1 to `simulations_per_experiment` simulations, each with its own
  label (letters, digits and `_`, at most 20 characters);
- every `params` key is a setting of the brief;
- the new simulations it needs fit in the budget left;
- `control` is one of the labels or null, and `varied` names knobs;
- kind `test`: `tests` lists open hypotheses, with at least one decision rule
  for each and none for any other; every rule is readable and has its rival;
- kind `explore`: a question, no tests and no decision rules.

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

**A simulation is not run twice.** One with the same settings and seed as an
earlier one of the session (compared on every program option, rates by value),
or as another of the same experiment, is not run again: its record carries the
earlier result and `same_as`, a note says so, and it is not counted against the
budget.

The budget counts simulations actually run.

### 8.6 The final report

```
{ "goal":           the goal the answer is best for (open brief: the one the model chose, and why)
  "recommendation": {knob: value}
  "expected":       {output: number}
  "explanation", "holds_when", "breaks_when": texts
  "claims":         [ {text, evidence: [ledger ids]} ]
  "open_questions": [texts] }
```

`loop.check_report` refuses a report whose recommendation names a fixed setting
or something that is not a knob, or has a value outside its range; whose
`expected` is not numbers by output names; or whose claims cite an id that is
not in the ledger.

If a hypothesis with a checked decision rule still has no verdict, the report
is refused once, with the list, and the verdicts are asked for together with
the report; the second time it is accepted as it comes.

An accepted report is a `report` record (`R1`) and `sessions/<id>/report.json`,
and the session is over.

### 8.7 The ledger

One JSON object per line: `{id, turn, type, by, parent, body, ts}`. `by` says
who produced the content and is written by the harness, never taken from the
model's answer.

| Type | Id | By | Body | In the prompt |
|---|---|---|---|---|
| hypothesis | H | model | text, prediction, follows_from | yes, with its current state |
| drop | W | model | for, why | yes |
| experiment | X | model (X0: harness) | kind, tests, question, varied, control, runs [{label, params, clamped}], decision_rules | yes |
| simulation | S | simulator | label, run_id, params, metrics or error, same_as | no (the evidence has its line) |
| evidence | E | harness | experiment, lines | yes |
| check | C | harness | for, experiment, decision_rule, rival, rival_predicts, with_numbers, result | yes |
| verdict | V | model | for, result, because, next | yes |
| report | R | model | the report | yes |
| note | N | harness (tool-only turn: model) | text, and fields of its kind | yes |
| malformed | M | harness | error, refused, content | yes, the reason only |
| turn | U | harness | simulations_left, open_hypotheses, added, last_turn | no |
| request / result | Q / T | model / harness | tool, args / tool, result | no (given once, next turn) |
| draft | D | model | chars, tokens, model, finish_reason | no |

Ids count up per type. The prompt shows one line per record, each cut at 6,000
characters. No record type is the operator's: the brief and the scheduling
policy are theirs, and they are not ledger records.

Old formats, read but not written: `s001` has one simulation per experiment,
`pass_if` instead of decision rules, `scratch` records and no `by`; `s002` and
`s003` say `rules` / `rule`; sessions before `s008` have no `follows_from`, no
`turn` records and no structured refusals.

### 8.8 How a session ends, and `session.json`

| `how` | When |
|---|---|
| done by the model | the model set `done` with an accepted report |
| simulation limit reached | the budget was used up; one last turn follows in which no experiment is accepted and the report is required; the report was accepted |
| simulation limit reached, no usable report | that last turn brought none |
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

It must not describe the scheduling policy, how the scheduler works, TCP
backoff, or any expected result.

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
`run_many` forces each setting into the brief's ranges (`clamp`), starts the
built program with every option explicit (`options`: the fixed settings, the
knobs' defaults, then the chosen values) and `TWOHOSTS_SCHED` in its
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
| `GET /api/status` | what is running, the briefs, the sweeps, and `sessions`: one row per session (brief, counts, checks held and failed, how it ended, policy, running, and from `checks/` the score in short and the review) |
| `GET /api/sessions` | that list alone |
| `POST /api/session` | starts `loop.py` with the chosen flags: a new session, or with `session` a continued one. Up to 6 loops run side by side |
| `POST /api/stop` | `{session}`: stops a session started here |
| `POST /api/run` | `{params, policy, brief}`: one operator simulation into `checks/op-<time>/`, listed in `checks/control.jsonl` |
| `POST /api/sweep`, `GET /api/sweep/<id>`, `POST /api/sweep/<id>/stop` | 10.2 |
| `POST /api/review` | 10.5 |
| `POST /api/export` | 10.6 |
| `POST /api/brief` | saves a new brief after `tools.check_brief`; an existing id is refused |

**Policy "random".** `POST /api/session` with `policy: "random"`: the server
chooses share or cap, lists the session in `checks/random.json`, and leaves its
policy out of `/api/status` until the session has a score. The page takes the
policy only from `/api/status`.

**Who may call it.** The server listens on 127.0.0.1 only. The machine is
shared, so a POST is accepted only when the connection was opened by a process
of the user who runs the server (looked up in `/proc/net/tcp`; that user's SSH
tunnel counts), only as `application/json`, and only from the server's own
page.

An operator simulation is made by the built program directly, never by
`tools.run`, so it never reaches a session's folder.

### 10.2 Sweeps

`POST /api/sweep {brief, policy, grid: {knob: [values]}}` runs every
combination of the grid, at most 64 at a time, one sweep at a time, at most
5,000 simulations. `checks/sweeps/<id>/table.csv` has one row per simulation
(its number, the nine options, the outputs, seconds, error); `status.json` the
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
- the checklist, each item `yes`, `no` or `unjudged`. The operator judges
  (`--judge 2=yes`); judgements are kept when the score is written again.

For a brief with an open goal the operator enters the goal the report states
(`--target`, `--direction`, `--condition`). There is no answer key or sweep for
`two-hosts-open` yet, so its sessions cannot be scored.

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

## 11. Results so far

19 sessions, all with the same model. `s001` is from 2026-11-09; the others are
from 2026-11-11. "Gap" is the best row of the sweep minus the recommendation,
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

**The top bar is the same in every view** (**DECISION 2026-11-12**, after the
operator found that it changed when a session was chosen and repeated what
Home offered). It has two groups, always with all of their items, each at its
own place:

- **All sessions**: Home, Compare sessions.
- **One session**: the list of sessions, then that session's two pages,
  Session and Operator. The two wait, greyed, until a session is chosen.

On the right is the switch "show operator columns". A chosen session stays
chosen on Home and on Compare. Every destination has one place: nothing the
bar offers is repeated as a button in a page. The earlier pages are one quiet
line at the foot of every view.

| Place | What is there |
|---|---|
| Home | A title line with the one action that belongs there, New session; the results so far, one line per brief; the table of every session, sortable and filterable, a running one first, where a row opens its session |
| New session | Brief (or the brief editor), scheduling policy (share, cap, random), the flags, Start. While it runs: a banner with turn, simulations left and Stop; the page refreshes by itself |
| A session | Header strip (always visible); "The system"; "What this session is made of"; overview from the final report with its claims as chips; highlights; best so far; the work; the tests list; "How to read this page" |
| The work | The left side switches between Tree (turn, experiment, test, simulation; each row names its kind in words: "experiment X1", "test of H1", "simulation S2"), Session flow (three lanes: model, harness, simulator) and Hypothesis map (arrows from `follows_from`). One selection is shared by all three. Replay greys everything after the chosen step in all three |
| Detail pane | On the right, beside all of the above: the work-log card of a turn, the flow chart of one test, the result panel of a simulation, the chart of an experiment. A second tab holds the review queue and the sign-off |
| Operator tab | From `checks/` only: the policy, the sweep as a heat map with the session's simulations on it, the score, the checklist; "Run one simulation" and "Run a sweep" |
| Compare tab | Sessions of one brief with a tick each; two or more ticked are shown side by side: their best-so-far lines, a table, the first test that held; with operator columns on, the sweep as a parallel-coordinates chart with each recommendation as a bold line |
| Share | "Copy link" on every item; export; print (overview, highlights, best so far, tests list; or the evidence sheet of one claim) |

**"The system"** (`evidence_system.js`) is the first card of a session's page,
under the header strip: the two computers of the brief, each an outline that
holds its ns-3 objects in the order a packet passes them (applications,
internet stack, traffic control, net device), and the link between them.

- The objects and what the scenario fixes about them come from
  `viewer/objects.json` (hand-kept; `harness/check_objects.py` compares it with
  the scenario source, 6.4). The values come from the session: its brief's
  fixed settings and each knob's default, or the settings of the simulation
  the reader opened last; "show the brief's defaults" brings the defaults back.
- A setting the model may change is written in the model's colour.
- A click on an object shows it beside the picture, inside the card: its
  settings; for a knob, its range and the values this session tried; and what
  is measured there, with the opened simulation's values. The object chosen is
  not the session's selection: the item open in the detail pane stays open, and
  the page does not move.
- The scheduling policy is shown only with the operator columns on.
- The card folds, and the browser remembers it. It is not printed. During the
  replay it shows nothing recorded after the chosen step.

**"What this session is made of"** (`evidence_glance.js`) is the second card:
the whole session as one picture.

- A column per turn (and "start" for the harness's baseline); a row per kind
  of item: hypotheses, decision rules, simulations (under the name of their
  experiment), checks, verdicts, the final report. One mark per item, and each
  row's title gives the number of items.
- Down a column stand a hypothesis, its decision rule, the simulations of the
  turn's experiment, the check and the verdict: together one test.
- A hypothesis that stands a second time (tested in a later turn, or put to
  another decision rule) and a verdict that stands under a second decision
  rule are drawn hollow and counted once.
- A mark opens its item in the detail pane, and the page does not move.
  Pointing at a mark marks what belongs with it, and a sentence under the
  table says what it is.
- The marks shrink and wrap so that every turn fits the width of the page; a
  session with too many turns for that scrolls sideways inside the card, and
  the card says so.
- During the replay an item recorded after the chosen step is an empty dot,
  with no text, state or title; the key and the sentence under the table name
  only what is recorded by then.
- The card is not printed.

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

**The model's numbers against the measurements.** Where the model's text names
a measure with a number, or gives a number that equals a measured value of the
same experiment, the page shows both and marks agrees or differs.

Rules of the page:

- **A click never moves the page.** Whatever is chosen opens in the pane
  beside it. The one exception is the structure map's boxes, which scroll.
- One fixed colour per producer: model violet, harness magenta, simulator
  green, operator yellow. UDP is blue and TCP orange in every chart. Never two
  scales in one chart.
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
opened simulation's, and the scheduling policy stays operator-only).
`ev_replay.py` does not count an id that stands in words the model itself had
written by that step, such as "next: run X4".
Anything that starts, stops or writes is tried on a scratch copy of the project
on port 8611, never on the real sessions.

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
- Do not open, print or show `drafts.jsonl`.
- Do not invent a value for something that was not recorded.
- Do not overwrite a brief, rewrite an old session, or edit a ledger line.
- Do not change the ns-3 scenario without the operator's word; after a change,
  run the eleven checks and `check_objects.py` again, bring
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

## 16. History in short

| Date | What |
|---|---|
| 2026-11-09 | First build in five stages: scenario with the stock priority scheduler, the weighted scheduler with two behaviours, tools, the loop, a first viewer. Session s001: 12 turns, 5 experiments; 40% of the model's answers were cut off at 8,000 tokens. |
| 2026-11-10 | Simulator revised (build 2) after a review found TCP segments split in two and the seed without effect. Operator checks 1 to 4. The viewer grew to six pages; the control server replaced the plain file server; the project became a task of the ADRS main viewer. |
| 2026-11-11 | Scheduler renamed and the policy moved to an environment variable (build 3), after s001 showed the model reading the policy's name in the source. `RESTRUCTURE_PLAN.md` stages 1 to 5: sessions in their own folders; briefs; experiments of several simulations with decision rules checked by the harness; the final report; sweep, answer key and score. `CHECKS_AND_REPAIRS.md`: checks 5 to 11, and repairs B1 (loss cannot be negative, build 4), B2 (a tested hypothesis needs a verdict), B3 (draft text in its own file). Terms fixed: decision rule, scheduling policy. Rivals; simulations not run twice; answers taken part by part. `EVIDENCE_VIEW.md` and `PAGE_REDESIGN.md`: the evidence page (replacing stage 6). Sessions s002 to s019. The project became a public git repository. |
| 2026-11-12 | Stage 7: this document rewritten as a whole. The top bar made the same in every view. Two cards at the top of a session's page: "The system" and "What this session is made of". `check_objects.py`. |

The operator's plans, in the order they were followed: `~/RESTRUCTURE_PLAN.md`,
`~/CHECKS_AND_REPAIRS.md`, `EVIDENCE_VIEW.md`, `PAGE_REDESIGN.md` (the last two
are in the repository).

## 17. Source files

Line counts on 2026-11-12. Many lines are long, in the viewer's JavaScript
above all, so the counts understate the size.

**Scenario (`ns-3.49/scratch/two-hosts/`, copied to `scratch/two-hosts/`)**

| File | Lines | What it is |
|---|---|---|
| `two-hosts.cc` | 462 | the scenario and its outputs |
| `link-queue-disc.cc` | 171 | the scheduler, both policies |
| `link-queue-disc.h` | 45 | its header |

**Harness (`harness/`)**

| File | Lines | What it is |
|---|---|---|
| `loop.py` | 516 | the loop: one session |
| `tools.py` | 219 | all the model can reach; the brief check; running simulations |
| `decision_rules.py` | 148 | reads and checks decision rules |
| `schema.json` | 430 | the answer format |
| `prompt.txt` | 31 | the system prompt |
| `manifest.json` | 22 | outputs and tools, described |
| `control.py` | 529 | the operator's server |
| `score.py` | 126 | operator: score a session |
| `export_session.py` | 70 | operator: export a session |
| `check_objects.py` | 188 | operator: the picture of the system against the scenario source |
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
| `index.html` | 134 | the shell: colours, styles, the list of scripts |
| `evidence.js` | 163 | the address, loading, the top bar, clicks, replay, review marks |
| `evidence_data.js` | 162 | a session's files read into what the page draws; the definitions; derives the tests |
| `evidence_home.js` | 56 | Home |
| `evidence_run.js` | 75 | the New session panel; the banner of a running session |
| `evidence_system.js` | 92 | "The system": the two computers with their ns-3 objects, and a card for the chosen object |
| `evidence_glance.js` | 108 | "What this session is made of": a column per turn, a row per kind of item, one mark per item |
| `evidence_page.js` | 65 | a session's page, top to bottom |
| `evidence_high.js` | 57 | highlights |
| `evidence_best.js` | 76 | best so far |
| `evidence_tree.js` | 56 | the work as a tree; the shared selection |
| `evidence_views.js` | 80 | View 1 (session flow) and View 2 (hypothesis map) |
| `evidence_flow.js` | 96 | View 3 (one test as a flow chart) and its chart |
| `evidence_cards.js` | 101 | the trail, the work-log card, the brief; the model's numbers against the measurements |
| `evidence_test.js` | 43 | the test panel |
| `evidence_panels.js` | 96 | the experiment panel; the result panel of a simulation |
| `evidence_more.js` | 69 | summary, the tests list, the final report in full, the evidence sheet |
| `evidence_top.js` | 57 | the drawings of "How to read this page" |
| `evidence_review.js` | 48 | the review queue and the sign-off |
| `evidence_operator.js` | 68 | the Operator tab |
| `evidence_oprun.js` | 78 | the operator's own simulation and sweep |
| `evidence_compare.js` | 63 | the Compare tab |
| `evidence_parallel.js` | 47 | the sweep as a parallel-coordinates chart |
| `evidence_share.js` | 54 | links, export, print |
| `objects.json` | 77 | the ns-3 objects of "The system" and what the scenario fixes about them (hand-kept; `check_objects.py` compares it with the scenario) |
| `brief_editor.js` | 182 | the brief editor |

**Earlier pages and the ADRS adapter (`viewer/`)**

| File | Lines | What it is |
|---|---|---|
| `adrs_view.js` | 801 | the run page and the drawing of one simulation; also loaded by the evidence page and by the ADRS main viewer |
| `adrs_view.py` | 526 | the project as a task of the ADRS main viewer |
| `index_runs.html` | 114 | shell of the run page |
| `index_full.html` | 516 | the six-page viewer |
| `adrs_view_full.js` | 988 | its content |
| `index_old.html` | 99 | the first page |

**Other**

| File | Lines | What it is |
|---|---|---|
| `snapshot.sh` | 13 | refresh the copies and stage everything |
| `README.md` | 47 | what is where, for a reader of the repository |

51 files, 8,394 lines in all.
