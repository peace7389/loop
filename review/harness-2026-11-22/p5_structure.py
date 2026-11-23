"""After the deploy (2026-11-23, night), found in session s056 turn 4, where the scheduler test (H5) was lost a second time:
- the supervisor sent it back as "a network-structure change outside the permitted settings": it is told the knobs the researcher may change and
  never that the brief lets the network change (s053's H1 was judged the same way). Every supervisor request on such a brief now says so, with
  the brief's limits;
- the third repair named q1000_cubic, a simulation of the second repair, which the harness had refused: the repair was read against the last test
  the harness accepted, without it. A repair is now read against the accepted test and the refused repair before it (the accepted one wins where
  both have a label); what the repaired rule does not name still leaves before anything is read;
- a rule that names a simulation its test does not have is refused with how to include it.
Usage: p5_structure.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:100], s.count(a)); s = s.replace(a, b)
rep('''    return (f"THE SYSTEM, in the brief's words: {' '.join(str(brief.get('description') or '').split())[:3000]}\\nTHE SETTINGS THE RESEARCHER MAY CHANGE: {knobs}\\n"
            f"TOLERANCE: two results that differ by less than {TOLERANCE:g} % count as equal.\\n")''',
    '''    st = brief.get("structure") or {}
    net = ""
    if brief.get("topology") and st.get("may_change"):   # the supervisor is told that the network itself may change (s056 H5, s053 H1: a scheduler was judged "outside the permitted settings")
        most = ", ".join(f"{n} {k}" for k, n in (st.get("most") or {}).items())
        net = ("THE NETWORK MAY CHANGE TOO: in this brief a simulation may change the structure of the network (add or remove hosts, links, flows and queues; "
               "for example a link's queue replaced by a scheduler), as a legitimate way to test a guess" + (f"; at most {most}" if most else "")
               + (f"; never removed: {', '.join(st['locked'])}" if st.get("locked") else "") + ". A planned simulation's change is shown with it (network changed: ...).\\n")
    return (f"THE SYSTEM, in the brief's words: {' '.join(str(brief.get('description') or '').split())[:3000]}\\nTHE SETTINGS THE RESEARCHER MAY CHANGE: {knobs}\\n" + net
            + f"TOLERANCE: two results that differ by less than {TOLERANCE:g} % count as equal.\\n")''')
rep('''    def repaired(test, hid, rp, every, reserved=0):''', '''    def repaired(test, hid, rp, every, reserved=0, refused_runs=()):''')
rep('''        base += [r for r in every if isinstance(r, dict) and r.get("label") not in {q.get("label") for q in base}]''',
    '''        base += [r for r in every if isinstance(r, dict) and r.get("label") not in {q.get("label") for q in base}]
        base += [r for r in refused_runs if isinstance(r, dict) and r.get("label") not in {q.get("label") for q in base}]   # the refused repair's simulations may be named again (s056 H5)''')
rep('''            t2, problem = repaired(test, hid, rp, every, reserved)''', '''            t2, problem = repaired(test, hid, rp, every, reserved, (refused or {}).get("runs") or [])''')
rep('''                return f"the decision rule for {r['for']} cannot be read: {e}. Decision rule: {r.get('decision_rule')}"''',
    '''                return (f"the decision rule for {r['for']} cannot be read: {e}. Decision rule: {r.get('decision_rule')}"
                        + (". A rule compares the simulations of its own test: to compare with one that ran before, list it among the runs with its settings "
                           "(the same settings are returned, not run again)" if "no simulation in this experiment is labelled" in str(e) else ""))''')
p.write_text(s); print("patched", p)

# applied after, by hand (2026-11-23 03:10): "1 link"; the refused repair's simulations as kept and as written (refused_runs in repair_rounds)
