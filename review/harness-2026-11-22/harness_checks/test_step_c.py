"""The harness side of ~/project/NOTEBOOK_VIEW.md, Part 3, Step C (new settings of the simulator), as scripted
sessions in a scratch copy. One block per setting, added as the settings are added.
  1. separate queue lengths: queuePktsUdp, queuePktsTcp (a brief may leave them out; then nothing changes)
  2. TCP's first window and TCP's buffers: tcpInitCwnd, tcpBufBytes (build 6; left out, the program does what it did)
  3. the device's transmit queue: devQueuePkts (build 7; left out, it holds 10 packets as before)
    python3 -I test_step_c.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new. Simulations are real ns-3 runs."""
import json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
ENV = {**os.environ, "HOME": str(SCR / "home")}
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, brief, answers, *flags):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps(answers))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env=ENV, capture_output=True, text=True, timeout=1200)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    led = [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
    return led, json.loads((P / "sessions" / sid / "session.json").read_text())
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led, turn: [(r["body"].get("part"), r["body"].get("reason")) for r in of(led, "note", turn) if "part" in r["body"]]
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def ex(runs, varied, question="what the settings do"): return {"kind": "explore", "tests": [], "question": question, "varied": list(varied), "control": None, "runs": runs, "decision_rules": []}
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import importlib; tools = importlib.import_module("tools"); loop = importlib.import_module("loop")
base = json.loads((REAL / "briefs/two-hosts-open.json").read_text())
def save(bid, change):
    b = json.loads(json.dumps(base)); b["id"] = bid; change(b); (P / "briefs" / f"{bid}.json").write_text(json.dumps(b, indent=1) + "\n"); return tools.load_brief(bid)
def params_of(sid, sims): return {l: json.loads((P / "sessions" / sid / "runs" / sims[l]["run_id"] / "params.json").read_text()) for l in sims if not sims[l].get("same_as")}
def fmt_of(b): return loop.answer_format(json.loads((P / "harness/schema.json").read_text()), b)["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["params"]

# ================================================================== 1. separate queue lengths
print("SEPARATE QUEUE LENGTHS  (Step C, setting 1)")
NINE = ("linkRate", "linkDelay", "mtu", "udpRate", "tcpVariant", "queuePkts", "duration", "seed", "weightUdp")
# "old" = the briefs on disk that state none of the settings added since build 4 (the operator's own briefs may state them: those are not the subject of these lines)
every = {p.stem: tools.load_brief(p.stem) for p in sorted((REAL / "briefs").glob("*.json"))}
old = {k: b for k, b in every.items() if "topology" not in b and not set(tools.EXTRA) & (set(b.get("system") or {}) | set(b.get("knobs") or {}))}   # a brief with a network has its own program and options (test_network.py)
assert {"two-hosts-open", "two-hosts-udp-demand"} <= set(old), sorted(old)
say(all(tuple(sorted(tools.options({}, b))) == tuple(sorted(NINE)) for b in old.values()) and all(set(fmt_of(b)["required"]) == set(b["knobs"]) for b in old.values()),
    f"the {len(old)} briefs that state none of the later settings (of {len(every)} on disk) are accepted as they are, and a simulation on them is started with the same nine options as before (no queuePktsUdp, no queuePktsTcp)")
QUEUE = {"min": 4, "max": 1000, "default": 100}
def queues(b):
    b["system"]["queuePkts"] = b["knobs"].pop("queuePkts")["default"]
    b["knobs"]["queuePktsUdp"] = {**QUEUE, "meaning": "most packets the UDP queue holds"}; b["knobs"]["queuePktsTcp"] = {**QUEUE, "meaning": "most packets the TCP queue holds"}
    b["description"] = b["description"].replace("Each queue holds at most queuePkts packets", "The UDP queue holds at most queuePktsUdp packets and the TCP queue at most queuePktsTcp packets")
bq = save("t-queues", queues); fmt = fmt_of(bq)
say("queuePktsUdp packets and the TCP queue" in bq["description"], "the test's brief says in its description that each queue has its own length (the text of the existing briefs was found and replaced)")
say(fmt["required"] == list(bq["knobs"]) and fmt["properties"]["queuePktsUdp"] == {"type": "integer"} and fmt["properties"]["queuePktsTcp"] == {"type": "integer"} and "queuePkts" not in fmt["properties"],
    f"a brief with both lengths as knobs: the answer format requires both in every design: {fmt['required']}")
K = dict(weightUdp=0.5, udpRate="2Gbps", tcpVariant="TcpCubic", duration=2, seed=1)
led, meta = session("q1", "t-queues", [turn(experiment=ex([{"label": "short_udp", "params": {**K, "queuePktsUdp": 20, "queuePktsTcp": 200}}, {"label": "short_tcp", "params": {**K, "queuePktsUdp": 200, "queuePktsTcp": 20}},
                                                              {"label": "outside", "params": {**K, "queuePktsUdp": 5000, "queuePktsTcp": 1}}, {"label": "one_only", "params": {**K, "queuePktsUdp": 50}}], ["queuePktsUdp", "queuePktsTcp"]))])
x = of(led, "experiment", 1)[0]["body"]; runs = {r["label"]: r for r in x["runs"]}; sims = {r["body"]["label"]: r["body"] for r in of(led, "simulation", 1)}; n = notes(led, 1); used = params_of("q1", sims)
say(list(runs) == ["short_udp", "short_tcp", "outside"] and ("design one_only", "design `one_only` does not state `queuePktsTcp`") in n, f"a scripted session on it: every accepted design states both lengths; the design that states one only is refused: {[q for q in n if q[0] == 'design one_only']}")
say(all((used[l].get("queuePktsUdp"), used[l].get("queuePktsTcp")) == w for l, w in (("short_udp", (20, 200)), ("short_tcp", (200, 20)), ("outside", (1000, 4)))) and all(sims[l]["params"].get("queuePktsUdp") == used[l]["queuePktsUdp"] for l in used),
    f"the simulator ran with them, and the simulation records say so (params.json: { {l: (u.get('queuePktsUdp'), u.get('queuePktsTcp')) for l, u in used.items()} })")
say(runs["outside"]["clamped"] == {"queuePktsUdp": [5000, 1000], "queuePktsTcp": [1, 4]}, f"lengths outside the range are clamped and recorded: {runs['outside']['clamped']}")
d = {l: sims[l]["metrics"]["drops_band1"] for l in ("short_udp", "short_tcp")}
say(d["short_tcp"] > d["short_udp"], f"the lengths reach the simulation: with a TCP queue of 20 instead of 200, TCP's queue drops {d['short_tcp']} packets instead of {d['short_udp']}")
base0 = [r["body"] for r in of(led, "simulation") if r["body"].get("label") == "default"]
say(len(base0) == 1 and (base0[0]["params"].get("queuePktsUdp"), base0[0]["params"].get("queuePktsTcp")) == (100, 100), f"the harness's own baseline runs at the knobs' defaults and records them: {[(b['params'].get('queuePktsUdp'), b['params'].get('queuePktsTcp')) for b in base0]}")
# one queue only, the other keeps the common length
def one(b): b["knobs"]["queuePktsTcp"] = {**QUEUE, "meaning": "most packets the TCP queue holds; the UDP queue holds queuePkts"}
bo = save("t-queue-tcp", one)
say("queuePkts" in bo["knobs"] and "queuePktsTcp" in bo["knobs"] and tools.options({}, bo).get("queuePktsTcp") == 100 and "queuePktsUdp" not in tools.options({}, bo), "a brief may give one queue its own length and leave the other with the common one (queuePkts stays a knob there)")
def fixed(b): b["system"]["queuePktsTcp"] = 20; b["description"] = b["description"].replace("Each queue holds at most queuePkts packets", "The UDP queue holds at most queuePkts packets and the TCP queue {queuePktsTcp}")
bf = save("t-queue-fixed", fixed)
c, cl = tools.clamp({"queuePktsTcp": 300, "weightUdp": 0.4}, bf)
say("the TCP queue 20" in bf["description"] and tools.options({}, bf)["queuePktsTcp"] == 20 and "queuePktsTcp" not in c and cl == {"queuePktsTcp": [300, 20]}, f"as a fixed setting it is filled into the description, goes to every simulation, and is not the model's to change: {cl}")
bad = []
for what, ch in (("the common length as a knob when both queues have their own", lambda b: (queues(b), b["knobs"].update(queuePkts={**QUEUE, "meaning": "x"}), b["system"].pop("queuePkts"))),
                 ("a length of 0", lambda b: b["system"].update(queuePktsUdp=0)), ("a length that is a text", lambda b: b["system"].update(queuePktsUdp="20p")),
                 ("fixed and a knob at once", lambda b: (one(b), b["system"].update(queuePktsTcp=20))), ("a step that is not whole", lambda b: (one(b), b["knobs"]["queuePktsTcp"].update(step=0.5))),
                 ("a setting the program does not have", lambda b: b["system"].update(queuePktsAck=5))):
    try: save("t-bad", ch); bad.append(what)
    except ValueError: pass
say(not bad, "refused: the common length as a knob when both queues have their own (it would change nothing), a length of 0, a text, fixed and knob at once, a step that is not whole, an unknown setting" + (f": accepted {bad}" if bad else ""))
def stepped(b): one(b); b["knobs"]["queuePktsTcp"]["step"] = 10
bs = save("t-queue-step", stepped); c, cl = tools.clamp({"queuePktsTcp": 37}, bs)
say(c == {"queuePktsTcp": 34} and cl == {"queuePktsTcp": [37, 34]}, f"a step works on it as on the other whole-number knobs (counted from the knob's min, 4): {cl}")
# ================================================================== 2. TCP's first window and TCP's buffers (build 6)
print("TCP'S FIRST WINDOW AND TCP'S BUFFERS  (settings of build 6)")
say(all(not {"tcpInitCwnd", "tcpBufBytes"} & set(tools.options({}, b)) for b in old.values()), f"the {len(old)} briefs that state none of the later settings start a simulation without tcpInitCwnd and without tcpBufBytes: the program does what it did before them")
WIN, BUF = {"min": 1, "max": 100, "default": 10, "meaning": "TCP's first window: the segments it sends before its first acknowledgement"}, {"min": 65536, "max": 4194304, "default": 1048576, "meaning": "TCP's send buffer and its receive buffer, in bytes each"}
def tcp(b): b["knobs"]["tcpInitCwnd"] = dict(WIN); b["knobs"]["tcpBufBytes"] = dict(BUF); b["system"]["linkDelay"] = "10ms"  # a round trip of 20 ms, so that a buffer of 65,536 bytes limits TCP (at most 26.2 Mbps)
bt = save("t-tcp", tcp); fmt = fmt_of(bt)
say(fmt["required"] == list(bt["knobs"]) and fmt["properties"]["tcpInitCwnd"] == {"type": "integer"} and fmt["properties"]["tcpBufBytes"] == {"type": "integer"}, f"a brief with both as knobs: the answer format requires both in every design, as whole numbers: {fmt['required'][-2:]}")
led, meta = session("c1", "t-tcp", [turn(experiment=ex([{"label": "small_buf", "params": {**K, "queuePkts": 100, "tcpInitCwnd": 10, "tcpBufBytes": 65536}}, {"label": "large_buf", "params": {**K, "queuePkts": 100, "tcpInitCwnd": 10, "tcpBufBytes": 1048576}},
                                                           {"label": "one_segment", "params": {**K, "queuePkts": 100, "tcpInitCwnd": 1, "tcpBufBytes": 1048576}}, {"label": "outside", "params": {**K, "queuePkts": 100, "tcpInitCwnd": 500, "tcpBufBytes": 100}},
                                                           {"label": "one_only", "params": {**K, "queuePkts": 100, "tcpInitCwnd": 4}}], ["tcpInitCwnd", "tcpBufBytes"]))])
x = of(led, "experiment", 1)[0]["body"]; runs = {r["label"]: r for r in x["runs"]}; sims = {r["body"]["label"]: r["body"] for r in of(led, "simulation", 1)}; n = notes(led, 1); used = params_of("c1", sims)
say(list(runs) == ["small_buf", "large_buf", "one_segment", "outside"] and ("design one_only", "design `one_only` does not state `tcpBufBytes`") in n, f"a scripted session on it: every accepted design states both; the design that states one only is refused: {[q for q in n if q[0] == 'design one_only']}")
want = {"small_buf": (10, 65536), "large_buf": (10, 1048576), "one_segment": (1, 1048576), "outside": (100, 65536)}
say(all((used[l].get("tcpInitCwnd"), used[l].get("tcpBufBytes")) == w for l, w in want.items() if l in used) and all((sims[l]["params"].get("tcpInitCwnd"), sims[l]["params"].get("tcpBufBytes")) == w for l, w in want.items()),
    f"the simulator ran with them, and the simulation records say so (params.json: { {l: (u.get('tcpInitCwnd'), u.get('tcpBufBytes')) for l, u in used.items()} })")
say(runs["outside"]["clamped"] == {"tcpInitCwnd": [500, 100], "tcpBufBytes": [100, 65536]}, f"values outside the range are clamped and recorded: {runs['outside']['clamped']}")
g = {l: sims[l]["metrics"]["tcp_goodput_bps"] for l in ("small_buf", "large_buf")}
say(g["small_buf"] <= 8 * 65536 / 0.020 and g["large_buf"] > 3 * g["small_buf"], f"the buffer reaches the simulation: with 65,536 bytes and a round trip of 20 ms TCP's goodput is {g['small_buf'] / 1e6:.1f} Mbps (the window cannot exceed the buffer: at most 26.2), with 1 MB {g['large_buf'] / 1e6:.1f} Mbps")
base0 = [r["body"] for r in of(led, "simulation") if r["body"].get("label") == "default"]
say(len(base0) == 1 and (base0[0]["params"].get("tcpInitCwnd"), base0[0]["params"].get("tcpBufBytes")) == (10, 1048576), f"the harness's own baseline runs at the knobs' defaults and records them: {[(b['params'].get('tcpInitCwnd'), b['params'].get('tcpBufBytes')) for b in base0]}")
def tfixed(b): b["system"]["tcpBufBytes"] = 262144; b["system"]["tcpInitCwnd"] = 4
bf = save("t-tcp-fixed", tfixed); c, cl = tools.clamp({"tcpBufBytes": 65536, "weightUdp": 0.4}, bf); o = tools.options({}, bf)
say((o["tcpBufBytes"], o["tcpInitCwnd"]) == (262144, 4) and "tcpBufBytes" not in c and cl == {"tcpBufBytes": [65536, 262144]}, f"as fixed settings they go to every simulation and are not the model's to change: {cl}")
bad = []
for what, ch in (("a first window of 0", lambda b: b["system"].update(tcpInitCwnd=0)), ("a buffer below 4,096 bytes", lambda b: b["system"].update(tcpBufBytes=1000)), ("a buffer that is a text", lambda b: b["system"].update(tcpBufBytes="1MB")),
                 ("a first window that is not whole", lambda b: b["system"].update(tcpInitCwnd=2.5)), ("fixed and a knob at once", lambda b: (tcp(b), b["system"].update(tcpInitCwnd=4))),
                 ("a knob whose least value the program refuses", lambda b: (tcp(b), b["knobs"]["tcpBufBytes"].update(min=100)))):
    try: save("t-bad", ch); bad.append(what)
    except ValueError: pass
say(not bad, "refused: a first window of 0, a buffer below 4,096 bytes, a text, a window that is not whole, fixed and knob at once, a knob whose least value the program refuses" + (f": accepted {bad}" if bad else ""))
# ================================================================== 3. the device's transmit queue (build 7)
print("THE DEVICE'S TRANSMIT QUEUE  (setting of build 7)")
say(all("devQueuePkts" not in tools.options({}, b) for b in old.values()), f"the {len(old)} briefs that state none of the later settings start a simulation without devQueuePkts: the program does what it did before it")
DEV = {"min": 1, "max": 1000, "default": 10, "meaning": "most packets a device's transmit queue holds; they wait there after the scheduler has chosen them"}
def dev(b): b["knobs"]["devQueuePkts"] = dict(DEV)
bd = save("t-dev", dev); fmt = fmt_of(bd)
say(fmt["required"] == list(bd["knobs"]) and fmt["properties"]["devQueuePkts"] == {"type": "integer"}, f"a brief with it as a knob: the answer format requires it in every design, as a whole number: {fmt['required'][-1:]}")
led, meta = session("d1", "t-dev", [turn(experiment=ex([{"label": "one", "params": {**K, "queuePkts": 100, "devQueuePkts": 1}}, {"label": "long", "params": {**K, "queuePkts": 100, "devQueuePkts": 400}},
                                                           {"label": "outside", "params": {**K, "queuePkts": 100, "devQueuePkts": 5000}}, {"label": "left_out", "params": {**K, "queuePkts": 100}}], ["devQueuePkts"]))])
x = of(led, "experiment", 1)[0]["body"]; runs = {r["label"]: r for r in x["runs"]}; sims = {r["body"]["label"]: r["body"] for r in of(led, "simulation", 1)}; n = notes(led, 1); used = params_of("d1", sims)
say(list(runs) == ["one", "long", "outside"] and ("design left_out", "design `left_out` does not state `devQueuePkts`") in n, f"a scripted session on it: every accepted design states it; the design that leaves it out is refused: {[q for q in n if q[0] == 'design left_out']}")
say(all(used[l].get("devQueuePkts") == w and sims[l]["params"].get("devQueuePkts") == w for l, w in (("one", 1), ("long", 400), ("outside", 1000))) and runs["outside"]["clamped"] == {"devQueuePkts": [5000, 1000]},
    f"the simulator ran with it, the simulation records say so, and a value outside the range is clamped and recorded (params.json: { {l: u.get('devQueuePkts') for l, u in used.items()} }; {runs['outside']['clamped']})")
base0 = [r["body"] for r in of(led, "simulation") if r["body"].get("label") == "default"]
say(len(base0) == 1 and base0[0]["params"].get("devQueuePkts") == 10, f"the harness's own baseline runs at the knob's default and records it: {[b['params'].get('devQueuePkts') for b in base0]}")
def dfixed(b): b["system"]["devQueuePkts"] = 50
bf = save("t-dev-fixed", dfixed); c, cl = tools.clamp({"devQueuePkts": 5, "weightUdp": 0.4}, bf)
say(tools.options({}, bf)["devQueuePkts"] == 50 and "devQueuePkts" not in c and cl == {"devQueuePkts": [5, 50]}, f"as a fixed setting it goes to every simulation and is not the model's to change: {cl}")
bad = []
for what, ch in (("a length of 0", lambda b: b["system"].update(devQueuePkts=0)), ("a text", lambda b: b["system"].update(devQueuePkts="10p")), ("fixed and a knob at once", lambda b: (dev(b), b["system"].update(devQueuePkts=4)))):
    try: save("t-bad", ch); bad.append(what)
    except ValueError: pass
say(not bad, "refused: a length of 0, a text, fixed and knob at once" + (f": accepted {bad}" if bad else ""))
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
