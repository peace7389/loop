"""Replay the supervisor's reviews of the tests of s063: each request as it was sent (calls.jsonl: what was given), once with the questions as
they were (v2) and once with v2.1's wording of Follows and Honest. Only answers are kept; the model's reasoning is not read or stored."""
import sys, json, re, importlib.util, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
OLD_H, NEW_H, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
def load(name, d):
    sys.path.insert(0, str(d))
    for m in ('tools', 'decision_rules', 'session_figures', 'network', 'loop'): sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location(name, d / 'loop.py'); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); sys.path.pop(0); return mod
old, new = load('loop_old', OLD_H), load('loop_new', NEW_H)
old.COMP["on"] = new.COMP["on"] = True
PAIRS = [(old.QUESTIONS["follows"], new.QUESTIONS["follows"]), (old.QUESTIONS["honest"], new.QUESTIONS["honest"]),
         (old.REVIEW3_SCHEMA["properties"]["follows_why"]["description"], new.REVIEW3_SCHEMA["properties"]["follows_why"]["description"]),
         (old.REVIEW3_SCHEMA["properties"]["honest_why"]["description"], new.REVIEW3_SCHEMA["properties"]["honest_why"]["description"])]
rows = [json.loads(l) for l in (Path.home() / 'project/sessions/s063/calls.jsonl').read_text().splitlines() if l.strip()]
jobs = []
for q in rows:
    st = q.get('step') or {}
    if q.get('agent') != 'supervisor' or 'Follows: ' + old.QUESTIONS["follows"] not in (q.get('user') or ''): continue
    user = q['user']; batch = st.get('step') == 'review'
    assert q['system'] == old.SUPERVISOR, 'the system text is not v2\'s'
    gs, ts = re.findall(r"^== NEW GUESS (G\d+) ==$", user, flags=re.M), re.findall(r"^== TEST OF (\S+) ==$", user, flags=re.M)
    user2 = user
    for a, b in PAIRS:
        assert a in user2, a[:60]; user2 = user2.replace(a, b)
    for which, mod, u in (('as it was', old, user), ('v2.1', new, user2)):
        schema = mod.batch_schema(gs, ts) if batch else mod.REVIEW3_SCHEMA
        jobs.append({'n': q['n'], 'turn': q['turn'], 'step': st, 'which': which, 'tests': ts if batch else [st.get('about')], 'round': 1 if batch else st.get('round'), 'system': mod.SUPERVISOR, 'user': u, 'schema': schema, 'max': q['max_tokens'], 'model': q['model'], 'mod': mod,
                     'recorded': json.loads(q['answer']) if (q.get('answer') or '').startswith('{') else None})
print(len(jobs), 'calls', flush=True)
def run(j):
    try:
        content, _reasoning, finish, usage = j['mod'].ask(j['model'], j['system'], j['user'], j['schema'], True, 0, j['max'])
        return {k: j[k] for k in ('n', 'turn', 'step', 'which', 'tests', 'round', 'recorded')} | {'finish': finish, 'answer': json.loads(content) if content.strip().startswith('{') else None, 'raw_len': len(content)}
    except Exception as e:
        return {k: j[k] for k in ('n', 'turn', 'step', 'which', 'tests', 'round', 'recorded')} | {'error': f'{type(e).__name__}: {e}'[:300]}
with ThreadPoolExecutor(4) as ex:
    res = []
    for r in ex.map(run, jobs):
        res.append(r); print('done', r['n'], r['which'], r.get('finish') or r.get('error'), flush=True)
OUT.write_text(json.dumps(res, indent=1) + '\n'); print('written', OUT)
