"""v2, stage 2e: the session's figures know the fourth box and what replaced "foreseeable". A session recorded before v2 gives the figures it gave
(its reviews have no box Follows: no new key appears); a v2 session adds, with no judgment in the code:
  questions.follows   how many tests passed and failed Follows at their last review round;
  cannot_tell         boxes answered "cannot tell", at the reviews (every round) and at the rulings (the three questions and the two fits);
  changed             by question, rulings that do not pass a question the review of that test passed (the harness compares the two sets of boxes).
refuted_by_competition counts as loop.guess_refutations refutes: the tested guess only where its hypothesis was found to follow from it."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
F = "harness/session_figures.py"
sub(F, '''    failed Consistent}."""
    rv = [r for r in recs''', '''    failed Consistent}. A session of v2 (its reviews have the box Follows) adds "follows" to the questions, and: "cannot_tell", the boxes answered
    "cannot tell" at the reviews (every round) and at the rulings (the questions and the two fits); "changed", by question, the rulings that do not pass
    a question the review passed (it replaces "misses" and "found_by_result", which stay at 0 there: the supervisor is no longer asked "foreseeable")."""
    rv = [r for r in recs''', "the figures' description")
sub(F, '''    refuted = {y for v in rulings if v["body"].get("fair") and not v["body"].get("fits_contradicted") for y, f in (v["body"].get("fits") or {}).items() if f == "does not fit"}
    return {"questions": {q: {"pass": sum(1 for r in last.values() if r["body"].get(q) == "pass"), "fail": sum(1 for r in last.values() if r["body"].get(q) == "fail")} for q in qs},''',
'''    from_why = {r["id"]: (r.get("body") or {}).get("from_why") for r in recs if r["type"] == "hypothesis"}
    # as loop.guess_refutations: the tested guess is refuted through its hypothesis only where the review found that the hypothesis follows from it (v2)
    refuted = {y for v in rulings if v["body"].get("fair") and not v["body"].get("fits_contradicted") for y, f in (v["body"].get("fits") or {}).items()
               if f == "does not fit" and not (y == from_why.get(v["body"].get("for")) and v["body"].get("follows") not in (None, "pass"))}
    v2 = any("follows" in r["body"] for r in rv)
    if v2:
        qs = ("follows",) + qs
    new = {} if not v2 else {
        "cannot_tell": sum(1 for r in rv for q in qs if r["body"].get(q) == "cannot tell") + sum(len(v["body"].get("cannot_tell") or []) for v in rulings),
        "changed": {q: sum(1 for v in rulings if q in (v["body"].get("changed") or [])) for q in qs if q != "follows"}}
    return {**new, "questions": {q: {"pass": sum(1 for r in last.values() if r["body"].get(q) == "pass"), "fail": sum(1 for r in last.values() if r["body"].get(q) == "fail")} for q in qs},''',
    "the figures of a v2 session: Follows, cannot tell, changed; refutations counted as the harness refutes")
sub(F, '''    misses = {q: sum(1 for v in rulings for m in v["body"].get("misses") or [] if m.get("question") == q and m.get("foreseeable") == "yes") for q in qs}
    found = {q: sum(1 for v in rulings for m in v["body"].get("misses") or [] if m.get("question") == q and m.get("foreseeable") != "yes") for q in qs}''',
'''    old = ("honest", "consistent", "correct")
    misses = {q: sum(1 for v in rulings for m in v["body"].get("misses") or [] if m.get("question") == q and m.get("foreseeable") == "yes") for q in old}
    found = {q: sum(1 for v in rulings for m in v["body"].get("misses") or [] if m.get("question") == q and m.get("foreseeable") != "yes") for q in old}''',
    "misses and found_by_result stay over the three older questions")
done("stage2e", "v2, stage 2e: the session's figures (no text an agent reads)")
