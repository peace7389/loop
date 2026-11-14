// "What it needed to find out": one row per test, in the order the tests were stated. Four columns, each a recorded
// text or a measured number: the question (the hypothesis's question; a session that recorded none: the hypothesis
// text, cut to two lines), the outcome (the model's verdict; "void" where the check compared a simulation with itself),
// what was measured (the check's numbers in words: "483 Mbps, not over 700 Mbps"), and what it led to (a mark for each
// later hypothesis that follows from the test, which goes to that hypothesis's row). A failed check is a result: it has
// no warning colour. A row opens its notebook card and brings it into view (one of the page's stated exceptions to
// "a click never moves the page"). At most nine rows are shown, then "n more". The replay greys the rows recorded after
// its step; a check or a verdict recorded later is absent from its row.
// ======================================================================================================
Object.assign(EV, {
  FIND_ROWS: 9,
  // the check's numbers in words. One comparison: "483 Mbps, not over 700 Mbps"; several: joined by "and" / "or"
  measuredWords(T) {
    const c = T.check; if (!c) return null; if (c.void) return '<span class="mut">compared a simulation with itself</span>';
    const h = EV.readHtml(T.rule, { sims: Object.fromEntries(T.sims.map(s => [s.label, s])), plain: true, words: true, max: 4 });
    return h ? `<span class="rr" data-rr="measured" title="${EV.e(c.numbers == null ? '' : c.numbers + ' : ' + (c.recorded || c.result))}">${h}</span>` : `<code>${EV.e(c.numbers ?? '')}</code>`;
  },
  findCard() {
    const M = EV.M, S = EV.s, e = EV.e, st = id => M.recStep[id] ?? 0, end = M.steps.length - 1, at = (k, html) => `<span data-step="${k}">${html}</span>`;
    const first = {}; M.tests.forEach(T => { if (!(T.hyp in first)) first[T.hyp] = T.id; });  // the row a hypothesis is first tested in
    const all = M.tests, open = S.full || S.findAll || all.length <= EV.FIND_ROWS, shown = open ? all : all.slice(0, EV.FIND_ROWS), sel = S.sel || {};
    const row = T => { const h = M.hypById[T.hyp], c = T.check, v = T.verdict, fol = T._fol || (T._fol = EV.followers(T)), fk = Math.max(v ? st(v.id) : 0, ...fol.ids.map(id => st(id)));
      const q = h && h.question ? e(h.question) : h ? `<span class="lc2">${e(h.text)}</span>` : EV.nr;
      const out = c && c.void ? at(st(c.id), `<span class="rs" data-void="1" title="${e(EV.VOID)}">${EV.gkey('void')}void</span>${v ? ` <span class="sm" data-step="${st(v.id)}">judged ${e(v.result)}</span>` : ''}`)
        : v ? at(st(v.id), EV.verdictRes(v.result)) : at(end, `<span class="mut">${M.ended ? 'none' : 'none yet'}</span>`);
      const led = fol.ids.filter(id => first[id]).map(id => `<a data-act="findrow" data-id="${e(first[id])}" title="${e(`${id} follows from this test${fol.via ? ' (through the table ' + fol.via + ' of its experiment)' : ''}: go to its row`)}">→ ${e(id)}</a>`).join(' ');
      return `<tr class="pick fr${sel.t === 'test' && sel.id === T.id ? ' sel' : ''}" id="fr-${e(T.id)}" data-act="find" data-id="${e(T.id)}" data-step="${st(T.exp)}"><td class="fq"><span class="fh">${e(T.hyp)}</span><span data-own="model">${q}</span></td>
        <td class="fo">${out}</td><td class="fm">${c ? at(st(c.id), EV.measuredWords(T)) : at(end, `<span class="mut">${T.rule ? (M.ended ? 'not checked' : 'not yet') : 'no decision rule'}</span>`)}</td>
        <td class="fl">${led ? at(fk, `${c && c.result === 'failed' ? '<span class="fturn" title="Its check failed, and a later hypothesis follows from it">changed course</span> ' : ''}${led}`) : ''}</td></tr>`; };
    const recorded = all.filter(T => EV.seen(T.exp)), more = recorded.length - shown.filter(T => EV.seen(T.exp)).length;  // "n more" counts only what is recorded by the replay's step
    return `<div class="ev-card" id="s-find"><h2>What it needed to find out</h2><p class="sec-q">Which questions did it set itself, and what did it learn?</p>
      ${all.length ? `<table class="ft"><thead><tr><th>The question</th><th>Outcome</th><th>Measured</th><th>Led to</th></tr></thead><tbody>${shown.map(row).join('')}</tbody></table>
        ${more > 0 ? `<p class="sm noprint" id="find-more"><button data-act="findall">${more} more</button> ${recorded.length} tests in all</p>` : S.findAll && !S.full && all.length > EV.FIND_ROWS ? `<p class="sm noprint"><button data-act="findall">show the first ${EV.FIND_ROWS}</button></p>` : ''}
        <p class="sm">One row per ${EV.term('Test', 'test')}: one hypothesis put to one decision rule. A row opens its card in the notebook below. “Measured” is the ${EV.term('Check', 'check')}'s numbers; a check that failed is a result, not a fault.</p>`
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
