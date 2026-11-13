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
