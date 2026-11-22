"""The supervisor's review before a test is run (gate 1): a rival it "cannot tell" from the guess sends the test back (2026-11-22, the operator, after
s050: H1 and H4 were approved while the supervisor wrote that under its own rival it could not tell what the rule would do, and both were ruled
inconclusive afterwards because a rival passes too; in s044 to s050, of 9 tests approved so, 4 were ruled inconclusive, 2 refuted, 3 never ruled).
On a copy of s050's ledger as it stood after turn 2 (read only, no simulation; the supervisor's answer is given by the check):
  - defect none, rival "cannot tell": the defect is "a rival passes too", and the review says that the harness made it so;
  - defect none, rival "held": as before, "a rival passes too";
  - defect none, rival "failed": no defect, as before;
  - "a rival passes too" named with a rival that would fail the rule: no defect stands, as before (s044: G14, G15);
  - "a rival passes too" named with "cannot tell": it stands.
python3 -I test_rival_cannot_tell.py SCRATCH_DIR [HARNESS_DIR]"""
import json, os, shutil, sys
from pathlib import Path
REAL = Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import loop
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
D = REAL / "sessions/s050"
led = [json.loads(l) for l in (D / "ledger.jsonl").read_text().splitlines() if l.strip()]   # read by the harness's own functions; nothing of it is printed but ids
brief = json.loads((D / "session.json").read_text())["given"]; loop.tools.BRIEF = brief
x = next(r for r in led if r["type"] == "experiment" and "H1" in (r["body"].get("tests") or []))
at = led[:led.index(x)]   # as it stood when the test of H1 was reviewed
print("A RIVAL IT CANNOT TELL FROM THE GUESS")
def review(outcome, defect):
    ans = {"rival": "a longer queue lets TCP through for another reason", "rival_outcome": outcome, "doubt_if": "nothing", "because": "the check's supervisor", "defect": defect}
    return loop.review_design("m", brief, at, x["body"], "H1", ask_fn=lambda model, user, schema: ans)[0]
r = review("cannot tell", "none")
say(r["defect"] == "rival_passes_too" and "the harness" in r["because"] and "cannot tell" in r["because"],
    f"defect none with a rival it cannot tell apart: sent back as “a rival passes too”, and the review says the harness made it so (“{r['because'][-120:]}”)")
r2, r3 = review("held", "none"), review("failed", "none")
say(r2["defect"] == "rival_passes_too" and r3["defect"] == "none", f"as before: a rival under which the rule holds is “a rival passes too” ({r2['defect']}); one under which it fails is no defect ({r3['defect']})")
r4, r5 = review("failed", "rival_passes_too"), review("cannot tell", "rival_passes_too")
say(r4["defect"] == "none" and "no defect stands" in r4["because"] and r5["defect"] == "rival_passes_too",
    f"“a rival passes too” named with a rival that fails the rule: no defect stands, as before (s044) ({r4['defect']}); named with “cannot tell”: it stands ({r5['defect']})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
