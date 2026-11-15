// "What it needed to find out": first the board (EV.viewMap in evidence_views.js): one box per hypothesis in the column
// of its turn, and an arrow, coloured by the result that led onward, to each hypothesis that follows from it. Under
// it, folded ("The same, test by test"; open in Full, and the browser remembers it), the table: one row per test, in the order the tests were stated. Four columns, each a recorded
// text or a measured number: the question (the hypothesis's question; a session that recorded none: the hypothesis
// text, cut to two lines), the outcome (the model's verdict; "void" where the check compared a simulation with itself),
// what was measured (the check's numbers in words: "483 Mbps, not over 700 Mbps"), and what it led to (a mark for each
// later hypothesis that follows from the test, which goes to that hypothesis's row). A failed check is a result: it has
// no warning colour. A row opens its notebook card and brings it into view (one of the page's stated exceptions to
// "a click never moves the page"). At most nine rows are shown, then "n more". The replay greys the rows recorded after
// its step; a check or a verdict recorded later is absent from its row. In a running session a row whose simulations are
// running says so, and while a reply is written that may ask a new question the table ends with one empty row.
// ======================================================================================================
Object.assign(EV, {
  // The card that opens when a hypothesis's box on the board is pointed at (through the box of evidence_words.js, key
  // "h:<id>"). Made for reading at a glance: the name and how it ended; the question, larger; then labelled lines, always
  // in this order, each a recorded text or a measured number: why it asked (the hypothesis's `why`; "not recorded" for a
  // session from before the field), what it follows from (each result named, with its sign), what was expected (the
  // decision rule of its last test, for reading), the result (the check's numbers in words, held or failed), the
  // conclusion (the verdict and the first sentence of its reason), what it led to. Only what the replay's step has reached.
  hypPop(id) {
    const M = EV.M, e = EV.e, seen = EV.seen, h = M.hypById[id]; if (!h || !seen(h.id)) return '';
    const st = EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open', ts = h.tests.map(q => M.testById[q]).filter(T => seen(T.exp)), T = ts[ts.length - 1] || null;
    const c = T && T.check && seen(T.check.id) ? T.check : null, v = h.verdict && seen(h.verdict.id) ? h.verdict : null;
    const word = ['supported', 'refuted', 'inconclusive'].includes(st) ? EV.verdictRes(st) : e(st === 'open' ? (M.ended ? 'not judged' : 'not judged yet') : st);
    const from = [...new Set((h.follows || []).map(EV.fromLine).filter(Boolean))];
    const led = (M.mapEdges || EV.mapEdges()).filter(x => x.from === id && x.kind !== 'weak' && seen(x.to)).map(x => e(x.to)), [first] = v ? EV.nbFirst(v.because) : [''];
    const line = (k, body, own) => `<div class="hp-l" data-hp="${k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k">${k}</span><div class="hp-v"${own ? ` data-own="${own}"` : ''}>${body}</div></div>`, none = t => `<span class="mut">${t}</span>`;
    return `<div class="hp" data-hyp="${e(h.id)}"><p class="hp-h"><b>${e(h.id)}</b> · ${word} <span class="sm">· stated in turn ${h.turn}</span></p>
      <p class="hp-q" data-own="model">${e(h.question || h.text)}</p>
      ${line('Why it asked', h.why ? e(h.why) : none('not recorded: sessions before 14 November 2026 were not asked for it'), h.why ? 'model' : '')}
      ${line('Follows from', from.length ? from.join('<br>') : h.follows ? none('nothing earlier: a first question') : none('not recorded'))}
      ${line('Expected', T && T.rule ? EV.ruleRead(T, 4) : h.prediction ? e(h.prediction) : none('no decision rule yet'), T && T.rule ? '' : h.prediction ? 'model' : '')}
      ${line('Result', c ? `${EV.checkRes(c)}${c.void ? '' : ' · ' + (EV.measuredWords(T) || '')}` : none(T ? (M.ended ? 'not checked' : 'not yet') : M.ended ? 'not put to a test' : 'not tested yet'))}
      ${line('Conclusion', v ? `${EV.verdictRes(v.result)}${first ? ' · ' + e(first) : ''}` : none(M.ended ? 'no verdict was given' : 'not judged yet'), v ? 'model' : '')}
      ${line('Led to', led.length ? '→ ' + led.join(', ') : none(M.ended ? 'no later hypothesis names its result' : 'nothing yet'))}
      <p class="sm hp-foot">${ts.length > 1 ? `Put to ${ts.length} decision rules: the last one is shown. ` : ''}Click the box to open its test beside the page.</p></div>`;
  },
  // one result a hypothesis follows from, in words: a check with what was measured, a verdict, an experiment's result table, the brief
  fromLine(f) {
    const M = EV.M, e = EV.e, r = M.byId[f]; if (f === 'brief') return 'the brief'; if (!r) return null;
    if (r.type === 'verdict') return `${EV.gkey(EV.vk(r.body.result))}${e(r.body.for)} was ${r.body.result === 'inconclusive' ? 'left inconclusive' : e(r.body.result)}`;
    if (r.type === 'check') { const k = M.voidIds.has(f) ? 'void' : r.body.result, T = M.tests.find(q => q.check && q.check.id === f), m = T && k !== 'void' ? EV.measuredWords(T) : null; return `${EV.gkey(EV.ck(k))}the check of ${e(r.body.for)} ${k === 'void' ? 'was void' : e(k)}${m ? `: ${m}` : ''}`; }
    const x = r.type === 'evidence' ? r.body.experiment || r.parent : r.type === 'simulation' ? r.parent : null; return x === 'X0' ? 'the baseline' : x ? `the results of experiment ${e(x)}` : null;
  },
  // the card of an arrow of the board (key "e:<from>><to>"): the result of the earlier hypothesis that the later one names, with what was measured,
  // how it was judged and what the AI said it would do next. A dotted arrow: only that experiment's result table is named.
  edgePop(key) {
    const M = EV.M, e = EV.e, seen = EV.seen, [from, to] = key.split('>'), x = (M.mapEdges || EV.mapEdges()).find(q => q.from === from && q.to === to); if (!x || !seen(to)) return '';
    const lines = [...new Set(x.ids.filter(f => f === 'brief' || seen(f)).map(EV.fromLine).filter(Boolean))], h = M.hypById[from], v = h && h.verdict && seen(h.verdict.id) && x.ids.some(f => f === h.verdict.id || (M.byId[f] || {}).type === 'check') ? h.verdict : null;
    return `<div class="hp" data-edge="${e(key)}"><p class="hp-h"><b>${from === 'brief' ? 'the brief' : e(from)} → ${e(to)}</b> <span class="sm">· what ${e(to)} follows from</span></p>
      <div class="hp-l" data-hp="result"><span class="hp-k">${x.kind === 'weak' ? 'It names' : 'The result'}</span><div class="hp-v">${lines.join('<br>') || '<span class="mut">not recorded</span>'}${x.kind === 'weak' ? '<br><span class="mut">only the result table of that experiment, not a check or a verdict</span>' : ''}</div></div>
      ${v ? `<div class="hp-l" data-hp="judged"><span class="hp-k">Judged</span><div class="hp-v" data-own="model">${EV.verdictRes(v.result)} · ${e(EV.nbFirst(v.because)[0])}</div></div><div class="hp-l" data-hp="next"><span class="hp-k">Its next step</span><div class="hp-v" data-own="model">${e(v.next || 'not recorded')}</div></div>` : ''}
      <p class="sm hp-foot">${from === 'brief' ? 'Click to open the brief beside the page.' : `Click to open the test of ${e(from)} beside the page.`}</p></div>`;
  },
  // the card of the answer (the last box of the board; key "a:report"): what it proposes, what it expects, and its reasons: the claims that support the
  // recommendation and those that say how the system behaves ("because"), those that say when it would change, with "holds when" and "breaks when" ("but")
  answerPop() {
    const M = EV.M, e = EV.e, rep = EV.repNow(); if (!rep) return ''; const R = EV.recParts(), X = EV.expRows(rep), kn = (M.brief && M.brief.knobs) || {}, roles = M.claims.length > 0 && M.claims.every(q => q.role);
    const adj = !R ? 'not recorded' : R.text ? e(R.text) : R.differ.map(([k, v]) => `${e(EV.LABEL[k] || k)} ${k in kn ? e(EV.adjVal(k, kn[k].default)) + ' → ' : ''}<b>${e(EV.adjVal(k, v))}</b>`).join(', ') || 'no setting changed';
    const claim = q => `<div class="ap-c"><span data-own="model">${e(q.text)}</span> <span class="sm">${EV.claimMarks(q, EV.seen)}</span></div>`, of = r => M.claims.filter(q => q.role === r), line = (k, body) => (body ? `<div class="hp-l" data-hp="${k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k">${k}</span><div class="hp-v ap-v">${body}</div></div>` : '');
    const txt = v => (Array.isArray(v) ? v.map(q => e(q)).join(' · ') : e(v ?? ''));
    return `<div class="hp ap"><p class="hp-h"><b>Its answer</b> <span class="sm">· the final report · ${M.claims.length} claim${M.claims.length === 1 ? '' : 's'}</span></p>
      ${line('Proposes', adj)}${line('Expects', X && X.top.length ? X.top.map(([k, v]) => `${e(TH_DATA.PLAIN[k] || k)} ${EV.v4(k, v)}`).join(' · ') : '')}
      ${roles ? line('Because', [...of('supports'), ...of('background')].map(claim).join('')) + line('But', of('limits').map(claim).join('') + (rep.breaks_when ? `<div class="ap-c sm">breaks when: <span data-own="model">${txt(rep.breaks_when)}</span></div>` : '')) : line('Its claims', M.claims.map(claim).join(''))}
      <p class="sm hp-foot">Click the box to open the final report beside the page.</p></div>`;
  },
  FIND_ROWS: 9,
  // the check's numbers in words. One comparison: "483 Mbps, not over 700 Mbps"; several: joined by "and" / "or"
  measuredWords(T) {
    const c = T.check; if (!c) return null; if (c.void) return '<span class="mut">compared a simulation with itself</span>';
    const h = EV.readHtml(T.rule, { sims: Object.fromEntries(T.sims.map(s => [s.label, s])), plain: true, words: true, max: 4 });
    return h ? `<span class="rr" data-rr="measured" title="${EV.e(c.numbers == null ? '' : c.numbers + ' : ' + (c.recorded || c.result))}">${h}</span>` : `<code>${EV.e(c.numbers ?? '')}</code>`;
  },
  findCard() {
    const M = EV.M, S = EV.s, e = EV.e, st = id => M.recStep[id] ?? 0, end = M.steps.length - 1, at = (k, html) => `<span data-step="${k}">${html}</span>`;
    const now = EV.liveNow(), wait = T => !!now && now.phase === 'sims' && T.exp === now.exp;  // a running session: the tests whose simulations the simulator is working on
    const first = {}; M.tests.forEach(T => { if (!(T.hyp in first)) first[T.hyp] = T.id; });  // the row a hypothesis is first tested in
    const all = M.tests, open = S.full || S.findAll || all.length <= EV.FIND_ROWS, shown = open ? all : all.slice(0, EV.FIND_ROWS), sel = S.sel || {};
    const row = T => { const h = M.hypById[T.hyp], c = T.check, v = T.verdict, fol = T._fol || (T._fol = EV.followers(T)), fk = Math.max(v ? st(v.id) : 0, ...fol.ids.map(id => st(id)));
      const q = h && h.question ? e(h.question) : h ? `<span class="lc2">${e(h.text)}</span>` : EV.nr;
      const out = c && c.void ? at(st(c.id), `<span class="rs" data-void="1" title="${e(EV.VOID)}">${EV.gkey('void')}void</span>${v ? ` <span class="sm" data-step="${st(v.id)}">judged ${e(v.result)}</span>` : ''}`)
        : v ? at(st(v.id), EV.verdictRes(v.result)) : at(end, `<span class="mut">${M.ended ? 'none' : 'none yet'}</span>`);
      const led = fol.ids.filter(id => first[id]).map(id => `<a data-act="findrow" data-id="${e(first[id])}" title="${e(`${id} follows from this test${fol.via ? ' (through the table ' + fol.via + ' of its experiment)' : ''}: go to its row`)}">→ ${e(id)}</a>`).join(' ');
      return `<tr class="pick fr${sel.t === 'test' && sel.id === T.id ? ' sel' : ''}" id="fr-${e(T.id)}" data-act="find" data-id="${e(T.id)}" data-step="${st(T.exp)}"${EV.freshAttr(T.exp)}><td class="fq"><span class="fh" data-wd="h:${e(T.hyp)}">${e(T.hyp)}</span><span data-own="model">${q}</span>${h && h.why ? `<div class="sm fwhy lc2" title="${e(h.why)}"><span class="mut">why:</span> <span data-own="model">${e(h.why)}</span></div>` : ''}</td>
        <td class="fo">${out}</td><td class="fm">${c ? at(st(c.id), EV.measuredWords(T)) : at(end, wait(T) ? `<span class="nowp" data-now="sims">${EV.nowDot()}its simulations are running</span>` : `<span class="mut">${T.rule ? (M.ended ? 'not checked' : 'not yet') : 'no decision rule'}</span>`)}</td>
        <td class="fl">${led ? at(fk, `${c && c.result === 'failed' ? '<span class="fturn" title="Its check failed, and a later hypothesis follows from it">changed course</span> ' : ''}${led}`) : ''}</td></tr>`; };
    const recorded = all.filter(T => EV.seen(T.exp)), more = recorded.length - shown.filter(T => EV.seen(T.exp)).length;  // "n more" counts only what is recorded by the replay's step
    // while the AI writes a reply that may ask a new question: one empty row, which says so
    const next = now && now.phase === 'reply' && !now.mode ? `<tr class="fr-slot" id="fr-next" data-slot="question"><td class="fq">${EV.nowDot()}<span class="mut">The next question, if this reply asks one</span></td><td class="fo"><span class="mut">empty</span></td><td class="fm"><span class="mut">empty</span></td><td class="fl"></td></tr>` : '';
    // the board (evidence_views.js): the hypotheses by turn, and which result led to which; under it, folded, the same test by test
    const listOpen = S.full || EV.store('ev-find') === '1', stage = now ? EV.liveStage(now, !M.hyps.length) : '', board = M.hyps.length ? `<div id="s-map">${EV.viewMap()}${EV.repNow() && M.claims.some(c => c.hyps.length) ? `<p class="sm noprint map-path"><button data-act="path" class="${S.path ? 'on' : ''}">${S.path ? 'hide' : 'show'} the path to the answer</button> the hypotheses the final report's claims rest on, and what they follow from</p>` : ''}</div>` : '';
    return `<div class="ev-card" id="s-find"><h2>What it needed to find out</h2><p class="sec-q">Which questions did it set itself, and what did it learn?</p>${stage}${board}${now && !M.hyps.length ? '<p class="sm" id="find-none" style="text-align:center;max-width:none">No question yet. Its questions will stand here, each in the column of its turn, with what each result led to.</p>' : ''}
      ${now && !M.hyps.length ? '' : all.length || next ? `<details id="find-list"${listOpen ? ' open' : ''}><summary><b>The same, test by test</b> <span class="sm">${recorded.length} ${recorded.length === 1 ? 'test' : 'tests'}: the question, the outcome, what was measured, what it led to</span></summary><table class="ft"><thead><tr><th>The question</th><th>Outcome</th><th>Measured</th><th>Led to</th></tr></thead><tbody>${shown.map(row).join('')}${next}</tbody></table>
        ${more > 0 ? `<p class="sm noprint" id="find-more"><button data-act="findall">${more} more</button> ${recorded.length} tests in all</p>` : S.findAll && !S.full && all.length > EV.FIND_ROWS ? `<p class="sm noprint"><button data-act="findall">show the first ${EV.FIND_ROWS}</button></p>` : ''}
        <p class="sm">One row per ${EV.term('Test', 'test')}: one hypothesis put to one decision rule. A row opens its card in the notebook below. “Measured” is the ${EV.term('Check', 'check')}'s numbers; a check that failed is a result, not a fault.</p></details>`
        : `<p class="sm">${M.ended ? 'This session put no hypothesis to a test.' : 'No test yet.'}</p>`}</div>`;
  },
});
EV.act = Object.assign(EV.act || {}, {
  findall() { EV.s.findAll = !EV.s.findAll; EV.draw(); },
  // a row: its test opens in the detail pane, and its notebook card comes into view
  find(id) { EV.s.sel = { t: 'test', id }; EV.draw(); const el = [...document.querySelectorAll('#s-notebook .nb-card')].find(q => q.dataset.id === id); if (el) el.scrollIntoView({ block: 'center' }); },
  // a "led to" mark: to the row of the hypothesis that follows (every row is shown if it is past the ninth)
  findrow(id) { const S = EV.s; if (!document.getElementById('fr-' + id)) { S.findAll = true; EV.draw(); } const el = document.getElementById('fr-' + id); if (!el) return;
    el.scrollIntoView({ block: 'nearest' }); el.classList.add('flash'); setTimeout(() => el.classList.remove('flash'), 1600); },
});
document.getElementById('ev').addEventListener('toggle', ev => { if (ev.target.id === 'find-list' && !EV.s.full) EV.store('ev-find', ev.target.open ? '1' : '0'); }, true);
