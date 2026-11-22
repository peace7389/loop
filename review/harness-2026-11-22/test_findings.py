"""Findings (2026-11-22, the operator, after a review of s047 to s049: the researcher noticed things it could not explain and then left them; "it is
parked and forgotten"). A finding (F) is one thing the results do not explain; the researcher raises them in every arm, the supervisor of the arm
"supervised" too (after the baseline, after an explore experiment, when it rules on a test); every turn lists them at the top; the researcher
decides on each (A records: work, park, close, same_as); a report is held back while a finding was never looked at and the researcher can still
work; the report names every finding not closed; at the end the harness records what looked at each one. Nothing about findings refuses another part.
  - the format and the instructions of each arm (findings after observations, decisions before the report; observations no longer ask for the
    most important unexplained thing; the arm "plain" names no hypothesis, check or verdict; the supervised one stays under 8,000 characters);
  - the rules, in-process on a ledger of its own: refs left out with a note and the decision kept; a decision that cannot be used left out with a
    note; a missing decision noted; due again after PARK_TURNS; a why about a finding works on it; the report's open questions completed;
    the supervisor's findings kept only with ids that exist and a measured number;
  - a scripted session in the ordinary arm (short answers): the list at the top of each turn; a park, a why about a finding, a missing decision; the
    report held back for findings never looked at while the verdict of that answer is accepted; then closed and worked on, the report accepted with
    the finding still open added to its open questions; the tally at the end;
  - a scripted session in the arm "supervised": the supervisor's finding about the baseline (kept, by the supervisor), one in its ruling kept and one
    without a number left out; the researcher's decision on the supervisor's finding; the supervisor shown the findings, never the observations;
  - old sessions: the ledger text the researcher reads is the same as before findings (s046 to s049, the loop of HARNESS_BEFORE).
python3 -I test_findings.py SCRATCH_DIR [HARNESS_DIR] [--before HARNESS_BEFORE]
SCRATCH_DIR is made new. Simulations are real ns-3 runs of 2 measured seconds."""
import importlib.util, json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
BEFORE = next((Path(sys.argv[i + 1]).resolve() for i, a in enumerate(sys.argv) if a == "--before" and i + 1 < len(sys.argv)), None)
args = [a for a in args if BEFORE is None or Path(a).resolve() != BEFORE]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
ENV = {**os.environ, "HOME": str(SCR / "home")}
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import loop
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])

print("THE FORMAT AND THE INSTRUCTIONS")
brief2 = loop.tools.load_brief("two-hosts-open-2")
whole = lambda: loop.answer_format(json.loads((P / "harness/schema.json").read_text()), brief2)
fmts = {"hypotheses": loop.with_findings(loop.short_format(whole())), "plain": loop.with_findings(loop.plain_format(whole())), "supervised": loop.with_findings(loop.supervised_format(whole()))}
order = {a: list(f["properties"]) for a, f in fmts.items()}
say(all(o[o.index("observations") + 1] == "findings" and o[o.index("report") - 1] == "decisions" and set(o) == set(fmts[a]["required"]) for a, o in order.items())
    and set(fmts["plain"]["properties"]["decisions"]["items"]["properties"]) == {"id", "action", "refs", "reason"} and set(fmts["plain"]["properties"]["findings"]["items"]["properties"]) == {"about", "text", "name"},
    f"every arm's format: findings right after observations, decisions right before the report; a finding has about, text and name (its name since 2026-11-22: the page shows it on the finding's bar), a decision id, action, refs, reason ({order['plain']})")
full = (P / "harness/prompt.txt").read_text(); FT = loop.FINDINGS_TEXT
say("Name the most important unexplained thing" not in full and "is a finding" in full and "an unexplained result goes in findings" in loop.LEAN_PROMPT and len(loop.LEAN_PROMPT + FT["supervised"]) < 10_000
    and not any(w in FT["plain"] for w in ("hypothesis", "decision rule", "verdict", "check")) and not any(w in FT["supervised"] for w in ("rethink", "the judge", "rival", "prediction", "follows_from", "holds_when", "budget_request"))
    and "does not change the recommendation" in FT["hypotheses"] and "part of the goal" in FT["plain"] and "supervisor raises findings too" in FT["supervised"],
    f"observations no longer ask for the most important unexplained thing: it is a finding; the findings text of each arm fits it (plain: no hypothesis or check; supervised: no rethink or rival; "
    f"the supervised arm's whole instructions {len(loop.LEAN_PROMPT + FT['supervised'])} characters, one limit of 10,000); parking because it does not change the recommendation is named as no reason")

print("THE RULES (in-process)")
loop.LEDGER = SCR / "rules.jsonl"; L = []
A = lambda turn, ty, body, parent=None, by=None: loop.append(L, turn, ty, parent, body, by=by)
A(0, "experiment", {"kind": "explore", "tests": [], "runs": []}, by="harness"); L[-1]["id"] = "X0"
A(0, "simulation", {"run_id": "r001", "label": "default"}); L[-1]["id"] = "S0"
A(0, "evidence", {"experiment": "X0", "lines": ["default r001 | udp_goodput_bps=485000000"]}); L[-1]["id"] = "E0"
A(1, "turn", {})
f1, f2, f3 = A(1, "finding", {"about": ["E0"], "text": "UDP gets 485 Mbps of the 1000 Mbps link"}), A(1, "finding", {"about": ["E0"], "text": "TCP gets 0 bps"}), A(1, "finding", {"about": ["E0"], "text": "the queue holds 100 packets at 2 s"})
A(2, "turn", {}); q = A(2, "request", {"tool": "metrics", "args": {"run_id": "r001"}}); t1 = A(2, "result", {"tool": "metrics", "result": "{}"}, q)
due2 = [f["id"] for f in loop.finding_states(L).values() if loop.finding_due(f, L, 2)]
loop.settle_findings({"findings": [{"about": ["E0", "r001"], "text": "a fourth thing, 7 drops"}, {"about": ["E9"], "text": "cites nothing there"}],
                      "decisions": [{"id": f1, "action": "work", "refs": ["Y9", t1], "reason": ""}, {"id": f2, "action": "park", "refs": [], "reason": ""}, {"id": "F9", "action": "close", "refs": ["E0"], "reason": ""},
                                    {"id": f3, "action": "close", "refs": [], "reason": ""}]}, L, 2, due2, [t1], [])
fs = loop.finding_states(L); notes = [r["body"].get("text", "") for r in L if r["type"] == "note" and r["turn"] == 2]
say(due2 == [f1, f2, f3] and fs[f1]["status"] == "working" and fs[f1]["refs"] == [t1] and any("left out of its refs" in n and "Y9" in n for n in notes) and fs["F4"]["about"] == ["E0", "S0"]
    and "F5" not in fs and any("not such a record: E9" in n for n in notes) and fs[f2]["status"] == "open" and any("park needs a reason" in n for n in notes) and any("'F9' is not one" in n for n in notes)
    and fs[f3]["status"] == "open" and any("close needs refs" in n for n in notes) and any(f"no decision for {f2}" in n for n in notes) and any(f"no decision for {f3}" in n for n in notes),
    f"turn 2: all three due; F1 works on the reading (Y9, not in the ledger, left out with a note); a new finding citing a run is kept (about {fs['F4']['about']}), one citing E9 left out; "
    f"a park without a reason, a decision for F9 and a close without refs each left out with a note; F2 and F3 noted as without a decision ({len(notes)} notes)")
A(3, "turn", {}); loop.settle_findings({"decisions": [{"id": f2, "action": "park", "refs": [], "reason": "the queue first"}]}, L, 3, [f2, f3], [], [])
fs = loop.finding_states(L)
say([loop.finding_due(fs[f2], L, k) for k in (4, 5)] == [False, True] and [loop.finding_due(fs[f1], L, k) for k in (3, 4)] == [False, True] and loop.finding_looked(fs[f1], L) == [t1] and loop.findings_unseen(L) == [f2, f3, "F4"],
    f"a finding parked in turn 3 is due again in turn {3 + loop.PARK_TURNS}, not before; one worked on by a reading of turn 2 is due again in turn {2 + loop.PARK_TURNS}; never looked at: {loop.findings_unseen(L)}")
t = loop.findings_in_whys({"whys": [{"about": [f2, "E0"], "guess": "g"}]}, L)
y = A(4, "why", {"about": t["whys"][0]["about"], "worth": "verify"}); loop.settle_findings({"decisions": []}, L, 4, [], [], [(y, t["whys"][0]["_findings"])])
fs = loop.finding_states(L); auto = [r for r in L if r["type"] == "decision" and r["body"].get("auto")]
say(t["whys"][0]["about"] == ["E0"] and fs[f2]["status"] == "working" and fs[f2]["refs"] == [y] and auto, f"a why whose about names {f2} is about what {f2} rests on ({t['whys'][0]['about']}) and works on it: {auto[0]['body'] if auto else None}")
rep, added = loop.findings_in_report({"open_questions": [f"{f1}: still open"]}, L)
say(added == [f2, f3, "F4"] and len(rep["open_questions"]) == 4 and "added by the harness" in rep["open_questions"][-1], f"a report naming only {f1} gets {added} added to its open questions, marked so")
kept = loop.take_sup_findings(L, 4, [{"about": ["E0"], "text": "UDP stays at 485 Mbps"}, {"about": ["E0"], "text": "UDP stays low"}], "E0") + loop.take_sup_findings(L, 4, [{"about": ["X7"], "text": "3 drops"}], "E0")
fs = loop.finding_states(L); sn = [r["body"]["text"] for r in L if r["type"] == "note" and r["turn"] == 4]
say(len(kept) == 1 and fs[kept[0]]["by"] == "supervisor" and any("no measured number" in n for n in sn) and any("not in the ledger (X7)" in n for n in sn),
    f"the supervisor's findings: one with a record and a number kept ({kept}, by {fs[kept[0]]['by'] if kept else None}); one without a number and one citing X7 left out with a note")
blk = loop.findings_block(L, 5, None)
say(blk.startswith("FINDINGS (") and f"[{kept[0]}] raised by the supervisor" in blk and f"[{f2}] raised by you in turn 1; working on it since turn 4" in blk and "DUE" in blk and "Never looked at yet" in blk,
    "the list at the top of a turn says who raised each finding, its status, which are due, and which were never looked at")

print("A SCRIPTED SESSION (the ordinary arm, short answers)")
def session(sid, brief, answers, *flags):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps(answers))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env=ENV, capture_output=True, text=True, timeout=1500)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    S = P / "sessions" / sid
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    sup = json.loads((S / "supervisor_sent.json").read_text()) if (S / "supervisor_sent.json").is_file() else []
    return led, json.loads((S / "session.json").read_text()), json.loads((S / "users_sent.json").read_text()), sup
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
nt = lambda led, turn: [r["body"].get("text", "") for r in of(led, "note", turn)]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
# the answers state every field of the full format too (worth, reason, prediction, varied, budget_request): the same script runs where the short format is off (the deployed harness, 2026-11-22)
def turn(**k): return {"observations": "read", "findings": [], "rethink": [], "whys": [], "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "decisions": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
REP = {"goal": "the larger UDP goodput", "recommendation": {"weightUdp": 0.7, **{k: v for k, v in KN.items() if k != "seed"}}, "expected": {"udp_goodput_bps": 685000000.0}, "no_difference": [],
       "limit": "UDP's part of the link: E1.", "explanation": "UDP's goodput follows its part of the link.", "holds_when": "as tested", "breaks_when": "other rates",
       "claims": [{"text": "A larger part gives UDP more.", "role": "supports", "evidence": ["E1"]}], "open_questions": []}
F = lambda text: {"about": ["E0"], "text": text}
ANS = [turn(findings=[F("UDP gets about half of the 1 Gbps link at the part 0.5"), F("TCP's goodput is far below the half it is given"), F("the queue is full 2 s in")], requests=[{"tool": "metrics", "args": {"run_id": "r001"}}]),
       turn(decisions=[{"id": "F2", "action": "park", "refs": [], "reason": "the part first"}],
            whys=[{"about": ["F1"], "result": "UDP gets about half", "guess": "the scheduler gives each flow its part", "unseen": "how it divides the link", "matters": "it decides the answer", "worth": "verify", "reason": "it serves the goal"}],
            hypotheses=[{"from_why": "Y1", "text": "UDP goodput rises with its part", "question": "Does UDP get more when its part is larger?", "why": "It decides the answer.", "prediction": "more", "follows_from": []}],
            experiment={"kind": "test", "tests": ["H1"], "question": "Does the part change what UDP gets?", "measurements": [], "runs": [d("a", 0.3), d("b", 0.7)], "varied": ["weightUdp"], "control": None,
                        "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "UDP's own rate limits it", "rival_predicts": "failed"}]}),
       turn(rethink=[{"id": "Y1", "in_light_of": ["C1"], "now": "supported", "because": "C1 held"}], verdicts=[{"for": "H1", "result": "supported", "because": "C1 held", "next": "report"}],
            decisions=[{"id": "F7", "action": "work", "refs": [], "reason": ""}], report=REP, done=True),
       turn(decisions=[{"id": "F1", "action": "close", "refs": ["C1"], "reason": ""}, {"id": "F3", "action": "close", "refs": ["E0"], "reason": ""}, {"id": "F2", "action": "work", "refs": ["T2"], "reason": ""}],
            requests=[{"tool": "metrics", "args": {"run_id": "r002"}}], report=REP, done=True)]
led, meta, users, _ = session("h1", "two-hosts-open-2", ANS, "--budget", "4")
fd = [r for r in led if r["type"] == "finding"]; dec = lambda turn: [(r["body"]["for"], r["body"]["action"], r["body"]["refs"], bool(r["body"].get("auto"))) for r in of(led, "decision", turn)]
say(users[0].startswith("FINDINGS: none so far") and len(fd) == 3 and all(r["by"] == "model" and r["turn"] == 1 for r in fd) and users[1].startswith("FINDINGS (") and users[1].count("; DUE") == 3,
    "turn 1 is told there is no finding yet and raises three; turn 2's text starts with the list, all three due")
say(dec(2) == [("F2", "park", [], False), ("F1", "work", ["Y1"], True)] and any("no decision for F3" in n for n in nt(led, 2)) and of(led, "check", 2),
    f"turn 2: F2 parked, F1 worked on by the guess Y1 about it (written by the harness), F3 without a decision noted; the test ran ({dec(2)})")
v3 = of(led, "verdict", 3); n3 = nt(led, 3)
say(v3 and not of(led, "report", 3) and any("report is held back" in n and "F2" in n and "F3" in n and "F1" not in n.split("reaches them):")[1][:20] for n in n3) and any("'F7' is not one" in n for n in n3),
    "turn 3: the report is held back for F2 and F3, never looked at (F1 was: its guess's test was checked); the verdict of the same answer is accepted; a decision for F7 is left out with a note")
rep = (of(led, "report") or [{}])[0].get("body", {}); oq = rep.get("open_questions") or []
say(dec(4)[:2] == [("F1", "close", ["C1"], False), ("F3", "close", ["E0"], False)] and dec(4)[2][:3] == ("F2", "work", ["T2"])
    and meta.get("how") == "done by the model" and len(oq) == 1 and oq[0].startswith("F2:") and "added by the harness" in oq[0],
    f"turn 4: F1 and F3 closed, F2 worked on by this turn's reading, named by the id it gets ({dec(4)[2][2] if len(dec(4)) > 2 else None}); the report is accepted, F2 added to its open questions; {meta.get('how')}")
end = (of(led, "findings_end") or [{}])[-1].get("body", {}).get("findings") or []
say([(x["id"], x["status"], x["never_looked_at"]) for x in end] == [("F1", "closed", False), ("F2", "working", False), ("F3", "closed", False)] and end[0]["turns_open"] == 3,
    f"the tally at the end: {[(x['id'], x['status'], x['turns_open'], x['looked_at']) for x in end]}")

import session_figures
fc = session_figures.findings_counts([r for r in led if r["type"] != "draft"])
say(fc and fc["raised"] == {"researcher": 3, "supervisor": 0} and fc["ended"]["closed"] == 2 and fc["ended"]["working"] == 1 and fc["turns_open"] == {"mean": 3.0, "max": 3} and fc["never_looked_at"] == 0 and fc["final"],
    f"session_figures counts them for the session's row: {fc}")
print("A SCRIPTED SESSION (the arm \"supervised\")")
SUPF = {"findings": [{"about": ["E0"], "text": "TCP's goodput stays at 0 bps while UDP gets 485 Mbps"}]}
GROUND = {"records_show": "what the records show", "nearest_earlier": "none", "defect": "none", "because": "sound"}
REVIEW = {"rival": "UDP's own rate", "rival_outcome": "failed", "doubt_if": "nothing", "defect": "none", "because": "fair"}
RULING = {"shows": "UDP gets more at b", "because": "C1 held", "fair": True, "defect": "none", "result": "supported", "retest": "",
          "findings": [{"about": ["E1"], "text": "UDP gets 30 % more at b than its part would give"}, {"about": ["E1"], "text": "TCP stays low"}]}
LEAN = {"observations": "SUP-OBS read", "requests": [], "whys": [{"about": ["E0"], "result": "UDP gets about half", "guess": "the scheduler gives each flow its part", "revises": None}],
        "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part"}], "drop": [],
        "experiment": {"kind": "test", "tests": ["H1"], "question": "", "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [], "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "UDP's own rate limits it", "rival_predicts": "failed"}]},
        "objections": [], "report": None, "findings": [], "decisions": [{"id": "F1", "action": "work", "refs": [], "reason": ""}]}
led, meta, users, sup = session("s1", "two-hosts-open-2", {"answers": [LEAN], "supervisor": [SUPF, GROUND, REVIEW, RULING]}, "--arm", "supervised", "--budget", "4")
fd = {r["id"]: r for r in led if r["type"] == "finding"}
say(fd.get("F1", {}).get("by") == "supervisor" and fd["F1"]["turn"] == 0 and fd["F1"]["parent"] == "E0" and "[F1] raised by the supervisor in turn 0" in users[0] and "; DUE" in users[0],
    "the supervisor's look at the baseline raises F1 (by the supervisor, from E0); the researcher's first turn lists it as due")
say(fd.get("F2", {}).get("by") == "supervisor" and fd["F2"]["parent"] == "V1" and "F3" not in fd and any("no measured number" in r["body"].get("text", "") for r in of(led, "note", 1))
    and [(r["body"]["for"], r["body"]["action"]) for r in of(led, "decision", 1)] == [("F1", "work")] and of(led, "decision", 1)[0]["body"]["refs"] == [] and loop.finding_states(led)["F1"]["status"] == "working" and not loop.finding_looked(loop.finding_states(led)["F1"], led),
    f"its ruling raises F2 (from V1); its finding without a number is left out with a note; the researcher's “work” on F1 without refs counts as worked on, not as looked at ({of(led, 'decision', 1)[0]['body']['refs'] if of(led, 'decision', 1) else None})")
say(len(sup) >= 4 and "THE FINDINGS SO FAR" in sup[0] and "[F1]" in sup[-1] and not any("SUP-OBS" in x for x in sup),
    f"the supervisor is shown the findings so far ({len(sup)} requests), and never the researcher's observations")

print("OLD SESSIONS")
if BEFORE:
    spec = importlib.util.spec_from_file_location("loop_before", BEFORE / "loop.py"); old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    same = []
    for sid in ("s046", "s047", "s048", "s049"):
        lg = [json.loads(l) for l in (REAL / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
        same.append((sid, old.render(lg) == loop.render(lg), len(loop.render(lg))))
    say(all(x[1] for x in same), f"the ledger text the researcher reads is the same as before findings on {[(s, n) for s, ok, n in same if ok]} (characters)")
    say(all(session_figures.findings_counts([json.loads(l) for l in (REAL / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]) is None for sid in ("s046", "s047", "s048", "s049")),
        "a session without findings has none in its row: every other figure of its row is computed as before")
else:
    say(False, "--before HARNESS_BEFORE not given: the comparison with old sessions did not run")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
