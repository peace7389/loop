"""The loop: rebuild the prompt from the ledger, ask the model once, run what it asked, append records.
One session = one folder, sessions/<id>/, and one brief (briefs/<id>.json, the assignment): session.json (what the
session was given) and ledger.jsonl are written here, runs/ by tools.run, and nothing in it is shared with another session. The operator's mode of each run goes to checks/operator.jsonl, outside that folder.
Who else may write what: control.py's docstring."""
import argparse, json, time
from pathlib import Path
import requests
import tools

ROOT = Path.home() / "project"
H, OPERATOR, API = ROOT / "harness", ROOT / "checks/operator.jsonl", "http://127.0.0.1:18000/v1"
LEDGER = SID = None  # the current session's ledger and id, set in main()
CAP = 6000  # characters of any tool result or ledger body shown to the model
CEILING = 150  # most experiments one invocation can be granted: the starting budget plus every budget_request grant
LEDGER_TOKENS = 100_000  # the loop stops when the rendered ledger is larger than this
PREFIX = {"hypothesis": "H", "experiment": "X", "evidence": "E", "verdict": "V", "malformed": "M", "note": "N", "draft": "D"}
DRAFT_TYPES = ("draft", "scratch")  # "scratch" is the name used in ledgers written before 2026-11-11

def load_ledger():
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()] if LEDGER.exists() else []

def append(ledger, turn, type_, parent, body, rid=None):
    rec = {"id": rid or f"{PREFIX[type_]}{sum(r['type'] == type_ and r['id'] != 'E0' for r in ledger) + 1}", "turn": turn, "type": type_,
           "parent": parent, "body": body, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with LEDGER.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    ledger.append(rec)
    return rec["id"]

def run(params):
    """tools.run, plus the operator's line for it: which session, which run, which mode, how long. No tool reads that file."""
    res = tools.run(params)
    OPERATOR.parent.mkdir(parents=True, exist_ok=True)
    with OPERATOR.open("a") as f:
        f.write(json.dumps({"session": SID, "id": res["id"], "mode": tools.MODE, "seconds": res.get("seconds")}) + "\n")
    return res

def baseline(ledger):
    """Before turn 1 of a new ledger: the harness runs the default experiment once and records it as evidence E0
    (turn 0, no parent, not counted in the run budget), so the model's first turn starts from an observed record."""
    if ledger:
        return
    res = run({})
    append(ledger, 0, "evidence", None, {"run_id": res["id"], "pass_if": None, "note": "default experiment (every parameter at its default), run by the harness before turn 1",
                                         **(res.get("metrics") or {}), **({"error": res["error"]} if "error" in res else {})}, rid="E0")

def shown(r):
    """One record's body as the prompt shows it. Evidence: run id, the metric values, pass_if. Hypothesis: its text.
    Verdict: result, because, next. Every other type: its JSON. The full body stays in ledger.jsonl."""
    b, flat = r["body"], lambda v: " ".join(str(v).split())
    if r["type"] == "evidence":
        vals = " ".join(f"{k}={b[k]}" for k in tools.MANIFEST["outputs"] if k in b) or "no metrics"
        err = f" error: {flat(b['error'])}" if "error" in b else ""
        return f"{b['run_id']} {vals}{err} | pass_if: {flat(b['pass_if']) if b.get('pass_if') else 'none'}" + (f" ({b['note']})" if b.get("note") else "")
    if r["type"] == "hypothesis":
        return flat(b["text"])
    if r["type"] == "verdict":
        return f"{b['result']}. {flat(b['because'])} Next: {flat(b['next'])}"
    return json.dumps(b)

def render(ledger):
    """The ledger as text for the prompt, one line per record. Draft records (what the model wrote before its answer) are kept on disk, not replayed."""
    lines = [f"[{r['id']}] turn {r['turn']} {r['type']}" + (f" (parent {r['parent']})" if r["parent"] else "") + ": " + shown(r)[:CAP]
             for r in ledger if r["type"] not in DRAFT_TYPES]
    return "\n".join(lines) or "(empty)"

def count_tokens(model, text):
    """Tokens of a text, counted by the model server's own tokenizer."""
    return requests.post(API.removesuffix("/v1") + "/tokenize", json={"model": model, "prompt": text}, timeout=300).json()["count"]

def ask(model, system, user, schema, draft, temperature):
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature, "max_tokens": 8000 if draft else 1500,
            "response_format": {"type": "json_schema", "json_schema": {"name": "turn", "schema": schema}}}
    if not draft:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    r = requests.post(API + "/chat/completions", json=body, timeout=1800).json()
    ch = r["choices"][0]
    return ch["message"].get("content") or "", ch["message"].get("reasoning") or "", ch.get("finish_reason"), r.get("usage", {})

def validate(t, manifest, ledger):
    ex, vd, rq = t.get("experiment"), t.get("verdict"), t.get("requests") or []
    if not rq and (ex is None) == (vd is None):
        return "exactly one of experiment / verdict must be given (unless only requests are made)"
    if ex is not None:
        if set(ex.get("params", {})) - set(manifest["knobs"]) - set(manifest["system"]):
            return "experiment.params has keys that are not settings of the brief"
        if not str(ex.get("pass_if", "")).strip():
            return "experiment without pass_if"
    if vd is not None and not any(r["id"] == vd.get("for") and r["type"] == "hypothesis" for r in ledger):
        return "verdict.for must be the id of an existing hypothesis record"
    br = t.get("budget_request")
    if br is not None and not (isinstance(br, dict) and type(br.get("experiments")) is int and br["experiments"] >= 1 and str(br.get("reason") or "").strip()):
        return "budget_request needs experiments (an integer of at least 1) and a one-sentence reason"
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
    ap.add_argument("--budget", type=int, help=f"experiments granted at the start; default: the brief's limits.simulations (at most {CEILING}; the model can ask for more, up to {CEILING} in total)")
    ap.add_argument("--draft", choices=["on", "off"], default="on", help="on: the model may write a draft before its JSON answer (max_tokens 8000) and the draft is kept in the ledger; off: answer only (max_tokens 1500)")
    ap.add_argument("--mode", choices=["share", "cap"], default="share")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--baseline", choices=["on", "off"], default="on", help="on an empty ledger, first run the default experiment and record it as evidence E0")
    a = ap.parse_args()
    global LEDGER, SID
    tools.MODE = a.mode
    schema, system = json.loads((H / "schema.json").read_text()), (H / "prompt.txt").read_text()
    model = requests.get(API + "/models", timeout=30).json()["data"][0]["id"]
    try:
        SID = tools.open_session(a.session, a.brief)  # after the model server answered, so a failed start leaves no empty session folder
    except ValueError as e:
        ap.error(str(e))
    manifest = tools.describe_system()  # the brief, with the descriptions of the outputs and the tools
    a.budget = manifest["limits"]["simulations"] if a.budget is None else a.budget
    if a.budget > CEILING:
        ap.error(f"the starting budget is at most {CEILING}")
    LEDGER, meta = tools.SESSION / "ledger.jsonl", tools.SESSION / "session.json"
    if not meta.exists():  # the session's own record of what it was given; the operator's mode is not in it
        meta.write_text(json.dumps({"id": SID, "brief": manifest["id"], "model": model, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "flags": {"budget": a.budget, "draft": a.draft, "temperature": a.temperature, "baseline": a.baseline}, "given": manifest}, indent=1) + "\n")
    print(f"session {SID} (brief {manifest['id']}): {tools.SESSION}", flush=True)
    ledger = load_ledger()
    if a.baseline == "on":
        baseline(ledger)
    turn, runs_done, tool_only, pending, budget = max([r["turn"] for r in ledger], default=0), 0, 0, [], a.budget
    while runs_done < budget:
        text = render(ledger)
        size = count_tokens(model, text)
        if size > LEDGER_TOKENS:
            append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"loop stopped by the harness: the rendered ledger is {size} tokens, over the limit of {LEDGER_TOKENS}"})
            break
        turn += 1
        user = (f"BRIEF:\n{json.dumps(manifest, indent=1)}\n\nRUN BUDGET: {budget - runs_done} experiments left"
                f" ({budget} granted so far; budget_request can raise that to at most {CEILING}).\n\nLEDGER:\n{text}")
        if pending:
            user += "\n\nTOOL RESULTS (for your last requests):\n" + "\n\n".join(pending)
            pending = []
        last, parsed, err, content = (ledger[-1]["id"] if ledger else None), None, None, ""
        for _attempt in range(2):
            content, draft, finish, usage = ask(model, system, user, schema, a.draft == "on", a.temperature)
            if a.draft == "on":
                last = append(ledger, turn, "draft", last, {"text": draft, "model": model, "finish_reason": finish, "tokens": usage.get("completion_tokens")})
            if not content.strip() or finish == "length":
                err = f"empty content or finish_reason={finish}"
                continue
            try:
                parsed = json.loads(content)
            except ValueError as e:
                err, parsed = f"invalid JSON: {e}", None
                continue
            err = validate(parsed, manifest, ledger)
            if err is None:
                break
            parsed = None
        if parsed is None:
            append(ledger, turn, "malformed", last, {"error": err, "content": content[:2000]})
            continue
        br = parsed.get("budget_request")
        if br:  # granted up to the ceiling, before this turn's experiment is counted
            granted = max(0, min(br["experiments"], CEILING - budget))
            budget += granted
            append(ledger, turn, "note", last, {"text": f"budget request: {br['experiments']} more experiments asked, {granted} granted; the budget is now {budget} (ceiling {CEILING})", "reason": br["reason"]})
        rq = (parsed.get("requests") or [])[:3]
        for q in rq:
            pending.append(f"{q.get('tool')}({json.dumps(q.get('args') or {})}) ->\n{call(q)}")
        if parsed.get("experiment") is None and parsed.get("verdict") is None:  # tool-only turn
            tool_only += 1
            if tool_only > 3:
                pending = [" (tool-only turn limit reached: results withheld, decide now)"]
            append(ledger, turn, "note", last, {"observations": parsed.get("observations"), "requests": rq})
            continue
        tool_only = 0
        hid = None
        if parsed.get("hypothesis"):
            hid = last = append(ledger, turn, "hypothesis", last, {"text": parsed["hypothesis"], "prediction": parsed.get("prediction"), "observations": parsed.get("observations")})
        if parsed.get("experiment") is not None:
            ex = parsed["experiment"]
            clean, clamps = tools.clamp(ex.get("params") or {})
            xid = append(ledger, turn, "experiment", hid or last, {"params": clean, "clamped": clamps, "metrics": ex.get("metrics"), "pass_if": ex["pass_if"], "observations": None if hid else parsed.get("observations")})
            res = run(clean)
            runs_done += 1
            append(ledger, turn, "evidence", xid, {"run_id": res["id"], "pass_if": ex["pass_if"], **(res.get("metrics") or {}), **({"error": res["error"]} if "error" in res else {})})
        if parsed.get("verdict") is not None:
            vd = parsed["verdict"]
            append(ledger, turn, "verdict", vd["for"], {k: vd.get(k) for k in ("for", "result", "because", "next")} | {"observations": parsed.get("observations")})
        if parsed.get("done"):
            append(ledger, turn, "note", last, {"text": "model declared done", "observations": parsed.get("observations")})
            break
    print(f"stopped: session {SID}, {runs_done} experiments, {turn} turns, ledger {LEDGER}")

if __name__ == "__main__":
    main()
