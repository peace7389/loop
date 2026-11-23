"""s052 (2026-11-22, 19:20): in the arm "supervised" a repaired test whose simulation carried a network change that cannot be applied (the model
filled an "add a queue" change with the run's own label in every field) stopped the session. A repair is now checked in the order of the normal
path, and whatever the harness cannot check in a repair refuses that round with its reason. Scripted session with stand-in agents (scripted.py) on
the brief again_again (a network the researcher may change: a shared queue at l1), real ns-3 runs:
  R  round 1: the supervisor sends the test back; round 2: the repair carries s052's change: refused by the harness with the network's reason, and
     the session goes on; round 3: a repair without a change: approved, run and ruled on in the same turn; the session ends only when the script has
     no more answers.
  U  a change written correctly that asks for more than the brief allows (s056 H10, a third flow) is refused for the limit, without the example of
     an unrelated change that a change written wrongly gets.
python3 -I test_repair_structure.py SCRATCH_DIR [HARNESS_DIR]"""
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
def run(l, q, t="TcpCubic"): return {"label": l, "params": {"l1.queue.length": q, "tcp.type": t}}
RULE = {"for": "H1", "decision_rule": "tcp_goodput_bps@q1000 > tcp_goodput_bps@q50", "rival": "the UDP flow fills any queue, so TCP gets nothing either way", "rival_predicts": "failed"}
T1 = {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None,
      "whys": [{"about": ["E0"], "result": "TCP gets 0 bps at the default", "guess": "the shared queue is always full of UDP packets", "revises": None}],
      "hypotheses": [{"from_why": "Y1", "text": "TCP gets more with a 1000-packet queue than with 50"}],
      "experiment": {"kind": "test", "tests": ["H1"], "question": "", "runs": [run("q50", 50), run("q1000", 1000)], "measurements": [], "decision_rules": [RULE]}}
BAD = {"decision_rule": "tcp_goodput_bps@q1000 > tcp_goodput_bps@q4_cubic", "rival": RULE["rival"], "rival_predicts": "failed",   # s052's call 21: a garbled change in the run of a repair; its rule names that run (a run no rule names is dropped before it is read, since 2026-11-23)
       "runs": [{**run("q4_cubic", 1000), "structure": [{"do": "add_queue", "id": "q4_cubic", "kind": "queue", "from": "q4_cubic", "to": "q4_cubic", "on": "q4_cubic", "rate": "q4_cubic", "type": "q4_cubic", "app": "bulk"}]},
                run("q1000", 1000)]}
GOOD = {"decision_rule": RULE["decision_rule"], "rival": RULE["rival"], "rival_predicts": "failed", "runs": []}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
REV = lambda defect="none", feedback="": {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": "failed",
                                          "doubt_if": "nothing", "because": "reasoned", "defect": defect, "feedback": feedback}
RULING = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
f = SCR / "r1.answers.json"; f.write_text(json.dumps({"answers": [T1, BAD, GOOD], "supervisor": [G, REV("confounded", "Compare two queue lengths only."), REV(), RULING]}))
r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "again_again", "--session", "r1", "--arm", "supervised", "--budget", "8"], env=ENV, capture_output=True, text=True, timeout=1500)
S = P / "sessions" / "r1"
led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()] if (S / "ledger.jsonl").is_file() else []
meta = json.loads((S / "session.json").read_text()) if (S / "session.json").is_file() else {}
print("R  A REPAIR WHOSE NETWORK CHANGE CANNOT BE APPLIED")
rounds = [(r["body"]["round"], r["body"]["decision"], r["by"]) for r in led if r["type"] == "review" and r["body"].get("gate") == "design" and r["body"].get("for") == "H1"]
r2 = next((r["body"] for r in led if r["type"] == "review" and r["body"].get("gate") == "design" and r["body"].get("round") == 2), {})
say("Traceback" not in r.stderr and meta.get("how") == "model server error", f"the session did not stop on the repair: it ended when the script had no more answers ({meta.get('how')}){' ' + r.stderr[-1500:] if 'Traceback' in r.stderr else ''}")
say(rounds == [(1, "sent_back", "supervisor"), (2, "sent_back", "harness"), (3, "approved", "supervisor")] and "structure cannot be used" in str(r2.get("feedback")),
    f"round 1 sent back by the supervisor, round 2 refused by the harness with the network's reason (“{str(r2.get('feedback'))[:120]}”), round 3 approved: {rounds}")
x = [r for r in led if r["type"] == "experiment" and r["turn"] == 1]; v = [r for r in led if r["type"] == "verdict" and r["body"].get("for") == "H1"]
say(x and x[-1]["body"]["tests"] == ["H1"] and not any((q.get("structure") or []) for q in x[-1]["body"]["runs"]) and v,
    f"the repaired test of round 3 ran in turn 1 without a network change and was ruled on ({[q['label'] for q in x[-1]['body']['runs']] if x else None}, {v[0]['body']['result'] if v else None})")
print("U  A CHANGE WRITTEN CORRECTLY THAT ASKS FOR MORE THAN THE BRIEF ALLOWS (s056 H10: a third flow)")
CODE = r'''
import json, sys
sys.path.insert(0, ".")
import loop
b = json.load(open(sys.argv[1]))
E = lambda es: [{k: (e.get(k) or "") for k in loop.network.EDIT} for e in es]
probe = [{"do": "add_flow", "id": "probe", "kind": "tcp", "from": "sender", "to": "receiver", "type": "TcpCubic"}]
wrong = [{"do": "add_queue", "id": "l1", "kind": "scheduler", "on": "sender"}]
print(json.dumps([loop.structure_problem(E(probe), b), loop.structure_problem(E(wrong), b)]))
'''
u = subprocess.run([sys.executable, "-I", "-c", CODE, str(P / "briefs/after_fix.json")], cwd=P / "harness", env=ENV, capture_output=True, text=True, timeout=300)
try:
    lim, form = json.loads(u.stdout.strip().splitlines()[-1])
except (ValueError, IndexError):
    lim, form = "", ""
    print(u.stderr[-1500:])
say("3 flows: this brief allows at most 2" in lim and "written correctly, but this brief does not allow it" in lim and "for example" not in lim,
    f"a third flow is refused for the limit, with no example of an unrelated change: {lim}")
say("A change written correctly for this network, for example:" in (form or ""), f"a change written wrongly still gets the example: {(form or '')[:140]}")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
