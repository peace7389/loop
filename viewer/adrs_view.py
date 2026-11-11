"""The two-hosts hypothesis loop (~/project) as a task of the ADRS main viewer (/?task=twohosts), served the way
ddloop and topoloop are: this module answers the page's own JSON shapes from the harness's files, read-only.

What maps to what (only where the harness recorded matching data):
  run "<session id>"     = one session (sessions/<id>/ledger.jsonl and runs/): one "iteration" per experiment the
                           model asked for. Run "loop" (old links) = the newest session
  run "operator_checks"  = the operator's sanity / share / cap simulations (checks/build1/): no AI
  the scheduling policy of every run (how the scheduler divides the link) comes from checks/operator.jsonl (a session's
  lines carry its id; lines written before 2026-11-11 call it "mode", both are read)
  research story         = hypothesis -> prediction -> decision rule -> experiment -> the model's own verdict
  drawing (adrs_view.js) = the run's series.csv (throughput per flow, TCP window, drops per queue)
There is NO score: the task asks the model to choose what "performance" means, and the harness records none.
The task entry says no_score, and the page hides its score sections (best so far, score chart, compare).
"""
import csv
import json
import os
import time

ROOT = os.path.expanduser("~/project")
SESSIONS = os.path.join(ROOT, "sessions")
BUILD1 = os.path.join(ROOT, "checks", "build1")
OPERATOR = os.path.join(ROOT, "checks", "operator.jsonl")
STAND_IN = (os.path.join(ROOT, "briefs", "two-hosts-open.json"), os.path.join(ROOT, "harness", "manifest.json"))
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "twohosts"
LOOP, CHECKS = "loop", "operator_checks"
_cache = {}


def _jsonl(path):
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _flat(led):
    """A ledger in the multi-simulation format as this module reads a ledger: one experiment and one evidence record per
    simulation (the same reading as TH_DATA.flat in adrs_view.js)."""
    if not any(r.get("type") == "simulation" for r in led):
        return led
    by_id, out = {r["id"]: r for r in led}, []
    for r in led:
        if r["type"] in ("experiment", "evidence", "check", "drop"):
            continue
        if r["type"] != "simulation":
            out.append(r)
            continue
        if (r.get("body") or {}).get("same_as"):   # the result of an earlier simulation, returned again: that one has its row
            continue
        x, b = by_id.get(r.get("parent")) or {"id": "?", "body": {}}, r.get("body") or {}
        run = next((q for q in x["body"].get("runs") or [] if q.get("label") == b.get("label")), {})
        hyp, xid = (x["body"].get("tests") or [None])[0], f"{x['id']}:{b.get('label')}"
        stated = x["body"].get("decision_rules") or x["body"].get("rules") or []   # records before 2026-11-11 say "rules" / "rule"
        rules = "; ".join(q.get("decision_rule") or q.get("rule") or "" for q in stated if q.get("for") == hyp) or None
        out.append({"id": xid, "turn": r["turn"], "type": "experiment", "parent": hyp, "ts": x.get("ts"), "body": {"params": run.get("params") or {}, "clamped": run.get("clamped") or {}, "pass_if": rules}})
        out.append({"id": r["id"], "turn": r["turn"], "type": "evidence", "parent": xid, "ts": r.get("ts"),
                    "body": {"run_id": b.get("run_id"), "pass_if": rules, **(b.get("metrics") or {}), **({"error": b["error"]} if b.get("error") else {}),
                             **({"note": x["body"].get("question")} if x["id"] == "X0" else {})}})
    return out


def _sessions():
    """Session ids, oldest first: the folders of sessions/ that have a ledger."""
    try:
        return sorted(d for d in os.listdir(SESSIONS) if os.path.isfile(os.path.join(SESSIONS, d, "ledger.jsonl")))
    except OSError:
        return []


def _load(sid=None):
    """Everything the harness wrote for one session (sid None: the operator's checks), re-read only when a file changed."""
    base = os.path.join(SESSIONS, sid, "runs") if sid else BUILD1
    ledger = os.path.join(SESSIONS, sid, "ledger.jsonl") if sid else None
    meta = os.path.join(SESSIONS, sid, "session.json") if sid else ""
    sig = (_mtime(ledger) if ledger else 0, _mtime(os.path.join(base, "index.json")), _mtime(OPERATOR), _mtime(meta), _mtime(STAND_IN[0]), _mtime(STAND_IN[1]))
    D = _cache.setdefault(("load", sid), {})
    if D.get("sig") != sig:
        # what the session was given: its session.json; a session made before briefs existed (and the operator's
        # checks) has none, and the open brief with the tool and output descriptions stands in
        model = None
        try:
            model = json.load(open(meta)).get("model")
            given = json.load(open(meta))["given"]
        except (OSError, ValueError, KeyError):
            given = {}
            for path in STAND_IN:
                try:
                    given.update(json.load(open(path)))
                except (OSError, ValueError):
                    pass
            given["id"] = None
        manifest = {**given, "params": given.get("knobs") or {}, "fixed": given.get("system") or {}, "brief": given.get("id"), "model": model}
        written = _jsonl(ledger) if ledger else []
        D.update(sig=sig, sid=sid, base=base, ledger_path=ledger, written=written, ledger=_flat(written), manifest=manifest,
                 index={r["id"]: r for r in _jsonl(os.path.join(base, "index.json"))},
                 oper={r["id"]: r for r in _jsonl(OPERATOR) if r.get("session") == sid})   # the build checks' lines carry no session
    return D


def _epoch(ts):
    try:
        return time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))
    except (TypeError, ValueError):
        return None


def _running(sid):
    """True while harness/loop.py is alive on this session (a process whose command names loop.py and whose folder is
    the project; its --session names the session, and without one it made the newest)."""
    now = time.time()
    if now - _cache.get("run_at", 0) < 5:
        return _cache.get("run") == sid
    alive = None
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = f.read().split(b"\0")
            if any(a.endswith(b"loop.py") for a in cmd) and os.readlink(f"/proc/{pid}/cwd").startswith(ROOT):
                alive = cmd[cmd.index(b"--session") + 1].decode(errors="replace") if b"--session" in cmd[:-1] else (_sessions() or [None])[-1]
                break
        except OSError:
            continue
    _cache.update(run=alive, run_at=now)
    return alive == sid


def _series(base, run_id):
    """series.csv of a run in folder `base`, as columns; drops are turned from running totals into per-sample counts."""
    path = os.path.join(base, run_id, "series.csv")
    key = ("series", path, _mtime(path))
    if key in _cache:
        return _cache[key]
    cols = {k: [] for k in ("t", "udp", "tcp", "cwnd", "d0", "d1")}
    try:
        with open(path) as f:
            prev0 = prev1 = 0.0
            for row in csv.DictReader(f):
                d0, d1 = float(row["drops_band0"]), float(row["drops_band1"])
                cols["t"].append(float(row["t"]))
                cols["udp"].append(float(row["udp_bps"]))
                cols["tcp"].append(float(row["tcp_bps"]))
                cols["cwnd"].append(float(row["cwnd"]))
                cols["d0"].append(d0 - prev0)
                cols["d1"].append(d1 - prev1)
                prev0, prev1 = d0, d1
    except (OSError, ValueError, KeyError):
        cols = None
    if cols and not cols["t"]:
        cols = None
    _cache[key] = cols
    return cols


def _mbps(v):
    return f"{v / 1e6:,.1f} Mbps" if isinstance(v, (int, float)) else "–"


def _pct(v):
    return f"{100 * v:.1f}%" if isinstance(v, (int, float)) else "–"


def _measured(m):
    if not m or "udp_goodput_bps" not in m:
        return "no measurement"
    return (f"UDP {_mbps(m.get('udp_goodput_bps'))} · TCP {_mbps(m.get('tcp_goodput_bps'))} · link use {_pct(m.get('link_util'))} · "
            f"UDP loss {_pct(m.get('udp_loss_frac'))} · drops: UDP queue {int(m.get('drops_band0', 0)):,}, TCP queue {int(m.get('drops_band1', 0)):,}"
            + (f" · TCP retransmissions {int(m['tcp_retrans']):,}" if "tcp_retrans" in m else ""))


def _params_text(p):
    return ", ".join(f"{k} {v}" for k, v in (p or {}).items()) or "defaults"


COLUMNS = ["Run", "UDP weight", "UDP offered", "Scheduling policy", "UDP Mbps", "TCP Mbps", "Link use", "UDP loss", "Drops UDP q", "Drops TCP q"]


def _policy(op):
    """The scheduling policy in an operator's line (written as "mode" before 2026-11-11)."""
    return (op or {}).get("policy") or (op or {}).get("mode")


def _row(rid, params, m, policy):
    m = m or {}
    w = (params or {}).get("weightUdp", m.get("weight_udp"))
    num = lambda v: f"{v / 1e6:,.1f}" if isinstance(v, (int, float)) else "–"
    cnt = lambda v: f"{int(v):,}" if isinstance(v, (int, float)) else "–"
    return {"Run": rid, "UDP weight": "–" if w is None else f"{w:g}", "UDP offered": (params or {}).get("udpRate") or "–",
            "Scheduling policy": policy or "–", "UDP Mbps": num(m.get("udp_goodput_bps")), "TCP Mbps": num(m.get("tcp_goodput_bps")),
            "Link use": _pct(m.get("link_util")), "UDP loss": _pct(m.get("udp_loss_frac")),
            "Drops UDP q": cnt(m.get("drops_band0")), "Drops TCP q": cnt(m.get("drops_band1"))}


def _program(i, rid, ts, params, m, error, policy, base, **extra):
    good = bool(m) and not error
    metrics = {"validity": 1 if good else 0, **(m or {})}
    if error:
        metrics["error"] = error
    sol = None
    if good:
        sol = {"run_id": rid, "params": params or {}, "metrics": m, "series": _series(base, rid), "policy": policy}
    p = {"id": f"x{i:03d}", "iteration": i, "timestamp": ts, "parent_id": None, "generation": 0, "metrics": metrics,
         "changes": f"run {rid}: {_params_text(params)}", "node_id": None, "island": None, "migrant": False,
         "reasoning": None, "notebook_entry": None, "lesson": None, "fail_kind": None if good else "simulation failed",
         "lookups": [], "cull_copy_of": None, "island_epoch": None, "copy_of": None, "solution": sol, "code": "",
         "no_program": True, "eval_review": None, "failure": None, "error_text": error, "answer_cut_off": False,
         "headline": "measured" if good else "failed", "headline_cls": "", "facts": [], "row": _row(rid, params, m, policy)}
    p.update(extra)
    return p


def _loop_parts(sid):
    """A session's ledger joined up: per experiment its hypothesis, evidence, verdict, thinking and timing."""
    D = _load(sid)
    led = D["ledger"]
    by_id = {r["id"]: r for r in led}
    verdict_for = {}
    for r in led:
        if r["type"] == "verdict":
            verdict_for[(r.get("body") or {}).get("for")] = r
    exps = []
    for k, r in enumerate(led):
        if r["type"] != "evidence":
            continue
        x = by_id.get(r.get("parent")) or {}
        h = by_id.get(x.get("parent")) or {}
        if h.get("type") != "hypothesis":
            h = {}
        # the thinking of the call that produced this experiment: the last scratch record of the same turn
        think = [s for s in led if s["type"] in ("draft", "scratch") and s["turn"] == r["turn"]]
        # the whole turn: from the last record before it to the evidence record
        before = [s for s in led[:k] if s["turn"] < r["turn"]]
        t0, t1 = _epoch(before[-1].get("ts")) if before else None, _epoch(r.get("ts"))
        exps.append({"e": r, "x": x, "h": h, "v": verdict_for.get(h.get("id")), "think": think[-1] if think else None,
                     "calls": len(think), "seconds": (t1 - t0) if t0 and t1 else None})
    return led, exps


def _loop_main(sid):
    D = _load(sid)
    led, exps = _loop_parts(sid)
    programs, times = [], {}
    for i, q in enumerate(exps, 1):
        e, x, h, v = q["e"], q["x"], q["h"], q["v"]
        eb, xb, hb, vb = e.get("body") or {}, x.get("body") or {}, h.get("body") or {}, (v or {}).get("body") or {}
        rid = eb.get("run_id")
        idx = D["index"].get(rid) or {}
        op = D["oper"].get(rid) or {}
        m = idx.get("metrics") or {k: val for k, val in eb.items() if k not in ("run_id", "pass_if", "error")}
        params = idx.get("params") or xb.get("params")
        result = vb.get("result")
        facts = []
        if hb:
            facts.append([f"Hypothesis {h['id']}", hb.get("text") or ""])
            if hb.get("prediction"):
                facts.append(["Prediction", hb["prediction"]])
        if eb.get("note"):   # E0: the harness's own baseline run before turn 1
            facts.append(["What this is", eb["note"]])
        else:
            facts.append(["Decision rule (stated before the simulations)", xb.get("pass_if") or eb.get("pass_if") or "–"])
        if xb.get("clamped"):
            facts.append(["Clamped to the allowed range", ", ".join(f"{k}: asked {a} → used {b}" for k, (a, b) in xb["clamped"].items())])
        facts.append([f"Measured (run {rid})", eb.get("error") or _measured(m)])
        if v:
            facts.append([f"Verdict {v['id']} (the model's own, turn {v['turn']})", f"{result}: {vb.get('because') or ''}"])
            if vb.get("next"):
                facts.append(["What it planned next", vb["next"]])
        else:
            facts.append(["Verdict", "none: a baseline has no hypothesis to judge" if eb.get("note") else "none: the loop stopped before the model judged this hypothesis"])
        tb = (q["think"] or {}).get("body") or {}
        p = _program(i, rid, _epoch(e.get("ts")), params, m if "udp_goodput_bps" in m else None, eb.get("error"), _policy(op), D["base"],
                     reasoning=tb.get("text") or tb.get("reasoning") or None,
                     headline=result or ("baseline" if eb.get("note") else "not judged"), headline_cls=result or "pending", facts=facts,
                     changes=f"{h.get('id', 'no hypothesis')} · turn {e['turn']} · run {rid}: {_params_text(xb.get('params') or params)}")
        if isinstance(op.get("seconds"), (int, float)):
            p["metrics"]["eval_time"] = op["seconds"]
        if q["seconds"] is not None:
            times[p["id"]] = q["seconds"]
        programs.append(p)
    running = _running(sid)
    last = programs[-1] if programs else None
    scratch = [r for r in led if r["type"] in ("draft", "scratch")]
    model = ((scratch[-1].get("body") or {}).get("model") if scratch else None) or "?"
    status = {"running": running,
              "last_completed": {"iteration": last["iteration"] if last else 0, "seconds": times.get(last["id"], 0) if last else 0,
                                 "at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((last or {}).get("timestamp") or time.time()))},
              "current": None, "server_now": time.time(), "planned_last": None, "completed": len(programs),
              "last_activity": _mtime(D["ledger_path"]) or time.time()}
    fixed = D["manifest"].get("fixed") or {}
    setup = {"model": model, "thinking": bool(scratch), "thinking_budget": None,
             "thinking_note": ("<b>on</b> · each answer may use up to 8,000 tokens, thinking included" if scratch
                               else "<b>off</b> (no reasoning recorded)"),
             "feedback": False, "feedback_note": "none: the model judges its own hypotheses against the decision rule it stated before the simulations",
             "search": False, "evaluator": "ns-3.49 simulation of the two-hosts scenario; the harness writes the evidence, never the model",
             "islands": None, "migration_interval": None, "migration_rate": None, "island_fix": None, "island_isolation": None,
             "cull_hours": None, "notebook": False, "history": False, "backend": "vllm", "old_server": False, "max_code": None,
             "changes": [],
             "references": "Fixed: " + ", ".join(f"{k} {v}" for k, v in fixed.items()) + ". No score: the model chooses what 'performance' means."}
    return {"status": status, "programs": programs, "times": times, "limits": {"llm": 1800, "eval": 600},
            "failures": [], "failure_breakdown": [], "feedback": {}, "thinking": {}, "review": False, "reviewer": None,
            "summaries": False, "setup": setup, "gpus": "viewer", "exchanges": [], "memory": {}, "research": _research(led, exps),
            "page": _raw(sid)}


def _research(led, exps):
    """The ledger as the page's research story: one entry per hypothesis, then the turns that produced no step."""
    if not led:
        return None
    ideas, n = [], 0
    for q in exps:
        n += 1
        e, x, h, v = q["e"], q["x"], q["h"], q["v"]
        eb, xb, hb, vb = e.get("body") or {}, x.get("body") or {}, h.get("body") or {}, (v or {}).get("body") or {}
        rows = ([] if eb.get("note") else [["Decision rule (stated before the simulations)", xb.get("pass_if") or "–"]]) + [["Measured", eb.get("error") or _measured(eb)]]
        if v:
            rows.append([f"Why ({v['id']}, turn {v['turn']})", vb.get("because") or "–"])
            if vb.get("next"):
                rows.append(["Planned next", vb["next"]])
        w = (xb.get("params") or {}).get("weightUdp")
        ideas.append({"id": h.get("id") or x.get("id") or e.get("id"), "kind": f"turn {e['turn']}", "title": "",
                      "hypothesis": hb.get("text") or eb.get("note") or "(experiment without a new hypothesis)", "prediction": hb.get("prediction"),
                      "verdict": vb.get("result"),
                      "verdict_title": "the model's own verdict, read against its decision rule; not computed by code",
                      "pending_text": "BASELINE" if eb.get("note") else "NO VERDICT (LOOP STOPPED)", "rows": rows,
                      "experiments": [{"id": n, "valid": "error" not in eb,
                                       "label": f"#{n} · run {eb.get('run_id')} · UDP weight {w if w is not None else eb.get('weight_udp', '?')}",
                                       "title": eb.get("error") or _measured(eb)}]})
    notes = []
    for r in led:
        b = r.get("body") or {}
        if r["type"] == "malformed":
            notes.append({"id": f"turn {r['turn']}", "status": "no usable answer",
                          "text": f"{b.get('error')}" + (" (the answer was cut off; its text is in the ledger)" if b.get("content") else "")})
        elif r["type"] == "note":
            asked = ", ".join(f"{q.get('tool')}({', '.join(str(a) for a in (q.get('args') or {}).values())})" for q in b.get("requests") or [])
            notes.append({"id": f"turn {r['turn']}", "status": "asked for information" if asked else "note",
                          "text": (f"Called {asked}. " if asked else "") + (b.get("observations") or b.get("text") or "")})
    turns = max(r["turn"] for r in led)
    first, last_ = (led[0].get("ts") or "").replace("T", " ")[:16], (led[-1].get("ts") or "").replace("T", " ")[:16]
    judged = sum(1 for i in ideas if i["verdict"])
    return {"sub": "Each turn the model reads the whole ledger and either states a hypothesis with a prediction and an experiment "
                   "(with a decision rule stated before the simulations), or gives a verdict on an earlier hypothesis. The harness runs the "
                   "experiment and writes the evidence. The verdicts are the model's own reading. Click an experiment to open it.",
            "exp_label": "Experiment", "notes_title": "Turns without a hypothesis",
            "notes_sub": "Every other turn in the ledger: tool requests, and answers the harness could not use.",
            "cycles": [{"cycle": 1, "title": f"Ledger · {turns} turns · {len(ideas)} hypotheses tested, {judged} judged · {first} → {last_}",
                        "status": "", "ideas": ideas}],
            "notes": notes, "findings": [], "strategist_calls": []}


# ---------- the ordered page: built in the browser by adrs_view.js (TH_DATA.build) from the raw records sent here,
# the same code that the harness's own static page (viewer/index.html) runs on the files directly
KNOB = {"weightUdp": "UDP share of the link", "udpRate": "UDP offered rate", "queuePkts": "Queue length", "tcpVariant": "TCP congestion control",
        "duration": "Measured time", "seed": "Random seed"}
KNOB_UNIT = {"queuePkts": " packets", "duration": " s"}


def _knob_value(k, v):
    return f"{v:g}" if isinstance(v, float) else f"{v}{KNOB_UNIT.get(k, '')}"


def _raw(sid=None):
    D = _load(sid)
    try:
        objects = json.load(open(os.path.join(HERE, "objects.json")))   # the network diagram's object list (viewer only)
    except (OSError, ValueError):
        objects = None
    return {"sig": f"{sid}/{len(D['ledger'])}/{len(D['index'])}",
            "raw": {"ledger": D["written"], "index": list(D["index"].values()), "oper": list(D["oper"].values()), "manifest": D["manifest"],
                    "series": {rid: _series(D["base"], rid) for rid in D["index"]}, "running": bool(sid) and _running(sid), "objects": objects}}


def _check_ids():
    return list(_load()["index"])


def _checks_main():
    D = _load()
    programs, times = [], {}
    for i, rid in enumerate(_check_ids(), 1):
        idx, op = D["index"][rid], D["oper"].get(rid) or {}
        ts = _mtime(os.path.join(BUILD1, rid, "metrics.json")) or None
        m = idx.get("metrics") or {}
        stage = f"build stage {op['stage']}" if op.get("stage") is not None else "harness test"
        p = _program(i, rid, ts, idx.get("params"), m, None, _policy(op), BUILD1,
                     facts=[["What this is", f"An operator check ({stage}), not an AI experiment."],
                            ["Scheduling policy", _policy(op) or "–"],
                            ["Settings", ", ".join(f"{KNOB.get(k, k)} {_knob_value(k, v)}" for k, v in (idx.get("params") or {}).items() if k in KNOB) or "all defaults"],
                            [f"Measured (run {rid})", _measured(m)]])
        if isinstance(op.get("seconds"), (int, float)):
            p["metrics"]["eval_time"] = times[p["id"]] = op["seconds"]
        programs.append(p)
    N = len(programs)
    last = programs[-1] if programs else None
    at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((last or {}).get("timestamp") or time.time()))
    status = {"running": False, "last_completed": {"iteration": N, "seconds": 0, "at": at}, "current": None,
              "server_now": time.time(), "planned_last": N, "completed": N,
              "last_activity": (last or {}).get("timestamp") or time.time()}
    setup = {"model": "none (operator checks)", "no_ai": True, "ai_type": "No AI in these runs", "thinking": False,
             "thinking_budget": None, "thinking_note": "no AI in these runs", "feedback": False, "feedback_note": "none",
             "search": False, "evaluator": "ns-3.49 simulation of the two-hosts scenario", "islands": None,
             "migration_interval": None, "migration_rate": None, "island_fix": None, "island_isolation": None,
             "cull_hours": None, "notebook": False, "history": False, "backend": "cpu", "old_server": False, "max_code": None,
             "changes": [], "hardware_note": "CPU only: each run is one ns-3 simulation",
             "references": "Simulations the operator ran while building the harness (both scheduling policies). No score."}
    return {"status": status, "programs": programs, "times": times, "limits": {"llm": 0, "eval": 600}, "failures": [],
            "failure_breakdown": [], "feedback": {}, "thinking": {}, "review": False, "reviewer": None, "summaries": False,
            "setup": setup, "gpus": [], "exchanges": [], "memory": {}, "page": _raw()}


def _intro_svg():
    """Two hosts and one wire; the sender's scheduler splits the wire between a UDP queue and a TCP queue."""
    return ('<svg viewBox="0 0 120 120" role="img" aria-label="Two hosts joined by one link; the sender splits the link between UDP and TCP">'
            '<rect x="6" y="38" width="34" height="44" rx="5" fill="none" stroke="var(--text-primary)" stroke-width="2"/>'
            '<rect x="88" y="38" width="26" height="44" rx="5" fill="none" stroke="var(--text-primary)" stroke-width="2"/>'
            '<rect x="12" y="46" width="22" height="10" rx="2" fill="var(--series-1)"/><rect x="12" y="64" width="22" height="10" rx="2" fill="var(--series-2)"/>'
            '<line x1="40" y1="57" x2="88" y2="57" stroke="var(--series-1)" stroke-width="5"/><line x1="40" y1="63" x2="88" y2="63" stroke="var(--series-2)" stroke-width="5"/>'
            '<text x="23" y="32" font-size="9" text-anchor="middle" fill="var(--text-secondary)">sender</text>'
            '<text x="101" y="32" font-size="9" text-anchor="middle" fill="var(--text-secondary)">receiver</text>'
            '<text x="64" y="50" font-size="8" text-anchor="middle" fill="var(--text-secondary)">UDP</text>'
            '<text x="64" y="76" font-size="8" text-anchor="middle" fill="var(--text-secondary)">TCP</text></svg>')


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def task_entry():
    D = _load()
    task = D["manifest"].get("task") or "Two hosts, one link."
    return {
        "name": NAME, "title": "Two hosts, one link (ns-3 hypothesis loop)", "metric": "combined_score",
        "metric_label": "Result", "decimals": 3, "no_score": True, "no_memory": True, "no_files": True, "unit": "experiment", "custom_page": True,
        "pop_simple": True, "think_title": "What the AI thought before proposing this experiment",
        "time_labels": ["AI thinking and answer", "Simulation run time"],
        "columns": COLUMNS,
        "easy": {"name": "none", "value": 0.0, "about": "This task has no score.", "solution": None},
        "target": {"name": "none", "value": 1.0, "about": "This task has no score.", "solution": None},
        "zoom_min": 0.0, "artifact": "run", "solution_label": "simulation run",
        "task_html": _intro_svg() + f'<div><p class="lead">{_esc(task)}</p>'
                     "<ul><li>The AI cannot see inside the system. It works through a ledger: hypothesis → prediction → "
                     "experiment with a decision rule stated first → evidence from the simulator → verdict.</li>"
                     "<li><b>No score:</b> the AI must say what 'performance' means, so this page shows measurements and "
                     "verdicts, not a best-so-far.</li></ul></div>",
        "invalid_note": "The simulation did not return measurements.",
        "runs": len(_sessions()) + (1 if _check_ids() else 0)}


def list_runs_main():
    out = []
    for sid in _sessions():
        led, exps = _loop_parts(sid)
        if not led:
            continue
        scratch = [r for r in led if r["type"] in ("draft", "scratch")]
        out.append({"name": sid, "mtime": _mtime(_load(sid)["ledger_path"]), "iterations": len(exps), "running": _running(sid),
                    "model": ((scratch[-1].get("body") or {}).get("model") if scratch else None) or "?", "backend": "vllm",
                    "switches": ["thinking"] if scratch else [], "started": (led[0].get("ts") or "").replace("T", " ")[:16] or None})
    ids = _check_ids()
    if ids:
        mt = max(_mtime(os.path.join(BUILD1, rid)) for rid in ids)
        out.append({"name": CHECKS, "mtime": mt, "iterations": len(ids), "running": False, "model": "none (operator checks)",
                    "backend": "cpu", "switches": ["no AI"],
                    "started": time.strftime("%Y-%m-%d %H:%M", time.localtime(min(_mtime(os.path.join(BUILD1, rid)) for rid in ids)))})
    return out


def api_run_main(name):
    if name == LOOP:   # links made before sessions had their own folders: the newest session
        name = (_sessions() or [None])[-1]
    if name in _sessions() and _load(name)["ledger"]:
        return _loop_main(name)
    if name == CHECKS and _check_ids():
        return _checks_main()
    return None


def memory_main(name):
    return {"parts": {}, "chars_per_token": 2.65, "limits": {}, "iterations": [], "current": None}


def request_main(name, it):
    return None


def compare_main():
    return []   # nothing to compare: no score


def extend_overview(ov):
    runs = [{**r, "task": NAME, "best": None, "planned": r["iterations"]} for r in list_runs_main()]
    return {"tasks": list(ov.get("tasks", [])) + [{"name": NAME, "title": task_entry()["title"], "target": None}],
            "runs": list(ov.get("runs", [])) + runs}


def trace_file(rel):
    """A file of the operator's event recordings (~/project/trace/): index.json or <name>/events.csv."""
    base = os.path.realpath(os.path.join(ROOT, "trace"))
    path = os.path.realpath(os.path.join(base, rel))
    if not path.startswith(base + os.sep) or not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def view_js():
    return open(os.path.join(HERE, "adrs_view.js"), "rb").read()
