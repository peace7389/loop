# v2, stage 9: the operator's decisions of 2026-11-25
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## a review that cannot be read: asked once more, then cannot tell in every box (the note and the feedback the researcher reads)

`harness/loop.py`

before:

```
def _review3(model, d, user, hid, rules, round_no, ask_fn, pre, pre_saw):
```

after:

```
UNREAD_REVIEW = "the supervisor's review of this test could not be read"   # v2: the reason of every box of a review that could not be read twice


def review_or_cannot(note, model, brief, ledger, ex, hid, **k):
    """review_design, and what happens when its answer cannot be read (v2, the operator's decision of 2026-11-25): it is asked for once more, alone;
    unreadable again, the review counts as "cannot tell" in every box, so the test is sent back as any box that could not be told sends it back
    (a test that ran unreviewed had no answer to Follows, and its guess could be refuted through it). note(text) writes the ledger's note. A session
    without competitors has no boxes: the error is raised again, and its test is run unreviewed as before."""
    try:
        return review_design(model, brief, ledger, ex, hid, **k)
    except (ValueError, KeyError, TypeError) as e:
        if not COMP["on"]:
            raise
        note(f"the supervisor's review of the test of {hid} could not be read ({type(e).__name__}): it is asked for once more")
    again = {**k, "pre": None, "pre_saw": None}
    try:
        return review_design(model, brief, ledger, ex, hid, **again)
    except (ValueError, KeyError, TypeError) as e:
        note(f"the supervisor's review of the test of {hid} could not be read a second time ({type(e).__name__}): it counts as \"cannot tell\" in every box, and the test is sent back")
    d = {"reads": "", **{q + "_why": UNREAD_REVIEW for q in REVIEW_QS}, **{q: CANNOT for q in REVIEW_QS}, "if_tested": "cannot tell", "if_competitor": "cannot tell", "missing": "",
         "feedback": UNREAD_REVIEW + ", twice, so no box could be told. Send the test again, as it is or changed."}
    rev, saw = review_design(model, brief, ledger, ex, hid, **{**again, "pre": d, "pre_saw": ""})
    rev["unread"] = True
    return rev, saw


def _review3(model, d, user, hid, rules, round_no, ask_fn, pre, pre_saw):
```

## no text changed: the first round of a review goes through it

`harness/loop.py`

before:

```
                rev, saw = review_design(model, brief, ledger, ex, hid, pre=pre[0] if pre else None, pre_saw=pre[1] if pre else None)
```

after:

```
                rev, saw = review_or_cannot(lambda text, hid=hid: append(ledger, turn, "note", hid, {"text": text}), model, brief, ledger, ex, hid, pre=pre[0] if pre else None, pre_saw=pre[1] if pre else None)
```

## no text changed: so does the review of a repaired test

`harness/loop.py`

before:

```
                rev, saw = review_design(model, brief, ledger, t2, hid, round_no=n, earlier=earlier)
```

after:

```
                rev, saw = review_or_cannot(lambda text, rid=rid: append(ledger, turn, "note", rid, {"text": text}), model, brief, ledger, t2, hid, round_no=n, earlier=earlier)
```

## no text changed: the fairness figures count the reviews that could not be read (each also counts as four boxes that could not be told)

`harness/session_figures.py`

before:

```
    return {"chain_refusals": chain, "cannot_tell": comp.get("cannot_tell"), "approved_by_round": {str(k): by_round[k] for k in sorted(by_round)},
```

after:

```
    return {"chain_refusals": chain, "cannot_tell": comp.get("cannot_tell"), "unread_reviews": sum(1 for r in rv if r["body"].get("unread")),
            "approved_by_round": {str(k): by_round[k] for k in sorted(by_round)},
```

## no text changed: its description

`harness/session_figures.py`

before:

```
      "cannot_tell": boxes answered "cannot tell" at the reviews of every round and at the rulings (None: a session before v2);
```

after:

```
      "cannot_tell": boxes answered "cannot tell" at the reviews of every round and at the rulings (None: a session before v2);
      "unread_reviews": reviews that could not be read twice and so count as "cannot tell" in every box (they are among the boxes above);
```

## a new brief: after_fix with the choices of tcp.type in alphabetical order

`briefs/after_fix-2.json`

before:

```
["TcpCubic", "TcpNewReno", "TcpLinuxReno", "TcpBbr", "TcpVegas", "TcpBic"]
```

after:

```
["TcpBbr", "TcpBic", "TcpCubic", "TcpLinuxReno", "TcpNewReno", "TcpVegas"]
```

## and its TCP flow locked (what may not be removed or replaced)

`briefs/after_fix-2.json`

before:

```
["host:sender", "flow:udp", "link:l1", "host:receiver"]
```

after:

```
["host:sender", "flow:udp", "link:l1", "host:receiver", "flow:tcp"]
```
