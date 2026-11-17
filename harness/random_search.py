"""Operator tool: the comparison arm "random". No model: N settings drawn at random from the brief's own ranges, each
simulated once, and the best of them (the goal's target, among those where every condition holds) taken as the
"recommendation". It answers what a session's budget buys without any thinking, so that a session of the loop can be
compared with it (the open question of 2026-11-15: does the loop help at all?). Usage:
    python3 harness/random_search.py --brief ID --policy share|cap --n N --seed K [--name NAME]
Each knob is drawn on its own, evenly over its range: a number between min and max (a whole number where the knob is
one, rounded to the knob's step where it has one), a rate between its smallest and largest rate, one of the choices.
The draw depends only on --seed, so it can be repeated. The simulations are made by the built program directly, like a
sweep's, at most 64 at a time. Written to checks/random/<name>/: table.csv (one row per simulation, in the order
drawn) and result.json (the brief, the policy, n, the seed, how many rows meet the conditions, the best row).
The brief's goal must be given (an open goal has no target to rank by).
Everything here is operator-only: it lives under checks/, and no function of tools.py can reach it."""
import argparse, csv, json, random, threading, time
import control, decision_rules, tools


def draw(rng, k, s):
    """One value of knob k (its entry s of the brief) at random, evenly over what the brief allows."""
    if "choices" in s:
        return rng.choice(s["choices"])
    if isinstance(s["min"], str):  # a rate: evenly between the two rates, in whole Mbps
        lo, hi = tools._rate_bps(s["min"]), tools._rate_bps(s["max"])
        return f"{round(rng.uniform(lo, hi) / 1e6)}Mbps"
    if isinstance(s["min"], int) and isinstance(s["max"], int):
        step = s.get("step", 1)
        return s["min"] + step * rng.randint(0, (s["max"] - s["min"]) // step)
    v = rng.uniform(s["min"], s["max"])
    return round(s["min"] + s["step"] * round((v - s["min"]) / s["step"]), 6) if "step" in s else round(v, 4)


def main():
    ap = argparse.ArgumentParser(description="The comparison arm 'random': N random settings of a brief, simulated, and the best of them.")
    ap.add_argument("--brief", required=True)
    ap.add_argument("--policy", choices=["share", "cap"], required=True, help="the scheduling policy")
    ap.add_argument("--n", type=int, required=True, help="how many settings to draw and simulate (a session's budget, to compare with it)")
    ap.add_argument("--seed", type=int, required=True, help="the seed of the draw (not the simulation's seed)")
    ap.add_argument("--name", help="folder name under checks/random/; default: <brief>-<policy>-n<N>-seed<K>")
    a = ap.parse_args()
    try:
        brief = tools.load_brief(a.brief)
    except ValueError as e:
        ap.error(str(e))
    goal = brief["goal"]
    if goal.get("kind") != "given":
        ap.error("the brief's goal is open: a random search needs a given target to rank by")
    if not 1 <= a.n <= control.SWEEP_MAX:
        ap.error(f"--n is from 1 to {control.SWEEP_MAX}")
    name = a.name or f"{brief['id']}-{a.policy}-n{a.n}-seed{a.seed}"
    folder = control.CHECKS / "random" / name
    if folder.exists():
        ap.error(f"{folder} exists already: a random search is not made twice under one name")
    folder.mkdir(parents=True)
    rng = random.Random(a.seed)
    combos = [{k: draw(rng, k, s) for k, s in brief["knobs"].items()} for _ in range(a.n)]
    st = {"id": name, "brief": brief["id"], "policy": a.policy, "total": a.n, "done": 0, "failed": 0, "running": 0, "state": "running", "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "ended": None, "seconds": 0}
    control.run_sweep(folder, brief, a.policy, combos, st, threading.Event())
    outputs, target, direction = tools.MANIFEST["outputs"], goal["target"]["measure"], goal["target"]["direction"]
    rows = [r for r in csv.DictReader((folder / "table.csv").open()) if not r.get("error")]
    num = lambda v: tools._rate_bps(v) if str(v).endswith("bps") else float(v)
    for r in rows:
        r["_m"] = {k: num(r[k]) for k in outputs if r.get(k) not in (None, "")}
    meets = [r for r in rows if all(decision_rules.check(c, outputs, ["row"], {"row": r["_m"]})[0] for c in goal["conditions"])]
    best = (max if direction == "max" else min)(meets, key=lambda r: r["_m"][target]) if meets else None
    result = {"name": name, "arm": "random", "brief": brief["id"], "scheduling_policy": a.policy, "n": a.n, "seed_of_the_draw": a.seed, "simulated": len(rows), "failed": st["failed"],
              "goal": {"target": target, "direction": direction, "conditions": goal["conditions"]}, "meet_the_conditions": len(meets),
              "best": None if best is None else {"settings": {k: best[k] for k in brief["knobs"]}, "measured": best["_m"], target: best["_m"][target]}, "seconds": st["seconds"]}
    (folder / "result.json").write_text(json.dumps(result, indent=1) + "\n")
    print(f"random search {name}: {len(rows)} of {a.n} simulated, {len(meets)} meet the conditions; best {target} = " + (f"{best['_m'][target]:.0f} at " + ", ".join(f"{k}={best[k]}" for k in brief["knobs"]) if best else "none"))


if __name__ == "__main__":
    main()
