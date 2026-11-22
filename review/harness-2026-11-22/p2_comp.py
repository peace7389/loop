"""After the deploy (2026-11-23, night), found in session s055 turn 2 (stage 5, competitors):
- a repair's record kept "rival" and not the competes_with the repair named: the researcher's own ledger text read "rival: None" for its repairs;
- the supervisor judged "missing" (a competing cause that is none of the researcher's guesses) without being shown the guesses: it held the test of
  H4 for "TCP still cannot establish", which the researcher's Y2 states. The test review (single and batched) now lists every guess of the
  researcher with its standing; "missing" is only a cause none of them states (a refuted guess counts as ruled out), and where one states it the
  feedback names its id, so that the repair can test against it in the same turn.
Usage: p2_comp.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a)); s = s.replace(a, b)
rep('''            rid = append(ledger, turn, "repair", parent, {"for": hid, "round": n, **{k: rp.get(k) for k in ("decision_rule", "rival", "rival_predicts")}, "runs": rp.get("runs") or []})''',
    '''            rid = append(ledger, turn, "repair", parent, {"for": hid, "round": n, **{k: rp.get(k) for k in ("decision_rule", "competes_with" if competitors else "rival", "rival_predicts")}, "runs": rp.get("runs") or []})''')
rep('''        return (f"your repair of the test of {b['for']} for round {b['round']}: {flat(b.get('decision_rule'))} (rival: {flat(b.get('rival'))}; under it: {str(b.get('rival_predicts')).upper()})"''',
    '''        return (f"your repair of the test of {b['for']} for round {b['round']}: {flat(b.get('decision_rule'))} (" + (f"competes with {b['competes_with']}" if b.get("competes_with") else f"rival: {flat(b.get('rival'))}") + f"; under it: {str(b.get('rival_predicts')).upper()})"''')
# the researcher's guesses, for the supervisor's test review
rep('''def competitor_text(ledger, rules, ex=None):''', '''def guesses_text(ledger):
    """Every guess of the researcher with its standing, for the supervisor's review of a test with competitors (it judges whether a competing cause is
    missing: s055, 2026-11-23, it held a test for a cause one of the guesses stated)."""
    flat = lambda v: " ".join(str(v).split())
    refuted, ws = guess_refutations(ledger), why_states(ledger)
    lines = [f"  [{r['id']}] " + (f"(refuted by {refuted[r['id']]}) " if r["id"] in refuted else f"(revised as {ws[r['id']]['as']}) " if (ws.get(r["id"]) or {}).get("as") else "")
             + f"{flat(r['body'].get('guess'))}" + (f" | competes with {r['body']['competes_with']}" if r["body"].get("competes_with") else "") for r in ledger if r["type"] == "why"]
    return "THE RESEARCHER'S GUESSES SO FAR (a competing cause may already be one of them):\\n" + ("\\n".join(lines) or "  (none)") + "\\n\\n"


def competitor_text(ledger, rules, ex=None):''')
rep('''{_looked(ledger)}\\n\\n" + item + (f"THIS IS ROUND {round_no} of at most {REVIEW_ROUNDS} for this test.''',
    '''{_looked(ledger)}\\n\\n" + (guesses_text(ledger) if COMP["on"] else "") + item + (f"THIS IS ROUND {round_no} of at most {REVIEW_ROUNDS} for this test.''')
rep('''            + (f"THE SESSION'S EARLIER GUESSES AND HYPOTHESES:\\n{gp[0]['earlier']}\\n\\nTHE RULINGS SO FAR:\\n{gp[0]['rulings']}\\n\\n" if gp else "")''',
    '''            + (f"THE SESSION'S EARLIER GUESSES AND HYPOTHESES:\\n{gp[0]['earlier']}\\n\\nTHE RULINGS SO FAR:\\n{gp[0]['rulings']}\\n\\n" if gp else "")
            + (guesses_text(tledger or ledger) if COMP["on"] and tests else "")''')
rep('''    "missing": {"type": "string", "description": "when the competing cause this test needs is not among the researcher's guesses: that cause, in one sentence; else empty"},''',
    '''    "missing": {"type": "string", "description": "only when the competing cause this test needs is stated by none of the researcher's guesses listed in the request (a refuted one is ruled out): that cause, in one sentence; else empty. When a listed guess states it, leave this empty and name that guess's id in feedback"},''')
rep('''"named, do not replace it with your own; if the cause this test needs is none of the researcher's guesses, name it in missing. Last, feedback for the researcher: which "''',
    '''"named, do not replace it with your own. If the competing cause this test needs is a guess listed above other than the one the rule names, say so in feedback with its id; only if none of them states it, name it in missing. Last, feedback for the researcher: which "''')
p.write_text(s); print("patched", p)
