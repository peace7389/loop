"""The operator's control server: the viewer's files, plus the few things the operator may start from the page.
It replaces the plain file server. Start it with:  python3 harness/control.py   (the page is http://127.0.0.1:8600/viewer/)

  GET  any file        the project's files, read-only, exactly as before
  GET  /api/status     what is running, the last lines of the session's output, "briefs" (the ids in briefs/) and
                       "sessions": every session folder (id, brief, records, experiments, first and last time, mode, model, running)
  GET  /api/sessions   that list alone
  POST /api/run        {params, mode, brief}: one operator simulation -> checks/op-<timestamp>/, returns its metrics.
                       The brief (default two-hosts-open) gives the fixed settings and the ranges.
  POST /api/session    {brief, budget, draft, mode, baseline, session}: starts loop.py with those flags, returns the session id.
                       Without "session" it is a new session (the next id sNNN) on the named brief (default two-hosts-open;
                       budget defaults to the brief's limit); with the id of an existing session it continues that one.
  POST /api/stop       stops the session that was started here
  POST /api/brief      {brief}: saves a NEW brief as briefs/<id>.json after the same check loop.py makes (tools.check_brief).
                       An id that already exists is refused: a brief is never overwritten.

Who writes what (the write-ownership rule):
  loop.py      its own session's folder, sessions/<id>/: session.json, ledger.jsonl, and runs/ through tools.run. Nothing else writes
               there, and no tool can read outside it. It also appends one line per run to checks/operator.jsonl
               (session, run, mode, seconds), which no tool reads.
  control.py   checks/: checks/op-<timestamp>/ (one operator run), checks/control.jsonl (the list of those runs),
               checks/sessions/<id>.log (a session's terminal output); and briefs/<id>.json, new files only.
               It starts and stops loop.py and does nothing else.
  the viewer   nothing. Its Control page only calls the POST endpoints above.
An operator run is made by the built program directly, never by tools.run, so it never reaches a session's folder: no
tool the model has can see it. The scheduler mode reaches the simulation as the environment variable TWOHOSTS_SCHED only; the model never sees it.

Who may call it. The server listens on 127.0.0.1 only (there is no option to change that). This machine is shared, so
that alone would let any local user start runs; a POST is therefore accepted only when the connection was opened by a
process of the user who runs this server (an SSH tunnel of that user counts), and only as application/json from this
page (so no other web page open in the same browser can call it). Parameters go through tools.clamp, like the model's.
Briefs (briefs/<id>.json) are the operator's: written by hand or saved from the page's brief editor.
Python standard library only."""
import argparse, http.server, json, os, re, signal, subprocess, sys, threading, time
from pathlib import Path
import tools

ROOT, H, CHECKS = tools.ROOT, tools.HARNESS, tools.ROOT / "checks"
BIN = tools.NS3 / "build/scratch/two-hosts/ns3.49-two-hosts-optimized"
LOOP = [sys.executable, str(H / "loop.py")]
HOST, PORT = "127.0.0.1", 8600
LOCK, RUN_LOCK = threading.Lock(), threading.Lock()
SESSION = {}  # the session started here, if any: id, proc, flags, started, log
CACHE = {}    # session id -> (file times, its row in /api/sessions)


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


def other_loop():
    """The session id of a loop.py of this user that is running and was not started here ("?" if its command does not
    name one), or None. Only one loop at a time is run from this server."""
    mine = SESSION["proc"].pid if SESSION and SESSION["proc"].poll() is None else None
    for p in Path("/proc").iterdir():
        try:
            if not p.name.isdigit() or int(p.name) == mine or p.stat().st_uid != os.getuid():
                continue
            args = (p / "cmdline").read_bytes().split(b"\0")
            if any(a.endswith(b"loop.py") and (Path(os.readlink(p / "cwd")) / a.decode()).resolve() == (H / "loop.py").resolve() for a in args[1:3]):
                names = [a.decode(errors="replace") for a in args]
                return names[names.index("--session") + 1] if "--session" in names[:-1] else "?"
        except OSError:
            continue
    return None


def sessions():
    """One row per folder in sessions/, oldest first, read from the session's own files and checks/operator.jsonl."""
    lines = lambda p: [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
    mode = {}
    for r in lines(CHECKS / "operator.jsonl"):
        if r.get("session"):
            mode[r["session"]] = r.get("mode")
    here = SESSION["id"] if SESSION and SESSION["proc"].poll() is None else None
    other = None if here else other_loop()
    dirs = sorted(p for p in tools.SESSIONS.iterdir() if p.is_dir() and re.fullmatch(r"[A-Za-z0-9_-]{1,40}", p.name)) if tools.SESSIONS.is_dir() else []
    if other == "?" and dirs:  # a loop started from a terminal without --session made the newest folder
        other = max(dirs, key=lambda p: p.stat().st_mtime).name
    out = []
    for d in dirs:
        led, idx = d / "ledger.jsonl", d / "runs/index.json"
        sig = tuple(p.stat().st_mtime if p.exists() else 0 for p in (led, idx))
        if CACHE.get(d.name, (None,))[0] != sig:
            recs = lines(led)
            drafts = [r for r in recs if r["type"] in ("draft", "scratch")]
            meta = json.loads((d / "session.json").read_text()) if (d / "session.json").is_file() else {}
            CACHE[d.name] = (sig, {"id": d.name, "brief": meta.get("brief"), "records": len(recs), "runs": len(lines(idx)),
                "experiments": sum(r["type"] == "evidence" and r["id"] != "E0" for r in recs), "turns": max([r["turn"] for r in recs], default=0),
                "started": recs[0].get("ts") if recs else None, "last": recs[-1].get("ts") if recs else None,
                "model": (drafts[-1]["body"].get("model") if drafts else None),
                "done": any(r["type"] == "note" and (r.get("body") or {}).get("text") == "model declared done" for r in recs)})
        out.append({**CACHE[d.name][1], "mode": mode.get(d.name), "running": d.name in (here, other)})
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
            "operator_runs": count(CHECKS / "control.jsonl")}


def operator_run(body):
    """One simulation with the operator's settings, by the built program directly, into checks/op-<timestamp>/."""
    params, mode = body.get("params") or {}, body.get("mode", "share")
    try:
        brief = tools.load_brief(body.get("brief", tools.DEFAULT_BRIEF))
    except ValueError as e:
        raise Refused(400, str(e))
    if mode not in ("share", "cap") or not isinstance(params, dict) or set(params) - set(brief["knobs"]) - set(brief["system"]):
        raise Refused(400, "params must be settings of the brief and mode must be share or cap")
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
            p = subprocess.run([str(BIN)] + args, cwd=out, env={"LD_LIBRARY_PATH": str(tools.NS3 / "build/lib"), "TWOHOSTS_SCHED": mode}, capture_output=True, text=True, timeout=tools.RUN_TIMEOUT)
            code, err = p.returncode, (p.stderr or p.stdout)[-800:]
        except subprocess.TimeoutExpired:
            code, err = "timeout", f"no result after {tools.RUN_TIMEOUT} s"
        seconds = round(time.time() - t0, 1)
        (out / "command.txt").write_text(f"TWOHOSTS_SCHED={mode} two-hosts {' '.join(args)}\nexit {code}, {seconds} s\n")
        if code != 0 or not (out / "metrics.json").exists():
            raise Refused(500, f"the simulation failed (exit {code}): {err}")
        rec = {"id": rid, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "brief": brief["id"], "mode": mode, "seconds": seconds, "clamped": clamps,
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


def start_session(body):
    """loop.py as a child process with the chosen flags; it then runs exactly as it does from a terminal."""
    budget, draft, mode, base = body.get("budget"), body.get("draft", "on"), body.get("mode", "share"), body.get("baseline", True)
    if (budget is not None and (type(budget) is not int or budget < 1)) or draft not in ("on", "off") or mode not in ("share", "cap") or type(base) is not bool:
        raise Refused(400, "budget must be a whole number of at least 1 (or left out: the brief's limit), draft on or off, mode share or cap, baseline true or false")
    sid, brief = body.get("session"), body.get("brief")
    if sid is not None and not (isinstance(sid, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid) and (tools.SESSIONS / sid / "session.json").is_file()):
        raise Refused(400, "session must be the id of an existing session that has a session.json (leave it out to start a new one)")
    if brief is not None:
        try:
            tools.load_brief(brief)
        except ValueError as e:
            raise Refused(400, str(e))
    with LOCK:
        if (SESSION and SESSION["proc"].poll() is None) or other_loop():
            raise Refused(409, "a session is already running")
        sid = sid or tools.next_session_id()
        (CHECKS / "sessions").mkdir(parents=True, exist_ok=True)
        log = CHECKS / "sessions" / f"{sid}.log"
        flags = {"session": sid, "brief": brief, "budget": budget, "draft": draft, "mode": mode, "baseline": "on" if base else "off"}
        cmd = LOOP + [x for k, v in flags.items() if v is not None for x in (f"--{k}", str(v))]
        with log.open("a") as f:
            f.write(" ".join(cmd) + "\n")
            f.flush()
            proc = subprocess.Popen(cmd, cwd=H, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        SESSION.clear()
        SESSION.update(id=sid, proc=proc, flags=flags, started=time.strftime("%Y-%m-%dT%H:%M:%S"), log=log)
    time.sleep(1.5)  # a refused flag (a budget over the loop's ceiling, say) ends the loop at once: report it now
    if proc.poll() not in (None, 0):
        raise Refused(400, "the loop did not start: " + tail(log, 400).strip().splitlines()[-1])
    return {"id": sid, "pid": proc.pid, "flags": flags}


def stop_session():
    with LOCK:
        if not SESSION or SESSION["proc"].poll() is not None:
            raise Refused(409, "no session started here is running")
        proc = SESSION["proc"]
        os.killpg(proc.pid, signal.SIGTERM)  # the loop and the simulation it may be running
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
        return {"stopped": SESSION["id"]}


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
            do = {"/api/run": lambda: operator_run(body), "/api/session": lambda: start_session(body), "/api/stop": stop_session, "/api/brief": lambda: save_brief(body)}.get(self.path)
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
