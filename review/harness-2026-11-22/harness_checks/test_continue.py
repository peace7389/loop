"""A turn ends with a step (2026-11-22, the operator, after s053's turns 1 and 2 passed with guesses and readings only: "Turn 1 and 2 passed without
any hypothesis are not what I intended. Fix it"): a reply that states no hypothesis, test, drop, verdict, objection or report is followed by another
call of the researcher in the same turn, at most CONTINUES (2) times, with what it asked for answered at once. Scripted sessions with stand-in agents
(scripted.py, SCRIPTED_SET {"CONTINUES": 2}), real ns-3 runs of 2 s:
  S  the arm "supervised": reply 1 states guesses and asks for a reading; reply 2 asks for readings only; reply 3 states a hypothesis and its test:
     all three in turn 1 (one turn record), each later reply told why the turn goes on and shown the readings; the test is reviewed, run and ruled
     on in turn 1; the session's next reply is turn 2's;
  L  three replies without a step: the turn ends after the third (turn 2 begins), the third told it is the last of its turn;
  H  the arm "hypotheses": a reply with requests only is followed by another in the same turn, which states the hypothesis and its test;
  and the instructions of both arms say it.
python3 -I test_continue.py SCRATCH_DIR [HARNESS_DIR]"""
import json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
ENV = {**os.environ, "HOME": str(SCR / "home"), "SCRIPTED_SET": json.dumps({"CONTINUES": 2})}
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import loop
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, answers, sup, arm):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup}))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "two-hosts-open-2", "--session", sid, "--budget", "8"] + (["--arm", arm] if arm != "hypotheses" else []),
                       env=ENV, capture_output=True, text=True, timeout=1500)
    S = P / "sessions" / sid
    if "Traceback" in r.stderr: print(r.stderr[-2500:])
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    users = json.loads((S / "users_sent.json").read_text()) if (S / "users_sent.json").is_file() else []
    return led, users
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
REQ = lambda of: {"tool": "measure", "args": {"run_id": "r001", "of": of, "stat": "max"}}
WHY = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "revises": None}
def sv(**k): return {"observations": "read", "findings": [], "requests": [], "whys": [], "hypotheses": [], "drop": [], "experiment": None, "objections": [], "decisions": [], "report": None, **k}
TEST = {"kind": "test", "tests": ["H1"], "question": "", "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [],
        "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "UDP's own sending rate limits it", "rival_predicts": "failed"}]}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
REV = {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": "failed", "doubt_if": "nothing", "because": "reasoned", "defect": "none", "feedback": ""}
RULING = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}

print("S  THE ARM \"supervised\": READINGS IN THE SAME TURN, THEN THE STEP")
led, users = session("s1", [sv(whys=[WHY], requests=[REQ("udp_bps")]), sv(requests=[REQ("tcp_bps"), REQ("tcp_cwnd")]),
                            sv(hypotheses=[{"from_why": "Y1", "text": "UDP goodput rises with its part"}], experiment=TEST), sv(requests=[REQ("udp_bps")])], [G, REV, RULING], "supervised")
t1 = [r["id"] for r in of(led, "turn")]; res1 = [r["id"] for r in of(led, "result", 1)]
say(t1[:2] == ["U1", "U2"] and len(res1) == 3 and of(led, "hypothesis", 1) and of(led, "experiment", 1) and of(led, "verdict", 1) and of(led, "check", 1),
    f"three replies in turn 1: its readings ({res1}), then H1, its test, run, checked and ruled on in turn 1; the next reply is turn 2's (turn records {t1})")
say(len(users) >= 4 and "THIS TURN GOES ON" not in users[0] and "THIS TURN GOES ON (your reply 2 in this turn, at most 3)" in users[1] and "asked once more in this turn" in users[1]
    and "THIS TURN GOES ON (your reply 3 in this turn, at most 3)" in users[2] and "this is the last reply of this turn" in users[2] and "THIS TURN GOES ON" not in users[3]
    and all(t in users[2] for t in res1),
    "reply 2 and reply 3 of turn 1 are told why the turn goes on (reply 3: the last of its turn) and are shown every reading of the turn; turn 2's first reply is not")

print("L  THREE REPLIES WITHOUT A STEP: THE TURN ENDS")
led, users = session("l1", [sv(requests=[REQ("udp_bps")]), sv(requests=[REQ("tcp_bps")]), sv(requests=[REQ("tcp_cwnd")]), sv(requests=[REQ("udp_bps")])], [], "supervised")
turns = [(r["id"], r["turn"]) for r in of(led, "turn")]; res = [(r["id"], r["turn"]) for r in of(led, "result")]
say(turns[:2] == [("U1", 1), ("U2", 2)] and [t for _, t in res] == [1, 1, 1, 2] and len(users) >= 4 and "THIS TURN GOES ON" not in users[3],
    f"after three replies without a step turn 1 ends and turn 2 begins: readings by turn {[t for _, t in res]}, turn records {turns}")

print("H  THE ARM \"hypotheses\"")
ONE = {"observations": "read", "findings": [], "rethink": [], "requests": [], "budget_request": None, "done": False, "verdicts": [], "drop": [], "decisions": [], "report": None, "whys": [], "hypotheses": [], "experiment": None}
H1 = {**ONE, "whys": [{"about": ["E0"], "result": "UDP gets about half", "guess": "the scheduler gives each flow its part", "unseen": "how it divides the link", "matters": "it decides the answer", "worth": "verify", "reason": "it serves the goal"}],
      "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part", "question": "Does UDP get more when its part is larger?", "why": "It decides the answer.", "prediction": "more", "follows_from": []}],
      "experiment": {**TEST, "question": "Does the part change what UDP gets?", "varied": ["weightUdp"], "control": None}}
led, users = session("h1", [{**ONE, "requests": [{"tool": "metrics", "args": {"run_id": "r001"}}]}, H1], [], "hypotheses")
say(of(led, "result", 1) and of(led, "hypothesis", 1) and of(led, "experiment", 1) and [r["id"] for r in of(led, "turn")][:2] == ["U1", "U2"] and len(users) >= 2 and "THIS TURN GOES ON (your reply 2" in users[1],
    f"a reply with a request only is followed by another in turn 1, which states H1 and its test (turn records {[r['id'] for r in of(led, 'turn')]})")

print("THE INSTRUCTIONS")
say("the results come back at once, in the same turn" in loop.LEAN_PROMPT and "A turn ends with a step" in loop.LEAN_PROMPT and "the results come back at once, in the same turn" in (P / "harness/prompt.txt").read_text()
    and len(loop.LEAN_PROMPT + loop.FINDINGS_TEXT["supervised"]) < 10_000, f"both arms' instructions say readings come back at once, in the same turn, and that a turn ends with a step; the supervised arm's whole text {len(loop.LEAN_PROMPT + loop.FINDINGS_TEXT['supervised'])} characters")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
