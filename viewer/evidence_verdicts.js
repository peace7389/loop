// Verdicts against checks: a table of counts, one verdict each. Row: the checks of the verdict's hypothesis in the last
// experiment that tested it before the verdict: all held, all failed, mixed, or no check (the first format). Column:
// the verdict (supported, inconclusive, refuted), and "no verdict" for a hypothesis that was checked and never judged.
// Two places: a session's summary in the detail pane (that session alone, counted here from its own records, and
// during the replay only from the records by the chosen step), and the Compare tab (the sessions of the chosen brief,
// from the counts control.py puts in each session's row; with the operator columns on, also one table per scheduling
// policy). Sessions of different briefs are never added together. Neither place is printed.
// ======================================================================================================
Object.assign(EV, {
  VC_ROWS: [['held', '<span class="ok">✓ held</span>', 'every check held'], ['mixed', 'mixed', 'some checks held and some failed'], ['failed', '<span class="bad">✗ failed</span>', 'every check failed'], ['no check', 'no check', 'the hypothesis was judged without a check by the harness']],
  VC_COLS: [['supported', 'supported'], ['inconclusive', 'inconclusive'], ['refuted', 'refuted'], ['no verdict', 'no verdict']],
  // one session, from its own records; only what is recorded by the replay's step
  vcCount(M) {
    const seen = EV.seen, made = {}, judged = new Set(), out = {}, add = (r, c) => { out[r] = out[r] || {}; out[r][c] = (out[r][c] || 0) + 1; };
    const row = (h, before) => { const cs = (made[h] || []).filter(c => c.i < before); if (!cs.length) return 'no check';
      const res = cs.filter(c => c.x === cs[cs.length - 1].x).map(c => c.r); return res.every(r => r === 'held') ? 'held' : res.every(r => r === 'failed') ? 'failed' : 'mixed'; };
    M.recs.forEach((r, i) => { if (!seen(r.id)) return; const b = r.body || {};
      if (r.type === 'check' && (b.result === 'held' || b.result === 'failed')) (made[b.for] = made[b.for] || []).push({ i, x: b.experiment || r.parent, r: b.result });
      else if (r.type === 'verdict') { add(row(b.for, i), b.result); judged.add(b.for); } });
    Object.keys(made).forEach(h => { if (!judged.has(h)) add(row(h, Infinity), 'no verdict'); });
    return out;
  },
  vcSum(list) { const out = {}; list.forEach(c => Object.entries(c || {}).forEach(([r, cols]) => Object.entries(cols).forEach(([k, n]) => { out[r] = out[r] || {}; out[r][k] = (out[r][k] || 0) + n; }))); return out; },
  vcTotal: c => Object.entries(c || {}).reduce((a, [, cols]) => a + Object.entries(cols).reduce((s, [k, n]) => s + (k === 'no verdict' ? 0 : n), 0), 0),
  // the table: a row of checks is drawn when it has a count; a count of nothing is a muted 0
  vcTable(c, name) {
    const rows = EV.VC_ROWS.filter(([r]) => c[r]), cell = (r, k) => { const n = (c[r] || {})[k] || 0; return `<td class="num${n ? '' : ' mut'}" data-r="${r}" data-c="${k}">${n ? `<b>${n}</b>` : 0}</td>`; };
    if (!rows.length) return `<p class="sm vc-none" data-vc="${EV.e(name || '')}">No verdict and no checked hypothesis${EV.s.step == null ? '' : ' by this step'}.</p>`;
    return `<table class="vc" data-vc="${EV.e(name || '')}"><thead><tr><th>the ${EV.term('Check', 'checks')} of the hypothesis</th>${EV.VC_COLS.map(([k, t]) => `<th class="num"${k === 'no verdict' ? ' title="A hypothesis that was checked and never judged"' : ''}>${t}</th>`).join('')}</tr></thead>
      <tbody>${rows.map(([r, label, tip]) => `<tr><td title="${tip}">${label}</td>${EV.VC_COLS.map(([k]) => cell(r, k)).join('')}</tr>`).join('')}</tbody></table>`;
  },
  VC_NOTE: 'One count per verdict. The row is the checks of its hypothesis in the last experiment that tested it before the verdict.',

  // ---- in a session's summary (the detail pane)
  vcSession() {
    const c = EV.vcCount(EV.M), n = EV.vcTotal(c);
    return `<div id="vc-session"><h3 style="margin-top:14px">${EV.term('Verdict', 'Verdicts')} against ${EV.term('Check', 'checks')}</h3>${EV.vcTable(c, 'session')}<p class="sm">${EV.VC_NOTE} ${n} verdict${n === 1 ? '' : 's'}${EV.s.step == null ? '' : ' by this step of the replay'}.</p></div>`;
  },

  // ---- on the Compare tab: the sessions of the chosen brief, never two briefs in one table
  vcCompare(rows) {
    const e = EV.e, S = EV.s, name = S.brief || 'before briefs', have = rows.filter(x => x.vc), n = k => `${k} session${k === 1 ? '' : 's'}`;
    if (!rows.length) return '';
    if (!have.length) return `<div class="ev-card noprint" id="cmp-vc"><h2>Verdicts against checks <small>brief ${e(name)}</small></h2><p class="sm">The counts of these sessions: ${EV.nr} (the control server gives them; it may need a restart).</p></div>`;
    const all = EV.vcSum(have.map(x => x.vc)), part = (title, list, key) => `<div><h3>${title} · ${n(list.length)} · ${EV.vcTotal(EV.vcSum(list.map(x => x.vc)))} verdicts</h3>${EV.vcTable(EV.vcSum(list.map(x => x.vc)), key)}</div>`;
    let split = '';
    if (S.op) {  // operator columns: one table per scheduling policy; a policy the harness chose stays out until the session is scored
      const known = have.filter(x => x.policy && !x.policy_hidden), pols = [...new Set(known.map(x => x.policy))].sort().reverse(), hidden = have.filter(x => x.policy_hidden).length, none = have.length - known.length - hidden;
      split = `<h3 style="margin-top:14px"><span data-by="operator"><i class="sw"></i></span> by ${EV.term('Scheduling policy', 'scheduling policy')} (operator columns)</h3><div class="vc-row">${pols.map(p => part('policy ' + e(p), known.filter(x => x.policy === p), 'policy-' + p)).join('')}</div>
        ${hidden || none ? `<p class="sm">${[hidden ? `${n(hidden)} whose policy is hidden until scored` : '', none ? `${n(none)} whose policy is not recorded` : ''].filter(Boolean).join(' and ')}: counted in the table of all sessions only.</p>` : ''}`;
    }
    return `<div class="ev-card noprint" id="cmp-vc"><h2>Verdicts against checks <small>the ${n(have.length)} of ${EV.term('Brief', 'brief')} ${e(name)} · sessions of different briefs are never added together</small></h2>
      <div class="vc-row">${part('all sessions of this brief', have, 'brief')}</div><p class="sm">${EV.VC_NOTE}${have.length < rows.length ? ` ${n(rows.length - have.length)} without counts: ${EV.nr}.` : ''}</p>${split}</div>`;
  },
});
