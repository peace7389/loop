"""The loop: rebuild the prompt from the ledger, ask the model once, do what its answer asks, append records.
One session = one folder, sessions/<id>/, and one brief (briefs/<id>.json, the assignment): session.json (what the
session was given), ledger.jsonl and drafts.jsonl are written here, runs/ by tools.run_many, and nothing in it is shared with another
session. The scheduling policy of each simulation (the operator's choice) goes to checks/operator.jsonl, outside that folder.

A turn's answer may state new hypotheses, drop hypotheses, give verdicts, and design ONE experiment: a set of
simulations with one purpose, run at once. An experiment that tests hypotheses carries decision rules, comparisons
stated before the simulations run, each with a rival explanation under which it would fail; the harness evaluates each
decision rule itself from the measured values (decision_rules.py) and records a check. A verdict is accepted only for a
hypothesis that has a checked decision rule. The budget counts simulations; a simulation with the same settings and seed
as an earlier one of the session is not run again.
A session ends with the model's final report: when the model sets done, or in one last turn after the budget is used
up. The accepted report goes to the ledger and to report.json; session.json records how the session ended.
Who else may write what: control.py's docstring."""
import argparse, json, re, signal, sys, time
from pathlib import Path
import requests
import decision_rules, tools

ROOT = Path.home() / "project"
H, OPERATOR, API = ROOT / "harness", ROOT / "checks/operator.jsonl", "http://127.0.0.1:18000/v1"
LEDGER = SID = None  # the current session's ledger and id, set in main()
CAP = 6000  # characters of any tool result or ledger body shown to the model
LEDGER_TOKENS = 100_000  # the loop stops when the rendered ledger is larger than this
NEED = "the report cannot be accepted yet: a hypothesis that has a checked decision rule needs a verdict. Still without one: "
UNUSABLE = 3  # the loop stops after this many turns in a row without a usable answer (each turn is already two attempts)
PREFIX = {"hypothesis": "H", "drop": "W", "experiment": "X", "simulation": "S", "evidence": "E", "check": "C", "verdict": "V", "report": "R",
          "malformed": "M", "note": "N", "draft": "D", "request": "Q", "result": "T"}
# who produced the content of a record, written into it as "by": the model (what it wrote), the simulator (what was
# measured), the harness (what it computed, found or decided itself), the operator (the person; no record type is theirs yet)
SOURCES = ("model", "harness", "simulator", "operator")
BY = {"draft": "model", "hypothesis": "model", "drop": "model", "experiment": "model", "verdict": "model", "report": "model",
      "simulation": "simulator", "evidence": "harness", "check": "harness", "malformed": "harness", "note": "harness", "request": "model", "result": "harness"}
HIDDEN = ("draft", "scratch", "simulation", "request", "result")  # kept on disk, not replayed: what the model wrote before its answer, and the
                                             # simulation records (the evidence record has one line for each of them)
SHOWN = [k for k in tools.MANIFEST["outputs"] if k not in ("link_rate_bps", "weight_udp")]  # the measures of an evidence line

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

def plan(ledger, runs):
    """Each simulation an experiment asks for: its clamped params, and whether it has to be run. A simulation with the same
    settings and seed as an earlier one of the session ("prior": that simulation record), or as an earlier one of the same
    experiment ("twin": that one's label), is not run again."""
    out = []
    for r in runs:
        clean, clamps = tools.clamp(r.get("params") or {})
        key = tools.same(tools.options(clean))
        prior = next((q for q in ledger if q["type"] == "simulation" and "metrics" in q["body"] and not q["body"].get("same_as") and tools.same(q["body"]["params"]) == key), None)
        out.append({"label": r["label"], "params": clean, "clamped": clamps, "key": key, "prior": prior, "twin": None if prior else next((q["label"] for q in out if q["key"] == key), None)})
    return out

def experiment(ledger, turn, parent, ex, zero=False):
    """What the harness does with an experiment: record the design and the decision rules as stated; run at once all its
    simulations that have not been run before in this session (one simulation record each, a note for each one reused);
    one evidence record, a line per simulation; then one check record per decision rule. Returns how many were run."""
    brief = tools.describe_system()
    runs, stated = plan(ledger, ex["runs"]), ex.get("decision_rules") or []
    xid = append(ledger, turn, "experiment", parent, {"kind": ex["kind"], "tests": ex.get("tests") or [], "question": ex.get("question") or "", "varied": ex.get("varied") or [],
                                                      "control": ex.get("control") or None, "runs": [{k: r[k] for k in ("label", "params", "clamped")} for r in runs], "decision_rules": stated,
                                                      **({"observations": ex["observations"]} if ex.get("observations") else {})},
                 rid="X0" if zero else None, by="harness" if zero else None)
    fresh = [r for r in runs if not r["prior"] and not r["twin"]]
    results = dict(zip((r["label"] for r in fresh), tools.run_many([r["params"] for r in fresh])))
    OPERATOR.parent.mkdir(parents=True, exist_ok=True)
    with OPERATOR.open("a") as f:  # the operator's line of each simulation run: session, run, scheduling policy, seconds. No tool reads that file
        for res in results.values():
            f.write(json.dumps({"session": SID, "id": res["id"], "policy": tools.POLICY, "seconds": res["seconds"]}) + "\n")
    values, lines, made = {}, [], {}  # made: label -> the simulation record that holds its result
    for r in runs:
        changed = ", ".join(f"{k}={v}" for k, v in r["params"].items() if v != brief["knobs"][k]["default"]) or "defaults"
        first = r["prior"] or made.get(r["twin"])  # the earlier simulation with the same settings and seed, if any
        if first and "metrics" in first["body"]:
            body = {"label": r["label"], "run_id": first["body"]["run_id"], "params": first["body"]["params"], "metrics": first["body"]["metrics"], "same_as": first["id"]}
        else:
            res = results.get(r["label"]) or results[r["twin"]]  # (a twin of a simulation that failed shares its failure)
            body = {"label": r["label"], "run_id": res["id"], "params": res.get("used") or r["params"], **({"metrics": res["metrics"]} if "metrics" in res else {"error": res["error"]})}
        sid = append(ledger, turn, "simulation", xid, body, rid="S0" if zero else None)
        made[r["label"]] = ledger[-1]
        if "same_as" in body:
            append(ledger, turn, "note", sid, {"text": f"simulation {r['label']} of {xid} has the same settings and seed as {first['id']} (run {body['run_id']}): the earlier result is returned, "
                                                       "nothing was run again, and it is not counted against the budget", "simulation": sid, "same_as": first["id"]})
        if "metrics" in body:
            values[r["label"]] = body["metrics"]
            lines.append(f"{r['label']} {body['run_id']} {changed} | " + " ".join(f"{k}={body['metrics'][k]}" for k in SHOWN if k in body["metrics"])
                         + (f" (the result of {first['id']}: same settings and seed, not run again)" if "same_as" in body else ""))
        else:
            lines.append(f"{r['label']} {body['run_id']} {changed} | FAILED: {' '.join(body['error'].split())[:300]}")
    append(ledger, turn, "evidence", xid, {"experiment": xid, "lines": lines}, rid="E0" if zero else None)
    labels = [r["label"] for r in runs]
    for d in stated:
        try:
            held, numbers = decision_rules.check(d["decision_rule"], tools.MANIFEST["outputs"], labels, values)
            result = "held" if held else "failed"
        except decision_rules.DecisionRuleError as e:  # it was readable (validate), so: a simulation it names gave no value
            result, numbers = "not checked", str(e)
        append(ledger, turn, "check", xid, {"for": d["for"], "experiment": xid, "decision_rule": d["decision_rule"], "rival": d.get("rival"), "rival_predicts": d.get("rival_predicts"),
                                            "with_numbers": numbers, "result": result})
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
    if t == "hypothesis":
        return f"({st.get(r['id'], 'open')}) {flat(b['text'])}" + (f" | prediction: {flat(b['prediction'])}" if b.get("prediction") else "")
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
        return f"of the decision rule for {b['for']} in {b['experiment']}: {flat(b.get('decision_rule', b.get('rule')))}  ->  {b['with_numbers']}  :  {b['result'].upper()}"
    if t == "verdict":
        return f"on {b['for']}: {b['result']}. {flat(b['because'])} Next: {flat(b['next'])}"
    if t == "malformed":
        return f"an answer the harness could not use, so nothing in it was recorded or run: {flat(b['error'])}"
    return json.dumps(b)

def render(ledger):
    """The ledger as text for the prompt: one line per record, and in an evidence record one line per simulation."""
    st = states(ledger)[0]
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

def check_report(rep, brief, ids):
    """None if the final report can be accepted; otherwise what is wrong with it."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    for k in ("goal", "explanation", "holds_when", "breaks_when"):
        if not text(rep.get(k)):
            return f"report.{k} must be a text"
    rec, exp, claims, open_q = rep.get("recommendation"), rep.get("expected"), rep.get("claims"), rep.get("open_questions")
    if not isinstance(rec, dict) or not rec:
        return "report.recommendation must give at least one knob and its value"
    if set(rec) & set(brief["system"]):
        return f"report.recommendation contains a setting the brief fixes, which cannot be recommended: {', '.join(sorted(set(rec) & set(brief['system'])))}"
    if set(rec) - set(brief["knobs"]):
        return f"report.recommendation names something that is not a knob: {', '.join(sorted(set(rec) - set(brief['knobs'])))}"
    try:
        clamps = tools.clamp(rec)[1]
    except (ValueError, TypeError) as e:
        return f"report.recommendation has a value that cannot be read: {e}"
    if clamps:
        return "report.recommendation has a value outside its allowed range: " + ", ".join(f"{k}={asked}" for k, (asked, _) in clamps.items())
    if not isinstance(exp, dict) or set(exp) - set(tools.MANIFEST["outputs"]) or not all(type(v) in (int, float) for v in exp.values()):
        return "report.expected must give numbers for outputs (by their names)"
    if not isinstance(claims, list) or not all(isinstance(c, dict) and text(c.get("text")) and isinstance(c.get("evidence"), list) for c in claims):
        return "report.claims must be a list of {text, evidence: [ledger ids]}"
    missing = sorted({i for c in claims for i in c["evidence"] if i not in ids})
    if missing:
        return f"report.claims cites ids that are not in the ledger: {', '.join(map(str, missing))}"
    if not isinstance(open_q, list) or not all(isinstance(q, str) for q in open_q):
        return "report.open_questions must be a list of texts (it may be empty)"
    return None

def experiment_problem(ex, brief, ledger, left, st):
    """None if the experiment can be run as designed; otherwise what is wrong with it. st: the hypotheses' states with the
    accepted parts of the same answer already applied."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    runs, per = ex.get("runs") or [], brief["limits"]["simulations_per_experiment"]
    labels = [r.get("label") for r in runs]
    if not 1 <= len(runs) <= per:
        return f"an experiment has 1 to {per} simulations"
    if len(set(labels)) != len(labels) or not all(re.fullmatch(r"[A-Za-z0-9_]{1,20}", str(l)) for l in labels):
        return "every simulation needs its own label: letters, digits and _ only, at most 20 characters"
    if any(set(r.get("params") or {}) - set(brief["knobs"]) - set(brief["system"]) for r in runs):
        return "a simulation's params has keys that are not settings of the brief"
    try:
        fresh = sum(1 for r in plan(ledger, runs) if not r["prior"] and not r["twin"])  # simulations already run in this session are not run again
    except (ValueError, TypeError) as e:
        return f"a simulation has a setting that cannot be read: {e}"
    if fresh > left:
        return f"the experiment needs {fresh} new simulations but only {left} are left in the budget"
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
                decision_rules.parse(r.get("decision_rule"), tools.MANIFEST["outputs"], labels)
            except decision_rules.DecisionRuleError as e:
                return f"the decision rule for {r['for']} cannot be read: {e}. Decision rule: {r.get('decision_rule')}"
            if not text(r.get("rival")) or r.get("rival_predicts") not in ("held", "failed"):
                return f"the decision rule for {r['for']} needs a rival (a competing explanation of how the system behaves) and rival_predicts (held or failed)"
            if r["rival_predicts"] == "held":
                return "this decision rule would hold under the rival too; choose simulations where the two explanations give different results"
    elif ex.get("kind") == "explore":
        if not text(ex.get("question")) or tests or rs:
            return "an explore experiment needs a question, and has no tests and no decision rules"
    else:
        return "experiment.kind must be test or explore"
    return None

def sort_out(t, brief, ledger, left, mode=None, insist=True):
    """The parts of an answer that can be used, and the parts that cannot, each with the reason: (ok, refused).
    ok = {verdicts, drop, hypotheses, experiment, report, budget_request}; refused = [(part, reason), ...].
    A refused part is left out and the rest is accepted. mode: None for an ordinary turn; "budget" for the last turn
    after the budget is used up (no experiment); "report" for a last turn that accepts only the final report."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    st, checked = states(ledger)
    ok, no = {"verdicts": [], "drop": [], "hypotheses": [], "experiment": None, "report": None, "budget_request": None}, []
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
    known = len([r for r in ledger if r["type"] == "hypothesis"])
    for h in t.get("hypotheses") or []:
        if mode == "report":
            no.append(("new hypothesis", only))
        elif not text(h.get("text")):
            no.append(("new hypothesis", "a hypothesis needs a text"))
        else:
            ok["hypotheses"].append(h)
            st[f"H{known + len(ok['hypotheses'])}"] = "open"  # the id it is about to get
    ex = t.get("experiment")
    if ex is not None:
        why = only if mode == "report" else "the simulation budget is used up: no experiment is accepted in the last turn" if mode == "budget" else experiment_problem(ex, brief, ledger, left, st)
        if why:
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
        why = check_report(report, brief, {r["id"] for r in ledger})
        if not why and insist and waiting and mode != "report":  # said once per session: the verdicts are asked for together with the report
            why = NEED + ", ".join(waiting) + ". Give their verdicts in the same answer as the report."
        if why:
            no.append(("report", why))
        else:
            ok["report"] = report
    return ok, no

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
    ap.add_argument("--max-tokens", type=int, help="most tokens of one answer, draft included; default 8000 with the draft, 3000 without")
    ap.add_argument("--policy", "--mode", dest="policy", choices=["share", "cap"], default="share", help="the scheduling policy: how the scheduler divides the link. The operator's choice, never shown to the model (--mode is its earlier name)")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--baseline", choices=["on", "off"], default="on", help="on an empty ledger, first run the harness's own default experiment X0")
    a = ap.parse_args()
    global LEDGER, SID
    tools.POLICY = a.policy
    schema, system = json.loads((H / "schema.json").read_text()), (H / "prompt.txt").read_text()
    model = requests.get(API + "/models", timeout=30).json()["data"][0]["id"]
    try:
        SID = tools.open_session(a.session, a.brief)  # after the model server answered, so a failed start leaves no empty session folder
    except ValueError as e:
        ap.error(str(e))
    brief = tools.describe_system()  # the brief, with the descriptions of the outputs and the tools
    per = brief["limits"]["simulations_per_experiment"]
    schema["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["maxItems"] = per
    a.budget = brief["limits"]["simulations"] if a.budget is None else a.budget
    a.max_tokens = a.max_tokens or (8000 if a.draft == "on" else 3000)
    limit = brief["limits"]["simulations"]  # the most simulations the session can ever be granted
    LEDGER, meta = tools.SESSION / "ledger.jsonl", tools.SESSION / "session.json"
    if a.budget > limit:
        if not meta.exists():  # a new session that cannot start leaves no empty folder behind
            (tools.SESSION / "runs").rmdir()
            tools.SESSION.rmdir()
        ap.error(f"the starting budget is at most the brief's limit of {limit} simulations")
    if not meta.exists():  # the session's own record of what it was given; the scheduling policy is not in it
        meta.write_text(json.dumps({"id": SID, "brief": brief["id"], "model": model, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "flags": {"budget": a.budget, "draft": a.draft, "max_tokens": a.max_tokens, "temperature": a.temperature, "baseline": a.baseline}, "given": brief, "prompt": system}, indent=1) + "\n")
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
            user = (f"BRIEF:\n{json.dumps(brief, indent=1)}\n\nSIMULATION BUDGET: " + ("used up. THIS IS THE LAST TURN: no experiment is accepted and budget_request is no longer possible. "
                    "Give your verdicts on hypotheses whose decision rules have been checked, and write the final report (report)." if mode == "budget" else
                    f"closed. THIS IS THE LAST TURN: the last {UNUSABLE} turns gave no usable answer, so the session ends now. Only the final report (report) is accepted in this turn; "
                    "write it from what the ledger holds." if mode == "report" else
                    f"{budget - sims} simulations left ({budget} granted so far; budget_request can raise that to at most {limit}, the brief's limit). One experiment holds at most {min(per, budget - sims)} simulations.")
                    + f"\n\nLEDGER:\n{text}")
            if pending:
                user += "\n\nTOOL RESULTS (for your last requests):\n" + "\n\n".join(pending)
                pending = []
            last, parsed, err, content = (ledger[-1]["id"] if ledger else None), None, None, ""
            for _attempt in range(2):
                content, draft, finish_reason, usage = ask(model, system, user, schema, a.draft == "on", a.temperature, a.max_tokens)
                count["calls"] += 1
                count["length"] += finish_reason == "length"
                if a.draft == "on":
                    last = append(ledger, turn, "draft", last, {"chars": len(draft), "tokens": usage.get("completion_tokens"), "model": model, "finish_reason": finish_reason})
                    with (tools.SESSION / "drafts.jsonl").open("a") as f:  # the text itself: its own file, one line per draft, by the ledger id
                        f.write(json.dumps({"id": last, "turn": turn, "text": draft}) + "\n")
                if not content.strip() or finish_reason == "length":
                    err = f"empty content or finish_reason={finish_reason}"
                    continue
                try:
                    parsed = json.loads(content)
                except ValueError as e:
                    err, parsed = f"invalid JSON: {e}", None
                    continue
                ok, no = sort_out(parsed, brief, ledger, budget - sims, mode, insist=not asked)
                rq = [] if mode else (parsed.get("requests") or [])[:3]
                if any(r.startswith(NEED) for _, r in no):  # said once; the note shows it, and the report is then taken as it comes
                    asked = need_now = True
                if any(ok.values()) or rq:  # something in the answer can be used: it is accepted, without the refused parts
                    err = None
                    break
                err = ("nothing in the answer could be used. " + " | ".join(f"{part}: {why}" for part, why in no)) if no else \
                    "the answer does nothing: no hypothesis, drop, verdict, experiment, report or request"
                parsed = None
                if need_now:  # no second try with the same text: the model must first see which verdicts are missing
                    break
            if parsed is None:
                append(ledger, turn, "malformed", last, {"error": err, "content": content[:2000]})
                if mode == "report":  # the last turn that was given for the report alone
                    how = f"{UNUSABLE} turns in a row without a usable answer"
                elif mode == "budget":
                    how = None if need_now else "simulation limit reached, no usable report"  # after the one request for verdicts: one more last turn
                else:
                    unusable += 1
                    if unusable >= UNUSABLE:  # no ending yet: one last turn follows, which accepts only the final report
                        giving_up = True
                        append(ledger, turn, "note", ledger[-1]["id"], {"text": f"{UNUSABLE} turns in a row gave no usable answer: the harness ends the session after one last turn, in which only the final report is accepted"})
                continue
            unusable = 0
            for part, why in no:  # each refused part: a note, shown to the model in the next turn; the rest of the answer was accepted
                append(ledger, turn, "note", last, {"text": f"refused part of the answer: {part}. Reason: {why.rstrip('.')}. The other parts of that answer were accepted.", "part": part})
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
            if not (ok["hypotheses"] or ok["drop"] or ok["verdicts"] or ex is not None or report is not None or br):  # only requests
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
            for h in ok["hypotheses"]:
                last = append(ledger, turn, "hypothesis", last, {"text": h["text"], "prediction": h.get("prediction")} | obs())
            if ex is not None:
                sims += experiment(ledger, turn, (ex.get("tests") or [last])[0], ex | obs())
            if report is not None:  # accepted (sort_out): the ledger, report.json, and the session is over
                append(ledger, turn, "report", last, report | obs())
                (tools.SESSION / "report.json").write_text(json.dumps(report, indent=1) + "\n")
                how = "done by the model" if mode is None else "simulation limit reached" if mode == "budget" else f"{UNUSABLE} turns in a row without a usable answer, report given in the last turn"
            elif mode == "report":
                how = f"{UNUSABLE} turns in a row without a usable answer"
            elif mode == "budget" and not need_now:  # a last turn without a usable report (after the one request for verdicts there is one more)
                how = "simulation limit reached, no usable report"
    except ModelServerError as e:  # the session ends cleanly: the error is in the ledger, and session.json says how it ended
        append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"model server error: {e}"})
        how = "model server error"
    finally:
        finish()
    print(f"stopped: session {SID}, {how or 'stopped from outside'}, {sims} simulations, {turn} turns, ledger {LEDGER}")

if __name__ == "__main__":
    main()
