"""Stage 4 of the coherence audit (2026-11-22), "Fixes from s052 and s053" item 4a: one batched first review per turn. Every new guess (gate 0) and every
new test (gate 1, round 1) of a reply goes to the supervisor in ONE request, the system, the measured results, the readings and the earlier guesses
written once (s052/s053: 24 guess and test reviews, one after another, took 20.3 of the 64 minutes of waiting). A dry run of sort_out (no call) finds
what the harness accepts; only that is reviewed; the answers are then taken as the single reviews would have been (the same caches, the same rules).
Restatements, repairs, later rounds and follow-up questions stay one per item. A batch that cannot be read leaves a note, and each item is asked
alone as before. One item alone is asked alone (nothing to share). Usage: s4_batch.py WT_DIR"""
import sys
from pathlib import Path
W = Path(sys.argv[1])
def rep(f, a, b, n=1):
    p = W / f; s = p.read_text(); assert s.count(a) == n, (f, a[:110], s.count(a)); p.write_text(s.replace(a, b))
L = "harness/loop.py"
rep(L, '''AGAIN_TOKENS = 2000   #''', '''BATCH_FIRST = True   # the arm "supervised": the new guesses and tests of a reply are reviewed in one request (stage 4 of the coherence audit, 2026-11-22; the operator's sheet "Fixes from s052 and s053", 4a)
AGAIN_TOKENS = 2000   #''')
# _case: a hypothesis and its guess not yet in the ledger
rep(L, '''def _case(ledger, hid, rules):
    """One hypothesis as the supervisor is shown it: the result its guess is about, the guess, the hypothesis, its decision rules. Not the researcher's reasons."""
    flat = lambda v: " ".join(str(v).split())
    h = next(r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid)
    w = next((r["body"] for r in ledger if r["type"] == "why" and r["id"] == h.get("from_why")), None)''',
    '''def _case(ledger, hid, rules, h=None, w=None):
    """One hypothesis as the supervisor is shown it: the result its guess is about, the guess, the hypothesis, its decision rules. Not the researcher's reasons.
    h, w: the hypothesis and its guess when they are not in the ledger yet (the batched first review, 2026-11-22)."""
    flat = lambda v: " ".join(str(v).split())
    h = h if h is not None else next(r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid)
    w = w if w is not None else next((r["body"] for r in ledger if r["type"] == "why" and r["id"] == h.get("from_why")), None)''')
# review_design: its parts, and an answer given in the batch
p = W / L; s = p.read_text()
a = s.index('def review_design(model, brief, ledger, ex, hid, ask_fn=None, round_no=1, earlier=()):')
s = s.replace('def review_design(model, brief, ledger, ex, hid, ask_fn=None, round_no=1, earlier=()):',
              'def review_design(model, brief, ledger, ex, hid, ask_fn=None, round_no=1, earlier=(), case=None, parts=False, pre=None, pre_saw=None):', 1)
u0 = s.index('    user = (_system_for_supervisor(brief) + f"\\nWHAT HAS BEEN MEASURED SO FAR:\\n{_measured(ledger)}', a)
u1 = s.index('    d = (ask_fn or supervise)(model, user, REVIEW_SCHEMA)', u0)
stmt = s[u0:u1]
k1 = stmt.index(' + _case(ledger, hid, rules)\n')
head = stmt[len("    user = ("):k1]
rest = stmt[k1 + len(' + _case(ledger, hid, rules)\n'):]
k2 = rest.index('+ (f"THIS IS ROUND {round_no} of at most {REVIEW_ROUNDS} for this test.')
mid = rest[:k2].rstrip()
assert mid.lstrip().startswith('+ "".join(f"A MEASUREMENT THE RESEARCHER DEFINES') and mid.endswith('f"THE SIMULATIONS PLANNED FOR IT:\\n{sims}\\n\\n"'), mid[-80:]
k3 = rest.index('\n            + "Before any of these simulations is run:')
rounds = rest[k2 + 2:k3].strip()
ask = rest[k3 + len('\n            + '):].rstrip()
assert ask.endswith('consequence of the guess.")'), ask[-60:]
ask = ask[:-1]
new = ('    item = (case if case is not None else _case(ledger, hid, rules))\n    item = (item\n            ' + mid.strip() + ')\n'
       '    ask = (' + ask + ')\n'
       '    if parts:   # the pieces of this review, for the batched first review\n        return {"item": item, "ask": ask}\n'
       '    user = (' + head + ' + item + ' + rounds + ' + ask)\n')
s = s[:u0] + new + s[u1:]
s = s.replace('    d = (ask_fn or supervise)(model, user, REVIEW_SCHEMA)\n    predicts =', '    d = pre if pre is not None else (ask_fn or supervise)(model, user, REVIEW_SCHEMA)   # pre: its answer in the batched first review\n    predicts =', 1)
r0 = s.index('    rev["rival"] = rev["stronger_rival"] if rev["rival_is_weak"] else ""', a)
r1 = s.index('    return rev, user\n', r0)
s = s[:r1] + ('    if pre is not None:   # what it was shown: the batched request (and a follow-up question, asked alone)\n'
              '        user = (pre_saw or "") + "\\n\\n[this test was answered in the batched first review of the turn]" + (f"\\n\\n[then asked alone]:\\n{user}" if rev.get("again") else "")\n') + s[r1:]
# ground_of: its parts, and an answer given in the batch
g0 = s.index('def ground_of(model, brief, ledger, why, ask_fn=None):')
s = s.replace('def ground_of(model, brief, ledger, why, ask_fn=None):', 'def ground_of(model, brief, ledger, why, ask_fn=None, parts=False, pre=None, pre_saw=None):', 1)
u0 = s.index('    user = (_system_for_supervisor(brief) + "\\nTHE RECORDS THE NEW GUESS CITES:\\n" + ("\\n".join(mark(r) for r in cited) or "  (it cites the brief only: nothing has been measured for it)")', g0)
u1 = s.index('    d = (ask_fn or supervise)(model, user, GROUND_SCHEMA)', u0)
stmt = s[u0:u1]
i_read = stmt.index('\n            + "\\n\\nEVERY READING OF THE SESSION')
i_guess = stmt.index('\n            + f"\\n\\nTHE NEW GUESS\\nThe result it starts from')
i_earl = stmt.index('            f"THE SESSION\'S EARLIER GUESSES AND HYPOTHESES:\\n{earlier}\\n\\nTHE RULINGS SO FAR:\\n{rulings}\\n\\n"\n')
i_ask = i_earl + len('            f"THE SESSION\'S EARLIER GUESSES AND HYPOTHESES:\\n{earlier}\\n\\nTHE RULINGS SO FAR:\\n{rulings}\\n\\n"\n')
readings_part = stmt[i_read + len('\n            + '):i_guess]
guess_part = stmt[i_guess + len('\n            + f"\\n\\nTHE NEW GUESS\\n'):i_earl].rstrip()
assert guess_part.endswith('+ "\\n"'), guess_part[-40:]
guess_part = guess_part[:-len('+ "\\n"')].rstrip()
ask_part = stmt[i_ask:].rstrip()
assert ask_part.endswith('for form only and the defect is not_from_what_was_learned."))'), ask_part[-60:]
ask_part = ask_part[:-1]
new = ('    cites = "\\n".join(mark(r) for r in cited) or "  (it cites the brief only: nothing has been measured for it)"\n'
       '    the_guess = (f"' + guess_part + ')\n'
       '    ask = (' + ask_part.strip() + ')\n'
       '    if parts:   # the pieces of this review, for the batched first review\n        return {"cites": cites, "guess": the_guess, "earlier": earlier, "rulings": rulings, "ask": ask}\n'
       '    user = (_system_for_supervisor(brief) + "\\nTHE RECORDS THE NEW GUESS CITES:\\n" + cites\n            + ' + readings_part.strip()
       + '\n            + "\\n\\nTHE NEW GUESS\\n" + the_guess + "\\n"\n            + f"THE SESSION\'S EARLIER GUESSES AND HYPOTHESES:\\n{earlier}\\n\\nTHE RULINGS SO FAR:\\n{rulings}\\n\\n" + ask)\n')
s = s[:u0] + new + s[u1:]
s = s.replace('    d = (ask_fn or supervise)(model, user, GROUND_SCHEMA)\n    return {"records_show"', '    d = pre if pre is not None else (ask_fn or supervise)(model, user, GROUND_SCHEMA)   # pre: its answer in the batched first review\n    if pre is not None:\n        user = pre_saw or ""\n    return {"records_show"', 1)
# the batched request itself
s = s.replace('def rule_on(model, brief, ledger, xid, hid, doubt_if, ask_fn=None, contested=None):', '''def batch_schema(ng, nt):
    """The answer of the batched first review: one item for each new guess (gate 0's fields) and one for each test (round 1's fields)."""
    g_item = {"type": "object", "additionalProperties": False, "required": ["guess"] + GROUND_SCHEMA["required"],
              "properties": {"guess": {"type": "string", "description": "the guess's name in this request: G1, G2, ..."}, **GROUND_SCHEMA["properties"]}}
    t_item = {"type": "object", "additionalProperties": False, "required": ["for"] + REVIEW_SCHEMA["required"],
              "properties": {"for": {"type": "string", "description": "the hypothesis whose test this item reviews, as its heading names it"}, **REVIEW_SCHEMA["properties"]}}
    return {"type": "object", "additionalProperties": False, "required": ["guesses", "tests"], "properties": {
        "guesses": {"type": "array", "minItems": ng, "maxItems": ng, "items": g_item, "description": "one item for each new guess, in their order"},
        "tests": {"type": "array", "minItems": nt, "maxItems": nt, "items": t_item, "description": "one item for each test, in their order"}}}


def first_review(model, brief, ledger, guesses, tests, ask_fn=None):
    """The batched first review of a reply (stage 4 of the coherence audit, 2026-11-22): every new guess (gate 0) and every test (round 1) in one
    request; what all of them share is written once. guesses: the guesses as stated; tests: [(hypothesis, its test, its case text or None)].
    Returns (an answer or None for each guess, an answer or None for each test, what was shown). The answers are the raw items: each is then read
    as a review of its own would be (ground_of, review_design with pre)."""
    gp = [ground_of(model, brief, ledger, w, parts=True) for w in guesses]
    tp = [review_design(model, brief, ledger, ex, hid, case=case, parts=True) for hid, ex, case in tests]
    user = (_system_for_supervisor(brief) + f"\\nWHAT HAS BEEN MEASURED SO FAR:\\n{_measured(ledger)}\\n\\nEVERY READING OF THE SESSION, as the researcher's ledger holds them (what the tools returned "
            f"when the researcher looked: these are measurements too, and a guess may start from them):\\n{_looked(ledger)}\\n\\n"
            + (f"THE SESSION'S EARLIER GUESSES AND HYPOTHESES:\\n{gp[0]['earlier']}\\n\\nTHE RULINGS SO FAR:\\n{gp[0]['rulings']}\\n\\n" if gp else "")
            + f"THIS REQUEST HOLDS EVERY NEW GUESS AND EVERY NEW TEST OF THE RESEARCHER'S REPLY IN THIS TURN ({len(guesses)} guess{'es' if len(guesses) != 1 else ''}, {len(tests)} test{'s' if len(tests) != 1 else ''}). "
              "Judge each on its own, as if it were asked alone, and answer each in its own item.\\n\\n"
            + "".join(f"== NEW GUESS G{i + 1} ==\\nTHE RECORDS IT CITES:\\n{q['cites']}\\nTHE GUESS:\\n{q['guess']}\\n" for i, q in enumerate(gp))
            + "".join(f"== TEST OF {hid} ==\\n{q['item']}" for (hid, _, _), q in zip(tests, tp))
            + (f"FOR EACH NEW GUESS (an item of guesses, named G1, G2, ... as above): {gp[0]['ask']}\\n\\n" if gp else "")
            + (f"FOR EACH TEST (an item of tests, by its hypothesis): {tp[0]['ask']}" if tp else ""))
    n = len(guesses) + len(tests)
    d = (ask_fn or (lambda m, u, sc: supervise(m, u, sc, 9000 + 2000 * (n - 1))))(model, user, batch_schema(len(guesses), len(tests)))   # 4,500 reasoning tokens and 1,000 more for each further item
    gs = {str(x.get("guess")): x for x in d.get("guesses") or [] if isinstance(x, dict)}
    ts = {str(x.get("for")): x for x in d.get("tests") or [] if isinstance(x, dict)}
    return [gs.get(f"G{i + 1}") for i in range(len(guesses))], [ts.get(hid) for hid, _, _ in tests], user


def test_key(ex, hid, h_text):
    """What makes a test the same in the batched first review and in round 1: its hypothesis, its rules and the simulations they name."""
    rules = [{k: d.get(k) for k in ("decision_rule", "rival", "rival_predicts")} for d in ex.get("decision_rules") or [] if d.get("for") == hid]
    need = next((n for n in ex.get("needs") or [] if n.get("for") == hid), {})
    runs = [{k: r.get(k) for k in ("label", "params", "structure")} for r in ex.get("runs") or [] if r.get("label") in (need.get("simulations") or [q.get("label") for q in ex.get("runs") or []])]
    return json.dumps([" ".join(str(h_text).split()), rules, runs], sort_keys=True)


def rule_on(model, brief, ledger, xid, hid, doubt_if, ask_fn=None, contested=None):''', 1)
p.write_text(s)
# main: the caches shared by the batch and the single reviews; the dry run
rep(L, '''    def ground_fn(w):
        k, about = (" ".join(str(w["guess"]).split()), tuple(w["about"])), tuple(sorted(w["about"]))
        if k not in grounded:
            try:
                stage("ground")
                g, saw = ground_of(model, brief, ledger, w)
            except (ValueError, KeyError, TypeError) as e:
                g, saw = {"records_show": "", "nearest_earlier": "none", "defect": "none", "because": f"the supervisor's reading could not be read ({type(e).__name__}): the guess is accepted unread", "unread": True}, ""
            warning = g["defect"] in GROUND_WARNINGS   # recorded, and the guess is accepted (2026-11-22, after s050 and s051)
            refuse = g["defect"] != "none" and not warning and not refused_about.get((turn, about))   # once in a turn (the coherence audit, 2026-11-22: it was once in the session)
            if refuse:
                refused_about[(turn, about)] = 1
            grounded[k] = {**g, "saw": saw, "refuse": refuse, "warning": warning, "result": w["result"], "guess": w["guess"]}
        return grounded[k]''',
    '''    def ground_take(k, w, g, saw):
        """A guess's reading, by itself or in the batched first review: whether it is refused (once in a turn for the same records), kept for the turn."""
        about = tuple(sorted(w["about"]))
        warning = g["defect"] in GROUND_WARNINGS   # recorded, and the guess is accepted (2026-11-22, after s050 and s051)
        refuse = g["defect"] != "none" and not warning and not refused_about.get((turn, about))   # once in a turn (the coherence audit, 2026-11-22: it was once in the session)
        if refuse:
            refused_about[(turn, about)] = 1
        grounded[k] = {**g, "saw": saw, "refuse": refuse, "warning": warning, "result": w["result"], "guess": w["guess"]}
    def ground_fn(w):
        k = (" ".join(str(w["guess"]).split()), tuple(w["about"]))
        if k not in grounded:
            try:
                stage("ground")
                g, saw = ground_of(model, brief, ledger, w)
            except (ValueError, KeyError, TypeError) as e:
                g, saw = {"records_show": "", "nearest_earlier": "none", "defect": "none", "because": f"the supervisor's reading could not be read ({type(e).__name__}): the guess is accepted unread", "unread": True}, ""
            ground_take(k, w, g, saw)
        return grounded[k]
    prereviewed = {}   # test_key -> (the batched first review's answer for that test, what was shown): taken by round 1 instead of a call of its own
    def prefetch(parsed, mode_now):
        """The batched first review of this reply (stage 4 of the coherence audit, 2026-11-22): a dry run of sort_out (no call to anyone) finds the new
        guesses and tests the harness accepts; those not yet read are asked in one request; the answers fill the caches the single reviews use."""
        found = []
        def collect(w):
            k = (" ".join(str(w["guess"]).split()), tuple(w["about"]))
            if k not in grounded and k not in [x[0] for x in found]:
                found.append((k, json.loads(json.dumps(w))))
            return {"records_show": "", "nearest_earlier": "none", "defect": "none", "because": "", "refuse": False, "warning": False}
        try:
            ok0, _no0 = sort_out(json.loads(json.dumps(parsed)), brief, ledger, max(0, budget - sims), mode_now, insist=not asked, judge=None, supervised=True, ground=collect, short=short, restate=None)
        except Exception:   # the real pass says what is wrong; the batch is only a way to ask sooner
            return
        tests = []
        ex0 = ok0.get("experiment")
        if ex0 is not None and ex0.get("kind") == "test":
            n_h, n_y = sum(r["type"] == "hypothesis" for r in ledger), sum(r["type"] == "why" for r in ledger)
            hyps, whys = {f"H{n_h + i + 1}": h for i, h in enumerate(ok0["hypotheses"])}, {f"Y{n_y + i + 1}": w for i, w in enumerate(ok0["whys"])}
            for hid in ex0.get("tests") or []:
                if any(rival_problem(d) or rule_size_problem(d) for d in ex0.get("decision_rules") or [] if d.get("for") == hid):
                    continue   # refused by the harness before any review
                h = hyps.get(hid) or next((r["body"] for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), None)
                if h is None:
                    continue
                w = whys.get(h.get("from_why")) or next((r["body"] for r in ledger if r["type"] == "why" and r["id"] == h.get("from_why")), None)
                key = test_key(ex0, hid, h.get("text"))
                if key not in prereviewed:
                    tests.append((hid, ex0, _case(ledger, hid, [d for d in ex0.get("decision_rules") or [] if d.get("for") == hid], h=h, w=w), key))
        if len(found) + len(tests) < 2:   # one item is asked alone, as before: nothing to share
            return
        try:
            stage("review")
            g_ans, t_ans, saw = first_review(model, brief, ledger, [w for _, w in found], [(hid, ex, case) for hid, ex, case, _ in tests])
        except (ValueError, KeyError, TypeError) as e:
            append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"the supervisor's batched first review could not be read ({type(e).__name__}): each new guess and test is asked alone"})
            return
        for (k, w), x in zip(found, g_ans):
            if isinstance(x, dict):
                try:
                    g, _saw = ground_of(model, brief, ledger, w, pre=x, pre_saw=saw)
                    ground_take(k, w, g, saw)
                except (ValueError, KeyError, TypeError):
                    pass   # an item that cannot be read: that guess is asked alone
        for (hid, ex, case, key), x in zip(tests, t_ans):
            if isinstance(x, dict):
                prereviewed[key] = (x, saw)''')
rep(L, '''        for hid in ex["tests"]:
            test = test_of(ex, hid)
            try:
                stage("design", hid, 1)
                rev, saw = review_design(model, brief, ledger, ex, hid)''',
    '''        for hid in ex["tests"]:
            test = test_of(ex, hid)
            pre = prereviewed.pop(test_key(ex, hid, next((r["body"].get("text") for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), "")), None)   # its answer in the batched first review
            try:
                if pre is None:
                    stage("design", hid, 1)
                rev, saw = review_design(model, brief, ledger, ex, hid, pre=pre[0] if pre else None, pre_saw=pre[1] if pre else None)''')
rep(L, '''                ok, no = sort_out(parsed, brief, ledger, max(0, budget - sims), mode, insist=not asked,''',
    '''                if arm == "supervised" and BATCH_FIRST and isinstance(parsed, dict) and mode in (None, "free"):
                    prefetch(parsed, mode)   # one request for the reply's new guesses and tests (stage 4 of the coherence audit, 2026-11-22)
                ok, no = sort_out(parsed, brief, ledger, max(0, budget - sims), mode, insist=not asked,''')
rep(L, '''"max_tokens": 9000, "draft_tokens": draft_tokens(9000), ''', '''"max_tokens": 9000, "draft_tokens": draft_tokens(9000), "follow_up_tokens": AGAIN_TOKENS, "first_review": "one request for the new guesses and tests of a reply" if BATCH_FIRST else "one request each", ''')
rep(L, '''    done). step: reply (the researcher), judge, ground (the supervisor reads a guess),''', '''    done). step: reply (the researcher), judge, review (the supervisor's batched first review of a reply's new guesses and tests), ground (the supervisor reads a guess),''')
# the page: the step "review"
V = "viewer/evidence_live.js"
rep(V, "  LIVE_AGENT_STEPS: ['judge', 'ground', 'restate', 'design', 'repair', 'ruling', 'objection', 'look'],", "  LIVE_AGENT_STEPS: ['judge', 'review', 'ground', 'restate', 'design', 'repair', 'ruling', 'objection', 'look'],")
rep(V, "['judge', 'ground', 'design', 'ruling', 'objection', 'look'].includes(p) ? 'supervisor' : 'harness'),", "['judge', 'review', 'ground', 'design', 'ruling', 'objection', 'look'].includes(p) ? 'supervisor' : 'harness'),")
rep(V, "      : now.phase === 'ground' ? `${t}the supervisor reads a new guess against the records it cites.`",
    "      : now.phase === 'review' ? `${t}the supervisor reads the new guesses and reviews the new tests, in one request.`\n      : now.phase === 'ground' ? `${t}the supervisor reads a new guess against the records it cites.`")
rep(V, "a guess it or the harness does not accept, the researcher restates once, in this turn', ['ground', 'restate']],",
    "a guess it or the harness does not accept, the researcher restates once, in this turn', ['review', 'ground', 'restate']],")
rep(V, "  CALL_STEPS: { reply: ['reply'], ground: ['ground', 'restate'], design: ['design', 'repair'],", "  CALL_STEPS: { reply: ['reply'], ground: ['review', 'ground', 'restate'], design: ['review', 'design', 'repair'],")
rep(V, "  CALL_SAYS: { reply: 'reply',", "  CALL_SAYS: { review: 'first review of the new guesses and tests, in one request', reply: 'reply',")
print("patched")
