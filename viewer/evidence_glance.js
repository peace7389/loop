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
    const M = EV.M, e = EV.e, seen = EV.seen, K = EV.gkey, by = (m, id) => (sel && sel.t === id ? m : null);
    const cut = (s, n) => { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; }, pl = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
    const now = (m, id) => (m && seen(id(m)) ? m : null), step = EV.s.step;  // nothing recorded after the replay's step is described, even while it is still selected
    const T = now(by(M.testById[sel && sel.id], 'test'), q => q.exp), h = now(by(M.hypById[sel && sel.id], 'hyp'), q => q.id), s = now(by(M.simById[sel && sel.id], 'sim'), q => q.id), x = now(by(M.expById[sel && sel.id], 'exp'), q => q.id);
    const t = by(M.turns.find(q => sel && q.n === sel.id && (step == null || (q.steps[0] ? q.steps[0].k : 0) <= step)), 'log');
    const xSay = q => (M.tests.some(u => u.exp === q.id) ? pl(M.tests.filter(u => u.exp === q.id).length, 'test') : q.by === 'harness' ? 'the baseline, run by the harness' : 'no tests: it explores “' + e(cut(q.question, 70)) + '”');
    if (T) { const hy = M.hypById[T.hyp], c = T.check && seen(T.check.id) ? T.check : null, v = T.verdict && seen(T.verdict.id) ? T.verdict : null;
      return `<b>Test of ${e(T.hyp)}</b> in experiment ${e(T.exp)}, turn ${T.turn}: ` + [`${K('hyp')}hypothesis “${e(cut(EV.hshort(hy), 64))}”`, T.rule ? K('rule') + 'its decision rule' : null, `${K('sim')}${pl(T.sims.length, 'simulation')}`,
        c ? `<span class="gn">${K(EV.ck(c.result))}check ${e(c.result)}</span>` : null, v ? `<span class="gn">${K(EV.vk(v.result))}verdict ${e(v.result)}</span>, given in turn ${v.turn}` : null].filter(Boolean).join(' → '); }
    if (h) { const st = EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open', n = h.tests.filter(q => seen(M.testById[q].exp)).length;
      return `<b>${K('hyp')}Hypothesis ${e(h.id)}</b>, stated in turn ${h.turn}: “${e(cut(EV.hshort(h), 96))}” · ${e(st)} · ${n ? 'put to ' + pl(n, 'test') : 'not put to a test'}`; }
    if (s) { const names = M.tests.filter(q => q.sims.includes(s)).map(q => q.hyp);
      return `<b>${K(s.same_as ? 'sim-returned' : 'sim')}Simulation ${e(s.id)}</b> “${e(s.label || '')}” of experiment ${e(s.exp)}${s.turn ? ', turn ' + s.turn : ''} · ${names.length ? `named by the decision rule${names.length === 1 ? '' : 's'} of ${e(names.join(', '))}` : 'named by no decision rule'}${s.same_as ? ` · returned from ${e(s.same_as)}, not run again` : ''}${s.error ? ' · <span class="bad">no measurements</span>' : ''}`; }
    if (x) return `<b>Experiment ${e(x.id)}</b>${x.turn ? ', turn ' + x.turn : ', before the first turn'}: ${pl(x.sims.length, 'simulation')} · ${xSay(x)}`;
    if (t) { const n = k => k.filter(r => seen(r.id)).length, bits = [[n(t.verdicts), 'verdict'], [n(t.hyps), 'new hypothes', 'is', 'es'], [n(t.drops), 'dropped hypothes', 'is', 'es'], [n(t.malformed) + n(t.refusals), 'refusal']]
        .filter(q => q[0]).map(([k, w, one, many]) => `${k} ${w}${one === undefined ? (k === 1 ? '' : 's') : k === 1 ? one : many}`);
      if (t.exp && seen(t.exp.id)) bits.push(`experiment ${e(t.exp.id)} with ${pl(t.exp.sims.length, 'simulation')}`); if (t.report && seen(t.report.id)) bits.push('the final report');
      return t.n ? `<b>Turn ${t.n}</b>: ${bits.join(' · ') || 'nothing the harness could use'}${t.left == null ? '' : ` · ${pl(t.left, 'simulation')} left at its start`}` : `<b>Start</b>: the brief, and the baseline the harness ran before the model's first turn`; }
    if (sel && sel.t === 'report' && M.report && M.repRec && seen(M.repRec.id)) { const r = M.report.recommendation;
      return `<b>${K('report')}Final report</b>: ${pl(M.claims.length, 'claim')}${r && typeof r === 'object' ? ' · recommends ' + e(Object.entries(r).map(([k, v]) => `${k} ${v}`).join(', ')) : ''}`; }
    return 'A hypothesis, its decision rule, the simulations that rule names, its check and its verdict stand in one line down a column: together they are one test.';
  },

  // how many of each kind the records hold by the replay's step
  glCounts() {
    const M = EV.M, S = EV.s, seen = EV.seen, ck = r => M.checks.filter(q => q.result === r && seen(q.id)).length;
    return { turn: M.turns.filter(t => t.n > 0 && (S.step == null || (t.steps[0] ? t.steps[0].k : 0) <= S.step)).length, hyp: M.hyps.filter(h => seen(h.id)).length, rule: M.tests.filter(T => T.rule && seen(T.exp)).length, sim: M.sims.filter(q => seen(q.id)).length,
      exp: M.exps.filter(x => seen(x.id)).length, check: M.checks.filter(q => seen(q.id)).length, held: ck('held'), failed: ck('failed'), void: ck('void'), verdict: M.recs.filter(r => r.type === 'verdict' && seen(r.id)).length, report: M.repRec && seen(M.repRec.id) ? 1 : 0 };
  },

  glance() {
    const fold = !EV.s.full && EV.store('ev-made') === '1', foldBtn = EV.s.full ? '' : `<button class="cl noprint" data-act="glfold" style="float:right">${fold ? 'unfold' : 'fold'}</button>`, n = EV.glCounts(), pl = (k, w, many) => `${k} ${k === 1 ? w : many || w + 's'}`;
    // folded, its line carries its content: the counts, from the records
    if (fold) return `<div class="ev-card noprint" id="s-made"><h2>What this session is made of <small id="gl-fold" data-counts="${[n.turn, n.hyp, n.check, n.held, n.failed, n.sim].join(',')}">${pl(n.turn, 'turn')} · ${pl(n.hyp, 'hypothesis', 'hypotheses')} · ${EV.M.old ? 'checks ' + EV.nr : `${pl(n.check, 'check')}, ${EV.tally(n.held, n.failed, n.void)}`} · ${pl(n.sim, 'simulation')}</small> ${foldBtn}</h2></div>`;
    const M = EV.M, S = EV.s, e = EV.e, seen = EV.seen, live = S.step == null, sel = S.sel || {}, info = EV.glInfo(S.sel), st = live ? null : EV_DATA.stateAt(M, S.step);
    const claim = S.claim ? M.claims[S.claim - 1] : null, hitT = new Set(claim ? claim.tests : []), hitH = new Set(claim ? claim.hyps : []);
    const gap = '<i class="gm"></i>';   // an empty place
    const mark = (m, t, id, rec, title, cls) => { if (!seen(rec)) return '<i class="gm gp"></i>';  // m: the kind of mark (EV.GK), with "-again" for one drawn before
      const on = t === 'hyp' ? info.hyps.has(id) : t === 'test' ? info.tests.has(id) : t === 'sim' ? info.sims.has(id) : sel.t === t, hit = t === 'hyp' ? hitH.has(id) : t === 'test' && hitT.has(id);
      return `<a class="gm ${EV.GC[m.replace('-again', '')] || ''}${m.endsWith('-again') ? ' ag' : ''} ${cls || ''}${on ? ' on' : ''}${hit ? ' hit' : ''}" data-act="open" data-t="${t}" data-id="${e(id)}" data-m="${m}" title="${e(title)}">${EV.gk(m)}</a>`; };
    // ---- the columns: every turn recorded by the replay's step; its experiment; the tests of that experiment, one place each
    const cols = M.turns.filter(t => live || (t.steps[0] ? t.steps[0].k : 0) <= S.step).map(t => { const x = t.exp && seen(t.exp.id) ? t.exp : null, ts = x ? M.tests.filter(T => T.exp === x.id) : [];
      const own = t.hyps.filter(h => seen(h.id) && !ts.some(T => T.hyp === h.id));  // stated in this turn and not tested in it
      return { t, x, ts, own }; });
    // the size of a mark, the marks in one line of a column and whether the rows' short notes are shown: the largest of these
    // with which every turn fits the width of the page; with none, the smallest, and the table scrolls sideways. A column
    // with more tests than fit in one line wraps, the same way in every row, so a test still stands in one line downwards.
    const anyLeft = cols.some(c => c.t.n && c.t.left != null);  // a session that records the simulations left at no turn says so once, in the key, not under every turn
    const room = document.getElementById('ev').clientWidth - 76, places = (c, cap, per) => Math.max(Math.min(c.ts.length + c.own.length, cap), Math.min(c.x ? c.x.sims.length : 0, per), 1);
    const fit = [[17, 8, 6, 1], [15, 8, 6, 1], [13, 6, 5, 1], [13, 6, 4, 0], [11, 5, 4, 0]].find(([w, cap, per, notes]) => (notes ? 320 : 170) + cols.reduce((a, c) => a + Math.max(c.t.n && c.t.left == null && anyLeft ? 66 : 52, places(c, cap, per) * w) + 25, 0) <= room), fits = !!fit;  // 66: room for "not recorded" under the turn's name
    const [W, cap, per, notes] = fit || [11, 5, 4, 0]; cols.forEach(c => { c.w = W * places(c, cap, per); });
    const hm = (h, first, c) => { const s = st ? st[h.id] || 'open' : h.state;  // a hypothesis is drawn in full once, where it was stated; small and faint wherever it stands again
      return mark(!first ? 'hyp-again' : s === 'dropped' ? 'dropped' : 'hyp', 'hyp', h.id, first ? h.id : c.x.id, first ? `${h.id} · ${s}` : `${h.id}, ${h.turn === c.t.n ? 'put to another decision rule' : `stated in turn ${h.turn} and tested here`}`); };
    const cell = {
      hyp: c => c.ts.map((T, i) => { const h = M.hypById[T.hyp]; return h ? hm(h, h.turn === c.t.n && c.ts.findIndex(q => q.hyp === h.id) === i, c) : gap; }).concat(c.own.map(h => hm(h, true))).join(''),
      rule: c => c.ts.map(T => (T.rule ? mark('rule', 'test', T.id, T.exp, `the decision rule for ${T.hyp}`) : gap)).join(''),
      sim: c => (!c.x ? '' : `<a class="gx${sel.t === 'exp' && sel.id === c.x.id ? ' on' : ''}" data-act="open" data-t="exp" data-id="${e(c.x.id)}" title="experiment ${e(c.x.id)}">${e(c.x.id)}</a>`
        + c.x.sims.map(q => mark(q.same_as ? 'sim-returned' : 'sim', 'sim', q.id, q.id, `${q.id} · ${q.label || ''}${q.same_as ? ' · returned from ' + q.same_as : ''}`, q.error ? 'bad' : '')).join('')),
      check: c => c.ts.map(T => { const k = T.check; return k ? mark(k.result === 'held' || k.result === 'failed' || k.result === 'void' ? k.result : 'not-checked', 'test', T.id, k.id, k.void ? `${k.id} · ${EV.VOID}` : `${k.id} · ${k.result}`) : gap; }).join(''),
      verdict: c => c.ts.map((T, i) => { const v = T.verdict, odd = v && EV.contradicts(v, T.check ? [T.check] : []), kind = v && ['supported', 'refuted'].includes(v.result) ? v.result : 'inconclusive';
        const again = v && c.ts.findIndex(q => q.verdict === v) !== i;  // one verdict for a hypothesis put to several decision rules: in full once, small and faint under the others
        return v ? mark(kind + (again ? '-again' : ''), 'test', T.id, v.id, `${v.id} · ${v.result}, given in turn ${v.turn}${again ? ' · the same verdict: one hypothesis, several decision rules' : ''}${v.voidOnly ? ' · ' + EV.RESTS : ''}${odd ? ' · disagrees with its check' : ''}`, odd ? 'odd' : '') : gap; }).join(''),
      report: c => (c.t.report ? mark('report', 'report', 'report', c.t.report.id, 'the final report') : ''),
    };
    const row = (by, icon, term, word, count, note, k) => `<tr data-by="${by}"><th><span class="gi">${EV.gk(icon)}</span>${EV.term(term, word)} <b>${count}</b>${notes || note === EV.nr ? ` <span class="sm">${note}</span>` : ''}</th>${cols.map(c => `<td><div class="gs" style="width:${c.w}px">${cell[k](c)}</div></td>`).join('')}</tr>`;
    const head = cols.map(c => { const r = c.t.malformed.concat(c.t.refusals).filter(q => seen(q.id)).length;
      return `<td><a class="gt${sel.t === 'log' && sel.id === c.t.n ? ' on' : ''}" data-act="open" data-t="log" data-id="${c.t.n}">${c.t.n ? 'turn ' + c.t.n : 'start'}</a>${r ? `<span class="grf warnc" data-refused="${r}" title="${r} refused answer${r === 1 ? '' : 's'} or part${r === 1 ? '' : 's'} of an answer in this turn">${r}</span>` : ''}${
        c.t.n && anyLeft ? `<div class="gleft" data-left="${c.t.left ?? ''}" title="${c.t.left == null ? 'How many simulations were left at the start of this turn is not recorded (sessions before s008)' : `${c.t.left} simulation${c.t.left === 1 ? ' was' : 's were'} left at the start of turn ${c.t.n}`}">${c.t.left == null ? EV.nr : c.t.left + ' left'}</div>` : ''}</td>`; }).join('');
    const has = f => cols.some(f), res = k => M.checks.some(q => q.result === k && seen(q.id)), vd = k => M.recs.some(r => r.type === 'verdict' && r.body.result === k && seen(r.id));  // the key names a sign only once one is drawn
    const K = EV.gkey, key = [[K('held') + 'held', res('held')], [K('failed') + 'failed', res('failed')], [K('void') + EV.VOID, res('void')], [K('supported') + 'supported', vd('supported')], [K('refuted') + 'refuted', vd('refuted')], [K('inconclusive') + 'inconclusive', vd('inconclusive')],
      [K('hyp-again') + 'small and faint: the same hypothesis or verdict again (stated in an earlier turn, or put to another decision rule)', has(c => c.ts.some((T, i) => { const h = M.hypById[T.hyp]; return (h && (h.turn !== c.t.n || c.ts.findIndex(q => q.hyp === T.hyp) !== i)) || (T.verdict && seen(T.verdict.id) && c.ts.findIndex(q => q.verdict === T.verdict) !== i); }))],
      [K('sim-returned') + 'a simulation returned from an earlier one, not run again', M.sims.some(q => q.same_as && seen(q.id))], ['X0: the harness\'s baseline, outside the budget', M.exps.some(x => x.by === 'harness' && seen(x.id))],
      [K('dropped') + 'dropped', M.hyps.some(h => h.drop && seen(h.drop.id))], ['<span class="grf warnc">n</span> refused answers or parts in that turn', cols.some(c => c.t.malformed.concat(c.t.refusals).some(q => seen(q.id)))],
      [`<span id="gl-left">simulations left at each turn: ${EV.nr}</span>`, !anyLeft && cols.some(c => c.t.n)]].filter(q => q[1]).map(q => `<span>${q[0]}</span>`).join('');
    EV._gl = '';
    return `<div class="ev-card noprint" id="s-made"><h2>What this session is made of <small>one mark per item · a column is one ${EV.term('Turn', 'turn')}, read downwards${fits ? '' : ` · <b class="warnc">the ${cols.length} columns are wider than the page: scroll the table sideways for the later turns</b>`}</small> ${foldBtn}</h2>
      <div class="ev-scroll gl-scroll${fits ? '' : ' gl-more'}"><table class="gl" style="--gw:${W}px"><thead><tr data-by="harness"><th><span class="gi"></span>${EV.term('Turn', 'Turns')} <b>${n.turn}</b>${notes ? ' <span class="sm">one answer of the model each</span>' : ''}</th>${head}</tr></thead><tbody>
        ${row('model', 'hyp', 'Hypothesis', 'Hypotheses', n.hyp, 'the model\'s claims', 'hyp')}
        ${row('model', 'rule', 'Decision rule', 'Decision rules', n.rule, 'stated before the simulations', 'rule')}
        ${row('simulator', 'sim', 'Simulation', 'Simulations', n.sim, `in ${n.exp} ${EV.term('Experiment', n.exp === 1 ? 'experiment' : 'experiments')}`, 'sim')}
        ${row('harness', 'held', 'Check', 'Checks', n.check, M.old ? EV.nr : 'the harness applies each rule', 'check')}
        ${row('model', 'supported', 'Verdict', 'Verdicts', n.verdict, 'the model\'s judgments', 'verdict')}
        ${row('model', 'report', 'Final report', 'Final report', n.report, 'the model\'s answer', 'report')}</tbody></table></div>
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
