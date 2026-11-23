"""The fixed chain of reasoning (2026-11-17, the operator): a result -> informed guesses of why it came out so (whys) ->
which of them are worth verifying for the goal -> a hypothesis from such a why -> what must be known to decide it (its
need) -> only the simulations that need asks for. And: one experiment may run at most half of the simulations left.
  - the answer format has whys before hypotheses, from_why first in a hypothesis, needs before the simulations of an
    experiment; the instructions say the role first and the chain link by link;
  - a scripted session through the whole chain: whys about the baseline (one to verify, one set aside), a hypothesis
    from the first, its need, two simulations that differ in one knob, the check, the verdict, the report; the ledger
    holds the why records and the links;
  - refused with the reason: a why about a record that is not there; a hypothesis from no why, from a why that was set
    aside; a test without needs; a need whose simulations differ in two knobs; a rule that names a simulation its need
    does not list, or not its measure; a simulation made for no hypothesis; an experiment larger than half of what is left;
  - the session's last turn says how the session ended in the new words.
    python3 -I test_chain.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new. Simulations are real ns-3 runs of 2 measured seconds."""
import copy, json, os, shutil, subprocess, sys
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
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import tools, loop
print("THE CHAIN: RESULT, WHY, WHAT IS WORTH VERIFYING, HYPOTHESIS, NEED, SIMULATIONS")
BRIEF = "two-hosts-udp-demand-2"; g = tools.load_brief(BRIEF)
fmt = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), g); prompt = (P / "harness/prompt.txt").read_text()
hyp, ex = fmt["properties"]["hypotheses"]["items"], fmt["properties"]["experiment"]["anyOf"][0]
say(list(fmt["properties"])[:4] == ["observations", "rethink", "whys", "hypotheses"] and fmt["properties"]["rethink"]["items"]["required"] == ["id", "in_light_of", "now", "because"] and fmt["properties"]["whys"]["items"]["required"] == ["about", "result", "guess", "unseen", "matters", "worth", "reason", "revises"] and hyp["required"][0] == "from_why"
    and list(ex["properties"]).index("needs") < list(ex["properties"]).index("runs") and ex["properties"]["needs"]["items"]["properties"]["varies"]["enum"] == [*g["knobs"], "none"] and "needs" in ex["required"],
    "the answer format: the rethink of earlier whys stands first, then the new whys (each may revise an earlier one), before hypotheses, a hypothesis states first the why it comes from, and an experiment states its needs before its simulations (varies: one of the brief's knobs, or none)")
say(all(x in prompt for x in ("Your main role is not to try many settings", "look into the system", "2. whys:", "from a why you chose to verify", "- needs:", "decide first what you need to know", "at most half of the simulations that are left"))
    and prompt.index("Your main role") < prompt.index("1. observations"), "the instructions say the role first (not many settings: look into the system, ask why), then the chain link by link, and the rule of half of what is left")

KN = dict(queuePkts=100, tcpVariant="TcpCubic", duration=2)
def d(label, w, **over): return {"label": label, "params": {"weightUdp": w, **KN, **over}}
def turn(**k): return {"observations": "read", "rethink": [], "whys": [], "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
W = lambda about, worth, guess="UDP's part of the link is larger than what UDP sends, and the scheduler passes the rest to TCP": {"about": about, "result": "TCP delivers more than its part of the link would allow.", "guess": guess,
    "unseen": "how the scheduler treats a part that is not used", "matters": "then a smaller UDP part gains nothing for TCP", "worth": worth, "reason": "it decides whether the ratio matters at all" if worth == "verify" else "it cannot change the goal"}
H = {"from_why": "Y1", "text": "TCP goodput does not change with the UDP part once UDP loses nothing", "question": "Does TCP get the same with a larger UDP part?", "why": "It says whether the ratio matters.", "prediction": "the same within 1 %"}
NEED = {"for": "H1", "to_know": "whether TCP goodput is the same at two UDP parts that are both above UDP's demand", "varies": "weightUdp", "measure": "tcp_goodput_bps", "simulations": ["w50", "w80"]}
RULE = {"for": "H1", "decision_rule": "abs(tcp_goodput_bps@w50 - tcp_goodput_bps@w80) < 0.05 * tcp_goodput_bps@w50", "rival": "TCP is held to its own part", "rival_predicts": "failed"}
EXP = {"kind": "test", "tests": ["H1"], "question": "", "needs": [NEED], "varied": ["weightUdp"], "control": "w50", "runs": [d("w50", 0.5), d("w80", 0.8)], "decision_rules": [RULE]}
REP = {"goal": "the largest TCP goodput while UDP loses at most 1 %", "recommendation": {"weightUdp": 0.5, **KN}, "expected": {"tcp_goodput_bps": 660000000.0}, "no_difference": ["weightUdp"],
       "limit": "The link is full once UDP has what it sends: E1.", "explanation": "The ratio does not matter above UDP's demand.", "holds_when": "as tested", "breaks_when": "other rates",
       "claims": [{"text": "TCP takes what UDP leaves.", "role": "supports", "evidence": ["C1"]}], "open_questions": []}
# the whys are not fixed by how they were first stated: in turn 2, with the results of E1, the guess that was set aside is taken up (rethink) and the
# first guess is replaced by a better one (a new why that revises it); the next hypothesis comes from that new why
H2 = {**H, "from_why": "Y3", "text": "TCP goodput is the same at any UDP part above UDP's demand, also a very large one", "question": "Is TCP the same with an even larger UDP part?"}
EXP2 = {**EXP, "tests": ["H2"], "control": "w60", "runs": [d("w60", 0.6), d("w90", 0.9)], "needs": [{**NEED, "for": "H2", "simulations": ["w60", "w90"]}],
        "decision_rules": [{**RULE, "for": "H2", "decision_rule": "abs(tcp_goodput_bps@w60 - tcp_goodput_bps@w90) < 0.05 * tcp_goodput_bps@w60"}]}
ANSWERS = [turn(whys=[W(["E0"], "verify"), W(["E0"], "set_aside", guess="the seed")], hypotheses=[H], experiment=EXP),
           turn(verdicts=[{"for": "H1", "result": "supported", "because": "C1 held.", "next": "a wider range"}],
                rethink=[{"id": "Y2", "in_light_of": ["E1"], "now": "verify", "because": "E1 leaves the seed as the only thing not yet looked at."}],
                whys=[{**W(["E1", "C1"], "verify", guess="the scheduler gives TCP everything UDP does not send, whatever the parts say"), "revises": "Y1"}],
                hypotheses=[H2, {**H2, "text": "UNRELATED: a longer measured time gives TCP more", "question": "Does a longer run give TCP more?"}], experiment=EXP2),   # the second one does not follow from Y3: the judge refuses it
           turn(verdicts=[{"for": "H2", "result": "supported", "because": "C2 held.", "next": "report"}], report=REP, done=True,   # Y2, taken up in turn 2, led to no hypothesis: it is settled before the report
                rethink=[{"id": "Y2", "in_light_of": ["E2"], "now": "set_aside", "because": "E2 shows the same to the last digit: the seed plays no part."},
                         {"id": "Y3", "in_light_of": ["C2"], "now": "supported", "because": "C2 held: TCP is the same at an even larger UDP part."}])]   # the last step is reviewed too: what C2 did to Y3
f = SCR / "k1.answers.json"; f.write_text(json.dumps(ANSWERS))
r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", BRIEF, "--session", "k1"], env=ENV, capture_output=True, text=True, timeout=1200)
if r.returncode: print(r.stdout[-600:], r.stderr[-2500:])
led = [json.loads(l) for l in (P / "sessions/k1/ledger.jsonl").read_text().splitlines() if l.strip()]; meta = json.loads((P / "sessions/k1/session.json").read_text())
of = lambda ty: [x for x in led if x["type"] == ty]
ws, hs, xs = of("why"), of("hypothesis"), [x for x in of("experiment") if x["id"] != "X0"]
say([w["id"] for w in ws][:2] == ["Y1", "Y2"] and [w["body"]["worth"] for w in ws][:2] == ["verify", "set_aside"] and ws[0]["by"] == "model" and hs and hs[0]["body"]["from_why"] == "Y1" and hs[0]["body"]["follows_from"] == ["E0"],
    f"the two whys about the baseline are recorded (Y1 to verify, Y2 set aside), and the hypothesis says it comes from Y1; what it follows from is taken from the why ({hs[0]['body'].get('follows_from') if hs else None})" + (f" {[n['body'] for n in of('malformed') + of('note')][-1:]}" if not hs else ""))
say(xs and xs[0]["body"].get("needs") == [NEED] and len([s for s in of("simulation") if s.get("parent") == xs[0]["id"]]) == 2 and of("check") and of("check")[0]["body"]["result"] in ("held", "failed"),
    f"its need is recorded with the experiment (what must be known, the one knob that varies, the measure, the two simulations), the two simulations ran, and the rule was checked ({of('check')[0]['body']['result'] if of('check') else None})")
user2 = json.loads((P / "sessions/k1/users_sent.json").read_text())[1]
say("[Y1] turn 1 why [worth verifying; stated before the results of E1, C1: rethink it before a new hypothesis comes from it] about E0:" in user2 and "[Y2] turn 1 why [set aside]" in user2 and "from Y1:" in user2 and "may run at most" in user2 and "half of what is left" in user2,
    "the next turn shows the model its whys (which it chose to verify, which it set aside), the hypothesis with the why it comes from, and how many simulations this turn may run")
user3 = json.loads((P / "sessions/k1/users_sent.json").read_text())[2]; ks = of("rethink")
say(len(ks) == 3 and ks[1]["body"]["now"] == "set_aside" and ks[2]["body"]["now"] == "supported" and ks[0]["id"] == "K1" and ks[0]["by"] == "model" and ks[0]["body"]["for"] == "Y2" and ks[0]["body"]["now"] == "verify" and len(ws) == 3 and ws[2]["body"].get("revises") == "Y1" and "revises" not in ws[0]["body"]
    and len(hs) == 2 and hs[1]["body"]["from_why"] == "Y3" and len(xs) == 2 and len(of("check")) == 2
    and "[Y1] turn 1 why [revised as Y3] about E0:" in user3 and "[Y2] turn 1 why [worth verifying" in user3 and "[K1] turn 2 rethink of Y2 in the light of E1: now worth verifying." in user3 and "[Y3] turn 2 why [worth verifying" in user3 and "revises Y1: about E1, C1:" in user3,
    "the whys are not fixed: in turn 2 the guess that was set aside is taken up in the light of E1 (rethink K1), the first guess is replaced by a better one (Y3 revises Y1), the next hypothesis comes from Y3 and is tested; the next turn shows each why with its standing now")
say(meta.get("how") == "done by the model" and len(of("report")) == 1, f"the report ends the session (“{meta.get('how')}”)")

# ---- each link refused where it is broken
loop.tools.open_session("k2", BRIEF); brief = loop.tools.describe_system(); ledger = [x for x in led if x["turn"] == 0]   # a session with its baseline only
def refusals(t): return [(p, w) for p, w in loop.sort_out(turn(**t), brief, ledger, 40)[1]]
def first(t, part): return next((w for p, w in refusals(t) if part in p), "")
ok = {"whys": [W(["E0"], "verify")], "hypotheses": [H]}   # the links before the experiment, as they should be
X = lambda **k: first({**ok, "experiment": {**EXP, **k}}, "experiment")
run0 = next(x["body"]["run_id"] for x in ledger if x["type"] == "simulation")
by_run = loop.sort_out(turn(whys=[W([f"series {run0}"], "verify"), W([run0], "set_aside")]), brief, ledger, 40)
cases = {"a why about a record that is not there": (first({"whys": [W(["E9"], "verify")]}, "why"), "about names ids that are not in the ledger: E9"),
         "a hypothesis from no why": (first({"hypotheses": [{k: v for k, v in H.items() if k != "from_why"}]}, "hypothesis"), "a hypothesis comes from a why you chose to verify"),
         "a hypothesis from a why that was set aside": (first({"whys": [W(["E0"], "set_aside")], "hypotheses": [H]}, "hypothesis"), "Y1 was set aside"),
         "a test without needs": (first({**ok, "experiment": {k: v for k, v in EXP.items() if k != "needs"}}, "experiment"), "needs one entry in needs for each hypothesis it tests"),
         "a need whose simulations differ in two knobs": (X(runs=[d("w50", 0.5), d("w80", 0.8, queuePkts=200)]), "also differ in queuePkts"),
         "a rule that names a simulation its need does not list": (X(runs=[d("w50", 0.5), d("w80", 0.8), d("w30", 0.3)], decision_rules=[{**RULE, "decision_rule": "tcp_goodput_bps@w30 > tcp_goodput_bps@w50"}]), "which is not one of the simulations its need lists"),
         "a rule that does not name the need's measure": (X(decision_rules=[{**RULE, "decision_rule": "udp_loss_frac@w50 <= udp_loss_frac@w80"}]), "does not name `tcp_goodput_bps`"),
         "a simulation made for no hypothesis": (X(runs=[d("w50", 0.5), d("w80", 0.8), d("w30", 0.3)]), "simulation `w30` is made for no hypothesis"),
         "whys about a run's series, by the run id (they stand for that run's simulation)": ("" if not by_run[1] and [w["about"] for w in by_run[0]["whys"]] == [["S0"], ["S0"]] else f"refused {by_run[1]} or about {[w.get('about') for w in by_run[0]['whys']]}", None),
         "a why without what is not visible": (first({"whys": [{**W(["E0"], "verify"), "unseen": ""}]}, "why"), "a why needs result"),
         "a hypothesis from no why": (first({"hypotheses": [{**H, "from_why": ""}]}, "hypothesis"), "a hypothesis comes from a why you chose to verify"),
         "a hypothesis from a why that was set aside": (first({"whys": [W(["E0"], "set_aside")], "hypotheses": [H]}, "hypothesis"), "Y1 was set aside"),
         "a test without needs": (first({"whys": [W(["E0"], "verify")], "hypotheses": [H], "experiment": {**EXP, "needs": []}}, "experiment"), "needs one entry in needs for each hypothesis"),
         "a need whose simulations differ in two knobs": (first({"whys": [W(["E0"], "verify")], "hypotheses": [H], "experiment": {**EXP, "runs": [d("w50", 0.5), d("w80", 0.8, queuePkts=20)]}}, "experiment"), "also differ in queuePkts"),
         "a need that says nothing varies but lists two": (first({"whys": [W(["E0"], "verify")], "hypotheses": [H], "experiment": {**EXP, "needs": [{**NEED, "varies": "none"}]}}, "experiment"), "says nothing varies"),
         "a rule that names a simulation its need does not list": (first({"whys": [W(["E0"], "verify")], "hypotheses": [H], "experiment": {**EXP, "runs": [d("w50", 0.5), d("w80", 0.8), d("w30", 0.3)], "needs": [NEED], "decision_rules": [{**RULE, "decision_rule": "tcp_goodput_bps@w30 > tcp_goodput_bps@w50"}]}}, "experiment"), "is not one of the simulations its need lists"),
         "a rule that does not name the need's measure": (first({"whys": [W(["E0"], "verify")], "hypotheses": [H], "experiment": {**EXP, "decision_rules": [{**RULE, "decision_rule": "udp_loss_frac@w50 <= udp_loss_frac@w80"}]}}, "experiment"), "does not name `tcp_goodput_bps`"),
         "a simulation made for no hypothesis": (first({"whys": [W(["E0"], "verify")], "hypotheses": [H], "experiment": {**EXP, "runs": [d("w50", 0.5), d("w80", 0.8), d("w30", 0.3), d("w20", 0.2)]}}, "experiment"), "is made for no hypothesis"),
         "the whole chain as it should be": ("; ".join(w for p, w in refusals({"whys": [W(["E0"], "verify")], "hypotheses": [H], "experiment": EXP})), None)}
say(all((w in got) if w else not got for got, w in cases.values()), "each link is refused where it is broken, with the reason: " + ", ".join(k for k, (g_, w) in cases.items() if w) + "; and the whole chain is accepted"
    + "".join(f" [{k}: {got[:120]}]" for k, (got, w) in cases.items() if (w not in got if w else got)))
# ---- the whys are looked at again: with the results of the first experiment in the ledger
ledger1 = [x for x in led if x["turn"] <= 1]; Hn = {**H, "text": "another claim from the first guess"}
def ref1(t, part): return next((w for p, w in loop.sort_out(turn(**t), brief, ledger1, 38)[1] if part in p), "")
again = lambda now, light=("E1",), y="Y1": {"id": y, "in_light_of": list(light), "now": now, "because": "what E1 shows"}
cases = {"a hypothesis from a why stated before the latest results, not looked at again": (ref1({"hypotheses": [Hn]}, "hypothesis"), "Y1 was stated before the results of E1"),
         "a rethink that names no result that came in since": (ref1({"rethink": [again("verify", ["E0"])]}, "rethink"), "at least one result that came in after Y1 was last settled"),
         "a rethink of a why that is not in the ledger": (ref1({"rethink": [again("verify", y="Y7")]}, "rethink"), "names an earlier why of the ledger"),
         "a hypothesis from a why the rethink found refuted": (ref1({"rethink": [again("refuted")], "hypotheses": [Hn]}, "hypothesis"), "Y1 was refuted"),
         "a hypothesis from a why that was found supported (it is settled: to go on with it, it is rethought to verify)": (ref1({"rethink": [again("supported")], "hypotheses": [Hn]}, "hypothesis") if not ref1({"rethink": [again("supported")]}, "rethink") else "the rethink itself was refused", "Y1 was supported"),
         "a hypothesis from a why that a better guess replaced": (ref1({"whys": [{**W(["E1"], "verify"), "revises": "Y1"}], "hypotheses": [Hn]}, "hypothesis"), "Y1 was revised as Y3"),
         "a why that revises one that is not there": (ref1({"whys": [{**W(["E1"], "verify"), "revises": "Y9"}]}, "why"), "revises is null, or the id of an earlier why"),
         "accepted: a hypothesis from the first why after it was looked at again and still holds": (ref1({"rethink": [again("verify")], "hypotheses": [Hn]}, "hypothesis") + ref1({"rethink": [again("verify")], "hypotheses": [Hn]}, "rethink"), None),
         "accepted: a why that was set aside is taken up": (ref1({"rethink": [again("verify", y="Y2"), again("supported")], "hypotheses": [{**Hn, "from_why": "Y2"}]}, "hypothesis"), None),
         "accepted: a hypothesis from the why that replaced the first": (ref1({"whys": [{**W(["E1"], "verify"), "revises": "Y1"}], "hypotheses": [{**Hn, "from_why": "Y3"}]}, "hypothesis"), None)}
say(all((w in got) if w else not got for got, w in cases.values()), "an earlier why must be looked at again before more is built on it: refused: " + ", ".join(k for k, (g_, w) in cases.items() if w) + "; "
    + ", ".join(k for k, (g_, w) in cases.items() if not w) + "".join(f" [{k}: {got[:140]}]" for k, (got, w) in cases.items() if (w not in got if w else got)))
# ---- two links that were hollow in the first real session (s041): a "test" on results already measured, and guesses marked to verify that nobody took up
ledger2 = [x for x in led if x["turn"] <= 2]; V2 = [{"for": "H2", "result": "supported", "because": "C2 held.", "next": "report"}]
known = ref1({"rethink": [again("verify")], "experiment": EXP}, "decision rule")   # H1 is still open in ledger1; EXP's two designs are the two simulations already run for it
hang = next((w for p, w in loop.sort_out(turn(verdicts=V2, report=REP, done=True), brief, ledger2, 36)[1] if p == "report"), "")
settled = loop.sort_out(turn(verdicts=V2, report=REP, done=True, rethink=[{"id": "Y2", "in_light_of": ["E2"], "now": "set_aside", "because": "the seed plays no part"}, {"id": "Y3", "in_light_of": ["C2"], "now": "supported", "because": "C2 held"}]), brief, ledger2, 36)
say("names only results that are already in the ledger (w50 = S1, w80 = S2), so it cannot fail and is no test" in known and hang.startswith(loop.WAIT) and "Y2" in hang and "not left hanging" in hang and settled[0]["report"] and not [w for p, w in settled[1] if p == "report"],
    f"a decision rule that names only results already measured is refused as no test (“{known[:90]}…”); the report waits once for a guess that was marked to verify and never taken up (“{hang[36:150]}…”), and is accepted once a rethink says what became of it")
# ---- the judge: a second reading of each new hypothesis against the guess it names
js = of("judge"); jn = [n["body"] for n in of("note") if "does not follow from Y3" in (n["body"].get("reason") or "")]
unrel = loop.sort_out(turn(whys=[W(["E0"], "verify")], hypotheses=[H]), brief, ledger, 40, judge=lambda w, h: (False, "it is about another setting"))
broken = loop.sort_out(turn(whys=[W(["E0"], "verify")], hypotheses=[H]), brief, ledger, 40, judge=lambda w, h: 1 / 0)
say(sorted(j["body"]["follows"] for j in js) == [False, True, True] and all(j["by"] == "harness" for j in js) and len(jn) == 1 and "the script's judge" in jn[0]["reason"] and hs[0]["body"].get("judge", {}).get("follows") is True and len(hs) == 2
    and "[J" not in user3 and not unrel[0]["hypotheses"] and any("it does not follow from Y1" in w and "it is about another setting" in w for p, w in unrel[1])
    and len(broken[0]["hypotheses"]) == 1 and broken[0]["hypotheses"][0]["judge"]["follows"] is None,
    f"the judge reads each new hypothesis against its guess: the {len(js)} readings are recorded (by the harness, not shown to the model), a hypothesis that does not follow is refused with the judge's reason (“{(jn or [{'reason': ''}])[0]['reason'][:110]}…”), "
    "one that follows carries the reading, and when the judge cannot be asked the hypothesis is taken unjudged and says so")
# ---- the review of each step from one hypothesis to the next: the guesses that were just tested are looked at again before anything new
NEWW = {**W(["E1", "C1"], "verify", guess="another cause"), "revises": None}; Hf = {**Hn, "from_why": "Y3"}   # a new why about the new results, and a hypothesis from it (Y1's hypothesis H1 was checked: C1)
moved = loop.sort_out(turn(whys=[NEWW], hypotheses=[Hf], experiment=EXP2), brief, ledger1, 38)
looked = loop.sort_out(turn(rethink=[again("supported")], whys=[NEWW], hypotheses=[Hf]), brief, ledger1, 38)
byrun = loop.sort_out(turn(rethink=[again("supported")], whys=[NEWW], hypotheses=[{**Hf, "follows_from": ["series " + run0, "E1"]}]), brief, ledger1, 38)   # a hypothesis may say it follows from a run's series: that run's simulation
bad_id = ref1({"rethink": [again("supported", y="K1")]}, "rethink"); rep_due = next((w for p, w in loop.sort_out(turn(verdicts=[{"for": "H1", "result": "supported", "because": "C1 held.", "next": "report"}], report=REP, done=True), brief, ledger1, 38)[1] if p == "report"), "")
say(loop.tested_whys(ledger1) == {"Y1": ["H1: C1 held"]} and not moved[0]["hypotheses"] and moved[0]["experiment"] is None and all("first look again at the guesses that were just tested: Y1 (H1: C1 held)" in w for p, w in moved[1] if p in ("new hypothesis", "experiment")) and len([p for p, w in moved[1] if p in ("new hypothesis", "experiment")]) == 2
    and len(looked[0]["hypotheses"]) == 1 and not [w for p, w in looked[1] if p == "new hypothesis"] and len(byrun[0]["hypotheses"]) == 1 and byrun[0]["hypotheses"][0]["follows_from"] == ["S0", "E1"] and "the K numbers are those of rethinks" in bad_id and rep_due.startswith(loop.WAIT) and "were tested and no rethink says what the results did to them: Y1 (H1: C1 held)" in rep_due
    and "LOOK AGAIN FIRST:" in user2 and "Y1 (H1: C1 held)" in user2 and fmt["properties"]["rethink"]["items"]["properties"]["id"].get("pattern") == "^Y[0-9]+$" and hyp["properties"]["from_why"].get("pattern") == "^Y[0-9]+$",
    "the step from one hypothesis to the next is reviewed: after a test, no new hypothesis and no experiment is accepted until the guess that was tested has its rethink (“" + next((w for p, w in moved[1] if p == "new hypothesis"), "")[:96] + "…”), the turn's text says so first, the report waits for it too, "
    "and an id of a guess can only be written as Y and a number (a rethink that names K1 is refused with the reason)")
big = {**EXP, "control": "w0", "runs": [d(f"w{i}", 0.3 + i / 100) for i in range(12)], "needs": [{**NEED, "simulations": [f"w{i}" for i in range(12)]}], "decision_rules": [{**RULE, "decision_rule": "tcp_goodput_bps@w0 > tcp_goodput_bps@w11"}]}
why20 = [w for p, w in loop.sort_out(turn(whys=[W(["E0"], "verify")], hypotheses=[H], experiment=big), brief, ledger, 20)[1] if "experiment" in p]
why40 = [w for p, w in loop.sort_out(turn(whys=[W(["E0"], "verify")], hypotheses=[H], experiment=big), brief, ledger, 40)[1] if "experiment" in p]
say(why20 and "at most 10 (half of what is left)" in why20[0] and not why40 and loop.spend_cap(40, 12) == 12 and loop.spend_cap(7, 12) == 4 and loop.spend_cap(1, 12) == 1,
    f"an experiment of 12 simulations is accepted with 40 left and refused with 20 left (“{(why20 or [''])[0][:110]}…”); with 7 left at most 4, with 1 left 1")
print("RESULT:", f"FAIL {len(FAILED)}" if FAILED else "PASS"); [print("  FAILED", f) for f in FAILED]
