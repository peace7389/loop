// Home: all sessions. A title line with the one action that belongs here (new session), the results so far as a table
// with one row per brief, and the table of every session: sortable, filterable, a running session marked and listed
// first; a row opens its session and is one line high (a text too long for its column ends in "…" and is given in full
// on hover; the checks in order are followed by their counts). Nothing the top bar already offers (the list of sessions, Compare sessions) is repeated as a button here.
// Everything comes from control.py's session list (the sessions' own files and, for the score and the review, checks/).
// ======================================================================================================
Object.assign(EV, {
  ended: x => (x.running ? 'running now' : x.how || 'not recorded'),
  // the scheduling policy as the page may show it: a policy the harness chose stays hidden until the session is scored
  policyText: x => (x && x.policy_hidden ? '<span class="mut">chosen by the harness: shown once the session is scored</span>' : x && x.policy ? EV.e(x.policy) : EV.nr),
  gapText: x => (!x.score || typeof x.score.gap !== 'number' ? null : (/_bps$/.test(x.score.target) ? (x.score.gap / 1e6).toFixed(3) + ' Mbps' : String(+x.score.gap.toPrecision(4))) + ` (${(100 * x.score.part).toFixed(2)}%)`),
  // "N sessions · R with a final report · C meet the brief's conditions · largest gap to the best G%", from the list
  results(brief) {
    const rows = EV.st.sessions.filter(x => (x.brief || '') === brief), scored = rows.filter(x => x.score), meet = scored.filter(x => x.score.holds).length, parts = scored.map(x => x.score.part).filter(v => typeof v === 'number');
    const bits = [`${rows.length} session${rows.length === 1 ? '' : 's'}`, `${rows.filter(x => x.has_report).length} with a final report`];
    if (scored.length) bits.push(`${meet} meet the brief's conditions`, `largest gap to the best ${(100 * Math.max(...parts)).toFixed(2)}%`); else bits.push('none scored yet');
    if (scored.length && scored.length < rows.length) bits.push(`${rows.length - scored.length} not scored`);
    if (rows.some(x => x.running)) bits.push(`${rows.filter(x => x.running).length} running now`);
    return bits.join(' · ');
  },
  // the same as a row of Home's table: sessions, with a final report, meet the brief's conditions, largest gap to the best, not scored
  resultRow(brief) {
    const rows = EV.st.sessions.filter(x => (x.brief || '') === brief), scored = rows.filter(x => x.score), parts = scored.map(x => x.score.part).filter(v => typeof v === 'number'), run = rows.filter(x => x.running).length, none = '<span class="mut">not scored</span>';
    return `<tr data-brief="${EV.e(brief)}"><td><b>${EV.e(brief || 'before briefs')}</b></td><td class="num">${rows.length}${run ? ` <span class="sm">· ${run} running now</span>` : ''}</td><td class="num">${rows.filter(x => x.has_report).length}</td>
      <td class="num">${scored.length ? scored.filter(x => x.score.holds).length : none}</td><td class="num">${parts.length ? (100 * Math.max(...parts)).toFixed(2) + '%' : none}</td><td class="num">${rows.length - scored.length}</td></tr>`;
  },
  // a text that must stay on one line: cut with "…" by the style when its column is too narrow, and given in full on hover
  one: (text, cls) => `<td class="one ${cls || ''}" title="${EV.e(text)}">${EV.e(text)}</td>`,
  seqCell: x => (x.seq === undefined ? EV.nr : EV.seqHtml(x.seq) + (x.held + x.failed ? ` <span class="sq-n">${EV.tally(x.held, x.failed)}</span>` : '')),
  reviewCell(x) {  // the reviewer's progress on a session, and the sign-off
    const r = x.review || { ticked: [] }, M = EV.modelOf(x), [a, n] = M ? EV.checked(M, r.ticked) : [r.ticked.length, null];  // the total comes from the session's own records, read in the background
    return (r.signed ? `<span class="ok">reviewed by ${EV.e(r.signed.name || 'not recorded')} on ${EV.e(String(r.signed.at || '').slice(0, 10))}</span> · ` : '') + (a || r.signed ? `checked ${a}${n == null ? '' : ' of ' + n}` : n ? `<span class="mut">${n} to check</span>` : '');  // until the first tick: how many there are to check
  },
  HOME: [['id', 'session'], ['brief', 'brief'], ['started', 'started'], ['how', 'how it ended'], ['simulations', 'simulations used', 'num tight'], ['seq', 'checks, in order', '', 'The checks of the session in the order they were made, a small gap between turns; then how many held and how many failed.'],
    ['returned', 'returned', 'num tight', 'Simulations returned from an earlier one: simulations with the same settings and seed as an earlier one of the session: the earlier result was returned and nothing was run. Of all the simulations of the session.'],
    ['unnamed', 'not named by a rule', 'num tight', 'Simulations that no decision rule of their experiment names, of the simulations of the experiments that test hypotheses.'],
    ['void', 'void checks', 'num tight w-void', 'Checks whose decision rule compared a simulation with itself: it named two or more labels, and at least two of them were the same simulation. Of all the checks of the session. They count neither as held nor as failed.'], ['review', 'review progress', 'tight']],
  HOME_OP: [['policy', 'scheduling policy'], ['gap', 'gap to the best', 'num']],
  homeList() {  // the rows after the filter, a running session first, then by the chosen column
    const h = EV.s.home, f = h.filter.trim().toLowerCase(), key = { how: x => EV.ended(x), review: x => (x.review ? x.review.ticked.length + (x.review.signed ? 1000 : 0) : 0), seq: x => (x.seq == null ? null : x.seq.replace(/ /g, '').length), returned: x => (x.returned ? x.returned[0] : null), unnamed: x => (x.unnamed ? x.unnamed[0] : null), void: x => (x.void ? x.void[0] : null), gap: x => (x.score ? x.score.gap : null), brief: x => x.brief || '' }[h.sort] || (x => x[h.sort]);
    const text = x => [x.id, x.brief || 'before briefs', x.started, EV.ended(x), EV.s.op ? x.policy : '', x.review && x.review.signed ? x.review.signed.name : ''].join(' ').toLowerCase();
    const cmp = (a, b) => { const p = key(a), q = key(b); return p == null ? (q == null ? 0 : 1) : q == null ? -1 : (typeof p === 'number' && typeof q === 'number' ? p - q : String(p).localeCompare(String(q))) * h.dir; };
    return EV.st.sessions.filter(x => !f || f.split(/\s+/).every(w => text(x).includes(w))).sort((a, b) => (b.running ? 1 : 0) - (a.running ? 1 : 0) || cmp(a, b) || a.id.localeCompare(b.id));
  },
  homeRows() {
    const e = EV.e, op = EV.s.op, rows = EV.homeList(), body = rows.map(x => `<tr class="pick${x.running ? ' run' : ''}" data-act="pick" data-id="${e(x.id)}"><td><b>${e(x.id)}</b>${x.running ? ' <span class="pill live">running</span>' : ''}</td>${EV.one(x.brief || 'before briefs', 'w-brief')}
      <td class="nb">${e(String(x.started || '').replace('T', ' ').slice(0, 16)) || EV.nr}</td>${x.running || x.how ? EV.one(x.running ? 'running now' : x.how, 'w-how') : `<td>${EV.nr}</td>`}<td class="num nb">${x.simulations ?? 0}${x.allowed ? ' / ' + x.allowed : ''}</td>
      <td class="sqc" data-col="seq">${EV.seqCell(x)}</td>${['returned', 'unnamed'].map(k => `<td class="num" data-col="${k}">${x[k] ? `<b>${x[k][0]}</b> of ${x[k][1]}` : EV.nr}</td>`).join('')}<td class="num" data-col="void"${x.void ? ` data-of="${x.void[1]}" title="${x.void[0]} of the ${x.void[1]} checks of this session are void: their decision rule compared a simulation with itself"` : ''}>${x.void ? (x.void[0] ? `<b>${x.void[0]}</b>` : '<span class="mut">0</span>') : '<span class="mut" title="not recorded: this session has no checks by the harness">–</span>'}</td><td class="nb" data-col="review">${EV.reviewCell(x)}</td>
      ${op ? `<td class="nb" data-col="policy">${x.policy_hidden ? '<span class="mut">hidden until the session is scored</span>' : e(x.policy || '') || EV.nr}</td><td class="num nb">${EV.gapText(x) || '<span class="mut">not scored</span>'}</td>` : ''}</tr>`).join('');
    const el = document.getElementById('home-rows'), n = document.getElementById('home-n');
    if (el) { el.innerHTML = body; if (n) n.textContent = `${rows.length} of ${EV.st.sessions.length}`; }
    return body;
  },
  homeView() {
    const e = EV.e, S = EV.s, st = EV.st, h = S.home, all = st.sessions, briefs = [...new Set(all.map(x => x.brief || ''))];
    const th = ([k, t, c, tip]) => `<th${c ? ` class="${c}"` : ''}><a data-act="sort" data-id="${k}" title="${tip ? e(tip) + ' ' : ''}Sort by this column">${t}${h.sort === k ? (h.dir > 0 ? ' ↑' : ' ↓') : ''}</a></th>`;
    const running = all.filter(x => x.running).length;
    // one title line with the page's one action, beside the title where the eye starts (not at the far right). Opening a session (a row below, or the top bar's list) and comparing
    // (the top bar) each have one place, so they are not repeated here
    return `<div class="ev-title"><h1>All sessions</h1>${EV.newPanel ? `<button class="big primary" data-act="new" title="Write or choose an assignment and start the AI on it">${S.newOpen ? 'Close' : 'New session…'}</button>` : ''}
        <span class="sm">${all.length} session${all.length === 1 ? '' : 's'}${running ? ` · ${running} running now` : ''} · each is one complete attempt by the AI at one ${EV.term('Brief', 'brief')}</span></div>
      ${S.newOpen && EV.newPanel ? EV.newPanel() : ''}
      <div class="ev-card"><h2>Results so far <small>one row per ${EV.term('Brief', 'brief')}, counted from the sessions and, where they exist, their scores</small></h2>
        ${briefs.length ? `<table id="home-results" style="width:auto"><thead><tr><th>${EV.term('Brief', 'brief')}</th><th class="num">sessions</th><th class="num">with a final report</th><th class="num">meet the brief's conditions</th><th class="num">largest gap to the best</th><th class="num">not scored</th></tr></thead>
          <tbody>${briefs.map(b => EV.resultRow(b)).join('')}</tbody></table>` : '<p class="sm">No session yet.</p>'}</div>
      <div class="ev-card"><h2>Sessions <small><span id="home-n">${all.length} of ${all.length}</span> shown</small></h2>
        <p><input type="text" data-in="filter" placeholder="filter: any words of the id, brief, start, ending…" value="${e(h.filter)}" style="width:min(420px,100%)"></p>
        <div class="ev-scroll"><table><thead><tr>${EV.HOME.concat(S.op ? EV.HOME_OP : []).map(th).join('')}</tr></thead><tbody id="home-rows">${EV.homeRows()}</tbody></table></div></div>`;
  },
});
