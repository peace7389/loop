"""Gate 0's cache (stage 2 item 25, corrected 2026-11-22 night, found by test_stage4 D): a guess's reading is kept by its guess, the records it cites
AND the result it states. A restatement that corrects its result (what not_in_the_records asks for) kept the guess's words and records, so it was
never read again and was recorded "contested" on the reading of its first statement. Usage: s2_fix_gkey.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
old = '(" ".join(str(w["guess"]).split()), tuple(w["about"]))'
n = s.count(old); assert n in (2, 3), n   # 3 with the batched first review (stage 4), 2 without
s = s.replace(old, 'gkey(w)')
a = '''def ground_of(model, brief, ledger, why, ask_fn=None'''
assert s.count(a) == 1
s = s.replace(a, '''def gkey(w):
    """What makes a guess the same for gate 0's reading: its guess, the records it cites and the result it states (a restatement that corrects its
    result is read again; the coherence audit, 2026-11-22)."""
    return (" ".join(str(w.get("guess")).split()), tuple(w.get("about") or []), " ".join(str(w.get("result")).split()))


''' + a)
p.write_text(s); print("patched", p, n)
