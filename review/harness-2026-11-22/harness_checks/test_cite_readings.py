"""Readings count as evidence (2026-11-22, after s047 and s048): what the tools returned (T records) may be cited by a rethink, a why and the
final report's claims, by their T id or by the run id they are about; and a reading the researcher saw after a why was last settled counts as a
new result for that why's rethink. Shown on the real s048 (read only): in its turn 6 the rethink of Y11 "in the light of r010" (its
measurements T10 to T12) was refused, note N2.
  - s048's turn-6 answer, run through sort_out with the ledger as it stood: the rethink of Y11 is accepted, in the light of r010's simulation
    and its readings; the same rethink naming only an old record (S9) is still refused (a rethink must rest on something new);
  - a rethink naming a reading by its T id is accepted; a why of the ordinary arm whose about names a reading is accepted;
  - the final report's claims may cite a reading (T10) and a run (r010, kept as its simulation S9);
  - a reading alone does not make a why due for a rethink (since() without readings lists no T record).
No simulation is run.     python3 -I test_cite_readings.py SCRATCH_DIR [HARNESS_DIR]"""
import json, os, shutil, sys
from pathlib import Path
REAL = Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import loop
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
D = REAL / "sessions/s048"
led = [json.loads(l) for l in (D / "ledger.jsonl").read_text().splitlines() if l.strip()]   # read by the harness's own functions; nothing of it is printed but ids
brief = json.loads((D / "session.json").read_text())["given"]; loop.LEDGER = D / "ledger.jsonl"; loop.tools.BRIEF = brief   # as a session sets it (tools.clamp reads it)
answers = {json.loads(l)["turn"]: json.loads(l)["answer"] for l in (D / "answers.jsonl").read_text().splitlines() if l.strip()}
u6 = next(i for i, r in enumerate(led) if r["type"] == "turn" and r["turn"] == 6); at6 = led[:u6 + 1]; left6 = led[u6]["body"]["simulations_left"]
def run(t, ledger=at6, left=left6, mode=None): return loop.sort_out(json.loads(json.dumps(t)), brief, ledger, left, mode, judge=None)
def rethink_of(ok, no, y): k = next((k for k in ok["rethink"] if k["id"] == y), None); return k, next((w for p, w in no if p == f"rethink of {y}"), None)
print("READINGS AS EVIDENCE")
t6 = answers[6]; ok, no = run(t6); k, why = rethink_of(ok, no, "Y11")
say(k is not None and {"S9", "T10", "T11", "T12"} <= set(k["in_light_of"]) and k["now"] == "refuted",
    f"s048, turn 6: the rethink of Y11 “in the light of r010” is accepted (in the light of {k['in_light_of'] if k else None}; refused before, note N2: {why})")
old = {**t6, "rethink": [{**q, "in_light_of": ["S9"]} if q.get("id") == "Y11" else q for q in t6["rethink"]]}; ok, no = run(old); k, why = rethink_of(ok, no, "Y11")
say(k is None and why and "came in after Y11 was last settled" in why and "T10" in why, f"the same rethink naming only S9 (run in turn 3, before Y11) is still refused, and the reason names what is new since: “{(why or '')[:150]}”")
byt = {**t6, "rethink": [{**q, "in_light_of": ["T11"]} if q.get("id") == "Y11" else q for q in t6["rethink"]]}; ok, no = run(byt); k, why = rethink_of(ok, no, "Y11")
say(k is not None and k["in_light_of"] == ["T11"], f"a rethink of Y11 naming the reading T11 by its id is accepted ({k['in_light_of'] if k else why})")
w0 = next(w for t in sorted(answers) for w in (answers[t].get("whys") or []) if isinstance(w, dict) and w.get("about"))
why_t = {**t6, "rethink": t6["rethink"], "whys": [{**w0, "about": ["T10"], "revises": None}], "hypotheses": [], "experiment": None}
ok, no = run(why_t); bad = [w for p, w in no if p == "new why"]
say(len(ok["whys"]) == 1 and ok["whys"][0]["about"] == ["T10"] and not bad, f"a why of the ordinary arm about the reading T10 is accepted ({bad[:1] or 'no refusal'})")
u7 = next(i for i, r in enumerate(led) if r["type"] == "turn" and r["turn"] == 7); t7 = answers[7]; rep = json.loads(json.dumps(t7["report"]))
rep["claims"] = [{**rep["claims"][0], "evidence": list(rep["claims"][0]["evidence"]) + ["T10", "r010"]}] + rep["claims"][1:]
ok, no = run({**t7, "report": rep}, led[:u7 + 1], led[u7]["body"]["simulations_left"], led[u7]["body"].get("last_turn"))
ev = (ok["report"] or {}).get("claims", [{}])[0].get("evidence", [])
say(ok["report"] is not None and "T10" in ev and "S9" in ev and "r010" not in ev, f"the final report's claim may cite the reading T10 and the run r010 (kept as its simulation S9): {ev} {[w for p, w in no if p == 'report'][:1]}")
ws = loop.why_states(led[:u6 + 1]); at = ws["Y11"]["at"]
say(not [x for x in loop.since(led, at) if x.startswith("T")] and {"T10", "T11", "T12"} <= set(loop.since(led, at, readings=True)),
    f"a reading alone does not make Y11 due for a rethink ({loop.since(led, at)[:6]}); for its rethink the readings seen since count too ({[x for x in loop.since(led, at, readings=True) if x.startswith('T')]})")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
