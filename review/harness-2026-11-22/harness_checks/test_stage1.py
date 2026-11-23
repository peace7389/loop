"""Stage 1 of the coherence audit (2026-11-22): the fixes that keep the record whole and the session running. Scripted sessions (scripted.py), real
ns-3 runs:
  A  the supervisor is shown its answer's fields (what each holds) in every request, and a planned simulation's network change in the test review
     (s053 H1's scheduler was reviewed as "unchanged from the default");
  B  a ruling after a round the harness refused and an unreadable last review: the test runs unreviewed and is ruled on (it stopped the session with
     KeyError 'doubt_if');
  C  an experiment's own measurement defined at no sample (it divided by zero and stopped the session after the simulations ran): its rule is "not
     checked" and the session goes on; min() of one value is refused when the rule is read;
  D  the last turn: a reply with only a finding decision ends the session (it came again without end);
  E  a continued session counts the simulations it used (it got its whole budget again);
  F  the model server fails on the supervisor's first look at the baseline: a note, and the session goes on (it stopped unrecorded);
  G  the arm "hypotheses": a reply with 5 requests: 3 are answered and a note says 2 were not (they were dropped silently).
python3 -I test_stage1.py SCRATCH_DIR [HARNESS_DIR]"""
import json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, answers, sup, arm="supervised", brief="two-hosts-open-2", budget=8, sets=None):
    f = SCR / f"{sid}.{len(list(SCR.glob(sid + '.*')))}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup}))
    env = {**os.environ, "HOME": str(SCR / "home"), **({"SCRIPTED_SET": json.dumps(sets)} if sets else {})}
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, "--budget", str(budget)] + (["--arm", arm] if arm != "hypotheses" else []),
                       env=env, capture_output=True, text=True, timeout=1500)
    S = P / "sessions" / sid
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    rd = lambda n: json.loads((S / n).read_text()) if (S / n).is_file() else []
    return led, rd("supervisor_sent.json"), json.loads((S / "session.json").read_text()), r.stderr
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led: [str(r["body"].get("text") or "") for r in of(led, "note")]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
REV = {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": "failed", "doubt_if": "nothing", "because": "reasoned", "defect": "none", "feedback": ""}
BACK = {**REV, "defect": "confounded", "feedback": "Another setting hides the effect."}
RUL = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
RIV = {"rival": "UDP's own sending rate limits it", "rival_predicts": "failed"}
def turn(why=True, hyp=True, ex=None, **k):
    return {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None,
            "whys": [{"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "revises": None}] if why else [],
            "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part"}] if hyp else [], "experiment": ex, **k}
TEST = {"kind": "test", "tests": ["H1"], "question": "", "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [], "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", **RIV}]}

print("A  THE SUPERVISOR'S FIELDS, AND A NETWORK CHANGE IN THE TEST REVIEW")
sched = [{"do": "remove", "id": "l1", "kind": "queue", "on": "sender"}, {"do": "add_queue", "id": "l1", "kind": "scheduler", "on": "sender"}]
NET = {"kind": "test", "tests": ["H1"], "question": "", "measurements": [],
       "runs": [{"label": "fifo", "params": {"l1.queue.length": 100, "tcp.type": "TcpCubic"}}, {"label": "sched", "params": {"l1.queue.length": 100, "tcp.type": "TcpCubic"}, "structure": sched}],
       "decision_rules": [{"for": "H1", "decision_rule": "tcp_goodput_bps@sched > tcp_goodput_bps@fifo", "rival": "UDP fills any queue", "rival_predicts": "failed"}]}
TA = {**turn(ex=NET), "whys": [{"about": ["E0"], "result": "TCP gets 0 bps at the default", "guess": "the shared FIFO is always full of UDP", "revises": None}],
      "hypotheses": [{"from_why": "Y1", "text": "a scheduler gives TCP a share"}]}
led, sup, meta, err = session("a1", [TA], [G, REV, RUL], brief="again_again")
review = next((u for u in sup if "THE SIMULATIONS PLANNED" in u), "")
say("network changed: " in review and "sched {" in review and "YOUR ANSWER: one JSON object with these fields, in this order:" in review and "stronger_rival (text):" in review and "rival_is_weak (true or false):" in review,
    "the test review shows the planned scheduler (network changed: ...) and lists its answer's fields with what each holds")
say(sup and all("YOUR ANSWER: one JSON object with these fields" in u for u in sup) and any("records_show (text):" in u for u in sup) and any("shows (text):" in u for u in sup),
    f"every one of the {len(sup)} supervisor requests lists its fields: the guess review, the look, the test review, the ruling")

print("B  A RULING AFTER A ROUND THE HARNESS REFUSED, AND AN UNREADABLE LAST REVIEW")
BAD = {"decision_rule": "udp_goodput_bps@b != udp_goodput_bps@a", **RIV, "runs": []}
GOOD = {"decision_rule": "udp_goodput_bps@b > 1.2 * udp_goodput_bps@a", **RIV, "runs": []}
led, sup, meta, err = session("b1", [turn(ex=TEST), BAD, GOOD], [G, BACK, {"_raw": "not a JSON object"}, RUL])
rounds = [(r["body"]["round"], r["body"]["decision"], r["by"]) for r in of(led, "review") if r["body"].get("gate") == "design"]
v = [(r["body"]["for"], r["body"]["result"]) for r in of(led, "verdict")]
say("Traceback" not in err and "harness error" not in meta.get("how", "") and rounds[:2] == [(1, "sent_back", "supervisor"), (2, "sent_back", "harness")] and ("H1", "supported") in v,
    f"round 1 by the supervisor, round 2 refused by the harness, round 3's review unreadable: the test runs unreviewed and is ruled on ({rounds}; {v}; ended: {meta.get('how')})")

print("C  A MEASUREMENT DEFINED AT NO SAMPLE, AND min() OF ONE VALUE")
M = [{"name": "qm", "of": "tcp_bps / (udp_bps - udp_bps)", "stat": "mean", "t_from": None, "t_to": None, "level": None}]
TC = turn(ex={**TEST, "measurements": M, "decision_rules": [{"for": "H1", "decision_rule": "qm@b > qm@a", **RIV}]})
led, sup, meta, err = session("c1", [TC], [G, REV, RUL])
ck = [(r["body"]["for"], r["body"]["result"]) for r in of(led, "check")]
say("Traceback" not in err and "harness error" not in meta.get("how", "") and ck == [("H1", "not checked")] and meta.get("how") == "model server error",
    f"the measurement is defined at no sample: its rule is not checked ({ck}), and the session goes on to the next turn (ended: {meta.get('how')})")
TM = turn(ex={**TEST, "decision_rules": [{"for": "H1", "decision_rule": "min(udp_goodput_bps@b) > udp_goodput_bps@a", **RIV}]})
led, sup, meta, err = session("c2", [TM], [G])
say(any("min() takes two values or more" in n for n in notes(led)) and "Traceback" not in err, "min() of one value is refused when the rule is read, with the reason")

print("D  THE LAST TURN: A REPLY WITH ONLY A FINDING DECISION")
DEC = {**turn(why=False, hyp=False), "decisions": [{"id": "F1", "action": "park", "refs": [], "reason": "the part matters more now"}]}
led, sup, meta, err = session("d1", ["not JSON"] * 6 + [DEC] * 6, [], sets={"CONTINUES": 0})   # an unusable reply is asked for once more in its turn: two replies per turn
lasts = [r["turn"] for r in of(led, "turn") if r["body"].get("last_turn") == "report"]
say(meta.get("how") == "3 turns in a row without a usable answer" and len(lasts) == 1,
    f"after three unusable turns the last one takes only the report; a reply with only a decision ends the session there ({meta.get('how')}; last turns {lasts})")

print("E  A CONTINUED SESSION COUNTS WHAT IT USED")
led, sup, meta, err = session("e1", [turn(ex=TEST)], [G, REV, RUL], budget=6)
used = [r for r in of(led, "simulation") if r["turn"] >= 1]
led, sup, meta, err = session("e1", [turn(why=False, hyp=False)], [], budget=6)
u = [r["body"]["simulations_left"] for r in of(led, "turn")]
say(len(used) == 2 and u[-1] == 4, f"turn 1 ran 2 simulations of 6; continued, the next turn has {u[-1]} left (it had 6 again): {u}")

print("F  THE MODEL SERVER FAILS ON THE SUPERVISOR'S FIRST LOOK")
led, sup, meta, err = session("f1", [turn(ex=TEST)], [{"_error": "the server is restarting"}, G, REV, RUL])
say("Traceback" not in err and any("look at the baseline could not be read" in n for n in notes(led)) and of(led, "verdict", 1),
    f"a note, and the session goes on: turn 1's test is ruled on ({[r['id'] for r in of(led, 'verdict')]})")

print("G  THE ARM \"hypotheses\": MORE REQUESTS THAN IT ANSWERS")
ONE = {"observations": "read", "findings": [], "rethink": [], "budget_request": None, "done": False, "verdicts": [], "drop": [], "decisions": [], "report": None, "whys": [], "hypotheses": [], "experiment": None,
       "requests": [{"tool": "metrics", "args": {"run_id": "r001"}}] * 5}
led, sup, meta, err = session("g1", [ONE], [], arm="hypotheses")
res = of(led, "result", 1)
say(len(res) == 3 and any("only the first 3 requests of a reply are answered: 2 more were left unanswered" in n for n in notes(led)), f"3 requests are answered ({len(res)}) and a note says 2 were not")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
