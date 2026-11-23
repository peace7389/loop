"""The harness's own list of varied knobs after it removes designs (stage 1, item 8 of the coherence audit, 2026-11-22). s050 t1: the researcher planned
designs at queue lengths 900, 950 and 1000; no rule named the 900 and 950 ones, the harness removed them, and then refused the whole experiment because
"l1.queue.length is listed as varied but has the single value 1000" -- a list the harness itself had written. Scripted session on the brief
again_again (s050's network), arm "supervised", real ns-3 runs:
  V  a test of BBR against Cubic at queue length 1000 with an extra design at 900 that no rule names: the extra design is left out with its note, and
     the test runs (it was refused as a whole).
python3 -I test_varied.py SCRATCH_DIR [HARNESS_DIR]"""
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
def run(l, q, t): return {"label": l, "params": {"l1.queue.length": q, "tcp.type": t}}
T = {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None,
     "whys": [{"about": ["E0"], "result": "TCP gets 0 bps at the default", "guess": "Cubic collapses under UDP's loss", "revises": None}],
     "hypotheses": [{"from_why": "Y1", "text": "BBR gets more than Cubic at queue length 1000"}],
     "experiment": {"kind": "test", "tests": ["H1"], "question": "", "runs": [run("q1000_cubic", 1000, "TcpCubic"), run("q1000_bbr", 1000, "TcpBbr"), run("q900_cubic", 900, "TcpCubic")],
                    "measurements": [], "decision_rules": [{"for": "H1", "decision_rule": "tcp_goodput_bps@q1000_bbr > tcp_goodput_bps@q1000_cubic", "rival": "UDP fills the queue for any TCP", "rival_predicts": "failed"}]}}
G = {"records_show": "what the cited records show", "nearest_earlier": "none", "defect": "none", "because": "the supervisor's reading"}
REV = {"reads": "r", "stronger_rival": "none stronger", "rival_is_weak": False, "under_rival": "reasoned", "rival_outcome": "failed", "doubt_if": "nothing", "because": "reasoned", "defect": "none", "feedback": ""}
RUL = {"shows": "what the numbers show", "because": "the checks", "fair": True, "defect": "none", "result": "supported", "retest": "", "findings": []}
f = SCR / "v1.answers.json"; f.write_text(json.dumps({"answers": [T], "supervisor": [G, REV, RUL]}))
r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "again_again", "--session", "v1", "--arm", "supervised", "--budget", "8"], env=ENV, capture_output=True, text=True, timeout=1500)
if "Traceback" in r.stderr: print(r.stderr[-2000:])
led = [json.loads(l) for l in (P / "sessions/v1/ledger.jsonl").read_text().splitlines() if l.strip()]
print("V  A DESIGN NO RULE NAMES, AND THE LIST OF VARIED KNOBS")
x = [q for q in led if q["type"] == "experiment" and q["turn"] == 1]; notes = [str(q["body"].get("part")) + ": " + str(q["body"].get("reason")) for q in led if q["type"] == "note" and q["turn"] == 1 and q["body"].get("part")]
say(x and [q["label"] for q in x[0]["body"]["runs"]] == ["q1000_cubic", "q1000_bbr"] and any(n.startswith("design q900_cubic") for n in notes) and not any("listed as varied" in n for n in notes)
    and [q for q in led if q["type"] == "check" and q["turn"] == 1],
    f"the design at 900 is left out with its note, the test of H1 runs on the two others and is checked ({[q['label'] for q in x[0]['body']['runs']] if x else None}; notes {notes})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
