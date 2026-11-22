"""Runs the same scripted sessions with two harness folders and compares what the supervisor was shown, request by request.
python3 -I same_prompts.py SCRATCH HARNESS_A HARNESS_B [SET_JSON]"""
import json, os, shutil, subprocess, sys
from pathlib import Path
SCR, A, B = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); SET = sys.argv[4] if len(sys.argv) > 4 else "{}"
assert "scratch" in str(SCR) or "scratchpad" in str(SCR)
HC, REAL = Path.home() / "research/tools/harness_checks", Path.home() / "project"
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
d = lambda label, w: {"label": label, "params": {"weightUdp": w, **KN}}
RIV = {"rival": "UDP's own sending rate limits it", "rival_predicts": "failed"}
def turn(ex): return {"observations": "read", "findings": [], "requests": [], "drop": [], "objections": [], "decisions": [], "report": None,
                      "whys": [{"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "revises": None},
                               {"about": ["E0"], "result": "TCP gets the other half", "guess": "TCP fills what UDP leaves", "revises": None}],
                      "hypotheses": [{"from_why": "Y1", "text": "UDP goodput rises with its part"}, {"from_why": "Y2", "text": "TCP goodput falls as UDP's part rises"}], "experiment": ex}
EX = {"kind": "test", "tests": ["H1", "H2"], "question": "", "runs": [d("a", 0.3), d("b", 0.7)], "measurements": [],
      "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", **RIV}, {"for": "H2", "decision_rule": "tcp_goodput_bps@b < tcp_goodput_bps@a", **RIV}]}
out = {}
for name, H in (("A", A), ("B", B)):
    root = SCR / name; shutil.rmtree(root, ignore_errors=True); P = root / "home/project"; (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
    shutil.copytree(H, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
    f = root / "a.json"; f.write_text(json.dumps({"answers": [turn(EX)], "supervisor": []}))
    env = {**os.environ, "HOME": str(root / "home"), "SCRIPTED_SET": SET}
    r = subprocess.run([sys.executable, "-I", str(HC / "scripted.py"), str(f), "--brief", "two-hosts-open-2", "--session", "p1", "--budget", "8", "--arm", "supervised"], env=env, capture_output=True, text=True, timeout=900)
    if "Traceback" in r.stderr: print(name, r.stderr[-1500:])
    out[name] = json.loads((P / "sessions/p1/supervisor_sent.json").read_text())
a, b = out["A"], out["B"]
print("requests:", len(a), len(b))
for i, (x, y) in enumerate(zip(a, b)):
    print(i, "same" if x == y else "DIFFERENT")
    if x != y:
        import difflib
        print("".join(list(difflib.unified_diff(x.splitlines(True), y.splitlines(True), n=1))[:30]))
