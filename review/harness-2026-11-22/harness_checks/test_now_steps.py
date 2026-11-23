"""now.json (2026-11-22, the operator, on the page's strip of the steps of a turn: "Shouldn't we reflect changes on this?"): the harness writes the
step a session is at as each step begins, so that the page can say who works on what while no record is written yet. Scripted sessions with
stand-in agents (scripted.py, which keeps every step written), real ns-3 runs of 2 s:
  S  the arm "supervised": the baseline's simulations, its checks, the supervisor's look at it; turn 1: the reply, the supervisor reads the guess,
     the researcher restates it (the supervisor did not accept it), the supervisor reads it again, the review of the test in round 1, the repair
     for round 2, the review in round 2, the simulations, the checks, the ruling; turn 2 (an explore experiment): the reply, the simulations, the
     checks, the supervisor's look; every write is whole (read back as JSON), with the turn and the time;
  H  the arm "hypotheses" (one AI, the judge on): the reply, the judge, the simulations, the checks;
  N  a finding's name (2026-11-22, the operator: the page shows a concise name on a finding's bar): one stated by the supervisor and one by the
     researcher are kept (cut to 6 words), one without a name is taken all the same, without one.
python3 -I test_now_steps.py SCRATCH_DIR [HARNESS_DIR]"""
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
def session(sid, answers, sup, arm):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup}))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "two-hosts-open-2", "--session", sid, "--budget", "8"] + (["--arm", arm] if arm != "hypotheses" else []),
                       env=ENV, capture_output=True, text=True, timeout=1500)
    S = P / "sessions" / sid
    if not (S / "stages_sent.json").is_file(): print(r.stdout[-800:], r.stderr[-2500:])
    st = json.loads((S / "stages_sent.json").read_text()) if (S / "stages_sent.json").is_file() else []
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    return st, led
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
WHY = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the link carries more than 1 Gbps", "revises": None}
def turn(whys=(), hyps=(), ex=None): return {"observations": "read", "findings": [], "requests": [], "whys": list(whys), "hypotheses": [{"from_why": y, "text": t} for y, t in hyps], "drop": [],
                                             "experiment": ex, "objections": [], "decisions": [], "report": None}
TEST = {"kind": "test", "tests": ["H1"], "question": "", "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [],
        "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "UDP's own sending rate limits it", "rival_predicts": "failed"}]}
EXPLORE = {"kind": "explore", "tests": [], "question": "what UDP gets at the part 0.5", "runs": [d("c", 0.5)], "measurements": [], "decision_rules": []}
G = lambda defect="none": {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": defect, "because": "the supervisor's reading"}
REV = lambda defect="none", outcome="failed", feedback="": {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": outcome,
                                                            "doubt_if": "nothing", "because": "reasoned", "defect": defect, "feedback": feedback}
RULING = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
REPAIR = {"decision_rule": "udp_goodput_bps@b > 1.5 * udp_goodput_bps@a", "rival": "the queue's length limits UDP", "rival_predicts": "failed", "runs": []}
key = lambda st: [(x["turn"], x["step"], x["about"], x["round"]) + ((x["by"],) if x["by"] else ()) for x in st if x]

print("S  THE ARM \"supervised\"")
T1 = {**turn([WHY], [("Y1", "UDP goodput rises with its part")], TEST), "findings": [{"about": ["E0"], "text": "TCP gets 0 bps at the default", "name": "TCP gets nothing"}]}
T2 = {**turn(ex=EXPLORE), "findings": [{"about": ["E1"], "text": "UDP gets 600 Mbps at the part 0.3 although it sends 2 Gbps"}]}
SUP_F = {"findings": [{"about": ["S0"], "text": "UDP loses 51 % of its packets at the default", "name": "  UDP loses half of its packets at the default "}]}
st, led = session("s1", [T1, {**WHY, "guess": "the link carries 1 Gbps and UDP gets its part of it"}, REPAIR, T2],
                  [SUP_F, G("not_in_the_records"), G(), REV("rival_passes_too", "held", "The rival passes this rule too."), REV(), RULING], "supervised")
x1 = next((r["id"] for r in led if r["type"] == "experiment" and r["turn"] == 1), None); x2 = next((r["id"] for r in led if r["type"] == "experiment" and r["turn"] == 2), None)
want = [(0, "sims", "X0", None), (0, "checks", "X0", None), (0, "look", "X0", None),
        (1, "reply", None, None), (1, "ground", None, None), (1, "restate", None, None, "supervisor"), (1, "ground", None, None), (1, "design", "H1", 1), (1, "repair", "H1", 2), (1, "design", "H1", 2),
        (1, "sims", x1, None), (1, "checks", x1, None), (1, "ruling", "H1", None),
        (2, "reply", None, None), (2, "sims", x2, None), (2, "checks", x2, None), (2, "look", x2, None), (3, "reply", None, None)]
say(key(st) == want, f"every step in its order, with the turn, what it is about and the round: {key(st)}")
say(st and all(x and x.get("at") and (x["rounds"] == 3) == (x["step"] in ("design", "repair")) for x in st) and not any(x.get("again") for x in st),
    "each write reads back whole, with its time; a review or a repair says the number of rounds (3); no reply was asked again")

calls = [(c["agent"], (c.get("step") or {}).get("step")) for c in map(json.loads, (P / "sessions/s1/calls.jsonl").read_text().splitlines())]
say(calls == [("supervisor", "look"), ("researcher", "reply"), ("supervisor", "ground"), ("researcher", "restate"), ("supervisor", "ground"), ("supervisor", "design"), ("researcher", "repair"),
              ("supervisor", "design"), ("supervisor", "ruling"), ("researcher", "reply"), ("supervisor", "look")],   # turn 3's reply fails (the script has no more answers): not a call
    f"every call in calls.jsonl names the step it was made in (the page shows a step's calls when it is clicked): {calls}")

print("N  A FINDING'S NAME")
fs = [(r["id"], r["by"], r["turn"], r["body"].get("name")) for r in led if r["type"] == "finding"]
say(fs == [("F1", "supervisor", 0, "UDP loses half of its packets"), ("F2", "model", 1, "TCP gets nothing"), ("F3", "model", 2, None)],
    f"the supervisor's name is kept cut to 6 words, the researcher's as stated, a finding without a name is taken without one: {fs}")

print("H  THE ARM \"hypotheses\" (ONE AI, THE JUDGE ON)")
# the full answer format of the arm (worth, reason, prediction, varied, budget_request: as test_findings.py states it)
ONE = {"observations": "read", "findings": [], "rethink": [], "requests": [], "budget_request": None, "done": False, "verdicts": [], "drop": [], "decisions": [], "report": None,
       "whys": [{"about": ["E0"], "result": "UDP gets about half", "guess": "the scheduler gives each flow its part", "unseen": "how it divides the link", "matters": "it decides the answer", "worth": "verify", "reason": "it serves the goal"}],
       "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part", "question": "Does UDP get more when its part is larger?", "why": "It decides the answer.", "prediction": "more", "follows_from": []}],
       "experiment": {**TEST, "question": "Does the part change what UDP gets?", "varied": ["weightUdp"], "control": None}}
st, led = session("h1", [ONE], [], "hypotheses")
x1 = next((r["id"] for r in led if r["type"] == "experiment" and r["turn"] == 1), None)
say(key(st)[:6] == [(0, "sims", "X0", None), (0, "checks", "X0", None), (1, "reply", None, None), (1, "judge", None, None), (1, "sims", x1, None), (1, "checks", x1, None)] and not any(s[1] in ("ground", "design", "ruling", "look") for s in key(st)),
      f"the reply, the judge, the simulations, the checks; no step of the supervisor: {key(st)}")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
