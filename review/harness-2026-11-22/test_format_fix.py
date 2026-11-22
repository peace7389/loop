"""The "Done when" checks of ~/project/FORMAT_FIX.md, Parts 1 and 2, as scripted sessions in a scratch copy, together
with the earlier behaviour of the harness that must stay as it was (the earlier scripted tests were not kept on disk;
their main cases are written again here).
    python3 -I test_format_fix.py SCRATCH_DIR [HARNESS_DIR]      (HARNESS_DIR: default ~/project/harness)
SCRATCH_DIR is made new: home/project/{harness (a copy), briefs (a copy), sessions, checks, ns-3.49 (a link)}.
Simulations are real ns-3 runs of 2 measured seconds. --server also sends one small request to the model server with
the new params format (does the server make an answer state every knob?). --part1: only what Part 1 needs (a harness
that has Part 1 and not yet Part 2): the first turn of T1, the formats, and session T2."""
import json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
FAILED = []
P1 = "--part1" in sys.argv
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, brief, answers, *flags):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps(answers))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env={**os.environ, "HOME": str(SCR / "home")}, capture_output=True, text=True, timeout=1200)
    led = [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
    return led, json.loads((P / "sessions" / sid / "session.json").read_text()), r
def bare(a):
    """An answer as the script wrote it: without what scripted.py fills in for a script written before 2026-11-17 (the why, from_why, the needs)."""
    a = json.loads(json.dumps(a)); a.pop("whys", None); [h.pop("from_why", None) for h in a.get("hypotheses") or []]; (a.get("experiment") or {}).pop("needs", None); return a
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
notes = lambda led, turn: [(r["body"].get("part"), r["body"].get("reason")) for r in of(led, "note", turn) if "part" in r["body"]]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)   # two-hosts-open: every knob but weightUdp
def d(label, w, **over): return {"label": label, "params": {"weightUdp": w, **KN, **over}}
def hyp(text, q="Does it?", ff=("brief",)): return {"text": text, "question": q, "why": "The goal depends on it.", "prediction": "a direction", "follows_from": list(ff)}  # why: required since 2026-11-14
def rule(h, text, predicts="failed"): return {"for": h, "decision_rule": text, "rival": "the knob does nothing", "rival_predicts": predicts}
def ex(kind, runs, rules=(), tests=(), varied=("weightUdp",), question="", control=None): return {"kind": kind, "tests": list(tests), "question": question, "varied": list(varied), "control": control, "runs": runs, "decision_rules": list(rules)}
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def verdict(h, res="supported"): return {"for": h, "result": res, "because": "the check", "next": "go on"}
REPORT = {"goal": "balanced goodput", "recommendation": {"weightUdp": 0.5, **KN}, "expected": {"udp_goodput_bps": 1.0}, "no_difference": [], "limit": "l", "explanation": "e", "holds_when": "h", "breaks_when": "b", "claims": [{"text": "c", "role": "supports", "evidence": ["C1"]}], "open_questions": []}

# ================================================================== session T1: brief two-hosts-open
no_w = {"label": "c", "params": dict(KN)}                       # a design that does not state weightUdp
h_no_q = {k: v for k, v in hyp("no question").items() if k != "question"}
T1 = [
 turn(hypotheses=[hyp("UDP goodput rises with the weight", "Does UDP get more when its part is larger?"), h_no_q, hyp("empty question", q="  "), hyp("TCP delivers something", "Does TCP deliver anything at all?")],
      experiment=ex("test", [d("a", 0.3), d("b", 0.7), no_w], [rule("H1", "udp_goodput_bps@b > udp_goodput_bps@a"), rule("H4", "tcp_goodput_bps@a > 1000")], ["H1", "H4"])),   # by position: the 4th hypothesis of this answer is H4 (ids by position since 2026-11-22, the coherence audit); it is recorded as H2
 turn(verdicts=[verdict("H1"), verdict("H2")], hypotheses=[hyp("h3", ff=["V1"]), hyp("h4", ff=["C1"]), hyp("h5", ff=["E1"])],
      experiment=ex("test", [d("p", 0.4), d("q", 0.4), d("r", 0.6), d("s", 0.6, seed=2), d("t", 0.6)],
                    [rule("H3", "udp_goodput_bps@p > udp_goodput_bps@q"), rule("H4", "abs(udp_goodput_bps@r - udp_goodput_bps@s) < 1e12 AND (tcp_goodput_bps@r > 0 OR tcp_goodput_bps@s > 0)"), rule("H5", "udp_goodput_bps@t > 0")], ["H3", "H4", "H5"], varied=["weightUdp", "seed"])),
 turn(hypotheses=[hyp("h6")], experiment=ex("explore", [d("u", 0.2), d("v", 0.8)], varied=["queuePkts"], question="what a weight does")),
 turn(experiment=ex("explore", [d("a_again", 0.3), d("w", 0.45)], question="one earlier design and a new one")),
 turn(done=True, report=REPORT, drop=[{"id": "H4", "why": "no longer needed"}]),
 turn(done=True, report=REPORT, verdicts=[verdict("H4", "inconclusive")]),
]
print("T1  scripted session on brief two-hosts-open"); led, meta, run = session("t1", "two-hosts-open", T1[:1] if P1 else T1)
if run.returncode: print(run.stdout[-1500:], run.stderr[-3000:])
brief = meta["given"]; knobs = list(brief["knobs"])
print(" Part 1")
n1 = notes(led, 1); x1 = next(r for r in of(led, "experiment", 1)); sims1 = [r["body"]["label"] for r in of(led, "simulation", 1)]
say(("design c", "design `c` does not state `weightUdp`") in n1 and sims1 == ["a", "b"], f"a design lacking a knob is refused with the message, and the rest is run: {[n for n in n1 if n[0] == 'design c']}; simulations run: {sims1}")
say(all(list(r["params"]) == knobs for r in x1["body"]["runs"]) and all(set(knobs) <= set(r["body"]["params"]) for r in of(led, "simulation", 1)), f"an accepted design's recorded params has every knob of the brief, in the brief's order: {list(x1['body']['runs'][0]['params'])}")
hy = of(led, "hypothesis", 1)
say([n[1] for n in n1 if n[0] == "new hypothesis"] == ["a hypothesis needs a question: the hypothesis put as one plain question"] * 2 and len(hy) == 2, f"a hypothesis without a question, and one with an empty question, are refused ({sum(n[0] == 'new hypothesis' for n in n1)} notes); the other {len(hy)} are accepted")
say([h["body"].get("question") for h in hy] == ["Does UDP get more when its part is larger?", "Does TCP deliver anything at all?"], f"the ledger holds the question with the hypothesis: {[(h['id'], h['body'].get('question')) for h in hy]}")
ans = [json.loads(l) for l in (P / "sessions/t1/answers.jsonl").read_text().splitlines()]
say([a["turn"] for a in ans] == ([1] if P1 else [1, 2, 3, 4, 6]) and bare(ans[0]["answer"]) == T1[0] and [r["label"] for r in ans[0]["answer"]["experiment"]["runs"]] == ["a", "b", "c"], f"answers.jsonl has one line per turn with an accepted answer ({[a['turn'] for a in ans]}), each as it was received (turn 1 still holds design c and the two refused hypotheses); turn 5, in which nothing could be used, has none")
sys.path.insert(0, str(P / "harness")); os.environ["HOME"] = str(SCR / "home")
import importlib; loop = importlib.import_module("loop"); tools = loop.tools
for b in ("two-hosts-udp-demand", "two-hosts-open"):
    bb = tools.load_brief(b); f = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), bb); pr = f["properties"]["experiment"]["anyOf"][0]["properties"]; pp = pr["runs"]["items"]["properties"]["params"]
    want_udp = b == "two-hosts-open"
    say(list(pp["properties"]) == list(bb["knobs"]) == pp["required"] and ("udpRate" in pp["properties"]) == want_udp and pp["additionalProperties"] is False and pp["properties"]["tcpVariant"].get("enum") == bb["knobs"]["tcpVariant"]["choices"] and not set(pp["properties"]) & set(bb["system"])
        and pr["varied"]["items"]["enum"] == list(bb["knobs"]), f"{b}: the format's params has one property per knob, in the brief's order, all required: {pp['required']}; udpRate a property: {'udpRate' in pp['properties']}; tcpVariant has the brief's choices; varied lists the same knobs")
sent = json.loads((P / "sessions/t1/format_sent.json").read_text())["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["params"]
say(sent["required"] == knobs and "question" in json.loads((P / "sessions/t1/format_sent.json").read_text())["properties"]["hypotheses"]["items"]["required"], "the format the session sent with its requests is that one, and requires a hypothesis's question")
if not P1:
    print(" Part 2")
    n2 = notes(led, 2); x2 = of(led, "experiment", 2)[0]["body"]; sims2 = [r["body"]["label"] for r in of(led, "simulation", 2)]; c2 = [(r["body"]["for"], r["body"]["result"]) for r in of(led, "check", 2)]
    say(("design q", "design `q` has the same settings and seed as `p`; give it different settings or remove it") in n2 and ("design t", "design `t` has the same settings and seed as `r`; give it different settings or remove it") in n2, f"two labels, one simulation: the later design is refused: {[n[1] for n in n2 if n[0] in ('design q', 'design t')]}")
    say(("decision rule for H3", "this decision rule compares `p` with `q`, which are the same simulation (same settings and seed), so it cannot hold or fail for a reason; change the designs or the rule") in n2, f"a decision rule that compares a simulation with itself is refused: {[n[1] for n in n2 if n[0] == 'decision rule for H3']}")
    say(sims2 == ["r", "s"] and c2 == [("H4", "held")] and x2["tests"] == ["H4"] and [r["label"] for r in x2["runs"]] == ["r", "s"] and any(n[0] == "design p" and "named only by a decision rule that was refused" in n[1] for n in n2) and any(n[0] == "decision rule for H5" and "names `t`, a design that was refused" in n[1] for n in n2),
        f"nothing is run for a refused rule's hypothesis, and the rest of the answer is kept: simulations run {sims2}, checks {c2}, the experiment's tests {x2['tests']}; also refused: {[n for n in n2 if n[0] in ('design p', 'decision rule for H5')]}")
    say(len(of(led, "verdict", 2)) == 2 and len(of(led, "hypothesis", 2)) == 3, f"in that turn the 2 verdicts and the 3 new hypotheses are accepted ({len(of(led, 'verdict', 2))}, {len(of(led, 'hypothesis', 2))})")
    n3 = notes(led, 3)
    say(n3 == [("experiment", "`queuePkts` is listed as varied but has the single value `100` in every design")] and not of(led, "experiment", 3) and not of(led, "simulation", 3) and len(of(led, "hypothesis", 3)) == 1, f"a varied knob that does not vary: the experiment is refused, the hypothesis of the same answer is kept: {n3}")
    texts = [r["body"]["reason"] for r in of(led, "note") if "reason" in r["body"] and (r["body"]["part"].startswith(("design", "decision rule")) or "varied" in r["body"]["reason"])]
    say(all(not any(w in t.lower() for w in ("scheduler", "policy", "share", "cap ", "link", "udp ", "tcp ")) for t in texts), f"none of the {len(texts)} refusal reasons says anything about the system")
    print(" earlier behaviour")
    s4 = of(led, "simulation", 4)
    say([(r["body"]["label"], bool(r["body"].get("same_as"))) for r in s4] == [("a_again", True), ("w", False)] and not notes(led, 4), f"a design equal to a simulation of an EARLIER experiment is still returned, not run again and not refused: {[(r['body']['label'], r['body'].get('same_as')) for r in s4]}")
    n5 = [(x["part"], x["reason"]) for m in of(led, "malformed", 5) for x in m["body"]["refused"]]
    say(any(p == "drop of H4" and "cannot be dropped" in r for p, r in n5) and any(p == "report" and r.startswith(loop.NEED) for p, r in n5) and not of(led, "report", 5) and len(of(led, "report", 6)) == 1, f"a tested hypothesis cannot be dropped, and the report waits once for its verdict (turn 5: {[p for p, _ in n5]} refused; turn 6: verdict and report accepted)")
    say(meta.get("how") == "done by the model" and meta.get("report") == "R1" and (P / "sessions/t1/report.json").is_file() and meta["simulations"] == 5 and meta["turns"] == 6, f"the session ends with its report: how “{meta.get('how')}”, report {meta.get('report')}, {meta['simulations']} simulations counted (a, b, r, s, w), {meta['turns']} turns")

c1 = [(r["body"]["for"], r["body"]["decision_rule"], r["body"]["result"]) for r in of(led, "check", 1)]
say([c[0] for c in c1] == ["H1", "H2"] and all(c[2] in ("held", "failed") for c in c1) and not [n for n in n1 if n[0].startswith("decision rule")], f"a rule that names labels of different simulations, and a rule that names one label, are accepted and checked as before: {c1}")
x0 = next(r for r in led if r["id"] == "X0")
say(x0["by"] == "harness" and x0["body"]["runs"][0]["params"] == {} and led[1]["id"] == "S0" and "metrics" in led[1]["body"], "the harness's own baseline X0 still runs with an empty design (the brief's defaults)")

# ================================================================== session T2: brief two-hosts-udp-demand, policy cap
K2 = dict(queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d2(label, w, **over): return {"label": label, "params": {"weightUdp": w, **K2, **over}}
T2 = [
 turn(hypotheses=[hyp("from nowhere", ff=["Z9"]), hyp("TCP gets more when UDP's part is smaller", "Does TCP get more when UDP's part shrinks?")], verdicts=[verdict("H1")],
      experiment=ex("test", [d2("a", 0.3), d2("b", 0.5)], [rule("H2", "tcp_goodput_bps@a > tcp_goodput_bps@b", predicts="held")], ["H2"])),   # by position: the 2nd hypothesis of this answer is H2 (recorded as H1; ids by position since 2026-11-22)
 *[turn(experiment=ex("test", [d2("a", 0.3), d2("b", 0.5)], [rule("H1", "tcp_goodput_bps@a >> tcp_goodput_bps@b")], ["H1"]))] * 2,   # an unusable answer is asked for twice
 turn(experiment=ex("test", [d2("a", 0.3, udpRate="500Mbps"), d2("b", 0.5), d2("far", 7.0)], [rule("H1", "(tcp_goodput_bps@a > tcp_goodput_bps@b AND udp_loss_frac@b <= 1) OR tcp_goodput_bps@far < 0")], ["H1"])),
 "this is not JSON", "this is not JSON",
]
print("T2  scripted session on brief two-hosts-udp-demand, policy cap"); led, meta, run = session("t2", "two-hosts-udp-demand", T2, "--policy", "cap")
if run.returncode: print(run.stdout[-1500:], run.stderr[-3000:])
n1 = notes(led, 1)
say(any(p == "new hypothesis" and "Z9" in r for p, r in n1) and any(p == "verdict for H1" and "not an open hypothesis" in r for p, r in n1) and any(p == "experiment" and "would hold under the rival too" in r for p, r in n1) and len(of(led, "hypothesis", 1)) == 1 and not of(led, "simulation", 1),
    f"turn 1: an unknown follows_from id, a verdict for a hypothesis that is not open and a rule that holds under its rival are refused, the good hypothesis is kept: {[p for p, _ in n1]}")
m2 = of(led, "malformed", 2)
say(len(m2) == 1 and "cannot be read" in m2[0]["body"]["error"] and not of(led, "simulation", 2), f"turn 2: an experiment with a decision rule the harness cannot read is refused and nothing is run: {m2[0]['body']['error'][:90] if m2 else None}")
x3 = of(led, "experiment", 3)[0]["body"]; ra = next(r for r in x3["runs"] if r["label"] == "a"); rf = next(r for r in x3["runs"] if r["label"] == "far"); c3 = of(led, "check", 3)[0]["body"]
say(ra["clamped"] == {"udpRate": ["500Mbps", "300Mbps"]} and "udpRate" not in ra["params"] and list(ra["params"]) == list(meta["given"]["knobs"]) and rf["clamped"] == {"weightUdp": [7.0, 0.95]} and of(led, "simulation", 3)[0]["body"]["params"]["udpRate"] == "300Mbps",
    f"turn 3: a setting the brief fixes is still replaced and recorded ({ra['clamped']}), a value outside its range is clamped ({rf['clamped']}), and the design's params are the brief's knobs {list(ra['params'])}")
say(c3["result"] in ("held", "failed") and "AND" in c3["decision_rule"] and c3["with_numbers"].count("(") == 1, f"a rule with AND, OR and brackets is checked: {c3['with_numbers']} : {c3['result']}")
ops = [json.loads(l) for l in (P / "checks/operator.jsonl").read_text().splitlines()]
say({o["policy"] for o in ops if o["session"] == "t2"} == {"cap"} and {o["policy"] for o in ops if o["session"] == "t1"} == {"share"} and "policy" not in json.dumps(meta), "the scheduling policy is in checks/operator.jsonl only (t1 share, t2 cap), not in session.json")
m4 = of(led, "malformed", 4)
say(len(m4) == 1 and "invalid JSON" in m4[0]["body"]["error"] and meta.get("how") == "model server error" and len((P / "sessions/t2/answers.jsonl").read_text().splitlines()) == 2, f"an answer that is not JSON is a malformed record; when the model server fails the session ends cleanly: “{meta.get('how')}”; answers.jsonl holds only the 2 accepted answers")
draft = [p for p in (P / "sessions").rglob("drafts.jsonl")]
say(not draft, "no drafts.jsonl was written in these sessions (--draft off)")

if "--server" in sys.argv:
    import requests
    print(" the model server and the new params format")
    API = "http://127.0.0.1:18000/v1"; model = requests.get(API + "/models", timeout=30).json()["data"][0]["id"]
    fmt = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), tools.load_brief("two-hosts-open"))["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["params"]
    got = []
    for t in (0.0, 0.3, 0.3):
        r = requests.post(API + "/chat/completions", json={"model": model, "messages": [{"role": "user", "content": "Give one design with udpRate 400Mbps and weightUdp 0.8, stating udpRate first. Every other knob keeps its usual value: queuePkts 100, tcpVariant TcpCubic, duration 10, seed 1."}], "temperature": t, "max_tokens": 300,
                                                       "response_format": {"type": "json_schema", "json_schema": {"name": "design", "schema": fmt}}, "chat_template_kwargs": {"enable_thinking": False}}, timeout=300).json()
        got.append(json.loads(r["choices"][0]["message"]["content"]))
    say(all(list(g) == fmt["required"] and g["weightUdp"] == 0.8 and g["udpRate"] == "400Mbps" for g in got), f"asked to state udpRate first, the answer under the new format still states every knob, weightUdp 0.8 among them: {got[0]} (3 answers, all so: {all(list(g) == fmt['required'] for g in got)})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
