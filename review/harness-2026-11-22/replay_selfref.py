"""s056's batched first reviews of turns 8 and 10 (calls 42 and 53), asked again on the real model: as they were, and with part 7's marks (the reply's
new guesses marked in the list of guesses, and the sentence that says which id each has and that a new guess's nearest earlier guess is never itself).
Counts how many new guesses the supervisor names as their own nearest earlier guess. python3 -I replay_selfref.py HARNESS_DIR"""
import json, re, sys, time, threading
sys.path.insert(0, sys.argv[1])
import loop, requests
model = requests.get(loop.API + "/models", timeout=30).json()["data"][0]["id"]
cs = {c["n"]: c for c in (json.loads(l) for l in open("/home/chunguck.kim/project/sessions/s056/calls.jsonl"))}
loop.COMP["on"] = True
jobs, out = [], {}
for n, first_y in ((42, 19), (53, 24)):
    c = cs[n]
    a = json.loads(c["answer"])
    gn = [g["guess"] for g in a["guesses"]]
    tn = [t["for"] for t in a["tests"]]
    new = {f"Y{first_y + i}": f"G{i + 1}" for i in range(len(gn))}
    u = c["user"]
    for y, g in new.items():
        assert u.count(f"\n  [{y}] ") == 1, (n, y)
        u = u.replace(f"\n  [{y}] ", f"\n  [{y}] (new in this reply: {g} below) ")
    key = "Judge each on its own, as if it were asked alone, and answer each in its own item.\n\n"
    assert u.count(key) == 1
    u = u.replace(key, key + f"The researcher's guesses listed above already hold this reply's new guesses ({', '.join(f'{g} is {y}' for y, g in new.items())}): the nearest earlier guess of a new guess is "
                  "one from before this reply, never the guess itself.\n\n")
    was_self = sum(1 for i, g in enumerate(a["guesses"]) if re.match(r"\s*([YH]\d+)", str(g.get("nearest_earlier"))) and re.match(r"\s*([YH]\d+)", str(g.get("nearest_earlier"))).group(1) == f"Y{first_y + i}")
    print(f"call {n} (turn {c['turn']}): in the session, {was_self} of {len(gn)} new guesses named themselves: {[(g['guess'], g['nearest_earlier'], g['defect']) for g in a['guesses']]}", flush=True)
    for label, text in (("as it was", c["user"]), ("with part 7", u)):
        jobs.append((n, label, text, loop.batch_schema(gn, tn), c["max_tokens"], new, c["system"]))

def run(n, label, text, schema, mt, new, system):
    t0 = time.time()
    try:
        content, reasoning, finish, usage = loop.ask(model, system, text, schema, True, 0, mt)
        d = json.loads(content)
        own = {g: y for y, g in new.items()}
        res = [(g.get("guess"), g.get("nearest_earlier"), g.get("defect")) for g in d.get("guesses") or []]
        selfs = sum(1 for g, ne, _ in res if (m := re.match(r"\s*([YH]\d+)", str(ne))) and own.get(re.match(r"\s*(G\d+)", str(g)).group(1) if re.match(r"\s*(G\d+)", str(g)) else "") == m.group(1))
        out[(n, label)] = f"call {n} {label}: {round(time.time() - t0)} s, {selfs} of {len(res)} name themselves: {res}"
    except Exception as e:
        out[(n, label)] = f"call {n} {label}: error {type(e).__name__}: {e}"

ts = [threading.Thread(target=run, args=j) for j in jobs]
for t in ts:
    t.start()
for t in ts:
    t.join()
for k in sorted(out):
    print(out[k])
