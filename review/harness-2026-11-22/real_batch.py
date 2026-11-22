"""The new supervisor calls, made for real on the model server with thinking on and the harness's own limits: the batched first review (2 guesses,
1 test, competitors), a follow-up question (2,000 tokens: 1,000 of reasoning), a ruling with three questions. Texts from a scripted session."""
import json, sys, time
sys.path.insert(0, sys.argv[1])
import loop, requests
SES = sys.argv[2]
model = requests.get(loop.API + "/models", timeout=30).json()["data"][0]["id"]
sent = lambda sid: json.load(open(f"{SES}/{sid}/supervisor_sent.json"))
loop.COMP["on"] = True
batch_user = next(u for u in sent("j1") if "THIS REQUEST HOLDS EVERY NEW GUESS" in u)
again_user = next(u for u in sent("d1") if "These do not fit together" in u)
ruling_user = next(u for u in sent("a1") if "THE HARNESS'S CHECKS (facts)" in u)
calls_all = [("batched first review", batch_user, loop.batch_schema(["G1", "G2"], ["H1"]), 9000 + 2000 * 2), ("follow-up question", again_user, loop.AGAIN3_SCHEMA, loop.AGAIN_TOKENS),
         ("ruling, three questions", ruling_user, loop.RULING3_SCHEMA, 9000)]
calls = calls_all[:1]
bad = 0
for name, user, schema, mt in calls:
    t0 = time.time()
    content, reasoning, finish, usage = loop.ask(model, loop.SUPERVISOR, user, schema, True, 0, mt)
    rt = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
    try:
        d = json.loads(content); ok = finish == "stop" and all(k in d for k in schema["required"])
    except ValueError:
        d, ok = None, False
    bad += not ok
    ok = ok and (name != "batched first review" or [t.get("for") for t in d.get("tests") or []] == ["H1"])
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {round(time.time() - t0)} s, max_tokens {mt}, finish {finish}, {usage.get('completion_tokens')} tokens written ({rt} reasoning), {len(reasoning)} chars of reasoning")
    if d:
        show = {k: v for k, v in d.items() if k in ("honest", "consistent", "correct", "if_tested", "if_competitor", "result", "fits_tested", "fits_competitor")}
        if "guesses" in d:
            show = {"guesses": [(g.get("guess"), g.get("defect")) for g in d["guesses"]], "tests": [(t.get("for"), t.get("honest"), t.get("consistent"), t.get("correct"), t.get("if_tested"), t.get("if_competitor"), (t.get("missing") or "")[:60]) for t in d["tests"]]}
        print("      ", json.dumps(show)[:400])
print("RESULT:", "PASS" if not bad else f"FAIL {bad}")
