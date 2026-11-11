// Highlights: up to seven key moments of a session, chosen by fixed rules from its records (no model is asked), each
// one sentence built from the record's fields and a link to the item. The rules, in priority order:
//   1 the first test that held · 2 every failed test from which a later hypothesis follows · 3 the tests cited by the
//   report's first claim · 4 the simulation after which the best valid result no longer improved · 5 every refused
//   answer or part · 6 a verdict that contradicts its check, a number in the model's text that differs from the
//   measurement · 7 the final report.
// When more than seven qualify, the first of each rule is kept before the second of any (so the list still runs from
// the first held test to the final report), and the page says how many were left out. Shown in the order they happened.
// ======================================================================================================
Object.assign(EV, {
  // the model's texts whose numbers differ from the measurements: a turn's observations, a verdict's "because", the report
  mismatches(M) {
    if (M._mis) return M._mis; const out = [], bad = (text, sims) => EV.numRows(M, text, sims).filter(q => q.status === 'differs');
    M.turns.forEach(t => { if (t.n < 1) return;
      const obs = t.observations ? bad(t.observations, M.exps.filter(x => x.turn === t.n - 1).flatMap(x => x.sims)) : [];
      if (obs.length) out.push({ key: 'log:' + t.n, where: `Turn ${t.n}, the observations`, open: { t: 'log', id: t.n }, step: t.steps[0] ? t.steps[0].k : 0, rows: obs });
      t.verdicts.forEach(v => { const h = M.hypById[v.body.for], xs = h ? h.exps.map(id => M.expById[id]).filter(q => q.turn < t.n) : [], rows = bad(v.body.because, xs.length ? xs[xs.length - 1].sims : []);
        if (rows.length) out.push({ key: 'log:' + t.n, where: `Turn ${t.n}, verdict ${v.id}`, open: { t: 'log', id: t.n }, step: M.recStep[v.id] ?? 0, rows }); }); });
    const rep = M.report, rows = rep ? bad([rep.explanation, rep.holds_when, rep.breaks_when, ...(rep.claims || []).map(c => c.text)].flat().filter(Boolean).join('\n'), M.sims) : [];
    if (rows.length) out.push({ key: 'report:report', where: 'The final report', open: { t: 'report', id: 'report' }, step: M.repRec ? M.recStep[M.repRec.id] ?? 0 : 0, rows });
    return (M._mis = out);
  },
  highlights(M) {
    if (M._hl) return M._hl; const e = EV.e, by = [[], [], [], [], [], [], []], cut = (s, n) => { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; }, st = id => M.recStep[id] ?? 0;
    const hyp = t => `${e(t.hyp)} (“${e(cut((M.hypById[t.hyp] || {}).text, 90))}”)`, test = t => ({ key: 'test:' + t.id, open: { t: 'test', id: t.id } });
    const first = M.tests.find(t => t.check && t.check.result === 'held');
    if (first) by[0].push({ ...test(first), step: st(first.check.id), html: `Turn ${first.turn}: the first test that held. ${hyp(first)}: <code>${e(cut(first.check.numbers, 80))}</code> held.` });
    M.tests.filter(t => t.check && t.check.result === 'failed').forEach(t => { const f = EV.followers(t, M); if (!f.ids.length || f.via) return;
      by[1].push({ ...test(t), step: Math.max(...f.ids.map(st)), html: `Turn ${t.turn}: the test of ${hyp(t)} failed (<code>${e(cut(t.check.numbers, 70))}</code>), and ${e(f.ids.join(', '))} follow${f.ids.length === 1 ? 's' : ''} from it: this changed the direction.` }); });
    const c1 = M.claims[0]; if (c1) c1.tests.forEach(id => { const t = M.testById[id], had = by[0].concat(by[1]).find(q => q.key === 'test:' + id);
      if (had) had.html += ' The report\'s first claim cites this test.';
      else by[2].push({ ...test(t), step: st(M.repRec.id), html: `The report's first claim (“${e(cut(c1.text, 90))}”) cites the test of ${hyp(t)}, which ${t.check ? e(t.check.result) : 'was not checked'}.` }); });
    const d = EV.bestData(M); if (d && d.last) { const p = d.last, [u, f] = EV.unit(d.g.target), n = d.pts.length;
      by[3].push({ key: 'sim:' + p.s.id, open: { t: 'sim', id: p.s.id }, step: st(d.pts[n - 1].s.id), html: `Turn ${p.turn}: simulation ${e(p.s.id)} (“${e(p.s.label || '')}”, number ${p.n} of ${n}) gave the best result that meets the brief's conditions, ${(+f(p.v).toPrecision(7)).toLocaleString('en-US')} ${u}; ${n - p.n ? `none of the ${n - p.n} after it improved on it` : 'it was the last one'}.` }); }
    M.turns.forEach(t => { t.malformed.forEach(m => by[4].push({ key: 'log:' + t.n, open: { t: 'log', id: t.n }, step: st(m.id), warn: true, html: `Turn ${t.n}: the harness refused the whole answer: ${e(cut((m.body.refused || []).map(q => q.part + ': ' + q.reason).join(' | ') || m.body.error, 160))}.` }));
      t.refusals.forEach(m => by[4].push({ key: 'log:' + t.n, open: { t: 'log', id: t.n }, step: st(m.id), warn: true, html: `Turn ${t.n}: the harness refused part of the answer (${e(m.body.part)}): ${e(cut(m.body.reason || m.body.text, 160))}.` })); });
    M.tests.filter(t => EV.contradicts(t.verdict, t.check ? [t.check] : [])).forEach(t => by[5].push({ ...test(t), step: st(t.verdict.id), warn: true, html: `Turn ${t.verdict.turn}: verdict ${e(t.verdict.id)} says ${e(t.hyp)} is ${e(t.verdict.result)}, but its check ${e(t.check.id)} ${e(t.check.result)}.` }));
    EV.mismatches(M).forEach(x => by[5].push({ key: x.key, open: x.open, step: x.step, warn: true, html: `${e(x.where)}: ${x.rows.length} number${x.rows.length === 1 ? '' : 's'} in the model's text differ${x.rows.length === 1 ? 's' : ''} from the measurement (it wrote “${e(x.rows[0].written)}”; measured ${e(x.rows[0].measured)}).` }));
    if (M.repRec) { const rep = M.report || {}, g = d && d.g, ex = g && rep.expected && typeof rep.expected === 'object' ? rep.expected[g.target] : null;
      by[6].push({ key: 'report:report', open: { t: 'report', id: 'report' }, step: st(M.repRec.id), html: `Turn ${M.repRec.turn}: the final report recommends ${e(typeof rep.recommendation === 'object' && rep.recommendation ? Object.entries(rep.recommendation).map(([k, v]) => `${k} ${v}`).join(', ') : cut(rep.recommendation, 120))}${typeof ex === 'number' ? `, expecting ${e(g.target)} ${e(EV.val(g.target, ex))}` : ''}.` }); }
    const all = by.reduce((n, q) => n + q.length, 0), items = [];
    for (let i = 0; items.length < 7 && items.length < all; i++) by.forEach((q, r) => { if (q[i] && items.length < 7) items.push({ ...q[i], rule: r + 1 }); });
    return (M._hl = { items: items.sort((a, b) => a.step - b.step || a.rule - b.rule), left: all - items.length, all });
  },
  highCard() {
    const M = EV.M, h = EV.highlights(M), S = EV.s, on = q => S.sel && `${S.sel.t}:${S.sel.id}` === q.key;
    return `<div class="ev-card" id="s-high"><h2>Highlights<small>the key moments, chosen by fixed rules from the records; click one to open it</small></h2>
      ${h.items.length ? `<ol class="hl">${h.items.map(q => `<li data-step="${q.step}" class="${q.warn ? 'warn' : ''}${on(q) ? ' on' : ''}"><a data-act="open" data-t="${q.open.t}" data-id="${EV.e(q.open.id)}">${q.html}</a></li>`).join('')}</ol>` : `<p class="sm">${M.ended ? 'Nothing in this session meets a rule for a highlight.' : 'Nothing yet.'}</p>`}
      ${h.left ? `<p class="sm">${h.all} moments qualified; ${h.left} ${h.left === 1 ? 'was' : 'were'} left out to keep seven (the first of each kind is kept before the second of any).</p>` : ''}</div>`;
  },
});
