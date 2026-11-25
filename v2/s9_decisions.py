"""v2, stage 9: the operator's decisions of 2026-11-25 on the three questions the report left ("Do as you recommend").
  1. three-hosts-moves stays as built (a new link at most 90 Mbit/s, 20 simulations, the condition not met at the defaults): it differs from
     three-hosts-2 in one thing, that the network may change.
  2. a brief after_fix-2: after_fix with its TCP types in alphabetical order and its TCP flow locked (it could be replaced by a TCP flow at a
     constant rate). after_fix and after_fix2 stay as their sessions read them.
  3. a review of the supervisor that cannot be read is asked for once more; unreadable again, it counts as "cannot tell" in every box: the test is
     sent back, as a box that could not be told sends it back. Until now the test ran unreviewed: it then had no answer to Follows, and its guess
     could be refuted through it, which the rule of item 4 forbids. (A session without competitors has no boxes and runs such a test as before.)"""
import sys, json; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done, ROOT, LOG
L = "harness/loop.py"
sub(L, '''def _review3(model, d, user, hid, rules, round_no, ask_fn, pre, pre_saw):''', '''UNREAD_REVIEW = "the supervisor's review of this test could not be read"   # v2: the reason of every box of a review that could not be read twice


def review_or_cannot(note, model, brief, ledger, ex, hid, **k):
    """review_design, and what happens when its answer cannot be read (v2, the operator's decision of 2026-11-25): it is asked for once more, alone;
    unreadable again, the review counts as "cannot tell" in every box, so the test is sent back as any box that could not be told sends it back
    (a test that ran unreviewed had no answer to Follows, and its guess could be refuted through it). note(text) writes the ledger's note. A session
    without competitors has no boxes: the error is raised again, and its test is run unreviewed as before."""
    try:
        return review_design(model, brief, ledger, ex, hid, **k)
    except (ValueError, KeyError, TypeError) as e:
        if not COMP["on"]:
            raise
        note(f"the supervisor's review of the test of {hid} could not be read ({type(e).__name__}): it is asked for once more")
    again = {**k, "pre": None, "pre_saw": None}
    try:
        return review_design(model, brief, ledger, ex, hid, **again)
    except (ValueError, KeyError, TypeError) as e:
        note(f"the supervisor's review of the test of {hid} could not be read a second time ({type(e).__name__}): it counts as \\"cannot tell\\" in every box, and the test is sent back")
    d = {"reads": "", **{q + "_why": UNREAD_REVIEW for q in REVIEW_QS}, **{q: CANNOT for q in REVIEW_QS}, "if_tested": "cannot tell", "if_competitor": "cannot tell", "missing": "",
         "feedback": UNREAD_REVIEW + ", twice, so no box could be told. Send the test again, as it is or changed."}
    rev, saw = review_design(model, brief, ledger, ex, hid, **{**again, "pre": d, "pre_saw": ""})
    rev["unread"] = True
    return rev, saw


def _review3(model, d, user, hid, rules, round_no, ask_fn, pre, pre_saw):''', "a review that cannot be read: asked once more, then cannot tell in every box (the note and the feedback the researcher reads)")
sub(L, '''                rev, saw = review_design(model, brief, ledger, ex, hid, pre=pre[0] if pre else None, pre_saw=pre[1] if pre else None)''',
    '''                rev, saw = review_or_cannot(lambda text, hid=hid: append(ledger, turn, "note", hid, {"text": text}), model, brief, ledger, ex, hid, pre=pre[0] if pre else None, pre_saw=pre[1] if pre else None)''',
    "no text changed: the first round of a review goes through it")
sub(L, '''                rev, saw = review_design(model, brief, ledger, t2, hid, round_no=n, earlier=earlier)''',
    '''                rev, saw = review_or_cannot(lambda text, rid=rid: append(ledger, turn, "note", rid, {"text": text}), model, brief, ledger, t2, hid, round_no=n, earlier=earlier)''',
    "no text changed: so does the review of a repaired test")
F = "harness/session_figures.py"
sub(F, '''    return {"chain_refusals": chain, "cannot_tell": comp.get("cannot_tell"), "approved_by_round": {str(k): by_round[k] for k in sorted(by_round)},''',
    '''    return {"chain_refusals": chain, "cannot_tell": comp.get("cannot_tell"), "unread_reviews": sum(1 for r in rv if r["body"].get("unread")),
            "approved_by_round": {str(k): by_round[k] for k in sorted(by_round)},''', "no text changed: the fairness figures count the reviews that could not be read (each also counts as four boxes that could not be told)")
sub(F, '''      "cannot_tell": boxes answered "cannot tell" at the reviews of every round and at the rulings (None: a session before v2);''',
    '''      "cannot_tell": boxes answered "cannot tell" at the reviews of every round and at the rulings (None: a session before v2);
      "unread_reviews": reviews that could not be read twice and so count as "cannot tell" in every box (they are among the boxes above);''', "no text changed: its description")
# the brief after_fix-2
b = json.loads((ROOT / "briefs/after_fix.json").read_text())
b["id"] = "after_fix-2"
old_ch, old_lock = list(b["knobs"]["tcp.type"]["choices"]), list(b["structure"]["locked"])
b["knobs"]["tcp.type"]["choices"] = sorted(old_ch)
b["structure"]["locked"] = old_lock + ["flow:tcp"]
(ROOT / "briefs/after_fix-2.json").write_text(json.dumps(b, indent=1) + "\n")
LOG.append(("briefs/after_fix-2.json", "a new brief: after_fix with the choices of tcp.type in alphabetical order", json.dumps(old_ch), json.dumps(b["knobs"]["tcp.type"]["choices"])))
LOG.append(("briefs/after_fix-2.json", "and its TCP flow locked (what may not be removed or replaced)", json.dumps(old_lock), json.dumps(b["structure"]["locked"])))
done("stage9", "v2, stage 9: the operator's decisions of 2026-11-25")
