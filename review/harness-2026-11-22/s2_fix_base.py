"""Stage 2, item 19, corrected (2026-11-22, night: test_repair_structure): a repair's runs are read against the last test the harness ACCEPTED, not
against a repair the harness refused (its garbled network change was kept by an empty runs list); the repair prompt shows that refused repair beside
the test, so the researcher sees what was refused. Usage: s2_fix_base.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:100], s.count(a)); s = s.replace(a, b)
rep('''    def repair_user(hid, test, n, who, feedback, reserved=0):''', '''    def repair_user(hid, test, n, who, feedback, reserved=0, refused=None):''')
rep('''f"YOUR HYPOTHESIS {hid}: {flat(h.get('text'))}\\n\\nTHE TEST AS PROPOSED:\\n{rules}  simulations:\\n{runs}\\nWHY IT WAS SENT BACK ({who}): {flat(feedback)}\\n\\n"''',
    '''f"YOUR HYPOTHESIS {hid}: {flat(h.get('text'))}\\n\\nTHE TEST AS PROPOSED:\\n{rules}  simulations:\\n{runs}\\n"
                + (f"YOUR LAST REPAIR, WHICH THE HARNESS COULD NOT USE (the test above stands until a repair is accepted):\\n" + "".join(f"  decision rule: {flat(d.get('decision_rule'))}\\n" for d in refused.get("decision_rules") or [])
                   + "  simulations:\\n" + "".join(f"  {r.get('label')} {{{', '.join(f'{k}={v}' for k, v in (r.get('params') or {}).items())}}}" + (f"; network changed: {edits_say(edits_of(r))}" if edits_of(r) else "") + "\\n" for r in refused.get("runs") or [] if isinstance(r, dict)) if refused else "")
                + f"WHY IT WAS SENT BACK ({who}): {flat(feedback)}\\n\\n"''')
rep('''        n, parent, earlier = 1, gid, [(1, "the supervisor", rev["feedback"])]
        while True:
            who, feedback = earlier[-1][1], earlier[-1][2]
            user = repair_user(hid, test, n + 1, who, feedback, reserved)''',
    '''        n, parent, earlier, refused = 1, gid, [(1, "the supervisor", rev["feedback"])], None
        while True:
            who, feedback = earlier[-1][1], earlier[-1][2]
            user = repair_user(hid, test, n + 1, who, feedback, reserved, refused)''')
rep('''                earlier.append((n, "the harness", problem))
                parent, test = gid, t2
                continue''',
    '''                earlier.append((n, "the harness", problem))
                parent, refused = gid, t2   # the test stays the last one the harness accepted: a refused repair is not what the next is read against
                continue''')
rep('''            earlier.append((n, "the supervisor", rev["feedback"]))
            parent, test = gid, t2''', '''            earlier.append((n, "the supervisor", rev["feedback"]))
            parent, test, refused = gid, t2, None''')
p.write_text(s); print("patched", p)
