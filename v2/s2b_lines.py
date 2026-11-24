"""v2, stage 2b: the lines the researcher reads about a ruling say what the new boxes mean.   python3 v2/s2b_lines.py"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
L = "harness/loop.py"
sub(L, '''("" if b.get("fair") else " Not a fair test: " + "; ".join(f"{q.capitalize()} failed: {flat(qs[q]['why'])}" for q in qs if qs[q]["box"] == "fail") + ".")''',
    '''("" if b.get("fair") else " Not a fair test: " + "; ".join(f"{q.capitalize()} {'could not be told' if qs[q]['box'] == CANNOT else 'failed'}: {flat(qs[q]['why'])}" for q in qs if qs[q]["box"] != "pass") + ".")''', "B12: a ruling's line names a question that could not be told")
sub(L, '''("." if b.get("fair") and not b.get("fits_contradicted") else " (not applied: " + ("its boxes contradicted each other" if b.get("fits_contradicted") else "the test was not fair") + ").") if b.get("fits") else "")''',
    '''("." if b.get("fair") and not b.get("fits_contradicted") else " (not applied: " + ("its boxes contradicted each other" if b.get("fits_contradicted") else "the test was not fair") + ").") if b.get("fits") else "")
                + (" The review had not found that the hypothesis follows from its guess: this ruling is about the hypothesis, and the guess is not refuted by it." if b.get("follows") not in (None, "pass") and b.get("result") == "refuted" else "")''', "item 4: a ruling's line says when it refutes the hypothesis and not the guess")
sub(L, '''a guess that does not fit the result of a fair test is refuted: no hypothesis comes from it, a new guess may revise it.''',
    '''a guess is refuted when a fair test of a hypothesis that follows from it fails, or when the supervisor finds that it does not fit a fair test's result: no new hypothesis comes from it, a new guess may revise it. A failed hypothesis that did not follow from its guess refutes only itself.''', "item 4: what the researcher is told about when a guess is refuted")
done("stage2b", "v2, stage 2b: the lines about a ruling")
