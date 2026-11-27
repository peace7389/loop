# after v2.1 (2026-11-27): faults found by the review of the harness, part 1 (the review of a test, its repairs, what the supervisor is shown)
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## C3. the line of facts at the ruling: four groups, each true of the records (it was two, and wrong for a simulation shared within a turn and for a measurement taken before)

`harness/loop.py`

before:

```
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

```

after:

```
    was not run again (same_as) and the value is not a measurement this test took of it (own). Returns the line, or "" when nothing can be told.
    The review of 2026-11-27 (C3): a rule is fixed before any simulation of its turn runs, so a simulation another test of the same turn ran first
    was not known to it; and a measurement an earlier experiment took of the same simulation was. Four groups, by the records: (1) of a simulation
    this test ran; (2) of a simulation run earlier in the same turn; (3) a measurement this test took of a simulation of an earlier turn, which
    no earlier simulation record holds (a reading may have shown the series: the readings say); (4) held by a simulation record of an earlier turn."""
    turn = next((r.get("turn") for r in ledger if r["id"] == xid), None)
    mine = [(i, r) for i, r in enumerate(ledger) if r["type"] == "simulation" and r.get("parent") == xid]
    sims = {r["body"].get("label"): (i, r["body"]) for i, r in mine}
    groups = {1: [], 2: [], 3: [], 4: []}
    for c in checks:
        for name, label in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)@([A-Za-z0-9_]+)", str(c["body"].get("decision_rule"))):
            if label not in sims:
                continue
            at, s = sims[label]
            held = [r for r in ledger[:at] if r["type"] == "simulation" and r.get("parent") != xid and r["body"].get("run_id") == s.get("run_id") and name in (r["body"].get("metrics") or {})]
            first = next((r for r in ledger[:at] if r["id"] == s.get("same_as")), None)
            if not s.get("same_as"):
                g = 1
            elif held:
                g = 4 if any(r.get("turn") != turn for r in held) else 2
            elif name in (s.get("own") or []) and first is not None:
                g = 3 if first.get("turn") != turn else 2
            else:
                continue   # nothing the records tell
            term = f"{name}@{label}" + (f" (in {held[0]['id']})" if held else f" (of {s['same_as']}'s simulation)" if g != 1 else "")
            if not any(term in v for v in groups.values()):
                groups[g].append(term)
    if not any(groups.values()):
        return ""
    said = ((1, "of a simulation this test ran"), (2, "of a simulation run earlier in this same turn, after this test's rule was fixed"),
            (3, "a measurement this test took of a simulation of an earlier turn (computed now; whether a reading had shown that series is in the readings above)"),
            (4, "in a simulation's record of an earlier turn, so known when the rule was fixed"))
    return "OF THE VALUES THESE RULES COMPARE (facts of the records): " + "; ".join(f"{text}: {', '.join(groups[g])}" for g, text in said if groups[g]) + ".\n\n"

```

## B1. the simulations of a refused repair are kept once each (code; no text)

`harness/loop.py`

before:

```
        base += [r for r in refused_runs if isinstance(r, dict) and r.get("label") not in {q.get("label") for q in base}]   # the refused repair's simulations may be named again (s056 H5)
```

after:

```
        for r in refused_runs:   # the refused repair's simulations may be named again (s056 H5); each label once (the review of 2026-11-27, B1: s063 G30 held q100 twice)
            if isinstance(r, dict) and r.get("label") not in {q.get("label") for q in base}:
                base.append(r)
```

## C2. the mark NEW stands on the record's first line and says that it is the whole record

`harness/loop.py`

before:

```
    mark = lambda r: record(r) + ("   <- NEW since the researcher's earlier guesses" if new is not None and r["id"] in new else "")
```

after:

```
    def mark(r):   # the mark at the end of the record's first line: at the end of a result table it read as "only the last simulation is new" (the review of 2026-11-27, C2: s066 G11, G13, G22)
        text = record(r)
        if new is None or r["id"] not in new:
            return text
        first, _, rest = text.partition("\n")
        return first + "   <- NEW since the researcher's earlier guesses (the whole record)" + ("\n" + rest if rest else "")
```

## B5. a guess restated in its result alone also sends the test to a review of its own (code; no text)

`harness/loop.py`

before:

```
    return sorted(r["id"] for r in ledger if r["type"] == "why" and r.get("turn") == turn and r["id"] in named and isinstance(r["body"].get("restated"), dict)
                  and flat((r["body"]["restated"].get("was") or {}).get("guess")) != flat(r["body"].get("guess")))
```

after:

```
    was = lambda r, k: flat((r["body"]["restated"].get("was") or {}).get(k))
    return sorted(r["id"] for r in ledger if r["type"] == "why" and r.get("turn") == turn and r["id"] in named and isinstance(r["body"].get("restated"), dict)
                  and (was(r, "guess") != flat(r["body"].get("guess")) or was(r, "result") != flat(r["body"].get("result"))))   # the review shows both (B5: s057 Y24 changed its result only)
```

## B5. what makes a test the same in the batched review and in round 1 includes the guess it competes with and the measurements its rules name (code; no text)

`harness/loop.py`

before:

```
    rules = [{k: d.get(k) for k in ("decision_rule", "rival", "rival_predicts")} for d in ex.get("decision_rules") or [] if d.get("for") == hid]
    need = next((n for n in ex.get("needs") or [] if n.get("for") == hid), {})
```

after:

```
    rules = [{k: d.get(k) for k in ("decision_rule", "rival", "rival_predicts", "competes_with")} for d in ex.get("decision_rules") or [] if d.get("for") == hid]   # competes_with, and the measurements below: B5
    rules.append({"measurements": [m for m in ex.get("measurements") or [] if isinstance(m, dict) and any(re.search(rf"(?<![A-Za-z0-9_]){re.escape(str(m.get('name')))}@", str(d.get("decision_rule"))) for d in ex.get("decision_rules") or [] if d.get("for") == hid)]})
    need = next((n for n in ex.get("needs") or [] if n.get("for") == hid), {})
```

## B5. an answer of the batched first review is not kept beyond its reply (code; no text)

`harness/loop.py`

before:

```
        found = []
        def collect(w):
```

after:

```
        found = []
        if prereviewed.get("turn") != turn:   # an answer no round took does not outlive its turn (B5: s055 turn 10, H14)
            prereviewed.clear()
            prereviewed["turn"] = turn
        def collect(w):
```

## B2. the request for a repair after a refusal by the harness keeps the supervisor's objection (code)

`harness/loop.py`

before:

```
            who, feedback = earlier[-1][1], earlier[-1][2]
            user = repair_user(hid, test, n + 1, who, feedback, reserved, refused)
```

after:

```
            who, feedback = earlier[-1][1], earlier[-1][2]
            stands = next((f for _n, w, f, _t in reversed(earlier) if w == "the supervisor"), None) if who != "the supervisor" else None   # B2: the supervisor's objection still stands after a refusal by the harness
            user = repair_user(hid, test, n + 1, who, feedback, reserved, refused, stands)
```

## B2. (the same, the function's head)

`harness/loop.py`

before:

```
    def repair_user(hid, test, n, who, feedback, reserved=0, refused=None):
```

after:

```
    def repair_user(hid, test, n, who, feedback, reserved=0, refused=None, stands=None):
```

## B2, B6. the request for a repair shows the supervisor's objection that still stands, and the guesses a rule may compete with

`harness/loop.py`

before:

```
                + f"WHY IT WAS SENT BACK ({who}): {flat(feedback)}\n\n"

```

after:

```
                + f"WHY IT WAS SENT BACK ({who}): {flat(feedback)}\n\n"
                + (f"THE SUPERVISOR'S OBJECTION TO THE TEST ABOVE, WHICH STILL STANDS: {flat(stands)}\n\n" if stands else "")
                + (live_guesses_text(ledger, hid) if competitors else "")

```

## B6. the helper that lists the live guesses (the text of its heading is new)

`harness/loop.py`

before:

```
def competitor_text(ledger, rules, ex=None):
```

after:

```
def live_guesses_text(ledger, hid):
    """The guesses a repaired rule of this hypothesis may name in competes_with, for the request for a repair (the review of 2026-11-27, B6: the
    request asked for "an existing live guess" and listed none; s065 P3 named the refuted Y5). Listed: exactly those competitor_problem accepts."""
    flat = lambda v: " ".join(str(v).split())
    lines = [f"  [{r['id']}] {flat(r['body'].get('guess'))}" for r in ledger if r["type"] == "why" and competitor_problem({"for": hid, "competes_with": r["id"], "rival_predicts": "failed"}, ledger) is None]
    return "THE GUESSES A RULE OF THIS TEST MAY COMPETE WITH NOW (live: not refuted, not revised, not your hypothesis's own guess nor one linked to it by revises):\n" + ("\n".join(lines) or "  (none: a competing cause that is no guess yet is written as a guess in your next reply)") + "\n\n"


def competitor_text(ledger, rules, ex=None):
```

## B3. the supervisor is told truly what happens to a test sent back in the last round

`harness/loop.py`

before:

```
f"earlier rounds. A test sent back in round {REVIEW_ROUNDS} is run all the same, marked as contested.\n{before}\n" if round_no > 1 else "")
```

after:

```
f"earlier rounds. A test sent back in round {REVIEW_ROUNDS} is run all the same, marked as contested" + (", unless Consistent does not pass or you name a competing cause that is no guess yet: then it is not run and its hypothesis stays open" if COMP["on"] else "") + f".\n{before}\n" if round_no > 1 else "")
```

## B4. the names of a reply's new guesses in the batched first review: NEW1, NEW2, ... (they were G1, G2, ..., the ids of reviews)

`harness/loop.py`

before:

```
    gn = ng if isinstance(ng, list) else [f"G{i + 1}" for i in range(ng)]
```

after:

```
    gn = ng if isinstance(ng, list) else [f"NEW{i + 1}" for i in range(ng)]
```

## B4. (the answer format)

`harness/loop.py`

before:

```
"enum": gn or ["G1"], "description": "the guess's name in this request
```

after:

```
"enum": gn or ["NEW1"], "description": "the guess's name in this request
```

## B4. (the heading of each new guess)

`harness/loop.py`

before:

```
"".join(f"== NEW GUESS G{i + 1} ==\nTHE RECORDS IT CITES
```

after:

```
"".join(f"== NEW GUESS NEW{i + 1} ==\nTHE RECORDS IT CITES
```

## B4. (the request)

`harness/loop.py`

before:

```
(an item of guesses, named G1, G2, ... as above)
```

after:

```
(an item of guesses, named NEW1, NEW2, ... as above)
```

## B4. (the names given to the answer format)

`harness/loop.py`

before:

```
batch_schema([f"G{i + 1}" for i in range(len(guesses))], [hid for hid, _, _ in tests]))
```

after:

```
batch_schema([f"NEW{i + 1}" for i in range(len(guesses))], [hid for hid, _, _ in tests]))
```

## B4. (reading the answer)

`harness/loop.py`

before:

```
re.match(r"\s*([GH]\d+)\b", str(v))) else str(v))   # an id with words after it is read by its id
```

after:

```
re.match(r"\s*(NEW\d+|H\d+)\b", str(v))) else str(v))   # an id with words after it is read by its id
```

## B4. (reading the answer)

`harness/loop.py`

before:

```
    return [gs.get(f"G{i + 1}") for i in range(len(guesses))], [ts.get(hid) for hid, _, _ in tests], user
```

after:

```
    return [gs.get(f"NEW{i + 1}") for i in range(len(guesses))], [ts.get(hid) for hid, _, _ in tests], user
```

## B4. (the id each new guess will have, by its name)

`harness/loop.py`

before:

```
            new = {ys[k]: f"G{i + 1}" for i, (k, _) in enumerate(found) if k in ys}
```

after:

```
            new = {ys[k]: f"NEW{i + 1}" for i, (k, _) in enumerate(found) if k in ys}
```

## B4. (a guess compared with itself)

`harness/loop.py`

before:

```
            if m and own.get(f"G{i + 1}") == m.group(1):
```

after:

```
            if m and own.get(f"NEW{i + 1}") == m.group(1):
```

## B4. (the note)

`harness/loop.py`

before:

```
the supervisor's batched reading of new guess G{i + 1} named the guess itself
```

after:

```
the supervisor's batched reading of new guess NEW{i + 1} named the guess itself
```

## B4. in the batched review's answers about tests, the name of a new guess is replaced by its id (what the researcher is then shown)

`harness/loop.py`

before:

```
        for (hid, ex, case, key), x in zip(tests, t_ans):
            if isinstance(x, dict):
                prereviewed[key] = (x, saw)
```

after:

```
        ided = lambda v: re.sub(r"\bNEW\d+\b", lambda m: own.get(m.group(0), m.group(0)), v) if isinstance(v, str) else v   # B4: in what is said about a test, a new guess by the id it has in the ledger
        for (hid, ex, case, key), x in zip(tests, t_ans):
            if isinstance(x, dict):
                prereviewed[key] = ({k: ided(v) for k, v in x.items()}, saw)
```
