# v2, stage 2c: the ruling's record
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## item 4, B4, B12: the ruling's record holds the review's Follows, the questions that changed, and what could not be told

`harness/loop.py`

before:

```
for k in ("questions", "fits", "competes_with", "fits_again", "fits_contradicted", "misses") if ruling.get(k)}
```

after:

```
for k in ("questions", "fits", "competes_with", "fits_again", "fits_contradicted", "misses", "follows", "changed", "cannot_tell") if ruling.get(k)}
```
