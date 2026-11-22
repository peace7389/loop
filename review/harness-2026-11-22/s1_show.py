"""Stage 1, items 2, 3, 4 and 12 (the coherence audit, 2026-11-22):
2. every supervisor request lists its answer's fields with what each means, from the schema (the schema reached the model server only as a constraint:
   the supervisor guessed its fields, "Need infer exact JSON schema? ... no explicit schema in user message"; "shows" held the verdict in 16 of 17
   rulings); the fields that had no description get one;
3. a simulation's network change is shown wherever a planned test is described: the review, its follow-up question, the repair, the round's record
   (s053 H1: the scheduler test was sent back as "unchanged from the default");
4. the ruling's doubt_if comes only from the supervisor's own reviews of the test, and a review without one gives none (a harness round has none: the
   ruling stopped the session with KeyError);
12. the ruling's findings have the finding's format, name included (the ruling asked for a name its schema forbade).
Usage: s1_show.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)
# 2: the fields of each answer, in its prompt
rep('''def supervise(model, user, schema):''', '''def fields_text(schema, indent="  "):
    """The fields of an answer as the model is to write them, in their order, each with what it holds (the coherence audit, 2026-11-22: the schema
    reached the model server only as a constraint, so the supervisor never saw its fields and guessed what each meant)."""
    out = []
    for k, v in (schema.get("properties") or {}).items():
        kind = ("true or false" if v.get("type") == "boolean" else "one of: " + ", ".join(map(str, v["enum"])) if v.get("enum") else
                "a list" if v.get("type") == "array" else "a number" if v.get("type") in ("number", "integer") else "text")
        out.append(f"{indent}{k} ({kind}){': ' + v['description'] if v.get('description') else ''}")
        items = v.get("items") if v.get("type") == "array" else None
        if isinstance(items, dict) and items.get("properties"):
            out.append(f"{indent}  each item of {k}:")
            out.append(fields_text(items, indent + "    "))
    return "\\n".join(out)


def supervise(model, user, schema):''')
rep('''    content = called("supervisor", model, SUPERVISOR, user, schema, True, 0, 9000)[0]''',
    '''    user += "\\n\\nYOUR ANSWER: one JSON object with these fields, in this order:\\n" + fields_text(schema)   # what each field holds (the coherence audit, 2026-11-22)
    content = called("supervisor", model, SUPERVISOR, user, schema, True, 0, 9000)[0]''')
rep('''    "rival_outcome": {"type": "string", "enum": ["held", "failed", "cannot tell"]}, "defect": {"type": "string", "enum": list(DEFECTS)}}}''',
    '''    "rival_outcome": {"type": "string", "enum": ["held", "failed", "cannot tell"], "description": "what the decision rule would give under the rival, after your answer"},
    "defect": {"type": "string", "enum": list(DEFECTS), "description": "the one defect your answer ends in, or none"}}}''')
rep('''    "result": {"type": "string", "enum": ["supported", "refuted", "inconclusive"]},
    "retest":''', '''    "result": {"type": "string", "enum": ["supported", "refuted", "inconclusive"], "description": "supported: every check held and the test was fair; refuted: a check failed and the test was fair; inconclusive: otherwise"},
    "retest":''')
# 12: the ruling's findings in the finding's format (with its name)
rep('''    "findings": {"type": "array", "maxItems": 2, "items": {"type": "object", "additionalProperties": False, "required": ["about", "text"], "properties": {
        "about": {"type": "array", "items": {"type": "string"}}, "text": {"type": "string"}}}, "description": "what the measured results leave unexplained (what, never why), at most 2; empty when nothing"}}}''',
    '''    "findings": {"type": "array", "maxItems": 2, "items": None, "description": "what the measured results leave unexplained (what, never why), at most 2; empty when nothing"}}}   # items: FINDING_ITEM, set where it is defined''')
# 3: a planned simulation's network change, wherever a test is described
rep('''    sims = "\\n".join(f"  {r['label']} {{{', '.join(f'{k}={v}' for k, v in r['params'].items())}}}" + (f"  (already run''',
    '''    sims = "\\n".join(f"  {r['label']} {{{', '.join(f'{k}={v}' for k, v in r['params'].items())}}}" + (f"; network changed: {edits_say(r['structure'])}" if r.get("structure") else "") + (f"  (already run''')
rep('''        runs = "".join(f"  {r.get('label')} {{{', '.join(f'{k}={v}' for k, v in (r.get('params') or {}).items())}}}\\n" for r in test.get("runs") or [] if isinstance(r, dict))''',
    '''        runs = "".join(f"  {r.get('label')} {{{', '.join(f'{k}={v}' for k, v in (r.get('params') or {}).items())}}}" + (f"; network changed: {edits_say(edits_of(r))}" if edits_of(r) else "") + "\\n" for r in test.get("runs") or [] if isinstance(r, dict))''')
rep('''                                                           "runs": [{"label": r.get("label"), "params": r.get("params")} for r in (test or {}).get("runs") or [] if isinstance(r, dict)]},''',
    '''                                                           "runs": [{"label": r.get("label"), "params": r.get("params"), **({"structure": r["structure"]} if r.get("structure") else {})} for r in (test or {}).get("runs") or [] if isinstance(r, dict)]},''')
# 4: doubt_if only from the supervisor's own reviews of the test; none when it has none
rep('''            doubt = next((r["body"]["doubt_if"] for r in reversed(ledger) if r["type"] == "review" and r["body"]["for"] == hid), "")''',
    '''            doubt = next((r["body"].get("doubt_if") or "" for r in reversed(ledger) if r["type"] == "review" and r.get("by") == "supervisor" and r["body"].get("gate") != "ground" and r["body"].get("for") == hid), "")   # a harness round has none (the coherence audit: KeyError stopped the session)''')
rep('''NAME_WORDS, NAME_CHARS = 6, 48   # a longer name is cut to this''', '''NAME_WORDS, NAME_CHARS = 6, 48   # a longer name is cut to this
RULING_SCHEMA["properties"]["findings"]["items"] = FINDING_ITEM   # the ruling's findings in the finding's format, name included (the coherence audit, 2026-11-22: the ruling asked for a name its schema forbade)''')
p.write_text(s); print("patched", p)
