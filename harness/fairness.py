"""Operator tool: the start of the fairness audit of one session (v2, stage 7). Usage:
    fairness.py SESSION

A session is fair to measure when its answer is the researcher's and not the texts': no text it was sent named the answer, no rule of the harness
it could not know stopped it, and what the supervisor decided follows from what the supervisor was shown. The audit itself is read and written by
the auditor; this tool gives it its figures and its form:
  checks/fairness/<session>.figures.json   the figures, from the session's records: session_figures.fairness_figures (the refusals by the rule of the
        chain, the boxes answered "cannot tell", in which round each test was approved, whether the answer stands in turn 1), the rounds, the guesses
        and the supervisor's boxes as the session's row has them, the parked findings with their reasons, the checks decided by less than the
        tolerance, the notes of the harness by the part they refused, and the confirmation of the answer in short where checks/confirm/<session>.json
        exists. Written again each time.
  checks/fairness/<session>.md             made once: the figures in sentences, then every item of checks/fairness/CHECKLIST.md with "not judged yet".
        A file that exists is never touched: the judgements in it are the auditor's.
Operator only: under checks/, named by no tool and no text of the agents."""
import argparse, json
from pathlib import Path
import session_figures, tools

CHECKS = tools.ROOT / "checks"


def figures(sid):
    D = tools.SESSIONS / sid
    meta = json.loads((D / "session.json").read_text())
    recs = [r for r in (json.loads(l) for l in (D / "ledger.jsonl").read_text().splitlines() if l.strip()) if r["type"] not in ("draft", "scratch")]
    body = lambda r: r.get("body") or {}
    parked = [{"finding": body(r).get("id"), "turn": r.get("turn"), "reason": body(r).get("reason")} for r in recs if r["type"] == "decision" and body(r).get("action") == "park"]
    little = [{"check": r.get("id"), "for": body(r).get("for"), "turn": r.get("turn"), "percent": [q.get("percent") for q in body(r).get("within_tolerance") or []]} for r in recs if r["type"] == "check" and body(r).get("within_tolerance")]
    notes = {}
    for r in recs:
        if r["type"] == "note" and body(r).get("part"):
            part = str(body(r)["part"]).split()[0]   # "decision for F2", "test of H3", "design q100": by their first word
            notes[part] = notes.get(part, 0) + 1
    conf = CHECKS / "confirm" / f"{sid}.json"
    c = json.loads(conf.read_text()) if conf.is_file() else None
    return {"session": sid, "brief": meta.get("brief") or (meta.get("given") or {}).get("id"), "arm": (meta.get("flags") or {}).get("arm") or "hypotheses", "how": meta.get("how"),
            "turns": meta.get("turns"), "simulations": meta.get("simulations"), "allowed": ((meta.get("given") or {}).get("limits") or {}).get("simulations"),
            "fairness": session_figures.fairness_figures(recs, meta.get("given")), "rounds": session_figures.design_rounds(recs), "guesses": session_figures.guess_reviews(recs),
            "boxes": session_figures.competitor_figures(recs), "findings": session_figures.findings_counts(recs), "parked": parked, "decided_by_less_than_the_tolerance": little,
            "changed_by_harness": sum(1 for r in recs if r["type"] == "verdict" and body(r).get("changed_by_harness")), "notes_by_part": notes,
            "confirmation": c and {"seeds": c["how"]["seeds"], "seconds": c["how"]["seconds"], "conditions_hold_in": c["conditions_hold_in"], "of": len(c["runs"]), "target": c["target"],
                                   "the_session_measured": [q["target"] for q in c["the_session_measured"] if not q["returned"]], "the_report_expects": c["the_report_expects"]}}


def sentences(f):
    """The figures as sentences, for the head of the audit."""
    fa, out, never = f["fairness"], [], "never"
    out.append(f"Session {f['session']} on the brief {f['brief']}, arm {f['arm']}: ended \"{f['how']}\" after {f['turns']} turns and {f['simulations']} of {f['allowed']} simulations.")
    if fa is None:
        out.append("It has no guesses (not the arm with a supervisor): the figures of the chain, of the boxes and of turn 1 do not apply.")
    else:
        t1 = fa["turn_1"]
        if t1 is None:
            out.append("It ended without a final report: there is no answer to look for in turn 1.")
        elif not t1["answer"]:
            out.append("Its answer changes nothing (every setting at its default, the network as given).")
        else:
            out.append(f"Its answer: {'; '.join(t1['answer'])}. Already simulated in turn 1: {'; '.join(t1['simulated_in_turn_1']) or 'none of it'}. Named in the words of turn 1's guesses and hypotheses: {'; '.join(t1['named_in_turn_1']) or 'none of it'}. "
                       f"First simulated in turn: {', '.join(f'{k}: {v if v is not None else never}' for k, v in t1['first_seen'].items())}.")
        out.append(f"Guesses refused by the rule of the chain: {fa['chain_refusals']}. Boxes answered \"cannot tell\": {fa['cannot_tell'] if fa['cannot_tell'] is not None else 'not recorded (a session before v2)'}. "
                   f"Tests approved, by round: {', '.join(f'round {k}: {v}' for k, v in fa['approved_by_round'].items()) or 'none'}; not approved in their last round: {fa['not_approved']}.")
    out.append(f"Findings parked: {len(f['parked'])}" + (": " + "; ".join(f"{p['finding']} in turn {p['turn']} (\"{p['reason']}\")" for p in f["parked"]) if f["parked"] else "") + ".")
    out.append(f"Checks decided by less than the tolerance: {len(f['decided_by_less_than_the_tolerance'])}" + (": " + ", ".join(f"{q['check']} for {q['for']}" for q in f["decided_by_less_than_the_tolerance"]) if f["decided_by_less_than_the_tolerance"] else "") + f". Rulings the harness changed: {f['changed_by_harness']}.")
    out.append("Parts the harness refused, by part: " + (", ".join(f"{k}: {v}" for k, v in sorted(f["notes_by_part"].items())) or "none") + ".")
    c = f["confirmation"]
    out.append("The answer was not measured again (harness/confirm.py)." if c is None else
               f"The answer measured again ({len(c['seeds'])} seeds, {c['seconds']} s each): the conditions hold in {c['conditions_hold_in']} of {c['of']}; the target between {c['target']['smallest']} and {c['target']['largest']}"
               f" (the session measured {', '.join(map(str, c['the_session_measured'])) or 'no simulation of this answer'}; the report expects {c['the_report_expects']}).")
    return out


def main():
    ap = argparse.ArgumentParser(description="The figures and the form of the fairness audit of one session.")
    ap.add_argument("session")
    a = ap.parse_args()
    D = tools.SESSIONS / a.session
    if not (D / "session.json").is_file() or not (D / "ledger.jsonl").is_file():
        ap.error(f"no session {a.session}")
    top = CHECKS / "fairness"
    top.mkdir(parents=True, exist_ok=True)
    f = figures(a.session)
    (top / f"{a.session}.figures.json").write_text(json.dumps(f, indent=1) + "\n")
    md = top / f"{a.session}.md"
    if md.is_file():
        print(f"{md.name} exists: left as it is (the figures were written again)")
        return
    listed = top / "CHECKLIST.md"
    items = [l[2:].strip() for l in listed.read_text().splitlines() if l.startswith("- ")] if listed.is_file() else []
    text = [f"# Fairness audit of {a.session}", "", "The figures (`" + f"{a.session}.figures.json" + "`, from the session's records):", ""] + [f"- {s}" for s in sentences(f)]
    text += ["", "## The checklist (`CHECKLIST.md`)", ""] + [x for i, item in enumerate(items, 1) for x in (f"{i}. {item}", "", "   not judged yet", "")]
    text += ["## Verdict", "", "not judged yet (fair to measure / fair with a reservation / not fair, and why in one sentence)", ""]
    md.write_text("\n".join(text))
    print(f"wrote {md} and {a.session}.figures.json")


if __name__ == "__main__":
    main()
