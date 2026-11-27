"""After v2.2.1 (2026-11-27): a fault of stage 16, found by me while reading the code for another change. The ruling's request with the three
questions is made by replacing the single-question paragraph of the older ruling, from "What does this test show about the hypothesis?" up to
"THE FINDINGS SO FAR". Stage 16 took the findings out of the ruling's request, the end mark was no longer found, and the replacement was not made:
from the deploy of 17:27 the request carried the older paragraph (supported / refuted / inconclusive by one question, and its list of defects)
instead of the paragraph of the three questions. The answer's fields still asked the three questions, each with its text, so every ruling of
s067 has its three boxes; what was missing in the request is the paragraph that says them together and how the two guesses are judged.
Now the paragraph is replaced up to the end mark, or to the end of the request where there is none."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
sub("harness/loop.py",
    '''    i, j = user.find("What does this test show about the hypothesis?"), user.find("\\n\\nTHE FINDINGS SO FAR:")
    if 0 <= i < j:   # the single-question paragraph and its defects give way to the three questions
        user = user[:i] + RULING3_ASK + user[j:]''',
    '''    i, j = user.find("What does this test show about the hypothesis?"), user.find("\\n\\nTHE FINDINGS SO FAR:")
    if j < 0:   # since stage 16 the ruling's request has no findings: the paragraph runs to the end (2026-11-27: it was left in place, and the three questions' paragraph left out)
        j = len(user)
    if 0 <= i < j:   # the single-question paragraph and its defects give way to the three questions
        user = user[:i] + RULING3_ASK + user[j:]''',
    "the ruling's request carries the paragraph of the three questions again (stage 16 had left the older single-question paragraph in its place)")
done("stage18_ruling_ask", "after v2.2.1: the ruling's request carries the paragraph of the three questions again")
