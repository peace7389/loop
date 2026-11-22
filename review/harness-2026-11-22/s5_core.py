"""Stage 5 of the coherence audit (2026-11-22, night), part 1: competitors are guesses (the operator's sheet "competitors are guesses", with the
corrections of plans/2026-11-22-coherence-audit.md). The arm "supervised", in a session started with COMPETITORS on:
- a decision rule names competes_with (the id of another guess) instead of a rival sentence; the harness checks it before any call: a guess that
  exists and is live (not revised, not refuted), not the hypothesis's own nor linked to it by revises; rival_predicts as before (held refused);
- a guess may declare competes_with: Yn; it then may cite Yn's records (the chain's exception), and its reading is told so;
- refutation follows the standing ruling: a guess that does not fit the result of a test ruled fair is refuted by that ruling (an objection that
  changes the ruling undoes it); with the earlier rule of the arm (a guess all of whose hypotheses were ruled refuted) it is ONE function, shown
  in the researcher's ledger text ("refuted by V4"); no hypothesis comes from a refuted guess; a new guess may revise it.
Usage: s5_core.py HARNESS_DIR"""
import sys
from pathlib import Path
H = Path(sys.argv[1])
p = H / "loop.py"; s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:110], s.count(a)); s = s.replace(a, b)

rep('''BATCH_FIRST = True   #''', '''COMPETITORS = True   # the arm "supervised": a decision rule names the guess it competes with, and the supervisor reviews and rules with three questions (stage 5 of the coherence audit, 2026-11-22; a session keeps what it started with)
COMP = {"on": False}   # whether the session at hand works with competitors (set in main)
BATCH_FIRST = True   #''')

# ---- the standing of a guess in the arm "supervised": refuted by a ruling (competition), or because every hypothesis from it was ruled refuted
rep('''def tested_whys(ledger):''', '''def standing_ruling(ledger, hid):
    """The ruling that stands on a hypothesis: its last ruling by the supervisor. A second look after an objection that let the ruling stand keeps the
    first ruling's boxes; one that changed it stands with its own result and no fits (the supervisor gave none)."""
    vs = [r for r in ledger if r["type"] == "verdict" and r.get("by") == "supervisor" and r["body"].get("for") == hid]
    if not vs:
        return None
    last = vs[-1]
    if last["body"].get("after") and last["body"].get("stands"):
        obj = next((r for r in ledger if r["id"] == last["body"]["after"]), None)
        first = next((r for r in ledger if obj and r["id"] == obj["body"].get("to")), None)
        return first or last
    return last


def guess_refutations(ledger):
    """The arm "supervised": {guess: the ruling that refutes it}. A guess that does not fit the result of a test the standing ruling found fair (its
    fits, stage 5 of the coherence audit, 2026-11-22: the code applies the supervisor's boxes and does not judge); and, as before, a guess every
    hypothesis of which was ruled refuted (the latest of their rulings). A revised guess is not refuted: it was replaced."""
    out, by_h = {}, {}
    hyps = {r["id"]: r["body"].get("from_why") for r in ledger if r["type"] == "hypothesis"}
    for hid in hyps:
        v = standing_ruling(ledger, hid)
        if v is None:
            continue
        by_h[hid] = v
        b = v["body"]
        if b.get("fair") and not b.get("fits_contradicted"):
            for y, f in (b.get("fits") or {}).items():
                if f == "does not fit":
                    out.setdefault(y, v["id"])
    of = {}
    for hid, y in hyps.items():
        if y:
            of.setdefault(y, []).append(hid)
    for y, hs in of.items():
        if y not in out and all(h in by_h and by_h[h]["body"].get("result") == "refuted" for h in hs):
            out[y] = by_h[hs[-1]]["id"]
    revised = {r["body"].get("revises") for r in ledger if r["type"] == "why" and r["body"].get("revises")}
    return {y: v for y, v in out.items() if y not in revised}


def revise_family(ledger, y):
    """The guesses linked to y by revises, in either direction and through each other (y itself included)."""
    links = [(r["id"], r["body"].get("revises")) for r in ledger if r["type"] == "why" and r["body"].get("revises")]
    fam, grew = {y}, True
    while grew:
        grew = False
        for a, b in links:
            if (a in fam) != (b in fam):
                fam |= {a, b}
                grew = True
    return fam


def competitor_problem(d, ledger):
    """The arm "supervised" with competitors: what is wrong with the guess a decision rule competes with, or None (checked before any call)."""
    cw, h = d.get("competes_with"), d.get("for")
    whys = {r["id"]: r for r in ledger if r["type"] == "why"}
    if not isinstance(cw, str) or not cw.strip():
        return f"the decision rule for {h} names the guess it competes with: competes_with, the id of another guess (for example Y3), whose cause would make the rule come out otherwise"
    if cw not in whys:
        return (f"the decision rule for {h} competes with {cw}, which is not a guess in the ledger: name an existing guess, or write the competing guess first (it is "
                "reviewed like any guess) and test against it in a later turn")
    later = next((r["id"] for r in ledger if r["type"] == "why" and r["body"].get("revises") == cw), None)
    if later:
        return f"the decision rule for {h} competes with {cw}, which {later} revised: name the live guess ({later}, or another)"
    refuted = guess_refutations(ledger).get(cw)
    if refuted:
        return f"the decision rule for {h} competes with {cw}, which the ruling {refuted} refuted: name a live guess"
    own = next((r["body"].get("from_why") for r in ledger if r["type"] == "hypothesis" and r["id"] == h), None)
    if own and cw in revise_family(ledger, own):
        return (f"the decision rule for {h} competes with {cw}, which is {h}'s own guess {own}" + (" or one linked to it by revises" if cw != own else "")
                + ": a test tells its guess from ANOTHER explanation of the same result")
    if d.get("rival_predicts") not in ("held", "failed"):
        return f"the decision rule for {h} needs rival_predicts: held or failed, what the rule gives if {cw} is true and {own or 'its own guess'} is false"
    if d["rival_predicts"] == "held":
        return f"this decision rule would hold if {cw} were true too, so it cannot tell the two apart: choose simulations where the two guesses give different results"
    return None


def tested_whys(ledger):''')

# sort_out: the competing guess of a rule by the id it was to get; refutations from the one function; a declared competitor of a new guess
rep('''    if supervised:   # no rethink in this arm: a guess all of whose hypotheses the supervisor ruled refuted is refuted, and nothing more comes from it unless a new why revises it
        of = {}
        for r in ledger:
            if r["type"] == "hypothesis" and r["body"].get("from_why"):
                of.setdefault(r["body"]["from_why"], []).append(st.get(r["id"]))
        stand.update({y: "refuted" for y, v in of.items() if stand.get(y) == "verify" and v and all(x == "refuted" for x in v)})''',
    '''    if supervised:   # no rethink in this arm: a guess refuted by a ruling (every hypothesis from it ruled refuted, or, with competitors, a fair test it did not fit) gives nothing more unless a new why revises it
        refuted_by = guess_refutations(ledger)   # one function, also for the ledger text (stage 5 of the coherence audit, 2026-11-22)
        stand.update({y: "refuted" for y in refuted_by if stand.get(y) == "verify"})''')
rep('''        if w.get("revises") is not None and (w["revises"] not in ws or stand[w["revises"]] == "revised"):
            return "revises is null, or the id of an earlier why in the ledger that this one replaces with a better guess (one that has not been revised already'''
    , '''        if supervised and COMP["on"] and w.get("competes_with") is not None and (w["competes_with"] not in ws or stand.get(w["competes_with"]) in ("revised", "refuted")):
            return (f"competes_with is null, or the id of a live guess in the ledger whose result this one explains by another cause: {w['competes_with']!r} is "
                    + ("not a guess in the ledger" if w["competes_with"] not in ws else f"{stand[w['competes_with']]}")), "harness", None
        if w.get("revises") is not None and (w["revises"] not in ws or stand[w["revises"]] == "revised"):
            return "revises is null, or the id of an earlier why in the ledger that this one replaces with a better guess (one that has not been revised already''')
rep('''        if supervised and (new_since := learned_since(ledger)) is not None and not any(a in new_since for a in about):''',
    '''        rival_of = whys.get(w.get("competes_with")) if supervised and COMP["on"] and isinstance(w.get("competes_with"), str) else None   # a declared competitor may cite the records of the guess it competes with (the chain's exception)
        if supervised and (new_since := learned_since(ledger)) is not None and not any(a in new_since for a in about) and not (rival_of and set(about) & set(rival_of.get("about") or [])):''')
rep('''        if isinstance(w, dict) and isinstance(w.get("revises"), str) and w["revises"] in why_map:   # an earlier guess of this same answer, by the id it was to get
            w["revises"] = why_map[w["revises"]]''', '''        if isinstance(w, dict) and isinstance(w.get("revises"), str) and w["revises"] in why_map:   # an earlier guess of this same answer, by the id it was to get
            w["revises"] = why_map[w["revises"]]
        if isinstance(w, dict) and isinstance(w.get("competes_with"), str) and w["competes_with"] in why_map:
            w["competes_with"] = why_map[w["competes_with"]]''')
rep('''        for d in [d for d in (ex.get("decision_rules") or []) + (ex.get("needs") or []) if isinstance(d, dict)]:
            d["for"] = to_h(d.get("for"))''', '''        for d in [d for d in (ex.get("decision_rules") or []) + (ex.get("needs") or []) if isinstance(d, dict)]:
            d["for"] = to_h(d.get("for"))
        for d in [d for d in ex.get("decision_rules") or [] if isinstance(d, dict) and isinstance(d.get("competes_with"), str) and d["competes_with"] in why_map]:   # a guess of this answer, by the id it was to get
            d["competes_with"] = why_map[d["competes_with"]] or f"{d['competes_with']} (your new guess number {nth(d['competes_with'], n_why)} of this answer, not accepted)"''')

# the ledger text: a guess refuted by a ruling says so
rep('''def render(ledger, readings=True, rethinks=True):''', '''def render(ledger, readings=True, rethinks=True, supervised=False):''')
rep('''    by = {r["id"]: r for r in ledger}
    out, forms = [], reading_forms(ledger)''', '''    if supervised:   # a guess refuted by a ruling, as sort_out holds it (stage 5 of the coherence audit, 2026-11-22: it was refused with no sign in this text)
        for y, v in guess_refutations(ledger).items():
            if isinstance(st.get(y), dict) and st[y].get("worth") == "verify":
                st[y] = {**st[y], "worth": "refuted", "by": v, "idle": False}
    by = {r["id"]: r for r in ledger}
    out, forms = [], reading_forms(ledger)''')
rep('''        now = STANDING[w["worth"]] + (f" as {w['as']}" if w.get("as") else "")''', '''        now = STANDING[w["worth"]] + (f" as {w['as']}" if w.get("as") else "") + (f" by {w['by']}: no hypothesis can come from it; a new guess may revise it" if w.get("by") else "")''')
rep('''            text = render(ledger, readings=arm == "supervised", rethinks=arm == "hypotheses")''', '''            text = render(ledger, readings=arm == "supervised", rethinks=arm == "hypotheses", supervised=arm == "supervised")''')
rep('''                    text = render(ledger, readings=True, rethinks=False)''', '''                    text = render(ledger, readings=True, rethinks=False, supervised=True)''')
# the competing guess of a guess, in the ledger text; and of a rule (the experiment and the check)
rep('''        return (f"[{now}] " + (f"revises {b['revises']}: " if b.get("revises") else "")''', '''        return (f"[{now}] " + (f"revises {b['revises']}: " if b.get("revises") else "") + (f"competes with {b['competes_with']}: " if b.get("competes_with") else "")''')
rep('''                + "".join(f" | decision rule for {x['for']}: {flat(x.get('decision_rule', x.get('rule')))}" + (f" (rival: {flat(x['rival'])})" if x.get("rival") else "")''',
    '''                + "".join(f" | decision rule for {x['for']}: {flat(x.get('decision_rule', x.get('rule')))}" + (f" (rival: {flat(x['rival'])})" if x.get("rival") else "") + (f" (competes with {x['competes_with']})" if x.get("competes_with") else "")''')
rep('''        rival = "" if not b.get("rival") or b.get("rival_predicts") not in ("held", "failed") or b["result"] not in ("held", "failed") else (''',
    '''        if b.get("competes_with") and b.get("rival_predicts") in ("held", "failed") and b["result"] in ("held", "failed"):   # the competing guess (stage 5): what it predicted; whether it fits is the supervisor's ruling
            b = {**b, "rival": f"the guess {b['competes_with']}"}
        rival = "" if not b.get("rival") or b.get("rival_predicts") not in ("held", "failed") or b["result"] not in ("held", "failed") else (''')
rep('''        append(ledger, turn, "check", xid, {"for": d["for"], "experiment": xid, "decision_rule": d["decision_rule"], "rival": d.get("rival"), "rival_predicts": d.get("rival_predicts"),''',
    '''        append(ledger, turn, "check", xid, {"for": d["for"], "experiment": xid, "decision_rule": d["decision_rule"], "rival": d.get("rival"), "rival_predicts": d.get("rival_predicts"), **({"competes_with": d["competes_with"]} if d.get("competes_with") else {}),''')
p.write_text(s); print("core patched")
