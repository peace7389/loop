// The work as a tree: turn → experiment → test → simulation (each row names its kind in words), with refused items in place (warning colour) and the final
// report under its turn. Each row: icon, id, a few words, its state. Rows fold; the tree follows the replay (data-step)
// and the selection shared with the session flow and the hypothesis map (EV.selInfo).
// ======================================================================================================
Object.assign(EV, {
  // what the current selection consists of: its ledger records, its hypotheses, its simulations, its turn; the three
  // views mark the same item from this
  selInfo() {
    const M = EV.M, s = EV.s.sel, o = { recs: new Set(), hyps: new Set(), sims: new Set(), turn: null }; if (!s || !M) return o;
    const add = (...ids) => ids.forEach(id => id && o.recs.add(id)), test = T => { add(T.exp, T.check && T.check.id, T.verdict && T.verdict.id, ...T.sims.map(q => q.id)); o.hyps.add(T.hyp); T.sims.forEach(q => o.sims.add(q.id)); };
    if (s.t === 'test' && M.testById[s.id]) test(M.testById[s.id]);
    else if (s.t === 'hyp' && M.hypById[s.id]) { const h = M.hypById[s.id]; add(h.id, h.verdict && h.verdict.id); o.hyps.add(h.id); h.tests.forEach(q => test(M.testById[q])); }
    else if (s.t === 'exp' && M.expById[s.id]) { const x = M.expById[s.id]; add(x.id, x.evidence && x.evidence.id, ...x.sims.map(q => q.id), ...x.checks.map(q => q.id)); x.tests.forEach(h => o.hyps.add(h)); }
    else if (s.t === 'sim' && M.simById[s.id]) { add(s.id); o.sims.add(s.id); M.tests.filter(T => T.sims.some(q => q.id === s.id) && (!s.test || s.test === T.id)).forEach(T => o.hyps.add(T.hyp)); }
    else if (s.t === 'log') { o.turn = s.id; const t = M.turns.find(q => q.n === s.id); if (t) { t.hyps.forEach(h => o.hyps.add(h.id)); t.verdicts.forEach(v => o.hyps.add(v.body.for)); } }
    else if (s.t === 'report' && M.repRec) add(M.repRec.id);
    return o;
  },
  // a row is unfolded unless the reader folded it; a test is folded unless it is the selected one or names the selected simulation
  treeOpen(key) { const v = EV.s.tree[key]; if (v !== undefined) return v; if (!key.startsWith('test:')) return true;
    const s = EV.s.sel || {}, T = EV.M.testById[key.slice(5)]; return (s.t === 'test' && s.id === T.id) || (s.t === 'sim' && (s.test ? s.test === T.id : T.sims.some(q => q.id === s.id))); },

  viewTree() {
    const M = EV.M, S = EV.s, e = EV.e, sel = S.sel || {}, st = id => M.recStep[id] ?? 0, cut = (s, n) => { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; };
    const row = (depth, o) => `<div class="tr${o.sel ? ' sel' : ''}${o.warn ? ' warn' : ''}" data-step="${o.step}" style="padding-left:${6 + depth * 18}px">${o.fold ? `<a class="tw" data-act="tfold" data-id="${e(o.fold)}" title="${o.open ? 'Fold' : 'Unfold'}">${o.open ? '▾' : '▸'}</a>` : '<span class="tw"></span>'}
      <a class="tl" data-act="open" data-t="${o.t}" data-id="${e(o.id)}"${o.test ? ` data-test="${e(o.test)}"` : ''}>${o.icon} <b>${e(o.name)}</b> <span class="sm">${o.words}</span></a><span class="ts">${o.state || ''}</span></div>`;
    const span = (k, html) => `<span data-step="${k}">${html}</span>`, res = c => EV.checkRes(c);
    const simRow = (depth, q, T) => row(depth, { t: 'sim', id: q.id, test: T ? T.id : '', icon: EV.gkey(q.same_as ? 'sim-returned' : 'sim'), name: 'simulation ' + q.id, words: e(q.label || '') + (T && q.label === T.control ? ' · control' : '') + (q.same_as ? ` · returned from ${e(q.same_as)}` : ''),
      step: st(q.id), sel: sel.t === 'sim' && sel.id === q.id && (!sel.test || !T || sel.test === T.id), state: q.error ? '<span class="bad">no measurements</span>' : '' });
    let out = '';
    M.turns.forEach(t => {
      const k0 = t.steps[0] ? t.steps[0].k : 0, tk = 'turn:' + t.n, open = EV.treeOpen(tk), x = t.exp, bits = [];
      if (t.verdicts.length) bits.push(`${t.verdicts.length} verdict${t.verdicts.length === 1 ? '' : 's'}`); if (t.hyps.length) bits.push(`${t.hyps.length} new hypothes${t.hyps.length === 1 ? 'is' : 'es'}`); if (t.drops.length) bits.push(`${t.drops.length} dropped`);
      out += row(0, { t: 'log', id: t.n, icon: EV_ICON.turn, name: t.n ? 'turn ' + t.n : 'start', words: t.n ? e(bits.join(' · ') || (t.report ? 'the final report' : x ? '' : M.ended || t.malformed.length ? 'nothing usable' : 'waiting for the answer')) : 'the brief and the baseline, by the harness', step: k0, fold: tk, open,
        sel: sel.t === 'log' && sel.id === t.n, state: t.n ? (t.left == null ? '' : `${t.left} left`) : '' });
      if (!open) return;
      t.malformed.forEach(m => { out += row(1, { t: 'log', id: t.n, icon: EV_ICON.malformed, name: 'refused', words: 'the whole answer: ' + e(cut((m.body.refused || []).map(q => q.reason).join(' | ') || m.body.error, 70)), step: st(m.id), warn: true }); });
      t.refusals.forEach(m => { out += row(1, { t: 'log', id: t.n, icon: EV_ICON.malformed, name: 'refused part', words: e(m.body.part) + ': ' + e(cut(m.body.reason || m.body.text, 70)), step: st(m.id), warn: true }); });
      if (x) { const ts = M.tests.filter(T => T.exp === x.id), xk = 'exp:' + x.id, xo = EV.treeOpen(xk), held = x.checks.filter(c => c.result === 'held').length, named = new Set(ts.flatMap(T => T.sims.map(q => q.id)));
        out += row(1, { t: 'exp', id: x.id, icon: EV_ICON.experiment, name: 'experiment ' + x.id, words: `${x.sims.length} simulation${x.sims.length === 1 ? '' : 's'} · ${ts.length ? ts.length + (ts.length === 1 ? ' test' : ' tests') : x.by === 'harness' ? 'the baseline' : 'explores: ' + e(cut(x.question, 50))}`,
          step: st(x.id), fold: xk, open: xo, sel: sel.t === 'exp' && sel.id === x.id, state: x.checks.length ? span(Math.max(...x.checks.map(c => st(c.id))), EV.tally(held, x.checks.length - held)) : '' });
        if (xo) { ts.forEach(T => { const k = 'test:' + T.id, to = EV.treeOpen(k), v = T.verdict, h = M.hypById[T.hyp];
            out += row(2, { t: 'test', id: T.id, icon: EV_ICON.test, name: 'test of ' + T.hyp, words: e(cut(h && h.text, 40)), step: st(x.id), fold: k, open: to, sel: sel.t === 'test' && sel.id === T.id || (sel.t === 'hyp' && sel.id === T.hyp),
              state: (T.check ? span(st(T.check.id), res(T.check)) : '') + (v ? span(st(v.id), ` · ${EV.verdictRes(v.result)}${EV.contradicts(v, T.check ? [T.check] : []) ? ' ' + EV.warn('', 'the verdict disagrees with its check') : ''}`) : '') });
            if (to) T.sims.forEach(q => { out += simRow(3, q, T); }); });
          x.sims.filter(q => !named.has(q.id)).forEach(q => { out += simRow(2, q, null); }); } }
      if (t.report) out += row(1, { t: 'report', id: 'report', icon: EV_ICON.report, name: 'final report', words: `${M.claims.length} claim${M.claims.length === 1 ? '' : 's'}`, step: st(t.report.id), sel: sel.t === 'report' });
    });
    return `<div class="tree">${out || '<p class="sm">No record yet.</p>'}</div>
      <p class="sm">A ${EV.term('Test', 'test')} lists the simulations its decision rule names; a simulation no rule names sits directly under its ${EV.term('Experiment', 'experiment')}. ${EV.gkey('sim-returned')}a simulation returned from an earlier one, not run again.</p>`;
  },
});
EV.act = Object.assign(EV.act || {}, {
  tfold(id) { EV.s.tree[id] = !EV.treeOpen(id); EV.draw(); },
  left(id) { EV.s.left = id; EV.draw(); },
});
