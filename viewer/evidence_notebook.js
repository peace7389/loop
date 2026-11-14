// The notebook: the main view of a session's work. One card per test (one hypothesis put to one decision rule), under a
// light heading per turn ("Turn 2 · 28 simulations left"); an exploration is a heading with its question and its
// simulations, without a card. A card has the same six lines, always in this order, each a recorded text or a measured
// number, with the small colour of who produced it:
//   Question    the hypothesis's question (a session that recorded none: the hypothesis text)          model
//   Plan        what differs between the simulations the decision rule names, from their settings       model's design
//   Expected    the decision rule for reading (evidence_read.js), and its rival in one line             model
//   Result      the same rule with the measured numbers, and held or failed; a number opens its run     simulator, harness
//   Conclusion  the verdict and the first sentence of its "because"; "more" shows the rest               model
//   So next     the verdict's "next", and a link to each hypothesis that follows from this test          model
// The left edge says the outcome: expected and found (held), expected and not found (failed); a failed check is a
// result, not a warning. A void check has a neutral edge. "changed course here": the check failed and a later
// hypothesis follows from this test (it names its check, its verdict or its simulations, or the table of its experiment). A click on a card opens the test in the detail pane, as a row of the tests list does.
// Under a result: how long before its simulations came back the decision rule was stated, from the records' times, or
// that the rule names a simulation that had already run (EV.nbGap). In a running session (evidence_live.js) the turn that
// is being worked on is marked, a line that waits says what it waits for, and while a reply is written that may set up
// a test the turn ends with one card whose six lines are empty.
// The same tests as a list (with margins) and as a tree are analysis views, folded under "Looking closer".
// The key moments of the session (once the card "Highlights") are marks on the cards: the first test that held,
// "changed course here", a test the report's first claim cites, the simulation that gave the best result.
// ======================================================================================================
Object.assign(EV, {
  // what differs between the simulations a test's rule names, in words built from their settings; then what they share
  // that is not the brief's default
  nbPlan(T) { if (T._plan === undefined) T._plan = EV.nbPlan1(T); return T._plan; },  // built once for a test: it depends on the records alone
  nbPlan1(T) {
    const M = EV.M, e = EV.e, x = M.expById[T.exp], planned = !T.sims.length && !M.ended && x && !x.evidence ? x.runs.filter(r => T.labels.includes(r.label) || (!T.labels.length && x.runs.length === 1)) : [];  // an experiment whose results are not in yet: its designs, as it stated them
    const sims = planned.length ? planned.map(r => ({ params: r.params || {} })) : T.sims, kn = (M.brief && M.brief.knobs) || null; if (!sims.length) return T.rule ? `the simulations this rule names: ${EV.nr}` : EV.nr;
    const keys = kn ? Object.keys(kn) : [...new Set(sims.flatMap(s => Object.keys(s.params)))], name = k => TH_DATA.KNOB[k] || k, show = (k, v) => TASK_VIEW._rate(String(EV.val(k, v))).replace(/^Tcp/, '');
    const num = v => (typeof v === 'number' ? v : /^[0-9.]+\s*[kMG]?bps$/.test(String(v)) ? EV.knNum(v) : NaN), same = (a, b) => (isNaN(num(a)) || isNaN(num(b)) ? String(a) === String(b) : num(a) === num(b));
    const vals = k => { const out = []; sims.forEach(s => { if (k in s.params && !out.some(v => same(v, s.params[k]))) out.push(s.params[k]); }); return out; };
    const vary = keys.filter(k => vals(k).length > 1), fixed = keys.filter(k => !vary.includes(k) && k in sims[0].params && kn && kn[k] && 'default' in kn[k] && !same(sims[0].params[k], kn[k].default));
    const words = k => { const v = vals(k), nums = v.every(q => !isNaN(num(q))); if (nums) v.sort((a, b) => num(a) - num(b));
      return `${name(k)} ${v.length <= 4 || !nums ? v.map(q => show(k, q)).join(', ') : `${show(k, v[0])} to ${show(k, v[v.length - 1])} (${v.length} values)`}`; };
    const at = fixed.map(k => `${name(k)} ${show(k, sims[0].params[k])}`).join(', ');
    return e(`${sims.length} simulation${sims.length === 1 ? '' : 's'}${planned.length ? ' planned' : ''}${vary.length ? ': ' + vary.map(words).join('; ') : sims.length > 1 ? ' with the same settings' : ''}${at ? (vary.length ? ' at ' : ': ') + at : vary.length ? '' : kn ? ', every knob at its default' : ''}`);
  },
  // the first sentence of a text (a full stop inside a number does not end it), and whether more follows
  nbFirst(text) { const s = String(text || '').trim(), m = s.match(/^[\s\S]*?[.!?](?=\s+[A-Z(“"']|\s*$)/); return m && m[0].length < s.length ? [m[0], true] : [s, false]; },
  nbCard(T) {
    const M = EV.M, S = EV.s, e = EV.e, x = M.expById[T.exp], h = M.hypById[T.hyp], c = T.check, v = T.verdict, st = id => M.recStep[id] ?? 0, end = M.steps.length - 1, sel = S.sel || {};
    const now = EV.liveNow(), wait = !!now && now.phase === 'sims' && T.exp === now.exp, judge = !!now && now.phase === 'reply' && now.mode !== 'report' && !!c && !v;  // a running session: its simulations are running; this reply may judge it
    const kx = st(x.id), kc = c ? st(c.id) : end, kv = v ? st(v.id) : end, fol = T._fol || (T._fol = EV.followers(T)), turned = !!c && c.result === 'failed' && fol.ids.length > 0;
    // own: the line is the model's own recorded text (not the page's words); exact: a setting's values, shown as recorded
    const line = (k, by, body, step, cls, mark) => `<div class="nb-l${cls ? ' ' + cls : ''}" data-l="${k.toLowerCase().replace(' ', '-')}" data-step="${step}"><span class="nb-k">${by.map(b => `<i class="sw" data-by="${b}" title="produced by the ${b === 'model' ? 'AI' : b}"></i>`).join('')}${k}</span><div class="nb-v"${mark ? ` ${mark}` : ''}>${body}</div></div>`;
    const gap = c ? EV.nbGap(T) : '', here = (text, k) => `<span class="nowp" data-now="${k}">${EV.nowDot()}${text}</span>`;
    const pending = M.ended ? (h && h.verdict ? 'no verdict here: the hypothesis was tested again first' : 'no verdict: the session ended without one') : 'not yet';
    const [first, rest] = v ? EV.nbFirst(v.because) : ['', false], open = (S.nbmore || {})[T.id];
    const fk = Math.max(kv, ...fol.ids.map(id => st(id))), mo = EV.moments(M), mis = v ? mo.verdict[v.id] : null;
    const marks = [mo.first === T.id ? `<span class="nb-mark" data-m="first" data-step="${kc}" title="The first test of this session whose check held">first test that held</span>` : '',
      turned ? `<span class="nb-mark nb-turn-mark" data-m="turned" data-step="${fk}" title="Its check failed, and ${e(fol.ids.join(', '))} follow${fol.ids.length === 1 ? 's' : ''} from it${fol.via ? ' (through the table ' + e(fol.via) + ' of its experiment)' : ''}">changed course here</span>` : '',
      mo.best && T.best ? `<a class="nb-mark" data-m="best" data-act="open" data-t="sim" data-id="${e(mo.best.sim.id)}" data-step="${mo.best.step}" title="${e(`Simulation ${mo.best.sim.id} (number ${mo.best.n} of ${mo.best.of}) gave the best result that meets the brief's conditions; none after it improved on it`)}">best result: ${e(mo.best.sim.id)}</a>` : '',
      mo.cited.has(T.id) ? `<span class="nb-mark" data-m="cited" data-step="${mo.citedStep}" title="The first claim of the final report cites this test">cited by claim 1</span>` : ''].join('');
    return `<div class="nb-card${sel.t === 'test' && sel.id === T.id ? ' sel' : ''}" data-act="open" data-t="test" data-id="${e(T.id)}" data-res="${c ? e(c.result) : 'none'}" data-step="${kx}"${EV.freshAttr(x.id)}>
      ${line('Question', ['model'], h && !h.question ? `<span class="lc3"><b>${e(T.hyp)}</b> ${e(h.text)}</span>` : `<b>${e(T.hyp)}</b> ${h ? EV.question(h) : EV.nr}`, st(T.hyp) < kx ? kx : st(T.hyp), 'nb-q', 'data-own="model"')}
      ${line('Plan', ['model'], EV.nbPlan(T), kx, '', 'data-exact="1"')}
      ${line('Expected', ['model'], `${EV.ruleRead(T, 4)}${T.rival ? `<div class="sm lc2" title="${e(T.rival)}">${EV.term('Rival', 'rival')}: <span data-own="model">${e(T.rival)}</span></div>` : ''}`, kx)}
      ${line('Result', ['simulator', 'harness'], c ? EV.checkRead(T, 4) + gap : wait ? here(`the simulator is working on its simulations${EV.liveTimer()}`, 'sims') : `<span class="mut">${T.rule ? (M.ended ? 'not checked' : 'not yet') : 'no decision rule'}</span>`, kc)}
      ${line('Conclusion', ['model'], v ? `${v.id} ${EV.verdictRes(v.result)}${EV.rests(v)}${EV.contradicts(v, c ? [c] : []) ? ' ' + EV.warn('disagrees with its check') : ''}${first ? ' · ' + e(open || !rest ? v.because : first) : ''}${rest ? ` <a class="noprint sm" data-act="nbmore" data-id="${e(T.id)}">${open ? 'less' : 'more'}</a>` : ''}${mis ? ' ' + EV.warn('a number differs from its measurement', `It wrote “${mis.rows[0].written}”; measured ${mis.rows[0].measured}`) : ''}` : judge ? here('not judged yet: the reply being written may judge it', 'reply') : `<span class="mut">${pending}</span>`, kv, '', v ? 'data-own="model"' : '')}
      ${line('So next', ['model'], v ? `${v.next ? e(v.next) : EV.nr}${fol.ids.length ? ` <span class="sm" data-step="${fk}">· followed by ${fol.ids.map(id => `<a data-act="open" data-t="hyp" data-id="${e(id)}">${EV_ICON.hypothesis}${e(id)}</a>`).join(', ')}${fol.via ? ` (through the table ${e(fol.via)})` : ''}</span>` : ''}` : `<span class="mut">${pending === 'not yet' ? 'not yet' : 'no verdict, so no next step'}</span>`, kv, '', v ? 'data-own="model"' : '')}
      ${marks ? `<div class="nb-marks">${marks}</div>` : ''}</div>`;
  },
  // how long after its decision rule was recorded a test's simulations came back, from the records' times; or that it names a simulation that had already run
  nbGap(T) {
    const M = EV.M, x = M.expById[T.exp], first = s => { const o = s.same_as && M.simById[s.same_as]; return o ? o.ts : s.ts; }, ts = T.sims.map(first).filter(Boolean).sort(); if (!T.rule || !x.ts || !ts.length) return '';
    const early = T.sims.filter(s => first(s) && first(s) < x.ts), secs = Math.round((new Date(ts[0]) - new Date(x.ts)) / 1000), tip = `The decision rule was recorded at ${EV.time(x.ts)}; its simulations at ${EV.time(ts[0])}${ts[ts.length - 1] !== ts[0] ? ' to ' + EV.time(ts[ts.length - 1]) : ''}. From the records' times.`;
    return `<div class="sm nb-when" data-before="${early.length ? 0 : 1}" data-secs="${early.length ? '' : secs}" title="${EV.e(tip)}">${early.length ? `the rule names ${early.length === T.sims.length && early.length > 1 ? 'simulations' : 'a simulation'} that had already run when it was stated (${EV.e(early.map(s => s.same_as || s.id).join(', '))})` : `the rule was stated ${EV.liveClock(secs * 1000)} before its simulations came back`}</div>`;
  },
  // while the AI writes a reply that may set up a test: a card with its six lines empty
  nbSlot() { const l = (k, by) => `<div class="nb-l"><span class="nb-k">${by.map(b => `<i class="sw" data-by="${b}"></i>`).join('')}${k}</span><div class="nb-v"><span class="mut">empty</span></div></div>`;
    return `<div class="nb-card nb-slot" id="nb-next" data-slot="test"><div class="nb-slot-h">${EV.nowDot()}The next test, if this reply sets one up${EV.liveTimer()}</div>${l('Question', ['model'])}${l('Plan', ['model'])}${l('Expected', ['model'])}${l('Result', ['simulator', 'harness'])}${l('Conclusion', ['model'])}${l('So next', ['model'])}</div>`; },
  notebookCard() {
    const now = EV.liveNow();
    const M = EV.M, S = EV.s, e = EV.e, st = id => M.recStep[id] ?? 0, sel = S.sel || {}, pl = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
    const dots = x => x.sims.map(q => `<a class="nb-dot" data-act="open" data-t="sim" data-id="${e(q.id)}" data-step="${st(q.id)}" title="${e(`${q.id} · ${q.label || ''}${q.same_as ? ' · returned from ' + q.same_as : ''}`)}">${EV.gkey(q.same_as ? 'sim-returned' : 'sim')}</a>`).join('');
    const mo = EV.moments(M), bs = mo.best ? mo.best.sim : null; M.tests.forEach(T => { T.best = false; }); const holder = bs ? M.tests.find(T => T.sims.includes(bs)) : null; if (holder) holder.best = true;
    const bestMark = bs && !holder ? ` <a class="nb-mark" data-m="best" data-act="open" data-t="sim" data-id="${e(bs.id)}" data-step="${mo.best.step}" title="${e(`Simulation ${bs.id} (number ${mo.best.n} of ${mo.best.of}) gave the best result that meets the brief's conditions; none after it improved on it`)}">best result: ${e(bs.id)}</a>` : '';
    const body = M.turns.map(t => { const k0 = t.steps[0] ? t.steps[0].k : 0, x = t.exp, ts = x ? M.tests.filter(T => T.exp === x.id) : [], bits = [], here = bestMark && x && x.sims.includes(bs) ? bestMark : '', om = mo.turn[t.n];
      if (t.verdicts.length) bits.push(pl(t.verdicts.length, 'verdict')); if (t.hyps.length) bits.push(`${t.hyps.length} new hypothes${t.hyps.length === 1 ? 'is' : 'es'}`); if (t.drops.length) bits.push(`${t.drops.length} dropped`);
      const refused = t.malformed.length + t.refusals.length; if (refused) bits.push(`${refused} refused`); if (t.report) bits.push('the final report');
      const head = t.n === 0 ? `<div class="nb-head nb-start" data-act="open" data-t="exp" data-id="${x ? e(x.id) : 'X0'}" data-step="${k0}"><b>Start</b> · the harness's baseline: ${x && !x.sims.length && now && now.phase === 'baseline' ? `<span class="nowp nb-now" data-now="baseline">${EV.nowDot()}its simulation is running${EV.liveTimer()}</span>` : x ? pl(x.sims.length, 'simulation') : EV.nr} ${x ? dots(x) : ''}</div>`
        : `<div class="nb-head nb-turn${sel.t === 'log' && sel.id === t.n ? ' sel' : ''}" data-act="open" data-t="log" data-id="${t.n}" data-turn="${t.n}" data-step="${k0}"><b>Turn ${t.n}</b> · ${t.left == null ? 'simulations left: ' + EV.nr : pl(t.left, 'simulation') + ' left'}${bits.length ? ` <span class="sm">· ${e(bits.join(' · '))}</span>` : ''}${om ? ` <span data-step="${om.step}">${EV.warn('a number in its observations differs from its measurement', `It wrote “${om.rows[0].written}”; measured ${om.rows[0].measured}`)}</span>` : ''}${here && ts.length ? here : ''}${now && now.turn === t.n ? ` <span class="nowp nb-now" data-now="${now.phase}">${EV.nowDot()}${now.phase === 'reply' ? 'the AI is writing its reply' : now.phase === 'sims' ? `the simulator is working on ${e(now.exp)}` : 'the harness is preparing the next turn'}${EV.liveTimer()}</span>` : ''}</div>`;
      const explore = x && t.n > 0 && !ts.length ? `<div class="nb-head nb-exp${sel.t === 'exp' && sel.id === x.id ? ' sel' : ''}" data-act="open" data-t="exp" data-id="${e(x.id)}" data-step="${st(x.id)}">${EV_ICON.experiment} ${e(x.id)} explores: <span data-own="model">“${e(x.question || 'not recorded')}”</span> · ${pl(x.sims.length, 'simulation')} ${dots(x)}${here}</div>` : '';
      const why = m => (m.body.refused || []).map(q => `${q.part}: ${q.reason}`).join(' | ') || m.body.reason || m.body.error || m.body.text || 'no reason recorded';
      const refusedLines = t.malformed.map(m => ['the whole answer', m]).concat(t.refusals.map(m => [m.body.part === 'report' ? 'the final report' : `the part “${m.body.part}”`, m]))
        .map(([what, m]) => `<div class="nb-refused" data-act="open" data-t="log" data-id="${t.n}" data-step="${st(m.id)}" data-rec="${e(m.id)}" title="${e(why(m))}">${EV.warn('refused')} <span data-own="harness">${e(what)}:</span> <span class="lc2" data-own="harness">${e(why(m))}</span></div>`).join('');
      const slot = now && now.phase === 'reply' && now.turn === t.n ? (now.mode ? `<div class="nb-refused nb-last" data-slot="report"><span class="mut">${now.mode === 'report' ? 'The last turn: only the final report is accepted.' : 'The last turn: the simulations are used up. No new test is accepted; the final report is due.'}</span></div>` : EV.nbSlot()) : '';
      return head + refusedLines + explore + ts.map(T => EV.nbCard(T)).join('') + slot; }).join('');
    return `<div class="ev-card" id="s-notebook"><h2>The work, step by step <small>the notebook · one card per ${EV.term('Test', 'test')}: the question, the plan, what was expected, what was found, the conclusion and what came next</small></h2>
        <p class="sec-q">How did it test each?</p><div class="ev-bar nb-bar">${EV.replayBar()}</div>
        ${M.turns.length ? body : '<p class="sm">No record yet.</p>'}
        <p class="sm nb-key">The left edge of a card: the outcome of its test. The small square before a line: who produced it. The colours are named in the legend at the top of the page. A number in Result opens its simulation.</p></div>`;
  },
});
EV.act = Object.assign(EV.act || {}, {
  nbmore(id) { const q = EV.s.nbmore = EV.s.nbmore || {}; q[id] = !q[id]; EV.draw(); },
});
