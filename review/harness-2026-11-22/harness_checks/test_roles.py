"""The harness side of ~/project/READABLE_PAGE.md, Part 5: each claim of a final report has a required role (supports,
background, limits); a report with a claim that has none is refused, as a refused part, with the reason; the answer
format requires the role; the prompt says so in one sentence. One scripted session, r1, which the page check uses too.
    python3 -I test_roles.py SCRATCH_DIR [HARNESS_DIR]
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
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env=ENV, capture_output=True, text=True, timeout=1200)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    led = [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
    return led, json.loads((P / "sessions" / sid / "session.json").read_text())
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led, turn: [(r["body"].get("part"), r["body"].get("reason")) for r in of(led, "note", turn) if "part" in r["body"]]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w, **over): return {"label": label, "params": {"weightUdp": w, **KN, **over}}
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def report(claims): return {"goal": "the larger of the two goodputs as large as possible", "recommendation": {"weightUdp": 0.7, **KN}, "expected": {"udp_goodput_bps": 685000000.0, "tcp_goodput_bps": 290000000.0}, "no_difference": [], "limit": "The part of the link given to UDP: C1.", "explanation": "UDP's goodput follows its part of the link.",
                            "holds_when": "UDP offers more than its part.", "breaks_when": "UDP offers less than its part.", "claims": claims, "open_questions": []}
ROLED = [{"text": "With a larger part UDP delivers more.", "role": "supports", "evidence": ["C1", "V1"]}, {"text": "TCP always delivers something.", "role": "background", "evidence": ["C2"]},
         {"text": "The two flows together fill the link.", "role": "background", "evidence": ["E1"]}, {"text": "With less UDP traffic than its part the advice would change.", "role": "limits", "evidence": ["V2"]}]
ANSWERS = [
 turn(hypotheses=[{"text": "UDP goodput rises with the weight", "question": "Does UDP get more when its part is larger?", "why": "The goal is about what UDP delivers.", "prediction": "more", "follows_from": ["brief"]},
                  {"text": "TCP delivers something", "question": "Does TCP deliver anything at all?", "why": "A setting that starves TCP would not be a good answer.", "prediction": "yes", "follows_from": ["brief"]}],
      experiment={"kind": "test", "tests": ["H1", "H2"], "question": "", "varied": ["weightUdp"], "control": None, "runs": [d("a", 0.3), d("b", 0.7)],
                  "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "the weight does nothing", "rival_predicts": "failed"}, {"for": "H2", "decision_rule": "tcp_goodput_bps@a > 1000", "rival": "TCP is starved", "rival_predicts": "failed"}]}),
 turn(verdicts=[{"for": "H1", "result": "supported", "because": "the check held", "next": "report"}, {"for": "H2", "result": "supported", "because": "the check held", "next": "report"}], done=True,
      report=report([{"text": "With a larger part UDP delivers more.", "evidence": ["C1"]}, ROLED[1], {"text": "A third.", "role": "because", "evidence": []}])),
 turn(done=True, report=report(ROLED)),
]
print("ROLES OF THE CLAIMS  (READABLE_PAGE.md, Part 5)")
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import importlib; tools = importlib.import_module("tools"); loop = importlib.import_module("loop")
schema = json.loads((P / "harness/schema.json").read_text()); claim = next(q for q in schema["properties"]["report"]["anyOf"] if q.get("type") == "object")["properties"]["claims"]["items"]
say(claim["required"] == ["text", "role", "evidence"] and claim["properties"]["role"]["enum"] == ["supports", "background", "limits"] == list(loop.ROLES) and list(claim["properties"]) == ["text", "role", "evidence"],
    f"the answer format requires a role for every claim, one of {claim['properties']['role']['enum']}, between its text and its evidence: required {claim['required']}")
prompt = (P / "harness/prompt.txt").read_text(); line = next((l for l in prompt.splitlines() if "- claims:" in l), "")
say("Give each claim its role: supports (a reason for the recommendation), background (how the system behaves), or limits (when the recommendation would change)." in line, "the prompt says it in one sentence, in the line about the claims")
led, meta = session("r1", "two-hosts-open", ANSWERS)
n2 = notes(led, 2); reps = of(led, "report")
say(("report", "report.claims: claim 1, 3 has no role: give each claim its role, one of supports, background, limits") in n2 and not of(led, "report", 2) and len(of(led, "verdict", 2)) == 2,
    f"a report whose claims 1 and 3 have no role (one has none, one has a word that is not a role) is refused as a part, with the reason, and the rest of the answer (the two verdicts) is used: {[q for q in n2 if q[0] == 'report']}")
say(len(reps) == 1 and reps[0]["turn"] == 3 and [c["role"] for c in reps[0]["body"]["claims"]] == ["supports", "background", "background", "limits"] and meta["how"] == "done by the model",
    f"the same report with a role for each claim is accepted in the next turn, and the ledger keeps the roles: {[c['role'] for c in reps[0]['body']['claims']] if reps else None}; the session ended “{meta['how']}”")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
