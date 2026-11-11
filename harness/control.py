"""The operator's control server: the viewer's files, plus the few things the operator may start from the page.
It replaces the plain file server. Start it with:  python3 harness/control.py   (the page is http://127.0.0.1:8600/viewer/)

  GET  any file        the project's files, read-only, exactly as before
  GET  /api/status     what is running, the last lines of the session's output, "briefs" (the ids in briefs/) and
                       "sessions": every session folder (id, brief, records, experiments, first and last time, policy, model, running,
                       checks held and failed, and from checks/: the score in short and the reviewer's ticks and sign-off)
  GET  /api/sessions   that list alone
  POST /api/run        {params, policy, brief}: one operator simulation -> checks/op-<timestamp>/, returns its metrics.
                       The brief (default two-hosts-open) gives the fixed settings and the ranges.
  POST /api/session    {brief, budget, draft, max_tokens, temperature, policy, baseline, session}: starts loop.py with those flags,
                       returns the session id (budget = simulations). Up to six loops run side by side. policy "random": the
                       server chooses share or cap and lists the session in checks/random.json; its policy is then left out
                       of the session list until the session is scored.
                       Without "session" it is a new session (the next id sNNN) on the named brief (default two-hosts-open;
                       budget defaults to the brief's limit); with the id of an existing session it continues that one.
  POST /api/stop       {session}: stops that session if it was started here (no session named: the newest started here)
  POST /api/sweep      {brief, policy, grid: {knob: [values]}} (or {add_to: <sweep id>, grid, rerun}: more combinations
                       into an existing sweep's table): every combination of the grid, run by the built program
                       directly, at most 64 at a time -> checks/sweeps/<id>/table.csv (one row per simulation) and
                       status.json (progress). One sweep at a time. Returns the sweep's status, with its id.
  GET  /api/sweep/<id> that sweep's status.json
  POST /api/sweep/<id>/stop   stops it; the rows finished so far stay in the table
  POST /api/review     {session, item, tick, note}: the reviewer's tick and note for one item of a session's page
                       -> checks/reviews/<session>.json (read back by the page as a file)
  POST /api/brief      {brief}: saves a NEW brief as briefs/<id>.json after the same check loop.py makes (tools.check_brief).
                       An id that already exists is refused: a brief is never overwritten.

Who writes what (the write-ownership rule):
  loop.py      its own session's folder, sessions/<id>/: session.json, ledger.jsonl, and runs/ through tools.run. Nothing else writes
               there, and no tool can read outside it. It also appends one line per run to checks/operator.jsonl
               (session, run, policy, seconds), which no tool reads. "policy" is the scheduling policy: how the scheduler
               divides the link, share or cap (records written before 2026-11-11 call it "mode"; both are read).
  control.py   checks/: checks/op-<timestamp>/ (one operator run), checks/control.jsonl (the list of those runs),
               checks/sessions/<id>.log (a session's terminal output), checks/sweeps/<id>/ (a sweep's table and
               status), checks/reviews/<session>.json (the reviewer's ticks and notes); and briefs/<id>.json, new files only.
               It starts and stops loop.py and does nothing else.
  the viewer   nothing. Its Control page only calls the POST endpoints above.
An operator run is made by the built program directly, never by tools.run, so it never reaches a session's folder: no
tool the model has can see it. The scheduling policy reaches the simulation as the environment variable TWOHOSTS_SCHED only; the model never sees it.

Who may call it. The server listens on 127.0.0.1 only (there is no option to change that). This machine is shared, so
that alone would let any local user start runs; a POST is therefore accepted only when the connection was opened by a
process of the user who runs this server (an SSH tunnel of that user counts), and only as application/json from this
page (so no other web page open in the same browser can call it). Parameters go through tools.clamp, like the model's.
Briefs (briefs/<id>.json) are the operator's: written by hand or saved from the page's brief editor.
Python standard library only."""
import argparse, csv, http.server, itertools, json, os, random, re, shutil, signal, subprocess, sys, threading, time
from pathlib import Path
import tools

ROOT, H, CHECKS = tools.ROOT, tools.HARNESS, tools.ROOT / "checks"
BIN = tools.NS3 / "build/scratch/two-hosts/ns3.49-two-hosts-optimized"
LOOP = [sys.executable, str(H / "loop.py")]
HOST, PORT = "127.0.0.1", 8600
LOCK, RUN_LOCK = threading.Lock(), threading.Lock()
SESSION = {}  # the newest session started here, if any: id, proc, flags, started, log (the older control page shows this one)
STARTED = {}  # every session started here, by id; MAX_LOOPS: most loops running at the same time, wherever they were started
MAX_LOOPS = 6
CACHE = {}    # session id -> (file times, its row in /api/sessions)
SWEEP = {}    # the sweep running here, if any: id, thread, stop
PARALLEL, SWEEP_MAX = 64, 5000  # simulations of a sweep running at the same time; most simulations one sweep may ask for


class Refused(Exception):
    def __init__(self, code, text):
        self.code, self.text = code, text


def peer_uid(peer_port, port):
    """The user id that owns the other end of a local connection, from /proc/net/tcp; None if it cannot be found."""
    local, remote = f"0100007F:{peer_port:04X}", f"0100007F:{port:04X}"
    for line in Path("/proc/net/tcp").read_text().splitlines()[1:]:
        f = line.split()
        if f[1] == local and f[2] == remote:
            return int(f[7])
    return None


def other_loops():
    """The session ids of every loop.py of this user that is running and was not started here ("?" for one whose command
    does not name its session). Sessions started from terminals can run side by side."""
    mine, out = {x["proc"].pid for x in STARTED.values() if x["proc"].poll() is None}, []
    for p in Path("/proc").iterdir():
        try:
            if not p.name.isdigit() or int(p.name) in mine or p.stat().st_uid != os.getuid():
                continue
            args = (p / "cmdline").read_bytes().split(b"\0")
            if any(a.endswith(b"loop.py") and (Path(os.readlink(p / "cwd")) / a.decode()).resolve() == (H / "loop.py").resolve() for a in args[1:3]):
                names = [a.decode(errors="replace") for a in args]
                out.append(names[names.index("--session") + 1] if "--session" in names[:-1] else "?")
        except OSError:
            continue
    return out


def other_loop():
    """One of other_loops(), or None. Only one loop at a time is started from this server."""
    return (other_loops() or [None])[0]


def sessions():
    """One row per folder in sessions/, oldest first, read from the session's own files and checks/operator.jsonl."""
    lines = lambda p: [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
    policy = {}
    for r in lines(CHECKS / "operator.jsonl"):
        if r.get("session"):
            policy[r["session"]] = r.get("policy", r.get("mode"))
    here = {i for i, x in STARTED.items() if x["proc"].poll() is None}
    others = set(other_loops())
    dirs = sorted(p for p in tools.SESSIONS.iterdir() if p.is_dir() and re.fullmatch(r"[A-Za-z0-9_-]{1,40}", p.name)) if tools.SESSIONS.is_dir() else []
    if "?" in others and dirs:  # a loop started from a terminal without --session made the newest folder
        others.add(max(dirs, key=lambda p: p.stat().st_mtime).name)
    hidden = set(json.loads((CHECKS / "random.json").read_text())) if (CHECKS / "random.json").is_file() else set()  # sessions whose scheduling policy the harness chose
    out = []
    for d in dirs:
        led, idx, score, review = d / "ledger.jsonl", d / "runs/index.json", CHECKS / "scores" / f"{d.name}.json", CHECKS / "reviews" / f"{d.name}.json"
        sig = tuple(p.stat().st_mtime if p.exists() else 0 for p in (led, idx, d / "session.json", score, review))
        if CACHE.get(d.name, (None,))[0] != sig:
            recs = lines(led)
            drafts = [r for r in recs if r["type"] in ("draft", "scratch")]
            meta = json.loads((d / "session.json").read_text()) if (d / "session.json").is_file() else {}
            checks = [(r.get("body") or {}).get("result") for r in recs if r["type"] == "check"]
            sc = json.loads(score.read_text()) if score.is_file() else None
            marks = json.loads(review.read_text()) if review.is_file() else {}
            CACHE[d.name] = (sig, {"id": d.name, "brief": meta.get("brief"), "records": len(recs), "runs": len(lines(idx)),
                "experiments": sum(r["type"] == "evidence" and r["id"] != "E0" for r in recs),
                "simulations": sum(r["type"] == "simulation" and r["id"] != "S0" and not (r.get("body") or {}).get("same_as") for r in recs),  # run, as the budget counts them
                "allowed": ((meta.get("given") or {}).get("limits") or {}).get("simulations") or (meta.get("flags") or {}).get("budget"),
                "turns": max([r["turn"] for r in recs], default=0), "held": checks.count("held"), "failed": checks.count("failed"),
                "started": recs[0].get("ts") if recs else None, "last": recs[-1].get("ts") if recs else None,
                "model": (drafts[-1]["body"].get("model") if drafts else None), "how": meta.get("how"), "report": meta.get("report"), "left_open": meta.get("left_open"),
                "has_report": any(r["type"] == "report" for r in recs),
                "done": any(r["type"] == "report" or (r["type"] == "note" and (r.get("body") or {}).get("text") == "model declared done") for r in recs),
                # operator-only, from checks/: the score in short, and the reviewer's ticks and sign-off
                "score": sc and {"gap": sc.get("gap_on_target"), "part": sc.get("gap_as_part_of_best"), "target": (sc.get("goal") or {}).get("target"),
                                 "holds": all((sc.get("conditions_hold_at_the_recommendation") or {}).values())},
                "review": {"n": len(marks), "ticked": sorted(k for k, m in marks.items() if m.get("tick") and k != "signoff"),
                           "signed": {"name": marks["signoff"].get("note"), "at": marks["signoff"].get("at")} if "signoff" in marks else None}})
        row = CACHE[d.name][1]
        secret = d.name in hidden and not row["score"]  # a policy the harness chose is shown only once the session is scored
        out.append({**row, "policy": None if secret else policy.get(d.name), "policy_hidden": secret, "running": d.name in here or d.name in others, "stoppable": d.name in here})
    return out


def tail(path, n=600):
    try:
        return Path(path).read_text(errors="replace")[-n:]
    except OSError:
        return ""


def status():
    s = None
    if SESSION:
        rc = SESSION["proc"].poll()
        s = {"id": SESSION["id"], "pid": SESSION["proc"].pid, "running": rc is None, "returncode": rc, "flags": SESSION["flags"],
             "started": SESSION["started"], "output": tail(SESSION["log"])}
    count = lambda p: sum(1 for l in p.open() if l.strip()) if p.exists() else 0
    return {"control": True, "session": s, "other_loop": other_loop(), "run_busy": RUN_LOCK.locked(),
            "sessions": sessions(), "briefs": sorted(p.stem for p in tools.BRIEFS.glob("*.json")),
            "operator_runs": count(CHECKS / "control.jsonl"),
            "sweeps": sorted(p.name for p in (CHECKS / "sweeps").iterdir() if (p / "status.json").is_file()) if (CHECKS / "sweeps").is_dir() else []}


def operator_run(body):
    """One simulation with the operator's settings, by the built program directly, into checks/op-<timestamp>/."""
    params, policy = body.get("params") or {}, body.get("policy", body.get("mode", "share"))
    try:
        brief = tools.load_brief(body.get("brief", tools.DEFAULT_BRIEF))
    except ValueError as e:
        raise Refused(400, str(e))
    if policy not in ("share", "cap") or not isinstance(params, dict) or set(params) - set(brief["knobs"]) - set(brief["system"]):
        raise Refused(400, "params must be settings of the brief and the scheduling policy must be share or cap")
    try:
        clean, clamps = tools.clamp(params, brief)
    except (ValueError, TypeError) as e:
        raise Refused(400, f"bad parameter value: {e}")
    if not RUN_LOCK.acquire(blocking=False):
        raise Refused(409, "an operator run is already in progress")
    try:
        rid = "op-" + time.strftime("%Y%m%d-%H%M%S")
        out = CHECKS / rid
        out.mkdir(parents=True)
        args = [f"--{k}={v}" for k, v in tools.options(clean, brief).items()] + [f"--out={out}"]
        t0 = time.time()
        try:
            p = subprocess.run([str(BIN)] + args, cwd=out, env={"LD_LIBRARY_PATH": str(tools.NS3 / "build/lib"), "TWOHOSTS_SCHED": policy}, capture_output=True, text=True, timeout=tools.RUN_TIMEOUT)
            code, err = p.returncode, (p.stderr or p.stdout)[-800:]
        except subprocess.TimeoutExpired:
            code, err = "timeout", f"no result after {tools.RUN_TIMEOUT} s"
        seconds = round(time.time() - t0, 1)
        (out / "command.txt").write_text(f"TWOHOSTS_SCHED={policy} two-hosts {' '.join(args)}\nexit {code}, {seconds} s\n")
        if code != 0 or not (out / "metrics.json").exists():
            raise Refused(500, f"the simulation failed (exit {code}): {err}")
        rec = {"id": rid, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "brief": brief["id"], "policy": policy, "seconds": seconds, "clamped": clamps,
               "params": json.loads((out / "params.json").read_text()), "metrics": json.loads((out / "metrics.json").read_text())}
        with (CHECKS / "control.jsonl").open("a") as f:
            f.write(json.dumps(rec) + "\n")
        return rec
    finally:
        RUN_LOCK.release()


def save_brief(body):
    """A brief from the page's editor, written as a new file briefs/<id>.json if tools.check_brief accepts it."""
    b = body.get("brief")
    bid = b.get("id") if isinstance(b, dict) else None
    if not isinstance(bid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,59}", bid):
        raise Refused(400, "the brief needs an id of 2 to 60 characters: lower-case letters, digits, - and _")
    path = tools.BRIEFS / f"{bid}.json"
    if path.exists():
        raise Refused(409, f"a brief named {bid} already exists. A brief is never overwritten: choose another id")
    knobs = b.get("knobs") if isinstance(b.get("knobs"), dict) else {}
    b = {**{k: b.get(k) for k in ("id", "task", "description", "system")},   # only the fields a brief has, in the usual order
         "knobs": {k: {x: s[x] for x in ("min", "max", "choices", "default", "meaning") if x in s} if isinstance(s, dict) else s for k, s in knobs.items()},
         "goal": b.get("goal"), "limits": b.get("limits")}
    try:
        tools.check_brief(b, bid)
    except ValueError as e:
        raise Refused(400, str(e))
    text = json.dumps(b, indent=2)
    for s in b["knobs"].values():  # one knob per line, like the briefs written by hand
        text = text.replace(json.dumps(s, indent=2).replace("\n", "\n    "), json.dumps(s))
    tools.BRIEFS.mkdir(exist_ok=True)
    try:
        with path.open("x") as f:
            f.write(text + "\n")
    except FileExistsError:
        raise Refused(409, f"a brief named {bid} already exists. A brief is never overwritten: choose another id")
    return {"saved": bid, "file": f"briefs/{bid}.json"}


def write_status(folder, st):
    tmp = folder / "status.json.tmp"
    tmp.write_text(json.dumps(st, indent=1) + "\n")
    tmp.replace(folder / "status.json")


def run_sweep(folder, brief, policy, combos, st, stop, kept=()):
    """Every combination, at most PARALLEL at a time, by the built program directly. One row per simulation in
    table.csv, in the order they finish (sorted by number at the end); a run's own folder is removed once its row is written.
    kept: the rows of the table that stay as they are when combinations are added to an existing sweep."""
    cols = ["i", *tools.OPTIONS, *tools.MANIFEST["outputs"], "seconds", "error"]
    rows, running, nxt, t_start, first = list(kept), {}, 0, time.time(), len(kept)
    with (folder / "table.csv").open("w", newline="") as f:
        out = csv.DictWriter(f, cols)
        out.writeheader()
        out.writerows(rows)
        while running or (nxt < len(combos) and not stop.is_set()):
            while nxt < len(combos) and len(running) < PARALLEL and not stop.is_set():
                opts, d = tools.options(combos[nxt], brief), folder / "runs" / str(nxt)
                d.mkdir(parents=True)
                proc = subprocess.Popen([str(BIN)] + [f"--{k}={v}" for k, v in opts.items()] + [f"--out={d}"], cwd=d, stdout=subprocess.DEVNULL, stderr=(d / "stderr.txt").open("w"),
                                        env={"LD_LIBRARY_PATH": str(tools.NS3 / "build/lib"), "TWOHOSTS_SCHED": policy})
                running[nxt] = (proc, d, time.time(), opts)
                nxt += 1
            time.sleep(0.2)
            for i, (proc, d, t0, opts) in list(running.items()):
                if stop.is_set() and proc.poll() is None:
                    proc.kill()
                if proc.poll() is None:
                    continue
                row = {"i": first + i, **opts, "seconds": round(time.time() - t0, 1)}
                if proc.returncode == 0 and (d / "metrics.json").exists():
                    row.update(json.loads((d / "metrics.json").read_text()))
                else:
                    row["error"] = "stopped" if stop.is_set() else (" ".join((d / "stderr.txt").read_text().split())[-300:] or f"exit {proc.returncode}")
                    st["failed"] += 1
                rows.append(row)
                out.writerow(row)
                f.flush()
                shutil.rmtree(d, ignore_errors=True)
                del running[i]
                st.update(done=len(rows), running=len(running), seconds=round(time.time() - t_start, 1))
                write_status(folder, st)
    with (folder / "table.csv").open("w", newline="") as f:
        out = csv.DictWriter(f, cols)
        out.writeheader()
        out.writerows(sorted(rows, key=lambda r: r["i"]))
    shutil.rmtree(folder / "runs", ignore_errors=True)
    st.update(state="stopped" if stop.is_set() else "done", running=0, ended=time.strftime("%Y-%m-%dT%H:%M:%S"), seconds=round(time.time() - t_start, 1))
    write_status(folder, st)


def start_sweep(body):
    """A grid of knob values for one brief and one scheduling policy; every combination is one simulation.
    With "add_to": <sweep id> the grid's combinations that the sweep does not have yet are added to its table (same brief
    and policy); with "rerun": true as well, every combination the table already has is run again too (after the
    simulator changed), so the whole table comes from one build. The table as it was is kept beside it."""
    old = None
    if body.get("add_to") is not None:
        old = sweep_status(str(body["add_to"]))
        if old["state"] == "running":
            raise Refused(409, f"sweep {old['id']} is still running")
        body = {**body, "brief": old["brief"], "policy": old["policy"]}
    policy, grid = body.get("policy", "share"), body.get("grid")
    try:
        brief = tools.load_brief(body.get("brief", tools.DEFAULT_BRIEF))
    except ValueError as e:
        raise Refused(400, str(e))
    if policy not in ("share", "cap") or not isinstance(grid, dict) or not grid or not all(isinstance(v, list) and v for v in grid.values()):
        raise Refused(400, "a sweep needs policy (share or cap) and grid: {knob: [values, ...]} with at least one value per knob")
    if set(grid) - set(brief["knobs"]):
        raise Refused(400, f"the grid names settings that are not knobs of the brief: {', '.join(sorted(set(grid) - set(brief['knobs'])))}")
    for k, values in grid.items():
        for v in values:
            try:
                clamps = tools.clamp({k: v}, brief)[1]
            except (ValueError, TypeError) as e:
                raise Refused(400, f"{k}={v!r} cannot be read: {e}")
            if clamps:
                raise Refused(400, f"{k}={v!r} is outside what the brief allows")
    combos, kept = [dict(zip(grid, c)) for c in itertools.product(*grid.values())], []
    if old:
        knobs, same = brief["knobs"], lambda c: tools.same(tools.options(c, brief))
        value = lambda k, v: v if "choices" in knobs[k] or isinstance(knobs[k]["min"], str) else int(float(v)) if isinstance(knobs[k]["min"], int) and isinstance(knobs[k]["max"], int) else float(v)
        have = [{**r, "i": int(r["i"])} for r in csv.DictReader((CHECKS / "sweeps" / old["id"] / "table.csv").open()) if not r.get("error")]
        earlier = [{k: value(k, r[k]) for k in knobs} for r in have]
        seen = {same(c) for c in earlier}
        new = [c for c in combos if same(c) not in seen]
        combos, kept = (earlier + new, []) if body.get("rerun") else (new, have)
    if len(combos) > SWEEP_MAX:
        raise Refused(400, f"the grid has {len(combos)} combinations; a sweep is at most {SWEEP_MAX}")
    with LOCK:
        if SWEEP and SWEEP["thread"].is_alive():
            raise Refused(409, f"sweep {SWEEP['id']} is still running")
        sid = old["id"] if old else "sw-" + time.strftime("%Y%m%d-%H%M%S")
        folder = CHECKS / "sweeps" / sid
        folder.mkdir(parents=True, exist_ok=True)
        st = {"id": sid, "brief": brief["id"], "policy": policy, "grid": grid, "total": len(kept) + len(combos), "done": len(kept), "failed": 0, "running": 0, "state": "running",
              "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "ended": None, "seconds": 0}
        if old:  # the grids the table was made from, in order; the table as it was stays beside the new one
            st.update(grid=old["grid"], added=[*old.get("added", []), {"grid": grid, "rerun": bool(body.get("rerun")), "at": st["started"]}], first_started=old.get("first_started", old["started"]))
            shutil.copy(folder / "table.csv", folder / f"table.before-{time.strftime('%Y%m%d-%H%M%S')}.csv")
        write_status(folder, st)
        stop = threading.Event()
        thread = threading.Thread(target=run_sweep, args=(folder, brief, policy, combos, st, stop, kept), daemon=True)
        SWEEP.clear()
        SWEEP.update(id=sid, thread=thread, stop=stop)
        thread.start()
    return st


def sweep_status(sid):
    path = CHECKS / "sweeps" / sid / "status.json"
    if not re.fullmatch(r"sw-[0-9-]{15}", sid) or not path.is_file():
        raise Refused(404, "no such sweep")
    return json.loads(path.read_text())


def stop_sweep(sid):
    if not SWEEP or SWEEP["id"] != sid or not SWEEP["thread"].is_alive():
        raise Refused(409, "that sweep is not running here")
    SWEEP["stop"].set()
    return {"stopping": sid}


def save_review(body):
    """The reviewer's tick and note for one item (a box of the page) of one session; nothing under sessions/ is written."""
    sid, item, note = body.get("session"), body.get("item"), body.get("note", "")
    if not (isinstance(sid, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid) and (tools.SESSIONS / sid).is_dir()):
        raise Refused(400, "session must be the id of an existing session")
    if not (isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_:.-]{1,60}", item)) or type(body.get("tick")) is not bool or not isinstance(note, str) or len(note) > 2000:
        raise Refused(400, "a review needs item (a short id), tick (true or false) and note (a text of at most 2000 characters)")
    with LOCK:
        path = CHECKS / "reviews" / f"{sid}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        marks = json.loads(path.read_text()) if path.is_file() else {}
        if body["tick"] or note.strip():
            marks[item] = {"tick": body["tick"], "note": note, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        else:
            marks.pop(item, None)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(marks, indent=1) + "\n")
        tmp.replace(path)
    return {"session": sid, "items": len(marks)}


def start_session(body):
    """loop.py as a child process with the chosen flags; it then runs exactly as it does from a terminal. Several can run
    side by side. With the scheduling policy "random" the server chooses share or cap itself and notes the session in
    checks/random.json: the session list then withholds its policy until the session has a score."""
    budget, draft, policy, base = body.get("budget"), body.get("draft", "on"), body.get("policy", body.get("mode", "share")), body.get("baseline", True)
    tokens, temp = body.get("max_tokens"), body.get("temperature")
    if (budget is not None and (type(budget) is not int or budget < 1)) or draft not in ("on", "off") or policy not in ("share", "cap", "random") or type(base) is not bool:
        raise Refused(400, "budget must be a whole number of at least 1 (or left out: the brief's limit), draft on or off, policy (the scheduling policy) share, cap or random, baseline true or false")
    if (tokens is not None and (type(tokens) is not int or not 256 <= tokens <= 100000)) or (temp is not None and (type(temp) not in (int, float) or not 0 <= temp <= 2)):
        raise Refused(400, "max_tokens must be a whole number from 256 to 100000 and temperature a number from 0 to 2 (or left out: the loop's defaults)")
    sid, brief = body.get("session"), body.get("brief")
    if sid is not None and not (isinstance(sid, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid) and (tools.SESSIONS / sid / "session.json").is_file()):
        raise Refused(400, "session must be the id of an existing session that has a session.json (leave it out to start a new one)")
    if brief is not None:
        try:
            tools.load_brief(brief)
        except ValueError as e:
            raise Refused(400, str(e))
    with LOCK:
        running = {i for i, x in STARTED.items() if x["proc"].poll() is None} | set(other_loops())
        if len(running) >= MAX_LOOPS:
            raise Refused(409, f"{len(running)} sessions are running, and at most {MAX_LOOPS} run at the same time: wait for one to end")
        if sid in running:
            raise Refused(409, f"session {sid} is running")
        if sid is None:  # a new id, also not one given to a loop that has not made its folder yet
            n = int(tools.next_session_id()[1:])
            while f"s{n:03d}" in STARTED or (tools.SESSIONS / f"s{n:03d}").exists():
                n += 1
            sid = f"s{n:03d}"
        chosen = random.choice(["share", "cap"]) if policy == "random" else policy
        if policy == "random":
            path = CHECKS / "random.json"
            path.write_text(json.dumps(sorted(set(json.loads(path.read_text()) if path.is_file() else []) | {sid})) + "\n")
        (CHECKS / "sessions").mkdir(parents=True, exist_ok=True)
        log = CHECKS / "sessions" / f"{sid}.log"
        flags = {"session": sid, "brief": brief, "budget": budget, "draft": draft, "max-tokens": tokens, "temperature": temp, "policy": chosen, "baseline": "on" if base else "off"}
        cmd = LOOP + [x for k, v in flags.items() if v is not None for x in (f"--{k}", str(v))]
        with log.open("a") as f:
            f.write(" ".join(cmd) + "\n")
            f.flush()
            proc = subprocess.Popen(cmd, cwd=H, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        shown = {**flags, "policy": "chosen by the harness" if policy == "random" else chosen}  # what the page is told
        STARTED[sid] = {"id": sid, "proc": proc, "flags": shown, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "log": log}
        SESSION.clear()
        SESSION.update(STARTED[sid])
    time.sleep(1.5)  # a refused flag (a budget over the loop's ceiling, say) ends the loop at once: report it now
    if proc.poll() not in (None, 0):
        raise Refused(400, "the loop did not start: " + tail(log, 400).strip().splitlines()[-1])
    return {"id": sid, "pid": proc.pid, "flags": shown}


def stop_session(body=None):
    """Stops a session that was started here: the one named, or (the older page names none) the newest."""
    with LOCK:
        sid = (body or {}).get("session") or (SESSION.get("id") if SESSION else None)
        x = STARTED.get(sid)
        if not x or x["proc"].poll() is not None:
            raise Refused(409, "no session started here is running" if not (body or {}).get("session") else f"session {sid} is not running, or was not started from this server (stop it where it was started)")
        proc = x["proc"]
        os.killpg(proc.pid, signal.SIGTERM)  # the loop and the simulation it may be running
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
        return {"stopped": sid}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def answer(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/status":
            return self.answer(200, status())
        if self.path.split("?")[0] == "/api/sessions":
            return self.answer(200, sessions())
        if self.path.split("?")[0].startswith("/api/sweep/"):
            try:
                return self.answer(200, sweep_status(self.path.split("?")[0].split("/")[3]))
            except Refused as e:
                return self.answer(e.code, {"error": e.text})
        super().do_GET()

    def do_POST(self):
        try:
            uid = peer_uid(self.client_address[1], self.server.server_address[1])
            if uid != os.getuid():
                raise Refused(403, f"refused: this connection was opened by user id {uid}, and only user id {os.getuid()} may start runs here")
            origin, host = self.headers.get("Origin"), self.headers.get("Host", "")
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json" or (origin and origin.split("://")[-1] != host):
                raise Refused(403, "refused: only this server's own page may call it")
            n = int(self.headers.get("Content-Length") or 0)
            if n > 65536:
                raise Refused(413, "request too large")
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                raise Refused(400, "the request is not JSON")
            if not isinstance(body, dict):
                raise Refused(400, "the request must be a JSON object")
            do = {"/api/run": lambda: operator_run(body), "/api/session": lambda: start_session(body), "/api/stop": lambda: stop_session(body), "/api/brief": lambda: save_brief(body), "/api/sweep": lambda: start_sweep(body), "/api/review": lambda: save_review(body)}.get(self.path)
            m = re.fullmatch(r"/api/sweep/([^/]+)/stop", self.path)
            if m:
                do = lambda: stop_sweep(m.group(1))
            if not do:
                raise Refused(404, "no such endpoint")
            self.answer(200, do())
        except Refused as e:
            self.answer(e.code, {"error": e.text})


def main():
    ap = argparse.ArgumentParser(description="Serve the viewer and the operator's three controls on 127.0.0.1.")
    ap.add_argument("--port", type=int, default=PORT)
    a = ap.parse_args()
    srv = http.server.ThreadingHTTPServer((HOST, a.port), Handler)
    print(f"control.py: http://{HOST}:{a.port}/viewer/  (files of {ROOT}; POST accepted from user id {os.getuid()} only)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
