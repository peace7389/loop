"""Stage 2 of the coherence audit (2026-11-22): one source per rule, each arm told what it can do. Scripted sessions (scripted.py), real ns-3 runs:
  P  the arm "plain" on a brief whose network may change: its whole system text names no hypothesis, verdict, decision rule or rethink, and its
     brief's how_to_run is its own (STRUCTURE was added after its word check; how_to_run spoke of decision rules);
  B  the follow-up question on a review whose boxes disagree: it shows the rival the review named, its box rival_is_weak may change (s052 H2 was
     approved this way and ruled inconclusive for that very rival), it is asked with 2,000 tokens (1,000 reasoning); one that cannot be read is
     a refusal (it was a run unreviewed);
  C  a repair the harness refuses in the last round is "not_run", by the harness, and the hypothesis stays open (it was "contested");
  D  a repair that gives only a new simulation keeps the others (any list replaced all); its prompt shows the records the feedback and the guess
     cite; the ruling is shown the researcher's rival;
  N  a repair on a network brief is shown a network change written correctly for that network, and a run keeps its change;
  F  the objection's second look sees the readings and says whether the test was fair: "supported" from an unfair test is inconclusive;
  G  a ruling asked for again at the start of a turn is in that turn's ledger text (it was rendered before);
  H  the arm "hypotheses" with continued replies: turns with requests only are counted by turn, not by reply;
  J  a guess whose review could not be read is shown as read by no one, not as sound;
  K  the arm "hypotheses": a report given with an experiment waits for that experiment's results;
  U  == within the tolerance; learned_since leaves out the harness's rounds and counts simulations; calls are counted by agent.
python3 -I test_stage2.py SCRATCH_DIR [HARNESS_DIR]"""
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
def session(sid, answers, sup=None, arm="supervised", brief="two-hosts-open-2", budget=8, sets=None):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup or []}))
    env = {**os.environ, "HOME": str(SCR / "home"), **({"SCRIPTED_SET": json.dumps(sets)} if sets else {})}
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, "--budget", str(budget)] + (["--arm", arm] if arm != "hypotheses" else []),
                       env=env, capture_output=True, text=True, timeout=1500)
    S = P / "sessions" / sid
    if "Traceback" in r.stderr: print(r.stderr[-2000:])
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    rd = lambda n: json.loads((S / n).read_text()) if (S / n).is_file() else []
    calls = [json.loads(l) for l in (S / "calls.jsonl").read_text().splitlines() if l.strip()] if (S / "calls.jsonl").is_file() else []
    return led, rd("supervisor_sent.json"), json.loads((S / "session.json").read_text()), r.stderr, rd("users_sent.json"), calls
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led: [str(r["body"].get("text") or r["body"].get("reason") or "") for r in of(led, "note")]
rounds = lambda led: [(r["body"]["round"], r["body"]["decision"], r.get("by")) for r in of(led, "review") if r["body"].get("gate") == "design"]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
REV = {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": "failed", "doubt_if": "nothing", "because": "reasoned", "defect": "none", "feedback": ""}
BACK = {**REV, "defect": "confounded", "feedback": "Another setting hides the effect, as E0 shows."}
CONTRA = {**REV, "stronger_rival": "a larger part only lowers the drops", "defect": "rival_passes_too", "feedback": "A stronger rival: a larger part only lowers the drops."}
AGAIN_WEAK = {"because": "the stronger rival passes the rule too", "stronger_rival": "a larger part only lowers the drops", "rival_is_weak": True, "rival_outcome": "held", "defect": "rival_passes_too"}
RUL = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
RIV = {"rival": "UDP's own sending rate limits it", "rival_predicts": "failed"}
def turn(why=True, hyp=True, ex=None, **k):
    return {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None,
            "whys": [{"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "revises": None}] if why else [],
            "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part"}] if hyp else [], "experiment": ex, **k}
TEST = {"kind": "test", "tests": ["H1"], "question": "", "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [], "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", **RIV}]}
GOOD = {"decision_rule": "udp_goodput_bps@b > 1.2 * udp_goodput_bps@a", **RIV, "runs": []}
BAD = {"decision_rule": "udp_goodput_bps@b != udp_goodput_bps@a", **RIV, "runs": []}
step_of = lambda c: (c.get("step") or {}).get("step")

print("P  THE ARM \"plain\": ITS WHOLE TEXT, AND ITS OWN how_to_run")
led, sup, meta, err, users, calls = session("p1", ["not JSON"] * 2, arm="plain", brief="again_again")
sys_text = calls[0]["system"].lower() if calls else ""
words = [w for w in ("hypothes", "verdict", "decision rule", "decision_rule", "rethink") if w in sys_text]
shown = json.loads(users[0].split("BRIEF:\n", 1)[1].split("\n\nSIMULATION BUDGET", 1)[0]) if users and "BRIEF:\n" in users[0] else {}
say(calls and not words and "structure of the network" in sys_text, f"the plain arm's instructions tell it how to change the network and name none of the other arms' words ({words or 'none'})")
say("how_to_run" not in shown or ("decision rule" not in shown["how_to_run"] and "every knob" in shown["how_to_run"]), f"its brief's how_to_run is its own: {shown.get('how_to_run', '(none in this brief)')[:160]}")

print("B  THE FOLLOW-UP QUESTION")
led, sup, meta, err, users, calls = session("b1", [turn(ex=TEST), GOOD], [G, CONTRA, AGAIN_WEAK, REV, RUL])
r1 = next((r["body"] for r in of(led, "review") if r["body"].get("gate") == "design" and r["body"]["round"] == 1), {})
fu = [c for c in calls if c["agent"] == "supervisor" and "These do not fit together" in c["user"]]
say(r1.get("decision") == "sent_back" and (r1.get("again") or {}).get("rival_is_weak") is True and r1.get("rival_is_weak") is True,
    f"the follow-up says a clearly stronger rival exists after all: the test is sent back ({r1.get('decision')}; again: {json.dumps(r1.get('again'))[:160]})")
say(fu and "The strongest rival you named: a larger part only lowers the drops" in fu[0]["user"] and fu[0]["max_tokens"] == 2000,
    f"the question shows the rival the review named, and is asked with {fu[0]['max_tokens'] if fu else '?'} tokens (1,000 of reasoning)")
say(meta.get("calls_by_agent", {}).get("supervisor", 0) >= 5 and meta.get("calls_by_agent", {}).get("researcher", 0) >= 2, f"calls are counted by agent: {meta.get('calls_by_agent')}")
led, sup, meta, err, users, calls = session("b2", [turn(ex=TEST), GOOD], [G, CONTRA, {"_raw": "not JSON"}, REV, RUL])
r1 = next((r["body"] for r in of(led, "review") if r["body"].get("gate") == "design" and r["body"]["round"] == 1), {})
say(r1.get("decision") == "sent_back" and (r1.get("again") or {}).get("unread") and not any("run unreviewed" in n for n in notes(led)),
    f"a follow-up that cannot be read is a refusal, not a run unreviewed ({r1.get('decision')}; {rounds(led)})")

print("C  A HARNESS REFUSAL IN THE LAST ROUND")
led, sup, meta, err, users, calls = session("c1", [turn(ex=TEST), BAD, BAD], [G, BACK])
rr = rounds(led)
say(rr == [(1, "sent_back", "supervisor"), (2, "sent_back", "harness"), (3, "not_run", "harness")] and not of(led, "drop") and not of(led, "experiment", 1),
    f"round 3 refused by the harness is not_run, and nothing is dropped or run ({rr})")
say(users and "not run: the harness could not use the last repair, and the hypothesis stays open" in users[-1], "the next turn's ledger text says so")

print("D  A REPAIR THAT GIVES ONLY A NEW SIMULATION; WHAT THE REPAIR AND THE RULING ARE SHOWN")
NEWC = {"decision_rule": "udp_goodput_bps@c > 1.2 * udp_goodput_bps@a", **RIV, "runs": [d("c", 0.9)]}
led, sup, meta, err, users, calls = session("d1", [turn(ex=TEST), NEWC], [G, BACK, REV, RUL])
xs = [[q["label"] for q in r["body"]["runs"]] for r in of(led, "experiment", 1)]
rp = next((c["user"] for c in calls if step_of(c) == "repair"), "")
say(xs == [["a", "c"]], f"the repaired test runs a (kept) and c (new): {xs}")
say("runs: only the simulations that are new or change" in rp and "THE RECORDS THE FEEDBACK AND YOUR GUESS CITE:" in rp and "[E0] measured in X0" in rp,
    "the repair prompt says how runs are read, and shows E0, which the feedback and the guess cite")
say(sup and "THE RESEARCHER'S RIVAL for the rule udp_goodput_bps@c > 1.2 * udp_goodput_bps@a: UDP's own sending rate limits it" in sup[-1], "the ruling is shown the researcher's rival")

print("N  A REPAIR ON A NETWORK BRIEF")
sched = [{"do": "remove", "id": "l1", "kind": "queue", "on": "sender"}, {"do": "add_queue", "id": "l1", "kind": "scheduler", "on": "sender"}]
NET = {"kind": "test", "tests": ["H1"], "question": "", "measurements": [],
       "runs": [{"label": "fifo", "params": {"l1.queue.length": 100, "tcp.type": "TcpCubic"}}, {"label": "sched", "params": {"l1.queue.length": 100, "tcp.type": "TcpCubic"}, "structure": sched}],
       "decision_rules": [{"for": "H1", "decision_rule": "tcp_goodput_bps@sched > tcp_goodput_bps@fifo", "rival": "UDP fills any queue", "rival_predicts": "failed"}]}
TA = {**turn(ex=NET), "whys": [{"about": ["E0"], "result": "TCP gets 0 bps at the default", "guess": "the shared FIFO is always full of UDP", "revises": None}],
      "hypotheses": [{"from_why": "Y1", "text": "a scheduler gives TCP a share"}]}
RN = {"decision_rule": "tcp_goodput_bps@sched > 1.1 * tcp_goodput_bps@fifo", "rival": "UDP fills any queue", "rival_predicts": "failed", "runs": []}
led, sup, meta, err, users, calls = session("n1", [TA, RN], [G, BACK, REV, RUL], brief="again_again")
rp = next((c["user"] for c in calls if step_of(c) == "repair"), "")
x = next((r["body"] for r in of(led, "experiment", 1)), {})
say('for example, on this network: [{"do": "remove", "id": "l1", "kind": "queue"' in rp and "a run keeps its change unless the feedback is about it" in rp,
    "the repair prompt shows a change written correctly for this network, and that a run keeps its change")
say(any(q["label"] == "sched" and q.get("structure") for q in x.get("runs") or []), f"the repaired test's sched run keeps its scheduler: {[(q['label'], bool(q.get('structure'))) for q in x.get('runs') or []]}")

print("F  THE OBJECTION'S SECOND LOOK")
OBJ = {**turn(why=False, hyp=False), "objections": [{"to": "V1", "because": "a rival passes the rule too"}]}
APPEAL = {"answer": "the objection is right", "fair": False, "stands": False, "result": "supported", "because": "a rival passes it too"}
led, sup, meta, err, users, calls = session("f1", [turn(ex=TEST), OBJ], [G, REV, RUL, APPEAL])
v = [(r["id"], r["body"]["result"], r["body"].get("fair")) for r in of(led, "verdict")]
look = next((u for u in sup if "THE RESEARCHER OBJECTS" in u), "")
say(len(v) == 2 and v[1][1:] == ("inconclusive", False), f"\"supported\" from a test the second look finds unfair is inconclusive: {v}")
say("EVERY READING OF THE SESSION" in look and "First say whether the test was fair" in look and "THE RESEARCHER'S RIVAL" in look, "the second look is shown the readings and the rival, and asked about fairness")

print("G  A RULING ASKED FOR AGAIN IS IN THAT TURN'S LEDGER TEXT")
led, sup, meta, err, users, calls = session("g1", [turn(ex=TEST), turn(why=False, hyp=False)], [G, REV, {"_raw": "not JSON"}, RUL])
v = of(led, "verdict")
say(v and v[0]["turn"] == 2 and len(users) >= 2 and f"[{v[0]['id']}]" in users[1], f"the ruling made at the start of turn 2 ({v[0]['id'] if v else '-'}) is in turn 2's ledger text")

print("H  THE ARM \"hypotheses\": TURNS WITH REQUESTS ONLY, COUNTED BY TURN")
ONE = {"observations": "read", "findings": [], "rethink": [], "budget_request": None, "done": False, "verdicts": [], "drop": [], "decisions": [], "report": None, "whys": [], "hypotheses": [], "experiment": None,
       "requests": [{"tool": "metrics", "args": {"run_id": "r001"}}]}
led, sup, meta, err, users, calls = session("h1", [ONE] * 9, arm="hypotheses", sets={"CONTINUES": 2})
said = [i for i, u in enumerate(users) if "The limit of turns with requests only is reached" in u]
say(len(of(led, "turn")) >= 3 and not any(i < 9 for i in said), f"three turns of three replies with requests only: the limit of 3 such turns is not reached ({len(of(led, 'turn'))} turns; limit said at replies {said})")

print("J  A GUESS WHOSE REVIEW COULD NOT BE READ")
led, sup, meta, err, users, calls = session("j1", [turn(hyp=False), turn(why=False, hyp=False)], [{"_raw": "not JSON"}])
g = next((r["body"] for r in of(led, "review") if r["body"].get("gate") == "ground"), {})
say(g.get("unread") and len(users) >= 2 and "not read (the supervisor's reading could not be read), and the guess is accepted unread" in users[1] and "sound: it starts from" not in users[1],
    "the ledger text says the guess was accepted unread, not that it is sound")

print("K  THE ARM \"hypotheses\": A REPORT GIVEN WITH AN EXPERIMENT")
def hturn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def hyp(text): return {"text": text, "question": "Is it so?", "why": "It decides the answer.", "prediction": "yes", "follows_from": ["brief"]}
HT = {"kind": "test", "tests": ["H1"], "question": "", "varied": ["weightUdp"], "control": None, "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [],
      "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "something else limits it", "rival_predicts": "failed"}]}
REP = {"goal": "the larger UDP goodput", "recommendation": {"weightUdp": 0.7, **{k: v for k, v in KN.items() if k != "seed"}}, "expected": {"udp_goodput_bps": 685000000.0}, "no_difference": [], "limit": "UDP's part of the link: E1.",
       "explanation": "UDP's goodput follows its part of the link.", "holds_when": "as tested", "breaks_when": "other rates", "claims": [{"text": "A larger part gives UDP more.", "role": "supports", "evidence": ["E1"]}], "open_questions": []}
REP0 = {**REP, "limit": "UDP's part of the link: E0.", "claims": [{"text": "UDP gets a part of the link.", "role": "supports", "evidence": ["E0"]}]}   # turn 1's report cites what exists then
led, sup, meta, err, users, calls = session("k1", [hturn(hypotheses=[hyp("UDP gets more at the part 0.7")], experiment=HT, report=REP0, done=True),
                                                   hturn(verdicts=[{"for": "H1", "result": "supported", "because": "C1 held", "next": "go on"}], report=REP, done=True)], arm="hypotheses")
reps = [r["turn"] for r in of(led, "report")]
say(of(led, "experiment", 1) and reps == [2] and any("the report is held back: this answer's experiment" in n for n in notes(led)) and meta.get("how") == "done by the model",
    f"turn 1's experiment runs and its report waits; turn 2's report ends the session (reports in turns {reps}; {meta.get('how')})")

print("U  UNITS: == WITHIN THE TOLERANCE, learned_since")
sys.path.insert(0, str(P / "harness"))
os.environ["HOME"] = str(SCR / "home")
import decision_rules, loop  # noqa: E402
vals = {"a": {"x": 100.0}, "b": {"x": 100.5}}
decision_rules.EQUAL_WITHIN = 1.0
h1 = decision_rules.check("x@a == x@b", {"x": ""}, ["a", "b"], vals)[0]
decision_rules.EQUAL_WITHIN = 0.0
h0 = decision_rules.check("x@a == x@b", {"x": ""}, ["a", "b"], vals)[0]
say(h1 and not h0, f"100 == 100.5 holds within a tolerance of 1 % ({h1}) and not with none ({h0})")
L = [{"id": "Y1", "type": "why", "turn": 1, "body": {}}, {"id": "G1", "type": "review", "turn": 1, "by": "harness", "body": {"decision": "sent_back"}},
     {"id": "G2", "type": "review", "turn": 1, "by": "supervisor", "body": {"decision": "sent_back"}}, {"id": "S3", "type": "simulation", "turn": 1, "body": {}}]
got = loop.learned_since(L, 2)
say(got == {"G2", "S3"}, f"learned since the last guess: the supervisor's objection and the simulation, not the harness's round ({sorted(got)})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
