"""Ids by position (stage 1, item 1 of the coherence audit, 2026-11-22). The researcher names a new guess or hypothesis of its answer by the id it will
get; when an earlier part was refused, every later id used to shift (s050 t4: the q4-vs-q1000 rule landed on the NewReno hypothesis; s051 t4, s051 t8,
s041 t2: hypotheses recorded under another guess). Scripted sessions (scripted.py), real ns-3 runs of 2 s:
  S  the arm "supervised": the answer's first guess is refused (no guess text), so its hypothesis is refused too, saying which guess was not accepted;
     the 2nd and 3rd guesses are recorded as Y1 and Y2 and their hypotheses come from exactly them; the rules written for the 2nd and 3rd hypotheses
     (H2, H3 by position) land on exactly those hypotheses (recorded H1, H2); the test of the refused one is left out, named as not accepted;
  H  the arm "hypotheses": the same with the full format (the first guess refused for its worth).
python3 -I test_ids_position.py SCRATCH_DIR [HARNESS_DIR]"""
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
    if "Traceback" in r.stderr: print(r.stderr[-2500:])
    return [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
REV = {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": "failed", "doubt_if": "nothing", "because": "reasoned", "defect": "none", "feedback": ""}
RUL = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
RULE = lambda h, a, b: {"for": h, "decision_rule": f"udp_goodput_bps@{b} > udp_goodput_bps@{a}", "rival": "UDP's own rate limits it", "rival_predicts": "failed"}
RUNS = [d("a", 0.3), d("b", 0.7), d("c", 0.2), d("e", 0.8)]
print("S  THE ARM \"supervised\"")
WH = lambda g: {"about": ["E0"], "result": "UDP gets about half of the link", "guess": g, "revises": None}
T = {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None,
     "whys": [WH(""), WH("the scheduler gives each flow its part"), WH("UDP's sending rate limits it")],
     "hypotheses": [{"from_why": "Y1", "text": "OF THE REFUSED GUESS"}, {"from_why": "Y2", "text": "SECOND: UDP rises with its part"}, {"from_why": "Y3", "text": "THIRD: UDP rises again"}],
     "experiment": {"kind": "test", "tests": ["H1", "H2", "H3"], "question": "", "runs": RUNS, "measurements": [], "decision_rules": [RULE("H1", "a", "b"), RULE("H2", "c", "e"), RULE("H3", "a", "e")]}}
led = session("s1", [T], [G, G, REV, REV, RUL, RUL], "supervised")
ys = {r["id"]: r["body"]["guess"] for r in of(led, "why")}; hs = {r["id"]: (r["body"]["from_why"], r["body"]["text"]) for r in of(led, "hypothesis")}
rules = {r["body"]["for"]: r["body"]["decision_rule"] for r in of(led, "check")}
notes = [r["body"].get("text", "") for r in of(led, "note")]
say(ys == {"Y1": "the scheduler gives each flow its part", "Y2": "UDP's sending rate limits it"} and hs == {"H1": ("Y1", "SECOND: UDP rises with its part"), "H2": ("Y2", "THIRD: UDP rises again")},
    f"the 2nd and 3rd guesses are Y1 and Y2, and each hypothesis hangs on the guess it was written from: {hs}")
say(any("your new guess number 1 of this answer, which was not accepted" in n for n in notes), "the hypothesis of the refused guess is refused, saying which guess was not accepted")
say(rules == {"H1": "udp_goodput_bps@e > udp_goodput_bps@c", "H2": "udp_goodput_bps@e > udp_goodput_bps@a"} and any("H1 (your new hypothesis number 1 of this answer, not accepted)" in n for n in notes),
    f"the rules written for the 2nd and 3rd hypotheses are checked for exactly them ({rules}); the test of the refused one is left out, named as not accepted")
print("H  THE ARM \"hypotheses\"")
ONE = {"observations": "read", "findings": [], "rethink": [], "requests": [], "budget_request": None, "done": False, "verdicts": [], "drop": [], "decisions": [], "report": None}
WF = lambda g, worth="verify": {"about": ["E0"], "result": "UDP gets about half", "guess": g, "unseen": "how it divides the link", "matters": "it decides the answer", "worth": worth, "reason": "it serves the goal"}
HF = lambda y, text: {"from_why": y, "text": text, "question": "Does UDP get more?", "why": "It decides the answer.", "prediction": "more", "follows_from": []}
TH = {**ONE, "whys": [WF("the first guess", worth="maybe"), WF("the scheduler gives each flow its part"), WF("UDP's sending rate limits it")],
      "hypotheses": [HF("Y2", "SECOND: UDP rises with its part"), HF("Y3", "THIRD: UDP rises again")],
      "experiment": {"kind": "test", "tests": ["H1", "H2"], "question": "Does the part change what UDP gets?", "runs": RUNS, "measurements": [], "varied": ["weightUdp"], "control": None,
                     "decision_rules": [RULE("H1", "c", "e"), RULE("H2", "a", "e")]}}
led = session("h1", [TH], [], "hypotheses")
hs = {r["id"]: (r["body"]["from_why"], r["body"]["text"]) for r in of(led, "hypothesis")}; rules = {r["body"]["for"]: r["body"]["decision_rule"] for r in of(led, "check")}
say(hs == {"H1": ("Y1", "SECOND: UDP rises with its part"), "H2": ("Y2", "THIRD: UDP rises again")} and rules == {"H1": "udp_goodput_bps@e > udp_goodput_bps@c", "H2": "udp_goodput_bps@e > udp_goodput_bps@a"},
    f"the first guess refused for its worth: the hypotheses hang on the guesses they were written from ({hs}) and the rules on their hypotheses ({rules})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
