"""Stage 5, part 3b: gate 0 in a session with competitors. A declared competitor (competes_with: Yn) is shown with the guess it competes with; there
"repeats" means the same cause as Yn, and the chain's question (not_from_what_was_learned) is not asked of it (a reading that names it is taken as
none). A guess that something makes no difference must name its cause (no_cause). Usage: s5_ground.py HARNESS_DIR"""
import sys
from pathlib import Path
H = Path(sys.argv[1])
p = H / "loop.py"; s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:110], s.count(a)); s = s.replace(a, b)
rep('''    the_guess = (f"''', '''    G = GROUNDS_COMP if COMP["on"] else GROUNDS
    rival_w = next((r["body"] for r in ledger if r["type"] == "why" and r["id"] == why.get("competes_with")), None) if COMP["on"] and why.get("competes_with") else None
    the_guess = (f"''')
s_i = s.index('    the_guess = (f"')
s_j = s.index('\n', s.index('    ask = (', s_i))
seg = s[s_i:s_j]
assert 'What would make it so, not directly visible' in seg
s = s[:s_i] + seg.replace('    ask = (', '''    if rival_w:   # a declared competitor (stage 5)
        the_guess += (f"It competes with {why['competes_with']}, whose guess is: {' '.join(str(rival_w.get('guess')).split())} (about {', '.join(rival_w.get('about') or [])}). It explains the same result by another "
                      f"cause and may cite {why['competes_with']}'s records: here the defect repeats means that it names the same cause as {why['competes_with']}, and the question whether it comes from "
                      "what was learned since is not asked of it.\\n")
    ask = (''', 1) + s[s_j:]
rep('''            "The defects: " + "; ".join(f"{k}: {v}" for k, v in GROUNDS.items()) + ". A guess may be wrong and still be sound here''',
    '''            "The defects: " + "; ".join(f"{k}: {v}" for k, v in G.items()) + ". A guess may be wrong and still be sound here''')
rep('''    d = pre if pre is not None else (ask_fn or supervise)(model, user, GROUND_SCHEMA)   # pre: its answer in the batched first review''',
    '''    d = pre if pre is not None else (ask_fn or supervise)(model, user, GROUND_SCHEMA_COMP if COMP["on"] else GROUND_SCHEMA)   # pre: its answer in the batched first review''')
rep('''"defect": d["defect"] if d["defect"] in GROUNDS else "none", "because": flat(d["because"])}, user''',
    '''"defect": d["defect"] if d["defect"] in G and not (rival_w and d["defect"] == "not_from_what_was_learned") else "none", "because": flat(d["because"])}, user''')
rep('''    g_item = {"type": "object", "additionalProperties": False, "required": ["guess"] + GROUND_SCHEMA["required"],
              "properties": {"guess": {"type": "string", "description": "the guess's name in this request: G1, G2, ..."}, **GROUND_SCHEMA["properties"]}}''',
    '''    GS = GROUND_SCHEMA_COMP if COMP["on"] else GROUND_SCHEMA
    g_item = {"type": "object", "additionalProperties": False, "required": ["guess"] + GS["required"],
              "properties": {"guess": {"type": "string", "description": "the guess's name in this request: G1, G2, ..."}, **GS["properties"]}}''')
# the record of a guess's reading names the defect in the words of the session's list
rep('''        return (f"by the supervisor of a guess it did not accept (“{flat(b.get('guess'))[:200]}”" + (f", about the result “{flat(b['result'])[:200]}”" if b.get("result") else "") + f"): {GROUNDS.get(b['defect'], b['defect'])}.''',
    '''        return (f"by the supervisor of a guess it did not accept (“{flat(b.get('guess'))[:200]}”" + (f", about the result “{flat(b['result'])[:200]}”" if b.get("result") else "") + f"): {GROUNDS_COMP.get(b['defect'], b['defect'])}.''')
p.write_text(s); print("ground patched")
