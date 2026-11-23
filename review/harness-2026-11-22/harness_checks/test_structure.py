"""The AI may change the structure (TOPOLOGY.md, stage 5; 2026-11-17): in a brief with a network and
"structure": {"may_change": true, "most": {...}, "locked": [...]}, a simulation may carry a list of changes to the
brief's network (add a host, a link, a flow, a queue; remove an object) and is then run on the changed network.
  - the answer format has `structure` in every simulation and in the report (after the recommendation), each change
    with its eight fields; the instructions get one paragraph; a brief that does not allow it has neither;
  - a scripted session: a simulation as given, one without the scheduler, one with a third flow; each is run on its
    own network (the run folder holds it), its record keeps the changes and the network, the new flow's measures are in
    its evidence line, and a rule that names them is checked; two designs with the same settings on different
    networks are two simulations; the report recommends a structure and is accepted;
  - refused with the reason, before anything is run: removing what the aim measures, removing a locked object, a
    network over the brief's limits, a network that cannot be built, a rule that names a measure one of its
    simulations does not have;
  - the brief check refuses a structure that locks an object that is not there, or allows less than the network has.
    python3 -I test_structure.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new. Simulations are real runs of `net`, 2 measured seconds each."""
import copy, json, os, shutil, subprocess, sys
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
L = lambda i, a, b, **k: {"id": i, "between": [a, b], "rate": "1Gbps", "delay": "50us", "mtu": 1500, "device_queue": 10, **k}
T = {"hosts": [{"id": "a"}, {"id": "b"}, {"id": "r"}, {"id": "c"}],
     "links": [L("la", "a", "r"), L("lb", "b", "r"), L("lc", "r", "c", rate="100Mbps", delay="1ms", queue={"on": "r", "kind": "scheduler", "length": 100, "parts": {"fa": 0.5, "fb": 0.5}})],
     "flows": [{"id": "fa", "kind": "tcp", "from": "a", "to": "c", "type": "TcpCubic"}, {"id": "fb", "kind": "udp", "from": "b", "to": "c", "rate": "80Mbps", "packet_bytes": 1400}]}
B = {"id": "change", "description": "Two senders, a and b, reach c through r; the link from r to c carries {lc.rate}.", "topology": T, "system": {"seed": 1, "duration": 2},
     "knobs": {"lc.queue.parts.fa": {"min": 0.05, "max": 4, "default": 0.5, "meaning": "the part of link lc for flow fa"}},
     "goal": {"kind": "given", "target": {"measure": "fa_goodput_bps", "direction": "max"}, "conditions": ["fb_loss_frac <= 0.9"]},
     "limits": {"simulations": 12, "simulations_per_experiment": 4},
     "structure": {"may_change": True, "most": {"hosts": 5, "links": 5, "flows": 3}, "locked": ["link:lc"]}}
(P / "briefs/change.json").write_text(json.dumps(B)); fixed = copy.deepcopy(B); fixed["id"] = "nochange"; fixed["structure"] = {"may_change": False}; (P / "briefs/nochange.json").write_text(json.dumps(fixed))
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import tools, network, loop
E = lambda do, **k: {"do": do, **{f: k.get(f, "") for f in network.EDIT[1:]}}
print("THE AI MAY CHANGE THE STRUCTURE")
g, g0 = tools.load_brief("change"), tools.load_brief("nochange")
fmt, fmt0 = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), g), loop.answer_format(json.loads((P / "harness/schema.json").read_text()), g0)
run, rep = fmt["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"], fmt["properties"]["report"]["anyOf"][0]
say(run["properties"]["structure"]["items"]["required"] == list(network.EDIT) and "structure" in run["required"] and list(rep["properties"]).index("structure") == list(rep["properties"]).index("recommendation") + 1 and "structure" in rep["required"]
    and "structure" not in fmt0["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"] and "structure" not in fmt0["properties"]["report"]["anyOf"][0]["properties"],
    f"the answer format: every simulation and the report (after its recommendation) carry structure, a list of changes of {len(network.EDIT)} fields each ({', '.join(network.EDIT)}); a brief that does not allow it has neither")
def refused(change):
    x = copy.deepcopy(B); change(x)
    try: tools.check_brief(x, "change"); return ""
    except ValueError as e: return str(e)
r1, r2 = refused(lambda x: x["structure"].update(locked=["flow:zz"])), refused(lambda x: x["structure"]["most"].update(hosts=3))
say("structure.locked names objects of the network" in r1 and "smaller than the network the session starts from" in r2, "the brief check refuses a structure that locks an object that is not there, or allows fewer hosts than the network has")

def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def d(label, edits, part=0.5): return {"label": label, "params": {"lc.queue.parts.fa": part}, "structure": edits}
H = lambda text, q: {"text": text, "question": q, "why": "It says whether the structure limits the goal.", "prediction": "less", "follows_from": ["brief"]}
NOQ, EXTRA = [E("remove", kind="queue", id="lc")], [E("add_flow", id="fc", kind="tcp", **{"from": "a", "to": "c"}, type="TcpBbr")]
ANSWERS = [turn(hypotheses=[H("Without the scheduler fa gets less", "Does flow fa get less when r has one plain queue?"), H("A third flow gets a part of the link", "Does a second TCP flow from a deliver anything?")],
                experiment={"kind": "test", "tests": ["H1", "H2"], "question": "", "varied": [], "control": "base", "runs": [d("base", []), d("noq", NOQ), d("extra", EXTRA), d("again", NOQ)],
                            "decision_rules": [{"for": "H1", "decision_rule": "fa_goodput_bps@noq < fa_goodput_bps@base", "rival": "the queue's kind does nothing", "rival_predicts": "failed"},
                                               {"for": "H2", "decision_rule": "fc_goodput_bps@extra > 1000000 AND fa_goodput_bps@extra < fa_goodput_bps@base", "rival": "the new flow is starved", "rival_predicts": "failed"}]}),
           turn(verdicts=[{"for": "H1", "result": "supported", "because": "C1 held.", "next": "report"}, {"for": "H2", "result": "supported", "because": "C2 held.", "next": "report"}],
                report={"goal": "the largest goodput of fa while fb loses at most 90 %", "recommendation": {"lc.queue.parts.fa": 0.5}, "structure": [],
                        "expected": {"fa_goodput_bps": 48000000.0}, "no_difference": [], "limit": "The 100 Mbps link from r to c, and fb's part of it: E1.",
                        "explanation": "The scheduler protects fa.", "holds_when": "as tested", "breaks_when": "other rates",
                        "claims": [{"text": "Without the scheduler fa gets less.", "role": "supports", "evidence": ["C1"]}], "open_questions": []}, done=True)]
f = SCR / "c1.answers.json"; f.write_text(json.dumps(ANSWERS))
r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", "change", "--session", "c1"], env=ENV, capture_output=True, text=True, timeout=1200)
if r.returncode: print(r.stdout[-600:], r.stderr[-2500:])
led = [json.loads(l) for l in (P / "sessions/c1/ledger.jsonl").read_text().splitlines() if l.strip()]; meta = json.loads((P / "sessions/c1/session.json").read_text())
of = lambda ty: [x for x in led if x["type"] == ty]
sims = {s["body"].get("label"): s["body"] for s in of("simulation")}; notes = [n["body"] for n in of("note") + of("malformed")]
net_of = lambda label: (P / "sessions/c1/runs" / sims[label]["run_id"] / "network.txt").read_text() if label in sims and "run_id" in sims[label] else ""
say(all(k in sims and "metrics" in sims[k] for k in ("base", "noq", "extra")) and "queue lc" not in net_of("noq") and "queue lc" in net_of("base") and "flow fc tcp a c type=TcpBbr" in net_of("extra") and "fc:" in net_of("extra"),
    "three networks were simulated: the brief's, one without the scheduler of lc, one with a third flow fc (which got a part in the scheduler); each run folder holds its own network" + (f" {notes[-1]}" if "noq" not in sims else ""))
cut = [n.get("reason") or n.get("text") or "" for n in notes if "again" in json.dumps(n)]
say("base" in sims and sims["base"]["run_id"] != sims["noq"]["run_id"] and "again" not in sims and any("same settings and seed as `noq`" in c for c in cut) and "structure" not in sims["base"] and sims["noq"]["structure"] == NOQ and [f["id"] for f in sims["extra"]["topology"]["flows"]] == ["fa", "fb", "fc"],
    "the same settings on two networks are two simulations (base and noq); a design with the same settings on the same changed network as another is refused as a repeat (again); a record on a changed network keeps the changes and the network it was run on")
ev = of("evidence")[-1]["body"]["lines"]; ck = {c["body"]["for"]: c["body"] for c in of("check")}
say(any("fc_goodput_bps=" in l and "structure: +tcp flow fc a>c" in l for l in ev) and any("structure: -queue lc" in l for l in ev) and ck.get("H2", {}).get("result") in ("held", "failed") and "fc_goodput_bps" in ck["H2"]["decision_rule"] and ck.get("H1", {}).get("result") in ("held", "failed"),
    f"the evidence lines say each change and give the new flow's measures; the rule that names them is checked ({ck.get('H2', {}).get('result')}: {ck.get('H2', {}).get('with_numbers', '')[:80]})")
say(meta.get("how") == "done by the model" and of("report") and of("report")[0]["body"].get("structure") == [] and "In this session you may also change the structure" in meta["prompt"],
    f"the report with a recommended structure (here: as given) is accepted (“{meta.get('how')}”), and the session's instructions hold the paragraph on structure")

# ---- refused before anything is run
loop.tools.open_session("c2", "change"); brief = loop.tools.describe_system(); st = {"H1": "open"}
def why(runs, rules=None):
    ex = {"kind": "test" if rules else "explore", "tests": ["H1"] if rules else [], "question": "" if rules else "what happens?", "varied": [], "control": None, "runs": runs, "decision_rules": rules or [],
          **({"needs": [{"for": "H1", "to_know": "what the changed network does", "varies": "structure", "measure": "fc_goodput_bps", "simulations": [r["label"] for r in runs]}]} if rules else {})}
    return loop.experiment_problem(ex, brief, [], None, st) or ""
R = lambda rule: [{"for": "H1", "decision_rule": rule, "rival": "x", "rival_predicts": "failed"}]
cases = {"removing what the aim measures": (why([d("x", [E("remove", kind="flow", id="fb")])]), "the aim is about fb_loss_frac"),
         "removing a locked object": (why([d("x", [E("remove", kind="link", id="lc")])]), "link lc may not be removed"),
         "a network over the brief's limits": (why([d("x", [E("add_host", id="h1"), E("add_host", id="h2"), E("add_link", id="l1", **{"from": "h1", "to": "r"}), E("add_link", id="l2", **{"from": "h2", "to": "r"})])]), "this brief allows at most 5"),
         "a flow without a way": (why([d("x", [E("add_host", id="h1"), E("add_flow", id="fz", kind="udp", **{"from": "h1", "to": "c"})])]), "there is no way from h1 to c"),
         "an id that is taken": (why([d("x", [E("add_host", id="a")])]), "an id of its own"),
         "a rule that names a measure one of its simulations does not have": (why([d("base", []), d("extra", EXTRA)], R("fc_goodput_bps@base > 1")), "has no such measure"),
         "a rule on the new measure in the simulation that has it": (why([d("base", []), d("extra", EXTRA)], R("fc_goodput_bps@extra > fa_goodput_bps@base")), None)}
say(all((w in got) if w else not got for got, w in cases.values()), "refused with the reason before anything is run: " + ", ".join(k for k, (g_, w) in cases.items() if w) + "; accepted: " + ", ".join(k for k, (g_, w) in cases.items() if not w)
    + "".join(f" [{k}: {got[:110]}]" for k, (got, w) in cases.items() if (w not in got if w else got)))
rp = loop.check_report({**ANSWERS[1]["report"], "structure": [E("remove", kind="flow", id="fb")]}, brief, {"C1"}, [])
say(rp and "report.structure cannot be used" in rp and "fb_loss_frac" in rp, f"a report that recommends removing what the aim measures is refused (“{(rp or '')[:90]}…”)")
loop.tools.open_session("c3", "nochange"); b0 = loop.tools.describe_system()
say(loop.edits_of(d("x", NOQ), b0) == [] and "structure" not in json.dumps(loop.answer_format(json.loads((P / "harness/schema.json").read_text()), b0)["properties"]["experiment"]), "in a brief that does not allow it, a simulation's structure is not read and the format has no place for it")
print("RESULT:", f"FAIL {len(FAILED)}" if FAILED else "PASS"); [print("  FAILED", f) for f in FAILED]
