"""Gate 0's "refused once" (stage 2 item 25): once in a turn (the default), or once in the session as before part D, for a check that reproduces the
arm without restatements (test_supervised.py's OLD_GUESSES). Usage: s2_fix_once.py LOOP_PY"""
import re, sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
a = '''RESTATE_GUESSES = True   #'''
assert s.count(a) == 1
s = s.replace(a, '''REFUSED_ONCE = "turn"   # the arm "supervised": a guess about the same records is refused once in a turn ("turn"; the coherence audit, 2026-11-22: once in the session left those records unguarded for the rest of it), or once in the session ("session": the rule before part D)
''' + a)
pat = re.compile(r'^( +)refuse = g\["defect"\] != "none" and not warning and not refused_about\.get\(\(turn, about\)\)(   # once in a turn[^\n]*)\n\1if refuse:\n\1    refused_about\[\(turn, about\)\] = 1\n', re.M)
m = pat.search(s); assert m and len(pat.findall(s)) == 1, "the refusal lines"
ind = m.group(1)
s = s[:m.start()] + (f'{ind}scope = (turn if REFUSED_ONCE == "turn" else None, about){m.group(2)}\n{ind}refuse = g["defect"] != "none" and not warning and not refused_about.get(scope)\n'
                     f'{ind}if refuse:\n{ind}    refused_about[scope] = 1\n') + s[m.end():]
p.write_text(s); print("patched", p)
