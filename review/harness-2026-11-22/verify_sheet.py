# verifications 1, 2 and 4 of the sheet (2026-11-22): GitHub's loop.py (before) against the work copy's (after), on the real s047 and s048
import importlib.util, json, sys, re
from pathlib import Path
P = Path.home() / "project"; S = Path(sys.argv[1]); sys.path.insert(0, str(P / "harness"))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
before, after = load("loop_before", S / "harness_github/loop.py"), load("loop_after", S / "work/home/project/harness/loop.py")
led = [json.loads(l) for l in open(P / "sessions/s048/ledger.jsonl") if l.strip()]
meta = json.load(open(P / "sessions/s048/session.json")); brief = meta["given"]
for m in (before, after): m.LEDGER = P / "sessions/s048/ledger.jsonl"
# 1. what the researcher reads at turn 7: the ledger as it stood before turn 7's turn record
u7 = next(i for i, r in enumerate(led) if r["type"] == "turn" and r["turn"] == 7)
want = {"tcp_rtt_ms mean 2.09": "2.090693", "tcp_inflight mean 137459": "137459.643564", "tcp_rwnd 1048576": "1048576.0"}
for name, m in (("before (GitHub 6c90598)", before), ("after (work copy)", after)):
    text = m.render(led[:u7])
    print(f"1. {name}: turn 7's ledger text, {len(text):,} characters; r010's measurements in it:", {k: v in text for k, v in want.items()})
    if m is after:
        for line in text.splitlines():
            if any(v in line for v in want.values()): print("     ", line.strip()[:190])
        print("     observation lines:", sum(1 for l in text.splitlines() if " your observations: " in l))
# 2. the turn-6 answer through sort_out, with the ledger as it stood when it came (after turn 6's turn record)
u6 = next(i for i, r in enumerate(led) if r["type"] == "turn" and r["turn"] == 6); t6 = next(json.loads(l)["answer"] for l in open(P / "sessions/s048/answers.jsonl") if json.loads(l)["turn"] == 6)
left, mode = led[u6]["body"]["simulations_left"], led[u6]["body"].get("last_turn")
for name, m in (("before", before), ("after", after)):
    ok, no = m.sort_out(json.loads(json.dumps(t6)), brief, led[:u6 + 1], left, mode, judge=None)
    y11 = [k for k in ok["rethink"] if k["id"] == "Y11"]
    print(f"2. {name}: rethink of Y11 citing r010 -> {'ACCEPTED, in the light of ' + ', '.join(y11[0]['in_light_of']) if y11 else 'refused: ' + next((w for p, w in no if 'Y11' in p), '?')[:150]}")
# 4. the size of the whole rendered ledger
for sid in ("s047", "s048"):
    L = [json.loads(l) for l in open(P / f"sessions/{sid}/ledger.jsonl") if l.strip()]; after.LEDGER = P / f"sessions/{sid}/ledger.jsonl"
    text = after.render(L); model = json.load(open(P / f"sessions/{sid}/session.json"))["model"]
    print(f"4. {sid}: rendered ledger after the change: {len(text):,} characters = {after.count_tokens(model, text):,} tokens of LEDGER_TOKENS {after.LEDGER_TOKENS:,}")
