"""Each answer format the live harness can send, sent to the real model server with thinking off: is it accepted, and filled as valid JSON?
python3 schema_smoke.py LIVE_HARNESS_DIR SUPERVISED_FORMAT PLAIN_FORMAT HYPOTHESES_FORMAT"""
import json, sys, time, copy
import requests
sys.path.insert(0, sys.argv[1])
import loop
API = loop.API
model = requests.get(API + "/models", timeout=30).json()["data"][0]["id"]
sup_fmt, plain_fmt, hyp_fmt = (json.load(open(p)) for p in sys.argv[2:5])
runs_item = sup_fmt["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]
repair_comp = {"type": "object", "additionalProperties": False, "required": ["decision_rule", "competes_with", "rival_predicts", "runs"], "properties": {
    "decision_rule": {"type": "string"}, "competes_with": {"type": "string"}, "rival_predicts": {"type": "string", "enum": ["held", "failed"]}, "runs": {"type": "array", "items": runs_item}}}
loop.COMP["on"] = True
batch_comp = loop.batch_schema(2, 2)
loop.COMP["on"] = False
batch_old = loop.batch_schema(2, 2)
small = [("REVIEW3", loop.REVIEW3_SCHEMA), ("AGAIN3", loop.AGAIN3_SCHEMA), ("RULING3", loop.RULING3_SCHEMA), ("FITS_AGAIN", loop.FITS_AGAIN_SCHEMA),
         ("GROUND_COMP", loop.GROUND_SCHEMA_COMP), ("APPEAL", loop.APPEAL_SCHEMA), ("AGAIN (stage 2)", loop.AGAIN_SCHEMA), ("REVIEW (stage 4 wording)", loop.REVIEW_SCHEMA),
         ("RULING", loop.RULING_SCHEMA), ("batch, competitors", batch_comp), ("batch, rivals", batch_old), ("repair, competitors", repair_comp),
         ("guess with competes_with", sup_fmt["properties"]["whys"]["items"])]
big = [("researcher, supervised with competitors", sup_fmt), ("researcher, plain", plain_fmt), ("researcher, hypotheses", hyp_fmt)]
def ask(schema, max_tokens):
    body = {"model": model, "temperature": 0, "max_tokens": max_tokens, "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "system", "content": "You fill a JSON format for a software test. Use short placeholder texts; for a list give the number of items it asks for."},
                         {"role": "user", "content": "Fill this format.\n" + loop.fields_text(schema)}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "turn", "schema": schema}}}
    t0 = time.time(); r = requests.post(API + "/chat/completions", json=body, timeout=600)
    return r.status_code, r.json(), round(time.time() - t0, 1)
bad = 0
for name, sc in small:
    code, j, sec = ask(copy.deepcopy(sc), 3000)
    if code != 200:
        bad += 1; print(f"REFUSED  {name}: {code} {json.dumps(j)[:300]}"); continue
    ch = j["choices"][0]; txt = ch["message"].get("content") or ""
    try:
        d = json.loads(txt); ok = all(k in d for k in sc.get("required", []))
        lens = {k: len(v) for k, v in d.items() if isinstance(v, list)}
        print(f"{'ok      ' if ok else 'MISSING '} {name}: accepted, filled ({ch['finish_reason']}, {sec} s){' lists ' + str(lens) if lens else ''}")
        bad += not ok
    except ValueError:
        bad += 1; print(f"NOT JSON {name}: {ch['finish_reason']} {txt[:200]}")
for name, sc in big:
    code, j, sec = ask(copy.deepcopy(sc), 120)
    print(f"{'ok      ' if code == 200 else 'REFUSED '} {name}: {'accepted by the server' if code == 200 else json.dumps(j)[:300]} ({sec} s)")
    bad += code != 200
print("RESULT:", "PASS" if not bad else f"FAIL {bad}")
