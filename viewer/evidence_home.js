// Home: all sessions. A title line with the one action that belongs here (new session), the results so far per brief,
// and the table of every session: sortable, filterable, a running session marked and listed first; a row opens its
// session. Nothing the top bar already offers (the list of sessions, Compare sessions) is repeated as a button here.
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
  reviewCell(x) {  // the reviewer's progress on a session, and the sign-off
    const r = x.review || { ticked: [] }, M = EV.modelOf(x), [a, n] = M ? EV.checked(M, r.ticked) : [r.ticked.length, null];  // the total comes from the session's own records, read in the background
    return (r.signed ? `<span class="ok">reviewed by ${EV.e(r.signed.name || 'not recorded')} on ${EV.e(String(r.signed.at || '').slice(0, 10))}</span> · ` : '') + (a || r.signed ? `checked ${a}${n == null ? '' : ' of ' + n}` : `<span class="mut">not started${n ? ' · ' + n + ' to check' : ''}</span>`);
  },
  HOME: [['id', 'session'], ['brief', 'brief'], ['started', 'started'], ['how', 'how it ended'], ['simulations', 'simulations used', 'num'], ['held', 'tests held / failed'], ['review', 'review progress']],
  HOME_OP: [['policy', 'scheduling policy'], ['gap', 'gap to the best', 'num']],
  homeList() {  // the rows after the filter, a running session first, then by the chosen column
    const h = EV.s.home, f = h.filter.trim().toLowerCase(), key = { how: x => EV.ended(x), review: x => (x.review ? x.review.ticked.length + (x.review.signed ? 1000 : 0) : 0), gap: x => (x.score ? x.score.gap : null), brief: x => x.brief || '' }[h.sort] || (x => x[h.sort]);
    const text = x => [x.id, x.brief || 'before briefs', x.started, EV.ended(x), EV.s.op ? x.policy : '', x.review && x.review.signed ? x.review.signed.name : ''].join(' ').toLowerCase();
    const cmp = (a, b) => { const p = key(a), q = key(b); return p == null ? (q == null ? 0 : 1) : q == null ? -1 : (typeof p === 'number' && typeof q === 'number' ? p - q : String(p).localeCompare(String(q))) * h.dir; };
    return EV.st.sessions.filter(x => !f || f.split(/\s+/).every(w => text(x).includes(w))).sort((a, b) => (b.running ? 1 : 0) - (a.running ? 1 : 0) || cmp(a, b) || a.id.localeCompare(b.id));
  },
  homeRows() {
    const e = EV.e, op = EV.s.op, rows = EV.homeList(), body = rows.map(x => `<tr class="pick${x.running ? ' run' : ''}" data-act="pick" data-id="${e(x.id)}"><td><b>${e(x.id)}</b>${x.running ? ' <span class="pill live">running</span>' : ''}</td><td>${e(x.brief || 'before briefs')}</td>
      <td>${e(String(x.started || '').replace('T', ' ').slice(0, 16)) || EV.nr}</td><td>${x.running ? 'running now' : x.how ? e(x.how) : EV.nr}</td><td class="num">${x.simulations ?? 0}${x.allowed ? ' / ' + x.allowed : ''}</td>
      <td>${x.held + x.failed ? `<span class="ok">${x.held} held</span> · <span class="${x.failed ? 'bad' : 'mut'}">${x.failed} failed</span>` : '<span class="mut">no checks</span>'}</td><td>${EV.reviewCell(x)}</td>
      ${op ? `<td>${x.policy_hidden ? '<span class="mut">hidden until the session is scored</span>' : e(x.policy || '') || EV.nr}</td><td class="num">${EV.gapText(x) || '<span class="mut">not scored</span>'}</td>` : ''}</tr>`).join('');
    const el = document.getElementById('home-rows'), n = document.getElementById('home-n');
    if (el) { el.innerHTML = body; if (n) n.textContent = `${rows.length} of ${EV.st.sessions.length}`; }
    return body;
  },
  homeView() {
    const e = EV.e, S = EV.s, st = EV.st, h = S.home, all = st.sessions, briefs = [...new Set(all.map(x => x.brief || ''))];
    const th = ([k, t, c]) => `<th${c ? ` class="${c}"` : ''}><a data-act="sort" data-id="${k}" title="Sort by this column">${t}${h.sort === k ? (h.dir > 0 ? ' ▲' : ' ▼') : ''}</a></th>`;
    const running = all.filter(x => x.running).length;
    // one title line with the page's one action, beside the title where the eye starts (not at the far right). Opening a session (a row below, or the top bar's list) and comparing
    // (the top bar) each have one place, so they are not repeated here
    return `<div class="ev-title"><h1>All sessions</h1>${EV.newPanel ? `<button class="big primary" data-act="new" title="Write or choose an assignment and start the AI on it">${S.newOpen ? 'Close' : 'New session…'}</button>` : ''}
        <span class="sm">${all.length} session${all.length === 1 ? '' : 's'}${running ? ` · ${running} running now` : ''} · each is one complete attempt by the AI at one ${EV.term('Brief', 'brief')}</span></div>
      ${S.newOpen && EV.newPanel ? EV.newPanel() : ''}
      <div class="ev-card"><h2>Results so far <small>one line per ${EV.term('Brief', 'brief')}, counted from the sessions and, where they exist, their scores</small></h2>
        ${briefs.map(b => `<p><b>${e(b || 'before briefs')}</b>: ${e(EV.results(b))}</p>`).join('') || '<p class="sm">No session yet.</p>'}</div>
      <div class="ev-card"><h2>Sessions <small><span id="home-n">${all.length} of ${all.length}</span> shown · click a row to open it · click a column title to sort</small></h2>
        <p><input type="text" data-in="filter" placeholder="filter: any words of the id, brief, start, ending…" value="${e(h.filter)}" style="width:min(420px,100%)"></p>
        <div class="ev-scroll"><table><thead><tr>${EV.HOME.concat(S.op ? EV.HOME_OP : []).map(th).join('')}</tr></thead><tbody id="home-rows">${EV.homeRows()}</tbody></table></div></div>`;
  },
});
