"""s056 call 23 (the supervisor's round-1 review of H5, the scheduler test, refused as "outside the permitted settings"), asked again on the real
model: as it was, and with the network sentence the fix adds to the supervisor's system text."""
import json, sys, time
sys.path.insert(0, sys.argv[1])
import loop, requests
model = requests.get(loop.API + "/models", timeout=30).json()["data"][0]["id"]
c = [json.loads(l) for l in open("/home/chunguck.kim/project/sessions/s056/calls.jsonl")][22]
assert c["n"] == 23
brief = json.load(open("/home/chunguck.kim/project/briefs/after_fix.json"))
loop.TOLERANCE = 1.0
new_sys = loop._system_for_supervisor({**brief, "knobs": brief["knobs"]})
sentence = new_sys[new_sys.index("THE NETWORK MAY CHANGE TOO"):].split("\n")[0] + "\n"
i = c["user"].index("TOLERANCE:")
user_new = c["user"][:i] + sentence + c["user"][i:]
loop.COMP["on"] = True
for label, u in (("as it was", c["user"]), ("with the fix", user_new)):
    t0 = time.time()
    content, reasoning, finish, usage = loop.ask(model, loop.SUPERVISOR, u, loop.REVIEW3_SCHEMA, True, 0, 9000)
    d = json.loads(content)
    print(f"{label}: {round(time.time() - t0)} s, Honest {d['honest']}, Consistent {d['consistent']}, Correct {d['correct']} (tested {d['if_tested']}, competitor {d['if_competitor']})")
    print("   consistent:", " ".join(d["consistent_why"].split())[:260])
    print("   feedback:", " ".join(d["feedback"].split())[:260])
