"""A brief with a network (TOPOLOGY.md, stage 2; 2026-11-17): hosts, links, flows and queues as data in the brief's
"topology", run by the program `net`. Its settings are addressed object.property, its measures are made from it.
  - the brief check accepts a three-host brief and refuses, with the reason: a knob that is no setting of the network,
    a goal that names a measure the network does not have, a flow without a way, a network setting put into system,
    a scheduler without a part for a flow that passes it, two equally short ways, a second link between two hosts;
  - the task sentence, the description's names in braces, the answer format (knobs by address, the report's expected
    values by the network's measures), clamping (a knob into its range, a fixed network setting back to its value);
  - a scripted session: the baseline and a test of four simulations run through `net` (each run folder holds the
    network as the program read it), the harness checks a rule that compares one flow in two simulations and a rule
    that compares two flows in one, the report by address is accepted;
  - an operator simulation and a small sweep on that brief through control.py;
  - a flow's application (OnOff, BulkSend) and its socket (UDP, TCP) are two choices: OnOff over TCP is accepted, simulated and
    gives the operator's figure; BulkSend over UDP is refused with ns-3's reason; a flow without an application is written as before;
  - a brief without a network is checked, clamped and started exactly as before.
    python3 -I test_network.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new. Simulations are real runs of `net`, 2 measured seconds each."""
import copy, json, os, shutil, subprocess, sys, time
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
T = {"hosts": [{"id": "a"}, {"id": "b"}, {"id": "r"}, {"id": "c"}],
     "links": [{"id": "la", "between": ["a", "r"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10},
               {"id": "lb", "between": ["b", "r"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10},
               {"id": "lc", "between": ["r", "c"], "rate": "100Mbps", "delay": "1ms", "mtu": 1500, "device_queue": 10,
                "queue": {"on": "r", "kind": "scheduler", "length": 100, "parts": {"fa": 0.5, "fb": 0.5}}}],
     "flows": [{"id": "fa", "kind": "tcp", "from": "a", "to": "c", "type": "TcpCubic"}, {"id": "fb", "kind": "udp", "from": "b", "to": "c", "rate": "80Mbps", "packet_bytes": 1400}]}
B = {"id": "three", "description": "Two senders, a and b, reach c through r. The link from r to c carries {lc.rate}; flow fb offers {fb.rate}; r gives flow fa the part {lc.queue.parts.fa} of that link, against 0.5 for fb.",
     "topology": T, "system": {"seed": 1},
     "knobs": {"lc.queue.parts.fa": {"min": 0.05, "max": 4, "default": 0.5, "meaning": "the part of link lc for flow fa (fb's part is 0.5; the parts are divided by their sum)"},
               "fa.type": {"choices": ["TcpCubic", "TcpBbr"], "default": "TcpCubic", "meaning": "TCP congestion control of flow fa"},
               "duration": {"min": 2, "max": 10, "default": 2, "meaning": "seconds of measured traffic"}},
     "goal": {"kind": "given", "target": {"measure": "fa_goodput_bps", "direction": "max"}, "conditions": ["fb_loss_frac <= 0.5"]},
     "limits": {"simulations": 12, "simulations_per_experiment": 4}}
(P / "briefs/three.json").write_text(json.dumps(B))
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import tools, network, loop
print("A BRIEF WITH A NETWORK")
g = tools.load_brief("three")
say(g["task"] == "Find the settings that give the largest fa_goodput_bps, while fb_loss_frac <= 0.5. You may change 3 settings (lc.queue.parts.fa, fa.type, duration); every other setting is fixed. Explain why they are best."
    and "carries 100Mbps; flow fb offers 80Mbps; r gives flow fa the part the knob lc.queue.parts.fa" in g["description"], f"the three-host brief is accepted; its task: “{g['task'][:95]}…”; a name in braces is a fixed setting's value or “the knob …”")
def refused(change):
    x = copy.deepcopy(B); change(x)
    try: tools.check_brief(x, "three"); return ""
    except ValueError as e: return str(e)
cases = {"a knob that is no setting of the network": (lambda x: x["knobs"].update({"zz.rate": {"min": "1Mbps", "max": "2Mbps", "default": "1Mbps", "meaning": "m"}}), "'zz.rate' is not a setting of this network"),
         "a goal that names a measure the network does not have": (lambda x: x["goal"]["target"].update(measure="tcp_goodput_bps"), "a measure that is one of the outputs"),
         "a flow without a way": (lambda x: x["topology"]["links"].pop(1), "there is no way from b to c"),
         "a network setting in system": (lambda x: x["system"].update({"lc.rate": "1Gbps"}), "its fixed value stands in the network"),
         "a scheduler without a part for a flow that passes it": (lambda x: x["topology"]["links"][2]["queue"]["parts"].pop("fb"), "has no part for fb"),
         "two equally short ways": (lambda x: (x["topology"]["hosts"].append({"id": "s"}), x["topology"]["links"].extend([{"id": "ls", "between": ["a", "s"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10}, {"id": "lt", "between": ["s", "c"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10}])), "equally short ways"),
         "a second link between two hosts": (lambda x: x["topology"]["links"].append({"id": "lz", "between": ["r", "a"], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10}), "joined by a link already"),
         "nine hosts": (lambda x: x["topology"]["hosts"].extend({"id": f"h{i}"} for i in range(5)), "at most 8")}
got = {k: refused(c) for k, (c, w) in cases.items()}
say(all(w in got[k] for k, (c, w) in cases.items()), f"refused with the reason: {', '.join(cases)}" + "".join(f" [{k}: {got[k][:80]}]" for k, (c, w) in cases.items() if w not in got[k]))
fmt = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), g)
params = fmt["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["params"]; exp = fmt["properties"]["report"]["anyOf"][0]["properties"]["expected"]["properties"]
say(params["properties"] == {"lc.queue.parts.fa": {"type": "number"}, "fa.type": {"type": "string", "enum": ["TcpCubic", "TcpBbr"]}, "duration": {"type": "number"}} and params["required"] == list(g["knobs"]) and list(exp) == list(network.outputs(T)) and "udp_goodput_bps" not in exp,
    f"the answer format: a design states the three knobs by address; the report's expected values are by the network's {len(exp)} measures ({', '.join(list(exp)[:4])}, …)")
clean, clamps = tools.clamp({"lc.queue.parts.fa": 9, "fa.type": "TcpVegas", "duration": 3, "lc.rate": "1Gbps"}, g, design="x")
say(clean == {"lc.queue.parts.fa": 4, "fa.type": "TcpCubic", "duration": 3} and clamps == {"lc.rate": ["1Gbps", "100Mbps"], "lc.queue.parts.fa": [9, 4], "fa.type": ["TcpVegas", "TcpCubic"]},
    f"clamping: a knob into its range, a choice that is not offered back to the default, and a setting the network fixes back to its value, each recorded: {clamps}")

# ---- a scripted session
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def d(label, part, **over): return {"label": label, "params": {"lc.queue.parts.fa": part, "fa.type": "TcpCubic", "duration": 2, **over}}
H = lambda text, q: {"text": text, "question": q, "why": "It says which setting moves the goal.", "prediction": "more", "follows_from": ["brief"]}
ANSWERS = [turn(hypotheses=[H("A larger part gives fa more", "Does flow fa get more when its part is larger?"), H("With equal parts the UDP flow gets less than it offers", "Does fb lose packets when it has half of the link?"), H("fa delivers with BBR too", "Does fa deliver with the other TCP kind?")],
                experiment={"kind": "test", "tests": ["H1", "H2", "H3"], "question": "", "varied": ["lc.queue.parts.fa"], "control": "even", "runs": [d("small", 0.125), d("even", 0.5), d("large", 2), d("bbr", 0.5, **{"fa.type": "TcpBbr"})],
                            "decision_rules": [{"for": "H1", "decision_rule": "fa_goodput_bps@large > 1.5 * fa_goodput_bps@small", "rival": "the parts do nothing", "rival_predicts": "failed"},
                                               {"for": "H2", "decision_rule": "fb_goodput_bps@even < 0.8 * 80000000 AND fb_goodput_bps@even > fa_goodput_bps@small", "rival": "fb gets all it offers", "rival_predicts": "failed"},
                                               {"for": "H3", "decision_rule": "fa_goodput_bps@bbr > 0.1 * fa_goodput_bps@even", "rival": "BBR stalls behind the scheduler", "rival_predicts": "failed"}]}),  # each design serves a hypothesis (the chain of 2026-11-17): bbr and even differ in fa.type alone
           turn(verdicts=[{"for": "H1", "result": "supported", "because": "C1 held: the larger part gave fa four times as much.", "next": "report"}, {"for": "H2", "result": "supported", "because": "C2 held.", "next": "report"}, {"for": "H3", "result": "supported", "because": "C3 held.", "next": "report"}],
                report={"goal": "the largest goodput of fa while fb loses at most half", "recommendation": {"lc.queue.parts.fa": 2, "fa.type": "TcpCubic", "duration": 2},
                        "expected": {"fa_goodput_bps": 77000000.0, "fb_loss_frac": 0.76}, "no_difference": [], "limit": "The 100 Mbps link from r to c: E1.",
                        "explanation": "fa's goodput follows its part of the bottleneck link.", "holds_when": "as tested", "breaks_when": "other rates",
                        "claims": [{"text": "A larger part gives fa more.", "role": "supports", "evidence": ["C1"]}], "open_questions": []}, done=True)]
f = SCR / "n1.answers.json"; f.write_text(json.dumps(ANSWERS))
r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "three", "--session", "n1"], env=ENV, capture_output=True, text=True, timeout=1200)
if r.returncode: print(r.stdout[-600:], r.stderr[-2500:])
led = [json.loads(l) for l in (P / "sessions/n1/ledger.jsonl").read_text().splitlines() if l.strip()]; meta = json.loads((P / "sessions/n1/session.json").read_text())
of = lambda ty: [x for x in led if x["type"] == ty]
sims = of("simulation"); runs = sorted(p.name for p in (P / "sessions/n1/runs").iterdir() if p.is_dir())
say(len(sims) == 5 and all("metrics" in s["body"] for s in sims) and len(runs) == 4 and sum(bool(s["body"].get("same_as")) for s in sims) == 1 and all((P / "sessions/n1/runs" / x / "network.txt").is_file() and (P / "sessions/n1/runs" / x / "series.csv").is_file() for x in runs),
    f"the baseline and the test's simulations ran through `net`: {len(runs)} run folders, each with the network as the program read it (the design that equals the baseline was not run again: its result was returned)" + (f" {[s['body'].get('error', '')[:200] for s in sims if 'metrics' not in s['body']]}" if any('metrics' not in s['body'] for s in sims) else ""))
m = {s["body"]["label"]: s["body"]["metrics"] for s in sims if "metrics" in s["body"] and s["body"].get("label")}
txt = next((t for t in ((P / "sessions/n1/runs" / x / "network.txt").read_text() for x in runs) if "parts=fa:2" in t), "")
say("parts=fa:2,fb:0.5" in txt or "parts=fa:2.0,fb:0.5" in txt, f"the design “large” reached the program as a network with fa's part at 2: “{([l for l in txt.splitlines() if l.startswith('queue')] or ['not found'])[0]}”")
ck = {c["body"]["for"]: c["body"] for c in of("check")}
say(set(ck) == {"H1", "H2", "H3"} and ck["H1"]["result"] == "held" and ck["H2"]["result"] == "held" and m and m["large"]["fa_goodput_bps"] > 1.5 * m["small"]["fa_goodput_bps"],
    f"the harness checked both rules from the measured values: H1 {ck.get('H1', {}).get('result')} ({ck.get('H1', {}).get('with_numbers', '')[:70]}), H2, which compares two flows in one simulation, {ck.get('H2', {}).get('result')}")
ev = of("evidence")[-1]["body"]; line = json.dumps(ev)
say("fa_goodput_bps=" in line and "lc_drops_fb=" in line and "udp_goodput_bps" not in line, "the evidence lines give the network's measures by their names (fa_goodput_bps, lc_drops_fb, …) and none of two-hosts")
say(meta.get("how") == "done by the model" and len(of("report")) == 1 and list(meta["given"]["outputs"]) == list(network.outputs(T)) and meta["given"]["topology"] == T,
    f"the report by address is accepted and ends the session (“{meta.get('how')}”); session.json holds the network and its measures")
told = json.dumps(meta["given"]["tools"]) + meta["prompt"]
say("<flow>_bps" in meta["given"]["tools"]["series"] and "grep_trace" not in meta["given"]["tools"] and not any(w in told for w in ("udp_bps", "drops_band0", "q_band0")),
    "what the session is told about its tools names the series by the network's columns and offers no packet trace; nothing it is given names a column of two-hosts")

# ---- the operator's simulation and a small sweep on the brief
import control
rec = control.operator_run({"brief": "three", "policy": "share", "params": {"lc.queue.parts.fa": 1.5, "duration": 2}})
say(rec["params"]["lc.queue.parts.fa"] == 1.5 and rec["metrics"]["fa_goodput_bps"] > 0 and (P / "checks" / rec["id"] / "network.txt").is_file(), f"an operator simulation on the brief runs through `net` ({rec['id']}: fa {rec['metrics']['fa_goodput_bps'] / 1e6:.1f} Mbps)")
st = control.start_sweep({"brief": "three", "policy": "cap", "grid": {"lc.queue.parts.fa": [0.5, 1, 2], "duration": [2]}})
for _ in range(120):
    if control.sweep_status(st["id"])["state"] != "running": break
    time.sleep(1)
rows = (P / "checks/sweeps" / st["id"] / "table.csv").read_text().splitlines()
say(control.sweep_status(st["id"])["state"] == "done" and len(rows) == 4 and rows[0].startswith("i,seed,lc.queue.parts.fa,fa.type,duration,fa_goodput_bps") and all(not x.endswith(",") or x.count(",") for x in rows[1:]) and "error" in rows[0] and all(x.split(",")[-1] == "" for x in rows[1:]),
    f"a sweep of three parts under cap: a table of {len(rows) - 1} rows with the settings by address and the network's measures ({rows[0][:70]}…), no error")

# ---- a brief with a network saved from the page keeps its network; the third policy exists for a network only
form = copy.deepcopy(B); form["id"] = "three-saved"; form["structure"] = {"may_change": False}
r = control.save_brief({"brief": form}); disk = json.loads((P / "briefs/three-saved.json").read_text())
say(r["saved"] == "three-saved" and disk["topology"] == T and "task" not in disk and list(disk)[:3] == ["id", "description", "topology"] and tools.load_brief("three-saved")["task"] == g["task"].replace("three", "three"),
    "a brief with a network saved from the page keeps its network in its file, has no task of its own, and is read with the harness's sentence")
rp = control.operator_run({"brief": "three", "policy": "prio", "params": {"duration": 2}})
try: control.operator_run({"brief": "two-hosts-udp-demand-2", "policy": "prio", "params": {}}); refused = ""
except control.Refused as e: refused = e.text
say(rp["metrics"]["fa_goodput_bps"] > 60e6 and rp["metrics"]["fb_loss_frac"] > 0.5 and "share, cap" in refused and "prio" not in refused.split("one of")[-1],
    f"under prio the first flow of the scheduler's list (fa) takes the link whatever the parts ({rp['metrics']['fa_goodput_bps'] / 1e6:.1f} Mbps of 100; fb loses {100 * rp['metrics']['fb_loss_frac']:.0f} %); for a brief without a network prio is refused (“{refused[-60:]}”)")

# ---- the two ends of a link, and several flows in one queue of a scheduler (TOPOLOGY.md, stages N1 and N2; the second build of net, checks/net2)
print("THE TWO ENDS OF A LINK, AND SEVERAL FLOWS IN ONE QUEUE")
import copy
LK = lambda i, x, y, rate="1Gbps", delay="50us", **k: {"id": i, "between": [x, y], "rate": rate, "delay": delay, "mtu": 1500, "device_queue": 10, **k}
T2 = {"hosts": [{"id": h} for h in "abrc"],
      "links": [LK("la", "a", "r"), LK("lb", "b", "r"),
                LK("lc", "r", "c", "100Mbps", "1ms", ends={"r": {"queue": {"kind": "scheduler", "length": 100, "parts": {"one": 0.25, "fb": 0.75}, "largest_rate": {}, "classes": {"one": ["fa", "fd"]}}},
                                                          "c": {"rate": "50Mbps", "queue": {"kind": "fifo", "length": 50}}})],
      "flows": [{"id": "fa", "kind": "tcp", "from": "a", "to": "c", "type": "TcpCubic"}, {"id": "fd", "kind": "tcp", "from": "a", "to": "c", "type": "TcpCubic"}, {"id": "fb", "kind": "tcp", "from": "b", "to": "c", "type": "TcpCubic"}]}
B2 = {"id": "ends", "description": "Three TCP flows reach c through r. On r's side of the link r-c, fa and fd share one queue with the part {lc.r.queue.parts.one}; fb has its own. The device of c on that link sends at {lc.c.rate}.",
      "topology": T2, "system": {"seed": 1, "duration": 10},
      "knobs": {"lc.r.queue.parts.one": {"min": 0.05, "max": 4, "default": 0.25, "meaning": "the part of link lc for the queue fa and fd share (fb's part is 0.75)"},
                "lc.c.rate": {"min": "10Mbps", "max": "1Gbps", "default": "50Mbps", "meaning": "the rate of c's device on link lc (the way back)"}},
      "goal": {"kind": "open"}, "limits": {"simulations": 8, "simulations_per_experiment": 4}}
(P / "briefs/ends.json").write_text(json.dumps(B2)); g2 = tools.load_brief("ends"); outs2 = tools.outputs(g2); set2 = network.settings(T2)
say(not network.problems(T2) and {"lc_drops_one", "lc_drops_fb", "lc_drops_back"} <= set(outs2) and "lc_drops" not in outs2 and "share (class one)" in outs2["lc_drops_one"] and "rate of c's device" in outs2["lc_util_back"]
    and {"lc.rate", "lc.c.rate", "lc.r.queue.length", "lc.r.queue.parts.one", "lc.r.queue.parts.fb", "lc.c.queue.length"} <= set(set2) and "lc.queue.length" not in set2 and "the knob lc.r.queue.parts.one" in g2["description"],
    f"a brief whose link describes its two ends is accepted: a scheduler on r's side in which fa and fd share one queue (class one), a plain queue and a rate of its own on c's side; its settings by address ({[k for k in set2 if k.startswith('lc.') and k.count('.') > 1]}) and its measures ({[k for k in outs2 if k.startswith('lc_drops')]})")
def bad2(change):
    t = copy.deepcopy(T2); change(t); return "; ".join(network.problems(t))
lc = lambda t: t["links"][2]
cases2 = {"a flow that is in no part": (bad2(lambda t: lc(t)["ends"]["r"]["queue"]["classes"].update(one=["fa"])), "has no part for fd"),
          "a flow in two queues": (bad2(lambda t: lc(t)["ends"]["r"]["queue"]["classes"].update(one=["fa", "fd", "fb"])), "fb would wait in two of its queues"),
          "a class named like a flow": (bad2(lambda t: (lc(t)["ends"]["r"]["queue"]["classes"].update(fa=["fd"]), lc(t)["ends"]["r"]["queue"]["parts"].update(fa=1))), "a name of its own (not a flow's)"),
          "a class without a part": (bad2(lambda t: lc(t)["ends"]["r"]["queue"]["classes"].update(two=["fb"])), "a name of its own"),
          "an end that is no host of the link": (bad2(lambda t: lc(t)["ends"].update(a={"rate": "1Gbps"})), "by their hosts (r, c)"),
          "a device rate that is no rate": (bad2(lambda t: lc(t)["ends"]["c"].update(rate="fast")), "the device of c: rate = 'fast'"),
          "two queues on one side": (bad2(lambda t: lc(t).update(queue={"on": "c", "kind": "fifo", "length": 10})), "one side has one queue"),
          "a host named like a word of an address": (bad2(lambda t: (t["hosts"].append({"id": "rate"}), t["links"].append(LK("lx", "rate", "c")))), "the id rate is kept")}
say(all(w in got for got, w in cases2.values()), "refused with the reason: " + ", ".join(cases2) + "".join(f" [{k}: {got[:110]}]" for k, (got, w) in cases2.items() if w not in got))
cl2, was2 = tools.clamp({"lc.c.rate": "5Mbps", "lc.r.queue.parts.one": 9}, g2)
r2 = control.operator_run({"brief": "ends", "policy": "share", "params": {}}); txt2 = (P / "checks" / r2["id"] / "network.txt").read_text(); m2 = r2["metrics"]
want2 = json.loads((REAL / "checks/net2/p05-class-and-flow/metrics.json").read_text())
say(cl2["lc.c.rate"] == "10Mbps" and cl2["lc.r.queue.parts.one"] == 4 and "dev lc c rate=50Mbps" in txt2 and "queue lc r kind=scheduler length=100 parts=one:0.25,fb:0.75 classes=one:fa+fd" in txt2 and "queue lc c kind=fifo length=50" in txt2
    and abs((m2["fa_goodput_bps"] + m2["fd_goodput_bps"]) / (want2["fa_goodput_bps"] + want2["fd_goodput_bps"]) - 1) < 0.01 and abs(m2["fb_goodput_bps"] / want2["fb_goodput_bps"] - 1) < 0.01 and set(m2) == set(outs2),
    f"a knob of an end is clamped into its range ({was2}); an operator simulation writes the two ends and the class into the program's input, and gives the measures the harness names: fa + fd {(m2['fa_goodput_bps'] + m2['fd_goodput_bps']) / 1e6:.2f} Mbps together, fb {m2['fb_goodput_bps'] / 1e6:.2f} Mbps (the operator's check p05: {(want2['fa_goodput_bps'] + want2['fd_goodput_bps']) / 1e6:.2f} and {want2['fb_goodput_bps'] / 1e6:.2f})")
e2 = network.apply(T, [{"do": "add_queue", "id": "lc", "on": "c", "kind": "fifo", "from": "", "to": "", "rate": "", "type": ""}]); back2 = network.apply(e2, [{"do": "remove", "kind": "queue", "id": "lc", "on": "c", "from": "", "to": "", "rate": "", "type": ""}])
say(not network.problems(e2) and network.objects(e2) - network.objects(T) == {"queue:lc.c"} and set(network.settings(T)) <= set(network.settings(e2)) and "lc.c.queue.length" in network.settings(e2) and back2 == network.apply(T, []),
    "a link that has a queue on one side can be given one on the other (a change of structure): the first keeps its name and its addresses, the new one is lc.c; removed again, the network is as it was")
# ---- a flow's application and its socket are two choices (2026-11-18; the third build of net, checks/net3)
print("AN APPLICATION AND THE SOCKET IT OPENS")
T3 = {"hosts": [{"id": "sender"}, {"id": "receiver"}],
      "links": [LK("l1", "sender", "receiver", queue={"on": "sender", "kind": "scheduler", "length": 100, "parts": {"udp": 0.5, "tcp": 0.5}, "largest_rate": {}})],
      "flows": [{"id": "udp", "kind": "udp", "from": "sender", "to": "receiver", "rate": "2Gbps", "packet_bytes": 1400},
                {"id": "tcp", "kind": "tcp", "app": "onoff", "from": "sender", "to": "receiver", "rate": "100Mbps", "packet_bytes": 1400, "type": "TcpCubic"}]}
B3 = {"id": "apps", "description": "UDP offers {udp.rate}. The TCP flow's application hands TCP data at a constant rate ({tcp.rate}); its congestion control is {tcp.type}.", "topology": T3, "system": {"seed": 1, "duration": 10},
      "knobs": {"tcp.rate": {"min": "10Mbps", "max": "2Gbps", "default": "100Mbps", "meaning": "the rate at which the application of flow tcp hands data to TCP"}}, "goal": {"kind": "open"}, "limits": {"simulations": 8, "simulations_per_experiment": 4}}
(P / "briefs/apps.json").write_text(json.dumps(B3)); g3 = tools.load_brief("apps"); set3 = network.settings(T3); outs3 = tools.outputs(g3)
plain3 = copy.deepcopy(T3); plain3["flows"][1] = {"id": "tcp", "kind": "tcp", "from": "sender", "to": "receiver", "type": "TcpCubic"}
say(not network.problems(T3) and [k for k in set3 if k.startswith("tcp.")] == ["tcp.rate", "tcp.packet_bytes", "tcp.type"] and "tcp_retrans" in outs3 and "tcp_loss_frac" not in outs3 and network.app(T3["flows"][0]) == "onoff" and network.app(plain3["flows"][1]) == "bulk"
    and "the knob tcp.rate" in g3["description"] and [k for k in network.settings(plain3) if k.startswith("tcp.")] == ["tcp.type"],
    f"a TCP flow whose application is OnOff (a constant rate) is accepted: its settings are {[k for k in set3 if k.startswith('tcp.')]}, its measures those of a TCP flow; a flow that names no application is OnOff over UDP and BulkSend over TCP, as every flow before")
def bad3(change):
    t = copy.deepcopy(T3); change(t); return "; ".join(network.problems(t))
cases3 = {"BulkSend over UDP": (bad3(lambda t: t["flows"][0].update(app="bulk")), "BulkSendApplication needs a TCP socket"),
          "an application ns-3 does not have here": (bad3(lambda t: t["flows"][1].update(app="echo")), "app must be onoff"),
          "OnOff over TCP without a rate": (bad3(lambda t: t["flows"][1].pop("rate")), "rate = None is not a rate")}
say(all(w in got for got, w in cases3.values()), "refused with the reason: " + ", ".join(cases3) + "".join(f" [{k}: {got[:110]}]" for k, (got, w) in cases3.items() if w not in got))
cl3, was3 = tools.clamp({"tcp.rate": "5Gbps"}, g3); old3 = network.text(plain3, {"duration": 10, "seed": 1})
r3 = control.operator_run({"brief": "apps", "policy": "share", "params": {}}); txt3 = (P / "checks" / r3["id"] / "network.txt").read_text(); m3 = r3["metrics"]
want3 = json.loads((REAL / "checks/net3/p03-share-tcp-100/metrics.json").read_text())
say(network.rate_bps(cl3["tcp.rate"]) == 2e9 and "flow tcp tcp sender receiver type=TcpCubic app=onoff rate=100Mbps packet=1400\n" in txt3 and "flow tcp tcp sender receiver type=TcpCubic\n" in old3 and "app=" not in old3
    and abs(m3["tcp_goodput_bps"] / 100e6 - 1) < 0.01 and abs(m3["udp_goodput_bps"] / want3["udp_goodput_bps"] - 1) < 0.01 and set(m3) == set(outs3),
    f"its rate is a knob like any other (clamped: {was3}); an operator simulation writes app=onoff with the rate into the program's input, and a flow without an application is written as before; "
    f"TCP delivers {m3['tcp_goodput_bps'] / 1e6:.2f} Mbps of the 100 offered and UDP {m3['udp_goodput_bps'] / 1e6:.1f} Mbps (the operator's check p03: {want3['udp_goodput_bps'] / 1e6:.1f})")
# ---- what else ns-3 has (2026-11-18; the fourth build of net, checks/net4): an application's times, a device's own largest packet and loss, TCP's options, ns-3's queue discs
print("AN APPLICATION'S TIMES, A DEVICE'S LOSS, TCP'S OPTIONS, NS-3'S QUEUE DISCS")
T4 = {"hosts": [{"id": "sender"}, {"id": "receiver"}],
      "links": [LK("l1", "sender", "receiver", ends={"sender": {"queue": {"kind": "fqcodel", "length": 100}}, "receiver": {"loss": 0.1, "mtu": 1400}})],
      "flows": [{"id": "udp", "kind": "udp", "from": "sender", "to": "receiver", "rate": "100Mbps", "packet_bytes": 1000, "start": 4, "stop": 9, "on_time": 0.5, "off_time": 0.5, "max_bytes": 900000000},
                {"id": "tcp", "kind": "tcp", "from": "sender", "to": "receiver", "type": "TcpCubic", "start": 3}]}
B4 = {"id": "times", "description": "UDP is on for {udp.on_time} s and off for {udp.off_time} s between {udp.start} s and {udp.stop} s. The receiver's device loses {l1.receiver.loss} of the packets.", "topology": T4,
      "system": {"seed": 1, "duration": 10, "tcpSack": 0, "tcpTimestamps": 0, "tcpDelAck": 1},
      "knobs": {"udp.on_time": {"min": 0.1, "max": 5, "default": 0.5, "meaning": "the length of the on period of flow udp, s"}, "l1.receiver.loss": {"min": 0, "max": 0.5, "default": 0.1, "meaning": "the part of the packets the receiver's device loses"}},
      "goal": {"kind": "open"}, "limits": {"simulations": 8, "simulations_per_experiment": 4}}
(P / "briefs/times.json").write_text(json.dumps(B4)); g4 = tools.load_brief("times"); set4 = network.settings(T4); outs4 = tools.outputs(g4)
say(not network.problems(T4) and [k for k in set4 if k.startswith("udp.")] == ["udp.rate", "udp.packet_bytes", "udp.start", "udp.stop", "udp.on_time", "udp.off_time", "udp.max_bytes"] and [k for k in set4 if k.startswith("tcp.")] == ["tcp.type", "tcp.start"]
    and {"l1.receiver.loss", "l1.receiver.mtu", "l1.sender.queue.length"} <= set(set4) and "l1_lost_receiver" in outs4 and "l1_lost_sender" not in outs4 and "l1_drops" in outs4,
    f"a brief whose flows state their times, whose device has a loss and a largest packet of its own and whose queue is ns-3's FqCoDel is accepted; its settings ({[k for k in set4 if k.split('.')[-1] in ('start', 'stop', 'on_time', 'off_time', 'max_bytes', 'loss')]}) and the measure l1_lost_receiver")
def bad4(change):
    t = copy.deepcopy(T4); change(t); return "; ".join(network.problems(t))
cases4 = {"an on period without an off period": (bad4(lambda t: t["flows"][0].pop("off_time")), "given together"),
          "on and off periods on BulkSend": (bad4(lambda t: t["flows"][1].update(on_time=1, off_time=1)), "no on and off periods"),
          "a stop before the start": (bad4(lambda t: t["flows"][0].update(stop=2)), "before it starts"),
          "a loss above 1": (bad4(lambda t: t["links"][0]["ends"]["receiver"].update(loss=1.5)), "the device of receiver: loss = 1.5"),
          "a packet larger than a device on its way carries": (bad4(lambda t: t["flows"][0].update(packet_bytes=1400)), "from 64 to 1372"),
          "a queue disc ns-3 does not have": (bad4(lambda t: t["links"][0]["ends"]["sender"]["queue"].update(kind="sfq")), "fifo, pfifofast, codel, fqcodel, red, pie or scheduler"),
          "an on period of 0": (bad4(lambda t: t["flows"][0].update(on_time=0)), "on_time = 0")}
say(all(w in got for got, w in cases4.values()), "refused with the reason: " + ", ".join(cases4) + "".join(f" [{k}: {got[:130]}]" for k, (got, w) in cases4.items() if w not in got))
cl4, was4 = tools.clamp({"udp.on_time": 9, "l1.receiver.loss": 0.9}, g4)
r4 = control.operator_run({"brief": "times", "policy": "share", "params": {}}); txt4 = (P / "checks" / r4["id"] / "network.txt").read_text(); m4 = r4["metrics"]
# UDP: on half of 4 s to 9 s, all inside the measured 2 s to 12 s: 100 Mbps x 2.5 s / 10 s = 25 Mbps offered, a tenth lost on arrival
say(cl4 == {"udp.on_time": 5.0, "l1.receiver.loss": 0.5} and type(tools.clamp({"lc.queue.length": 7.6}, tools.load_brief("three-hosts"))[0]["lc.queue.length"]) is int and "dev l1 receiver mtu=1400 loss=0.1\n" in txt4 and "queue l1 sender kind=fqcodel length=100\n" in txt4
    and "flow udp udp sender receiver rate=100Mbps packet=1000 start=4 stop=9 on=0.5 off=0.5 maxbytes=900000000\n" in txt4 and "flow tcp tcp sender receiver type=TcpCubic start=3\n" in txt4 and "tcp delack=1 sack=0 timestamps=0\n" in txt4
    and set(m4) == set(outs4) and abs(m4["udp_goodput_bps"] / 22.5e6 - 1) < 0.05 and abs(m4["udp_loss_frac"] - 0.1) < 0.02 and m4["l1_lost_receiver"] > 0,
    f"knobs of a time and of a loss are clamped ({was4}); an operator simulation writes the times, the device's loss and largest packet, the queue disc and TCP's options into the program's input; "
    f"UDP, on half of five seconds, delivers {m4['udp_goodput_bps'] / 1e6:.1f} Mbps (25 offered, a tenth lost: 22.5) with a loss of {m4['udp_loss_frac']:.3f}; l1_lost_receiver {m4['l1_lost_receiver']:.0f}")
ED = lambda **k: {"do": "", "id": "", "kind": "", "from": "", "to": "", "on": "", "rate": "", "type": "", "app": "", **k}
e4 = network.apply(T3, [ED(do="add_flow", id="t2", kind="tcp", app="onoff", rate="50Mbps", type="TcpBbr", **{"from": "sender", "to": "receiver"}), ED(do="remove", kind="queue", id="l1"), ED(do="add_queue", id="l1", on="sender", kind="codel")])
t2 = next(f for f in e4["flows"] if f["id"] == "t2")
try: network.apply(T3, [ED(do="add_flow", id="u9", kind="udp", app="bulk", **{"from": "sender", "to": "receiver"})]); no4 = ""
except ValueError as x: no4 = str(x)
say(not network.problems(e4) and t2 == {"id": "t2", "kind": "tcp", "app": "onoff", "from": "sender", "to": "receiver", "rate": "50Mbps", "packet_bytes": 1400, "type": "TcpBbr"} and network.ends(e4["links"][0])["sender"]["queue"]["kind"] == "codel" and "tcp only" in no4
    and network.EDIT[-1] == "app", f"a change of structure can add a TCP flow that sends at a constant rate (app onoff: {t2['rate']}, {t2['type']}) and put one of ns-3's queue discs on a link (codel); BulkSend over UDP is refused (“{no4[-70:]}”)")
# ---- a brief without a network is as before
old = tools.load_brief("two-hosts-udp-demand-2"); o = tools.options(tools.clamp({"weightUdp": 0.3}, old)[0], old); cmd = tools.command(o, "/tmp/x", old)
say("topology" not in old and cmd[0].endswith("ns3.49-two-hosts-optimized") and "--weightUdp=0.3" in cmd and "--out=/tmp/x" in cmd and tools.outputs(old) == tools.MANIFEST["outputs"] and tools.kind("udpRate", old) == "rate",
    "a brief without a network is started with two-hosts and its options, and has the seven measures of two-hosts, as before")
print("RESULT:", f"FAIL {len(FAILED)}" if FAILED else "PASS"); [print("  FAILED", f) for f in FAILED]
