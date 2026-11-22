"""The review of a test before it runs, in rounds (the arm "supervised"; 2026-11-22, the operator, after the reviews of s047 and s050): the researcher
states each rule's rival and rival_predicts; the harness refuses "held" before any call; the supervisor judges the researcher's rival (a clearly
stronger one? would the rule give rival_predicts under it?), each box after its reasoning; boxes that contradict each other are asked about once
more, a second contradiction is a refusal; feedback never holds a decision rule (cut, with a note); a refused test is repaired by the researcher in
the same turn, at most REVIEW_ROUNDS rounds, then AFTER_ROUNDS ("contested": it runs and the ruling knows; "dropped": its hypothesis is dropped);
approved tests of the same experiment run without waiting; a repair that cannot be read gives a note and nothing else is refused.
Scripted sessions with stand-in agents (scripted.py), real ns-3 runs of 2 s:
  A  H1 approved in round 1 after one question about contradicting boxes; H2 refused with feedback holding a rule (cut), repaired, approved in
     round 2 before any simulation ran (its rule fixed before its results), then H1 and H2 run in the same turn; H3 refused by the harness (rival_predicts "held") with no call to the supervisor;
  B  H1 refused three times (round 1: boxes still contradictory after the question), then contested: it runs, the ruling is told, the verdict says so;
  C  the same with AFTER_ROUNDS "dropped" and REVIEW_ROUNDS 2: H1 dropped with the supervisor's last reason, nothing run;
  D  H2's repair cannot be read: a note, H2 is not run and stays open; H1 of the same experiment ran;
  and the figures of session_figures.design_rounds; what the researcher is shown in a repair and the supervisor in a review (written to
  SCRATCH_DIR/prompts.txt); s047 to s050 render as before (--before HARNESS_BEFORE).
python3 -I test_design_rounds.py SCRATCH_DIR [HARNESS_DIR] [--before HARNESS_BEFORE]"""
import importlib.util, json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
BEFORE = next((Path(sys.argv[i + 1]).resolve() for i, a in enumerate(sys.argv) if a == "--before" and i + 1 < len(sys.argv)), None)
args = [a for a in sys.argv[1:] if not a.startswith("--") and (BEFORE is None or Path(a).resolve() != BEFORE)]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
ENV = {**os.environ, "HOME": str(SCR / "home")}
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import loop, session_figures
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, answers, sup, set_=None):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup}))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "two-hosts-open-2", "--session", sid, "--arm", "supervised", "--budget", "8"],
                       env={**ENV, **({"SCRIPTED_SET": json.dumps(set_)} if set_ else {})}, capture_output=True, text=True, timeout=1500)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    S = P / "sessions" / sid
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    rd = lambda n: json.loads((S / n).read_text()) if (S / n).is_file() else []
    return led, rd("users_sent.json"), rd("supervisor_sent.json")
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
rounds = lambda led, h: [(r["body"]["round"], r["body"]["decision"], r["by"]) for r in of(led, "review") if r["body"].get("gate") == "design" and r["body"]["for"] == h]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w, **o): return {"label": label, "params": {"weightUdp": w, **KN, **o}}
def rule(h, text, rival="UDP's own sending rate limits it", predicts="failed"): return {"for": h, "decision_rule": text, "rival": rival, "rival_predicts": predicts}
WHY = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "revises": None}
def turn(hyps, rules, runs): return {"observations": "OBS-MARK read", "findings": [], "requests": [], "whys": [WHY], "hypotheses": [{"from_why": "Y1", "text": t} for t in hyps], "drop": [],
                                     "experiment": {"kind": "test", "tests": [f"H{i + 1}" for i in range(len(hyps))], "question": "", "runs": runs, "measurements": [], "decision_rules": rules},
                                     "objections": [], "decisions": [], "report": None}
GROUND = {"records_show": "what the records show", "nearest_earlier": "none", "defect": "none", "because": "sound"}
def REV(defect="none", outcome="failed", weak=False, feedback=""):
    return {"reads": "what the rule compares", "stronger_rival": "a stronger one: the queue limits it" if weak else "none stronger", "rival_is_weak": weak, "under_rival": "reasoned",
            "rival_outcome": outcome, "doubt_if": "UDP equal in both", "because": "reasoned to the decision", "defect": defect, "feedback": feedback}
AGAIN = lambda outcome, defect="none": {"because": "the second answer", "rival_outcome": outcome, "defect": defect}
RULING = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
REPAIR = lambda text, runs=(): {"decision_rule": text, "rival": "the queue's length limits TCP", "rival_predicts": "failed", "runs": list(runs)}

print("A  ROUND ONE, A CONTRADICTION ASKED ABOUT, A CUT, A REPAIR, A REFUSAL BY THE HARNESS")
TA = turn(["UDP goodput rises with its part", "TCP goodput falls as UDP's part rises", "TCP gets something at both parts"],
          [rule("H1", "udp_goodput_bps@b > udp_goodput_bps@a"), rule("H2", "tcp_goodput_bps@a > tcp_goodput_bps@b"), rule("H3", "tcp_goodput_bps@a > 0", predicts="held")], [d("a", 0.3), d("b", 0.7)])
led, users, sup = session("a1", [TA, REPAIR("tcp_goodput_bps@a > 1.05 * tcp_goodput_bps@b")],
                          [GROUND, REV("none", "held"), AGAIN("failed"), REV("rival_passes_too", "held", feedback="The rival passes this rule too. Compare tcp_goodput_bps@a > 2 * tcp_goodput_bps@b instead."), REV(), RULING, RULING])
xs = [(r["id"], r["body"]["tests"]) for r in of(led, "experiment", 1)]; order = [r["id"] for r in led]
p1 = (of(led, "repair") or [{}])[0]; r1 = [r for r in of(led, "review") if r["body"].get("for") == "H1" and r["body"].get("gate") == "design"]
r2 = [r for r in of(led, "review") if r["body"].get("for") == "H2" and r["body"].get("gate") == "design"]
say(rounds(led, "H1") == [(1, "approved", "supervisor")] and r1 and r1[0]["body"].get("again", {}).get("rival_outcome") == "failed" and "still" not in r1[0]["body"]["again"],
    f"H1: the boxes contradicted each other (no defect, HELD under the rival); asked once more it answered FAILED: approved in round 1 ({r1[0]['body'].get('again') if r1 else None})")
say(rounds(led, "H2") == [(1, "sent_back", "supervisor"), (2, "approved", "supervisor")] and r2 and "@" not in r2[0]["body"]["feedback"] and r2[0]["body"].get("cut") == 1
    and any("cut 1 part" in r["body"].get("text", "") for r in of(led, "note", 1)) and p1.get("body", {}).get("round") == 2 and p1.get("by") == "model",
    f"H2: sent back in round 1 with feedback that held a rule (cut, with a note: “{r2[0]['body']['feedback'] if r2 else ''}”); repaired by the researcher ({p1.get('id')}, round 2), approved in round 2")
sim1 = min((order.index(r["id"]) for r in of(led, "simulation", 1)), default=-1)
say(xs == [("X1", ["H1"]), ("X2", ["H2"])] and p1.get("id") in order and order.index(p1["id"]) < sim1 and len(of(led, "verdict", 1)) == 2,
    f"H1 is not held to a later turn by H2: in the same turn H2 was repaired first, before any simulation ran (its rule fixed before the results it names), then H1 ran (X1) and H2 as an experiment of its own (X2); both ruled on: {xs}")
reviewed = [u for u in sup if "THE HYPOTHESIS H" in u and "Before any of these simulations is run" in u and "One question:" not in u]   # a review, not the question asked after it
say(not rounds(led, "H3") and any("test of H3" in (r["body"].get("part") or "") and "hold under the rival too" in r["body"].get("reason", "") for r in of(led, "note", 1))
    and not any("THE HYPOTHESIS H3" in u for u in reviewed) and len(reviewed) == 3,
    f"H3 (rival_predicts held) refused by the harness with no call to the supervisor; the supervisor reviewed H1, H2 and H2's repair ({len(reviewed)} reviews)")
rep = next((u for u in users if u.startswith("YOUR TEST OF H2 WAS SENT BACK")), ""); rv2 = next((u for u in reviewed if "THIS IS ROUND 2" in u), "")
say(rep and "round 2 of at most 3" in rep and "The rival passes this rule too." in rep and "tcp_goodput_bps@a > 2" not in rep and rv2 and "The rival passes this rule too." in rv2
    and "THE RESEARCHER'S RIVAL for this rule: the queue's length limits TCP" in rv2 and not any("OBS-MARK" in u for u in sup),
    "the repair call shows the round and the (cut) feedback; the supervisor's second review shows the earlier feedback and the researcher's new rival, and never its observations")
(SCR / "prompts.txt").write_text("=== WHAT THE RESEARCHER IS SHOWN IN A REPAIR (session a1, H2, round 2) ===\n" + loop.REPAIR_SYSTEM + "\n\n" + rep
                                + "\n\n=== WHAT THE SUPERVISOR IS SHOWN IN A REVIEW (session a1, H2, round 2) ===\n" + loop.SUPERVISOR + "\n\n" + rv2 + "\n")
fa = session_figures.design_rounds(led)
say(fa and fa["tests"] == 3 and fa["reviewed"] == 2 and fa["approved_first"] == 1 and fa["repaired_approved"] == 1 and fa["refused_by_harness"] == 1 and fa["rounds"]["max"] == 2,
    f"session_figures.design_rounds: {fa}")

print("B  REFUSED UNTIL THE LIMIT, THEN CONTESTED")
TB = turn(["UDP goodput rises with its part"], [rule("H1", "udp_goodput_bps@b > udp_goodput_bps@a")], [d("a", 0.3), d("b", 0.7)])
led, users, sup = session("b1", [TB, REPAIR("udp_goodput_bps@b > 1.1 * udp_goodput_bps@a"), REPAIR("udp_goodput_bps@d > 1.1 * udp_goodput_bps@c", [d("c", 0.2), d("d", 0.8)])],
                          [GROUND, REV("none", "held"), AGAIN("held"), REV("confounded", "failed", feedback="Another setting limits the effect."), REV("confounded", "failed", feedback="Still limited by another setting."), RULING])
rb = [r for r in of(led, "review") if r["body"].get("gate") == "design"]; vb = of(led, "verdict"); xb = of(led, "experiment", 1)
say(rounds(led, "H1") == [(1, "sent_back", "supervisor"), (2, "sent_back", "supervisor"), (3, "contested", "supervisor")] and rb[0]["body"].get("again", {}).get("still"),
    f"round 1: the boxes still contradicted each other after the question: a refusal ({(rb[0]['body'].get('again') or {}).get('still', '')[:80]}); rounds 2 and 3 refused; after round 3: contested")
say(len(xb) == 1 and xb[0]["body"]["tests"] == ["H1"] and [r["label"] for r in xb[0]["body"]["runs"]] == ["c", "d"] and vb and vb[0]["body"].get("contested")
    and any("BEFORE IT RAN" in u and "Still limited by another setting." in u for u in sup),
    "the contested test runs (its repaired simulations c and d); the ruling is told the supervisor still objected, and the verdict says contested")
fb = session_figures.design_rounds(led)
say(fb and fb["contested"] == 1 and fb["rounds"] == {"mean": 3.0, "max": 3}, f"session_figures.design_rounds: {fb}")

print("C  REFUSED UNTIL THE LIMIT, THEN DROPPED (AFTER_ROUNDS \"dropped\", REVIEW_ROUNDS 2)")
led, users, sup = session("c1", [TB, REPAIR("udp_goodput_bps@b > 1.1 * udp_goodput_bps@a")],
                          [GROUND, REV("confounded", "failed", feedback="Another setting limits the effect."), REV("confounded", "failed", feedback="Still limited.")], set_={"AFTER_ROUNDS": "dropped", "REVIEW_ROUNDS": 2})
dr = of(led, "drop")
say(rounds(led, "H1") == [(1, "sent_back", "supervisor"), (2, "dropped", "supervisor")] and dr and dr[0]["by"] == "harness" and "Still limited." in dr[0]["body"]["why"] and not of(led, "experiment", 1),
    f"after round 2 of 2 the hypothesis is dropped with the supervisor's last reason (“{dr[0]['body']['why'] if dr else ''}”); nothing is run")

print("D  A REPAIR THAT CANNOT BE READ")
led, users, sup = session("d1", [turn(["UDP goodput rises with its part", "TCP goodput falls as UDP's part rises"], [rule("H1", "udp_goodput_bps@b > udp_goodput_bps@a"), rule("H2", "tcp_goodput_bps@a > tcp_goodput_bps@b")],
                                      [d("a", 0.3), d("b", 0.7)]), "this is not a JSON object"],
                          [GROUND, REV(), REV("rival_passes_too", "held", feedback="The rival passes too."), RULING])
say([(r["body"]["tests"]) for r in of(led, "experiment", 1)] == [["H1"]] and any("could not be read" in r["body"].get("text", "") and "H2" in r["body"].get("text", "") for r in of(led, "note", 1))
    and of(led, "verdict", 1) and not [r for r in of(led, "drop") if r["body"]["for"] == "H2"],
    "H2's repair could not be read: a note, H2 is not run and stays open; H1 of the same experiment ran and was ruled on")

print("OLD SESSIONS")
if BEFORE:
    spec = importlib.util.spec_from_file_location("loop_before", BEFORE / "loop.py"); old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    same = []
    for sid in ("s047", "s048", "s049", "s050"):
        lg = [json.loads(l) for l in (REAL / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
        same.append((sid, old.render(lg) == loop.render(lg), len(loop.render(lg)), session_figures.design_rounds(lg)))
    say(all(x[1] and x[3] is None for x in same), f"s047 to s050 render the same ledger text as before ({[(s, n) for s, ok, n, _ in same if ok]} characters), and have no rounds in their figures")
else:
    say(False, "--before HARNESS_BEFORE not given")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
