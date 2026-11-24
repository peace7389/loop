# v2, stage 2: the supervisor
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## item 4, B8, B9, B12: the questions; a box may say cannot tell

`harness/loop.py`

before:

```
QUESTIONS = {"honest": "can the test fail? Its result is not already known from the records, and its threshold is not one that almost any result passes",
             "consistent": "does the rule test what the hypothesis claims, and only that? The simulations it compares differ only in what the claim is about, its measure can see it, and the competing guess explains the same result",
             "correct": "does the rule come out differently under the two guesses: HELD if the tested guess is true, FAILED if the competing guess is true?"}
BOX = {"type": "string", "enum": ["pass", "fail"]}
```

after:

```
QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? Pass only if someone who held the guess to be true would have to expect what the hypothesis says; fail if the guess leaves it open, or would expect otherwise",
             "honest": "can the test fail? Pass only if no value its rule compares, and no series such a value is computed from, already stands in the records you are shown, and its threshold is not one that almost any result passes; otherwise fail",
             "consistent": "does the rule test what the hypothesis claims, and only that? Pass only if the simulations it compares differ only in what the claim is about, its measure can see it, and the competing guess is about the same result; otherwise fail",
             "correct": "does the rule come out differently under the two guesses: HELD if the tested guess is true, FAILED if the competing guess is true?"}
# the same questions once the result is there (v2): Honest is about the time before the run, when its result was not known
QUESTIONS_AFTER = {"honest": "could the test have failed? Pass only if, before it ran, no value its rule compares stood in the records, and its threshold is not one that almost any result passes; otherwise fail",
                   "consistent": QUESTIONS["consistent"], "correct": QUESTIONS["correct"]}
REVIEW_QS, RULING_QS = ("follows", "honest", "consistent", "correct"), ("honest", "consistent", "correct")
CANNOT = "cannot tell"   # v2: an answer of every box; at the review it counts as a fail (its sentence says what is missing to tell), at the ruling it makes the result inconclusive
BOX = {"type": "string", "enum": ["pass", "fail", CANNOT]}
```

## item 4: the review's answer has the box Follows

`harness/loop.py`

before:

```
REVIEW3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reads", "honest_why", "honest",
```

after:

```
REVIEW3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reads", "follows_why", "follows", "honest_why", "honest",
```

## item 4, B8, B12: what each answer of a box means

`harness/loop.py`

before:

```
    "honest_why": {"type": "string", "description": "one sentence, with record ids: can the test fail? (its result not already known from the records; a threshold that not almost any result passes)"},
    "honest": {**BOX, "description": "pass: it can fail"},
    "consistent_why": {"type": "string", "description": "one sentence, with record ids: does the rule test what the hypothesis claims and only that (its simulations differ only in what the claim is about, its measure can see it), and does the competing guess explain the same result?"},
    "consistent": {**BOX, "description": "pass: it tests the claim and only it, against a guess about the same result"},
```

after:

```
    "follows_why": {"type": "string", "description": "one sentence: would someone who held the tested guess to be true have to expect what the hypothesis says, and why (or what is missing to tell)"},
    "follows": {**BOX, "description": "pass: the hypothesis follows from the guess; fail: the guess leaves it open or would expect otherwise; cannot tell: the sentence says what is missing"},
    "honest_why": {"type": "string", "description": "one sentence, with record ids: can the test fail? (no value its rule compares, and no series it is computed from, already in the records shown; a threshold that not almost any result passes)"},
    "honest": {**BOX, "description": "pass: it can fail; fail: it cannot; cannot tell: the sentence says what is missing"},
    "consistent_why": {"type": "string", "description": "one sentence, with record ids: does the rule test what the hypothesis claims and only that (its simulations differ only in what the claim is about, its measure can see it), and is the competing guess about the same result?"},
    "consistent": {**BOX, "description": "pass: it tests the claim and only it, against a guess about the same result; fail: it does not; cannot tell: the sentence says what is missing"},
```

## B12: Correct may say cannot tell

`harness/loop.py`

before:

```
"description": "pass only when if_tested is held and if_competitor is failed"}
```

after:

```
"description": "pass only when if_tested is held and if_competitor is failed; cannot tell when one of the two cannot be told"}
```

## B12: the feedback's description

`harness/loop.py`

before:

```
"description": "for the researcher: which question failed and the one problem that matters most, the record ids and numbers it rests on, and what a repaired test must achieve (empty when all pass).
```

after:

```
"description": "for the researcher: which question did not pass and the one problem that matters most, the record ids and numbers it rests on, and what a repaired test must achieve (empty when all pass).
```

## B4: the ruling's answer without the fields that asked about its earlier answers

`harness/loop.py`

before:

```
"required": ["shows", "honest_why", "honest", "honest_foreseeable", "consistent_why", "consistent", "consistent_foreseeable", "correct_why", "correct", "correct_foreseeable", "because", "result", "fits_tested", "fits_competitor", "retest", "findings"]
```

after:

```
"required": ["shows", "honest_why", "honest", "consistent_why", "consistent", "correct_why", "correct", "because", "result", "fits_tested", "fits_competitor", "retest", "findings"]
```

## B4, B8, B12: the ruling's three questions

`harness/loop.py`

before:

```
    **{k: v for q in ("honest", "consistent", "correct") for k, v in ((f"{q}_why", {"type": "string", "description": f"one sentence, with the result in hand and record ids: {QUESTIONS[q]}"}), (q, BOX),
        (f"{q}_foreseeable", {**FORESEE, "description": "only when this question passed at the review before the run and fails now: could the problem have been seen before the simulations ran? Otherwise n/a"}))},
```

after:

```
    **{k: v for q in RULING_QS for k, v in ((f"{q}_why", {"type": "string", "description": f"one sentence, with the result in hand and record ids: {QUESTIONS_AFTER[q]}"}),
                                              (q, {**BOX, "description": "pass, fail, or cannot tell: then the sentence says what is missing to tell"}))},
```

## B1, B12: whether a guess fits is said freely for each guess

`harness/loop.py`

before:

```
"description": "supported: every check held and all three questions pass; refuted: a check failed and all three pass; inconclusive: otherwise"},
    "fits_tested": {"type": "string", "enum": ["fits", "does not fit"], "description": "whether the tested guess fits this result"},
    "fits_competitor": {"type": "string", "enum": ["fits", "does not fit"], "description": "whether the competing guess fits this result"},
```

after:

```
"description": "supported: every check held and all three questions pass; refuted: a check failed and all three pass; inconclusive: otherwise (a question failed or could not be told, or the checks disagree)"},
    "fits_tested": {"type": "string", "enum": ["fits", "does not fit", CANNOT], "description": "whether the tested guess, as the researcher states it above, fits this result: fits, does not fit, or cannot tell. A result may fit both guesses, or neither"},
    "fits_competitor": {"type": "string", "enum": ["fits", "does not fit", CANNOT], "description": "whether the competing guess, as the researcher states it above, fits this result: fits, does not fit, or cannot tell. A result may fit both guesses, or neither"},
```

## item 4, B8, B12: what the review asks

`harness/loop.py`

before:

```
QUESTIONS_ASK = ("Before any of these simulations is run, answer three questions about this test, each with one sentence that cites record ids, then its box. Honest: "
                 + QUESTIONS["honest"] + ". Consistent: " + QUESTIONS["consistent"] + ". Correct: say what the rule gives if the tested guess is true and the competing guess false, and "
                 "what it gives if the competing guess is true and the tested guess false; pass only when the first is HELD and the second FAILED. Judge the competing guess the researcher "
                 "named, do not replace it with your own. If the competing cause this test needs is a guess listed above other than the one the rule names, say so in feedback with its id; only if none of them states it, name it in missing. Last, feedback for the researcher: which "
                 "question failed and the one problem that matters most, the record ids and numbers it rests on, and what a repaired test must achieve. The feedback never contains a "
                 "decision rule, a measure@label, simulations or a network change: the researcher must find the repair itself. A test is not wanting for being small or for testing only "
                 "one consequence of the guess.")
```

after:

```
QUESTIONS_ASK = ("Before any of these simulations is run, answer four questions about this test, each with one sentence that cites record ids, then its box: pass, fail, or cannot tell "
                 "(then the sentence says what is missing to tell). Follows: " + QUESTIONS["follows"] + ". Honest: " + QUESTIONS["honest"] + ". Consistent: " + QUESTIONS["consistent"]
                 + ". Correct: say what the rule gives if the tested guess is true and the competing guess false, and "
                 "what it gives if the competing guess is true and the tested guess false; pass only when the first is HELD and the second FAILED. Judge the competing guess the researcher "
                 "named, do not replace it with your own. If the competing cause this test needs is a guess listed above other than the one the rule names, say so in feedback with its id; only if none of them states it, name it in missing. Last, feedback for the researcher: which "
                 "question did not pass and the one problem that matters most, the record ids and numbers it rests on, and what a repaired test must achieve. The feedback never contains a "
                 "decision rule, a measure@label, simulations or a network change: the researcher must find the repair itself. A test is not wanting for being small or for testing only "
                 "one consequence of the guess. A test that passes runs; one that does not goes back to the researcher to repair.")
```

## B7: the line that always read FAILED

`harness/loop.py`

before:

```
        out += (f"THE GUESS THIS RULE COMPETES WITH [{d.get('competes_with')}]: the result it explains: {flat(w.get('result'))} | its guess: {flat(w.get('guess'))}\n"
                f"WHAT THE RESEARCHER SAYS THE RULE GIVES IF THAT GUESS IS TRUE AND THE TESTED ONE FALSE: {str(d.get('rival_predicts')).upper()}\n")
```

after:

```
        out += f"THE GUESS THIS RULE COMPETES WITH [{d.get('competes_with')}]: the result it explains: {flat(w.get('result'))} | its guess: {flat(w.get('guess'))}\n"
```

## item 4, B12: the review's boxes as read

`harness/loop.py`

before:

```
    box = lambda v: v if v in ("pass", "fail") else "fail"
    gives = lambda v: v if v in ("held", "failed", "cannot tell") else "cannot tell"
    rev = {"reads": flat(d.get("reads")), **{k: flat(d.get(k)) for k in ("honest_why", "consistent_why", "correct_why")}, **{q: box(d.get(q)) for q in ("honest", "consistent", "correct")},
```

after:

```
    box = lambda v: v if v in ("pass", "fail", CANNOT) else "fail"
    gives = lambda v: v if v in ("held", "failed", "cannot tell") else "cannot tell"
    rev = {"reads": flat(d.get("reads")), **{q + "_why": flat(d.get(q + "_why")) for q in REVIEW_QS}, **{q: box(d.get(q)) for q in REVIEW_QS},
```

## item 4, B12: a test passes only with four passes; cannot tell is counted

`harness/loop.py`

before:

```
    ok = not (rev.get("again") or {}).get("still") and not (clash and "again" not in rev) and all(rev[q] == "pass" for q in ("honest", "consistent", "correct"))
    failed = [q for q in ("honest", "consistent", "correct") if rev[q] == "fail"]
    rev["defect"] = failed[0] if failed else ("contradiction" if not ok else "none")   # which question failed (the figures and the page read the three boxes)
    if not ok and not rev["feedback"]:   # a refusal always says what is wrong
        rev["feedback"] = ("; ".join(f"{q.capitalize()} failed: {rev[q + '_why']}" for q in failed) if failed else
```

after:

```
    ok = not (rev.get("again") or {}).get("still") and not (clash and "again" not in rev) and all(rev[q] == "pass" for q in REVIEW_QS)
    failed = [q for q in REVIEW_QS if rev[q] != "pass"]   # a box that says cannot tell does not pass (v2)
    cannot = [q for q in REVIEW_QS if rev[q] == CANNOT]
    if cannot:
        rev["cannot_tell"] = cannot
    rev["defect"] = failed[0] if failed else ("contradiction" if not ok else "none")   # which question did not pass (the figures and the page read the boxes)
    if not ok and not rev["feedback"]:   # a refusal always says what is wrong
        rev["feedback"] = ("; ".join(f"{q.capitalize()} {'could not be told' if rev[q] == CANNOT else 'failed'}: {rev[q + '_why']}" for q in failed) if failed else
```

## B10: the table of one test's simulations

`harness/loop.py`

before:

```
def _measured(ledger, only=None):
    """Every simulation measured so far as the evidence tables give it (label, run, settings changed from the defaults | measured), or those of one experiment."""
    lines = [f"  [{r['id']}] " + l for r in ledger if r["type"] == "evidence" and (only is None or r["body"]["experiment"] == only) for l in r["body"]["lines"]]
```

after:

```
def _measured(ledger, only=None, labels=None, others=False):
    """Every simulation measured so far as the evidence tables give it (label, run, settings changed from the defaults | measured), or those of one experiment.
    labels (v2): of that experiment, only the simulations with these labels (those a test's rules name); others: only the rest."""
    named = lambda l: l.split(" ", 1)[0] in (labels or ())
    lines = [f"  [{r['id']}] " + l for r in ledger if r["type"] == "evidence" and (only is None or r["body"]["experiment"] == only) for l in r["body"]["lines"] if labels is None or named(l) != others]
```

## B2, B10: what the ruling's request shows

`harness/loop.py`

before:

```
    user = (_system_for_supervisor(brief) + "\n" + _case(ledger, hid, rules) + f"\nTHE SIMULATIONS OF THIS TEST, as measured:\n{_measured(ledger, xid)}\n\nTHE BASELINE and what was measured before:\n{_measured([r for r in ledger if not (r['type'] == 'evidence' and r['body']['experiment'] == xid)])}\n\n"
```

after:

```
    named = sorted({l for c in checks for l in re.findall(r"@([A-Za-z0-9_]+)", c["body"]["decision_rule"])})   # v2 (B10): under the test, only the simulations its rules name
    rest = _measured(ledger, xid, named, others=True)
    comp = competitor_text(ledger, [c["body"] for c in checks if c["body"].get("competes_with")][:1]) if COMP["on"] else ""   # v2 (B2): the competing guess in the researcher's words, as at the review
    user = (_system_for_supervisor(brief) + "\n" + _case(ledger, hid, rules) + comp + f"\nTHE SIMULATIONS THIS TEST'S RULES NAME, as measured:\n{_measured(ledger, xid, named)}\n\n"
            + (f"OTHER SIMULATIONS OF THE SAME EXPERIMENT (they belong to other tests of it, not to this one):\n{rest}\n\n" if rest != "  (nothing yet)" else "")
            + f"THE BASELINE and what was measured before:\n{_measured([r for r in ledger if not (r['type'] == 'evidence' and r['body']['experiment'] == xid)])}\n\n"
```

## B4: the ruling's request no longer quotes the review's answers (the harness compares the two itself)

`harness/loop.py`

before:

```
            + (("AT THE REVIEW BEFORE THE RUN you answered: " + "; ".join(f"{q.capitalize()} {review.get(q)}: {flat(review.get(q + '_why'))}" for q in ("honest", "consistent", "correct"))
                + f" (the rule gives {str(review.get('if_tested')).upper()} if the tested guess is true, {str(review.get('if_competitor')).upper()} if {review.get('competes_with')} is true)\n\n") if COMP["on"] and review else "")

```

after:

```

```

## B1, B4, B8: what the ruling asks

`harness/loop.py`

before:

```
RULING3_ASK = ("Answer the three questions again with the result in hand, each with one sentence that cites record ids, then its box: Honest: " + QUESTIONS["honest"]
               + ". Consistent: " + QUESTIONS["consistent"] + ". Correct: " + QUESTIONS["correct"] + " For a question that passed at the review and fails now, say whether the problem could have "
               "been seen before the run (foreseeable). Then your reasoning, the result (supported: every check HELD and all three pass; refuted: a check FAILED and all three pass; inconclusive: "
               "otherwise), and whether each guess the test named fits this result.")
```

after:

```
RULING3_ASK = ("Answer three questions with the result in hand, each with one sentence that cites record ids, then its box (pass, fail, or cannot tell: then the sentence says what is missing "
               "to tell): Honest: " + QUESTIONS_AFTER["honest"] + ". Consistent: " + QUESTIONS_AFTER["consistent"] + ". Correct: " + QUESTIONS_AFTER["correct"]
               + " Then your reasoning, the result (supported: every check HELD and all three pass; refuted: a check FAILED and all three pass; inconclusive: otherwise), and, for each of the "
               "two guesses the test named, whether it fits this result: each is judged by itself, from its own words above, and a result may fit both, or neither.")
```

## B1, B4, B12, item 4: the ruling as the harness reads it (no second question that forced an answer; the review's Follows goes with it)

`harness/loop.py`

before:

```
    box = lambda v: v if v in ("pass", "fail") else "fail"
    qs = {q: {"why": flat(d.get(q + "_why")), "box": box(d.get(q)), "foreseeable": d.get(q + "_foreseeable") if d.get(q + "_foreseeable") in ("yes", "no") else "n/a"} for q in ("honest", "consistent", "correct")}
    fair = all(v["box"] == "pass" for v in qs.values())
    res = [c["body"]["result"] for c in checks]
    fits = {"supported": all(x == "held" for x in res) and fair, "refuted": any(x == "failed" for x in res) and fair, "inconclusive": True}.get(d.get("result"), False)
    result = d.get("result") if fits else "inconclusive"
    h = next((r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), {})
    own, cw = h.get("from_why"), next((c["body"].get("competes_with") for c in checks if c["body"].get("competes_with")), None) or (review or {}).get("competes_with")
    given = {"tested": d.get("fits_tested") if d.get("fits_tested") in ("fits", "does not fit") else None, "competitor": d.get("fits_competitor") if d.get("fits_competitor") in ("fits", "does not fit") else None}
    want = {"supported": {"tested": "fits", "competitor": "does not fit"}, "refuted": {"tested": "does not fit", "competitor": "fits"}}.get(result) if fair else None
    contradicted, again = False, None
    if want and given != want:   # the fits do not fit the result of a fair test: one question, and its answer stands only if it fits
        q = (user + f"\n\nYOUR RULING: {result}, a fair test; the tested guess {own}: {given['tested']}; the competing guess {cw}: {given['competitor']}. These do not fit together: a fair test "
             f"that {('held' if result == 'supported' else 'failed')} fits the guess that predicted it and not the other. One question: which of the two guesses does this result fit? Answer, then the two boxes.")
        try:
            a = (ask_fn or (lambda m, u, sc: supervise(m, u, sc, AGAIN_TOKENS)))(model, q, FITS_AGAIN_SCHEMA)
            again = {"because": flat(a.get("because")), "tested": a.get("fits_tested"), "competitor": a.get("fits_competitor")}
            if {"tested": again["tested"], "competitor": again["competitor"]} == want:
                given = dict(want)
            else:
                contradicted = True
        except (ValueError, KeyError, TypeError, AttributeError):
            contradicted = True
        user = q
    rev = review or {}
    misses = [{"question": q, "foreseeable": qs[q]["foreseeable"]} for q in ("honest", "consistent", "correct") if rev.get(q) == "pass" and qs[q]["box"] == "fail"]
    failed = [q for q in qs if qs[q]["box"] == "fail"]
    ruling = {"shows": flat(d.get("shows")), "fair": fair, "defect": failed[0] if failed else "none", "result": result, "because": flat(d.get("because")), "retest": flat(d.get("retest") or ""),
              "checks": [c["id"] for c in checks], "questions": qs, "fits": {k: v for k, v in ((own, given["tested"]), (cw, given["competitor"])) if k and v}, "competes_with": cw,
              **({"fits_again": again} if again else {}), **({"fits_contradicted": True} if contradicted else {}), **({"misses": misses} if misses else {}),
              "findings": list(d.get("findings") or []) if isinstance(d.get("findings"), list) else [], **({"findings_cut": True} if d.get("findings_cut") else {}),
              **({} if fits else {"changed_by_harness": f"the supervisor said {d.get('result')}, which does not fit the checks ({', '.join(res)}) or its three questions (" + ", ".join(f"{q} {qs[q]['box']}" for q in qs) + ")"})}
    return ruling, user

```

after:

```
    box = lambda v: v if v in ("pass", "fail", CANNOT) else "fail"
    qs = {q: {"why": flat(d.get(q + "_why")), "box": box(d.get(q))} for q in RULING_QS}
    fair = all(v["box"] == "pass" for v in qs.values())   # a question that failed or could not be told: not a fair test, and the result is inconclusive
    res = [c["body"]["result"] for c in checks]
    fits = {"supported": all(x == "held" for x in res) and fair, "refuted": any(x == "failed" for x in res) and fair, "inconclusive": True}.get(d.get("result"), False)
    result = d.get("result") if fits else "inconclusive"
    h = next((r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), {})
    own, cw = h.get("from_why"), next((c["body"].get("competes_with") for c in checks if c["body"].get("competes_with")), None) or (review or {}).get("competes_with")
    fit = lambda v: v if v in ("fits", "does not fit", CANNOT) else None
    given = {"tested": fit(d.get("fits_tested")), "competitor": fit(d.get("fits_competitor"))}   # v2 (B1): as the supervisor says it of each guess; no answer is asked for a second time
    rev = review or {}
    changed = [q for q in RULING_QS if rev.get(q) == "pass" and qs[q]["box"] != "pass"]   # v2 (B4): a question the review passed and the ruling does not, found by comparing the two
    failed = [q for q in qs if qs[q]["box"] != "pass"]
    cannot = [q for q in qs if qs[q]["box"] == CANNOT] + [k for k, v in (("fits_tested", given["tested"]), ("fits_competitor", given["competitor"])) if v == CANNOT]
    ruling = {"shows": flat(d.get("shows")), "fair": fair, "defect": failed[0] if failed else "none", "result": result, "because": flat(d.get("because")), "retest": flat(d.get("retest") or ""),
              "checks": [c["id"] for c in checks], "questions": qs, "fits": {k: v for k, v in ((own, given["tested"]), (cw, given["competitor"])) if k and v}, "competes_with": cw,
              # v2 (item 4): whether the review found that the hypothesis follows from its guess; only then can this ruling refute the guess (guess_refutations)
              **({"follows": rev["follows"]} if rev.get("follows") else {}), **({"changed": changed} if changed else {}), **({"cannot_tell": cannot} if cannot else {}),
              "findings": list(d.get("findings") or []) if isinstance(d.get("findings"), list) else [], **({"findings_cut": True} if d.get("findings_cut") else {}),
              **({} if fits else {"changed_by_harness": f"the supervisor said {d.get('result')}, which does not fit the checks ({', '.join(res)}) or its three questions (" + ", ".join(f"{q} {qs[q]['box']}" for q in qs) + ")"})}
    return ruling, user

```

## item 4: when a ruling refutes a guess

`harness/loop.py`

before:

```
        if b.get("fair") and not b.get("fits_contradicted"):
            for y, f in (b.get("fits") or {}).items():
                if f == "does not fit":
                    out.setdefault(y, v["id"])
```

after:

```
        if b.get("fair") and not b.get("fits_contradicted"):
            for y, f in (b.get("fits") or {}).items():
                # v2 (item 4): the tested guess is refuted through its hypothesis only where the review found that the hypothesis follows from it (s058: H1 did
                # not follow from Y1, failed, and Y1 was marked refuted); a ruling made before the box Follows existed counts as before
                if f == "does not fit" and not (y == hyps.get(hid) and b.get("follows") not in (None, "pass")):
                    out.setdefault(y, v["id"])
```

## item 4: a guess all of whose hypotheses were refuted is refuted only where they followed from it

`harness/loop.py`

before:

```
    for y, hs in of.items():
        if y not in out and all(h in by_h and by_h[h]["body"].get("result") == "refuted" for h in hs):
```

after:

```
    for y, hs in of.items():
        if y not in out and all(h in by_h and by_h[h]["body"].get("result") == "refuted" and by_h[h]["body"].get("follows") in (None, "pass") for h in hs):
```

## A9: the mark on a refuted guess

`harness/loop.py`

before:

```
(f" by {w['by']}: no hypothesis can come from it" + (", and no guess or test may compete with it" if COMP["on"] else "") + "; a new guess may revise it" if w.get("by") else "")
```

after:

```
(f" by the ruling {w['by']} on a hypothesis that follows from it: no new hypothesis is accepted from it" + (", and no guess or test may name it as a competitor" if COMP["on"] else "") + "; a new guess may revise it" if w.get("by") else "")
```

## A9: the mark on a check says what was declared and what came out

`harness/loop.py`

before:

```
            f"  [this is what the rival explanation predicted: {flat(b['rival'])}]" if b["rival_predicts"] == b["result"]
            else f"  [the rival explanation predicted {b['rival_predicts'].upper()} and does not fit this result: {flat(b['rival'])}]")
```

after:

```
            f"  [the rule was declared to give {b['rival_predicts'].upper()} under {flat(b['rival'])}, and gave {b['result'].upper()}]")
```

## B3, B6: what an earlier round was, and no example change

`harness/loop.py`

before:

```
    before = "".join(f"ROUND {k} of this test: {who} sent it back: {flat(fb)}\n" for k, who, fb in earlier)
```

after:

```
    # v2 (B3, B6): each earlier round with the test as it stood then; the harness's reason without the example change it gives the researcher
    before = "".join(f"ROUND {k} of this test" + (f", as it stood then: {flat(rest[0])}" if rest and rest[0] else "") + f"\n  {who} sent it back: {flat(re.sub(r'[.] A change written correctly for this network, for example: .*$', '', str(fb)))}\n" for k, who, fb, *rest in earlier)
```

## B3: what a later round is told

`harness/loop.py`

before:

```
(f"THIS IS ROUND {round_no} of at most {REVIEW_ROUNDS} for this test. The researcher repaired it after:\n{before}\n" if round_no > 1 else "")
```

after:

```
(f"THIS IS ROUND {round_no} of at most {REVIEW_ROUNDS} for this test. The test above is the researcher's answer to these rounds; it may be unchanged, so judge it as it stands and compare it with the "
                                                                                                                 f"earlier rounds. A test sent back in round {REVIEW_ROUNDS} is run all the same, marked as contested.\n{before}\n" if round_no > 1 else "")
```

## B3: the first round's test is kept for the later rounds

`harness/loop.py`

before:

```
        n, parent, earlier, refused, refused_runs = 1, gid, [(1, "the supervisor", rev["feedback"])], None, []
```

after:

```
        say = lambda t: "; ".join(f"{d.get('decision_rule')}" + (f" (competes with {d['competes_with']})" if d.get("competes_with") else "") for d in (t or {}).get("decision_rules") or [] if d.get("for") == hid) + " | simulations: " + ", ".join(str(r.get("label")) for r in (t or {}).get("runs") or [] if isinstance(r, dict))   # v2 (B3): a round's test in a line
        n, parent, earlier, refused, refused_runs = 1, gid, [(1, "the supervisor", rev["feedback"], say(test))], None, []
```

## B3

`harness/loop.py`

before:

```
                earlier.append((n, "the harness", problem))
```

after:

```
                earlier.append((n, "the harness", problem, say(t2)))
```

## B3

`harness/loop.py`

before:

```
            earlier.append((n, "the supervisor", rev["feedback"]))
```

after:

```
            earlier.append((n, "the supervisor", rev["feedback"], say(t2)))
```

## B11: what the supervisor is told about a declared competitor

`harness/loop.py`

before:

```
It explains the same result by another "
                      f"cause and may cite {why['competes_with']}'s records: here the defect repeats means that it names the same cause as {why['competes_with']}, and the question whether it comes from "
                      "what was learned since is not asked of it.\n")
```

after:

```
The researcher declares it a competitor of "
                      f"{why['competes_with']}, so it may cite {why['competes_with']}'s records without a new one: whether it is about the same result is for you to say; here the defect repeats means that it names the same cause as {why['competes_with']}.\n")
```

## B14: the two fields that ask it to name something

`harness/loop.py`

before:

```
You never propose a hypothesis, a setting or an experiment of your own.
```

after:

```
You never propose a hypothesis, a setting or an experiment of your own; only where a field asks what is missing or what a fair test would have to compare do you name it.
```

## B9: a test on a simulation that already ran

`harness/loop.py`

before:

```
That costs nothing and is a proper test, never by itself a reason to send it back: the defect already_answered means only "
              "that the very value the rule compares already stands in the ledger or in the tool results you are shown.
```

after:

```
That costs nothing and is a proper test as long as the value its rule compares, and the series it is computed from, are not already "
              "in the records you are shown.
```

## B14 (low): both costs are named

`harness/loop.py`

before:

```
a test that cannot tell whether the guess is true wastes simulations and puts a false certainty on record.
```

after:

```
a test that cannot tell whether the guess is true wastes simulations and puts a false certainty on record, and a sound test sent back wastes a round.
```

## item 4: the review's line in the ledger

`harness/loop.py`

before:

```
                + (" Honest {honest}, Consistent {consistent}, Correct {correct}.".format(**b) if b.get("honest") else "")   # the three questions (stage 5)
```

after:

```
                + ((f" Follows {b['follows']}," if b.get("follows") else "") + " Honest {honest}, Consistent {consistent}, Correct {correct}.".format(**b) if b.get("honest") else "")   # the questions (stage 5; Follows since v2)
```

## item 4: the researcher is told of the fourth question

`harness/loop.py`

before:

```
a test, before it runs, by three questions: can it fail (Honest), does it test your claim and only it (Consistent), does its rule give HELD under your guess and FAILED under the guess it competes with (Correct)? 
```

after:

```
a test, before it runs, by four questions: does your hypothesis follow from your guess (Follows), can the test fail (Honest), does it test your claim and only it (Consistent), does its rule give HELD under your guess and FAILED under the guess it competes with (Correct)? 
```
