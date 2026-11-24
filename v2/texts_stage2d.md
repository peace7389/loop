# v2, stage 2d: a refusal without an example value; the mark of a refuted guess says how it was refuted
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## A2/A7: the refusal of a new link without a rate names no value

`harness/network.py`

before:

```
raise ValueError(f"{n}: a new link states its rate (for example 1Gbps)")
```

after:

```
raise ValueError(f"{n}: a new link states its rate")
```

## A9 / item 4: the standing of a refuted guess keeps how it was refuted

`harness/loop.py`

before:

```
                st[y] = {**st[y], "worth": "refuted", "by": v, "idle": False}
```

after:

```
                hid = next((r["body"].get("for") for r in ledger if r["id"] == v), None)   # the hypothesis that ruling is about: this guess's own, or another guess's (then this one was its competitor)
                own = any(r["type"] == "hypothesis" and r["id"] == hid and r["body"].get("from_why") == y for r in ledger)
                st[y] = {**st[y], "worth": "refuted", "by": v, "through": "own" if own else "fit", "idle": False}
```

## A9 / item 4: the mark of a refuted guess says how it was refuted (through its own hypothesis, or as a competitor that does not fit)

`harness/loop.py`

before:

```
(f" by the ruling {w['by']} on a hypothesis that follows from it: no new hypothesis is accepted from it"
```

after:

```
(f" by the ruling {w['by']}" + (", which found that it does not fit the result of a fair test" if w.get("through") == "fit" else " on a hypothesis that follows from it") + ": no new hypothesis is accepted from it"
```

## the code's description of the ruling, as stage 2 left it (no text an agent reads)

`harness/loop.py`

before:

```
    """The ruling with the three questions (stage 5): (ruling, what it was shown). fair is all three passing; the result must fit the checks and the fits
    must fit the result of a fair test (one follow-up question; still contradictory, the fits are kept but refute nothing). A question the review passed
    and the ruling fails is a miss when it was foreseeable, else found by the result."""
```

after:

```
    """The ruling with the three questions (stage 5; v2): (ruling, what it was shown). fair is all three passing ("cannot tell" is not passing); the
    result must fit the checks. Each guess is said to fit, not to fit, or "cannot tell", by itself: no answer is asked for a second time (v2, B1). A
    question the review passed and the ruling does not is kept as "changed": the harness compares the two sets of boxes itself (v2, B4)."""
```
