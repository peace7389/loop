"""Used by control.py (POST /api/export): one session as a folder that opens by double-clicking index.html, with no server.

The folder holds the evidence page (viewer/index.html, adrs_view.js and the evidence_*.js files, without the two that
only start things) and one file export_data.js with this session's files as text: its ledger WITHOUT the draft records,
session.json, report.json, runs/index.json and every run's series.csv. drafts.jsonl is never read. Chart.js is put
beside them when it can be fetched once (the time charts need it; everything else draws without it).

Operator-only data is left out unless asked for: the scheduling policy, the score, the review, the answer key and the
sweep table go in only with operator=True. Exports live in checks/exports/<session>-<time>[-operator]/, with a zip of
the same name beside the folder."""
import json, re, shutil, time, urllib.request, zipfile
import tools

CHECKS = tools.ROOT / "checks"
LEFT_OUT = ("evidence_run.js", "evidence_oprun.js")  # the New session panel and the operator's runs: they need the server
CHART = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
ROW = ("id", "brief", "records", "runs", "experiments", "simulations", "allowed", "turns", "held", "failed", "started", "last", "model", "how", "report",
       "left_open", "has_report", "done", "vc")  # what a session's line of the list may say without the operator's data


def make(sid, operator, row):
    """row: this session's line of control.py's session list. Returns where the export is."""
    src, viewer = tools.SESSIONS / sid, tools.ROOT / "viewer"
    name = f"{sid}-{time.strftime('%Y%m%d-%H%M%S')}" + ("-operator" if operator else "")
    out = CHECKS / "exports" / name
    out.mkdir(parents=True)
    files = {}
    ledger = [l for l in (src / "ledger.jsonl").read_text().splitlines() if l.strip() and json.loads(l).get("type") not in ("draft", "scratch")]
    files[f"sessions/{sid}/ledger.jsonl"] = "\n".join(ledger) + "\n"
    for rel in ("session.json", "report.json", "runs/index.json"):
        if (src / rel).is_file():
            files[f"sessions/{sid}/{rel}"] = (src / rel).read_text()
    if (viewer / "objects.json").is_file():  # the ns-3 objects of the picture of the system; it holds no operator-only value
        files["objects.json"] = (viewer / "objects.json").read_text()
    for series in sorted((src / "runs").glob("*/series.csv")):
        files[f"sessions/{sid}/runs/{series.parent.name}/series.csv"] = series.read_text()
    line = {k: row.get(k) for k in ROW} | {"running": False, "stoppable": False, "policy": None, "policy_hidden": False, "score": None, "review": {"n": 0, "ticked": [], "signed": None}}
    if operator:
        line.update(policy=row.get("policy"), policy_hidden=row.get("policy_hidden"), score=row.get("score"), review=row.get("review"))
        for rel in (f"checks/scores/{sid}.json", f"checks/reviews/{sid}.json", f"checks/keys/{row.get('brief')}.json"):
            if (tools.ROOT / rel).is_file():
                files[rel] = (tools.ROOT / rel).read_text()
        sweep = json.loads(files[f"checks/scores/{sid}.json"]).get("sweep") if f"checks/scores/{sid}.json" in files else None
        if sweep and (CHECKS / "sweeps" / sweep / "table.csv").is_file():
            files[f"checks/sweeps/{sweep}/table.csv"] = (CHECKS / "sweeps" / sweep / "table.csv").read_text()
    scripts = ["adrs_view.js"] + [p.name for p in sorted(viewer.glob("evidence*.js")) if p.name not in LEFT_OUT]
    for n in scripts:
        shutil.copy(viewer / n, out / n)
    cache = CHECKS / "exports" / "chart.umd.min.js"  # fetched once, then copied into every export
    if not cache.is_file():
        try:
            cache.write_bytes(urllib.request.urlopen(CHART, timeout=15).read())
        except OSError:
            pass
    data = {"session": sid, "made": time.strftime("%Y-%m-%dT%H:%M:%S"), "operator": bool(operator), "chart": None,
            "status": {"control": False, "session": None, "other_loop": None, "sessions": [line], "briefs": [], "sweeps": []}, "files": files}
    if cache.is_file():
        shutil.copy(cache, out / "chart.umd.min.js")
        data["chart"] = "chart.umd.min.js"
    (out / "export_data.js").write_text("// One session's files as text, for the page beside it (made by harness/export_session.py). No draft is in here.\nwindow.EV_EXPORT = "
                                        + json.dumps(data) + ";\n")
    html = (viewer / "index.html").read_text()
    listed = re.search(r"\[('adrs_view\.js'.*?)\]\.reduce", html, re.S)  # the page's own list of scripts: the data first, the two left out removed
    names = ["export_data.js"] + [n for n in re.findall(r"'([^']+\.js)'", listed.group(1)) if n not in LEFT_OUT]
    (out / "index.html").write_text(html.replace(listed.group(1), ", ".join(f"'{n}'" for n in names)))
    with zipfile.ZipFile(out.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):
            z.write(p, f"{name}/{p.name}")
    return {"folder": f"checks/exports/{name}", "zip": f"checks/exports/{name}.zip", "open": f"checks/exports/{name}/index.html", "operator": bool(operator),
            "files": len(list(out.iterdir())), "bytes": sum(p.stat().st_size for p in out.iterdir()), "chart_library": bool(data["chart"])}
