// ======================================================================================================
// Findings on the board of "What it needed to find out" (2026-11-22, the operator: "showing findings ... between hypothesis and turn x axis each
// as a bar stretching from the turn it appeared to the turn it settled? And when users hover over hypotheses we highlight related bars and vice
// versa"). A finding (F1, F2, ...) is one thing the results did not explain (harness/loop.py, since 2026-11-22): who raised it (the researcher,
// or the supervisor), the records it rests on, and each decision of the researcher on it (work, park, close, same_as).
//  - each finding is a bar under the hypotheses, from the turn it was raised to the turn it was closed; one not closed runs on to the last turn
//    and ends open (a chevron). Its stretches say what it was then: open (outlined), worked on (filled), parked (hatched); a closed one ends in a
//    bar end. An icon at its start says who raised it (a magnifier: the researcher; an eye: the supervisor); "!" at its end: never looked at;
//  - pointing at a bar outlines the hypotheses that worked on it or closed it, and pointing at a hypothesis outlines its findings' bars;
//  - a click opens the finding's history beside the board.
// During the replay only what was recorded by then is drawn.
// ======================================================================================================
Object.assign(EV, {
  FND_STATE: { open: 'open', working: 'worked on', parked: 'parked', closed: 'closed', same_as: 'the same as another' },
  FND_ACT: { work: 'worked on', park: 'parked', close: 'closed', same_as: 'the same as' },
  // every finding of the open session, with its decisions, the hypotheses linked to it and the harness's tally at the end; made once per session
  fndAll() {
    const M = EV.M; if (!M) return []; if (M._find) return M._find;
    const recs = M.recs || [], fs = recs.filter(r => r.type === 'finding').map(r => ({ id: r.id, by: r.by === 'supervisor' ? 'supervisor' : 'model', turn: r.turn, text: (r.body || {}).text || '',
      about: (r.body || {}).about || [], from: (r.body || {}).from || r.parent || null, decisions: [] })), byF = Object.fromEntries(fs.map(f => [f.id, f]));
    recs.forEach(r => { const b = r.body || {}; if (r.type === 'decision' && byF[b.for]) byF[b.for].decisions.push({ id: r.id, turn: r.turn, action: b.action, refs: b.refs || [], reason: b.reason || '', auto: b.auto || '' }); });
    const end = [...recs].reverse().find(r => r.type === 'findings_end'), endRow = end ? Object.fromEntries(((end.body || {}).findings || []).map(x => [x.id, x])) : {};
    fs.forEach(f => {
      f.end = endRow[f.id] || null; f.endId = end ? end.id : null;
      f.links = [...new Set(f.decisions.flatMap(d => d.refs).filter(x => !byF[x]))];
      const hy = new Set();
      f.links.forEach(x => { const r = M.byId[x], b = (r && r.body) || {}; if (!r) return;
        if (r.type === 'hypothesis') hy.add(x);
        if (r.type === 'why') M.hyps.filter(h => h.from_why === x).forEach(h => hy.add(h.id));
        if ((r.type === 'check' || r.type === 'verdict') && b.for) hy.add(b.for);
        if (r.type === 'experiment') (b.tests || []).forEach(h => hy.add(h)); });
      f.hyps = [...hy].filter(h => M.hypById[h]);
    });
    return (M._find = fs);
  },
  // the turns the findings span (from the first one raised to the last decision on one): each gets a column of the board, so that every bar starts and ends at a turn
  fndTurns() { const ts = EV.fndAll().filter(f => EV.seen(f.id)).flatMap(f => [f.turn, ...f.decisions.filter(d => EV.seen(d.id)).map(d => d.turn)]).filter(t => t > 0); if (!ts.length) return [];
    const lo = Math.min(...ts), hi = Math.max(...ts); return Array.from({ length: hi - lo + 1 }, (_, i) => lo + i); },
  fndOf(hid) { return EV.fndAll().filter(f => EV.seen(f.id) && f.hyps.includes(hid)); },
  // a finding as it stood at the step the page is at: its status, since when, and its stretches [from turn, to turn, status]
  fndNow(f, last) {
    const ST = { work: 'working', park: 'parked', close: 'closed', same_as: 'same_as' }, segs = []; let st = 'open', from = f.turn;
    f.decisions.filter(d => EV.seen(d.id)).forEach(d => { if (d.turn > from) segs.push([from, d.turn, st]); st = ST[d.action] || st; from = Math.max(from, d.turn); });
    const done = st === 'closed' || st === 'same_as';
    if (!done && last > from) segs.push([from, last, st]); else if (!done) segs.push([from, from, st]);
    return { status: st, since: from, segs, done, never: f.end && EV.seen(f.endId) ? !!f.end.never_looked_at : null };
  },
  // the bars, under the boxes of the board: o = { cols, colX, NW, GX, y0 (the top of the lane), last (the last turn drawn), endX (the end's column, or null) }
  fndLane(o) {
    const fs = EV.fndAll().filter(f => EV.seen(f.id)); if (!fs.length) return { h: 0, svg: '' };
    const e = EV.e, BH = 16, GAP = 5, { cols, colX, NW, GX } = o;
    const xL = t => { if (t <= 0) return 6; const i = cols.indexOf(t); if (i >= 0) return colX(t); const after = cols.findIndex(c => c > t);
      if (after < 0) return colX(cols[cols.length - 1]) + Math.min(GX * 0.6, (t - cols[cols.length - 1]) * GX * 0.3);
      const a = after === 0 ? { t: 0, x: 6 } : { t: cols[after - 1], x: colX(cols[after - 1]) }, b = { t: cols[after], x: colX(cols[after]) }; return a.x + (t - a.t) / (b.t - a.t) * (b.x - a.x); };
    const who = (by, x, y) => by === 'supervisor'
      ? `<g class="fb-who" transform="translate(${x},${y})"><path d="M0,5 C3,0.5 9,0.5 12,5 C9,9.5 3,9.5 0,5 Z"/><circle cx="6" cy="5" r="1.8"/></g>`
      : `<g class="fb-who" transform="translate(${x},${y})"><circle cx="4.6" cy="4.6" r="3.6"/><path d="M7.3,7.3 L11,11"/></g>`;
    const rows = fs.map((f, i) => {
      const now = EV.fndNow(f, o.last), y = o.y0 + i * (BH + GAP), x1 = xL(f.turn), xEnd = now.done ? xL(now.since) + NW : xL(o.last) + NW + Math.min(18, GX * 0.4);
      const segs = now.segs.map(([a, b, s], k) => { const sx = k === 0 ? x1 : xL(a), ex = k === now.segs.length - 1 ? xEnd : xL(b); return ex - sx < 1 ? '' : `<rect class="fbar fb-${s}" x="${sx.toFixed(1)}" y="${y}" width="${(ex - sx).toFixed(1)}" height="${BH}" rx="${k === 0 ? 4 : 0}"/>`; }).join('');
      const cap = now.done ? `<path class="fb-cap" d="M${xEnd.toFixed(1)},${y - 1} V${y + BH + 1}"/>` : `<path class="fb-go" d="M${(xEnd - 2).toFixed(1)},${y + 2} L${(xEnd + 5).toFixed(1)},${y + BH / 2} L${(xEnd - 2).toFixed(1)},${y + BH - 2}"/>`;
      const room = Math.max(0, Math.floor((xEnd - x1 - 34) / 6.2)), say = `${f.id}${now.status === 'same_as' ? ' = ' + ((f.decisions.filter(d => EV.seen(d.id) && d.action === 'same_as').pop() || {}).refs || [''])[0] : ''} · ${f.text}`;
      const label = room < 3 ? f.id : say.length > room ? say.slice(0, room - 1) + '…' : say;
      const never = now.never ? `<g class="fb-never"><circle cx="${(xEnd + (now.done ? 9 : 14)).toFixed(1)}" cy="${y + BH / 2}" r="6"/><text x="${(xEnd + (now.done ? 9 : 14)).toFixed(1)}" y="${y + BH / 2 + 3.6}">!</text></g>` : '';
      const tip = `${f.id}, raised by ${f.by === 'supervisor' ? 'the supervisor' : 'the researcher'} in turn ${f.turn}: ${f.text}\nNow: ${EV.FND_STATE[now.status]}${now.status === 'open' ? '' : ' (since turn ' + now.since + ')'}`
        + (f.hyps.length ? `\nHypotheses linked to it: ${f.hyps.join(', ')}` : '') + (now.never ? '\nNever looked at: no reading, check or result reached it.' : '') + '\nClick to open its history beside the board.';
      return `<g class="fb" data-f="${e(f.id)}" data-step="${EV.M.recStep[f.id] ?? 0}" data-hyps="${e(f.hyps.join(' '))}" data-act="open" data-t="finding" data-id="${e(f.id)}" tabindex="0"><title>${e(tip)}</title>`
        + `${segs}${cap}${who(f.by, x1 + 4, y + 3)}<text class="fb-t" x="${(x1 + 20).toFixed(1)}" y="${y + 11.5}">${e(label)}</text>${never}</g>`;
    }).join('');
    // the turns a bar starts or changes in that have no column of their own (a turn that stated no hypothesis): a small mark with its number under the lane
    const used = [...new Set(fs.flatMap(f => [f.turn, ...f.decisions.filter(d => EV.seen(d.id)).map(d => d.turn)]).concat([o.last]))].filter(t => t > 0 && !cols.includes(t)).sort((a, b) => a - b);
    const yT = o.y0 + fs.length * (BH + GAP) + 2, ticks = used.map(t => `<g class="fb-tick"><path d="M${xL(t).toFixed(1)},${yT} v4"/><text x="${xL(t).toFixed(1)}" y="${yT + 15}">turn ${t}</text></g>`).join('');
    return { h: 14 + fs.length * (BH + GAP) + (used.length ? 16 : 0), svg: `<g class="f-lane" id="f-lane">${rows}${ticks}</g>` };
  },
  // the detail pane: a finding's whole history
  fndCard(id) {
    const M = EV.M, e = EV.e, f = EV.fndAll().find(q => q.id === id); if (!f) return '<p class="sm">Nothing to open.</p>';
    const last = Math.max(0, ...(M.turns || []).map(t => t.n)), now = EV.fndNow(f, last), links = ids => ids.map(x => (M.byId[x] ? EV.link(x) : e(x))).join(', ');
    const hist = [`<li><b>turn ${e(f.turn)}</b>: raised by ${f.by === 'supervisor' ? 'the supervisor' : 'the researcher'}${f.from ? ` <span class="sm">(with ${links([f.from])})</span>` : ''}</li>`]
      .concat(f.decisions.filter(d => EV.seen(d.id)).map(d => `<li><b>turn ${e(d.turn)}</b>: ${e(EV.FND_ACT[d.action] || d.action)}${d.refs.length ? (d.action === 'park' ? '' : ' by ') + links(d.refs) : ''}${d.reason ? ` <span data-own="model">“${e(d.reason)}”</span>` : ''}${d.auto ? ` <span class="sm">(the harness: ${e(d.auto)})</span>` : ''}</li>`));
    const end = f.end && EV.seen(f.endId) ? `<p>${f.end.never_looked_at ? '<b class="warnc">Never looked at</b>: no reading, check or result reached it in the whole session.' : `Looked at by ${links(f.end.looked_at || [])}.`} <span class="sm">It stayed open ${e(f.end.turns_open)} turn${f.end.turns_open === 1 ? '' : 's'}.</span></p>` : '';
    return `<h2>Finding ${e(f.id)} <small>raised by ${f.by === 'supervisor' ? 'the supervisor' : 'the researcher'} in turn ${e(f.turn)} · ${e(EV.FND_STATE[now.status])}</small></h2>
      <p class="hq-line" data-own="${f.by === 'supervisor' ? 'supervisor' : 'model'}">${e(f.text)}</p><p class="sm">It rests on ${links(f.about) || '–'}.</p>
      <p class="sm">A finding is one thing the results did not explain. It stays on the researcher's list at the top of every turn until the researcher closes it; each turn it decides on it: works on it, parks it, closes it with what explains it, or marks it the same as another.</p>
      <h3>What became of it</h3><ul class="f-hist">${hist.join('')}</ul>${end}
      ${f.hyps.length ? `<h3>Hypotheses linked to it</h3><p>${f.hyps.map(h => `${EV.link(h)} <span class="sm">${e(EV.hshort ? EV.hshort(M.hypById[h]) : M.hypById[h].text)}</span>`).join('<br>')}</p>` : ''}`;
  },
  fndIcon: () => '<svg class="fk-ic" width="28" height="12" viewBox="0 0 28 12" aria-hidden="true"><rect class="fbar fb-working" x="1" y="1" width="22" height="10" rx="3"/><path class="fb-cap" d="M23,0 V12"/></svg>',
  // pointing at a bar outlines its hypotheses; pointing at a hypothesis outlines the bars of its findings
  fndPoint(el) {
    EV.fndUnpoint(); if (!el) return;
    const map = el.closest('.ev-map'); if (!map) return;
    if (el.matches('g.fb')) { el.classList.add('f-me'); (el.dataset.hyps || '').split(' ').filter(Boolean).forEach(h => map.querySelectorAll(`g[data-node="${CSS.escape(h)}"]`).forEach(g => g.classList.add('f-rel'))); }
    else { const h = el.dataset.node; map.querySelectorAll('g.fb').forEach(g => { if ((g.dataset.hyps || '').split(' ').includes(h)) g.classList.add('f-rel'); }); if (map.querySelector('g.fb.f-rel')) el.classList.add('f-me'); }
  },
  fndUnpoint() { document.querySelectorAll('.ev-map .f-me, .ev-map .f-rel').forEach(g => g.classList.remove('f-me', 'f-rel')); },
});
document.addEventListener('mouseover', ev => { const g = ev.target.closest && ev.target.closest('.ev-map g.fb, .ev-map g[data-node]');
  if (g && !g.classList.contains('f-me')) EV.fndPoint(g); else if (!g && document.querySelector('.ev-map .f-me, .ev-map .f-rel')) EV.fndUnpoint(); });
document.addEventListener('focusin', ev => { const g = ev.target.closest && ev.target.closest('.ev-map g.fb'); if (g) EV.fndPoint(g); });
