# v2, stage 3: one purpose, parking a finding, statements true of the code, limits from the constants
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## A4: the task sentence the harness writes

`harness/tools.py`

before:

```
        aim = f"Find the settings that give the {'largest' if t['direction'] == 'max' else 'smallest'} {t['measure']}"
        return f"{aim}{', while ' + ' and '.join(c.strip() for c in conds) if conds else ''}. {may} Explain why they are best."
    return f"No aim is given. Choose what 'performance' should mean for this system and say why; then find the settings that are best for it. {may} Explain why they are best."
```

after:

```
        # v2 (A4, the operator's sentence, 2026-11-24): one purpose, the same as the first lines of the instructions
        return (f"Explain what decides {t['measure']}, and say which {what} give the {'largest' if t['direction'] == 'max' else 'smallest'} {t['measure']}"
                + (f" within the brief's conditions ({' and '.join(c.strip() for c in conds)})" if conds else "") + f". {may}")
    return f"No aim is given. Choose what 'performance' should mean for this system and say why; then explain what decides it, and say which {what} are best for it. {may}"
```

## A4: settings, and the network where it may change

`harness/tools.py`

before:

```
    if goal.get("kind") == "given":
        t, conds = goal["target"], goal.get("conditions") or []
```

after:

```
    what = "settings and network" if net else "settings"
    if goal.get("kind") == "given":
        t, conds = goal["target"], goal.get("conditions") or []
```

## A4: the first lines of the supervised researcher's instructions (and the same words in the pair that shortens them)

`harness/loop.py`

before:

```
The purpose of the work is to understand why the system behaves as it does. You are not an optimiser: do not try many settings and keep whichever comes out slightly ahead. Look at the system,
```

after:

```
The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value. Look at the system,
```

## A4: when to stop

`harness/loop.py`

before:

```
 An explanation of what limits the result is worth more than one more setting. Stop when you can say what makes the system behave as it does and what that means for the goal.
```

after:

```
 Stop when you can say both.
```

## A4: the same lines in a session with competitors

`harness/loop.py`

before:

```
"The purpose is to understand why the system behaves as it does, not to optimise: look at it, ask why each result came out so, guess what in the system (not directly visible) makes it so, and test that guess."
```

after:

```
"The purpose is the task's: to explain what decides the measure it names, and to say which settings give its best value. Look at the system, ask why each result came out so, guess what in it (not directly visible) makes it so, and test that guess."
```

## A4: the first lines of the other two arms' instructions

`harness/prompt.txt`

before:

```
The purpose of the work is to understand why the system behaves as it does. Good settings follow from that understanding; they are not the work itself. A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.
```

after:

```
The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value. A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.
```

## A5: what may be parked (both texts on findings)

`harness/loop.py`

before:

```
- "It does not change the recommendation" is not a reason to park a finding: the task asks why the settings you recommend are best, so explaining a measured result is part of the goal.
```

after:

```
- A finding about a difference inside the tolerance, or about no measure the task names, may be parked with that reason; "it does not change the recommendation" alone is no reason.
```

## A5: the report is not held back for a parked finding (both texts)

`harness/loop.py`

before:

```
- A final report is held back while a finding was never looked at (no reading or
```

after:

```
- A final report is held back while a finding that is not parked was never looked at (no reading or
```

## A5: the code that holds a report back

`harness/loop.py`

before:

```
    return [f["id"] for f in finding_states(ledger).values() if f["status"] in ("open", "working", "parked") and not finding_looked(f, ledger)]
```

after:

```
    return [f["id"] for f in finding_states(ledger).values() if f["status"] in ("open", "working") and not finding_looked(f, ledger)]   # v2 (A5): a parked finding holds no report back
```

## A5: the turn's list of findings never looked at

`harness/loop.py`

before:

```
    never = [f["id"] for f in live if not finding_looked(f, ledger)]
```

after:

```
    never = [f["id"] for f in live if f["status"] != "parked" and not finding_looked(f, ledger)]
```

## A5: the turn's sentence about them

`harness/loop.py`

before:

```
+ "A final report is held back while a finding was never looked at." if never else ""))
```

after:

```
+ "A final report is held back while one of these was never looked at." if never else ""))
```

## C1: requests, in the supervised researcher's instructions

`harness/loop.py`

before:

```
Up to six requests in a reply; the results come back at once, in the same turn, and stay in the ledger with their ids (T1, T2, ...): a reply that states no hypothesis, test, drop or report is answered and you are asked again in the same turn, at most twice. A turn ends with a step.
```

after:

```
Up to <<LOOKS>> requests in a reply; the results stay in the ledger with their ids (T1, T2, ...). Sent alone (no hypothesis, test, drop or report), they are answered and you are asked again in the same turn, at most <<CONTINUES>>; sent with a step, they are answered in the next turn. A turn ends with a step.
```

## C1: requests, in the other two arms' instructions

`harness/prompt.txt`

before:

```
at most 3 in one reply; the results come back at once, in the same turn (a reply that states no hypothesis, test, verdict, drop or report is answered and you are asked again in the same turn, at most twice: a turn ends with a step), and stay in the ledger
```

after:

```
at most 3 in one reply. Sent alone, they are answered in the same turn (a reply that states no hypothesis, test, verdict, drop or report is answered and you are asked again in the same turn, at most twice: a turn ends with a step); sent with a step, they are answered in the next turn. The results stay in the ledger
```

## C2, C3: the budget, in the supervised researcher's instructions

`harness/loop.py`

before:

```
Every turn says how many are left; one experiment may run at most half of them. When they run out you get two more turns
```

after:

```
Every turn says how many are left and how many new ones its experiment may run. When they run out you get <<FREE_TURNS>> more turns
```

## C2, C3: each turn's sentence on the budget (every arm)

`harness/loop.py`

before:

```
This turn's experiment may run at most {spend_cap(budget - sims, per)} new simulations: never more than half of what is left, so that something remains for what its results raise.")
```

after:

```
This turn's experiment may run at most {spend_cap(budget - sims, per)} new simulations (half of what is left, rounded up, and never more than the brief's {per} for one experiment; it may list at most {per}, repeats included), so that something remains for what its results raise.")
```

## C2: the budget, in the other two arms' instructions

`harness/prompt.txt`

before:

```
One experiment may run at most half of the simulations that are left (each turn says how many that is)
```

after:

```
One experiment may run at most half of the simulations that are left, and never more than limits.simulations_per_experiment (each turn says how many that is)
```

## C4: what the tolerance means in a rule, in one place

`harness/loop.py`

before:

```
DEFAULT_TOLERANCE = 1.0  # what a brief that states none gets
```

after:

```
DEFAULT_TOLERANCE = 1.0  # what a brief that states none gets
# v2 (C4): what the tolerance means in a decision rule, as decision_rules.py and decided_by_little apply it; said with each turn's tolerance
TOLERANCE_IN_A_RULE = "in a decision rule == holds for two values closer than that; <, <=, > and >= compare the numbers as measured, and a check that two measured results decide by less is marked"
```

## C4: the tolerance, in the supervised researcher's instructions

`harness/loop.py`

before:

```
Two results closer than the tolerance count as equal: a difference inside it is not a finding.
```

after:

```
A difference inside the tolerance is not a finding (every turn says how a rule treats it).
```

## C4: the tolerance, as the supervisor is told it

`harness/loop.py`

before:

```
+ f"TOLERANCE: two results that differ by less than {TOLERANCE:g} % count as equal.\n")
```

after:

```
+ f"TOLERANCE: {TOLERANCE:g} %: {TOLERANCE_IN_A_RULE}.\n")
```

## C4: the tolerance, in each turn's text

`harness/loop.py`

before:

```
+ f"\n\nTOLERANCE: two results that differ by less than {TOLERANCE:g} % count as equal ({'stated by the brief' if tol_given else 'the default of the harness: the brief states none'}). "
```

after:

```
+ f"\n\nTOLERANCE: {TOLERANCE:g} % ({'stated by the brief' if tol_given else 'the default of the harness: the brief states none'}){'' if arm == 'plain' else ': ' + TOLERANCE_IN_A_RULE}. "
```

## C4: the tolerance, in the other two arms' instructions

`harness/prompt.txt`

before:

```
Two results that differ by less than the tolerance count as equal; every turn says which tolerance holds (TOLERANCE).
```

after:

```
Two results that differ by less than the tolerance do not differ meaningfully; every turn says which tolerance holds (TOLERANCE).
```

## C4: the note on a check decided by less than the tolerance

`harness/loop.py`

before:

```
less than the tolerance of {b['tolerance']:g} %. They count as equal: "
                        "this comparison is decided by a difference that does not matter, so it is no evidence of a difference.]"
```

after:

```
less than the tolerance of {b['tolerance']:g} %. The result stands as the numbers give it, "
                        "but a difference this small is no evidence of a difference.]"
```

## C5: a side with a number the rule states is not a plain result

`harness/decision_rules.py`

before:

```
    [(left, op, right, (left_kind, right_kind))]. A side's kind: "measured" (it holds a measured value), "number" (one number, as written),
    or "stated" (worked out from numbers the rule states)."""
    out = []
    def measured(node):
        return node[0] == "val" or any(measured(m) for n in node[1:] for m in (n if isinstance(n, list) else [n]) if isinstance(m, tuple))
```

after:

```
    [(left, op, right, (left_kind, right_kind))]. A side's kind: "measured" (measured values and nothing else), "margin" (a measured value with a
    number the rule states: 1.01 * x@a), "number" (one number, as written), or "stated" (worked out from numbers the rule states)."""
    out = []
    def measured(node):
        return node[0] == "val" or any(measured(m) for n in node[1:] for m in (n if isinstance(n, list) else [n]) if isinstance(m, tuple))
    def states(node):   # v2 (C5): the side holds a number of the rule's own
        return node[0] == "num" or any(states(m) for n in node[1:] for m in (n if isinstance(n, list) else [n]) if isinstance(m, tuple))
```

## C5: the kind of a side

`harness/decision_rules.py`

before:

```
            kind = lambda n: "measured" if measured(n) else "number" if n[0] == "num" else "stated"
```

after:

```
            kind = lambda n: ("margin" if states(n) else "measured") if measured(n) else "number" if n[0] == "num" else "stated"
```

## C5: the note only between two measured results

`harness/loop.py`

before:

```
    results = lambda kinds, a, b: kinds == ("measured", "measured") or (kinds == ("measured", "number") and b in earlier) or (kinds == ("number", "measured") and a in earlier)
```

after:

```
    results = lambda kinds, a, b: kinds == ("measured", "measured")   # v2 (C5): two measured results, and nothing the rule states (a margin, a threshold; s061 C3: "10.0 against 10.0")
```

## C6: a guess that names a finding (the supervised arm, which has the rule of the chain)

`harness/loop.py`

before:

```
FINDINGS_TEXT["supervised"] = FINDINGS_TEXT["hypotheses"].replace("checks, verdicts or readings", "checks, rulings or readings")
```

after:

```
FINDINGS_TEXT["supervised"] = FINDINGS_TEXT["hypotheses"].replace("checks, verdicts or readings", "checks, rulings or readings").replace("(for example F2) works on it.", "(for example F2) works on it (the chain's rule still holds for the records it rests on).")
```

## C7: a rule names a measurement only where its own experiment defines it

`harness/loop.py`

before:

```
measure@label (an output, or a measurement of your own, in the simulation with that label)
```

after:

```
measure@label (an output, or a measurement this experiment defines, in the simulation with that label)
```

## C8: the repair step's system text in a session with competitors

`harness/loop.py`

before:

```
                 "true, and the simulations only if they must change. Answer with one JSON object in the format you are given.")
```

after:

```
                 "true, and the simulations only if they must change. Answer with one JSON object in the format you are given.")
REPAIR_SYSTEM_COMP = ("You are the researcher. The supervisor, or the harness, sent back one of your tests before any of its simulations was run. Repair that test only, from the "   # v2 (C8)
                      "feedback: a decision rule that can tell your guess from the guess it competes with (a guess already written: a cause no guess states yet cannot be named "
                      "here), what the rule would give if that guess were true, and the simulations only if they must change. Answer with one JSON object in the format you are given.")
```

## C8: which of the two is sent

`harness/loop.py`

before:

```
called("researcher", model, REPAIR_SYSTEM + (structure_text(brief)
```

after:

```
called("researcher", model, (REPAIR_SYSTEM_COMP if COMP["on"] else REPAIR_SYSTEM) + (structure_text(brief)
```

## C9: the shown brief states the session's own number where no more can be asked for

`harness/loop.py`

before:

```
            shown = {**brief, "how_to_run": HOW_TO_RUN["plain" if arm == "plain" else "other"]} if "how_to_run" in brief else brief
```

after:

```
            shown = {**brief, "how_to_run": HOW_TO_RUN["plain" if arm == "plain" else "other"]} if "how_to_run" in brief else brief
            if not asks_budget and shown["limits"].get("simulations") != budget:   # v2 (C9; s059: "limits": {"simulations": 20} beside "12 granted so far", in an arm that cannot ask for more)
                shown = {**shown, "limits": {**shown["limits"], "simulations": budget}}
```

## C10: the rounds (the instructions, and both sides of the pair for a session with competitors)

`harness/loop.py`

before:

```
you repair that test at once, up to three rounds; the other tests run meanwhile;
```

after:

```
you repair that test at once (<<REVIEW_ROUNDS>> rounds at most, the first proposal counted); the other tests run afterwards;
```

## C10 / B12: a box that says cannot tell does not pass either

`harness/loop.py`

before:

```
If one fails, it says what is wrong and you repair
```

after:

```
If one does not pass, it says what is wrong and you repair
```

## C11: the format's line on a finding's name is written from the constant

`harness/loop.py`

before:

```
    "name": {"type": "string", "description": "at most 5 words, to show it by"}}}   # the name (2026-11-22, the operator: the page shows it on the finding's bar)
NAME_WORDS, NAME_CHARS = 6, 48   # a longer name is cut to this
```

after:

```
    "name": {"type": "string", "description": f"at most {NAME_WORDS} words, to show it by"}}}   # the name (2026-11-22, the operator: the page shows it on the finding's bar)
```

## C11: the constant (5 words, as the texts say), defined before the format that states it

`harness/loop.py`

before:

```
PARK_TURNS = 2        # a parked finding
```

after:

```
NAME_WORDS, NAME_CHARS = 5, 48   # a finding's name: a longer one is cut to this (v2, C11: the texts said 5 words and the cut was at 6; both are this constant now)
PARK_TURNS = 2        # a parked finding
```

## C11: the instructions' line on a finding's name (both texts)

`harness/loop.py`

before:

```
name (at most 5 words, to show it by)
```

after:

```
name (at most <<NAME_WORDS>> words, to show it by)
```

## C11: the supervisor's line on a finding's name

`harness/loop.py`

before:

```
a name of at most 5 words to show it by (name)
```

after:

```
a name of at most " + str(NAME_WORDS) + " words to show it by (name)
```

## C12: what stays of a reading

`harness/loop.py`

before:

```
". Every reading stays in the ledger for the rest of the session."
```

after:

```
f". Every reading stays in the ledger for the rest of the session (one longer than {CAP:,} characters is cut to that, and once the readings pass {READINGS_ROOM:,} characters in all the older long ones are shortened)."
```

## C13: when the flows start (a brief of v2)

`briefs/three-hosts-2.json`

before:

```
In each simulation the flows start within the first 10 ms, traffic runs for one second that is not measured, and then for duration seconds
```

after:

```
In each simulation the flows start at 1 s of the simulation's clock, within 10 ms of each other; traffic runs for one second that is not measured, and then for duration seconds
```

## C13: when the flows start (a brief of v2)

`briefs/three-hosts-link-2.json`

before:

```
In each simulation the flows start within the first 10 ms, traffic runs for one second that is not measured, and then for duration seconds
```

after:

```
In each simulation the flows start at 1 s of the simulation's clock, within 10 ms of each other; traffic runs for one second that is not measured, and then for duration seconds
```

## told to the other arms only: a value out of its range is moved into it

`harness/loop.py`

before:

```
params: a value for EVERY knob of the brief (a knob left as it was is stated with the value it has).
```

after:

```
params: a value for EVERY knob of the brief (also one left as it was; a value outside its range is moved into it, as the record then says).
```

## told to the other arms only (there: the experiment is refused): what happens to a rule the harness cannot read

`harness/loop.py`

before:

```
exactly one of < <= > >= == in each comparison; at most 3 comparisons, joined by AND and OR.
```

after:

```
exactly one of < <= > >= == in each comparison; at most <<COMPARISONS_MOST>> comparisons, joined by AND and OR. A rule the harness cannot read comes back to you as a round of that test.
```

## room: the same thing said twice

`harness/loop.py`

before:

```
You do not work alone. A supervisor works apart from you.
```

after:

```
A supervisor works apart from you.
```

## room: "one or two sentences" stands in the line above it, for every text

`harness/loop.py`

before:

```
1. observations: one or two sentences: what you read this turn;
```

after:

```
1. observations: what you read this turn;
```

## room: where they stand is seen in the ledger itself

`harness/loop.py`

before:

```
They stay in the ledger (turn N your observations).
```

after:

```
They stay in the ledger.
```

## room: a reason, not a rule (both texts on findings)

`harness/loop.py`

before:

```
until you close it, so that nothing unexplained is lost.
```

after:

```
until you close it.
```

## limits: a label's length

`harness/loop.py`

before:

```
(letters, digits and _, at most 20 characters) and params
```

after:

```
(letters, digits and _, at most <<LABEL_MOST>> characters) and params
```

## limits: new hypotheses in one answer

`harness/loop.py`

before:

```
state at most three in one answer
```

after:

```
state at most <<OPEN_MOST>> in one answer
```

## limits: when a parked finding comes back (both texts)

`harness/loop.py`

before:

```
nothing new about it for 2 turns, comes back as DUE.
```

after:

```
nothing new about it for <<PARK_TURNS>> turns, comes back as DUE.
```

## limits: the texts are filled from the constants when the program starts

`harness/loop.py`

before:

```
def supervised_prompt(text, competitors=False):
```

after:

```
# v2 (item 5): the limits the instructions state are written from the constants the code applies. A text above names one as <<NAME>>.
_SAID = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
def limits_filled(text):
    """A text of the instructions with every <<NAME>> replaced by the constant of that name, as a sentence says it."""
    said = {"LOOKS": _SAID.get(LOOKS, str(LOOKS)), "CONTINUES": {1: "once", 2: "twice"}.get(CONTINUES, f"{CONTINUES} times"), "REVIEW_ROUNDS": _SAID.get(REVIEW_ROUNDS, str(REVIEW_ROUNDS)),
            "OPEN_MOST": _SAID.get(OPEN_MOST, str(OPEN_MOST)), "FREE_TURNS": _SAID.get(FREE_TURNS, str(FREE_TURNS)), "LABEL_MOST": str(LABEL_MOST), "COMPARISONS_MOST": str(COMPARISONS_MOST),
            "PARK_TURNS": str(PARK_TURNS), "NAME_WORDS": str(NAME_WORDS)}
    for k, v in said.items():
        text = text.replace(f"<<{k}>>", v)
    if "<<" in text:
        raise ValueError(f"the instructions name a limit the code does not have: {text[text.find('<<'):][:40]!r}")
    return text
LEAN_PROMPT = limits_filled(LEAN_PROMPT)
FINDINGS_TEXT = {k: limits_filled(v) for k, v in FINDINGS_TEXT.items()}
COMP_LEAN = tuple((limits_filled(a_), limits_filled(b_)) for a_, b_ in COMP_LEAN)


def supervised_prompt(text, competitors=False):
```

## A4: the page's copy of the task sentence keeps the two older forms

`viewer/evidence_setting.js`

before:

```
  taskText(b, before) { const kn = Object.keys((b && b.knobs) || {}), g = (b && b.goal) || {}, net = !before && !!(b && b.topology && b.structure && b.structure.may_change),
```

after:

```
  // 'v1': the sentence from 2026-11-23 until v2 ("Find the settings that give ... Explain why they are best."), which the sessions of those days keep
  taskText(b, before) { const kn = Object.keys((b && b.knobs) || {}), g = (b && b.goal) || {}, net = before !== true && !!(b && b.topology && b.structure && b.structure.may_change), what = net ? 'settings and network' : 'settings',
```

## A4: the page's copy of the task sentence

`viewer/evidence_setting.js`

before:

```
    if (g.kind === 'given') { const t = g.target || {}, c = (g.conditions || []).map(x => String(x).trim()); return `Find the settings that give the ${t.direction === 'max' ? 'largest' : 'smallest'} ${t.measure}${c.length ? ', while ' + c.join(' and ') : ''}. ${may} Explain why they are best.`; }
    return `No aim is given. Choose what 'performance' should mean for this system and say why; then find the settings that are best for it. ${may} Explain why they are best.`; },
```

after:

```
    if (g.kind === 'given') { const t = g.target || {}, c = (g.conditions || []).map(x => String(x).trim()), best = t.direction === 'max' ? 'largest' : 'smallest';
      return before ? `Find the settings that give the ${best} ${t.measure}${c.length ? ', while ' + c.join(' and ') : ''}. ${may} Explain why they are best.`
        : `Explain what decides ${t.measure}, and say which ${what} give the ${best} ${t.measure}${c.length ? ` within the brief's conditions (${c.join(' and ')})` : ''}. ${may}`; }
    return before ? `No aim is given. Choose what 'performance' should mean for this system and say why; then find the settings that are best for it. ${may} Explain why they are best.`
      : `No aim is given. Choose what 'performance' should mean for this system and say why; then explain what decides it, and say which ${what} are best for it. ${may}`; },
```

## A4: a task in an older form of the harness's sentence is still said to be the harness's

`viewer/evidence_cards.js`

before:

```
b.task === EV.taskText(b) || b.task === EV.taskText(b, true)
```

after:

```
b.task === EV.taskText(b) || b.task === EV.taskText(b, true) || b.task === EV.taskText(b, 'v1')
```

## C13: the page's writer of a network's description

`viewer/brief_net.js`

before:

```
In each simulation the flows start within the first 10 ms${t.flows.some(f => 'start' in f) ? ' after one second (a flow that states its own start begins then)' : ''}, traffic runs
```

after:

```
In each simulation the flows start at 1 s of the simulation's clock, within 10 ms of each other${t.flows.some(f => 'start' in f) ? ' (a flow that states its own start begins then)' : ''}; traffic runs
```
