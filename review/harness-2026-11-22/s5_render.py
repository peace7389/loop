"""Stage 5, part 3c: the researcher's ledger text in a session with competitors: a review round shows its three boxes and the guess the rule competes
with; a ruling shows the questions that failed and which guess fits the result. Usage: s5_render.py HARNESS_DIR"""
import sys
from pathlib import Path
H = Path(sys.argv[1])
p = H / "loop.py"; s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:110], s.count(a)); s = s.replace(a, b)
rep('''        return (f"by the supervisor of the guess {b['for']}, before anything is built on it: " + ("sound: it starts from what the records show" if b["defect"] == "none" else f"accepted with a warning ({GROUNDS.get(b['defect'], b['defect'])})" if b.get("warning") else f"accepted on its second statement, but the supervisor still objects ({GROUNDS.get(b['defect'], b['defect'])})")''',
    '''        return (f"by the supervisor of the guess {b['for']}, before anything is built on it: " + ("sound: it starts from what the records show" if b["defect"] == "none" else f"accepted with a warning ({GROUNDS_COMP.get(b['defect'], b['defect'])})" if b.get("warning") else f"accepted on its second statement, but the supervisor still objects ({GROUNDS_COMP.get(b['defect'], b['defect'])})")''')
rep('''        rules = "; ".join(f"{flat(d.get('decision_rule'))} (your rival: {flat(d.get('rival'))}; under it: {str(d.get('rival_predicts')).upper()})" for d in (b.get("test") or {}).get("decision_rules") or [])''',
    '''        rules = "; ".join(f"{flat(d.get('decision_rule'))} (" + (f"competes with {d['competes_with']}" if d.get("competes_with") else f"your rival: {flat(d.get('rival'))}") + f"; under it: {str(d.get('rival_predicts')).upper()})" for d in (b.get("test") or {}).get("decision_rules") or [])''')
rep('''                + (f" Feedback: {flat(b['feedback'])}" if b.get("feedback") else "") + (f" A stronger rival: {flat(b['stronger_rival'])}" if b.get("rival_is_weak") else "")''',
    '''                + (" Honest {honest}, Consistent {consistent}, Correct {correct}.".format(**b) if b.get("honest") else "")   # the three questions (stage 5)
                + (f" Feedback: {flat(b['feedback'])}" if b.get("feedback") else "") + (f" A stronger rival: {flat(b['stronger_rival'])}" if b.get("rival_is_weak") else "")''')
rep('''        verdict = {"approved": "approved", "sent_back": "SENT BACK, and repaired in the same turn", "contested": "run, but the supervisor still objects after the last round", "dropped": "refused in the last round: the hypothesis is dropped",''',
    '''        verdict = {"approved": "approved", "sent_back": "SENT BACK, and repaired in the same turn", "contested": "run, but the supervisor still objects after the last round", "dropped": "refused in the last round: the hypothesis is dropped",
                   "held": "HELD: not run in this turn, the hypothesis stays open (see the note)",''')
rep('''    if t == "verdict" and r.get("by") == "supervisor":
        return (f"by the supervisor on {b['for']}: {b['result']}. {flat(b['because'])}" + ("" if b.get("fair", True) else f" The test was not a fair test ({DEFECTS.get(b.get('defect'), b.get('defect'))}).")''',
    '''    if t == "verdict" and r.get("by") == "supervisor" and b.get("questions"):   # the three questions (stage 5): which failed, and which guess fits the result
        qs = b["questions"]
        return (f"by the supervisor on {b['for']}: {b['result']}. {flat(b['because'])}" + ("" if b.get("fair") else " Not a fair test: " + "; ".join(f"{q.capitalize()} failed: {flat(qs[q]['why'])}" for q in qs if qs[q]["box"] == "fail") + ".")
                + (" " + "; ".join(f"the guess {y} {f} this result" for y, f in (b.get("fits") or {}).items()) + ("." if b.get("fair") and not b.get("fits_contradicted") else " (not applied: " + ("its boxes contradicted each other" if b.get("fits_contradicted") else "the test was not fair") + ").") if b.get("fits") else "")
                + (f" A fair test: {flat(b['next'])}" if b.get("next") else "") + (f" [after your objection {b['after']}: {'the ruling stands' if b.get('stands') else 'the ruling is changed'}]" if b.get("after") else "")
                + (f" What the records show: {flat(b['shows'])}" if b.get("shows") else ""))
    if t == "verdict" and r.get("by") == "supervisor":
        return (f"by the supervisor on {b['for']}: {b['result']}. {flat(b['because'])}" + ("" if b.get("fair", True) else f" The test was not a fair test ({DEFECTS.get(b.get('defect'), b.get('defect'))}).")''')
p.write_text(s); print("render patched")
