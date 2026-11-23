"""Part D (2026-11-22, the operator, after s050 and s051): in the arm "supervised" a guess is no longer refused for good. The supervisor's defect
"not_from_what_was_learned" is a recorded warning; any other refusal (the harness's own, such as the chain rule, or the supervisor's) brings one
restatement in the same turn, after which the guess is accepted, contested if it still fails; its hypotheses and test go ahead (no cascade).
Scripted sessions with stand-in agents (scripted.py), real ns-3 runs of 2 s:
  W  a guess the supervisor reads as not from what was learned: accepted with a warning (its review says so), its hypothesis and test run;
  H  a guess the harness refuses (the chain rule: nothing learned since cited): restated once, checked again by the harness alone (no call to
     the supervisor), still failing: accepted as contested; its hypothesis and test run in that turn;
  S  a guess the supervisor refuses: restated once, read again by the supervisor, accepted as contested; its hypothesis and test run;
  U  a restatement that cannot be read: the guess as first stated is accepted as contested, with a note of it in its record; its test runs;
  and session_figures.guess_reviews; the instructions (restatement, revises for a refinement; one limit on the whole text); s047 to s051 render
  as before (--before HARNESS_BEFORE).
python3 -I test_guess_restate.py SCRATCH_DIR [HARNESS_DIR] [--before HARNESS_BEFORE]"""
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
def session(sid, answers, sup):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps({"answers": answers, "supervisor": sup}))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "two-hosts-open-2", "--session", sid, "--arm", "supervised", "--budget", "8"],
                       env=ENV, capture_output=True, text=True, timeout=1500)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    S = P / "sessions" / sid
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()]
    rd = lambda n: json.loads((S / n).read_text()) if (S / n).is_file() else []
    return led, rd("users_sent.json"), rd("supervisor_sent.json"), json.loads((S / "session.json").read_text())
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led, turn: [(r["body"].get("part"), r["body"].get("reason") or r["body"].get("text")) for r in of(led, "note", turn)]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w): return {"label": label, "params": {"weightUdp": w, **KN}}
RIVAL = {"rival": "UDP's own sending rate limits it", "rival_predicts": "failed"}
def why(about, guess): return {"about": about, "result": "UDP gets about half of the link", "guess": guess, "revises": None}
def turn(whys=(), hyps=(), h=None, a=0.3, b=0.7): return {"observations": "read", "findings": [], "requests": [], "whys": list(whys), "hypotheses": [{"from_why": y, "text": t} for y, t in hyps], "drop": [],
    "experiment": {"kind": "test", "tests": [h], "question": "", "runs": [d("a", a), d("b", b)], "measurements": [], "decision_rules": [{"for": h, "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", **RIVAL}]} if h else None,
    "objections": [], "decisions": [], "report": None}
G = lambda defect="none": {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": defect, "because": "the supervisor's reading"}
RULING = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
REV = {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "it fails", "rival_outcome": "failed", "doubt_if": "nothing", "because": "fair", "defect": "none", "feedback": ""}

print("W  NOT FROM WHAT WAS LEARNED: A WARNING")
led, users, sup, meta = session("w1", [turn([why(["E0"], "the scheduler gives each flow its part")], [("Y1", "UDP goodput rises with its part")], "H1"),
                                       turn([why(["E1"], "UDP's part sets its goodput exactly")], [("Y2", "UDP goodput rises again from 0.5 to 0.9")], "H2", 0.5, 0.9)],
                                [G(), REV, RULING, G("not_from_what_was_learned"), REV, RULING])
g2 = [r for r in of(led, "review", 2) if r["body"].get("gate") == "ground"]
say(g2 and g2[0]["body"]["decision"] == "approved" and g2[0]["body"].get("warning") is True and g2[0]["body"]["defect"] == "not_from_what_was_learned" and not [n for n in notes(led, 2) if n[0] == "new why"]
    and len(of(led, "hypothesis", 2)) == 1 and of(led, "experiment", 2) and "accepted with a warning" in loop.render(led),
    f"turn 2: the guess read as not from what was learned is accepted with a warning ({g2[0]['body']['decision'] if g2 else None}, warning {g2[0]['body'].get('warning') if g2 else None}); its hypothesis and its test run; the ledger text says “accepted with a warning”")
fw = session_figures.guess_reviews(led)
say(fw and fw["warnings"] == 1 and fw["restated"] == 0 and fw["contested"] == 0, f"session_figures.guess_reviews: {fw}")

print("H  REFUSED BY THE HARNESS (THE CHAIN RULE): RESTATED, CHECKED BY THE HARNESS ALONE, CONTESTED")
led, users, sup, meta = session("h1", [turn([why(["E0"], "the scheduler gives each flow its part")], [("Y1", "UDP goodput rises with its part")], "H1"),
                                       turn([why(["E0"], "the link is shared evenly")], [("Y2", "UDP goodput rises from 0.5 to 0.9")], "H2", 0.5, 0.9),
                                       why(["E0"], "the link is shared evenly, as the baseline shows")],
                                [G(), REV, RULING, REV, RULING])
y2 = (of(led, "why", 2) or [{}])[0].get("body", {}); rq = [u for u in users if u.startswith("YOUR GUESS WAS NOT ACCEPTED")]
ground2 = [u for u in sup if "THE GUESS of why it came out so: the link is shared evenly" in u or "the link is shared evenly, as the baseline shows" in u and "records_show" not in u]
say(y2.get("restated", {}).get("by") == "harness" and "starts only from records your earlier guesses already had" in y2["restated"]["reason"] and y2.get("contested") and y2["guess"] == "the link is shared evenly, as the baseline shows"
    and rq and "(the harness)" in rq[0] and len(sup) == 6 and not [n for n in notes(led, 2) if n[0] in ("new why", "new hypothesis")] and len(of(led, "hypothesis", 2)) == 1 and of(led, "experiment", 2),
    f"turn 2: the chain rule refused the guess; the researcher restated it once in the same turn (shown the harness's reason); still from the baseline alone, it is accepted as contested, "
    f"with no call to the supervisor for it ({len(sup)} supervisor requests: the baseline's look, the first guess, two reviews, two rulings); its hypothesis and test run")
say("[restated in the same turn: first not accepted by the harness" in loop.render(led) and "accepted as contested" in loop.render(led), "the ledger text says the guess was restated and accepted as contested")
fh = session_figures.guess_reviews(led)
say(fh and fh["restated"] == 1 and fh["contested"] == 1, f"session_figures.guess_reviews: {fh}")

print("S  REFUSED BY THE SUPERVISOR: RESTATED, READ AGAIN, CONTESTED")
led, users, sup, meta = session("s1", [turn([why(["E0"], "the link carries more than 1 Gbps")], [("Y1", "UDP goodput exceeds 1 Gbps at the part 0.7")], "H1"),
                                       why(["E0"], "the link carries 1 Gbps and UDP gets its part of it")],
                                [G("not_in_the_records"), G("not_in_the_records"), REV, RULING])
y1 = (of(led, "why", 1) or [{}])[0].get("body", {}); g1 = [(r["body"]["decision"], r["body"]["defect"]) for r in of(led, "review", 1) if r["body"].get("gate") == "ground"]
say(y1.get("restated", {}).get("by") == "supervisor" and y1["guess"] == "the link carries 1 Gbps and UDP gets its part of it" and ("sent_back", "not_in_the_records") in g1 and ("contested", "not_in_the_records") in g1
    and of(led, "hypothesis", 1) and of(led, "experiment", 1) and of(led, "verdict", 1) and not [n for n in notes(led, 1) if n[0] in ("new why", "new hypothesis", "experiment")],
    f"turn 1: the supervisor refused the guess; restated once, it read it again and still objected: accepted as contested ({g1}); its hypothesis and test ran and were ruled on in the same turn, nothing fell with it")

print("U  A RESTATEMENT THAT CANNOT BE READ")
led, users, sup, meta = session("u1", [turn([why(["E0"], "the link carries more than 1 Gbps")], [("Y1", "UDP goodput exceeds 1 Gbps at the part 0.7")], "H1"), "not a JSON object"],
                                [G("not_in_the_records"), REV, RULING])
y1 = (of(led, "why", 1) or [{}])[0].get("body", {})
say(y1.get("restated", {}).get("unread") is True and y1["guess"] == "the link carries more than 1 Gbps" and y1.get("contested") and of(led, "experiment", 1) and of(led, "verdict", 1),
    "the restatement could not be read: the guess as first stated is accepted as contested (its record says so), and its hypothesis and test run")

print("THE INSTRUCTIONS")
lean = loop.LEAN_PROMPT; whole = lean + loop.FINDINGS_TEXT["supervised"]
say("comes back to you once, in the same turn, to restate" in lean and "states more exactly with new numbers or a narrower cause" in lean and len(whole) < 10_000,
    f"the supervised arm's instructions say a guess not accepted comes back once to be restated, and that a refinement names the guess it states more exactly in revises; the whole text (with findings) is {len(whole)} characters, under the one limit of 10,000")

print("OLD SESSIONS")
if BEFORE:
    spec = importlib.util.spec_from_file_location("loop_before", BEFORE / "loop.py"); old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    same = []
    for sid in ("s047", "s048", "s049", "s050", "s051"):
        lg = [json.loads(l) for l in (REAL / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
        same.append((sid, old.render(lg) == loop.render(lg), session_figures.guess_reviews(lg) is None))
    say(all(a and b for _, a, b in same), f"s047 to s051 render the same ledger text as before part D, and have no guess figures: {same}")
else:
    say(False, "--before HARNESS_BEFORE not given")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
