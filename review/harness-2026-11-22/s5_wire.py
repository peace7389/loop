"""Stage 5 of the coherence audit (2026-11-22, night), part 3: the session with competitors. The answer format (competes_with in a rule and in a guess),
the instructions (COMP_LEAN: what is new, and three passages said shorter to stay within the one limit), the repair, the checks before any review,
"held" (a missing competitor; a test whose Consistent failed after the last round), what the ruling is given, the records (a guess's competitor and
"from feedback"; a ruling's three questions, fits and misses), gate 0 told of a declared competitor, no_cause. A session keeps what it started with
(session.json flags.competitors). Usage: s5_wire.py HARNESS_DIR"""
import sys
from pathlib import Path
H = Path(sys.argv[1])
p = H / "loop.py"; s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:110], s.count(a)); s = s.replace(a, b)

# ---- the instructions
rep('''def supervised_prompt(text):
    """The researcher's instructions in the arm "supervised": written for the short reply (LEAN_PROMPT), not made from prompt.txt."""
    return LEAN_PROMPT''', '''COMP_LEAN = (   # LEAN_PROMPT -> the instructions of a session with competitors (stage 5): (as it stands, what replaces it), each found once
    ("it is shown your guess, your hypothesis, your decision rule and its rival, the planned simulations", "it is shown your guess, your hypothesis, your decision rule and the guess it competes with, the planned simulations"),
    ("- a test, before it runs: can it tell your guess from your rival? If not, it says what is wrong and you repair that test at once, up to three rounds; the other tests run meanwhile;",
     "- a test, before it runs, by three questions: can it fail (Honest), does it test your claim and only it (Consistent), does its rule give HELD under your guess and FAILED under the guess it competes with (Correct)? "
     "If one fails, it says what is wrong and you repair that test at once, up to three rounds; the other tests run meanwhile;"),
    ("closes the hypothesis. You do not give verdicts.", "closes the hypothesis; a guess that does not fit the result of a fair test is refuted: no hypothesis comes from it, a new guess may revise it. You do not give verdicts."),
    ("The purpose of the work is to understand why the system behaves as it does. You are not an optimiser: do not try many settings and keep whichever comes out slightly ahead. Look at the system, ask why each result came out so, guess what in the system (not directly visible in the outputs) makes it so, and test that guess.",
     "The purpose is to understand why the system behaves as it does, not to optimise: look at it, ask why each result came out so, guess what in the system (not directly visible) makes it so, and test that guess."),
    ("(the ids of the records it starts from: evidence tables, simulations, checks or rulings, for example E0, S2, C1; a reading a tool returned, by its id, for example T7; a review in which the supervisor objected, for example G4; the word brief only when nothing is measured yet)",
     "(the ids of the records it starts from, for example E0, S2, C1, V1, a reading T7, an objection of the supervisor G4; the word brief only when nothing is measured yet)"),
    ("and revises (the id of an earlier guess this one replaces, or states more exactly with new numbers or a narrower cause; or null).",
     "revises (the id of an earlier guess this one replaces or states more exactly; or null), and competes_with (the id of an earlier guess whose result this one explains by another cause, or null; it may cite that guess's records). A guess that something makes no difference names its cause."),
    ("The work is a chain: your first guesses start from the baseline, and every later guess is the fruit of what you learned since: its about must name at least one record made since your last guesses (a ruling, a check, a new result table, a reading, an objection of the supervisor), and its result says what that record showed. A later guess that starts from the baseline alone is refused, and the supervisor reads whether the guess really comes from the newer record or only names it.",
     "The work is a chain: your first guesses start from the baseline; every later guess names in about a record made since your last guesses (a ruling, a check, a result table, a reading, an objection) and says in result what it showed, or competes with an earlier guess."),
    ("rival (the strongest competing explanation, one sentence) and rival_predicts (held or failed: what the rule gives if the rival is true; held is refused)",
     "competes_with (another live guess, not the hypothesis's own nor one linked to it by revises: write the competing explanation as a guess first) and rival_predicts (what the rule gives if that guess is true and yours false: failed; held is refused)"))


def supervised_prompt(text, competitors=False):
    """The researcher's instructions in the arm "supervised": written for the short reply (LEAN_PROMPT), not made from prompt.txt. competitors: the
    session's rules name the guess they compete with (COMP_LEAN; stage 5 of the coherence audit, 2026-11-22)."""
    out = LEAN_PROMPT
    for a_, b_ in COMP_LEAN if competitors else ():
        if out.count(a_) != 1:
            raise ValueError(f"LEAN_PROMPT: {a_[:60]!r}... stands {out.count(a_)} times; the instructions with competitors expect once")
        out = out.replace(a_, b_)
    return out''')
# ---- the answer format
rep('''def supervised_format(schema):''', '''def supervised_format(schema, competitors=False):''')
rep('''             "whys": {**P["whys"], "items": keep(P["whys"]["items"], ["about", "result", "guess", "revises"])},''',
    '''             "whys": {**P["whys"], "items": keep(P["whys"]["items"], ["about", "result", "guess", "revises"])},''')
rep('''    ex["properties"]["decision_rules"]["items"] = keep(ex["properties"]["decision_rules"]["items"], ["for", "decision_rule", "rival", "rival_predicts"])   # the rival is the researcher's since 2026-11-22 (after the reviews of s047 and s050)''',
    '''    if competitors:   # stage 5: a rule names the guess it competes with; a guess may name one
        CW = {"type": "string", "description": "the id of another live guess (for example Y3): not the hypothesis's own, nor one linked to it by revises"}
        ex["properties"]["decision_rules"]["items"]["properties"]["competes_with"] = CW
        ex["properties"]["decision_rules"]["items"]["properties"]["rival_predicts"] = {**ex["properties"]["decision_rules"]["items"]["properties"]["rival_predicts"], "description": "what this rule gives if that guess is true and the tested one false (held is refused)"}
        props["whys"]["items"]["properties"]["competes_with"] = {"anyOf": [{"type": "string", "pattern": "^Y[0-9]+$", "description": "the id of an earlier guess whose result this one explains by another cause"}, {"type": "null"}]}
        props["whys"]["items"]["required"] = list(props["whys"]["items"]["properties"])
    ex["properties"]["decision_rules"]["items"] = keep(ex["properties"]["decision_rules"]["items"], ["for", "decision_rule", "competes_with" if competitors else "rival", "rival_predicts"])   # the rival is the researcher's since 2026-11-22 (after the reviews of s047 and s050); a guess with competitors (stage 5)''')
rep('''    for w in t.get("whys") or []:
        if isinstance(w, dict):
            w.update({k: w.get(k, v) for k, v in (("unseen", ""), ("matters", ""), ("reason", ""), ("worth", "verify"))})''',
    '''    for w in t.get("whys") or []:
        if isinstance(w, dict):
            w.update({k: w.get(k, v) for k, v in (("unseen", ""), ("matters", ""), ("reason", ""), ("worth", "verify"), ("competes_with", None))})''')
# ---- main: the session's choice, kept
rep('''    if arm == "supervised":
        schema, system = supervised_format(schema), supervised_prompt(system)''', '''    competitors = arm == "supervised" and (json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("competitors", False) if was else COMPETITORS)   # a session keeps what it started with
    COMP["on"] = competitors
    if arm == "supervised":
        schema, system = supervised_format(schema, competitors), supervised_prompt(system, competitors)''')
rep('''"follow_up_tokens": AGAIN_TOKENS, ''', '''"follow_up_tokens": AGAIN_TOKENS, "questions": "honest, consistent, correct" if competitors else "rival and defect", ''')
rep('''**({"arm": arm} if arm != "hypotheses" else {"format": "short"} if short else {}),''', '''**({"arm": arm} if arm != "hypotheses" else {"format": "short"} if short else {}), **({"competitors": True} if competitors else {}),''')
# the repair: competes_with in place of the rival sentence
rep('''    repair_schema = {"type": "object", "additionalProperties": False, "required": ["decision_rule", "rival", "rival_predicts", "runs"], "properties": {   # a repaired test (the arm "supervised", 2026-11-22)
        "decision_rule": {"type": "string"}, "rival": {"type": "string"}, "rival_predicts": {"type": "string", "enum": ["held", "failed"]},''',
    '''    RV = "competes_with" if competitors else "rival"   # stage 5: the repair names an existing guess
    repair_schema = {"type": "object", "additionalProperties": False, "required": ["decision_rule", RV, "rival_predicts", "runs"], "properties": {   # a repaired test (the arm "supervised", 2026-11-22)
        "decision_rule": {"type": "string"}, RV: {"type": "string", **({"description": "the id of an existing live guess the rule competes with (not the hypothesis's own)"} if competitors else {})}, "rival_predicts": {"type": "string", "enum": ["held", "failed"]},''')
rep('''        rule = {"for": hid, "decision_rule": rp.get("decision_rule"), "rival": rp.get("rival"), "rival_predicts": rp.get("rival_predicts")}''',
    '''        rule = {"for": hid, "decision_rule": rp.get("decision_rule"), **({"competes_with": rp.get("competes_with")} if competitors else {"rival": rp.get("rival")}), "rival_predicts": rp.get("rival_predicts")}''')
rep('''        why = rival_problem(rule) or rule_size_problem(rule)
        if why:
            return t2, why''', '''        why = (competitor_problem(rule, ledger) if competitors else rival_problem(rule)) or rule_size_problem(rule)
        if why:
            return t2, why''')
rep('''        rules = "".join(f"  decision rule: {flat(d.get('decision_rule'))}\\n  rival: {flat(d.get('rival'))}\\n  rival_predicts: {d.get('rival_predicts')}\\n" for d in test.get("decision_rules") or [])''',
    '''        rules = "".join(f"  decision rule: {flat(d.get('decision_rule'))}\\n" + (f"  competes_with: {d.get('competes_with')}\\n" if competitors else f"  rival: {flat(d.get('rival'))}\\n") + f"  rival_predicts: {d.get('rival_predicts')}\\n" for d in test.get("decision_rules") or [])''')
rep('''f"min(), max(); one of < <= > >= == in each comparison; at most {COMPARISONS_MOST} comparisons, joined by AND and OR). rival: the strongest competing explanation you can think of, one sentence. "
                "rival_predicts: held or failed, what the rule gives if the rival is true (held is refused: choose simulations where the two differ). runs:''',
    '''f"min(), max(); one of < <= > >= == in each comparison; at most {COMPARISONS_MOST} comparisons, joined by AND and OR). "
                + ("competes_with: the id of an existing live guess the rule tells yours from (not your hypothesis's own guess nor one linked to it by revises); a competing cause you have not written as a guess cannot be named here: write it as a guess in your next reply. "
                   "rival_predicts: what the rule gives if that guess is true and yours false (held is refused: choose simulations where the two differ). " if competitors else
                   "rival: the strongest competing explanation you can think of, one sentence. rival_predicts: held or failed, what the rule gives if the rival is true (held is refused: choose simulations where the two differ). ")
                + "runs:''')
# the checks before any review
rep('''            why = rival_problem(d) or rule_size_problem(d)
            if why and d.get("for") not in bad:''', '''            why = (competitor_problem(d, ledger) if competitors else rival_problem(d)) or rule_size_problem(d)
            if why and d.get("for") not in bad:''')
rep('''                if any(rival_problem(d) or rule_size_problem(d) for d in ex0.get("decision_rules") or [] if d.get("for") == hid):''',
    '''                if any((competitor_problem(d, ledger) if competitors else rival_problem(d)) or rule_size_problem(d) for d in ex0.get("decision_rules") or [] if d.get("for") == hid):''')
# "held": a missing competitor; Consistent failed after the last round
rep('''        label = label or round_label(rev.get("approved"), n)''', '''        label = label or round_label(rev.get("approved"), n)
        if competitors and by == "supervisor" and not rev.get("approved") and (rev.get("missing") or (label == "contested" and rev.get("consistent") != "pass")):
            label = "held"   # stage 5: the competing cause is no guess yet (no repair this turn), or after the last round the test does not test its claim: not run, the hypothesis stays open''')
rep('''            gid, label = record_round(hid, 1, test, rev, saw)
            if label == "sent_back":''', '''            gid, label = record_round(hid, 1, test, rev, saw)
            if label == "held":
                held_note(hid, gid, rev)
                gone_h.append(hid)
                continue
            if label == "sent_back":''')
rep('''        held, gone = [], []
        for hid in ex["tests"]:''', '''        held, gone, gone_h = [], [], []
        for hid in ex["tests"]:''')
rep('''        out = without_tests(ex, [h for h, *_ in held] + gone) if held or gone else ex''', '''        out = without_tests(ex, [h for h, *_ in held] + gone + gone_h) if held or gone or gone_h else ex''')
rep('''            gid, label = record_round(hid, n, t2, rev, saw)
            if label == "approved":
                return t2''', '''            gid, label = record_round(hid, n, t2, rev, saw)
            if label == "held":
                held_note(hid, gid, rev)
                return None
            if label == "approved":
                return t2''')
rep('''    def drop_after(hid, feedback, n):''', '''    def held_note(hid, gid, rev):
        """A test held by the supervisor (stage 5): not run in this turn, and its hypothesis stays open; the note says why and what to do."""
        own = next((r["body"].get("from_why") for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), None)
        append(ledger, turn, "note", gid, {"text": (f"the test of {hid} is not run in this turn and {hid} stays open: the supervisor names a competing cause that is none of your guesses: {rev['missing']} "
                                                    f"Write it as a guess (competes_with: {own}), then test {hid} against it" if rev.get("missing") else
                                                    f"the test of {hid} is not run and {hid} stays open: after the last round it does not test its claim (Consistent failed): {rev.get('consistent_why')}"),
                                           "part": f"test of {hid}", "reason": "held by the supervisor"})

    def drop_after(hid, feedback, n):''')
# the ruling is given the last review's three answers; the verdict keeps the three questions, the fits and the misses
rep('''                ruling, saw = rule_on(model, brief, ledger, xid, hid, doubt, contested=objected.get(hid))''',
    '''                last_rev = next((r["body"] for r in reversed(ledger) if r["type"] == "review" and r.get("by") == "supervisor" and r["body"].get("gate") == "design" and r["body"].get("for") == hid), None)
                ruling, saw = rule_on(model, brief, ledger, xid, hid, doubt, contested=objected.get(hid), review=last_rev if competitors else None)''')
rep('''                                                       **({"changed_by_harness": ruling["changed_by_harness"]} if ruling.get("changed_by_harness") else {}), **({"contested": True} if objected.get(hid) else {})}, by="supervisor")''',
    '''                                                       **({"changed_by_harness": ruling["changed_by_harness"]} if ruling.get("changed_by_harness") else {}), **({"contested": True} if objected.get(hid) else {}),
                                                       **{k: ruling[k] for k in ("questions", "fits", "competes_with", "fits_again", "fits_contradicted", "misses") if ruling.get(k)}}, by="supervisor")''')
# a guess's competitor, and "from feedback"
rep('''                last = append(ledger, turn, "why", last, {k: w[k] for k in ("about", "result", "guess", "unseen", "matters", "worth", "reason")} | ({"revises": w["revises"]} if w.get("revises") else {})''',
    '''                fb = next((r["id"] for r in reversed(ledger) if r["type"] == "review" and r["body"].get("missing") and w.get("competes_with")
                           and next((q["body"].get("from_why") for q in ledger if q["type"] == "hypothesis" and q["id"] == r["body"].get("for")), None) == w["competes_with"]), None) if competitors else None
                last = append(ledger, turn, "why", last, {k: w[k] for k in ("about", "result", "guess", "unseen", "matters", "worth", "reason")} | ({"revises": w["revises"]} if w.get("revises") else {})
                              | ({"competes_with": w["competes_with"]} if w.get("competes_with") else {}) | ({"from_feedback": fb} if fb else {})''')
# gate 0: a declared competitor, and no_cause
rep('''GROUND_WARNINGS = ("not_from_what_was_learned",)''', '''GROUNDS_COMP = {**GROUNDS, "no_cause": "the guess says that something makes no difference, or that nothing happens, without naming what in the system would make it so"}   # stage 5
GROUND_SCHEMA_COMP = {**GROUND_SCHEMA, "properties": {**GROUND_SCHEMA["properties"], "defect": {"type": "string", "enum": list(GROUNDS_COMP), "description": "the one defect your reasoning ends in, or none"}}}
GROUND_WARNINGS = ("not_from_what_was_learned",)''')
p.write_text(s); print("wired (part a)")
