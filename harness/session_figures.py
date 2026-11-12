"""Figures counted from one session's records, for the row control.py gives the page for each session (Home, Compare),
so that the page does not read every ledger to show them. recs: the records of the ledger WITHOUT its draft records.
The page counts the same figures for the one session it has open, from that session's own records
(viewer/evidence_verdicts.js); the page checks compare both with a third count made from the ledgers."""


def verdicts_against_checks(recs):
    """One count per verdict: {row: {column: n}}.
    Row: the checks of the verdict's hypothesis in the last experiment that tested it before the verdict: "held" (all
    held), "failed" (all failed), "mixed", or "no check" (the first format has no checks).
    Column: the verdict's result (supported, inconclusive, refuted), and "no verdict" for a hypothesis that was checked
    and never judged."""
    made, judged, out = {}, set(), {}

    def row(h, before):
        cs = [c for c in made.get(h, []) if c[0] < before]
        if not cs:
            return "no check"
        res = [r for _, x, r in cs if x == cs[-1][1]]
        return "held" if all(r == "held" for r in res) else "failed" if all(r == "failed" for r in res) else "mixed"

    def add(r, c):
        out.setdefault(r, {})
        out[r][c] = out[r].get(c, 0) + 1

    for i, r in enumerate(recs):
        b = r.get("body") or {}
        if r["type"] == "check" and b.get("result") in ("held", "failed"):
            made.setdefault(b.get("for"), []).append((i, b.get("experiment") or r.get("parent"), b["result"]))
        elif r["type"] == "verdict":
            add(row(b.get("for"), i), b.get("result"))
            judged.add(b.get("for"))
    for h in made:
        if h not in judged:
            add(row(h, len(recs)), "no verdict")
    return out


def checks_in_order(recs):
    """The session's checks in the order they were made, one letter each (h = held, f = failed, n = not checked), with
    a space between turns: "hhh hf hfh hhhh". None for a session in the first format, which has no checks by the harness."""
    if not any(r["type"] in ("check", "simulation") for r in recs):
        return None if any(r["type"] == "evidence" for r in recs) else ""
    out, last = [], None
    for r in recs:
        if r["type"] == "check":
            if last is not None and r.get("turn") != last:
                out.append(" ")
            out.append({"held": "h", "failed": "f"}.get((r.get("body") or {}).get("result"), "n"))
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
