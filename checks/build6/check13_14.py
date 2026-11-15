"""Operator checks 13 and 14: the two settings added in build 6.
  13  TCP's first window (--tcpInitCwnd, in segments; not given = ns-3's own, 10)
  14  TCP's send and receive buffer (--tcpBufBytes, in bytes each; not given = 1 MB)
The predictions are stated here, before the program is run (a probe of three short runs showed beforehand where a
connection's start stands in series.csv; the numbers below follow from TCP's rules, not from that probe).
usage: check13_14.py BIN OUT   -> OUT/c13*/, OUT/c14*/ (kept), OUT/check13.json, OUT/check14.json"""
import csv, json, hashlib, subprocess, sys, time
from pathlib import Path
ROOT = Path.home() / "project"; BIN, OUT = sys.argv[1], Path(sys.argv[2]); SEG = 1448  # payload bytes of a full segment at mtu 1500
ENV = {"LD_LIBRARY_PATH": str(ROOT / "ns-3.49/build/lib"), "TWOHOSTS_SCHED": "share"}
SLOW = "--udpRate=0bps --linkDelay=200ms --warmup=0 --duration=3"   # TCP alone, a long delay: the first window arrives as one burst before any acknowledgement returns
WAN = "--udpRate=0bps --linkDelay=10ms --duration=10"                # TCP alone, round trip 20 ms: the buffer, not the link, limits the window
RUNS = {
    "c13a-first1": SLOW + " --tcpInitCwnd=1", "c13a-first4": SLOW + " --tcpInitCwnd=4", "c13a-first40": SLOW + " --tcpInitCwnd=40", "c13b-first-not-given": SLOW,
    "c13c-first10": "--tcpInitCwnd=10", "c13c-defaults": "", "c13d-first1-10s": "--udpRate=0bps --tcpInitCwnd=1", "c13d-first40-10s": "--udpRate=0bps --tcpInitCwnd=40",
    "c14a-buf64k": WAN + " --tcpBufBytes=65536", "c14b-buf256k": WAN + " --tcpBufBytes=262144", "c14c-buf1m": "--tcpBufBytes=1048576", "c14c-defaults": "",
}
PREDICTED = {
    "13a": "first window 1, 4, 40 segments: the first congestion window recorded is N x 1448 bytes, and the first burst that arrives is N x 1448 bytes (N full segments before any acknowledgement)",
    "13b": "not given: the same with N = 10, ns-3's own first window",
    "13c": "given as 10 = the default: metrics.json, series.csv and flowmon.xml byte-identical to a run without it",
    "13d": "over 10 measured seconds on the default link the first window changes the goodput by less than 1 % (1 against 40 segments): it matters at the start only",
    "14a": "buffers of 65,536 bytes, round trip 20 ms: the window cannot exceed the buffer, so goodput is at most 8 x 65,536 / 0.020 = 26.2 Mbps, and at least 40 % of that",
    "14b": "buffers of 262,144 bytes: at most 104.9 Mbps and at least 40 % of that; between 3 and 4.5 times the goodput of 14a (four times the buffer)",
    "14c": "given as 1,048,576 = the default: metrics.json, series.csv and flowmon.xml byte-identical to a run without it",
}
procs = []
for name, opts in RUNS.items():
    o = OUT / name; o.mkdir(parents=True, exist_ok=True); (o / "command.txt").write_text(f"TWOHOSTS_SCHED=share two-hosts {opts} --out={o}\n")
    procs.append((name, o, time.time(), subprocess.Popen([BIN] + opts.split() + [f"--out={o}"], cwd=o, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
for name, o, t0, p in procs:
    said = p.communicate()[0]
    with (o / "command.txt").open("a") as f: f.write(f"exit {p.returncode}, {time.time() - t0:.1f} s\n")
    if p.returncode: print(name, "exit", p.returncode, (said or "").strip()[-300:])
rows = lambda n: list(csv.DictReader((OUT / n / "series.csv").open())); met = lambda n: json.loads((OUT / n / "metrics.json").read_text())
same = lambda a, b: {f: hashlib.sha256((OUT / a / f).read_bytes()).hexdigest() == hashlib.sha256((OUT / b / f).read_bytes()).hexdigest() for f in ("metrics.json", "series.csv", "flowmon.xml")}
def start(n):
    """The first congestion window recorded, and the bytes of the first burst that arrives (one sample of 0.1 s)."""
    r = rows(n); cw = next(int(float(x["cwnd"])) for x in r if float(x["cwnd"]) > 0); burst = next(round(float(x["tcp_bps"]) * 0.1 / 8) for x in r if float(x["tcp_bps"]) > 0); return cw, burst
c13 = []
for n_seg, name in ((1, "c13a-first1"), (4, "c13a-first4"), (40, "c13a-first40")):
    cw, burst = start(name); c13.append({"check": "13a", "run": name, "predicted_bytes": n_seg * SEG, "first_window_bytes": cw, "first_burst_bytes": burst, "pass": cw == n_seg * SEG == burst})
cw, burst = start("c13b-first-not-given"); c13.append({"check": "13b", "run": "c13b-first-not-given", "predicted_bytes": 10 * SEG, "first_window_bytes": cw, "first_burst_bytes": burst, "pass": cw == 10 * SEG == burst})
s = same("c13c-first10", "c13c-defaults"); c13.append({"check": "13c", "identical": s, "pass": all(s.values())})
g1, g40 = met("c13d-first1-10s")["tcp_goodput_bps"], met("c13d-first40-10s")["tcp_goodput_bps"]; c13.append({"check": "13d", "goodput_first1_bps": g1, "goodput_first40_bps": g40, "difference_percent": round(100 * abs(g1 - g40) / g40, 4), "pass": abs(g1 - g40) / g40 < 0.01})
c14 = []
ga, gb = met("c14a-buf64k")["tcp_goodput_bps"], met("c14b-buf256k")["tcp_goodput_bps"]; ba, bb = 8 * 65536 / 0.020, 8 * 262144 / 0.020
c14.append({"check": "14a", "bound_bps": ba, "goodput_bps": ga, "share_of_bound": round(ga / ba, 4), "pass": 0.4 * ba <= ga <= ba})
c14.append({"check": "14b", "bound_bps": bb, "goodput_bps": gb, "share_of_bound": round(gb / bb, 4), "ratio_to_14a": round(gb / ga, 3), "pass": 0.4 * bb <= gb <= bb and 3 <= gb / ga <= 4.5})
s = same("c14c-buf1m", "c14c-defaults"); c14.append({"check": "14c", "identical": s, "pass": all(s.values())})
for name, checks, keys in (("check13.json", c13, ("13a", "13b", "13c", "13d")), ("check14.json", c14, ("14a", "14b", "14c"))):
    (OUT / name).write_text(json.dumps({"predicted_before_the_run": {k: PREDICTED[k] for k in keys}, "checks": checks}, indent=1) + "\n")
    for c in checks: print(json.dumps(c))
    print(name[:-5].replace("check", "check "), "pass" if all(c["pass"] for c in checks) else "FAIL")
