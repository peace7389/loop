"""The operator's control server: the viewer's files, plus the few things the operator may start from the page.
It replaces the plain file server. Start it with:  python3 harness/control.py   (the page is http://127.0.0.1:8600/viewer/)

  GET  any file        the project's files, read-only, exactly as before
  GET  /api/status     what is running, the ledger's size, the last lines of the session's output
  POST /api/run        {params, mode}: one operator simulation -> checks/op-<timestamp>/, returns its metrics
  POST /api/session    {budget, thinking, mode, baseline}: starts loop.py with those flags, returns the session id
  POST /api/stop       stops the session that was started here

Who writes what (the write-ownership rule):
  loop.py      ledger.jsonl, and runs/ through tools.run. Nothing else writes either of them.
  control.py   checks/ only: checks/op-<timestamp>/ (one operator run), checks/control.jsonl (the list of those runs),
               checks/sessions/<id>.log (a session's terminal output). It starts and stops loop.py and does nothing else.
  the viewer   nothing. Its Control page only calls the three POST endpoints above.
An operator run is made by the built program directly, never by tools.run, so it never reaches runs/index.json: no tool
the model has can see it. The scheduler mode is passed on the command line only, as before; the model never sees it.

Who may call it. The server listens on 127.0.0.1 only (there is no option to change that). This machine is shared, so
that alone would let any local user start runs; a POST is therefore accepted only when the connection was opened by a
process of the user who runs this server (an SSH tunnel of that user counts), and only as application/json from this
page (so no other web page open in the same browser can call it). Parameters go through tools.clamp, like the model's.
Python standard library only."""
import argparse, http.server, json, os, signal, subprocess, sys, threading, time
from pathlib import Path
import tools

ROOT, H, CHECKS = tools.ROOT, tools.HARNESS, tools.ROOT / "checks"
BIN = tools.NS3 / "build/scratch/two-hosts/ns3.49-two-hosts-optimized"
LOOP = [sys.executable, str(H / "loop.py")]
HOST, PORT = "127.0.0.1", 8600
LOCK, RUN_LOCK = threading.Lock(), threading.Lock()
SESSION = {}  # the session started here, if any: id, proc, flags, started, log


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
    """True if a loop.py of this user is running that was not started here (two loops must never share the ledger)."""
    mine = SESSION["proc"].pid if SESSION and SESSION["proc"].poll() is None else None
    for p in Path("/proc").iterdir():
        try:
            if not p.name.isdigit() or int(p.name) == mine or p.stat().st_uid != os.getuid():
                continue
            args = (p / "cmdline").read_bytes().split(b"\0")
            if any(a.endswith(b"loop.py") and (Path(os.readlink(p / "cwd")) / a.decode()).resolve() == (H / "loop.py").resolve() for a in args[1:3]):
                return True
        except OSError:
            continue
    return False


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
            "ledger_records": count(ROOT / "ledger.jsonl"), "operator_runs": count(CHECKS / "control.jsonl")}


def operator_run(body):
    """One simulation with the operator's settings, by the built program directly, into checks/op-<timestamp>/."""
    params, mode = body.get("params") or {}, body.get("mode", "share")
    if mode not in ("share", "cap") or not isinstance(params, dict) or set(params) - set(tools.MANIFEST["params"]):
        raise Refused(400, "params must be manifest parameters and mode must be share or cap")
    try:
        clean, clamps = tools.clamp(params)
    except (ValueError, TypeError) as e:
        raise Refused(400, f"bad parameter value: {e}")
    if not RUN_LOCK.acquire(blocking=False):
        raise Refused(409, "an operator run is already in progress")
    try:
        rid = "op-" + time.strftime("%Y%m%d-%H%M%S")
        out = CHECKS / rid
        out.mkdir(parents=True)
        args = [f"--{k}={v}" for k, v in clean.items()] + [f"--mode={mode}", f"--out={out}"]
        t0 = time.time()
        try:
            p = subprocess.run([str(BIN)] + args, cwd=out, env={"LD_LIBRARY_PATH": str(tools.NS3 / "build/lib")}, capture_output=True, text=True, timeout=tools.RUN_TIMEOUT)
            code, err = p.returncode, (p.stderr or p.stdout)[-800:]
        except subprocess.TimeoutExpired:
            code, err = "timeout", f"no result after {tools.RUN_TIMEOUT} s"
        seconds = round(time.time() - t0, 1)
        (out / "command.txt").write_text(f"two-hosts {' '.join(args)}\nexit {code}, {seconds} s\n")
        if code != 0 or not (out / "metrics.json").exists():
            raise Refused(500, f"the simulation failed (exit {code}): {err}")
        rec = {"id": rid, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": mode, "seconds": seconds, "clamped": clamps,
               "params": json.loads((out / "params.json").read_text()), "metrics": json.loads((out / "metrics.json").read_text())}
        with (CHECKS / "control.jsonl").open("a") as f:
            f.write(json.dumps(rec) + "\n")
        return rec
    finally:
        RUN_LOCK.release()


def start_session(body):
    """loop.py as a child process with the chosen flags; it then runs exactly as it does from a terminal."""
    budget, thinking, mode, base = body.get("budget", 30), body.get("thinking", "on"), body.get("mode", "share"), body.get("baseline", True)
    if type(budget) is not int or budget < 1 or thinking not in ("on", "off") or mode not in ("share", "cap") or type(base) is not bool:
        raise Refused(400, "budget must be a whole number of at least 1, thinking on or off, mode share or cap, baseline true or false")
    with LOCK:
        if (SESSION and SESSION["proc"].poll() is None) or other_loop():
            raise Refused(409, "a session is already running")
        sid = "s-" + time.strftime("%Y%m%d-%H%M%S")
        (CHECKS / "sessions").mkdir(parents=True, exist_ok=True)
        log = CHECKS / "sessions" / f"{sid}.log"
        flags = {"budget": budget, "thinking": thinking, "mode": mode, "baseline": "on" if base else "off"}
        cmd = LOOP + [x for k, v in flags.items() for x in (f"--{k}", str(v))]
        with log.open("w") as f:
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
            do = {"/api/run": lambda: operator_run(body), "/api/session": lambda: start_session(body), "/api/stop": stop_session}.get(self.path)
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
