import json, sys, importlib.util
def load(d, name):
    sys.path.insert(0, d); spec = importlib.util.spec_from_file_location(name, d + "/loop.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); sys.path.pop(0); return m
a, b = load(sys.argv[1], "loop_a"), load(sys.argv[2], "loop_b")
for sid in sys.argv[3:]:
    led = [json.loads(l) for l in open(f"/home/chunguck.kim/project/sessions/{sid}/ledger.jsonl") if l.strip()]
    arm = json.load(open(f"/home/chunguck.kim/project/sessions/{sid}/session.json")).get("flags", {}).get("arm", "hypotheses")
    ta = a.render(led, readings=arm == "supervised", rethinks=arm == "hypotheses")
    try: tb = b.render(led, readings=arm == "supervised", rethinks=arm == "hypotheses", supervised=arm == "supervised")
    except TypeError: tb = b.render(led, readings=arm == "supervised", rethinks=arm == "hypotheses")
    if ta == tb: print(sid, arm, "same"); continue
    la, lb = ta.splitlines(), tb.splitlines()
    diff = [(x, y) for x, y in zip(la, lb) if x != y]
    print(sid, arm, f"{len(diff)} lines differ"); [print("   was:", x[:230], "\n   now:", y[:230]) for x, y in diff[:3]]
