"""v2, stage 8b: what the checks of the supervisor's wrong answers found (section T of harness_checks/test_stage5.py).
  - a box that fails or cannot be told with an empty reason reached the researcher as "Honest could not be told: " with nothing after it; it now
    says that the supervisor gave no reason (the operator's rule: "cannot tell" counts as a fail with a required reason; the format requires the
    field, not that it be filled);
  - a reason that was missing altogether was recorded as the word "None";
  - an answer of the supervisor that is JSON but no object (a sentence in quotes) ended the session with a Python error of the harness's own
    (AttributeError); it is now read as an answer that cannot be read is: a review's test is run unreviewed with a note, a ruling is asked for again."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
L = "harness/loop.py"
sub(L, '''    rev = {"reads": flat(d.get("reads")), **{q + "_why": flat(d.get(q + "_why")) for q in REVIEW_QS}, **{q: box(d.get(q)) for q in REVIEW_QS},''',
    '''    rev = {"reads": flat(d.get("reads")), **{q + "_why": flat(d.get(q + "_why") or "") for q in REVIEW_QS}, **{q: box(d.get(q)) for q in REVIEW_QS},''', "no text changed: a missing reason of a review's box is recorded as empty, not as the word None")
sub(L, '''    qs = {q: {"why": flat(d.get(q + "_why")), "box": box(d.get(q))} for q in RULING_QS}''', '''    qs = {q: {"why": flat(d.get(q + "_why") or ""), "box": box(d.get(q))} for q in RULING_QS}''', "no text changed: the same at a ruling")
sub(L, '''        rev["feedback"] = ("; ".join(f"{q.capitalize()} {'could not be told' if rev[q] == CANNOT else 'failed'}: {rev[q + '_why']}" for q in failed) if failed else''',
    '''        rev["feedback"] = ("; ".join(f"{q.capitalize()} {'could not be told' if rev[q] == CANNOT else 'failed'}: {rev[q + '_why'] or NO_REASON}" for q in failed) if failed else''', "what the researcher is told of a box without a reason (the review)")
sub(L, '''"; ".join(f"{q.capitalize()} {'could not be told' if qs[q]['box'] == CANNOT else 'failed'}: {flat(qs[q]['why'])}" for q in qs if qs[q]["box"] != "pass")''',
    '''"; ".join(f"{q.capitalize()} {'could not be told' if qs[q]['box'] == CANNOT else 'failed'}: {flat(qs[q]['why']) or NO_REASON}" for q in qs if qs[q]["box"] != "pass")''', "what the researcher is told of a box without a reason (the ruling's line in the ledger)")
sub(L, '''def supervise(model, user, schema, max_tokens=9000):''', '''NO_REASON = "(the supervisor gave no reason)"   # a box that failed or could not be told, with its reason left empty


def supervise(model, user, schema, max_tokens=9000):''', "the words for a box without a reason")
sub(L, '''    try:
        return json.loads(content)
    except ValueError:
        d = findings_cut(content) if "findings" in (schema.get("properties") or {}) else None''', '''    try:
        d = json.loads(content)
        if not isinstance(d, dict):
            raise ValueError("the supervisor's answer is not a JSON object")
        return d
    except ValueError:
        d = findings_cut(content) if "findings" in (schema.get("properties") or {}) else None''', "no text changed: an answer that is JSON but no object is an answer that cannot be read")
done("stage8b", "v2, stage 8b: what the checks of the supervisor's wrong answers found")
