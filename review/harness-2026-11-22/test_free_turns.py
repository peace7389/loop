"""Free turns after the budget is used up (2026-11-22, after s048: its receiver-window guess needed only measurements of runs it already had, and
the last turn took only the report). When the last simulation is used, the researcher has FREE_TURNS more turns in which it may look (requests)
and test on simulations already run (a test whose simulations all ran: their results are returned, a measurement of its own is computed from
what they recorded); a test that needs a new simulation and a budget_request are refused, each with the reason; then the report-only last turn
as before. A report given in a free turn ends the session as one given by the model.
  - the ordinary arm, a budget of 1: turn 1 spends it; turns 2 and 3 are free (the turn says so and how many are left): a request is answered,
    a test on a simulation already run is checked with no new simulation; a test that needs one is refused, and so is a budget_request; turn 4
    takes only the report;
  - the arm "plain", a budget of 1: a free turn answers a request and refuses an experiment that needs a new simulation; a report in the next
    free turn ends the session ("done by the model").
Scripted sessions.     python3 -I test_free_turns.py SCRATCH_DIR [HARNESS_DIR]
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
    S = P / "sessions" / sid
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    return led, json.loads((S / "session.json").read_text()), json.loads((S / "users_sent.json").read_text())
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led, turn: [(r["body"].get("part"), r["body"].get("reason")) for r in of(led, "note", turn) if "part" in r["body"]]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w, **over): return {"label": label, "params": {"weightUdp": w, **KN, **over}}
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def plain(**k): return {"observations": "read", "experiment": None, "report": None, "requests": [], "budget_request": None, "done": False, **k}
def hyp(text): return {"text": text, "question": "Is it so?", "why": "It decides the answer.", "prediction": "yes", "follows_from": ["brief"]}
M = lambda name, of, stat, **k: {"name": name, "of": of, "stat": stat, "t_from": None, "t_to": None, "level": None, **k}
def test(h, rule, runs, ms=()): return {"kind": "test", "tests": [h], "question": "", "varied": ["weightUdp"] if len(runs) > 1 else [], "control": None, "runs": runs, "measurements": list(ms),
                                        "decision_rules": [{"for": h, "decision_rule": rule, "rival": "something else limits it", "rival_predicts": "failed"}]}
REP = {"goal": "the larger UDP goodput", "recommendation": {"weightUdp": 0.7, **{k: v for k, v in KN.items() if k != "seed"}}, "expected": {"udp_goodput_bps": 685000000.0}, "no_difference": [], "limit": "UDP's part of the link: E1.",
       "explanation": "UDP's goodput follows its part of the link.", "holds_when": "as tested", "breaks_when": "other rates", "claims": [{"text": "A larger part gives UDP more.", "role": "supports", "evidence": ["E1"]}], "open_questions": []}
V = lambda h, c: {"for": h, "result": "supported", "because": f"{c} held", "next": "go on"}
print("FREE TURNS AFTER THE BUDGET IS USED UP")
led, meta, u = session("f1", "two-hosts-open-2", [
    turn(hypotheses=[hyp("UDP gets something at the part 0.3")], experiment=test("H1", "udp_goodput_bps@a > 1", [d("a", 0.3)])),
    turn(verdicts=[V("H1", "C1")], requests=[{"tool": "metrics", "args": {"run_id": "r002"}}], hypotheses=[hyp("the round trip stays below five milliseconds at the part 0.3")],
         experiment=test("H2", "rtt_mean@a < 5", [d("a", 0.3)], [M("rtt_mean", "rtt_ms", "mean", t_from=1, t_to=2)])),
    turn(verdicts=[V("H2", "C2")], hypotheses=[hyp("TCP gets more at the part 0.5")], experiment=test("H3", "tcp_goodput_bps@c > 1", [d("c", 0.5)]), budget_request={"simulations": 2, "why": "one more part"}),
    turn(report=REP, done=True)], "--budget", "1")
modes = [r["body"].get("last_turn") for r in of(led, "turn")]; runs = sorted({r["body"]["run_id"] for r in of(led, "simulation") if r["id"] != "S0"}); reused = [r for r in of(led, "note", 2) if r["body"].get("same_as")]
say(modes == [None, "free", "free", "budget"], f"a budget of 1, spent in turn 1: turns 2 and 3 are free, turn 4 is the last (the turn records say {modes})")
say("used up: all 1 simulations have run" in u[1] and "you have this turn and 1 more" in u[1] and "you have this turn to look" in u[2] and "THIS IS THE LAST TURN" in u[3],
    "each free turn says so and how many are left; the fourth is the last turn")
x2 = of(led, "experiment", 2); c2 = [c for c in of(led, "check", 2) if c["body"]["for"] == "H2"]
say(of(led, "result", 2) and x2 and c2 and c2[0]["body"]["result"] in ("held", "failed") and runs == ["r002"] and reused and "nothing was run again" in reused[0]["body"]["text"],
    f"turn 2 (free): a request is answered ({[r['id'] for r in of(led, 'result', 2)]}) and the test of H2 on the simulation already run is checked ({c2[0]['body']['result'] if c2 else None}) with no new simulation (runs of the session: {runs}; “{reused[0]['body']['text'][:70] if reused else None}…”)")
n3 = dict(notes(led, 3))
say(not of(led, "experiment", 3) and "the simulation budget is used up: in the turns before the report" in (n3.get("experiment") or "") and "once the budget is used up" in (n3.get("budget_request") or ""),
    f"turn 3 (free): a test that needs a new simulation is refused (“{(n3.get('experiment') or '')[:110]}…”) and so is a budget_request (“{n3.get('budget_request')}”)")
say(of(led, "report") and meta.get("how") == "all simulations used, report given in the last turn", f"turn 4 takes the report: {meta.get('how')}")
led, meta, u = session("p2", "two-hosts-open-2", [
    plain(experiment={"kind": "explore", "question": "What does UDP get at the part 0.3?", "varied": [], "control": None, "runs": [d("a", 0.3)]}),
    plain(requests=[{"tool": "metrics", "args": {"run_id": "r002"}}], experiment={"kind": "explore", "question": "And at a third?", "varied": [], "control": None, "runs": [d("c", 0.5)]}),
    plain(report=REP, done=True)], "--arm", "plain", "--budget", "1")
modes = [r["body"].get("last_turn") for r in of(led, "turn")]; n2 = dict(notes(led, 2))
say(modes == [None, "free", "free"] and of(led, "result", 2) and "the simulation budget is used up" in (n2.get("experiment") or "") and meta.get("how") == "done by the model",
    f"the arm “plain”: a free turn answers a request and refuses an experiment that needs a new simulation; a report in the next free turn ends the session ({modes}, {meta.get('how')})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
