"""After the deploy, part 9 (s057 turn 3, 2026-11-23 04:42): the researcher numbered its new guesses from Y13 where the harness numbers them from Y10
(the ledger's last guess was Y9): its hypothesis came "from Y16" and was refused, and the test of it with it; the turn ran no simulation. The ids a
reply's new guesses and hypotheses will get were said only in a refusal, after the fact. Now every reply request of the arms with guesses ends by
saying them: the guesses of this answer are recorded as Y10, Y11, ..., its hypotheses as H4, H5, ..., in the order written.
python3 -I p9_ids.py LOOP_PY"""
import sys
from pathlib import Path
f = Path(sys.argv[1])
s = f.read_text()

def rep(a, b):
    global s
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)

rep('''                         "too, and you are asked once more in this turn." if stay < CONTINUES else f"this is the last reply of this turn, so {step_now} "
                         "(what this reply asks for is answered, and shown to you in the next turn)."))''',
    '''                         "too, and you are asked once more in this turn." if stay < CONTINUES else f"this is the last reply of this turn, so {step_now} "
                         "(what this reply asks for is answered, and shown to you in the next turn)."))
            if arm != "plain" and mode in (None, "free"):   # the ids a reply's new parts get, said before it writes them (part 9: s057 turn 3 numbered its guesses from Y13, not Y10)
                n_y_now, n_h_now = sum(r["type"] == "why" for r in ledger), sum(r["type"] == "hypothesis" for r in ledger)
                user += (f"\\n\\nNEW IDS: the {'guesses' if arm == 'supervised' else 'whys'} you write in this answer are recorded as Y{n_y_now + 1}, Y{n_y_now + 2}, ... and your new hypotheses "
                         f"as H{n_h_now + 1}, H{n_h_now + 2}, ..., in the order you write them: name them by these ids (in from_why, competes_with, revises, tests and decision rules).")''')
f.write_text(s)
print("p9 applied to", f)
