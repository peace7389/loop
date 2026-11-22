"""After the deploy (2026-11-23, night), found in s055 turn 5: a repair's runs are merged with the test's (stage 2), and the simulations its rule no
longer names were dropped only after the count was checked: H7's repair (four simulations named) was refused with "an experiment has 1 to 4
simulations". They are dropped before; the refusal says how many there are. Usage: p3_count.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:100], s.count(a)); s = s.replace(a, b)
rep('''        runs = [dict(given.pop(r.get("label"), r)) for r in base] + [dict(r) for r in given.values()]''',
    '''        runs = [dict(given.pop(r.get("label"), r)) for r in base] + [dict(r) for r in given.values()]
        named = set(re.findall(r"@([A-Za-z0-9_]+)", str(rule.get("decision_rule") or "")))
        if named and any(r.get("label") in named for r in runs):   # the simulations the repaired rule no longer names leave before anything is counted (s055 H7)
            runs = [r for r in runs if r.get("label") in named]''')
rep('''        return f"an experiment has 1 to {per} simulations"''', '''        return f"an experiment has 1 to {per} simulations; this one has {len(runs)}"''')
p.write_text(s); print("patched", p)
