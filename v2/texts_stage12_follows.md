# After v2.1: Follows in two parts with its record; the crash of s064
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## no text changed: the refusal of a guess finds the sentence of every reason the supervisor can give (s064 stopped on no_cause)

`harness/loop.py`

before:

```
return (f"the supervisor does not accept this guess as it stands: {GROUNDS[g['defect']]}. The records show:
```

after:

```
return (f"the supervisor does not accept this guess as it stands: {GROUNDS_COMP.get(g['defect']) or g['defect']}. The records show:
```

## Follows, as the review asks it: two parts

`harness/loop.py`

before:

```
QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? Pass if someone who held the guess to be true would expect this result, in its direction and rough size; a threshold the hypothesis states follows if the guess expects the result beyond it. Fail if the guess leaves the direction open, or would expect otherwise",
```

after:

```
QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? It has two parts. First, strictly: the hypothesis is about a measure the guess speaks about, and in the direction the guess requires; if not, fail. Second, the number: a threshold or a size the hypothesis states is the researcher's choice; fail for it only if it lies clearly outside what the guess could give, and say why",
```

## Follows, the fields of the review's answer: the sentence, the box, and the part that failed

`harness/loop.py`

before:

```
    "follows_why": {"type": "string", "description": "one sentence: would someone who held the tested guess to be true expect this result, in its direction and rough size (a stated threshold: beyond it), and why (or what is missing to tell)"},
    "follows": {**BOX, "description": "pass: the hypothesis follows from the guess; fail: the guess leaves it open or would expect otherwise; cannot tell: the sentence says what is missing"},
```

after:

```
    "follows_why": {"type": "string", "description": "one sentence: is the hypothesis about a measure the guess speaks about, in the direction the guess requires; and, if it states a number, does that number lie clearly outside what the guess could give (then say why)? Or what is missing to tell"},
    "follows": {**BOX, "description": "pass: both parts hold; fail: one of them does not; cannot tell: the sentence says what is missing"},
    "follows_part": {"type": "string", "enum": ["none"] + list(FOLLOWS_PARTS), "description": "the part of Follows that did not hold: measure or direction (the hypothesis is not about a measure the guess speaks about, or not in the direction the guess requires), or number (its number lies clearly outside what the guess could give); none when Follows passes or cannot be told"},
```

## no text changed: the part that failed is a required field of the review's answer

`harness/loop.py`

before:

```
REVIEW3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reads", "follows_why", "follows", "honest_why",
```

after:

```
FOLLOWS_PARTS = ("measure or direction", "number")   # the two parts of Follows; a review's record keeps which one failed (follows_part)
REVIEW3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reads", "follows_why", "follows", "follows_part", "honest_why",
```

## no text changed: the review's record keeps the part of Follows that failed

`harness/loop.py`

before:

```
           "competes_with": next((x.get("competes_with") for x in rules if x.get("competes_with")), None), "defect": "none"}
    def clash_of(r):   # what contradicts what, or None
```

after:

```
           "competes_with": next((x.get("competes_with") for x in rules if x.get("competes_with")), None), "defect": "none"}
    if rev["follows"] == "fail":   # which of the two parts of Follows failed, as the supervisor said it (the operator, 2026-11-25: "Record which part failed")
        rev["follows_part"] = d.get("follows_part") if d.get("follows_part") in FOLLOWS_PARTS else "not said"
    def clash_of(r):   # what contradicts what, or None
```
