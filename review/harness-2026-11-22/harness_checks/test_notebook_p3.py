"""The harness side of ~/project/NOTEBOOK_VIEW.md, Part 3 (Steps A2 and B), as scripted sessions in a scratch copy:
a knob's step (the model's value is rounded to it and the rounding recorded as a clamp), a goal's tolerance (score.py:
"at the best, within the tolerance"), and link rate, link delay and MTU as knobs a brief may open to the model.
    python3 -I test_notebook_p3.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new; it gets a copy of s006 with the answer key, the sweep tables and the operator's lines, so
that score.py can run there. Simulations are real ns-3 runs."""
import json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks/keys").mkdir(parents=True); (P / "checks/sweeps").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
shutil.copytree(REAL / "sessions/s006", P / "sessions/s006", ignore=shutil.ignore_patterns("drafts.jsonl", "flowmon.xml", "series.csv"))
shutil.copy(REAL / "checks/keys/two-hosts-udp-demand.json", P / "checks/keys/"); key = json.loads((REAL / "checks/keys/two-hosts-udp-demand.json").read_text())
for pol in key["per_scheduling_policy"].values(): shutil.copytree(REAL / "checks/sweeps" / pol["sweep"], P / "checks/sweeps" / pol["sweep"])
(P / "checks/operator.jsonl").write_text("".join(l + "\n" for l in (REAL / "checks/operator.jsonl").read_text().splitlines() if '"s006"' in l))
ENV = {**os.environ, "HOME": str(SCR / "home")}
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, brief, answers, *flags):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps(answers))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env=ENV, capture_output=True, text=True, timeout=1200)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    led = [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
    return led, json.loads((P / "sessions" / sid / "session.json").read_text())
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led, turn: [(r["body"].get("part"), r["body"].get("reason")) for r in of(led, "note", turn) if "part" in r["body"]]
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def ex(runs, varied, question="what the settings do"): return {"kind": "explore", "tests": [], "question": question, "varied": list(varied), "control": None, "runs": runs, "decision_rules": []}
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import importlib; tools = importlib.import_module("tools"); loop = importlib.import_module("loop")
base = json.loads((REAL / "briefs/two-hosts-open.json").read_text())
def save(bid, change):
    b = json.loads(json.dumps(base)); b["id"] = bid; change(b); (P / "briefs" / f"{bid}.json").write_text(json.dumps(b, indent=1) + "\n"); return tools.load_brief(bid)

# ================================================================== a knob's step
print("A STEP  (Step A2)")
def step(b): b["knobs"]["weightUdp"]["step"] = 0.01
bs = save("t-step", step)
K = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
led, meta = session("p1", "t-step", [turn(experiment=ex([{"label": "a", "params": {"weightUdp": 0.3034, **K}}, {"label": "b", "params": {"weightUdp": 0.4051, **K}}, {"label": "c", "params": {"weightUdp": 0.3, **K}}, {"label": "d", "params": {"weightUdp": 0.955, **K}}], ["weightUdp"]))])
x = of(led, "experiment", 1)[0]["body"]; runs = {r["label"]: r for r in x["runs"]}; sims = {r["body"]["label"]: r["body"] for r in of(led, "simulation", 1)}; n = notes(led, 1)
say(runs["a"]["params"]["weightUdp"] == 0.3 and runs["a"]["clamped"] == {"weightUdp": [0.3034, 0.3]} and sims["a"]["params"]["weightUdp"] == 0.3,
    f"a brief with a ratio step of 0.01: the design at 0.3034 runs at {sims['a']['params']['weightUdp']} and the rounding is recorded as a clamp: {runs['a']['clamped']}")
say(runs["b"]["params"]["weightUdp"] == 0.41 and runs["b"]["clamped"] == {"weightUdp": [0.4051, 0.41]} and runs["d"]["params"]["weightUdp"] == 0.95 and runs["d"]["clamped"] == {"weightUdp": [0.955, 0.95]},
    f"0.4051 runs at {runs['b']['params']['weightUdp']}; 0.955 (past the range) at {runs['d']['params']['weightUdp']}: {runs['d']['clamped']}")
say(("design c", "design `c` has the same settings and seed as `a`; give it different settings or remove it") in n and "c" not in runs, f"two designs that round to the same value are one simulation, and the later one is refused: {[q for q in n if q[0] == 'design c']}")
say(meta["given"]["knobs"]["weightUdp"]["step"] == 0.01 and '"step": 0.01' in json.dumps(meta["given"]["knobs"]["weightUdp"]), "the step is in the brief the model is shown, with the knob's range")
bad = []
for what, ch in (("a step larger than the range", lambda b: b["knobs"]["weightUdp"].update(step=2)), ("a step of 0", lambda b: b["knobs"]["weightUdp"].update(step=0)), ("a step for a knob with choices", lambda b: b["knobs"]["tcpVariant"].update(step=1)),
                 ("a step that is not whole for a whole-number knob", lambda b: b["knobs"]["queuePkts"].update(step=0.5)), ("a step for a rate", lambda b: b["knobs"]["udpRate"].update(step=5))):
    try: save("t-bad", ch); bad.append(what)
    except ValueError: pass
say(not bad, "a brief with a step that makes no sense is refused (larger than the range, 0, on a knob with choices, not whole on a whole-number knob, on a rate)" + (f": accepted {bad}" if bad else ""))

# ================================================================== link delay as a knob
print("LINK DELAY AS A KNOB  (Step B)")
def delay(b):
    del b["system"]["linkDelay"]; b["knobs"]["linkDelay"] = {"min": "10us", "max": "10ms", "default": "50us", "meaning": "one-way delay of the link, e.g. '200us'"}
    b["description"] = b["description"].replace("with a one-way delay of {linkDelay}", "with a one-way delay that is a setting (linkDelay)")
bd = save("t-delay", delay)
fmt = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), bd)["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["params"]
say(fmt["required"] == list(bd["knobs"]) and "linkDelay" in fmt["required"] and fmt["properties"]["linkDelay"] == {"type": "string"}, f"the answer format of that brief requires linkDelay in every design: {fmt['required']}")
D = dict(weightUdp=0.5, **K)
led, meta = session("p2", "t-delay", [turn(experiment=ex([{"label": "near", "params": {**D, "linkDelay": "50us"}}, {"label": "far", "params": {**D, "linkDelay": "5ms"}}, {"label": "too_far", "params": {**D, "linkDelay": "2s"}}, {"label": "none", "params": dict(D)}], ["linkDelay"]))])
x = of(led, "experiment", 1)[0]["body"]; runs = {r["label"]: r for r in x["runs"]}; sims = {r["body"]["label"]: r["body"] for r in of(led, "simulation", 1)}; n = notes(led, 1)
used = {l: json.loads((P / "sessions/p2/runs" / sims[l]["run_id"] / "params.json").read_text()).get("linkDelay") for l in sims if not sims[l].get("same_as")}
say(all("linkDelay" in r["params"] for r in x["runs"]) and list(runs) == ["near", "far", "too_far"] and ("design none", "design `none` does not state `linkDelay`") in n, f"a scripted session on it: every accepted design states linkDelay ({ {l: r['params']['linkDelay'] for l, r in runs.items()} }); the design without it is refused: {[q for q in n if q[0] == 'design none']}")
say(used.get("far") in ("5ms", "+5ms", "+5e+06ns") or str(used.get("far")).startswith(("5ms", "+5")) and runs["too_far"]["params"]["linkDelay"] == "10ms" and runs["too_far"]["clamped"] == {"linkDelay": ["2s", "10ms"]}, f"the simulator ran with it (params.json of “far”: {used.get('far')}); a delay outside the range is clamped and recorded: {runs['too_far']['clamped']}")
t0 = {l: sims[l]["metrics"].get("tcp_goodput_bps") for l in sims}
say(t0["far"] != t0["near"], f"the delay reaches the simulation: with 5 ms instead of 50 us the result differs (TCP goodput {t0['near'] / 1e6:.1f} against {t0['far'] / 1e6:.1f} Mbps)")
for k, spec, a, want in (("linkRate", {"min": "100Mbps", "max": "10Gbps", "default": "1Gbps", "meaning": "rate of the link"}, "20Gbps", "10000Mbps"), ("mtu", {"min": 1428, "max": 1500, "default": 1500, "meaning": "largest packet"}, 9000, 1500)):
    def ch(b, k=k, spec=spec):
        del b["system"][k]; b["knobs"][k] = spec
        b["description"] = b["description"].replace("{" + k + "}", k)
    try: bb = save(f"t-{k.lower()}", ch); clean, clamps = tools.clamp({kk: s["default"] for kk, s in bb["knobs"].items()} | {k: a}, bb); ok = clean[k] == want and clamps == {k: [a, want]}
    except ValueError as e: ok, clean, clamps = False, str(e), None
    say(ok, f"{k} can be a knob too: a brief with it is accepted, and {a!r} is clamped to {want!r}: {clamps}")

# ================================================================== a goal's tolerance
print("A TOLERANCE  (Step A2)")
def run_score(*a):
    r = subprocess.run([sys.executable, str(P / "harness/score.py"), "s006", *a], env=ENV, capture_output=True, text=True, timeout=900); return r, json.loads((P / "checks/scores/s006.json").read_text()) if (P / "checks/scores/s006.json").is_file() else {}
r, sc = run_score()
say(r.returncode == 0 and "tolerance_per_cent" not in sc and abs(sc["gap_on_target"] - (-47494.0)) < 1, f"s006 scored as before when no tolerance is given: gap {sc.get('gap_on_target')} bps, no line about a tolerance")
r, sc = run_score("--tolerance", "1")
say(r.returncode == 0 and sc.get("against_the_best") == "at the best, within the tolerance" and sc.get("within_the_tolerance") is True and sc.get("tolerance_per_cent") == 1.0 and sc.get("tolerance_from") == "entered by the operator" and "TOLERANCE 1%" in r.stdout,
    f"a tolerance of 1% entered by the operator scores s006 as “{sc.get('against_the_best')}” ({[l for l in r.stdout.splitlines() if l.startswith('TOLERANCE')]})")
m = json.loads((P / "sessions/s006/session.json").read_text()); m["given"]["goal"]["tolerance"] = 1; (P / "sessions/s006/session.json").write_text(json.dumps(m, indent=1) + "\n")
r, sc = run_score()
say(r.returncode == 0 and sc.get("against_the_best") == "at the best, within the tolerance" and sc.get("tolerance_from") == "the brief", f"a goal with a 1% tolerance in the session's brief (scripted here in the scratch copy) scores s006 as “{sc.get('against_the_best')}”, tolerance from {sc.get('tolerance_from')}")
r, sc = run_score("--tolerance", "0.000001")
say(sc.get("within_the_tolerance") is True, f"s006's recommendation is better than the sweep's best row (a negative gap), so it is within any tolerance: {sc.get('against_the_best')}")
def tol(b): b["goal"] = {"kind": "given", "target": {"measure": "tcp_goodput_bps", "direction": "max"}, "conditions": ["udp_loss_frac <= 0.01"], "tolerance": 1}
bt = save("t-tol", tol); bad = []
for what, t in (("0", 0), ("100", 100), ("a text", "1%")):
    try: save("t-bad", lambda b, t=t: (tol(b), b["goal"].update(tolerance=t))); bad.append(what)
    except ValueError: pass
try: save("t-bad", lambda b: b["goal"].update(tolerance=1)); open_ok = True
except ValueError: open_ok = False
say(bt["goal"]["tolerance"] == 1 and not bad, f"a brief whose given goal has a tolerance of 1 (per cent) is accepted and shown to the model in the brief; 0, 100 and a text are refused" + (f": accepted {bad}" if bad else ""))
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
