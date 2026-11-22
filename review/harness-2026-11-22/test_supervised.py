"""The arm "supervised" (2026-11-18, the operator's decision): two agents. The researcher proposes and does not rule on its own tests; a supervisor,
asked apart from it, checks each transition of the chain:
  gate 0  a new guess against the records it cites (not what they show; a repetition; a ruling ignored): refused once, then accepted as contested;
  gate 1  a test before any of its simulations is run: sent back once with the defect, nothing run or counted; sent again it runs, contested;
  gate 2  what the harness's checks mean: the ruling is the hypothesis's verdict; a ruling that does not fit the checks is recorded as inconclusive;
  an objection of the researcher to a ruling: the supervisor's second look stands.
  looking: up to six requests in a turn, and a measurement the researcher defines (measure) computed from a recorded series, at no cost.
And: the researcher's answer format has no verdicts and no rethink; its instructions say what the supervisor does; the supervisor is never shown the
researcher's observations or reasons; what it was shown and answered is kept beside the ledger; the other arms are as before.
One scripted session with a scripted supervisor.     python3 -I test_supervised.py SCRATCH_DIR [HARNESS_DIR]
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
SECRET = "RESEARCHERS-OWN-REASONING"   # stands in every text of the researcher that the supervisor must not be shown
# the short reply of the arm: observations, requests, whys (about, result, guess, revises), hypotheses (from_why, text), drop, experiment (kind, tests, question, runs, measurements, decision_rules: for, decision_rule), objections, report
def turn(**k): return {"observations": SECRET + " read", "requests": [], "whys": [], "hypotheses": [], "drop": [], "experiment": None, "objections": [], "report": None, **k}
def why(about, guess, **k): return {"about": about, "result": "TCP delivers about half of the link at the default part", "guess": guess, "revises": None, **k}
def hyp(y, text): return {"from_why": y, "text": text}
def test(h, rule, a, b, extra=()): return {"kind": "test", "tests": [h], "question": "", "runs": [d("a", a), d("b", b), *extra], "measurements": [], "decision_rules": [{"for": h, "decision_rule": rule}]}
REPORT = {"goal": "the largest UDP goodput", "recommendation": {"weightUdp": 0.7, "udpRate": "2Gbps", "queuePkts": 100, "tcpVariant": "TcpCubic", "duration": 2},
          "limit": "the part of the link: C2 shows it", "explanation": "a larger part gives UDP more", "claims": [{"text": "UDP gets more with a larger part", "evidence": ["C2", "V3"]}]}
G = lambda defect, **k: {"records_show": "E0: TCP 482 Mbps at the default part", "nearest_earlier": "none", "defect": defect, "because": "the supervisor's ground", **k}
R1 = lambda defect, out="failed": {"rival": "UDP offers more than the link in both simulations", "rival_outcome": out, "doubt_if": "UDP goodput equal in both", "defect": defect, "because": "the supervisor's reason"}
R2 = lambda result, fair=True, defect="none": {"shows": "what the two simulations give", "fair": fair, "defect": defect, "result": result, "because": "the supervisor's ruling", "retest": "" if fair else "compare parts below UDP's demand"}
SCRIPT = {"answers": [
  # 1: a guess, a hypothesis from it, its test: gate 0 accepts, gate 1 sends the test back
  turn(whys=[why(["E0"], "the scheduler gives each flow its part")], hypotheses=[hyp("Y1", "UDP goodput falls when its part falls")], experiment=test("H1", "udp_goodput_bps@a > udp_goodput_bps@b", 0.3, 0.7)),
  # 2: the same test again: the supervisor still objects, it runs as contested; the rule fails (UDP gets more at 0.7); the supervisor says "supported", which does not fit
  turn(experiment=test("H1", "udp_goodput_bps@a > udp_goodput_bps@b", 0.3, 0.7), requests=[{"tool": "measure", "args": {"run_id": "r001", "of": "cwnd", "stat": "max"}}]),
  # 3: an objection to the ruling; a guess that is not in the records (refused), and a hypothesis from it (falls with it); a verdict of the researcher's own (refused)
  turn(objections=[{"to": "V1", "because": "C1 failed, so the hypothesis is refuted, not inconclusive"}], whys=[why(["E1"], "the link carries more than 1 Gbps")], hypotheses=[hyp("Y2", "UDP goodput exceeds 1 Gbps")],
       verdicts=[{"for": "H1", "result": "supported", "because": "I say so", "next": "go on"}]),   # not a part of the short reply: sent anyway, it is refused
  # 4: a guess about the same records again: accepted as contested; its hypothesis and test: approved, run, ruled supported
  turn(whys=[why(["E1"], "UDP gets more when its part is larger")], hypotheses=[hyp("Y2", "UDP goodput rises with its part")], experiment=test("H2", "udp_goodput_bps@b > udp_goodput_bps@a", 0.4, 0.8, extra=[d("idle", 0.6)])),   # two parts not simulated yet: a rule over known results is refused by the harness itself
  # 5: a turn that only looks: seven requests, among them a measurement of its own over the series of a simulation it has
  turn(requests=[{"tool": "measure", "args": {"run_id": "r001", "of": "udp_bps + tcp_bps", "stat": "mean"}}, {"tool": "measure", "args": {"run_id": "r001", "of": "q_band0", "stat": "time_above", "level": 50, "t_from": 2, "t_to": 4}},
                 {"tool": "measure", "args": {"run_id": "r001", "of": "open('/etc/passwd')", "stat": "mean"}}] + [{"tool": "metrics", "args": {"run_id": "r001"}}] * 4),
  # 6: a test whose two simulations differ in two settings: refused with the reason, before the supervisor is asked
  turn(hypotheses=[hyp("Y2", "UDP goodput also rises with a longer queue")], experiment={"kind": "test", "tests": ["H3"], "question": "", "runs": [d("p", 0.45), d("q", 0.85, queuePkts=500)], "measurements": [], "decision_rules": [{"for": "H3", "decision_rule": "udp_goodput_bps@q > udp_goodput_bps@p"}]}),
  # 7: the report: nothing is owed for the hypotheses (H3 stays open and untested)
  turn(report=REPORT)],
 "supervisor": [G("none"), R1("rival_passes_too", "held"),          # turn 1: the guess is sound; the test is sent back
                R1("none", "held"), R2("supported"),                # turn 2: no defect named, but its own rival would pass: contested; "supported" on a failed check
                G("not_in_the_records"), {"answer": "the objection is right: C1 failed in a test that could have held", "stands": False, "result": "refuted", "because": "C1 failed"},  # turn 3 (the guess is read first, in sort_out)
                G("repeats", nearest_earlier="Y1"), R1("rival_passes_too", "failed"), R2("supported")]}   # turn 4: it names "a rival passes too" although its own rival would fail the rule: no defect stands
print("THE ARM “SUPERVISED”")
led, meta = session("v1", "two-hosts-open-2", SCRIPT, "--arm", "supervised")
fmt = json.loads((P / "sessions/v1/format_sent.json").read_text()); sent = json.loads((P / "sessions/v1/supervisor_sent.json").read_text()); log = [json.loads(l) for l in (P / "sessions/v1/supervisor.jsonl").read_text().splitlines()]
EX = fmt["properties"]["experiment"]["anyOf"][0]; RP = fmt["properties"]["report"]["anyOf"][0]
say(list(fmt["properties"]) == ["observations", "requests", "whys", "hypotheses", "drop", "experiment", "objections", "report"] and list(fmt["properties"]["whys"]["items"]["properties"]) == ["about", "result", "guess", "revises"]
    and list(fmt["properties"]["hypotheses"]["items"]["properties"]) == ["from_why", "text"] and list(EX["properties"]) == ["kind", "tests", "question", "runs", "measurements", "decision_rules"] and list(EX["properties"]["decision_rules"]["items"]["properties"]) == ["for", "decision_rule"]
    and list(RP["properties"]) == ["goal", "recommendation", "limit", "explanation", "claims"] and set(EX["properties"]["runs"]["items"]["properties"]["params"]["required"]) == {"weightUdp", "udpRate", "queuePkts", "tcpVariant", "duration"}
    and meta["flags"].get("arm") == "supervised" and meta["flags"].get("judge") == "off" and "supervisor" in meta["flags"] and "A supervisor works apart from you" in meta["prompt"] and len(meta["prompt"]) < 8000
    and not any(w in meta["prompt"] for w in ("rethink", "the judge", "rival", "prediction", "follows_from", "holds_when", "budget_request")),
    f"the researcher's reply is short: eight parts ({', '.join(fmt['properties'])}); a guess is about, result, guess; a hypothesis is from_why and text; an experiment is its simulations, its own measurements and one rule for each test; the report is goal, recommendation, limit, explanation, claims. "
    f"Its instructions are {len(meta['prompt'])} characters and ask for nothing else; a design still states every knob")
rv = of(led, "review"); g0 = [r for r in rv if r["body"].get("gate") == "ground"]; g1 = [r for r in rv if r["body"].get("gate") != "ground"]
say([r["turn"] for r in g1] == [1, 2, 4] and [r["body"]["decision"] for r in g1] == ["sent_back", "contested", "approved"] and g1[0]["body"]["defect"] == "rival_passes_too" and g1[1]["body"]["defect"] == "rival_passes_too"
    and "no defect stands" in g1[2]["body"]["because"] and g1[2]["body"]["defect"] == "none" and not of(led, "experiment", 1) and not [r for r in of(led, "simulation", 1) if r["id"] != "S0"] and any("sent back" in (q[1] or "") for q in notes(led, 1)) and len(of(led, "experiment", 2)) == 1 and all(r["by"] == "supervisor" for r in rv),
    f"gate 1: the test of H1 is sent back before any simulation (turn 1: no experiment, no simulation, a note; defect {g1[0]['body']['defect']}); sent again it is run and its review says “contested” "
    f"(the supervisor named no defect, but under its own rival the rule would hold); the test of H2 is approved, because the defect the supervisor named is one its own rival does not support: {[(r['turn'], r['body']['decision']) for r in g1]}")
v = of(led, "verdict"); c1 = of(led, "check", 2)
say(len(v) == 3 and all(r["by"] == "supervisor" for r in v) and c1[0]["body"]["result"] == "failed" and v[0]["body"]["result"] == "inconclusive" and "does not fit the checks" in v[0]["body"].get("changed_by_harness", "") and v[0]["body"]["checks"] == [c1[0]["id"]]
    and v[0]["body"].get("doubt_if") == "UDP goodput equal in both",
    f"gate 2: the ruling is the hypothesis's verdict, by the supervisor; “supported” on a check that FAILED is recorded as inconclusive, and the record says the harness changed it; the ruling carries what the supervisor said beforehand would make it doubt the test")
ob = of(led, "objection")
say(len(ob) == 1 and ob[0]["by"] == "model" and v[1]["turn"] == 3 and v[1]["body"].get("after") == ob[0]["id"] and v[1]["body"]["stands"] is False and v[1]["body"]["result"] == "refuted"
    and ("verdict for H1", "in this session the verdicts are the supervisor's: it rules on each tested hypothesis after the checks. If you think a ruling is wrong, object to it (objections)") in notes(led, 3),
    "an objection to V1 is a record of the researcher's; the supervisor's second look is a new ruling (refuted: the check had failed), which stands; a verdict of the researcher's own is refused as a part, with the reason")
y = of(led, "why"); n3 = [q for q in notes(led, 3) if q[0] in ("new why", "new hypothesis")]
say([r["turn"] for r in y] == [1, 4] and [r["body"]["decision"] for r in g0] == ["approved", "sent_back", "contested"] and g0[1]["body"]["for"] is None and g0[1]["body"]["guess"] == "the link carries more than 1 Gbps"
    and len(n3) == 2 and "the supervisor does not accept this guess" in n3[0][1] and y[1]["body"]["ground"]["defect"] == "repeats" and y[1]["body"]["ground"]["nearest_earlier"] == "Y1" and len(of(led, "hypothesis")) == 3,
    f"gate 0: a guess that is not what its records show is refused with the supervisor's reading (a review record of its own), and the hypothesis said to come from it falls with it; "
    f"a guess about the same records stated again is accepted although the supervisor still objects (“repeats”, nearest Y1), and its record says so: {[r['body']['decision'] for r in g0]}")
rq = of(led, "request", 5); rs = [json.loads(r["body"]["result"]) if r["body"]["result"].startswith("{") else r["body"]["result"] for r in of(led, "result", 5)]; before = len(of(led, "simulation"))
metric = json.loads((P / "sessions/v1/runs/r001/metrics.json").read_text()); schema_sent = fmt["properties"]["requests"]["items"]["properties"]["tool"]["enum"]
say(len(rq) == 6 and "measure" in schema_sent and isinstance(rs[0], dict) and rs[0]["stat"] == "mean" and abs(rs[0]["value"] / (metric["udp_goodput_bps"] + metric["tcp_goodput_bps"]) - 1) < 0.05 and "nothing was simulated again" in rs[0]["note"]
    and isinstance(rs[1], dict) and rs[1]["from_s"] == 2 and rs[1]["to_s"] == 4 and isinstance(rs[2], str) and rs[2].startswith("error: cannot read") and not of(led, "simulation", 5) and of(led, "turn", 6)[0]["body"]["simulations_left"] == of(led, "turn", 5)[0]["body"]["simulations_left"]
    and "look before you simulate" in meta["prompt"],
    f"a turn may only look: six of its seven requests are answered (the arm's limit), a measurement the researcher defines is computed from the recorded series (the mean of udp_bps + tcp_bps: {rs[0]['value'] / 1e6:.1f} Mbps, the goodputs give {(metric['udp_goodput_bps'] + metric['tcp_goodput_bps']) / 1e6:.1f}), "
    f"an expression that is no arithmetic over columns is refused (“{str(rs[2])[:60]}…”), no simulation is run for any of it and the budget is unchanged; the instructions say “look before you simulate”")
x2 = of(led, "experiment", 4)[0]; n4 = notes(led, 4); n6 = [q for q in notes(led, 6) if q[0] == "experiment"]
say([r["label"] for r in x2["body"]["runs"]] == ["a", "b"] and any(q[0] == "design idle" and "named by no decision rule" in q[1] for q in n4) and [{**n, "simulations": sorted(n["simulations"])} for n in x2["body"]["needs"]] == [{"for": "H2", "to_know": "", "varies": "weightUdp", "measure": "udp_goodput_bps", "simulations": ["a", "b"], "derived": True}]
    and x2["body"]["varied"] == ["weightUdp"] and len(n6) == 1 and "differ in more than one setting (queuePkts, weightUdp)" in n6[0][1] and not of(led, "experiment", 6) and not [r for r in of(led, "review", 6) if r["body"].get("gate") != "ground"],
    f"what the researcher no longer states, the harness derives: for H2 the simulations its rule compares, the one setting they differ in and the measure ({x2['body']['needs'][0]['varies']}, {x2['body']['needs'][0]['measure']}); a design no rule names is left out with a note; "
    f"a test whose two simulations differ in two settings is refused before the supervisor is asked: “{n6[0][1][:110] if n6 else None}…”")
rep = of(led, "report")
say(len(rep) == 1 and meta.get("how") == "done by the model" and not [q for q in notes(led, 7) if q[0] == "report"] and rep[0]["body"]["claims"][0].get("role") == "supports", f"the report is accepted without a verdict or a rethink being owed by the researcher ({meta.get('how')})")
seen = "\n".join(sent)
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import importlib; loop = importlib.import_module("loop"); loop_schemas = {"review": loop.REVIEW_SCHEMA["properties"], "ruling": loop.RULING_SCHEMA["properties"]}
say(len(sent) == 9 == len(log) and SECRET not in seen.replace("C1 failed, so the hypothesis is refuted, not inconclusive", "") and "THE GUESS of why it came out so: the scheduler gives each flow its part" in seen and "udp_goodput_bps@a > udp_goodput_bps@b" in seen
    and "reading measure(" in sent[7] and '"of": "cwnd"' in sent[7] and "EVERY READING OF THE SESSION" in sent[0] and list(loop_schemas["review"])[-2:] == ["because", "defect"] and list(loop_schemas["ruling"])[:2] == ["shows", "because"]
    and [q["gate"] for q in log] == ["ground", "design", "design", "ruling", "ground", "objection", "ground", "design", "ruling"] and all(q["shown"] and q["answer"] for q in log) and {q["id"] for q in log} <= {r["id"] for r in led},
    f"the supervisor was asked {len(sent)} times, each in a request of its own; it was shown the guess, the hypothesis, the rules and the numbers, and nowhere the researcher's observations, its reasons for a guess or its question "
    f"(a marker put into each of them is in none of the requests); it is shown what the tools returned when the researcher looked at a simulation (a measurement of its own stands in the review that came after it); in its answer the ground is written before the decision; supervisor.jsonl holds what it was shown and answered for each of its records: {[q['gate'] for q in log]}")
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import importlib; loop = importlib.import_module("loop")
text = loop.render(led) if not setattr(loop, "LEDGER", P / "sessions/v1/ledger.jsonl") else ""
say("SENT BACK, the test was not run" in text and "by the supervisor on H1: inconclusive" in text and "by the supervisor of a guess it did not accept" in text and "after your objection" in text and "run, but the supervisor still objects" in text,
    "the ledger text the researcher reads holds each review and ruling in words: sent back, contested, a guess that was not accepted, a ruling after its objection")
# the other arms are as before
ANS2 = [{"observations": "read", "rethink": [], "whys": [{"about": ["E0"], "result": "TCP delivers about half of the link", "guess": "the scheduler gives each flow its part", "unseen": "how it divides the link", "matters": "it decides the answer", "worth": "verify", "reason": "it serves the goal", "revises": None}],
         "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part", "question": "Does it?", "why": "It decides the answer.", "prediction": "yes", "follows_from": []}], "drop": [],
         "experiment": {"kind": "test", "tests": ["H1"], "question": "", "varied": ["weightUdp"], "control": None, "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [],
                        "needs": [{"for": "H1", "to_know": "whether the part changes it", "varies": "weightUdp", "measure": "udp_goodput_bps", "simulations": ["a", "b"]}],
                        "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "the part does nothing", "rival_predicts": "failed"}]},
         "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False}]
led2, meta2 = session("v2", "two-hosts-open-2", ANS2)
say(len(of(led2, "check")) == 1 and not of(led2, "review") and not of(led2, "verdict") and "arm" not in meta2["flags"] and not (P / "sessions/v2/supervisor.jsonl").exists() and "rethink" in meta2["prompt"] and len(meta2["prompt"]) > 15000 and "rival" in json.dumps(json.loads((P / "sessions/v2/format_sent.json").read_text())),
    "a session of the ordinary arm asks no supervisor and keeps the full reply: its test runs at once, no review and no ruling is recorded, and its instructions are prompt.txt as it stands")
# one test sent back does not stop the tests the supervisor let through (2026-11-18, after s047: an approved test waited two turns behind sent-back ones)
ANS3 = {"answers": [turn(whys=[why(["E0"], "the scheduler gives each flow its part")], hypotheses=[hyp("Y1", "UDP goodput rises with its part"), hyp("Y1", "TCP goodput falls when the part of UDP rises")],
                         experiment={"kind": "test", "tests": ["H1", "H2"], "question": "", "runs": [d("a", 0.3), d("b", 0.6), d("c", 0.8)], "measurements": [],
                                     "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@c > udp_goodput_bps@a"}, {"for": "H2", "decision_rule": "tcp_goodput_bps@a > tcp_goodput_bps@b"}]})],
        "supervisor": [{"records_show": "E0: TCP 482 Mbps at the default part", "nearest_earlier": "none", "defect": "none", "because": "it starts from E0"},
                       {"rival": "UDP offers more than the link in both simulations", "rival_outcome": "held", "doubt_if": "UDP is below its part in both", "defect": "rival_passes_too", "because": "the rival gives the same outcome"},
                       {"rival": "TCP is limited by its window", "rival_outcome": "failed", "doubt_if": "TCP is window-limited in both", "defect": "none", "because": "the rival would fail the rule"}]}
led3, meta3 = session("v3", "two-hosts-open-2", ANS3, "--arm", "supervised")
g3, x3, n3 = [r for r in of(led3, "review") if r["body"].get("gate") != "ground"], [r for r in of(led3, "experiment") if r["by"] == "model"], [r["body"] for r in of(led3, "note", 1) if "part" in r["body"]]
say([(r["body"]["for"], r["body"]["decision"]) for r in g3] == [("H1", "sent_back"), ("H2", "approved")] and len(x3) == 1 and x3[0]["body"]["tests"] == ["H2"] and [r["label"] for r in x3[0]["body"]["runs"]] == ["a", "b"]
    and [d_["for"] for d_ in x3[0]["body"]["decision_rules"]] == ["H2"] and len(of(led3, "simulation", 1)) == 2 and [c["body"]["for"] for c in of(led3, "check")] == ["H2"]
    and [(v_["body"]["for"], v_["by"]) for v_ in of(led3, "verdict")] == [("H2", "supervisor")] and len(n3) == 1 and n3[0]["part"] == "tests H1" and "a part of the experiment was not run" in n3[0]["text"] and "run now: H2" in n3[0]["text"],
    f"one of two tests sent back: the approved one is run now (2 of the 3 simulations, its check, its ruling), the other waits and the note says so: {[(r['body']['for'], r['body']['decision']) for r in g3]}, tests run {x3 and x3[0]['body']['tests']}, {len(of(led3, 'simulation', 1))} simulations, note part {n3 and n3[0]['part']!r}")
sup_text = json.loads((P / "sessions/v3/session.json").read_text())
import importlib.util
spec = importlib.util.spec_from_file_location("loop_read", P / "harness/loop.py"); src = (P / "harness/loop.py").read_text()
say("A test need not run a new simulation" in src and "the very value the rule compares already stands" in src and "A value you can simply read is an observation, not a hypothesis" in meta3["prompt"] and "the other tests of the same experiment are run" in meta3["prompt"],
    "the supervisor is told that a new measurement of a simulation that already ran is a proper test, and the researcher that a plain reading is not a hypothesis")
# the chain (2026-11-18, after s047: eight hypotheses in four turns, none tested, each guess from the baseline again). Test first; a later guess names
# what was learned since the earlier guesses; the supervisor reads whether it really comes from that
GOK = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "it starts from them"}
ANS4 = {"answers": [turn(whys=[why(["E0"], "the scheduler gives each flow its part")], hypotheses=[hyp("Y1", "UDP goodput rises with its part")]),
                    turn(whys=[why(["E0"], "TCP is limited by its window")], hypotheses=[hyp("Y1", "TCP goodput falls when the part of UDP rises")],
                         requests=[{"tool": "measure", "args": {"run_id": "r001", "of": "cwnd", "stat": "max", "t_from": None, "t_to": None, "level": None}}]),
                    turn(whys=[{"about": ["T1"], "result": "the window of TCP reaches its largest value in r001", "guess": "TCP is limited by its window, not by its part", "revises": None}], drop=[{"id": "H1", "why": "the reading T1 points at the window: that is tested first"}],
                         hypotheses=[hyp("Y2", "UDP goodput rises with its part while TCP stays window-limited")], experiment=test("H2", "udp_goodput_bps@b > udp_goodput_bps@a", 0.3, 0.6)),
                    turn(whys=[{"about": ["E1"], "result": "UDP got more with the larger part in E1", "guess": "the queue length decides the loss of UDP", "revises": None}], requests=[{"tool": "metrics", "args": {"run_id": "r001"}}]),
                    turn(whys=[why(["E0"], "the link is too slow")]), turn(requests=[{"tool": "metrics", "args": {"run_id": "r001"}}])],
        "supervisor": [GOK, GOK, {"rival": "UDP offers more than the link in both", "rival_outcome": "failed", "doubt_if": "UDP is below its part in both", "defect": "none", "because": "the rival would fail the rule"},
                       {"shows": "the check held", "fair": True, "defect": "none", "result": "supported", "because": "C1 held in a fair test", "retest": ""},
                       {"records_show": "E1: UDP delivered more with the larger part", "nearest_earlier": "Y2", "defect": "not_from_what_was_learned", "because": "E1 says nothing of the queue: the guess would be the same without it"}]}
led4, meta4 = session("v4", "two-hosts-open-2", ANS4, "--arm", "supervised")
n2, y4, h4 = notes(led4, 2), of(led4, "why"), of(led4, "hypothesis")
say(len(of(led4, "why", 2)) == 0 and len(of(led4, "hypothesis", 2)) == 0 and any(q[0] == "new why" and "starts only from records your earlier guesses already had" in q[1] and "nothing has been learned since" in q[1] for q in n2)
    and any(q[0] == "new hypothesis" and "H1 is still open and untested" in q[1] for q in n2),
    f"turn 2: a second guess from the baseline alone is refused (nothing was learned since the first), and so is a second hypothesis while H1 is untested: {[q[0] for q in n2]}")
u4 = json.loads((P / "sessions/v4/users_sent.json").read_text()); s4 = json.loads((P / "sessions/v4/supervisor_sent.json").read_text())
say([r["turn"] for r in y4] == [1, 3] and y4[1]["body"]["about"] == ["T1"] and [r["turn"] for r in h4] == [1, 3] and len(of(led4, "simulation", 3)) == 2 and [(v_["body"]["for"], v_["body"]["result"]) for v_ in of(led4, "verdict")] == [("H2", "supported")]
    and "[T1] turn 2 reading measure(" in u4[2] and "<- NEW since the researcher's earlier guesses" in s4[1] and "would the researcher have made this same guess without them" in s4[1] and "NEW since" not in s4[0],
    "turn 3: a guess that names the reading T1 (made since the first guess) is accepted, H1 is given up, the new hypothesis is tested at once; the researcher sees the reading with its id, and the supervisor is shown which record is new and asked whether the guess comes from it")
n5 = notes(led4, 4)
say(len(of(led4, "why", 4)) == 0 and any(q[0] == "new why" and "does not come from the newer records it cites" in q[1] for q in n5),
    f"turn 4: a guess that names a new record for form only (the supervisor: it would be the same without it) is refused: {[q[1][:90] for q in n5]}")
u4 = json.loads((P / "sessions/v4/users_sent.json").read_text())
say(len(u4) == 7 and "YOUR ANSWER TO THIS TURN COULD NOT BE USED" not in u4[4] and "YOUR ANSWER TO THIS TURN COULD NOT BE USED, AND YOU ARE ASKED ONCE MORE" in u4[5] and "starts only from records your earlier guesses already had" in u4[5] and u4[5].startswith(u4[4]),
    "turn 5: an answer of which nothing can be used is asked again in the same turn, and the second request says what was refused and why")
# every reading and every observation stays (2026-11-22, the operator: "keep every lookup result in the notebook, so both agents see the same thing";
# "I want the researcher to see all lookup results and its own observations previously accumulated all the time"): the researcher's last request still
# holds the reading of turn 2 and its observations of the earlier turns; the supervisor is given the same reading in the same form, and no observation
s4 = json.loads((P / "sessions/v4/supervisor_sent.json").read_text()); led4 = [json.loads(l) for l in (P / "sessions/v4/ledger.jsonl").read_text().splitlines() if l.strip()]
t1 = next((r for r in led4 if r["id"] == "T1"), None); line1 = f"[T1] turn {t1['turn']} reading measure(" if t1 else "?"
obs_turns = sorted({r["turn"] for r in led4 if r.get("by") == "model" and (r.get("body") or {}).get("observations")})
say(t1 is not None and line1 in u4[-1] and all(f"turn {k} your observations: {SECRET} read" in u4[-1] for k in obs_turns if k < max(obs_turns)) and len(obs_turns) >= 2
    and any(line1 in s for s in s4) and not any(SECRET in s for s in s4),
    f"the researcher's last request still holds the reading T1 (turn {t1['turn'] if t1 else None}) and its observations of turns {obs_turns[:-1]}; the supervisor is given T1 in the same form, and none of the observations")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
