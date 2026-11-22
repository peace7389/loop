"""The harness side of "why a question is asked" (the operator's word of 2026-11-14): every new hypothesis has a required
`why`, one plain sentence saying how answering it helps reach the goal. A hypothesis without one is refused, as a
refused part, with the reason, and the rest of the answer is used; the answer format requires it; the prompt says so in
the line about hypotheses; the ledger keeps it. One scripted session, w1 (the page check uses it too).
    python3 -I test_why.py SCRATCH_DIR [HARNESS_DIR]
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
WHY1, WHY2 = "The goal is about what UDP delivers, so its part of the link has to matter.", "A setting that starves TCP would not be a good answer."
H1 = {"text": "UDP goodput rises with the weight", "question": "Does UDP get more when its part is larger?", "why": WHY1, "prediction": "more", "follows_from": ["brief"]}
H2 = {"text": "TCP delivers something", "question": "Does TCP deliver anything at all?", "prediction": "yes", "follows_from": ["brief"]}   # no why
H3 = {"text": "TCP delivers something at a small UDP part", "question": "Does TCP deliver anything at all?", "why": "  ", "prediction": "yes", "follows_from": ["brief"]}  # an empty why
ANSWERS = [
 turn(hypotheses=[H1, H2, H3]),
 turn(hypotheses=[{**H2, "why": WHY2}],
      experiment={"kind": "test", "tests": ["H1", "H2"], "question": "", "varied": ["weightUdp"], "control": None, "runs": [d("a", 0.3), d("b", 0.7)],
                  "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "the weight does nothing", "rival_predicts": "failed"},
                                     {"for": "H2", "decision_rule": "tcp_goodput_bps@a > 0", "rival": "TCP starves", "rival_predicts": "failed"}]}),
]
print("WHY A QUESTION IS ASKED")
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
schema = json.loads((P / "harness/schema.json").read_text()); hyp = schema["properties"]["hypotheses"]["items"]
say(hyp["required"] == ["from_why", "text", "question", "why", "prediction"] and hyp["properties"]["why"]["type"] == "string" and list(hyp["properties"]).index("why") == list(hyp["properties"]).index("question") + 1,
    f"the answer format requires a why for every new hypothesis, after its question: required {hyp['required']}; “{hyp['properties'].get('why', {}).get('description')}”")
prompt = (P / "harness/prompt.txt").read_text(); line = next((l for l in prompt.splitlines() if l.startswith("3. hypotheses:")), "")
say("and why: one plain sentence of at most 25 words saying how answering it helps reach the goal." in line and line.index("question:") < line.index("and why:"), "the prompt says it in the line about hypotheses, after the question")
led, meta = session("w1", "two-hosts-open", ANSWERS)
n1 = notes(led, 1); h1 = of(led, "hypothesis", 1); h2 = of(led, "hypothesis", 2)
reason = "a hypothesis needs a why: one plain sentence saying how answering it helps reach the goal"
say([q for q in n1 if q[0] == "new hypothesis"] == [("new hypothesis", reason)] * 2 and [h["id"] for h in h1] == ["H1"] and h1[0]["body"].get("why") == WHY1,
    f"of three hypotheses in one answer, the one with a why is recorded as H1 with its why; the one without and the one with an empty why are refused as parts, each with the reason: {[q for q in n1 if q[0] == 'new hypothesis'][:1]}")
say([h["id"] for h in h2] == ["H2"] and h2[0]["body"].get("why") == WHY2 and len(of(led, "check", 2)) == 2,
    f"given again with its why in the next turn, it is recorded as H2, and the experiment that tests H1 and H2 runs ({len(of(led, 'check', 2))} checks)")
import importlib; loop = importlib.import_module("loop")
st = {"H1": "open", "H2": "open"}; shown = loop.shown(h1[0], st)
# since 2026-11-22 (the operator: "make agents access all accumulated information across the turns") the model reads its own why back with the hypothesis
say(" ".join(WHY1.split())[:40] in shown and "why it matters: " in shown, f"the ledger text the model reads back holds the hypothesis's text, its prediction and its why: “{shown[:120]}”")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
