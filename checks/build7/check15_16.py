"""Operator checks 15 and 16: what build 7 added.
  15  the length of a device's transmit queue (--devQueuePkts, in packets; not given = 10)
  16  series.csv is written sample by sample (a flush after each row), so a run can be watched while it runs
The predictions are stated here, before the program is run. They follow from how ns-3 hands packets from the
traffic-control layer to a point-to-point device: the device's queue takes packets until it holds its limit, then stops
the scheduler; when a transmission ends the device takes the next packet from its queue and the scheduler may hand over
one more. A packet "waits in the device's queue" from the moment the scheduler hands it over (events.csv: dequeue at
queue0 or queue1) until its transmission starts (tx_begin at dev0).
usage: check15_16.py BIN OUT   -> OUT/c15*/, OUT/c16*/ (kept), OUT/check15.json, OUT/check16.json"""
import csv, json, hashlib, subprocess, sys, time
from pathlib import Path
ROOT = Path.home() / "project"; BIN, OUT = sys.argv[1], Path(sys.argv[2])
ENV = {"LD_LIBRARY_PATH": str(ROOT / "ns-3.49/build/lib"), "TWOHOSTS_SCHED": "share"}
SAT = "--duration=3 --events=40"   # the defaults: UDP offers 2 Gbps on a 1 Gbps link, so the scheduler always has a packet to hand over; 40 ms of packet events
RUNS = {"c15a-dev1": SAT + " --devQueuePkts=1", "c15a-dev10-not-given": SAT, "c15a-dev50": SAT + " --devQueuePkts=50", "c15a-dev200": SAT + " --devQueuePkts=200",
        "c15b-dev10": "--devQueuePkts=10", "c15b-defaults": ""}
PREDICTED = {
    "15a": "with the scheduler never empty, the packets waiting in the sender's device queue number at most N and reach N (N = 1, 10 when not given, 50, 200); "
           "a packet waits there for the transmissions of the N packets before it: between N x 11.44 and N x 12.02 microseconds on the 1 Gbps link (frames of 1430 to 1502 bytes)",
    "15b": "given as 10 = the default: metrics.json, series.csv and flowmon.xml byte-identical to a run without it",
    "16a": "a run of 10 measured seconds takes about 25 s: 6 s after it was started its series.csv already holds samples (at least 5 rows) and its metrics.json does not exist yet",
    "16b": "the finished series.csv is byte-identical to the one build 6 wrote for the same options (the runs of checks 1 to 14 are compared separately; here the watched run itself, against build 6's run with no options)",
}
procs = []
for name, opts in RUNS.items():
    o = OUT / name; o.mkdir(parents=True, exist_ok=True); (o / "command.txt").write_text(f"TWOHOSTS_SCHED=share two-hosts {opts} --out={o}\n")
    procs.append((name, o, time.time(), subprocess.Popen([BIN] + opts.split() + [f"--out={o}"], cwd=o, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
# 16a, while the others run: one more default run, looked at after 6 s
o16 = OUT / "c16a-watched"; o16.mkdir(parents=True, exist_ok=True); (o16 / "command.txt").write_text(f"TWOHOSTS_SCHED=share two-hosts --out={o16}\n")
p16 = subprocess.Popen([BIN, f"--out={o16}"], cwd=o16, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True); time.sleep(6)
early = {"rows_after_6s": max(0, len((o16 / "series.csv").read_text().splitlines()) - 1) if (o16 / "series.csv").is_file() else 0, "metrics_json_after_6s": (o16 / "metrics.json").is_file(), "still_running_after_6s": p16.poll() is None}
p16.communicate()
for name, o, t0, p in procs:
    said = p.communicate()[0]
    with (o / "command.txt").open("a") as f: f.write(f"exit {p.returncode}, {time.time() - t0:.1f} s\n")
    if p.returncode: print(name, "exit", p.returncode, (said or "").strip()[-300:])
def waits(name):
    """From events.csv: the most packets waiting in dev0's queue, and each packet's wait there in microseconds (packets handed over inside the window only)."""
    inq, most, w = {}, 0, []
    for r in csv.DictReader((OUT / name / "events.csv").open()):
        if r["kind"] == "dequeue" and r["obj"] in ("queue0", "queue1"): inq[r["key"]] = int(r["t_ns"]); most = max(most, len(inq))
        elif r["kind"] == "tx_begin" and r["obj"] == "dev0" and r["key"] in inq: w.append((int(r["t_ns"]) - inq.pop(r["key"])) / 1000)
    w = sorted(w[len(w) // 4:])   # the first quarter of the window: the queue's packets from before the window are not known
    return most, w
c15 = []
for name, n in (("c15a-dev1", 1), ("c15a-dev10-not-given", 10), ("c15a-dev50", 50), ("c15a-dev200", 200)):
    most, w = waits(name); med = w[len(w) // 2] if w else None; lo, hi = n * 11.44, n * 12.02
    c15.append({"check": "15a", "run": name, "N": n, "most_waiting": most, "packets_timed": len(w), "wait_us": {"least": w[0] if w else None, "median": med, "most": w[-1] if w else None}, "predicted_wait_us": [round(lo, 2), round(hi, 2)],
                "pass": most == n and bool(w) and lo - 0.01 <= w[0] and w[-1] <= hi + 0.01})
same = lambda a, b: {f: hashlib.sha256((OUT / a / f).read_bytes()).hexdigest() == hashlib.sha256((OUT / b / f).read_bytes()).hexdigest() for f in ("metrics.json", "series.csv", "flowmon.xml")}
s = same("c15b-dev10", "c15b-defaults"); c15.append({"check": "15b", "identical": s, "pass": all(s.values())})
pj = json.loads((OUT / "c15a-dev50" / "params.json").read_text()); pd = json.loads((OUT / "c15b-defaults" / "params.json").read_text())
c15.append({"check": "15 params.json", "stated_when_given": pj.get("devQueuePkts"), "absent_when_not_given": "devQueuePkts" not in pd, "pass": pj.get("devQueuePkts") == 50 and "devQueuePkts" not in pd})
(OUT / "check15.json").write_text(json.dumps({"predicted_before_the_run": {k: v for k, v in PREDICTED.items() if k.startswith("15")}, "checks": c15}, indent=1) + "\n")
ref = ROOT / "checks/build6/c13c-defaults/series.csv"; ref = ref if ref.is_file() else None   # build 6, the same options: none
c16 = [{"check": "16a", **early, "pass": early["rows_after_6s"] >= 5 and not early["metrics_json_after_6s"] and early["still_running_after_6s"]},
       {"check": "16b", "compared_with": str(ref.relative_to(ROOT)) if ref else None, "command_of_that_run": (ref.parent / "command.txt").read_text().splitlines()[0] if ref and (ref.parent / "command.txt").is_file() else None,
        "identical": bool(ref) and hashlib.sha256(ref.read_bytes()).hexdigest() == hashlib.sha256((o16 / "series.csv").read_bytes()).hexdigest()}]
c16[1]["pass"] = c16[1]["identical"] if ref else None
(OUT / "check16.json").write_text(json.dumps({"predicted_before_the_run": {k: v for k, v in PREDICTED.items() if k.startswith("16")}, "checks": c16}, indent=1) + "\n")
for c in c15 + c16: print(("ok  " if c["pass"] else "FAIL" if c["pass"] is False else "n/a "), json.dumps({k: v for k, v in c.items() if k != "pass"})[:260])
