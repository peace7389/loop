"""Stage 1, item 8 (the coherence audit, 2026-11-22): when the harness itself removes designs of an experiment (a design no rule names, the tests of
hypotheses that are not open), a knob listed as varied that no longer varies leaves the list: trim refused whole experiments for the harness's own
leftover ("`l1.queue.length` is listed as varied but has the single value `1000` in every design": s050 t1 lost H1 to H3, s051 t4).
Usage: s1_varied.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)
rep('''def without_tests(ex, gone):''', '''def still_varied(ex):
    """The experiment with its list of varied knobs cut to those that still take more than one value in its designs: after the harness has removed
    designs, a knob it left with one value is no longer varied, and the experiment is not refused for it (the coherence audit, 2026-11-22)."""
    if not isinstance(ex, dict) or not isinstance(ex.get("varied"), list):
        return ex
    runs = [r for r in ex.get("runs") or [] if isinstance(r, dict)]
    takes = lambda k: len({json.dumps((r.get("params") or {}).get(k), sort_keys=True) for r in runs})
    return {**ex, "varied": [k for k in ex["varied"] if not isinstance(k, str) or k not in {q for r in runs for q in (r.get("params") or {})} or takes(k) > 1]}


def without_tests(ex, gone):''')
rep('''    if ex.get("control") and ex["control"] not in {r.get("label") for r in runs}:
        out["control"] = None
    return out''', '''    if ex.get("control") and ex["control"] not in {r.get("label") for r in runs}:
        out["control"] = None
    return still_varied(out)''')
rep('''                ex = {**ex, "runs": [r for r in ex["runs"] if r.get("label") not in idle]}''', '''                ex = still_varied({**ex, "runs": [r for r in ex["runs"] if r.get("label") not in idle]})''')
p.write_text(s); print("patched", p)
