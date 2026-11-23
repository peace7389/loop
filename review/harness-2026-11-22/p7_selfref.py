"""After the deploy, part 7 (s056, 2026-11-23 03:50): the batched first review lists the researcher's guesses so far, and since part 2 that list holds
the reply's own new guesses (a test may compete with one of them), under the ids they will get; the new guesses themselves are shown as G1, G2, ...
without those ids. The supervisor then named a new guess as its own nearest earlier guess (s056: in turns 1, 8, 9 and 10, eleven of the
twenty-three guesses read in a batch; none in s055, before part 2); in turn 10 it judged both new guesses repeats of themselves (Y25 contested, the other sent back and restated). Now:
1. the list marks each of the reply's new guesses as new, with its name in the request (G1, G2, ...);
2. the request says which id each new guess has and that its nearest earlier guess is one from before this reply, never itself;
3. a batched reading that still names the guess itself is not taken: a note, and that guess is read alone (as without the batch).
python3 -I p7_selfref.py LOOP_PY"""
import sys
from pathlib import Path
f = Path(sys.argv[1])
s = f.read_text()

def rep(a, b):
    global s
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)

# 1. guesses_text marks the reply's new guesses
rep('''def guesses_text(ledger):
    """Every guess of the researcher with its standing, for the supervisor's review of a test with competitors (it judges whether a competing cause is
    missing: s055, 2026-11-23, it held a test for a cause one of the guesses stated)."""
    flat = lambda v: " ".join(str(v).split())
    refuted, ws = guess_refutations(ledger), why_states(ledger)
    lines = [f"  [{r['id']}] " + (f"(refuted by {refuted[r['id']]}) " if r["id"] in refuted else f"(revised as {ws[r['id']]['as']}) " if (ws.get(r["id"]) or {}).get("as") else "")''',
    '''def guesses_text(ledger, new=None):
    """Every guess of the researcher with its standing, for the supervisor's review of a test with competitors (it judges whether a competing cause is
    missing: s055, 2026-11-23, it held a test for a cause one of the guesses stated). new: {id: its name in the batched first review} for the reply's
    own new guesses, marked as new (s056, 2026-11-23: unmarked, the supervisor named a new guess as its own nearest earlier guess)."""
    flat = lambda v: " ".join(str(v).split())
    refuted, ws, new = guess_refutations(ledger), why_states(ledger), new or {}
    lines = [f"  [{r['id']}] " + (f"(new in this reply: {new[r['id']]} below) " if r["id"] in new else "")
             + (f"(refuted by {refuted[r['id']]}) " if r["id"] in refuted else f"(revised as {ws[r['id']]['as']}) " if (ws.get(r["id"]) or {}).get("as") else "")''')

# 2. first_review takes the map and says it
rep('''def first_review(model, brief, ledger, guesses, tests, ask_fn=None, tledger=None):''',
    '''def first_review(model, brief, ledger, guesses, tests, ask_fn=None, tledger=None, new=None):''')
rep('''            + (guesses_text(tledger or ledger) if COMP["on"] and tests else "")
            + f"THIS REQUEST HOLDS EVERY NEW GUESS AND EVERY NEW TEST OF THE RESEARCHER'S REPLY IN THIS TURN ({len(guesses)} guess{'es' if len(guesses) != 1 else ''}, {len(tests)} test{'s' if len(tests) != 1 else ''}). "
              "Judge each on its own, as if it were asked alone, and answer each in its own item.\\n\\n"''',
    '''            + (guesses_text(tledger or ledger, new) if COMP["on"] and tests else "")
            + f"THIS REQUEST HOLDS EVERY NEW GUESS AND EVERY NEW TEST OF THE RESEARCHER'S REPLY IN THIS TURN ({len(guesses)} guess{'es' if len(guesses) != 1 else ''}, {len(tests)} test{'s' if len(tests) != 1 else ''}). "
              "Judge each on its own, as if it were asked alone, and answer each in its own item.\\n\\n"
            + (f"The researcher's guesses listed above already hold this reply's new guesses ({', '.join(f'{g} is {y}' for y, g in new.items())}): the nearest earlier guess of a new guess is "
               "one from before this reply, never the guess itself.\\n\\n" if new and COMP["on"] and tests else "")''')

# 3. prefetch: the map, and a reading that names the guess itself is not taken
rep('''        tests = []
        ex0 = ok0.get("experiment")
        if ex0 is not None and ex0.get("kind") == "test":
            n_h, n_y = sum(r["type"] == "hypothesis" for r in ledger), sum(r["type"] == "why" for r in ledger)
            hyps, whys = {f"H{n_h + i + 1}": h for i, h in enumerate(ok0["hypotheses"])}, {f"Y{n_y + i + 1}": w for i, w in enumerate(ok0["whys"])}''',
    '''        tests, new = [], {}
        ex0 = ok0.get("experiment")
        if ex0 is not None and ex0.get("kind") == "test":
            n_h, n_y = sum(r["type"] == "hypothesis" for r in ledger), sum(r["type"] == "why" for r in ledger)
            hyps, whys = {f"H{n_h + i + 1}": h for i, h in enumerate(ok0["hypotheses"])}, {f"Y{n_y + i + 1}": w for i, w in enumerate(ok0["whys"])}
            ys = {gkey(w): y for y, w in whys.items()}
            new = {ys[k]: f"G{i + 1}" for i, (k, _) in enumerate(found) if k in ys}   # the id each new guess will have, by its name in the request''')
rep('''            g_ans, t_ans, saw = first_review(model, brief, ledger, [w for _, w in found], [(hid, ex, case) for hid, ex, case, _ in tests], tledger=pseudo if tests else None)''',
    '''            g_ans, t_ans, saw = first_review(model, brief, ledger, [w for _, w in found], [(hid, ex, case) for hid, ex, case, _ in tests], tledger=pseudo if tests else None, new=new if tests else None)''')
rep('''        for (k, w), x in zip(found, g_ans):
            if isinstance(x, dict):
                try:''',
    '''        own = {g: y for y, g in new.items()}
        for i, ((k, w), x) in enumerate(zip(found, g_ans)):
            m = re.match(r"\\s*([YH]\\d+)\\b", str((x or {}).get("nearest_earlier") or "")) if isinstance(x, dict) else None
            if m and own.get(f"G{i + 1}") == m.group(1):   # the guess compared with itself (s056): not taken, the guess is read alone
                append(ledger, turn, "note", ledger[-1]["id"] if ledger else None, {"text": f"the supervisor's batched reading of new guess G{i + 1} named the guess itself ({m.group(1)}) as its nearest earlier guess: that reading is not taken, and the guess is read alone"})
                continue
            if isinstance(x, dict):
                try:''')
f.write_text(s)
print("p7 applied to", f)
