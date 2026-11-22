"""Stage 1, items 10, 11 and 13 (the coherence audit, 2026-11-22):
10. budget: each repaired test that is accepted counts its new simulations before the next repair is checked (several repairs could overrun the brief's
    limit); what is left is never below 0 (the free turns refused every experiment at -1); a continued session takes what it used, was granted, and
    which of its last turns it is in, from its ledger (it got its whole budget again);
11. the last turns ("budget", "report"): a reply with no report ends the session as an unusable last turn does (a reply carrying a finding decision
    took the requests-only path, which sets no ending, and the last turn came again without end);
13. the baseline and the supervisor's first look run inside the guard that records how a session ended, after the stop handlers are set.
Usage: s1_loop.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)
# 13: the baseline moves inside the guard
rep('''    fresh = not ledger   # a new ledger: the baseline runs now
    if a.baseline == "on":
        baseline(ledger)
    turn, sims,''', '''    fresh = not ledger   # a new ledger: the baseline runs now (inside the guard below, after the stop handlers: the coherence audit, 2026-11-22)
    turn, sims,''')
rep('''    free_left = FREE_TURNS  # the turns after the budget is used up in which the researcher may still look and test on simulations already run (s048)''',
    '''    free_left = FREE_TURNS  # the turns after the budget is used up in which the researcher may still look and test on simulations already run (s048)
    if not fresh:   # a continued session (the coherence audit, 2026-11-22: it got its whole budget again): what it used, was granted and where it stands, from its ledger
        sims = sum(1 for r in ledger if r["type"] == "simulation" and r["turn"] >= 1 and "same_as" not in r["body"])
        grants = [int(g.group(1)) for r in ledger if r["type"] == "note" and (g := re.search(r"the budget is now (\\d+)", str(r["body"].get("text") or "")))]
        budget = grants[-1] if grants else budget
        free_left = max(0, FREE_TURNS - sum(1 for r in ledger if r["type"] == "turn" and r["body"].get("last_turn") == "free"))
        giving_up = any(r["type"] == "turn" and r["body"].get("last_turn") == "report" for r in ledger)''')
rep('''    if arm == "supervised" and fresh and any(r["id"] == "E0" for r in ledger):   # findings (2026-11-22): the baseline's results come in with no ruling, so the supervisor looks at them
        try:
            stage("look", "X0")
            items, saw = sup_findings_of(model, brief, ledger, "X0")
            take_sup_findings(ledger, 0, items, "E0")
            sup_log("X0", "findings", saw, {"findings": items})
        except (ValueError, KeyError, TypeError) as e:
            append(ledger, 0, "note", "E0", {"text": f"the supervisor's look at the baseline could not be read ({type(e).__name__}): no finding of its own"})
    try:
        while how is None:''', '''    try:
        if a.baseline == "on":
            baseline(ledger)
        if arm == "supervised" and fresh and any(r["id"] == "E0" for r in ledger):   # findings (2026-11-22): the baseline's results come in with no ruling, so the supervisor looks at them
            try:
                stage("look", "X0")
                items, saw = sup_findings_of(model, brief, ledger, "X0")
                take_sup_findings(ledger, 0, items, "E0")
                sup_log("X0", "findings", saw, {"findings": items})
            except Exception as e:   # its look is not needed to go on: a note, and the session goes on (the coherence audit, 2026-11-22: a model server error stopped it unrecorded)
                append(ledger, 0, "note", "E0", {"text": f"the supervisor's look at the baseline could not be read ({type(e).__name__}): no finding of its own"})
        while how is None:''')
# 10: never below 0; each accepted repair is counted before the next
rep('''                ok, no = sort_out(parsed, brief, ledger, budget - sims, mode,''', '''                ok, no = sort_out(parsed, brief, ledger, max(0, budget - sims), mode,''')
rep('''            why = experiment_problem(t3, brief, ledger, budget - sims - reserved, states(ledger)[0], lean=True)''', '''            why = experiment_problem(t3, brief, ledger, max(0, budget - sims - reserved), states(ledger)[0], lean=True)''')
rep('''                    ex2 = repair_rounds(hid, test, rev, gid, every, reserved)
                    if ex2 is not None:
                        later.append(ex2)''', '''                    ex2 = repair_rounds(hid, test, rev, gid, every, reserved)
                    if ex2 is not None:
                        later.append(ex2)
                        reserved += sum(1 for q in plan(ledger, ex2["runs"]) if not q.get("prior"))   # the next repair is checked against what is left after this one (the coherence audit, 2026-11-22)''')
# 11: the last turns: findings and decisions alone are not a usable reply, and a reply with no report ends the session there
rep('''                if any(ok.values()) or rq or parsed.get("findings") or parsed.get("decisions"):''', '''                if any(ok.values()) or rq or ((parsed.get("findings") or parsed.get("decisions")) and mode not in ("budget", "report")):   # in the last turns only the report is a usable reply (the coherence audit, 2026-11-22)''')
rep('''                stay_next = mode in (None, "free") and stay < CONTINUES   # no step yet: the researcher is asked again in this turn, with what it asked for answered
                continue''', '''                stay_next = mode in (None, "free") and stay < CONTINUES   # no step yet: the researcher is asked again in this turn, with what it asked for answered
                if mode == "report":   # a last turn without the report ends the session, as an unusable one does (the coherence audit, 2026-11-22: the last turn came again without end)
                    how = f"{UNUSABLE} turns in a row without a usable answer"
                elif mode == "budget" and not need_now:
                    how = "all simulations used, no usable report"
                continue''')
p.write_text(s); print("patched", p)
