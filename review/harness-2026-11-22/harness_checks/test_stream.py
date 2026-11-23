"""The calls of the model are streamed (2026-11-22, the operator: "When user clicks past or ongoing stage here they should be able to see tokens
directly"): one small real call to the local model server (the one sessions use; SKIP when it does not answer) through loop.called():
  - the answer comes back as before: an answer that is the JSON object of the schema, the text before it (reasoning), why it stopped, the token counts;
  - while it comes in and at its end, live_call.json says it: its number, turn, agent, step (as calls.jsonl has it, since stage 3 of the coherence
    audit), what was written so far, and at the end done;
  - its line in calls.jsonl names the step (now.json's) it was made in.
python3 -I test_stream.py SCRATCH_DIR [HARNESS_DIR]"""
import json, os, sys, threading, time
from pathlib import Path
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else Path.home() / "project/harness"
assert "scratch" in str(SCR)
SCR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SRC))
import loop, requests
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
try:
    model = requests.get(loop.API + "/models", timeout=10).json()["data"][0]["id"]
except Exception as e:
    print(f"RESULT: SKIP the model server does not answer ({type(e).__name__})"); sys.exit(0)
loop.tools.SESSION = SCR
for f in ("calls.jsonl", "live_call.json"):
    (SCR / f).unlink(missing_ok=True)
loop.CALLS["turn"] = 4
loop.stage("ruling", "H7")
seen = []
def watch():
    for _ in range(200):
        p = SCR / "live_call.json"
        if p.is_file():
            try: seen.append(json.loads(p.read_text()))
            except ValueError: pass
        time.sleep(0.25)
        if seen and seen[-1].get("done"): return
th = threading.Thread(target=watch); th.start()
schema = {"type": "object", "additionalProperties": False, "required": ["count", "word"], "properties": {"count": {"type": "integer"}, "word": {"type": "string"}}}
print("A REAL CALL, STREAMED")
content, reasoning, finish, usage = loop.called("supervisor", model, "Answer with one JSON object.", "Count the letters of the word network, then give the word and the count. Think it through first.",
                                                schema, True, 0, 2000)
th.join()
a = json.loads(content)
say(a == {"count": 7, "word": "network"} or (isinstance(a.get("count"), int) and a.get("word")), f"the answer is the schema's object: {content.strip()[:80]}")
say(reasoning.strip() and finish == "stop" and usage.get("completion_tokens", 0) > 0 and (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) > 0,
    f"the text before it ({len(reasoning)} characters), why it stopped ({finish}) and the token counts ({usage.get('completion_tokens')}, of them reasoning {(usage.get('completion_tokens_details') or {}).get('reasoning_tokens')}) as before")
last = seen[-1] if seen else {}
say(seen and not seen[0].get("done") and last.get("done") and last.get("agent") == "supervisor" and last.get("step") == {"step": "ruling", "about": "H7", "round": None, "by": None} and last.get("turn") == 4
    and last.get("answer") == content and last.get("reasoning") == reasoning and last.get("n") == loop.CALLS["n"],
    f"live_call.json while it ran and at its end: {len(seen)} readings, the first not done, the last done, with agent, step, turn and the whole text ({[(x.get('done'), len(x.get('reasoning') or '')) for x in seen[:4]]} …)")
line = json.loads((SCR / "calls.jsonl").read_text().splitlines()[-1])
say(line.get("step") == {"step": "ruling", "about": "H7", "round": None, "by": None} and line["answer"] == content, f"its line in calls.jsonl names the step: {line.get('step')}")
print("RESULT:", "PASS" if not FAILED else "FAIL " + " | ".join(FAILED))
