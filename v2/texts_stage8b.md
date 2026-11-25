# v2, stage 8b: what the checks of the supervisor's wrong answers found
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## no text changed: a missing reason of a review's box is recorded as empty, not as the word None

`harness/loop.py`

before:

```
    rev = {"reads": flat(d.get("reads")), **{q + "_why": flat(d.get(q + "_why")) for q in REVIEW_QS}, **{q: box(d.get(q)) for q in REVIEW_QS},
```

after:

```
    rev = {"reads": flat(d.get("reads")), **{q + "_why": flat(d.get(q + "_why") or "") for q in REVIEW_QS}, **{q: box(d.get(q)) for q in REVIEW_QS},
```

## no text changed: the same at a ruling

`harness/loop.py`

before:

```
    qs = {q: {"why": flat(d.get(q + "_why")), "box": box(d.get(q))} for q in RULING_QS}
```

after:

```
    qs = {q: {"why": flat(d.get(q + "_why") or ""), "box": box(d.get(q))} for q in RULING_QS}
```

## what the researcher is told of a box without a reason (the review)

`harness/loop.py`

before:

```
        rev["feedback"] = ("; ".join(f"{q.capitalize()} {'could not be told' if rev[q] == CANNOT else 'failed'}: {rev[q + '_why']}" for q in failed) if failed else
```

after:

```
        rev["feedback"] = ("; ".join(f"{q.capitalize()} {'could not be told' if rev[q] == CANNOT else 'failed'}: {rev[q + '_why'] or NO_REASON}" for q in failed) if failed else
```

## what the researcher is told of a box without a reason (the ruling's line in the ledger)

`harness/loop.py`

before:

```
"; ".join(f"{q.capitalize()} {'could not be told' if qs[q]['box'] == CANNOT else 'failed'}: {flat(qs[q]['why'])}" for q in qs if qs[q]["box"] != "pass")
```

after:

```
"; ".join(f"{q.capitalize()} {'could not be told' if qs[q]['box'] == CANNOT else 'failed'}: {flat(qs[q]['why']) or NO_REASON}" for q in qs if qs[q]["box"] != "pass")
```

## the words for a box without a reason

`harness/loop.py`

before:

```
def supervise(model, user, schema, max_tokens=9000):
```

after:

```
NO_REASON = "(the supervisor gave no reason)"   # a box that failed or could not be told, with its reason left empty


def supervise(model, user, schema, max_tokens=9000):
```

## no text changed: an answer that is JSON but no object is an answer that cannot be read

`harness/loop.py`

before:

```
    try:
        return json.loads(content)
    except ValueError:
        d = findings_cut(content) if "findings" in (schema.get("properties") or {}) else None
```

after:

```
    try:
        d = json.loads(content)
        if not isinstance(d, dict):
            raise ValueError("the supervisor's answer is not a JSON object")
        return d
    except ValueError:
        d = findings_cut(content) if "findings" in (schema.get("properties") or {}) else None
```
