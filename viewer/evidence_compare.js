// Compare sessions: the sessions of one brief with a tick on each row. Two or more ticked are shown side by side: their
// best-so-far lines on one chart (one colour per session), a table of how they went (differences in the recommendation
// marked), and for each the first test that held. With the operator columns on, the sweep as a parallel-coordinates
// chart with each ticked session's recommendation as a bold line (evidence_parallel.js).
// A session other than the open one is read here from its own ledger and session.json (never its drafts).
// ======================================================================================================
Object.assign(EV, {
  models: {},   // session id -> { sig, M }: the session as EV_DATA builds it, read once and again when it has grown
  picked: [],   // the ticked sessions: [{ id, slot }]; slot is the colour, kept while the session stays ticked
  modelOf(x) {
    const c = EV.models[x.id], sig = `${x.records}|${!!x.running}`; if (c && c.sig === sig) return c.M;
    EV.models[x.id] = { sig, M: c ? c.M : null };
    Promise.all([EV.get(`../sessions/${x.id}/ledger.jsonl`), EV.json(`../sessions/${x.id}/session.json`)]).then(([led, meta]) => {
      if (EV.models[x.id].sig !== sig) return; EV.models[x.id].M = EV_DATA.build({ id: x.id, ledger: EV_DATA.lines(led), session: meta, report: null, running: !!x.running });
      clearTimeout(EV.modelsT); EV.modelsT = setTimeout(() => { if (EV.s.view === 'home') EV.homeRows(); else if (EV.s.view === 'compare') EV.draw(); }, 60); });
    return c ? c.M : null;
  },
  color: slot => `var(--cat-${slot})`,

  compareTab() {
    const e = EV.e, S = EV.s, st = EV.st, briefs = [...new Set(st.sessions.map(x => x.brief || ''))], rows = st.sessions.filter(x => (x.brief || '') === (S.brief || '')).sort((a, b) => (b.running ? 1 : 0) - (a.running ? 1 : 0) || a.id.localeCompare(b.id));
    EV.picked = EV.picked.filter(t => rows.some(x => x.id === t.id)); const slot = id => (EV.picked.find(t => t.id === id) || {}).slot, list = EV.picked.map(t => ({ x: rows.find(x => x.id === t.id), slot: t.slot })).sort((a, b) => a.x.id.localeCompare(b.x.id));
    const tr = x => `<tr class="${x.running ? 'run' : ''}"><td><label style="font-weight:400;white-space:nowrap"><input type="checkbox" data-ch="tick" data-id="${e(x.id)}"${slot(x.id) ? ' checked' : ''}${!slot(x.id) && EV.picked.length >= 8 ? ' disabled' : ''}> ${slot(x.id) ? `<i class="sw" style="background:${EV.color(slot(x.id))}"></i>` : ''}</label></td>
      <td><a data-act="pick" data-id="${e(x.id)}"><b>${e(x.id)}</b></a>${x.running ? ' <span class="pill live">running</span>' : ''}</td><td class="nb">${e(String(x.started || '').replace('T', ' ').slice(0, 16)) || EV.nr}</td>${x.running || x.how ? EV.one(x.running ? 'running now' : x.how, 'w-how') : `<td>${EV.nr}</td>`}
      <td class="num nb">${x.simulations ?? 0}${x.allowed ? ' / ' + x.allowed : ''}</td><td class="sqc" data-col="seq">${EV.seqCell(x)}</td><td class="nb" data-col="review">${EV.reviewCell(x)}</td>
      ${S.op ? `<td class="nb">${x.policy_hidden ? '<span class="mut">hidden until scored</span>' : e(x.policy || '') || EV.nr}</td><td class="num nb">${EV.gapText(x) || '<span class="mut">not scored</span>'}</td>` : ''}</tr>`;
    return `<div class="ev-card"><h2>Compare sessions <small>the sessions of one ${EV.term('Brief', 'brief')} · those ticked stand side by side below (at most eight)</small></h2>
        <p><label>${EV.term('Brief', 'Brief')} <select data-ch="brief">${briefs.map(b => `<option value="${e(b)}"${b === (S.brief || '') ? ' selected' : ''}>${e(b || 'before briefs')} (${st.sessions.filter(x => (x.brief || '') === b).length})</option>`).join('')}</select></label> <span class="sm">${e(EV.results(S.brief || ''))}</span></p>
        <div class="ev-scroll"><table><thead><tr><th>compare</th><th>session</th><th>started</th><th>how it ended</th><th class="num">simulations used</th><th>checks, in order</th><th>review progress</th>${S.op ? '<th>scheduling policy</th><th class="num">gap to the best</th>' : ''}</tr></thead>
          <tbody id="cmp-rows">${rows.map(tr).join('')}</tbody></table></div></div>
      ${EV.vcCompare(rows)}
      ${list.length >= 2 ? EV.compareBody(list) : `<div class="ev-card"><p class="sm">${list.length ? 'One session is ticked: tick another one.' : 'Tick two or more sessions.'}</p></div>`}`;
  },

  compareBody(list) {
    const e = EV.e, S = EV.s; list.forEach(q => { q.M = EV.modelOf(q.x); });
    if (list.some(q => !q.M)) return '<div class="ev-card"><p class="sm">Reading the ticked sessions…</p></div>';
    const head = q => `<th><i class="sw" style="background:${EV.color(q.slot)}"></i>${e(q.x.id)}</th>`, series = list.map(q => ({ d: EV.bestData(q.M), name: q.x.id, color: EV.color(q.slot) })).filter(q => q.d && q.d.pts.length);
    const open = list[0].M.brief && list[0].M.brief.goal && list[0].M.brief.goal.kind === 'open';
    const rb = open || !series.length ? [] : EV.randomCompare(list, Math.max(...series.map(q => q.d.pts.length), 2) - 1), bands = rb.filter(b => b.B && !b.B.none).map(b => ({ B: b.B, offset: 1 }));
    const chart = open ? '<p class="sm">Not applicable: the goal is chosen by the model.</p>' : series.length ? EV.bestSvg(series, { dots: false, zoom: true, bands }) : `<p class="sm">the brief's goal: ${EV.nr}</p>`;
    const rkey = !rb.length ? '' : `<p class="sm" id="cmp-rnd" data-by="operator"><i class="sw"></i>${rb.map(b => (!b.B ? `reading the sweep ${e(b.sweep)}…` : b.B.none ? `random choice under “${e(b.policy)}”: ${EV.nr}` : `<i class="rnd-band"></i>random choice under “${e(b.policy)}” (behind ${e(b.sessions.join(', '))}): ${EV.RND.reps.toLocaleString('en-US')} repetitions of ${b.B.n} draws from the ${b.B.first} rows of the first grid of sweep ${e(b.sweep)}; the band is the 10th to the 90th percentile of the best valid result so far, <span class="rnd-med">- -</span> the median; after ${b.B.n} draws the median is ${e(EV.val(series[0].d.g.target, b.B.p50[b.B.n - 1]))}`)).join(' · ')} (${EV.term('Operator', 'operator')} column).</p>`;
    const row = (name, f, cls) => `<tr${cls ? ` class="${cls}"` : ''}><td>${name}</td>${list.map(q => `<td>${f(q)}</td>`).join('')}</tr>`;
    const recs = list.map(q => (q.M.report && typeof q.M.report.recommendation === 'object' && q.M.report.recommendation) || {}), keys = [...new Set(recs.flatMap(r => Object.keys(r)))];
    const recRows = keys.map(k => { const vals = recs.map(r => (k in r ? String(r[k]) : '')), n = {}; vals.forEach(v => { n[v] = (n[v] || 0) + 1; }); const top = Object.keys(n).sort((a, b) => n[b] - n[a])[0], most = n[top] > 1 ? top : null, differ = Object.keys(n).length > 1;  // no value shared by two sessions: every cell is marked
      return `<tr><td>recommends ${e(k)}${differ ? ' <span class="warnc" title="the ticked sessions differ here">≠</span>' : ''}</td>${vals.map(v => `<td${differ && v !== most ? ' class="dif"' : ''}>${v === '' ? '<span class="mut">not stated</span>' : e(v)}</td>`).join('')}</tr>`; }).join('');
    const firsts = list.map(q => { const h = EV.highlights(q.M).items.find(i => i.rule === 1);
      return `<p><i class="sw" style="background:${EV.color(q.slot)}"></i><b>${e(q.x.id)}</b> ${h ? `<a data-act="pickitem" data-id="${e(q.x.id)}" data-t="${h.open.t}" data-item="${e(h.open.id)}">${h.html}</a>` : '<span class="mut">no test held</span>'}</p>`; }).join('');
    return `<div class="ev-card" id="cmp-best"><h2>Best so far, side by side <small>the best value so far among the simulations that meet the brief's conditions; one line per session, named at its end</small></h2>${chart}${rkey}</div>
      <div class="ev-card" id="cmp-table"><h2>How they went</h2><div class="ev-scroll"><table><thead><tr><th></th>${list.map(head).join('')}</tr></thead><tbody>
        ${row('how it ended', q => (q.x.running ? 'running now' : e(q.x.how || 'not recorded')))}${row(EV.term('Simulation', 'simulations') + ' used', q => `${q.x.simulations ?? 0}${q.x.allowed ? ' / ' + q.x.allowed : ''}`)}
        ${row(EV.term('Turn', 'turns'), q => q.M.counts.turn)}${row(EV.term('Hypothesis', 'hypotheses'), q => `${q.M.hyps.length}<span class="sm"> · ${EV.STATES.filter(s => q.M.hyps.some(h => h.state === s)).map(s => `${q.M.hyps.filter(h => h.state === s).length} ${s}`).join(' · ')}</span>`)}
        ${row(EV.term('Test', 'tests') + ' held / failed', q => EV.tally(q.x.held, q.x.failed, q.x.void ? q.x.void[0] : 0))}${row('refused answers or parts', q => q.M.counts.refused)}
        ${recRows || row('recommendation', q => '<span class="mut">no final report</span>')}
        ${S.op ? row(EV.term('Scheduling policy', 'scheduling policy'), q => EV.policyText(q.x)) + row('gap to the best', q => EV.gapText(q.x) || '<span class="mut">not scored</span>') : ''}</tbody></table></div>
        <p class="sm">≠ the ticked sessions recommend different values; the cells that differ from the most common value are marked.</p></div>
      ${EV.researchCompare(list)}
      <div class="ev-card" id="cmp-first"><h2>The first ${EV.term('Test', 'test')} that held, in each <small>one for each ticked session</small></h2>${firsts}</div>
      ${S.op ? EV.parallelCards(list) : ''}`;
  },
});
EV.chg = Object.assign(EV.chg || {}, {
  tick(t) { const id = t.dataset.id; if (t.checked) { const used = new Set(EV.picked.map(q => q.slot)), slot = [1, 2, 3, 4, 5, 6, 7, 8].find(n => !used.has(n)); if (slot) EV.picked.push({ id, slot }); } else EV.picked = EV.picked.filter(q => q.id !== id); EV.draw(); },
});
EV.act = Object.assign(EV.act || {}, {
  pickitem(id, t) { const sel = { t: t.dataset.t, id: /^\d+$/.test(t.dataset.item) && t.dataset.t === 'log' ? Number(t.dataset.item) : t.dataset.item }; EV.go({ view: 'session', sid: id }).then(() => { EV.s.sel = sel; EV.draw(); }); },
});
