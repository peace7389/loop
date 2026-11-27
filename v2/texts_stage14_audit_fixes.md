# after v2.1 (2026-11-27): what the fairness audits of s063 and s065 found
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## 1. a test approved in the batched first review is reviewed again when a guess it names was restated in the same turn (code; no text)

`harness/loop.py`

before:

```
"")), None)   # its answer in the batched first review
            try:
                if pre is None:
                    stage("design", hid, 1)
                rev, saw = review_or_cannot(lambda text, hid=hid: append(ledger, turn, "note", hid, {"text": text}), model, brief, ledger, ex, hid, pre=pre[0] if pre else None, pre_saw=pre[1] if pre else None)

```

after:

```
"")), None)   # its answer in the batched first review
            moved = restated_since(ledger, turn, ex, hid) if pre is not None else []
            if moved:   # 2026-11-27 (s065 H3): that answer read a guess as first stated, and the guess was restated in this turn: the test is reviewed again, alone
                pre = None
            try:
                if pre is None:
                    stage("design", hid, 1)
                rev, saw = review_or_cannot(lambda text, hid=hid: append(ledger, turn, "note", hid, {"text": text}), model, brief, ledger, ex, hid, pre=pre[0] if pre else None, pre_saw=pre[1] if pre else None)
                if moved:
                    rev["after_restatement"] = moved

```

## 1, 2. the two helpers (code; the line of item 2 is the text the supervisor is shown)

`harness/loop.py`

before:

```
def test_key(ex, hid, h_text):
```

after:

```
def restated_since(ledger, turn, ex, hid):
    """The guesses a test names (its hypothesis's own, and those its rules compete with) that were restated in this turn with other words: the
    batched first review read them as first stated (2026-11-27, s065 H3: the approval stood against a competitor that had changed)."""
    flat = lambda v: " ".join(str(v).split())
    h = next((r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), {})
    named = {h.get("from_why")} | {d.get("competes_with") for d in ex.get("decision_rules") or [] if d.get("for") == hid}
    return sorted(r["id"] for r in ledger if r["type"] == "why" and r.get("turn") == turn and r["id"] in named and isinstance(r["body"].get("restated"), dict)
                  and flat((r["body"]["restated"].get("was") or {}).get("guess")) != flat(r["body"].get("guess")))


def values_before(ledger, xid, checks):
    """Which of the values a test's rules compare stood in the records before the test ran, as a fact for the ruling (2026-11-27, s065 H8: the test's
    own table, which carries the run ids of simulations not run again, was taken for earlier records). A value stood before when its simulation
    was not run again (same_as) and the value is not a measurement this test took of it (own). Returns the line, or "" when nothing can be told."""
    sims = {r["body"].get("label"): r["body"] for r in ledger if r["type"] == "simulation" and r.get("parent") == xid}
    new, old = [], []
    for c in checks:
        for name, label in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)@([A-Za-z0-9_]+)", str(c["body"].get("decision_rule"))):
            s = sims.get(label)
            if s is None:
                continue
            before = bool(s.get("same_as")) and name not in (s.get("own") or [])
            term = f"{name}@{label}" + (f" (the result of {s['same_as']})" if before else "")
            if term not in new + old:
                (old if before else new).append(term)
    return f"OF THE VALUES THESE RULES COMPARE (a fact): first measured by this test: {', '.join(new) or 'none'}; in the records before it ran: {', '.join(old) or 'none'}.\n\n" if new or old else ""


def test_key(ex, hid, h_text):
```

## 2. the ruling is told which compared values were first measured by the test and which stood in the records before it ran

`harness/loop.py`

before:

```
THE HARNESS'S CHECKS (facts):\n{lines}\n\n" + _test_terms(ledger, xid, hid) + "\n" + (f"Before the simulations
```

after:

```
THE HARNESS'S CHECKS (facts):\n{lines}\n\n" + values_before(ledger, xid, checks) + _test_terms(ledger, xid, hid) + "\n" + (f"Before the simulations
```

## 2. the same line at the supervisor's second look after an objection

`harness/loop.py`

before:

```
f"THE HARNESS'S CHECKS (facts):\n{lines}\n\n" + (_test_terms(ledger, xid, hid) if xid else "")
```

after:

```
f"THE HARNESS'S CHECKS (facts):\n{lines}\n\n" + (values_before(ledger, xid, checks) + _test_terms(ledger, xid, hid) if xid else "")
```

## 3. the request for a repair says that a repair cannot change the hypothesis's sentence

`harness/loop.py`

before:

```
"Repair this test only. decision_rule: the comparison
```

after:

```
"Repair this test only. The hypothesis's sentence and its guess stay as they are: a repair changes the rule, the guess it competes with and the simulations. If the objection is to the "
                "sentence itself, no repair meets it: send the test as it stands, and if it is then not run, drop the hypothesis in your next reply and state a new one. decision_rule: the comparison
```

## 4a. in a test a simulation no rule names is not run (it stood only in the refusal and in the request for a repair)

`harness/loop.py`

before:

```
tests lists the open hypotheses it tests; decision_rules has at least one rule for each. kind "explore"
```

after:

```
tests lists the open hypotheses it tests; decision_rules has at least one rule for each, and a simulation no rule names is not run. kind "explore"
```

## 4c. a rule names simulations of its own experiment (an earlier one is listed again, at no cost: the text says so already)

`harness/loop.py`

before:

```
measure@label (an output, or a measurement this experiment defines, in the simulation with that label)
```

after:

```
measure@label (an output, or a measurement this experiment defines, in this experiment's simulation with that label)
```

## 4c. the same in the instructions of the arm with stated needs

`harness/prompt.txt`

before:

```
measure@label, the value of an output in the simulation with that label
```

after:

```
measure@label, the value of an output in this experiment's simulation with that label
```

## 4. room for 4a and 4c in the 10,000 characters: a list of example ids leaves (part 3 of the same text shows the ids' forms)

`harness/loop.py`

before:

```
the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).
```

after:

```
the ids of the checks, rulings, evidence tables and readings that support it).
```

## 4. room for 4a and 4c: the second list of example ids leaves

`harness/loop.py`

before:

```
- findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings, for example E2, C3, T7) text
```

after:

```
- findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings) text
```

## 4b. a queue is added only on a side that has none (the paragraph on changes of the network; outside the 10,000 characters)

`harness/loop.py`

before:

```
on (the host whose sending side of the link it is) and kind (state it). A new queue holds 100 packets, and a link may have a queue on each of its two sides.
```

after:

```
on (the host whose sending side of the link it is) and kind (state it). A queue is added only on a side that has none: to put another kind where one stands, remove that one first, in the same list. A new queue holds 100 packets, and a link may have a queue on each of its two sides.
```

## 5. the tool measure says which samples a window holds (a network brief)

`harness/network.py`

before:

```
t_from, t_to: the window in seconds (left out: the measured seconds, from 2 s to the end)")
```

after:

```
t_from, t_to: the window in seconds (left out: the measured seconds, from 2 s to the end); a sample at time t stands for the step that ends at t, so a window holds the samples after t_from, up to t_to (first is the earliest of them; rate also takes the sample at t_from, the count it starts from)")
```

## 5. the same in the tool list of a two-hosts brief

`harness/manifest.json`

before:

```
t_from, t_to: the window in seconds (left out: the measured seconds, from 2 s to the end)",
```

after:

```
t_from, t_to: the window in seconds (left out: the measured seconds, from 2 s to the end); a sample at time t stands for the step that ends at t, so a window holds the samples after t_from, up to t_to (first is the earliest of them; rate also takes the sample at t_from, the count it starts from)",
```

## 5. the tool series says on which side of the measured seconds the sample at t = 2 lies (a network brief)

`harness/network.py`

before:

```
(at most 100 rows; the measured seconds begin at t = 2)")
```

after:

```
(at most 100 rows; the sample at t = 2 closes the second that is not measured, the measured seconds are the samples after it)")
```

## 5. the same in the tool list of a two-hosts brief

`harness/manifest.json`

before:

```
the measured seconds begin at t = 2)",
```

after:

```
the sample at t = 2 closes the second that is not measured, the measured seconds are the samples after it)",
```
