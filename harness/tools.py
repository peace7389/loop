"""Read-only tools plus run(): all the model can reach. Every path a tool reads or writes is inside the current
session's folder (sessions/<id>/); a run id is accepted only if that session's own runs/index.json lists it."""
import json, os, re, shutil, subprocess, time
from pathlib import Path

ROOT = Path.home() / "project"
NS3, HARNESS, SESSIONS = ROOT / "ns-3.49", ROOT / "harness", ROOT / "sessions"
SESSION = None          # the current session's folder, set by open_session(); no tool works before that
MANIFEST = json.loads((HARNESS / "manifest.json").read_text())
MODE = "share"          # operator's choice, set by loop.py; goes to the simulation as the environment variable TWOHOSTS_SCHED, never into the session's folder or anything a tool returns
RUN_TIMEOUT = 600

def next_session_id():
    ids = [int(p.name[1:]) for p in SESSIONS.iterdir() if re.fullmatch(r"s\d{3}", p.name)] if SESSIONS.is_dir() else []
    return f"s{max(ids, default=0) + 1:03d}"

def open_session(sid=None):
    """Make sessions/<sid>/ the only folder the tools can reach (sid None: a new id sNNN). A new session gets its
    own copy of the scenario source: that copy is what read_source returns, and the record of what the session could read."""
    global SESSION
    sid = sid or next_session_id()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid):
        raise ValueError(f"bad session id {sid!r}")
    new = not (SESSIONS / sid).is_dir()
    (SESSIONS / sid / "runs").mkdir(parents=True, exist_ok=True)
    if new:
        shutil.copy(NS3 / "scratch/two-hosts/two-hosts.cc", SESSIONS / sid / "two-hosts.cc")
    SESSION = SESSIONS / sid
    return sid

def _runs():
    if SESSION is None:
        raise RuntimeError("no session is open")
    return SESSION / "runs"

def describe_system():
    return MANIFEST

def _rate_bps(s):
    m = re.fullmatch(r"\s*([0-9.]+)\s*([kMG]?)bps\s*", str(s))
    if not m:
        raise ValueError(f"bad rate {s!r}")
    return float(m.group(1)) * {"": 1, "k": 1e3, "M": 1e6, "G": 1e9}[m.group(2)]

def clamp(params):
    """Keep only manifest params and force each into its range. Returns (clean, {param: [asked, used]})."""
    clean, clamps = {}, {}
    for k, spec in MANIFEST["params"].items():
        if k not in params:
            continue
        v = params[k]
        if "choices" in spec:
            nv = v if v in spec["choices"] else spec["default"]
        elif k == "udpRate":
            bps = min(max(_rate_bps(v), _rate_bps(spec["min"])), _rate_bps(spec["max"]))
            nv = f"{int(round(bps / 1e6))}Mbps"
            if abs(bps - _rate_bps(v)) < 1:
                nv = str(v).strip()
        else:
            nv = min(max(float(v), spec["min"]), spec["max"])
            nv = int(round(nv)) if isinstance(spec["min"], int) else nv
        if nv != v:
            clamps[k] = [v, nv]
        clean[k] = nv
    return clean, clamps

def run(params):
    """Clamp, allocate the session's runs/<id>/, run ns-3 (no rebuild), parse metrics, append to the session's runs/index.json."""
    clean, clamps = clamp(params)
    RUNS = _runs()
    ids = [int(p.name[1:]) for p in RUNS.iterdir() if re.fullmatch(r"r\d{3}", p.name)]
    rid = f"r{max(ids, default=0) + 1:03d}"
    out = RUNS / rid
    out.mkdir()
    args = " ".join(f"--{k}={v}" for k, v in clean.items()) + f" --out={out}"
    t0 = time.time()
    p = subprocess.run(["./ns3", "run", f"two-hosts {args}", "--no-build"], cwd=NS3, env={**os.environ, "TWOHOSTS_SCHED": MODE}, capture_output=True, text=True, timeout=RUN_TIMEOUT)
    if p.returncode or not (out / "metrics.json").exists():
        return {"id": rid, "params": clean, "clamped": clamps, "error": (p.stderr or p.stdout)[-800:]}
    m = json.loads((out / "metrics.json").read_text())
    with (RUNS / "index.json").open("a") as f:
        f.write(json.dumps({"id": rid, "params": json.loads((out / "params.json").read_text()), "metrics": m}) + "\n")
    return {"id": rid, "params": clean, "clamped": clamps, "metrics": m, "seconds": round(time.time() - t0, 1)}

def _dir(run_id):
    """The folder of a run of THIS session: the id must be one that the session's own index lists."""
    if not any(r["id"] == run_id for r in list_runs()):
        raise ValueError(f"unknown run {run_id!r}")
    return _runs() / run_id

def metrics(run_id):
    return json.loads((_dir(run_id) / "metrics.json").read_text())

def series(run_id, every_n=1):
    rows = (_dir(run_id) / "series.csv").read_text().splitlines()
    step = max(int(every_n), 1, -(-(len(rows) - 1) // 100))
    return "\n".join([rows[0]] + rows[1::step][:100])

def grep_trace(run_id, pattern, limit=50):
    rx, hits = re.compile(str(pattern)[:200]), []
    for line in (_dir(run_id) / "flowmon.xml").open():
        if rx.search(line):
            hits.append(line.strip()[:300])
        if len(hits) >= min(int(limit), 50):
            break
    return "\n".join(hits) or "no match"

def list_runs():
    p = _runs() / "index.json"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []

def read_source(name):
    p = _runs().parent / "two-hosts.cc"   # the session's own copy, made when the session was created
    return p.read_text() if name == "two-hosts.cc" and p.is_file() else "not available"

TOOLS = {"describe_system": describe_system, "metrics": metrics, "series": series,
         "grep_trace": grep_trace, "list_runs": list_runs, "read_source": read_source}
