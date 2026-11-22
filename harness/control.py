"""The operator's control server: the viewer's files, plus the few things the operator may start from the page.
It replaces the plain file server. Start it with:  python3 harness/control.py   (the page is http://127.0.0.1:8600/viewer/)

  GET  any file        the project's files, read-only, exactly as before
  GET  /api/status     what is running, the last lines of the session's output, "briefs" (the ids in briefs/) and
                       "sessions": every session folder (id, brief, records, experiments, first and last time, policy, model, running,
                       checks held and failed, the figures of session_figures.py, and from checks/: the score in short and the
                       reviewer's ticks and sign-off)
  GET  /api/sessions   that list alone
  GET  /api/agents?session=<id>   what the local model was given and wrote in that session, call by call (calls.jsonl; for an older session its
                       drafts, its accepted answers and the supervisor's records), for the page viewer/agents.html. Everyone who can read the
                       page may read it (2026-11-22, the operator: "everyone who sees the page"), view-only visitors from the network included.
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
  POST /api/judge      {session, n, judgement, note}: the operator's judgement (yes | no | unjudged) and note for item n of the
                       checklist of a scored session -> checks/scores/<session>.json, as score.py --judge writes it
  POST /api/review     {session, item, tick, note}: the reviewer's tick and note for one item of a session's page
                       -> checks/reviews/<session>.json (read back by the page as a file)
  POST /api/export     {session, operator}: that session as a folder that opens without a server (export_session.py) ->
                       checks/exports/<session>-<time>/ and a zip; never its drafts; operator-only data only with operator true
  POST /api/brief      {brief}: saves a NEW brief as briefs/<id>.json after the same check loop.py makes (tools.check_brief).
                       An id that already exists is refused: a brief is never overwritten.

Who writes what (the write-ownership rule):
  loop.py      its own session's folder, sessions/<id>/: session.json, ledger.jsonl, and runs/ through tools.run. Nothing else writes
               there, and no tool can read outside it. It also appends one line per run to checks/operator.jsonl
               (session, run, policy, seconds), which no tool reads. "policy" is the scheduling policy: how the scheduler
               divides the link, share or cap (records written before 2026-11-11 call it "mode"; both are read).
  control.py   checks/: checks/op-<timestamp>/ (one operator run), checks/control.jsonl (the list of those runs),
               checks/sessions/<id>.log (a session's terminal output), checks/sweeps/<id>/ (a sweep's table and
               status), checks/reviews/<session>.json (the reviewer's ticks and notes), checks/random.json (sessions whose policy
               the server chose), checks/exports/ (exported sessions); and briefs/<id>.json, new files only.
               It starts and stops loop.py and does nothing else.
  the viewer   nothing. Its Control page only calls the POST endpoints above.
An operator run is made by the built program directly, never by tools.run, so it never reaches a session's folder: no
tool the model has can see it. The scheduling policy reaches the simulation as the environment variable TWOHOSTS_SCHED only; the model never sees it.

Who may call it (since 2026-11-17, at the operator's word: the page is shared with the lab). The server listens on
127.0.0.1 only (there is no option to change that), so it is reached from this machine alone: by a browser here, or
through an SSH tunnel of somebody who has an account here. Every such account may use the page as the owner does: a POST
is accepted from any account of this machine, as application/json from this page only (so no other web page open in
the same browser can call it). The account is read from the connection (/proc/net/tcp; an SSH tunnel is opened by its
user's own sshd process); a connection whose account cannot be found is refused. Three rules keep people out of each
other's way:
  - one session at a time: a session is not started while another is running, wherever that one was started. The
    refusal and the page say which session is running and who started it;
  - a running session is stopped only by the account that started it, or by the owner (the account that runs this server);
  - every accepted POST is noted in checks/people.jsonl (time, account, what, the id it concerned). That file holds
    account names, so it is kept out of git and out of exports.
Looking from the network (since 2026-11-17, the operator: "I want my professor to be able to view it on webbrowser on
computer or mobile. Consider him has technion VPN"). Started with --network on, the server also answers on the
machine's network address, so that a browser on the campus network or its VPN opens the page with no tunnel:
http://<this machine>:8600/viewer/. Whoever comes that way can only look:
  - every POST is refused ("view only"): nothing is started, stopped, saved or marked from the network;
  - only the page's own material is given: viewer/, sessions/ (never drafts.jsonl), briefs/, trace/, checks/ (never
    people.jsonl, never exports/), and the three GET endpoints. Nothing else of the project folder, and no listing of
    a folder;
  - /api/status says view_only, and names no account as "you".
A connection from this machine itself (127.0.0.1: a browser here, or an SSH tunnel) is treated as before.
A personal link (since 2026-11-17, the operator: "I want my professor to be able to run new session and do everything
as me"). The owner makes one with `python3 harness/invite.py NAME`; it is the page's address with a long key
(?key=...). Opened once in a browser, the server keeps the key in a cookie of that browser and takes it out of the
address. A visitor from the network who shows a key of checks/access.json is that person, by name, and uses the page
as the owner does: starts sessions (one at a time, like everybody), stops any session started here, saves briefs,
reviews. Each thing done is noted with the name and "(by link)". The key travels over plain HTTP, so it is as safe
as the network it crosses; a line taken out of checks/access.json ends its link at once. The file is not in git, not
in an export, and is given to nobody over HTTP. Without a key a visitor from the network can only look, as before.
Without --network on the server listens on 127.0.0.1 only, as it always did (the scratch copies of the checks do).

drafts.jsonl and calls.jsonl are given to nobody as files over HTTP; what they hold is read through /api/agents, by the page viewer/agents.html. Everything else under the project folder is readable by
every account, as before. Parameters go through tools.clamp, like the model's.
Briefs (briefs/<id>.json) are the operator's: written by hand or saved from the page's brief editor.
Python standard library only."""
import argparse, csv, http.server, itertools, json, os, pwd, random, re, shutil, signal, socket, subprocess, sys, threading, time, urllib.parse
from pathlib import Path
import export_session, session_figures, tools

ROOT, H, CHECKS = tools.ROOT, tools.HARNESS, tools.ROOT / "checks"
BIN = tools.NS3 / "build/scratch/two-hosts/ns3.49-two-hosts-optimized"
LOOP = [sys.executable, str(H / "loop.py")]
HOST, PORT = "127.0.0.1", 8600
LOCK, RUN_LOCK = threading.Lock(), threading.Lock()
SESSION = {}  # the newest session started here, if any: id, proc, flags, started, log (the older control page shows this one)
STARTED = {}  # every session started here, by id (with "by": the account that started it); MAX_LOOPS: most loops running at the same time, wherever they were started
MAX_LOOPS = 1  # one session at a time since the page is shared (2026-11-17); until then 6 ran side by side
ACCESS = CHECKS / "access.json"  # {key: name}: the personal links (harness/invite.py). Whoever shows a key from the network is that person and uses the page as the owner does
VISITS, VISITS_LOCK, SEEN = CHECKS / "visits.jsonl", threading.Lock(), {}   # who opened the page and from where (2026-11-22, the operator: "Any other IPs who accessed the viewer? ... we should record from now"): not in git, not served to the network, not in exports
PEOPLE, PEOPLE_LOCK = CHECKS / "people.jsonl", threading.Lock()  # who did what through the page: one line per accepted POST (account names: not in git, not in exports)
CACHE = {}    # session id -> (file times, its row in /api/sessions)
SWEEP = {}    # the sweep running here, if any: id, thread, stop
SERVING = {}  # the port this server answers on, and whether it also answers on the network (main() sets both)
OPEN_TO_NETWORK = ("viewer", "sessions", "briefs", "trace", "checks")  # the folders a visitor from the network may read (the page's own material)
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


def account(uid):
    """The account name of a user id of this machine (the number as text when it has no name; None for None)."""
    if uid is None:
        return None
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


OWNER = account(os.getuid())  # the account that runs this server: the loops it starts run under it


def invited():
    """The personal links that hold now: {key: name}. Read each time, so a line added or taken out counts at once."""
    try:
        d = json.loads(ACCESS.read_text())
        return {k: str(v) for k, v in d.items() if isinstance(k, str) and len(k) >= 16} if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def noted(who, did, result):
    """One line in checks/people.jsonl for a POST that was carried out: when, which account, what, and the id it concerned."""
    thing = next((result[k] for k in ("id", "stopped", "stopping", "saved", "session") if isinstance(result, dict) and isinstance(result.get(k), str)), None)
    with PEOPLE_LOCK:
        PEOPLE.parent.mkdir(parents=True, exist_ok=True)
        with PEOPLE.open("a") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "account": who, "did": did, "id": thing}) + "\n")


def visited(h):
    """One line in checks/visits.jsonl for each page opened (an .html page, or the page's own address) and for the first request of each address and
    visitor in each hour (a page left open asks every minute; that is not written again): when, the address, who (the account of a connection from
    this machine, the name of a personal link, or none), what, the browser. It never stops a request."""
    try:
        path = urllib.parse.urlparse(h.path).path
        page = path.endswith((".html", "/viewer/", "/viewer")) or path == "/"
        who, ip, hour = h.person(), h.client_address[0], time.strftime("%Y-%m-%dT%H")
        if not page and SEEN.get((ip, who)) == hour:
            return
        SEEN[(ip, who)] = hour
        line = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "ip": ip, "who": who or ("this machine" if ip == "127.0.0.1" else "the network, without a personal link"),
                "what": f"{h.command} {path}" if page else f"first request this hour: {h.command} {path}", "browser": (h.headers.get("User-Agent") or "")[:160]}
        with VISITS_LOCK:
            VISITS.parent.mkdir(parents=True, exist_ok=True)
            with VISITS.open("a") as f:
                f.write(json.dumps(line) + "\n")
    except Exception:
        pass


def starters():
    """Session id -> the account that started it through the page (from checks/people.jsonl; a session started from a terminal is not in it)."""
    out = {}
    if PEOPLE.is_file():
        for line in PEOPLE.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("did") == "/api/session" and isinstance(r.get("id"), str):
                out.setdefault(r["id"], r.get("account"))
    return out


def agent_view(sid):
    """What the local model was given and wrote in one session, for the owner's page viewer/agents.html (GET /api/agents?session=<id>): every call
    of calls.jsonl (written since 2026-11-22: the agent, the messages it was given, what it wrote before its answer, its answer, its tokens); for an
    older session what was kept of its calls: drafts.jsonl, the accepted answers (answers.jsonl), the supervisor's records (supervisor.jsonl: what it
    was shown and what it answered), and each draft's counts in the ledger."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid or ""):
        raise Refused(400, "no such session")
    d = ROOT / "sessions" / sid
    if not d.is_dir():
        raise Refused(404, f"no session {sid}")
    def lines(name):
        f, out = d / name, []
        for line in (f.read_text(errors="replace").splitlines() if f.is_file() else []):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
        return out
    try:
        meta = json.loads((d / "session.json").read_text())
    except (OSError, ValueError):
        meta = {}
    counts = [{"id": r.get("id"), "turn": r.get("turn"), **{k: (r.get("body") or {}).get(k) for k in ("chars", "tokens", "finish_reason", "model")}}
              for r in lines("ledger.jsonl") if r.get("type") in ("draft", "scratch")]
    return {"session": sid, "model": meta.get("model"), "flags": meta.get("flags"), "started": meta.get("started"), "brief": meta.get("brief"),
            "running": any(i == sid for i, _ in running_now()), "calls": lines("calls.jsonl"), "drafts": lines("drafts.jsonl"),
            "answers": lines("answers.jsonl"), "supervisor": lines("supervisor.jsonl"), "counts": counts}

def running_now():
    """The sessions that are running, wherever they were started: [(id, the account that started it)]. A loop started from a terminal runs
    under the owner's account, so it is the owner's; so is one whose start is not in checks/people.jsonl."""
    by = starters()
    ids = sorted({i for i, x in STARTED.items() if x["proc"].poll() is None} | set(other_loops()))
    return [(i, (STARTED.get(i) or {}).get("by") or by.get(i) or OWNER) for i in ids]


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


def sessions(you=None, trusted=False):
    """One row per folder in sessions/, oldest first, read from the session's own files and checks/operator.jsonl.
    you: the account that asks. A row says who started the session through the page ("by"; a running session that nobody
    started through the page is the owner's) and whether the one who asks may stop it ("can_stop")."""
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
    by = starters()
    out = []
    for d in dirs:
        led, idx, score, review = d / "ledger.jsonl", d / "runs/index.json", CHECKS / "scores" / f"{d.name}.json", CHECKS / "reviews" / f"{d.name}.json"
        sig = tuple(p.stat().st_mtime if p.exists() else 0 for p in (led, idx, d / "session.json", score, review))
        if CACHE.get(d.name, (None,))[0] != sig:
            recs = lines(led)
            drafts = [r for r in recs if r["type"] in ("draft", "scratch")]
            shown = [r for r in recs if r["type"] not in ("draft", "scratch")]  # what the figures are counted from
            meta = json.loads((d / "session.json").read_text()) if (d / "session.json").is_file() else {}
            held, failed = session_figures.held_failed(shown)  # without the void checks (a decision rule that compared a simulation with itself)
            sc = json.loads(score.read_text()) if score.is_file() else None
            marks = json.loads(review.read_text()) if review.is_file() else {}
            CACHE[d.name] = (sig, {"id": d.name, "brief": meta.get("brief"), "records": len(recs), "runs": len(lines(idx)),
                "experiments": sum(r["type"] == "evidence" and r["id"] != "E0" for r in recs),
                "simulations": sum(r["type"] == "simulation" and r["id"] != "S0" and not (r.get("body") or {}).get("same_as") for r in recs),  # run, as the budget counts them
                "allowed": ((meta.get("given") or {}).get("limits") or {}).get("simulations") or (meta.get("flags") or {}).get("budget"),
                "turns": max([r["turn"] for r in recs], default=0), "held": held, "failed": failed,
                "started": recs[0].get("ts") if recs else None, "last": recs[-1].get("ts") if recs else None,
                "model": (drafts[-1]["body"].get("model") if drafts else None), "how": meta.get("how"), "report": meta.get("report"), "left_open": meta.get("left_open"),
                "has_report": any(r["type"] == "report" for r in recs),
                "vc": session_figures.verdicts_against_checks(shown),  # verdicts against checks: {row: {column: n}}
                "seq": session_figures.checks_in_order(shown),         # the checks in order: "hhh hf ..." (None: not recorded)
                "returned": session_figures.returned_simulations(shown),  # [returned from an earlier one, all simulations]
                "unnamed": session_figures.unnamed_simulations(shown),    # [named by no decision rule, simulations of the experiments that test]
                "void": session_figures.void_count(shown),                # [void checks, all checks]
                "findings": session_figures.findings_counts(shown),       # findings raised, how they ended, turns open (None: a session without findings, 2026-11-22)
                "guesses": session_figures.guess_reviews(shown),          # guesses accepted with a warning, restated, contested (None: before 2026-11-22)
                "rounds": session_figures.design_rounds(shown),           # the review of tests in rounds: proposed, rounds, approved first, repaired, contested, dropped (None: before 2026-11-22)
                "done": any(r["type"] == "report" or (r["type"] == "note" and (r.get("body") or {}).get("text") == "model declared done") for r in recs),
                # operator-only, from checks/: the score in short, and the reviewer's ticks and sign-off
                "score": sc and {"gap": sc.get("gap_on_target"), "part": sc.get("gap_as_part_of_best"), "target": (sc.get("goal") or {}).get("target"), "against": sc.get("against_the_best"),
                                 "holds": all((sc.get("conditions_hold_at_the_recommendation") or {}).values())},
                "review": {"n": len(marks), "ticked": sorted(k for k, m in marks.items() if m.get("tick") and k != "signoff"),
                           "signed": {"name": marks["signoff"].get("note"), "at": marks["signoff"].get("at")} if "signoff" in marks else None}})
        row = CACHE[d.name][1]
        secret = d.name in hidden and not row["score"]  # a policy the harness chose is shown only once the session is scored
        running = d.name in here or d.name in others
        who = (STARTED.get(d.name) or {}).get("by") or by.get(d.name) or (OWNER if running else None)
        out.append({**row, "policy": None if secret else policy.get(d.name), "policy_hidden": secret, "running": running, "stoppable": d.name in here,
                    "by": who, "can_stop": d.name in here and (trusted or you in (OWNER, who))})
    return out


NET_BRIEFS = {}  # brief id -> (file time, whether it has a network)


def network_briefs():
    """The ids of the saved briefs that have a network ("topology"), read once per change of a file."""
    out = []
    for p in sorted(tools.BRIEFS.glob("*.json")):
        t = p.stat().st_mtime
        if NET_BRIEFS.get(p.stem, (None,))[0] != t:
            try:
                NET_BRIEFS[p.stem] = (t, isinstance(json.loads(p.read_text()).get("topology"), dict))
            except (OSError, ValueError, AttributeError):
                NET_BRIEFS[p.stem] = (t, False)
        if NET_BRIEFS[p.stem][1]:
            out.append(p.stem)
    return out


def tail(path, n=600):
    try:
        return Path(path).read_text(errors="replace")[-n:]
    except OSError:
        return ""


def status(you=None, local=True, trusted=False):
    s = None
    if SESSION:
        rc = SESSION["proc"].poll()
        s = {"id": SESSION["id"], "pid": SESSION["proc"].pid, "running": rc is None, "returncode": rc, "flags": SESSION["flags"],
             "started": SESSION["started"], "output": tail(SESSION["log"])}
    count = lambda p: sum(1 for l in p.open() if l.strip()) if p.exists() else 0
    return {"control": True, "session": s, "other_loop": other_loop(), "run_busy": RUN_LOCK.locked(),
            # the page is shared: who asks, who runs the server, the sessions running now with who started each, and how somebody else reaches the page
            "you": you, "owner": OWNER, "running_now": [{"id": i, "by": w} for i, w in running_now()], "one_at_a_time": MAX_LOOPS == 1,
            "share": {"host": socket.getfqdn(), "port": SERVING.get("port", PORT), "network": bool(SERVING.get("network"))},  # network: the page can be opened without a tunnel, to look only
            "view_only": not (local or trusted),  # the one who asks came from the network without a personal link: nothing can be started or changed
            "by_link": bool(trusted and not local),  # the one who asks came through a personal link (harness/invite.py)
            "sessions": sessions(you, trusted), "briefs": sorted(p.stem for p in tools.BRIEFS.glob("*.json")),
            "network_briefs": network_briefs(),  # those of the briefs that have a network: the set-up page offers them to its builder, the others to the two-host form
            "operator_runs": count(CHECKS / "control.jsonl"),
            "sweeps": sorted(p.name for p in (CHECKS / "sweeps").iterdir() if (p / "status.json").is_file()) if (CHECKS / "sweeps").is_dir() else []}


def operator_run(body):
    """One simulation with the operator's settings, by the built program directly, into checks/op-<timestamp>/."""
    params, policy = body.get("params") or {}, body.get("policy", body.get("mode", "share"))
    try:
        brief = tools.load_brief(body.get("brief", tools.DEFAULT_BRIEF))
    except ValueError as e:
        raise Refused(400, str(e))
    if policy not in tools.policies(brief) or not isinstance(params, dict) or set(params) - set(brief["knobs"]) - set(brief["system"]):
        raise Refused(400, f"params must be settings of the brief and the scheduling policy must be one of {', '.join(tools.policies(brief))}")
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
        argv = tools.command(tools.options(clean, brief), out, brief)
        args = argv[1:]
        t0 = time.time()
        try:
            p = subprocess.run(argv, cwd=out, env={"LD_LIBRARY_PATH": str(tools.NS3 / "build/lib"), "TWOHOSTS_SCHED": policy}, capture_output=True, text=True, timeout=tools.RUN_TIMEOUT)
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
    net = {k: b[k] for k in ("topology", "structure") if isinstance(b.get(k), dict)}   # a brief with a network (network.py): the network, and whether the AI may change its structure
    b = {**{k: b.get(k) for k in ("id", "task", "description")}, **({"topology": net["topology"]} if "topology" in net else {}), "system": b.get("system"),   # only the fields a brief has, in the usual order
         "knobs": {k: {x: s[x] for x in ("min", "max", "choices", "default", "step", "meaning") if x in s} if isinstance(s, dict) else s for k, s in knobs.items()},
         "goal": b.get("goal"), "limits": b.get("limits"), **({"structure": net["structure"]} if "structure" in net else {})}
    if not (isinstance(b["task"], str) and b["task"].strip()):  # no task of its own: the harness writes it from the aim and the settings (tools.task_text), each time the brief is read
        del b["task"]
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
    cols = (["i", *tools.options({}, brief), *tools.outputs(brief), "seconds", "error"] if brief.get("topology") else   # a network: its simulation's settings and its knobs by address, then its own measures
            ["i", *tools.OPTIONS, *[k for k in tools.EXTRA if k in brief["knobs"] or k in brief["system"]], *tools.MANIFEST["outputs"], "seconds", "error"])  # an option a brief may leave out has a column only where the brief sets it
    rows, running, nxt, t_start, first = list(kept), {}, 0, time.time(), len(kept)
    with (folder / "table.csv").open("w", newline="") as f:
        out = csv.DictWriter(f, cols)
        out.writeheader()
        out.writerows(rows)
        while running or (nxt < len(combos) and not stop.is_set()):
            while nxt < len(combos) and len(running) < PARALLEL and not stop.is_set():
                opts, d = tools.options(combos[nxt], brief), folder / "runs" / str(nxt)
                d.mkdir(parents=True)
                proc = subprocess.Popen(tools.command(opts, d, brief), cwd=d, stdout=subprocess.DEVNULL, stderr=(d / "stderr.txt").open("w"),
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
    if policy not in tools.policies(brief) or not isinstance(grid, dict) or not grid or not all(isinstance(v, list) and v for v in grid.values()):
        raise Refused(400, f"a sweep needs policy ({' or '.join(tools.policies(brief))}) and grid: {{knob: [values, ...]}} with at least one value per knob")
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


def save_judgement(body):
    """The operator's judgement of one checklist item of a scored session (yes, no or unjudged) and a note: written into
    checks/scores/<session>.json, where score.py --judge writes it. score.py keeps both when the session is scored again."""
    sid, n, judgement, note = body.get("session"), body.get("n"), body.get("judgement"), body.get("note", "")
    if not (isinstance(sid, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid) and (tools.SESSIONS / sid).is_dir()):
        raise Refused(400, "session must be the id of an existing session")
    if type(n) is not int or judgement not in ("yes", "no", "unjudged") or not isinstance(note, str) or len(note) > 2000:
        raise Refused(400, "a judgement needs n (the number of the checklist item), judgement (yes, no or unjudged) and note (a text of at most 2000 characters)")
    path = CHECKS / "scores" / f"{sid}.json"
    with LOCK:
        if not path.is_file():
            raise Refused(400, f"{sid} has no score yet (harness/score.py {sid} writes it): only a scored session is judged")
        score = json.loads(path.read_text())
        item = next((c for c in score.get("checklist") or [] if c.get("n") == n), None)
        if item is None:
            raise Refused(400, f"the checklist of {sid} has no item {n}")
        item["judgement"] = judgement
        if note.strip():
            item["note"] = note
        else:
            item.pop("note", None)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(score, indent=1) + "\n")
        tmp.replace(path)
    return {"session": sid, "n": n, "judgement": judgement, "note": item.get("note", "")}


def export(body):
    """One session as a folder (and a zip) that opens without a server; operator-only data only when asked for."""
    sid = body.get("session")
    row = next((r for r in sessions() if r["id"] == sid), None) if isinstance(sid, str) else None
    if not row or type(body.get("operator", False)) is not bool:
        raise Refused(400, "an export needs session (the id of an existing session) and operator (true or false: include the operator-only data)")
    if row["running"]:
        raise Refused(409, f"session {sid} is still running: export it when it has ended")
    with LOCK:
        return export_session.make(sid, body.get("operator", False), row)


def start_session(body, who=None):
    """loop.py as a child process with the chosen flags; it then runs exactly as it does from a terminal. One session runs
    at a time (MAX_LOOPS): while one is running, wherever it was started, a new one is refused, and the refusal says which
    is running and who started it. who: the account that asks. With the scheduling policy "random" the server chooses share or cap itself and notes the session in
    checks/random.json: the session list then withholds its policy until the session has a score."""
    budget, draft, policy, base = body.get("budget"), body.get("draft", "on"), body.get("policy", body.get("mode", "share")), body.get("baseline", True)
    tokens, temp, arm = body.get("max_tokens"), body.get("temperature"), body.get("arm")
    if arm not in (None, "hypotheses", "supervised", "plain"):
        raise Refused(400, "arm is supervised (a researcher and a supervisor, a second AI that reviews each test and rules on its checks), hypotheses (one AI that judges its own tests) or plain (no hypothesis format); left out: hypotheses")
    if (budget is not None and (type(budget) is not int or budget < 1)) or draft not in ("on", "off") or policy not in ("share", "cap", "prio", "random") or type(base) is not bool:
        raise Refused(400, "budget must be a whole number of at least 1 (or left out: the brief's limit), draft on or off, policy (the scheduling policy) share, cap or random, baseline true or false")
    if (tokens is not None and (type(tokens) is not int or not 256 <= tokens <= 100000)) or (temp is not None and (type(temp) not in (int, float) or not 0 <= temp <= 2)):
        raise Refused(400, "max_tokens must be a whole number from 256 to 100000 and temperature a number from 0 to 2 (or left out: the loop's defaults)")
    sid, brief = body.get("session"), body.get("brief")
    sid_given = sid
    if sid is not None and not (isinstance(sid, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid) and (tools.SESSIONS / sid / "session.json").is_file()):
        raise Refused(400, "session must be the id of an existing session that has a session.json (leave it out to start a new one)")
    if brief is not None:
        try:
            given = tools.load_brief(brief)
        except ValueError as e:
            raise Refused(400, str(e))
        if policy == "prio" and "prio" not in tools.policies(given):
            raise Refused(400, "the scheduling policy prio (the first flow of a scheduler's list first) exists only for a brief that has a network")
    with LOCK:
        now = running_now()
        running = {i for i, _ in now}
        if len(running) >= MAX_LOOPS:
            raise Refused(409, (f"session {now[0][0]} is running, started by {now[0][1]}: one session runs at a time. A new one can start when it has ended" if MAX_LOOPS == 1
                                else f"{len(running)} sessions are running, and at most {MAX_LOOPS} run at the same time: wait for one to end"))
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
        flags = {"session": sid, "brief": brief, "budget": budget, "draft": draft, "max-tokens": tokens, "temperature": temp, "policy": chosen, "baseline": "on" if base else "off", "arm": arm if sid_given is None and arm not in (None, "hypotheses") else None}   # an existing session keeps its own arm
        cmd = LOOP + [x for k, v in flags.items() if v is not None for x in (f"--{k}", str(v))]
        with log.open("a") as f:
            f.write(" ".join(cmd) + "\n")
            f.flush()
            proc = subprocess.Popen(cmd, cwd=H, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        shown = {**flags, "policy": "chosen by the harness" if policy == "random" else chosen}  # what the page is told
        STARTED[sid] = {"id": sid, "proc": proc, "flags": shown, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "log": log, "by": who or OWNER}
        SESSION.clear()
        SESSION.update(STARTED[sid])
    time.sleep(1.5)  # a refused flag (a budget over the loop's ceiling, say) ends the loop at once: report it now
    if proc.poll() not in (None, 0):
        raise Refused(400, "the loop did not start: " + tail(log, 400).strip().splitlines()[-1])
    return {"id": sid, "pid": proc.pid, "flags": shown}


def stop_session(body=None, who=None, trusted=False):
    """Stops a session that was started here: the one named, or (the older page names none) the newest. who: the account
    that asks; only the account that started the session, or the owner, stops it."""
    with LOCK:
        sid = (body or {}).get("session") or (SESSION.get("id") if SESSION else None)
        x = STARTED.get(sid)
        if not x or x["proc"].poll() is not None:
            raise Refused(409, "no session started here is running" if not (body or {}).get("session") else f"session {sid} is not running, or was not started from this server (stop it where it was started)")
        if not trusted and who not in (OWNER, x.get("by")):
            raise Refused(403, f"session {sid} was started by {x.get('by')}: only {x.get('by')} or {OWNER}, who runs this page, can stop it")
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

    def end_headers(self):
        # a file of the page: the browser asks each time whether it has changed, so that nobody keeps reading an old copy of the page after a change
        if not any(h.lower().startswith(b"cache-control") for h in getattr(self, "_headers_buffer", [])):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def answer(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def local(self):
        """Whether the connection comes from this machine itself (a browser here, or an SSH tunnel), not from the network."""
        return self.client_address[0] == "127.0.0.1"

    def key(self):
        """The key of a personal link the request shows (its cookie, or ?key= in its address), if it is one that holds; else None."""
        shown = [c.split("=", 1)[1].strip() for c in (self.headers.get("Cookie") or "").split(";") if c.strip().startswith("th_key=")]
        shown += urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("key", [])
        links = invited()
        return next((k for k in shown if k in links), None)

    def person(self):
        """Who asks: the account of a connection from this machine; the name of a personal link shown from the network (with "(by link)"); None for any other visitor from the network."""
        if self.local():
            return account(peer_uid(self.client_address[1], self.server.server_address[1]))
        k = self.key()
        return f"{invited()[k]} (by link)" if k else None

    def send_head(self):
        """The file server's own step for GET and HEAD. drafts.jsonl is given to nobody: no page reads it. A visitor
        from the network gets the page's own material only (OPEN_TO_NETWORK), never the list of accounts or the exports."""
        path = urllib.parse.unquote(self.path.split("?")[0].split("#")[0])
        parts = [p for p in path.split("/") if p]
        if parts and parts[-1].lower() in ("drafts.jsonl", "calls.jsonl", "access.json"):
            self.send_error(404, "not given out by this server")
            return None
        if "key=" in self.path and not self.local():  # a personal link, opened: the key goes into a cookie of this browser and out of the address
            q = urllib.parse.urlparse(self.path)
            rest = urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(q.query, keep_blank_values=True) if k != "key"])
            self.send_response(302)
            if self.key():
                self.send_header("Set-Cookie", f"th_key={self.key()}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax")
            self.send_header("Location", (q.path if parts else "/viewer/") + ("?" + rest if rest else ""))
            self.end_headers()
            return None
        if not self.local():
            if not parts:  # the bare address: the page
                self.send_response(302)
                self.send_header("Location", "/viewer/")
                self.end_headers()
                return None
            page_reads = parts == ["harness", "manifest.json"]  # the set-up page reads the list of measures and tools from it
            if (parts[0] not in OPEN_TO_NETWORK and not page_reads) or ".." in parts or parts[-1].lower() in ("people.jsonl", "visits.jsonl") or parts[:2] == ["checks", "exports"]:
                self.send_error(404, "not given out over the network")
                return None
        return super().send_head()

    def list_directory(self, path):
        """A folder without an index page: listed for this machine itself, as always; not for a visitor from the network."""
        if not self.local():
            self.send_error(404, "folders are not listed over the network")
            return None
        return super().list_directory(path)

    def do_GET(self):
        visited(self)
        you, trusted = self.person(), not self.local() and self.key() is not None
        if self.path.split("?")[0] == "/api/status":
            return self.answer(200, status(you, self.local(), trusted))
        if self.path.split("?")[0] == "/api/sessions":
            return self.answer(200, sessions(you, trusted))
        if self.path.split("?")[0] == "/api/agents":   # what the local model was given and wrote: for everyone who can read the page (2026-11-22, the operator)
            try:
                return self.answer(200, agent_view((urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("session") or [""])[0]))
            except Refused as e:
                return self.answer(e.code, {"error": e.text})
        if self.path.split("?")[0].startswith("/api/sweep/"):
            try:
                return self.answer(200, sweep_status(self.path.split("?")[0].split("/")[3]))
            except Refused as e:
                return self.answer(e.code, {"error": e.text})
        super().do_GET()

    def do_POST(self):
        visited(self)
        try:
            trusted = not self.local() and self.key() is not None
            if not self.local() and not trusted:
                raise Refused(403, "view only: over the network this page can be read, but nothing can be started or changed. To use it fully, open it through a personal link from its owner, or through an SSH tunnel (the command is at the foot of the page)")
            who = self.person()
            if who is None:
                raise Refused(403, "refused: the account that opened this connection cannot be found, and everything started or changed here is noted with its account")
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
            do = {"/api/run": lambda: operator_run(body), "/api/session": lambda: start_session(body, who), "/api/stop": lambda: stop_session(body, who, trusted), "/api/brief": lambda: save_brief(body), "/api/sweep": lambda: start_sweep(body), "/api/review": lambda: save_review(body), "/api/judge": lambda: save_judgement(body), "/api/export": lambda: export(body)}.get(self.path)
            m = re.fullmatch(r"/api/sweep/([^/]+)/stop", self.path)
            if m:
                do = lambda: stop_sweep(m.group(1))
            if not do:
                raise Refused(404, "no such endpoint")
            result = do()
            noted(who, re.sub(r"/api/sweep/[^/]+/stop", "/api/sweep/stop", self.path), result)
            self.answer(200, result)
        except Refused as e:
            self.answer(e.code, {"error": e.text})


def main():
    ap = argparse.ArgumentParser(description="Serve the viewer and the operator's three controls on 127.0.0.1.")
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--network", choices=["on", "off"], default="off", help="on: also answer on the machine's network address, to look only (no POST, the page's own material only). Default off: 127.0.0.1 alone")
    a = ap.parse_args()
    SERVING.update(port=a.port, network=a.network == "on")
    srv = http.server.ThreadingHTTPServer(("0.0.0.0" if a.network == "on" else HOST, a.port), Handler)
    print(f"control.py: http://{HOST}:{a.port}/viewer/  (files of {ROOT}; run by {OWNER}; every account of this machine may use the page; one session at a time)"
          + (f"; to look only, from the network: http://{socket.getfqdn()}:{a.port}/viewer/" if a.network == "on" else ""), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
