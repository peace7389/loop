"""Measurements of relations, and help to make them (2026-11-22, the operator: the researcher should come up with flexible, creative measurements on
demand). On copies of the real s048's recorded runs (r008: its series alone; r001, r010: with their probes), no simulation:
  - measure has three more statistics: crossings (how often a quantity crosses level), corr (how closely it moves with a second one, `with`) and
    lag (the seconds by which `with` trails it, with the correlation there); each refuses what it lacks (corr without with, crossings without level),
    and an argument measure does not take is named;
  - an expression it cannot read is refused with every quantity it can use: the series' and, once the probe exists, the probe's (until then the
    series' alone, which hid the probe's quantities);
  - an experiment may define such a measurement (the answer format has the statistics and `with`; measurement_problem checks them);
  - the tool's description and the instructions give examples of combined measurements, in every arm.
python3 -I test_measure_relations.py SCRATCH_DIR [HARNESS_DIR]"""
import json, os, shutil, sys
from pathlib import Path
REAL = Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions/s048/runs").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
for r in ("r001", "r008", "r010"): shutil.copytree(REAL / "sessions/s048/runs" / r, P / "sessions/s048/runs" / r)
shutil.copy(REAL / "sessions/s048/session.json", P / "sessions/s048/session.json"); shutil.copy(REAL / "sessions/s048/runs/index.json", P / "sessions/s048/runs/index.json")
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import loop, tools
if "corr" not in getattr(tools, "MEASURE_STATS", ()):   # part 2 (2026-11-22) is not in this harness (the deployed one leaves it out)
    print("RESULT: SKIP the measurements of relations (part 2) are not in this harness"); sys.exit(0)
tools.SESSION = P / "sessions/s048"; brief = json.loads((P / "sessions/s048/session.json").read_text())["given"]; tools.BRIEF = brief
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def M(run, of, stat, **k):
    out = tools.measure(run, of, stat, **k)
    try: return json.loads(out)
    except ValueError: return out
print("MEASUREMENTS OF RELATIONS")
cr = M("r010", "l1_q_udp", "crossings", level=50); co = M("r010", "tcp_inflight", "corr", **{"with": "tcp_cwnd"}); lg = M("r010", "tcp_cwnd", "lag", **{"with": "tcp_inflight"})
say(isinstance(cr, dict) and isinstance(cr["value"], int) and cr["value"] >= 0 and isinstance(co, dict) and co["value"] is not None and -1 <= co["value"] <= 1 and co.get("with") == "tcp_cwnd"
    and isinstance(lg, dict) and isinstance(lg["value"], (int, float)) and lg.get("corr_at_lag") is not None and lg.get("searched_s", 0) > 0,
    f"crossings of UDP's queue at 50 packets: {cr['value'] if isinstance(cr, dict) else cr}; corr of TCP's bytes in flight with its window: {co['value'] if isinstance(co, dict) else co}; "
    f"lag of its window behind the bytes in flight: {lg['value'] if isinstance(lg, dict) else lg} s (corr there {lg.get('corr_at_lag') if isinstance(lg, dict) else None}, searched ±{lg.get('searched_s') if isinstance(lg, dict) else None} s)")
e1, e2, e3 = M("r010", "tcp_rtt_ms", "corr"), M("r010", "tcp_rtt_ms", "crossings"), M("r010", "tcp_rtt_ms", "mean", foo=1)
say(all(isinstance(x, str) for x in (e1, e2, e3)) and "needs with" in e1 and "needs level" in e2 and "foo" in e3 and "with" in e3, f"each refuses what it lacks: “{e1[:60]}”, “{e2[:60]}”, “{e3[:70]}”")
e4 = M("r010", "log(tcp_rtt_ms)", "mean"); e5 = M("r008", "log(udp_bps)", "mean")
say(isinstance(e4, str) and "of the probe (" in e4 and "tcp_rtt_ms" in e4 and isinstance(e5, str) and "of the probe" not in e5,
    "an expression it cannot read is refused with every quantity it can use: the probe's too where the probe exists (r010), the series' alone where it does not (r008)")
ex = lambda ms: {"kind": "test", "tests": ["H1"], "runs": [], "measurements": ms}
mm = lambda **k: {"name": "m1", "of": "tcp_inflight", "stat": "corr", "t_from": None, "t_to": None, "level": None, "with": "tcp_cwnd", **k}
ok1, no1, no2 = loop.measurement_problem(ex([mm()]), brief), loop.measurement_problem(ex([mm(**{"with": None})]), brief), loop.measurement_problem(ex([mm(stat="crossings", **{"with": None})]), brief)
item = json.loads((P / "harness/schema.json").read_text())
def find(o):
    if isinstance(o, dict):
        if o.get("type") == "object" and {"name", "of", "stat"} <= set(o.get("properties", {})): yield o
        for v in o.values(): yield from find(v)
    elif isinstance(o, list):
        for v in o: yield from find(v)
its = list(find(item))
say(ok1 is None and no1 and "needs with" in no1 and no2 and "needs level" in no2 and its and all({"crossings", "corr", "lag"} <= set(i["properties"]["stat"]["enum"]) and "with" in i["required"] for i in its),
    f"an experiment may define such a measurement (the answer format has the three and `with`); one without with or level is refused: “{no1}”, “{no2}”")
man = json.loads((P / "harness/manifest.json").read_text()); full = (P / "harness/prompt.txt").read_text(); plain = loop.plain_prompt(full)
ex_ = "tcp_inflight / min(tcp_cwnd, tcp_rwnd)"
say(ex_ in json.dumps(man) and "corr" in json.dumps(man) and ex_ in full and ex_ in plain and ex_ in loop.LEAN_PROMPT,
    "the tool's description and the instructions of every arm (ordinary, plain, supervised) give examples of combined measurements, and name corr and lag")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
