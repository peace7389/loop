"""Stage 4 of the coherence audit (2026-11-22), "Fixes from s052 and s053" items 3: the supervisor's feedback names one problem, with the record ids
and numbers it rests on, and what a repaired test must achieve (s052 H4: "make it show the mechanism" led to a rule of twelve comparisons); a decision
rule of the arm "supervised" makes at most COMPARISONS_MOST comparisons (the operator: the supervised arm only), stated in its instructions and the
repair prompt, refused per test with the reason before any call, and checked against the constant at the start. Usage: s4_feedback.py WT_DIR"""
import sys
from pathlib import Path
W = Path(sys.argv[1])
def rep(f, a, b, n=1):
    p = W / "harness" / f; s = p.read_text(); assert s.count(a) == n, (f, a[:100], s.count(a)); p.write_text(s.replace(a, b))
rep("decision_rules.py", '''def parse(text, measures, labels):''', '''def comparisons_in(text):
    """How many comparisons a decision rule makes (its < <= > >= ==), from its words alone; 0 when it cannot be read (the reading refuses it then)."""
    try:
        return sum(1 for t in _tokens(text) if t[0] == "op" and t[1] in COMPARE)
    except DecisionRuleError:
        return 0

def parse(text, measures, labels):''')
rep("loop.py", '''REVIEW_ROUNDS = 3        #''', '''COMPARISONS_MOST = 3   # the arm "supervised": the most comparisons in one decision rule (the operator, 2026-11-22, after s052 H4's rule of twelve); stated in LEAN_PROMPT and the repair prompt
REVIEW_ROUNDS = 3        #''')
rep("loop.py", '''def rival_problem(r):''', '''def rule_size_problem(r):
    """The arm "supervised": what is wrong with the size of one decision rule, or None (at most COMPARISONS_MOST comparisons)."""
    k = decision_rules.comparisons_in(r.get("decision_rule"))
    return (f"the decision rule for {r.get('for')} makes {k} comparisons, and a rule makes at most {COMPARISONS_MOST}: a rule that needs more asks more than one "
            "question. Decide the hypothesis by the one comparison its guess predicts, and leave the rest to a later test") if k > COMPARISONS_MOST else None


def rival_problem(r):''')
rep("loop.py", '''        for d in ex.get("decision_rules") or []:
            why = rival_problem(d)
            if why and d.get("for") not in bad:''', '''        for d in ex.get("decision_rules") or []:
            why = rival_problem(d) or rule_size_problem(d)
            if why and d.get("for") not in bad:''')
rep("loop.py", '''        why = rival_problem(rule)
        if why:
            return t2, why
        try:   # in the order of the normal path''', '''        why = rival_problem(rule) or rule_size_problem(rule)
        if why:
            return t2, why
        try:   # in the order of the normal path''')
rep("loop.py", '''exactly one of < <= > >= == in each comparison; comparisons joined by AND and OR. The harness checks it from the measured values''',
    '''exactly one of < <= > >= == in each comparison; at most 3 comparisons, joined by AND and OR. The harness checks it from the measured values''')
rep("loop.py", '''                "min(), max(); one of < <= > >= == in each comparison; comparisons joined by AND and OR). rival:''',
    '''                f"min(), max(); one of < <= > >= == in each comparison; at most {COMPARISONS_MOST} comparisons, joined by AND and OR). rival:''')
rep("loop.py", '''    want = [("a label's length", r"at most (\\d+) characters", LABEL_MOST)] + ([("the requests of one reply", r"at most (\\d+) in one reply", REQUESTS_MOST)] if arm != "supervised" else [])''',
    '''    want = [("a label's length", r"at most (\\d+) characters", LABEL_MOST)] + ([("the requests of one reply", r"at most (\\d+) in one reply", REQUESTS_MOST)] if arm != "supervised" else
                                                                                [("a decision rule's comparisons", r"at most (\\d+) comparisons", COMPARISONS_MOST)])''')
# the feedback: one problem
rep("loop.py", '''    "feedback": {"type": "string", "description": "for the researcher: what is wrong with the test (empty when there is nothing), and a stronger rival if there is one. Never a decision rule, a measure@label or simulations: the researcher finds the repair"}}}''',
    '''    "feedback": {"type": "string", "description": "for the researcher: the one problem that matters most (empty when there is none; a clearly stronger rival is that problem), the record ids and numbers it rests on, and what a repaired test must achieve. Never a decision rule, a measure@label, simulations or a network change: the researcher finds the repair"}}}''')
rep("loop.py", '''"reason to the decision, and name the defect, or none. Last, feedback for the researcher: what is wrong with the test, and a stronger rival if there is one. The feedback never "
            "contains a decision rule, a measure@label or simulations: the researcher must find the repair itself. The defects: "''',
    '''"reason to the decision, and name the defect, or none. Last, feedback for the researcher: the one problem that matters most (a clearly stronger rival is that problem), "
            "the record ids and numbers it rests on, and what a repaired test must achieve. The feedback never contains a decision rule, a measure@label, simulations or a network "
            "change: the researcher must find the repair itself. The defects: "''')
print("patched")
