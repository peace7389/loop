"""Figures counted from one session's records, for the row control.py gives the page for each session (Home, Compare),
so that the page does not read every ledger to show them. recs: the records of the ledger WITHOUT its draft records.
The page counts the same figures for the one session it has open, from that session's own records
(viewer/evidence_verdicts.js); the page checks compare both with a third count made from the ledgers.
A void check (void_checks: its decision rule compared a simulation with itself) counts neither as held nor as failed
in any of these figures; harness/audit.py writes the same finding out in full for one session."""
import re

LABEL = re.compile(r"[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)")  # measure@label in a decision rule


def void_checks(recs):
    """{check id: "void" or "one simulation"} for the checks whose decision rule compared a simulation with itself: the
    rule names two or more labels, and at least two of them are the same simulation (the same run in that experiment:
    a design repeated under another label, or returned from the same earlier simulation). "one simulation" is the
    stricter case: every label the rule names is that one simulation."""
    run, out = {}, {}
    for r in recs:
        if r["type"] == "simulation":
            run[(r.get("parent"), (r.get("body") or {}).get("label"))] = (r.get("body") or {}).get("run_id")
    for r in recs:
        if r["type"] != "check":
            continue
        b = r.get("body") or {}
        labels = list(dict.fromkeys(LABEL.findall(str(b.get("decision_rule") or b.get("rule") or ""))))
        ids = [run.get((r.get("parent"), l)) for l in labels]
        known = [i for i in ids if i]
        if len(labels) >= 2 and len(set(known)) < len(known):
            out[r["id"]] = "one simulation" if len(set(ids)) == 1 else "void"
    return out


def void_count(recs):
    """[void checks, all checks]; None for the first format, which has no checks by the harness."""
    if not any(r["type"] in ("check", "simulation") for r in recs):
        return None if any(r["type"] == "evidence" for r in recs) else [0, 0]
    return [len(void_checks(recs)), sum(r["type"] == "check" for r in recs)]


def held_failed(recs):
    """[checks that held, checks that failed], without the void ones."""
    void = void_checks(recs)
    res = [(r.get("body") or {}).get("result") for r in recs if r["type"] == "check" and r["id"] not in void]
    return [res.count("held"), res.count("failed")]


def verdicts_against_checks(recs):
    """One count per verdict: {row: {column: n}}.
    Row: the checks of the verdict's hypothesis in the last experiment that tested it before the verdict: "held" (all
    held), "failed" (all failed), "mixed", "void" (every one of them void: the verdict rests on void checks), or
    "no check" (the first format has no checks). A void check beside checks that are not void is left out of the row.
    Column: the verdict's result (supported, inconclusive, refuted), and "no verdict" for a hypothesis that was checked
    and never judged."""
    made, judged, out, void = {}, set(), {}, void_checks(recs)

    def row(h, before):
        cs = [c for c in made.get(h, []) if c[0] < before]
        if not cs:
            return "no check"
        res = [r for _, x, r in cs if x == cs[-1][1] and r != "void"]
        return "void" if not res else "held" if all(r == "held" for r in res) else "failed" if all(r == "failed" for r in res) else "mixed"

    def add(r, c):
        out.setdefault(r, {})
        out[r][c] = out[r].get(c, 0) + 1

    for i, r in enumerate(recs):
        b = r.get("body") or {}
        if r["type"] == "check" and b.get("result") in ("held", "failed"):
            made.setdefault(b.get("for"), []).append((i, b.get("experiment") or r.get("parent"), "void" if r["id"] in void else b["result"]))
        elif r["type"] == "verdict":
            add(row(b.get("for"), i), b.get("result"))
            judged.add(b.get("for"))
    for h in made:
        if h not in judged:
            add(row(h, len(recs)), "no verdict")
    return out


def checks_in_order(recs):
    """The session's checks in the order they were made, one letter each (h = held, f = failed, v = void, n = not checked), with
    a space between turns: "hhh hf hfh hhhh". None for a session in the first format, which has no checks by the harness."""
    if not any(r["type"] in ("check", "simulation") for r in recs):
        return None if any(r["type"] == "evidence" for r in recs) else ""
    out, last, void = [], None, void_checks(recs)
    for r in recs:
        if r["type"] == "check":
            if last is not None and r.get("turn") != last:
                out.append(" ")
            out.append("v" if r["id"] in void else {"held": "h", "failed": "f"}.get((r.get("body") or {}).get("result"), "n"))
            last = r.get("turn")
    return "".join(out)


def returned_simulations(recs):
    """[simulations returned from an earlier one (same settings and seed, not run again), all simulations]; None for the
    first format, which has no simulation records."""
    sims = [r for r in recs if r["type"] == "simulation"]
    if not sims:
        return None if any(r["type"] == "evidence" for r in recs) else [0, 0]
    return [sum(1 for r in sims if (r.get("body") or {}).get("same_as")), len(sims)]


def unnamed_simulations(recs):
    """[simulations that no decision rule names, the simulations of the experiments that test]; None for the first
    format. A decision rule names a simulation by its label after @; in an experiment of one simulation a rule names it
    without a label."""
    import re
    sims = [r for r in recs if r["type"] == "simulation"]
    if not sims:
        return None if any(r["type"] == "evidence" for r in recs) else [0, 0]
    exps = {r["id"]: r.get("body") or {} for r in recs if r["type"] == "experiment"}
    unnamed = testing = 0
    for r in sims:
        x = exps.get(r.get("parent")) or {}
        if x.get("kind") != "test":
            continue
        testing += 1
        rules = x.get("decision_rules") or x.get("rules") or []
        text = " ".join(str(d.get("decision_rule") or d.get("rule") or "") for d in rules)
        named = (r.get("body") or {}).get("label") in set(re.findall(r"@([A-Za-z0-9_]+)", text)) or (len(x.get("runs") or []) == 1 and bool(rules))
        unnamed += not named
    return [unnamed, testing]


def findings_counts(recs):
    """The findings of a session (2026-11-22, the operator: findings raised by each agent, how many ended closed, parked or unresolved, and how
    many turns each stayed open), or None for a session without findings (every session before 2026-11-22: its row is as before).
    {"raised": {"researcher": n, "supervisor": n}, "ended": {"closed": n, "same_as": n, "parked": n, "working": n, "unresolved": n},
     "turns_open": {"mean": x, "max": n}, "never_looked_at": n, "final": whether the harness's tally at the end was read}.
    From the harness's tally at the end (findings_end) when there is one; for a session still running, from its findings and decisions so far
    (turns counted to its latest turn; never_looked_at is then not counted: None)."""
    fs = [r for r in recs if r["type"] == "finding"]
    if not fs:
        return None
    raised = {"researcher": sum(r.get("by") == "model" for r in fs), "supervisor": sum(r.get("by") == "supervisor" for r in fs)}
    end = next((r for r in reversed(recs) if r["type"] == "findings_end"), None)
    if end:
        rows = (end.get("body") or {}).get("findings") or []
        status = [x.get("status") for x in rows]
        spans = [x.get("turns_open") or 0 for x in rows]
        never = sum(bool(x.get("never_looked_at")) for x in rows)
    else:
        now, st = max((r.get("turn") or 0 for r in recs), default=0), {r["id"]: ("open", r.get("turn") or 0, None) for r in fs}
        for r in recs:
            b = r.get("body") or {}
            if r["type"] == "decision" and b.get("for") in st:
                st[b["for"]] = ({"work": "working", "park": "parked", "close": "closed", "same_as": "same_as"}.get(b.get("action"), "open"), st[b["for"]][1], r.get("turn"))
        status = ["unresolved" if s == "open" else s for s, _, _ in st.values()]
        spans = [((at if s in ("closed", "same_as") else now) - t) for s, t, at in st.values()]
        never = None
    return {"raised": raised, "ended": {k: status.count(k) for k in ("closed", "same_as", "parked", "working", "unresolved")},
            "turns_open": {"mean": round(sum(spans) / len(spans), 1), "max": max(spans)}, "never_looked_at": never, "final": end is not None}


def design_rounds(recs):
    """The review of tests before they run, in rounds (the arm "supervised", since 2026-11-22, after the reviews of s047 and s050), or None for a
    session without rounds (every session before: its row is as before). A test is one hypothesis's test proposed in one turn.
    {"tests": proposed (reviewed, or refused by the harness before any review), "reviewed": n, "rounds": {"mean": x, "max": n} per reviewed test,
     "approved_first": approved in round 1, "repaired_approved": approved after a repair, "contested": run although the supervisor still objected,
     "dropped": its hypothesis dropped after the last round, "unsettled": left sent back (its repair could not be read or used),
     "refused_by_harness": refused before any review (no rival, or one under which the rule would hold too), "not_run": the harness could not use
     the repair of the last round, so the test did not run (present only where it occurs)}"""
    rv = [r for r in recs if r["type"] == "review" and (r.get("body") or {}).get("gate") == "design" and (r.get("body") or {}).get("round")]
    if not rv:
        return None
    tests = {}
    for r in rv:
        tests.setdefault((r["body"].get("for"), r.get("turn")), []).append((r["body"]["round"], r["body"].get("decision")))
    refused = sum(1 for r in recs if r["type"] == "note" and str((r.get("body") or {}).get("part") or "").startswith("test of "))
    last = {k: max(v)[1] for k, v in tests.items()}
    rounds = [max(n for n, _ in v) for v in tests.values()]
    return {"tests": len(tests) + refused, "reviewed": len(tests), "rounds": {"mean": round(sum(rounds) / len(rounds), 2), "max": max(rounds)},
            "approved_first": sum(1 for v in tests.values() if (1, "approved") in v), "repaired_approved": sum(1 for v in tests.values() if any(d == "approved" and n > 1 for n, d in v)),
            "contested": sum(d == "contested" for d in last.values()), "dropped": sum(d == "dropped" for d in last.values()),
            "unsettled": sum(d == "sent_back" for d in last.values()), "refused_by_harness": refused,
            **({"not_run": n} if (n := sum(d == "not_run" for d in last.values())) else {})}   # not_run: the harness could not use the last repair (the coherence audit, 2026-11-22); only where it occurs


def guess_reviews(recs):
    """The guesses of a session in the arm "supervised" since 2026-11-22 (part D, after s050 and s051), or None for a session before it (its row is as
    before): {"guesses": accepted, "warnings": accepted with the supervisor's warning (not_from_what_was_learned), "restated": restated in the same
    turn after a refusal, "contested": accepted although the harness or the supervisor still found something against them}."""
    ws = [r for r in recs if r["type"] == "why"]
    ground = [r for r in recs if r["type"] == "review" and (r.get("body") or {}).get("gate") == "ground"]
    if not any("warning" in (r.get("body") or {}) for r in ground) and not any((r.get("body") or {}).get("restated") for r in ws):
        return None
    contested = {r["id"] for r in ws if (r.get("body") or {}).get("contested")} | {(r.get("body") or {}).get("for") for r in ground if (r.get("body") or {}).get("decision") == "contested"}
    return {"guesses": len(ws), "warnings": sum(1 for r in ground if (r.get("body") or {}).get("warning")), "restated": sum(1 for r in ws if (r.get("body") or {}).get("restated")),
            "contested": len({c for c in contested if c})}


def competitor_figures(recs):
    """A session with competitors (stage 5 of the coherence audit, 2026-11-22), or None for one without (its row is as before): {"questions": for each
    of honest, consistent, correct, how many tests passed and failed it at their last review round; "approved_then_unfair": tests approved at review and
    ruled not fair; "misses": by question, the ruling's failures of a question the review passed that could have been seen before the run, and
    "found_by_result" those that could not; "from_feedback": competing guesses written after the supervisor named a missing competitor;
    "refuted_by_competition": guesses refuted because they did not fit the result of a fair test; "held": tests held for a missing competitor or a
    failed Consistent}. A session of v2 (its reviews have the box Follows) adds "follows" to the questions, and: "cannot_tell", the boxes answered
    "cannot tell" at the reviews (every round) and at the rulings (the questions and the two fits); "changed", by question, the rulings that do not pass
    a question the review passed (it replaces "misses" and "found_by_result", which stay at 0 there: the supervisor is no longer asked "foreseeable")."""
    rv = [r for r in recs if r["type"] == "review" and r.get("by") == "supervisor" and (r.get("body") or {}).get("gate") == "design" and "honest" in (r.get("body") or {})]
    if not rv:
        return None
    last = {}
    for r in rv:
        k = (r["body"].get("for"), r.get("turn"))
        if k not in last or r["body"].get("round", 0) >= last[k]["body"].get("round", 0):
            last[k] = r
    qs = ("honest", "consistent", "correct")
    rulings = [r for r in recs if r["type"] == "verdict" and r.get("by") == "supervisor" and (r.get("body") or {}).get("questions")]
    approved = {(r["body"].get("for"), r.get("turn")) for r in last.values() if r["body"].get("decision") == "approved"}
    old = ("honest", "consistent", "correct")
    misses = {q: sum(1 for v in rulings for m in v["body"].get("misses") or [] if m.get("question") == q and m.get("foreseeable") == "yes") for q in old}
    found = {q: sum(1 for v in rulings for m in v["body"].get("misses") or [] if m.get("question") == q and m.get("foreseeable") != "yes") for q in old}
    from_why = {r["id"]: (r.get("body") or {}).get("from_why") for r in recs if r["type"] == "hypothesis"}
    # as loop.guess_refutations: the tested guess is refuted through its hypothesis only where the review found that the hypothesis follows from it (v2)
    refuted = {y for v in rulings if v["body"].get("fair") and not v["body"].get("fits_contradicted") for y, f in (v["body"].get("fits") or {}).items()
               if f == "does not fit" and not (y == from_why.get(v["body"].get("for")) and v["body"].get("follows") not in (None, "pass"))}
    v2 = any("follows" in r["body"] for r in rv)
    if v2:
        qs = ("follows",) + qs
    new = {} if not v2 else {
        "cannot_tell": sum(1 for r in rv for q in qs if r["body"].get(q) == "cannot tell") + sum(len(v["body"].get("cannot_tell") or []) for v in rulings),
        "changed": {q: sum(1 for v in rulings if q in (v["body"].get("changed") or [])) for q in qs if q != "follows"}}
    return {**new, "questions": {q: {"pass": sum(1 for r in last.values() if r["body"].get(q) == "pass"), "fail": sum(1 for r in last.values() if r["body"].get(q) == "fail")} for q in qs},
            "approved_then_unfair": sum(1 for v in rulings if (v["body"].get("for"), v.get("turn")) in approved and not v["body"].get("fair")),
            "misses": misses, "found_by_result": found, "from_feedback": sum(1 for r in recs if r["type"] == "why" and (r.get("body") or {}).get("from_feedback")),
            "refuted_by_competition": len(refuted), "held": sum(1 for r in last.values() if r["body"].get("decision") == "held")}
