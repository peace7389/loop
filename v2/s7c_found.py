"""v2, stage 7c: two more sentences the text audit marked in v2's own paragraph on changes of the network (every arm reads it).
  - "rate (state it, for example 1Gbps)": an example value (the rate of the brief's fast links); the form is said without a value;
  - "The kinds, each ns-3's queue disc of that name except the scheduler: codel ...": the sentence named the scheduler before the list and apart
    from the others. The list is alphabetical and each kind is described at the same length; the clause is gone."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
L, TA = "harness/loop.py", "harness/text_audit.py"
sub(L, "   - do add_link: id, from and to (the two hosts it joins) and rate (state it, for example 1Gbps).", "   - do add_link: id, from and to (the two hosts it joins) and rate (state it, written as the brief writes rates).",
    "the line on a new link: no example rate (found by the text audit)")
sub(L, '''    old, old2 = "rate (state it, for example 1Gbps)", "A new link has a one-way delay of 50us,"''', '''    old, old2 = "rate (state it, written as the brief writes rates)", "A new link has a one-way delay of 50us,"''',
    "no text changed: the same line, where a brief caps a new link (its cap replaces the words as before)")
sub(L, "The kinds, each ns-3's queue disc of that name except the scheduler: codel:", "The kinds: codel:", "the kinds of queue: no kind named before the list or apart from it (found by the text audit)")
sub(TA, '''m = re.search(r"The kinds,[^:]*:(.*?)(?:\\n|$)", text)''', '''m = re.search(r"The kinds[^:]*:(.*?)(?:\\n|$)", text)''', "no text changed: the text audit reads the list in its new form")
done("stage7c", "v2, stage 7c: two more sentences the text audit marked in v2's own texts")
