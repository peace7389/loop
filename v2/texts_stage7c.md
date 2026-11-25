# v2, stage 7c: two more sentences the text audit marked in v2's own texts
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## the line on a new link: no example rate (found by the text audit)

`harness/loop.py`

before:

```
   - do add_link: id, from and to (the two hosts it joins) and rate (state it, for example 1Gbps).
```

after:

```
   - do add_link: id, from and to (the two hosts it joins) and rate (state it, written as the brief writes rates).
```

## no text changed: the same line, where a brief caps a new link (its cap replaces the words as before)

`harness/loop.py`

before:

```
    old, old2 = "rate (state it, for example 1Gbps)", "A new link has a one-way delay of 50us,"
```

after:

```
    old, old2 = "rate (state it, written as the brief writes rates)", "A new link has a one-way delay of 50us,"
```

## the kinds of queue: no kind named before the list or apart from it (found by the text audit)

`harness/loop.py`

before:

```
The kinds, each ns-3's queue disc of that name except the scheduler: codel:
```

after:

```
The kinds: codel:
```

## no text changed: the text audit reads the list in its new form

`harness/text_audit.py`

before:

```
m = re.search(r"The kinds,[^:]*:(.*?)(?:\n|$)", text)
```

after:

```
m = re.search(r"The kinds[^:]*:(.*?)(?:\n|$)", text)
```
