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
UNUSABLE = 3  # the loop stops after this many turns in a row without a usable answer (each turn is already two attempts)
PREFIX = {"why": "Y", "rethink": "K", "judge": "J", "hypothesis": "H", "drop": "W", "experiment": "X", "simulation": "S", "evidence": "E", "check": "C", "verdict": "V", "report": "R",
          "malformed": "M", "note": "N", "draft": "D", "request": "Q", "result": "T", "turn": "U"}
# who produced the content of a record, written into it as "by": the model (what it wrote), the simulator (what was
# measured), the harness (what it computed, found or decided itself), the operator (the person; no record type is theirs yet)
SOURCES = ("model", "harness", "simulator", "operator")
BY = {"draft": "model", "why": "model", "rethink": "model", "judge": "harness", "hypothesis": "model", "drop": "model", "experiment": "model", "verdict": "model", "report": "model",
      "simulation": "simulator", "evidence": "harness", "check": "harness", "malformed": "harness", "note": "harness", "request": "model", "result": "harness", "turn": "harness"}
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


def outputs_of(edits, brief=None):
    """The measures of the brief's network with these changes made (the brief's own where there is none)."""
    b = brief or tools.describe_system()
    return network.outputs(network.apply(b["topology"], edits)) if edits else tools.outputs(b)


def design_key(clean, edits):
    """What makes two designs the same simulation: the same settings and seed, on the same network."""
    return (tools.same(tools.options(clean)), json.dumps(edits, sort_keys=True))


def edits_say(edits):
    """A list of changes in a few words, for an evidence line."""
    one = lambda e: (f"+host {e['id']}" if e["do"] == "add_host" else f"+link {e['id']} {e['from']}-{e['to']}" if e["do"] == "add_link" else f"+{e['kind']} flow {e['id']} {e['from']}>{e['to']}" if e["do"] == "add_flow"
                     else f"+{e['kind'] or 'scheduler'} on {e['on']}'s side of {e['id']}" if e["do"] == "add_queue" else f"-{e['kind']} {e['id']}")
    return ", ".join(one(e) for e in edits)


STRUCTURE = """

In this session you may also change the structure of the network. A simulation of an experiment carries structure: a list of changes made, in order, to the network of the brief (always to the brief's network, never to that of an earlier simulation); an empty list runs the network as it is. A change states every field (do, id, kind, from, to, on, rate, type), with "" where one does not apply:
   - do add_host: id, a new name (at most 12 lower-case letters and digits, beginning with a letter).
   - do add_link: id, from and to (the two hosts it joins), rate (for example 1Gbps). One link for each two hosts.
   - do add_flow: id, kind (udp or tcp), from, to, and rate for udp (for example 100Mbps) or type for tcp (for example TcpCubic). A flow needs one shortest way from its sender to its receiver.
   - do add_queue: id (the link), on (the host whose sending side of the link it is), kind (scheduler or fifo). A scheduler gives each flow that passes it a part of the link.
   - do remove: kind (host, link, flow or queue) and id (a queue's id is its link's). A host goes with its links and with the flows that start or end at it.
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
        if not text(n.get("to_know")) or not text(n.get("measure")):
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


def since(ledger, at):
    """The results recorded after place `at` of the ledger: ids of evidence tables, checks and verdicts."""
    return [r["id"] for r in ledger[at + 1:] if r["type"] in ("evidence", "check", "verdict")]


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
    xid = append(ledger, turn, "experiment", parent, {"kind": ex["kind"], "tests": ex.get("tests") or [], "question": ex.get("question") or "", "varied": ex.get("varied") or [],
                                                      "control": ex.get("control") or None, "runs": [{k: r[k] for k in ("label", "params", "clamped") + (("structure",) if r["structure"] else ())} for r in runs], "decision_rules": stated,
                                                      **({"needs": ex["needs"]} if ex.get("needs") else {}),
                                                      **({"observations": ex["observations"]} if ex.get("observations") else {})},
                 rid="X0" if zero else None, by="harness" if zero else None)
    fresh = [r for r in runs if not r["prior"] and not r["twin"]]
    results = dict(zip((r["label"] for r in fresh), tools.run_many([r["params"] for r in fresh], [r["structure"] for r in fresh])))
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
        sid = append(ledger, turn, "simulation", xid, body, rid="S0" if zero else None)
        made[r["label"]] = ledger[-1]
        if "same_as" in body:
            append(ledger, turn, "note", sid, {"text": f"simulation {r['label']} of {xid} has the same settings and seed as {first['id']} (run {body['run_id']}): the earlier result is returned, "
                                                       "nothing was run again, and it is not counted against the budget", "simulation": sid, "same_as": first["id"]})
        if "metrics" in body:
            values[r["label"]] = body["metrics"]
            lines.append(f"{r['label']} {body['run_id']} {changed} | " + " ".join(f"{k}={body['metrics'][k]}" for k in (body["metrics"] if "structure" in body else evidence_measures()) if k in body["metrics"])
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
        return (f"[{now}] " + (f"revises {b['revises']}: " if b.get("revises") else "") + f"about {', '.join(b['about'])}: {flat(b['result'])} | guess: {flat(b['guess'])} | not visible: {flat(b['unseen'])} "
                f"| for the goal: {flat(b['matters'])} | {flat(b['reason'])}")
    if t == "rethink":
        return f"of {b['for']} in the light of {', '.join(b['in_light_of'])}: now {STANDING[b['now']]}. {flat(b['because'])}"
    if t == "hypothesis":
        return f"({st.get(r['id'], 'open')}) " + (f"from {b['from_why']}: " if b.get("from_why") else "") + f"{flat(b['text'])}" + (f" | prediction: {flat(b['prediction'])}" if b.get("prediction") else "")
    if t == "drop":
        return f"{b['for']}: {flat(b['why'])}"
    if t == "experiment":
        sims = "; ".join(f"{x['label']} {{{', '.join(f'{k}={v}' for k, v in x['params'].items()) or 'defaults'}}}"
                         + ("".join(f" [{k}: asked {a}, used {u}]" for k, (a, u) in x["clamped"].items())) for x in b["runs"])
        return ((f"test of {', '.join(b['tests'])}" if b["kind"] == "test" else f"explore: {flat(b['question'])}") + (f" | varied: {', '.join(b['varied'])}" if b["varied"] else "")
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
    if t == "verdict":
        return f"on {b['for']}: {b['result']}. {flat(b['because'])} Next: {flat(b['next'])}"
    if t == "malformed":
        return f"an answer the harness could not use, so nothing in it was recorded or run: {flat(b['error'])}"
    return json.dumps(b)

def render(ledger):
    """The ledger as text for the prompt: one line per record, and in an evidence record one line per simulation."""
    st = dict(states(ledger)[0])
    for y, w in why_states(ledger).items():   # a why with its standing now, and whether results have come in since it was last settled
        st[y] = {**w, "stale": since(ledger, w["at"]) if w["worth"] == "verify" else [], "idle": w["worth"] == "verify" and not any(r["type"] == "hypothesis" and r["body"].get("from_why") == y for r in ledger)}
    return "\n".join(f"[{r['id']}] turn {r['turn']} {r['type']} " + shown(r, st)[:CAP] for r in ledger if r["type"] not in HIDDEN) or "(empty)"

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

def ask(model, system, user, schema, draft, temperature, max_tokens):
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature, "max_tokens": max_tokens,
            "response_format": {"type": "json_schema", "json_schema": {"name": "turn", "schema": schema}}}
    if not draft:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    r = post(API + "/chat/completions", body, 1800)
    ch = r["choices"][0]
    return ch["message"].get("content") or "", ch["message"].get("reasoning") or "", ch.get("finish_reason"), r.get("usage", {})

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
            f"THE HYPOTHESIS said to come from this guess: {hyp['text']}\nIts prediction: {hyp.get('prediction') or 'not stated'}\n\nWould testing this hypothesis tell whether the guess is true?")
    def read():
        d = json.loads(ask(model, JUDGE, user, JUDGE_SCHEMA, False, 0, 400)[0])
        return bool(d["follows"]), " ".join(str(d["because"]).split())
    follows, because = read()
    if not follows:   # a refusal costs the model a turn and the judge is not steady on a pair at the border (s041 H3: no, then yes): it refuses only when a second reading agrees
        again, because2 = read()
        if again:
            return True, f"read twice. The second reading: {because2} The first found no link: {because}"
    return follows, because


ROLES = ("supports", "background", "limits")  # what a claim of a final report does: a reason for the recommendation, how the system behaves, when the recommendation would change

def check_report(rep, brief, ids, ledger=None):
    """None if the final report can be accepted; otherwise what is wrong with it. ledger: the session's records, to know which knobs it varied."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    for k in ("goal", "explanation", "holds_when", "breaks_when"):
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

def experiment_problem(ex, brief, ledger, left, st):
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
        if i not in refused and named[i] and all(l in prior for l in named[i]):
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

def sort_out(t, brief, ledger, left, mode=None, insist=True, judge=None):
    """The parts of an answer that can be used, and the parts that cannot, each with the reason: (ok, refused).
    ok = {verdicts, drop, hypotheses, experiment, report, budget_request}; refused = [(part, reason), ...].
    A refused part is left out and the rest is accepted. mode: None for an ordinary turn; "budget" for the last turn
    after the budget is used up (no experiment); "report" for a last turn that accepts only the final report."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    st, checked = states(ledger)
    ok, no = {"verdicts": [], "drop": [], "rethink": [], "whys": [], "hypotheses": [], "experiment": None, "report": None, "budget_request": None}, []
    only = "this last turn accepts only the final report"
    for v in t.get("verdicts") or []:
        part = f"verdict for {v.get('for')}"
        if mode == "report":
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
    # A why is not fixed by how it was first stated. Its standing now (stand) is what a rethink or a revising why last made it; it is fresh when no
    # result has come in since it was last settled, when this answer rethinks it, or when it is one of this answer's own. A hypothesis comes only from
    # a why that is worth verifying AND fresh: the early guesses are looked at again in the light of each new result before anything is built on them.
    ws = why_states(ledger)
    stand = {y: w["worth"] for y, w in ws.items()}
    revised_as = {y: w["as"] for y, w in ws.items() if w.get("as")}
    later = {y: since(ledger, w["at"]) + [f"V{sum(r['type'] == 'verdict' for r in ledger) + i + 1}" for i in range(len(ok["verdicts"]))] for y, w in ws.items()}
    fresh = {y for y in ws if not later[y]}
    for k in t.get("rethink") or []:
        y = k.get("id") if isinstance(k, dict) else None
        light = [of_run(a) for a in k["in_light_of"]] if isinstance(k, dict) and isinstance(k.get("in_light_of"), list) else None
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
        elif not light or any(kinds.get(a) not in ("evidence", "simulation", "check", "verdict") for a in light):
            no.append((f"rethink of {y}", "in_light_of must list the results you looked at it again with: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3)"))
        elif later[y] and not set(light) & set(later[y]):
            no.append((f"rethink of {y}", f"in_light_of must name at least one result that came in after {y} was last settled ({', '.join(later[y][:4])}): a rethink looks at a why again in the light of what was measured since"))
        else:
            ok["rethink"].append({"id": y, "in_light_of": light, "now": k["now"], "because": k["because"]})
            stand[y] = k["now"]
            fresh.add(y)
    # the review of the step from one hypothesis to the next: the guesses whose hypotheses were checked since they were last settled must be rethought
    # in this answer before it goes on to a new hypothesis or an experiment (and before the report). A new why that replaces one of them settles it too.
    tested = tested_whys(ledger)
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
        elif not isinstance(w, dict) or not all(text(w.get(k)) for k in ("result", "guess", "unseen", "matters", "reason")):
            no.append(("new why", "a why needs result (the result it is about, in one sentence), guess (why it came out so), unseen (what in the system, not directly visible, would make it so), "
                                  "matters (how it could matter for the goal) and reason (why it is or is not worth verifying now)"))
        elif w.get("worth") not in ("verify", "set_aside"):
            no.append(("new why", "a why says whether it is worth verifying now: worth is verify or set_aside"))
        elif not isinstance(about, list) or not about or any(a != "brief" and kinds.get(a) not in ("evidence", "simulation", "check", "verdict") for a in about):
            bad = [a for a in about or [] if a != "brief" and a not in kinds] if isinstance(about, list) else []
            no.append(("new why", (f"about names ids that are not in the ledger: {', '.join(map(str, bad))}" if bad else
                                   "about must list the records whose result the why explains: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), "
                                   "a run id for what you read in that run's series or trace (for example r001), or the word brief")))
        elif w.get("revises") is not None and (w["revises"] not in ws or stand[w["revises"]] == "revised"):
            no.append(("new why", "revises is null, or the id of an earlier why in the ledger that this one replaces with a better guess (one that has not been revised already)"))
        else:
            ok["whys"].append(w)
            new = f"Y{n_why + len(ok['whys'])}"   # the id it is about to get
            whys[new], stand[new] = w, w["worth"]
            fresh.add(new)
            if w.get("revises"):
                stand[w["revises"]], revised_as[w["revises"]] = "revised", new
    for h in t.get("hypotheses") or []:
        if isinstance(h, dict) and not h.get("follows_from") and whys.get(h.get("from_why")):
            h["follows_from"] = list(whys[h["from_why"]]["about"])   # what the hypothesis follows from: what its why is about
        if mode == "report":
            no.append(("new hypothesis", only))
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
        elif not text(h.get("question")):
            no.append(("new hypothesis", "a hypothesis needs a question: the hypothesis put as one plain question"))
        elif not text(h.get("why")):
            no.append(("new hypothesis", "a hypothesis needs a why: one plain sentence saying how answering it helps reach the goal"))
        elif not isinstance(h.get("follows_from"), list) or not h["follows_from"] or any(f != "brief" and kinds.get(f) not in ("verdict", "check", "evidence", "simulation") for f in h["follows_from"]):
            bad = [f for f in h.get("follows_from") or [] if f != "brief" and f not in kinds] if isinstance(h.get("follows_from"), list) else []
            no.append(("new hypothesis", (f"follows_from names ids that are not in the ledger: {', '.join(map(str, bad))}" if bad else
                                          "follows_from must list what the hypothesis follows from: ids of verdicts, checks, evidence tables or simulations in the ledger (for example V2, C3, E1), or the word brief")))
        else:
            # the judge (judge: a function of the why and the hypothesis, given by the loop; None: no judging): does testing this hypothesis tell whether its guess is true?
            read = None
            if judge is not None:
                try:
                    follows, because = judge(whys[h["from_why"]], h)
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
    if ex is not None:
        why = only if mode == "report" else "the simulation budget is used up: no experiment is accepted in the last turn" if mode == "budget" else FIRST.format(look_again(due())) if due() else experiment_problem(ex, brief, ledger, None, st)
        if not why:  # readable as sent: now cut back what cannot test anything, then count what is left against the budget
            ex, cuts = trim(ex, brief, ledger)
            no.extend(cuts)
            why = experiment_problem(ex, brief, ledger, left, st) if ex is not None else None
        if ex is None:
            pass
        elif why:
            no.append(("experiment", why))
        else:
            ok["experiment"] = ex
    br = t.get("budget_request")
    if br is not None:
        if mode:
            no.append(("budget_request", "no more simulations can be asked for in a last turn"))
        elif not (isinstance(br, dict) and type(br.get("simulations")) is int and br["simulations"] >= 1 and text(br.get("why"))):
            no.append(("budget_request", "it needs simulations (a whole number of at least 1) and a one-sentence why"))
        else:
            ok["budget_request"] = br
    report = t.get("report")
    if report is None:
        if t.get("done") and not mode:
            no.append(("done", "done needs the final report: fill report, or set done to false"))
    elif not (mode or t.get("done")):
        no.append(("report", "a report ends the session: give it together with done = true, or leave it null"))
    else:
        waiting = sorted((h for h in checked if st.get(h) == "open"), key=lambda h: int(h[1:]))  # tested, and not judged even by this answer
        why = check_report(report, brief, set(kinds), ledger)  # the ledger's ids, and those of the verdicts accepted from this same answer
        # the guesses marked worth verifying from which no hypothesis came and which no rethink settled (s041: all 11 guesses were marked verify, none set
        # aside; two of them, one the true cause, were never taken up): choosing which guesses to verify is a link of the chain, so it is closed too
        taken = {r["body"].get("from_why") for r in ledger if r["type"] == "hypothesis"} | {h.get("from_why") for h in ok["hypotheses"]}
        hanging = sorted((y for y, s in stand.items() if s == "verify" and y not in taken), key=lambda y: int(y[1:]))
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
            "do": {"type": "string", "enum": list(network.DOES)}, "id": {"type": "string"}, "kind": {"type": "string", "enum": ["", "udp", "tcp", "host", "link", "flow", "queue", "scheduler", "fifo"]},
            "from": {"type": "string"}, "to": {"type": "string"}, "on": {"type": "string"}, "rate": {"type": "string"}, "type": {"type": "string"}}}
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


PLAIN = (  # prompt.txt -> the instructions of the arm "plain": (text as it stands in prompt.txt, what replaces it). Each must be found exactly once.
    ("everything you have hypothesised, run, observed and concluded", "everything you have run, observed and concluded"),
    ("Name the most important unexplained thing: your guesses of why are about it.", "Name the most important unexplained thing; your next experiment is about it."),
    ("\n5. experiment: at most one per turn.", "\n2. experiment: at most one per turn."),
    ('   - kind "explore": question says what you want to find out; tests, needs and decision_rules stay empty. Use it when you do not yet have a claim to test.', '   - kind is always "explore": question says what you want to find out.'),
    ("\n6. After an experiment the harness appends the evidence (one line per simulation) and, for every decision rule, a check: the decision rule with the measured numbers written into it, and HELD or FAILED. You never write evidence or checks yourself.",
     "\n3. After an experiment the harness appends the evidence (one line per simulation). You never write evidence yourself."),
    ("\n8. requests:", "\n4. requests:"), ("\n9. budget_request:", "\n5. budget_request:"), ("\n10. done and report:", "\n6. done and report:"),
    ("do not leave the decisive test for later than you can afford", "do not leave the decisive experiment for later than you can afford"),
    ("(for example E3, C5)", "(for example E3)"),
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
    ap.add_argument("--max-tokens", type=int, help="most tokens of one answer, draft included; default 32000 with the draft (the default), 3000 without")
    ap.add_argument("--policy", "--mode", dest="policy", choices=["share", "cap", "prio"], default="share", help="the scheduling policy: how the scheduler divides the link (prio: only for a brief with a network). The operator's choice, never shown to the model (--mode is its earlier name)")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--judge", choices=["on", "off"], default="on", help="on (the default): a second model call judges whether each new hypothesis follows from the guess of why it names, and a hypothesis that does not is refused; off: no such call")
    ap.add_argument("--arm", choices=["hypotheses", "plain"], help="hypotheses (the default): the loop as it is. plain: the same loop, model, brief, budget and final report without the hypothesis format "
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
    if may_change(brief):  # only a session that may change the structure is told how
        system += STRUCTURE
    judged, judge_written = {}, set()   # each pair of a guess and a hypothesis is judged once in a session: a second attempt of the same turn gets the same reading
    def judge_fn(why, h):
        k = (why["guess"], h["text"])
        if k not in judged:
            judged[k] = judge_link(model, brief, why, h)
        return judged[k]
    judge = judge_fn if a.judge == "on" and arm != "plain" else None
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
                                    "flags": {"budget": a.budget, "draft": a.draft, "max_tokens": a.max_tokens, "temperature": a.temperature, "baseline": a.baseline, "judge": a.judge, **({"arm": arm} if arm != "hypotheses" else {})}, "given": brief, "prompt": system}, indent=1) + "\n")
    print(f"session {SID} (brief {brief['id']}): {tools.SESSION}", flush=True)
    ledger = load_ledger()
    if a.baseline == "on":
        baseline(ledger)
    turn, sims, tool_only, pending, budget = max([r["turn"] for r in ledger], default=0), 0, 0, [], a.budget
    asked = False  # whether the model was already asked for the verdicts that were missing when it sent its report
    giving_up = False  # set after UNUSABLE turns in a row without a usable answer: the next turn is the last and takes only the report
    how, unusable = None, 0  # how the session ended (None while it runs); turns in a row without a usable answer
    count = {"calls": 0, "length": 0}  # requests answered by the model server, and how many of them ended with finish_reason "length"

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
            mode, need_now = "report" if giving_up else "budget" if sims >= budget else None, False
            text = render(ledger)
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
            last_ask = (f"Give a verdict on each hypothesis that is still open and has a checked decision rule ({', '.join(waiting)}), and write the final report (report). " if waiting
                   else "Every hypothesis that has a checked decision rule already has its verdict: write the final report (report). ") + \
                "A hypothesis that already has a verdict is closed: do not judge it again (a second verdict for it is refused)."
            user = (f"BRIEF:\n{json.dumps(brief, indent=1)}\n\nSIMULATION BUDGET: " + ("used up. THIS IS THE LAST TURN: no experiment is accepted and budget_request is no longer possible. "
                    + last_ask if mode == "budget" else
                    f"closed. THIS IS THE LAST TURN: the last {UNUSABLE} turns gave no usable answer, so the session ends now. Only the final report (report) is accepted in this turn; "
                    "write it from what the ledger holds." if mode == "report" else
                    f"{budget - sims} simulations left ({budget} granted so far; budget_request can raise that to at most {limit}, the brief's limit). This turn's experiment may run at most {spend_cap(budget - sims, per)} new simulations: never more than half of what is left, so that something remains for what its results raise.")
                    + (f"\n\nLOOK AGAIN FIRST: results have come in for hypotheses of these guesses since you last settled them: {look_again(tested_whys(ledger))}. Before anything new, give a rethink "
                       "for each in this answer (id: the why's own id; now: supported, refuted, verify or set_aside; because of what in those results). No new hypothesis and no experiment "
                       "is accepted until each has its rethink." if arm != "plain" and mode != "report" and tested_whys(ledger) else "")
                    + f"\n\nTOLERANCE: two results that differ by less than {TOLERANCE:g} % count as equal ({'stated by the brief' if tol_given else 'the default of the harness: the brief states none'}). "
                      "A difference inside it is not a finding, and a setting is not better for it."
                    + f"\n\nLEDGER:\n{text}")
            if pending:
                user += "\n\nTOOL RESULTS (for your last requests):\n" + "\n\n".join(pending)
                pending = []
            last, parsed, err, content, refused = (ledger[-1]["id"] if ledger else None), None, None, "", []
            for _attempt in range(2):
                content, draft, finish_reason, usage = ask(model, system, user, schema, a.draft == "on", a.temperature, a.max_tokens)
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
                ok, no = sort_out(parsed, brief, ledger, budget - sims, mode, insist=not asked, judge=judge)
                rq = [] if mode else (parsed.get("requests") or [])[:3]
                if any(r.startswith(WAIT) for _, r in no):  # said once; the note shows it, and the report is then taken as it comes
                    asked = need_now = True
                if any(ok.values()) or rq:  # something in the answer can be used: it is accepted, without the refused parts
                    err = None
                    break
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
            br = ok["budget_request"]
            if br:  # granted up to the brief's limit, before this turn's experiment is counted
                granted = max(0, min(br["simulations"], limit - budget))
                budget += granted
                append(ledger, turn, "note", last, {"text": f"budget request: {br['simulations']} more simulations asked, {granted} granted; the budget is now {budget} (the brief's limit is {limit})", "why": br["why"]})
            for q in rq:  # each tool request and what came back are kept in the ledger (request: by the model; result: by the harness);
                out = call(q)  # like the simulation records they are not part of the ledger text of later turns
                qid = append(ledger, turn, "request", last, {"tool": q.get("tool"), "args": q.get("args") or {}})
                append(ledger, turn, "result", qid, {"tool": q.get("tool"), "result": out})
                pending.append(f"{q.get('tool')}({json.dumps(q.get('args') or {})}) ->\n{out}")
            ex, report = ok["experiment"], ok["report"]
            if not (ok["rethink"] or ok["whys"] or ok["hypotheses"] or ok["drop"] or ok["verdicts"] or ex is not None or report is not None or br):  # only requests
                tool_only += 1
                if tool_only > 3:
                    pending = [" (tool-only turn limit reached: results withheld, decide now)"]
                append(ledger, turn, "note", last, {"observations": parsed.get("observations"), "requests": rq}, by="model")
                continue
            tool_only = 0
            seen = [parsed.get("observations")]  # what the model said it read, kept once: in the first record this turn adds
            obs = lambda: {"observations": seen.pop()} if seen else {}
            for v in ok["verdicts"]:
                append(ledger, turn, "verdict", v["for"], {k: v.get(k) for k in ("for", "result", "because", "next")} | obs())
            for d in ok["drop"]:
                append(ledger, turn, "drop", d["id"], {"for": d["id"], "why": d["why"]} | obs())
            for k, (follows, because) in judged.items():  # what the judge read in this turn, kept for a person (not shown to the model: a refusal reaches it as a note)
                if k not in judge_written:
                    judge_written.add(k)
                    append(ledger, turn, "judge", None, {"guess": k[0], "hypothesis": k[1], "follows": follows, "because": because})
            for k in ok["rethink"]:
                append(ledger, turn, "rethink", k["id"], {"for": k["id"], "in_light_of": k["in_light_of"], "now": k["now"], "because": k["because"]} | obs())
            for w in ok["whys"]:
                last = append(ledger, turn, "why", last, {k: w[k] for k in ("about", "result", "guess", "unseen", "matters", "worth", "reason")} | ({"revises": w["revises"]} if w.get("revises") else {}) | obs())
            for h in ok["hypotheses"]:
                last = append(ledger, turn, "hypothesis", last, {"text": h["text"], "question": h["question"], "why": h["why"], "prediction": h.get("prediction"), "follows_from": h["follows_from"], "from_why": h["from_why"]} | ({"judge": h["judge"]} if h.get("judge") else {}) | obs())
            if ex is not None:
                sims += experiment(ledger, turn, (ex.get("tests") or [last])[0], ex | obs())
            if report is not None:  # accepted (sort_out): the ledger, report.json, and the session is over
                append(ledger, turn, "report", last, report | obs())
                (tools.SESSION / "report.json").write_text(json.dumps(report, indent=1) + "\n")
                how = "done by the model" if mode is None else "all simulations used, report given in the last turn" if mode == "budget" else f"{UNUSABLE} turns in a row without a usable answer, report given in the last turn"
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
