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
import argparse, json, re, signal, sys, time
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
          "malformed": "M", "note": "N", "draft": "D", "request": "Q", "result": "T", "turn": "U", "review": "G", "objection": "O"}
# who produced the content of a record, written into it as "by": the model (what it wrote), the simulator (what was
# measured), the harness (what it computed, found or decided itself), the operator (the person; no record type is theirs yet)
SOURCES = ("model", "harness", "simulator", "operator", "supervisor")   # supervisor: the second agent of the arm "supervised" (its reviews, and there the verdicts)
BY = {"draft": "model", "why": "model", "rethink": "model", "judge": "harness", "hypothesis": "model", "drop": "model", "experiment": "model", "verdict": "model", "report": "model",
      "simulation": "simulator", "evidence": "harness", "check": "harness", "malformed": "harness", "note": "harness", "request": "model", "result": "harness", "turn": "harness", "review": "supervisor", "objection": "model"}
HIDDEN = ("draft", "scratch", "simulation", "request", "result", "turn", "judge")  # kept on disk, not replayed: what the model wrote before its answer, and the
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


def structure_problem(edits, brief=None):
    """None if the brief's network with these changes may be simulated; otherwise why not."""
    b = brief or tools.describe_system()
    if not edits:
        return None
    try:
        t1 = network.apply(b["topology"], edits)
    except (ValueError, KeyError, TypeError) as e:
        return str(e)
    bad = network.problems(t1) + network.changed_problems(b["topology"], t1, b.get("structure") or {}, b.get("goal") or {}, aim_measures(b))
    return "; ".join(bad) or None


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
    series, fine = network.record_columns(brief["topology"]) if brief.get("topology") else TWO_HOSTS_COLUMNS
    outs, seen = tools.outputs(brief), set()
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
        if not used or not (used <= set(series) or used <= set(fine)):
            return (f"measurement {n}: of must be a column a simulation records, or arithmetic over columns of one record. The series (every 0.1 s): {', '.join(series)}. "
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
    results = dict(zip((r["label"] for r in fresh), tools.run_many([r["params"] for r in fresh], [r["structure"] for r in fresh], probe=tools.PROBE_EVERY if own else None)))
    def measured(run_id):
        """The experiment's own measurements of one simulation: {name: value}. A simulation that ran earlier has no finer record yet: the harness
        runs it again with the probe, and uses that record only if the result is the same."""
        out = {}
        if own and "probe.csv" not in [p.name for p in tools._dir(run_id).iterdir()]:
            said = tools.probe(run_id)
            if said.startswith("error"):
                return {}
        for m in own:
            said = tools.measure(run_id, m["of"], m["stat"], m.get("t_from"), m.get("t_to"), m.get("level"), **({"with": m["with"]} if m.get("with") else {}))
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
                mine = measured(body["run_id"])
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
    labels = [r["label"] for r in runs]
    for d in stated:
        try:
            held, numbers = decision_rules.check(d["decision_rule"], {**tools.outputs(), **{k: "" for v in values.values() for k in v}}, labels, values)   # a changed network's own measures count too
            result = "held" if held else "failed"
            close = decided_by_little(d["decision_rule"], labels, values, ledger)
        except decision_rules.DecisionRuleError as e:  # it was readable (validate), so: a simulation it names gave no value
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
                + (f" | not visible: {flat(b['unseen'])}" if b.get("unseen") else "") + (f" | for the goal: {flat(b['matters'])}" if b.get("matters") else "") + (f" | {flat(b['reason'])}" if b.get("reason") else ""))
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
        return (f"by the supervisor of the guess {b['for']}, before anything is built on it: " + ("sound: it starts from what the records show" if b["defect"] == "none" else f"accepted on its second statement, but the supervisor still objects ({GROUNDS.get(b['defect'], b['defect'])})")
                + f". The records show: {flat(b['records_show'])} {flat(b['because'])}" + (f" The nearest earlier guess: {flat(b['nearest_earlier'])}" if b.get("nearest_earlier") else ""))
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

def render(ledger, readings=True):
    """The ledger as text for the prompt: one line per record, and in an evidence record one line per simulation. Every reading (what a tool returned)
    stays in it in full, in its place, with its id, so that the researcher keeps all it found and a later guess can name the reading it starts from.
    The researcher's own observations of each turn stand in it too, in their place, as "turn N your observations: ..." (2026-11-22, the operator:
    "I want the researcher to see all lookup results and its own observations previously accumulated all the time"): until then a turn's
    observations were kept in its first record but shown only for a turn of requests only. The supervisor is never given them.
    readings: no longer used (every arm keeps the readings since 2026-11-22)."""
    st = dict(states(ledger)[0])
    for y, w in why_states(ledger).items():   # a why with its standing now, and whether results have come in since it was last settled
        st[y] = {**w, "stale": since(ledger, w["at"]) if w["worth"] == "verify" else [], "idle": w["worth"] == "verify" and not any(r["type"] == "hypothesis" and r["body"].get("from_why") == y for r in ledger)}
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
        r = post(API + "/chat/completions", body, 1800)
    except ModelServerError as e:  # a model server that cannot limit the draft says so: asked once more without the limit, and not asked for it again
        if "thinking_token_budget" not in body or "thinking_token_budget" not in str(e):
            raise
        THINK["limit"] = False
        del body["thinking_token_budget"]
        r = post(API + "/chat/completions", body, 1800)
    ch = r["choices"][0]
    return ch["message"].get("content") or "", ch["message"].get("reasoning") or "", ch.get("finish_reason"), r.get("usage", {})

# ---- every call of the model, as it was made (2026-11-22, the operator: a page of their own to see what the agents are shown and what they write):
# sessions/<id>/calls.jsonl, one line per call: which agent (researcher, judge, supervisor), the two messages it was given, what it wrote before its
# answer, its answer, the counts of tokens, why it stopped and how long it took. No tool and no model reads it; the server gives it only to the
# page of the account that runs it (control.py, /api/agents). The calls go through here, so a scripted session (harness_checks) writes it too.
CALLS = {"n": 0, "turn": 0}
def called(agent, model, system, user, schema, draft, temperature, max_tokens):
    t0 = time.time()
    content, reasoning, finish_reason, usage = ask(model, system, user, schema, draft, temperature, max_tokens)
    CALLS["n"] += 1
    try:
        with (tools.SESSION / "calls.jsonl").open("a") as f:
            f.write(json.dumps({"n": CALLS["n"], "turn": CALLS["turn"], "agent": agent, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "seconds": round(time.time() - t0, 1),
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
REVIEW_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["rival", "rival_outcome", "doubt_if", "because", "defect"], "properties": {
    "rival": {"type": "string", "description": "the strongest other explanation of the result the guess is about, in one sentence: not the researcher's guess"},
    "rival_outcome": {"type": "string", "enum": ["held", "failed", "cannot tell"], "description": "what the decision rule would do if your rival were true and the guess false"},
    "doubt_if": {"type": "string", "description": "written before anything is measured: what in the results would make you doubt this test even if its rule comes out as the researcher predicts"},
    "because": {"type": "string", "description": "your reasoning to the decision, with the numbers or record ids it rests on: written before you name the defect"},
    "defect": {"type": "string", "enum": list(DEFECTS), "description": "the one defect your reasoning ends in, or none"}}}
RULING_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["shows", "because", "fair", "defect", "result", "retest"], "properties": {
    "shows": {"type": "string", "description": "what the measured numbers show, in one sentence, before any conclusion"},
    "because": {"type": "string", "description": "your reasoning from the numbers to the ruling: written before you rule"},
    "fair": {"type": "boolean", "description": "whether this was a fair test of the hypothesis: one that could have come out the other way if the hypothesis were false"},
    "defect": {"type": "string", "enum": list(DEFECTS), "description": "none when the test was fair"},
    "result": {"type": "string", "enum": ["supported", "refuted", "inconclusive"]},
    "retest": {"type": "string", "description": "when the result is inconclusive: what a fair test would have to compare; else empty"}}}
GROUNDS = {"none": "no defect",
           "not_in_the_records": "the result the guess starts from is not what the cited records show",
           "repeats": "the guess says again, in other words, what an earlier guess or hypothesis already said, and that one has its ruling",
           "ignores_a_ruling": "the guess goes on as if a ruling against it had not been given: it does not say what is different now",
           "not_from_what_was_learned": "the guess does not come from the newer records it cites: it would be the same guess without them"}
GROUND_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["records_show", "nearest_earlier", "because", "defect"], "properties": {
    "records_show": {"type": "string", "description": "what the cited records show about the result the guess starts from, with the numbers"},
    "nearest_earlier": {"type": "string", "description": "the id of the earlier guess or hypothesis that is nearest to this one in what it claims (for example Y2 or H3), or none"},
    "because": {"type": "string", "description": "your reasoning to the decision: written before you name the defect"}, "defect": {"type": "string", "enum": list(GROUNDS), "description": "the one defect your reasoning ends in, or none"}}}
APPEAL_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answer", "stands", "result", "because"], "properties": {
    "answer": {"type": "string", "description": "what in the records the objection gets right or wrong"}, "stands": {"type": "boolean", "description": "true: your ruling stands as it was"},
    "result": {"type": "string", "enum": ["supported", "refuted", "inconclusive"]}, "because": {"type": "string"}}}
LOOKS = 6   # the arm "supervised": the most requests in one turn, and the most turns in a row that only look (the operator, 2026-11-18: observe the system whenever it wants, rather than try many simulations)
SUPERVISOR_FILE = "supervisor.jsonl"   # beside the ledger: for each record of the supervisor, what it was shown and what it answered


def supervise(model, user, schema):
    """One request to the supervisor: its own instructions, a request of its own (nothing of the researcher's conversation), temperature 0. The model
    reasons before it answers, as the researcher does; that reasoning is not kept (its answer says its ground)."""
    return json.loads(called("supervisor", model, SUPERVISOR, user, schema, True, 0, 9000)[0])


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


def _case(ledger, hid, rules):
    """One hypothesis as the supervisor is shown it: the result its guess is about, the guess, the hypothesis, its decision rules. Not the researcher's reasons."""
    flat = lambda v: " ".join(str(v).split())
    h = next(r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid)
    w = next((r["body"] for r in ledger if r["type"] == "why" and r["id"] == h.get("from_why")), None)
    return ((f"THE RESULT the guess is about: {flat(w['result'])}\nTHE GUESS of why it came out so: {flat(w['guess'])}\n" + (f"What would make it so, not directly visible: {flat(w['unseen'])}\n" if w.get("unseen") else "") if w else "")
            + f"THE HYPOTHESIS {hid}: {flat(h['text'])}\n" + "".join(f"DECISION RULE: {flat(d['decision_rule'])}\n" for d in rules))


def review_design(model, brief, ledger, ex, hid, ask_fn=None):
    """Gate 1. The supervisor's reading of the test of one hypothesis, before any of its simulations is run: (review, what it was shown).
    review = {rival, rival_outcome, doubt_if, defect, because}. Its own rival decides with it: a rival under which the rule would hold as well is the
    defect rival_passes_too, whatever it called the defect."""
    flat = lambda v: " ".join(str(v).split())
    rules = [d for d in ex.get("decision_rules") or [] if d.get("for") == hid]
    need = next((n for n in ex.get("needs") or [] if n.get("for") == hid), {})
    planned = plan(ledger, [r for r in ex["runs"] if r["label"] in (need.get("simulations") or [r["label"] for r in ex["runs"]])])
    sims = "\n".join(f"  {r['label']} {{{', '.join(f'{k}={v}' for k, v in r['params'].items())}}}" + (f"  (already run as {r['prior']['id']}: its result is in the table above and will be returned, not run again)" if r["prior"] else "  (new)") for r in planned)
    user = (_system_for_supervisor(brief) + f"\nWHAT HAS BEEN MEASURED SO FAR:\n{_measured(ledger)}\n\nEVERY READING OF THE SESSION, as the researcher's ledger holds them (what the tools returned when the researcher looked: measurements too):\n{_looked(ledger)}\n\n" + _case(ledger, hid, rules)
            + "".join(f"A MEASUREMENT THE RESEARCHER DEFINES FOR THIS TEST: {m['name']} = {m['stat']} of {m['of']}" + (f" against the level {m['level']}" if m.get("level") is not None else "") + f", from {m.get('t_from') if m.get('t_from') is not None else 2} s to {m.get('t_to') if m.get('t_to') is not None else 'the end'} (computed by the harness from what each simulation records; the probe only listens)\n" for m in ex.get("measurements") or [])
            + (f"What the researcher says it must know to decide it: {flat(need['to_know'])}\n" if need.get("to_know") else "") + f"Between the simulations its rule compares, the one setting that differs: {need.get('varies') or 'not stated'}; the measure the rule is about: {need.get('measure') or 'not stated'}\n"
            + f"THE SIMULATIONS PLANNED FOR IT:\n{sims}\n\n"
            "Before any of these simulations is run: can this test tell whether the guess is true? First name the strongest rival explanation you can think of and say what the decision rule would do "
            "under it. Then say what would make you doubt the test even if it comes out as predicted. Then name the defect, or none. The defects: "
            + "; ".join(f"{k}: {v}" for k, v in DEFECTS.items()) + ". A test is not defective for being small or for testing only one consequence of the guess.")
    d = (ask_fn or supervise)(model, user, REVIEW_SCHEMA)
    rev = {"rival": flat(d["rival"]), "rival_outcome": d["rival_outcome"], "doubt_if": flat(d["doubt_if"]), "defect": d["defect"] if d["defect"] in DEFECTS else "none", "because": flat(d["because"])}
    if rev["defect"] == "none" and rev["rival_outcome"] == "held":   # its own rival would pass the rule: by its own words the test cannot tell the two apart
        rev["defect"] = "rival_passes_too"
    elif rev["defect"] == "rival_passes_too" and rev["rival_outcome"] != "held":   # it names that defect, but says its own rival would not pass the rule (s044: G14, G15): the defect does not stand
        rev["defect"], rev["because"] = "none", rev["because"] + f" [the harness: it named “a rival passes too”, but under its own rival the rule would {'fail' if rev['rival_outcome'] == 'failed' else 'come out in a way it could not tell'}; no defect stands]"
    return rev, user


def ground_of(model, brief, ledger, why, ask_fn=None):
    """Gate 0. The supervisor's reading of one new guess before anything is built on it: is the result it starts from what the records it cites show,
    and is it more than an earlier guess or hypothesis said again? (ground, what it was shown). ground = {records_show, nearest_earlier, defect, because}.
    The supervisor is shown the cited records as the ledger holds them, the session's guesses and hypotheses with their rulings, and of the new guess
    its three statements (the result, the guess, what would make it so): not why the researcher thinks it worth verifying."""
    flat = lambda v: " ".join(str(v).split())
    st = states(ledger)[0]
    cited = [r for r in ledger if r["id"] in why["about"]]
    def record(r):
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
            return f"[{r['id']}] the supervisor's review of {b.get('for') or 'a guess'}: {b.get('decision')}. {flat(b.get('because'))}" + (f" The rival it named: {flat(b['rival'])}" if b.get("rival") else "")
        return f"[{r['id']}] ruling on {b['for']}: {b['result']}. {flat(b['because'])}"
    new = learned_since(ledger)
    mark = lambda r: record(r) + ("   <- NEW since the researcher's earlier guesses" if new is not None and r["id"] in new else "")
    earlier = "\n".join([f"  [{r['id']}] guess: {flat(r['body']['guess'])}" for r in ledger if r["type"] == "why"]
                        + [f"  [{r['id']}] hypothesis ({st.get(r['id'], 'open')}): {flat(r['body']['text'])}" for r in ledger if r["type"] == "hypothesis"]) or "  (none yet)"
    rulings = "\n".join(f"  [{r['id']}] on {r['body']['for']}: {r['body']['result']}. {flat(r['body']['because'])}" for r in ledger if r["type"] == "verdict") or "  (none yet)"
    runs = {r["body"].get("run_id") for r in cited if r["type"] == "simulation"} | {q["body"].get("run_id") for r in cited if r["type"] == "evidence" for q in ledger if q["type"] == "simulation" and q.get("parent") == r["body"]["experiment"]}
    user = (_system_for_supervisor(brief) + "\nTHE RECORDS THE NEW GUESS CITES:\n" + ("\n".join(mark(r) for r in cited) or "  (it cites the brief only: nothing has been measured for it)")
            + "\n\nEVERY READING OF THE SESSION, as the researcher's ledger holds them (the researcher asked; the harness read it from what the simulations recorded over time: these are measurements too, and a guess may start from them):\n" + _looked(ledger)
            + f"\n\nTHE NEW GUESS\nThe result it starts from, as the researcher states it: {flat(why['result'])}\nThe guess of why: {flat(why['guess'])}\n" + (f"What would make it so, not directly visible: {flat(why['unseen'])}\n" if why.get("unseen") else "") + "\n"
            f"THE SESSION'S EARLIER GUESSES AND HYPOTHESES:\n{earlier}\n\nTHE RULINGS SO FAR:\n{rulings}\n\n"
            "Before anything is built on this guess: first say what the cited records show about the result it starts from. Then name the earlier guess or hypothesis nearest to it. Then name the defect, or none. "
            "The defects: " + "; ".join(f"{k}: {v}" for k, v in GROUNDS.items()) + ". A guess may be wrong and still be sound here: you judge whether it starts from what was measured and adds something, "
            "not whether it is true. A guess that takes up an earlier one with a stated difference (another cause, another range, a reason why the earlier test was not fair) is not a repetition."
            + ("" if new is None else " This is not the researcher's first guess, and a later guess has to be the fruit of what was learned since the earlier ones. The records marked NEW are what it says it "
               "learned from. Say in your reasoning what they show that the earlier guesses did not have, and ask: would the researcher have made this same guess without them? If yes, the citation is "
               "for form only and the defect is not_from_what_was_learned."))
    d = (ask_fn or supervise)(model, user, GROUND_SCHEMA)
    return {"records_show": flat(d["records_show"]), "nearest_earlier": flat(d["nearest_earlier"]), "defect": d["defect"] if d["defect"] in GROUNDS else "none", "because": flat(d["because"])}, user


def rule_on(model, brief, ledger, xid, hid, doubt_if, ask_fn=None):
    """Gate 2. The supervisor's ruling on one tested hypothesis after the harness has checked its rules: (ruling, what it was shown).
    ruling = {shows, fair, defect, result, because, retest, checks}. The checks are facts: supported needs every check HELD, refuted needs one that
    FAILED, and either needs a fair test; a ruling that does not fit is recorded as inconclusive, and the record says that the harness changed it."""
    flat = lambda v: " ".join(str(v).split())
    checks = [r for r in ledger if r["type"] == "check" and r["body"]["experiment"] == xid and r["body"]["for"] == hid]
    rules = [{"decision_rule": c["body"]["decision_rule"]} for c in checks]
    lines = "\n".join(f"  [{c['id']}] {flat(c['body']['decision_rule'])}  ->  {c['body']['with_numbers']}  :  {c['body']['result'].upper()}"
                       + "".join(f"  (note: {q['left']} against {q['right']} differ by {q['percent']:.3g} %)" for q in c["body"].get("within_tolerance") or []) for c in checks)
    user = (_system_for_supervisor(brief) + "\n" + _case(ledger, hid, rules) + f"\nTHE SIMULATIONS OF THIS TEST, as measured:\n{_measured(ledger, xid)}\n\nTHE BASELINE and what was measured before:\n{_measured([r for r in ledger if not (r['type'] == 'evidence' and r['body']['experiment'] == xid)])}\n\n"
            f"EVERY READING OF THE SESSION, as the researcher's ledger holds them (what the tools returned when the researcher looked: measurements too):\n{_looked(ledger)}\n\nTHE HARNESS'S CHECKS (facts):\n{lines}\n\n" + (f"Before the simulations you wrote what would make you doubt this test: {doubt_if}\n\n" if doubt_if else "")
            + "What does this test show about the hypothesis? supported: every check HELD and the test was a fair one. refuted: a check FAILED and the test was a fair one. inconclusive: the test "
              "was not fair (name the defect and what a fair test would compare), or the checks disagree. A check that failed because another setting limited the result, or one that held "
              "although it would have held under a rival explanation too, is not a fair test. The defects: " + "; ".join(f"{k}: {v}" for k, v in DEFECTS.items()) + ".")
    d = (ask_fn or supervise)(model, user, RULING_SCHEMA)
    res = [c["body"]["result"] for c in checks]
    fits = {"supported": all(x == "held" for x in res) and d["fair"], "refuted": any(x == "failed" for x in res) and d["fair"], "inconclusive": True}.get(d["result"], False)
    ruling = {"shows": flat(d["shows"]), "fair": bool(d["fair"]), "defect": d["defect"] if d["defect"] in DEFECTS else "none", "result": d["result"] if fits else "inconclusive", "because": flat(d["because"]),
              "retest": flat(d.get("retest") or ""), "checks": [c["id"] for c in checks], **({} if fits else {"changed_by_harness": f"the supervisor said {d['result']}, which does not fit the checks ({', '.join(res)}) or its own finding that the test was {'fair' if d['fair'] else 'not fair'}"})}
    return ruling, user


def answer_objection(model, brief, ledger, verdict, objection, ask_fn=None):
    """The supervisor's second look at one of its rulings, after the researcher's objection: ({stands, result, because, answer}, what it was shown)."""
    flat = lambda v: " ".join(str(v).split())
    b, hid = verdict["body"], verdict["body"]["for"]
    checks = [r for r in ledger if r["id"] in (b.get("checks") or [])]
    xid = checks[0]["body"]["experiment"] if checks else None
    lines = "\n".join(f"  [{c['id']}] {flat(c['body']['decision_rule'])}  ->  {c['body']['with_numbers']}  :  {c['body']['result'].upper()}" for c in checks)
    user = (_system_for_supervisor(brief) + "\n" + _case(ledger, hid, [{"decision_rule": c["body"]["decision_rule"]} for c in checks]) + f"\nTHE SIMULATIONS OF THE TEST, as measured:\n{_measured(ledger, xid)}\n\nEVERYTHING MEASURED IN THE SESSION:\n{_measured(ledger)}\n\n"
            f"THE HARNESS'S CHECKS (facts):\n{lines}\n\nYOUR RULING [{verdict['id']}]: {b['result']}. {b['because']}" + (f" Defect: {DEFECTS.get(b.get('defect'), '')}." if not b.get("fair", True) else "")
            + f"\n\nTHE RESEARCHER OBJECTS: {flat(objection)}\n\nLook at the records again. An objection is right only for what the records show, not for how sure it sounds. Does your ruling stand? "
              "supported needs every check HELD, refuted needs a check that FAILED; otherwise inconclusive.")
    d = (ask_fn or supervise)(model, user, APPEAL_SCHEMA)
    res = [c["body"]["result"] for c in checks]
    result = b["result"] if d["stands"] else d["result"]
    if (result == "supported" and not all(x == "held" for x in res)) or (result == "refuted" and not any(x == "failed" for x in res)):
        result = "inconclusive"
    return {"stands": result == b["result"], "result": result, "because": flat(d["because"]), "answer": flat(d["answer"])}, user


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
    if len(set(labels)) != len(labels) or not all(re.fullmatch(r"[A-Za-z0-9_]{1,20}", str(l)) for l in labels):
        return "every simulation needs its own label: letters, digits and _ only, at most 20 characters"
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
            if lean:   # the short reply states no rival: the supervisor names its own before the simulations
                continue
            if not text(r.get("rival")) or r.get("rival_predicts") not in ("held", "failed"):
                return f"the decision rule for {r['for']} needs a rival (a competing explanation of how the system behaves) and rival_predicts (held or failed)"
            if r["rival_predicts"] == "held":
                return "this decision rule would hold under the rival too; choose simulations where the two explanations give different results"
        why = needs_problem(ex, brief, planned, full=left is not None)
        if why:
            return why
    elif ex.get("kind") == "explore":
        if not text(ex.get("question")) or tests or rs or ex.get("needs"):
            return "an explore experiment needs a question, and has no tests, no needs and no decision rules"
    else:
        return "experiment.kind must be test or explore"
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

def sort_out(t, brief, ledger, left, mode=None, insist=True, judge=None, supervised=False, ground=None, short=False):
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
        elif d.get("id") in checked and st.get(d["id"]) == "open":
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
    for w in t.get("whys") or []:
        if isinstance(w, dict) and isinstance(w.get("about"), list):
            w["about"] = list(dict.fromkeys(of_run(a) for a in w["about"]))
        about = w.get("about") if isinstance(w, dict) else None
        if mode == "report":
            no.append(("new why", only))
        elif not isinstance(w, dict) or not all(text(w.get(k)) for k in (("result", "guess") if supervised else ("result", "guess", "unseen", "matters") if short else ("result", "guess", "unseen", "matters", "reason"))):
            no.append(("new why", "a why needs result (the result it is about, in one sentence), guess (why it came out so), unseen (what in the system, not directly visible, would make it so), "
                                  + ("and matters (how it could matter for the goal)" if short else "matters (how it could matter for the goal) and reason (why it is or is not worth verifying now)")))
        elif w.get("worth") not in ("verify", "set_aside"):
            no.append(("new why", "a why says whether it is worth verifying now: worth is verify or set_aside"))
        elif not isinstance(about, list) or not about or any(a != "brief" and kinds.get(a) not in ("evidence", "simulation", "check", "verdict", "result") + (("review",) if supervised else ()) for a in about):
            bad = [a for a in about or [] if a != "brief" and a not in kinds] if isinstance(about, list) else []
            no.append(("new why", (f"about names ids that are not in the ledger: {', '.join(map(str, bad))}" if bad else
                                   "about must list the records whose result the why explains: ids of evidence tables, simulations, checks, verdicts or readings in the ledger (for example E2, C3, T7), "
                                   "a run id for what you read in that run's series or trace (for example r001), or the word brief")))
        elif supervised and (new_since := learned_since(ledger)) is not None and not any(a in new_since for a in about):
            # the chain: a later guess is the fruit of what was learned since the earlier ones (s047: five guesses in four turns, each from the baseline again)
            no.append(("new why", "this guess starts only from records your earlier guesses already had (" + ", ".join(map(str, about)) + "). A later guess must come from something learned since: "
                                  "a ruling, a check, a new result table, a reading a tool returned, or a review in which the supervisor objected. Name its id in about (for example V2, C3, E2, T7, G4) and say in "
                                  "result what it showed" + (f"; made since your last guess: {', '.join(sorted(new_since, key=lambda i: (i[0], int(i[1:]))))}" if new_since else
                                  "; nothing has been learned since your last guess: test what is open, or look with a request, before you guess again")))
        elif w.get("revises") is not None and (w["revises"] not in ws or stand[w["revises"]] == "revised"):
            no.append(("new why", "revises is null, or the id of an earlier why in the ledger that this one replaces with a better guess (one that has not been revised already)"))
        elif ground is not None and (g := ground(w)) and g["refuse"]:
            # gate 0 (the arm "supervised"): the supervisor read the records the guess cites. A guess that does not start from what they show, or that only
            # says an earlier one again, is refused once; stated again it is accepted, and its review says that the supervisor still objects
            no.append(("new why", f"the supervisor does not accept this guess as it stands: {GROUNDS[g['defect']]}. The records show: {g['records_show']} {g['because']} "
                                  "State what the cited records show, and what in them is new, or leave the guess. No hypothesis can come from a guess that was not accepted"))
        else:
            if ground is not None:
                w = {**w, "ground": {k: g[k] for k in ("records_show", "nearest_earlier", "defect", "because")}}   # kept with the guess: what the supervisor read in the records
            ok["whys"].append(w)
            new = f"Y{n_why + len(ok['whys'])}"   # the id it is about to get
            whys[new], stand[new] = w, w["worth"]
            fresh.add(new)
            if w.get("revises"):
                stand[w["revises"]], revised_as[w["revises"]] = "revised", new
    for h in t.get("hypotheses") or []:
        if isinstance(h, dict) and isinstance(h.get("follows_from"), list):   # a run id stands for that run's simulation, as in a why's about (s043: three hypotheses refused for "r001")
            h["follows_from"] = list(dict.fromkeys(of_run(a) for a in h["follows_from"]))
        if isinstance(h, dict) and not h.get("follows_from") and whys.get(h.get("from_why")):
            h["follows_from"] = list(whys[h["from_why"]]["about"])   # what the hypothesis follows from: what its why is about
        if mode == "report":
            no.append(("new hypothesis", only))
        elif supervised and (waiting := [i for i, v in states(ledger)[0].items() if v == "open" and i not in {d["id"] for d in ok["drop"]}]):
            # the chain is result, guess, hypothesis, test: a hypothesis is stated to be tested, and the next one comes from what its test showed (s047: eight stated, none tested)
            no.append(("new hypothesis", f"{', '.join(waiting)} {'is' if len(waiting) == 1 else 'are'} still open and untested: test {'it' if len(waiting) == 1 else 'them'} (send the experiment), or give "
                                         f"{'it' if len(waiting) == 1 else 'them'} up in drop with what you learned, before you state another hypothesis. The next hypothesis comes from what a test showed"))
        elif supervised and len(ok["hypotheses"]) >= OPEN_MOST:
            no.append(("new hypothesis", f"at most {OPEN_MOST} new hypotheses in one answer: state the ones you will test now"))
        elif stand.get(h.get("from_why")) != "verify":
            y = h.get("from_why")
            no.append(("new hypothesis", "a hypothesis comes from a why you chose to verify: from_why must be the id of a why whose worth is verify, one in the ledger or one of this answer "
                                         f"(the harness numbers new whys in order: the first new one is Y{n_why + 1})"
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
                    hid = f"H{known + len(ok['hypotheses']) + 1}"   # the id it is about to get: its test's rule in this answer stands for a prediction the short format does not ask
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
    ex = t.get("experiment")
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
                ex = {**ex, "runs": [r for r in ex["runs"] if r.get("label") not in idle]}
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

You do not work alone. A supervisor works apart from you. It proposes nothing and never sees your notes or your reasons; it is shown your guess, your hypothesis, your decision rule, the planned simulations, the measured numbers and what the tools returned. It checks each step:
- a new guess: does it start from what the records show, and is it more than an earlier guess said again? A guess it does not accept is refused once, with its reason;
- a test, before any simulation is run: can it tell whether the guess is true? A test with a defect is sent back once, and it is not run or counted; the other tests of the same experiment are run. Sent again, it is run;
- after the harness has checked your rule: what the check means. Its ruling (supported, refuted, or inconclusive because the test was not a fair one) closes the hypothesis. You do not give verdicts.

The ledger is the complete record of the session. You have no other memory. Each turn you read it and answer with ONE JSON object. Keep every text short: one or two sentences. Its parts:

1. observations: one or two sentences: the most important thing the results do not yet explain. They stay in the ledger (turn N your observations).
2. requests: look before you simulate. Looking costs no simulation. metrics, series and measure read what a simulation you already ran recorded (measure: a statistic of a quantity you combine from them, e.g. tcp_inflight / min(tcp_cwnd, tcp_rwnd); corr and lag: do two move together, which leads); probe makes a finer record of such a simulation (TCP's round-trip time, the receiver's window, the bytes in flight, the time packets wait in each queue) by running it again with taps that only listen. Up to six requests in a turn; the results come back in the next turn and stay in the ledger with their ids (T1, T2, ...). A turn may consist of requests only.
3. whys: your guesses of why a result came out so. Each has about (the ids of the records it starts from: evidence tables, simulations, checks or rulings, for example E0, S2, C1; a reading a tool returned, by its id, for example T7; a review in which the supervisor objected, for example G4; the word brief only when nothing is measured yet), result (that result in one sentence, with its numbers), guess (what in the system would make it so), and revises (the id of an earlier guess this one replaces, or null). The harness numbers them Y1, Y2, ... The work is a chain: your first guesses start from the baseline, and every later guess is the fruit of what you learned since: its about must name at least one record made since your last guesses (a ruling, a check, a new result table, a reading, an objection of the supervisor), and its result says what that record showed. A later guess that starts from the baseline alone is refused, and the supervisor reads whether the guess really comes from the newer record or only names it. Make your several first guesses in one answer.
4. hypotheses: a hypothesis is a measurable consequence of one guess: from_why (the guess's id, one in the ledger or one of this answer) and text (one sentence that a measurement can show to be false). The harness numbers them H1, H2, ... A hypothesis is stated to be tested: state at most three in one answer, with the experiment that tests them, and while one is still open and untested no further hypothesis is accepted. Test what is open, or give it up in drop saying what you learned; the next hypothesis comes from what a test showed. A value you can simply read is an observation, not a hypothesis: ask for it in requests (measure, probe) and say it in a guess's result. A hypothesis is a consequence that would come out differently if your guess were wrong and the nearest other explanation were right; a test whose outcome every explanation shares is sent back.
5. drop: open hypotheses you give up before they were tested (id, and why in one sentence). Usually empty.
6. experiment: at most one per turn, or null.
   - kind "test": tests lists the open hypotheses it tests; decision_rules has at least one rule for each. kind "explore": question says what you want to find out; tests and decision_rules stay empty.
   - runs: the simulations, each with a label of its own (letters, digits and _) and params: a value for EVERY knob of the brief (a knob left as it was is stated with the value it has). A simulation with the same settings as an earlier one is not run again: its result is returned and costs nothing. The simulations one rule compares must differ in one setting only, so that a difference has one possible cause.
   - measurements: measurements of your own that this experiment takes of each of its simulations, beside the outputs; an empty list when the outputs are enough. Each has name (lower-case letters, digits and _, for example rwnd_max), of (a column a simulation records over time, or arithmetic over columns of one record: the columns the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), t_from and t_to (seconds; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise). The harness computes them with taps that only listen: a measurement cannot change a result.
   - decision_rules: for each tested hypothesis, the comparison that decides it, fixed BEFORE the simulations: for (the hypothesis) and decision_rule. Write it exactly in this form: numbers; measure@label (an output, or a measurement of your own, in the simulation with that label); + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == in each comparison; comparisons joined by AND and OR. The harness checks it from the measured values: HELD or FAILED. A rule must be able to fail: it names at least one result you do not know yet. A rule on a measurement of your own may be about simulations you already ran (the measurement is new), and then no simulation is spent.
7. objections: if the records show that a ruling of the supervisor is wrong, object once: to (the ruling's id, for example V2) and because (the numbers it overlooked). Usually empty.
8. report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).

The budget counts simulations. Every turn says how many are left; one experiment may run at most half of them. When they run out you get two more turns to look and to test on simulations already run, then one last turn for the report.

If a part of your answer cannot be used, the harness leaves that part out, accepts the rest, and says in a note which part and why: read the note and repair that part. Two results closer than the tolerance count as equal: a difference inside it is not a finding."""


def supervised_format(schema):
    """The researcher's answer format in the arm "supervised": the six things only it can say (see LEAN_PROMPT). Made from the full format after
    answer_format() has fitted it to the brief, so that a design still states every knob and the recommendation every knob."""
    P = schema["properties"]
    keep = lambda obj, keys: (obj.update(properties={k: obj["properties"][k] for k in keys}, required=list(keys)), obj)[1]
    props = {"observations": {"type": "string", "description": "one or two sentences: the most important thing the results do not yet explain"}, "requests": P["requests"],
             "whys": {**P["whys"], "items": keep(P["whys"]["items"], ["about", "result", "guess", "revises"])},
             "hypotheses": {**P["hypotheses"], "items": keep(P["hypotheses"]["items"], ["from_why", "text"])}, "drop": P["drop"]}
    ex = P["experiment"]["anyOf"][0]
    ex["properties"]["decision_rules"]["items"] = keep(ex["properties"]["decision_rules"]["items"], ["for", "decision_rule"])
    keep(ex, ["kind", "tests", "question", "runs", "measurements", "decision_rules"])
    props["experiment"] = P["experiment"]
    props["objections"] = {"type": "array", "description": "objections to rulings of the supervisor, at most one for each ruling; empty when you have none",
                           "items": {"type": "object", "additionalProperties": False, "required": ["to", "because"], "properties": {
                               "to": {"type": "string", "description": "the id of the supervisor's ruling, for example V2"}, "because": {"type": "string", "description": "what in the records shows that the ruling is wrong"}}}}
    rp = P["report"]["anyOf"][0]
    rp["properties"]["claims"]["items"] = keep(rp["properties"]["claims"]["items"], ["text", "evidence"])
    keep(rp, [k for k in ("goal", "recommendation", "structure", "limit", "explanation", "claims") if k in rp["properties"]])
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
    return {r["id"] for r in ledger if r["type"] in LEARNED and r["turn"] >= k and not (r["type"] == "review" and r["body"].get("decision") == "approved")}


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
    return out


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

def supervised_prompt(text):
    """The researcher's instructions in the arm "supervised": written for the short reply (LEAN_PROMPT), not made from prompt.txt."""
    return LEAN_PROMPT


PLAIN = (  # prompt.txt -> the instructions of the arm "plain": (text as it stands in prompt.txt, what replaces it). Each must be found exactly once.
    ("everything you have hypothesised, run, observed and concluded", "everything you have run, observed and concluded"),
    ("Name the most important unexplained thing: your guesses of why are about it.", "Name the most important unexplained thing; your next experiment is about it."),
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
        system += STRUCTURE
    judged, judge_written = {}, set()   # each pair of a guess and a hypothesis is judged once in a session: a second attempt of the same turn gets the same reading
    def judge_fn(why, h):
        k = (why["guess"], h["text"])
        if k not in judged:
            judged[k] = judge_link(model, brief, why, h)
        return judged[k]
    # gate 0 of the arm "supervised": each new guess is read by the supervisor against the records it cites, once for a statement (a second attempt of the same
    # turn gets the same reading). A guess with a defect is refused the first time; a guess about the same records stated after that is accepted whatever the
    # supervisor finds, and its review says so: the supervisor can be wrong, and it must not be able to stop the work
    grounded, refused_about, ground_written = {}, {}, set()
    def ground_fn(w):
        k, about = (" ".join(str(w["guess"]).split()), tuple(w["about"])), tuple(sorted(w["about"]))
        if k not in grounded:
            try:
                g, saw = ground_of(model, brief, ledger, w)
            except (ValueError, KeyError, TypeError) as e:
                g, saw = {"records_show": "", "nearest_earlier": "none", "defect": "none", "because": f"the supervisor's reading could not be read ({type(e).__name__}): the guess is accepted unread"}, ""
            refuse = g["defect"] != "none" and not refused_about.get(about)
            if refuse:
                refused_about[about] = 1
            grounded[k] = {**g, "saw": saw, "refuse": refuse, "result": w["result"], "guess": w["guess"]}
        return grounded[k]
    judge = judge_fn if a.judge == "on" and arm == "hypotheses" else None   # the supervised arm has the supervisor's review of the test in its place
    tol_given = type((brief.get("goal") or {}).get("tolerance")) in (int, float)   # tools.check_brief has made sure it is a number of per cent between 0 and 100
    TOLERANCE = float(brief["goal"]["tolerance"]) if tol_given else DEFAULT_TOLERANCE
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
                                              **({"supervisor": {"model": model, "temperature": 0, "max_tokens": 9000, "draft_tokens": draft_tokens(9000), "sees": "the brief's description, the guess, the hypothesis, the decision rules, the planned simulations, the measured numbers; not the researcher's observations or reasons"}} if arm == "supervised" else {})}, "given": brief, "prompt": system}, indent=1) + "\n")
    print(f"session {SID} (brief {brief['id']}): {tools.SESSION}", flush=True)
    ledger = load_ledger()
    if a.baseline == "on":
        baseline(ledger)
    turn, sims, tool_only, pending, budget = max([r["turn"] for r in ledger], default=0), 0, 0, [], a.budget
    asked = False  # whether the model was already asked for the verdicts that were missing when it sent its report
    giving_up = False  # set after UNUSABLE turns in a row without a usable answer: the next turn is the last and takes only the report
    free_left = FREE_TURNS  # the turns after the budget is used up in which the researcher may still look and test on simulations already run (s048)
    how, unusable = None, 0  # how the session ended (None while it runs); turns in a row without a usable answer
    count = {"calls": 0, "length": 0}  # requests answered by the model server, and how many of them ended with finish_reason "length"

    def sup_log(rid, gate, saw, answer):
        """Beside the ledger: what the supervisor was shown for one of its records, and what it answered (no tool reads it; the page shows it on request)."""
        with (tools.SESSION / SUPERVISOR_FILE).open("a") as f:
            f.write(json.dumps({"id": rid, "turn": turn, "gate": gate, "shown": saw, "answer": answer}) + "\n")

    def finish():
        """session.json: when and how the session ended, the report's ledger id, the hypotheses still open."""
        m = json.loads(meta.read_text())
        st = states(ledger)[0]
        m.update(ended=time.strftime("%Y-%m-%dT%H:%M:%S"), how=how or "stopped from outside", report=next((r["id"] for r in reversed(ledger) if r["type"] == "report"), None),
                 left_open=[h for h, v in st.items() if v == "open"], without_verdict=[h for h in sorted(states(ledger)[1], key=lambda h: int(h[1:])) if st.get(h) == "open"], turns=turn, simulations=sims, calls=count["calls"], cut_off=count["length"])
        meta.write_text(json.dumps(m, indent=1) + "\n")

    if meta.exists() and json.loads(meta.read_text()).get("report"):
        ap.error(f"session {SID} ended with its final report ({json.loads(meta.read_text())['report']}) and cannot be continued")
    if meta.exists() and "how" in (m := json.loads(meta.read_text())):  # a session that is continued is running again
        meta.write_text(json.dumps({k: v for k, v in m.items() if k not in ("ended", "how", "report", "left_open")}, indent=1) + "\n")
    for sig in (signal.SIGTERM, signal.SIGHUP):  # stopped from outside, or its terminal closed: still record that it ended
        signal.signal(sig, lambda *_: sys.exit(143))
    try:
        while how is None:
            # a last turn: "report" after too many unusable answers (only the final report is accepted), "budget" when the
            # budget is used up (no experiment is accepted and the report is required); otherwise an ordinary turn
            mode, need_now = "report" if giving_up else ("free" if free_left > 0 else "budget") if sims >= budget else None, False
            free_left -= mode == "free"
            text = render(ledger, readings=arm == "supervised")
            size = count_tokens(model, text)
            if size > LEDGER_TOKENS:
                append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"loop stopped by the harness: the rendered ledger is {size} tokens, over the limit of {LEDGER_TOKENS}"})
                how = "ledger too large"
                break
            turn += 1
            since = max((i for i, r in enumerate(ledger) if r["type"] == "turn"), default=-1)  # what was added after the previous turn's record
            append(ledger, turn, "turn", ledger[-1]["id"] if ledger else None, {"simulations_left": max(0, budget - sims), "open_hypotheses": sum(v == "open" for v in states(ledger)[0].values()),
                                                                                    "added": [r["id"] for r in ledger[since + 1:]], "last_turn": mode})
            # the last turn names the hypotheses that still need a verdict: "give your verdicts on the checked hypotheses" was read as "judge every one again"
            # (s030: seventeen second verdicts, each refused)
            st_now, checked_now = states(ledger)
            waiting = sorted((h for h, v in st_now.items() if v == "open" and h in checked_now), key=lambda h: (len(h), h))
            last_ask = "Write the final report (report). The rulings on the tested hypotheses are the supervisor's; none is owed by you." if arm == "supervised" else ((f"Give a verdict on each hypothesis that is still open and has a checked decision rule ({', '.join(waiting)}), and write the final report (report). " if waiting
                   else "Every hypothesis that has a checked decision rule already has its verdict: write the final report (report). ") + \
                "A hypothesis that already has a verdict is closed: do not judge it again (a second verdict for it is refused).")
            user = (f"BRIEF:\n{json.dumps(brief, indent=1)}\n\nSIMULATION BUDGET: " + (f"used up. THIS IS THE LAST TURN: no experiment is accepted{' and budget_request is no longer possible' if asks_budget else ''}. "
                    + last_ask if mode == "budget" else
                    f"closed. THIS IS THE LAST TURN: the last {UNUSABLE} turns gave no usable answer, so the session ends now. Only the final report (report) is accepted in this turn; "
                    "write it from what the ledger holds." if mode == "report" else
                    f"used up: all {budget} simulations have run. Before the last turn, which takes only the final report, you have this turn{f' and {free_left} more' if free_left else ''} "
                    "to look further and to test on the simulations already run: requests, guesses and their rethinks, hypotheses, and tests whose simulations have all run "
                    "already (their results are returned, not run again; measurements you define are computed from what they recorded). An experiment that needs a new "
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
            last, parsed, err, content, refused = (ledger[-1]["id"] if ledger else None), None, None, "", []
            again = ""   # the second attempt of a turn is told why the first could not be used (it was asked the very same thing before: a refused answer cost a whole reply and taught nothing)
            CALLS["turn"] = turn
            for _attempt in range(2):
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
                ok, no = sort_out(parsed, brief, ledger, budget - sims, mode, insist=not asked, judge=judge, supervised=arm == "supervised", ground=ground_fn if arm == "supervised" else None, short=short)
                rq = [] if mode not in (None, "free") else (parsed.get("requests") or [])[:LOOKS if arm == "supervised" else 3]   # a free turn may look too (s048, 2026-11-22)   # looking is cheap in the supervised arm: more requests in one turn
                if any(r.startswith(WAIT) for _, r in no):  # said once; the note shows it, and the report is then taken as it comes
                    asked = need_now = True
                if any(ok.values()) or rq:  # something in the answer can be used: it is accepted, without the refused parts
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
                f.write(json.dumps({"turn": turn, "answer": parsed}) + "\n")
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
            for q in rq:  # each tool request and what came back are kept in the ledger (request: by the model; result: by the harness);
                out = call(q)  # the result (a reading) stays in the ledger text of every later turn, and the supervisor is given it too
                qid = append(ledger, turn, "request", last, {"tool": q.get("tool"), "args": q.get("args") or {}})
                tid = append(ledger, turn, "result", qid, {"tool": q.get("tool"), "result": out})
                pending.append(tid)
            ex, report = ok["experiment"], ok["report"]
            if not (ok["rethink"] or ok["whys"] or ok["hypotheses"] or ok["drop"] or ok["verdicts"] or ok["objections"] or ex is not None or report is not None or br):  # only requests
                tool_only += 1
                if tool_only > (LOOKS if arm == "supervised" else 3):
                    pending.append("limit")
                append(ledger, turn, "note", last, {"observations": parsed.get("observations"), "requests": rq}, by="model")
                continue
            tool_only = 0
            seen = [parsed.get("observations")]  # what the model said it read, kept once: in the first record this turn adds
            obs = lambda: {"observations": seen.pop()} if seen else {}
            for v in ok["verdicts"]:
                append(ledger, turn, "verdict", v["for"], {k: v.get(k) for k in ("for", "result", "because", "next")} | obs())
            for o in ok["objections"]:   # the researcher's objection to one ruling, and the supervisor's second look at it: a new ruling record, which stands
                was = next(r for r in ledger if r["id"] == o["to"])
                oid = append(ledger, turn, "objection", o["to"], {"to": o["to"], "for": was["body"]["for"], "because": o["because"]} | obs())
                try:
                    again, saw = answer_objection(model, brief, ledger, was, o["because"])
                    vid = append(ledger, turn, "verdict", was["body"]["for"], {"for": was["body"]["for"], "result": again["result"], "because": again["because"], "next": was["body"].get("next") or "" if again["stands"] else "",
                                                                             "fair": was["body"].get("fair", True) if again["stands"] else again["result"] != "inconclusive", "defect": was["body"].get("defect", "none") if again["stands"] else "none",
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
            for w in ok["whys"]:
                last = append(ledger, turn, "why", last, {k: w[k] for k in ("about", "result", "guess", "unseen", "matters", "worth", "reason")} | ({"revises": w["revises"]} if w.get("revises") else {}) | ({"ground": w["ground"]} if w.get("ground") else {}) | obs())
                if w.get("ground"):   # the supervisor's reading of the records this guess cites
                    k = (" ".join(str(w["guess"]).split()), tuple(w["about"]))
                    ground_written.add(k)
                    gid = append(ledger, turn, "review", last, {"for": last, "gate": "ground", "decision": "approved" if w["ground"]["defect"] == "none" else "contested", **w["ground"]})
                    sup_log(gid, "ground", (grounded.get(k) or {}).get("saw", ""), w["ground"])
            for h in ok["hypotheses"]:
                last = append(ledger, turn, "hypothesis", last, {"text": h["text"], "question": h["question"], "why": h["why"], "prediction": h.get("prediction"), "follows_from": h["follows_from"], "from_why": h["from_why"]} | ({"judge": h["judge"]} if h.get("judge") else {}) | obs())
            if ex is not None and arm == "supervised" and ex.get("kind") == "test":
                # gate 1: before any simulation of the test is run, the supervisor reads the design of each tested hypothesis. A defect sends the whole
                # experiment back, once for a hypothesis: sent again it is run, and the record says that the supervisor still objects ("contested")
                back = []
                for hid in ex["tests"]:
                    before = sum(r["type"] == "review" and r["body"]["for"] == hid and r["body"]["decision"] == "sent_back" for r in ledger)
                    try:
                        rev, saw = review_design(model, brief, ledger, ex, hid)
                    except (ValueError, KeyError, TypeError) as e:
                        append(ledger, turn, "note", hid, {"text": f"the supervisor's review of the test of {hid} could not be read ({type(e).__name__}): the test is run unreviewed"})
                        continue
                    decision = "approved" if rev["defect"] == "none" else "contested" if before else "sent_back"
                    gid = append(ledger, turn, "review", hid, {"for": hid, "decision": decision, **rev, "rules": [d["decision_rule"] for d in ex.get("decision_rules") or [] if d.get("for") == hid],
                                                               "simulations": next((n.get("simulations") for n in ex.get("needs") or [] if n.get("for") == hid), [r["label"] for r in ex["runs"]])})
                    sup_log(gid, "design", saw, rev)
                    if decision == "sent_back":
                        back.append(f"{hid} ({gid}: {DEFECTS[rev['defect']]})")
                if back:   # a test that was sent back is not run or counted; the tests the supervisor let through are (2026-11-18: in s047 one sent-back test kept an approved one from being checked for two turns)
                    gone = [x.split(" ", 1)[0] for x in back]
                    kept = without_tests(ex, gone)
                    append(ledger, turn, "note", last, {"text": ("the experiment was not run" if kept is None else "a part of the experiment was not run") + ": the supervisor sent back the test of " + "; ".join(back) + ". Its reasons stand in those review records. Repair the design and send "
                                                                + ("the experiment" if kept is None else "that test") + " again, or read the answer from the records you have. A test is sent back once: sent again, it is run."
                                                                + ("" if kept is None else f" The other tests of this experiment are run now: {', '.join(kept['tests'])}."), "part": "experiment" if kept is None else "tests " + ", ".join(gone), "reason": "sent back by the supervisor"})
                    ex = kept
            if ex is not None:
                sims += experiment(ledger, turn, (ex.get("tests") or [last])[0], ex | obs())
                if arm == "supervised" and ex.get("kind") == "test":
                    # gate 2: the harness has checked the rules; the supervisor says what each check means. Its ruling is the hypothesis's verdict
                    xid = next(r["id"] for r in reversed(ledger) if r["type"] == "experiment")
                    for hid in ex["tests"]:
                        if not any(r["type"] == "check" and r["body"]["experiment"] == xid and r["body"]["for"] == hid and r["body"]["result"] in ("held", "failed") for r in ledger):
                            continue   # nothing was checked for it (a simulation its rule names failed): it stays open
                        doubt = next((r["body"]["doubt_if"] for r in reversed(ledger) if r["type"] == "review" and r["body"]["for"] == hid), "")
                        try:
                            ruling, saw = rule_on(model, brief, ledger, xid, hid, doubt)
                        except (ValueError, KeyError, TypeError) as e:
                            append(ledger, turn, "note", hid, {"text": f"the supervisor's ruling on {hid} could not be read ({type(e).__name__}): {hid} stays open"})
                            continue
                        vid = append(ledger, turn, "verdict", hid, {"for": hid, "result": ruling["result"], "because": ruling["because"], "next": ruling["retest"], "fair": ruling["fair"], "defect": ruling["defect"],
                                                                   "shows": ruling["shows"], "checks": ruling["checks"], "experiment": xid, **({"doubt_if": doubt} if doubt else {}),
                                                                   **({"changed_by_harness": ruling["changed_by_harness"]} if ruling.get("changed_by_harness") else {})}, by="supervisor")
                        sup_log(vid, "ruling", saw, ruling)
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
    finally:
        finish()
    print(f"stopped: session {SID}, {how or 'stopped from outside'}, {sims} simulations, {turn} turns, ledger {LEDGER}")

if __name__ == "__main__":
    main()
