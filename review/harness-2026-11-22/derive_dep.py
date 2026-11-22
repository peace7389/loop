"""The harness to deploy (2026-11-22, the operator: "Deploy A, B and D together, nothing else"): the review branch's harness (part 1, which A needs,
and A, B, D) with part 2 (the measurement statistics crossings/corr/lag, `with`, taps, trace_points) and part 3 (the short answer format of the
single-AI arm) left out: tools.py, schema.json, manifest.json and network.py as they run live; the two sentences of part 2 in the instructions as
they run live; the short format switched off (SHORT_FORMAT = False). Usage: derive_dep.py FROM_HARNESS LIVE_HARNESS OUT_HARNESS"""
import shutil, sys
from pathlib import Path
src, live, out = map(Path, sys.argv[1:4])
shutil.rmtree(out, ignore_errors=True)
shutil.copytree(src, out, ignore=shutil.ignore_patterns("__pycache__", "loop.log"))
for f in ("tools.py", "schema.json", "manifest.json", "network.py"):
    shutil.copy(live / f, out / f)
# prompt.txt: the sentence of part 2 (measure and probe, with combined measurements and taps) back to the live one
p, l = (out / "prompt.txt").read_text(), (live / "prompt.txt").read_text()
key = " Two of the tools look deeper than the outputs and cost no simulation:"
i, j = p.index(key), l.index(key)
p_end, l_end = p.index("\n", i), l.index("\n", j)
p = p[:i] + l[j:l_end] + p[p_end:]
(out / "prompt.txt").write_text(p)
# loop.py: the part-2 parenthetical of the supervised arm's instructions out; the short format of part 3 behind a switch, off
s = (out / "loop.py").read_text()
a = "metrics, series and measure read what a simulation you already ran recorded (measure: a statistic of a quantity you combine from them, e.g. tcp_inflight / min(tcp_cwnd, tcp_rwnd); corr and lag: do two move together, which leads);"
assert s.count(a) == 1, "LEAN part-2 parenthetical"
s = s.replace(a, "metrics, series and measure read what a simulation you already ran recorded;")
a = '''    short = arm == "hypotheses" and (was is None or json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("format") == "short")'''
assert s.count(a) == 1, "short gate"
s = s.replace(a, '''    short = SHORT_FORMAT and arm == "hypotheses" and (was is None or json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("format") == "short")''')
a = '''SHORT_DROP = {'''
assert s.count(a) == 1
s = s.replace(a, '''SHORT_FORMAT = False   # the short format of the arm "hypotheses" is under review and not deployed (2026-11-22, the operator: deploy A, B and D, nothing else)
SHORT_DROP = {''')
(out / "loop.py").write_text(s)
print("derived", out)
