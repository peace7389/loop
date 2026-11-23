"""Measurements the researcher defines, produced by the simulator without changing any result (2026-11-18, the operator).
  - the tool probe runs a simulation that already ran again with the program's probe (trace sinks only) and keeps its finer record only when the
    result is byte for byte the same; measure then reads its columns (a round-trip time, the receiver's window) as it reads the series;
  - an experiment may define measurements of its own; its simulations are run with the probe (the first also without it, and the two compared), the
    values stand with each simulation and in its evidence line, and a decision rule and a need name them like an output: the harness checks them;
  - a rule on such a measurement may be about simulations that already ran: nothing is simulated, the budget is untouched, and the harness makes the
    finer record of that earlier simulation itself;
  - a measurement that names no recorded column is refused with the columns there are; the same on a brief with a network (the program net).
Scripted sessions.     python3 -I test_measure.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new. Simulations are real ns-3 runs of 2 measured seconds."""
import json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
ENV = {**os.environ, "HOME": str(SCR / "home")}
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, brief, answers, *flags):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps(answers))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env=ENV, capture_output=True, text=True, timeout=1500)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    led = [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
    return led, json.loads((P / "sessions" / sid / "session.json").read_text())
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led, turn: [(r["body"].get("part"), r["body"].get("reason")) for r in of(led, "note", turn) if "part" in r["body"]]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w, **over): return {"label": label, "params": {"weightUdp": w, **KN, **over}}
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def hyp(text): return {"text": text, "question": "Is it so?", "why": "It decides the answer.", "prediction": "yes", "follows_from": ["brief"]}
M = lambda name, of, stat, **k: {"name": name, "of": of, "stat": stat, "t_from": None, "t_to": None, "level": None, **k}
def test(h, rule, runs, ms): return {"kind": "test", "tests": [h], "question": "", "varied": ["weightUdp"] if len(runs) > 1 else [], "control": None, "runs": runs, "measurements": ms,
                                     "decision_rules": [{"for": h, "decision_rule": rule, "rival": "something else limits it", "rival_predicts": "failed"}]}
ANSWERS = [
 # 1: a finer look at the baseline (r001), three measurements over it, one before the probe exists
 turn(requests=[{"tool": "measure", "args": {"run_id": "r001", "of": "rtt_ms", "stat": "mean"}}, {"tool": "probe", "args": {"run_id": "r001"}}, {"tool": "measure", "args": {"run_id": "r001", "of": "rwnd", "stat": "max"}}]),
 # 2: a test whose rule is about a measurement of its own, on two new simulations
 turn(requests=[{"tool": "measure", "args": {"run_id": "r001", "of": "inflight / rwnd", "stat": "p95"}}],
      hypotheses=[hyp("the receiver's window stays at one megabyte whatever the part")], experiment=test("H1", "rwnd_max@a == rwnd_max@b AND rwnd_max@a >= 1000000", [d("a", 0.3), d("b", 0.7)], [M("rwnd_max", "rwnd", "max"), M("wait_tcp", "wait_band1_ms", "p95")])),
 # 3: a rule on a new measurement of a simulation that already ran: nothing is simulated
 turn(verdicts=[{"for": "H1", "result": "supported", "because": "C1 held", "next": "look at the round trip"}], hypotheses=[hyp("the round trip stays below five milliseconds at the part 0.3")],
      experiment=test("H2", "rtt_mean@a < 5", [d("a", 0.3)], [M("rtt_mean", "rtt_ms", "mean", t_from=2, t_to=4)])),
 # 4: a measurement that names nothing a simulation records
 turn(verdicts=[{"for": "H2", "result": "supported", "because": "C2 held", "next": "stop"}], hypotheses=[hyp("the jitter is small")],
      experiment=test("H3", "jit@c < 1", [d("c", 0.5)], [M("jit", "jitter_ms", "mean")])),
]
print("MEASUREMENTS OF THE RESEARCHER'S OWN")
led, meta = session("m1", "two-hosts-open-2", ANSWERS)
S = P / "sessions/m1"; fmt = json.loads((S / "format_sent.json").read_text())
rs = [r["body"]["result"] for r in of(led, "result", 1)]; pr = json.loads(rs[1]) if rs[1].startswith("{") else {}
log = [json.loads(l) for l in (S / "probes.jsonl").read_text().splitlines()]; idx = {json.loads(l)["id"]: json.loads(l) for l in (S / "runs/index.json").read_text().splitlines()}
say(rs[0].startswith("error: rtt_ms is not recorded") and "probe(run_id)" in rs[0] and pr.get("same_result") is True and {"rtt_ms", "rwnd", "inflight", "wait_band1_ms", "devq"} <= set(pr.get("columns") or []) and pr["samples"] > 250
    and json.loads(rs[2])["value"] == 1048576 and (S / "runs/r001/probe.csv").is_file() and not (S / "runs/r001/_probe").exists() and json.loads((S / "runs/r001/metrics.json").read_text()) == idx["r001"]["metrics"] and log[0] == {**log[0], "run": "r001", "same_result": True},
    f"before a probe a round-trip time is “not recorded” and the answer says how to get it; probe runs the baseline again with taps that only listen, keeps {pr.get('samples')} samples of {len(pr.get('columns') or [])} columns "
    f"because the result was the same, and measure then reads the receiver's window: {json.loads(rs[2])['value']:.0f} bytes; the run's measures are untouched")
x1 = of(led, "experiment", 2)[0]; s1 = of(led, "simulation", 2); e1 = of(led, "evidence", 2)[0]; c1 = of(led, "check", 2)[0]
say([m["name"] for m in x1["body"].get("measurements", [])] == ["rwnd_max", "wait_tcp"] and len(s1) == 2 and all(q["body"]["own"] == ["rwnd_max", "wait_tcp"] and q["body"]["metrics"]["rwnd_max"] == 1048576 and "probe" not in q["body"] for q in s1)
    and all("rwnd_max=1048576" in l and "wait_tcp=" in l for l in e1["body"]["lines"]) and c1["body"]["result"] == "held" and "1048576" in c1["body"]["with_numbers"] and not list((S / "runs").glob("*/_plain"))
    and all((S / "runs" / q["body"]["run_id"] / "probe.csv").is_file() for q in s1) and "measurements" in fmt["properties"]["experiment"]["anyOf"][0]["required"] and "probe" in fmt["properties"]["requests"]["items"]["properties"]["tool"]["enum"],
    f"an experiment defines two measurements of its own: its simulations are run with the probe (the first also without, and the two gave the same result), each simulation holds them with its outputs "
    f"(rwnd_max {s1[0]['body']['metrics'].get('rwnd_max')}, wait_tcp {s1[0]['body']['metrics'].get('wait_tcp')} ms), its evidence line names them, and the harness checks the rule that names them: {c1['body']['with_numbers']} : {c1['body']['result']}")
x2 = of(led, "experiment", 3); s2 = of(led, "simulation", 3); c2 = of(led, "check", 3); left = [r["body"]["simulations_left"] for r in of(led, "turn")]
say(len(x2) == 1 and len(s2) == 1 and s2[0]["body"].get("same_as") == s1[0]["id"] and 0 < s2[0]["body"]["metrics"]["rtt_mean"] < 5 and c2 and c2[0]["body"]["result"] == "held" and left[2] == left[3] and not [q for q in notes(led, 3) if q[0].startswith("decision rule")],
    f"a rule on a new measurement of a simulation that already ran is a test: nothing is simulated ({s2[0]['body'].get('same_as')} is returned, {left[2]} simulations left before and {left[3]} after), "
    f"the measurement is made from that simulation's finer record (rtt_mean {s2[0]['body']['metrics'].get('rtt_mean')} ms between 2 s and 4 s) and the rule is checked: {c2[0]['body']['result'] if c2 else None}")
n4 = [q for q in notes(led, 4) if q[0] == "experiment"]
say(len(n4) == 1 and "measurement jit: of must be a column a simulation records" in n4[0][1] and "rtt_ms" in n4[0][1] and "it only listens" in n4[0][1] and not of(led, "experiment", 4),
    f"a measurement that names no recorded column is refused with the columns there are: “{n4[0][1][:120] if n4 else None}…”")
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import importlib; loop = importlib.import_module("loop")
prompt = (P / "harness/prompt.txt").read_text()
say("   - measurements:" in prompt and "rwnd_mean@label" in prompt and "probe makes a finer record" in prompt and "probe makes a finer record" in loop.supervised_prompt(prompt) and "measurements:" in loop.plain_prompt(prompt) and "measurements" in loop.plain_format(json.loads((P / "harness/schema.json").read_text()))["properties"]["experiment"]["anyOf"][0]["properties"],
    "the instructions say how to define a measurement, how a rule names it, and what probe and measure do; the three arms' instructions and formats are made with them")
# a brief with a network: the program net has the same probe, by the network's own names
def dn(label, part): return {"label": label, "params": {"lc.queue.parts.fa": part, "lc.queue.length": 100, "fa.type": "TcpCubic"}}
NET = [turn(hypotheses=[hyp("packets of fa wait longer when its part is small")], experiment={"kind": "test", "tests": ["H1"], "question": "", "varied": ["lc.queue.parts.fa"], "control": None, "runs": [dn("small", 0.1), dn("large", 2)],
                                                                                         "measurements": [M("fa_wait", "lc_wait_fa_ms", "p95"), M("fa_rtt", "fa_rtt_ms", "mean")],
                                                                                         "decision_rules": [{"for": "H1", "decision_rule": "fa_wait@small > fa_wait@large", "rival": "the queue is never the limit", "rival_predicts": "failed"}]})]
led2, meta2 = session("m2", "three-hosts", NET); sn = of(led2, "simulation", 1); cn = of(led2, "check", 1)
say(len(sn) == 2 and all(q["body"]["own"] == ["fa_rtt", "fa_wait"] for q in sn) and cn and cn[0]["body"]["result"] in ("held", "failed") and "fa_wait" in cn[0]["body"]["decision_rule"] and sn[0]["body"]["metrics"]["fa_rtt"] > 2,
    f"on a brief with a network the measurements are taken by the network's names: fa waits {sn[0]['body']['metrics'].get('fa_wait')} ms (95th per cent) with the small part and {sn[1]['body']['metrics'].get('fa_wait')} ms with the large one, "
    f"its round trip {sn[0]['body']['metrics'].get('fa_rtt')} ms and {sn[1]['body']['metrics'].get('fa_rtt')} ms; the rule on them: {cn[0]['body']['result'] if cn else None}")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
