"""What the supervisor of a supervised session did, counted from the session's ledger (draft and scratch records are skipped; drafts.jsonl is never opened):
    python3 -I supervisor_figures.py SESSION_DIR
How many guesses it read and what it found; how many tests it reviewed and what it decided; its rulings beside the harness's checks; objections and
second looks; and what the researcher did after a send-back. Prints text; writes nothing."""
import json, sys, collections
from pathlib import Path
D = Path(sys.argv[1]); led = [json.loads(l) for l in (D / "ledger.jsonl").read_text().splitlines() if l.strip()]
led = [r for r in led if r["type"] not in ("draft", "scratch")]
meta = json.loads((D / "session.json").read_text()); of = lambda t: [r for r in led if r["type"] == t]
cut = lambda s, n=230: " ".join(str(s).split())[:n]
print(f"{meta['id']} · brief {meta['brief']} · arm {meta['flags'].get('arm', 'hypotheses')} · {meta.get('how', 'running')} · turns {meta.get('turns')} · simulations {meta.get('simulations')} · model calls of the researcher {meta.get('calls')}")
sup = [r for r in led if r.get("by") == "supervisor"]; print(f"records: {len(led)}, of them the supervisor's {len(sup)}; guesses {len(of('why'))}, hypotheses {len(of('hypothesis'))}, experiments {len(of('experiment'))}, checks {len(of('check'))}, requests {len(of('request'))} ({dict(collections.Counter(r['body'].get('tool') for r in of('request')))})")
g0 = [r for r in of("review") if r["body"].get("gate") == "ground"]; g1 = [r for r in of("review") if r["body"].get("gate") != "ground"]
print(f"\nGATE 0, guesses read against their records: {len(g0)}: {dict(collections.Counter(r['body']['decision'] for r in g0))}; defects {dict(collections.Counter(r['body']['defect'] for r in g0))}")
for r in g0:
    b = r["body"]; print(f"  [{r['id']} t{r['turn']}] {b['decision']:9s} {b['defect']:18s} {b.get('for') or '(refused)'}: guess “{cut(b.get('guess') or next((w['body']['guess'] for w in of('why') if w['id'] == b.get('for')), ''), 110)}” | records show: {cut(b['records_show'], 150)} | {cut(b['because'], 170)}")
print(f"\nGATE 1, tests reviewed before any simulation: {len(g1)}: {dict(collections.Counter(r['body']['decision'] for r in g1))}; defects {dict(collections.Counter(r['body']['defect'] for r in g1))}; its own rival's outcome {dict(collections.Counter(r['body']['rival_outcome'] for r in g1))}")
for r in g1:
    b = r["body"]; print(f"  [{r['id']} t{r['turn']}] {b['decision']:9s} {b['defect']:18s} {b['for']}: rule {cut(b['rules'][0] if b.get('rules') else '', 90)} | rival: {cut(b['rival'], 120)} ({b['rival_outcome']}) | {cut(b['because'], 170)}")
checks = {c["id"]: c["body"] for c in of("check")}; v = [r for r in of("verdict") if r.get("by") == "supervisor"]
pairs = collections.Counter(("+".join(sorted({checks[c]["result"] for c in r["body"].get("checks", []) if c in checks})) or "?", r["body"]["result"], "fair" if r["body"].get("fair", True) else "not fair") for r in v if not r["body"].get("after"))
print(f"\nGATE 2, rulings: {len([r for r in v if not r['body'].get('after')])}; (the checks -> the ruling): {dict(pairs)}; changed by the harness {sum(1 for r in v if r['body'].get('changed_by_harness'))}")
for r in v:
    b = r["body"]; print(f"  [{r['id']} t{r['turn']}] {b['for']} {b['result']:12s} {'fair' if b.get('fair', True) else 'NOT FAIR: ' + str(b.get('defect'))}{' (after ' + b['after'] + ': ' + ('stands' if b.get('stands') else 'changed') + ')' if b.get('after') else ''} | {cut(b['because'], 200)}" + (f" | fair test: {cut(b['next'], 120)}" if b.get("next") else ""))
ob = of("objection"); print(f"\nOBJECTIONS of the researcher: {len(ob)}")
for o in ob: print(f"  [{o['id']} t{o['turn']}] to {o['body']['to']}: {cut(o['body']['because'], 220)}")
notes = [r for r in of("note") if r["body"].get("part")]; print(f"\nrefused parts: {len(notes)}: {dict(collections.Counter(r['body']['part'].split(' for ')[0].split(' of ')[0] for r in notes))}; malformed answers {len(of('malformed'))}")
rep = of("report")
if rep:
    b = rep[-1]["body"]; print(f"\nREPORT: recommends {b.get('recommendation')} | limit: {cut(b.get('limit'), 260)}"); kinds = {r["id"]: (r["type"], r.get("by")) for r in led}
    cited = collections.Counter(kinds.get(i, ("?", None)) for c in b.get("claims", []) for i in c.get("evidence", [])); print(f"  claims {len(b.get('claims', []))}; they cite {dict(cited)}")
