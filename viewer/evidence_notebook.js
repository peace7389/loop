// The notebook: the main view of a session's work. One card per test (one hypothesis put to one decision rule), under a
// light heading per turn ("Turn 2 · 28 simulations left"); an exploration is a heading with its question and its
// simulations, without a card. A card has the same six lines, always in this order, each a recorded text or a measured
// number, with the small colour of who produced it:
//   Question    the hypothesis's question (a session that recorded none: the hypothesis text)          model
//   Why         why answering it helps reach the goal, in the model's words; only where it is recorded   model
//               (the harness requires it of every new hypothesis since 2026-11-14)
//   Plan        what differs between the simulations the decision rule names, from their settings       model's design
//   Expected    the decision rule for reading (evidence_read.js), and its rival in one line             model
//   Result      the same rule with the measured numbers, and held or failed; a number opens its run     simulator, harness
//   Verdict     the verdict and the first sentence of its "because"; "more" shows the rest               model
//   So next     the verdict's "next", and a link to each hypothesis that follows from this test          model
// A turn's heading and everything of that turn (its refused parts, its exploration, its cards) stand in one bordered
// region, with more space between two turns than inside one, so that what belongs to one turn is seen at a glance.
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
    const keys = kn ? Object.keys(kn) : [...new Set(sims.flatMap(s => Object.keys(s.params)))], name = k => TH_DATA.KNOB[k] || k, show = (k, v) => (k === 'tcpBufBytes' && /^\d+$/.test(String(v)) ? EV.bytes(+v) : TASK_VIEW._rate(String(EV.val(k, v))).replace(/^Tcp/, '') + (k === 'duration' ? ' s' : ''));
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
    const line = (k, by, body, step, cls, mark) => `<div class="nb-l${cls ? ' ' + cls : ''}" data-l="${k === 'Hypothesis' ? 'question' : k === 'Verdict' ? 'conclusion' : k.toLowerCase().replace(' ', '-')}" data-step="${step}"><span class="nb-k">${by.map(b => `<i class="sw" data-by="${b}" title="produced by ${b === 'model' ? 'the AI' : b === 'simulator' ? 'ns-3' : 'the ' + b}"></i>`).join('')}${k}</span><div class="nb-v"${mark ? ` ${mark}` : ''}>${body}</div></div>`;
    const why = h && h.from_why ? (M.whyById || {})[h.from_why] : null;  // the informed guess this hypothesis comes from (sessions since 2026-11-17)
    const gap = c ? EV.nbGap(T) : '', here = (text, k) => `<span class="nowp" data-now="${k}">${EV.nowDot()}${text}</span>`;
    const pending = M.ended ? (h && h.verdict ? 'no verdict here: the hypothesis was tested again first' : 'no verdict: the session ended without one') : 'not yet';
    const [first, rest] = v ? EV.nbFirst(v.because) : ['', false], open = (S.nbmore || {})[T.id];
    const fk = Math.max(kv, ...fol.ids.map(id => st(id))), mo = EV.moments(M), mis = v ? mo.verdict[v.id] : null;
    const marks = [mo.first === T.id ? `<span class="nb-mark" data-m="first" data-step="${kc}" title="The first test of this session whose check held">first test that held</span>` : '',
      turned ? `<span class="nb-mark nb-turn-mark" data-m="turned" data-step="${fk}" title="Its check failed, and ${e(fol.ids.join(', '))} follow${fol.ids.length === 1 ? 's' : ''} from it${fol.via ? ' (through the table ' + e(fol.via) + ' of its experiment)' : ''}">changed course here</span>` : '',
      mo.best && T.best ? `<a class="nb-mark" data-m="best" data-act="open" data-t="sim" data-id="${e(mo.best.sim.id)}" data-step="${mo.best.step}" title="${e(`Simulation ${mo.best.sim.id} (number ${mo.best.n} of ${mo.best.of}) gave the best result that meets the brief's conditions; none after it improved on it`)}">best result: ${e(mo.best.sim.id)}</a>` : '',
      mo.cited.has(T.id) ? `<span class="nb-mark" data-m="cited" data-step="${mo.citedStep}" data-wd="c:1">cited by claim 1</span>` : ''].join('');
    return `<div class="nb-card${sel.t === 'test' && sel.id === T.id ? ' sel' : ''}" data-act="open" data-t="test" data-id="${e(T.id)}" data-res="${c ? e(c.result) : 'none'}" data-step="${kx}"${EV.freshAttr(x.id)}>
      <div class="nb-blk nb-blk-q">${why ? line('Its guess', ['model'], `<span class="lc2" title="${e(`${why.result} Its guess of why: ${why.guess} Not visible: ${why.unseen} For the goal: ${why.matters}`)}">${EV.whyLink(h.from_why)} ${e(why.guess)}</span>`, st(T.hyp) < kx ? kx : st(T.hyp), 'nb-guess', 'data-own="model"') : ''}
      ${line('Hypothesis', ['model'], h && !h.question ? `<span class="lc3"><b>${e(T.hyp)}</b> ${e(h.text)}</span>` : `<b>${e(T.hyp)}</b> ${h ? EV.question(h) : EV.nr}`, st(T.hyp) < kx ? kx : st(T.hyp), 'nb-q', 'data-own="model"')}
      ${h && h.why ? line('Why', ['model'], `<span class="lc2" title="${e(h.why)}">${e(h.why)}</span>`, st(T.hyp) < kx ? kx : st(T.hyp), 'nb-why', 'data-own="model"') : ''}
</div>
      <div class="nb-blk nb-blk-t">${T.need ? line('Needs', ['model'], `<span class="lc2" title="${e(T.need.to_know)}">${e(T.need.to_know)}</span><div class="sm">${T.need.varies === 'none' ? 'one simulation against a number it states' : `only ${e(T.need.varies === 'structure' ? 'the structure' : TH_DATA.KNOB[T.need.varies] || T.need.varies)} differs between its simulations`} · decided by ${e(TH_DATA.PLAIN[T.need.measure] || T.need.measure)}</div>`, kx, 'nb-need', 'data-own="model"') : ''}
      ${line('Plan', ['model'], EV.nbPlan(T), kx, '', 'data-exact="1"')}
      ${line('Expected', ['model'], `${EV.ruleList(T, 3)}${T.rival ? `<div class="sm lc2" title="${e(T.rival)}">${EV.term('Rival', 'rival')}: <span data-own="model">${e(T.rival)}</span></div>` : ''}`, kx)}
      ${line('Result', ['simulator', 'harness'], c ? (bars => (bars ? `<span class="hp-badge ck-${c.void ? 'void' : e(c.result)} nb-res" data-rr="check" title="${e(c.numbers == null ? '' : c.numbers + ' : ' + (c.recorded || c.result))}">${EV.checkRes(c)}</span>${bars}` : EV.checkRead(T, 4)))(EV.ruleBars(T, 3, false, true)) + EV.closeNote(T, true) + gap : wait ? here(`ns-3 is working on its simulations${EV.liveTimer()}<span class="nb-sims-n"></span> · <a data-act="livego" data-id="tiles" style="text-decoration:underline;cursor:pointer" title="To the pictures of the running simulations, in “What it needed to find out”">watch them</a>`, 'sims') : `<span class="mut">${T.rule ? (M.ended ? 'not checked' : 'not yet') : 'no decision rule'}</span>`, kc)}
</div>
      <div class="nb-blk nb-blk-o">${line('Verdict', ['model'], v ? `${v.id} ${EV.verdictRes(v.result)}${EV.rests(v)}${EV.contradicts(v, c ? [c] : []) ? ' ' + EV.warn('disagrees with its check') : ''}${first ? ' · ' + e(open || !rest ? v.because : first) : ''}${rest ? ` <a class="noprint sm" data-act="nbmore" data-id="${e(T.id)}">${open ? 'less' : 'more'}</a>` : ''}${mis ? ' ' + EV.warn('a number differs from its measurement', `It wrote “${mis.rows[0].written}”; measured ${mis.rows[0].measured}`) : ''}` : judge ? here('not judged yet: the reply being written may judge it', 'reply') : `<span class="mut">${pending}</span>`, kv, '', v ? 'data-own="model"' : '')}
      ${line('So next', ['model'], v ? `${v.next ? e(v.next) : EV.nr}${fol.ids.length ? ` <span class="sm" data-step="${fk}">· followed by ${fol.ids.map(id => `<a data-act="open" data-t="hyp" data-id="${e(id)}">${EV_ICON.hypothesis}${e(id)}</a>`).join(', ')}${fol.via ? ` (through the table ${e(fol.via)})` : ''}</span>` : ''}` : `<span class="mut">${pending === 'not yet' ? 'not yet' : 'no verdict, so no next step'}</span>`, kv, '', v ? 'data-own="model"' : '')}
</div>
      ${marks ? `<div class="nb-marks">${marks}</div>` : ''}</div>`;
  },
  // how long after its decision rule was recorded a test's simulations came back, from the records' times; or that it names a simulation that had already run
  nbGap(T) {
    const M = EV.M, x = M.expById[T.exp], first = s => { const o = s.same_as && M.simById[s.same_as]; return o ? o.ts : s.ts; }, ts = T.sims.map(first).filter(Boolean).sort(); if (!T.rule || !x.ts || !ts.length) return '';
    const early = T.sims.filter(s => first(s) && first(s) < x.ts), secs = Math.round((new Date(ts[0]) - new Date(x.ts)) / 1000), tip = `The decision rule was recorded at ${EV.time(x.ts)}; its simulations at ${EV.time(ts[0])}${ts[ts.length - 1] !== ts[0] ? ' to ' + EV.time(ts[ts.length - 1]) : ''}. From the records' times.`;
    return `<div class="sm nb-when" data-before="${early.length ? 0 : 1}" data-secs="${early.length ? '' : secs}" title="${EV.e(tip)}">${early.length ? `the rule names ${early.length === T.sims.length && early.length > 1 ? 'simulations' : 'a simulation'} that had already run when it was stated (${EV.e(early.map(s => s.same_as || s.id).join(', '))})` : `the rule was stated ${EV.liveClock(secs * 1000)} before its simulations came back`}</div>`;
  },
  // while the AI writes a reply that may set up a test: a card with its six lines empty
  nbSlot() { const l = (k, by) => `<div class="nb-l" data-l="${k === 'Hypothesis' ? 'question' : k === 'Verdict' ? 'conclusion' : k.toLowerCase().replace(' ', '-')}"><span class="nb-k">${by.map(b => `<i class="sw" data-by="${b}"></i>`).join('')}${k}</span><div class="nb-v"><span class="mut">empty</span></div></div>`;
    return `<div class="nb-card nb-slot" id="nb-next" data-slot="test"><div class="nb-slot-h">${EV.nowDot()}The next test, if this reply sets one up${EV.liveTimer()}</div>${l('Hypothesis', ['model'])}${l('Why', ['model'])}${l('Plan', ['model'])}${l('Expected', ['model'])}${l('Result', ['simulator', 'harness'])}${l('Verdict', ['model'])}${l('So next', ['model'])}</div>`; },
  notebookCard() {
    const now = EV.liveNow();
    const M = EV.M, S = EV.s, e = EV.e, st = id => M.recStep[id] ?? 0, sel = S.sel || {}, pl = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
    const dots = x => x.sims.map(q => `<a class="nb-dot" data-act="open" data-t="sim" data-id="${e(q.id)}" data-step="${st(q.id)}" title="${e(`${q.id} · ${q.label || ''}${q.same_as ? ' · returned from ' + q.same_as : ''}`)}">${EV.gkey(q.same_as ? 'sim-returned' : 'sim')}</a>`).join('');
    const mo = EV.moments(M), bs = mo.best ? mo.best.sim : null; M.tests.forEach(T => { T.best = false; }); const holder = bs ? M.tests.find(T => T.sims.includes(bs)) : null; if (holder) holder.best = true;
    const bestMark = bs && !holder ? ` <a class="nb-mark" data-m="best" data-act="open" data-t="sim" data-id="${e(bs.id)}" data-step="${mo.best.step}" title="${e(`Simulation ${bs.id} (number ${mo.best.n} of ${mo.best.of}) gave the best result that meets the brief's conditions; none after it improved on it`)}">best result: ${e(bs.id)}</a>` : '';
    const body = M.turns.map(t => { const k0 = t.steps[0] ? t.steps[0].k : 0, x = t.exp, ts = x ? M.tests.filter(T => T.exp === x.id) : [], bits = [], here = bestMark && x && x.sims.includes(bs) ? bestMark : '', om = mo.turn[t.n];
      if (t.verdicts.length) bits.push(pl(t.verdicts.length, 'verdict')); if (t.hyps.length) bits.push(`${t.hyps.length} new hypothes${t.hyps.length === 1 ? 'is' : 'es'}`); if (t.drops.length) bits.push(`${t.drops.length} dropped`);
      const refused = t.malformed.length + t.refusals.length; if (refused) bits.push(`<span data-wd="z:${t.n}">${refused} part${refused === 1 ? '' : 's'} of its answer not accepted</span>`); if (t.report) bits.push('the final report');
      // a turn folds to its heading at a click on it (EV.nbFolded, kept while the page is open); folded, the heading names its tests' hypotheses with how each stands at this step
      const folded = !!EV.nbFolded[`${M.id}:${t.n}`], stNow = S.step == null ? null : EV_DATA.stateAt(M, S.step), hypState = id => (stNow ? stNow[id] || 'open' : (M.hyps.find(h => h.id === id) || {}).state);
      const foldSum = ts.length ? ` <span class="nb-fold-sum sm">· ${ts.filter(T => EV.seen(T.exp)).map(T => { const s = hypState(T.hyp); return `<span style="white-space:nowrap">${e(T.hyp)} ${['supported', 'refuted', 'inconclusive'].includes(s) ? EV.verdictRes(s) : s === 'dropped' ? 'dropped' : 'not judged'}</span>`; }).join(' · ')}</span>` : '';
      const head = t.n === 0 ? `<div class="nb-head nb-start" data-act="open" data-t="exp" data-id="${x ? e(x.id) : 'X0'}" data-step="${k0}"><b>Start</b> · the harness's baseline: ${x && !x.sims.length && now && now.phase === 'baseline' ? `<span class="nowp nb-now" data-now="baseline">${EV.nowDot()}its simulation is running${EV.liveTimer()}</span>` : x ? pl(x.sims.length, 'simulation') : EV.nr} ${x ? dots(x) : ''}</div>`
        : `<div class="nb-head nb-turn${sel.t === 'log' && sel.id === t.n ? ' sel' : ''}" data-act="nbfold" data-id="${t.n}" data-turn="${t.n}" data-step="${k0}" role="button" aria-expanded="${folded ? 'false' : 'true'}" title="Click: fold this turn to its heading, or open it again"><span class="nb-chev" aria-hidden="true">▾</span><b>Turn ${t.n}</b> · ${t.left == null ? 'simulations left: ' + EV.nr : pl(t.left, 'simulation') + ' left'}${bits.length ? ` <span class="sm">· ${e(bits.join(' · '))}</span>` : ''}${om ? ` <span data-step="${om.step}">${EV.warn('a number in its observations differs from its measurement', `It wrote “${om.rows[0].written}”; measured ${om.rows[0].measured}`)}</span>` : ''}${here && ts.length ? here : ''}${now && now.turn === t.n ? ` <span class="nowp nb-now" data-now="${now.phase}">${EV.nowDot()}${now.phase === 'reply' ? 'the AI is writing its reply' : now.phase === 'sims' ? `ns-3 is working on ${e(now.exp)}` : 'the harness is preparing the next turn'}${EV.liveTimer()}</span>` : ''}${foldSum}<a class="nb-rec" data-act="open" data-t="log" data-id="${t.n}" title="Everything this turn recorded, in the pane on the right">the turn's record</a></div>`;
      const explore = x && t.n > 0 && !ts.length ? `<div class="nb-head nb-exp${sel.t === 'exp' && sel.id === x.id ? ' sel' : ''}" data-act="open" data-t="exp" data-id="${e(x.id)}" data-step="${st(x.id)}" data-wd="x:${e(x.id)}">${EV_ICON.experiment} ${e(x.id)} explores: <span data-own="model">“${e(x.question || 'not recorded')}”</span> · ${pl(x.sims.length, 'simulation')} ${dots(x)}${here}</div>` : '';
      const why = m => (m.body.refused || []).map(q => `${q.part}: ${q.reason}`).join(' | ') || m.body.reason || m.body.error || m.body.text || 'no reason recorded';
      // Refusals of one answer that say the same thing of one hypothesis after another (an answer that judges again what was judged: "H1 is not an open hypothesis",
      // seventeen times) are one line that says how many, what and why; each stands under it, shown at a click. Counted from what is recorded by the step the page is at.
      const refs = t.malformed.map(m => ['the whole answer', m]).concat(t.refusals.map(m => [m.body.part === 'report' ? 'the final report' : `the part “${m.body.part}”`, m])), shape = ([what, m]) => `${what}|${why(m)}`.replace(/\bH\d+\b/g, 'H#');
      const alike = {}; refs.filter(([, m]) => EV.seen(m.id)).forEach(q => { (alike[shape(q)] = alike[shape(q)] || []).push(q); });
      const refLine = ([what, m], inGroup) => `<div class="nb-refused${inGroup ? ' nb-ref-in' : ''}" data-act="open" data-t="log" data-id="${t.n}" data-step="${st(m.id)}" data-rec="${e(m.id)}" title="${e(why(m))}">${EV.warn('refused')} <span data-own="harness">${e(what)}:</span> <span class="lc2" data-own="harness">${e(why(m))}</span></div>`;
      const refSum = g => { const ids = g.map(([what]) => (/\bH\d+\b/.exec(what) || [])[0]).filter(Boolean), verdicts = g.every(([what]) => /verdict for H\d+/.test(what)), judged = /is not an open hypothesis/.test(why(g[0][1]));
        return `<div class="nb-refsum" data-act="nbrefs" data-id="${t.n}" data-n="${g.length}" data-step="${Math.min(...g.map(([, m]) => st(m.id)))}" role="button" title="Click: show each of them">${EV.warn('refused')} <b>${g.length} parts of this answer were refused, for one reason:</b> ${verdicts && judged ? `it gave verdicts again for ${e(ids[0])}${ids.length > 1 ? ' to ' + e(ids[ids.length - 1]) : ''}, which already had theirs; the earlier verdicts stand` : `<span data-own="harness">${e(g[0][0])}</span> and ${g.length - 1} more like it: <span data-own="harness">${e(why(g[0][1]))}</span>`}. <span class="sm">Not an error of the system: the harness left these parts out and used the rest of the answer${t.report ? ', the final report' : ''}. <span class="nb-refs-t">show each</span></span></div>`; };
      const shown = new Set(), refusedLines = refs.map(q => { const g = EV.seen(q[1].id) ? alike[shape(q)] : null; if (!g || g.length < 3) return refLine(q); const first = !shown.has(shape(q)); shown.add(shape(q)); return (first ? refSum(g) : '') + refLine(q, true); }).join('');
      const slot = now && now.phase === 'reply' && now.turn === t.n ? (now.mode ? `<div class="nb-refused nb-last" data-slot="report"><span class="mut">${now.mode === 'report' ? 'The last turn: only the final report is accepted.' : 'The last turn: the simulations are used up. No new test is accepted; the final report is due.'}</span></div>` : EV.nbSlot()) : '';
      return `<div class="nb-group${now && now.turn === t.n ? ' nb-now-group' : ''}${folded && t.n > 0 ? ' nb-folded' : ''}${EV.nbRefsOpen[`${M.id}:${t.n}`] ? ' nb-refs-open' : ''}" data-group="${t.n}">${head + refusedLines + EV.nbWhys(t.n) + explore + ts.map(T => EV.nbCard(T)).join('') + slot}</div>`; }).join('');
    return `<div class="ev-card" id="s-notebook"><h2>The work, step by step <small>the notebook · one card per ${EV.term('Test', 'test')}: the hypothesis, the plan, what was expected, what was found, the verdict and what came next</small></h2>
        <p class="sec-q">How did it test each?</p>${EV.nbLegend()}<div class="ev-bar nb-bar">${EV.replayBar()}</div>
        ${M.turns.some(t => t.n > 0) ? `<p class="sm nb-folds noprint" id="nb-folds">Click a turn's heading to fold it to one line, and again to open it. <button class="cl" data-act="nbfoldall" data-id="1">fold every turn</button> <button class="cl" data-act="nbfoldall" data-id="0">open every turn</button></p>` : ''}
        ${M.turns.length ? body : '<p class="sm">No record yet.</p>'}
        <p class="sm nb-key">The left edge of a card: the outcome of its test. The small icon before a line: who produced it. The icons and the colours are named in the legend at the top of this card. A measured number in Result that is one measure of one simulation opens that simulation.</p></div>`;
  },
  // A guess of why is a standing part of the work (the chain: result, guess of why, hypothesis, what it needs to know, simulations), with its own mark,
  // a question mark in a ring. Its standing is not fixed by how it was first stated: the AI may look at it again (rethink) or replace it with a better one.
  WHY_NOW: { verify: 'to verify', set_aside: 'set aside', refuted: 'refuted', supported: 'supported', revised: 'replaced' },
  // a why's standing at the step the page is at: { worth, by: the record that last changed it, turn }
  whyNow(w) { const M = EV.M; let now = { worth: w.worth, by: null, turn: w.turn };
    M.recs.forEach(r => { if (!EV.seen(r.id)) return; if (r.type === 'rethink' && r.body.for === w.id) now = { worth: r.body.now, by: r.id, turn: r.turn }; else if (r.type === 'why' && r.body.revises === w.id) now = { worth: 'revised', by: r.id, turn: r.turn }; });
    return now; },
  whyPill(w) { const now = EV.whyNow(w), e = EV.e, word = EV.WHY_NOW[now.worth] + (now.worth === 'revised' ? ' by ' + now.by : '');
    return `<span class="pill" data-now="${e(now.worth)}" title="${e(now.by ? `stated as “${EV.WHY_NOW[w.worth]}” in turn ${w.turn}; ${now.worth === 'revised' ? `replaced by the better guess ${now.by}` : `looked at again (${now.by})`} in turn ${now.turn}` : `as the AI stated it in turn ${w.turn}`)}">${e(word)}</span>`; },
  whyLink(id, plain) { return `<a data-act="open" data-t="why" data-id="${EV.e(id)}" data-wd="y:${EV.e(id)}">${EV.e(id)}</a>`; },  // the mark of a guess (the question mark) stands on the headings only: the panel's, the pane's, the legend's
  // a turn's guesses of why: the earlier guesses it looked at again, then each new guess (what it saw, why it thinks so, what is not visible, what it would
  // mean for the goal), its standing now, and the hypotheses that come from it
  nbWhys(n) {
    const M = EV.M, e = EV.e, S = EV.s, ws = (M.whys || []).filter(w => w.turn === n), ks = (M.rethinks || []).filter(k => k.turn === n); if (!ws.length && !ks.length) return '';
    const used = id => M.hyps.filter(h => h.from_why === id && EV.seen(h.id)), about = w => (w.about || []).map(a => (a === 'brief' ? 'the brief' : EV.link(a))).join(', '), st = id => M.recStep[id] ?? 0;
    const count = k => ws.filter(w => w.worth === k).length, head = [ws.length ? `${count('verify')} to verify, ${count('set_aside')} set aside` : '', ks.length ? `${ks.length} earlier ${ks.length === 1 ? 'guess' : 'guesses'} looked at again` : ''].filter(Boolean).join(' · ');
    return `<div class="nb-whys" data-whys="${n}" data-step="${Math.min(...ws.concat(ks).map(q => st(q.id)))}"><div class="nb-whys-h">${EV_ICON.why}<b>Its guesses of why</b> <span class="sm">why did the results come out so? · ${head}</span></div>
      ${ks.map(k => `<div class="nb-again" data-again="${e(k.id)}" data-step="${st(k.id)}"><span class="nb-whyk">${EV_ICON.rethink} ${EV.whyLink(k.for, true)}</span><div>looked at again in the light of ${(k.in_light_of || []).map(EV.link).join(', ')}: now <span class="pill">${e(EV.WHY_NOW[k.now] || k.now)}</span> <span data-own="model">${e(k.because)}</span></div></div>`).join('')}
      ${ws.map(w => { const hs = used(w.id); return `<div class="nb-whyl pickrow${S.sel && S.sel.t === 'why' && S.sel.id === w.id ? ' sel' : ''}" data-why="${e(w.id)}" data-worth="${e(w.worth)}" data-step="${st(w.id)}" data-act="open" data-t="why" data-id="${e(w.id)}">
        <div class="nb-whyh"><b class="nb-whyid" data-wd="y:${e(w.id)}">${e(w.id)}</b> ${EV.whyPill(w)}${w.revises ? ` <span class="sm">replaces ${EV.whyLink(w.revises, true)}</span>` : ''}${hs.length ? ` <span class="nb-whyto" title="the hypotheses that come from this guess">→ ${hs.map(h => EV.link(h.id)).join(', ')}</span>` : ''}</div>
        <div class="nb-whyb"><p><span class="nb-wk">It saw</span><span><span data-own="model">${e(w.result)}</span> <span class="sm">(${about(w)})</span></span></p>
          <p class="nb-whyq"><span class="nb-wk">Why?</span><span data-own="model">${e(w.guess)}</span></p>
          <p class="sm"><span class="nb-wk">Not visible</span><span data-own="model">${e(w.unseen)}</span></p><p class="sm"><span class="nb-wk">For the goal</span><span data-own="model">${e(w.matters)}</span></p>
          <p class="sm"><span class="nb-wk">${w.worth === 'verify' ? 'Worth verifying' : 'Set aside'}</span><span data-own="model">${e(w.reason)}</span></p></div></div>`; }).join('')}</div>`;
  },
  // ---- the links of the chain, on hover (2026-11-17, the operator: the relations between whys, hypotheses and claims, in a short box):
  // a guess of why: what it saw, what became of it, the hypotheses that come from it and the claims of the report that rest on those
  whyPop(id) {
    const M = EV.M, e = EV.e, w = (M.whyById || {})[id]; if (!w || !EV.seen(id)) return '';
    const line = (k, body, cls) => `<div class="hp-l${cls ? ' ' + cls : ''}" data-yp="${k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k">${k}</span><div class="hp-v">${body}</div></div>`, none = t => `<span class="mut">${t}</span>`, cut = (t, n) => (String(t || '').length > n ? String(t).slice(0, n - 1) + '…' : String(t || ''));
    const now = EV.whyNow(w), hs = M.hyps.filter(h => h.from_why === id && EV.seen(h.id)), state = h => (EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open');
    const cl = EV.repNow() ? M.claims.filter(q => (q.hyps || []).some(h => hs.some(x => x.id === h))) : [], ks = (M.rethinks || []).filter(k => k.for === id && EV.seen(k.id)), by = (M.whys || []).find(q => q.revises === id && EV.seen(q.id));
    const became = [...ks.map(k => `turn ${k.turn}: looked at again, now ${e(EV.WHY_NOW[k.now] || k.now)}`), by ? `turn ${by.turn}: replaced by the better guess ${e(by.id)}` : ''].filter(Boolean);
    return `<div class="hp" data-why-pop="${e(id)}"><p class="hp-h"><b class="hp-id">${EV_ICON.why}${e(id)}</b><span class="hp-badge">${e(EV.WHY_NOW[now.worth] + (now.worth === 'revised' ? ' by ' + now.by : ''))}</span><span class="hp-turn">guess of why · turn ${w.turn}</span></p>
      <p class="hp-q" data-own="model">${e(w.guess)}</p>
      ${line('It saw', `<span data-own="model">${e(w.result)}</span>`, 'hp-clamp')}${line('Not visible', `<span data-own="model">${e(w.unseen)}</span>`, 'hp-clamp')}
      ${became.length ? line('Became of it', became.join('<br>')) : ''}
      ${line('Hypotheses', hs.length ? hs.map(h => `<span class="hp-chip">${e(h.id)}</span> <span data-own="model">${e(cut(h.question || h.text, 76))}</span> <span class="sm">· ${e(state(h))}</span>`).join('<br>') : none(now.worth === 'verify' ? 'none comes from it yet' : 'none came from it'))}
      ${EV.repNow() ? line('Claims', cl.length ? cl.map(q => `<span class="hp-chip">claim ${q.n}</span> <span data-own="model">${e(cut(q.text, 70))}</span>`).join('<br>') : none('no claim of the final report rests on it')) : ''}
      <p class="sm hp-foot">The chain: a result, this guess of why, the hypotheses from it, their tests, the report’s claims. Click to open the guess.</p></div>`;
  },
  // a claim of the final report: the hypotheses it rests on (through the checks and verdicts it cites) and the guesses of why behind them
  claimPop(n) {
    const M = EV.M, e = EV.e, c = M.claims[Number(n) - 1]; if (!c || !EV.repNow()) return '';
    const line = (k, body, cls) => `<div class="hp-l${cls ? ' ' + cls : ''}" data-cp="${k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k">${k}</span><div class="hp-v">${body}</div></div>`, none = t => `<span class="mut">${t}</span>`, cut = (t, k) => (String(t || '').length > k ? String(t).slice(0, k - 1) + '…' : String(t || ''));
    const hs = (c.hyps || []).map(id => M.hypById[id]).filter(Boolean), ys = [...new Set(hs.map(h => h.from_why).filter(Boolean))].map(y => (M.whyById || {})[y]).filter(Boolean);
    const other = c.evidence.filter(id => !['check', 'verdict'].includes((M.byId[id] || {}).type)), role = { supports: 'supports the proposal', background: 'background', limits: 'a limit of the proposal' }[c.role];
    return `<div class="hp" data-claim-pop="${e(n)}"><p class="hp-h"><b class="hp-id">claim ${e(n)}</b>${role ? `<span class="hp-badge">${role}</span>` : ''}<span class="hp-turn">of the final report</span></p>
      <p class="hp-q" data-own="model">${e(c.text)}</p>
      ${line('Rests on', hs.length ? hs.map(h => `<span class="hp-chip">${e(h.id)}</span> <span data-own="model">${e(cut(h.question || h.text, 76))}</span> <span class="sm">· ${e(h.state)}</span>`).join('<br>') : none(c.evidence.length ? 'no tested hypothesis: only the records below' : 'nothing: it cites no record'))}
      ${other.length ? line('Also cites', other.map(id => `<span class="hp-chip">${e(id)}</span>`).join(' ') + ' <span class="sm">· tables of results, not a check or a verdict</span>') : ''}
      ${(M.whys || []).length ? line('Guesses behind', ys.length ? ys.map(w => `<span class="hp-chip">${e(w.id)}</span> <span data-own="model">${e(cut(w.guess, 84))}</span>`).join('<br>') : none('none: it rests on no hypothesis')) : ''}
      <p class="sm hp-foot">Click to see the records it cites.</p></div>`;
  },
  // The legend of this card: the marks the notebook itself uses, and no others (2026-11-17, the operator: the page's legend, with the flows' colours and
  // the operator, did not match the notebook). Who wrote a line; what a card's left edge says; the signs of a check and of a verdict; the marks of the
  // guesses of why (only in a session that has them); the signs of the records it names.
  nbLegend() {
    const M = EV.M, t = s => ` title="${EV.e(s)}"`, by = (who, name, says) => `<span class="lg" data-by="${who}"${t(says)}><i class="sw" data-icon="${who}" data-col="${name}"></i>${name}</span>`;
    const edge = (v, name, says) => `<span class="lg"${t(says)}><i class="eg" style="background:var(${v})"></i>${name}</span>`, sign = (k, name, says) => `<span class="lg"${t(says)}>${EV.gkey(k)}${name}</span>`, pill = w => `<span class="pill">${w}</span>`;
    return `<div class="ev-legend noprint" id="nb-legend">
      <span class="lg-grp"><b>who wrote a line</b>${by('model', 'AI', 'The small mark before a line: the AI wrote it (its hypothesis, plan, verdict)')}${by('harness', 'harness', 'The harness computed it: the check of a decision rule against the measurements')}${by('simulator', 'ns-3', 'Measured by ns-3 in a simulation')}</span>
      <span class="lg-grp"><b>a card’s left edge</b>${edge('--good', 'its test held', 'What the hypothesis expected was found')}${edge('--critical', 'its test failed', 'Expected and not found: a result, not a warning')}${edge('--border', 'not checked', 'No check yet, or a check that compared a simulation with itself')}</span>
      <span class="lg-grp"><b>a check</b>${sign('held', 'held', 'The harness checked the decision rule: it held')}${sign('failed', 'failed', 'The harness checked the decision rule: it failed')}</span>
      <span class="lg-grp"><b>a verdict</b>${sign('supported', 'supported', 'The AI’s judgement of its hypothesis')}${sign('refuted', 'refuted', 'The AI’s judgement of its hypothesis')}${sign('inconclusive', 'inconclusive', 'The AI’s judgement of its hypothesis')}</span>
      ${(M.whys || []).length ? `<span class="lg-grp"><b>guesses of why</b><span class="lg"${t('A guess of why a result came out so; a hypothesis comes from one')}>${EV_ICON.why}a guess</span><span class="lg"${t('The AI looked at an earlier guess again in the light of later results')}>${EV_ICON.rethink} looked at again</span><span class="lg"${t('What a guess is now')}>${['to verify', 'set aside', 'supported', 'refuted', 'replaced'].map(pill).join(' ')}</span></span>` : ''}
      <span class="lg-grp"><b>named records</b><span class="lg"${t('H: a hypothesis')}>${EV_ICON.hypothesis} hypothesis</span><span class="lg"${t('E: the measures of an experiment’s simulations')}>${EV_ICON.evidence} result table</span><span class="lg"${t('C: the harness’s check of one decision rule')}>${EV_ICON.check} check</span><span class="lg"${t('S: one simulation')}>${EV_ICON.simulation} simulation</span></span></div>`;
  },
  // ---- from one hypothesis to the next (2026-11-17, the operator: the AI reviews each step from one hypothesis to the next; that should be drawn).
  // One line for each hypothesis: the results it started from; the earlier guesses it looked at again in that turn (rethink) and what each became;
  // its guess of why; what the judge (a second model call) read of the step from the guess to the hypothesis; the hypothesis. A hypothesis the judge
  // refused has its line too. Folded until asked for; the browser remembers.
  transView() {
    const M = EV.M, e = EV.e, S = EV.s; if (!(M.whys || []).length) return '';
    const cut = (t, n) => (String(t || '').length > n ? String(t).slice(0, n - 1) + '…' : String(t || '')), st = id => M.recStep[id] ?? 0, folded = EV.store('ev-trans') === '0' && !S.full;
    const from = w => (w.about || []).map(a => (a === 'brief' ? '<span class="tv-rec">the brief</span>' : `<span class="tv-rec">${EV.link(a)}</span>`)).join(' ');
    const cell = (k, html, cls, attr) => `<div class="tv-c tv-${k}${cls ? ' ' + cls : ''}" data-col="${k}"${attr || ''}>${html}</div>`;
    // what the turn looked at again before it went on: each earlier guess with what it became and the reason (said once for the turn's lines)
    const again = n => { const ks = (M.rethinks || []).filter(k => k.turn === n && EV.seen(k.id)); return ks.map(k => `<div class="tv-again" data-again="${e(k.id)}" title="${e(`In the light of ${(k.in_light_of || []).join(', ')}: ${k.because}`)}">${EV.whyLink(k.for)} <span class="pill" data-now="${e(k.now)}">${e(EV.WHY_NOW[k.now] || k.now)}</span><span class="tv-why-because" data-own="model">${e(cut(k.because, 96))}</span></div>`).join(''); };
    const guess = w => `${EV.whyLink(w.id)}${w.revises ? ` <span class="sm">replaces ${EV.whyLink(w.revises)}</span>` : ''} <span data-own="model">${e(cut(w.guess, 110))}</span>`;
    const judge = j => (!j ? '<span class="mut" title="This session ran before the judge existed, or without it">no judge</span>' : j.follows === true ? `<span class="tv-j ok" title="${e('The judge (a second model call) read the guess and the hypothesis: ' + j.because + ' It can be wrong.')}">${EV.gkey('held')}follows</span>` : `<span class="tv-j mut" title="${e(j.because)}">not judged</span>`);
    // what the hypothesis's test showed: the harness's check and the AI's verdict (what the next turn then looks at again)
    const shown = h => { const ts = h.tests.map(q => M.testById[q]).filter(T => T && EV.seen(T.exp)); if (!ts.length) return `<span class="mut">${M.ended ? 'not tested' : 'not tested yet'}</span>`;
      const cs = ts.filter(T => T.check && EV.seen(T.check.id)).map(T => `<a data-act="open" data-t="test" data-id="${e(T.id)}" title="Open this test">${EV.checkRes(T.check)}</a>`).join(' '), v = h.verdict && EV.seen(h.verdict.id) ? h.verdict : null;
      return `${cs || '<span class="mut">its simulations are running</span>'}${v ? ` <span class="tv-v" title="${e(v.because || '')}">${EV.verdictRes(v.result)}</span>` : ''}`; };
    const rows = M.hyps.filter(h => h.from_why && M.whyById[h.from_why] && EV.seen(h.id)).map(h => { const w = M.whyById[h.from_why];
      return { k: st(h.id), turn: h.turn, html: `<div class="tv-row" data-trans="${e(h.id)}" data-step="${st(h.id)}">${cell('res', from(w))}${cell('why', guess(w))}${cell('judge', judge(h.judge))}${cell('hyp', `${EV.link(h.id)} <span data-own="model">${e(cut(h.question || h.text, 110))}</span>`)}${cell('out', shown(h))}</div>` }; });
    const no = M.recs.filter(r => r.type === 'judge' && r.body.follows === false && EV.seen(r.id)).map(r => { const w = (M.whys || []).find(q => q.guess === r.body.guess);
      return { k: st(r.id), turn: r.turn, html: `<div class="tv-row tv-no" data-trans-no="${e(r.id)}" data-step="${st(r.id)}">${cell('res', w ? from(w) : '')}${cell('why', w ? guess(w) : `<span data-own="model">${e(cut(r.body.guess, 110))}</span>`)}${cell('judge', `<span class="tv-j no" title="${e('The judge read twice and found no link: ' + r.body.because)}">${EV.gkey('failed')}does not follow</span>`)}${cell('hyp', `<span class="pill warnc">refused</span> <span data-own="model">${e(cut(r.body.hypothesis, 110))}</span>`)}${cell('out', '<span class="mut">not accepted: the AI was told why</span>')}</div>` }; });
    const all = rows.concat(no).sort((a, b) => a.k - b.k); if (!all.length) return '';
    // a turn that went on without the review: the guesses whose tests had come back before it, still marked "to verify", that it did not look at again
    // (sessions before the harness required the review; s042, turn 3)
    // a session that never looked again at a guess ran before that was asked for (the first chain session, s041): it is told once, not held against every turn
    const asked = (M.rethinks || []).length > 0 || (M.whys || []).some(w => w.revises);
    const skipped = n => (!asked ? [] : (M.whys || []).filter(w => w.turn < n && EV.seen(w.id))).filter(w => { const ks = (M.rethinks || []).filter(k => k.for === w.id && EV.seen(k.id)), rv = (M.whys || []).filter(q => q.revises === w.id && EV.seen(q.id));
      if (ks.some(k => k.turn === n) || rv.some(q => q.turn === n)) return false;
      const before = ks.filter(k => k.turn < n), worth = rv.some(q => q.turn < n) ? 'revised' : before.length ? before[before.length - 1].now : w.worth, settled = Math.max(w.turn, ...before.map(k => k.turn));
      return worth === 'verify' && M.hyps.some(h => h.from_why === w.id && h.tests.some(q => { const T = M.testById[q]; return T && T.check && EV.seen(T.check.id) && T.turn < n && T.turn >= settled; })); }).map(w => w.id);
    const turns = [...new Set(all.map(q => q.turn))], unlooked = (M.whys || []).filter(w => EV.seen(w.id) && EV.whyNow(w).worth === 'verify' && EV.whyNow(w).by == null && M.hyps.some(h => h.from_why === w.id && h.tests.some(q => { const T = M.testById[q]; return T && T.check && EV.seen(T.check.id); })));
    const head = `<div class="tv-row tv-head" aria-hidden="true">${cell('res', 'The results it had')}${cell('why', 'Its guess of why')}${cell('judge', 'The judge')}${cell('hyp', 'The hypothesis')}${cell('out', 'What its test showed')}</div>`;
    return `<div id="s-trans" class="noprint${folded ? ' tv-folded' : ''}"><h3 class="tv-h">From one hypothesis to the next <button class="cl noprint" data-act="transfold" aria-expanded="${folded ? 'false' : 'true'}">${folded ? 'unfold' : 'fold'}</button></h3>
      <p class="sm tv-says">Each line is one step: the results it started from, its guess of why, the judge's reading of whether the hypothesis follows from that guess, the hypothesis, and what its test showed. Before a turn goes on, it looks again at the guesses that were just tested: that stands at the head of the turn.${no.length ? ` ${no.length} hypothes${no.length === 1 ? 'is was' : 'es were'} refused by the judge.` : ''}${!asked ? ' <span id="tv-before">This session ran before the AI was asked to look again at its guesses after each test (17 November 2026).</span>' : unlooked.length ? ` <span class="warnc" id="tv-unlooked">Tested and not looked at again: ${unlooked.map(w => e(w.id)).join(', ')}.</span>` : ''}</p>
      ${folded ? '' : `<div class="tv" id="tv-grid">${head}${turns.map(n => { const a = again(n); return `<div class="tv-turn" data-turn="${n}" data-step="${Math.min(...all.filter(q => q.turn === n).map(q => q.k))}"><div class="tv-turnh"><b>Turn ${n}</b>${a ? `<span class="tv-againh">${EV_ICON.rethink} first it looked again at what was just tested</span>` : n === turns[0] && !skipped(n).length ? '<span class="tv-againh mut">the first guesses, from the baseline</span>' : ''}${skipped(n).length ? `<span class="tv-againh tv-skip warnc" data-skipped="${e(skipped(n).join(','))}" title="Their tests had come back and they were still marked “to verify”. Since 17 November 2026 the harness accepts no new hypothesis until such a guess is looked at again.">${EV.gkey('warn')}it went on without looking again at ${e(skipped(n).join(', '))}, whose tests had come back</span>` : !a && n !== turns[0] ? '<span class="tv-againh mut">no guess was waiting to be looked at again</span>' : ''}${a ? `<div class="tv-agains">${a}</div>` : ''}</div>${all.filter(q => q.turn === n).map(q => q.html).join('')}</div>`; }).join('')}</div>`}</div>`;
  },
  // a guess of why in the detail pane: the guess in full, what became of it (looked at again, replaced), and the hypotheses that come from it with how each ended
  whyCard(id) {
    const M = EV.M, e = EV.e, w = (M.whyById || {})[id]; if (!w || !EV.seen(id)) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const row = (k, body, own, step) => `<div class="td-l" data-td="${k.toLowerCase().replace(/[^a-z]+/g, '-')}"${step != null ? ` data-step="${step}"` : ''}><span class="td-k">${k}</span><div class="td-v"${own ? ' data-own="model"' : ''}>${body}</div></div>`;
    const ks = (M.rethinks || []).filter(k => k.for === id && EV.seen(k.id)), by = (M.whys || []).find(q => q.revises === id && EV.seen(q.id)), hs = M.hyps.filter(h => h.from_why === id && EV.seen(h.id)), now = EV.whyNow(w);
    const state = h => (EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open');
    return `<h2 class="td-head">${EV_ICON.why} Guess of why ${e(id)} ${EV.whyPill(w)} <small>stated in turn ${w.turn}</small></h2>
      <div class="td td-top" id="why-card" data-why="${e(id)}">${row('About', (w.about || []).map(a => (a === 'brief' ? 'the brief' : EV.link(a))).join(', ') + (w.revises ? ` <span class="sm">· replaces the earlier guess ${EV.whyLink(w.revises)}</span>` : ''))}
        ${row('It saw', e(w.result), 1)}${row('Why?', `<b>${e(w.guess)}</b>`, 1)}${row('Not visible', e(w.unseen), 1)}${row('For the goal', e(w.matters), 1)}
        ${row(w.worth === 'verify' ? 'Worth verifying' : 'Set aside', e(w.reason), 1)}
        ${row('What became of it', (ks.length || by ? '' : `<p>Not looked at again since it was stated: it stands as “${e(EV.WHY_NOW[now.worth])}”.</p>`)
          + ks.map(k => `<p data-again="${e(k.id)}">${EV_ICON.rethink} turn ${k.turn}: looked at again in the light of ${(k.in_light_of || []).map(EV.link).join(', ')}: now <span class="pill">${e(EV.WHY_NOW[k.now] || k.now)}</span> <span data-own="model">${e(k.because)}</span></p>`).join('')
          + (by ? `<p>turn ${by.turn}: replaced by the better guess ${EV.whyLink(by.id)}: <span data-own="model">${e(by.guess)}</span></p>` : ''))}
        ${row('Hypotheses from it', hs.length ? hs.map(h => `<p>${EV.link(h.id)} <span data-own="model">${e(h.question || h.text)}</span> <span class="sm">· ${e(state(h))}</span></p>`).join('') : '<p class="sm">No hypothesis came from this guess.</p>')}</div>`;
  },
});
EV.nbRefsOpen = EV.nbRefsOpen || {};  // the turns whose alike refusals are shown one by one: "<session>:<turn>" -> true
EV.nbFolded = EV.nbFolded || {};  // the turns of the notebook that are folded to their heading: "<session>:<turn>" -> true
EV.act = Object.assign(EV.act || {}, {
  // a turn's heading: fold the turn to that one line, or open it again; nothing else on the page is drawn again, so nothing above it moves
  // the view of the steps from one hypothesis to the next: folded or open (open as the page comes); the browser remembers
  transfold() { EV.store('ev-trans', EV.store('ev-trans') === '0' ? '1' : '0'); EV.draw(); },
  nbfold(id, t) { const key = `${EV.M.id}:${id}`, g = t.closest('.nb-group'); EV.nbFolded[key] = !EV.nbFolded[key]; if (g) g.classList.toggle('nb-folded', EV.nbFolded[key]); t.setAttribute('aria-expanded', EV.nbFolded[key] ? 'false' : 'true'); },
  nbrefs(id, t) { const key = `${EV.M.id}:${id}`, g = t.closest('.nb-group'); EV.nbRefsOpen[key] = !EV.nbRefsOpen[key]; if (g) g.classList.toggle('nb-refs-open', EV.nbRefsOpen[key]); const w = t.querySelector('.nb-refs-t'); if (w) w.textContent = EV.nbRefsOpen[key] ? 'hide them' : 'show each'; },
  nbfoldall(id) { EV.M.turns.filter(t => t.n > 0).forEach(t => { EV.nbFolded[`${EV.M.id}:${t.n}`] = id === '1'; }); document.querySelectorAll('#s-notebook .nb-group').forEach(g => { if (g.dataset.group !== '0') { g.classList.toggle('nb-folded', id === '1'); const h = g.querySelector('.nb-turn'); if (h) h.setAttribute('aria-expanded', id === '1' ? 'false' : 'true'); } }); },
  nbmore(id) { const q = EV.s.nbmore = EV.s.nbmore || {}; q[id] = !q[id]; EV.draw(); },
});
