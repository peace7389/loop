"""Stage 5 of the coherence audit (2026-11-22, night), part 2: the supervisor's review and ruling with three questions, in a session with competitors.
Review (before the run): Honest (can the test fail?), Consistent (does the rule test what the hypothesis claims and only that, and does the competing
guess explain the same result?), Correct (what the rule gives if the tested guess is true and if the competing guess is true: pass only when held and
failed). The code checks the boxes against each other (Correct against the two predictions), asks one follow-up question on a contradiction and never
picks; approved only with all three passing. A cause the test needs that is no guess of the researcher's (missing): the test is held, with no repair
call, and its note names the cause. After the last round a test runs as contested only if Consistent passed; otherwise it is held.
Ruling (after the run): the same three questions with the result in hand, the result, and for each guess the test named whether it fits; fair is all
three passing; supported/refuted must fit the checks as before; the fits must fit the result of a fair test (one follow-up; still contradictory, the
fits are kept but refute nothing). A question the review passed and the ruling fails is a miss (foreseeable) or found by the result.
Usage: s5_questions.py HARNESS_DIR"""
import sys
from pathlib import Path
H = Path(sys.argv[1])
p = H / "loop.py"; s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:110], s.count(a)); s = s.replace(a, b)

rep('''GROUNDS = {"none": "no defect",''', '''QUESTIONS = {"honest": "can the test fail? Its result is not already known from the records, and its threshold is not one that almost any result passes",
             "consistent": "does the rule test what the hypothesis claims, and only that? The simulations it compares differ only in what the claim is about, its measure can see it, and the competing guess explains the same result",
             "correct": "does the rule come out differently under the two guesses: HELD if the tested guess is true, FAILED if the competing guess is true?"}
BOX = {"type": "string", "enum": ["pass", "fail"]}
GIVES = {"type": "string", "enum": ["held", "failed", "cannot tell"]}
REVIEW3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reads", "honest_why", "honest", "consistent_why", "consistent", "if_tested", "if_competitor", "correct_why", "correct", "missing", "feedback"], "properties": {
    "reads": {"type": "string", "description": "what the decision rule compares, in which simulations"},
    "honest_why": {"type": "string", "description": "one sentence, with record ids: can the test fail? (its result not already known from the records; a threshold that not almost any result passes)"},
    "honest": {**BOX, "description": "pass: it can fail"},
    "consistent_why": {"type": "string", "description": "one sentence, with record ids: does the rule test what the hypothesis claims and only that (its simulations differ only in what the claim is about, its measure can see it), and does the competing guess explain the same result?"},
    "consistent": {**BOX, "description": "pass: it tests the claim and only it, against a guess about the same result"},
    "if_tested": {**GIVES, "description": "what the rule gives if the tested guess is true and the competing guess false"},
    "if_competitor": {**GIVES, "description": "what the rule gives if the competing guess is true and the tested guess false"},
    "correct_why": {"type": "string", "description": "one sentence: why the rule gives those two outcomes"},
    "correct": {**BOX, "description": "pass only when if_tested is held and if_competitor is failed"},
    "missing": {"type": "string", "description": "when the competing cause this test needs is not among the researcher's guesses: that cause, in one sentence; else empty"},
    "feedback": {"type": "string", "description": "for the researcher: which question failed and the one problem that matters most, the record ids and numbers it rests on, and what a repaired test must achieve (empty when all pass). Never a decision rule, a measure@label, simulations or a network change"}}}
AGAIN3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["because", "if_tested", "if_competitor", "correct"], "properties": {
    "because": {"type": "string", "description": "your answer to the question, with the numbers or record ids it rests on"},
    "if_tested": {**GIVES, "description": "what the rule gives if the tested guess is true and the competing guess false"},
    "if_competitor": {**GIVES, "description": "what the rule gives if the competing guess is true and the tested guess false"},
    "correct": {**BOX, "description": "pass only when if_tested is held and if_competitor is failed"}}}
FORESEE = {"type": "string", "enum": ["yes", "no", "n/a"]}
RULING3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["shows", "honest_why", "honest", "honest_foreseeable", "consistent_why", "consistent", "consistent_foreseeable", "correct_why", "correct", "correct_foreseeable", "because", "result", "fits_tested", "fits_competitor", "retest", "findings"], "properties": {
    "shows": {"type": "string", "description": "what the measured numbers show, in one sentence, before any conclusion"},
    **{k: v for q in ("honest", "consistent", "correct") for k, v in ((f"{q}_why", {"type": "string", "description": f"one sentence, with the result in hand and record ids: {QUESTIONS[q]}"}), (q, BOX),
        (f"{q}_foreseeable", {**FORESEE, "description": "only when this question passed at the review before the run and fails now: could the problem have been seen before the simulations ran? Otherwise n/a"}))},
    "because": {"type": "string", "description": "your reasoning from the numbers to the result: written before you give it"},
    "result": {"type": "string", "enum": ["supported", "refuted", "inconclusive"], "description": "supported: every check held and all three questions pass; refuted: a check failed and all three pass; inconclusive: otherwise"},
    "fits_tested": {"type": "string", "enum": ["fits", "does not fit"], "description": "whether the tested guess fits this result"},
    "fits_competitor": {"type": "string", "enum": ["fits", "does not fit"], "description": "whether the competing guess fits this result"},
    "retest": {"type": "string", "description": "when the result is inconclusive: what a fair test would have to compare; else empty"},
    "findings": {"type": "array", "maxItems": 2, "items": None, "description": "what the measured results leave unexplained (what, never why), at most 2; empty when nothing"}}}   # items: FINDING_ITEM, set where it is defined
FITS_AGAIN_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["because", "fits_tested", "fits_competitor"], "properties": {
    "because": {"type": "string", "description": "your answer to the question"},
    "fits_tested": {"type": "string", "enum": ["fits", "does not fit"]}, "fits_competitor": {"type": "string", "enum": ["fits", "does not fit"]}}}
GROUNDS = {"none": "no defect",''')
rep('''RULING_SCHEMA["properties"]["findings"]["items"] = FINDING_ITEM''', '''RULING_SCHEMA["properties"]["findings"]["items"] = FINDING_ITEM
RULING3_SCHEMA["properties"]["findings"]["items"] = FINDING_ITEM''') if 'RULING_SCHEMA["properties"]["findings"]["items"] = FINDING_ITEM' in s else None

# the competing guess in the case the supervisor is shown
rep('''    theirs = "".join(f"THE RESEARCHER'S RIVAL for this rule: {flat(d.get('rival'))}\\nWHAT THE RESEARCHER SAYS THE RULE GIVES IF THAT RIVAL IS TRUE: {str(d.get('rival_predicts')).upper()}\\n" for d in rules)''',
    '''    theirs = "".join(f"THE RESEARCHER'S RIVAL for this rule: {flat(d.get('rival'))}\\nWHAT THE RESEARCHER SAYS THE RULE GIVES IF THAT RIVAL IS TRUE: {str(d.get('rival_predicts')).upper()}\\n" for d in rules) if not COMP["on"] else competitor_text(ledger, rules, ex)''')
rep('''    ask = ("Before any of these simulations is run: can this test tell the guess from the researcher's rival?''', '''    ask = QUESTIONS_ASK if COMP["on"] else ("Before any of these simulations is run: can this test tell the guess from the researcher's rival?''')
rep('''    d = pre if pre is not None else (ask_fn or supervise)(model, user, REVIEW_SCHEMA)   # pre: its answer in the batched first review
    predicts =''', '''    d = pre if pre is not None else (ask_fn or supervise)(model, user, REVIEW3_SCHEMA if COMP["on"] else REVIEW_SCHEMA)   # pre: its answer in the batched first review
    if COMP["on"]:   # the three questions (stage 5)
        return _review3(model, d, user, hid, rules, round_no, ask_fn, pre, pre_saw)
    predicts =''')
rep('''def gkey(w):''', '''QUESTIONS_ASK = ("Before any of these simulations is run, answer three questions about this test, each with one sentence that cites record ids, then its box. Honest: "
                 + QUESTIONS["honest"] + ". Consistent: " + QUESTIONS["consistent"] + ". Correct: say what the rule gives if the tested guess is true and the competing guess false, and "
                 "what it gives if the competing guess is true and the tested guess false; pass only when the first is HELD and the second FAILED. Judge the competing guess the researcher "
                 "named, do not replace it with your own; if the cause this test needs is none of the researcher's guesses, name it in missing. Last, feedback for the researcher: which "
                 "question failed and the one problem that matters most, the record ids and numbers it rests on, and what a repaired test must achieve. The feedback never contains a "
                 "decision rule, a measure@label, simulations or a network change: the researcher must find the repair itself. A test is not wanting for being small or for testing only "
                 "one consequence of the guess.")


def competitor_text(ledger, rules, ex=None):
    """The guess each rule competes with, as the supervisor is shown it (stage 5): its result and its guess, from the ledger or from the reply at hand."""
    flat = lambda v: " ".join(str(v).split())
    whys = {r["id"]: r["body"] for r in ledger if r["type"] == "why"}
    out = ""
    for d in rules:
        w = whys.get(d.get("competes_with")) or {}
        out += (f"THE GUESS THIS RULE COMPETES WITH [{d.get('competes_with')}]: the result it explains: {flat(w.get('result'))} | its guess: {flat(w.get('guess'))}\\n"
                f"WHAT THE RESEARCHER SAYS THE RULE GIVES IF THAT GUESS IS TRUE AND THE TESTED ONE FALSE: {str(d.get('rival_predicts')).upper()}\\n")
    return out


def _review3(model, d, user, hid, rules, round_no, ask_fn, pre, pre_saw):
    """The three questions' review of one test (stage 5): (review, what it was shown). The boxes are read as given; Correct is checked against the two
    predictions (pass only with HELD and FAILED); on a contradiction one follow-up question, and still contradictory it is a refusal."""
    flat = lambda v: " ".join(str(v).split())
    box = lambda v: v if v in ("pass", "fail") else "fail"
    gives = lambda v: v if v in ("held", "failed", "cannot tell") else "cannot tell"
    rev = {"reads": flat(d.get("reads")), **{k: flat(d.get(k)) for k in ("honest_why", "consistent_why", "correct_why")}, **{q: box(d.get(q)) for q in ("honest", "consistent", "correct")},
           "if_tested": gives(d.get("if_tested")), "if_competitor": gives(d.get("if_competitor")), "missing": flat(d.get("missing") or ""), "feedback": flat(d.get("feedback") or ""),
           "competes_with": next((x.get("competes_with") for x in rules if x.get("competes_with")), None), "defect": "none"}
    def clash_of(r):   # what contradicts what, or None
        differs = r["if_tested"] == "held" and r["if_competitor"] == "failed"
        if r["correct"] == "pass" and not differs:
            return f"you passed Correct, but you said the rule gives {r['if_tested'].upper()} if the tested guess is true and {r['if_competitor'].upper()} if the competing guess is true: pass needs HELD and FAILED"
        if r["correct"] == "fail" and differs:
            return "you failed Correct, but you said the rule gives HELD if the tested guess is true and FAILED if the competing guess is true: then the two guesses give different outcomes"
        return None
    clash = clash_of(rev)
    if clash:
        q = (user + f"\\n\\nYOUR REVIEW: Correct {rev['correct']}; if the tested guess is true the rule gives {rev['if_tested'].upper()}; if the competing guess {rev['competes_with']} is true, "
             f"{rev['if_competitor'].upper()}. These do not fit together: {clash}. One question: if {rev['competes_with']} were true and the tested guess false, what would this rule give, and if the "
             "tested guess were true? Answer it, then give the two outcomes and the box Correct again.")
        try:
            stage("design", hid, round_no, again=True)
            a = (ask_fn or (lambda m, u, sc: supervise(m, u, sc, AGAIN_TOKENS)))(model, q, AGAIN3_SCHEMA)
            if not isinstance(a, dict):
                raise ValueError("not an object")
        except (ValueError, KeyError, TypeError) as e:   # unreadable: the contradiction stands, a refusal
            a = None
            rev["again"] = {"question": clash, "unread": type(e).__name__, "still": clash}
        if a is not None:
            again = {"question": clash, "because": flat(a.get("because")), "if_tested": gives(a.get("if_tested")), "if_competitor": gives(a.get("if_competitor")), "correct": box(a.get("correct"))}
            rev["again"] = again
            clash2 = clash_of({**rev, **{k: again[k] for k in ("if_tested", "if_competitor", "correct")}})
            if clash2:
                rev["again"]["still"] = clash2
            else:
                rev.update({k: again[k] for k in ("if_tested", "if_competitor", "correct")})
        user = q + "\\n[the answer: " + (json.dumps(a) if a is not None else "could not be read") + "]"
    ok = not (rev.get("again") or {}).get("still") and not (clash and "again" not in rev) and all(rev[q] == "pass" for q in ("honest", "consistent", "correct"))
    failed = [q for q in ("honest", "consistent", "correct") if rev[q] == "fail"]
    rev["defect"] = failed[0] if failed else ("contradiction" if not ok else "none")   # which question failed (the figures and the page read the three boxes)
    if not ok and not rev["feedback"]:   # a refusal always says what is wrong
        rev["feedback"] = ("; ".join(f"{q.capitalize()} failed: {rev[q + '_why']}" for q in failed) if failed else
                           "the supervisor's review contradicted itself: " + (rev.get("again", {}).get("still") or clash or "").replace("you passed", "it passed").replace("you failed", "it failed").replace("you said", "it said"))
    if RULE_IN_TEXT.search(rev["feedback"]):
        bits = re.split(r"(?<=[.;!?])\\s+", rev["feedback"])
        kept = [x for x in bits if not RULE_IN_TEXT.search(x)]
        rev["feedback"], rev["cut"] = " ".join(kept) or "(the harness cut the whole feedback: it wrote a decision rule)", len(bits) - len(kept)
    rev["approved"] = ok
    rev["rival"] = ""
    if pre is not None:
        user = (pre_saw or "") + "\\n\\n[this test was answered in the batched first review of the turn]" + (f"\\n\\n[then asked alone]:\\n{user}" if rev.get("again") else "")
    return rev, user


def gkey(w):''')
# the batch: the three questions' items
rep('''    t_item = {"type": "object", "additionalProperties": False, "required": ["for"] + REVIEW_SCHEMA["required"],
              "properties": {"for": {"type": "string", "description": "the hypothesis whose test this item reviews, as its heading names it"}, **REVIEW_SCHEMA["properties"]}}''',
    '''    R = REVIEW3_SCHEMA if COMP["on"] else REVIEW_SCHEMA
    t_item = {"type": "object", "additionalProperties": False, "required": ["for"] + R["required"],
              "properties": {"for": {"type": "string", "description": "the hypothesis whose test this item reviews, as its heading names it"}, **R["properties"]}}''')

# the ruling: three questions
rep('''def rule_on(model, brief, ledger, xid, hid, doubt_if, ask_fn=None, contested=None):''', '''def rule_on(model, brief, ledger, xid, hid, doubt_if, ask_fn=None, contested=None, review=None):''')
rep('''            + (f"BEFORE IT RAN, the review of this test ended with you still objecting, after the last round: {flat(contested)}\\n\\n" if contested else "")   # contested (2026-11-22)''',
    '''            + (f"BEFORE IT RAN, the review of this test ended with you still objecting, after the last round: {flat(contested)}\\n\\n" if contested else "")   # contested (2026-11-22)
            + (("AT THE REVIEW BEFORE THE RUN you answered: " + "; ".join(f"{q.capitalize()} {review.get(q)}: {flat(review.get(q + '_why'))}" for q in ("honest", "consistent", "correct"))
                + f" (the rule gives {str(review.get('if_tested')).upper()} if the tested guess is true, {str(review.get('if_competitor')).upper()} if {review.get('competes_with')} is true)\\n\\n") if COMP["on"] and review else "")''')
rep('''    d = (ask_fn or supervise)(model, user, RULING_SCHEMA)
    res = [c["body"]["result"] for c in checks]''', '''    if COMP["on"]:   # the same three questions with the result in hand (stage 5)
        return _rule3(model, ledger, user, hid, checks, review, ask_fn)
    d = (ask_fn or supervise)(model, user, RULING_SCHEMA)
    res = [c["body"]["result"] for c in checks]''')
rep('''def answer_objection(model, brief, ledger, verdict, objection, ask_fn=None):''', '''RULING3_ASK = ("Answer the three questions again with the result in hand, each with one sentence that cites record ids, then its box: Honest: " + QUESTIONS["honest"]
               + ". Consistent: " + QUESTIONS["consistent"] + ". Correct: " + QUESTIONS["correct"] + " For a question that passed at the review and fails now, say whether the problem could have "
               "been seen before the run (foreseeable). Then your reasoning, the result (supported: every check HELD and all three pass; refuted: a check FAILED and all three pass; inconclusive: "
               "otherwise), and whether each guess the test named fits this result.")


def _rule3(model, ledger, user, hid, checks, review, ask_fn):
    """The ruling with the three questions (stage 5): (ruling, what it was shown). fair is all three passing; the result must fit the checks and the fits
    must fit the result of a fair test (one follow-up question; still contradictory, the fits are kept but refute nothing). A question the review passed
    and the ruling fails is a miss when it was foreseeable, else found by the result."""
    flat = lambda v: " ".join(str(v).split())
    user = user.replace("What does this test show about the hypothesis? supported:", RULING3_ASK + "\\n\\nThe earlier wording, for the defects only: supported:", 1)
    d = (ask_fn or supervise)(model, user, RULING3_SCHEMA)
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
        q = (user + f"\\n\\nYOUR RULING: {result}, a fair test; the tested guess {own}: {given['tested']}; the competing guess {cw}: {given['competitor']}. These do not fit together: a fair test "
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


def answer_objection(model, brief, ledger, verdict, objection, ask_fn=None):''')
p.write_text(s); print("questions patched")
