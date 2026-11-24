# v2, stage 2b: the lines about a ruling
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## B12: a ruling's line names a question that could not be told

`harness/loop.py`

before:

```
("" if b.get("fair") else " Not a fair test: " + "; ".join(f"{q.capitalize()} failed: {flat(qs[q]['why'])}" for q in qs if qs[q]["box"] == "fail") + ".")
```

after:

```
("" if b.get("fair") else " Not a fair test: " + "; ".join(f"{q.capitalize()} {'could not be told' if qs[q]['box'] == CANNOT else 'failed'}: {flat(qs[q]['why'])}" for q in qs if qs[q]["box"] != "pass") + ".")
```

## item 4: a ruling's line says when it refutes the hypothesis and not the guess

`harness/loop.py`

before:

```
("." if b.get("fair") and not b.get("fits_contradicted") else " (not applied: " + ("its boxes contradicted each other" if b.get("fits_contradicted") else "the test was not fair") + ").") if b.get("fits") else "")
```

after:

```
("." if b.get("fair") and not b.get("fits_contradicted") else " (not applied: " + ("its boxes contradicted each other" if b.get("fits_contradicted") else "the test was not fair") + ").") if b.get("fits") else "")
                + (" The review had not found that the hypothesis follows from its guess: this ruling is about the hypothesis, and the guess is not refuted by it." if b.get("follows") not in (None, "pass") and b.get("result") == "refuted" else "")
```

## item 4: what the researcher is told about when a guess is refuted

`harness/loop.py`

before:

```
a guess that does not fit the result of a fair test is refuted: no hypothesis comes from it, a new guess may revise it.
```

after:

```
a guess is refuted when a fair test of a hypothesis that follows from it fails, or when the supervisor finds that it does not fit a fair test's result: no new hypothesis comes from it, a new guess may revise it. A failed hypothesis that did not follow from its guess refutes only itself.
```
