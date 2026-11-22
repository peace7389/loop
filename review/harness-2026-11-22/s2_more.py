"""Stage 2 of the coherence audit (2026-11-22), items 17-22 and 25 (loop.py; decision_rules.py with the argument "rules"):
17. the follow-up question shows the supervisor its own stronger rival and feedback, may change its box rival_is_weak, gets a thinking budget of
    1,000 tokens (the operator's choice), and one that cannot be read is a refusal (it was a run unreviewed);
18. a harness refusal in the last round is "not_run", by the harness (it was recorded as the supervisor's "contested");
19. the repair prompt: runs given replace those of the same label and add new ones (the prompt said "only if they must change", while any list
    replaced all); the exemption for a measurement of the test's own; the records the feedback cites; every measurement of the answer; a network
    change's form, with an example built and checked on the brief;
20. the ruling and the objection's second look see the rivals judged at the review and the measurement definitions; the second look sees the
    readings and says whether the test was fair;
21. a ruling asked for again is in the ledger text of the turn that asks for it;
22. continued replies: turns with requests only are counted by turn; a due finding's note says when it is asked for again;
25. == within the tolerance; an unread guess review is shown as unread; gate 0's "refused once" is per turn; learned_since leaves out the
    harness's reviews and counts simulations; the restatement is shown the records, not only their ids; calls are counted by agent; a report
    given with an experiment waits for that experiment's results."""
import sys
from pathlib import Path
kind, p = sys.argv[1], Path(sys.argv[2]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a))
    s = s.replace(a, b)
if kind == "rules":
    rep('''COMPARE = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b, "==": lambda a, b: a == b}''',
        '''EQUAL_WITHIN = 0.0   # per cent: == holds for two values that differ by less than this (the harness sets it to the session's tolerance; the coherence audit, 2026-11-22: == was exact)
COMPARE = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
           "==": lambda a, b: a == b or abs(a - b) < EQUAL_WITHIN / 100 * max(abs(a), abs(b))}''')
    p.write_text(s); print("patched", kind, p); sys.exit()

# ---- 17: the follow-up question
rep('''AGAIN_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["because", "rival_outcome", "defect"], "properties": {
    "because": {"type": "string", "description": "your answer to the question, with the numbers or record ids it rests on"},''',
    '''AGAIN_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["because", "stronger_rival", "rival_is_weak", "rival_outcome", "defect"], "properties": {
    "because": {"type": "string", "description": "your answer to the question, with the numbers or record ids it rests on"},
    "stronger_rival": {"type": "string", "description": "the strongest competing explanation after your answer: a stronger one your review or feedback named, or say why the researcher's is the strongest"},
    "rival_is_weak": {"type": "boolean", "description": "true when there is a clearly stronger rival than the researcher's"},''')
rep('''SUPERVISOR_FILE = "supervisor.jsonl"''', '''AGAIN_TOKENS = 2000   # the supervisor's follow-up question: 1,000 of them reasoning (the operator, 2026-11-22: a thinking budget of 1,000)
SUPERVISOR_FILE = "supervisor.jsonl"''')
rep('''def supervise(model, user, schema):''', '''def supervise(model, user, schema, max_tokens=9000):''')
rep('''    content = called("supervisor", model, SUPERVISOR, user, schema, True, 0, 9000)[0]''', '''    content = called("supervisor", model, SUPERVISOR, user, schema, True, 0, max_tokens)[0]''')
rep('''        q = (user + f"\\n\\nYOUR REVIEW: defect {rev['defect']}; under the rival the rule would give {rev['rival_outcome'].upper()}; a clearly stronger rival: {'yes' if rev['rival_is_weak'] else 'no'}. "
             f"These do not fit together: {clash}. One question: under the rival (the researcher's, or the stronger one you named), would this rule give {predicts.upper()}, as the researcher says, "
             "or not? Answer it, then give the outcome under the rival and the defect again.")
        a = (ask_fn or supervise)(model, q, AGAIN_SCHEMA)
        again = {"question": clash, "because": flat(a.get("because")), "rival_outcome": a.get("rival_outcome") if a.get("rival_outcome") in ("held", "failed", "cannot tell") else "cannot tell",
                 "defect": a.get("defect") if a.get("defect") in DEFECTS else "none"}
        rev["again"] = again
        ok, clash2 = judge({**rev, "rival_outcome": again["rival_outcome"], "defect": again["defect"]})
        if clash2:   # still contradictory: a refusal
            ok = False
            rev["again"]["still"] = clash2
        else:
            rev["rival_outcome"], rev["defect"] = again["rival_outcome"], again["defect"]
        user = q + "\\n[the answer: " + json.dumps(a) + "]"''',
    '''        # the question shows the rival the review itself named, and its box rival_is_weak may change (the coherence audit, 2026-11-22: s052 H2's feedback
        # named a stronger rival, the question asked only about the researcher's, the test was approved, and it was ruled inconclusive for that very rival)
        q = (user + f"\\n\\nYOUR REVIEW: defect {rev['defect']}; under the rival the rule would give {rev['rival_outcome'].upper()}; a clearly stronger rival: {'yes' if rev['rival_is_weak'] else 'no'}. "
             f"The strongest rival you named: {rev['stronger_rival'] or '(none)'} Your feedback: {rev['feedback'] or '(none)'}\\n"
             f"These do not fit together: {clash}. One question: take the strongest rival there is, the researcher's or one your review or feedback names; under it, would this rule give "
             f"{predicts.upper()}, as the researcher says, or not? Answer it; then say again which rival is the strongest and whether it is clearly stronger than the researcher's, "
             "the outcome under it, and the defect.")
        try:
            stage("design", hid, round_no, again=True)
            a = (ask_fn or (lambda m, u, s: supervise(m, u, s, AGAIN_TOKENS)))(model, q, AGAIN_SCHEMA)
            if not isinstance(a, dict):
                raise ValueError("not an object")
        except (ValueError, KeyError, TypeError) as e:   # a follow-up that cannot be read leaves the contradiction standing: a refusal (it was a run unreviewed)
            a = None
            ok = False
            rev["again"] = {"question": clash, "unread": f"{type(e).__name__}", "still": clash}
        if a is not None:
            again = {"question": clash, "because": flat(a.get("because")), "stronger_rival": flat(a.get("stronger_rival") or rev["stronger_rival"]), "rival_is_weak": bool(a.get("rival_is_weak")),
                     "rival_outcome": a.get("rival_outcome") if a.get("rival_outcome") in ("held", "failed", "cannot tell") else "cannot tell", "defect": a.get("defect") if a.get("defect") in DEFECTS else "none"}
            rev["again"] = again
            ok, clash2 = judge({**rev, "rival_is_weak": again["rival_is_weak"], "rival_outcome": again["rival_outcome"], "defect": again["defect"]})
            if clash2:   # still contradictory: a refusal
                ok = False
                rev["again"]["still"] = clash2
            else:
                rev["rival_is_weak"], rev["stronger_rival"], rev["rival_outcome"], rev["defect"] = again["rival_is_weak"], again["stronger_rival"], again["rival_outcome"], again["defect"]
        user = q + "\\n[the answer: " + (json.dumps(a) if a is not None else "could not be read") + "]"''')

# ---- 18: "not_run" for a harness refusal in the last round
rep('''    def record_round(hid, n, test, rev, saw, by="supervisor"):
        """One round of the review of a test: the test as proposed, the boxes and the feedback, the round and the decision. By the supervisor, or by the
        harness when its own checks refused the repaired test. Returns (the record's id, the decision)."""
        label = round_label(rev.get("approved"), n)''',
    '''    def record_round(hid, n, test, rev, saw, by="supervisor", label=None):
        """One round of the review of a test: the test as proposed, the boxes and the feedback, the round and the decision. By the supervisor, or by the
        harness when its own checks refused the repaired test (in the last round: not_run, the coherence audit, 2026-11-22: it was "contested", the
        supervisor's word, for a test that did not run). Returns (the record's id, the decision)."""
        label = label or round_label(rev.get("approved"), n)''')
rep('''                gid, label = record_round(hid, n, t2, {"approved": False, "feedback": problem, "because": problem, "defect": "none"}, "", by="harness")
                if label != "sent_back":   # the last round: a test the harness cannot use is not run, contested or not
                    if label == "dropped":
                        drop_after(hid, problem, n)
                    else:
                        append(ledger, turn, "note", gid, {"text": f"the test of {hid} is not run: its last repair could not be used ({problem}); {hid} stays open"})
                    return None''',
    '''                gid, label = record_round(hid, n, t2, {"approved": False, "feedback": problem, "because": problem, "defect": "none"}, "", by="harness", label="not_run" if n >= REVIEW_ROUNDS else None)
                if label != "sent_back":   # the last round: a test the harness cannot use is not run, and its hypothesis stays open (the harness's refusal is no objection of the supervisor's)
                    append(ledger, turn, "note", gid, {"text": f"the test of {hid} is not run: its last repair could not be used ({problem}); {hid} stays open"})
                    return None''')
rep('''        verdict = {"approved": "approved", "sent_back": "SENT BACK, and repaired in the same turn", "contested": "run, but the supervisor still objects after the last round", "dropped": "refused in the last round: the hypothesis is dropped"}.get(b["decision"], b["decision"])''',
    '''        verdict = {"approved": "approved", "sent_back": "SENT BACK, and repaired in the same turn", "contested": "run, but the supervisor still objects after the last round", "dropped": "refused in the last round: the hypothesis is dropped",
                   "not_run": "not run: the harness could not use the last repair, and the hypothesis stays open"}.get(b["decision"], b["decision"])''')

# ---- 19: the repair prompt, and the repaired test
rep('''        rule = {"for": hid, "decision_rule": rp.get("decision_rule"), "rival": rp.get("rival"), "rival_predicts": rp.get("rival_predicts")}
        runs = [r for r in rp["runs"] if isinstance(r, dict)] if isinstance(rp.get("runs"), list) and rp["runs"] else [dict(r) for r in every]
        t2 = {"kind": "test", "tests": [hid], "question": test.get("question") or "", "measurements": test.get("measurements") or [], "runs": runs, "decision_rules": [rule],''',
    '''        rule = {"for": hid, "decision_rule": rp.get("decision_rule"), "rival": rp.get("rival"), "rival_predicts": rp.get("rival_predicts")}
        # runs given replace the simulations of the same label and add new ones; the others are kept (the coherence audit, 2026-11-22: the prompt said
        # "only if they must change", while any list replaced all of them); what no rule names leaves below
        given = {r.get("label"): r for r in rp.get("runs") or [] if isinstance(r, dict)} if isinstance(rp.get("runs"), list) else {}
        base = [r for r in test.get("runs") or [] if isinstance(r, dict)]
        base += [r for r in every if isinstance(r, dict) and r.get("label") not in {q.get("label") for q in base}]
        runs = [dict(given.pop(r.get("label"), r)) for r in base] + [dict(r) for r in given.values()]
        t2 = {"kind": "test", "tests": [hid], "question": test.get("question") or "", "measurements": list(MEASURES.values()) or test.get("measurements") or [], "runs": runs, "decision_rules": [rule],   # every measurement of the answer: a repaired rule may name one a sibling test defined''')
rep('''    def repair_user(hid, test, n, who, feedback):
        """What the researcher is given to repair one test: the hypothesis and its guess, the test as proposed, the round, the feedback, what was measured, the knobs."""''',
    '''    def repair_user(hid, test, n, who, feedback, reserved=0):
        """What the researcher is given to repair one test: the hypothesis and its guess, the test as proposed, the round, the feedback, the records the
        feedback and the guess cite, what was measured, the measurements of the answer, the knobs, and how a network change is written."""''')
rep('''        knobs = "; ".join(f"{k} ({', '.join(map(str, v['choices'])) if 'choices' in v else str(v['min']) + ' to ' + str(v['max'])})" for k, v in brief["knobs"].items())
        return (f"YOUR TEST OF {hid} WAS SENT BACK BEFORE IT RAN.''',
    '''        knobs = "; ".join(f"{k} ({', '.join(map(str, v['choices'])) if 'choices' in v else str(v['min']) + ' to ' + str(v['max'])})" for k, v in brief["knobs"].items())
        ids = {r["id"]: r for r in ledger}
        cited = [i for i in dict.fromkeys(re.findall(r"\\b([A-Z]{1,2}\\d+)\\b", str(feedback)) + [a_ for a_ in y.get("about") or [] if isinstance(a_, str)]) if i in ids and ids[i]["type"] in LEARNED + ("simulation",)]
        mine = "".join(f"  {m['name']} = {m['stat']} of {m['of']}" + (f" against the level {m['level']}" if m.get("level") is not None else "") + "\\n" for m in MEASURES.values())
        left = max(0, budget - sims - reserved)
        example = change_example(brief) if may_change(brief) else None
        return (f"YOUR TEST OF {hid} WAS SENT BACK BEFORE IT RAN.''')
rep('''                f"WHAT HAS BEEN MEASURED SO FAR:\\n{_measured(ledger)}\\n\\nTHE KNOBS: {knobs}\\n\\n"
                "Repair this test only. decision_rule: the comparison that decides the hypothesis, in the form of your instructions (numbers; measure@label; + - * / and parentheses; abs(), "
                "min(), max(); one of < <= > >= == in each comparison; comparisons joined by AND and OR). rival: the strongest competing explanation you can think of, one sentence. "
                "rival_predicts: held or failed, what the rule gives if the rival is true (held is refused: choose simulations where the two differ). runs: the simulations, each with a "
                "label and a value for every knob, only if they must change; an empty list keeps them. The harness refuses a rule that names only simulations already run (what they "
                "measured is known, so the rule cannot fail): name at least one simulation that has not run yet."
                + (" A simulation may change the network (structure), as your instructions describe." if may_change(brief) else ""))''',
    '''                + (f"THE RECORDS THE FEEDBACK AND YOUR GUESS CITE:\\n" + "\\n".join(record_line(ids[i], ledger) for i in cited) + "\\n\\n" if cited else "")
                + f"WHAT HAS BEEN MEASURED SO FAR:\\n{_measured(ledger)}\\n\\n" + (f"THE MEASUREMENTS YOUR ANSWER DEFINES (a rule may name them as name@label):\\n{mine}\\n" if mine else "") + f"THE KNOBS: {knobs}\\n\\n"
                "Repair this test only. decision_rule: the comparison that decides the hypothesis, in the form of your instructions (numbers; measure@label; + - * / and parentheses; abs(), "
                "min(), max(); one of < <= > >= == in each comparison; comparisons joined by AND and OR). rival: the strongest competing explanation you can think of, one sentence. "
                "rival_predicts: held or failed, what the rule gives if the rival is true (held is refused: choose simulations where the two differ). runs: only the simulations that are new "
                "or change, each with a label and a value for every knob: one with the label of a simulation of the test replaces it, the others are kept; an empty list keeps them all. "
                "A rule that names only simulations already run cannot fail and is refused, unless it compares a measurement your answer defines (listed above), which is computed now from "
                "what those simulations recorded: " + (f"name at least one simulation that has not run yet ({left} can still run), or such a measurement." if left else "no new simulation can run now, so compare such a measurement.")
                + (" A simulation may change the network (structure), as your instructions describe: a run keeps its change unless the feedback is about it, and a run you give states its "
                   "whole change again. Each change states every field, for example, on this network: " + json.dumps(example) if example else
                   " A simulation may change the network (structure), as your instructions describe: a run keeps its change unless the feedback is about it." if may_change(brief) else ""))''')
rep('''            user = repair_user(hid, test, n + 1, who, feedback)''', '''            user = repair_user(hid, test, n + 1, who, feedback, reserved)''')
# a refused network change ends with the example too
rep('''def structure_problem(edits, brief=None):
    """None if the brief's network with these changes may be simulated; otherwise why not."""
    b = brief or tools.describe_system()
    if not edits:
        return None
    try:
        t1 = network.apply(b["topology"], edits)
    except (ValueError, KeyError, TypeError) as e:
        return str(e)
    bad = network.problems(t1) + network.changed_problems(b["topology"], t1, b.get("structure") or {}, b.get("goal") or {}, aim_measures(b))
    return "; ".join(bad) or None''',
    '''def structure_problem(edits, brief=None, example=True):
    """None if the brief's network with these changes may be simulated; otherwise why not, ending with one change written correctly for this
    network (s053, 2026-11-22: H1's change was written wrongly in every round)."""
    b = brief or tools.describe_system()
    if not edits:
        return None
    try:
        t1 = network.apply(b["topology"], edits)
        bad = network.problems(t1) + network.changed_problems(b["topology"], t1, b.get("structure") or {}, b.get("goal") or {}, aim_measures(b))
    except (ValueError, KeyError, TypeError) as e:
        bad = [str(e)]
    if not bad:
        return None
    ok = change_example(b) if example else None
    return "; ".join(bad) + (f". A change written correctly for this network, for example: {json.dumps(ok)}" if ok else "")


def change_example(brief):
    """One network change written correctly for this brief, built and checked on its network: a list of changes, or None. The first that can be
    simulated of: a link's queue replaced by a scheduler (or by a fifo where it is a scheduler), a scheduler added on a link's side."""
    t = brief.get("topology")
    if not t or not (brief.get("structure") or {}).get("may_change"):
        return None
    blank = {k: "" for k in network.EDIT}
    tries = [[{**blank, "do": "remove", "kind": "queue", "id": l["id"], "on": h}, {**blank, "do": "add_queue", "kind": "fifo" if (q or {}).get("kind") == "scheduler" else "scheduler", "id": l["id"], "on": h}]
             for l, h, q, _ in network.queues(t)] + [[{**blank, "do": "add_queue", "kind": "scheduler", "id": l["id"], "on": h}] for l in t.get("links") or [] for h in l.get("between") or []]
    for edits in tries:
        if structure_problem(edits, brief, example=False) is None:
            return edits
    return None''')

# ---- 20: what the ruling and the second look see
rep('''def rule_on(model, brief, ledger, xid, hid, doubt_if, ask_fn=None, contested=None):''',
    '''def _test_terms(ledger, xid, hid):
    """What a test was judged against before it ran, for its ruling and a second look (the coherence audit, 2026-11-22: the ruling saw neither): the
    researcher's rival of each rule and what it said the rule gives under it, a stronger rival the supervisor named in its last review, and the
    measurements the experiment defined."""
    flat = lambda v: " ".join(str(v).split())
    checks = [r for r in ledger if r["type"] == "check" and r["body"]["experiment"] == xid and r["body"]["for"] == hid]
    rev = next((r["body"] for r in reversed(ledger) if r["type"] == "review" and r.get("by") == "supervisor" and r["body"].get("gate") == "design" and r["body"].get("for") == hid and r["id"] < "~"), None)
    x = next((r["body"] for r in ledger if r["id"] == xid), {})
    out = "".join(f"THE RESEARCHER'S RIVAL for the rule {flat(c['body']['decision_rule'])}: {flat(c['body']['rival'])}; it said the rule gives {str(c['body'].get('rival_predicts')).upper()} if that rival is true\\n" for c in checks if c["body"].get("rival"))
    if rev and rev.get("rival_is_weak") and rev.get("stronger_rival"):
        out += f"THE STRONGER RIVAL YOU NAMED IN YOUR REVIEW: {flat(rev['stronger_rival'])} (you said the rule gives {str(rev.get('rival_outcome')).upper()} under it)\\n"
    out += "".join(f"A MEASUREMENT THE EXPERIMENT DEFINED: {m['name']} = {m['stat']} of {m['of']}" + (f" against the level {m['level']}" if m.get("level") is not None else "") + f", from {m.get('t_from') if m.get('t_from') is not None else 2} s to {m.get('t_to') if m.get('t_to') is not None else 'the end'}\\n" for m in x.get("measurements") or [] if isinstance(m, dict))
    return out


def rule_on(model, brief, ledger, xid, hid, doubt_if, ask_fn=None, contested=None):''')
rep('''            f"EVERY READING OF THE SESSION, as the researcher's ledger holds them (what the tools returned when the researcher looked: measurements too):\\n{_looked(ledger)}\\n\\nTHE HARNESS'S CHECKS (facts):\\n{lines}\\n\\n" + (f"Before the simulations you wrote''',
    '''            f"EVERY READING OF THE SESSION, as the researcher's ledger holds them (what the tools returned when the researcher looked: measurements too):\\n{_looked(ledger)}\\n\\nTHE HARNESS'S CHECKS (facts):\\n{lines}\\n\\n" + _test_terms(ledger, xid, hid) + "\\n" + (f"Before the simulations you wrote''')
rep('''APPEAL_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answer", "stands", "result", "because"], "properties": {
    "answer": {"type": "string", "description": "what in the records the objection gets right or wrong"}, "stands": {"type": "boolean", "description": "true: your ruling stands as it was"},''',
    '''APPEAL_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answer", "fair", "stands", "result", "because"], "properties": {
    "answer": {"type": "string", "description": "what in the records the objection gets right or wrong"},
    "fair": {"type": "boolean", "description": "whether this was a fair test of the hypothesis: one that could have come out the other way if the hypothesis were false"},
    "stands": {"type": "boolean", "description": "true: your ruling stands as it was"},''')
rep('''    user = (_system_for_supervisor(brief) + "\\n" + _case(ledger, hid, [{"decision_rule": c["body"]["decision_rule"]} for c in checks]) + f"\\nTHE SIMULATIONS OF THE TEST, as measured:\\n{_measured(ledger, xid)}\\n\\nEVERYTHING MEASURED IN THE SESSION:\\n{_measured(ledger)}\\n\\n"
            f"THE HARNESS'S CHECKS (facts):\\n{lines}\\n\\nYOUR RULING''',
    '''    user = (_system_for_supervisor(brief) + "\\n" + _case(ledger, hid, [{"decision_rule": c["body"]["decision_rule"]} for c in checks]) + f"\\nTHE SIMULATIONS OF THE TEST, as measured:\\n{_measured(ledger, xid)}\\n\\nEVERYTHING MEASURED IN THE SESSION:\\n{_measured(ledger)}\\n\\n"
            f"EVERY READING OF THE SESSION, as the researcher's ledger holds them:\\n{_looked(ledger)}\\n\\n"   # the readings, the rivals and the measurements, as at the ruling (the coherence audit, 2026-11-22)
            f"THE HARNESS'S CHECKS (facts):\\n{lines}\\n\\n" + (_test_terms(ledger, xid, hid) if xid else "") + "\\nYOUR RULING''')
rep('''              "supported needs every check HELD, refuted needs a check that FAILED; otherwise inconclusive.")
    d = (ask_fn or supervise)(model, user, APPEAL_SCHEMA)
    res = [c["body"]["result"] for c in checks]
    result = b["result"] if d["stands"] else d["result"]
    if (result == "supported" and not all(x == "held" for x in res)) or (result == "refuted" and not any(x == "failed" for x in res)):
        result = "inconclusive"
    return {"stands": result == b["result"], "result": result, "because": flat(d["because"]), "answer": flat(d["answer"])}, user''',
    '''              "First say whether the test was fair: one that could have come out the other way if the hypothesis were false (a rival that passes the rule too, or another setting that "
              "limited the result, makes it unfair). supported needs every check HELD and a fair test, refuted needs a check that FAILED and a fair test; otherwise inconclusive.")
    d = (ask_fn or supervise)(model, user, APPEAL_SCHEMA)
    res = [c["body"]["result"] for c in checks]
    fair = bool(d.get("fair", b.get("fair", True)))
    result = b["result"] if d["stands"] else d["result"]
    if (result == "supported" and not (all(x == "held" for x in res) and fair)) or (result == "refuted" and not (any(x == "failed" for x in res) and fair)):
        result = "inconclusive"
    return {"stands": result == b["result"], "result": result, "fair": fair, "because": flat(d["because"]), "answer": flat(d["answer"])}, user''')
rep('''                                                                             "fair": was["body"].get("fair", True) if again["stands"] else again["result"] != "inconclusive", "defect": was["body"].get("defect", "none") if again["stands"] else "none",''',
    '''                                                                             "fair": again["fair"], "defect": was["body"].get("defect", "none") if again["stands"] else "none",''')

# ---- 21: a ruling asked for again is in this turn's ledger text
rep('''                rule_missing()   # a checked hypothesis whose ruling could not be read: asked for once more, before the researcher's reply (s053, 2026-11-22)''',
    '''                n_was = len(ledger)
                rule_missing()   # a checked hypothesis whose ruling could not be read: asked for once more, before the researcher's reply (s053, 2026-11-22)
                if len(ledger) > n_was:   # what it added is in this turn's ledger text (the coherence audit, 2026-11-22: the text was rendered before it)
                    text = render(ledger, readings=True, rethinks=False)''')

# ---- 22: counters and notes of continued replies
rep('''            if not (ok["rethink"] or ok["whys"] or ok["hypotheses"] or ok["drop"] or ok["verdicts"] or ok["objections"] or ex is not None or report is not None or br):  # only requests
                tool_only += 1''',
    '''            if not (ok["rethink"] or ok["whys"] or ok["hypotheses"] or ok["drop"] or ok["verdicts"] or ok["objections"] or ex is not None or report is not None or br):  # only requests
                tool_only += not staying   # turns that only look, not replies (the coherence audit, 2026-11-22: a turn's continued replies counted as turns)''')
rep('''                append(ledger, turn, "note", last, {"observations": parsed.get("observations"), "requests": rq}, by="model")
                settle_findings(remap_refs(parsed), ledger, turn, due_before, [r["id"] for r in ledger if r["turn"] == turn and r["type"] == "result"], [])
                stay_next = mode in (None, "free") and stay < CONTINUES   # no step yet: the researcher is asked again in this turn, with what it asked for answered''',
    '''                append(ledger, turn, "note", last, {"observations": parsed.get("observations"), "requests": rq}, by="model")
                stay_next = mode in (None, "free") and stay < CONTINUES   # no step yet: the researcher is asked again in this turn, with what it asked for answered
                settle_findings(remap_refs(parsed), ledger, turn, due_before, [r["id"] for r in ledger if r["turn"] == turn and r["type"] == "result"], [], goes_on=stay_next)''')
rep('''            settle_findings(remap_refs(parsed), ledger, turn, due_before, made, [x for x in whys_made if x[1]])''',
    '''            settle_findings(remap_refs(parsed), ledger, turn, due_before, made, [x for x in whys_made if x[1]], goes_on=stay_next)''')
rep('''def settle_findings(t, ledger, turn, due_before, made, whys_made):''', '''def settle_findings(t, ledger, turn, due_before, made, whys_made, goes_on=False):''')
rep('''            _note(ledger, turn, f"decision for {fid}", f"no decision for {fid}, which was due this turn: it stays {fs[fid]['status']} and is asked for again in the next turn")''',
    '''            _note(ledger, turn, f"decision for {fid}", f"no decision for {fid}, which was due this turn: it stays {fs[fid]['status']} and is asked for again in " + ("your next reply, in this same turn" if goes_on else "the next turn"))''')

# ---- 25: smaller
rep('''                g, saw = {"records_show": "", "nearest_earlier": "none", "defect": "none", "because": f"the supervisor's reading could not be read ({type(e).__name__}): the guess is accepted unread"}, ""''',
    '''                g, saw = {"records_show": "", "nearest_earlier": "none", "defect": "none", "because": f"the supervisor's reading could not be read ({type(e).__name__}): the guess is accepted unread", "unread": True}, ""''')
rep('''            refuse = g["defect"] != "none" and not warning and not refused_about.get(about)
            if refuse:
                refused_about[about] = 1''',
    '''            refuse = g["defect"] != "none" and not warning and not refused_about.get((turn, about))   # once in a turn (the coherence audit, 2026-11-22: it was once in the session)
            if refuse:
                refused_about[(turn, about)] = 1''')
rep('''            w = {**w, "ground": {k: g[k] for k in ("records_show", "nearest_earlier", "defect", "because")} | {"warning": bool(g.get("warning"))}}''',
    '''            w = {**w, "ground": {k: g[k] for k in ("records_show", "nearest_earlier", "defect", "because")} | {"warning": bool(g.get("warning"))} | ({"unread": True} if g.get("unread") else {})}''')
rep('''        return (f"by the supervisor of the guess {b['for']}, before anything is built on it: " + ("sound: it starts from what the records show" if b["defect"] == "none" else''',
    '''        if b.get("unread"):   # the coherence audit, 2026-11-22: it was shown as sound
            return f"by the supervisor of the guess {b['for']}, before anything is built on it: not read (the supervisor's reading could not be read), and the guess is accepted unread"
        return (f"by the supervisor of the guess {b['for']}, before anything is built on it: " + ("sound: it starts from what the records show" if b["defect"] == "none" else''')
rep('''    return {r["id"] for r in ledger if r["type"] in LEARNED and r["turn"] >= k and not (r["type"] == "review" and r["body"].get("decision") == "approved")}''',
    '''    return {r["id"] for r in ledger if (r["type"] in LEARNED or r["type"] == "simulation") and r["turn"] >= k and not (r["type"] == "review" and (r["body"].get("decision") == "approved" or r.get("by") == "harness"))}   # a harness's round is no objection of the supervisor's; a simulation is a result (the coherence audit, 2026-11-22)''')
# the record lines of gate 0, for the restatement and the repair too
rep('''    flat = lambda v: " ".join(str(v).split())
    st = states(ledger)[0]
    cited = [r for r in ledger if r["id"] in why["about"]]
    def record(r):
        b = r["body"]
        if r["type"] == "evidence":
            return f"[{r['id']}] measured in {b['experiment']}:\\n" + "\\n".join("    " + l for l in b["lines"])
        if r["type"] == "simulation":
            return f"[{r['id']}] simulation {b.get('label')} {{{', '.join(f'{k}={v}' for k, v in (b.get('params') or {}).items())}}} | " + " ".join(f"{k}={v}" for k, v in (b.get("metrics") or {}).items())
        if r["type"] == "check":
            return f"[{r['id']}] check for {b['for']}: {flat(b['decision_rule'])}  ->  {b['with_numbers']}  :  {b['result'].upper()}"
        if r["type"] == "result":   # in full, as the researcher's ledger holds it (until 2026-11-22: one line of 1,500 characters)
            return reading(r, {x["id"]: x for x in ledger})
        if r["type"] == "review":
            return f"[{r['id']}] the supervisor's review of {b.get('for') or 'a guess'}: {b.get('decision')}. {flat(b.get('because'))}" + (f" The rival it named: {flat(b['rival'])}" if b.get("rival") else "")
        return f"[{r['id']}] ruling on {b['for']}: {b['result']}. {flat(b['because'])}"
    new = learned_since(ledger)''',
    '''    flat = lambda v: " ".join(str(v).split())
    st = states(ledger)[0]
    cited = [r for r in ledger if r["id"] in why["about"]]
    record = lambda r: record_line(r, ledger)
    new = learned_since(ledger)''')
rep('''def ground_of(model, brief, ledger, why, ask_fn=None):''',
    '''def record_line(r, ledger):
    """One record as the supervisor and a short call of the researcher are shown it: a result table, a simulation, a check, a reading in full, a review,
    a ruling (gate 0, the restatement and the repair; the coherence audit, 2026-11-22: the restatement and the repair were given ids only)."""
    flat = lambda v: " ".join(str(v).split())
    b = r["body"]
    if r["type"] == "evidence":
        return f"[{r['id']}] measured in {b['experiment']}:\\n" + "\\n".join("    " + l for l in b["lines"])
    if r["type"] == "simulation":
        return f"[{r['id']}] simulation {b.get('label')} {{{', '.join(f'{k}={v}' for k, v in (b.get('params') or {}).items())}}} | " + " ".join(f"{k}={v}" for k, v in (b.get("metrics") or {}).items())
    if r["type"] == "check":
        return f"[{r['id']}] check for {b['for']}: {flat(b['decision_rule'])}  ->  {b['with_numbers']}  :  {b['result'].upper()}"
    if r["type"] == "result":   # in full, as the researcher's ledger holds it (until 2026-11-22: one line of 1,500 characters)
        return reading(r, {x["id"]: x for x in ledger})
    if r["type"] == "review":
        return f"[{r['id']}] the {'harness' if r.get('by') == 'harness' else 'supervisor'}'s review of {b.get('for') or 'a guess'}: {b.get('decision')}. {flat(b.get('feedback') or b.get('because'))}" + (f" The rival it named: {flat(b['rival'])}" if b.get("rival") else "")
    if r["type"] == "verdict":
        return f"[{r['id']}] ruling on {b['for']}: {b['result']}. {flat(b['because'])}"
    return f"[{r['id']}] {r['type']}: {flat(json.dumps(b))[:600]}"


def ground_of(model, brief, ledger, why, ask_fn=None):''')
rep('''                f"  result: {flat(w.get('result'))}\\n  guess: {flat(w.get('guess'))}\\n  revises: {w.get('revises')}\\n\\nWHAT WAS LEARNED SINCE YOUR LAST GUESS: {', '.join(sorted(since or [])) or 'nothing'}\\n"''',
    '''                f"  result: {flat(w.get('result'))}\\n  guess: {flat(w.get('guess'))}\\n  revises: {w.get('revises')}\\n\\nWHAT WAS LEARNED SINCE YOUR LAST GUESS:\\n"
                + ("\\n".join(record_line(r, ledger) for r in ledger if r["id"] in (since or ()) and r["type"] != "simulation") or "  nothing") + "\\n"''')
rep('''    CALLS["n"] += 1
    try:''', '''    CALLS["n"] += 1
    CALLS.setdefault("by", {})[agent] = CALLS["by"].get(agent, 0) + 1   # every call of this run, by agent (the coherence audit, 2026-11-22: "calls" counts the researcher's only)
    try:''')
rep('''turns=turn, simulations=sims, calls=count["calls"], cut_off=count["length"])''', '''turns=turn, simulations=sims, calls=count["calls"], calls_by_agent=dict(CALLS.get("by") or {}), cut_off=count["length"])''')
rep('''            if report is not None and mode in (None, "free") and len(held_turns - {turn}) < FINDING_HOLDS and (unseen := findings_unseen(ledger)):''',
    '''            if report is not None and (ran_now := [r["id"] for r in ledger if r["turn"] == turn and r["type"] == "experiment" and r.get("by") != "harness"]):   # the coherence audit, 2026-11-22: a report with an experiment was taken before its results
                _note(ledger, turn, "report", f"the report is held back: this answer's experiment ({', '.join(ran_now)}) ran in this turn, and its results and checks come to you in the next turn. Give the report after you have read them")
                report = None
            if report is not None and mode in (None, "free") and len(held_turns - {turn}) < FINDING_HOLDS and (unseen := findings_unseen(ledger)):''')
# == within the tolerance: the session's tolerance
rep('''    TOLERANCE = float(brief["goal"]["tolerance"]) if tol_given else DEFAULT_TOLERANCE''',
    '''    TOLERANCE = float(brief["goal"]["tolerance"]) if tol_given else DEFAULT_TOLERANCE
    decision_rules.EQUAL_WITHIN = TOLERANCE   # == holds within the tolerance, as the turn's text says two results are equal (the coherence audit, 2026-11-22)''')
p.write_text(s); print("patched", kind, p)
