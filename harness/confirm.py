"""Operator tool: confirm the answer of a finished session. Usage:
    confirm.py SESSION [--target MEASURE --direction max|min --condition "udp_loss_frac <= 0.01" ...]

A session measures its answer once, with one seed, over the brief's measured time. This tool measures the answer again,
apart from the session: the settings its report recommends (on a brief whose network may change: on the network with the
changes the report recommends), with SEEDS seeds (the session's seed and the next ones) at TIMES times the measured time.
It writes checks/confirm/<session>.json:
  - for each of the simulations: the seed, the measured seconds, the target, every condition with its numbers and
    whether it holds;
  - whether every condition holds in every one of them, and the smallest, the largest and the mean of the target;
  - what the session itself measured at the same settings and network (its own simulations of the recommendation), and
    what the report says it expects, so that the three can be read side by side.
The simulations are kept in checks/confirm/<session>/seed<k>/ and are run again only when the settings, the network, the
scheduling policy or the built program changed.
For a brief with an open goal the operator enters the goal the report states: --target, --direction, --condition.
Everything here is operator-only: it lives under checks/, no function of tools.py can reach it, and no agent is shown it."""
import argparse, json, subprocess
from pathlib import Path
import decision_rules, network, tools

CHECKS = tools.ROOT / "checks"
SEEDS = 3   # simulations of one confirmation: the session's seed and the next ones
TIMES = 5   # each over this many times the measured seconds of the session's simulations


def main():
    ap = argparse.ArgumentParser(description=f"Measure a finished session's answer again: {SEEDS} seeds at {TIMES} times the measured time.")
    ap.add_argument("session")
    ap.add_argument("--target", help="open goal only: the measure the report's goal optimises")
    ap.add_argument("--direction", choices=["max", "min"], help="open goal only")
    ap.add_argument("--condition", action="append", default=[], help="open goal only: a condition of the report's goal, e.g. \"udp_loss_frac <= 0.01\" (repeatable)")
    a = ap.parse_args()
    D = tools.SESSIONS / a.session
    if not (D / "session.json").is_file() or not (D / "report.json").is_file():
        ap.error(f"session {a.session} has no session.json or no report.json: only a session that ended with its report can be confirmed")
    meta, report = json.loads((D / "session.json").read_text()), json.loads((D / "report.json").read_text())
    brief = meta["given"]
    op = CHECKS / "operator.jsonl"
    lines = [json.loads(l) for l in op.read_text().splitlines() if l.strip()] if op.is_file() else []
    policy = next((l.get("policy") or l.get("mode") for l in lines if l.get("session") == a.session), None)
    if policy is None:
        ap.error(f"checks/operator.jsonl names no scheduling policy for {a.session}: it ran no simulation")

    goal = brief["goal"]
    if goal["kind"] == "given":
        target, direction, conditions, source = goal["target"]["measure"], goal["target"]["direction"], goal["conditions"], "the brief"
    else:
        if not (a.target and a.direction):
            ap.error("this brief's goal is open: enter the goal the report states with --target, --direction and --condition")
        target, direction, conditions, source = a.target, a.direction, a.condition, "entered by the operator from the report"

    # the answer: the knobs the report names, the others at their defaults; on a network that may change, the report's changes
    knobs = brief["knobs"]
    rec = report.get("recommendation") or {}
    want = {k: rec.get(k, spec["default"]) for k, spec in knobs.items()}
    clean = tools.clamp(want, brief)[0]
    opts = tools.options(clean, brief)
    changes = report.get("structure") or []
    net = network.apply(brief["topology"], changes, (brief.get("structure") or {}).get("new_link")) if changes and brief.get("topology") else None
    outputs = network.outputs(net) if net else tools.outputs(brief)
    if target not in outputs:
        ap.error(f"{target} is not one of the outputs of the recommended network" if net else f"{target} is not one of the outputs")
    seed0, seconds0 = int(opts["seed"]), float(opts["duration"])
    seconds = seconds0 * TIMES
    seconds = int(seconds) if seconds == int(seconds) else seconds

    # the simulations, side by side; each is run again only when something it depends on changed
    top = CHECKS / "confirm" / a.session
    jobs = []
    for k in range(SEEDS):
        d = top / f"seed{seed0 + k}"
        o = {**opts, "seed": seed0 + k, "duration": seconds}
        stamp = [o, changes, policy, tools.BIN.stat().st_mtime if not brief.get("topology") else tools.NET_BIN.stat().st_mtime]
        fresh = (d / "metrics.json").is_file() and (d / "options.json").is_file() and json.loads((d / "options.json").read_text()) == stamp
        proc = None
        if not fresh:
            d.mkdir(parents=True, exist_ok=True)
            for f in ("metrics.json", "options.json"):
                (d / f).unlink(missing_ok=True)
            proc = subprocess.Popen(tools.command(o, d, brief, topology=net), cwd=d, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    env={"LD_LIBRARY_PATH": str(tools.NS3 / "build/lib"), "TWOHOSTS_SCHED": policy})
        jobs.append((seed0 + k, d, stamp, proc))
    runs = []
    for seed, d, stamp, proc in jobs:
        said = ""
        if proc is not None:
            try:
                said = proc.communicate(timeout=tools.RUN_TIMEOUT * TIMES)[0]
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                said = f"no result after {tools.RUN_TIMEOUT * TIMES} s"
            if proc.returncode == 0 and (d / "metrics.json").is_file():
                (d / "options.json").write_text(json.dumps(stamp))
        if not (d / "options.json").is_file():
            runs.append({"seed": seed, "seconds": seconds, "error": (said or "no metrics.json")[-800:]})
            continue
        m = json.loads((d / "metrics.json").read_text())
        conds = []
        for c in conditions:
            held, with_numbers = decision_rules.check(c, outputs, ["run"], {"run": m})
            conds.append({"condition": c, "with_numbers": with_numbers, "holds": bool(held)})
        runs.append({"seed": seed, "seconds": seconds, "target": m.get(target), "conditions": conds, "holds": all(c["holds"] for c in conds), "metrics": m})

    # what the session itself measured at the same settings and network, and what its report expects
    led = [json.loads(l) for l in (D / "ledger.jsonl").read_text().splitlines() if l.strip()]
    key = tools.same(opts)
    own = []
    for r in led:
        b = r.get("body") or {}
        if r.get("type") != "simulation" or not isinstance(b.get("metrics"), dict) or not isinstance(b.get("params"), dict):
            continue
        try:
            same = tools.same(tools.options(tools.clamp(b["params"], brief)[0], brief)) == key
        except Exception:
            same = False
        if same and (b.get("structure") or []) == changes:
            own.append({"id": r.get("id"), "target": b["metrics"].get(target), "returned": bool(b.get("same_as"))})
    good = [r for r in runs if "error" not in r and isinstance(r.get("target"), (int, float))]
    values = [r["target"] for r in good]
    expected = (report.get("expected") or {}).get(target) if isinstance(report.get("expected"), dict) else None
    result = {
        "session": a.session, "brief": brief["id"], "scheduling_policy": policy,
        "goal": {"target": target, "direction": direction, "conditions": conditions, "source": source},
        "answer": {"settings": clean, "structure": changes},
        "how": {"seeds": [r["seed"] for r in runs], "seconds": seconds, "the_session_measured_over": seconds0, "times": TIMES},
        "runs": [{k: v for k, v in r.items() if k != "metrics"} for r in runs],
        "all_run": len(good) == SEEDS,
        "conditions_hold_in_all": bool(good) and len(good) == SEEDS and all(r["holds"] for r in good),
        "conditions_hold_in": sum(1 for r in good if r["holds"]),
        "target": {"smallest": min(values), "largest": max(values), "mean": sum(values) / len(values)} if values else None,
        "the_session_measured": own,
        "the_report_expects": expected,
    }
    out = CHECKS / "confirm" / f"{a.session}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("session", "brief", "how", "all_run", "conditions_hold_in_all", "conditions_hold_in", "target", "the_session_measured", "the_report_expects")}, indent=1))
    for r in runs:
        print(f"  seed {r['seed']}: " + (f"error: {r['error'][-200:]}" if "error" in r else f"{target} = {r['target']}, " + ("no condition" if not r["conditions"] else "; ".join(f"{c['with_numbers']} {'holds' if c['holds'] else 'DOES NOT HOLD'}" for c in r["conditions"]))))


if __name__ == "__main__":
    main()
