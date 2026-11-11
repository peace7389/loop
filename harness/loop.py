"""The loop: rebuild the prompt from the ledger, ask the model once, do what its answer asks, append records.
One session = one folder, sessions/<id>/, and one brief (briefs/<id>.json, the assignment): session.json (what the
session was given) and ledger.jsonl are written here, runs/ by tools.run_many, and nothing in it is shared with another
session. The operator's mode of each simulation goes to checks/operator.jsonl, outside that folder.

A turn's answer may state new hypotheses, drop hypotheses, give verdicts, and design ONE experiment: a set of
simulations with one purpose, run at once. An experiment that tests hypotheses carries rules, comparisons written
before the simulations run; the harness evaluates each rule itself from the measured values (rules.py) and records a
check. A verdict is accepted only for a hypothesis that has a checked rule. The budget counts simulations.
A session ends with the model's final report: when the model sets done, or in one last turn after the budget is used
up. The accepted report goes to the ledger and to report.json; session.json records how the session ended.
Who else may write what: control.py's docstring."""
import argparse, json, re, signal, sys, time
from pathlib import Path
import requests
import rules, tools

ROOT = Path.home() / "project"
H, OPERATOR, API = ROOT / "harness", ROOT / "checks/operator.jsonl", "http://127.0.0.1:18000/v1"
LEDGER = SID = None  # the current session's ledger and id, set in main()
CAP = 6000  # characters of any tool result or ledger body shown to the model
CEILING = 150  # most simulations one invocation can be granted: the starting budget plus every budget_request grant
LEDGER_TOKENS = 100_000  # the loop stops when the rendered ledger is larger than this
PREFIX = {"hypothesis": "H", "drop": "W", "experiment": "X", "simulation": "S", "evidence": "E", "check": "C", "verdict": "V", "report": "R",
          "malformed": "M", "note": "N", "draft": "D"}
# who produced the content of a record, written into it as "by": the model (what it wrote), the simulator (what was
# measured), the harness (what it computed, found or decided itself), the operator (the person; no record type is theirs yet)
SOURCES = ("model", "harness", "simulator", "operator")
BY = {"draft": "model", "hypothesis": "model", "drop": "model", "experiment": "model", "verdict": "model", "report": "model",
      "simulation": "simulator", "evidence": "harness", "check": "harness", "malformed": "harness", "note": "harness"}
HIDDEN = ("draft", "scratch", "simulation")  # kept on disk, not replayed: what the model wrote before its answer, and the
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
    """Every hypothesis's state (open, or its verdict's result, or dropped), and the hypotheses that have a checked rule."""
    st = {r["id"]: "open" for r in ledger if r["type"] == "hypothesis"}
    for r in ledger:
        if r["type"] == "verdict":
            st[r["body"]["for"]] = r["body"]["result"]
        elif r["type"] == "drop":
            st[r["body"]["for"]] = "dropped"
    return st, {r["body"]["for"] for r in ledger if r["type"] == "check" and r["body"]["result"] in ("held", "failed")}

def experiment(ledger, turn, parent, ex, zero=False):
    """What the harness does with an experiment: record the design and the rules as written; run all its simulations at
    once (one simulation record each); one evidence record, a line per simulation; then one check record per rule."""
    brief = tools.describe_system()
    runs = []
    for r in ex["runs"]:
        clean, clamps = tools.clamp(r.get("params") or {})
        runs.append({"label": r["label"], "params": clean, "clamped": clamps})
    xid = append(ledger, turn, "experiment", parent, {"kind": ex["kind"], "tests": ex.get("tests") or [], "question": ex.get("question") or "", "varied": ex.get("varied") or [],
                                                      "control": ex.get("control") or None, "runs": runs, "rules": ex.get("rules") or [],
                                                      **({"observations": ex["observations"]} if ex.get("observations") else {})},
                 rid="X0" if zero else None, by="harness" if zero else None)
    results = tools.run_many([r["params"] for r in runs])
    OPERATOR.parent.mkdir(parents=True, exist_ok=True)
    with OPERATOR.open("a") as f:  # the operator's line of each simulation: session, run, mode, seconds. No tool reads that file
        for res in results:
            f.write(json.dumps({"session": SID, "id": res["id"], "mode": tools.MODE, "seconds": res["seconds"]}) + "\n")
    values, lines = {}, []
    for r, res in zip(runs, results):
        append(ledger, turn, "simulation", xid, {"label": r["label"], "run_id": res["id"], "params": res.get("used") or r["params"],
                                                 **({"metrics": res["metrics"]} if "metrics" in res else {"error": res["error"]})}, rid="S0" if zero else None)
        changed = ", ".join(f"{k}={v}" for k, v in r["params"].items() if v != brief["knobs"][k]["default"]) or "defaults"
        if "metrics" in res:
            values[r["label"]] = res["metrics"]
            lines.append(f"{r['label']} {res['id']} {changed} | " + " ".join(f"{k}={res['metrics'][k]}" for k in SHOWN if k in res["metrics"]))
        else:
            lines.append(f"{r['label']} {res['id']} {changed} | FAILED: {' '.join(res['error'].split())[:300]}")
    append(ledger, turn, "evidence", xid, {"experiment": xid, "lines": lines}, rid="E0" if zero else None)
    labels = [r["label"] for r in runs]
    for rule in ex.get("rules") or []:
        try:
            held, numbers = rules.check(rule["rule"], tools.MANIFEST["outputs"], labels, values)
            result = "held" if held else "failed"
        except rules.RuleError as e:  # it was readable (validate), so: a simulation it names gave no value
            result, numbers = "not checked", str(e)
        append(ledger, turn, "check", xid, {"for": rule["for"], "experiment": xid, "rule": rule["rule"], "with_numbers": numbers, "result": result})
    return len(runs)

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
                + (f" | control: {b['control']}" if b["control"] else "") + f" | simulations: {sims}" + "".join(f" | rule for {x['for']}: {flat(x['rule'])}" for x in b["rules"]))
    if t == "evidence":
        return f"of {b['experiment']}, one line per simulation (label, run id, settings changed from the defaults | measured):\n" + "\n".join("    " + l for l in b["lines"])
    if t == "check":
        return f"for {b['for']} in {b['experiment']}: {flat(b['rule'])}  ->  {b['with_numbers']}  :  {b['result'].upper()}"
    if t == "verdict":
        return f"on {b['for']}: {b['result']}. {flat(b['because'])} Next: {flat(b['next'])}"
    if t == "malformed":
        return f"an answer the harness could not use, so nothing in it was recorded or run: {flat(b['error'])}"
    return json.dumps(b)

def render(ledger):
    """The ledger as text for the prompt: one line per record, and in an evidence record one line per simulation."""
    st = states(ledger)[0]
    return "\n".join(f"[{r['id']}] turn {r['turn']} {r['type']} " + shown(r, st)[:CAP] for r in ledger if r["type"] not in HIDDEN) or "(empty)"

def count_tokens(model, text):
    """Tokens of a text, counted by the model server's own tokenizer."""
    return requests.post(API.removesuffix("/v1") + "/tokenize", json={"model": model, "prompt": text}, timeout=300).json()["count"]

def ask(model, system, user, schema, draft, temperature, max_tokens):
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature, "max_tokens": max_tokens,
            "response_format": {"type": "json_schema", "json_schema": {"name": "turn", "schema": schema}}}
    if not draft:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    r = requests.post(API + "/chat/completions", json=body, timeout=1800).json()
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

def validate(t, brief, ledger, left, final=False):
    """None if the answer can be used as it is; otherwise the first thing wrong with it (the turn is then malformed and
    nothing in it is recorded or run). final: the budget is used up and this is the last turn."""
    text = lambda v: isinstance(v, str) and bool(v.strip())
    st, checked = states(ledger)
    new, drops, verdicts, ex = t.get("hypotheses") or [], t.get("drop") or [], t.get("verdicts") or [], t.get("experiment")
    for v in verdicts:
        if st.get(v.get("for")) != "open":
            return f"verdict: {v.get('for')} is not an open hypothesis"
        if v["for"] not in checked:
            return f"verdict for {v['for']}: no rule of that hypothesis has been checked yet, so there is nothing to judge it by"
        if v.get("result") not in ("supported", "refuted", "inconclusive") or not text(v.get("because")):
            return f"verdict for {v['for']}: needs a result (supported, refuted or inconclusive) and a because"
        st[v["for"]] = v["result"]
    for d in drops:
        if st.get(d.get("id")) != "open" or not text(d.get("why")):
            return f"drop: {d.get('id')} must be an open hypothesis, with a reason"
        st[d["id"]] = "dropped"
    if not all(text(h.get("text")) for h in new):
        return "a hypothesis needs a text"
    for i in range(len(new)):
        st[f"H{len([r for r in ledger if r['type'] == 'hypothesis']) + i + 1}"] = "open"  # the ids they are about to get
    if final and ex is not None:
        return "the simulation budget is used up: no experiment is accepted in the last turn"
    if ex is not None:
        runs, per = ex.get("runs") or [], brief["limits"]["simulations_per_experiment"]
        labels = [r.get("label") for r in runs]
        if not 1 <= len(runs) <= per:
            return f"an experiment has 1 to {per} simulations"
        if len(set(labels)) != len(labels) or not all(re.fullmatch(r"[A-Za-z0-9_]{1,20}", str(l)) for l in labels):
            return "every simulation needs its own label: letters, digits and _ only, at most 20 characters"
        if len(runs) > left:
            return f"the experiment has {len(runs)} simulations but only {left} are left in the budget"
        if any(set(r.get("params") or {}) - set(brief["knobs"]) - set(brief["system"]) for r in runs):
            return "a simulation's params has keys that are not settings of the brief"
        if ex.get("control") not in (None, "", *labels) or set(ex.get("varied") or []) - set(brief["knobs"]):
            return "control must be the label of one of the simulations (or null), and varied must name knobs"
        tests, rs = ex.get("tests") or [], ex.get("rules") or []
        if ex.get("kind") == "test":
            if not tests or any(st.get(h) != "open" for h in tests):
                return "a test experiment needs tests: the ids of open hypotheses"
            if any(r.get("for") not in tests for r in rs) or set(tests) - {r.get("for") for r in rs}:
                return "a test experiment needs at least one rule for each tested hypothesis, and no rule for any other"
            for r in rs:
                try:
                    rules.parse(r.get("rule"), tools.MANIFEST["outputs"], labels)
                except rules.RuleError as e:
                    return f"the rule for {r['for']} cannot be read: {e}. Rule: {r.get('rule')}"
        elif ex.get("kind") == "explore":
            if not text(ex.get("question")) or tests or rs:
                return "an explore experiment needs a question, and has no tests and no rules"
        else:
            return "experiment.kind must be test or explore"
    br = t.get("budget_request")
    if br is not None and not (isinstance(br, dict) and type(br.get("simulations")) is int and br["simulations"] >= 1 and text(br.get("why"))):
        return "budget_request needs simulations (a whole number of at least 1) and a one-sentence why"
    report = t.get("report")
    if report is None:
        if final or t.get("done"):
            return "the last turn needs the final report" if final else "done needs the final report: fill report, or set done to false"
    elif not (final or t.get("done")):
        return "a report ends the session: give it together with done = true, or leave it null"
    else:
        err = check_report(report, brief, {r["id"] for r in ledger})
        if err:
            return err
    if not (new or drops or verdicts or ex is not None or t.get("requests") or t.get("done") or report is not None):
        return "the answer does nothing: no hypothesis, drop, verdict, experiment or request, and done is false"
    return None

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
    ap.add_argument("--budget", type=int, help=f"simulations granted at the start; default: the brief's limits.simulations (at most {CEILING}; the model can ask for more, up to {CEILING} in total)")
    ap.add_argument("--draft", choices=["on", "off"], default="on", help="on: the model may write a draft before its JSON answer and the draft is kept in the ledger; off: answer only")
    ap.add_argument("--max-tokens", type=int, help="most tokens of one answer, draft included; default 8000 with the draft, 3000 without")
    ap.add_argument("--mode", choices=["share", "cap"], default="share")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--baseline", choices=["on", "off"], default="on", help="on an empty ledger, first run the harness's own default experiment X0")
    a = ap.parse_args()
    global LEDGER, SID
    tools.MODE = a.mode
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
    if a.budget > CEILING:
        ap.error(f"the starting budget is at most {CEILING}")
    LEDGER, meta = tools.SESSION / "ledger.jsonl", tools.SESSION / "session.json"
    if not meta.exists():  # the session's own record of what it was given; the operator's mode is not in it
        meta.write_text(json.dumps({"id": SID, "brief": brief["id"], "model": model, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "flags": {"budget": a.budget, "draft": a.draft, "max_tokens": a.max_tokens, "temperature": a.temperature, "baseline": a.baseline}, "given": brief}, indent=1) + "\n")
    print(f"session {SID} (brief {brief['id']}): {tools.SESSION}", flush=True)
    ledger = load_ledger()
    if a.baseline == "on":
        baseline(ledger)
    turn, sims, tool_only, pending, budget = max([r["turn"] for r in ledger], default=0), 0, 0, [], a.budget
    how = None  # how the session ended; None while it runs

    def finish():
        """session.json: when and how the session ended, the report's ledger id, the hypotheses still open."""
        m = json.loads(meta.read_text())
        st = states(ledger)[0]
        m.update(ended=time.strftime("%Y-%m-%dT%H:%M:%S"), how=how or "stopped from outside", report=next((r["id"] for r in reversed(ledger) if r["type"] == "report"), None),
                 left_open=[h for h, v in st.items() if v == "open"])
        meta.write_text(json.dumps(m, indent=1) + "\n")

    if meta.exists() and json.loads(meta.read_text()).get("report"):
        ap.error(f"session {SID} ended with its final report ({json.loads(meta.read_text())['report']}) and cannot be continued")
    if meta.exists() and "how" in (m := json.loads(meta.read_text())):  # a session that is continued is running again
        meta.write_text(json.dumps({k: v for k, v in m.items() if k not in ("ended", "how", "report", "left_open")}, indent=1) + "\n")
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))  # stopped from outside: still record that it ended
    try:
        while how is None:
            final = sims >= budget  # the budget is used up: one last turn, in which no experiment is accepted and the report is required
            text = render(ledger)
            size = count_tokens(model, text)
            if size > LEDGER_TOKENS:
                append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"loop stopped by the harness: the rendered ledger is {size} tokens, over the limit of {LEDGER_TOKENS}"})
                how = "ledger too large"
                break
            turn += 1
            user = (f"BRIEF:\n{json.dumps(brief, indent=1)}\n\nSIMULATION BUDGET: " + ("used up. THIS IS THE LAST TURN: no experiment is accepted and budget_request is no longer possible. "
                    "Give your verdicts on hypotheses whose rules have been checked, and write the final report (report)." if final else
                    f"{budget - sims} simulations left ({budget} granted so far; budget_request can raise that to at most {CEILING}). One experiment holds at most {min(per, budget - sims)} simulations.")
                    + f"\n\nLEDGER:\n{text}")
            if pending:
                user += "\n\nTOOL RESULTS (for your last requests):\n" + "\n\n".join(pending)
                pending = []
            last, parsed, err, content = (ledger[-1]["id"] if ledger else None), None, None, ""
            for _attempt in range(2):
                content, draft, finish_reason, usage = ask(model, system, user, schema, a.draft == "on", a.temperature, a.max_tokens)
                if a.draft == "on":
                    last = append(ledger, turn, "draft", last, {"text": draft, "model": model, "finish_reason": finish_reason, "tokens": usage.get("completion_tokens")})
                if not content.strip() or finish_reason == "length":
                    err = f"empty content or finish_reason={finish_reason}"
                    continue
                try:
                    parsed = json.loads(content)
                except ValueError as e:
                    err, parsed = f"invalid JSON: {e}", None
                    continue
                err = validate(parsed, brief, ledger, budget - sims, final)
                if err is None:
                    break
                parsed = None
            if parsed is None:
                append(ledger, turn, "malformed", last, {"error": err, "content": content[:2000]})
                if final:
                    how = "simulation limit reached, no usable report"
                continue
            br = parsed.get("budget_request")
            if br and not final:  # granted up to the ceiling, before this turn's experiment is counted
                granted = max(0, min(br["simulations"], CEILING - budget))
                budget += granted
                append(ledger, turn, "note", last, {"text": f"budget request: {br['simulations']} more simulations asked, {granted} granted; the budget is now {budget} (ceiling {CEILING})", "why": br["why"]})
            rq = (parsed.get("requests") or [])[:3]
            for q in rq:
                pending.append(f"{q.get('tool')}({json.dumps(q.get('args') or {})}) ->\n{call(q)}")
            ex, report = parsed.get("experiment"), parsed.get("report")
            if not (parsed.get("hypotheses") or parsed.get("drop") or parsed.get("verdicts") or ex is not None or report is not None):  # only requests
                tool_only += 1
                if tool_only > 3:
                    pending = [" (tool-only turn limit reached: results withheld, decide now)"]
                append(ledger, turn, "note", last, {"observations": parsed.get("observations"), "requests": rq}, by="model")
                continue
            tool_only = 0
            seen = [parsed.get("observations")]  # what the model said it read, kept once: in the first record this turn adds
            obs = lambda: {"observations": seen.pop()} if seen else {}
            for v in parsed.get("verdicts") or []:
                append(ledger, turn, "verdict", v["for"], {k: v.get(k) for k in ("for", "result", "because", "next")} | obs())
            for d in parsed.get("drop") or []:
                append(ledger, turn, "drop", d["id"], {"for": d["id"], "why": d["why"]} | obs())
            for h in parsed.get("hypotheses") or []:
                last = append(ledger, turn, "hypothesis", last, {"text": h["text"], "prediction": h.get("prediction")} | obs())
            if ex is not None:
                sims += experiment(ledger, turn, (ex.get("tests") or [last])[0], ex | obs())
            if report is not None:  # accepted (validate): the ledger, report.json, and the session is over
                append(ledger, turn, "report", last, report | obs())
                (tools.SESSION / "report.json").write_text(json.dumps(report, indent=1) + "\n")
                how = "done by the model" if parsed.get("done") else "simulation limit reached"
    finally:
        finish()
    print(f"stopped: session {SID}, {how or 'stopped from outside'}, {sims} simulations, {turn} turns, ledger {LEDGER}")

if __name__ == "__main__":
    main()
