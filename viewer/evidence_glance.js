// What a session is made of, as one picture at the top of its page: a column per turn, a row per kind of item, one mark
// per item. Down a column stand a hypothesis, its decision rule, the simulations of the turn's experiment, the check and
// the verdict: together one test. A mark opens its item in the pane on the right (the page does not move); pointing at
// it marks what belongs with it and says in words what it is. During the replay nothing recorded after the chosen step
// is drawn here at all: a later item is an empty dot, with no text, state or title; the key and the sentence under the
// table name only what is recorded by then. The card is not printed (the page prints four parts, and this is not one).
// It folds like the card "The system": a "fold" button in its heading, and the browser remembers it.
// Under each turn's name its header says how many simulations were left at its start ("not recorded" before s008).
// ======================================================================================================
Object.assign(EV, {
  // the hypotheses, tests and simulations that belong with an item (the selected one, or the one pointed at)
  glInfo(sel) {
    const M = EV.M, o = { hyps: new Set(), tests: new Set(), sims: new Set() }; if (!sel || !M) return o;
    const test = (T, withSims) => { o.tests.add(T.id); o.hyps.add(T.hyp); if (withSims) T.sims.forEach(q => o.sims.add(q.id)); };
    if (sel.t === 'test' && M.testById[sel.id]) test(M.testById[sel.id], true);
    else if (sel.t === 'hyp' && M.hypById[sel.id]) { o.hyps.add(sel.id); M.hypById[sel.id].tests.forEach(q => test(M.testById[q], true)); }
    else if (sel.t === 'sim' && M.simById[sel.id]) { o.sims.add(sel.id); M.tests.filter(T => T.sims.some(q => q.id === sel.id)).forEach(T => test(T, false)); }
    else if (sel.t === 'exp' && M.expById[sel.id]) { M.expById[sel.id].sims.forEach(q => o.sims.add(q.id)); M.tests.filter(T => T.exp === sel.id).forEach(T => test(T, false)); }
    return o;
  },

  // one sentence that says what an item is and what it consists of; only what is recorded by the replay's step
  glSay(sel) {
    const M = EV.M, e = EV.e, seen = EV.seen, I = EV_ICON, by = (m, id) => (sel && sel.t === id ? m : null);
    const cut = (s, n) => { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; }, pl = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
    const now = (m, id) => (m && seen(id(m)) ? m : null), step = EV.s.step;  // nothing recorded after the replay's step is described, even while it is still selected
    const T = now(by(M.testById[sel && sel.id], 'test'), q => q.exp), h = now(by(M.hypById[sel && sel.id], 'hyp'), q => q.id), s = now(by(M.simById[sel && sel.id], 'sim'), q => q.id), x = now(by(M.expById[sel && sel.id], 'exp'), q => q.id);
    const t = by(M.turns.find(q => sel && q.n === sel.id && (step == null || (q.steps[0] ? q.steps[0].k : 0) <= step)), 'log');
    const xSay = q => (M.tests.some(u => u.exp === q.id) ? pl(M.tests.filter(u => u.exp === q.id).length, 'test') : q.by === 'harness' ? 'the baseline, run by the harness' : 'no tests: it explores “' + e(cut(q.question, 70)) + '”');
    if (T) { const hy = M.hypById[T.hyp], c = T.check && seen(T.check.id) ? T.check : null, v = T.verdict && seen(T.verdict.id) ? T.verdict : null;
      return `<b>${I.test} Test of ${e(T.hyp)}</b> in experiment ${e(T.exp)}, turn ${T.turn}: ` + [`${I.hypothesis} hypothesis “${e(cut(hy && hy.text, 64))}”`, T.rule ? '⊢ its decision rule' : null, `${I.simulation} ${pl(T.sims.length, 'simulation')}`,
        c ? `<span class="gn ${c.result === 'held' ? 'ok' : c.result === 'failed' ? 'bad' : 'mut'}">check ${e(c.result)}</span>` : null, v ? `<span class="gn">verdict <b>${e(v.result)}</b></span>, given in turn ${v.turn}` : null].filter(Boolean).join(' → '); }
    if (h) { const st = EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open', n = h.tests.filter(q => seen(M.testById[q].exp)).length;
      return `<b>${I.hypothesis} Hypothesis ${e(h.id)}</b>, stated in turn ${h.turn}: “${e(cut(h.text, 96))}” · ${e(st)} · ${n ? 'put to ' + pl(n, 'test') : 'not put to a test'}`; }
    if (s) { const names = M.tests.filter(q => q.sims.includes(s)).map(q => q.hyp);
      return `<b>${I.simulation} Simulation ${e(s.id)}</b> “${e(s.label || '')}” of experiment ${e(s.exp)}${s.turn ? ', turn ' + s.turn : ''} · ${names.length ? `named by the decision rule${names.length === 1 ? '' : 's'} of ${e(names.join(', '))}` : 'named by no decision rule'}${s.same_as ? ` · returned from ${e(s.same_as)}, not run again` : ''}${s.error ? ' · <span class="bad">no measurements</span>' : ''}`; }
    if (x) return `<b>${I.experiment} Experiment ${e(x.id)}</b>${x.turn ? ', turn ' + x.turn : ', before the first turn'}: ${pl(x.sims.length, 'simulation')} · ${xSay(x)}`;
    if (t) { const n = k => k.filter(r => seen(r.id)).length, bits = [[n(t.verdicts), 'verdict'], [n(t.hyps), 'new hypothes', 'is', 'es'], [n(t.drops), 'dropped hypothes', 'is', 'es'], [n(t.malformed) + n(t.refusals), 'refusal']]
        .filter(q => q[0]).map(([k, w, one, many]) => `${k} ${w}${one === undefined ? (k === 1 ? '' : 's') : k === 1 ? one : many}`);
      if (t.exp && seen(t.exp.id)) bits.push(`experiment ${e(t.exp.id)} with ${pl(t.exp.sims.length, 'simulation')}`); if (t.report && seen(t.report.id)) bits.push('the final report');
      return t.n ? `<b>${I.turn} Turn ${t.n}</b>: ${bits.join(' · ') || 'nothing the harness could use'}${t.left == null ? '' : ` · ${pl(t.left, 'simulation')} left at its start`}` : `<b>Start</b>: the brief, and the baseline the harness ran before the model's first turn`; }
    if (sel && sel.t === 'report' && M.report && M.repRec && seen(M.repRec.id)) { const r = M.report.recommendation;
      return `<b>${I.report} Final report</b>: ${pl(M.claims.length, 'claim')}${r && typeof r === 'object' ? ' · recommends ' + e(Object.entries(r).map(([k, v]) => `${k} ${v}`).join(', ')) : ''}`; }
    return 'Point at a mark to read what it is. A hypothesis, its decision rule, the simulations that rule names, its check and its verdict stand in one line down a column: together they are one test.';
  },

  glance() {
    const fold = EV.store('ev-made') === '1', foldBtn = `<button class="cl noprint" data-act="glfold" style="float:right">${fold ? 'unfold' : 'fold'}</button>`;
    if (fold) return `<div class="ev-card noprint" id="s-made"><h2>What this session is made of <small>one mark per item, a column per ${EV.term('Turn', 'turn')} · folded</small> ${foldBtn}</h2></div>`;
    const M = EV.M, S = EV.s, e = EV.e, seen = EV.seen, live = S.step == null, I = EV_ICON, sel = S.sel || {}, info = EV.glInfo(S.sel), st = live ? null : EV_DATA.stateAt(M, S.step);
    const claim = S.claim ? M.claims[S.claim - 1] : null, hitT = new Set(claim ? claim.tests : []), hitH = new Set(claim ? claim.hyps : []);
    const gap = '<i class="gm"></i>';   // an empty place
    const mark = (ch, t, id, rec, title, cls) => { if (!seen(rec)) return '<i class="gm gp"></i>';
      const on = t === 'hyp' ? info.hyps.has(id) : t === 'test' ? info.tests.has(id) : t === 'sim' ? info.sims.has(id) : sel.t === t, hit = t === 'hyp' ? hitH.has(id) : t === 'test' && hitT.has(id);
      return `<a class="gm ${cls || ''}${on ? ' on' : ''}${hit ? ' hit' : ''}" data-act="open" data-t="${t}" data-id="${e(id)}" title="${e(title)}">${ch}</a>`; };
    // ---- the columns: every turn recorded by the replay's step; its experiment; the tests of that experiment, one place each
    const cols = M.turns.filter(t => live || (t.steps[0] ? t.steps[0].k : 0) <= S.step).map(t => { const x = t.exp && seen(t.exp.id) ? t.exp : null, ts = x ? M.tests.filter(T => T.exp === x.id) : [];
      const own = t.hyps.filter(h => seen(h.id) && !ts.some(T => T.hyp === h.id));  // stated in this turn and not tested in it
      return { t, x, ts, own }; });
    // the size of a mark, the marks in one line of a column and whether the rows' short notes are shown: the largest of these
    // with which every turn fits the width of the page; with none, the smallest, and the table scrolls sideways. A column
    // with more tests than fit in one line wraps, the same way in every row, so a test still stands in one line downwards.
    const room = document.getElementById('ev').clientWidth - 76, places = (c, cap, per) => Math.max(Math.min(c.ts.length + c.own.length, cap), Math.min(c.x ? c.x.sims.length : 0, per), 1);
    const fit = [[17, 8, 6, 1], [15, 8, 6, 1], [13, 6, 5, 1], [13, 6, 4, 0], [11, 5, 4, 0]].find(([w, cap, per, notes]) => (notes ? 320 : 170) + cols.reduce((a, c) => a + Math.max(c.t.n && c.t.left == null ? 66 : 52, places(c, cap, per) * w) + 19, 0) <= room), fits = !!fit;  // 66: room for "not recorded" under the turn's name
    const [W, cap, per, notes] = fit || [11, 5, 4, 0]; cols.forEach(c => { c.w = W * places(c, cap, per); });
    const hm = (h, first, c) => { const s = st ? st[h.id] || 'open' : h.state;  // a hypothesis is drawn filled once, where it was stated; hollow wherever it stands again
      return mark(first ? I.hypothesis : '◇', 'hyp', h.id, first ? h.id : c.x.id, first ? `${h.id} · ${s}` : `${h.id}, ${h.turn === c.t.n ? 'put to another decision rule' : `stated in turn ${h.turn} and tested here`}`, s === 'dropped' ? 'dr' : ''); };
    const cell = {
      hyp: c => c.ts.map((T, i) => { const h = M.hypById[T.hyp]; return h ? hm(h, h.turn === c.t.n && c.ts.findIndex(q => q.hyp === h.id) === i, c) : gap; }).concat(c.own.map(h => hm(h, true))).join(''),
      rule: c => c.ts.map(T => (T.rule ? mark('⊢', 'test', T.id, T.exp, `the decision rule for ${T.hyp}`) : gap)).join(''),
      sim: c => (!c.x ? '' : `<a class="gx${sel.t === 'exp' && sel.id === c.x.id ? ' on' : ''}" data-act="open" data-t="exp" data-id="${e(c.x.id)}" title="experiment ${e(c.x.id)}">${I.experiment} ${e(c.x.id)}</a>`
        + c.x.sims.map(q => mark(q.same_as ? '○' : I.simulation, 'sim', q.id, q.id, `${q.id} · ${q.label || ''}${q.same_as ? ' · returned from ' + q.same_as : ''}`, q.error ? 'bad' : '')).join('')),
      check: c => c.ts.map(T => { const k = T.check; return k ? mark(k.result === 'held' ? '✓' : k.result === 'failed' ? '✗' : '–', 'test', T.id, k.id, `${k.id} · ${k.result}`, k.result === 'held' ? 'ok' : k.result === 'failed' ? 'bad' : '') : gap; }).join(''),
      verdict: c => c.ts.map((T, i) => { const v = T.verdict, odd = v && EV.contradicts(v, T.check ? [T.check] : []), k = v ? ['supported', 'refuted'].indexOf(v.result) : 0;
        const again = v && c.ts.findIndex(q => q.verdict === v) !== i;  // one verdict for a hypothesis put to several decision rules: filled once, hollow under the others
        return v ? mark((again ? '△▽□' : '▲▼■')[k < 0 ? 2 : k], 'test', T.id, v.id, `${v.id} · ${v.result}, given in turn ${v.turn}${again ? ' · the same verdict: one hypothesis, several decision rules' : ''}${odd ? ' · disagrees with its check' : ''}`, ['ok', 'bad', ''][k < 0 ? 2 : k] + (odd ? ' odd' : '')) : gap; }).join(''),
      report: c => (c.t.report ? mark(I.report, 'report', 'report', c.t.report.id, 'the final report') : ''),
    };
    const n = { turn: cols.filter(c => c.t.n > 0).length, hyp: M.hyps.filter(h => seen(h.id)).length, rule: M.tests.filter(T => T.rule && seen(T.exp)).length, sim: M.sims.filter(q => seen(q.id)).length, exp: M.exps.filter(x => seen(x.id)).length,
                check: M.checks.filter(q => seen(q.id)).length, verdict: M.recs.filter(r => r.type === 'verdict' && seen(r.id)).length, report: M.repRec && seen(M.repRec.id) ? 1 : 0 };
    const row = (by, icon, term, word, count, note, k) => `<tr data-by="${by}"><th><span class="gi">${icon}</span>${EV.term(term, word)} <b>${count}</b>${notes || note === EV.nr ? ` <span class="sm">${note}</span>` : ''}</th>${cols.map(c => `<td><div class="gs" style="width:${c.w}px">${cell[k](c)}</div></td>`).join('')}</tr>`;
    const head = cols.map(c => { const r = c.t.malformed.concat(c.t.refusals).filter(q => seen(q.id)).length;
      return `<td><a class="gt${sel.t === 'log' && sel.id === c.t.n ? ' on' : ''}" data-act="open" data-t="log" data-id="${c.t.n}">${c.t.n ? 'turn ' + c.t.n : 'start'}</a>${r ? ` <span class="warnc" title="${r} refused answer${r === 1 ? '' : 's'} or part${r === 1 ? '' : 's'} of an answer in this turn">⚠${r > 1 ? r : ''}</span>` : ''}${
        c.t.n ? `<div class="gleft" data-left="${c.t.left ?? ''}" title="${c.t.left == null ? 'How many simulations were left at the start of this turn is not recorded (sessions before s008)' : `${c.t.left} simulation${c.t.left === 1 ? ' was' : 's were'} left at the start of turn ${c.t.n}`}">${c.t.left == null ? EV.nr : c.t.left + ' left'}</div>` : ''}</td>`; }).join('');
    const has = f => cols.some(f), res = k => M.checks.some(q => q.result === k && seen(q.id)), vd = k => M.recs.some(r => r.type === 'verdict' && r.body.result === k && seen(r.id));  // the key names a sign only once one is drawn
    const key = [['<span class="ok">✓</span> held', res('held')], ['<span class="bad">✗</span> failed', res('failed')], ['<span class="ok">▲</span> supported', vd('supported')], ['<span class="bad">▼</span> refuted', vd('refuted')], ['■ inconclusive', vd('inconclusive')],
      ['◇ a hypothesis drawn before: stated in an earlier turn, or put to another decision rule', has(c => c.ts.some((T, i) => { const h = M.hypById[T.hyp]; return h && (h.turn !== c.t.n || c.ts.findIndex(q => q.hyp === T.hyp) !== i); }))],
      ['△ ▽ □ the same verdict again, under another decision rule of its hypothesis', has(c => c.ts.some((T, i) => T.verdict && seen(T.verdict.id) && c.ts.findIndex(q => q.verdict === T.verdict) !== i))],
      ['○ a simulation returned from an earlier one, not run again', M.sims.some(q => q.same_as && seen(q.id))], [`${I.experiment} X0 the harness's baseline, outside the budget`, M.exps.some(x => x.by === 'harness' && seen(x.id))],
      ['<s>◆</s> dropped', M.hyps.some(h => h.drop && seen(h.drop.id))], ['<span class="warnc">⚠</span> refused', cols.some(c => c.t.malformed.concat(c.t.refusals).some(q => seen(q.id)))]].filter(q => q[1]).map(q => `<span>${q[0]}</span>`).join('');
    EV._gl = '';
    return `<div class="ev-card noprint" id="s-made"><h2>What this session is made of <small>one mark per item · a column is one ${EV.term('Turn', 'turn')}, read it downwards · click a mark to open it on the right${fits ? '' : ` · <b class="warnc">the ${cols.length} columns are wider than the page: scroll the table sideways for the later turns</b>`}</small> ${foldBtn}</h2>
      <div class="ev-scroll gl-scroll${fits ? '' : ' gl-more'}"><table class="gl" style="--gw:${W}px"><thead><tr data-by="harness"><th><span class="gi">${I.turn}</span>${EV.term('Turn', 'Turns')} <b>${n.turn}</b>${notes ? ' <span class="sm">one answer of the model each</span>' : ''}</th>${head}</tr></thead><tbody>
        ${row('model', I.hypothesis, 'Hypothesis', 'Hypotheses', n.hyp, 'the model\'s claims', 'hyp')}
        ${row('model', '⊢', 'Decision rule', 'Decision rules', n.rule, 'stated before the simulations', 'rule')}
        ${row('simulator', I.simulation, 'Simulation', 'Simulations', n.sim, `in ${n.exp} ${EV.term('Experiment', n.exp === 1 ? 'experiment' : 'experiments')}`, 'sim')}
        ${row('harness', I.check, 'Check', 'Checks', n.check, M.old ? EV.nr : 'the harness applies each rule', 'check')}
        ${row('model', I.verdict, 'Verdict', 'Verdicts', n.verdict, 'the model\'s judgments', 'verdict')}
        ${row('model', I.report, 'Final report', 'Final report', n.report, 'the model\'s answer', 'report')}</tbody></table></div>
      <p class="gl-say" id="gl-say">${EV.glSay(S.sel)}</p>
      <p class="sm gl-key">${key}<span>row stripe, who produced it: ${['model', 'harness', 'simulator'].map(b => `<span data-by="${b}"><i class="sw"></i>${b}</span>`).join(' ')}</span></p></div>`;
  },

  // pointing at a mark: what belongs with it is marked, and the line below says what it is; away from the marks, the selected item again
  glHover(ev) {
    const m = ev.target.closest ? ev.target.closest('#s-made [data-act="open"]') : null, key = m ? m.dataset.t + ':' + m.dataset.id : ''; if (key === EV._gl || !EV.M) return; EV._gl = key;
    const say = document.getElementById('gl-say'); if (!say) return;
    const sel = m ? { t: m.dataset.t, id: m.dataset.t === 'log' ? Number(m.dataset.id) : m.dataset.id } : null, o = EV.glInfo(sel);
    document.querySelectorAll('#s-made a.gm').forEach(a => a.classList.toggle('hov', !!sel && (a.dataset.t === 'hyp' ? o.hyps.has(a.dataset.id) : a.dataset.t === 'test' ? o.tests.has(a.dataset.id) : a.dataset.t === 'sim' && o.sims.has(a.dataset.id))));
    say.innerHTML = EV.glSay(sel || EV.s.sel);
  },
});
EV.act = Object.assign(EV.act || {}, { glfold() { EV.store('ev-made', EV.store('ev-made') === '1' ? '0' : '1'); EV.draw(); } });
document.getElementById('ev').addEventListener('mouseover', EV.glHover);
