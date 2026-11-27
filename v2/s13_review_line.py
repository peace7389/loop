"""After v2.1: found by the fairness audit of s065 (2026-11-27), repaired at the operator's word ("fix it").
  - a review of a test, shown as a cited record (to the supervisor, and to the researcher in a short call), read "[G16] the supervisor's review
    of H3: held. None": the line printed the field `because`, which only the review of a guess has. The review of a test keeps what it told the
    researcher in `feedback`. In s065 the researcher cited G16 for what its feedback says, and the supervisor, shown "held. None", sent the guess
    back as not in the records. The line now shows the feedback of a review of a test, and nothing after the decision when there is none
    (an approved test). The line of a review of a guess is unchanged, character for character."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
sub("harness/loop.py",
    '''review of {b.get('for') or 'a guess'}: {b.get('decision')}. {flat(b.get('because'))}" + (f" The rival it named''',
    '''review of {b.get('for') or 'a guess'}: {b.get('decision')}." + (f" {flat(b['because'])}" if b.get("because") is not None else f" {flat(b['feedback'])}" if b.get("feedback") else "") + (f" The rival it named''',
    'a cited review of a test showed "None" where its reason belongs: it shows the feedback the review gave (the audit of s065)')
done("stage13_review_line", 'after v2.1: a cited review of a test shows its feedback, not "None"')
