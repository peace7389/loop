# v2.1: Honest and Follows reworded (the operator, after s063)
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## Follows, as the review asks it (v2.1)

`harness/loop.py`

before:

```
QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? Pass only if someone who held the guess to be true would have to expect what the hypothesis says; fail if the guess leaves it open, or would expect otherwise",
```

after:

```
QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? Pass if someone who held the guess to be true would expect this result, in its direction and rough size; a threshold the hypothesis states follows if the guess expects the result beyond it. Fail if the guess leaves the direction open, or would expect otherwise",
```

## Honest, as the review asks it (v2.1)

`harness/loop.py`

before:

```
             "honest": "can the test fail? Pass only if no value its rule compares, and no series such a value is computed from, already stands in the records you are shown, and its threshold is not one that almost any result passes; otherwise fail",
```

after:

```
             "honest": "can the test fail? Fail only if every value its rule compares already stands in the records you are shown (or is computed from a series that stands there), or if its threshold is one that almost any result passes; a rule that compares a new result with one already measured can fail. Otherwise pass",
```

## Honest, as the ruling asks it with the result in hand (v2.1)

`harness/loop.py`

before:

```
QUESTIONS_AFTER = {"honest": "could the test have failed? Pass only if, before it ran, no value its rule compares stood in the records, and its threshold is not one that almost any result passes; otherwise fail",
```

after:

```
QUESTIONS_AFTER = {"honest": "could the test have failed? Fail only if, before it ran, every value its rule compares stood in the records, or if its threshold is one that almost any result passes; otherwise pass",
```

## Follows, the field of the review's answer (v2.1)

`harness/loop.py`

before:

```
    "follows_why": {"type": "string", "description": "one sentence: would someone who held the tested guess to be true have to expect what the hypothesis says, and why (or what is missing to tell)"},
```

after:

```
    "follows_why": {"type": "string", "description": "one sentence: would someone who held the tested guess to be true expect this result, in its direction and rough size (a stated threshold: beyond it), and why (or what is missing to tell)"},
```

## Honest, the field of the review's answer (v2.1)

`harness/loop.py`

before:

```
    "honest_why": {"type": "string", "description": "one sentence, with record ids: can the test fail? (no value its rule compares, and no series it is computed from, already in the records shown; a threshold that not almost any result passes)"},
```

after:

```
    "honest_why": {"type": "string", "description": "one sentence, with record ids: can the test fail? (it cannot only if every value its rule compares, or the series each is computed from, is already in the records shown, or if its threshold is one almost any result passes)"},
```

## the supervisor's instructions on a test that runs no new simulation (v2.1)

`harness/loop.py`

before:

```
That costs nothing and is a proper test as long as the value its rule compares, and the series it is computed from, are not already "
              "in the records you are shown.
```

after:

```
That costs nothing and is a proper test as long as not every value its rule compares, with the series it is computed from, is already "
              "in the records you are shown.
```
