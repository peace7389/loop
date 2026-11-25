"""v2.1: two questions of the supervisor's review, reworded at the operator's word after the first session of v2 (s063, 2026-11-25).
  Honest   "Pass only if no value its rule compares ... already stands in the records" failed every test that compares a new run with an earlier
           one (s063, H8). Now it fails only if every value the rule compares already stands there.
  Follows  "would have to expect what the hypothesis says" failed any hypothesis with a number or a hedged guess (10 of the 15 reviews of s063; 5
           of its 10 hypotheses never ran). Now: someone who held the guess would expect this result, in direction and rough size; a stated threshold
           follows if the guess expects the result beyond it.
The same words are used wherever the question is asked: the review (alone and in the batched first review), the field of the answer, the ruling's
question on Honest with the result in hand, and the supervisor's instructions on a test that runs no new simulation."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
L = "harness/loop.py"
sub(L, '''QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? Pass only if someone who held the guess to be true would have to expect what the hypothesis says; fail if the guess leaves it open, or would expect otherwise",''',
    '''QUESTIONS = {"follows": "does the hypothesis follow from the tested guess? Pass if someone who held the guess to be true would expect this result, in its direction and rough size; a threshold the hypothesis states follows if the guess expects the result beyond it. Fail if the guess leaves the direction open, or would expect otherwise",''',
    "Follows, as the review asks it (v2.1)")
sub(L, '''             "honest": "can the test fail? Pass only if no value its rule compares, and no series such a value is computed from, already stands in the records you are shown, and its threshold is not one that almost any result passes; otherwise fail",''',
    '''             "honest": "can the test fail? Fail only if every value its rule compares already stands in the records you are shown (or is computed from a series that stands there), or if its threshold is one that almost any result passes; a rule that compares a new result with one already measured can fail. Otherwise pass",''',
    "Honest, as the review asks it (v2.1)")
sub(L, '''QUESTIONS_AFTER = {"honest": "could the test have failed? Pass only if, before it ran, no value its rule compares stood in the records, and its threshold is not one that almost any result passes; otherwise fail",''',
    '''QUESTIONS_AFTER = {"honest": "could the test have failed? Fail only if, before it ran, every value its rule compares stood in the records, or if its threshold is one that almost any result passes; otherwise pass",''',
    "Honest, as the ruling asks it with the result in hand (v2.1)")
sub(L, '''    "follows_why": {"type": "string", "description": "one sentence: would someone who held the tested guess to be true have to expect what the hypothesis says, and why (or what is missing to tell)"},''',
    '''    "follows_why": {"type": "string", "description": "one sentence: would someone who held the tested guess to be true expect this result, in its direction and rough size (a stated threshold: beyond it), and why (or what is missing to tell)"},''',
    "Follows, the field of the review's answer (v2.1)")
sub(L, '''    "honest_why": {"type": "string", "description": "one sentence, with record ids: can the test fail? (no value its rule compares, and no series it is computed from, already in the records shown; a threshold that not almost any result passes)"},''',
    '''    "honest_why": {"type": "string", "description": "one sentence, with record ids: can the test fail? (it cannot only if every value its rule compares, or the series each is computed from, is already in the records shown, or if its threshold is one almost any result passes)"},''',
    "Honest, the field of the review's answer (v2.1)")
sub(L, '''That costs nothing and is a proper test as long as the value its rule compares, and the series it is computed from, are not already "
              "in the records you are shown.''', '''That costs nothing and is a proper test as long as not every value its rule compares, with the series it is computed from, is already "
              "in the records you are shown.''', "the supervisor's instructions on a test that runs no new simulation (v2.1)")
done("stage11_v21", "v2.1: Honest and Follows reworded (the operator, after s063)")
