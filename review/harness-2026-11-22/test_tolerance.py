"""The harness side of "tell a meaningful difference from a marginal one" and "ask why" (the operator's word of 2026-11-15):
two results that differ by less than the tolerance count as equal. The tolerance is the brief's (goal.tolerance) or the
harness's default of 1 %; every turn states it; a check whose rule was decided by less than it says so, in its record
(tolerance, within_tolerance) and in the line the model reads; a check's line also carries the rival explanation; the
prompt puts why before which. Two scripted sessions (tol1 on a brief without a tolerance, tol5 on one that states 5 %)
and the checks of the real session s031 worked out again.
    python3 -I test_tolerance.py SCRATCH_DIR [HARNESS_DIR]
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
    return led, json.loads((P / "sessions" / sid / "users_sent.json").read_text())
of = lambda led, ty: [r for r in led if r["type"] == ty]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w, **over): return {"label": label, "params": {"weightUdp": w, **KN, **over}}
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
H = lambda text, q: {"text": text, "question": q, "why": "It says whether the setting matters for the goal.", "prediction": "as stated", "follows_from": ["brief"]}
ANSWERS = [turn(hypotheses=[H("The seed changes TCP goodput", "Does the seed change what TCP delivers?"), H("UDP goodput rises with its part of the link", "Does UDP get more when its part is larger?")],
                experiment={"kind": "test", "tests": ["H1", "H2"], "question": "", "varied": ["weightUdp", "seed"], "control": "a", "runs": [d("a", 0.5), d("b", 0.5, seed=2), d("c", 0.7)],
                            "decision_rules": [{"for": "H1", "decision_rule": "tcp_goodput_bps@a > tcp_goodput_bps@b OR tcp_goodput_bps@b >= tcp_goodput_bps@a", "rival": "the seed changes nothing that matters", "rival_predicts": "failed"},
                                               {"for": "H2", "decision_rule": "udp_goodput_bps@c > udp_goodput_bps@a AND udp_loss_frac@c > 0.01", "rival": "the part of the link does nothing", "rival_predicts": "failed"}]})]
print("TOLERANCE: A MEANINGFUL DIFFERENCE AND A MARGINAL ONE")
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import importlib; tools = importlib.import_module("tools"); loop = importlib.import_module("loop"); dr = importlib.import_module("decision_rules")
# ---- the kinds of a comparison's sides
vals = {"a": {"tcp_goodput_bps": 100.0}, "b": {"tcp_goodput_bps": 99.5}}; M = tools.MANIFEST["outputs"]
cs = dr.comparisons("tcp_goodput_bps@a > tcp_goodput_bps@b AND tcp_goodput_bps@a > 100 AND (tcp_goodput_bps@a > 50 + 50 OR 2 * tcp_goodput_bps@b <= tcp_goodput_bps@a)", M, ["a", "b"], vals)
say([c[3] for c in cs] == [("measured", "measured"), ("measured", "number"), ("measured", "stated"), ("measured", "measured")] and [(c[0], c[2]) for c in cs] == [(100.0, 99.5), (100.0, 100), (100.0, 100), (199.0, 100.0)],
    f"a rule's comparisons come with the two numbers of their sides and what each side is (measured, one number, or worked out from stated numbers): {[c[3] for c in cs]}")
loop.TOLERANCE = 1.0; led0 = [{"type": "simulation", "body": {"metrics": {"tcp_goodput_bps": 100.2}}}]
c1 = loop.decided_by_little("tcp_goodput_bps@a > tcp_goodput_bps@b", ["a", "b"], vals, [])
c2 = loop.decided_by_little("tcp_goodput_bps@a > 100.2", ["a", "b"], vals, led0); c3 = loop.decided_by_little("tcp_goodput_bps@a > 100.2", ["a", "b"], vals, []); c4 = loop.decided_by_little("tcp_goodput_bps@a > tcp_goodput_bps@b * 0.9", ["a", "b"], vals, [])
say(len(c1) == 1 and c1[0]["percent"] == 0.5 and len(c2) == 1 and not c3 and not c4, f"decided by less than 1 %: two measured sides 0.5 % apart (yes: {c1}); a measured side against a number that is an earlier result of the session (yes); against a number the rule states of its own (no); against a side 10 % away (no)")
# ---- the checks of the real session s031, worked out again: the three that rested on differences of a few hundredths of a per cent, and no other
L = [json.loads(l) for l in (REAL / "sessions/s031/ledger.jsonl").read_text().splitlines() if l.strip() and '"type": "draft"' not in l[:70]]; marked = {}
for i, x in enumerate(L):
    if x["type"] != "experiment" or not (x["body"].get("decision_rules")): continue
    sims = [r for r in L if r["type"] == "simulation" and r["parent"] == x["id"]]; values = {s["body"]["label"]: s["body"].get("metrics") for s in sims}; before = [r for r in L[:i] if r["type"] == "simulation"]
    for r in x["body"]["decision_rules"]:
        c = loop.decided_by_little(r["decision_rule"], [q["label"] for q in x["body"]["runs"]], values, before)
        if c: marked[r["for"]] = [q["percent"] for q in c]
say(sorted(marked) == ["H11", "H12", "H16"] and all(p < 0.05 for v in marked.values() for p in v), f"s031, its fourteen checks worked out again with the tolerance of 1 %: marked are H11, H12 and H16 (the comparisons of two TCP types and of two measured times, {marked}), and no other")
# ---- a scripted session on a brief that states no tolerance
led, users = session("tol1", "two-hosts-open", ANSWERS); ck = {c["body"]["for"]: c["body"] for c in of(led, "check")}; text = loop.render(led); line = {h: next((l for l in text.splitlines() if f"decision rule for {h} " in l and l.startswith("[C")), "") for h in ("H1", "H2")}
say(set(ck) == {"H1", "H2"} and ck["H1"]["result"] == "held" and ck["H1"].get("tolerance") == 1.0 and len(ck["H1"].get("within_tolerance") or []) >= 1 and all(q["percent"] < 1 for q in ck["H1"]["within_tolerance"]),
    f"tol1 (no tolerance in the brief): the check of H1, two seeds compared, held and its record says which comparison was decided by less than the tolerance of 1 %: {ck.get('H1', {}).get('within_tolerance')}")
say("within_tolerance" not in ck["H2"] and "tolerance" not in ck["H2"], f"the check of H2 (UDP goodput at a part of 0.7 against 0.5: {ck['H2']['with_numbers'][:60]}) has no such mark")
say("[NOTE:" in line["H1"] and "less than the tolerance of 1 %" in line["H1"] and "count as equal" in line["H1"] and "[NOTE:" not in line["H2"], f"the line of H1's check, as the model reads it, ends with the note: “…{line['H1'][line['H1'].find('[NOTE:'):][:150]}”; H2's has none")
say("the rival explanation predicted FAILED and does not fit this result: the seed changes nothing that matters" in line["H1"], f"a check's line carries the rival explanation: “…{line['H1'][line['H1'].find('[the rival'):][:110]}”")
say(len(users) == 2 and all("TOLERANCE: two results that differ by less than 1 % count as equal (the default of the harness" in u for u in users), f"each of the {len(users)} turns told the model the tolerance (1 %, the default of the harness)")
# ---- a brief that states its own
b = json.loads((REAL / "briefs/two-hosts-udp-demand.json").read_text()); b["id"] = "tol-five"; b["goal"]["tolerance"] = 5; (P / "briefs/tol-five.json").write_text(json.dumps(b, indent=1) + "\n")
kn = {k: (v["default"] if k != "weightUdp" else None) for k, v in b["knobs"].items()}; mk = lambda label, w, **o: {"label": label, "params": {**kn, "weightUdp": w, **o}}
A5 = [turn(hypotheses=[H("TCP goodput changes with a step of 0.02 of the ratio", "Does a step of 0.02 of the ratio change what TCP delivers?")],
           experiment={"kind": "test", "tests": ["H1"], "question": "", "varied": ["weightUdp"], "control": "a", "runs": [mk("a", 0.28), mk("b", 0.30)],
                       "decision_rules": [{"for": "H1", "decision_rule": "tcp_goodput_bps@a > tcp_goodput_bps@b", "rival": "a step of 0.02 does nothing", "rival_predicts": "failed"}]})]
led5, users5 = session("tol5", "tol-five", A5); c5 = of(led5, "check")[0]["body"]; pct = [q["percent"] for q in c5.get("within_tolerance") or []]
say(c5.get("tolerance") == 5.0 and len(pct) == 1 and 1 < pct[0] < 5 and all("less than 5 % count as equal (stated by the brief)" in u for u in users5),
    f"tol5 (the brief states 5 %): a difference of {pct} %, which the default would let pass, is marked under the brief's tolerance ({c5.get('tolerance')}), and each turn says “5 % … stated by the brief”")
# ---- the final report: what limits the result, and which settings made no meaningful difference
schema = json.loads((P / "harness/schema.json").read_text()); rep = schema["properties"]["report"]["anyOf"][0]; order = list(rep["properties"])
fmt = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), tools.load_brief("two-hosts-open"))["properties"]["report"]["anyOf"][0]["properties"]["no_difference"]
say({"limit", "no_difference"} <= set(rep["required"]) and order.index("no_difference") < order.index("limit") < order.index("explanation") and fmt["items"].get("enum") == list(tools.load_brief("two-hosts-open")["knobs"]),
    f"the report's format requires no_difference and limit, before the explanation; no_difference takes only the brief's knobs: {fmt['items'].get('enum')}")
REP = lambda **k: {"goal": "the larger TCP goodput", "recommendation": {"weightUdp": 0.5, **KN}, "expected": {"tcp_goodput_bps": 482000000.0}, "no_difference": ["seed"], "limit": "TCP's part of the link: C2 shows what UDP takes.",
                   "explanation": "The seed changes nothing; the part of the link does.", "holds_when": "as tested", "breaks_when": "other rates", "claims": [{"text": "The part of the link decides what UDP delivers.", "role": "supports", "evidence": ["C2"]}], "open_questions": [], **k}
V = [{"for": "H1", "result": "refuted", "because": "C1: the two seeds give the same goodput within the tolerance.", "next": "report"}, {"for": "H2", "result": "supported", "because": "C2 held.", "next": "report"}]
no_limit = REP(); del no_limit["limit"]
# an answer of which nothing can be used is asked for a second time in the same turn, and the record keeps the second one: each refused report stands twice in the script
ledL, usersL = session("lim1", "two-hosts-open", [ANSWERS[0], turn(verdicts=V, report=no_limit, done=True), *[turn(report=REP(no_difference=["queuePkts"]), done=True)] * 2, *[turn(report=REP(no_difference=["bandwidth"]), done=True)] * 2, turn(report=REP(), done=True)])
why = [q for r in ledL for q in ([r["body"].get("reason") or ""] if r["type"] == "note" and r["body"].get("part") == "report" else [x.get("reason") or "" for x in (r["body"].get("refused") or []) if x.get("part") == "report"] if r["type"] == "malformed" else [])]; reps = of(ledL, "report")
say(len(why) == 3 and why[0].startswith("report.limit must be a text") and "queuePkts, which this session never varied" in why[1] and "names something that is not a knob: bandwidth" in why[2],
    f"a report without limit is refused (“{why[0][:60] if why else ''}…”); one that says a knob it never varied made no difference is refused (“{why[1][:90] if len(why) > 1 else ''}…”); one that names something that is no knob too")
say(len(reps) == 1 and reps[0]["body"]["no_difference"] == ["seed"] and reps[0]["body"]["limit"].startswith("TCP's part") and json.loads((P / "sessions/lim1/session.json").read_text()).get("how") == "done by the model",
    f"the report that says what limits the result and names the seed, which it varied, as making no difference is recorded, and the session ends “done by the model”")
# ---- the prompt
prompt = (P / "harness/prompt.txt").read_text()
say(all(x in prompt for x in ("The purpose of the work is to understand why", "Ask why before you ask which", "Tell a meaningful difference from a marginal one", "the results do not yet explain", "what limits the result", "- no_difference:", "- limit:")),
    "the prompt puts understanding before settings, asks each turn for what the results do not yet explain (since 2026-11-22 a finding), says “ask why before you ask which” and how to treat a difference inside the tolerance, and wants the report to say what limits the result")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
