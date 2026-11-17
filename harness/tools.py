"""Read-only tools plus run(): all the model can reach. Every path a tool reads or writes is inside the current
session's folder (sessions/<id>/); a run id is accepted only if that session's own runs/index.json lists it.
A session works on one brief (briefs/<id>.json): the task, the fixed settings (system), the settings the model may
change (knobs), the goal and the limits. The brief is read once, when the session is created."""
import json, os, re, subprocess, time
from pathlib import Path
import network

ROOT = Path.home() / "project"
NS3, HARNESS, SESSIONS, BRIEFS = ROOT / "ns-3.49", ROOT / "harness", ROOT / "sessions", ROOT / "briefs"
SESSION = None          # the current session's folder, set by open_session(); no tool works before that
BRIEF = None            # what the current session was given: its brief (description filled in) plus MANIFEST
MANIFEST = json.loads((HARNESS / "manifest.json").read_text())  # the same for every brief: outputs, tools, how an experiment is run
OPTIONS = ("linkRate", "linkDelay", "mtu", "udpRate", "tcpVariant", "queuePkts", "duration", "seed", "weightUdp")  # program options every brief sets
EXTRA = ("queuePktsUdp", "queuePktsTcp", "tcpInitCwnd", "tcpBufBytes", "devQueuePkts")  # (build 6: TCP's first window in segments, TCP's send and receive buffer in bytes; not given: ns-3's 10 segments, 1 MB.
                                          # build 7: the length of each device's transmit queue in packets; not given: 10)
        # program options a brief may leave out (settings added after build 4): the program is then started without them
                                          # and does what it did before they existed. Here: a queue without its own length is as long as queuePkts says
KNOBS = ("weightUdp", "udpRate", "queuePkts", "tcpVariant", "duration", "seed", "linkRate", "linkDelay", "mtu") + EXTRA  # those a brief may make knobs: every option of the program (the answer format has a type for each)
KNOB_TYPES = {"weightUdp": "number", "udpRate": "string", "queuePkts": "integer", "tcpVariant": "string", "duration": "number", "seed": "integer",
              "linkRate": "string", "linkDelay": "string", "mtu": "integer", "queuePktsUdp": "integer", "queuePktsTcp": "integer", "tcpInitCwnd": "integer", "tcpBufBytes": "integer", "devQueuePkts": "integer"}  # their types in the answer format
RATES, STEPPED = ("udpRate", "linkRate"), ("weightUdp", "queuePkts", "duration", "seed", "mtu", "queuePktsUdp", "queuePktsTcp", "tcpInitCwnd", "tcpBufBytes", "devQueuePkts")  # knobs given as a rate ("400Mbps"); numeric knobs, which may have a step
DEFAULT_BRIEF = "two-hosts-open"
def policies(brief=None):
    """The scheduling policies a brief's program has: share and cap; and prio (the first flow of a scheduler's list is served first, the parts unused)
    for a brief with a network, whose program `net` has it."""
    return ("share", "cap", "prio") if (brief or BRIEF or {}).get("topology") else ("share", "cap")


POLICY = "share"        # the scheduling policy (how the scheduler divides the link: share or cap): the operator's choice, set by loop.py. It goes to
                        # the simulation as the environment variable TWOHOSTS_SCHED, never into the session's folder or anything a tool returns
RUN_TIMEOUT = 600
BIN = NS3 / "build/scratch/two-hosts/ns3.49-two-hosts-optimized"  # the built program, started directly (several at once)
NET_BIN = NS3 / "build/scratch/net/ns3.49-net-optimized"          # the program that builds a network from a description: for a brief that has "topology" (network.py)
KIND_TYPES = {"rate": "string", "time": "string", "choice": "string", "int": "integer", "number": "number"}  # a network setting's kind -> its type in the answer format


def outputs(brief=None):
    """The measures of a simulation with what each is: a brief with a network has its own (made from the network), every other brief the manifest's."""
    b = brief or BRIEF or {}
    return network.outputs(b["topology"]) if b.get("topology") else MANIFEST["outputs"]


def kind(k, brief=None):
    """What kind of value setting k holds: rate, time, choice, int or number."""
    b = brief or BRIEF or {}
    if b.get("topology"):
        return "choice" if "choices" in (b.get("knobs") or {}).get(k, {}) else network.kind(k)
    return "rate" if k in RATES else "time" if k == "linkDelay" else "choice" if k == "tcpVariant" else "number" if k in ("weightUdp", "duration") else "int"


def knob_type(k, brief=None):
    """The type of knob k in the answer format."""
    b = brief or BRIEF or {}
    return KIND_TYPES[kind(k, b)] if b.get("topology") else KNOB_TYPES[k]


def command(opts, out, brief=None, topology=None):
    """The command that starts one simulation with these settings into folder out. For a brief with a network it first
    writes out/network.txt (the network with the settings at their values) and out/params.json (the settings used:
    `net` writes none); two-hosts takes its settings as options and writes its own params.json."""
    b = brief or BRIEF or {}
    if not b.get("topology"):
        return [str(BIN)] + [f"--{k}={v}" for k, v in opts.items()] + [f"--out={out}"]
    run = {k: v for k, v in opts.items() if k in network.RUN}
    base = topology or b["topology"]   # topology: the brief's network with a simulation's own changes made (network.apply); a knob of an object that is gone there has nothing to set
    net = network.with_values(base, {k: v for k, v in opts.items() if k not in network.RUN and k in network.settings(base)})
    bad = network.problems(net)
    if bad:
        raise ValueError("the network cannot be built with these settings: " + "; ".join(bad))
    (Path(out) / "network.txt").write_text(network.text(net, run))
    (Path(out) / "params.json").write_text(json.dumps(opts) + "\n")
    return [str(NET_BIN), f"--net={Path(out) / 'network.txt'}", f"--out={out}"]

def _ok(k, v):
    """Whether the program can be started with setting k = v."""
    try:
        if k in ("linkRate", "udpRate"):
            return _rate_bps(v) >= (1 if k == "linkRate" else 0)
        if k == "linkDelay":
            return bool(re.fullmatch(r"\d+(\.\d+)?(ns|us|ms|s)", str(v)))
        if k == "tcpVariant":
            return bool(re.fullmatch(r"Tcp[A-Za-z0-9]+", str(v)))
        if k in ("mtu", "queuePkts", "seed", "queuePktsUdp", "queuePktsTcp", "tcpInitCwnd", "tcpBufBytes", "devQueuePkts"):
            return type(v) is int and v >= (576 if k == "mtu" else 4096 if k == "tcpBufBytes" else 1)
        if k in ("weightUdp", "duration"):
            return type(v) in (int, float) and (0.05 <= v <= 0.95 if k == "weightUdp" else v > 0)
        return k == "udpPacketBytes" and v == 1400   # set by the scenario; a brief can only state it
    except (TypeError, ValueError):
        return False

def task_text(b):
    """The task as the model reads it, written here from the brief's aim and from the settings it leaves open, so that it
    cannot contradict them. Until 2026-11-17 the task was a text typed into the brief, and a brief made from another one
    kept the other's text: `trap` told the model "both at maximum rate", "find the best ratio" and "say what performance
    you chose to mean" while its UDP rate was fixed, five settings were open and its aim was given (session s031). A
    brief that still states a task of its own keeps it (the briefs and sessions made before); a brief without one gets
    this. The system itself is told in the description, not here; what a measure is, in the brief's list of outputs.
    The set-up page writes the same sentence as the form changes (brief_editor.js, taskText): keep the two alike."""
    knobs, goal = b["knobs"], b["goal"]
    may = f"You may change {len(knobs)} setting{'' if len(knobs) == 1 else 's'} ({', '.join(knobs)}); every other setting is fixed."
    if goal.get("kind") == "given":
        t, conds = goal["target"], goal.get("conditions") or []
        aim = f"Find the settings that give the {'largest' if t['direction'] == 'max' else 'smallest'} {t['measure']}"
        return f"{aim}{', while ' + ' and '.join(c.strip() for c in conds) if conds else ''}. {may} Explain why they are best."
    return f"No aim is given. Choose what 'performance' should mean for this system and say why; then find the settings that are best for it. {may} Explain why they are best."

def check_brief(b, brief_id):
    """Every reason a brief cannot be used, or none; returns it with the {placeholders} of its description filled
    (a fixed setting by its value, a knob as "the knob <name>", so that one description stays true whoever decides a
    setting) and, when it states no task of its own, with the task written by task_text.
    The one check for a brief: loop.py (through open_session) and control.py both use it."""
    if "topology" in b:
        return _check_network_brief(b, brief_id)
    knobs, system, goal, limits = (b.get(k) if isinstance(b.get(k), dict) else {} for k in ("knobs", "system", "goal", "limits"))
    num = lambda k, v: _rate_bps(v) if k in RATES else _seconds(v) if k == "linkDelay" else v
    bad = [] if b.get("id") == brief_id and re.fullmatch(r"[A-Za-z0-9_-]{1,60}", str(brief_id)) else ["id must equal the file name (letters, digits, - and _)"]
    bad += [f"'{k}' must be a text" for k in ("description",) if not isinstance(b.get(k), str) or not b[k].strip()]
    if b.get("task") is not None and (not isinstance(b["task"], str) or not b["task"].strip()):
        bad.append("'task' must be a text, or be left out: the harness then writes it from the aim and the settings")
    bad += [f"'{k}' is not a setting of the program" for k in list(knobs) + list(system) if k not in OPTIONS + EXTRA + ("udpPacketBytes",)]
    bad += [f"'{k}' is both fixed (system) and adjustable (knobs)" for k in knobs if k in system]
    bad += [f"'{k}' can only be a fixed setting (the answer format has no field for it)" for k in knobs if k in OPTIONS + EXTRA and k not in KNOBS]
    bad += [f"'{k}' is missing: give it a fixed value (system) or make it a knob" for k in OPTIONS if k not in knobs and k not in system]
    bad += [f"fixed setting '{k}': {v!r} is not a value the program accepts" for k, v in system.items() if k in OPTIONS + EXTRA + ("udpPacketBytes",) and not _ok(k, v)]
    if "queuePkts" in knobs and all(k in knobs or k in system for k in ("queuePktsUdp", "queuePktsTcp")):  # a knob that changes nothing makes tests that test nothing
        bad.append("'queuePkts' is a knob, but both queues have their own length (queuePktsUdp, queuePktsTcp), so it would change nothing: fix it, or leave one queue without its own length")
    for k, s in knobs.items():
        if k not in KNOBS or not isinstance(s, dict):
            continue
        if not isinstance(s.get("meaning"), str) or not s["meaning"].strip():
            bad.append(f"knob '{k}' needs a meaning (one line the model reads)")
        if "step" in s and ("choices" in s or k not in STEPPED):
            bad.append(f"knob '{k}': a step is for a numeric knob (not for one with choices, a rate or a time)")
        if "choices" in s:
            if not isinstance(s["choices"], list) or not s["choices"] or not all(_ok(k, c) for c in s["choices"]) or s.get("default") not in s["choices"]:
                bad.append(f"knob '{k}' needs a list of acceptable choices and a default that is one of them")
        elif not all(x in s and _ok(k, s[x]) for x in ("min", "max", "default")):
            bad.append(f"knob '{k}' needs min, max and default, each a value the program accepts (or a list of choices)")
        elif not num(k, s["min"]) <= num(k, s["default"]) <= num(k, s["max"]) or num(k, s["min"]) == num(k, s["max"]):
            bad.append(f"knob '{k}' needs min < max and a default between them")
        elif "step" in s:  # optional: the model's values are rounded to it, counted from the knob's min
            whole = type(s["min"]) is int and type(s["max"]) is int
            if k not in STEPPED or type(s["step"]) not in (int, float) or not 0 < s["step"] <= s["max"] - s["min"] or (whole and type(s["step"]) is not int):
                bad.append(f"knob '{k}': a step is a number above 0 and at most max - min, for a numeric knob (a whole number where the knob is one)")
    if goal.get("kind") == "given":
        t = goal.get("target") if isinstance(goal.get("target"), dict) else {}
        c = goal.get("conditions")
        if t.get("measure") not in MANIFEST["outputs"] or t.get("direction") not in ("max", "min"):
            bad.append("a given goal needs a target: a measure that is one of the outputs, and a direction max or min")
        if not isinstance(c, list) or not all(isinstance(x, str) and x.strip() for x in c):
            bad.append("a given goal needs a list of conditions, each a text (the list may be empty)")
        if "tolerance" in goal and (type(goal["tolerance"]) not in (int, float) or not 0 < goal["tolerance"] < 100):
            bad.append("goal.tolerance is a number of per cent above 0 and below 100: two results closer than this count as equal")
    elif goal.get("kind") != "open":
        bad.append("goal.kind must be open or given")
    bad += [f"limits.{k} must be a whole number of at least 1" for k in ("simulations", "simulations_per_experiment") if type(limits.get(k)) is not int or limits[k] < 1]
    used = set(re.findall(r"\{(\w+)\}", b["description"])) if isinstance(b.get("description"), str) else set()
    bad += [f"the description uses {{{k}}}, which is not one of the brief's settings" for k in sorted(used - set(system) - set(knobs))]
    if bad:
        raise ValueError(f"brief {brief_id}: " + "; ".join(bad))
    fill = lambda m: str(system[m.group(1)]) if m.group(1) in system else f"the knob {m.group(1)}"
    return {**b, "task": b["task"] if b.get("task") is not None else task_text(b), "description": re.sub(r"\{(\w+)\}", fill, b["description"])}

def _check_network_brief(b, brief_id):
    """check_brief for a brief that has "topology" (network.py). Its settings are the network's, by address
    (l1.rate, udp.rate, l1.queue.parts.udp, ...), and the four of a simulation that belong to no object (duration, seed,
    and optionally tcpInitCwnd, tcpBufBytes). The network holds each setting's fixed value; "knobs" names, by address,
    those the model may change (a knob's default is used in place of the network's value); "system" holds only the
    simulation's own settings. Its measures are made from the network."""
    t, knobs, system, goal, limits = b.get("topology"), *(b.get(k) if isinstance(b.get(k), dict) else {} for k in ("knobs", "system", "goal", "limits"))
    bad = [] if b.get("id") == brief_id and re.fullmatch(r"[A-Za-z0-9_-]{1,60}", str(brief_id)) else ["id must equal the file name (letters, digits, - and _)"]
    if not isinstance(b.get("description"), str) or not b["description"].strip():
        bad.append("'description' must be a text")
    if b.get("task") is not None and (not isinstance(b["task"], str) or not b["task"].strip()):
        bad.append("'task' must be a text, or be left out: the harness then writes it from the aim and the settings")
    bad += network.problems(t)
    if bad:
        raise ValueError(f"brief {brief_id}: " + "; ".join(bad))
    have, outs = network.settings(t), network.outputs(t)
    bad += [f"'{k}' is not a setting of this network (its settings: {', '.join(have)}) nor of a simulation ({', '.join(network.RUN)})" for k in list(knobs) + list(system) if k not in have and k not in network.RUN]
    bad += [f"'{k}' is a setting of the network: its fixed value stands in the network, not in system" for k in system if k in have]
    bad += [f"'{k}' is both fixed (system) and adjustable (knobs)" for k in knobs if k in system]
    bad += [f"'{k}' is missing: give it a fixed value (system) or make it a knob" for k in ("duration", "seed") if k not in knobs and k not in system]
    bad += [f"fixed setting '{k}': {v!r} is not a value the program accepts" for k, v in system.items() if k in network.RUN and not (type(v) in (int, float) and v > 0 if k == "duration" else network.ok(k, v))]
    num = lambda k, v: network.rate_bps(v) if network.kind(k) == "rate" else network.seconds(v) if network.kind(k) == "time" else v
    for k, s in knobs.items():
        if (k not in have and k not in network.RUN) or not isinstance(s, dict):
            continue
        fine = (lambda v: type(v) in (int, float) and v > 0) if k == "duration" else (lambda v: network.ok(k, v))
        numeric = network.kind(k) in ("int", "number")
        if not isinstance(s.get("meaning"), str) or not s["meaning"].strip():
            bad.append(f"knob '{k}' needs a meaning (one line the model reads)")
        if "step" in s and ("choices" in s or not numeric):
            bad.append(f"knob '{k}': a step is for a numeric knob (not for one with choices, a rate or a time)")
        if network.kind(k) == "choice" or "choices" in s:
            if network.kind(k) != "choice" or not isinstance(s.get("choices"), list) or not s["choices"] or not all(fine(c) for c in s["choices"]) or s.get("default") not in s["choices"]:
                bad.append(f"knob '{k}' needs a list of acceptable choices and a default that is one of them" if network.kind(k) == "choice" else f"knob '{k}' is not a setting with choices")
        elif not all(x in s and fine(s[x]) for x in ("min", "max", "default")):
            bad.append(f"knob '{k}' needs min, max and default, each a value the program accepts")
        elif not num(k, s["min"]) <= num(k, s["default"]) <= num(k, s["max"]) or num(k, s["min"]) == num(k, s["max"]):
            bad.append(f"knob '{k}' needs min < max and a default between them")
        elif "step" in s and numeric:
            whole = type(s["min"]) is int and type(s["max"]) is int
            if type(s["step"]) not in (int, float) or not 0 < s["step"] <= s["max"] - s["min"] or (whole and type(s["step"]) is not int):
                bad.append(f"knob '{k}': a step is a number above 0 and at most max - min (a whole number where the knob is one)")
    if "structure" in b:
        bad += network.structure_problems(b["structure"], t)
    if not bad:  # the network as a session starts it: every knob at its default
        try:
            bad += network.problems(network.with_values(t, {k: s["default"] for k, s in knobs.items() if k in have}))
        except (ValueError, KeyError, TypeError) as e:
            bad.append(f"the network cannot be built with the knobs at their defaults: {e}")
    if goal.get("kind") == "given":
        tg, c = goal.get("target") if isinstance(goal.get("target"), dict) else {}, goal.get("conditions")
        if tg.get("measure") not in outs or tg.get("direction") not in ("max", "min"):
            bad.append(f"a given goal needs a target: a measure that is one of the outputs ({', '.join(outs)}), and a direction max or min")
        if not isinstance(c, list) or not all(isinstance(x, str) and x.strip() for x in c):
            bad.append("a given goal needs a list of conditions, each a text (the list may be empty)")
        if "tolerance" in goal and (type(goal["tolerance"]) not in (int, float) or not 0 < goal["tolerance"] < 100):
            bad.append("goal.tolerance is a number of per cent above 0 and below 100: two results closer than this count as equal")
    elif goal.get("kind") != "open":
        bad.append("goal.kind must be open or given")
    bad += [f"limits.{k} must be a whole number of at least 1" for k in ("simulations", "simulations_per_experiment") if type(limits.get(k)) is not int or limits[k] < 1]
    used = set(re.findall(r"\{([\w.]+)\}", b["description"]))
    bad += [f"the description uses {{{k}}}, which is not one of the brief's settings" for k in sorted(used - set(have) - set(system) - set(knobs))]
    if bad:
        raise ValueError(f"brief {brief_id}: " + "; ".join(bad))
    fill = lambda m: f"the knob {m.group(1)}" if m.group(1) in knobs else str(system[m.group(1)] if m.group(1) in system else have[m.group(1)])
    return {**b, "task": b["task"] if b.get("task") is not None else task_text(b), "description": re.sub(r"\{([\w.]+)\}", fill, b["description"])}


def load_brief(brief_id):
    """briefs/<id>.json, checked, with its description filled in."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", str(brief_id)) or not (BRIEFS / f"{brief_id}.json").is_file():
        raise ValueError(f"unknown brief {brief_id!r}")
    return check_brief(json.loads((BRIEFS / f"{brief_id}.json").read_text()), brief_id)

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
        if given.get("topology"):  # a brief with a network has measures of its own, and its series has other columns
            given["outputs"] = network.outputs(given["topology"])
            given["tools"] = network.tools_told(given["tools"])
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

class Missing(ValueError):
    """A design of the model's experiment that does not state every knob of the brief."""

def clamp(params, brief=None, design=None):
    """Keep only the brief's knobs and force each into its range. A setting the brief fixes (system) is not the
    model's to change: the brief's value is used. Returns (clean, {param: [asked, used]}).
    design: the label of a design of the model's experiment. Such a design states every knob of the brief (the answer
    format requires it; this is the guard): a missing knob raises Missing. Without design, a knob left out keeps the
    brief's default: the harness's own baseline, the operator's runs and sweeps, the recommendation of a report."""
    b = brief or BRIEF
    if design is not None and [k for k in b["knobs"] if k not in params]:
        raise Missing(f"design `{design}` does not state " + ", ".join(f"`{k}`" for k in b["knobs"] if k not in params))
    clean, clamps = {}, {k: [v, b["system"][k]] for k, v in params.items() if k in b["system"] and v != b["system"][k]}
    if b.get("topology"):  # a setting the network fixes is not the model's to change either: the network's value is used
        have = network.settings(b["topology"])
        clamps.update({k: [v, have[k]] for k, v in params.items() if k in have and k not in b["knobs"] and v != have[k]})
    for k, spec in b["knobs"].items():
        if k not in params:
            continue
        v = params[k]
        if "choices" in spec:
            nv = v if v in spec["choices"] else spec["default"]
        elif kind(k, b) == "rate":
            bps = min(max(_rate_bps(v), _rate_bps(spec["min"])), _rate_bps(spec["max"]))
            nv = f"{int(round(bps / 1e6))}Mbps"
            if abs(bps - _rate_bps(v)) < 1:
                nv = str(v).strip()
        elif kind(k, b) == "time":  # a time with its unit: inside the range it is kept as written, outside it the range's end is used
            sec = _seconds(v)
            nv = spec["min"] if sec < _seconds(spec["min"]) else spec["max"] if sec > _seconds(spec["max"]) else str(v).strip()
        else:
            nv = min(max(float(v), spec["min"]), spec["max"])
            if spec.get("step"):  # rounded to the knob's step, counted from its min; never past its max
                n = round((nv - spec["min"]) / spec["step"])
                while spec["min"] + n * spec["step"] > spec["max"] + 1e-12:
                    n -= 1
                nv = round(spec["min"] + n * spec["step"], 10)
            nv = int(round(nv)) if isinstance(spec["min"], int) else nv
        if nv != v:
            clamps[k] = [v, nv]
        clean[k] = nv
    return clean, clamps

def _seconds(s):
    m = re.fullmatch(r"\s*([0-9.]+)\s*(ns|us|ms|s)\s*", str(s))
    if not m:
        raise ValueError(f"bad time {s!r}")
    return float(m.group(1)) * {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0}[m.group(2)]


def options(clean, brief=None):
    """Every option the program is started with: the brief's fixed settings, its knobs' defaults, then the chosen values."""
    b = brief or BRIEF
    if b.get("topology"):  # a network: its fixed settings stand in the network itself; here the simulation's own, the knobs' defaults, the chosen values
        return {**{k: v for k, v in b["system"].items() if k in network.RUN}, **{k: s["default"] for k, s in b["knobs"].items()}, **clean}
    return {**{k: v for k, v in b["system"].items() if k in OPTIONS + EXTRA}, **{k: s["default"] for k, s in b["knobs"].items()}, **clean}

def same(opts):
    """The settings and the seed of a simulation in a form that is equal exactly when the simulation would be the same
    (an option of EXTRA that was not given counts as not given: within one brief it is given always or never)."""
    if "linkRate" not in opts:  # the settings of a network, by address: every one of them, each as a number where it is one
        val = lambda k, v: network.rate_bps(v) if network.kind(k) == "rate" else network.seconds(v) if network.kind(k) == "time" else float(v) if type(v) in (int, float) else str(v)
        return tuple((k, val(k, opts[k])) for k in sorted(opts))
    return tuple((k, _rate_bps(opts[k]) if k in RATES else _seconds(opts[k]) if k == "linkDelay" else float(opts[k]) if type(opts[k]) in (int, float) else str(opts[k])) for k in OPTIONS + EXTRA if k in OPTIONS or k in opts)

def run_many(param_sets, structures=None):
    """Several simulations at once, each in its own runs/<id>/ of the session: clamp, start the built program for all
    of them, wait, parse the metrics, append to the session's runs/index.json in order. One result per set, in order.
    structures: for a brief with a network whose structure the model may change, the changes of each simulation
    (network.apply), or None; a simulation that has some is run on the changed network, which its result names."""
    RUNS = _runs()
    first = max([int(p.name[1:]) for p in RUNS.iterdir() if re.fullmatch(r"r\d{3}", p.name)], default=0) + 1
    jobs, results, deadline = [], [], time.time() + RUN_TIMEOUT
    nets = {}
    for i, params in enumerate(param_sets):
        clean, clamps = clamp(params)
        rid = f"r{first + i:03d}"
        out = RUNS / rid
        out.mkdir()
        if structures and structures[i]:
            nets[rid] = network.apply(BRIEF["topology"], structures[i])
        proc = subprocess.Popen(command(options(clean), out, topology=nets.get(rid)), cwd=out, env={"LD_LIBRARY_PATH": str(NS3 / "build/lib"), "TWOHOSTS_SCHED": POLICY}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        jobs.append((rid, clean, clamps, out, time.time(), proc))
    for rid, clean, clamps, out, t0, proc in jobs:
        try:
            said = proc.communicate(timeout=max(1, deadline - time.time()))[0]
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            said = f"no result after {RUN_TIMEOUT} s"
        res = {"id": rid, "params": clean, "clamped": clamps, "seconds": round(time.time() - t0, 1), **({"topology": nets[rid]} if rid in nets else {})}
        if proc.returncode or not (out / "metrics.json").exists():
            results.append({**res, "error": (said or f"exit {proc.returncode}")[-800:]})
            continue
        res.update(metrics=json.loads((out / "metrics.json").read_text()), used=json.loads((out / "params.json").read_text()))
        with (RUNS / "index.json").open("a") as f:
            f.write(json.dumps({"id": rid, "params": res["used"], "metrics": res["metrics"]}) + "\n")
        results.append(res)
    return results

def run(params):
    """One simulation: see run_many."""
    return run_many([params])[0]

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
    if not (_dir(run_id) / "flowmon.xml").is_file():
        return "this simulation has no packet trace (the program that builds a network writes none)"
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
