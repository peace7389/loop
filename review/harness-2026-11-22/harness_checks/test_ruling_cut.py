"""s053 (2026-11-22, turn 3): the supervisor's ruling on H2 was sound, then ran on in its findings ("It is not a finding." to its limit), and the
whole answer could not be read: H2 stayed open. An answer of the supervisor cut off in its findings is now kept without them. Scripted session
(scripted.py; a supervisor answer {"_raw": text} is sent as that text), real ns-3 runs of 2 s:
  C  the ruling on H1 cut off in its findings: H1 is ruled as the supervisor said, with a note that its findings were cut off, and no finding
     comes from it;
  U  a ruling cut off before its findings: still unreadable, H1 stays open with the note as before.
python3 -I test_ruling_cut.py SCRATCH_DIR [HARNESS_DIR]"""
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
def session(sid, answers, sup):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup}))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "two-hosts-open-2", "--session", sid, "--arm", "supervised", "--budget", "8"], env=ENV, capture_output=True, text=True, timeout=1500)
    if "Traceback" in r.stderr: print(r.stderr[-2000:])
    return [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
of = lambda led, ty: [r for r in led if r["type"] == ty]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
T1 = {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None,
      "whys": [{"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "revises": None}],
      "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part"}],
      "experiment": {"kind": "test", "tests": ["H1"], "question": "", "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [],
                     "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "UDP's own sending rate limits it", "rival_predicts": "failed"}]}}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
REV = {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": "failed", "doubt_if": "nothing", "because": "reasoned", "defect": "none", "feedback": ""}
CUT = '{"shows": "inconclusive", "because": "The check held, but the test is not about the guess.", "fair": false, "defect": "not_about_the_guess", "result": "inconclusive", "retest": "Compare the transient.", "findings": [{"about": ["E1"], "text": "It is not a finding.' + " It is not a finding." * 40
print("C  A RULING CUT OFF IN ITS FINDINGS")
led = session("c1", [T1], [G, REV, {"_raw": CUT}])
v = of(led, "verdict"); notes = [r["body"].get("text", "") for r in of(led, "note")]
say(v and v[0]["body"]["for"] == "H1" and v[0]["body"]["result"] == "inconclusive" and v[0]["body"]["defect"] == "not_about_the_guess" and any("ran on in its findings and was cut off" in n for n in notes)
    and not [r for r in of(led, "finding") if r["turn"] == 1], f"H1 is ruled as the supervisor said ({v[0]['body']['result'] if v else None}), with the note, and no finding comes from the cut-off part")
print("U  A RULING CUT OFF BEFORE ITS FINDINGS")
led = session("u1", [T1], [G, REV, {"_raw": '{"shows": "inconclusive", "because": "The check held, but'}])
notes = [r["body"].get("text", "") for r in of(led, "note")]
say(not [r for r in of(led, "verdict") if r["turn"] == 1] and any("ruling on H1 could not be read" in n for n in notes), "unreadable as before: no ruling in turn 1, with the note (the next turn asks for it again: R below)")
T2 = {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None,
      "whys": [{"about": ["E1"], "result": "UDP gets more at 0.7 than at 0.3", "guess": "the part sets UDP's share", "revises": None}],
      "hypotheses": [{"from_why": "Y2", "text": "TCP goodput falls as UDP's part rises"}],
      "experiment": {"kind": "test", "tests": ["H2"], "question": "", "runs": [d("c", 0.2), d("e", 0.8)], "measurements": [],
                     "decision_rules": [{"for": "H2", "decision_rule": "tcp_goodput_bps@c > tcp_goodput_bps@e", "rival": "TCP's own window limits it", "rival_predicts": "failed"}]}}
RUL = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
BAD = {"_raw": '{"shows": "inconclusive", "because": "The check held, but'}
print("R  A RULING THAT COULD NOT BE READ IS ASKED FOR AGAIN AT THE NEXT TURN")
led = session("r1", [T1, T2], [G, REV, BAD, RUL, G, REV, RUL])
v = [(r["body"]["for"], r["turn"]) for r in of(led, "verdict")]; notes = [r["body"].get("text", "") for r in of(led, "note")]
say(("H1", 2) in v and any("has no ruling: the supervisor is asked for it again" in n for n in notes) and [r["id"] for r in of(led, "hypothesis") if r["turn"] == 2] == ["H2"] and ("H2", 2) in v,
    f"turn 1's ruling on H1 could not be read; at the start of turn 2 the supervisor is asked again and rules; H2 is stated, tested and ruled in turn 2 ({v})")
print("W  A CHECKED HYPOTHESIS WAITING FOR ITS RULING KEEPS NOTHING OUT")
led = session("w1", [T1, T2], [G, REV, BAD, BAD, G, REV, RUL])
v = [(r["body"]["for"], r["turn"]) for r in of(led, "verdict")]; notes = [r["body"].get("text", "") for r in of(led, "note")]
say(not [x for x in v if x[0] == "H1"] and [r["id"] for r in of(led, "hypothesis") if r["turn"] == 2] == ["H2"] and ("H2", 2) in v and not any("still open and untested" in n for n in notes)
    and sum("has no ruling: the supervisor is asked for it again" in n for n in notes) == 1,
    f"H1's ruling could not be read twice (asked again once only); H2 is accepted all the same, tested and ruled ({v})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
