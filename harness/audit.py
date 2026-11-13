"""Operator tool: what the records of a finished session are worth as tests.   audit.py <session> [<session> ...]
Writes checks/audit/<session>.json; the session's own files are only read (and never its drafts).
It lists, from the ledger alone:
  checks       for each check, the labels its decision rule names and the simulation (run) behind each; "void": the rule
               names two or more labels and at least two are the same simulation, so it compared a simulation with
               itself; "one_simulation": the stricter case, every label it names is one simulation
  verdicts     for each verdict, the checks of its hypothesis in the last experiment that tested it before the verdict,
               and whether it rests only on void checks
  experiments  for each experiment of the model, the knobs it lists as varied that have one value in all its simulations
  designs      for each design of the model, the knobs of the brief it does not state (they ran at the default), and
               whether its label names a weight (w followed by a digit) while the design states no weightUdp
and the counts of each. The page marks the same void checks from the ledger itself (viewer/evidence_data.js) and
control.py counts them for Home (session_figures.py); this file is the full account, for the operator."""
import json, re, sys, time
from pathlib import Path
import session_figures, tools

AUDIT = tools.ROOT / "checks/audit"
WEIGHT = re.compile(r"(^|_)w\d")  # a label that names a weight: w30, u400_w80, w0303_q100


def audit(sid):
    folder = tools.SESSIONS / sid
    recs = [r for r in (json.loads(l) for l in (folder / "ledger.jsonl").read_text().splitlines() if l.strip()) if r["type"] not in ("draft", "scratch")]
    meta = json.loads((folder / "session.json").read_text()) if (folder / "session.json").is_file() else {}
    knobs = list(((meta.get("given") or {}).get("knobs") or {}))
    void, run, sims = session_figures.void_checks(recs), {}, {}
    for r in recs:
        if r["type"] == "simulation":
            b = r.get("body") or {}
            run[(r.get("parent"), b.get("label"))] = b.get("run_id")
            sims.setdefault(r.get("parent"), []).append(b.get("params") or {})
    checks, made = [], {}
    for i, r in enumerate(recs):
        if r["type"] != "check":
            continue
        b = r["body"]
        labels = list(dict.fromkeys(session_figures.LABEL.findall(str(b.get("decision_rule") or b.get("rule") or ""))))
        runs = {l: run.get((r.get("parent"), l)) for l in labels}
        same = [[a, c] for j, a in enumerate(labels) for c in labels[j + 1:] if runs[a] and runs[a] == runs[c]]
        checks.append({"id": r["id"], "turn": r["turn"], "experiment": r.get("parent"), "for": b.get("for"), "decision_rule": b.get("decision_rule") or b.get("rule"), "result": b.get("result"),
                       "runs": runs, "void": r["id"] in void, "one_simulation": void.get(r["id"]) == "one simulation", "same_simulation": same})
        made.setdefault(b.get("for"), []).append((i, r.get("parent"), r["id"]))
    verdicts = []
    for i, r in enumerate(recs):
        if r["type"] == "verdict":
            cs = [c for c in made.get(r["body"].get("for"), []) if c[0] < i]
            rests = [c[2] for c in cs if c[1] == cs[-1][1]] if cs else []
            verdicts.append({"id": r["id"], "turn": r["turn"], "for": r["body"].get("for"), "result": r["body"].get("result"), "rests_on": rests, "rests_only_on_void_checks": bool(rests) and all(c in void for c in rests)})
    experiments, designs = [], []
    for r in recs:
        if r["type"] != "experiment" or r.get("by") == "harness" or r["id"] == "X0":
            continue
        b = r["body"]
        if "runs" not in b:  # the first format: one simulation per experiment, no labels
            continue
        own = sims.get(r["id"], [])
        still = {k: sorted({str(p.get(k)) for p in own})[0] for k in b.get("varied") or [] if own and len({str(p.get(k)) for p in own}) == 1}
        experiments.append({"id": r["id"], "turn": r["turn"], "kind": b.get("kind"), "simulations": len(own), "varied": b.get("varied") or [], "varied_but_one_value": still})
        for d in b["runs"]:
            p = d.get("params") or {}
            designs.append({"experiment": r["id"], "label": d.get("label"), "does_not_state": [k for k in knobs if k not in p],
                            "label_names_a_weight_without_weightUdp": bool(WEIGHT.search(str(d.get("label")))) and "weightUdp" not in p})
    counts = {"checks": len(checks), "void": sum(c["void"] for c in checks), "one_simulation": sum(c["one_simulation"] for c in checks),
              "verdicts": len(verdicts), "verdicts_resting_only_on_void_checks": sum(v["rests_only_on_void_checks"] for v in verdicts),
              "experiments": len(experiments), "experiments_with_a_varied_knob_of_one_value": sum(bool(x["varied_but_one_value"]) for x in experiments),
              "designs": len(designs), "designs_stating_every_knob": sum(not d["does_not_state"] for d in designs),
              "designs_whose_label_names_a_weight_without_weightUdp": sum(d["label_names_a_weight_without_weightUdp"] for d in designs)}
    return {"session": sid, "brief": meta.get("brief"), "made": time.strftime("%Y-%m-%dT%H:%M:%S"), "counts": counts, "checks": checks, "verdicts": verdicts, "experiments": experiments, "designs": designs}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    AUDIT.mkdir(parents=True, exist_ok=True)
    for sid in sys.argv[1:]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", sid) or not (tools.SESSIONS / sid / "ledger.jsonl").is_file():
            sys.exit(f"unknown session {sid!r}")
        a = audit(sid)
        (AUDIT / f"{sid}.json").write_text(json.dumps(a, indent=1) + "\n")
        c = a["counts"]
        print(f"{sid} ({a['brief']}): {c['void']} void of {c['checks']} checks ({c['one_simulation']} name one simulation only) · {c['verdicts_resting_only_on_void_checks']} of {c['verdicts']} verdicts rest only on void checks · "
              f"{c['experiments_with_a_varied_knob_of_one_value']} of {c['experiments']} experiments list a varied knob that has one value · {c['designs_stating_every_knob']} of {c['designs']} designs state every knob · "
              f"{c['designs_whose_label_names_a_weight_without_weightUdp']} designs whose label names a weight state no weightUdp")


if __name__ == "__main__":
    main()
