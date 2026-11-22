"""Stage 3 of the coherence audit (2026-11-22), the page, part b: item 26, every experiment of a turn (s053 turn 3 ran X1 and, after a repair, X2; the
page showed X1 alone). t.xs: the turn's experiments in order; t.exp stays the first. Usage: s3_page_b.py WT_DIR"""
import sys
from pathlib import Path
W = Path(sys.argv[1])
def rep(f, a, b, n=1):
    p = W / "viewer" / f; s = p.read_text(); assert s.count(a) == n, (f, a[:100], s.count(a)); p.write_text(s.replace(a, b))
rep("evidence_data.js", "exp: exps.find(x => x.turn === n && (multi ? byId[x.id] && byId[x.id].turn === n : true)) || null, report: rs.find(r => r.type === 'report') || null,",
    "xs: exps.filter(x => x.turn === n && (multi ? byId[x.id] && byId[x.id].turn === n : true)), exp: exps.find(x => x.turn === n && (multi ? byId[x.id] && byId[x.id].turn === n : true)) || null, report: rs.find(r => r.type === 'report') || null,   // xs: every experiment of the turn (a repaired test runs as one of its own); exp: the first")
rep("evidence_data.js", '''        const nt = t.exp ? tests.filter(q => q.exp === t.exp.id).length : 0;
        if (t.exp) parts.push(`experiment ${t.exp.id} (${t.exp.sims.length} simulation${t.exp.sims.length === 1 ? '' : 's'}, ${nt ? nt + (nt === 1 ? ' test' : ' tests') : 'no tests: it explores'})`);''',
    '''        t.xs.forEach(x => { const nt = tests.filter(q => q.exp === x.id).length; parts.push(`experiment ${x.id} (${x.sims.length} simulation${x.sims.length === 1 ? '' : 's'}, ${nt ? nt + (nt === 1 ? ' test' : ' tests') : 'no tests: it explores'})`); });''')
# the track: each experiment of the turn, its simulations and its checks; the first also "plan accepted"
p = W / "viewer" / "evidence_data.js"; s = p.read_text().split("\n")
k = next(i for i, l in enumerate(s) if l == "        if (t.exp) {")
assert s[k + 5] == "        }" and "plan accepted" in s[k + 1], s[k:k + 6]
body = "\n".join(s[k + 1:k + 5]).replace("t.exp", "x").replace("push({ turn: n, lane: 'harness', kind: 'accepted'", "if (!i) push({ turn: n, lane: 'harness', kind: 'accepted'")
body = body.replace("label: `${x.sims.length} simulation${x.sims.length === 1 ? '' : 's'}`", "label: `${x.sims.length} simulation${x.sims.length === 1 ? '' : 's'}${t.xs.length > 1 ? ' of ' + x.id : ''}`")
assert body.count("if (!i) push") == 1 and " of ' + x.id" in body
s[k:k + 6] = ["        t.xs.forEach((x, i) => {   // every experiment of the turn (the coherence audit, 2026-11-22: a repaired test's experiment was not drawn)"] + body.split("\n") + ["        });"]
p.write_text("\n".join(s))
print("data part 1")
# the turn card: each experiment
rep("evidence_cards.js", "    const x = t.exp, fixed = x ? Object.keys(x.sims[0] ? x.sims[0].params : {}).filter(k => x.sims.every(s => JSON.stringify(s.params[k]) === JSON.stringify(x.sims[0].params[k]))) : [];",
    "    const xs = t.xs || (t.exp ? [t.exp] : []), fixedOf = x => Object.keys(x.sims[0] ? x.sims[0].params : {}).filter(k => x.sims.every(s => JSON.stringify(s.params[k]) === JSON.stringify(x.sims[0].params[k])));   // every experiment of the turn")
rep("evidence_cards.js", "      ...(x ? [`<li>${EV.term('Experiment', 'experiment')} ${EV.link(x.id)}:", "      ...xs.map(x => { const fixed = fixedOf(x); return `<li>${EV.term('Experiment', 'experiment')} ${EV.link(x.id)}:")
rep("evidence_cards.js", "<li class=\"mut\">no tests: it explores “${e(x.question || 'not recorded')}”</li>`}</ul></li>`] : []),",
    "<li class=\"mut\">no tests: it explores “${e(x.question || 'not recorded')}”</li>`}</ul></li>`; }),")
# the glance, the knob view, the tree
rep("evidence_glance.js", "      if (t.exp && seen(t.exp.id)) bits.push(`experiment ${e(t.exp.id)} with ${pl(t.exp.sims.length, 'simulation')}`);",
    "      (t.xs || (t.exp ? [t.exp] : [])).filter(x => seen(x.id)).forEach(x => bits.push(`experiment ${e(x.id)} with ${pl(x.sims.length, 'simulation')}`));")
rep("evidence_glance.js", "map(t => { const x = t.exp && seen(t.exp.id) ? t.exp : null; return { t, x, ts: x ? M.tests.filter(T => T.exp === x.id) : [] }; });",
    "map(t => { const xs = (t.xs || (t.exp ? [t.exp] : [])).filter(q => seen(q.id)), x = xs[0] || null; return { t, x, ts: M.tests.filter(T => xs.some(q => q.id === T.exp)) }; });   // the tests of every experiment of the turn")
rep("evidence_knob.js", "  knTurns(M) { return M.turns.filter(t => t.exp && EV.seen(t.exp.id)).map(t => ({ t, sims: t.exp.sims.filter(q => EV.seen(q.id)) })).filter(c => c.sims.length); },",
    "  knTurns(M) { return M.turns.filter(t => t.exp && EV.seen(t.exp.id)).map(t => ({ t, sims: (t.xs || [t.exp]).filter(x => EV.seen(x.id)).flatMap(x => x.sims).filter(q => EV.seen(q.id)) })).filter(c => c.sims.length); },   // every experiment of the turn")
rep("evidence_tree.js", "      if (x) { const ts = M.tests.filter(T => T.exp === x.id), xk = 'exp:' + x.id,", "      (t.xs || (x ? [x] : [])).forEach(x => { const ts = M.tests.filter(T => T.exp === x.id), xk = 'exp:' + x.id,   // every experiment of the turn\n       ")
rep("evidence_tree.js", "          x.sims.filter(q => !named.has(q.id)).forEach(q => { out += simRow(2, q, null); }); } }\n      if (t.report)",
    "          x.sims.filter(q => !named.has(q.id)).forEach(q => { out += simRow(2, q, null); }); } });\n      if (t.report)")
print("page b patched")
