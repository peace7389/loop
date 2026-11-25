"""After v2.1 (the operator's sheet of 2026-11-25, evening): Follows in two parts, with a record of which part failed; and a crash found in s064.
  Follows   (1) strict: the hypothesis is about a measure the guess speaks about, in the direction the guess requires; fail if not.
            (2) the number is the researcher's choice: fail only if it lies clearly outside what the guess could give, and say why.
            The review's answer has a field for the part that failed, and the review's record keeps it (follows_part).
  Honest    is as the sheet asks since the wording deployed at 18:46 (fail only if every value the rule compares already stands in the records;
            the same in the question asked after the run): not changed here.
  s064      ended in turn 1 with "harness error: KeyError: 'no_cause'": the supervisor refused a guess for saying that something makes no
            difference without naming a cause, and the refusal looked that reason up in the list of a session without competing guesses, which
            has no such reason (since 2026-11-23; no session had met it). The sentence is the one the supervisor's own list has; no text is new."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
L = "harness/loop.py"
sub(L, '''return (f"the supervisor does not accept this guess as it stands: {GROUNDS[g['defect']]}. The records show:''',
    '''return (f"the supervisor does not accept this guess as it stands: {GROUNDS_COMP.get(g['defect']) or g['defect']}. The records show:''',
    "no text changed: the refusal of a guess finds the sentence of every reason the supervisor can give (s064 stopped on no_cause)")
sub(L, '''QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? Pass if someone who held the guess to be true would expect this result, in its direction and rough size; a threshold the hypothesis states follows if the guess expects the result beyond it. Fail if the guess leaves the direction open, or would expect otherwise",''',
    '''QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? It has two parts. First, strictly: the hypothesis is about a measure the guess speaks about, and in the direction the guess requires; if not, fail. Second, the number: a threshold or a size the hypothesis states is the researcher's choice; fail for it only if it lies clearly outside what the guess could give, and say why",''',
    "Follows, as the review asks it: two parts")
sub(L, '''    "follows_why": {"type": "string", "description": "one sentence: would someone who held the tested guess to be true expect this result, in its direction and rough size (a stated threshold: beyond it), and why (or what is missing to tell)"},
    "follows": {**BOX, "description": "pass: the hypothesis follows from the guess; fail: the guess leaves it open or would expect otherwise; cannot tell: the sentence says what is missing"},''',
    '''    "follows_why": {"type": "string", "description": "one sentence: is the hypothesis about a measure the guess speaks about, in the direction the guess requires; and, if it states a number, does that number lie clearly outside what the guess could give (then say why)? Or what is missing to tell"},
    "follows": {**BOX, "description": "pass: both parts hold; fail: one of them does not; cannot tell: the sentence says what is missing"},
    "follows_part": {"type": "string", "enum": ["none"] + list(FOLLOWS_PARTS), "description": "the part of Follows that did not hold: measure or direction (the hypothesis is not about a measure the guess speaks about, or not in the direction the guess requires), or number (its number lies clearly outside what the guess could give); none when Follows passes or cannot be told"},''',
    "Follows, the fields of the review's answer: the sentence, the box, and the part that failed")
sub(L, '''REVIEW3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reads", "follows_why", "follows", "honest_why",''',
    '''FOLLOWS_PARTS = ("measure or direction", "number")   # the two parts of Follows; a review's record keeps which one failed (follows_part)
REVIEW3_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reads", "follows_why", "follows", "follows_part", "honest_why",''',
    "no text changed: the part that failed is a required field of the review's answer")
sub(L, '''           "competes_with": next((x.get("competes_with") for x in rules if x.get("competes_with")), None), "defect": "none"}
    def clash_of(r):   # what contradicts what, or None''',
    '''           "competes_with": next((x.get("competes_with") for x in rules if x.get("competes_with")), None), "defect": "none"}
    if rev["follows"] == "fail":   # which of the two parts of Follows failed, as the supervisor said it (the operator, 2026-11-25: "Record which part failed")
        rev["follows_part"] = d.get("follows_part") if d.get("follows_part") in FOLLOWS_PARTS else "not said"
    def clash_of(r):   # what contradicts what, or None''',
    "no text changed: the review's record keeps the part of Follows that failed")
done("stage12_follows", "After v2.1: Follows in two parts with its record; the crash of s064")
