"""After the deploy, part 11 (s057 turn 8, 2026-11-23 05:27): the researcher's ledger text marks a refuted guess "refuted by V8: no hypothesis can
come from it; a new guess may revise it", and says nothing of competing with it; in one reply the researcher named the refuted Y23 as the competitor
of two new guesses and of a test, and all three were refused ("'Y23' is refuted"). With competitors the mark now says that no guess or test may
compete with it either. python3 -I p11_refuted.py LOOP_PY"""
import sys
from pathlib import Path
f = Path(sys.argv[1]); s = f.read_text()
a = '''(f" by {w['by']}: no hypothesis can come from it; a new guess may revise it" if w.get("by") else "")'''
b = '''(f" by {w['by']}: no hypothesis can come from it" + (", and no guess or test may compete with it" if COMP["on"] else "") + "; a new guess may revise it" if w.get("by") else "")'''
assert s.count(a) == 1; f.write_text(s.replace(a, b)); print("p11 applied to", f)
