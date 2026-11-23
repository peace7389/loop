"""After the deploy (2026-11-23, night), found in s055 turn 10: a guess competing with Y10 was restated, the restatement prompt showed no
competes_with, and the researcher put Y10 into revises: Y29 both revised and competed with Y10. Y10, "revised", was no longer live, and the test of
the scheduler hypothesis H14 (from Y29), competing with Y10, was refused; the refusal suggested Y29, the hypothesis's own guess. Now:
- a guess competes with another or revises it, never both: where both name the same guess, competes_with stands and revises is dropped;
- the restatement shows competes_with and asks for it, and keeps what the restatement gives;
- the refusal of a revised competitor never suggests the hypothesis's own guess or one linked to it.
Usage: p4_revcomp.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:100], s.count(a)); s = s.replace(a, b)
rep('''        if isinstance(w, dict) and isinstance(w.get("competes_with"), str) and w["competes_with"] in why_map:
            w["competes_with"] = why_map[w["competes_with"]]''',
    '''        if isinstance(w, dict) and isinstance(w.get("competes_with"), str) and w["competes_with"] in why_map:
            w["competes_with"] = why_map[w["competes_with"]]
        if isinstance(w, dict) and w.get("competes_with") and w.get("competes_with") == w.get("revises"):   # an alternative to a guess, not its revision (s055 Y29)
            w["revises"] = None''')
rep('''                w2 = {**w, **{k: v for k, v in w2.items() if k in ("about", "result", "guess", "revises")}}''',
    '''                w2 = {**w, **{k: v for k, v in w2.items() if k in ("about", "result", "guess", "revises") + (("competes_with",) if COMP["on"] else ())}}
                if w2.get("competes_with") and w2.get("competes_with") == w2.get("revises"):   # never both (s055 Y29)
                    w2["revises"] = None''')
rep('''f"  result: {flat(w.get('result'))}\\n  guess: {flat(w.get('guess'))}\\n  revises: {w.get('revises')}\\n\\nWHAT WAS LEARNED SINCE YOUR LAST GUESS:\\n"''',
    '''f"  result: {flat(w.get('result'))}\\n  guess: {flat(w.get('guess'))}\\n  revises: {w.get('revises')}\\n" + (f"  competes_with: {w.get('competes_with')}\\n" if COMP["on"] else "") + "\\nWHAT WAS LEARNED SINCE YOUR LAST GUESS:\\n"''')
rep('''"guess (what in the system would make it so), revises (the id of an earlier guess it states more exactly, or null). It is taken as you restate it; if it still does not meet "''',
    '''"guess (what in the system would make it so), revises (the id of an earlier guess it states more exactly, or null)"
                + (", competes_with (the id of an earlier guess whose result it explains by another cause, or null: a guess competes with a guess or revises it, never both)" if COMP["on"] else "")
                + ". It is taken as you restate it; if it still does not meet "''')
rep('''        return f"the decision rule for {h} competes with {cw}, which {later} revised: name the live guess ({later}, or another)"''',
    '''        own_y = next((r["body"].get("from_why") for r in ledger if r["type"] == "hypothesis" and r["id"] == h), None)
        own_fam = revise_family(ledger, own_y) if own_y else set()
        return f"the decision rule for {h} competes with {cw}, which {later} revised: " + (f"name the live guess ({later}, or another)" if later not in own_fam else
                                                                                         f"{later} is {h}'s own guess, so name another live guess that explains the same result otherwise, or write one")''')
p.write_text(s); print("patched", p)
