"""The loop: rebuild the prompt from the ledger, ask the model once, do what its answer asks, append records.
One session = one folder, sessions/<id>/, and one brief (briefs/<id>.json, the assignment): session.json (what the
session was given), ledger.jsonl and drafts.jsonl are written here, runs/ by tools.run_many, and nothing in it is shared with another
session. The scheduling policy of each simulation (the operator's choice) goes to checks/operator.jsonl, outside that folder.

A turn's answer may state new hypotheses, drop hypotheses, give verdicts, and design ONE experiment: a set of
simulations with one purpose, run at once. An experiment that tests hypotheses carries decision rules, comparisons
stated before the simulations run, each with a rival explanation under which it would fail; the harness evaluates each
decision rule itself from the measured values (decision_rules.py) and records a check. A verdict is accepted only for a
hypothesis that has a checked decision rule. The budget counts simulations; a simulation with the same settings and seed
as one of an earlier experiment of the session is not run again.
The answer format (schema.json) gets its params object from the session's brief: every design states every knob. A plan
that cannot test anything is cut back before it runs (trim): a design that repeats another of the same experiment, a
decision rule that compares a simulation with itself, a knob listed as varied that does not vary.
Each turn's accepted answer is kept as received in sessions/<id>/answers.jsonl, which no tool reads.
A session ends with the model's final report: when the model sets done, or in one last turn after the budget is used
up. The accepted report goes to the ledger and to report.json; session.json records how the session ended.
Who else may write what: control.py's docstring."""
import argparse, json, os, re, signal, sys, time
from pathlib import Path
import requests
import decision_rules, network, tools

ROOT = Path.home() / "project"
H, OPERATOR, API = ROOT / "harness", ROOT / "checks/operator.jsonl", "http://127.0.0.1:18000/v1"
LEDGER = SID = None  # the current session's ledger and id, set in main()
CAP = 6000  # characters of any tool result or ledger body shown to the model
TOLERANCE = 1.0  # per cent: two results closer than this count as equal. The brief's goal may state its own (goal.tolerance); main() puts that here.
DEFAULT_TOLERANCE = 1.0  # what a brief that states none gets
LEDGER_TOKENS = 100_000  # the loop stops when the rendered ledger is larger than this
WAIT = "the report cannot be accepted yet: "   # said once per session; the answer after it is taken as it comes
NEED = WAIT + "a hypothesis that has a checked decision rule needs a verdict. Still without one: "
FREE_TURNS = 2  # once the budget is used up, this many more turns to look and to test on simulations already run, before the report-only turn (s048, 2026-11-22: the receiver-window guess needed only measurements of runs it had, and the last turn took only the report)
UNUSABLE = 3  # the loop stops after this many turns in a row without a usable answer (each turn is already two attempts)
PREFIX = {"why": "Y", "rethink": "K", "judge": "J", "hypothesis": "H", "drop": "W", "experiment": "X", "simulation": "S", "evidence": "E", "check": "C", "verdict": "V", "report": "R",
          "malformed": "M", "note": "N", "draft": "D", "request": "Q", "result": "T", "turn": "U", "review": "G", "objection": "O",
          "finding": "F", "decision": "A", "findings_end": "Z", "repair": "P"}   # findings (2026-11-22): a thing the results do not explain, the researcher's decision on one, the end tally
# who produced the content of a record, written into it as "by": the model (what it wrote), the simulator (what was
# measured), the harness (what it computed, found or decided itself), the operator (the person; no record type is theirs yet)
SOURCES = ("model", "harness", "simulator", "operator", "supervisor")   # supervisor: the second agent of the arm "supervised" (its reviews, and there the verdicts)
BY = {"draft": "model", "why": "model", "rethink": "model", "judge": "harness", "hypothesis": "model", "drop": "model", "experiment": "model", "verdict": "model", "report": "model",
      "simulation": "simulator", "evidence": "harness", "check": "harness", "malformed": "harness", "note": "harness", "request": "model", "result": "harness", "turn": "harness", "review": "supervisor", "objection": "model",
      "finding": "model", "decision": "model", "findings_end": "harness", "repair": "model"}
HIDDEN = ("draft", "scratch", "simulation", "request", "result", "turn", "judge", "finding", "decision", "findings_end")  # kept on disk, not replayed: what the model wrote before its answer, and the
                                             # simulation records (the evidence record has one line for each of them)
# ---- a brief with a network whose structure the model may change (TOPOLOGY.md, stage 5): a simulation may carry "structure", a list of changes
# against the brief's network (network.apply); it is then run on the changed network, which has measures of its own
def may_change(brief=None):
    b = brief or tools.describe_system()
    return bool(b.get("topology") and (b.get("structure") or {}).get("may_change"))


def edits_of(r, brief=None):
    """The changes a design asks for, as a list of plain objects with every field; none where the brief does not let the structure be changed."""
    return [{k: (e.get(k) or "") for k in network.EDIT} for e in (r.get("structure") or []) if isinstance(e, dict)] if may_change(brief) else []


def aim_measures(brief):
    """The measures the brief's aim is about: its target and those its conditions name. They must exist in every network that is simulated."""
    g, outs = brief.get("goal") or {}, tools.outputs(brief)
    if g.get("kind") != "given":
        return set()
    return {g["target"]["measure"]} | {m for c in g.get("conditions") or [] for m in outs if re.search(rf"\b{re.escape(m)}\b", c)}


def structure_problem(edits, brief=None, example=True):
    """None if the brief's network with these changes may be simulated; otherwise why not, ending with one change written correctly for this
    network (s053, 2026-11-22: H1's change was written wrongly in every round)."""
    b = brief or tools.describe_system()
    if not edits:
        return None
    try:
        t1 = network.apply(b["topology"], edits)
        bad = network.problems(t1) + network.changed_problems(b["topology"], t1, b.get("structure") or {}, b.get("goal") or {}, aim_measures(b))
    except (ValueError, KeyError, TypeError) as e:
        bad = [str(e)]
    if not bad:
        return None
    ok = change_example(b) if example else None
    return "; ".join(bad) + (f". A change written correctly for this network, for example: {json.dumps(ok)}" if ok else "")


def change_example(brief):
    """One network change written correctly for this brief, built and checked on its network: a list of changes, or None. The first that can be
    simulated of: a link's queue replaced by a scheduler (or by a fifo where it is a scheduler), a scheduler added on a link's side."""
    t = brief.get("topology")
    if not t or not (brief.get("structure") or {}).get("may_change"):
        return None
    blank = {k: "" for k in network.EDIT}
    tries = [[{**blank, "do": "remove", "kind": "queue", "id": l["id"], "on": h}, {**blank, "do": "add_queue", "kind": "fifo" if (q or {}).get("kind") == "scheduler" else "scheduler", "id": l["id"], "on": h}]
             for l, h, q, _ in network.queues(t)] + [[{**blank, "do": "add_queue", "kind": "scheduler", "id": l["id"], "on": h}] for l in t.get("links") or [] for h in l.get("between") or []]
    for edits in tries:
        if structure_problem(edits, brief, example=False) is None:
            return edits
    return None


MEASURES = {}   # the measurements the experiment in hand defines itself: {name: its definition}. Set when an answer's experiment is read (sort_out)
TWO_HOSTS_COLUMNS = (["udp_bps", "tcp_bps", "cwnd", "drops_band0", "drops_band1", "q_band0", "q_band1", "qmin_band0", "qmin_band1"],
                     ["udp_bps", "tcp_bps", "cwnd", "ssthresh", "inflight", "rwnd", "rtt_ms", "rto_ms", "wait_band0_ms", "wait_band1_ms", "q_band0", "q_band1", "devq"])   # what two-hosts records: its series, its probe


def outputs_of(edits, brief=None):
    """The measures of the brief's network with these changes made (the brief's own where there is none), and the measurements the experiment
    in hand defines itself: a decision rule and a need may name those like any measure."""
    b = brief or tools.describe_system()
    own = {n: f"your own measurement: {m['stat']} of {m['of']}" + (f" with {m['with']}" if m.get("with") else "") for n, m in MEASURES.items()}
    return {**(network.outputs(network.apply(b["topology"], edits)) if edits else tools.outputs(b)), **own}


def measurement_problem(ex, brief):
    """None if the measurements an experiment defines can be made; otherwise what is wrong (2026-11-18, the operator: the researcher comes up with
    the measurements it needs, the simulator produces them, and it cannot change what a simulation gives). A measurement is a name, a column of
    what a simulation records over time or arithmetic over columns (of), a statistic (stat), a window in seconds, and a level where the statistic
    compares with one. The simulations of such an experiment are run with the program's probe, which only listens."""
    import ast
    ms = ex.get("measurements")
    if ms in (None, []):
        return None
    if not isinstance(ms, list) or not all(isinstance(m, dict) for m in ms) or len(ms) > 8:
        return "measurements is a list of at most 8, each with name, of, stat, t_from, t_to, level and with"
    def cols_of(r):   # what one design records, on its own network (the coherence audit, 2026-11-22: the brief's network was used)
        if not brief.get("topology"):
            return TWO_HOSTS_COLUMNS
        e = edits_of(r, brief) if isinstance(r, dict) else []
        if e and structure_problem(e, brief):
            return None   # a change that cannot be made: experiment_problem refuses it with its own reason
        try:
            return network.record_columns(network.apply(brief["topology"], e) if e else brief["topology"])
        except (ValueError, KeyError, TypeError):
            return None
    designs = [(r.get("label"), cols_of(r)) for r in ex.get("runs") or [] if isinstance(r, dict)]
    designs = [(l, c) for l, c in designs if c] or [("the brief's network", network.record_columns(brief["topology"]) if brief.get("topology") else TWO_HOSTS_COLUMNS)]
    series, fine = designs[0][1]
    outs, seen = tools.outputs(brief), set()
    for r in ex.get("runs") or []:   # the names of the outputs of every design's network, which a measurement may not take
        if isinstance(r, dict) and edits_of(r, brief) and not structure_problem(edits_of(r, brief), brief):
            try:
                outs = {**outs, **network.outputs(network.apply(brief["topology"], edits_of(r, brief)))}
            except (ValueError, KeyError, TypeError):
                pass
    for m in ms:
        n = m.get("name")
        if not (isinstance(n, str) and re.fullmatch(r"[a-z][a-z0-9_]{1,30}", n)) or n in outs or n in seen:
            return f"a measurement needs a name of its own: 2 to 31 lower-case letters, digits and _, beginning with a letter, not the name of an output and not used twice ({n!r})"
        seen.add(n)
        if m.get("stat") not in tools.MEASURE_STATS:
            return f"measurement {n}: stat must be one of {', '.join(tools.MEASURE_STATS)}"
        if m["stat"] in ("time_above", "time_below", "first_time_above", "first_time_below", "crossings") and type(m.get("level")) not in (int, float):
            return f"measurement {n}: {m['stat']} needs level, the number to compare with"
        if m["stat"] in ("corr", "lag") and not (isinstance(m.get("with"), str) and m["with"].strip()):   # how two things go together (2026-11-22)
            return f"measurement {n}: {m['stat']} needs with, the second column or arithmetic over columns it is compared with"
        if any(m.get(k) is not None and type(m.get(k)) not in (int, float) for k in ("t_from", "t_to")) or (type(m.get("t_from")) in (int, float) and type(m.get("t_to")) in (int, float) and m["t_to"] <= m["t_from"]):
            return f"measurement {n}: t_from and t_to are seconds of the simulation (or null: the measured seconds), t_from before t_to"
        try:
            used = {x.id for e in [m.get("of")] + ([m["with"]] if m.get("with") else []) for x in ast.walk(ast.parse(str(e), mode="eval")) if isinstance(x, ast.Name)} - {"abs", "min", "max"}
        except SyntaxError:
            used = None
        lacking = [(l, c) for l, c in designs if not used or not (used <= set(c[0]) or used <= set(c[1]))]
        if lacking:
            l, (series, fine) = lacking[0]
            return (f"measurement {n}: of must be a column a simulation records, or arithmetic over columns of one record" + (f", in every design: design {l} does not record it" if len(designs) > 1 and len(lacking) < len(designs) else "")
                    + f". What {l if len(designs) > 1 or l != designs[0][0] else 'a simulation'} records: the series (every 0.1 s): {', '.join(series)}. "
                    f"The probe (every {tools.PROBE_EVERY} s; it only listens): {', '.join(fine)}")
    return None


def design_key(clean, edits):
    """What makes two designs the same simulation: the same settings and seed, on the same network."""
    return (tools.same(tools.options(clean)), json.dumps(edits, sort_keys=True))


def edits_say(edits):
    """A list of changes in a few words, for an evidence line."""
    one = lambda e: (f"+host {e['id']}" if e["do"] == "add_host" else f"+link {e['id']} {e['from']}-{e['to']}" if e["do"] == "add_link" else f"+{e['kind']} flow {e['id']} {e['from']}>{e['to']}" + (" at a constant rate" if e.get("app") == "onoff" and e["kind"] == "tcp" else "") if e["do"] == "add_flow"
                     else f"+{e['kind'] or 'scheduler'} on {e['on']}'s side of {e['id']}" if e["do"] == "add_queue" else f"-{e['kind']} {e['id']}" + (f" ({e['on']}'s side)" if e.get("kind") == "queue" and e.get("on") else ""))
    return ", ".join(one(e) for e in edits)


STRUCTURE = """

In this session you may also change the structure of the network. A simulation of an experiment carries structure: a list of changes made, in order, to the network of the brief (always to the brief's network, never to that of an earlier simulation); an empty list runs the network as it is. A change states every field (do, id, kind, from, to, on, rate, type, app), with "" where one does not apply:
   - do add_host: id, a new name (at most 12 lower-case letters and digits, beginning with a letter).
   - do add_link: id, from and to (the two hosts it joins), rate (for example 1Gbps). One link for each two hosts.
   - do add_flow: id, kind (udp or tcp: the socket), from, to, and rate for udp (for example 100Mbps) or type for tcp (for example TcpCubic). app is the application that sends: "" for the usual one (udp: packets at a constant rate; tcp: always has data, as fast as TCP accepts), or onoff with kind tcp for a TCP flow that sends at the constant rate you state in rate. A flow needs one shortest way from its sender to its receiver.
   - do add_queue: id (the link), on (the host whose sending side of the link it is), kind (scheduler, fifo, or another of ns-3's queue discs: pfifofast, codel, fqcodel, red, pie). A scheduler gives each flow that passes it a part of the link; fifo is one queue for all, first in, first out. A link may have a queue on each of its two sides.
   - do remove: kind (host, link, flow or queue) and id (a queue's id is its link's; where the link has a queue on each side, on says which). A host goes with its links and with the flows that start or end at it.
The brief's structure says how many hosts, links and flows a network may have at most, and which objects you may not remove; what the goal measures cannot be removed either. A simulation whose network cannot be built is refused with the reason, and the rest of the experiment is not run. A changed network has measures of its own (a new flow f has f_goodput_bps, and so on, as the brief's outputs are named); a decision rule may only name a measure that exists in every simulation it names. A change of structure is a hypothesis like any other: say what it should change and why, before you run it. In the final report, structure is the list of changes you recommend (an empty list: the network as given), and the settings and expected values are read on that network."""


def spend_cap(left, per):
    """The most new simulations one experiment may run when `left` are left: half of them (rounded up), and never more than the
    brief allows in one experiment. Until 2026-11-17 an experiment could take all that was left, and a session often spent three
    experiments of the largest size and had three simulations for the comparison that decided its answer (s012: 12, 12, 12, 3, 1)."""
    return max(1, min(per, (left + 1) // 2))


def needs_problem(ex, brief, planned, full=True):
    """None if a test's needs tie each tested hypothesis to simulations that can decide it; otherwise what is wrong (2026-11-17, the
    operator: "after the AI formed a hypothesis, it clearly chooses what it needs to know and subsequently forms simulations").
    For each tested hypothesis one need: what must be known, the one knob that differs between the simulations made for it, the
    measure that decides it, those simulations. Checked here: the simulations of a need differ in that knob and in nothing else;
    the hypothesis's decision rules name only those simulations and that measure; every simulation is made for some hypothesis.
    planned: plan()'s rows of the experiment's designs (their clamped settings and their changes of structure).
    full False: the experiment as it was sent, before trim(): only that each need is there and readable. What its simulations
    differ in, what its rules name and whether a simulation serves no hypothesis are judged on what trim() leaves, like the budget."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    tests, needs, rules = ex.get("tests") or [], ex.get("needs"), ex.get("decision_rules") or []
    row = {r["label"]: r for r in planned}
    if not isinstance(needs, list) or sorted(n.get("for") for n in needs if isinstance(n, dict)) != sorted(tests) or len(needs) != len(tests):
        return "a test experiment needs one entry in needs for each hypothesis it tests (for: the hypothesis), written before the simulations: what you must know to decide it"
    used = set()
    for n in needs:
        h, sims, varies = n["for"], n.get("simulations"), n.get("varies")
        if n.get("derived") and not text(n.get("measure")):   # a need the harness derived from the rules (the short reply): its rule names no measure the harness can read
            return f"the decision rule for {h} names no measure: write it as measure@label, for example an output or a measurement of your own in the simulation with that label"
        if not n.get("derived") and (not text(n.get("to_know")) or not text(n.get("measure"))):
            return f"the need of {h} must say to_know (what you must know to decide {h}, in one sentence) and measure (the output that decides it)"
        if not isinstance(sims, list) or not sims or len(set(sims)) != len(sims) or set(sims) - set(row):
            return f"the need of {h} must list its simulations: labels of this experiment's designs, each once"
        if varies not in (*brief["knobs"], "none", *(["structure"] if may_change(brief) else [])):
            return f"the need of {h}: varies must be a knob of the brief, or none (a single simulation against a number you state)"
        if not full:
            continue
        differ = sorted({k for a in sims for b in sims for k in brief["knobs"] if row[a]["params"].get(k) != row[b]["params"].get(k)})
        other_net = any(row[a]["structure"] != row[b]["structure"] for a in sims for b in sims)
        if varies == "none":
            if len(sims) != 1:
                return f"the need of {h} says nothing varies, so it is decided by one simulation against a number; it lists {len(sims)}. Name the knob that varies between them, or keep one"
        elif len(sims) < 2:
            return f"the need of {h} says `{varies}` varies but lists one simulation: a comparison needs at least two that differ in `{varies}`"
        elif varies == "structure":
            if differ or not other_net:
                return (f"the need of {h} says the structure varies, but its simulations " + (f"also differ in {', '.join(differ)}" if differ else "all have the same structure")
                        + ": make them differ in the structure and in nothing else")
        else:
            if differ != [varies] or other_net:
                extra = [k for k in differ if k != varies] + (["the structure"] if other_net else [])
                return (f"the need of {h} says its simulations differ only in `{varies}`, but they " + (f"also differ in {', '.join(extra)}" if extra else f"all have the same `{varies}`")
                        + f": change the designs so that `{varies}` alone differs between them (a difference in the measure then has one possible cause), or test that in another hypothesis")
        outs = {k: v for r in planned for k, v in outputs_of(r["structure"], brief).items()}
        for d in rules:
            if d.get("for") != h:
                continue
            try:
                named = decision_rules.pairs(d.get("decision_rule"), outs, list(row))
            except decision_rules.DecisionRuleError:
                continue   # said by the check of the rule itself
            stray = sorted({l for _, l in named} - set(sims))
            if stray:
                return f"the decision rule for {h} names `{stray[0]}`, which is not one of the simulations its need lists ({', '.join(sims)}): a rule is decided by the simulations made for its hypothesis"
            if n["measure"] not in {m for m, _ in named}:
                return f"the decision rule for {h} does not name `{n['measure']}`, the measure its need says decides it"
        used |= set(sims)
    idle = [l for l in row if l not in used] if full else []
    if idle:
        return (f"simulation `{idle[0]}` is made for no hypothesis: no need lists it" + (f" (nor {', '.join('`' + l + '`' for l in idle[1:4])})" if idle[1:] else "")
                + ". Run only what a hypothesis needs: remove it, or say which hypothesis needs it and why")
    return None


def evidence_measures():
    """The measures of an evidence line: the session's, without the two of two-hosts that only repeat a setting."""
    return [k for k in tools.outputs() if k not in ("link_rate_bps", "weight_udp")]

def load_ledger():
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()] if LEDGER.exists() else []

def append(ledger, turn, type_, parent, body, rid=None, by=None):
    """One more record. Ids count up per type (H1, X1, S1, E1, C1, ...); the harness's own first experiment is X0, S0, E0."""
    rec = {"id": rid or f"{PREFIX[type_]}{sum(r['type'] == type_ and r['id'] not in ('X0', 'S0', 'E0') for r in ledger) + 1}", "turn": turn, "type": type_,
           "by": by or BY[type_], "parent": parent, "body": body, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    assert rec["by"] in SOURCES, rec["by"]
    with LEDGER.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    ledger.append(rec)
    return rec["id"]

def states(ledger):
    """Every hypothesis's state (open, or its verdict's result, or dropped), and the hypotheses that have a checked decision rule."""
    st = {r["id"]: "open" for r in ledger if r["type"] == "hypothesis"}
    for r in ledger:
        if r["type"] == "verdict":
            st[r["body"]["for"]] = r["body"]["result"]
        elif r["type"] == "drop":
            st[r["body"]["for"]] = "dropped"
    return st, {r["body"]["for"] for r in ledger if r["type"] == "check" and r["body"]["result"] in ("held", "failed")}

def why_states(ledger):
    """Every why's standing now: {id: {"worth": verify | set_aside | refuted | revised, "at": the place in the ledger of the record that last settled
    it, "as": the why that revised it}}. A why is not fixed by how it was first stated (2026-11-17, the operator: "I want the cause and effect in the
    stages of the chain strong and grounded by whys, but I don't want it fixed by the initially formed whys"): a rethink changes its standing, and a
    later why may revise it."""
    out = {}
    for i, r in enumerate(ledger):
        b = r["body"]
        if r["type"] == "why":
            out[r["id"]] = {"worth": b["worth"], "at": i}
            if b.get("revises") in out and b["revises"] != r["id"]:
                out[b["revises"]] = {"worth": "revised", "at": i, "as": r["id"]}
        elif r["type"] == "rethink" and b.get("for") in out:
            out[b["for"]] = {"worth": b["now"], "at": i}
    return out


def tested_whys(ledger):
    """The guesses that were just tested and not yet looked at again: {why: ["H4: C4 held", ...]}. A why is in it when it is still marked
    verify and a decision rule of a hypothesis that comes from it was checked after the why was last settled (stated, rethought or replaced).
    This is the review of the step from one hypothesis to the next (2026-11-17, the operator: "the most significant upgrade"; s042, turn 3: the
    model's three rethinks named K4, K5, K6 instead of the whys, were refused, and it went on to new hypotheses without the review)."""
    ws, from_why, out = why_states(ledger), {r["id"]: r["body"].get("from_why") for r in ledger if r["type"] == "hypothesis"}, {}
    for i, r in enumerate(ledger):
        y = from_why.get(r["body"].get("for")) if r["type"] == "check" else None
        if y in ws and ws[y]["worth"] == "verify" and i > ws[y]["at"]:
            out.setdefault(y, []).append(f"{r['body']['for']}: {r['id']} {r['body']['result']}")
    return out


def look_again(due):
    """The words for the guesses that are due: Y4 (H4: C4 held; H5: C5 failed), Y5 (H6: C6 held)."""
    return ", ".join(f"{y} ({'; '.join(v)})" for y, v in sorted(due.items(), key=lambda q: int(q[0][1:])))


def since(ledger, at, readings=False):
    """The results recorded after place `at` of the ledger: ids of evidence tables, checks and verdicts; with readings, also what the tools
    returned (T). A rethink may rest on a reading (s048, 2026-11-22: the rethink of Y11 in the light of r010's measurements T10 to T12 was refused,
    note N2, because readings did not count). A reading is new to a why when its request was made in the turn the why was settled or later: what a
    turn's requests return is seen only in the next turn, though it stands before that turn's whys in the ledger (s048: T10 to T12 were asked for in
    turn 5 with Y11 and seen in turn 6). A reading alone does not make a why due for a rethink: that stays with results (readings=False)."""
    t0 = ledger[at]["turn"] if 0 <= at < len(ledger) else -1
    return [r["id"] for i, r in enumerate(ledger) if (i > at and r["type"] in ("evidence", "check", "verdict")) or (readings and r["type"] == "result" and (i > at or r["turn"] >= t0))]


STANDING = {"verify": "worth verifying", "set_aside": "set aside", "refuted": "refuted", "supported": "supported", "revised": "revised"}


def plan(ledger, runs, complete=True):
    """Each simulation an experiment asks for: its clamped params, and whether it has to be run. A simulation with the same
    settings and seed as an earlier one of the session ("prior": that simulation record), or as an earlier one of the same
    experiment ("twin": that one's label), is not run again. complete: each design must state every knob of the brief
    (tools.Missing otherwise); only the harness's own baseline, whose design is empty, is planned without that."""
    out = []
    for r in runs:
        clean, clamps = tools.clamp(r.get("params") or {}, design=r["label"] if complete else None)
        edits = edits_of(r)
        key = design_key(clean, edits)
        prior = next((q for q in ledger if q["type"] == "simulation" and "metrics" in q["body"] and not q["body"].get("same_as")
                      and (tools.same(q["body"]["params"]), json.dumps(q["body"].get("structure") or [], sort_keys=True)) == key), None)
        out.append({"label": r["label"], "params": clean, "clamped": clamps, "structure": edits, "key": key, "prior": prior, "twin": None if prior else next((q["label"] for q in out if q["key"] == key), None)})
    return out

def decided_by_little(rule, labels, values, ledger):
    """The comparisons of a decision rule that were decided by less than the tolerance: [{left, op, right, percent}]. A comparison of two results
    whose sides differ by less than the tolerance is decided by nothing: its two sides count as equal. The check keeps the result the rule gives
    (held or failed) and says beside it which comparisons were that close, so that the model, and a reader, do not take a difference of a few
    hundredths of a per cent for a finding (s031: three checks rested on differences of 0.02 %; of the 459 checks of s001 to s031, 75 compared two different simulations less than 1 % apart).
    Two results: both sides measured, or one side measured and the other a number that is an earlier result of this session written out (the
    model often copies a result into a later rule as a number). A number the rule states of its own (a limit, a margin) is not a result."""
    earlier = {v for q in ledger if q["type"] == "simulation" for v in (q["body"].get("metrics") or {}).values() if type(v) in (int, float) and v}
    results = lambda kinds, a, b: kinds == ("measured", "measured") or (kinds == ("measured", "number") and b in earlier) or (kinds == ("number", "measured") and a in earlier)
    return [{"left": a, "op": op, "right": b, "percent": round(100 * abs(a - b) / max(abs(a), abs(b)), 6)}
            for a, op, b, kinds in decision_rules.comparisons(rule, {**tools.outputs(), **{k: "" for v in values.values() for k in v}}, labels, values)
            if results(kinds, a, b) and op != "==" and max(abs(a), abs(b)) > 0 and 100 * abs(a - b) / max(abs(a), abs(b)) < TOLERANCE]

def experiment(ledger, turn, parent, ex, zero=False):
    """What the harness does with an experiment: record the design and the decision rules as stated; run at once all its
    simulations that have not been run before in this session (one simulation record each, a note for each one reused);
    one evidence record, a line per simulation; then one check record per decision rule. Returns how many were run."""
    brief = tools.describe_system()
    runs, stated = plan(ledger, ex["runs"], complete=not zero), ex.get("decision_rules") or []
    own = [m for m in ex.get("measurements") or [] if isinstance(m, dict) and m.get("name") in MEASURES] if not zero else []   # the measurements this experiment defines itself
    xid = append(ledger, turn, "experiment", parent, {"kind": ex["kind"], "tests": ex.get("tests") or [], "question": ex.get("question") or "", "varied": ex.get("varied") or [],
                                                      "control": ex.get("control") or None, "runs": [{k: r[k] for k in ("label", "params", "clamped") + (("structure",) if r["structure"] else ())} for r in runs], "decision_rules": stated,
                                                      **({"needs": ex["needs"]} if ex.get("needs") else {}), **({"measurements": own} if own else {}),
                                                      **({"observations": ex["observations"]} if ex.get("observations") else {})},
                 rid="X0" if zero else None, by="harness" if zero else None)
    fresh = [r for r in runs if not r["prior"] and not r["twin"]]
    stage("sims", xid)
    results = dict(zip((r["label"] for r in fresh), tools.run_many([r["params"] for r in fresh], [r["structure"] for r in fresh], probe=tools.PROBE_EVERY if own else None)))
    def measured(run_id):
        """The experiment's own measurements of one simulation: {name: value}. A simulation that ran earlier has no finer record yet: the harness
        runs it again with the probe, and uses that record only if the result is the same."""
        out = {}
        if own and "probe.csv" not in [p.name for p in tools._dir(run_id).iterdir()]:
            try:   # one that fails gives no finer record: its measurements are left out, and its rules say "not checked" (the coherence audit, 2026-11-22)
                said = tools.probe(run_id)
            except Exception as e:
                said = f"error: {type(e).__name__}"
            if said.startswith("error"):
                return {}
        for m in own:
            try:   # each measurement on its own: one that fails leaves the others (the coherence audit, 2026-11-22)
                said = tools.measure(run_id, m["of"], m["stat"], m.get("t_from"), m.get("t_to"), m.get("level"), **({"with": m["with"]} if m.get("with") else {}))
            except Exception as e:
                said = f"error: {type(e).__name__}"
            v = json.loads(said).get("value") if said.startswith("{") else None
            if v is not None:
                out[m["name"]] = v
        return out
    OPERATOR.parent.mkdir(parents=True, exist_ok=True)
    with OPERATOR.open("a") as f:  # the operator's line of each simulation run: session, run, scheduling policy, seconds. No tool reads that file
        for res in results.values():
            f.write(json.dumps({"session": SID, "id": res["id"], "policy": tools.POLICY, "seconds": res["seconds"]}) + "\n")
    values, lines, made = {}, [], {}  # made: label -> the simulation record that holds its result
    for r in runs:
        changed = ", ".join(f"{k}={v}" for k, v in r["params"].items() if v != brief["knobs"][k]["default"]) or "defaults"
        if r["structure"]:
            changed += f"; structure: {edits_say(r['structure'])}"
        first = r["prior"] or made.get(r["twin"])  # the earlier simulation with the same settings and seed, if any
        if first and "metrics" in first["body"]:
            body = {"label": r["label"], "run_id": first["body"]["run_id"], "params": first["body"]["params"], "metrics": first["body"]["metrics"], "same_as": first["id"],
                    **({k: first["body"][k] for k in ("structure", "topology") if k in first["body"]})}
        else:
            res = results.get(r["label"]) or results[r["twin"]]  # (a twin of a simulation that failed shares its failure)
            body = {"label": r["label"], "run_id": res["id"], "params": res.get("used") or r["params"], **({"metrics": res["metrics"]} if "metrics" in res else {"error": res["error"]}),
                    **({"structure": r["structure"], "topology": res["topology"]} if r["structure"] and "topology" in res else {})}   # a simulation on a changed network: the changes, and the network it was run on
        if own and "metrics" in body:
            if (results.get(r["label"]) or {}).get("probe_same") is False:   # the simulation without the probe gave another result: its finer record is not used
                body["probe"] = "not used: the same simulation run without the probe gave another result"
            else:
                try:   # a measurement that fails is left out with its reason: it never stops the session after its simulations ran (the coherence audit, 2026-11-22)
                    mine = measured(body["run_id"])
                except Exception as e:
                    mine, body["measured_error"] = {}, f"{type(e).__name__}: {' '.join(str(e).split())[:200]}"
                body["metrics"], body["own"] = {**body["metrics"], **mine}, sorted(mine)   # own: which of its measures the experiment defined itself
        sid = append(ledger, turn, "simulation", xid, body, rid="S0" if zero else None)
        made[r["label"]] = ledger[-1]
        if "same_as" in body:
            append(ledger, turn, "note", sid, {"text": f"simulation {r['label']} of {xid} has the same settings and seed as {first['id']} (run {body['run_id']}): the earlier result is returned, "
                                                       "nothing was run again, and it is not counted against the budget", "simulation": sid, "same_as": first["id"]})
        if "metrics" in body:
            values[r["label"]] = body["metrics"]
            lines.append(f"{r['label']} {body['run_id']} {changed} | " + " ".join(f"{k}={body['metrics'][k]}" for k in (body["metrics"] if "structure" in body else evidence_measures() + list(body.get("own") or [])) if k in body["metrics"])
                         + (f" (the result of {first['id']}: same settings and seed, not run again)" if "same_as" in body else ""))
        else:
            lines.append(f"{r['label']} {body['run_id']} {changed} | FAILED: {' '.join(body['error'].split())[:300]}")
    append(ledger, turn, "evidence", xid, {"experiment": xid, "lines": lines}, rid="E0" if zero else None)
    stage("checks", xid)
    labels = [r["label"] for r in runs]
    for d in stated:
        try:
            held, numbers = decision_rules.check(d["decision_rule"], {**tools.outputs(), **{k: "" for v in values.values() for k in v}}, labels, values)   # a changed network's own measures count too
            result = "held" if held else "failed"
            close = decided_by_little(d["decision_rule"], labels, values, ledger)
        except Exception as e:  # it was readable (validate), so: a simulation it names gave no value; anything else is "not checked" with its reason (the coherence audit, 2026-11-22)
            result, numbers, close = "not checked", str(e), []
        append(ledger, turn, "check", xid, {"for": d["for"], "experiment": xid, "decision_rule": d["decision_rule"], "rival": d.get("rival"), "rival_predicts": d.get("rival_predicts"),
                                            "with_numbers": numbers, "result": result, **({"tolerance": TOLERANCE, "within_tolerance": close} if close else {})})
    return len(fresh)

def baseline(ledger):
    """Before turn 1 of a new ledger: the harness's own experiment X0, one simulation with every setting at its default
    (turn 0, not counted in the budget), so the model's first turn starts from an observed record."""
    if not ledger:
        experiment(ledger, 0, None, {"kind": "explore", "question": "what the system does with every setting at its default (run by the harness before turn 1)",
                                     "runs": [{"label": "default", "params": {}}]}, zero=True)

def shown(r, st):
    """One record's body as the prompt shows it. The full body stays in ledger.jsonl."""
    b, t, flat = r["body"], r["type"], lambda v: " ".join(str(v).split())
    if t == "why":
        w = st.get(r["id"]) if isinstance(st.get(r["id"]), dict) else {"worth": b["worth"]}   # its standing now, which a rethink or a later why may have changed
        now = STANDING[w["worth"]] + (f" as {w['as']}" if w.get("as") else "") + (f"; stated before the results of {', '.join(w['stale'][:3])}: rethink it before a new hypothesis comes from it" if w.get("stale") else "") + ("; no hypothesis has come from it yet" if w.get("idle") else "")
        return (f"[{now}] " + (f"revises {b['revises']}: " if b.get("revises") else "") + f"about {', '.join(b['about'])}: {flat(b['result'])} | guess: {flat(b['guess'])}"
                + (f" | not visible: {flat(b['unseen'])}" if b.get("unseen") else "") + (f" | for the goal: {flat(b['matters'])}" if b.get("matters") else "") + (f" | {flat(b['reason'])}" if b.get("reason") else "")
                + (f" [restated in the same turn: first not accepted by the {b['restated'].get('by')}: {flat(b['restated'].get('reason'))[:240]}" + (f"; accepted as contested: {flat('; '.join(b['contested']))[:240]}" if b.get("contested") else "") + "]" if b.get("restated") else ""))   # 2026-11-22
    if t == "rethink":
        return f"of {b['for']} in the light of {', '.join(b['in_light_of'])}: now {STANDING[b['now']]}. {flat(b['because'])}"
    if t == "hypothesis":
        return (f"({st.get(r['id'], 'open')}) " + (f"from {b['from_why']}: " if b.get("from_why") else "") + f"{flat(b['text'])}" + (f" | prediction: {flat(b['prediction'])}" if b.get("prediction") else "")
                + (f" | its question: {flat(b['question'])}" if b.get("question") else "") + (f" | why it matters: {flat(b['why'])}" if b.get("why") else ""))   # all it stated (2026-11-22)
    if t == "drop":
        return f"{b['for']}: {flat(b['why'])}"
    if t == "experiment":
        sims = "; ".join(f"{x['label']} {{{', '.join(f'{k}={v}' for k, v in x['params'].items()) or 'defaults'}}}"
                         + ("".join(f" [{k}: asked {a}, used {u}]" for k, (a, u) in x["clamped"].items())) for x in b["runs"])
        return ((f"test of {', '.join(b['tests'])}" + (f" | its question: {flat(b['question'])}" if b.get("question") else "") if b["kind"] == "test" else f"explore: {flat(b['question'])}") + (f" | varied: {', '.join(b['varied'])}" if b["varied"] else "")
                + (f" | control: {b['control']}" if b["control"] else "") + f" | simulations: {sims}"
                + "".join(f" | decision rule for {x['for']}: {flat(x.get('decision_rule', x.get('rule')))}" + (f" (rival: {flat(x['rival'])})" if x.get("rival") else "")
                          for x in b.get("decision_rules", b.get("rules", []))))
    if t == "evidence":
        return f"of {b['experiment']}, one line per simulation (label, run id, settings changed from the defaults | measured):\n" + "\n".join("    " + l for l in b["lines"])
    if t == "check":
        # the rival stands with the result: a rule that FAILED came out as the rival explanation predicted, and that explanation is the first thing to
        # read then (it stood only in the experiment's line, some records earlier; s031: the rival of H2 named the limit the session spent its budget around)
        rival = "" if not b.get("rival") or b.get("rival_predicts") not in ("held", "failed") or b["result"] not in ("held", "failed") else (
            f"  [this is what the rival explanation predicted: {flat(b['rival'])}]" if b["rival_predicts"] == b["result"]
            else f"  [the rival explanation predicted {b['rival_predicts'].upper()} and does not fit this result: {flat(b['rival'])}]")
        close = "".join(f"  [NOTE: {q['left']} against {q['right']}: the two sides differ by {q['percent']:.3g} %, less than the tolerance of {b['tolerance']:g} %. They count as equal: "
                        "this comparison is decided by a difference that does not matter, so it is no evidence of a difference.]" for q in b.get("within_tolerance") or [])
        return f"of the decision rule for {b['for']} in {b['experiment']}: {flat(b.get('decision_rule', b.get('rule')))}  ->  {b['with_numbers']}  :  {b['result'].upper()}{rival}{close}"
    if t == "verdict" and r.get("by") == "supervisor":
        return (f"by the supervisor on {b['for']}: {b['result']}. {flat(b['because'])}" + ("" if b.get("fair", True) else f" The test was not a fair test ({DEFECTS.get(b.get('defect'), b.get('defect'))}).")
                + (f" A fair test: {flat(b['next'])}" if b.get("next") else "") + (f" [after your objection {b['after']}: {'the ruling stands' if b.get('stands') else 'the ruling is changed'}]" if b.get("after") else "")
                + (f" What the records show: {flat(b['shows'])}" if b.get("shows") else "") + (f" Defect named: {DEFECTS.get(b['defect'], b['defect'])}." if b.get("fair", True) and b.get("defect") not in (None, "", "none") else "")
                + (f" It said beforehand it would doubt the test if: {flat(b['doubt_if'])}" if b.get("doubt_if") else ""))
    if t == "verdict":
        return f"on {b['for']}: {b['result']}. {flat(b['because'])} Next: {flat(b['next'])}"
    if t == "review" and b.get("gate") == "ground" and b["decision"] == "sent_back":
        return (f"by the supervisor of a guess it did not accept (“{flat(b.get('guess'))[:200]}”" + (f", about the result “{flat(b['result'])[:200]}”" if b.get("result") else "") + f"): {GROUNDS.get(b['defect'], b['defect'])}. The records show: {flat(b['records_show'])} {flat(b['because'])}"
                + (f" The nearest earlier guess: {flat(b['nearest_earlier'])}" if b.get("nearest_earlier") else ""))
    if t == "review" and b.get("gate") == "ground":
        if b.get("unread"):   # the coherence audit, 2026-11-22: it was shown as sound
            return f"by the supervisor of the guess {b['for']}, before anything is built on it: not read (the supervisor's reading could not be read), and the guess is accepted unread"
        return (f"by the supervisor of the guess {b['for']}, before anything is built on it: " + ("sound: it starts from what the records show" if b["defect"] == "none" else f"accepted with a warning ({GROUNDS.get(b['defect'], b['defect'])})" if b.get("warning") else f"accepted on its second statement, but the supervisor still objects ({GROUNDS.get(b['defect'], b['defect'])})")
                + f". The records show: {flat(b['records_show'])} {flat(b['because'])}" + (f" The nearest earlier guess: {flat(b['nearest_earlier'])}" if b.get("nearest_earlier") else ""))
    if t == "review" and b.get("round"):   # a round of the review of a test before it runs (2026-11-22, after the reviews of s047 and s050)
        rules = "; ".join(f"{flat(d.get('decision_rule'))} (your rival: {flat(d.get('rival'))}; under it: {str(d.get('rival_predicts')).upper()})" for d in (b.get("test") or {}).get("decision_rules") or [])
        verdict = {"approved": "approved", "sent_back": "SENT BACK, and repaired in the same turn", "contested": "run, but the supervisor still objects after the last round", "dropped": "refused in the last round: the hypothesis is dropped",
                   "not_run": "not run: the harness could not use the last repair, and the hypothesis stays open"}.get(b["decision"], b["decision"])
        return (f"by {'the harness' if r.get('by') == 'harness' else 'the supervisor'} of the test of {b['for']}, round {b['round']} of {REVIEW_ROUNDS}, before any simulation: {verdict}. The test: {rules}."
                + (f" Feedback: {flat(b['feedback'])}" if b.get("feedback") else "") + (f" A stronger rival: {flat(b['stronger_rival'])}" if b.get("rival_is_weak") else "")
                + (f" It would doubt the test if: {flat(b['doubt_if'])}" if b.get("doubt_if") and r.get("by") != "harness" else ""))
    if t == "repair":
        return (f"your repair of the test of {b['for']} for round {b['round']}: {flat(b.get('decision_rule'))} (rival: {flat(b.get('rival'))}; under it: {str(b.get('rival_predicts')).upper()})"
                + (f"; simulations: {', '.join(str(x.get('label')) for x in b.get('runs') or [] if isinstance(x, dict))}" if b.get("runs") else ""))
    if t == "review":
        return (f"by the supervisor of the test of {b['for']}, before any simulation: " + {"approved": "approved", "sent_back": "SENT BACK, the test was not run", "contested": "run, but the supervisor still objects"}[b["decision"]]
                + (f". Defect: {DEFECTS.get(b['defect'], b['defect'])}" if b["defect"] != "none" else "") + f". {flat(b['because'])}"
                + (f" A rival explanation: {flat(b['rival'])} (under it the rule would have {b['rival_outcome'].upper() if b['rival_outcome'] in ('held', 'failed') else 'an outcome that cannot be told'})" if b.get("rival") else "")
                + (f" It would doubt the test if: {flat(b['doubt_if'])}" if b.get("doubt_if") else ""))
    if t == "objection":
        return f"to {b['to']}: {flat(b['because'])}"
    if t == "malformed":
        return f"an answer the harness could not use, so nothing in it was recorded or run: {flat(b['error'])}"
    if t == "note" and r.get("by") == "model" and b.get("requests"):
        return "a turn of requests only: " + "; ".join(f"{q.get('tool')}({json.dumps(q.get('args') or {})})" for q in b["requests"] if isinstance(q, dict))
    return json.dumps(b)

READINGS_ROOM = 40_000   # characters of readings given in full; past it, the older long ones are shortened (reading_forms)
def reading(r, by, short=False):
    """One reading: what a tool returned when the researcher looked, with its id, its turn, the tool and its arguments, in full up to CAP characters
    (its line breaks kept). The researcher's ledger text and the supervisor are given every reading of the session, the same way (2026-11-22, the
    operator: "keep every lookup result in the notebook, so both agents see the same thing"). Until then a reading was shown once, in the turn after
    its request (the arm "supervised": then one line of 260 characters), and the supervisor a selection of its own."""
    out, args = str(r["body"].get("result")), json.dumps((by.get(r.get("parent")) or {}).get("body", {}).get("args") or {})
    head = f"[{r['id']}] turn {r['turn']} reading {r['body'].get('tool')}({args}) returned:\n    "
    if short and len(out) > 1500:
        return head + out[:600].replace("\n", "\n    ") + f"\n    (... {len(out) - 600} more characters of this reading are left out here, to keep the ledger within its size: ask again with the same request for the whole of it)"
    return head + out[:CAP].replace("\n", "\n    ") + (f"\n    (cut here: {len(out)} characters in all)" if len(out) > CAP else "")

def reading_forms(ledger):
    """Each reading's text as the researcher and the supervisor are given it, by its id. While the readings together hold at most READINGS_ROOM
    characters, each stands in full (up to CAP); past that, a long reading (a series, a probe: over 1,500 characters) older than the newest four
    is shortened to its first 600 characters and says how much was left out (2026-11-22, after s047/s048: every reading is kept for both agents,
    and the ledger must stay within LEDGER_TOKENS; measure and metrics readings are short and stay whole)."""
    by, res = {r["id"]: r for r in ledger}, [r for r in ledger if r["type"] == "result"]
    full, newest = sum(min(len(str(r["body"].get("result"))), CAP) for r in res) <= READINGS_ROOM, {r["id"] for r in res[-4:]}
    return {r["id"]: reading(r, by, short=not full and r["id"] not in newest) for r in res}

def render(ledger, readings=True, rethinks=True):
    """The ledger as text for the prompt: one line per record, and in an evidence record one line per simulation. Every reading (what a tool returned)
    stays in it in full, in its place, with its id, so that the researcher keeps all it found and a later guess can name the reading it starts from.
    The researcher's own observations of each turn stand in it too, in their place, as "turn N your observations: ..." (2026-11-22, the operator:
    "I want the researcher to see all lookup results and its own observations previously accumulated all the time"): until then a turn's
    observations were kept in its first record but shown only for a turn of requests only. The supervisor is never given them.
    readings: no longer used (every arm keeps the readings since 2026-11-22)."""
    st = dict(states(ledger)[0])
    for y, w in why_states(ledger).items():   # a why with its standing now, and whether results have come in since it was last settled
        st[y] = {**w, "stale": since(ledger, w["at"]) if w["worth"] == "verify" and rethinks else [], "idle": w["worth"] == "verify" and not any(r["type"] == "hypothesis" and r["body"].get("from_why") == y for r in ledger)}   # rethinks: only the arm "hypotheses" has them (the coherence audit, 2026-11-22)
    by = {r["id"]: r for r in ledger}
    out, forms = [], reading_forms(ledger)
    for r in ledger:
        b = r.get("body") or {}
        if r.get("by") == "model" and b.get("observations"):
            out.append(f"turn {r['turn']} your observations: " + " ".join(str(b["observations"]).split())[:CAP])
        if r["type"] == "note" and r.get("by") == "model" and not b.get("requests"):
            continue   # a note that holds only the observations of an answer none of whose parts was recorded
        if r["type"] == "result":
            out.append(forms[r["id"]])
        elif r["type"] not in HIDDEN:
            out.append(f"[{r['id']}] turn {r['turn']} {r['type']} " + shown(r, st)[:CAP])
    return "\n".join(out) or "(empty)"

class ModelServerError(RuntimeError):
    pass

def post(url, body, timeout):
    """One request to the model server; ModelServerError when it fails or answers with an error."""
    try:
        r = requests.post(url, json=body, timeout=timeout).json()
    except Exception as e:
        raise ModelServerError(f"{type(e).__name__}: {e}")
    if not isinstance(r, dict) or "error" in r or r.get("object") == "error":
        raise ModelServerError(json.dumps(r)[:600])
    return r

LIVE = {"call": None, "last": 0.0}   # the call being made: what live_call.json says of it


def live_write(done=False, **kw):
    """live_call.json beside the ledger (2026-11-22, the operator: "they should be able to see tokens directly"): the call of the model being made, as
    it comes in: its number, turn, agent and step, when it began, how long it has run, what the agent has written so far (reasoning, answer) and
    whether it is done. Written whole (a temporary file, then a rename); never stops the session."""
    c = LIVE.get("call")
    if not c:
        return
    try:
        c.update(kw)
        c["done"], c["seconds"] = done, round(time.time() - c["t0"], 1)
        p = tools.SESSION / "live_call.json"
        tmp = p.with_name("live_call.json.tmp")
        tmp.write_text(json.dumps({k: v for k, v in c.items() if k != "t0"}) + "\n")
        os.replace(tmp, p)
    except (OSError, TypeError, ValueError, NameError):
        pass


def post_stream(url, body, timeout):
    """One request to the model server, streamed: the same answer as post() gives ({"choices": [{"message": {content, reasoning}, "finish_reason"}],
    "usage"}), and while it comes in, live_call.json says what has been written so far, about once a second. ModelServerError when it fails."""
    reasoning, content, finish, usage = [], [], None, {}
    try:
        with requests.post(url, json={**body, "stream": True, "stream_options": {"include_usage": True}}, timeout=timeout, stream=True) as r:
            if r.status_code != 200:
                try:
                    err = r.json()
                except ValueError:
                    err = r.text
                raise ModelServerError(json.dumps(err)[:600])
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                if line[6:].strip() == "[DONE]":
                    break
                ch = json.loads(line[6:])
                if not isinstance(ch, dict) or "error" in ch:
                    raise ModelServerError(json.dumps(ch)[:600])
                usage = ch.get("usage") or usage
                for c in ch.get("choices") or []:
                    d = c.get("delta") or {}
                    if d.get("reasoning") or d.get("reasoning_content"):
                        reasoning.append(d.get("reasoning") or d.get("reasoning_content"))
                    if d.get("content"):
                        content.append(d["content"])
                    finish = c.get("finish_reason") or finish
                if time.time() - LIVE["last"] >= 1.0:
                    LIVE["last"] = time.time()
                    live_write(reasoning="".join(reasoning), answer="".join(content))
    except ModelServerError:
        raise
    except Exception as e:
        raise ModelServerError(f"{type(e).__name__}: {e}")
    return {"choices": [{"message": {"content": "".join(content), "reasoning": "".join(reasoning)}, "finish_reason": finish}], "usage": usage}


def count_tokens(model, text):
    """Tokens of a text, counted by the model server's own tokenizer."""
    return post(API.removesuffix("/v1") + "/tokenize", {"model": model, "prompt": text}, 300)["count"]

THINK = {"limit": True}   # False once the model server has said that it cannot limit the draft


def draft_tokens(max_tokens):
    """The most tokens the model may spend on its draft (its reasoning before the answer): half of the answer's limit, so that the other half is always
    left for the answer itself. Without it a draft could use the whole limit and leave no answer at all (s045, s046: 5 of 11 answers were empty for
    that reason). The model server ends the draft at that length and the model goes on to its answer."""
    return max(128, max_tokens // 2)


def ask(model, system, user, schema, draft, temperature, max_tokens):
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature, "max_tokens": max_tokens,
            "response_format": {"type": "json_schema", "json_schema": {"name": "turn", "schema": schema}}}
    if not draft:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    elif THINK["limit"]:
        body["thinking_token_budget"] = draft_tokens(max_tokens)
    try:
        r = post_stream(API + "/chat/completions", body, 1800)
    except ModelServerError as e:  # a model server that cannot limit the draft says so: asked once more without the limit, and not asked for it again
        if "thinking_token_budget" not in body or "thinking_token_budget" not in str(e):
            raise
        THINK["limit"] = False
        del body["thinking_token_budget"]
        r = post_stream(API + "/chat/completions", body, 1800)
    ch = r["choices"][0]
    return ch["message"].get("content") or "", ch["message"].get("reasoning") or "", ch.get("finish_reason"), r.get("usage", {})

# ---- every call of the model, as it was made (2026-11-22, the operator: a page of their own to see what the agents are shown and what they write):
# sessions/<id>/calls.jsonl, one line per call: which agent (researcher, judge, supervisor), the two messages it was given, what it wrote before its
# answer, its answer, the counts of tokens, why it stopped and how long it took. No tool and no model reads it; the server gives it only to the
# page of the account that runs it (control.py, /api/agents). The calls go through here, so a scripted session (harness_checks) writes it too.
CALLS = {"n": 0, "turn": 0}
def stage(step, about=None, round_no=None, by=None, again=False):
    """now.json beside the ledger (2026-11-22, the operator, on the page's strip of the steps of a turn): the step the session is at, written as it
    begins, so that the page can say who works on what while no record is written yet (a supervisor's reading is recorded only when its step is
    done). step: reply (the researcher), judge, review (the supervisor's batched first review of a reply's new guesses and tests), ground (the supervisor reads a guess), restate (the researcher restates a guess; by: who did not
    accept it), design (the supervisor reviews a test; round_no of REVIEW_ROUNDS), repair (the researcher repairs a test for round_no), sims, checks,
    ruling (the supervisor rules on a test), objection (the supervisor looks again at a ruling the researcher objected to), look (the supervisor looks
    at results with no ruling for findings). Never stops the session."""
    CALLS["step"] = {"step": step, "about": about, "round": round_no, "by": by}   # the step of the calls that follow (calls.jsonl, live_call.json)
    try:
        p = tools.SESSION / "now.json"
        tmp = p.with_name("now.json.tmp")
        tmp.write_text(json.dumps({"turn": CALLS["turn"], "step": step, "about": about, "round": round_no, "rounds": REVIEW_ROUNDS if step in ("design", "repair") else None,
                                   "by": by, "again": again, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
        os.replace(tmp, p)
    except (OSError, TypeError, ValueError, NameError):
        pass


def called(agent, model, system, user, schema, draft, temperature, max_tokens):
    t0 = time.time()
    LIVE["call"] = {"n": CALLS["n"] + 1, "turn": CALLS["turn"], "agent": agent, "step": CALLS.get("step"), "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "t0": t0, "reasoning": "", "answer": ""}   # step: as calls.jsonl has it (the coherence audit, 2026-11-22: it was spread into the call)
    LIVE["last"] = 0.0
    live_write()
    try:
        content, reasoning, finish_reason, usage = ask(model, system, user, schema, draft, temperature, max_tokens)
    except Exception as e:
        live_write(done=True, error=f"{type(e).__name__}: {' '.join(str(e).split())[:300]}")
        raise
    live_write(done=True, reasoning=reasoning, answer=content, finish_reason=finish_reason, usage=usage)
    CALLS["n"] += 1
    by_agent = CALLS.setdefault("by", {})   # every call of this run, by agent (the coherence audit, 2026-11-22: "calls" counts the researcher's only)
    by_agent[agent] = by_agent.get(agent, 0) + 1
    try:
        with (tools.SESSION / "calls.jsonl").open("a") as f:
            f.write(json.dumps({"n": CALLS["n"], "turn": CALLS["turn"], "agent": agent, "step": CALLS.get("step"), "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "seconds": round(time.time() - t0, 1),
                                "model": model, "draft": bool(draft), "temperature": temperature, "max_tokens": max_tokens, "system": system, "user": user,
                                "reasoning": reasoning, "answer": content, "finish_reason": finish_reason, "usage": usage}) + "\n")
    except (OSError, TypeError, ValueError):
        pass   # the record of a call never stops the session
    return content, reasoning, finish_reason, usage

# ---- the judge (2026-11-17, the operator's decision): a second model call that reads one guess of why and one hypothesis said to come from it, and says whether
# testing the hypothesis would tell if the guess is true. The harness could only check that the guess exists (s041: H2 named a guess about the 1 MB / 20 ms
# cap and was about measuring for 30 s instead of 10 s). A hypothesis the judge finds unconnected is refused, with the judge's reason. The judge can be wrong:
# its reading is kept with the hypothesis (and, for a refused one, in a record of its own) so that a person can see it.
JUDGE = ("You check one step of a researcher's reasoning about a simulated network. You are given a RESULT, the researcher's GUESS of why it came out so, and a HYPOTHESIS "
         "the researcher says comes from that guess. Decide one thing: would testing the hypothesis tell whether the guess is true? It does when the hypothesis is a consequence "
         "of the guess: if the guess is true the hypothesis should hold, and if the hypothesis is refuted the guess becomes less likely. It does not when the hypothesis is about "
         "another cause or another setting than the guess, or when it would come out the same whether the guess is true or not. A hypothesis may test only one consequence of "
         "the guess: that is enough. The RESULT is only the background the guess was made on: judge the hypothesis against the GUESS, not against the result. Do not judge "
         "whether the guess or the hypothesis is correct, only whether the one follows from the other. Answer with follows (true or "
         "false) and because: one plain sentence of at most 30 words.")
JUDGE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["follows", "because"],
                "properties": {"follows": {"type": "boolean"}, "because": {"type": "string"}}}


def judge_link(model, brief, why, hyp):
    """(follows, because): whether testing hypothesis hyp would tell if the guess why is true, as a second model call sees it. Raises when the model
    cannot be asked or its answer cannot be read; the caller then accepts the hypothesis unjudged and records that. A "no" is asked for twice: only
    two readings that agree refuse a hypothesis."""
    user = (f"THE SYSTEM, in the brief's words: {' '.join(str(brief.get('description') or '').split())[:1500]}\nThe settings the researcher may change: {', '.join(brief['knobs'])}\n\n"
            f"THE RESULT: {why['result']}\nTHE GUESS of why it came out so: {why['guess']}\nWhat would make it so, not directly visible: {why['unseen']}\n\n"
            f"THE HYPOTHESIS said to come from this guess: {hyp['text']}\nIts prediction: {hyp.get('prediction') or ('the decision rule of its test: ' + '; '.join(hyp['rules']) if hyp.get('rules') else 'not stated')}\n\nWould testing this hypothesis tell whether the guess is true?")
    def read():
        d = json.loads(called("judge", model, JUDGE, user, JUDGE_SCHEMA, False, 0, 400)[0])
        return bool(d["follows"]), " ".join(str(d["because"]).split())
    follows, because = read()
    if not follows:   # a refusal costs the model a turn and the judge is not steady on a pair at the border (s041 H3: no, then yes): it refuses only when a second reading agrees
        again, because2 = read()
        if again:
            return True, f"read twice. The second reading: {because2} The first found no link: {because}"
    return follows, because


# ---- the supervisor (2026-11-18, the operator's decision after the review of the loop's objects: no verdict ever contradicted its check, the judge passed 20 of 20,
# a rethink could call a guess supported after its only hypothesis was refuted). The arm "supervised" has two agents. The researcher proposes: guesses,
# hypotheses, decision rules, experiments, the report. It does not rule on its own tests. The supervisor proposes nothing; it acts at two gates:
#   gate 1, before any simulation of a test is run: can this test tell whether the guess is true? A test with a named defect is sent back, once;
#   gate 2, after the harness has checked the rules: what does the check mean? Supported, refuted, or inconclusive because the test was not a fair one.
# The two are kept apart although they are the same model: the supervisor has its own instructions, its own request with nothing of the researcher's
# conversation in it, its own sampling (temperature 0), and it is shown the artifacts and the measured numbers, never the researcher's observations or
# reasons. At gate 1 it writes down what would make it doubt the test before anything is measured, and at gate 2 it is held to that. What it was shown
# and what it answered is kept beside the ledger (supervisor.jsonl) so that a person can see on what ground it decided. Facts stay the harness's: a
# ruling that does not fit the checks (supported although a check failed) is recorded as inconclusive.
SUPERVISOR = ("You are the supervisor of a researcher who studies a simulated network by experiments. You are not the researcher and you do not help it to find anything: your one "
              "task is that what goes on record is sound. You never propose a hypothesis, a setting or an experiment of your own. You are shown the system as its brief describes it, "
              "the researcher's guess of a cause, the hypothesis it wants to test, its decision rules, the simulations and the measured numbers. You are not shown the researcher's "
              "reasoning and you owe it no agreement: a test that cannot tell whether the guess is true wastes simulations and puts a false certainty on record. Words: a guess is the "
              "researcher's idea of a cause; a hypothesis is a measurable consequence of it; a decision rule is the comparison, fixed before the simulations, that the harness checks "
              "from the measured values; HELD or FAILED is the harness's finding and is a fact. A test need not run a new simulation: its rule may be about a measurement of the researcher's own, taken now "
              "from the record of a simulation that already ran. That costs nothing and is a proper test, never by itself a reason to send it back: the defect already_answered means only "
              "that the very value the rule compares already stands in the ledger or in the tool results you are shown. Judge by the description of the system and by the numbers, name the numbers and record "
              "ids you rest on, and say plainly when something cannot be told. Answer in the JSON format you are given, each text in one or two plain sentences.")
DEFECTS = {"none": "no defect",
           "not_about_the_guess": "the hypothesis would come out the same whether the guess is true or not, or is about another cause than the guess",
           "rival_passes_too": "a rival explanation predicts the same outcome of the decision rule, so the test cannot tell the two apart",
           "already_answered": "the very value this test asks for already stands in the ledger or in a tool's result: read it there instead of testing for it",
           "confounded": "another setting, at the values chosen, limits or hides the effect, so the result would not show what the hypothesis says",
           "threshold": "the rule's threshold or margin makes it hold or fail whatever happens, or lies inside the tolerance"}
# the review of a test before it runs (since 2026-11-22, after the reviews of s047 and s050): the supervisor judges the researcher's own rival, and each
# box comes after the reasoning it follows from, so that it chooses after it has reasoned
REVIEW_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reads", "stronger_rival", "rival_is_weak", "under_rival", "rival_outcome", "doubt_if", "because", "defect", "feedback"], "properties": {
    "reads": {"type": "string", "description": "what the decision rule compares, in which simulations, and what the guess says it will give"},
    "stronger_rival": {"type": "string", "description": "the strongest competing explanation you can see, set against the researcher's rival: name a clearly stronger one, or say why the researcher's is the strongest"},
    "rival_is_weak": {"type": "boolean", "description": "true when there is a clearly stronger rival than the researcher's"},
    "under_rival": {"type": "string", "description": "your reasoning: what the decision rule would give if the rival (the researcher's, or the stronger one you named) were true and the guess false"},
    "rival_outcome": {"type": "string", "enum": ["held", "failed", "cannot tell"], "description": "what the decision rule would give under that rival"},
    "doubt_if": {"type": "string", "description": "written before anything is measured: what in the results would make you doubt this test even if its rule comes out as the researcher predicts"},
    "because": {"type": "string", "description": "your reasoning to the decision, with the numbers or record ids it rests on"},
    "defect": {"type": "string", "enum": list(DEFECTS), "description": "the one defect your reasoning ends in, or none"},
    "feedback": {"type": "string", "description": "for the researcher: the one problem that matters most (empty when there is none; a clearly stronger rival is that problem), the record ids and numbers it rests on, and what a repaired test must achieve. Never a decision rule, a measure@label, simulations or a network change: the researcher finds the repair"}}}
AGAIN_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["because", "stronger_rival", "rival_is_weak", "rival_outcome", "defect"], "properties": {
    "because": {"type": "string", "description": "your answer to the question, with the numbers or record ids it rests on"},
    "stronger_rival": {"type": "string", "description": "the strongest competing explanation after your answer: a stronger one your review or feedback named, or say why the researcher's is the strongest"},
    "rival_is_weak": {"type": "boolean", "description": "true when there is a clearly stronger rival than the researcher's"},
    "rival_outcome": {"type": "string", "enum": ["held", "failed", "cannot tell"], "description": "what the decision rule would give under the rival, after your answer"},
    "defect": {"type": "string", "enum": list(DEFECTS), "description": "the one defect your answer ends in, or none"}}}
RULING_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["shows", "because", "fair", "defect", "result", "retest", "findings"], "properties": {
    "shows": {"type": "string", "description": "what the measured numbers show, in one sentence, before any conclusion"},
    "because": {"type": "string", "description": "your reasoning from the numbers to the ruling: written before you rule"},
    "fair": {"type": "boolean", "description": "whether this was a fair test of the hypothesis: one that could have come out the other way if the hypothesis were false"},
    "defect": {"type": "string", "enum": list(DEFECTS), "description": "none when the test was fair"},
    "result": {"type": "string", "enum": ["supported", "refuted", "inconclusive"], "description": "supported: every check held and the test was fair; refuted: a check failed and the test was fair; inconclusive: otherwise"},
    "retest": {"type": "string", "description": "when the result is inconclusive: what a fair test would have to compare; else empty"},
    "findings": {"type": "array", "maxItems": 2, "items": None, "description": "what the measured results leave unexplained (what, never why), at most 2; empty when nothing"}}}   # items: FINDING_ITEM, set where it is defined
GROUNDS = {"none": "no defect",
           "not_in_the_records": "the result the guess starts from is not what the cited records show",
           "repeats": "the guess says again, in other words, what an earlier guess or hypothesis already said, and that one has its ruling",
           "ignores_a_ruling": "the guess goes on as if a ruling against it had not been given: it does not say what is different now",
           "not_from_what_was_learned": "the guess does not come from the newer records it cites: it would be the same guess without them"}
GROUND_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["records_show", "nearest_earlier", "because", "defect"], "properties": {
    "records_show": {"type": "string", "description": "what the cited records show about the result the guess starts from, with the numbers"},
    "nearest_earlier": {"type": "string", "description": "the id of the earlier guess or hypothesis that is nearest to this one in what it claims (for example Y2 or H3), or none"},
    "because": {"type": "string", "description": "your reasoning to the decision: written before you name the defect"}, "defect": {"type": "string", "enum": list(GROUNDS), "description": "the one defect your reasoning ends in, or none"}}}
APPEAL_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answer", "fair", "stands", "result", "because"], "properties": {
    "answer": {"type": "string", "description": "what in the records the objection gets right or wrong"},
    "fair": {"type": "boolean", "description": "whether this was a fair test of the hypothesis: one that could have come out the other way if the hypothesis were false"},
    "stands": {"type": "boolean", "description": "true: your ruling stands as it was"},
    "result": {"type": "string", "enum": ["supported", "refuted", "inconclusive"]}, "because": {"type": "string"}}}
GROUND_WARNINGS = ("not_from_what_was_learned",)   # the arm "supervised": defects of a guess the supervisor records as a warning; the guess is accepted (2026-11-22, the operator, after s050 and s051: most refusals were this one, and in s050 turn 6 a guess that quantified an earlier one with new readings was refused)
REFUSED_ONCE = "turn"   # the arm "supervised": a guess about the same records is refused once in a turn ("turn"; the coherence audit, 2026-11-22: once in the session left those records unguarded for the rest of it), or once in the session ("session": the rule before part D)
RESTATE_GUESSES = True   # the arm "supervised": a guess that is not accepted (by the harness or the supervisor) comes back once in the same turn to be restated, and is then accepted, contested if it still fails: its hypotheses and test go ahead (2026-11-22, the operator: no cascade)
RESTATE_SYSTEM = ("You are the researcher. One of your guesses of why a result came out so was not accepted as you stated it. Restate it once, from the reason you are given: "
                  "what records it starts from, the result, the guess, and the earlier guess it states more exactly, if any. Answer with one JSON object in the format you are given.")
COMPARISONS_MOST = 3   # the arm "supervised": the most comparisons in one decision rule (the operator, 2026-11-22, after s052 H4's rule of twelve); stated in LEAN_PROMPT and the repair prompt
REVIEW_ROUNDS = 3        # the arm "supervised": the most rounds of review for one test in one turn (the first proposal and its repairs; 2026-11-22, after the reviews of s047 and s050)
AFTER_ROUNDS = "contested"   # what becomes of a test still refused after the last round: "contested" (it runs, and the review and the ruling say that the supervisor objects) or "dropped" (its hypothesis is dropped with the supervisor's last reason)
RULE_IN_TEXT = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*@[A-Za-z0-9_]+")   # a decision rule's measure@label: the supervisor's feedback never holds one
REPAIR_SYSTEM = ("You are the researcher. The supervisor, or the harness, sent back one of your tests before any of its simulations was run. Repair that test only, from the "
                 "feedback: a decision rule that can tell your guess from a competing explanation, the strongest rival you can think of, what the rule would give if that rival were "
                 "true, and the simulations only if they must change. Answer with one JSON object in the format you are given.")
SHORT_CALL_TOKENS = 12000   # a repair and a restatement (2026-11-22, the operator chose it after the review of s050 to s053): 6,000 of them reasoning; a whole reply keeps its own
CONTINUES = 2   # (2026-11-22, the operator: "Turn 1 and 2 passed without any hypothesis are not what I intended. Fix it") a reply that states no hypothesis, test, drop, verdict, objection or report is followed by another call in the same turn, at most this many times: what it asked for is answered at once
LABEL_MOST = 20   # a simulation's label: letters, digits and _, at most this many (the refusal, the answer format's maxLength, prompt.txt and LEAN_PROMPT say it)
PLAIN_WORDS = ("hypothes", "verdict", "decision rule", "decision_rule", "rethink")   # what the arm "plain" is never told about (checked on its whole system text)
HOW_TO_RUN = {   # the brief's how_to_run as each arm is shown it (the coherence audit, 2026-11-22: "the params that differ from the defaults", though a run states every knob; the plain arm was told of decision rules)
    "plain": "An experiment is a set of simulations with one purpose, run at once. Fill the 'experiment' field of your answer: its question and the simulations (runs: a label and a value for every knob). The harness runs the simulations and appends the evidence (one line per simulation).",
    "other": "An experiment is a set of simulations with one purpose, run at once. Fill the 'experiment' field of your answer: its kind (test or explore), the simulations (runs: a label and a value for every knob), and for a test the decision rules, comparisons stated before the simulations run. The harness runs the simulations, appends the evidence (one line per simulation) and checks every decision rule itself."}
STRUCTURE_PLAIN = (("a decision rule may only name a measure that exists in every simulation it names", "an experiment's simulations are compared on the measures that exist in every one of them"),
                   ("A change of structure is a hypothesis like any other: say what it should change and why, before you run it.", "Say what a change of structure should change and why, before you run it."))
REQUESTS_MOST = 3   # the arms "hypotheses" and "plain": the most requests answered in one reply (stated in prompt.txt; the answer format's maxItems; a cut is noted)
LOOK_TURNS = 3   # the arms "hypotheses" and "plain": the most turns in a row with requests only; then the turn's text asks for a decision
LOOKS = 6   # the arm "supervised": the most requests in one turn, and the most turns in a row that only look (the operator, 2026-11-18: observe the system whenever it wants, rather than try many simulations)
BATCH_FIRST = True   # the arm "supervised": the new guesses and tests of a reply are reviewed in one request (stage 4 of the coherence audit, 2026-11-22; the operator's sheet "Fixes from s052 and s053", 4a)
AGAIN_TOKENS = 2000   # the supervisor's follow-up question: 1,000 of them reasoning (the operator, 2026-11-22: a thinking budget of 1,000)
SUPERVISOR_FILE = "supervisor.jsonl"   # beside the ledger: for each record of the supervisor, what it was shown and what it answered


def stated_rules(text, arm):
    """The numbers the instructions state for rules the harness enforces, against the constants that enforce them (the coherence audit, 2026-11-22:
    one source per rule). ValueError at the start of the session when they differ; the texts stay plain text that the checks can read."""
    want = [("a label's length", r"at most (\d+) characters", LABEL_MOST)] + ([("the requests of one reply", r"at most (\d+) in one reply", REQUESTS_MOST)] if arm != "supervised" else
                                                                                [("a decision rule's comparisons", r"at most (\d+) comparisons", COMPARISONS_MOST)])
    for what, pat, n in want:
        found = [int(x) for x in re.findall(pat, text)]
        if not found or any(x != n for x in found):
            raise ValueError(f"the instructions state {what} as {found or 'nothing'}, the harness enforces {n}")


def fields_text(schema, indent="  "):
    """The fields of an answer as the model is to write them, in their order, each with what it holds (the coherence audit, 2026-11-22: the schema
    reached the model server only as a constraint, so the supervisor never saw its fields and guessed what each meant)."""
    out = []
    for k, v in (schema.get("properties") or {}).items():
        kind = ("true or false" if v.get("type") == "boolean" else "one of: " + ", ".join(map(str, v["enum"])) if v.get("enum") else
                "a list" if v.get("type") == "array" else "a number" if v.get("type") in ("number", "integer") else "text")
        out.append(f"{indent}{k} ({kind}){': ' + v['description'] if v.get('description') else ''}")
        items = v.get("items") if v.get("type") == "array" else None
        if isinstance(items, dict) and items.get("properties"):
            out.append(f"{indent}  each item of {k}:")
            out.append(fields_text(items, indent + "    "))
    return "\n".join(out)


def supervise(model, user, schema, max_tokens=9000):
    """One request to the supervisor: its own instructions, a request of its own (nothing of the researcher's conversation), temperature 0. The model
    reasons before it answers, as the researcher does; that reasoning is not kept (its answer says its ground)."""
    user += "\n\nYOUR ANSWER: one JSON object with these fields, in this order:\n" + fields_text(schema)   # what each field holds (the coherence audit, 2026-11-22)
    content = called("supervisor", model, SUPERVISOR, user, schema, True, 0, max_tokens)[0]
    try:
        return json.loads(content)
    except ValueError:
        d = findings_cut(content) if "findings" in (schema.get("properties") or {}) else None
        if d is None:
            raise
        return d


def findings_cut(content):
    """An answer of the supervisor cut off in its findings, which stand last in its format (s053, 2026-11-22: a sound ruling, then "It is not a
    finding." to the limit): what stands before them, with no findings and marked findings_cut; None when that is not a whole object."""
    m = re.search(r',\s*"findings"\s*:', content)
    if not m:
        return None
    try:
        d = json.loads(content[:m.start()] + "}")
    except ValueError:
        return None
    return {**d, "findings": [], "findings_cut": True} if isinstance(d, dict) else None


def _system_for_supervisor(brief):
    knobs = "; ".join(f"{k} ({', '.join(map(str, s['choices'])) if 'choices' in s else str(s['min']) + ' to ' + str(s['max'])}, default {s['default']})" for k, s in brief["knobs"].items())
    return (f"THE SYSTEM, in the brief's words: {' '.join(str(brief.get('description') or '').split())[:3000]}\nTHE SETTINGS THE RESEARCHER MAY CHANGE: {knobs}\n"
            f"TOLERANCE: two results that differ by less than {TOLERANCE:g} % count as equal.\n")


def _measured(ledger, only=None):
    """Every simulation measured so far as the evidence tables give it (label, run, settings changed from the defaults | measured), or those of one experiment."""
    lines = [f"  [{r['id']}] " + l for r in ledger if r["type"] == "evidence" and (only is None or r["body"]["experiment"] == only) for l in r["body"]["lines"]]
    return "\n".join(lines[-60:]) or "  (nothing yet)"


def _looked(ledger, runs=None, room=None):
    """Every reading of the session (what the tools returned when the researcher looked: series, measure, metrics, probe, a trace search, the
    description of the system), in the same form as in the researcher's ledger text (reading): the supervisor is given what the researcher is given
    (2026-11-22, the operator). From s044 (2026-11-18) to then it was shown the readings of the simulations at hand, newest first, each cut at
    1,800 characters and 5,000 to 9,000 in all. runs and room are no longer used."""
    forms = reading_forms(ledger)
    return "\n".join(forms[r["id"]] for r in ledger if r["type"] == "result") or "  (the researcher has asked the tools for nothing yet)"


def _case(ledger, hid, rules, h=None, w=None):
    """One hypothesis as the supervisor is shown it: the result its guess is about, the guess, the hypothesis, its decision rules. Not the researcher's reasons.
    h, w: the hypothesis and its guess when they are not in the ledger yet (the batched first review, 2026-11-22)."""
    flat = lambda v: " ".join(str(v).split())
    h = h if h is not None else next(r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid)
    w = w if w is not None else next((r["body"] for r in ledger if r["type"] == "why" and r["id"] == h.get("from_why")), None)
    return ((f"THE RESULT the guess is about: {flat(w['result'])}\nTHE GUESS of why it came out so: {flat(w['guess'])}\n" + (f"What would make it so, not directly visible: {flat(w['unseen'])}\n" if w.get("unseen") else "") if w else "")
            + f"THE HYPOTHESIS {hid}: {flat(h['text'])}\n" + "".join(f"DECISION RULE: {flat(d['decision_rule'])}\n" for d in rules))


def review_design(model, brief, ledger, ex, hid, ask_fn=None, round_no=1, earlier=(), case=None, parts=False, pre=None, pre_saw=None):
    """Gate 1. The supervisor's review of the test of one hypothesis, before any of its simulations is run: (review, what it was shown).
    Since 2026-11-22 (the operator, after the reviews of s047 and s050: the supervisor invented the rival itself, and its boxes defect and rival_outcome
    disagreed 12 times in s047, the harness siding with rival_outcome each time) it judges the researcher's own rival: is there a clearly stronger one,
    and would the rule really give rival_predicts under it. Approved only with no defect, no clearly stronger rival and the rule failing under the
    rival, as the researcher says. Boxes that contradict each other are asked about once more, one direct question; still contradictory, it is a
    refusal. Its feedback says what is wrong and never the repair: a part that holds a decision rule (measure@label) is cut.
    round_no, earlier: the round, and the feedback of the earlier rounds of this test (in this turn).
    review = {reads, stronger_rival, rival_is_weak, under_rival, rival_outcome, doubt_if, because, defect, feedback, approved, rival, again?, cut?}"""
    flat = lambda v: " ".join(str(v).split())
    rules = [d for d in ex.get("decision_rules") or [] if d.get("for") == hid]
    need = next((n for n in ex.get("needs") or [] if n.get("for") == hid), {})
    planned = plan(ledger, [r for r in ex["runs"] if r["label"] in (need.get("simulations") or [r["label"] for r in ex["runs"]])])
    sims = "\n".join(f"  {r['label']} {{{', '.join(f'{k}={v}' for k, v in r['params'].items())}}}" + (f"; network changed: {edits_say(r['structure'])}" if r.get("structure") else "") + (f"  (already run as {r['prior']['id']}: its result is in the table above and will be returned, not run again)" if r["prior"] else "  (new)") for r in planned)
    theirs = "".join(f"THE RESEARCHER'S RIVAL for this rule: {flat(d.get('rival'))}\nWHAT THE RESEARCHER SAYS THE RULE GIVES IF THAT RIVAL IS TRUE: {str(d.get('rival_predicts')).upper()}\n" for d in rules)
    before = "".join(f"ROUND {k} of this test: {who} sent it back: {flat(fb)}\n" for k, who, fb in earlier)
    item = (case if case is not None else _case(ledger, hid, rules))
    item = (item
            + "".join(f"A MEASUREMENT THE RESEARCHER DEFINES FOR THIS TEST: {m['name']} = {m['stat']} of {m['of']}" + (f" against the level {m['level']}" if m.get("level") is not None else "") + f", from {m.get('t_from') if m.get('t_from') is not None else 2} s to {m.get('t_to') if m.get('t_to') is not None else 'the end'} (computed by the harness from what each simulation records; the probe only listens)\n" for m in ex.get("measurements") or [])
            + (f"What the researcher says it must know to decide it: {flat(need['to_know'])}\n" if need.get("to_know") else "") + f"Between the simulations its rule compares, the one setting that differs: {need.get('varies') or 'not stated'}; the measure the rule is about: {need.get('measure') or 'not stated'}\n"
            + theirs + f"THE SIMULATIONS PLANNED FOR IT:\n{sims}\n\n")
    ask = ("Before any of these simulations is run: can this test tell the guess from the researcher's rival? Judge the researcher's rival, do not replace it with your own. First say what "
            "the rule compares. Then say whether you see a clearly stronger rival (name it, or say why the researcher's is the strongest). Then reason what the decision rule would give if that "
            "rival (the researcher's, or the stronger one) were true and the guess false, and give that outcome. Then say what would make you doubt the test even if it comes out as predicted, "
            "reason to the decision, and name the defect, or none. Last, feedback for the researcher: the one problem that matters most (a clearly stronger rival is that problem), "
            "the record ids and numbers it rests on, and what a repaired test must achieve. The feedback never contains a decision rule, a measure@label, simulations or a network "
            "change: the researcher must find the repair itself. The defects: "
            + "; ".join(f"{k}: {v}" for k, v in DEFECTS.items()) + ". A test is not defective for being small or for testing only one consequence of the guess.")
    if parts:   # the pieces of this review, for the batched first review
        return {"item": item, "ask": ask}
    user = (_system_for_supervisor(brief) + f"\nWHAT HAS BEEN MEASURED SO FAR:\n{_measured(ledger)}\n\nEVERY READING OF THE SESSION, as the researcher's ledger holds them (what the tools returned when the researcher looked: measurements too):\n{_looked(ledger)}\n\n" + item + (f"THIS IS ROUND {round_no} of at most {REVIEW_ROUNDS} for this test. The researcher repaired it after:\n{before}\n" if round_no > 1 else "") + ask)
    d = pre if pre is not None else (ask_fn or supervise)(model, user, REVIEW_SCHEMA)   # pre: its answer in the batched first review
    predicts = next((str(x.get("rival_predicts")) for x in rules if x.get("rival_predicts") in ("held", "failed")), "failed")
    rev = {"reads": flat(d.get("reads")), "stronger_rival": flat(d.get("stronger_rival")), "rival_is_weak": bool(d.get("rival_is_weak")), "under_rival": flat(d.get("under_rival")),
           "rival_outcome": d.get("rival_outcome") if d.get("rival_outcome") in ("held", "failed", "cannot tell") else "cannot tell", "doubt_if": flat(d.get("doubt_if")),
           "because": flat(d.get("because")), "defect": d.get("defect") if d.get("defect") in DEFECTS else "none", "feedback": flat(d.get("feedback"))}
    def judge(r):   # (approved, what contradicts what, or None)
        ok = r["defect"] == "none" and not r["rival_is_weak"] and r["rival_outcome"] == predicts
        if r["defect"] == "none" and (r["rival_is_weak"] or r["rival_outcome"] != predicts):
            return False, (f"you named no defect, but you said that a clearly stronger rival exists" if r["rival_is_weak"] else
                           f"you named no defect, but you said that under the rival the rule would give {r['rival_outcome'].upper()}, where the researcher says {predicts.upper()}")
        if r["defect"] == "rival_passes_too" and not r["rival_is_weak"] and r["rival_outcome"] == predicts:
            return False, f"you named the defect that a rival passes the rule too, but you said that under the rival the rule would give {predicts.upper()}, as the researcher says, so the rule tells the two apart"
        return ok, None
    ok, clash = judge(rev)
    if clash:   # the two boxes contradict each other: one direct question, and the decision from its answer (2026-11-22: no siding with one box)
        # the question shows the rival the review itself named, and its box rival_is_weak may change (the coherence audit, 2026-11-22: s052 H2's feedback
        # named a stronger rival, the question asked only about the researcher's, the test was approved, and it was ruled inconclusive for that very rival)
        q = (user + f"\n\nYOUR REVIEW: defect {rev['defect']}; under the rival the rule would give {rev['rival_outcome'].upper()}; a clearly stronger rival: {'yes' if rev['rival_is_weak'] else 'no'}. "
             f"The strongest rival you named: {rev['stronger_rival'] or '(none)'} Your feedback: {rev['feedback'] or '(none)'}\n"
             f"These do not fit together: {clash}. One question: take the strongest rival there is, the researcher's or one your review or feedback names; under it, would this rule give "
             f"{predicts.upper()}, as the researcher says, or not? Answer it; then say again which rival is the strongest and whether it is clearly stronger than the researcher's, "
             "the outcome under it, and the defect.")
        try:
            stage("design", hid, round_no, again=True)
            a = (ask_fn or (lambda m, u, s: supervise(m, u, s, AGAIN_TOKENS)))(model, q, AGAIN_SCHEMA)
            if not isinstance(a, dict):
                raise ValueError("not an object")
        except (ValueError, KeyError, TypeError) as e:   # a follow-up that cannot be read leaves the contradiction standing: a refusal (it was a run unreviewed)
            a = None
            ok = False
            rev["again"] = {"question": clash, "unread": f"{type(e).__name__}", "still": clash}
        if a is not None:
            again = {"question": clash, "because": flat(a.get("because")), "stronger_rival": flat(a.get("stronger_rival") or rev["stronger_rival"]), "rival_is_weak": bool(a.get("rival_is_weak")),
                     "rival_outcome": a.get("rival_outcome") if a.get("rival_outcome") in ("held", "failed", "cannot tell") else "cannot tell", "defect": a.get("defect") if a.get("defect") in DEFECTS else "none"}
            rev["again"] = again
            ok, clash2 = judge({**rev, "rival_is_weak": again["rival_is_weak"], "rival_outcome": again["rival_outcome"], "defect": again["defect"]})
            if clash2:   # still contradictory: a refusal
                ok = False
                rev["again"]["still"] = clash2
            else:
                rev["rival_is_weak"], rev["stronger_rival"], rev["rival_outcome"], rev["defect"] = again["rival_is_weak"], again["stronger_rival"], again["rival_outcome"], again["defect"]
        user = q + "\n[the answer: " + (json.dumps(a) if a is not None else "could not be read") + "]"
    if not ok and not rev["feedback"]:   # a refusal always says what is wrong
        said = (rev.get("again", {}).get("still") or clash or "").replace("you named", "it named").replace("you said", "it said")   # for the researcher: of the supervisor, not to it
        rev["feedback"] = DEFECTS.get(rev["defect"]) if rev["defect"] != "none" else "the supervisor's review contradicted itself: " + said
    if RULE_IN_TEXT.search(rev["feedback"]):   # the feedback never writes the repair: a part that holds a decision rule is cut, and the record says so
        parts = re.split(r"(?<=[.;!?])\s+", rev["feedback"])
        kept = [x for x in parts if not RULE_IN_TEXT.search(x)]
        rev["feedback"], rev["cut"] = " ".join(kept) or "(the harness cut the whole feedback: it wrote a decision rule)", len(parts) - len(kept)
    rev["approved"] = ok
    rev["rival"] = rev["stronger_rival"] if rev["rival_is_weak"] else ""   # the rival the supervisor names itself: only a clearly stronger one (the review's "rival" since 2026-11-18)
    if pre is not None:   # what it was shown: the batched request (and a follow-up question, asked alone)
        user = (pre_saw or "") + "\n\n[this test was answered in the batched first review of the turn]" + (f"\n\n[then asked alone]:\n{user}" if rev.get("again") else "")
    return rev, user


def record_line(r, ledger):
    """One record as the supervisor and a short call of the researcher are shown it: a result table, a simulation, a check, a reading in full, a review,
    a ruling (gate 0, the restatement and the repair; the coherence audit, 2026-11-22: the restatement and the repair were given ids only)."""
    flat = lambda v: " ".join(str(v).split())
    b = r["body"]
    if r["type"] == "evidence":
        return f"[{r['id']}] measured in {b['experiment']}:\n" + "\n".join("    " + l for l in b["lines"])
    if r["type"] == "simulation":
        return f"[{r['id']}] simulation {b.get('label')} {{{', '.join(f'{k}={v}' for k, v in (b.get('params') or {}).items())}}} | " + " ".join(f"{k}={v}" for k, v in (b.get("metrics") or {}).items())
    if r["type"] == "check":
        return f"[{r['id']}] check for {b['for']}: {flat(b['decision_rule'])}  ->  {b['with_numbers']}  :  {b['result'].upper()}"
    if r["type"] == "result":   # in full, as the researcher's ledger holds it (until 2026-11-22: one line of 1,500 characters)
        return reading(r, {x["id"]: x for x in ledger})
    if r["type"] == "review":
        return f"[{r['id']}] the {'harness' if r.get('by') == 'harness' else 'supervisor'}'s review of {b.get('for') or 'a guess'}: {b.get('decision')}. {flat(b.get('because'))}" + (f" The rival it named: {flat(b['rival'])}" if b.get("rival") else "")
    if r["type"] == "verdict":
        return f"[{r['id']}] ruling on {b['for']}: {b['result']}. {flat(b['because'])}"
    return f"[{r['id']}] {r['type']}: {flat(json.dumps(b))[:600]}"


def gkey(w):
    """What makes a guess the same for gate 0's reading: its guess, the records it cites and the result it states (a restatement that corrects its
    result is read again; the coherence audit, 2026-11-22)."""
    return (" ".join(str(w.get("guess")).split()), tuple(w.get("about") or []), " ".join(str(w.get("result")).split()))


def ground_of(model, brief, ledger, why, ask_fn=None, parts=False, pre=None, pre_saw=None):
    """Gate 0. The supervisor's reading of one new guess before anything is built on it: is the result it starts from what the records it cites show,
    and is it more than an earlier guess or hypothesis said again? (ground, what it was shown). ground = {records_show, nearest_earlier, defect, because}.
    The supervisor is shown the cited records as the ledger holds them, the session's guesses and hypotheses with their rulings, and of the new guess
    its three statements (the result, the guess, what would make it so): not why the researcher thinks it worth verifying."""
    flat = lambda v: " ".join(str(v).split())
    st = states(ledger)[0]
    cited = [r for r in ledger if r["id"] in why["about"]]
    record = lambda r: record_line(r, ledger)
    new = learned_since(ledger)
    mark = lambda r: record(r) + ("   <- NEW since the researcher's earlier guesses" if new is not None and r["id"] in new else "")
    earlier = "\n".join([f"  [{r['id']}] guess: {flat(r['body']['guess'])}" for r in ledger if r["type"] == "why"]
                        + [f"  [{r['id']}] hypothesis ({st.get(r['id'], 'open')}): {flat(r['body']['text'])}" for r in ledger if r["type"] == "hypothesis"]) or "  (none yet)"
    rulings = "\n".join(f"  [{r['id']}] on {r['body']['for']}: {r['body']['result']}. {flat(r['body']['because'])}" for r in ledger if r["type"] == "verdict") or "  (none yet)"
    runs = {r["body"].get("run_id") for r in cited if r["type"] == "simulation"} | {q["body"].get("run_id") for r in cited if r["type"] == "evidence" for q in ledger if q["type"] == "simulation" and q.get("parent") == r["body"]["experiment"]}
    cites = "\n".join(mark(r) for r in cited) or "  (it cites the brief only: nothing has been measured for it)"
    the_guess = (f"The result it starts from, as the researcher states it: {flat(why['result'])}\nThe guess of why: {flat(why['guess'])}\n" + (f"What would make it so, not directly visible: {flat(why['unseen'])}\n" if why.get("unseen") else ""))
    ask = ("Before anything is built on this guess: first say what the cited records show about the result it starts from. Then name the earlier guess or hypothesis nearest to it. Then name the defect, or none. "
            "The defects: " + "; ".join(f"{k}: {v}" for k, v in GROUNDS.items()) + ". A guess may be wrong and still be sound here: you judge whether it starts from what was measured and adds something, "
            "not whether it is true. A guess that takes up an earlier one with a stated difference (another cause, another range, a reason why the earlier test was not fair) is not a repetition."
            + ("" if new is None else " This is not the researcher's first guess, and a later guess has to be the fruit of what was learned since the earlier ones. The records marked NEW are what it says it "
               "learned from. Say in your reasoning what they show that the earlier guesses did not have, and ask: would the researcher have made this same guess without them? If yes, the citation is "
               "for form only and the defect is not_from_what_was_learned."))
    if parts:   # the pieces of this review, for the batched first review
        return {"cites": cites, "guess": the_guess, "earlier": earlier, "rulings": rulings, "ask": ask}
    user = (_system_for_supervisor(brief) + "\nTHE RECORDS THE NEW GUESS CITES:\n" + cites
            + "\n\nEVERY READING OF THE SESSION, as the researcher's ledger holds them (the researcher asked; the harness read it from what the simulations recorded over time: these are measurements too, and a guess may start from them):\n" + _looked(ledger)
            + "\n\nTHE NEW GUESS\n" + the_guess + "\n"
            + f"THE SESSION'S EARLIER GUESSES AND HYPOTHESES:\n{earlier}\n\nTHE RULINGS SO FAR:\n{rulings}\n\n" + ask)
    d = pre if pre is not None else (ask_fn or supervise)(model, user, GROUND_SCHEMA)   # pre: its answer in the batched first review
    if pre is not None:
        user = pre_saw or ""
    return {"records_show": flat(d["records_show"]), "nearest_earlier": flat(d["nearest_earlier"]), "defect": d["defect"] if d["defect"] in GROUNDS else "none", "because": flat(d["because"])}, user


def _test_terms(ledger, xid, hid):
    """What a test was judged against before it ran, for its ruling and a second look (the coherence audit, 2026-11-22: the ruling saw neither): the
    researcher's rival of each rule and what it said the rule gives under it, a stronger rival the supervisor named in its last review, and the
    measurements the experiment defined."""
    flat = lambda v: " ".join(str(v).split())
    checks = [r for r in ledger if r["type"] == "check" and r["body"]["experiment"] == xid and r["body"]["for"] == hid]
    rev = next((r["body"] for r in reversed(ledger) if r["type"] == "review" and r.get("by") == "supervisor" and r["body"].get("gate") == "design" and r["body"].get("for") == hid), None)
    x = next((r["body"] for r in ledger if r["id"] == xid), {})
    out = "".join(f"THE RESEARCHER'S RIVAL for the rule {flat(c['body']['decision_rule'])}: {flat(c['body']['rival'])}; it said the rule gives {str(c['body'].get('rival_predicts')).upper()} if that rival is true\n" for c in checks if c["body"].get("rival"))
    if rev and rev.get("rival_is_weak") and rev.get("stronger_rival"):
        out += f"THE STRONGER RIVAL YOU NAMED IN YOUR REVIEW: {flat(rev['stronger_rival'])} (you said the rule gives {str(rev.get('rival_outcome')).upper()} under it)\n"
    out += "".join(f"A MEASUREMENT THE EXPERIMENT DEFINED: {m['name']} = {m['stat']} of {m['of']}" + (f" against the level {m['level']}" if m.get("level") is not None else "") + f", from {m.get('t_from') if m.get('t_from') is not None else 2} s to {m.get('t_to') if m.get('t_to') is not None else 'the end'}\n" for m in x.get("measurements") or [] if isinstance(m, dict))
    return out


def batch_schema(ng, nt):
    """The answer of the batched first review: one item for each new guess (gate 0's fields) and one for each test (round 1's fields)."""
    g_item = {"type": "object", "additionalProperties": False, "required": ["guess"] + GROUND_SCHEMA["required"],
              "properties": {"guess": {"type": "string", "description": "the guess's name in this request: G1, G2, ..."}, **GROUND_SCHEMA["properties"]}}
    t_item = {"type": "object", "additionalProperties": False, "required": ["for"] + REVIEW_SCHEMA["required"],
              "properties": {"for": {"type": "string", "description": "the hypothesis whose test this item reviews, as its heading names it"}, **REVIEW_SCHEMA["properties"]}}
    return {"type": "object", "additionalProperties": False, "required": ["guesses", "tests"], "properties": {
        "guesses": {"type": "array", "minItems": ng, "maxItems": ng, "items": g_item, "description": "one item for each new guess, in their order"},
        "tests": {"type": "array", "minItems": nt, "maxItems": nt, "items": t_item, "description": "one item for each test, in their order"}}}


def first_review(model, brief, ledger, guesses, tests, ask_fn=None):
    """The batched first review of a reply (stage 4 of the coherence audit, 2026-11-22): every new guess (gate 0) and every test (round 1) in one
    request; what all of them share is written once. guesses: the guesses as stated; tests: [(hypothesis, its test, its case text or None)].
    Returns (an answer or None for each guess, an answer or None for each test, what was shown). The answers are the raw items: each is then read
    as a review of its own would be (ground_of, review_design with pre)."""
    gp = [ground_of(model, brief, ledger, w, parts=True) for w in guesses]
    tp = [review_design(model, brief, ledger, ex, hid, case=case, parts=True) for hid, ex, case in tests]
    user = (_system_for_supervisor(brief) + f"\nWHAT HAS BEEN MEASURED SO FAR:\n{_measured(ledger)}\n\nEVERY READING OF THE SESSION, as the researcher's ledger holds them (what the tools returned "
            f"when the researcher looked: these are measurements too, and a guess may start from them):\n{_looked(ledger)}\n\n"
            + (f"THE SESSION'S EARLIER GUESSES AND HYPOTHESES:\n{gp[0]['earlier']}\n\nTHE RULINGS SO FAR:\n{gp[0]['rulings']}\n\n" if gp else "")
            + f"THIS REQUEST HOLDS EVERY NEW GUESS AND EVERY NEW TEST OF THE RESEARCHER'S REPLY IN THIS TURN ({len(guesses)} guess{'es' if len(guesses) != 1 else ''}, {len(tests)} test{'s' if len(tests) != 1 else ''}). "
              "Judge each on its own, as if it were asked alone, and answer each in its own item.\n\n"
            + "".join(f"== NEW GUESS G{i + 1} ==\nTHE RECORDS IT CITES:\n{q['cites']}\nTHE GUESS:\n{q['guess']}\n" for i, q in enumerate(gp))
            + "".join(f"== TEST OF {hid} ==\n{q['item']}" for (hid, _, _), q in zip(tests, tp))
            + (f"FOR EACH NEW GUESS (an item of guesses, named G1, G2, ... as above): {gp[0]['ask']}\n\n" if gp else "")
            + (f"FOR EACH TEST (an item of tests, by its hypothesis): {tp[0]['ask']}" if tp else ""))
    n = len(guesses) + len(tests)
    d = (ask_fn or (lambda m, u, sc: supervise(m, u, sc, 9000 + 2000 * (n - 1))))(model, user, batch_schema(len(guesses), len(tests)))   # 4,500 reasoning tokens and 1,000 more for each further item
    gs = {str(x.get("guess")): x for x in d.get("guesses") or [] if isinstance(x, dict)}
    ts = {str(x.get("for")): x for x in d.get("tests") or [] if isinstance(x, dict)}
    return [gs.get(f"G{i + 1}") for i in range(len(guesses))], [ts.get(hid) for hid, _, _ in tests], user


def test_key(ex, hid, h_text):
    """What makes a test the same in the batched first review and in round 1: its hypothesis, its rules and the simulations they name."""
    rules = [{k: d.get(k) for k in ("decision_rule", "rival", "rival_predicts")} for d in ex.get("decision_rules") or [] if d.get("for") == hid]
    need = next((n for n in ex.get("needs") or [] if n.get("for") == hid), {})
    runs = [{k: r.get(k) for k in ("label", "params", "structure")} for r in ex.get("runs") or [] if r.get("label") in (need.get("simulations") or [q.get("label") for q in ex.get("runs") or []])]
    return json.dumps([" ".join(str(h_text).split()), rules, runs], sort_keys=True)


def rule_on(model, brief, ledger, xid, hid, doubt_if, ask_fn=None, contested=None):
    """Gate 2. The supervisor's ruling on one tested hypothesis after the harness has checked its rules: (ruling, what it was shown).
    ruling = {shows, fair, defect, result, because, retest, checks}. The checks are facts: supported needs every check HELD, refuted needs one that
    FAILED, and either needs a fair test; a ruling that does not fit is recorded as inconclusive, and the record says that the harness changed it."""
    flat = lambda v: " ".join(str(v).split())
    checks = [r for r in ledger if r["type"] == "check" and r["body"]["experiment"] == xid and r["body"]["for"] == hid]
    rules = [{"decision_rule": c["body"]["decision_rule"]} for c in checks]
    lines = "\n".join(f"  [{c['id']}] {flat(c['body']['decision_rule'])}  ->  {c['body']['with_numbers']}  :  {c['body']['result'].upper()}"
                       + "".join(f"  (note: {q['left']} against {q['right']} differ by {q['percent']:.3g} %)" for q in c["body"].get("within_tolerance") or []) for c in checks)
    user = (_system_for_supervisor(brief) + "\n" + _case(ledger, hid, rules) + f"\nTHE SIMULATIONS OF THIS TEST, as measured:\n{_measured(ledger, xid)}\n\nTHE BASELINE and what was measured before:\n{_measured([r for r in ledger if not (r['type'] == 'evidence' and r['body']['experiment'] == xid)])}\n\n"
            f"EVERY READING OF THE SESSION, as the researcher's ledger holds them (what the tools returned when the researcher looked: measurements too):\n{_looked(ledger)}\n\nTHE HARNESS'S CHECKS (facts):\n{lines}\n\n" + _test_terms(ledger, xid, hid) + "\n" + (f"Before the simulations you wrote what would make you doubt this test: {doubt_if}\n\n" if doubt_if else "")
            + (f"BEFORE IT RAN, the review of this test ended with you still objecting, after the last round: {flat(contested)}\n\n" if contested else "")   # contested (2026-11-22)
            + "What does this test show about the hypothesis? supported: every check HELD and the test was a fair one. refuted: a check FAILED and the test was a fair one. inconclusive: the test "
              "was not fair (name the defect and what a fair test would compare), or the checks disagree. A check that failed because another setting limited the result, or one that held "
              "although it would have held under a rival explanation too, is not a fair test. The defects: " + "; ".join(f"{k}: {v}" for k, v in DEFECTS.items()) + "."
            + f"\n\nTHE FINDINGS SO FAR:\n{findings_for_supervisor(ledger)}\n" + SUP_FINDINGS_ASK)   # findings (2026-11-22)
    d = (ask_fn or supervise)(model, user, RULING_SCHEMA)
    res = [c["body"]["result"] for c in checks]
    fits = {"supported": all(x == "held" for x in res) and d["fair"], "refuted": any(x == "failed" for x in res) and d["fair"], "inconclusive": True}.get(d["result"], False)
    ruling = {"shows": flat(d["shows"]), "fair": bool(d["fair"]), "defect": d["defect"] if d["defect"] in DEFECTS else "none", "result": d["result"] if fits else "inconclusive", "because": flat(d["because"]),
              "retest": flat(d.get("retest") or ""), "checks": [c["id"] for c in checks], "findings": list(d.get("findings") or []) if isinstance(d.get("findings"), list) else [], **({"findings_cut": True} if d.get("findings_cut") else {}), **({} if fits else {"changed_by_harness": f"the supervisor said {d['result']}, which does not fit the checks ({', '.join(res)}) or its own finding that the test was {'fair' if d['fair'] else 'not fair'}"})}
    return ruling, user


def answer_objection(model, brief, ledger, verdict, objection, ask_fn=None):
    """The supervisor's second look at one of its rulings, after the researcher's objection: ({stands, result, because, answer}, what it was shown)."""
    flat = lambda v: " ".join(str(v).split())
    b, hid = verdict["body"], verdict["body"]["for"]
    checks = [r for r in ledger if r["id"] in (b.get("checks") or [])]
    xid = checks[0]["body"]["experiment"] if checks else None
    lines = "\n".join(f"  [{c['id']}] {flat(c['body']['decision_rule'])}  ->  {c['body']['with_numbers']}  :  {c['body']['result'].upper()}" for c in checks)
    user = (_system_for_supervisor(brief) + "\n" + _case(ledger, hid, [{"decision_rule": c["body"]["decision_rule"]} for c in checks]) + f"\nTHE SIMULATIONS OF THE TEST, as measured:\n{_measured(ledger, xid)}\n\nEVERYTHING MEASURED IN THE SESSION:\n{_measured(ledger)}\n\n"
            f"EVERY READING OF THE SESSION, as the researcher's ledger holds them:\n{_looked(ledger)}\n\n"   # the readings, the rivals and the measurements, as at the ruling (the coherence audit, 2026-11-22)
            f"THE HARNESS'S CHECKS (facts):\n{lines}\n\n" + (_test_terms(ledger, xid, hid) if xid else "") + "\nYOUR RULING [{verdict['id']}]: {b['result']}. {b['because']}" + (f" Defect: {DEFECTS.get(b.get('defect'), '')}." if not b.get("fair", True) else "")
            + f"\n\nTHE RESEARCHER OBJECTS: {flat(objection)}\n\nLook at the records again. An objection is right only for what the records show, not for how sure it sounds. Does your ruling stand? "
              "First say whether the test was fair: one that could have come out the other way if the hypothesis were false (a rival that passes the rule too, or another setting that "
              "limited the result, makes it unfair). supported needs every check HELD and a fair test, refuted needs a check that FAILED and a fair test; otherwise inconclusive.")
    d = (ask_fn or supervise)(model, user, APPEAL_SCHEMA)
    res = [c["body"]["result"] for c in checks]
    fair = bool(d.get("fair", b.get("fair", True)))
    result = b["result"] if d["stands"] else d["result"]
    if (result == "supported" and not (all(x == "held" for x in res) and fair)) or (result == "refuted" and not (any(x == "failed" for x in res) and fair)):
        result = "inconclusive"
    return {"stands": result == b["result"], "result": result, "fair": fair, "because": flat(d["because"]), "answer": flat(d["answer"])}, user


ROLES = ("supports", "background", "limits")  # what a claim of a final report does: a reason for the recommendation, how the system behaves, when the recommendation would change

def check_report(rep, brief, ids, ledger=None, lean=False):
    """None if the final report can be accepted; otherwise what is wrong with it. ledger: the session's records, to know which knobs it varied."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    for k in (("goal", "explanation") if lean else ("goal", "explanation", "holds_when", "breaks_when")):   # lean: the short report of the arm "supervised"
        if not text(rep.get(k)):
            return f"report.{k} must be a text"
    # Why the result is not better, and which settings made no meaningful difference: the two parts that keep a report from naming a "best" setting
    # without saying what limits the result (s031 recommended a TCP type and a seed for differences of 0.02 % and never asked what held TCP at its limit).
    if not text(rep.get("limit")):
        return "report.limit must be a text: what limits the result at your recommendation (why it is not better) and the ledger ids that show it; if you did not find it, say so and what you would test next"
    nd = rep.get("no_difference")
    if not isinstance(nd, list) or not all(isinstance(k, str) for k in nd):
        return "report.no_difference must be a list of knob names (it may be empty): the knobs whose tested values made no meaningful difference to the goal"
    if set(nd) - set(brief["knobs"]):
        return f"report.no_difference names something that is not a knob: {', '.join(sorted(set(nd) - set(brief['knobs'])))}"
    if ledger is not None:
        seen = {}
        for q in ledger:
            if q["type"] == "simulation":
                for k, v in (q["body"].get("params") or {}).items():
                    seen.setdefault(k, set()).add(json.dumps(v))
        untested = [k for k in nd if len(seen.get(k, ())) < 2]
        if untested:
            return f"report.no_difference names {', '.join(untested)}, which this session never varied: a setting that was not tested cannot be said to make no difference"
    rec, exp, claims, open_q = rep.get("recommendation"), rep.get("expected"), rep.get("claims"), rep.get("open_questions")
    edits = []
    if may_change(brief):  # the structure it recommends: a list of changes to the brief's network (empty: as given)
        if not isinstance(rep.get("structure"), list):
            return "report.structure must be a list of changes to the network of the brief (an empty list: the network as given)"
        edits = edits_of(rep, brief)
        why = structure_problem(edits, brief)
        if why:
            return f"report.structure cannot be used: {why}"
    if not isinstance(rec, dict) or not rec:
        return "report.recommendation must give at least one knob and its value"
    if set(rec) & set(brief["system"]):
        return f"report.recommendation contains a setting the brief fixes, which cannot be recommended: {', '.join(sorted(set(rec) & set(brief['system'])))}"
    if set(rec) - set(brief["knobs"]):
        return f"report.recommendation names something that is not a knob: {', '.join(sorted(set(rec) - set(brief['knobs'])))}"
    if [k for k in brief["knobs"] if k not in rec]:  # the answer format requires every knob (answer_format); this is the guard, as tools.clamp(design=) is for a design
        return "report.recommendation must state a value for every knob of the brief (a knob left as it was is stated with the value it has); missing: " + ", ".join(k for k in brief["knobs"] if k not in rec)
    try:
        clamps = tools.clamp(rec)[1]
    except (ValueError, TypeError) as e:
        return f"report.recommendation has a value that cannot be read: {e}"
    if clamps:
        return "report.recommendation has a value outside its allowed range: " + ", ".join(f"{k}={asked}" for k, (asked, _) in clamps.items())
    if not isinstance(exp, dict) or set(exp) - set(outputs_of(edits, brief)) or not all(type(v) in (int, float) for v in exp.values()):
        return "report.expected must give numbers for outputs (by their names)"
    if not isinstance(claims, list) or not all(isinstance(c, dict) and text(c.get("text")) and isinstance(c.get("evidence"), list) for c in claims):
        return "report.claims must be a list of {text, role, evidence: [ledger ids]}"
    norole = [str(i + 1) for i, c in enumerate(claims) if c.get("role") not in ROLES]  # what each claim does in the argument: the page orders the report by it
    if norole:
        return f"report.claims: claim {', '.join(norole)} has no role: give each claim its role, one of {', '.join(ROLES)}"
    missing = sorted({i for c in claims for i in c["evidence"] if i not in ids})
    if missing:
        return f"report.claims cites ids that are not in the ledger: {', '.join(map(str, missing))}"
    if not isinstance(open_q, list) or not all(isinstance(q, str) for q in open_q):
        return "report.open_questions must be a list of texts (it may be empty)"
    return None

def experiment_problem(ex, brief, ledger, left, st, lean=False):
    """None if the experiment can be run as designed; otherwise what is wrong with it. st: the hypotheses' states with the
    accepted parts of the same answer already applied. left None: the experiment as it was sent, before trim() (how many
    simulations it needs is counted afterwards, on what trim leaves)."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    runs, per = ex.get("runs") or [], brief["limits"]["simulations_per_experiment"]
    labels = [r.get("label") for r in runs]
    if not 1 <= len(runs) <= per:
        return f"an experiment has 1 to {per} simulations"
    if len(set(labels)) != len(labels) or not all(re.fullmatch(rf"[A-Za-z0-9_]{{1,{LABEL_MOST}}}", str(l)) for l in labels):
        return f"every simulation needs its own label: letters, digits and _ only, at most {LABEL_MOST} characters"
    if any(set(r.get("params") or {}) - set(brief["knobs"]) - set(brief["system"]) for r in runs):
        return "a simulation's params has keys that are not settings of the brief"
    for r in runs:  # a brief that lets the structure be changed: each simulation's changes must give a network that can be built, within the brief's limits
        why = structure_problem(edits_of(r, brief), brief)
        if why:
            return f"simulation `{r['label']}`: its structure cannot be used: {why}"
    has = {r["label"]: outputs_of(edits_of(r, brief), brief) for r in runs}   # the measures each simulation will have
    every = {k: v for o in has.values() for k, v in o.items()}
    try:
        planned = plan(ledger, runs, complete=left is not None)
        fresh = sum(1 for r in planned if not r["prior"] and not r["twin"])  # simulations already run in this session are not run again
    except (ValueError, TypeError) as e:
        return f"a simulation has a setting that cannot be read: {e}"
    if left is not None and fresh > left:
        return f"the experiment needs {fresh} new simulations but only {left} are left in the budget"
    if left is not None and fresh > spend_cap(left, per):
        return (f"the experiment needs {fresh} new simulations; with {left} left, one experiment may run at most {spend_cap(left, per)} (half of what is left), "
                "so that something remains for what its results raise. Keep the simulations that decide your hypotheses and leave the others out")
    if ex.get("control") not in (None, "", *labels) or set(ex.get("varied") or []) - set(brief["knobs"]):
        return "control must be the label of one of the simulations (or null), and varied must name knobs"
    tests, rs = ex.get("tests") or [], ex.get("decision_rules") or []
    if ex.get("kind") == "test":
        if not tests or any(st.get(h) != "open" for h in tests):
            return "a test experiment needs tests: the ids of open hypotheses"
        if any(r.get("for") not in tests for r in rs) or set(tests) - {r.get("for") for r in rs}:
            return "a test experiment needs at least one decision rule for each tested hypothesis, and none for any other"
        for r in rs:
            try:
                absent = [(m, l) for m, l in decision_rules.pairs(r.get("decision_rule"), every, labels) if m not in has[l]]
            except decision_rules.DecisionRuleError as e:
                return f"the decision rule for {r['for']} cannot be read: {e}. Decision rule: {r.get('decision_rule')}"
            if absent:
                return (f"the decision rule for {r['for']} names {absent[0][0]}@{absent[0][1]}, but the network of simulation `{absent[0][1]}` has no such measure: "
                        "a decision rule may only name measures that exist in every simulation it names")
            if lean:   # the arm "supervised": each test's rival is checked on its own before the supervisor's review (rival_problem, design rounds), so that one test's slip does not stop the others
                continue
            why = rival_problem(r)
            if why:
                return why
        why = needs_problem(ex, brief, planned, full=left is not None)
        if why:
            return why
    elif ex.get("kind") == "explore":
        if not text(ex.get("question")) or tests or rs or ex.get("needs"):
            return "an explore experiment needs a question, and has no tests, no needs and no decision rules"
    else:
        return "experiment.kind must be test or explore"
    return None

def rule_size_problem(r):
    """The arm "supervised": what is wrong with the size of one decision rule, or None (at most COMPARISONS_MOST comparisons)."""
    k = decision_rules.comparisons_in(r.get("decision_rule"))
    return (f"the decision rule for {r.get('for')} makes {k} comparisons, and a rule makes at most {COMPARISONS_MOST}: a rule that needs more asks more than one "
            "question. Decide the hypothesis by the one comparison its guess predicts, and leave the rest to a later test") if k > COMPARISONS_MOST else None


def rival_problem(r):
    """What is wrong with the rival of one decision rule, or None: a rival (a competing explanation, one sentence) and rival_predicts (held or failed),
    and a rival under which the rule would hold too is refused. The arm "hypotheses" since 2026-11-17; the arm "supervised" since 2026-11-22 (after
    the reviews of s047 and s050: the researcher states its own rival, and the harness refuses "held" before any call to the supervisor)."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    if not text(r.get("rival")) or r.get("rival_predicts") not in ("held", "failed"):
        return f"the decision rule for {r.get('for')} needs a rival (a competing explanation of how the system behaves) and rival_predicts (held or failed)"
    if r["rival_predicts"] == "held":
        return "this decision rule would hold under the rival too; choose simulations where the two explanations give different results"
    return None

def trim(ex, brief, ledger):
    """A plan that cannot test anything is cut back before anything is run: (what is left of the experiment, or None when
    nothing is; [(part, reason), ...]). ex has passed experiment_problem(left=None). In this order:
    a design that does not state every knob is refused (the guard behind the answer format);
    a knob listed as varied that has one value in every design: the whole experiment is refused;
    a decision rule that names two labels of one simulation (same settings and seed) is refused;
    of two designs with the same settings and seed, the later one is refused;
    a decision rule that names a refused design is refused; a design that only refused decision rules name is not run;
    a tested hypothesis left without a decision rule is no longer tested by this experiment.
    No reason says anything about the system: each speaks only of the model's own plan."""
    cuts, runs, key, clean = [], [], {}, {}
    for r in ex["runs"]:
        try:
            clean[r["label"]] = tools.clamp(r.get("params") or {}, design=r["label"])[0]
        except tools.Missing as e:
            cuts.append((f"design {r['label']}", str(e)))
            continue
        key[r["label"]] = design_key(clean[r["label"]], edits_of(r))
        runs.append(r)
    if not runs:
        return None, cuts + [("experiment", "no design of this experiment is left, so nothing is run")]
    for k in ex.get("varied") or []:
        if len({dict(key[r["label"]][0])[k] for r in runs}) == 1:
            return None, cuts + [("experiment", f"`{k}` is listed as varied but has the single value `{clean[runs[0]['label']][k]}` in every design")]
    labels, rules, refused = [r["label"] for r in ex["runs"]], ex.get("decision_rules") or [], set()
    every = {k: v for r in ex["runs"] for k, v in outputs_of(edits_of(r)).items()}
    named = [decision_rules.names(d["decision_rule"], every, labels) for d in rules]
    for i, d in enumerate(rules):
        pair = next(((a, b) for j, a in enumerate(named[i]) for b in named[i][j + 1:] if a in key and b in key and key[a] == key[b]), None)
        if pair:
            refused.add(i)
            cuts.append((f"decision rule for {d['for']}", f"this decision rule compares `{pair[0]}` with `{pair[1]}`, which are the same simulation (same settings and seed), "
                                                          "so it cannot hold or fail for a reason; change the designs or the rule"))
    first, kept = {}, []
    for r in runs:
        if key[r["label"]] in first:
            cuts.append((f"design {r['label']}", f"design `{r['label']}` has the same settings and seed as `{first[key[r['label']]]}`; give it different settings or remove it"))
        else:
            first[key[r["label"]]] = r["label"]
            kept.append(r)
    for i, d in enumerate(rules):
        gone = [l for l in named[i] if l not in first.values()]
        if i not in refused and gone:
            refused.add(i)
            cuts.append((f"decision rule for {d['for']}", f"this decision rule names `{gone[0]}`, a design that was refused; change the designs or the rule"))
    # a decision rule all of whose simulations were already run earlier in the session can only repeat what is known: it cannot fail, so it is no test
    # (2026-11-17: 12 such rules in s026 to s041, all "held", all cited as evidence by the final report; s041 H5 and s033 H14 "tested" the limit they
    # had already measured). The design that equals an earlier simulation may still stand as the control of a rule that also names a new one.
    try:
        prior = {r["label"]: r["prior"]["id"] for r in plan(ledger, kept, complete=False) if r["prior"]}
    except (ValueError, TypeError):
        prior = {}
    for i, d in enumerate(rules):
        if i not in refused and named[i] and all(l in prior for l in named[i]) and not any(re.search(rf"(?<![A-Za-z0-9_]){re.escape(n)}@", d["decision_rule"]) for n in MEASURES):   # a measurement of its own is made only now: its result is not known
            refused.add(i)
            cuts.append((f"decision rule for {d['for']}", f"this decision rule names only results that are already in the ledger ({', '.join(f'{l} = {prior[l]}' for l in dict.fromkeys(named[i]))}), so it cannot fail and is no test. "
                                                          "What the known results show belongs in a why or in observations; a test needs a simulation whose result you do not know yet"))
    if not cuts:
        return ex, []
    still = {l for i in range(len(rules)) if i not in refused for l in named[i]}
    for r in list(kept):  # nothing is run for a refused decision rule's hypothesis
        if r["label"] not in still and any(r["label"] in named[i] for i in refused):
            kept.remove(r)
            cuts.append((f"design {r['label']}", f"design `{r['label']}` is named only by a decision rule that was refused, so it is not run"))
    rules = [d for i, d in enumerate(rules) if i not in refused]
    tests = [h for h in ex.get("tests") or [] if any(d["for"] == h for d in rules)]
    if not kept:
        return None, cuts + [("experiment", "no design of this experiment is left, so nothing is run")]
    if ex.get("kind") == "test" and not tests:
        return None, cuts + [("experiment", "no decision rule of this experiment is left, so nothing is run")]
    left_labels = {r["label"] for r in kept}   # what is left of the needs: those of the hypotheses still tested, with the designs that are still run
    needs = [{**n, "simulations": [l for l in n.get("simulations") or [] if l in left_labels]} for n in ex.get("needs") or [] if isinstance(n, dict) and n.get("for") in tests]
    return {**ex, "runs": kept, "decision_rules": rules, "tests": tests, "needs": needs, "control": ex.get("control") if ex.get("control") in left_labels else None}, cuts

def sort_out(t, brief, ledger, left, mode=None, insist=True, judge=None, supervised=False, ground=None, short=False, restate=None):
    """The parts of an answer that can be used, and the parts that cannot, each with the reason: (ok, refused).
    ok = {verdicts, drop, hypotheses, experiment, report, budget_request}; refused = [(part, reason), ...].
    A refused part is left out and the rest is accepted. mode: None for an ordinary turn; "budget" for the last turn
    after the budget is used up (no experiment); "report" for a last turn that accepts only the final report; "free" for one of the FREE_TURNS
    after the budget is used up: an ordinary turn whose experiment may use only simulations already run, and no budget_request."""
    free, mode = mode == "free", (None if mode == "free" else mode)
    text = lambda v: isinstance(v, str) and bool(v.strip())
    st, checked = states(ledger)
    ok, no = {"verdicts": [], "drop": [], "rethink": [], "whys": [], "hypotheses": [], "experiment": None, "report": None, "budget_request": None, "objections": []}, []
    only = "this last turn accepts only the final report"
    # the arm "supervised": the verdicts are the supervisor's. The researcher may object to one of them, once; the supervisor then looks at it again
    ruled = {r["id"]: r for r in ledger if r["type"] == "verdict" and r.get("by") == "supervisor"}
    objected = {r["body"]["to"] for r in ledger if r["type"] == "objection"}
    for o in (t.get("objections") or []) if supervised else []:
        to = o.get("to") if isinstance(o, dict) else None
        if mode == "report":
            no.append(("objection", only))
        elif to not in ruled:
            no.append(("objection", f"an objection names a ruling of the supervisor by its id (to: for example V2): {to!r} is not one"))
        elif to in objected or any(q["to"] == to for q in ok["objections"]) or ruled[to]["body"].get("after"):
            no.append((f"objection to {to}", "a ruling is objected to once, and the supervisor's second look stands"))
        elif not text(o.get("because")):
            no.append((f"objection to {to}", "an objection says what in the records shows that the ruling is wrong (because)"))
        else:
            ok["objections"].append({"to": to, "because": o["because"]})
    for v in t.get("verdicts") or []:
        part = f"verdict for {v.get('for')}"
        if supervised:
            no.append((part, "in this session the verdicts are the supervisor's: it rules on each tested hypothesis after the checks. If you think a ruling is wrong, object to it (objections)"))
        elif mode == "report":
            no.append((part, only))
        elif st.get(v.get("for")) != "open":
            no.append((part, f"{v.get('for')} is not an open hypothesis"))
        elif v["for"] not in checked:
            no.append((part, "no decision rule of that hypothesis has been checked yet, so there is nothing to judge it by"))
        elif v.get("result") not in ("supported", "refuted", "inconclusive") or not text(v.get("because")):
            no.append((part, "a verdict needs a result (supported, refuted or inconclusive) and a because"))
        else:
            ok["verdicts"].append(v)
            st[v["for"]] = v["result"]
    for d in t.get("drop") or []:
        part = f"drop of {d.get('id')}"
        if mode == "report":
            no.append((part, only))
        elif d.get("id") in checked and st.get(d["id"]) == "open" and not supervised:   # the arm "supervised": only the supervisor rules; a checked hypothesis still open has no ruling, and may be dropped (the coherence audit, 2026-11-22)
            no.append((part, f"{d['id']} has a checked decision rule, so it cannot be dropped: it needs a verdict (supported, refuted or inconclusive) instead"))
        elif st.get(d.get("id")) != "open" or not text(d.get("why")):
            no.append((part, f"{d.get('id')} must be an open hypothesis, and a drop needs a reason"))
        else:
            ok["drop"].append(d)
            st[d["id"]] = "dropped"
    known, kinds = len([r for r in ledger if r["type"] == "hypothesis"]), {r["id"]: r["type"] for r in ledger}
    for i in range(len(ok["verdicts"])):  # a verdict given in this same answer can be cited: the id it is about to get
        kinds[f"V{sum(r['type'] == 'verdict' for r in ledger) + i + 1}"] = "verdict"
    # the chain (2026-11-17, the operator): a result, informed guesses of why it came out so, which of them are worth verifying for the goal, and
    # only from those a hypothesis. A why names records that exist; a hypothesis names a why that was chosen to be verified.
    whys = {r["id"]: r["body"] for r in ledger if r["type"] == "why"}
    n_why = len(whys)
    # what a why read in a tool's result (a series, a trace) is about that run's simulation: "series r001" or "r001" stands for the simulation of
    # run r001 (s041, 2026-11-17: three whys about a series were refused, and with them the turn's hypotheses and experiment)
    run_sim = {r["body"]["run_id"]: r["id"] for r in ledger if r["type"] == "simulation" and r["body"].get("run_id")}
    def of_run(a):
        m = re.fullmatch(r"(?:[A-Za-z_ ]+[ :])?\s*(r\d+)", a.strip()) if isinstance(a, str) else None
        return run_sim.get(m.group(1), a) if m else a
    # what the tools returned about each run (its T records): a rethink that names a run id rests on that run's simulation and on its readings (s048, 2026-11-22)
    by_id, readings_of = {r["id"]: r for r in ledger}, {}
    for r in ledger:
        if r["type"] == "result":
            args = ((by_id.get(r.get("parent")) or {}).get("body") or {}).get("args") or {}
            if args.get("run_id") or args.get("run"):
                readings_of.setdefault(args.get("run_id") or args.get("run"), []).append(r["id"])
    run_of = lambda a: (m.group(1) if isinstance(a, str) and (m := re.fullmatch(r"(?:[A-Za-z_ ]+[ :])?\s*(r\d+)", a.strip())) else None)
    # A why is not fixed by how it was first stated. Its standing now (stand) is what a rethink or a revising why last made it; it is fresh when no
    # result has come in since it was last settled, when this answer rethinks it, or when it is one of this answer's own. A hypothesis comes only from
    # a why that is worth verifying AND fresh: the early guesses are looked at again in the light of each new result before anything is built on them.
    ws = why_states(ledger)
    stand = {y: w["worth"] for y, w in ws.items()}
    if supervised:   # no rethink in this arm: a guess all of whose hypotheses the supervisor ruled refuted is refuted, and nothing more comes from it unless a new why revises it
        of = {}
        for r in ledger:
            if r["type"] == "hypothesis" and r["body"].get("from_why"):
                of.setdefault(r["body"]["from_why"], []).append(st.get(r["id"]))
        stand.update({y: "refuted" for y, v in of.items() if stand.get(y) == "verify" and v and all(x == "refuted" for x in v)})
    revised_as = {y: w["as"] for y, w in ws.items() if w.get("as")}
    later = {y: since(ledger, w["at"]) + [f"V{sum(r['type'] == 'verdict' for r in ledger) + i + 1}" for i in range(len(ok["verdicts"]))] for y, w in ws.items()}
    later_r = {y: since(ledger, w["at"], readings=True) + [f"V{sum(r['type'] == 'verdict' for r in ledger) + i + 1}" for i in range(len(ok["verdicts"]))] for y, w in ws.items()}   # and the readings since (s048)
    fresh = set(ws) if supervised else {y for y in ws if not later[y]}
    for k in (t.get("rethink") or []) if not supervised else []:
        y = k.get("id") if isinstance(k, dict) else None
        light = [of_run(a) for a in k["in_light_of"]] if isinstance(k, dict) and isinstance(k.get("in_light_of"), list) else None
        if light:   # a run id stands for its simulation and for what the tools returned about that run (s048: Y11 "in the light of r010")
            light = list(dict.fromkeys(light + [x for a in k["in_light_of"] if run_of(a) for x in readings_of.get(run_of(a), [])]))
        if mode == "report":
            no.append(("rethink", only))
        elif y not in ws:
            no.append(("rethink", f"a rethink names an earlier why of the ledger by the why's own id (Y1, Y2, ...): {y!r} is not one (the K numbers are those of rethinks; a why of this same answer needs none)"))
        elif stand[y] == "revised":
            no.append((f"rethink of {y}", f"{y} was revised as {revised_as.get(y)}: rethink that one instead"))
        elif any(q["id"] == y for q in ok["rethink"]):
            no.append((f"rethink of {y}", f"{y} is looked at once in an answer"))
        elif k.get("now") not in ("verify", "set_aside", "refuted", "supported") or not text(k.get("because")):
            no.append((f"rethink of {y}", "a rethink says what the why is now (now: verify, set_aside, refuted or supported) and because of what in the results"))
        elif not light or any(kinds.get(a) not in ("evidence", "simulation", "check", "verdict", "result") for a in light):
            no.append((f"rethink of {y}", "in_light_of must list the results you looked at it again with: ids of evidence tables, simulations, checks, verdicts or readings in the ledger (for example E2, C3, T7), or a run id for that run's simulation and what the tools returned about it (for example r010)"))
        elif later[y] and not set(light) & set(later_r[y]):   # a reading since counts as new (s048, 2026-11-22: the rethink of Y11 resting on T10 to T12)
            no.append((f"rethink of {y}", f"in_light_of must name at least one result that came in after {y} was last settled, or a reading seen since ({', '.join(later_r[y][-6:])}): a rethink looks at a why again in the light of what was measured since"))
        else:
            ok["rethink"].append({"id": y, "in_light_of": light, "now": k["now"], "because": k["because"]})
            stand[y] = k["now"]
            fresh.add(y)
    # the review of the step from one hypothesis to the next: the guesses whose hypotheses were checked since they were last settled must be rethought
    # in this answer before it goes on to a new hypothesis or an experiment (and before the report). A new why that replaces one of them settles it too.
    tested = {} if supervised else tested_whys(ledger)
    due = lambda: {y: v for y, v in tested.items() if stand.get(y) == "verify" and not any(q["id"] == y for q in ok["rethink"])}
    FIRST = ("first look again at the guesses that were just tested: {}. Give a rethink for each in this answer (id: the why's own id, for example Y4, never a K number; now: supported, "
             "refuted, verify or set_aside; because: what in those results makes it so). No new hypothesis and no experiment is accepted until then: this is the review of the step from "
             "one hypothesis to the next")
    def why_problem(w, ask=True):
        """What keeps a new why out, and by whom: (reason or None, "harness" or "supervisor", the supervisor's reading or None). ask: whether the
        supervisor is asked (gate 0); a guess restated after a refusal of the harness's is checked by the harness alone (2026-11-22)."""
        about = w.get("about") if isinstance(w, dict) else None
        if not isinstance(w, dict) or not all(text(w.get(k)) for k in (("result", "guess") if supervised else ("result", "guess", "unseen", "matters") if short else ("result", "guess", "unseen", "matters", "reason"))):
            return ("a why needs result (the result it is about, in one sentence), guess (why it came out so), unseen (what in the system, not directly visible, would make it so), "
                    + ("and matters (how it could matter for the goal)" if short else "matters (how it could matter for the goal) and reason (why it is or is not worth verifying now)")), "harness", None
        if w.get("worth") not in ("verify", "set_aside"):
            return "a why says whether it is worth verifying now: worth is verify or set_aside", "harness", None
        if not isinstance(about, list) or not about or any(a != "brief" and kinds.get(a) not in ("evidence", "simulation", "check", "verdict", "result") + (("review",) if supervised else ()) for a in about):
            bad = [a for a in about or [] if a != "brief" and a not in kinds] if isinstance(about, list) else []
            return ((f"about names ids that are not in the ledger: {', '.join(map(str, bad))}" if bad else
                     "about must list the records whose result the why explains: ids of evidence tables, simulations, checks, verdicts or readings in the ledger (for example E2, C3, T7), "
                     "a run id for what you read in that run's series or trace (for example r001), or the word brief")), "harness", None
        if supervised and (new_since := learned_since(ledger)) is not None and not any(a in new_since for a in about):
            # the chain: a later guess is the fruit of what was learned since the earlier ones (s047: five guesses in four turns, each from the baseline again)
            return ("this guess starts only from records your earlier guesses already had (" + ", ".join(map(str, about)) + "). A later guess must come from something learned since: "
                    "a ruling, a check, a new result table, a reading a tool returned, or a review in which the supervisor objected. Name its id in about (for example V2, C3, E2, T7, G4) and say in "
                    "result what it showed" + (f"; made since your last guess: {', '.join(sorted(new_since, key=lambda i: (i[0], int(i[1:]))))}" if new_since else
                    "; nothing has been learned since your last guess: test what is open, or look with a request, before you guess again")), "harness", None
        if w.get("revises") is not None and (w["revises"] not in ws or stand[w["revises"]] == "revised"):
            return "revises is null, or the id of an earlier why in the ledger that this one replaces with a better guess (one that has not been revised already)", "harness", None
        if ground is not None and ask:
            g = ground(w)
            if g["refuse"]:
                # gate 0 (the arm "supervised"): the supervisor read the records the guess cites. A guess that does not start from what they show, or that only
                # says an earlier one again, is refused once; stated again it is accepted, and its review says that the supervisor still objects
                return (f"the supervisor does not accept this guess as it stands: {GROUNDS[g['defect']]}. The records show: {g['records_show']} {g['because']} "
                        "State what the cited records show, and what in them is new, or leave the guess. No hypothesis can come from a guess that was not accepted"), "supervisor", g
            return None, None, g
        return None, None, None

    def made_whole(w2, w):
        """A restated guess that still fails is accepted all the same (contested): what keeps it from being a record at all is filled from its first
        statement (2026-11-22): texts, the ids of about that are records (or the first statement's, or the brief), revises only when it names an earlier why."""
        w2 = {**w2, **{k: w.get(k) for k in ("result", "guess", "unseen", "matters", "reason") if not text(w2.get(k)) and text(w.get(k))}, "worth": w2.get("worth") if w2.get("worth") in ("verify", "set_aside") else "verify"}
        good = lambda xs: [a for a in xs or [] if isinstance(a, str) and (a == "brief" or kinds.get(a) in ("evidence", "simulation", "check", "verdict", "result", "review"))]
        w2["about"] = good(w2.get("about")) or good(w.get("about")) or ["brief"]
        if w2.get("revises") is not None and (w2["revises"] not in ws or stand[w2["revises"]] == "revised"):
            w2["revises"] = None
        return w2

    why_map, h_map = {}, {}   # an id by position in this answer -> the id it was recorded with, or None (not accepted): the coherence audit, 2026-11-22
    for k_w, w in enumerate(t.get("whys") or []):
        pid = f"Y{n_why + k_w + 1}"
        why_map[pid] = None
        if isinstance(w, dict) and isinstance(w.get("revises"), str) and w["revises"] in why_map:   # an earlier guess of this same answer, by the id it was to get
            w["revises"] = why_map[w["revises"]]
        if isinstance(w, dict) and isinstance(w.get("about"), list):
            w["about"] = list(dict.fromkeys(of_run(a) for a in w["about"]))
        if mode == "report":
            no.append(("new why", only))
            continue
        why, by, g = why_problem(w)
        if why and restate is not None and isinstance(w, dict) and text(w.get("guess")):
            # the arm "supervised" (2026-11-22, the operator, after s050 and s051: a refused guess took its hypotheses and the test down with it): the guess
            # comes back once, in this turn, to be restated; then it is accepted, contested if it still fails, and nothing built on it falls
            first = {"by": by, "reason": why, "was": {k: w.get(k) for k in ("about", "result", "guess", "revises")}}
            w2 = restate(w, why, by)
            if isinstance(w2, dict):
                w2 = {**w, **{k: v for k, v in w2.items() if k in ("about", "result", "guess", "revises")}}
                if isinstance(w2.get("about"), list):
                    w2["about"] = list(dict.fromkeys(of_run(a) for a in w2["about"]))
            else:
                w2, first["unread"] = dict(w), True   # a restatement that could not be read: the guess as first stated goes on, contested
            why2, by2, g2 = why_problem(w2, ask=by == "supervisor")   # checked again: by the supervisor only when the supervisor refused it first
            still = [why2] if why2 else []
            if still:
                w2 = made_whole(w2, w)
                if not text(w2.get("result")) or not text(w2.get("guess")):
                    no.append(("new why", why))
                    continue
            w = {**w2, "restated": first, **({"contested": still} if still else {})}
            g = g2 if g2 is not None else None
        elif why:
            no.append(("new why", why))
            continue
        if ground is not None and g is not None:
            w = {**w, "ground": {k: g[k] for k in ("records_show", "nearest_earlier", "defect", "because")} | {"warning": bool(g.get("warning"))} | ({"unread": True} if g.get("unread") else {})}   # kept with the guess: what the supervisor read in the records
        ok["whys"].append(w)
        new = f"Y{n_why + len(ok['whys'])}"   # the id it is about to get
        why_map[pid] = new
        whys[new], stand[new] = w, w["worth"]
        fresh.add(new)
        if w.get("revises"):
            stand[w["revises"]], revised_as[w["revises"]] = "revised", new
    nth = lambda pid, base: int(pid[1:]) - base   # the position of a part of this answer, from the id it was to get
    for k_h, h in enumerate(t.get("hypotheses") or []):
        pid_h = f"H{known + k_h + 1}"
        h_map[pid_h] = None
        gone_why = isinstance(h, dict) and isinstance(h.get("from_why"), str) and h["from_why"] in why_map and why_map[h["from_why"]] is None
        if isinstance(h, dict) and isinstance(h.get("from_why"), str) and why_map.get(h["from_why"]):
            h["from_why"] = why_map[h["from_why"]]   # the guess of this answer it names, by the id that guess was recorded with
        if isinstance(h, dict) and isinstance(h.get("follows_from"), list):   # a run id stands for that run's simulation, as in a why's about (s043: three hypotheses refused for "r001")
            h["follows_from"] = list(dict.fromkeys(of_run(a) for a in h["follows_from"]))
        if isinstance(h, dict) and not h.get("follows_from") and whys.get(h.get("from_why")):
            h["follows_from"] = list(whys[h["from_why"]]["about"])   # what the hypothesis follows from: what its why is about
        if gone_why:
            no.append(("new hypothesis", f"it comes from {h['from_why']}, your new guess number {nth(h['from_why'], n_why)} of this answer, which was not accepted (its note says why): "
                                         "no hypothesis can come from it in this answer"))
        elif mode == "report":
            no.append(("new hypothesis", only))
        elif supervised and (waiting := (lambda st_c: [i for i, v in st_c[0].items() if v == "open" and i not in st_c[1] and i not in {d["id"] for d in ok["drop"]}])(states(ledger))):   # one checked and waiting for its ruling keeps nothing out (s053)
            # the chain is result, guess, hypothesis, test: a hypothesis is stated to be tested, and the next one comes from what its test showed (s047: eight stated, none tested)
            no.append(("new hypothesis", f"{', '.join(waiting)} {'is' if len(waiting) == 1 else 'are'} still open and untested: test {'it' if len(waiting) == 1 else 'them'} (send the experiment), or give "
                                         f"{'it' if len(waiting) == 1 else 'them'} up in drop with what you learned, before you state another hypothesis. The next hypothesis comes from what a test showed"))
        elif supervised and len(ok["hypotheses"]) >= OPEN_MOST:
            no.append(("new hypothesis", f"at most {OPEN_MOST} new hypotheses in one answer: state the ones you will test now"))
        elif stand.get(h.get("from_why")) != "verify":
            y = h.get("from_why")
            no.append(("new hypothesis", ("a hypothesis comes from a guess: from_why must be the id of a guess, one in the ledger or one of this answer " if supervised else
                                          "a hypothesis comes from a why you chose to verify: from_why must be the id of a why whose worth is verify, one in the ledger or one of this answer ")
                                         + f"(the harness numbers new {'guesses' if supervised else 'whys'} in order: the first new one is Y{n_why + 1})"
                                         + (f"; {y} was {STANDING[stand[y]]}" + (f" as {revised_as[y]}" if stand[y] == "revised" and y in revised_as else "") if y in stand else "")))
        elif h["from_why"] in fresh and due():
            no.append(("new hypothesis", FIRST.format(look_again(due()))))
        elif h["from_why"] not in fresh:
            y = h["from_why"]
            no.append(("new hypothesis", f"{y} was stated before the results of {', '.join(later[y][:4])}: look at it again first (rethink: does it still hold in the light of them, and why?), "
                                         "or make a new why from the new results. A hypothesis comes from a why that has seen the latest results, so that the first guesses do not fix the work"))
        elif not text(h.get("text")):
            no.append(("new hypothesis", "a hypothesis needs a text"))
        elif not supervised and not text(h.get("question")):
            no.append(("new hypothesis", "a hypothesis needs a question: the hypothesis put as one plain question"))
        elif not supervised and not text(h.get("why")):
            no.append(("new hypothesis", "a hypothesis needs a why: one plain sentence saying how answering it helps reach the goal"))
        elif not isinstance(h.get("follows_from"), list) or not h["follows_from"] or any(f != "brief" and kinds.get(f) not in ("verdict", "check", "evidence", "simulation", "result") + (("review",) if supervised else ()) for f in h["follows_from"]):
            bad = [f for f in h.get("follows_from") or [] if f != "brief" and f not in kinds] if isinstance(h.get("follows_from"), list) else []
            no.append(("new hypothesis", (f"follows_from names ids that are not in the ledger: {', '.join(map(str, bad))}" if bad else
                                          "follows_from must list what the hypothesis follows from: ids of verdicts, checks, evidence tables or simulations in the ledger (for example V2, C3, E1), or the word brief")))
        else:
            # the judge (judge: a function of the why and the hypothesis, given by the loop; None: no judging): does testing this hypothesis tell whether its guess is true?
            read = None
            if judge is not None:
                try:
                    hid = pid_h   # the id the researcher gave it by its position: its test's rule in this answer names it so (a prediction the short format does not ask)
                    rules = [d.get("decision_rule") for d in ((t.get("experiment") or {}).get("decision_rules") or []) if isinstance(d, dict) and d.get("for") == hid and d.get("decision_rule")] if isinstance(t.get("experiment"), dict) else []
                    follows, because = judge(whys[h["from_why"]], {**h, "rules": rules})
                    read = {"follows": follows, "because": because}
                except Exception as e:   # the judge could not be asked: the hypothesis is taken unjudged, and the record says so
                    read = {"follows": None, "because": f"the judge could not be asked ({type(e).__name__}): accepted unjudged"}
            if read and read["follows"] is False:
                no.append(("new hypothesis", f"it does not follow from {h['from_why']}: a second reading of the guess and the hypothesis (the judge) finds that testing it would not tell whether the guess is true. "
                                             f"{read['because']} State a hypothesis whose result depends on that guess, or state the guess this hypothesis really comes from and name that one"))
                continue
            if read:
                h = {**h, "judge": read}   # a copy: the answer as it was received (answers.jsonl) stays as the model wrote it
            ok["hypotheses"].append(h)
            st[f"H{known + len(ok['hypotheses'])}"] = "open"  # the id it is about to get
            h_map[pid_h] = f"H{known + len(ok['hypotheses'])}"
    ex = t.get("experiment")
    # (c) the experiment of this answer names its hypotheses by the ids they were to get: mapped to the recorded ones; one that was not accepted is named as such
    gone_h = lambda x: f"{x} (your new hypothesis number {nth(x, known)} of this answer, not accepted)"
    to_h = lambda x: (h_map[x] or gone_h(x)) if isinstance(x, str) and x in h_map else x
    if isinstance(ex, dict):
        if isinstance(ex.get("tests"), list):
            ex["tests"] = [to_h(x) for x in ex["tests"]]
        for d in [d for d in (ex.get("decision_rules") or []) + (ex.get("needs") or []) if isinstance(d, dict)]:
            d["for"] = to_h(d.get("for"))
    t["_ids"] = {**why_map, **h_map}   # for the decisions on findings of this answer (remap_refs)
    global MEASURES
    MEASURES = {}
    if isinstance(ex, dict) and mode is None:
        bad = measurement_problem(ex, brief)
        if bad:
            no.append(("experiment", bad))
            ex = None
        else:
            MEASURES = {m["name"]: m for m in ex.get("measurements") or []}
    if supervised and isinstance(ex, dict) and ex.get("kind") == "test" and mode is None and isinstance(ex.get("tests"), list) and ex["tests"]:
        # a test of something that is not an open hypothesis (one this answer stated and the harness did not accept, one already ruled on or given up) is left
        # out, and the tests of the open ones are run: one refused part must not stop the rest (the replay of s047's replies, 2026-11-18)
        shut = [h for h in ex["tests"] if st.get(h) != "open"]
        if shut and len(shut) < len(ex["tests"]):
            no.append(("tests " + ", ".join(map(str, shut)), f"{', '.join(map(str, shut))}: not an open hypothesis (not accepted in this answer, or already ruled on or given up), so its test is left out. "
                                                                  "The other tests of this experiment are taken as they are"))
            ex = without_tests(ex, shut)
    if (supervised or short) and isinstance(ex, dict) and ex.get("kind") == "test" and "needs" not in ex and mode is None:   # the short formats: needs from the rules
        needs, bad, idle = lean_needs(ex, brief)
        if bad:
            no.append(("experiment", bad))
            ex = None
        else:
            if idle:   # a simulation that no decision rule names can decide nothing: it is not run, and the note says so
                no.extend((f"design {l}", f"design `{l}` is named by no decision rule of this test, so it is not run. In a test every simulation is one a rule compares; to look around without a rule, use an explore experiment") for l in idle)
                ex = still_varied({**ex, "runs": [r for r in ex["runs"] if r.get("label") not in idle]})
            ex = {**ex, "needs": needs}
    if ex is not None:
        why = only if mode == "report" else "the simulation budget is used up: no experiment is accepted in the last turn" if mode == "budget" else FIRST.format(look_again(due())) if due() else experiment_problem(ex, brief, ledger, None, st, lean=supervised)
        if not why:  # readable as sent: now cut back what cannot test anything, then count what is left against the budget
            ex, cuts = trim(ex, brief, ledger)
            no.extend(cuts)
            why = experiment_problem(ex, brief, ledger, left, st, lean=supervised) if ex is not None else None
            if free and why and why.startswith("the experiment needs"):   # a free turn (s048, 2026-11-22): only simulations already run
                why = ("the simulation budget is used up: in the turns before the report an experiment may use only simulations already run (their results are returned, "
                       "not run again; measurements you define are computed from what they recorded), and " + why)
        if ex is None:
            pass
        elif why:
            no.append(("experiment", why))
        else:
            ok["experiment"] = ex
    br = t.get("budget_request")
    if br is not None:
        if mode or free:
            no.append(("budget_request", "no more simulations can be asked for once the budget is used up" if free else "no more simulations can be asked for in a last turn"))
        elif not (isinstance(br, dict) and type(br.get("simulations")) is int and br["simulations"] >= 1 and text(br.get("why"))):
            no.append(("budget_request", "it needs simulations (a whole number of at least 1) and a one-sentence why"))
        else:
            ok["budget_request"] = br
    report = t.get("report")
    if isinstance(report, dict) and isinstance(report.get("claims"), list):   # a claim may cite a run by its id: it stands for that run's simulation (2026-11-22; readings by their T ids are ledger ids already)
        report = {**report, "claims": [{**c, "evidence": list(dict.fromkeys(of_run(a) for a in c["evidence"]))} if isinstance(c, dict) and isinstance(c.get("evidence"), list) else c for c in report["claims"]]}
    if report is None:
        if t.get("done") and not mode:
            no.append(("done", "done needs the final report: fill report, or set done to false"))
    elif not (mode or t.get("done")):
        no.append(("report", "a report ends the session: give it together with done = true, or leave it null"))
    else:
        waiting = sorted((h for h in checked if st.get(h) == "open"), key=lambda h: int(h[1:]))  # tested, and not judged even by this answer
        why = check_report(report, brief, set(kinds), ledger, lean=supervised)  # the ledger's ids, and those of the verdicts accepted from this same answer
        # the guesses marked worth verifying from which no hypothesis came and which no rethink settled (s041: all 11 guesses were marked verify, none set
        # aside; two of them, one the true cause, were never taken up): choosing which guesses to verify is a link of the chain, so it is closed too
        taken = {r["body"].get("from_why") for r in ledger if r["type"] == "hypothesis"} | {h.get("from_why") for h in ok["hypotheses"]}
        hanging = sorted((y for y, s in stand.items() if s == "verify" and y not in taken), key=lambda y: int(y[1:]))
        if supervised:   # nothing is owed by the researcher: the rulings are the supervisor's, and a guess that was never taken up stays what it is, in the open
            waiting, hanging = [], []
        elif short:   # the short format asks no worth: every guess counts as worth verifying, and one never taken up does not hold back the report (2026-11-22)
            hanging = []
        if not why and insist and waiting and mode != "report":  # said once per session: the verdicts are asked for together with the report
            why = NEED + ", ".join(waiting) + ". Give their verdicts in the same answer as the report."
        if insist and due() and mode != "report" and (not why or why.startswith(NEED)):   # tested, and not looked at again: the last step is reviewed like every other
            why = (why + " Also: " if why else WAIT) + ("these guesses were tested and no rethink says what the results did to them: " + look_again(due())
                   + ". In the same answer as the report, give a rethink for each (id: the why's own id; now: supported, refuted, verify or set_aside; because of what).")
        if insist and hanging and mode != "report" and (not why or why.startswith(WAIT)):
            why = (why + " Also: " if why else WAIT) + ("these guesses are marked worth verifying, but no hypothesis came from them and no rethink says what became of them: " + ", ".join(hanging)
                   + ". In the same answer as the report, say in rethink what each is now (set_aside or refuted, and because of what), or test it first: a guess you chose to verify is not left hanging.")
        if why:
            no.append(("report", why))
        else:
            ok["report"] = report
    return ok, no

def answer_format(schema, brief):
    """The answer format of a session: schema.json with the parts that depend on the brief put in. params: one property
    per knob of the brief, in the brief's order, all required, so that every design states every knob (a setting the
    brief fixes is not a property); varied: the brief's knobs; runs: at most the brief's simulations per experiment;
    the report's recommendation: the same properties, all required."""
    ex = schema["properties"]["experiment"]["anyOf"][0]["properties"]
    props = {k: {"type": "string", "enum": list(s["choices"])} if "choices" in s else {"type": tools.knob_type(k, brief)} for k, s in brief["knobs"].items()}
    ex["runs"]["items"]["properties"]["params"] = {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
    ex["runs"]["maxItems"] = brief["limits"]["simulations_per_experiment"]
    ex["varied"]["items"] = {"type": "string", "enum": list(props)}
    need = ex["needs"]["items"]["properties"]   # what a hypothesis needs: the one knob that differs between its simulations (or none; or the structure, where that may be changed), and the measure that decides it
    need["varies"] = {**need["varies"], "enum": [*props, "none", *(["structure"] if may_change(brief) else [])]}
    if not may_change(brief):   # a changed network has measures of its own, which are not known before the answer
        need["measure"] = {**need["measure"], "enum": list(tools.outputs(brief))}
    # the recommendation of the final report: every knob of the brief, all required, like a design. Until 2026-11-15 it had a fixed list of six knobs, all optional,
    # and the model server writes an object's properties in the format's order: a report that had passed over one could not name it any more, and a knob that was
    # not in the list (tcpBufBytes) could not be recommended at all (s030: ratio, TCP type, measured time and seed recorded; UDP rate, queue length and buffers lost)
    schema["properties"]["report"]["anyOf"][0]["properties"]["no_difference"]["items"] = {"type": "string", "enum": list(props)}   # the brief's knobs
    if may_change(brief):  # a simulation may carry changes to the network, and the report recommends some: every field of a change is stated, in this order
        edit = {"type": "object", "additionalProperties": False, "required": list(network.EDIT), "properties": {
            "do": {"type": "string", "enum": list(network.DOES)}, "id": {"type": "string"}, "kind": {"type": "string", "enum": ["", "udp", "tcp", "host", "link", "flow", "queue", "scheduler", *network.QUEUE_DISCS]},
            "from": {"type": "string"}, "to": {"type": "string"}, "on": {"type": "string"}, "rate": {"type": "string"}, "type": {"type": "string"}, "app": {"type": "string", "enum": ["", "onoff", "bulk"]}}}
        item = ex["runs"]["items"]
        item["properties"]["structure"] = {"type": "array", "items": edit, "description": "the changes this simulation makes to the network of the brief, in order; an empty list: the network as it is"}
        item["required"] = [*item["required"], "structure"]
        rep = schema["properties"]["report"]["anyOf"][0]
        ordered = {}
        for k, v in rep["properties"].items():   # after the recommendation, in the order the report is written
            ordered[k] = v
            if k == "recommendation":
                ordered["structure"] = {"type": "array", "items": edit, "description": "the changes to the network of the brief that you recommend, in order; an empty list: the network as given"}
        rep["properties"] = ordered
        rep["required"] = [x for k in rep["required"] for x in ((k, "structure") if k == "recommendation" else (k,))]
    if brief.get("topology"):  # a network has measures of its own: the expected values of the report are by their names
        schema["properties"]["report"]["anyOf"][0]["properties"]["expected"]["properties"] = {k: {"type": "number"} for k in tools.outputs(brief)}
    schema["properties"]["report"]["anyOf"][0]["properties"]["recommendation"] = {"type": "object", "properties": dict(props), "required": list(props), "additionalProperties": False,
        "description": "the settings you recommend: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has)"}
    return schema

def plain_format(schema):
    """The answer format of the comparison arm "plain" (--arm plain): the same answer without the hypothesis format. No
    hypotheses, no drop, no verdicts; an experiment only explores (no tests, no decision rules). Everything else, the
    final report included, is as in the ordinary arm."""
    for k in ("rethink", "whys", "hypotheses", "drop", "verdicts"):
        del schema["properties"][k]
        schema["required"].remove(k)
    ex = schema["properties"]["experiment"]["anyOf"][0]
    ex["properties"]["kind"] = {"type": "string", "enum": ["explore"]}
    for k in ("tests", "needs", "decision_rules"):
        del ex["properties"][k]
        ex["required"].remove(k)
    return schema


# ---- the researcher's reply in the arm "supervised", cut to what only the researcher can say (2026-11-18, the operator's "ok do it", after s046: the
# researcher looked at the right things and reached no test in 40 minutes; 3 of its 6 replies were cut off at 32,000 tokens and two experiments were
# refused for slips in fields that only repeated something or guarded what the supervisor now guards). The reply has six things: what it looks at
# (requests), its guesses (whys: about, result, guess), its hypotheses (from_why, text), the simulations and what to measure (experiment: runs,
# measurements), the rule that decides each test (decision_rules: for, decision_rule), and at the end the report (goal, recommendation, limit,
# explanation, claims). The harness derives the rest: what a rule's simulations differ in, the knobs that vary, when the session is done. Not asked
# for any more: a prediction beside the rule, what a hypothesis follows from, its question and its reason, a rival (the supervisor names its own),
# needs, varied, control, whether a guess is worth verifying, a request for more budget, and of the report expected, no_difference, holds_when,
# breaks_when, a claim's role and open_questions.
LEAN_PROMPT = """You are a researcher working on a system you cannot see inside. You reach it only through the tools listed in the brief and through experiments the harness runs for you.

The purpose of the work is to understand why the system behaves as it does. You are not an optimiser: do not try many settings and keep whichever comes out slightly ahead. Look at the system, ask why each result came out so, guess what in the system (not directly visible in the outputs) makes it so, and test that guess. An explanation of what limits the result is worth more than one more setting. Stop when you can say what makes the system behave as it does and what that means for the goal.

You do not work alone. A supervisor works apart from you. It proposes nothing and never sees your notes or your reasons; it is shown your guess, your hypothesis, your decision rule and its rival, the planned simulations, the measured numbers and what the tools returned. It checks each step:
- a new guess: does it start from what the records show, and is it more than an earlier guess said again? A guess it does not accept comes back to you once, in the same turn, to restate;
- a test, before it runs: can it tell your guess from your rival? If not, it says what is wrong and you repair that test at once, up to three rounds; the other tests run meanwhile;
- after the harness has checked your rule: what the check means. Its ruling (supported, refuted, or inconclusive because the test was not a fair one) closes the hypothesis. You do not give verdicts.

The ledger is the complete record of the session. You have no other memory. Each turn you read it and answer with ONE JSON object. Keep every text short: one or two sentences. Its parts:

1. observations: one or two sentences: what you read this turn; an unexplained result goes in findings (below), once. They stay in the ledger (turn N your observations).
2. requests: look before you simulate. Looking costs no simulation. metrics, series and measure read what a simulation you already ran recorded (measure: a statistic of a quantity you combine from them, e.g. tcp_inflight / min(tcp_cwnd, tcp_rwnd); corr and lag: do two move together, which leads); probe makes a finer record of such a simulation (TCP's round-trip time, the receiver's window, the bytes in flight, the time packets wait in each queue) by running it again with taps that only listen. Up to six requests in a reply; the results come back at once, in the same turn, and stay in the ledger with their ids (T1, T2, ...): a reply that states no hypothesis, test, drop or report is answered and you are asked again in the same turn, at most twice. A turn ends with a step.
3. whys: your guesses of why a result came out so. Each has about (the ids of the records it starts from: evidence tables, simulations, checks or rulings, for example E0, S2, C1; a reading a tool returned, by its id, for example T7; a review in which the supervisor objected, for example G4; the word brief only when nothing is measured yet), result (that result in one sentence, with its numbers), guess (what in the system would make it so), and revises (the id of an earlier guess this one replaces, or states more exactly with new numbers or a narrower cause; or null). The harness numbers them Y1, Y2, ... The work is a chain: your first guesses start from the baseline, and every later guess is the fruit of what you learned since: its about must name at least one record made since your last guesses (a ruling, a check, a new result table, a reading, an objection of the supervisor), and its result says what that record showed. A later guess that starts from the baseline alone is refused, and the supervisor reads whether the guess really comes from the newer record or only names it. Make your several first guesses in one answer.
4. hypotheses: a hypothesis is a measurable consequence of one guess: from_why (the guess's id, one in the ledger or one of this answer) and text (one sentence that a measurement can show to be false). The harness numbers them H1, H2, ... A hypothesis is stated to be tested: state at most three in one answer, with the experiment that tests them, and while one is still open and untested no further hypothesis is accepted. Test what is open, or give it up in drop saying what you learned; the next hypothesis comes from what a test showed. A value you can simply read is an observation, not a hypothesis: ask for it in requests (measure, probe) and say it in a guess's result. A hypothesis is a consequence that would come out differently if your guess were wrong and the nearest other explanation were right; a test whose outcome every explanation shares is sent back.
5. drop: open hypotheses you give up before they were tested (id, and why in one sentence). Usually empty.
6. experiment: at most one per turn, or null.
   - kind "test": tests lists the open hypotheses it tests; decision_rules has at least one rule for each. kind "explore": question says what you want to find out; tests and decision_rules stay empty.
   - runs: the simulations, each with a label of its own (letters, digits and _, at most 20 characters) and params: a value for EVERY knob of the brief (a knob left as it was is stated with the value it has). A simulation with the same settings as an earlier one is not run again: its result is returned and costs nothing. The simulations one rule compares must differ in one setting only, so that a difference has one possible cause.
   - measurements: measurements of your own that this experiment takes of each of its simulations, beside the outputs; an empty list when the outputs are enough. Each has name (lower-case, for example rwnd_max), of (a column a simulation records over time, or arithmetic over columns of one record: the columns the tools series and probe name in the brief), stat (one of the statistics the format lists), t_from and t_to (seconds; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise). The harness computes them with taps that only listen: a measurement cannot change a result.
   - decision_rules: for each tested hypothesis, the comparison that decides it, fixed BEFORE the simulations: for (the hypothesis), decision_rule, rival (the strongest competing explanation, one sentence) and rival_predicts (held or failed: what the rule gives if the rival is true; held is refused). Write it exactly in this form: numbers; measure@label (an output, or a measurement of your own, in the simulation with that label); + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == in each comparison; at most 3 comparisons, joined by AND and OR. The harness checks it from the measured values: HELD or FAILED. A rule must be able to fail: it names at least one result you do not know yet. A rule on a measurement of your own may be about simulations you already ran (the measurement is new), and then no simulation is spent.
7. objections: if the records show that a ruling of the supervisor is wrong, object once: to (the ruling's id, for example V2) and because (the numbers it overlooked). Usually empty.
8. report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).

The budget counts simulations. Every turn says how many are left; one experiment may run at most half of them. When they run out you get two more turns to look and to test on simulations already run, then one last turn for the report.

If a part of your answer cannot be used, the harness leaves that part out, accepts the rest, and says in a note which part and why: read the note and repair that part. Two results closer than the tolerance count as equal: a difference inside it is not a finding."""


def supervised_format(schema):
    """The researcher's answer format in the arm "supervised": the six things only it can say (see LEAN_PROMPT). Made from the full format after
    answer_format() has fitted it to the brief, so that a design still states every knob and the recommendation every knob."""
    P = schema["properties"]
    keep = lambda obj, keys: (obj.update(properties={k: obj["properties"][k] for k in keys}, required=list(keys)), obj)[1]
    props = {"observations": {"type": "string", "description": "one or two sentences: what you read this turn (an unexplained result goes in findings)"}, "requests": P["requests"],
             "whys": {**P["whys"], "items": keep(P["whys"]["items"], ["about", "result", "guess", "revises"])},
             "hypotheses": {**P["hypotheses"], "items": keep(P["hypotheses"]["items"], ["from_why", "text"])}, "drop": P["drop"]}
    ex = P["experiment"]["anyOf"][0]
    ex["properties"]["decision_rules"]["items"] = keep(ex["properties"]["decision_rules"]["items"], ["for", "decision_rule", "rival", "rival_predicts"])   # the rival is the researcher's since 2026-11-22 (after the reviews of s047 and s050)
    keep(ex, ["kind", "tests", "question", "runs", "measurements", "decision_rules"])
    props["experiment"] = P["experiment"]
    props["objections"] = {"type": "array", "description": "objections to rulings of the supervisor, at most one for each ruling; empty when you have none",
                           "items": {"type": "object", "additionalProperties": False, "required": ["to", "because"], "properties": {
                               "to": {"type": "string", "description": "the id of the supervisor's ruling, for example V2"}, "because": {"type": "string", "description": "what in the records shows that the ruling is wrong"}}}}
    rp = P["report"]["anyOf"][0]
    rp["properties"]["claims"]["items"] = keep(rp["properties"]["claims"]["items"], ["text", "evidence"])
    keep(rp, [k for k in ("goal", "recommendation", "structure", "limit", "explanation", "claims", "open_questions") if k in rp["properties"]])   # open_questions: the findings text asks for it (the coherence audit, 2026-11-22)
    props["report"] = P["report"]
    schema["properties"], schema["required"] = props, list(props)
    return schema


OPEN_MOST = 3   # the arm "supervised": the most new hypotheses in one answer
LEARNED = ("evidence", "check", "verdict", "result", "review")   # the kinds of record a later guess can have learned from


def learned_since(ledger, turn=None):
    """The chain (the arm "supervised"): the ids of the records a new guess of this turn can have learned from since the researcher's earlier guesses:
    a result table, a check, a ruling, what a tool returned, a review in which the supervisor objected, made in or after the turn of the newest
    earlier guess (what a turn's requests returned and what its experiment gave is seen only in the next turn). None when there is no earlier guess:
    the first guesses start from the baseline."""
    turn = max((r["turn"] for r in ledger), default=0) if turn is None else turn
    earlier = [r["turn"] for r in ledger if r["type"] == "why" and r["turn"] < turn]
    if not earlier:
        return None
    k = max(earlier)
    return {r["id"] for r in ledger if (r["type"] in LEARNED or r["type"] == "simulation") and r["turn"] >= k and not (r["type"] == "review" and (r["body"].get("decision") == "approved" or r.get("by") == "harness"))}   # a harness's round is no objection of the supervisor's; a simulation is a result (the coherence audit, 2026-11-22)


def still_varied(ex):
    """The experiment with its list of varied knobs cut to those that still take more than one value in its designs: after the harness has removed
    designs, a knob it left with one value is no longer varied, and the experiment is not refused for it (the coherence audit, 2026-11-22)."""
    if not isinstance(ex, dict) or not isinstance(ex.get("varied"), list):
        return ex
    runs = [r for r in ex.get("runs") or [] if isinstance(r, dict)]
    takes = lambda k: len({json.dumps((r.get("params") or {}).get(k), sort_keys=True) for r in runs})
    return {**ex, "varied": [k for k in ex["varied"] if not isinstance(k, str) or k not in {q for r in runs for q in (r.get("params") or {})} or takes(k) > 1]}


def without_tests(ex, gone):
    """A test experiment without the tests of the hypotheses in gone (sent back by the supervisor): their rules and needs leave, and so does a simulation
    that only they named. None when no test is left."""
    tests = [h for h in ex.get("tests") or [] if h not in gone]
    if not tests:
        return None
    rules = [d for d in ex.get("decision_rules") or [] if d.get("for") in tests]
    needs = [n for n in ex.get("needs") or [] if n.get("for") in tests]
    named = {l for n in needs for l in n.get("simulations") or []} | {l for d in rules for l in re.findall(r"@([A-Za-z0-9_]+)", d.get("decision_rule") or "")}
    runs = [r for r in ex.get("runs") or [] if r.get("label") in named] or list(ex.get("runs") or [])
    used = " ".join(d.get("decision_rule") or "" for d in rules)
    out = {**ex, "tests": tests, "decision_rules": rules, "runs": runs, "measurements": [m for m in ex.get("measurements") or [] if re.search(rf"\b{re.escape(str(m.get('name')))}@", used)]}
    if "needs" in ex:
        out["needs"] = needs
    if ex.get("control") and ex["control"] not in {r.get("label") for r in runs}:
        out["control"] = None
    return still_varied(out)


def as_run(r):
    """A design's settings as trim compares them: clamped and normalised (tools.same of tools.options), so that 100 and 100.4 packets, or 2Gbps and
    2000Mbps, are one value (2026-11-22). A design that cannot be clamped stays as written."""
    try:
        return dict(tools.same(tools.options(tools.clamp(r.get("params") or {}, design=r.get("label"))[0])))
    except Exception:
        return dict(r.get("params") or {})

def varied_of(runs, brief):
    """The knobs whose values differ between the designs, compared as trim compares them (as_run), not as written (2026-11-22, the operator's
    decision for both arms: written values that differ only before rounding listed a knob that trim then found single-valued, or made a test's
    designs differ in "more than one setting", and the whole experiment was refused)."""
    vals = {}
    for r in runs:
        d = as_run(r)
        for k in brief["knobs"]:
            if k in d:
                vals.setdefault(k, set()).add(json.dumps(d[k], sort_keys=True, default=str))
    return [k for k in brief["knobs"] if len(vals.get(k, ())) > 1]

def lean_fill(t, brief):
    """A reply in the short format of the arm "supervised", made whole for the loop: every part the researcher is no longer asked for gets what the
    harness derives or an empty value, so that one loop serves both formats. Returns the reply (changed in place)."""
    for w in t.get("whys") or []:
        if isinstance(w, dict):
            w.update({k: w.get(k, v) for k, v in (("unseen", ""), ("matters", ""), ("reason", ""), ("worth", "verify"))})
    for h in t.get("hypotheses") or []:
        if isinstance(h, dict):
            h.update({k: h.get(k, v) for k, v in (("question", ""), ("why", ""), ("prediction", None), ("follows_from", []))})
    ex = t.get("experiment")
    if isinstance(ex, dict):
        runs = [r for r in ex.get("runs") or [] if isinstance(r, dict)]
        ex.setdefault("varied", varied_of(runs, brief))
        ex.setdefault("control", None)
        ex.setdefault("question", "")
        ex.setdefault("measurements", [])
    rep = t.get("report")
    if isinstance(rep, dict):
        rep.update({k: rep.get(k, v) for k, v in (("expected", {}), ("no_difference", []), ("holds_when", ""), ("breaks_when", ""), ("open_questions", []))})
        for c in rep.get("claims") or []:
            if isinstance(c, dict):
                c.setdefault("role", "supports")
    t.update({k: t.get(k, v) for k, v in (("verdicts", []), ("rethink", []), ("budget_request", None))})
    t["done"] = t.get("report") is not None
    return t


def lean_needs(ex, brief):
    """What the harness derives where the researcher states no needs: for each tested hypothesis the simulations its rules name, the one setting those
    differ in and the first measure its rules name: (needs, what is wrong or None, the designs no rule names). The simulations one hypothesis's rules
    compare must differ in one setting only: a difference in the measure then has one possible cause."""
    runs = {r["label"]: r for r in ex.get("runs") or [] if isinstance(r, dict) and isinstance(r.get("label"), str)}
    needs, seen = [], set()
    for h in ex.get("tests") or []:
        rules = [str(d.get("decision_rule") or "") for d in ex.get("decision_rules") or [] if isinstance(d, dict) and d.get("for") == h]
        labs = [l for l in dict.fromkeys(l for r in rules for l in re.findall(r"@([A-Za-z0-9_]+)", r)) if l in runs]
        seen |= set(labs)
        m = re.search(r"([A-Za-z_][A-Za-z0-9_.]*)@", " ".join(rules))
        got = {l: {**(runs[l].get("params") or {}), **{k: v for k, v in as_run(runs[l]).items() if k in (runs[l].get("params") or {})}} for l in labs}   # the settings it states, compared as trim compares them (2026-11-22)
        differ = sorted({k for a in labs for b in labs for k in set(got[a]) | set(got[b]) if got[a].get(k) != got[b].get(k)})
        other = len({json.dumps(runs[l].get("structure") or [], sort_keys=True) for l in labs}) > 1
        if len(differ) + other > 1:
            return None, (f"the simulations the rule for {h} compares ({', '.join(labs)}) differ in more than one setting ({', '.join(differ + (['the structure'] if other else []))}): a difference in the measure then has more than "
                          "one possible cause. Make them differ in one setting only, or test the settings in separate hypotheses"), []
        needs.append({"for": h, "to_know": "", "varies": "structure" if other else differ[0] if differ else "none", "measure": m.group(1) if m else "", "simulations": labs, "derived": True})
    return needs, None, [l for l in runs if l not in seen]


# The arm "hypotheses" asks for a shorter answer since 2026-11-22 (the operator, after a review of every answers.jsonl: fields that repeat something
# else or carry almost no information cost tokens and got experiments refused over slips), the way the arm "supervised" was trimmed on 2026-11-18:
# hypothesis.prediction (repeats the decision rule: 43 of 288 word for word), follows_from (taken from the guess's about), experiment.varied,
# control and needs (derived from the runs and the rules), why.worth and why.reason (78 of 91 whys were "verify"), budget_request (used 0 times in
# 166 answers). Kept: a hypothesis's question and why (the page shows them on a click: the operator), why.unseen and matters, each rule's rival,
# rethinks, verdicts and the whole report. short_fill makes each answer whole for the loop with what the harness derives or a fixed default.
SHORT_DROP = {"whys": ("worth", "reason"), "hypotheses": ("prediction", "follows_from"), "experiment": ("varied", "control", "needs"), "": ("budget_request",)}

def short_format(schema):
    """The answer format of the arm "hypotheses": the full one (after answer_format) without the fields of SHORT_DROP."""
    P = schema["properties"]
    def drop(obj, keys):
        for k in keys:
            obj["properties"].pop(k, None)
        obj["required"] = [k for k in obj.get("required", []) if k not in keys]
    drop(P["whys"]["items"], SHORT_DROP["whys"])
    drop(P["hypotheses"]["items"], SHORT_DROP["hypotheses"])
    for ex in P["experiment"].get("anyOf", [P["experiment"]]):
        if ex.get("type") == "object":
            drop(ex, SHORT_DROP["experiment"])
    drop(schema, SHORT_DROP[""])
    return schema

def short_fill(t, brief):
    """An answer in the short format of the arm "hypotheses", made whole for the loop (as lean_fill does for the arm "supervised"): worth "verify",
    reason "", prediction None, follows_from [] (sort_out takes it from the guess's about), varied derived from the runs (varied_of), control None,
    budget_request None; needs are derived in sort_out from the rules (lean_needs). A field the answer does give is kept. Returns the answer."""
    for w in t.get("whys") or []:
        if isinstance(w, dict):
            w.update({k: w.get(k, v) for k, v in (("worth", "verify"), ("reason", ""))})
    for h in t.get("hypotheses") or []:
        if isinstance(h, dict):
            h.update({k: h.get(k, v) for k, v in (("prediction", None), ("follows_from", []))})
    ex = t.get("experiment")
    if isinstance(ex, dict):
        ex.setdefault("varied", varied_of([r for r in ex.get("runs") or [] if isinstance(r, dict)], brief))
        ex.setdefault("control", None)
    t.setdefault("budget_request", None)
    return t

# prompt.txt -> the instructions of the arm "hypotheses" in its short format: (text as it stands in prompt.txt, what replaces it), each found exactly once
SHORT = (
    (" Then choose: worth is verify if verifying it now serves the goal, set_aside if not, with the reason either way (reason). Make more than one guess for a result that matters: the first explanation that comes to mind is often not the one that holds. Choosing is part of the work: mark verify only the guesses you will test now, and set the others aside (you can take one up later). Before the final report every guess you marked verify must have led to a hypothesis, or a rethink must say what became of it.",
     " Make more than one guess for a result that matters: the first explanation that comes to mind is often not the one that holds. A guess you do not take up stays as it is; a rethink can set it aside or say it is refuted."),
    ("each from a why you chose to verify (from_why: its id, one in the ledger or one of this answer) and each with a falsifiable prediction (a number, a range, or a direction).",
     "each from a why (from_why: its id, one in the ledger or one of this answer); what it predicts is said by the decision rule of its test."),
    ("the chain is result, why, what is worth verifying, hypothesis, what you need to know, simulations.", "the chain is result, why, hypothesis, its decision rule, simulations."),
    (" follows_from may be left empty: the harness takes it from the why's about.", ""),
    ("tests, needs and decision_rules stay empty", "tests and decision_rules stay empty"),
    ("   - needs: for a test, decide first what you need to know, and only then which simulations give it.", "   - what a test compares: decide first what you need to know, and only then which simulations give it; the harness reads it from your decision rules."),
    (" One entry for each hypothesis the experiment tests: to_know (one plain sentence: what you must know to decide the hypothesis), varies (the one knob whose value differs between the simulations made for it; none when a single simulation against a number you state decides it), measure (what decides it: an output, or a measurement of your own that this experiment defines, by its name), simulations (the labels of the simulations made for it). The simulations of one need differ in that one knob and in nothing else,",
     " The simulations the rules of one hypothesis name differ in one knob and in nothing else,"),
    ("The decision rules of the hypothesis name only those simulations, and that measure. Every simulation of a test is made for at least one hypothesis: a simulation that no need lists is not run, and the experiment is refused.",
     "Every simulation of a test is named by a decision rule: a simulation that no rule names is not run."),
    ("   - varied: the knobs that differ between the simulations. control: the label of the simulation the others are compared with, or null.\n", ""),
    ("is a comparison that decides whether its prediction held.", "is a comparison that decides it: it says what the hypothesis predicts."),
    ("\n9. budget_request: the budget counts simulations,", "\nThe budget counts simulations,"),
    (" If the simulations left will not be enough to answer the task, say how many more you need and why, in a turn that also does something else. The harness grants it only up to the limit of the brief (limits.simulations) and records the grant. Otherwise leave it null.", ""),
    ("\n10. done and report:", "\n9. done and report:"),
)

def short_prompt(text):
    """The instructions of the arm "hypotheses" in its short format, made from prompt.txt: no worth or reason, no prediction or follows_from, no
    needs, varied or control, no budget_request. A sentence of SHORT that no longer stands exactly once in prompt.txt stops the session."""
    for a, b in SHORT:
        if text.count(a) != 1:
            raise ValueError(f"prompt.txt: {a[:50]!r}... stands {text.count(a)} times; the short format of the arm 'hypotheses' expects once")
        text = text.replace(a, b)
    return text

# ======================================================================================================
# Findings (2026-11-22, the operator, after a review of s047 to s049: the researcher often noticed something unexplained and then never worked on
# it; in s048 and s049 six guesses were set aside and none was taken up again, and threads that ask "why" were parked as "less urgent for the goal"
# while threads pointing to a setting were followed: "Nothing is lost from view any more; it is parked and forgotten").
# A finding (F1, F2, ...) is one thing the results do not explain: text (one sentence, with its numbers) and about (the records it rests on). The
# researcher raises findings in every arm; the supervisor of the arm "supervised" raises them when it rules on a test and after the baseline and
# each explore experiment: what is unexplained, never why. Every finding keeps who raised it. Its status changes only by the researcher's
# decisions (A1, A2, ...): work (refs: the why, hypothesis, experiment or reading that works on it), park (a reason), close (refs: the evidence,
# checks, verdicts or readings that explain it) or same_as (refs: the other finding). Every finding is listed at the top of each turn's text; an
# open one needs a decision each turn; a parked one, and a working one with nothing new linked to it, come back after PARK_TURNS turns. A report
# offered while the researcher can still work is held back while a finding was never looked at (no reading or check reaches it), at most
# FINDING_HOLDS times (the operator: "make the researcher work on it instead of abandoning it"); in the last turn a finding the report leaves out
# of its open questions is added there by the harness. At the end the harness records, for each finding, what looked at it.
# Nothing about findings refuses any other part of the answer (s049, turn 2: one refused citation cascaded until the whole turn was lost): a
# finding or a decision the harness cannot use is left out with a note.
# ======================================================================================================
PARK_TURNS = 2        # a parked finding, and a working one with nothing new linked to it, comes back for a decision after this many turns
FINDING_HOLDS = 2     # the most times in a session a report is held back for findings never looked at
SUP_FINDINGS = 2      # the most findings of the supervisor in one call
ACTIONS = {"work": "working", "park": "parked", "close": "closed", "same_as": "same_as"}
RESTS = ("evidence", "simulation", "check", "verdict", "result", "review")             # what a finding may rest on (about)
WORKS = ("why", "hypothesis", "experiment", "result", "check", "evidence", "rethink")  # what a "work" decision may name
CLOSES = ("evidence", "check", "verdict", "result", "simulation", "review")           # what a "close" decision may name
FINDING_ITEM = {"type": "object", "additionalProperties": False, "required": ["about", "text", "name"], "properties": {
    "about": {"type": "array", "items": {"type": "string"}, "description": "the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings (for example E2, C3, T7)"},
    "text": {"type": "string", "description": "one sentence: what the results do not explain, with its numbers"},
    "name": {"type": "string", "description": "at most 5 words, to show it by (for example: TCP gets nothing)"}}}   # the name (2026-11-22, the operator: the page shows it on the finding's bar)
NAME_WORDS, NAME_CHARS = 6, 48   # a longer name is cut to this
RULING_SCHEMA["properties"]["findings"]["items"] = FINDING_ITEM   # the ruling's findings in the finding's format, name included (the coherence audit, 2026-11-22: the ruling asked for a name its schema forbade)


def finding_name(f):
    """{"name": ...} of a finding as it was stated, cut to NAME_WORDS words and NAME_CHARS characters; {} without one (a finding is never refused for it)."""
    n = " ".join(str(f.get("name") or "").split()[:NAME_WORDS])[:NAME_CHARS].strip(" .,;:") if isinstance(f, dict) and isinstance(f.get("name"), str) else ""
    return {"name": n} if n else {}
DECISION_ITEM = {"type": "object", "additionalProperties": False, "required": ["id", "action", "refs", "reason"], "properties": {
    "id": {"type": "string", "description": "the finding, for example F2"}, "action": {"type": "string", "enum": list(ACTIONS)},
    "refs": {"type": "array", "items": {"type": "string"}, "description": "work: what works on it; close: what explains it; same_as: the other finding; park: empty"},
    "reason": {"type": "string", "description": "park: why not now; otherwise empty"}}}

def _flat(v):
    return " ".join(str(v or "").split())

def finding_states(ledger):
    """Every finding's standing now: {F: {id, by, turn, about, text, status (open | working | parked | closed | same_as), since (the turn of the
    decision that set it, or of the finding), refs and reason (of that decision), links (every id a decision on it ever named)}}."""
    out = {}
    for r in ledger:
        b = r.get("body") or {}
        if r["type"] == "finding":
            out[r["id"]] = {"id": r["id"], "by": r.get("by"), "turn": r["turn"], "about": list(b.get("about") or []), "text": b.get("text") or "", "status": "open",
                            "since": r["turn"], "refs": [], "reason": "", "links": []}
        elif r["type"] == "decision" and b.get("for") in out and b.get("action") in ACTIONS:
            f = out[b["for"]]
            f.update(status=ACTIONS[b["action"]], since=r["turn"], refs=list(b.get("refs") or []), reason=b.get("reason") or "")
            f["links"] = list(dict.fromkeys(f["links"] + [x for x in f["refs"] if x not in out]))
    return out

def finding_reach(ledger, links):
    """The records that ids linked to a finding reach: the records themselves; the hypotheses of a linked why, with their checks and verdicts; the
    checks and verdicts of a linked hypothesis; the evidence and checks of a linked experiment; the rethinks of a linked why."""
    links = set(links)
    hyps = {r["id"] for r in ledger if r["type"] == "hypothesis" and (r["id"] in links or (r.get("body") or {}).get("from_why") in links)}
    out = []
    for r in ledger:
        b = r.get("body") or {}
        if (r["id"] in links or r["id"] in hyps or (r["type"] in ("check", "verdict") and b.get("for") in hyps)
                or (r["type"] in ("evidence", "check") and b.get("experiment") in links) or (r["type"] == "rethink" and b.get("for") in links)):
            out.append(r)
    return out

def finding_looked(f, ledger):
    """What looked at a finding: the readings, checks and evidence its links reach (the ids, in ledger order)."""
    return [r["id"] for r in finding_reach(ledger, f["links"]) if r["type"] in ("result", "check", "evidence")]

def finding_due(f, ledger, turn):
    """Whether the finding needs a decision in this turn: an open one always; a parked one PARK_TURNS turns after it was parked; a working one
    PARK_TURNS turns after the last record linked to it (its decision, or what its refs reach); a closed one never."""
    if f["status"] == "open":
        return True
    if f["status"] == "parked":
        return turn >= f["since"] + PARK_TURNS
    if f["status"] == "working":
        return turn >= max([f["since"]] + [r["turn"] for r in finding_reach(ledger, f["refs"])]) + PARK_TURNS
    return False

def findings_block(ledger, turn, mode):
    """The list at the top of each turn's text: every finding not closed in full (who raised it, its status, DUE when it needs a decision now),
    the closed ones in brief, and what is asked."""
    fs = finding_states(ledger)
    if not fs:
        return "FINDINGS: none so far. When a result is not explained, state it in findings (about, text).\n\n"
    who = lambda f: "you" if f["by"] == "model" else "the supervisor"
    live = [f for f in fs.values() if f["status"] in ("open", "working", "parked")]
    done = [f for f in fs.values() if f["status"] in ("closed", "same_as")]
    due = [f["id"] for f in live if finding_due(f, ledger, turn)]
    never = [f["id"] for f in live if not finding_looked(f, ledger)]
    state = lambda f: {"open": "open", "working": f"working on it since turn {f['since']} ({', '.join(f['refs'])})", "parked": f"parked in turn {f['since']} ({_flat(f['reason'])[:200]})"}[f["status"]]
    lines = [f"[{f['id']}] raised by {who(f)} in turn {f['turn']}; {state(f)}{'; DUE' if f['id'] in due else ''}: {_flat(f['text'])[:400]} (about {', '.join(f['about'])})" for f in live]
    if done:
        lines.append("Closed: " + "; ".join(f"{f['id']} " + (f"same as {(f['refs'] or ['?'])[0]}" if f["status"] == "same_as" else f"in turn {f['since']} by {', '.join(f['refs'])}") + f" ({_flat(f['text'])[:80]})" for f in done))
    if mode in ("budget", "report"):
        ask = ("THIS IS THE LAST TURN: in the report, name each finding that is not closed in open_questions with its id (for example \"F2: ...\"). " if live else "") + "A decision may still close a finding."
    else:
        ask = ((f"Give one decision (decisions) for each finding marked DUE: {', '.join(due)}. " if due else "No finding needs a decision this turn. ")
               + (f"Never looked at yet (no reading or test reaches it): {', '.join(never)}. " + ("Look at them in these turns: a reading or a measurement on simulations already run costs no simulation. " if mode == "free" else "")
                  + "A final report is held back while a finding was never looked at." if never else ""))
    return "FINDINGS (what the results do not yet explain; each stays on this list until you close it):\n" + "\n".join(lines) + "\n" + ask.strip() + "\n\n"

def findings_in_whys(t, ledger):
    """A why whose about names a finding works on it (the operator, 2026-11-22: one decision less to write). Before sort_out: each finding id in a
    why's about is put back as the records the finding rests on, and kept aside in the why (_findings) for the decision the harness then writes.
    An id that is not a finding is left as it is (sort_out reads it as before)."""
    fs = finding_states(ledger)
    for w in t.get("whys") or []:
        if isinstance(w, dict) and isinstance(w.get("about"), list):
            named = [a for a in w["about"] if a in fs]
            if named:
                rest = [a for a in w["about"] if a not in fs]
                w["about"] = list(dict.fromkeys(rest + [x for a in named for x in fs[a]["about"]]))
                w["_findings"] = named
    return t

def remap_refs(t):
    """The refs of an answer's decisions on findings, mapped from the ids of its new guesses and hypotheses by position to the ids they were recorded
    with (sort_out leaves the map in t["_ids"]); a ref to a part that was not accepted stays as written, and settle_findings leaves it out with a note."""
    ids = t.get("_ids") or {}
    for d in t.get("decisions") or []:
        if isinstance(d, dict) and isinstance(d.get("refs"), list):
            d["refs"] = [ids.get(r) or r if isinstance(r, str) else r for r in d["refs"]]
    return t


def findings_fill(t):
    """An answer without findings or decisions has none (every arm; an older script, or a model that leaves them out)."""
    t.setdefault("findings", [])
    t.setdefault("decisions", [])
    for d in t["decisions"] if isinstance(t["decisions"], list) else []:
        if isinstance(d, dict):
            d.setdefault("refs", [])
            d.setdefault("reason", "")
    return t

def with_findings(schema):
    """The answer format with findings (after observations) and decisions (before the report): every arm."""
    P = schema["properties"]
    out = {}
    for k, v in P.items():
        if k == "report":
            out["decisions"] = {"type": "array", "items": DECISION_ITEM, "description": "one decision for each finding marked DUE, and for any other you act on"}
        out[k] = v
        if k == "observations":
            out["findings"] = {"type": "array", "items": FINDING_ITEM, "description": "each new thing the results do not explain, once; empty when there is none"}
    out.setdefault("findings", {"type": "array", "items": FINDING_ITEM})
    out.setdefault("decisions", {"type": "array", "items": DECISION_ITEM})
    schema["properties"], schema["required"] = out, list(out)
    return schema

def _ref_kinds(ledger):
    kinds = {r["id"]: r["type"] for r in ledger}
    run_sim = {r["body"]["run_id"]: r["id"] for r in ledger if r["type"] == "simulation" and (r.get("body") or {}).get("run_id")}
    def of_run(a):   # a run id stands for its simulation, as in a why's about
        m = re.fullmatch(r"(?:[A-Za-z_ ]+[ :])?\s*(r\d+)", a.strip()) if isinstance(a, str) else None
        return run_sim.get(m.group(1), a) if m else a
    return kinds, of_run

def _note(ledger, turn, part, why, refused=True):
    text = f"refused part of the answer: {part}. Reason: {why.rstrip('.')}. The other parts of that answer were accepted." if refused else f"{part}: {why}"
    return append(ledger, turn, "note", None, {"text": text, "part": part, "reason": why, **({} if refused else {"refused": False})})   # refused False: a note on a part that was accepted (the page told them apart by nothing; the coherence audit, 2026-11-22)

def settle_findings(t, ledger, turn, due_before, made, whys_made, goes_on=False):
    """The researcher's findings and decisions of one answer, after its other parts made their records (so that a decision can name a why,
    hypothesis, experiment or reading of this same answer). Each one the harness cannot use is left out with a note; nothing else is refused.
    due_before: the findings that needed a decision this turn; made: the readings and the experiment this answer produced (not used since a work
    decision without refs counts as worked on, not as looked at, 2026-11-22); whys_made: [(why id, the findings its about named)]."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    kinds, of_run = _ref_kinds(ledger)
    for f in t.get("findings") or []:
        about = [of_run(a) for a in f["about"] if isinstance(a, str)] if isinstance(f, dict) and isinstance(f.get("about"), list) else []
        bad = [a for a in about if kinds.get(a) not in RESTS]
        if not isinstance(f, dict) or not text(f.get("text")):
            _note(ledger, turn, "finding", "a finding needs text: one sentence, what the results do not explain, with its numbers")
        elif not about or bad:
            _note(ledger, turn, "finding", "about must name the records it rests on: ids of evidence tables, simulations, checks, verdicts or readings in the ledger (for example E2, C3, T7)"
                  + (f"; not such a record: {', '.join(map(str, bad))}" if bad else ""))
        else:
            append(ledger, turn, "finding", None, {"about": list(dict.fromkeys(about)), "text": _flat(f["text"]), **finding_name(f)})
    kinds, of_run = _ref_kinds(ledger)
    fs, done = finding_states(ledger), set()
    allowed = {"work": WORKS, "close": CLOSES, "same_as": ("finding",)}
    for d in t.get("decisions") or []:
        fid = d.get("id") if isinstance(d, dict) else None
        part, act = f"decision for {fid}", d.get("action") if isinstance(d, dict) else None
        refs = [of_run(x) for x in d.get("refs") or [] if isinstance(x, str)] if isinstance(d, dict) and isinstance(d.get("refs"), list) else []
        if fid not in fs:
            _note(ledger, turn, "decision", f"a decision names a finding by its id (F1, F2, ...): {fid!r} is not one")
            continue
        if fid in done:
            _note(ledger, turn, part, "a finding gets one decision in an answer")
            continue
        if fs[fid]["status"] in ("closed", "same_as"):
            _note(ledger, turn, part, f"{fid} is closed already: if it is unexplained again, state it as a new finding")
            continue
        if act not in ACTIONS:
            _note(ledger, turn, part, "action is work, park, close or same_as")
            continue
        good = [x for x in dict.fromkeys(refs) if kinds.get(x) in allowed.get(act, ()) and x != fid]
        left = [x for x in dict.fromkeys(refs) if x not in good]
        if act == "park":
            if not text(d.get("reason")):
                _note(ledger, turn, part, "park needs a reason: why not now")
                continue
            good, left = [], []
        elif act == "work" and not refs:   # no refs: it counts as worked on, not as looked at (the operator's change after the review of the findings design, 2026-11-22)
            good = []
        elif not good:
            _note(ledger, turn, part, {"work": "work needs refs: the why, hypothesis, experiment or reading that works on it (one of this answer by the id it gets), or requests or an experiment in this same answer",
                                       "close": "close needs refs: the evidence, checks, verdicts or readings in the ledger that explain it",
                                       "same_as": "same_as needs refs: the id of the other finding"}[act] + (f"; not usable here: {', '.join(left)}" if left else ""))
            continue
        if left:
            _note(ledger, turn, part, f"left out of its refs, not records a {act} decision can name: {', '.join(left)}; the decision stands with {', '.join(good)}", refused=False)
        done.add(fid)
        append(ledger, turn, "decision", fid, {"for": fid, "action": act, "refs": good[:1] if act == "same_as" else good, "reason": _flat(d.get("reason")) if act == "park" else ""})
    for y, named in whys_made:   # a why about a finding works on it, unless this answer decided on that finding itself
        for fid in named:
            if fid in fs and fid not in done and fs[fid]["status"] not in ("closed", "same_as"):
                done.add(fid)
                append(ledger, turn, "decision", fid, {"for": fid, "action": "work", "refs": [y], "reason": "", "auto": f"the guess {y} is about {fid}"})
    for fid in due_before:
        if fid not in done and fid in fs and fs[fid]["status"] not in ("closed", "same_as"):
            _note(ledger, turn, f"decision for {fid}", f"no decision for {fid}, which was due this turn: it stays {fs[fid]['status']} and is asked for again in " + ("your next reply, in this same turn" if goes_on else "the next turn"))

def findings_unseen(ledger):
    """The findings not closed that nothing has looked at yet (no reading, check or evidence reaches them)."""
    return [f["id"] for f in finding_states(ledger).values() if f["status"] in ("open", "working", "parked") and not finding_looked(f, ledger)]

def findings_in_report(report, ledger):
    """The report accounts for every finding: each one not closed stands in open_questions by its id. One it leaves out is added there by the
    harness, marked so. Returns (report, the ids added)."""
    live = [f for f in finding_states(ledger).values() if f["status"] in ("open", "working", "parked")]
    oq = [q for q in report.get("open_questions") or [] if isinstance(q, str)] if isinstance(report.get("open_questions"), list) else []
    missing = [f for f in live if not any(re.search(rf"\b{f['id']}\b", q) for q in oq)]
    if missing:
        report = {**report, "open_questions": list(report.get("open_questions") or []) + [f"{f['id']}: {_flat(f['text'])} (not resolved; added by the harness: the report did not name it)" for f in missing]}
    return report, [f["id"] for f in missing]

def findings_end(ledger, turn):
    """At the end of a session: for each finding, who raised it, how it ended, how many turns it stayed open and what looked at it."""
    fs = finding_states(ledger)
    if not fs:
        return None
    rows = []
    for f in fs.values():
        looked = finding_looked(f, ledger)
        ended = f["status"] in ("closed", "same_as")
        rows.append({"id": f["id"], "by": f["by"], "raised": f["turn"], "status": f["status"] if ended or f["status"] == "parked" else "unresolved" if f["status"] == "open" else "working",
                     "turns_open": (f["since"] if ended else turn) - f["turn"], "looked_at": looked, "never_looked_at": not looked})
    return append(ledger, turn, "findings_end", None, {"findings": rows})

# The supervisor's findings (the arm "supervised"): when it rules on a test, and after the baseline and each explore experiment, where results come in
# without a ruling. What is unexplained, never why. One is kept only if every id it cites is in the ledger and its text holds a measured number.
SUP_FINDINGS_ASK = ("FINDINGS (findings, at most 2, or none): a measured result in what you are shown that nothing on record explains yet. State WHAT is "
                    "unexplained, never why: no cause, no guess, no test to run. Each with its numbers (text), a name of at most 5 words to show it by (name) and the ids of the records it rests on (about). "
                    "Do not raise again one of the findings so far.")
SUP_FINDINGS_ITEMS = {"type": "array", "maxItems": SUP_FINDINGS, "items": FINDING_ITEM, "description": "what the measured results leave unexplained (what, never why), at most 2; empty when nothing"}
FINDINGS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["findings"], "properties": {"findings": SUP_FINDINGS_ITEMS}}

def findings_for_supervisor(ledger):
    """The findings so far as the supervisor is shown them: id, who raised it, its text and its status; not the researcher's reasons."""
    fs = finding_states(ledger)
    return "\n".join(f"  [{f['id']}] ({'the researcher' if f['by'] == 'model' else 'you'}, {f['status']}) {_flat(f['text'])[:300]}" for f in fs.values()) or "  (none yet)"

def sup_findings_of(model, brief, ledger, xid, ask_fn=None):
    """The supervisor's look at the results of an experiment no ruling covers (the baseline, an explore experiment): (findings, what it was shown)."""
    user = (_system_for_supervisor(brief) + f"\nWHAT HAS JUST BEEN MEASURED ({xid}):\n{_measured(ledger, xid)}\n\nWHAT WAS MEASURED BEFORE:\n"
            f"{_measured([r for r in ledger if not (r['type'] == 'evidence' and r['body']['experiment'] == xid)])}\n\nEVERY READING OF THE SESSION:\n{_looked(ledger)}\n\n"
            f"THE FINDINGS SO FAR:\n{findings_for_supervisor(ledger)}\n\n" + SUP_FINDINGS_ASK)
    d = (ask_fn or supervise)(model, user, FINDINGS_SCHEMA)
    return list(d.get("findings") or [])[:SUP_FINDINGS], user

def take_sup_findings(ledger, turn, items, parent):
    """The supervisor's findings that cite records of the ledger and state a measured number; each other one is dropped with a note. Their ids."""
    kinds, of_run = _ref_kinds(ledger)
    out = []
    for f in list(items or [])[:SUP_FINDINGS]:
        about = [of_run(a) for a in f.get("about") or [] if isinstance(a, str)] if isinstance(f, dict) and isinstance(f.get("about"), list) else []
        text = _flat(f.get("text")) if isinstance(f, dict) else ""
        bad = [a for a in about if a not in kinds]
        if not about or bad or not text:
            append(ledger, turn, "note", parent, {"text": "a finding of the supervisor was left out: " + (f"it cites ids that are not in the ledger ({', '.join(bad)})" if bad else "it cites no record" if not about else "it has no text")})
        elif not re.search(r"\d", text):
            append(ledger, turn, "note", parent, {"text": "a finding of the supervisor was left out: it states no measured number"})
        else:
            out.append(append(ledger, turn, "finding", parent, {"about": list(dict.fromkeys(about)), "text": text, **finding_name(f), "from": parent}, by="supervisor"))
    return out

# what the researcher is told about findings, by arm (appended to its instructions)
FINDINGS_TEXT = {
    "hypotheses": """

FINDINGS. A finding is one thing the results do not yet explain. Each stays on the list at the top of every turn until you close it, so that nothing unexplained is lost.
- findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by). The harness numbers them F1, F2, ...{sup}
- decisions: one for each finding the list marks DUE, and for any other you act on: id (F1), action, and refs or reason. work: refs names the guess, hypothesis, experiment or reading that works on it (one of this answer by the id it will get; left empty, it counts as worked on but not as looked at). close: refs names the evidence, checks, verdicts or readings that explain it. same_as: refs names the finding it repeats. park: reason says why not now. A parked finding, and one you work on with nothing new about it for 2 turns, comes back as DUE.
- A guess of why whose about names a finding (for example F2) works on it.
- "It does not change the recommendation" is not a reason to park a finding: the task asks why the settings you recommend are best, so explaining a measured result is part of the goal.
- A final report is held back while a finding was never looked at (no reading or test about it) and you can still work: look at each one first. In the report, name each finding that is not closed in open_questions, with its id (F3: ...).
""",
    "plain": """

FINDINGS. A finding is one thing the results do not yet explain. Each stays on the list at the top of every turn until you close it, so that nothing unexplained is lost.
- findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations or readings, for example E2, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by). The harness numbers them F1, F2, ...
- decisions: one for each finding the list marks DUE, and for any other you act on: id (F1), action, and refs or reason. work: refs names the experiment or reading that works on it (left empty, it counts as worked on but not as looked at). close: refs names the evidence tables or readings that explain it. same_as: refs names the finding it repeats. park: reason says why not now. A parked finding, and one you work on with nothing new about it for 2 turns, comes back as DUE.
- "It does not change the recommendation" is not a reason to park a finding: the task asks why the settings you recommend are best, so explaining a measured result is part of the goal.
- A final report is held back while a finding was never looked at (no reading or experiment about it) and you can still work: look at each one first. In the report, name each finding that is not closed in open_questions, with its id (F3: ...).
""",
}
FINDINGS_TEXT["supervised"] = FINDINGS_TEXT["hypotheses"].replace("checks, verdicts or readings", "checks, rulings or readings").replace("{sup}", " The supervisor raises findings too: they stand on the same list and need your decisions like yours.")
FINDINGS_TEXT["hypotheses"] = FINDINGS_TEXT["hypotheses"].replace("{sup}", "")


def supervised_prompt(text):
    """The researcher's instructions in the arm "supervised": written for the short reply (LEAN_PROMPT), not made from prompt.txt."""
    return LEAN_PROMPT


PLAIN = (  # prompt.txt -> the instructions of the arm "plain": (text as it stands in prompt.txt, what replaces it). Each must be found exactly once.
    ("everything you have hypothesised, run, observed and concluded", "everything you have run, observed and concluded"),
    ("(a reply that states no hypothesis, test, verdict, drop or report is answered and you are asked again in the same turn, at most twice: a turn ends with a step)",
     "(a reply that states no experiment or report is answered and you are asked again in the same turn, at most twice: a turn ends with a step)"),   # CONTINUES (2026-11-22)
    ("\n5. experiment: at most one per turn.", "\n2. experiment: at most one per turn."),
    ('   - kind "explore": question says what you want to find out; tests, needs and decision_rules stay empty. Use it when you do not yet have a claim to test.', '   - kind is always "explore": question says what you want to find out.'),
    ("\n6. After an experiment the harness appends the evidence (one line per simulation) and, for every decision rule, a check: the decision rule with the measured numbers written into it, and HELD or FAILED. You never write evidence or checks yourself.",
     "\n3. After an experiment the harness appends the evidence (one line per simulation). You never write evidence yourself."),
    ("\n8. requests:", "\n4. requests:"), ("\n9. budget_request:", "\n5. budget_request:"), ("\n10. done and report:", "\n6. done and report:"),
    ("look further and test on the simulations already run (no new simulation), then one last turn for the report, so do not leave a decisive test that needs new simulations for later than you can afford",
     "look further and explore the simulations already run (no new simulation), then one last turn for the report, so do not leave a decisive experiment that needs new simulations for later than you can afford"),   # the free turns (2026-11-22)
    ("(for example E3, C5; a reading a tool returned", "(for example E3; a reading a tool returned"),   # the claims may cite readings (2026-11-22)
    ("(for example a verdict on a hypothesis that has not been tested, or a decision rule the harness cannot read)", "(for example an experiment that repeats a design you already ran)"),
    ("A hypothesis about a cause (what makes a result what it is, what limits it) is worth more than one about which of two values is larger.", "A question about a cause (what makes a result what it is, what limits it) is worth more than one about which of two values is larger."),
    ("State that as a hypothesis and test it, with the settings you may change and with the tools:", "Explore that, with the settings you may change and with the tools:"),
    ("do not write a decision rule that such a difference can decide, do not build a hypothesis on it, do not spend further simulations on it,", "do not spend further simulations on it,"),
    (' The harness marks every check that was decided by less than the tolerance; read such a check as "no difference".', ""),
)
PLAIN_DROP = ("2. whys:", "   - rethink:", "3. hypotheses:", "4. drop:", '   - kind "test":', "   - needs:", "   - decision_rules:", "7. verdicts:", "   Before the report, give a verdict")  # whole lines of prompt.txt the arm does not have, by how they begin


def plain_prompt(text):
    """The instructions of the arm "plain", made from prompt.txt: the lines about hypotheses, decision rules and verdicts
    are left out and the sentences that name them are reworded; every other word is the same, so that the two arms
    differ in the hypothesis format alone. Stops if prompt.txt has changed so that a line or sentence is not found."""
    lines = text.split("\n")
    for start in PLAIN_DROP:
        hit = [i for i, l in enumerate(lines) if l.startswith(start)]
        if len(hit) != 1:
            raise ValueError(f"prompt.txt: {len(hit)} lines begin with {start!r}; the arm 'plain' expects one")
        del lines[hit[0]]
    text = "\n".join(lines)
    for a, b in PLAIN:
        if text.count(a) != 1:
            raise ValueError(f"prompt.txt: {a[:50]!r}... stands {text.count(a)} times; the arm 'plain' expects once")
        text = text.replace(a, b)
    left = [w for w in ("hypothes", "decision rule", "decision_rule", "verdict", "HELD", "FAILED", "from_why", "whys", "rethink") if w in text]
    if left:
        raise ValueError(f"the instructions of the arm 'plain' still name: {', '.join(left)}")
    return text


def call(q):
    fn = tools.TOOLS.get(q.get("tool"))
    try:
        out = fn(**(q.get("args") or {})) if fn else "unknown tool"
    except Exception as e:  # a bad argument is the model's problem, reported back to it
        out = f"error: {e}"
    s = out if isinstance(out, str) else json.dumps(out)
    return s[:CAP] + (" ...[truncated]" if len(s) > CAP else "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", help="session id: its folder is sessions/<id>/ (ledger.jsonl and runs/). Default: a new id sNNN. An existing id continues that session")
    ap.add_argument("--brief", help=f"brief id (briefs/<id>.json) of a new session; default {tools.DEFAULT_BRIEF}. An existing session keeps its own")
    ap.add_argument("--budget", type=int, help=f"simulations granted at the start; default: the brief's limits.simulations (never more than that limit; when it is lower, a budget_request can raise it up to the limit)")
    ap.add_argument("--draft", choices=["on", "off"], default="on", help="on: the model may write a draft before its JSON answer and the draft is kept in the ledger; off: answer only")
    ap.add_argument("--max-tokens", type=int, help="most tokens of one answer, draft included; default 32000 with the draft (the default), 3000 without. The draft may use at most half of them")
    ap.add_argument("--policy", "--mode", dest="policy", choices=["share", "cap", "prio"], default="share", help="the scheduling policy: how the scheduler divides the link (prio: only for a brief with a network). The operator's choice, never shown to the model (--mode is its earlier name)")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--judge", choices=["on", "off"], default="on", help="on (the default): a second model call judges whether each new hypothesis follows from the guess of why it names, and a hypothesis that does not is refused; off: no such call")
    ap.add_argument("--arm", choices=["hypotheses", "plain", "supervised"], help="supervised: two agents. The researcher proposes and does not rule on its own tests; a supervisor, asked apart from it, reviews each test before "
                    "its simulations are run and rules on what its checks mean (no judge, no rethink, no verdicts by the researcher). hypotheses (the default): the loop as it is. plain: the same loop, model, brief, budget and final report without the hypothesis format "
                    "(no hypotheses, decision rules or verdicts; experiments only explore), for the comparison that asks whether the format helps. An existing session keeps its own")
    ap.add_argument("--baseline", choices=["on", "off"], default="on", help="on an empty ledger, first run the harness's own default experiment X0")
    a = ap.parse_args()
    global LEDGER, SID, TOLERANCE
    tools.POLICY = a.policy
    schema, system = json.loads((H / "schema.json").read_text()), (H / "prompt.txt").read_text()
    model = requests.get(API + "/models", timeout=30).json()["data"][0]["id"]
    try:
        SID = tools.open_session(a.session, a.brief)  # after the model server answered, so a failed start leaves no empty session folder
    except ValueError as e:
        ap.error(str(e))
    brief = tools.describe_system()  # the brief, with the descriptions of the outputs and the tools
    if a.policy not in tools.policies(brief):
        ap.error(f"the scheduling policy {a.policy} exists only for a brief that has a network")
    per = brief["limits"]["simulations_per_experiment"]
    schema = answer_format(schema, brief)
    was = json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("arm", "hypotheses") if (tools.SESSION / "session.json").is_file() else None
    if was and a.arm and a.arm != was:
        ap.error(f"session {SID} works in the arm {was}, not {a.arm}")
    arm = was or a.arm or "hypotheses"
    if arm == "plain":
        schema, system = plain_format(schema), plain_prompt(system)
    if arm == "supervised":
        schema, system = supervised_format(schema), supervised_prompt(system)
    # the short format of the arm "hypotheses" (2026-11-22): a new session, or one that started in it; a session started before keeps the full format
    short = arm == "hypotheses" and (was is None or json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("format") == "short")
    if short:
        schema, system = short_format(schema), short_prompt(system)
    asks_budget = arm == "plain" or (arm == "hypotheses" and not short)   # the formats that still have budget_request (the turn's text names it)
    if may_change(brief):  # only a session that may change the structure is told how
        plain_s = STRUCTURE
        for a_, b_ in STRUCTURE_PLAIN if arm == "plain" else ():
            assert plain_s.count(a_) == 1, a_
            plain_s = plain_s.replace(a_, b_)
        system += plain_s
    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)
    stated_rules(system, arm)
    if arm == "plain" and [w for w in PLAIN_WORDS if w in system.lower()]:   # the plain arm is told nothing of hypotheses (the coherence audit, 2026-11-22: STRUCTURE was added after plain_prompt's check)
        raise ValueError(f"the instructions of the arm 'plain' name: {', '.join(w for w in PLAIN_WORDS if w in system.lower())}")
    try:   # a label's length, in the answer format too
        schema["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["label"]["maxLength"] = LABEL_MOST
    except (KeyError, IndexError, TypeError):
        pass
    if isinstance(schema["properties"].get("requests"), dict):   # the most requests a reply may hold, in the answer format too (the coherence audit, 2026-11-22)
        schema["properties"]["requests"]["maxItems"] = LOOKS if arm == "supervised" else REQUESTS_MOST
    why_schema = schema["properties"]["whys"]["items"] if "whys" in schema["properties"] else None   # a restated guess (the arm "supervised", 2026-11-22)
    repair_schema = {"type": "object", "additionalProperties": False, "required": ["decision_rule", "rival", "rival_predicts", "runs"], "properties": {   # a repaired test (the arm "supervised", 2026-11-22)
        "decision_rule": {"type": "string"}, "rival": {"type": "string"}, "rival_predicts": {"type": "string", "enum": ["held", "failed"]},
        "runs": {"type": "array", "items": schema["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"], "description": "only if the simulations must change; empty keeps them"}}}
    judged, judge_written = {}, set()   # each pair of a guess and a hypothesis is judged once in a session: a second attempt of the same turn gets the same reading
    def judge_fn(why, h):
        k = (why["guess"], h["text"])
        if k not in judged:
            stage("judge")
            judged[k] = judge_link(model, brief, why, h)
        return judged[k]
    # gate 0 of the arm "supervised": each new guess is read by the supervisor against the records it cites, once for a statement (a second attempt of the same
    # turn gets the same reading). A guess with a defect is refused the first time; a guess about the same records stated after that is accepted whatever the
    # supervisor finds, and its review says so: the supervisor can be wrong, and it must not be able to stop the work
    grounded, refused_about, ground_written = {}, {}, set()
    def ground_take(k, w, g, saw):
        """A guess's reading, by itself or in the batched first review: whether it is refused (once in a turn for the same records), kept for the turn."""
        about = tuple(sorted(w["about"]))
        warning = g["defect"] in GROUND_WARNINGS   # recorded, and the guess is accepted (2026-11-22, after s050 and s051)
        scope = (turn if REFUSED_ONCE == "turn" else None, about)   # once in a turn (the coherence audit, 2026-11-22: it was once in the session)
        refuse = g["defect"] != "none" and not warning and not refused_about.get(scope)
        if refuse:
            refused_about[scope] = 1
        grounded[k] = {**g, "saw": saw, "refuse": refuse, "warning": warning, "result": w["result"], "guess": w["guess"]}
    def ground_fn(w):
        k = gkey(w)
        if k not in grounded:
            try:
                stage("ground")
                g, saw = ground_of(model, brief, ledger, w)
            except (ValueError, KeyError, TypeError) as e:
                g, saw = {"records_show": "", "nearest_earlier": "none", "defect": "none", "because": f"the supervisor's reading could not be read ({type(e).__name__}): the guess is accepted unread", "unread": True}, ""
            ground_take(k, w, g, saw)
        return grounded[k]
    prereviewed = {}   # test_key -> (the batched first review's answer for that test, what was shown): taken by round 1 instead of a call of its own
    def prefetch(parsed, mode_now):
        """The batched first review of this reply (stage 4 of the coherence audit, 2026-11-22): a dry run of sort_out (no call to anyone) finds the new
        guesses and tests the harness accepts; those not yet read are asked in one request; the answers fill the caches the single reviews use."""
        found = []
        def collect(w):
            k = gkey(w)
            if k not in grounded and k not in [x[0] for x in found]:
                found.append((k, json.loads(json.dumps(w))))
            return {"records_show": "", "nearest_earlier": "none", "defect": "none", "because": "", "refuse": False, "warning": False}
        try:
            ok0, _no0 = sort_out(json.loads(json.dumps(parsed)), brief, ledger, max(0, budget - sims), mode_now, insist=not asked, judge=None, supervised=True, ground=collect, short=short, restate=None)
        except Exception:   # the real pass says what is wrong; the batch is only a way to ask sooner
            return
        tests = []
        ex0 = ok0.get("experiment")
        if ex0 is not None and ex0.get("kind") == "test":
            n_h, n_y = sum(r["type"] == "hypothesis" for r in ledger), sum(r["type"] == "why" for r in ledger)
            hyps, whys = {f"H{n_h + i + 1}": h for i, h in enumerate(ok0["hypotheses"])}, {f"Y{n_y + i + 1}": w for i, w in enumerate(ok0["whys"])}
            for hid in ex0.get("tests") or []:
                if any(rival_problem(d) or rule_size_problem(d) for d in ex0.get("decision_rules") or [] if d.get("for") == hid):
                    continue   # refused by the harness before any review
                h = hyps.get(hid) or next((r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), None)
                if h is None:
                    continue
                w = whys.get(h.get("from_why")) or next((r["body"] for r in ledger if r["type"] == "why" and r["id"] == h.get("from_why")), None)
                key = test_key(ex0, hid, h.get("text"))
                if key not in prereviewed:
                    tests.append((hid, ex0, _case(ledger, hid, [d for d in ex0.get("decision_rules") or [] if d.get("for") == hid], h=h, w=w), key))
        if len(found) + len(tests) < 2:   # one item is asked alone, as before: nothing to share
            return
        try:
            stage("review")
            g_ans, t_ans, saw = first_review(model, brief, ledger, [w for _, w in found], [(hid, ex, case) for hid, ex, case, _ in tests])
        except (ValueError, KeyError, TypeError, IndexError, AttributeError) as e:   # a model server error ends the session, as at any other call
            append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"the supervisor's batched first review could not be read ({type(e).__name__}): each new guess and test is asked alone"})
            return
        for (k, w), x in zip(found, g_ans):
            if isinstance(x, dict):
                try:
                    g, _saw = ground_of(model, brief, ledger, w, pre=x, pre_saw=saw)
                    ground_take(k, w, g, saw)
                except (ValueError, KeyError, TypeError):
                    pass   # an item that cannot be read: that guess is asked alone
        for (hid, ex, case, key), x in zip(tests, t_ans):
            if isinstance(x, dict):
                prereviewed[key] = (x, saw)
    restated_cache = {}
    def restate_fn(w, why, by):
        """One restatement of a guess that was not accepted (the arm "supervised", 2026-11-22): a short call to the researcher with the reason, the guess as
        stated, what was learned since its last guess and what was measured; the guess's own format. Returns the restated guess, or None (not readable)."""
        k = (" ".join(str(w.get("guess")).split()), why)
        if k in restated_cache:   # a second attempt of the same turn: the same restatement
            return restated_cache[k]
        flat = lambda v: " ".join(str(v).split())
        since = learned_since(ledger)
        user = (f"YOUR GUESS WAS NOT ACCEPTED AS YOU STATED IT ({'the supervisor' if by == 'supervisor' else 'the harness'}): {flat(why)}\n\nTHE GUESS AS YOU STATED IT:\n  about: {', '.join(map(str, w.get('about') or []))}\n"
                f"  result: {flat(w.get('result'))}\n  guess: {flat(w.get('guess'))}\n  revises: {w.get('revises')}\n\nWHAT WAS LEARNED SINCE YOUR LAST GUESS:\n"
                + ("\n".join(record_line(r, ledger) for r in ledger if r["id"] in (since or ()) and r["type"] != "simulation") or "  nothing") + "\n"
                f"WHAT HAS BEEN MEASURED SO FAR:\n{_measured(ledger)}\n\nRestate this guess once, in the same form: about (the ids of the records it starts from), result (that result, with its numbers), "
                "guess (what in the system would make it so), revises (the id of an earlier guess it states more exactly, or null). It is taken as you restate it; if it still does not meet "
                "the rule above, it is recorded as contested. Answer with one JSON object.")
        try:
            stage("restate", by=by)
            content, _d, _f, _u = called("researcher", model, RESTATE_SYSTEM, user, why_schema, a.draft == "on", a.temperature, min(a.max_tokens, SHORT_CALL_TOKENS))
            count["calls"] += 1
            out = json.loads(content)
            out = findings_in_whys({"whys": [out]}, ledger)["whys"][0] if isinstance(out, dict) else None
        except ValueError:
            out = None
        restated_cache[k] = out
        return out
    judge = judge_fn if a.judge == "on" and arm == "hypotheses" else None   # the supervised arm has the supervisor's review of the test in its place
    tol_given = type((brief.get("goal") or {}).get("tolerance")) in (int, float)   # tools.check_brief has made sure it is a number of per cent between 0 and 100
    TOLERANCE = float(brief["goal"]["tolerance"]) if tol_given else DEFAULT_TOLERANCE
    decision_rules.EQUAL_WITHIN = TOLERANCE   # == holds within the tolerance, as the turn's text says two results are equal (the coherence audit, 2026-11-22)
    a.budget = brief["limits"]["simulations"] if a.budget is None else a.budget
    a.max_tokens = a.max_tokens or (32000 if a.draft == "on" else 3000)
    limit = brief["limits"]["simulations"]  # the most simulations the session can ever be granted
    LEDGER, meta = tools.SESSION / "ledger.jsonl", tools.SESSION / "session.json"
    if a.budget > limit:
        if not meta.exists():  # a new session that cannot start leaves no empty folder behind
            (tools.SESSION / "runs").rmdir()
            tools.SESSION.rmdir()
        ap.error(f"the starting budget is at most the brief's limit of {limit} simulations")
    if not meta.exists():  # the session's own record of what it was given; the scheduling policy is not in it
        meta.write_text(json.dumps({"id": SID, "brief": brief["id"], "model": model, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "flags": {"budget": a.budget, "draft": a.draft, "max_tokens": a.max_tokens, **({"draft_tokens": draft_tokens(a.max_tokens)} if a.draft == "on" else {}), "temperature": a.temperature, "baseline": a.baseline, "judge": a.judge if arm == "hypotheses" else "off", **({"arm": arm} if arm != "hypotheses" else {"format": "short"} if short else {}),
                                              **({"supervisor": {"model": model, "temperature": 0, "max_tokens": 9000, "draft_tokens": draft_tokens(9000), "follow_up_tokens": AGAIN_TOKENS, "first_review": "one request for the new guesses and tests of a reply" if BATCH_FIRST else "one request each", "sees": "the brief's description, the guess, the hypothesis, the decision rules, the planned simulations, the measured numbers; not the researcher's observations or reasons"}} if arm == "supervised" else {})}, "given": brief, "prompt": system}, indent=1) + "\n")
    print(f"session {SID} (brief {brief['id']}): {tools.SESSION}", flush=True)
    ledger = load_ledger()
    fresh = not ledger   # a new ledger: the baseline runs now (inside the guard below, after the stop handlers: the coherence audit, 2026-11-22)
    turn, sims, tool_only, pending, budget = max([r["turn"] for r in ledger], default=0), 0, 0, [], a.budget
    stay, stay_next = 0, False   # the calls of the researcher after the first in this turn; whether the next call stays in this turn (CONTINUES)
    asked = False  # whether the model was already asked for the verdicts that were missing when it sent its report
    held_turns = set()  # the turns in which a report was held back for findings never looked at (at most FINDING_HOLDS)
    giving_up = False  # set after UNUSABLE turns in a row without a usable answer: the next turn is the last and takes only the report
    free_left = FREE_TURNS  # the turns after the budget is used up in which the researcher may still look and test on simulations already run (s048)
    if not fresh:   # a continued session (the coherence audit, 2026-11-22: it got its whole budget again): what it used, was granted and where it stands, from its ledger
        sims = sum(1 for r in ledger if r["type"] == "simulation" and r["turn"] >= 1 and "same_as" not in r["body"])
        grants = [int(g.group(1)) for r in ledger if r["type"] == "note" and (g := re.search(r"the budget is now (\d+)", str(r["body"].get("text") or "")))]
        budget = grants[-1] if grants else budget
        free_left = max(0, FREE_TURNS - sum(1 for r in ledger if r["type"] == "turn" and r["body"].get("last_turn") == "free"))
        giving_up = any(r["type"] == "turn" and r["body"].get("last_turn") == "report" for r in ledger)
    how, unusable = None, 0  # how the session ended (None while it runs); turns in a row without a usable answer
    count = {"calls": 0, "length": 0}  # requests answered by the model server, and how many of them ended with finish_reason "length"

    def sup_log(rid, gate, saw, answer):
        """Beside the ledger: what the supervisor was shown for one of its records, and what it answered (no tool reads it; the page shows it on request)."""
        with (tools.SESSION / SUPERVISOR_FILE).open("a") as f:
            f.write(json.dumps({"id": rid, "turn": turn, "gate": gate, "shown": saw, "answer": answer}) + "\n")


    # ---- the review of a test before it runs, in rounds (the arm "supervised"; 2026-11-22, the operator, after the reviews of s047 and s050) ----
    objected = {}   # hypothesis -> the supervisor's last feedback, for a test run although it still objected (AFTER_ROUNDS "contested")
    def round_label(approved, n):
        return "approved" if approved else AFTER_ROUNDS if n >= REVIEW_ROUNDS else "sent_back"

    def test_of(ex, hid):
        """One test of an experiment as an experiment of its own: its rules, the simulations they name, its needs."""
        return without_tests(ex, [h for h in ex.get("tests") or [] if h != hid])

    def record_round(hid, n, test, rev, saw, by="supervisor", label=None):
        """One round of the review of a test: the test as proposed, the boxes and the feedback, the round and the decision. By the supervisor, or by the
        harness when its own checks refused the repaired test (in the last round: not_run, the coherence audit, 2026-11-22: it was "contested", the
        supervisor's word, for a test that did not run). Returns (the record's id, the decision)."""
        label = label or round_label(rev.get("approved"), n)
        gid = append(ledger, turn, "review", hid, {"for": hid, "gate": "design", "round": n, "decision": label,
                                                  "test": {"decision_rules": [{k: d.get(k) for k in ("decision_rule", "rival", "rival_predicts")} for d in (test or {}).get("decision_rules") or []],
                                                           "runs": [{"label": r.get("label"), "params": r.get("params"), **({"structure": r["structure"]} if r.get("structure") else {})} for r in (test or {}).get("runs") or [] if isinstance(r, dict)]},
                                                  "rules": [d.get("decision_rule") for d in (test or {}).get("decision_rules") or []],
                                                  "simulations": next((x.get("simulations") for x in (test or {}).get("needs") or [] if x.get("for") == hid), [r.get("label") for r in (test or {}).get("runs") or []]),
                                                  **{k: v for k, v in rev.items() if k != "approved"}}, by=by)
        if by == "supervisor":
            sup_log(gid, "design", saw, rev)
        if rev.get("cut"):
            append(ledger, turn, "note", gid, {"text": f"the harness cut {rev['cut']} part(s) of the supervisor's feedback on the test of {hid} (round {n}): they wrote a decision rule, and the repair is the researcher's"})
        return gid, label

    def drop_after(hid, feedback, n):
        append(ledger, turn, "drop", hid, {"for": hid, "why": f"the supervisor still refused its test after round {n} of {REVIEW_ROUNDS}: {feedback}"}, by="harness")

    def design_round_one(ex):
        """Round one of each test of an experiment: the harness refuses, with no call, a rule whose rival is missing or would pass it too
        (rival_problem, as in the arm "hypotheses"); the supervisor reviews each other test. Returns (the experiment of the tests that run now,
        or None; the tests sent back for repair: (hypothesis, its test, the review, the review's id, the experiment's simulations))."""
        bad = {}
        for d in ex.get("decision_rules") or []:
            why = rival_problem(d) or rule_size_problem(d)
            if why and d.get("for") not in bad:
                bad[d.get("for")] = why
        for h, why in bad.items():
            append(ledger, turn, "note", h, {"text": f"refused part of the answer: test of {h}. Reason: {why}. The other parts of that answer were accepted.", "part": f"test of {h}", "reason": why})
        every = list(ex.get("runs") or [])
        if bad:
            ex = without_tests(ex, list(bad))
            if ex is None:
                return None, []
        held, gone = [], []
        for hid in ex["tests"]:
            test = test_of(ex, hid)
            pre = prereviewed.pop(test_key(ex, hid, next((r["body"].get("text") for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), "")), None)   # its answer in the batched first review
            try:
                if pre is None:
                    stage("design", hid, 1)
                rev, saw = review_design(model, brief, ledger, ex, hid, pre=pre[0] if pre else None, pre_saw=pre[1] if pre else None)
            except (ValueError, KeyError, TypeError) as e:
                append(ledger, turn, "note", hid, {"text": f"the supervisor's review of the test of {hid} could not be read ({type(e).__name__}): the test is run unreviewed"})
                continue
            gid, label = record_round(hid, 1, test, rev, saw)
            if label == "sent_back":
                held.append((hid, test, rev, gid, every))
            elif label == "contested":
                objected[hid] = rev["feedback"]
            elif label == "dropped":
                drop_after(hid, rev["feedback"], 1)
                gone.append(hid)
        out = without_tests(ex, [h for h, *_ in held] + gone) if held or gone else ex
        return out, held

    def repaired(test, hid, rp, every, reserved=0):
        """The test as the researcher repaired it, made whole and checked by the harness as any test: (the test, what is wrong with it, or None)."""
        rule = {"for": hid, "decision_rule": rp.get("decision_rule"), "rival": rp.get("rival"), "rival_predicts": rp.get("rival_predicts")}
        # runs given replace the simulations of the same label and add new ones; the others are kept (the coherence audit, 2026-11-22: the prompt said
        # "only if they must change", while any list replaced all of them); what no rule names leaves below
        given = {r.get("label"): r for r in rp.get("runs") or [] if isinstance(r, dict)} if isinstance(rp.get("runs"), list) else {}
        base = [r for r in test.get("runs") or [] if isinstance(r, dict)]
        base += [r for r in every if isinstance(r, dict) and r.get("label") not in {q.get("label") for q in base}]
        runs = [dict(given.pop(r.get("label"), r)) for r in base] + [dict(r) for r in given.values()]
        t2 = {"kind": "test", "tests": [hid], "question": test.get("question") or "", "measurements": list(MEASURES.values()) or test.get("measurements") or [], "runs": runs, "decision_rules": [rule],   # every measurement of the answer: a repaired rule may name one a sibling test defined
              "varied": varied_of(runs, brief), "control": None}
        if not isinstance(rule["decision_rule"], str) or not rule["decision_rule"].strip():
            return t2, "the repaired test needs a decision rule"
        why = rival_problem(rule) or rule_size_problem(rule)
        if why:
            return t2, why
        try:   # in the order of the normal path (s052, 2026-11-22: a repair's network change that could not be applied stopped the session)
            needs, why, idle = lean_needs(t2, brief)
            if why:
                return t2, why
            t2 = {**t2, "needs": needs}
            why = experiment_problem(t2, brief, ledger, None, states(ledger)[0], lean=True)   # the experiment as sent: labels, knobs, its network changes
            if why:
                return t2, why
            t3, cuts = trim(t2, brief, ledger)
            if t3 is None:
                return t2, "; ".join(w for _, w in cuts) or "no simulation of the repaired test can be run"
            needs, why, idle = lean_needs(t3, brief)
            if why:
                return t3, why
            t3 = without_tests({**t3, "needs": needs}, []) or t3   # the simulations no rule names leave
            why = experiment_problem(t3, brief, ledger, max(0, budget - sims - reserved), states(ledger)[0], lean=True)   # within what the approved tests of this turn leave
            return t3, why
        except (ValueError, KeyError, TypeError) as e:   # whatever the harness cannot check in a repair refuses that round, with its reason; it never stops the session
            return t2, f"the repaired test could not be checked: {' '.join(str(e).split())[:300]}"

    def repair_user(hid, test, n, who, feedback, reserved=0, refused=None):
        """What the researcher is given to repair one test: the hypothesis and its guess, the test as proposed, the round, the feedback, the records the
        feedback and the guess cite, what was measured, the measurements of the answer, the knobs, and how a network change is written."""
        flat = lambda v: " ".join(str(v).split())
        h = next((r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), {})
        y = next((r["body"] for r in ledger if r["type"] == "why" and r["id"] == h.get("from_why")), {})
        rules = "".join(f"  decision rule: {flat(d.get('decision_rule'))}\n  rival: {flat(d.get('rival'))}\n  rival_predicts: {d.get('rival_predicts')}\n" for d in test.get("decision_rules") or [])
        runs = "".join(f"  {r.get('label')} {{{', '.join(f'{k}={v}' for k, v in (r.get('params') or {}).items())}}}" + (f"; network changed: {edits_say(edits_of(r))}" if edits_of(r) else "") + "\n" for r in test.get("runs") or [] if isinstance(r, dict))
        knobs = "; ".join(f"{k} ({', '.join(map(str, v['choices'])) if 'choices' in v else str(v['min']) + ' to ' + str(v['max'])})" for k, v in brief["knobs"].items())
        ids = {r["id"]: r for r in ledger}
        cited = [i for i in dict.fromkeys(re.findall(r"\b([A-Z]{1,2}\d+)\b", str(feedback)) + [a_ for a_ in y.get("about") or [] if isinstance(a_, str)]) if i in ids and ids[i]["type"] in LEARNED + ("simulation",)]
        mine = "".join(f"  {m['name']} = {m['stat']} of {m['of']}" + (f" against the level {m['level']}" if m.get("level") is not None else "") + "\n" for m in MEASURES.values())
        left = max(0, budget - sims - reserved)
        example = change_example(brief) if may_change(brief) else None
        return (f"YOUR TEST OF {hid} WAS SENT BACK BEFORE IT RAN. This is round {n} of at most {REVIEW_ROUNDS}.\n\nYOUR GUESS {h.get('from_why')}: {flat(y.get('guess'))}\n"
                f"YOUR HYPOTHESIS {hid}: {flat(h.get('text'))}\n\nTHE TEST AS PROPOSED:\n{rules}  simulations:\n{runs}\n"
                + (f"YOUR LAST REPAIR, WHICH THE HARNESS COULD NOT USE (the test above stands until a repair is accepted):\n" + "".join(f"  decision rule: {flat(d.get('decision_rule'))}\n" for d in refused.get("decision_rules") or [])
                   + "  simulations:\n" + "".join(f"  {r.get('label')} {{{', '.join(f'{k}={v}' for k, v in (r.get('params') or {}).items())}}}" + (f"; network changed: {edits_say(edits_of(r))}" if edits_of(r) else "") + "\n" for r in refused.get("runs") or [] if isinstance(r, dict)) if refused else "")
                + f"WHY IT WAS SENT BACK ({who}): {flat(feedback)}\n\n"
                + (f"THE RECORDS THE FEEDBACK AND YOUR GUESS CITE:\n" + "\n".join(record_line(ids[i], ledger) for i in cited) + "\n\n" if cited else "")
                + f"WHAT HAS BEEN MEASURED SO FAR:\n{_measured(ledger)}\n\n" + (f"THE MEASUREMENTS YOUR ANSWER DEFINES (a rule may name them as name@label):\n{mine}\n" if mine else "") + f"THE KNOBS: {knobs}\n\n"
                "Repair this test only. decision_rule: the comparison that decides the hypothesis, in the form of your instructions (numbers; measure@label; + - * / and parentheses; abs(), "
                f"min(), max(); one of < <= > >= == in each comparison; at most {COMPARISONS_MOST} comparisons, joined by AND and OR). rival: the strongest competing explanation you can think of, one sentence. "
                "rival_predicts: held or failed, what the rule gives if the rival is true (held is refused: choose simulations where the two differ). runs: only the simulations that are new "
                "or change, each with a label and a value for every knob: one with the label of a simulation of the test replaces it, the others are kept; an empty list keeps them all. "
                "A rule that names only simulations already run cannot fail and is refused, unless it compares a measurement your answer defines (listed above), which is computed now from "
                "what those simulations recorded: " + (f"name at least one simulation that has not run yet ({left} can still run), or such a measurement." if left else "no new simulation can run now, so compare such a measurement.")
                + (" A simulation may change the network (structure), as your instructions describe: a run keeps its change unless the feedback is about it, and a run you give states its "
                   "whole change again. Each change states every field, for example, on this network: " + json.dumps(example) if example else
                   " A simulation may change the network (structure), as your instructions describe: a run keeps its change unless the feedback is about it." if may_change(brief) else ""))

    def repair_rounds(hid, test, rev, gid, every, reserved=0):
        """The rounds after the first for one test sent back: the researcher repairs it from the feedback (a short call that asks for the test only),
        the harness checks the repair, the supervisor reviews it; at most REVIEW_ROUNDS rounds, then AFTER_ROUNDS. Returns the test to run now, or
        None. A repair that cannot be read gives a note: the test does not run in this turn, and nothing else is refused."""
        n, parent, earlier, refused = 1, gid, [(1, "the supervisor", rev["feedback"])], None
        while True:
            who, feedback = earlier[-1][1], earlier[-1][2]
            user = repair_user(hid, test, n + 1, who, feedback, reserved, refused)
            try:
                stage("repair", hid, n + 1)
                content, _d, _f, _u = called("researcher", model, REPAIR_SYSTEM + (STRUCTURE if may_change(brief) else ""), user, repair_schema, a.draft == "on", a.temperature, min(a.max_tokens, SHORT_CALL_TOKENS))
                count["calls"] += 1
                rp = json.loads(content)
                if not isinstance(rp, dict):
                    raise ValueError("not an object")
            except ValueError as e:
                append(ledger, turn, "note", parent, {"text": f"your repair of the test of {hid} for round {n + 1} could not be read ({e}): the test is not run in this turn and {hid} stays open", "part": f"repair of {hid}", "reason": "could not be read"})
                return None
            n += 1
            rid = append(ledger, turn, "repair", parent, {"for": hid, "round": n, **{k: rp.get(k) for k in ("decision_rule", "rival", "rival_predicts")}, "runs": rp.get("runs") or []})
            t2, problem = repaired(test, hid, rp, every, reserved)
            if problem:   # the harness's own checks: a round of its own, with its reason as the feedback
                gid, label = record_round(hid, n, t2, {"approved": False, "feedback": problem, "because": problem, "defect": "none"}, "", by="harness", label="not_run" if n >= REVIEW_ROUNDS else None)
                if label != "sent_back":   # the last round: a test the harness cannot use is not run, and its hypothesis stays open (the harness's refusal is no objection of the supervisor's)
                    append(ledger, turn, "note", gid, {"text": f"the test of {hid} is not run: its last repair could not be used ({problem}); {hid} stays open"})
                    return None
                earlier.append((n, "the harness", problem))
                parent, refused = gid, t2   # the test stays the last one the harness accepted: a refused repair is not what the next is read against
                continue
            try:
                stage("design", hid, n)
                rev, saw = review_design(model, brief, ledger, t2, hid, round_no=n, earlier=earlier)
            except (ValueError, KeyError, TypeError) as e:
                append(ledger, turn, "note", rid, {"text": f"the supervisor's review of the repaired test of {hid} could not be read ({type(e).__name__}): the test is run unreviewed"})
                return t2
            gid, label = record_round(hid, n, t2, rev, saw)
            if label == "approved":
                return t2
            if label == "contested":
                objected[hid] = rev["feedback"]
                return t2
            if label == "dropped":
                drop_after(hid, rev["feedback"], n)
                return None
            earlier.append((n, "the supervisor", rev["feedback"]))
            parent, test, refused = gid, t2, None

    def rule_tests(ex):
        """Gate 2: the harness has checked the rules; the supervisor says what each check means. Its ruling is the hypothesis's verdict."""
        xid = next(r["id"] for r in reversed(ledger) if r["type"] == "experiment")
        for hid in ex["tests"]:
            rule_one(xid, hid)

    ruled_again = set()   # the checked hypotheses whose missing ruling was asked for again (once each)
    def rule_missing():
        """A checked hypothesis without a ruling (its ruling could not be read) gets it asked for again at the start of the next turn, once (s053, 2026-11-22:
        H2's ruling was lost, H2 could be neither dropped nor followed, and the session was stuck)."""
        ruled = {r["body"]["for"] for r in ledger if r["type"] == "verdict"}
        for r in [r for r in ledger if r["type"] == "check" and r["body"]["result"] in ("held", "failed")]:
            hid, xid = r["body"]["for"], r["body"]["experiment"]
            if hid not in ruled and (xid, hid) not in ruled_again and states(ledger)[0].get(hid) == "open":
                ruled_again.add((xid, hid))
                append(ledger, turn, "note", hid, {"text": f"{hid}'s test was checked ({r['id']}) but has no ruling: the supervisor is asked for it again"})
                rule_one(xid, hid)
                ruled.add(hid)

    def rule_one(xid, hid):
        """The supervisor's ruling on one checked test: the hypothesis's verdict."""
        if True:
            if not any(r["type"] == "check" and r["body"]["experiment"] == xid and r["body"]["for"] == hid and r["body"]["result"] in ("held", "failed") for r in ledger):
                return   # nothing was checked for it (a simulation its rule names failed): it stays open
            doubt = next((r["body"].get("doubt_if") or "" for r in reversed(ledger) if r["type"] == "review" and r.get("by") == "supervisor" and r["body"].get("gate") != "ground" and r["body"].get("for") == hid), "")   # a harness round has none (the coherence audit: KeyError stopped the session)
            try:
                stage("ruling", hid)
                ruling, saw = rule_on(model, brief, ledger, xid, hid, doubt, contested=objected.get(hid))
            except (ValueError, KeyError, TypeError) as e:
                append(ledger, turn, "note", hid, {"text": f"the supervisor's ruling on {hid} could not be read ({type(e).__name__}): {hid} stays open"})
                return
            vid = append(ledger, turn, "verdict", hid, {"for": hid, "result": ruling["result"], "because": ruling["because"], "next": ruling["retest"], "fair": ruling["fair"], "defect": ruling["defect"],
                                                       "shows": ruling["shows"], "checks": ruling["checks"], "experiment": xid, **({"doubt_if": doubt} if doubt else {}),
                                                       **({"changed_by_harness": ruling["changed_by_harness"]} if ruling.get("changed_by_harness") else {}), **({"contested": True} if objected.get(hid) else {})}, by="supervisor")
            sup_log(vid, "ruling", saw, ruling)
            if ruling.get("findings_cut"):
                append(ledger, turn, "note", vid, {"text": f"the supervisor's ruling on {hid} ran on in its findings and was cut off at its limit: the ruling stands, its findings are left out"})
            take_sup_findings(ledger, turn, ruling.get("findings"), vid)   # what it found unexplained in these results (2026-11-22)

    def finish():
        """session.json: when and how the session ended, the report's ledger id, the hypotheses still open."""
        m = json.loads(meta.read_text())
        st = states(ledger)[0]
        m.update(ended=time.strftime("%Y-%m-%dT%H:%M:%S"), how=how or "stopped from outside", report=next((r["id"] for r in reversed(ledger) if r["type"] == "report"), None),
                 left_open=[h for h, v in st.items() if v == "open"], without_verdict=[h for h in sorted(states(ledger)[1], key=lambda h: int(h[1:])) if st.get(h) == "open"], turns=turn, simulations=sims, calls=count["calls"], calls_by_agent=dict(CALLS.get("by") or {}), cut_off=count["length"])
        meta.write_text(json.dumps(m, indent=1) + "\n")

    if meta.exists() and json.loads(meta.read_text()).get("report"):
        ap.error(f"session {SID} ended with its final report ({json.loads(meta.read_text())['report']}) and cannot be continued")
    if meta.exists() and "how" in (m := json.loads(meta.read_text())):  # a session that is continued is running again
        meta.write_text(json.dumps({k: v for k, v in m.items() if k not in ("ended", "how", "report", "left_open")}, indent=1) + "\n")
    for sig in (signal.SIGTERM, signal.SIGHUP):  # stopped from outside, or its terminal closed: still record that it ended
        signal.signal(sig, lambda *_: sys.exit(143))
    try:
        if a.baseline == "on":
            baseline(ledger)
        if arm == "supervised" and fresh and any(r["id"] == "E0" for r in ledger):   # findings (2026-11-22): the baseline's results come in with no ruling, so the supervisor looks at them
            try:
                stage("look", "X0")
                items, saw = sup_findings_of(model, brief, ledger, "X0")
                take_sup_findings(ledger, 0, items, "E0")
                sup_log("X0", "findings", saw, {"findings": items})
            except Exception as e:   # its look is not needed to go on: a note, and the session goes on (the coherence audit, 2026-11-22: a model server error stopped it unrecorded)
                append(ledger, 0, "note", "E0", {"text": f"the supervisor's look at the baseline could not be read ({type(e).__name__}): no finding of its own"})
        while how is None:
            # a last turn: "report" after too many unusable answers (only the final report is accepted), "budget" when the
            # budget is used up (no experiment is accepted and the report is required); otherwise an ordinary turn
            staying, stay_next = stay_next, False   # the same turn goes on (CONTINUES): its mode as it was, no new turn record
            if staying:
                need_now = False
            else:
                mode, need_now = "report" if giving_up else ("free" if free_left > 0 else "budget") if sims >= budget else None, False
                free_left -= mode == "free"
            text = render(ledger, readings=arm == "supervised", rethinks=arm == "hypotheses")
            size = count_tokens(model, text)
            if size > LEDGER_TOKENS:
                append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"loop stopped by the harness: the rendered ledger is {size} tokens, over the limit of {LEDGER_TOKENS}"})
                how = "ledger too large"
                break
            stay = stay + 1 if staying else 0
            if not staying:
              turn += 1
              since = max((i for i, r in enumerate(ledger) if r["type"] == "turn"), default=-1)  # what was added after the previous turn's record
              append(ledger, turn, "turn", ledger[-1]["id"] if ledger else None, {"simulations_left": max(0, budget - sims), "open_hypotheses": sum(v == "open" for v in states(ledger)[0].values()),
                                                                                    "added": [r["id"] for r in ledger[since + 1:]], "last_turn": mode})
            if arm == "supervised" and not staying:
                CALLS["turn"] = turn
                n_was = len(ledger)
                rule_missing()   # a checked hypothesis whose ruling could not be read: asked for once more, before the researcher's reply (s053, 2026-11-22)
                if len(ledger) > n_was:   # what it added is in this turn's ledger text (the coherence audit, 2026-11-22: the text was rendered before it)
                    text = render(ledger, readings=True, rethinks=False)
            # the last turn names the hypotheses that still need a verdict: "give your verdicts on the checked hypotheses" was read as "judge every one again"
            # (s030: seventeen second verdicts, each refused)
            st_now, checked_now = states(ledger)
            waiting = sorted((h for h, v in st_now.items() if v == "open" and h in checked_now), key=lambda h: (len(h), h))
            last_ask = "Write the final report (report). The rulings on the tested hypotheses are the supervisor's; none is owed by you." if arm == "supervised" else "Write the final report (report)." if arm == "plain" else ((f"Give a verdict on each hypothesis that is still open and has a checked decision rule ({', '.join(waiting)}), and write the final report (report). " if waiting
                   else "Every hypothesis that has a checked decision rule already has its verdict: write the final report (report). ") + \
                "A hypothesis that already has a verdict is closed: do not judge it again (a second verdict for it is refused).")
            due_before = [f["id"] for f in finding_states(ledger).values() if finding_due(f, ledger, turn)]   # the findings that need a decision in this turn
            shown = {**brief, "how_to_run": HOW_TO_RUN["plain" if arm == "plain" else "other"]} if "how_to_run" in brief else brief
            user = findings_block(ledger, turn, mode) + (f"BRIEF:\n{json.dumps(shown, indent=1)}\n\nSIMULATION BUDGET: " + (f"used up. THIS IS THE LAST TURN: no experiment is accepted{' and budget_request is no longer possible' if asks_budget else ''}. "
                    + last_ask if mode == "budget" else
                    f"closed. THIS IS THE LAST TURN: the last {UNUSABLE} turns gave no usable answer, so the session ends now. Only the final report (report) is accepted in this turn; "
                    "write it from what the ledger holds." if mode == "report" else
                    f"used up: all {budget} simulations have run. Before the last turn, which takes only the final report, you have this turn{f' and {free_left} more' if free_left else ''} "
                    + {"plain": "to look further: requests, and experiments whose simulations have all run already (their results are returned, not run again). ",
                       "supervised": "to look further and to test on the simulations already run: requests, guesses, hypotheses, and tests whose simulations have all run already. ",
                       "hypotheses": "to look further and to test on the simulations already run: requests, guesses and their rethinks, hypotheses, and tests whose simulations have all run already. "}[arm]
                    + ("" if arm == "plain" else "What those simulations gave is known, so a test on them is decided by a measurement you define for it (computed from what they recorded): a rule on their outputs alone cannot fail and is refused. ")
                    + "An experiment that needs a new "
                    f"simulation is not accepted{', and budget_request is no longer possible' if asks_budget else ''}. You may also give the final report now." if mode == "free" else
                    f"{budget - sims} simulations left ({budget} granted so far{f"; budget_request can raise that to at most {limit}, the brief's limit" if asks_budget else ""}). This turn's experiment may run at most {spend_cap(budget - sims, per)} new simulations: never more than half of what is left, so that something remains for what its results raise.")
                    + (f"\n\nLOOK AGAIN FIRST: results have come in for hypotheses of these guesses since you last settled them: {look_again(tested_whys(ledger))}. Before anything new, give a rethink "
                       "for each in this answer (id: the why's own id; now: supported, refuted, verify or set_aside; because of what in those results). No new hypothesis and no experiment "
                       "is accepted until each has its rethink." if arm == "hypotheses" and mode != "report" and tested_whys(ledger) else "")
                    + f"\n\nTOLERANCE: two results that differ by less than {TOLERANCE:g} % count as equal ({'stated by the brief' if tol_given else 'the default of the harness: the brief states none'}). "
                      "A difference inside it is not a finding, and a setting is not better for it."
                    + f"\n\nLEDGER:\n{text}")
            if pending:
                ids = [p for p in pending if p != "limit"]
                user += ("\n\nTOOL RESULTS: your last requests were answered" + (f": {', '.join(ids)}, in the LEDGER above" if ids else "") + ". Every reading stays in the ledger for the rest of the session."
                         + (" The limit of turns with requests only is reached: decide now." if "limit" in pending else ""))
                pending = []
            if staying:   # the same turn goes on (CONTINUES): why, and what ends it
                step_is, step_now = ("an experiment or a report", "state your experiment now") if arm == "plain" else ("a hypothesis, test, drop, verdict or report" if arm == "hypotheses" else "a hypothesis, test, drop or report", "state your hypotheses and their test now")
                user += (f"\n\nTHIS TURN GOES ON (your reply {stay + 1} in this turn, at most {CONTINUES + 1}): your last reply stated no {step_is}, "
                         "and what it asked for is answered in the LEDGER above. A turn ends with a step: " + (f"{step_now}. Requests in this reply are answered "
                         "too, and you are asked once more in this turn." if stay < CONTINUES else f"this is the last reply of this turn, so {step_now} "
                         "(what this reply asks for is answered, and shown to you in the next turn)."))
            last, parsed, err, content, refused = (ledger[-1]["id"] if ledger else None), None, None, "", []
            again = ""   # the second attempt of a turn is told why the first could not be used (it was asked the very same thing before: a refused answer cost a whole reply and taught nothing)
            CALLS["turn"] = turn
            for _attempt in range(2):
                stage("reply", round_no=stay + 1 if staying else None, again=_attempt > 0)
                content, draft, finish_reason, usage = called("researcher", model, system, user + again, schema, a.draft == "on", a.temperature, a.max_tokens)
                count["calls"] += 1
                count["length"] += finish_reason == "length"
                if a.draft == "on":
                    last = append(ledger, turn, "draft", last, {"chars": len(draft), "tokens": usage.get("completion_tokens"), "model": model, "finish_reason": finish_reason})
                    with (tools.SESSION / "drafts.jsonl").open("a") as f:  # the text itself: its own file, one line per draft, by the ledger id
                        f.write(json.dumps({"id": last, "turn": turn, "text": draft}) + "\n")
                if not content.strip() or finish_reason == "length":
                    err, refused = f"empty content or finish_reason={finish_reason}", []
                    continue
                try:
                    parsed = json.loads(content)
                except ValueError as e:
                    err, parsed = f"invalid JSON: {e}", None
                    continue
                if arm == "supervised" and isinstance(parsed, dict):
                    parsed = lean_fill(parsed, brief)
                elif short and isinstance(parsed, dict):
                    parsed = short_fill(parsed, brief)
                received = json.loads(json.dumps(parsed))   # answers.jsonl keeps the answer as before findings (what findings_fill and findings_in_whys add is the harness's)
                if isinstance(parsed, dict):   # findings (2026-11-22): none given is none; a why about a finding is about the records it rests on
                    parsed = findings_in_whys(findings_fill(parsed), ledger)
                if arm == "supervised" and BATCH_FIRST and isinstance(parsed, dict) and mode in (None, "free"):
                    prefetch(parsed, mode)   # one request for the reply's new guesses and tests (stage 4 of the coherence audit, 2026-11-22)
                ok, no = sort_out(parsed, brief, ledger, max(0, budget - sims), mode, insist=not asked, judge=judge, supervised=arm == "supervised", ground=ground_fn if arm == "supervised" else None, short=short, restate=restate_fn if arm == "supervised" and RESTATE_GUESSES else None)
                rq = [] if mode not in (None, "free") else (parsed.get("requests") or [])[:LOOKS if arm == "supervised" else REQUESTS_MOST]   # a free turn may look too (s048, 2026-11-22)   # looking is cheap in the supervised arm: more requests in one turn
                if any(r.startswith(WAIT) for _, r in no):  # said once; the note shows it, and the report is then taken as it comes
                    asked = need_now = True
                if any(ok.values()) or rq or ((parsed.get("findings") or parsed.get("decisions")) and mode not in ("budget", "report")):   # in the last turns only the report is a usable reply (the coherence audit, 2026-11-22)  # something in the answer can be used: it is accepted, without the refused parts
                    err = None
                    break
                again = ("\n\nYOUR ANSWER TO THIS TURN COULD NOT BE USED, AND YOU ARE ASKED ONCE MORE. What the harness refused, and why: " + " | ".join(f"{part}: {why}" for part, why in no)) if no else ""
                err = ("nothing in the answer could be used. " + " | ".join(f"{part}: {why}" for part, why in no)) if no else \
                    "the answer does nothing: no hypothesis, drop, verdict, experiment, report or request"
                refused = [{"part": part, "reason": why} for part, why in no]
                parsed = None
                if need_now:  # no second try with the same text: the model must first see which verdicts are missing
                    break
            if parsed is None:
                append(ledger, turn, "malformed", last, {"error": err, "refused": refused or [{"part": "whole answer", "reason": err}], "content": content[:2000]})
                if mode == "report":  # the last turn that was given for the report alone
                    how = f"{UNUSABLE} turns in a row without a usable answer"
                elif mode == "budget":
                    how = None if need_now else "all simulations used, no usable report"  # after the one request for verdicts: one more last turn
                else:
                    unusable += 1
                    if unusable >= UNUSABLE:  # no ending yet: one last turn follows, which accepts only the final report
                        giving_up = True
                        append(ledger, turn, "note", ledger[-1]["id"], {"text": f"{UNUSABLE} turns in a row gave no usable answer: the harness ends the session after one last turn, in which only the final report is accepted"})
                continue
            unusable = 0
            with (tools.SESSION / "answers.jsonl").open("a") as f:  # the accepted answer as it was received, before any part was refused or cut: what was asked, to compare with what was run. No tool reads it
                f.write(json.dumps({"turn": turn, "answer": received}) + "\n")
            for part, why in no:  # each refused part: a note, shown to the model in the next turn; the rest of the answer was accepted
                append(ledger, turn, "note", last, {"text": f"refused part of the answer: {part}. Reason: {why.rstrip('.')}. The other parts of that answer were accepted.", "part": part, "reason": why})
            for k, g in grounded.items():   # a guess the supervisor did not accept: its reading is a record of its own, so that a person sees on what ground
                if g["refuse"] and k not in ground_written:
                    ground_written.add(k)
                    gid = append(ledger, turn, "review", None, {"for": None, "gate": "ground", "decision": "sent_back", "result": g["result"], "guess": g["guess"], "about": list(k[1]), **{q: g[q] for q in ("records_show", "nearest_earlier", "defect", "because")}})
                    sup_log(gid, "ground", g["saw"], {q: g[q] for q in ("records_show", "nearest_earlier", "defect", "because")})
            br = ok["budget_request"]
            if br:  # granted up to the brief's limit, before this turn's experiment is counted
                granted = max(0, min(br["simulations"], limit - budget))
                budget += granted
                append(ledger, turn, "note", last, {"text": f"budget request: {br['simulations']} more simulations asked, {granted} granted; the budget is now {budget} (the brief's limit is {limit})", "why": br["why"]})
            asked_for = [q for q in parsed.get("requests") or [] if isinstance(q, dict)]
            if len(asked_for) > len(rq):   # what was not answered, and why (the coherence audit, 2026-11-22: they were dropped silently)
                append(ledger, turn, "note", last, {"text": (f"requests are not answered in the last turns: {len(asked_for)} left unanswered" if mode not in (None, "free") else
                                                             f"only the first {len(rq)} requests of a reply are answered: {len(asked_for) - len(rq)} more were left unanswered ({', '.join(str(q.get('tool')) for q in asked_for[len(rq):])})")})
            for q in rq:  # each tool request and what came back are kept in the ledger (request: by the model; result: by the harness);
                out = call(q)  # the result (a reading) stays in the ledger text of every later turn, and the supervisor is given it too
                qid = append(ledger, turn, "request", last, {"tool": q.get("tool"), "args": q.get("args") or {}})
                tid = append(ledger, turn, "result", qid, {"tool": q.get("tool"), "result": out})
                pending.append(tid)
            ex, report = ok["experiment"], ok["report"]
            if not (ok["rethink"] or ok["whys"] or ok["hypotheses"] or ok["drop"] or ok["verdicts"] or ok["objections"] or ex is not None or report is not None or br):  # only requests
                tool_only += not staying   # turns that only look, not replies (the coherence audit, 2026-11-22: a turn's continued replies counted as turns)
                if tool_only > (LOOKS if arm == "supervised" else LOOK_TURNS):
                    pending.append("limit")
                append(ledger, turn, "note", last, {"observations": parsed.get("observations"), "requests": rq}, by="model")
                stay_next = mode in (None, "free") and stay < CONTINUES   # no step yet: the researcher is asked again in this turn, with what it asked for answered
                settle_findings(remap_refs(parsed), ledger, turn, due_before, [r["id"] for r in ledger if r["turn"] == turn and r["type"] == "result"], [], goes_on=stay_next)
                if mode == "report":   # a last turn without the report ends the session, as an unusable one does (the coherence audit, 2026-11-22: the last turn came again without end)
                    how = f"{UNUSABLE} turns in a row without a usable answer"
                elif mode == "budget" and not need_now:
                    how = "all simulations used, no usable report"
                continue
            tool_only = 0
            stay_next = mode in (None, "free") and stay < CONTINUES and not (ok["hypotheses"] or ok["drop"] or ok["verdicts"] or ok["objections"] or ex is not None or report is not None)
            seen = [parsed.get("observations")]  # what the model said it read, kept once: in the first record this turn adds
            obs = lambda: {"observations": seen.pop()} if seen else {}
            for v in ok["verdicts"]:
                append(ledger, turn, "verdict", v["for"], {k: v.get(k) for k in ("for", "result", "because", "next")} | obs())
            for o in ok["objections"]:   # the researcher's objection to one ruling, and the supervisor's second look at it: a new ruling record, which stands
                was = next(r for r in ledger if r["id"] == o["to"])
                oid = append(ledger, turn, "objection", o["to"], {"to": o["to"], "for": was["body"]["for"], "because": o["because"]} | obs())
                try:
                    stage("objection", was["body"]["for"])   # its own step (the coherence audit, 2026-11-22: its call carried the step before it)
                    again, saw = answer_objection(model, brief, ledger, was, o["because"])
                    vid = append(ledger, turn, "verdict", was["body"]["for"], {"for": was["body"]["for"], "result": again["result"], "because": again["because"], "next": was["body"].get("next") or "" if again["stands"] else "",
                                                                             "fair": again["fair"], "defect": was["body"].get("defect", "none") if again["stands"] else "none",
                                                                             "checks": was["body"].get("checks") or [], "after": oid, "stands": again["stands"], "answer": again["answer"]}, by="supervisor")
                    sup_log(vid, "objection", saw, again)
                except (ValueError, KeyError, TypeError) as e:
                    append(ledger, turn, "note", oid, {"text": f"the supervisor's answer to the objection {oid} could not be read ({type(e).__name__}): the ruling {o['to']} stands as it was"})
            for d in ok["drop"]:
                append(ledger, turn, "drop", d["id"], {"for": d["id"], "why": d["why"]} | obs())
            for k, (follows, because) in judged.items():  # what the judge read in this turn, kept for a person (not shown to the model: a refusal reaches it as a note)
                if k not in judge_written:
                    judge_written.add(k)
                    append(ledger, turn, "judge", None, {"guess": k[0], "hypothesis": k[1], "follows": follows, "because": because})
            for k in ok["rethink"]:
                append(ledger, turn, "rethink", k["id"], {"for": k["id"], "in_light_of": k["in_light_of"], "now": k["now"], "because": k["because"]} | obs())
            made_whys = []   # the ids of this reply's guesses (the coherence audit: a continued turn paired them with the turn's first ones)
            for w in ok["whys"]:
                last = append(ledger, turn, "why", last, {k: w[k] for k in ("about", "result", "guess", "unseen", "matters", "worth", "reason")} | ({"revises": w["revises"]} if w.get("revises") else {}) | ({"ground": w["ground"]} if w.get("ground") else {}) | ({"restated": w["restated"]} if w.get("restated") else {}) | ({"contested": w["contested"]} if w.get("contested") else {}) | obs())
                made_whys.append(last)
                if w.get("ground"):   # the supervisor's reading of the records this guess cites
                    k = gkey(w)
                    ground_written.add(k)
                    gid = append(ledger, turn, "review", last, {"for": last, "gate": "ground", "decision": "approved" if w["ground"]["defect"] == "none" or w["ground"].get("warning") else "contested", **w["ground"]})
                    sup_log(gid, "ground", (grounded.get(k) or {}).get("saw", ""), w["ground"])
            for h in ok["hypotheses"]:
                last = append(ledger, turn, "hypothesis", last, {"text": h["text"], "question": h["question"], "why": h["why"], "prediction": h.get("prediction"), "follows_from": h["follows_from"], "from_why": h["from_why"]} | ({"judge": h["judge"]} if h.get("judge") else {}) | obs())
            later = []   # the arm "supervised" (2026-11-22, after the reviews of s047 and s050): the tests sent back in round one, repaired in this same turn
            if ex is not None and arm == "supervised" and ex.get("kind") == "test":
                ex, repairs = design_round_one(ex)
                reserved = sum(1 for q in plan(ledger, ex["runs"]) if not q.get("prior")) if ex is not None else 0   # the new simulations the approved tests will run
                for hid, test, rev, gid, every in repairs:   # every repair round ends before any simulation of this experiment runs, so that each rule is fixed before the results it names
                    ex2 = repair_rounds(hid, test, rev, gid, every, reserved)
                    if ex2 is not None:
                        later.append(ex2)
                        reserved += sum(1 for q in plan(ledger, ex2["runs"]) if not q.get("prior"))   # the next repair is checked against what is left after this one (the coherence audit, 2026-11-22)
            if ex is not None:
                sims += experiment(ledger, turn, (ex.get("tests") or [last])[0], ex | obs())
                if arm == "supervised" and ex.get("kind") == "test":
                    rule_tests(ex)
            for ex2 in later:   # a repaired test that was approved (or contested) runs now, in this turn, as an experiment of its own
                sims += experiment(ledger, turn, ex2["tests"][0], ex2 | obs())
                rule_tests(ex2)
            if ex is not None:
                if arm == "supervised" and ex.get("kind") != "test":   # results with no ruling (an explore experiment): the supervisor looks at them for findings (2026-11-22)
                    xid = next(r["id"] for r in reversed(ledger) if r["type"] == "experiment")
                    try:
                        stage("look", xid)
                        items, saw = sup_findings_of(model, brief, ledger, xid)
                        take_sup_findings(ledger, turn, items, xid)
                        sup_log(xid, "findings", saw, {"findings": items})
                    except (ValueError, KeyError, TypeError) as e:
                        append(ledger, turn, "note", xid, {"text": f"the supervisor's look at {xid} could not be read ({type(e).__name__}): no finding of its own"})
            # findings and decisions (2026-11-22): after every other record of this answer, so that a decision can name what this answer made
            made = [r["id"] for r in ledger if r["turn"] == turn and (r["type"] == "result" or (r["type"] == "experiment" and r.get("by") == "model"))]
            whys_made = [(rid, w.get("_findings") or []) for rid, w in zip(made_whys, ok["whys"])]
            settle_findings(remap_refs(parsed), ledger, turn, due_before, made, [x for x in whys_made if x[1]], goes_on=stay_next)
            if report is not None and (ran_now := [r["id"] for r in ledger if r["turn"] == turn and r["type"] == "experiment" and r.get("by") != "harness"]):   # the coherence audit, 2026-11-22: a report with an experiment was taken before its results
                _note(ledger, turn, "report", f"the report is held back: this answer's experiment ({', '.join(ran_now)}) ran in this turn, and its results and checks come to you in the next turn. Give the report after you have read them")
                report = None
            if report is not None and mode in (None, "free") and len(held_turns - {turn}) < FINDING_HOLDS and (unseen := findings_unseen(ledger)):
                held_turns.add(turn)   # the researcher can still work: a finding never looked at is worked on, not left (the operator, 2026-11-22)
                _note(ledger, turn, "report", f"the report is held back: these findings were never looked at (no reading, check or evidence reaches them): {', '.join(unseen)}. "
                      "Look at each first (a reading, a measurement on simulations already run, or a test), or close it with the records that explain it; then give the report")
                report = None
            if report is not None:   # every finding not closed stands in open_questions by its id
                report, added = findings_in_report(report, ledger)
                if added:
                    _note(ledger, turn, "report", f"open_questions did not name {', '.join(added)}: the harness added them there, as not resolved", refused=False)
            if report is None and seen and seen[0]:   # an answer none of whose parts made a record (each was refused): its observations are kept all the same
                append(ledger, turn, "note", last, {"observations": seen.pop()}, by="model")
            if report is not None:  # accepted (sort_out): the ledger, report.json, and the session is over
                append(ledger, turn, "report", last, report | obs())
                (tools.SESSION / "report.json").write_text(json.dumps(report, indent=1) + "\n")
                how = "done by the model" if mode in (None, "free") else "all simulations used, report given in the last turn" if mode == "budget" else f"{UNUSABLE} turns in a row without a usable answer, report given in the last turn"
            elif mode == "report":
                how = f"{UNUSABLE} turns in a row without a usable answer"
            elif mode == "budget" and not need_now:  # a last turn without a usable report (after the one request for verdicts there is one more)
                how = "all simulations used, no usable report"
    except ModelServerError as e:  # the session ends cleanly: the error is in the ledger, and session.json says how it ended
        append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"model server error: {e}"})
        how = "model server error"
    except Exception as e:   # a fault of the harness itself (s052, 2026-11-22: it was recorded as "stopped from outside"): the ledger and session.json say so
        try:
            append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"harness error: {type(e).__name__}: {' '.join(str(e).split())[:300]}"})
        except Exception:
            pass
        how = f"harness error: {type(e).__name__}"
        raise
    finally:
        try:
            if any(r["type"] == "finding" for r in ledger):   # for each finding: how it ended and what looked at it (2026-11-22)
                findings_end(ledger, turn)
        except Exception as e:   # the session's end is recorded whatever happens here
            print(f"findings at the end could not be recorded: {type(e).__name__}: {e}", flush=True)
        finish()
    print(f"stopped: session {SID}, {how or 'stopped from outside'}, {sims} simulations, {turn} turns, ledger {LEDGER}")

if __name__ == "__main__":
    main()
