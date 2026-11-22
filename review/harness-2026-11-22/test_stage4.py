"""Stage 4 of the coherence audit (2026-11-22): the rest of the operator's sheet "Fixes from s052 and s053". Scripted sessions (scripted.py), real ns-3 runs:
  A  the batched first review: a reply's two new guesses and two tests go to the supervisor in ONE request (no single guess or test review), and are
     recorded as four reviews, each with what was shown;
  B  a test whose boxes disagree in the batch gets its follow-up question alone, and is sent back and repaired as before;
  C  a batch that cannot be read leaves a note, and each guess and test is asked alone;
  D  a guess the batch does not accept is restated and read again alone; its hypothesis's test was reviewed in the batch;
  E  the arm "supervised": a decision rule of 4 comparisons is refused with the reason before any review; the instructions state the limit;
  F  the supervisor's test review asks for the one problem that matters most.
python3 -I test_stage4.py SCRATCH_DIR [HARNESS_DIR]"""
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
def session(sid, answers, sup, brief="two-hosts-open-2", sets=None):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup}))
    env = {**os.environ, "HOME": str(SCR / "home"), "SCRIPTED_SET": json.dumps({"BATCH_FIRST": True, **(sets or {})})}
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, "--budget", "8", "--arm", "supervised"], env=env, capture_output=True, text=True, timeout=1500)
    S = P / "sessions" / sid
    if "Traceback" in r.stderr: print(r.stderr[-2000:])
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    calls = [json.loads(l) for l in (S / "calls.jsonl").read_text().splitlines() if l.strip()] if (S / "calls.jsonl").is_file() else []
    sl = [json.loads(l) for l in (S / "supervisor.jsonl").read_text().splitlines() if l.strip()] if (S / "supervisor.jsonl").is_file() else []
    return led, calls, sl, json.loads((S / "session.json").read_text())
of = lambda led, ty: [r for r in led if r["type"] == ty]
notes = lambda led: [str(r["body"].get("text") or r["body"].get("reason") or "") for r in of(led, "note")]
steps = lambda calls: [(c["agent"][0], (c.get("step") or {}).get("step")) for c in calls]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
RIV = {"rival": "UDP's own sending rate limits it", "rival_predicts": "failed"}
def turn(rules=None, n_why=2):
    ws = [{"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "revises": None},
          {"about": ["E0"], "result": "TCP gets the other half", "guess": "TCP fills what UDP leaves", "revises": None}][:n_why]
    hs = [{"from_why": "Y1", "text": "UDP goodput rises with its part"}, {"from_why": f"Y{min(2, n_why)}", "text": "TCP goodput falls as UDP's part rises"}]
    rules = rules or [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", **RIV}, {"for": "H2", "decision_rule": "tcp_goodput_bps@b < tcp_goodput_bps@a", **RIV}]
    return {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None, "whys": ws, "hypotheses": hs,
            "experiment": {"kind": "test", "tests": sorted({r["for"] for r in rules}), "question": "", "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [], "decision_rules": rules}}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
REV = {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": "failed", "doubt_if": "nothing", "because": "reasoned", "defect": "none", "feedback": ""}
CONTRA = {**REV, "stronger_rival": "a larger part only lowers the drops", "defect": "rival_passes_too", "feedback": "A stronger rival: a larger part only lowers the drops."}
AGAIN_WEAK = {"because": "the stronger rival passes the rule too", "stronger_rival": "a larger part only lowers the drops", "rival_is_weak": True, "rival_outcome": "held", "defect": "rival_passes_too"}
RUL = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
def batch(gs, ts): return {"guesses": [{"guess": f"G{i + 1}", **g} for i, g in enumerate(gs)], "tests": [{"for": h, **t} for h, t in ts]}
GOOD = {"decision_rule": "udp_goodput_bps@b > 1.2 * udp_goodput_bps@a", **RIV, "runs": []}

print("A  ONE REQUEST FOR THE REPLY'S NEW GUESSES AND TESTS")
led, calls, sl, meta = session("a1", [turn()], [batch([G, G], [("H1", REV), ("H2", REV)]), RUL, RUL])
rv = [(r["body"].get("gate"), r["body"].get("for"), r["body"].get("decision")) for r in of(led, "review")]
st = steps(calls)
say(st.count(("s", "review")) == 1 and ("s", "ground") not in st and ("s", "design") not in st, f"one batched request, no single guess or test review: {st}")
say(rv == [("ground", "Y1", "approved"), ("ground", "Y2", "approved"), ("design", "H1", "approved"), ("design", "H2", "approved")] and len(of(led, "verdict")) == 2,
    f"recorded as four reviews, then both tests ruled on: {rv}")
say(all("THIS REQUEST HOLDS EVERY NEW GUESS AND EVERY NEW TEST" in (x["shown"] or "") for x in sl if x["gate"] in ("ground", "design")) and "one request" in str((meta.get("flags") or {}).get("supervisor", {}).get("first_review")),
    "each review keeps the batched request as what it was shown, and session.json says the reviews were batched")
batch_call = next((c for c in calls if (c.get("step") or {}).get("step") == "review"), {})
say(batch_call.get("max_tokens") == 9000 + 2000 * 3, f"the batch is asked with {batch_call.get('max_tokens')} tokens: 4,500 of reasoning and 1,000 more for each further item")

print("B  A TEST WHOSE BOXES DISAGREE IN THE BATCH")
led, calls, sl, meta = session("b1", [turn(), GOOD], [batch([G, G], [("H1", CONTRA), ("H2", REV)]), AGAIN_WEAK, REV, RUL, RUL])
r1 = [(r["body"].get("for"), r["body"].get("round"), r["body"].get("decision")) for r in of(led, "review") if r["body"].get("gate") == "design"]
st = steps(calls)
say(("H1", 1, "sent_back") in r1 and ("H1", 2, "approved") in r1 and ("H2", 1, "approved") in r1 and st.count(("s", "review")) == 1 and ("r", "repair") in st,
    f"its follow-up is asked alone, it is sent back and repaired; the other test was approved in the batch: {r1}; {st}")

print("C  A BATCH THAT CANNOT BE READ")
led, calls, sl, meta = session("c1", [turn()], [{"_raw": "not JSON"}, G, G, REV, REV, RUL, RUL])
st = steps(calls)
say(any("batched first review could not be read" in n for n in notes(led)) and st.count(("s", "ground")) == 2 and st.count(("s", "design")) == 2 and len(of(led, "verdict")) == 2,
    f"a note, and each guess and test is asked alone: {st}")

print("D  A GUESS THE BATCH DOES NOT ACCEPT")
NOT = {**G, "defect": "not_in_the_records", "because": "E0 shows no half"}
RESTATED = {"about": ["E0"], "result": "UDP gets 49 % of the link in E0", "guess": "the scheduler gives each flow its part", "revises": None}
led, calls, sl, meta = session("d1", [turn(), RESTATED], [batch([NOT, G], [("H1", REV), ("H2", REV)]), G, RUL, RUL])
st = steps(calls)
w1 = next((r["body"] for r in of(led, "why")), {})
say(w1.get("restated") and st.count(("s", "review")) == 1 and st.count(("s", "ground")) == 1 and ("s", "design") not in st and len(of(led, "verdict")) == 2,
    f"restated, read again alone; both tests were reviewed in the batch and ruled on: {st}")

print("E  A DECISION RULE OF FOUR COMPARISONS")
BIG = [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a AND udp_goodput_bps@b > 1 AND udp_goodput_bps@a > 1 AND tcp_goodput_bps@a > 1", **RIV}]
led, calls, sl, meta = session("e1", [{**turn(BIG, 1), "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part"}]}], [G])
st = steps(calls)
say(any("makes 4 comparisons, and a rule makes at most 3" in n for n in notes(led)) and ("s", "design") not in st and ("s", "review") not in st,
    f"refused with the reason, before any review of it: {st}")
say(calls and "at most 3 comparisons, joined by AND and OR" in next(c["system"] for c in calls if c["agent"] == "researcher"), "the researcher's instructions state the limit")

print("F  THE FEEDBACK NAMES ONE PROBLEM")
led, calls, sl, meta = session("f1", [turn()], [], sets={"BATCH_FIRST": False})
rq = next((c["user"] for c in calls if (c.get("step") or {}).get("step") == "design"), "")
say("the one problem that matters most" in rq and "the record ids and numbers it rests on, and what a repaired test must achieve" in rq, "the test review asks for the one problem that matters most, what it rests on, and what a repair must achieve")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
