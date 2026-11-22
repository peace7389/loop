"""Taps: the researcher names any trace source of the network's ns-3 objects and gets it recorded (2026-11-22, the operator: flexible, creative
measurements on demand). On a copy of the real s048's run r010 (a sender, a receiver, a scheduler, UDP and TCP), with the program net-taps:
  - trace_points(run_id) lists every object a tap can name (devices and their transmit queues, queue discs, IPv4, TCP sockets, applications,
    the channel) with each trace source, as a value or an event; it costs no simulation;
  - probe(run_id, every, taps={name: path}) records them in probe.csv (tap_<name>, tap_<name>_n, tap_<name>_bytes), and the simulation run again
    with them gives its measures and its series byte for byte as before; the answer says how each tap was connected, or why not;
  - measure reads a tap's columns like any other (the device's bytes sent per 10 ms make 1 Gbps, the link's rate);
  - a wrong tap is refused with its reason (an unknown trace source, a path that names two objects), a malformed request and a two-host
    simulation are refused before anything runs; a probe without taps still uses the program net.
Real ns-3 runs of the 10 s simulation (about 20 s each).     python3 -I test_taps.py SCRATCH_DIR [HARNESS_DIR]"""
import json, os, shutil, sys
from pathlib import Path
REAL = Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions/s048/runs").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
for r in ("r010",): shutil.copytree(REAL / "sessions/s048/runs" / r, P / "sessions/s048/runs" / r, ignore=shutil.ignore_patterns("probe.csv", "taps.json", "trace_points.json"))
shutil.copy(REAL / "sessions/s048/session.json", P / "sessions/s048/session.json"); shutil.copy(REAL / "sessions/s048/runs/index.json", P / "sessions/s048/runs/index.json")
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import tools
tools.SESSION = P / "sessions/s048"; tools.BRIEF = json.loads((P / "sessions/s048/session.json").read_text())["given"]; tools.POLICY = "share"
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
print("TAPS")
tp = tools.trace_points("r010"); lines = tp.splitlines()
say("TcpL4Protocol/SocketList/0  (ns3::TcpSocketBase)" in tp and "CongestionWindow [value]" in tp and "MacTx [event]" in tp and "RootQueueDiscList/1  (ns3::FlowQueueDisc)" in tp and "/ChannelList/0" in tp and len(lines) >= 10,
    f"trace_points lists {len(lines) - 1} objects of the network, the sender's TCP socket among them, each trace source as a value or an event")
taps = {"cwnd": "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow", "mactx": "/NodeList/0/DeviceList/1/MacTx", "sojourn": "/NodeList/0/$ns3::TrafficControlLayer/RootQueueDiscList/1/SojournTime",
        "retx": "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/Retransmission", "bad": "/NodeList/0/DeviceList/1/NoSuchThing", "two": "/NodeList/*/DeviceList/1/MacTx"}
pr = json.loads(tools.probe("r010", 0.01, taps=taps)); k = {t["name"]: t for t in pr.get("taps", [])}
say(pr["same_result"] and {"tap_cwnd", "tap_mactx_n", "tap_mactx_bytes", "tap_sojourn", "tap_retx_n"} <= set(pr["columns"]) and k["cwnd"]["kind"] == "value" and k["mactx"]["kind"] == "event" and k["sojourn"]["kind"] == "time event"
    and k["retx"]["kind"] == "event" and k["bad"]["kind"] == "refused" and "has no trace source NoSuchThing" in k["bad"]["said"] and k["two"]["kind"] == "refused" and "names 2 objects" in k["two"]["said"],
    f"probe with 6 taps: the same result as before ({pr['same_result']}); {[(n, t['kind']) for n, t in k.items()]}; the refusals say why (“{k['bad']['said'][:60]}…”)")
rate = json.loads(tools.measure("r010", "tap_mactx_bytes * 8 / 0.01", "mean")); cw = json.loads(tools.measure("r010", "tap_cwnd", "mean")); so = json.loads(tools.measure("r010", "tap_sojourn", "p95"))
say(0.97e9 < rate["value"] < 1.03e9 and cw["value"] > 1000 and so["value"] > 0, f"measure reads the taps: the device sends {rate['value'] / 1e9:.3f} Gbps (its rate is 1 Gbps), TCP's window {cw['value']:.0f} bytes on average, packets wait {so['value']} ms (p95) in the scheduler")
e1, e2 = tools.probe("r010", 0.01, taps={"Bad Name": "/x"}), tools.probe("r010", 0.01, taps={f"t{i}": "/NodeList/0/DeviceList/1/MacTx" for i in range(9)})
say(e1.startswith("error: taps is {name: path}") and e2.startswith("error: taps is {name: path}"), f"a malformed request is refused before anything runs: “{e1[:80]}…”")
plain = json.loads(tools.probe("r010", 0.01)); src = (P / "harness/tools.py").read_text()
say(plain["same_result"] and not any(c.startswith("tap_") for c in plain["columns"]) and "NET_TAPS_BIN if taps else NET_BIN" in src, "a probe without taps runs the program net as before, and its record has no tap column")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
