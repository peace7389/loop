"""Stage 1, item 1 (the coherence audit, 2026-11-22): ids by position. The researcher names a new guess or hypothesis of its answer by the id it will
get (the instructions say so), but only accepted parts got ids, so one refusal shifted every later id of that answer: hypotheses were recorded under
another guess (s050 t4, s051 t4 and t8, s041 t2, s044 t2, s046 t3) and rules landed on another hypothesis (s050 t4). Now each new guess and
hypothesis keeps the id of its position for the references of its own answer: a reference is mapped to the id the part was recorded with, and a
reference to a part that was not accepted is refused with that reason. Usage: s1_ids.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)
# (a) the guesses: the id of each position, and the id it was recorded with (None: not accepted)
rep('''        return w2

    for w in t.get("whys") or []:
        if isinstance(w, dict) and isinstance(w.get("about"), list):''', '''        return w2

    why_map, h_map = {}, {}   # an id by position in this answer -> the id it was recorded with, or None (not accepted): the coherence audit, 2026-11-22
    for k_w, w in enumerate(t.get("whys") or []):
        pid = f"Y{n_why + k_w + 1}"
        why_map[pid] = None
        if isinstance(w, dict) and isinstance(w.get("revises"), str) and w["revises"] in why_map:   # an earlier guess of this same answer, by the id it was to get
            w["revises"] = why_map[w["revises"]]
        if isinstance(w, dict) and isinstance(w.get("about"), list):''')
rep('''        new = f"Y{n_why + len(ok['whys'])}"   # the id it is about to get
''', '''        new = f"Y{n_why + len(ok['whys'])}"   # the id it is about to get
        why_map[pid] = new
''')
# (b) the hypotheses: from_why mapped; a hypothesis of a guess that was not accepted is refused, saying so; each position's id
rep('''    for h in t.get("hypotheses") or []:
        if isinstance(h, dict) and isinstance(h.get("follows_from"), list):   # a run id stands for that run's simulation, as in a why's about (s043: three hypotheses refused for "r001")''',
'''    nth = lambda pid, base: int(pid[1:]) - base   # the position of a part of this answer, from the id it was to get
    for k_h, h in enumerate(t.get("hypotheses") or []):
        pid_h = f"H{known + k_h + 1}"
        h_map[pid_h] = None
        gone_why = isinstance(h, dict) and isinstance(h.get("from_why"), str) and h["from_why"] in why_map and why_map[h["from_why"]] is None
        if isinstance(h, dict) and isinstance(h.get("from_why"), str) and why_map.get(h["from_why"]):
            h["from_why"] = why_map[h["from_why"]]   # the guess of this answer it names, by the id that guess was recorded with
        if isinstance(h, dict) and isinstance(h.get("follows_from"), list):   # a run id stands for that run's simulation, as in a why's about (s043: three hypotheses refused for "r001")''')
rep('''        if mode == "report":
            no.append(("new hypothesis", only))
        elif supervised and (waiting :=''', '''        if gone_why:
            no.append(("new hypothesis", f"it comes from {h['from_why']}, your new guess number {nth(h['from_why'], n_why)} of this answer, which was not accepted (its note says why): "
                                         "no hypothesis can come from it in this answer"))
        elif mode == "report":
            no.append(("new hypothesis", only))
        elif supervised and (waiting :=''')
rep('''                    hid = f"H{known + len(ok['hypotheses']) + 1}"   # the id it is about to get: its test's rule in this answer stands for a prediction the short format does not ask''',
    '''                    hid = pid_h   # the id the researcher gave it by its position: its test's rule in this answer names it so (a prediction the short format does not ask)''')
rep('''            ok["hypotheses"].append(h)
            st[f"H{known + len(ok['hypotheses'])}"] = "open"  # the id it is about to get
    ex = t.get("experiment")''', '''            ok["hypotheses"].append(h)
            st[f"H{known + len(ok['hypotheses'])}"] = "open"  # the id it is about to get
            h_map[pid_h] = f"H{known + len(ok['hypotheses'])}"
    ex = t.get("experiment")
    # (c) the experiment of this answer names its hypotheses by the ids they were to get: mapped to the recorded ones; one that was not accepted is named as such
    gone_h = lambda x: f"{x} (your new hypothesis number {nth(x, known)} of this answer, not accepted)"
    to_h = lambda x: (h_map[x] or gone_h(x)) if isinstance(x, str) and x in h_map else x
    if isinstance(ex, dict):
        if isinstance(ex.get("tests"), list):
            ex["tests"] = [to_h(x) for x in ex["tests"]]
        for d in [d for d in (ex.get("decision_rules") or []) + (ex.get("needs") or []) if isinstance(d, dict)]:
            d["for"] = to_h(d.get("for"))
    t["_ids"] = {**why_map, **h_map}   # for the decisions on findings of this answer (remap_refs)''')
# (d) the decisions on findings name parts of this answer by position too
rep('''def findings_fill(t):''', '''def remap_refs(t):
    """The refs of an answer's decisions on findings, mapped from the ids of its new guesses and hypotheses by position to the ids they were recorded
    with (sort_out leaves the map in t["_ids"]); a ref to a part that was not accepted stays as written, and settle_findings leaves it out with a note."""
    ids = t.get("_ids") or {}
    for d in t.get("decisions") or []:
        if isinstance(d, dict) and isinstance(d.get("refs"), list):
            d["refs"] = [ids.get(r) or r if isinstance(r, str) else r for r in d["refs"]]
    return t


def findings_fill(t):''')
rep('''                settle_findings(parsed, ledger, turn, due_before, [r["id"] for r in ledger if r["turn"] == turn and r["type"] == "result"], [])''',
    '''                settle_findings(remap_refs(parsed), ledger, turn, due_before, [r["id"] for r in ledger if r["turn"] == turn and r["type"] == "result"], [])''')
# (e) the automatic "work" decision: the guesses of THIS reply, by the ids append gave them (a continued turn has earlier replies' guesses too)
rep('''            for w in ok["whys"]:
                last = append(ledger, turn, "why", last,''', '''            made_whys = []   # the ids of this reply's guesses (the coherence audit: a continued turn paired them with the turn's first ones)
            for w in ok["whys"]:
                last = append(ledger, turn, "why", last,''')
rep('''                if w.get("ground"):   # the supervisor's reading of the records this guess cites''', '''                made_whys.append(last)
                if w.get("ground"):   # the supervisor's reading of the records this guess cites''')
rep('''            whys_made = [(r["id"], w.get("_findings") or []) for r, w in zip([r for r in ledger if r["turn"] == turn and r["type"] == "why"], ok["whys"])]
            settle_findings(parsed, ledger, turn, due_before, made, [x for x in whys_made if x[1]])''', '''            whys_made = [(rid, w.get("_findings") or []) for rid, w in zip(made_whys, ok["whys"])]
            settle_findings(remap_refs(parsed), ledger, turn, due_before, made, [x for x in whys_made if x[1]])''')
p.write_text(s); print("patched", p)
