"""After the deploy, part 6 (s056 turn 8, 2026-11-23 03:40): two refusals of the harness gave advice that led the researcher wrong.
1. A rule of 4 comparisons was told "Decide the hypothesis by the one comparison its guess predicts"; H11 claims two things (lower inflight AND higher
   RTO), the repair kept one, and the supervisor held the test because it does not test the whole claim (Consistent). The advice now says to keep
   every part of the claim and leave further settings to a later test.
2. A change that asks for more than the brief allows (3 flows; at most 2) was answered with "A change written correctly for this network, for
   example: [remove the queue, add a scheduler]": the change was written correctly, and the example offers an unrelated change. The example is now
   given only when the change is written wrongly; a limit says that the change is written correctly and what to do.
python3 -I p6_advice.py LOOP_PY"""
import sys
from pathlib import Path
f = Path(sys.argv[1])
s = f.read_text()

def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)

rep('''    return (f"the decision rule for {r.get('for')} makes {k} comparisons, and a rule makes at most {COMPARISONS_MOST}: a rule that needs more asks more than one "
            "question. Decide the hypothesis by the one comparison its guess predicts, and leave the rest to a later test") if k > COMPARISONS_MOST else None''',
    '''    return (f"the decision rule for {r.get('for')} makes {k} comparisons, and a rule makes at most {COMPARISONS_MOST}: keep the comparisons that decide what "
            f"{r.get('for')} claims, every part of it, and leave the rest, such as further settings, to a later test (a claim that needs more than "
            f"{COMPARISONS_MOST} comparisons is more than one claim)") if k > COMPARISONS_MOST else None''')

rep('''    if not bad:
        return None
    ok = change_example(b) if example else None
    return "; ".join(bad) + (f". A change written correctly for this network, for example: {json.dumps(ok)}" if ok else "")''',
    '''    if not bad:
        return None
    if all(any(w in x for w in LIMIT_WORDS) for x in bad):   # written correctly, asks for more than the brief allows (s056 H10: 3 flows)
        more = any("at most" in x for x in bad)
        return "; ".join(bad) + ". The change is written correctly, but this brief does not allow it" + (": change a part the network has instead of adding one" if more else "")
    ok = change_example(b) if example else None
    return "; ".join(bad) + (f". A change written correctly for this network, for example: {json.dumps(ok)}" if ok else "")''')

rep('''def structure_problem(edits, brief=None, example=True):''',
    '''LIMIT_WORDS = ("this brief allows at most", "a network holds at most", "may not be removed (the operator keeps it)", "which this network would not have")   # network.py's limits


def structure_problem(edits, brief=None, example=True):''')
f.write_text(s)
print("p6 applied to", f)
