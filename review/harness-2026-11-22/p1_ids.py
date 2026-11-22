"""After the deploy (2026-11-23, night), found by a real call of the batched first review: the model named its test item "H1 UDP goodput rises
with its part", not "H1", and the harness, matching ids exactly, would have dropped that answer and asked the test again alone. The ids the model
must give back are now constrained to the exact values (an enum in the answer format), and read by the id they begin with as well. The same for
a decision rule's competes_with and a repair's (a pattern: a guess id). Usage: p1_ids.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a)); s = s.replace(a, b)
rep('''def batch_schema(ng, nt):
    """The answer of the batched first review: one item for each new guess (gate 0's fields) and one for each test (round 1's fields)."""''',
    '''def batch_schema(ng, nt):
    """The answer of the batched first review: one item for each new guess (gate 0's fields) and one for each test (round 1's fields). ng, nt: the
    names of the guesses (G1, G2, ...) and the hypotheses of the tests, given back exactly (an enum: a real call wrote "H1 UDP goodput rises with
    its part"); a number gives the names G1.. and H1.. (the older form)."""
    gn = ng if isinstance(ng, list) else [f"G{i + 1}" for i in range(ng)]
    tn = nt if isinstance(nt, list) else [f"H{i + 1}" for i in range(nt)]
    ng, nt = len(gn), len(tn)''')
rep('''"properties": {"guess": {"type": "string", "description": "the guess's name in this request: G1, G2, ..."}, **GS["properties"]}}''',
    '''"properties": {"guess": {"type": "string", "enum": gn or ["G1"], "description": "the guess's name in this request, exactly as its heading writes it"}, **GS["properties"]}}''')
rep('''"properties": {"for": {"type": "string", "description": "the hypothesis whose test this item reviews, as its heading names it"}, **R["properties"]}}''',
    '''"properties": {"for": {"type": "string", "enum": tn or ["H1"], "description": "the id of the hypothesis whose test this item reviews, exactly as its heading writes it"}, **R["properties"]}}''')
rep('''(model, user, batch_schema(len(guesses), len(tests)))''', '''(model, user, batch_schema([f"G{i + 1}" for i in range(len(guesses))], [hid for hid, _, _ in tests]))''')
rep('''    gs = {str(x.get("guess")): x for x in d.get("guesses") or [] if isinstance(x, dict)}
    ts = {str(x.get("for")): x for x in d.get("tests") or [] if isinstance(x, dict)}''',
    '''    lead = lambda v: (m.group(1) if (m := re.match(r"\\s*([GH]\\d+)\\b", str(v))) else str(v))   # an id with words after it is read by its id
    gs, ts = {}, {}
    for x in d.get("guesses") or []:
        if isinstance(x, dict):
            gs.setdefault(lead(x.get("guess")), x)
    for x in d.get("tests") or []:
        if isinstance(x, dict):
            ts.setdefault(lead(x.get("for")), x)''')
# a rule's and a repair's competes_with: a guess id, by the answer format
rep('''        CW = {"type": "string", "description": "the id of another live guess (for example Y3): not the hypothesis's own, nor one linked to it by revises"}''',
    '''        CW = {"type": "string", "pattern": "^Y[0-9]+$", "description": "the id of another live guess (for example Y3): not the hypothesis's own, nor one linked to it by revises"}''')
rep('''"decision_rule": {"type": "string"}, RV: {"type": "string", **({"description": "the id of an existing live guess the rule competes with (not the hypothesis's own)"} if competitors else {})},''',
    '''"decision_rule": {"type": "string"}, RV: {"type": "string", **({"pattern": "^Y[0-9]+$", "description": "the id of an existing live guess the rule competes with (not the hypothesis's own)"} if competitors else {})},''')
p.write_text(s); print("patched", p)
