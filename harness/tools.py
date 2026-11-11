"""Read-only tools plus run(): all the model can reach. Every path a tool reads or writes is inside the current
session's folder (sessions/<id>/); a run id is accepted only if that session's own runs/index.json lists it.
A session works on one brief (briefs/<id>.json): the task, the fixed settings (system), the settings the model may
change (knobs), the goal and the limits. The brief is read once, when the session is created."""
import json, os, re, subprocess, time
from pathlib import Path

ROOT = Path.home() / "project"
NS3, HARNESS, SESSIONS, BRIEFS = ROOT / "ns-3.49", ROOT / "harness", ROOT / "sessions", ROOT / "briefs"
SESSION = None          # the current session's folder, set by open_session(); no tool works before that
BRIEF = None            # what the current session was given: its brief (description filled in) plus MANIFEST
MANIFEST = json.loads((HARNESS / "manifest.json").read_text())  # the same for every brief: outputs, tools, how an experiment is run
OPTIONS = ("linkRate", "linkDelay", "mtu", "udpRate", "tcpVariant", "queuePkts", "duration", "seed", "weightUdp")  # program options a brief sets
DEFAULT_BRIEF = "two-hosts-open"
MODE = "share"          # operator's choice, set by loop.py; goes to the simulation as the environment variable TWOHOSTS_SCHED, never into the session's folder or anything a tool returns
RUN_TIMEOUT = 600

def load_brief(brief_id):
    """briefs/<id>.json, checked, with the {placeholders} of its description filled from its own system settings."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", str(brief_id)) or not (BRIEFS / f"{brief_id}.json").is_file():
        raise ValueError(f"unknown brief {brief_id!r}")
    b = json.loads((BRIEFS / f"{brief_id}.json").read_text())
    knobs, system, goal, limits = b.get("knobs") or {}, b.get("system") or {}, b.get("goal") or {}, b.get("limits") or {}
    bad = [f"'{k}' is not a setting of the program" for k in list(knobs) + list(system) if k not in OPTIONS + ("udpPacketBytes",)]
    bad += [f"'{k}' is both fixed (system) and adjustable (knobs)" for k in knobs if k in system]
    bad += [f"knob '{k}' needs a default and either choices or min and max" for k, s in knobs.items() if "default" not in s or not ("choices" in s or ("min" in s and "max" in s))]
    bad += [f"'{k}' must be a text" for k in ("task", "description") if not str(b.get(k) or "").strip()] + ([] if b.get("id") == brief_id else ["id must equal the file name"])
    if system.get("udpPacketBytes", 1400) != 1400:
        bad.append("udpPacketBytes is 1400 in the scenario and cannot be set")
    if goal.get("kind") == "given":
        t = goal.get("target") or {}
        if t.get("measure") not in MANIFEST["outputs"] or t.get("direction") not in ("max", "min") or not isinstance(goal.get("conditions"), list):
            bad.append("a given goal needs target {measure: an output, direction: max|min} and a list of conditions")
    elif goal.get("kind") != "open":
        bad.append("goal.kind must be open or given")
    bad += [f"limits.{k} must be a whole number of at least 1" for k in ("simulations", "simulations_per_experiment") if type(limits.get(k)) is not int or limits[k] < 1]
    used = set(re.findall(r"\{(\w+)\}", str(b.get("description"))))
    bad += [f"the description uses {{{k}}}, which is not one of the brief's system settings" for k in sorted(used - set(system))]
    if bad:
        raise ValueError(f"brief {brief_id}: " + "; ".join(bad))
    return {**b, "description": re.sub(r"\{(\w+)\}", lambda m: str(system[m.group(1)]), b["description"])}

def next_session_id():
    ids = [int(p.name[1:]) for p in SESSIONS.iterdir() if re.fullmatch(r"s\d{3}", p.name)] if SESSIONS.is_dir() else []
    return f"s{max(ids, default=0) + 1:03d}"

def open_session(sid=None, brief=None):
    """Make sessions/<sid>/ the only folder the tools can reach (sid None: a new id sNNN). A new session takes the
    named brief (default two-hosts-open); an existing one keeps what its session.json says it was given."""
    global SESSION, BRIEF
    sid = sid or next_session_id()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid):
        raise ValueError(f"bad session id {sid!r}")
    meta = SESSIONS / sid / "session.json"
    if meta.is_file():
        given = json.loads(meta.read_text())["given"]
        if brief and brief != given["id"]:
            raise ValueError(f"session {sid} works on brief {given['id']}, not {brief}")
    elif (SESSIONS / sid / "ledger.jsonl").is_file():
        raise ValueError(f"session {sid} was made before briefs existed and cannot be continued")
    else:
        given = {**load_brief(brief or DEFAULT_BRIEF), **MANIFEST}
    (SESSIONS / sid / "runs").mkdir(parents=True, exist_ok=True)
    SESSION, BRIEF = SESSIONS / sid, given
    return sid

def _runs():
    if SESSION is None:
        raise RuntimeError("no session is open")
    return SESSION / "runs"

def describe_system():
    if BRIEF is None:
        raise RuntimeError("no session is open")
    return BRIEF

def _rate_bps(s):
    m = re.fullmatch(r"\s*([0-9.]+)\s*([kMG]?)bps\s*", str(s))
    if not m:
        raise ValueError(f"bad rate {s!r}")
    return float(m.group(1)) * {"": 1, "k": 1e3, "M": 1e6, "G": 1e9}[m.group(2)]

def clamp(params, brief=None):
    """Keep only the brief's knobs and force each into its range. A setting the brief fixes (system) is not the
    model's to change: the brief's value is used. Returns (clean, {param: [asked, used]})."""
    b = brief or BRIEF
    clean, clamps = {}, {k: [v, b["system"][k]] for k, v in params.items() if k in b["system"] and v != b["system"][k]}
    for k, spec in b["knobs"].items():
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

def options(clean, brief=None):
    """Every option the program is started with: the brief's fixed settings, its knobs' defaults, then the chosen values."""
    b = brief or BRIEF
    return {**{k: v for k, v in b["system"].items() if k in OPTIONS}, **{k: s["default"] for k, s in b["knobs"].items()}, **clean}

def run(params):
    """Clamp, allocate the session's runs/<id>/, run ns-3 (no rebuild), parse metrics, append to the session's runs/index.json."""
    clean, clamps = clamp(params)
    RUNS = _runs()
    ids = [int(p.name[1:]) for p in RUNS.iterdir() if re.fullmatch(r"r\d{3}", p.name)]
    rid = f"r{max(ids, default=0) + 1:03d}"
    out = RUNS / rid
    out.mkdir()
    args = " ".join(f"--{k}={v}" for k, v in options(clean).items()) + f" --out={out}"
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

TOOLS = {"describe_system": describe_system, "metrics": metrics, "series": series, "grep_trace": grep_trace, "list_runs": list_runs}
