"""The researcher keeps what it found (2026-11-22, after s047 and s048, where it lost track of its own findings): every reading (what the tools
returned, T records) stays in the ledger text it reads in every later turn, and so do its own observations of each turn; the turn after a
request names the new readings instead of giving them a second time. Within LEDGER_TOKENS: past READINGS_ROOM characters of readings, an older
long reading is shortened and says how much was left out; short ones (measure, metrics) stay whole. The supervisor is given the same readings
(the operator, 2026-11-22: "yes for now"; test_supervised.py checks that and that it never sees the observations).
  - a scripted session of the ordinary arm: three turns of requests, then the report; its fourth request still holds every reading and every
    observation of the earlier turns, each reading once;
  - reading_forms on a ledger past the room: older long readings shortened with the words that say so, the newest four and the short ones whole;
  - the arm "plain" keeps its readings and observations the same way.
Scripted sessions.     python3 -I test_keep_readings.py SCRATCH_DIR [HARNESS_DIR]
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
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, brief, answers, *flags):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps(answers))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env=ENV, capture_output=True, text=True, timeout=1500)
    if r.returncode: print(r.stdout[-800:], r.stderr[-2500:])
    led = [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]
    return led, json.loads((P / "sessions" / sid / "users_sent.json").read_text())
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def turn(**k): return {"observations": "read", "hypotheses": [], "drop": [], "experiment": None, "verdicts": [], "report": None, "requests": [], "budget_request": None, "done": False, **k}
def plain(**k): return {"observations": "read", "experiment": None, "report": None, "requests": [], "budget_request": None, "done": False, **k}
REP = {"goal": "the larger UDP goodput", "recommendation": {"weightUdp": 0.5, **{k: v for k, v in KN.items() if k != "seed"}}, "expected": {"udp_goodput_bps": 500000000.0}, "no_difference": [], "limit": "UDP's part of the link: E0.",
       "explanation": "The baseline gives UDP its part.", "holds_when": "as measured", "breaks_when": "other rates", "claims": [{"text": "UDP gets its part.", "role": "supports", "evidence": ["E0"]}], "open_questions": []}
Q = lambda tool, **a: {"tool": tool, "args": a}
print("THE RESEARCHER KEEPS WHAT IT FOUND")
led, u = session("k1", "two-hosts-open-2", [turn(observations="OBS-ONE seen", requests=[Q("metrics", run_id="r001"), Q("measure", run_id="r001", of="udp_bps", stat="mean")]),
                                            turn(observations="OBS-TWO seen", requests=[Q("series", run_id="r001", every_n=5)]),
                                            turn(observations="OBS-THREE seen", requests=[Q("measure", run_id="r001", of="tcp_bps", stat="max")]),
                                            turn(observations="OBS-FOUR seen", report=REP, done=True)])
T = [(r["id"], r["turn"]) for r in led if r["type"] == "result"]
lines = lambda text: [f"[{i}] turn {t} reading" for i, t in T if t < 4]
say(len(T) == 4 and all(text.count(l) == 1 for text in [u[3]] for l in lines(u[3])) and all(f"turn {k} your observations: OBS-{w} seen" in u[3] for k, w in ((1, "ONE"), (2, "TWO"), (3, "THREE"))),
    f"its fourth request still holds every reading of the first three turns, each once ({[i for i, _ in T]}), and its observations of turns 1 to 3")
say("TOOL RESULTS: your last requests were answered: T1, T2, in the LEDGER above" in u[1] and u[1].count("[T1] turn 1 reading") == 1 and "[T1] turn 1 reading" in u[2],
    "the turn after a request names its readings (T1, T2) and gives each once, in the ledger; the turn after that still has T1")
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import loop
long_ = "x" * 2000; fake = []
for i in range(1, 31):
    fake += [{"id": f"Q{i}", "turn": i, "type": "request", "body": {"tool": "series", "args": {"run_id": "r001"}}}, {"id": f"T{i}", "turn": i, "type": "result", "parent": f"Q{i}", "body": {"tool": "series", "result": long_}}]
fake += [{"id": "Q31", "turn": 31, "type": "request", "body": {"tool": "measure", "args": {}}}, {"id": "T31", "turn": 31, "type": "result", "parent": "Q31", "body": {"tool": "measure", "result": "{\"value\": 2.09}"}}]
F = loop.reading_forms(fake); cut = [k for k, v in F.items() if "left out here" in v]
small = loop.reading_forms(fake[:20])
say(sum(len(v) for v in F.values()) < 30 * 2000 and cut == [f"T{i}" for i in range(1, 28)] and all(long_ in F[f"T{i}"] for i in (28, 29, 30)) and '"value": 2.09' in F["T31"] and not [v for v in small.values() if "left out" in v],
    f"past {loop.READINGS_ROOM:,} characters of readings the older long ones are shortened and say so ({len(cut)} of 30 series), the newest four and a short measure stay whole; under it nothing is shortened")
led, u = session("p1", "two-hosts-open-2", [plain(observations="PLAIN-ONE seen", requests=[Q("metrics", run_id="r001")]), plain(observations="PLAIN-TWO seen", requests=[Q("metrics", run_id="r001")]), plain(report=REP, done=True)], "--arm", "plain")
say("[T1] turn 1 reading metrics(" in u[2] and "turn 1 your observations: PLAIN-ONE seen" in u[2] and "turn 2 your observations: PLAIN-TWO seen" in u[2],
    "the arm “plain” keeps its readings and its observations the same way")
# everything recorded reaches the researcher (2026-11-22, the operator: "the most important task is to make agents access all accumulated information
# across the turns"): on the real s047 and s048 (read only), every string the ledger holds of a shown record stands in
# the ledger text of the last turn, except a code word the text gives in plain words (a defect) and the judge's readings (kept for a person,
# 2026-11-17); and the text stays within LEDGER_TOKENS
for sid in ("s047", "s048"):
    L = [json.loads(l) for l in (REAL / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()]; loop.LEDGER = REAL / "sessions" / sid / "ledger.jsonl"
    text = loop.render(L); flat = " ".join(text.split()); miss = []
    for r in L:
        if r["type"] in loop.HIDDEN: continue
        for k, v in (r.get("body") or {}).items():
            if k not in ("observations", "defect") and isinstance(v, str) and len(v.strip()) >= 12 and " ".join(v.split())[:40] not in flat: miss.append(f"{r['id']}.{k}")
    js = [r for r in L if r["type"] == "judge"]; hs = [r for r in L if r["type"] == "hypothesis"]
    say(not miss and not any(f"[{r['id']}]" in text for r in js) and all(" ".join(str(h["body"].get("why") or "").split())[:40] in flat for h in hs) and len(text) < 4 * loop.LEDGER_TOKENS,
        f"{sid}: every string of a shown record stands in the last turn's ledger text ({len(L)} records; {len(hs)} hypotheses with their question and why; the {len(js)} judge readings stay for a person, as decided 2026-11-17); missing: {miss[:5] or 'none'}; {len(text):,} characters")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
