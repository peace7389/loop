"""Operator check 12: separate queue lengths for UDP and TCP (--queuePktsUdp, --queuePktsTcp).
The predictions are stated here, before the program is run.
usage: check12.py BIN OUT EVENTS_DIR   -> OUT/c12*/ (kept) and OUT/check12.json; the event recordings go to EVENTS_DIR (large, not kept)"""
import csv, json, subprocess, sys, time
from pathlib import Path
ROOT = Path.home() / "project"
BIN, OUT, EVD = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
ENV = lambda pol: {"LD_LIBRARY_PATH": str(ROOT / "ns-3.49/build/lib"), "TWOHOSTS_SCHED": pol}
# name: (policy, options)
RUNS = {
    "c12a-udp20-tcp200":        ("share", "--queuePktsUdp=20 --queuePktsTcp=200"),
    "c12b-udp200-tcp20":        ("share", "--queuePktsUdp=200 --queuePktsTcp=20"),
    "c12c-both100":             ("share", "--queuePktsUdp=100 --queuePktsTcp=100"),
    "c12c-defaults":            ("share", ""),
    "c12d-common37":            ("share", "--queuePkts=37"),
    "c12d-common999-own37":     ("share", "--queuePkts=999 --queuePktsUdp=37 --queuePktsTcp=37"),
    "c12e-udp37-only":          ("share", "--queuePktsUdp=37"),
    "c12e-udp37-tcp100":        ("share", "--queuePkts=100 --queuePktsUdp=37 --queuePktsTcp=100"),
    "c12f-cap-udp20-tcp200":    ("cap", "--queuePktsUdp=20 --queuePktsTcp=200"),
}
# the same settings with every packet event of the two measured seconds recorded (duration 2), to read how many packets waited at each drop
EVENTS = {"c12a-udp20-tcp200": (20, 200), "c12b-udp200-tcp20": (200, 20), "c12f-cap-udp20-tcp200": (20, 200)}
PREDICTED = {
    "12a": "queuePktsUdp 20, queuePktsTcp 200: the UDP queue never holds more than 20 packets and every UDP drop happens with exactly 20 waiting; the TCP queue never more than 200 and every TCP drop with exactly 200 waiting; the TCP queue is seen above 100 (the common default)",
    "12b": "swapped (200, 20): the same with 200 for UDP and 20 for TCP",
    "12c": "both given as 100 = the default: metrics.json, series.csv and flowmon.xml byte-identical to a run without them (difference 0)",
    "12d": "queuePkts 37 against queuePkts 999 with both own lengths 37: metrics.json, series.csv and flowmon.xml byte-identical (the common length has no effect once both are given)",
    "12e": "queuePktsUdp 37 alone against queuePkts 100, queuePktsUdp 37, queuePktsTcp 100: byte-identical (a queue without its own length uses the common one)",
    "12f": "under the other scheduling policy, (20, 200): the same limits as 12a",
}
procs = []
for name, (pol, opts) in RUNS.items():
    o = OUT / name; o.mkdir(parents=True, exist_ok=True)
    (o / "command.txt").write_text(f"TWOHOSTS_SCHED={pol} two-hosts {opts} --out={o}\n")
    procs.append((o, time.time(), subprocess.Popen([BIN] + opts.split() + [f"--out={o}"], cwd=o, env=ENV(pol), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
for name in EVENTS:
    pol, opts = RUNS[name]; o = EVD / name; o.mkdir(parents=True, exist_ok=True)
    procs.append((o, time.time(), subprocess.Popen([BIN] + opts.split() + ["--duration=2", "--events=2000", "--eventsAt=2", f"--out={o}"], cwd=o, env=ENV(pol), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
for o, t0, p in procs:
    said = p.communicate()[0]
    if o.parent == OUT:
        with (o / "command.txt").open("a") as f:
            f.write(f"exit {p.returncode}, {time.time() - t0:.1f} s\n")
    if p.returncode:
        print("FAILED", o, said[-300:]); sys.exit(2)

def series_max(name):
    rows = list(csv.DictReader((OUT / name / "series.csv").open()))
    return max(int(r["q_band0"]) for r in rows), max(int(r["q_band1"]) for r in rows)

def at_drops(name):
    """From the event recording: per queue, how many drops at each number waiting, and the most ever waiting after an enqueue."""
    drops, most = {"queue0": {}, "queue1": {}}, {"queue0": 0, "queue1": 0}
    with (EVD / name / "events.csv").open() as f:
        next(f)
        for line in f:
            t, ev, kind, obj, flow, key, size, info = line.rstrip("\n").split(",")
            if obj in most:
                if kind == "drop":
                    drops[obj][info] = drops[obj].get(info, 0) + 1
                elif kind == "enqueue":
                    most[obj] = max(most[obj], int(info))
    return drops, most

same = lambda a, b: {f: (OUT / a / f).read_bytes() == (OUT / b / f).read_bytes() for f in ("metrics.json", "series.csv", "flowmon.xml")}
res = {"predicted_before_the_run": PREDICTED, "checks": []}
for tag, name in (("12a", "c12a-udp20-tcp200"), ("12b", "c12b-udp200-tcp20"), ("12f", "c12f-cap-udp20-tcp200")):
    lu, lt = EVENTS[name]; mu, mt = series_max(name); drops, most = at_drops(name); m = json.loads((OUT / name / "metrics.json").read_text())
    ok = (mu <= lu and mt <= lt and most["queue0"] <= lu and most["queue1"] <= lt and set(drops["queue0"]) == {str(lu)} and set(drops["queue1"]) == {str(lt)}
          and (max(mt, most["queue1"]) > 100 if lt > 100 else max(mu, most["queue0"]) > 100))
    res["checks"].append({"check": tag, "run": name, "limits": {"udp": lu, "tcp": lt},
        "whole_run_series": {"most_waiting_udp": mu, "most_waiting_tcp": mt, "drops_band0": m["drops_band0"], "drops_band1": m["drops_band1"]},
        "two_recorded_seconds": {"most_waiting_udp": most["queue0"], "most_waiting_tcp": most["queue1"], "udp_drops_by_number_waiting": drops["queue0"], "tcp_drops_by_number_waiting": drops["queue1"]},
        "params_json": json.loads((OUT / name / "params.json").read_text()), "pass": bool(ok)})
for tag, a, b in (("12c", "c12c-both100", "c12c-defaults"), ("12d", "c12d-common37", "c12d-common999-own37"), ("12e", "c12e-udp37-only", "c12e-udp37-tcp100")):
    s = same(a, b)
    res["checks"].append({"check": tag, "runs": [a, b], "byte_identical": s, "params_json": [json.loads((OUT / x / "params.json").read_text()) for x in (a, b)], "pass": all(s.values())})
(OUT / "check12.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(res["checks"], indent=1))
print("check 12:", "pass" if all(c["pass"] for c in res["checks"]) else "FAIL")
