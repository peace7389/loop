"""The short answer format of the arm "hypotheses" (2026-11-22, the operator: trim the fields that repeat something else or carry almost no
information, the way the arm "supervised" was trimmed on 2026-11-18). Dropped: why.worth and why.reason, hypothesis.prediction and follows_from,
experiment.varied, control and needs, budget_request. Kept: a hypothesis's question and why (the operator: "User should read the detail when they
click"), why.unseen and matters, each rule's rival, rethinks, verdicts, the whole report. The operator's decisions: a guess never taken up does not
hold back the report; varied is worked out from the designs as trim compares them, in both arms; the turn's text of the arm "supervised" no longer
names budget_request either.
  - the answer format lacks the eight fields and keeps the rest; the instructions name none of them; the arm "plain" keeps budget_request;
  - on the real s048 (read only, no simulation): a short answer is made whole (short_fill), its hypothesis follows from what its why is about
    (a reading, T10: refused before in this arm), the judge is given the decision rule of its test, needs and varied are worked out;
  - a report with a guess never taken up: held back in the full format, not in the short one;
  - a scripted session in short answers: its test runs (two designs written differently in a setting that rounds to the same value: varied
    names only the knob that differs), the check is made, the report ends the session; the session records the format "short", the format
    sent to the model and the turn's text have no dropped field; the arm "supervised"'s turn names no budget_request, the arm "plain"'s does;
  - a session started before (no format flag) keeps the full format when it goes on; score.py does not read loop.py.
python3 -I test_short_format.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new. Simulations are real ns-3 runs of 2 measured seconds."""
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
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import loop
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
DROPPED = {"whys": ("worth", "reason"), "hypotheses": ("prediction", "follows_from"), "experiment": ("varied", "control", "needs"), "": ("budget_request",)}

print("THE FORMAT AND THE INSTRUCTIONS")
brief2 = loop.tools.load_brief("two-hosts-open-2")
whole = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), brief2)
short = loop.short_format(json.loads(json.dumps(whole)))
props = lambda f, part: (f["properties"] if not part else f["properties"][part]["items"]["properties"] if part != "experiment"
                         else next(x for x in f["properties"]["experiment"].get("anyOf", [f["properties"]["experiment"]]) if x.get("type") == "object")["properties"])
gone = {part: [k for k in ks if k in props(short, part)] for part, ks in DROPPED.items()}
kept = {part: sorted(set(props(whole, part)) - set(ks)) for part, ks in DROPPED.items()}
rules = props(short, "experiment")["decision_rules"]["items"]["properties"]
say(not any(gone.values()) and {"question", "why", "text", "from_why"} <= set(props(short, "hypotheses")) and {"unseen", "matters", "result", "guess", "about"} <= set(props(short, "whys"))
    and {"rival", "rival_predicts", "decision_rule"} <= set(rules),
    f"the short format lacks the eight fields ({sum(map(len, DROPPED.values()))} dropped, none left: {gone}) and keeps the rest: a hypothesis has {list(props(short, 'hypotheses'))}, "
    f"a why {list(props(short, 'whys'))}, a rule {list(rules)}")
say(all(set(kept[p]) <= set(props(short, p)) for p in DROPPED) and {"rethink", "verdicts", "report", "whys"} <= set(props(short, "")) and props(short, "")["report"] == whole["properties"]["report"],
    "every other field of the full format is there, and the report's format is the full one")
full = (P / "harness/prompt.txt").read_text(); sp = loop.short_prompt(full)
words = ("budget_request", "follows_from", "to_know", "prediction", "varied:", "control:", "needs:", "worth is verify", "set_aside if not")
say(not [w for w in words if w in sp] and all(w in sp for w in ("rival", "rethink", "unseen", "matters", "question", "decision rule")) and len(sp) < len(full),
    f"the instructions name none of them ({[w for w in words if w in sp] or 'none found'}), keep the rest, and are shorter ({len(full)} -> {len(sp)} characters)")
say("budget_request" in loop.plain_prompt(full) and "budget_request" in loop.plain_format(json.loads(json.dumps(whole)))["properties"],
    "the arm “plain” keeps budget_request, in its instructions and its format")

print("ON THE REAL s048 (read only)")
D = REAL / "sessions/s048"
led = [json.loads(l) for l in (D / "ledger.jsonl").read_text().splitlines() if l.strip()]   # read by the harness's own functions; nothing of it is printed but ids
brief = json.loads((D / "session.json").read_text())["given"]; loop.LEDGER = D / "ledger.jsonl"; loop.tools.BRIEF = brief
u6 = next(i for i, r in enumerate(led) if r["type"] == "turn" and r["turn"] == 6); at6 = led[:u6 + 1]
y = f"Y{sum(r['type'] == 'why' for r in at6) + 1}"; h = f"H{sum(r['type'] == 'hypothesis' for r in at6) + 1}"
Q, T = "l1.queue.length", "tcp.type"
rule = f"tcp_goodput_bps@long > tcp_goodput_bps@short"
due = [{"id": "Y9", "in_light_of": ["C7"], "now": "supported", "because": "C7 held"}]   # due at s048's turn 6 (H7: C7 held)
ans = {"observations": "read", "rethink": due, "drop": [], "verdicts": [], "report": None, "requests": [], "done": False,
       "whys": [{"about": ["T10"], "result": "TCP's window stays at the receiver's", "guess": "the receiver's window limits TCP", "unseen": "the receive buffer", "matters": "it caps TCP's goodput"}],
       "hypotheses": [{"from_why": y, "text": "a longer queue does not raise TCP's goodput", "question": "Does the queue's length change what TCP delivers?", "why": "If the receiver's window limits it, it should not."}],
       "experiment": {"kind": "test", "tests": [h], "question": "Is TCP limited by the queue or by the receiver?", "measurements": [],
                      "runs": [{"label": "short", "params": {Q: 37, T: "TcpNewReno"}}, {"label": "long", "params": {Q: 777, T: "TcpNewReno"}}],
                      "decision_rules": [{"for": h, "decision_rule": rule, "rival": "the queue limits TCP", "rival_predicts": "failed"}]}}
given = []
def judge(why, hyp): given.append(hyp); return True, "the check's judge"
t = loop.short_fill(json.loads(json.dumps(ans)), brief)
say(t["whys"][0]["worth"] == "verify" and t["hypotheses"][0]["prediction"] is None and t["hypotheses"][0]["follows_from"] == [] and t["experiment"]["varied"] == [Q]
    and t["experiment"]["control"] is None and t["budget_request"] is None and "needs" not in t["experiment"],
    f"short_fill makes the answer whole: worth verify, no prediction, follows_from empty, varied worked out ({t['experiment']['varied']}), no control or budget_request; needs are left to sort_out")
ok, no = loop.sort_out(t, brief, at6, 10, None, judge=judge, short=True)
hy = ok["hypotheses"][0] if ok["hypotheses"] else {}; ex = ok["experiment"] or {}
say(hy.get("follows_from") == ["T10"] and not [w for p, w in no if p.startswith("hypothes") or p == "new why"],
    f"its hypothesis follows from what its why is about, the reading T10 ({hy.get('follows_from')}; refused before in this arm: a reading was not among the records a hypothesis may follow from) {[w for p, w in no][:2]}")
say(given and given[0].get("rules") == [rule], f"the judge is given the decision rule of its test in place of a prediction ({given[0].get('rules') if given else None})")
nd = (ex.get("needs") or [{}])[0]
say(ex.get("varied") == [Q] and nd.get("for") == h and nd.get("varies") == Q and sorted(nd.get("simulations") or []) == ["long", "short"] and "tcp_goodput_bps" in str(nd.get("measure")),
    f"needs and varied are worked out from the rules and the designs ({ex.get('varied')}; {nd})")
said = {}
def fake_ask(model, system, user, schema, draft, temperature, max_tokens): said["user"] = user; return json.dumps({"follows": True, "because": "yes"}), "", "stop", {}
was_ask, loop.ask = loop.ask, fake_ask
try:
    loop.judge_link("m", brief, {"guess": "the receiver's window limits TCP", "result": "r", "unseen": "u", "matters": "m", "about": ["T10"]}, {"text": "a longer queue does not raise it", "prediction": None, "rules": [rule]})
except Exception as e:
    said.setdefault("user", f"(error {type(e).__name__}: {e})")
finally:
    loop.ask = was_ask
say("the decision rule of its test: " + rule in said.get("user", ""), f"the judge's request says the rule where the prediction stood (“{said.get('user', '').split('Its prediction: ', 1)[-1][:90]}”)")

print("A GUESS NEVER TAKEN UP")
u7 = next(i for i, r in enumerate(led) if r["type"] == "turn" and r["turn"] == 7); at7 = led[:u7 + 1]; answers = {json.loads(l)["turn"]: json.loads(l)["answer"] for l in (D / "answers.jsonl").read_text().splitlines() if l.strip()}
y7 = f"Y{sum(r['type'] == 'why' for r in at7) + 1}"
extra = {"about": ["T10"], "result": "TCP's window stays at the receiver's", "guess": "a guess never taken up", "unseen": "the receive buffer", "matters": "it caps TCP"}
rep = {**answers[7], "whys": [{**extra, "worth": "verify", "reason": "it serves the goal"}], "hypotheses": [], "experiment": None, "done": True}
okF, noF = loop.sort_out(json.loads(json.dumps(rep)), brief, at7, 1, None, judge=None)
okS, noS = loop.sort_out(loop.short_fill({**json.loads(json.dumps(rep)), "whys": [dict(extra)]}, brief), brief, at7, 1, None, judge=None, short=True)
held = lambda ok, no: ok["report"] is None and any(y7 in str(w) and "worth verifying" in str(w) for p, w in no)
say(held(okF, noF) and okS["report"] is not None and okS["whys"] and not held(okS, noS),
    f"s048's final report with a new guess ({y7}) never taken up: the full format holds the report back ({[str(w)[:80] for p, w in noF if 'worth' in str(w)][:1]}), the short one takes it")

print("A SCRIPTED SESSION IN SHORT ANSWERS")
def session(sid, brief, answers, *flags):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps(answers))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env=ENV, capture_output=True, text=True, timeout=1500)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    S = P / "sessions" / sid
    led = [json.loads(l) for l in (S / "ledger.jsonl").read_text().splitlines() if l.strip()] if (S / "ledger.jsonl").is_file() else []
    return led, json.loads((S / "session.json").read_text()), json.loads((S / "users_sent.json").read_text()), json.loads((S / "format_sent.json").read_text())
of = lambda led, ty, turn=None: [r for r in led if r["type"] == ty and (turn is None or r["turn"] == turn)]
KN = dict(udpRate="2Gbps", tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w, q=100): return {"label": label, "params": {"weightUdp": w, "queuePkts": q, **KN}}
def turn(**k): return {"observations": "read", "rethink": [], "whys": [], "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "done": False, **k}
W1 = {"about": ["E0"], "result": "UDP gets about half of the link", "guess": "the scheduler gives each flow its part", "unseen": "how it divides the link", "matters": "it decides the answer"}
W2 = {**W1, "guess": "UDP's own rate limits it", "unseen": "UDP's sending rate"}
REP = {"goal": "the larger UDP goodput", "recommendation": {"weightUdp": 0.7, "queuePkts": 100, **{k: v for k, v in KN.items() if k != "seed"}}, "expected": {"udp_goodput_bps": 685000000.0}, "no_difference": [],
       "limit": "UDP's part of the link: E1.", "explanation": "UDP's goodput follows its part of the link.", "holds_when": "as tested", "breaks_when": "other rates",
       "claims": [{"text": "A larger part gives UDP more.", "role": "supports", "evidence": ["E1"]}], "open_questions": []}
ANS = [turn(whys=[W1, W2], hypotheses=[{"from_why": "Y1", "text": "UDP goodput rises with its part", "question": "Does UDP get more when its part is larger?", "why": "The goal is about what UDP delivers."}],
            experiment={"kind": "test", "tests": ["H1"], "question": "Does the part change what UDP gets?", "measurements": [], "runs": [d("a", 0.3), d("b", 0.7, 100.4)],
                        "decision_rules": [{"for": "H1", "decision_rule": "udp_goodput_bps@b > udp_goodput_bps@a", "rival": "UDP's own rate limits it", "rival_predicts": "failed"}]}),
       turn(rethink=[{"id": "Y1", "in_light_of": ["C1"], "now": "supported", "because": "C1 held"}], verdicts=[{"for": "H1", "result": "supported", "because": "C1 held", "next": "report"}], report=REP, done=True)]
led1, meta, users, fmt = session("h1", "two-hosts-open-2", ANS, "--budget", "6")
x = (of(led1, "experiment", 1) or [{}])[0].get("body", {}); hy = (of(led1, "hypothesis", 1) or [{}])[0].get("body", {}); c = of(led1, "check"); n = (x.get("needs") or [{}])[0]
say(x.get("varied") == ["weightUdp"] and x.get("control") is None and n.get("varies") == "weightUdp" and sorted(n.get("simulations") or []) == ["a", "b"] and len(of(led1, "simulation", 1)) == 2,
    f"its test runs: two designs written with queuePkts 100 and 100.4 (the same after rounding): varied {x.get('varied')} (before, both knobs, and the test was refused), needs worked out ({n.get('varies')}, {n.get('simulations')})")
say(hy.get("prediction") is None and hy.get("follows_from") == ["E0"] and hy.get("question") and hy.get("why") and c and c[0]["body"].get("result") == "held",
    f"its hypothesis keeps its question and why, follows from E0 (its why's about), and its check is made ({c[0]['body'].get('result') if c else None})")
say(of(led1, "report") and meta.get("how") == "done by the model" and any(r["body"].get("guess") == W2["guess"] for r in of(led1, "why")),
    f"the report ends the session ({meta.get('how')}), with Y2 never taken up")
fh = fmt["properties"]
say(meta["flags"].get("format") == "short" and "arm" not in meta["flags"] and "budget_request" not in fh and "prediction" not in fh["hypotheses"]["items"]["properties"]
    and "worth" not in fh["whys"]["items"]["properties"] and not any("budget_request" in u for u in users) and meta.get("prompt") == loop.short_prompt(full),
    "the session records the format “short”; the format sent to the model and every turn's text name no dropped field; its instructions are the short ones")
_, metaS, usersS, _ = session("s1", "two-hosts-open-2", {"answers": []}, "--arm", "supervised", "--budget", "6")
_, metaP, usersP, _ = session("p1", "two-hosts-open-2", [], "--arm", "plain", "--budget", "6")
say(usersS and not any("budget_request" in u for u in usersS) and usersP and "budget_request can raise that" in usersP[0],
    "the arm “supervised”: its turn names no budget_request any more; the arm “plain”: its turn still does")
_, metaO, usersO, _ = session("o1", "two-hosts-open-2", [], "--budget", "6")
m = P / "sessions/o1/session.json"; j = json.loads(m.read_text()); j["flags"].pop("format", None); m.write_text(json.dumps(j))
_, metaO, usersO, fmtO = session("o1", "two-hosts-open-2", [], "--budget", "6")
say("format" not in metaO["flags"] and "prediction" in fmtO["properties"]["hypotheses"]["items"]["properties"] and "budget_request" in fmtO["properties"] and "budget_request can raise that" in usersO[0],
    "a session started before (no format flag) keeps the full format when it goes on: the format, and the turn's text naming budget_request")
sc = (P / "harness/score.py").read_text()
say("import loop" not in sc and "from loop" not in sc, "score.py does not read loop.py: the scores of earlier sessions cannot change with it")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
