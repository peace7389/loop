"""Stage 2 of the coherence audit (2026-11-22), the texts each arm is told (items 15, 16, 22-24):
15. the arm "plain" is told nothing about hypotheses, decision rules or verdicts: its own wording of the network-change sentences (STRUCTURE), of the
    last turn, the free turns, a continued reply, and of the brief's how_to_run; its whole system text is checked for those words at the start;
16. the arm "supervised": no "rethink it" in its ledger text; its report has open_questions (it was told to use them, then blamed); a checked
    hypothesis without a ruling may be dropped (only the supervisor rules, and a lost ruling left it with no exit); a from_why refusal speaks of guesses,
    not of "worth";
22-24. every arm: how_to_run says a run states every knob; the free turns say a test on simulations already run is decided by a measurement of its own;
    a label has at most LABEL_MOST characters, in the instructions, the answer format and the refusal.
Usage: s2_texts.py loop LOOP_PY | prompt PROMPT_TXT"""
import sys
from pathlib import Path
kind, p = sys.argv[1], Path(sys.argv[2]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)
if kind == "prompt":
    rep("each with a label of its own (letters, digits and _ only) and params", "each with a label of its own (letters, digits and _ only, at most 20 characters) and params")
else:
    rep('''REQUESTS_MOST = 3   #''', '''LABEL_MOST = 20   # a simulation's label: letters, digits and _, at most this many (the refusal, the answer format's maxLength, prompt.txt and LEAN_PROMPT say it)
PLAIN_WORDS = ("hypothes", "verdict", "decision rule", "decision_rule", "rethink")   # what the arm "plain" is never told about (checked on its whole system text)
HOW_TO_RUN = {   # the brief's how_to_run as each arm is shown it (the coherence audit, 2026-11-22: "the params that differ from the defaults", though a run states every knob; the plain arm was told of decision rules)
    "plain": "An experiment is a set of simulations with one purpose, run at once. Fill the 'experiment' field of your answer: its question and the simulations (runs: a label and a value for every knob). The harness runs the simulations and appends the evidence (one line per simulation).",
    "other": "An experiment is a set of simulations with one purpose, run at once. Fill the 'experiment' field of your answer: its kind (test or explore), the simulations (runs: a label and a value for every knob), and for a test the decision rules, comparisons stated before the simulations run. The harness runs the simulations, appends the evidence (one line per simulation) and checks every decision rule itself."}
STRUCTURE_PLAIN = (("a decision rule may only name a measure that exists in every simulation it names", "an experiment's simulations are compared on the measures that exist in every one of them"),
                   ("A change of structure is a hypothesis like any other: say what it should change and why, before you run it.", "Say what a change of structure should change and why, before you run it."))
REQUESTS_MOST = 3   #''')
    rep('''    if len(set(labels)) != len(labels) or not all(re.fullmatch(r"[A-Za-z0-9_]{1,20}", str(l)) for l in labels):
        return "every simulation needs its own label: letters, digits and _ only, at most 20 characters"''',
        '''    if len(set(labels)) != len(labels) or not all(re.fullmatch(rf"[A-Za-z0-9_]{{1,{LABEL_MOST}}}", str(l)) for l in labels):
        return f"every simulation needs its own label: letters, digits and _ only, at most {LABEL_MOST} characters"''')
    rep("   - runs: the simulations, each with a label of its own (letters, digits and _) and params", "   - runs: the simulations, each with a label of its own (letters, digits and _, at most 20 characters) and params")
    # 15: the plain arm's network text and its whole-text check; the label's maxLength
    rep('''    if may_change(brief):  # only a session that may change the structure is told how
        system += STRUCTURE''', '''    if may_change(brief):  # only a session that may change the structure is told how
        plain_s = STRUCTURE
        for a_, b_ in STRUCTURE_PLAIN if arm == "plain" else ():
            assert plain_s.count(a_) == 1, a_
            plain_s = plain_s.replace(a_, b_)
        system += plain_s''')
    rep('''    if isinstance(schema["properties"].get("requests"), dict):   # the most requests a reply may hold, in the answer format too (the coherence audit, 2026-11-22)''',
        '''    if arm == "plain" and [w for w in PLAIN_WORDS if w in system.lower()]:   # the plain arm is told nothing of hypotheses (the coherence audit, 2026-11-22: STRUCTURE was added after plain_prompt's check)
        raise ValueError(f"the instructions of the arm 'plain' name: {', '.join(w for w in PLAIN_WORDS if w in system.lower())}")
    try:   # a label's length, in the answer format too
        schema["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["label"]["maxLength"] = LABEL_MOST
    except (KeyError, IndexError, TypeError):
        pass
    if isinstance(schema["properties"].get("requests"), dict):   # the most requests a reply may hold, in the answer format too (the coherence audit, 2026-11-22)''')
    # how_to_run per arm, in the brief the researcher is shown
    rep('''            user = findings_block(ledger, turn, mode) + (f"BRIEF:\\n{json.dumps(brief, indent=1)}''', '''            shown = {**brief, "how_to_run": HOW_TO_RUN["plain" if arm == "plain" else "other"]} if "how_to_run" in brief else brief
            user = findings_block(ledger, turn, mode) + (f"BRIEF:\\n{json.dumps(shown, indent=1)}''')
    # the last turn, the free turns, a continued reply: per arm
    rep('''            last_ask = "Write the final report (report). The rulings on the tested hypotheses are the supervisor's; none is owed by you." if arm == "supervised" else ((''',
        '''            last_ask = "Write the final report (report). The rulings on the tested hypotheses are the supervisor's; none is owed by you." if arm == "supervised" else "Write the final report (report)." if arm == "plain" else ((''')
    rep('''                    "to look further and to test on the simulations already run: requests, guesses and their rethinks, hypotheses, and tests whose simulations have all run "
                    "already (their results are returned, not run again; measurements you define are computed from what they recorded). An experiment that needs a new "''',
        '''                    + {"plain": "to look further: requests, and experiments whose simulations have all run already (their results are returned, not run again). ",
                       "supervised": "to look further and to test on the simulations already run: requests, guesses, hypotheses, and tests whose simulations have all run already. ",
                       "hypotheses": "to look further and to test on the simulations already run: requests, guesses and their rethinks, hypotheses, and tests whose simulations have all run already. "}[arm]
                    + ("" if arm == "plain" else "What those simulations gave is known, so a test on them is decided by a measurement you define for it (computed from what they recorded): a rule on their outputs alone cannot fail and is refused. ")
                    + "An experiment that needs a new "''')
    rep('''                user += (f"\\n\\nTHIS TURN GOES ON (your reply {stay + 1} in this turn, at most {CONTINUES + 1}): your last reply stated no hypothesis, test, drop, verdict or report, "
                         "and what it asked for is answered in the LEDGER above. A turn ends with a step: " + ("state your hypotheses and their test now. Requests in this reply are answered "
                         "too, and you are asked once more in this turn." if stay < CONTINUES else "this is the last reply of this turn, so state your hypotheses and their test now "
                         "(what this reply asks for is answered, and shown to you in the next turn)."))''',
        '''                step_is, step_now = ("an experiment or a report", "state your experiment now") if arm == "plain" else ("a hypothesis, test, drop, verdict or report" if arm == "hypotheses" else "a hypothesis, test, drop or report", "state your hypotheses and their test now")
                user += (f"\\n\\nTHIS TURN GOES ON (your reply {stay + 1} in this turn, at most {CONTINUES + 1}): your last reply stated no {step_is}, "
                         "and what it asked for is answered in the LEDGER above. A turn ends with a step: " + (f"{step_now}. Requests in this reply are answered "
                         "too, and you are asked once more in this turn." if stay < CONTINUES else f"this is the last reply of this turn, so {step_now} "
                         "(what this reply asks for is answered, and shown to you in the next turn)."))''')
    # 16: no rethink note where there are no rethinks; open_questions in the supervised report; drop; the from_why refusal
    rep('''def render(ledger, readings=True):''', '''def render(ledger, readings=True, rethinks=True):''')
    rep('''        st[y] = {**w, "stale": since(ledger, w["at"]) if w["worth"] == "verify" else [], "idle": w["worth"] == "verify" and not any(r["type"] == "hypothesis" and r["body"].get("from_why") == y for r in ledger)}''',
        '''        st[y] = {**w, "stale": since(ledger, w["at"]) if w["worth"] == "verify" and rethinks else [], "idle": w["worth"] == "verify" and not any(r["type"] == "hypothesis" and r["body"].get("from_why") == y for r in ledger)}   # rethinks: only the arm "hypotheses" has them (the coherence audit, 2026-11-22)''')
    rep('''            text = render(ledger, readings=arm == "supervised")''', '''            text = render(ledger, readings=arm == "supervised", rethinks=arm == "hypotheses")''')
    rep('''    keep(rp, [k for k in ("goal", "recommendation", "structure", "limit", "explanation", "claims") if k in rp["properties"]])''',
        '''    keep(rp, [k for k in ("goal", "recommendation", "structure", "limit", "explanation", "claims", "open_questions") if k in rp["properties"]])   # open_questions: the findings text asks for it (the coherence audit, 2026-11-22)''')
    rep('''        elif d.get("id") in checked and st.get(d["id"]) == "open":
            no.append((part, f"{d['id']} has a checked decision rule, so it cannot be dropped: it needs a verdict (supported, refuted or inconclusive) instead"))''',
        '''        elif d.get("id") in checked and st.get(d["id"]) == "open" and not supervised:   # the arm "supervised": only the supervisor rules; a checked hypothesis still open has no ruling, and may be dropped (the coherence audit, 2026-11-22)
            no.append((part, f"{d['id']} has a checked decision rule, so it cannot be dropped: it needs a verdict (supported, refuted or inconclusive) instead"))''')
    rep('''            no.append(("new hypothesis", "a hypothesis comes from a why you chose to verify: from_why must be the id of a why whose worth is verify, one in the ledger or one of this answer "''',
        '''            no.append(("new hypothesis", ("a hypothesis comes from a guess: from_why must be the id of a guess, one in the ledger or one of this answer " if supervised else
                                          "a hypothesis comes from a why you chose to verify: from_why must be the id of a why whose worth is verify, one in the ledger or one of this answer ")''')
    rep('''                                         f"(the harness numbers new whys in order: the first new one is Y{n_why + 1})"''',
        '''                                         + f"(the harness numbers new {'guesses' if supervised else 'whys'} in order: the first new one is Y{n_why + 1})"''')
p.write_text(s); print("patched", kind, p)
