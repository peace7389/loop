# after v2.1: a cited review of a test shows its feedback, not "None"
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## a cited review of a test showed "None" where its reason belongs: it shows the feedback the review gave (the audit of s065)

`harness/loop.py`

before:

```
review of {b.get('for') or 'a guess'}: {b.get('decision')}. {flat(b.get('because'))}" + (f" The rival it named
```

after:

```
review of {b.get('for') or 'a guess'}: {b.get('decision')}." + (f" {flat(b['because'])}" if b.get("because") is not None else f" {flat(b['feedback'])}" if b.get("feedback") else "") + (f" The rival it named
```
