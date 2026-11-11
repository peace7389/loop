"""Operator tool: score a finished session against a sweep. Usage:
    score.py SESSION [--target MEASURE --direction max|min --condition "udp_loss_frac <= 0.01" ...] [--judge N=yes|no|unjudged ...]

It reads the session's own session.json and report.json, the session's scheduling policy (checks/operator.jsonl), the
answer key of its brief (checks/keys/<brief>.json: which sweep belongs to which scheduling policy, and the checklist)
and that sweep's table (checks/sweeps/<id>/table.csv), and writes checks/scores/<session>.json:
  - the best row of the sweep for the goal (the target, among the rows where every condition holds);
  - the row nearest the model's recommendation, the gap between the two on the target, and whether the conditions hold there;
  - when the recommendation is not a point of the grid: one operator simulation at exactly the recommended settings
    (checks/scores/<session>.recommendation/), with the same gap and conditions from it, because the nearest row can sit
    on the other side of a threshold;
  - the simulations the session used, and the size of the sweep;
  - the checklist, each item yes / no / unjudged. The operator judges: --judge 2=yes, or edit the file; judgements
    already in the file are kept when the score is written again.
For a brief with an open goal the operator enters the goal the report states: --target, --direction, --condition.
Everything here is operator-only: it lives under checks/, and no function of tools.py can reach it."""
import argparse, csv, json, subprocess
from pathlib import Path
import decision_rules, tools

CHECKS = tools.ROOT / "checks"

def number(v):
    try:
        return tools._rate_bps(v) if str(v).endswith("bps") else float(v)
    except (TypeError, ValueError):
        return None

def distance(row, want, knobs):
    """How far a sweep row is from the recommended settings: per knob the difference as a part of its range (0 or 1 for a choice)."""
    d = 0.0
    for k, spec in knobs.items():
        a, b = row.get(k), want[k]
        if "choices" in spec:
            d += str(a) != str(b)
        else:
            lo, hi = number(spec["min"]), number(spec["max"])
            d += abs(number(a) - number(b)) / ((hi - lo) or 1)
    return d

def main():
    ap = argparse.ArgumentParser(description="Score a finished session against the sweep of its brief and scheduling policy.")
    ap.add_argument("session")
    ap.add_argument("--target", help="open goal only: the measure the report's goal optimises")
    ap.add_argument("--direction", choices=["max", "min"], help="open goal only")
    ap.add_argument("--condition", action="append", default=[], help="open goal only: a condition of the report's goal, e.g. \"udp_loss_frac <= 0.01\" (repeatable)")
    ap.add_argument("--judge", action="append", default=[], metavar="N=yes|no|unjudged", help="the operator's judgement of checklist item N (repeatable)")
    a = ap.parse_args()
    D = tools.SESSIONS / a.session
    if not (D / "session.json").is_file() or not (D / "report.json").is_file():
        ap.error(f"session {a.session} has no session.json or no report.json: only a session that ended with its report can be scored")
    meta, report = json.loads((D / "session.json").read_text()), json.loads((D / "report.json").read_text())
    brief, outputs = meta["given"], tools.MANIFEST["outputs"]
    lines = [json.loads(l) for l in (CHECKS / "operator.jsonl").read_text().splitlines() if l.strip()]
    policy = next((l.get("policy") or l.get("mode") for l in lines if l.get("session") == a.session), None)
    key_file = CHECKS / "keys" / f"{brief['id']}.json"
    if not key_file.is_file():
        ap.error(f"no answer key {key_file}")
    key = json.loads(key_file.read_text())
    sweep = (key.get("per_scheduling_policy") or {}).get(policy) or {}
    table = CHECKS / "sweeps" / str(sweep.get("sweep")) / "table.csv"
    if not table.is_file():
        ap.error(f"the answer key names no finished sweep for scheduling policy {policy!r}")

    # the goal: the brief's when it is given; otherwise what the operator enters from the report
    goal = brief["goal"]
    if goal["kind"] == "given":
        target, direction, conditions, source = goal["target"]["measure"], goal["target"]["direction"], goal["conditions"], "the brief"
    else:
        if not (a.target and a.direction):
            ap.error("this brief's goal is open: enter the goal the report states with --target, --direction and --condition")
        target, direction, conditions, source = a.target, a.direction, a.condition, "entered by the operator from the report"
    if target not in outputs:
        ap.error(f"{target} is not one of the outputs")
    rows = [r for r in csv.DictReader(table.open()) if not r.get("error")]
    for r in rows:
        r["_m"] = {k: number(r[k]) for k in outputs if r.get(k) not in (None, "")}
    holds = lambda m: [bool(decision_rules.check(c, outputs, ["row"], {"row": m})[0]) for c in conditions]
    allowed = [r for r in rows if all(holds(r["_m"]))]
    pick = max if direction == "max" else min
    best = pick(allowed, key=lambda r: r["_m"][target]) if allowed else None
    knobs = brief["knobs"]
    show = lambda r: {k: r[k] for k in knobs} | {k: r["_m"][k] for k in ("udp_goodput_bps", "tcp_goodput_bps", "udp_loss_frac", "link_util") if k in r["_m"]}

    # the recommendation: the knobs the report names, the others at their defaults; the nearest row of the sweep
    rec = report["recommendation"]
    want = {k: rec.get(k, spec["default"]) for k, spec in knobs.items()}
    near = min(rows, key=lambda r: distance(r, want, knobs))
    dist = distance(near, want, knobs)
    gap = None if best is None else (best["_m"][target] - near["_m"][target]) * (1 if direction == "max" else -1)
    ties = [r for r in allowed if best is not None and r["_m"][target] == best["_m"][target]]

    # off the grid: measure the recommendation itself, once, by the built program (an operator simulation)
    exact = None
    if dist >= 1e-9:
        opts = tools.options(tools.clamp(want, brief)[0], brief)
        d = CHECKS / "scores" / f"{a.session}.recommendation"
        d.mkdir(parents=True, exist_ok=True)
        if not (d / "metrics.json").is_file() or json.loads((d / "options.json").read_text()) != [opts, policy]:
            subprocess.run([str(tools.BIN)] + [f"--{k}={v}" for k, v in opts.items()] + [f"--out={d}"], cwd=d, check=True, capture_output=True, timeout=tools.RUN_TIMEOUT,
                           env={"LD_LIBRARY_PATH": str(tools.NS3 / "build/lib"), "TWOHOSTS_SCHED": policy})
            (d / "options.json").write_text(json.dumps([opts, policy]))
        exact = json.loads((d / "metrics.json").read_text())
    exact_gap = None if exact is None or best is None else (best["_m"][target] - exact[target]) * (1 if direction == "max" else -1)

    out_file = CHECKS / "scores" / f"{a.session}.json"
    old = json.loads(out_file.read_text()) if out_file.is_file() else {}
    judged = {c["item"]: c["judgement"] for c in old.get("checklist", [])}
    checklist = [{"n": i + 1, "item": item, "judgement": judged.get(item, "unjudged")} for i, item in enumerate(key.get("checklist", []))]
    for j in a.judge:
        n, _, v = j.partition("=")
        if not n.isdigit() or not 1 <= int(n) <= len(checklist) or v not in ("yes", "no", "unjudged"):
            ap.error(f"--judge {j}: use N=yes, N=no or N=unjudged with N from 1 to {len(checklist)}")
        checklist[int(n) - 1]["judgement"] = v
    score = {"session": a.session, "brief": brief["id"], "scheduling_policy": policy, "sweep": sweep["sweep"], "sweep_size": len(rows),
             "goal": {"target": target, "direction": direction, "conditions": conditions, "from": source},
             "best_row": show(best) if best else None, "rows_meeting_the_conditions": len(allowed), "rows_as_good_as_the_best": len(ties),
             "recommendation": rec, "recommendation_with_defaults": want, "nearest_row": show(near), "nearest_row_distance": round(dist, 6), "on_the_grid": dist < 1e-9,
             "conditions_hold_at_the_recommendation": dict(zip(conditions, holds(near["_m"]))),
             "gap_on_target": gap, "gap_as_part_of_best": None if gap is None or not best["_m"][target] else gap / best["_m"][target],
             "at_the_recommendation_itself": None if exact is None else {"measured": {k: exact[k] for k in ("udp_goodput_bps", "tcp_goodput_bps", "udp_loss_frac", "link_util")},
                                                                         "conditions_hold": dict(zip(conditions, holds(exact))), "gap_on_target": exact_gap},
             "expected_by_the_model": report.get("expected"), "simulations_used": meta.get("simulations"), "simulations_allowed": brief["limits"]["simulations"],
             "how_the_session_ended": meta.get("how"), "left_open": meta.get("left_open"), "checklist": checklist}
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(score, indent=1) + "\n")

    unit = (lambda v: f"{v / 1e6:,.3f} Mbps") if target.endswith("_bps") else (lambda v: f"{v:g}")
    print(f"session {a.session}: brief {brief['id']}, scheduling policy {policy}, sweep {sweep['sweep']} ({len(rows)} simulations)")
    print(f"goal ({source}): {direction} {target}" + (" while " + " and ".join(conditions) if conditions else ""))
    if best:
        print(f"best row of the sweep:   {target} = {unit(best['_m'][target])}  at " + ", ".join(f"{k}={best[k]}" for k in knobs)
              + f"   ({len(allowed)} rows meet the conditions; {len(ties)} are as good as the best)")
    else:
        print("no row of the sweep meets the conditions")
    print(f"the model's recommendation: " + ", ".join(f"{k}={v}" for k, v in rec.items()) + f"   -> nearest row{'' if dist < 1e-9 else f' (not on the grid, distance {dist:.4f})'}: "
          + ", ".join(f"{k}={near[k]}" for k in knobs) + f"; {target} = {unit(near['_m'][target])}")
    print("conditions at the recommendation: " + (", ".join(f"{c}: {'holds' if ok else 'DOES NOT HOLD'}" for c, ok in zip(conditions, holds(near["_m"]))) or "none"))
    if gap is not None:
        print(f"GAP on {target}, best row minus nearest row: {unit(gap)} ({100 * gap / best['_m'][target]:.3f}% of the best)")
    if exact is not None:
        print(f"at the recommendation itself (one operator simulation): {target} = {unit(exact[target])}; "
              + (", ".join(f"{c}: {'holds' if ok else 'DOES NOT HOLD'}" for c, ok in zip(conditions, holds(exact))) or "no conditions")
              + (f"; GAP, best row minus this: {unit(exact_gap)} ({100 * exact_gap / best['_m'][target]:.3f}% of the best)" if exact_gap is not None else ""))
    print(f"SIMULATIONS: the session used {meta.get('simulations')} of {brief['limits']['simulations']} allowed; the sweep has {len(rows)}")
    print("checklist (the operator's judgement): " + "; ".join(f"{c['n']}. {c['judgement']}" for c in checklist))
    print(f"written: {out_file}")

if __name__ == "__main__":
    main()
