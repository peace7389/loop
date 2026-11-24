"""v2, stage 2d: three corrections found while bringing the harness checks in line.
1. The refusal of a new link without a rate named a value ("for example 1Gbps"): an example of a value is a pointer (the audit's A2, A7).
2. The mark of a refuted guess said "on a hypothesis that follows from it" for every refuted guess. A competing guess is refuted another way: the
   supervisor found that it does not fit the result of a fair test of another guess's hypothesis. The mark now says which of the two it was.
3. The description of the ruling in the code still spoke of the second question and of "foreseeable", which stage 2 removed."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done

sub("harness/network.py", 'raise ValueError(f"{n}: a new link states its rate (for example 1Gbps)")', 'raise ValueError(f"{n}: a new link states its rate")',
    "A2/A7: the refusal of a new link without a rate names no value")

sub("harness/loop.py", """                st[y] = {**st[y], "worth": "refuted", "by": v, "idle": False}""",
    """                hid = next((r["body"].get("for") for r in ledger if r["id"] == v), None)   # the hypothesis that ruling is about: this guess's own, or another guess's (then this one was its competitor)
                own = any(r["type"] == "hypothesis" and r["id"] == hid and r["body"].get("from_why") == y for r in ledger)
                st[y] = {**st[y], "worth": "refuted", "by": v, "through": "own" if own else "fit", "idle": False}""",
    "A9 / item 4: the standing of a refuted guess keeps how it was refuted")

sub("harness/loop.py", """(f" by the ruling {w['by']} on a hypothesis that follows from it: no new hypothesis is accepted from it\"""",
    """(f" by the ruling {w['by']}" + (", which found that it does not fit the result of a fair test" if w.get("through") == "fit" else " on a hypothesis that follows from it") + ": no new hypothesis is accepted from it\"""",
    "A9 / item 4: the mark of a refuted guess says how it was refuted (through its own hypothesis, or as a competitor that does not fit)")

sub("harness/loop.py", '''    """The ruling with the three questions (stage 5): (ruling, what it was shown). fair is all three passing; the result must fit the checks and the fits
    must fit the result of a fair test (one follow-up question; still contradictory, the fits are kept but refute nothing). A question the review passed
    and the ruling fails is a miss when it was foreseeable, else found by the result."""''',
    '''    """The ruling with the three questions (stage 5; v2): (ruling, what it was shown). fair is all three passing ("cannot tell" is not passing); the
    result must fit the checks. Each guess is said to fit, not to fit, or "cannot tell", by itself: no answer is asked for a second time (v2, B1). A
    question the review passed and the ruling does not is kept as "changed": the harness compares the two sets of boxes itself (v2, B4)."""''',
    "the code's description of the ruling, as stage 2 left it (no text an agent reads)")
done("stage2d", "v2, stage 2d: a refusal without an example value; the mark of a refuted guess says how it was refuted")
