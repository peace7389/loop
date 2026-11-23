"""After the deploy, part 8 (s057 turn 1, 2026-11-23 04:24): a guess may name as its competitor a later guess of the same answer. Y3 named Y4, the
guess written after it; the harness accepts only a guess of the ledger or one earlier in the answer, so Y3 was restated and then marked contested:
"'Y4' is not a guess", while Y4 was recorded a moment later. Now a later guess of the same answer may be named, by the id it is to get: the check
waits for it, and when the answer's guesses are all read, the name becomes the id that guess was recorded with; if that guess was not accepted, the
guess competes with none and says so (contested).
python3 -I p8_forward.py LOOP_PY"""
import sys
from pathlib import Path
f = Path(sys.argv[1])
s = f.read_text()

def rep(a, b):
    global s
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)

rep('''        if supervised and COMP["on"] and w.get("competes_with") is not None and (w["competes_with"] not in stand or stand.get(w["competes_with"]) in ("revised", "refuted")):   # stand: the ledger's guesses and this answer's''',
    '''        if supervised and COMP["on"] and w.get("competes_with") is not None and w["competes_with"] not in ahead and (w["competes_with"] not in stand or stand.get(w["competes_with"]) in ("revised", "refuted")):   # stand: the ledger's guesses and this answer's; ahead: a later guess of this answer (part 8)''')

rep('''    why_map, h_map = {}, {}   # an id by position in this answer -> the id it was recorded with, or None (not accepted): the coherence audit, 2026-11-22
    for k_w, w in enumerate(t.get("whys") or []):
        pid = f"Y{n_why + k_w + 1}"
        why_map[pid] = None''',
    '''    why_map, h_map = {}, {}   # an id by position in this answer -> the id it was recorded with, or None (not accepted): the coherence audit, 2026-11-22
    why_list, forward = t.get("whys") or [], []   # forward: (the id a guess got, a later guess of this answer it competes with, by the id that one was to get)
    for k_w, w in enumerate(why_list):
        pid = f"Y{n_why + k_w + 1}"
        why_map[pid] = None
        ahead.clear()
        ahead.update(f"Y{n_why + j + 1}" for j in range(k_w + 1, len(why_list)))''')

rep('''        ok["whys"].append(w)
        new = f"Y{n_why + len(ok['whys'])}"   # the id it is about to get
        why_map[pid] = new
        whys[new], stand[new] = w, w["worth"]''',
    '''        ok["whys"].append(w)
        new = f"Y{n_why + len(ok['whys'])}"   # the id it is about to get
        why_map[pid] = new
        whys[new], stand[new] = w, w["worth"]
        if supervised and COMP["on"] and w.get("competes_with") in ahead:
            forward.append((new, w["competes_with"]))''')

# after the answer's guesses: a later guess named as competitor, by the id it was recorded with
rep('''    nth = lambda pid, base: int(pid[1:]) - base   # the position of a part of this answer, from the id it was to get''',
    '''    ahead.clear()
    for new, fwd in forward:   # part 8 (s057 Y3 named Y4, the guess after it)
        got = why_map.get(fwd)
        whys[new]["competes_with"] = got if got and stand.get(got) not in ("revised", "refuted") else None
        if not whys[new]["competes_with"]:
            whys[new]["contested"] = list(whys[new].get("contested") or []) + [f"competes_with {fwd}: your new guess number {int(fwd[1:]) - n_why} of this answer was not accepted, so this guess competes with none"]
    nth = lambda pid, base: int(pid[1:]) - base   # the position of a part of this answer, from the id it was to get''')

# ahead exists before why_problem is first called
rep('''    def why_problem(w, ask=True):''',
    '''    ahead = set()   # part 8: the ids the later guesses of this answer are to get, while a guess is read
    def why_problem(w, ask=True):''')
f.write_text(s)
print("p8 applied to", f)
