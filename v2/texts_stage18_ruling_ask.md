# after v2.2.1: the ruling's request carries the paragraph of the three questions again
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## the ruling's request carries the paragraph of the three questions again (stage 16 had left the older single-question paragraph in its place)

`harness/loop.py`

before:

```
    i, j = user.find("What does this test show about the hypothesis?"), user.find("\n\nTHE FINDINGS SO FAR:")
    if 0 <= i < j:   # the single-question paragraph and its defects give way to the three questions
        user = user[:i] + RULING3_ASK + user[j:]
```

after:

```
    i, j = user.find("What does this test show about the hypothesis?"), user.find("\n\nTHE FINDINGS SO FAR:")
    if j < 0:   # since stage 16 the ruling's request has no findings: the paragraph runs to the end (2026-11-27: it was left in place, and the three questions' paragraph left out)
        j = len(user)
    if 0 <= i < j:   # the single-question paragraph and its defects give way to the three questions
        user = user[:i] + RULING3_ASK + user[j:]
```
