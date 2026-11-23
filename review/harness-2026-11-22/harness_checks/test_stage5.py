"""Stage 5 of the coherence audit (2026-11-22): competitors are guesses; the supervisor reviews and rules with three questions (Honest, Consistent,
Correct). The arm "supervised", COMPETITORS on. Scripted sessions (scripted.py), real ns-3 runs. Every kind of bad input of the operator's sheet, and
for each that nothing unrelated is refused and the session does not stop:
  A  a competitor written in the same answer; its test reviewed with three questions and ruled; the competitor does not fit a fair result: refuted
     by that ruling, said in the ledger text, no hypothesis from it; a competitor in a later turn citing an old result (the chain accepts it);
  B  competes_with missing, unknown, not a guess; the hypothesis's own guess; rival_predicts missing and "held": each refused with its reason before
     any review, the guesses and hypotheses of the answer accepted;
  C  a competitor revised, and one linked to the guess by revises; a refuted competitor;
  D  "correct: pass" with predictions that differ from the researcher's, and a follow-up that still contradicts: a refusal; a repair naming a guess
     that does not exist: refused by the harness; the next repair approved;
  E  equal predictions with "correct: pass": the follow-up settles it, approved;
  F  the supervisor names a missing competitor: held with no repair call, the hypothesis open; the guess written next turn is "from feedback";
  G  a review that cannot be read: a note, the session goes on;
  H  rulings that fail a question the review passed: a miss (foreseeable) and one found by the result; an unfair test refutes no guess;
  I  fits that contradict a fair result, still after one question: kept, refute nothing;
  J  the batched first review takes a test competing with a guess of the same reply;
  K  the instructions with competitors: their size, and the figures;
  L  a restated competitor that also revises (s055);
  M  the batched first review marks the reply's new guesses in the list of guesses, and a reading that names the guess itself is not taken (s056);
  N  a guess that competes with a later guess of the same answer (s057); if that guess is not accepted, it competes with none and says so;
  O  each reply request says the ids its new guesses and hypotheses will get (s057).
python3 -I test_stage5.py SCRATCH_DIR [HARNESS_DIR]"""
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
def session(sid, answers, sup, batch=False):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup}))
    env = {**os.environ, "HOME": str(SCR / "home"), "SCRIPTED_SET": json.dumps({"COMPETITORS": True, "BATCH_FIRST": batch})}
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "two-hosts-open-2", "--session", sid, "--budget", "8", "--arm", "supervised"], env=env, capture_output=True, text=True, timeout=1500)
    S = P / "sessions" / sid
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    calls = [json.loads(l) for l in (S / "calls.jsonl").read_text().splitlines() if l.strip()] if (S / "calls.jsonl").is_file() else []
    users = json.loads((S / "users_sent.json").read_text()) if (S / "users_sent.json").is_file() else []
    return led, calls, users, json.loads((S / "session.json").read_text()), r.stderr
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led: [str(r["body"].get("text") or r["body"].get("reason") or "") for r in of(led, "note")]
steps = lambda calls: [(c["agent"][0], (c.get("step") or {}).get("step")) for c in calls]
rounds = lambda led, h=None: [(r["body"]["for"], r["body"]["round"], r["body"]["decision"], r.get("by")) for r in of(led, "review") if r["body"].get("gate") == "design" and (h is None or r["body"]["for"] == h)]
calm = lambda err, meta: "Traceback" not in err and "harness error" not in str(meta.get("how"))
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
A_ = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "revises": None, "competes_with": None}
B_ = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "UDP's own sending rate limits it", "revises": None, "competes_with": "Y1"}
def rule(h, cw, pred="failed", r="udp_goodput_bps@b > udp_goodput_bps@a"): return {"for": h, "decision_rule": r, **({"competes_with": cw} if cw is not None else {}), **({"rival_predicts": pred} if pred is not None else {})}
def turn(whys=(), hyps=(), rules=(), runs=None, **k):
    ex = {"kind": "test", "tests": sorted({x["for"] for x in rules}), "question": "", "runs": runs or [d("a", 0.3), d("b", 0.7)], "measurements": [], "decision_rules": list(rules)} if rules else None
    return {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None, "whys": list(whys), "hypotheses": list(hyps), "experiment": ex, **k}
H = lambda y, text="UDP goodput rises with its part": {"from_why": y, "text": text}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
OK3 = {"reads": "r", "honest_why": "it can fail: b is not yet run", "honest": "pass", "consistent_why": "it tests the part and only it", "consistent": "pass", "if_tested": "held", "if_competitor": "failed",
       "correct_why": "the two guesses differ", "correct": "pass", "missing": "", "feedback": ""}
def RUL3(result="supported", fair=("pass", "pass", "pass"), fore=("n/a", "n/a", "n/a"), ft="fits", fc="does not fit"):
    return {"shows": "what the numbers show", **{k: v for q, b, f in zip(("honest", "consistent", "correct"), fair, fore) for k, v in ((f"{q}_why", f"{q}: as seen"), (q, b), (f"{q}_foreseeable", f))},
            "because": "the checks", "result": result, "fits_tested": ft, "fits_competitor": fc, "retest": "", "findings": []}

print("A  A COMPETITOR OF THE SAME ANSWER; REFUTED BY A FAIR RESULT; A LATER COMPETITOR OF AN OLD RESULT")
C_ = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the queue drops UDP packets first", "revises": None, "competes_with": "Y1"}
led, calls, users, meta, err = session("a1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")]), turn([C_], [H("Y2", "UDP goodput does not change with its part")])], [G, G, OK3, RUL3()])
y2 = next((r["body"] for r in of(led, "why") if r["id"] == "Y2"), {})
v = of(led, "verdict")
say(calm(err, meta) and y2.get("competes_with") == "Y1" and rounds(led) == [("H1", 1, "approved", "supervisor")] and v and v[0]["body"].get("questions") and v[0]["body"].get("fits") == {"Y1": "fits", "Y2": "does not fit"},
    f"Y2 competes with Y1; H1's test, competing with Y2, is approved by three questions and ruled: {v[0]['body'].get('result') if v else None}, fits {v[0]['body'].get('fits') if v else None}")
say(len(users) >= 2 and "refuted by V1: no hypothesis can come from it" in users[1] and any("Y2 was refuted" in n for n in notes(led)),
    "turn 2's ledger text says Y2 is refuted by V1, and a hypothesis from Y2 is refused")
say(len(users) >= 2 and "refuted by V1: no hypothesis can come from it, and no guess or test may compete with it; a new guess may revise it" in users[1],
    "the mark says too that no guess or test may compete with a refuted guess (s057 turn 8: three refusals for naming the refuted Y23)")
y3 = next((r["body"] for r in of(led, "why", 2)), None)
say(y3 is not None and y3.get("competes_with") == "Y1" and y3.get("about") == ["E0"], "a competitor written in turn 2 citing only E0, the old result it explains otherwise, is accepted (the chain's exception)")
say(meta["flags"].get("competitors") is True and "competes_with" in meta["prompt"] and "rival (the strongest competing explanation" not in meta["prompt"], "session.json keeps that the session works with competitors, and its instructions say so")

print("B  BAD COMPETITORS AND PREDICTIONS, REFUSED BEFORE ANY REVIEW")
hy3 = [H("Y1", "UDP goodput rises with its part"), H("Y1", "UDP loss falls with its part"), H("Y1", "TCP goodput falls with UDP's part")]
led, calls, users, meta, err = session("b1", [turn([A_, B_], hy3, [rule("H1", None), rule("H2", "Y9", r="udp_loss_frac@b < udp_loss_frac@a"), rule("H3", "E0", r="tcp_goodput_bps@b < tcp_goodput_bps@a")])], [G, G])
n = notes(led)
say(calm(err, meta) and any("names the guess it competes with: competes_with" in x for x in n) and any("competes with Y9, which is not a guess" in x for x in n) and any("competes with E0, which is not a guess" in x for x in n)
    and ("s", "design") not in steps(calls) and len(of(led, "why")) == 2 and len(of(led, "hypothesis")) == 3, f"missing, unknown and not a guess: each refused with its reason, no review; the 2 guesses and 3 hypotheses stand")
led, calls, users, meta, err = session("b2", [turn([A_, B_], hy3, [rule("H1", "Y1"), rule("H2", "Y2", pred=None, r="udp_loss_frac@b < udp_loss_frac@a"), rule("H3", "Y2", pred="held", r="tcp_goodput_bps@b < tcp_goodput_bps@a")])], [G, G])
n = notes(led)
say(calm(err, meta) and any("which is H1's own guess Y1" in x for x in n) and any("needs rival_predicts" in x for x in n) and any("would hold if Y2 were true too" in x for x in n) and ("s", "design") not in steps(calls),
    "the hypothesis's own guess, rival_predicts missing and held: each refused with its reason, before any review")

print("C  A REVISED COMPETITOR, ONE LINKED BY REVISES, A REFUTED ONE")
Y2REV = {"about": ["T1"], "result": "the metrics of r001 show UDP at 49 % of the link", "guess": "the scheduler gives each flow exactly its part", "revises": "Y1", "competes_with": None}
LOOK = {"tool": "metrics", "args": {"run_id": "r001"}}
led, calls, users, meta, err = session("c1", [turn([A_], [H("Y1")], requests=[LOOK]), turn([Y2REV], [], [rule("H1", "Y2")])], [G, G])
n = notes(led)
say(calm(err, meta) and any("competes with Y2, which is H1's own guess Y1 or one linked to it by revises" in x for x in n) and of(led, "why", 2), "H1 (from Y1) competing with Y2, which revises Y1: refused as linked by revises; Y2 itself stands")
led2, calls2, users2, meta2, err2 = session("c2", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")]), turn([], [H("Y1", "UDP loss falls with its part")], [rule("H2", "Y2", r="udp_loss_frac@e < udp_loss_frac@c")], runs=[d("c", 0.4), d("e", 0.8)])], [G, G, OK3, RUL3()])   # new simulations: a rule on known results is refused first
n2 = notes(led2)
say(calm(err2, meta2) and any("competes with Y2, which the ruling V1 refuted" in x for x in n2), "a test competing with Y2 after V1 refuted it: refused, name a live guess")

print("D  CONTRADICTIONS, A FOLLOW-UP THAT STILL CONTRADICTS, A REPAIR NAMING NO GUESS")
DIFF = {**OK3, "if_competitor": "held"}   # "correct: pass", but the competitor would pass the rule too: differs from the researcher's FAILED
STILL = {"because": "still so", "if_tested": "held", "if_competitor": "held", "correct": "pass"}
R9 = {"decision_rule": "udp_goodput_bps@b > 1.2 * udp_goodput_bps@a", "competes_with": "Y9", "rival_predicts": "failed", "runs": []}
RG = {"decision_rule": "udp_goodput_bps@b > 1.2 * udp_goodput_bps@a", "competes_with": "Y2", "rival_predicts": "failed", "runs": []}
led, calls, users, meta, err = session("d1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")]), R9, RG], [G, G, DIFF, STILL, OK3, RUL3()])
rr = rounds(led)
r1 = next((r["body"] for r in of(led, "review") if r["body"].get("round") == 1), {})
say(calm(err, meta) and rr[:3] == [("H1", 1, "sent_back", "supervisor"), ("H1", 2, "sent_back", "harness"), ("H1", 3, "approved", "supervisor")] and (r1.get("again") or {}).get("still"),
    f"round 1 a refusal (its follow-up still contradicted), round 2 refused by the harness (Y9 is no guess), round 3 approved: {rr}")

reps = [(r["body"].get("round"), r["body"].get("competes_with")) for r in of(led, "repair")]
say(reps == [(2, "Y9"), (3, "Y2")] and users and "(competes with Y2; under it: FAILED)" in users[-1] and "rival: None" not in users[-1],
    f"each repair keeps the guess it competes with, and the researcher's ledger text says it (s055: \"rival: None\"): {reps}")
rq = next((c["user"] for c in calls if (c.get("step") or {}).get("step") == "design"), "")
say("THE RESEARCHER'S GUESSES SO FAR" in rq and "[Y1] the scheduler gives each flow its part" in rq and "[Y2] UDP's own sending rate limits it | competes with Y1" in rq,
    "the test review lists every guess of the researcher, so that a competing cause is called missing only when none states it (s055: H4 held for a cause Y2 stated)")

print("E  EQUAL PREDICTIONS WITH \"CORRECT: PASS\", SETTLED BY ONE QUESTION")
EQ = {**OK3, "if_tested": "held", "if_competitor": "held"}
FIX = {"because": "under Y2 the rule fails", "if_tested": "held", "if_competitor": "failed", "correct": "pass"}
led, calls, users, meta, err = session("e1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")])], [G, G, EQ, FIX, RUL3()])
r1 = next((r["body"] for r in of(led, "review") if r["body"].get("round") == 1), {})
say(calm(err, meta) and rounds(led) == [("H1", 1, "approved", "supervisor")] and r1.get("again") and not r1["again"].get("still") and r1.get("if_competitor") == "failed",
    "asked once, the follow-up says the rule fails under Y2: approved")

print("F  A MISSING COMPETITOR: HELD, AND THE GUESS WRITTEN FROM THE FEEDBACK")
MISS = {**OK3, "consistent": "fail", "consistent_why": "the competing cause is the receiver window, which no guess names", "missing": "the receiver's window limits TCP", "feedback": "Consistent failed: no guess names the receiver window."}
FB = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the receiver's window limits TCP", "revises": None, "competes_with": "Y1"}
led, calls, users, meta, err = session("f1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")]), turn([FB])], [G, G, MISS, G])
st = steps(calls)
y3 = next((r["body"] for r in of(led, "why", 2)), {})
say(calm(err, meta) and rounds(led) == [("H1", 1, "held", "supervisor")] and ("r", "repair") not in st and not of(led, "experiment", 1) and any("the receiver's window limits TCP" in x for x in notes(led)),
    f"held with no repair call, nothing run, the note names the cause: {rounds(led)}")
say(y3.get("competes_with") == "Y1" and str(y3.get("from_feedback", "")).startswith("G"), f"the guess written next turn competing with Y1 is recorded from feedback: {y3.get('from_feedback')}")

print("G  A REVIEW THAT CANNOT BE READ")
led, calls, users, meta, err = session("g1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")])], [G, G, {"_raw": "not JSON"}, RUL3()])
say(calm(err, meta) and any("could not be read" in x for x in notes(led)) and of(led, "verdict"), "a note, and the session goes on")

print("H  MISSES, AND AN UNFAIR TEST REFUTES NOTHING")
led, calls, users, meta, err = session("h1", [turn([A_, B_], [H("Y1"), H("Y1", "UDP loss falls with its part")], [rule("H1", "Y2"), rule("H2", "Y2", r="udp_loss_frac@b < udp_loss_frac@a")])],
                                       [G, G, OK3, OK3, RUL3("inconclusive", ("pass", "fail", "pass"), ("n/a", "yes", "n/a")), RUL3("inconclusive", ("pass", "pass", "fail"), ("n/a", "n/a", "no"))])
v = {r["body"]["for"]: r["body"] for r in of(led, "verdict")}
say(calm(err, meta) and v.get("H1", {}).get("misses") == [{"question": "consistent", "foreseeable": "yes"}] and v.get("H2", {}).get("misses") == [{"question": "correct", "foreseeable": "no"}]
    and not v["H1"].get("fair") and not v["H2"].get("fair"), "H1: Consistent failed, foreseeable (a miss); H2: Correct failed, found by the result")
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import loop, session_figures  # noqa: E402
say(loop.guess_refutations(led) == {}, f"neither unfair test refutes Y2: {loop.guess_refutations(led)}")
cf = session_figures.competitor_figures(led)
say(cf and cf["misses"]["consistent"] == 1 and cf["found_by_result"]["correct"] == 1 and cf["approved_then_unfair"] == 2 and cf["refuted_by_competition"] == 0, f"the figures: {cf}")

print("I  FITS THAT CONTRADICT A FAIR RESULT")
led, calls, users, meta, err = session("i1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")])], [G, G, OK3, RUL3(fc="fits"), {"because": "both fit", "fits_tested": "fits", "fits_competitor": "fits"}])
v = of(led, "verdict")
say(calm(err, meta) and v and v[0]["body"].get("fits_contradicted") and loop.guess_refutations(led) == {}, "asked once and still contradictory: the fits are kept, and refute nothing")

print("J  THE BATCHED FIRST REVIEW WITH A COMPETITOR OF THE SAME REPLY")
BATCH = {"guesses": [{"guess": "G1", **G}, {"guess": "G2", **G}], "tests": [{"for": "H1", **OK3}]}
led, calls, users, meta, err = session("j1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")])], [BATCH, RUL3()], batch=True)
st = steps(calls)
rq = next((c["user"] for c in calls if (c.get("step") or {}).get("step") == "review"), "")
say(calm(err, meta) and st.count(("s", "review")) == 1 and ("s", "design") not in st and "THE GUESS THIS RULE COMPETES WITH [Y2]: the result it explains: UDP gets about half of the link | its guess: UDP's own sending rate limits it" in rq,
    f"one batched request holds the test, with its competitor Y2 written in full: {st}")

print("L  A RESTATED COMPETITOR THAT ALSO REVISES (s055 turn 10: Y29 revised and competed with Y10, and the test against Y10 was refused)")
COMP_G = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the FIFO discipline, not the scheduler, decides the shares", "revises": None, "competes_with": "Y1"}
RESTATE = {"about": ["E0"], "result": "UDP gets 49 % of the link in E0", "guess": "the FIFO discipline, not the scheduler, decides the shares", "revises": "Y1"}
REPEATS = {**G, "defect": "repeats", "nearest_earlier": "Y1"}
led, calls, users, meta, err = session("l1", [turn([A_, COMP_G], [H("Y2", "UDP goodput does not follow its part")], [rule("H1", "Y1")]), RESTATE], [G, REPEATS, G, OK3, RUL3()])
y2 = next((r["body"] for r in of(led, "why") if r["id"] == "Y2"), {})
rq = next((c["user"] for c in calls if (c.get("step") or {}).get("step") == "restate"), "")
say(calm(err, meta) and y2.get("competes_with") == "Y1" and not y2.get("revises") and y2.get("restated") and rounds(led) == [("H1", 1, "approved", "supervisor")] and of(led, "verdict"),
    f"the restated guess competes with Y1 and does not revise it (it named both), so Y1 stays live and the test against it is reviewed and ruled: {y2.get('competes_with')}, revises {y2.get('revises')}, {rounds(led)}")
say("competes_with: Y1" in rq and "never both" in rq, "the restatement is shown the guess's competes_with and asked for it")
L2 = [{"id": "Y1", "type": "why", "turn": 1, "body": {"guess": "a"}}, {"id": "Y2", "type": "why", "turn": 2, "body": {"guess": "b", "revises": "Y1"}},
      {"id": "Y3", "type": "why", "turn": 2, "body": {"guess": "c"}}, {"id": "H1", "type": "hypothesis", "turn": 2, "body": {"from_why": "Y2", "text": "x"}},
      {"id": "H2", "type": "hypothesis", "turn": 2, "body": {"from_why": "Y3", "text": "y"}}]
loop.COMP["on"] = True
m1 = loop.competitor_problem({"for": "H1", "competes_with": "Y1", "rival_predicts": "failed"}, L2); m2 = loop.competitor_problem({"for": "H2", "competes_with": "Y1", "rival_predicts": "failed"}, L2)
say("Y2 is H1's own guess" in str(m1) and "name the live guess (Y2" not in str(m1) and "name the live guess (Y2, or another)" in str(m2),
    f"a revised competitor: the refusal never offers the hypothesis's own guess ({m1}); for another hypothesis it offers the reviser ({m2})")

print("M  THE BATCHED FIRST REVIEW MARKS THE REPLY'S NEW GUESSES (s056: the supervisor named a new guess as its own nearest earlier guess, a repeat of itself)")
SELF = {"guesses": [{"guess": "G1", **G, "nearest_earlier": "Y1", "defect": "repeats", "because": "it repeats Y1"}, {"guess": "G2", **G}], "tests": [{"for": "H1", **OK3}]}
led, calls, users, meta, err = session("m1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")])], [SELF, G, RUL3()], batch=True)
st = steps(calls)
rq = next((c["user"] for c in calls if (c.get("step") or {}).get("step") == "review"), "")
gr = [(r["body"].get("for"), r["body"].get("decision"), r["body"].get("defect")) for r in of(led, "review") if r["body"].get("gate") == "ground"]
say("[Y1] (new in this reply: G1 below)" in rq and "[Y2] (new in this reply: G2 below)" in rq and "(G1 is Y1, G2 is Y2)" in rq and "never the guess itself" in rq,
    "the request marks the reply's new guesses in the list, says which id each has, and that a new guess's nearest earlier guess is never itself")
say(calm(err, meta) and any("named the guess itself (Y1)" in n for n in notes(led)) and st.count(("s", "review")) == 1 and st.count(("s", "ground")) == 1
    and gr == [("Y1", "approved", "none"), ("Y2", "approved", "none")] and rounds(led) == [("H1", 1, "approved", "supervisor")] and of(led, "verdict"),
    f"a batched reading that names the guess itself is not taken: a note, that guess is read alone and accepted, the other guess and the test as the batch read them: {st}; {gr}")

print("N  A GUESS THAT COMPETES WITH A LATER GUESS OF THE SAME ANSWER (s057: Y3 named Y4, and was marked contested: \"'Y4' is not a guess\")")
FWD = {**A_, "competes_with": "Y2"}
led, calls, users, meta, err = session("n1", [turn([FWD, {**B_, "competes_with": None}], [H("Y1")], [rule("H1", "Y2")])], [G, G, OK3, RUL3()])
ys = {r["id"]: r["body"] for r in of(led, "why")}
st = steps(calls)
say(calm(err, meta) and ys.get("Y1", {}).get("competes_with") == "Y2" and not ys.get("Y1", {}).get("contested") and not ys.get("Y1", {}).get("restated") and "Y2" in ys
    and ("r", "restate") not in st and rounds(led) == [("H1", 1, "approved", "supervisor")] and of(led, "verdict"),
    f"Y1 competes with Y2, written after it, with no restatement and no contest; the test is reviewed and ruled: {[(k, v.get('competes_with'), bool(v.get('contested'))) for k, v in ys.items()]}; {st}")
led, calls, users, meta, err = session("n2", [turn([FWD, {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "", "revises": None, "competes_with": None}], [H("Y1")], [rule("H1", "Y2")])], [G, G, OK3, RUL3()])
ys = {r["id"]: r["body"] for r in of(led, "why")}
say(calm(err, meta) and list(ys) == ["Y1"] and ys["Y1"].get("competes_with") is None and "was not accepted, so this guess competes with none" in str(ys["Y1"].get("contested")),
    f"if that later guess is not accepted, the guess competes with none and says so: {[(k, v.get('competes_with'), v.get('contested')) for k, v in ys.items()]}")

print("O  EACH REPLY REQUEST SAYS THE IDS ITS NEW GUESSES AND HYPOTHESES WILL GET (s057 turn 3 numbered its guesses from Y13, not Y10, and lost its test)")
led, calls, users, meta, err = session("o1", [turn([A_, B_], [H("Y1")], [rule("H1", "Y2")])], [G, G, OK3, RUL3()])
rq = [u for u in users if "NEW IDS" in u or "LEDGER:" in u]   # every reply request, the last one too (the script had no answer for it)
say(len(rq) >= 2 and "NEW IDS: the guesses you write in this answer are recorded as Y1, Y2, ... and your new hypotheses as H1, H2, ..." in rq[0]
    and "recorded as Y3, Y4, ... and your new hypotheses as H2, H3, ..." in rq[1],
    f"turn 1 is told Y1 and H1, turn 2 (after Y1, Y2 and H1) Y3 and H2: {[x[x.find('NEW IDS'):x.find('NEW IDS') + 110] for x in rq[:2]]}")

print("K  THE INSTRUCTIONS AND THEIR SIZE")
t = loop.supervised_prompt("", True) + loop.FINDINGS_TEXT["supervised"]
say(len(t) <= 10_000 and "competes_with" in t and "Honest" in t, f"the instructions with competitors: {len(t)} characters of the one limit of 10,000 (without: {len(loop.LEAN_PROMPT + loop.FINDINGS_TEXT['supervised'])})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
