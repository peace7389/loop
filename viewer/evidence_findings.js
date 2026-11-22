// ======================================================================================================
// Findings on the board of "What it needed to find out" (2026-11-22, the operator: "showing findings ... between hypothesis and turn x axis each
// as a bar stretching from the turn it appeared to the turn it settled? And when users hover over hypotheses we highlight related bars and vice
// versa"). A finding (F1, F2, ...) is one thing the results did not explain (harness/loop.py, since 2026-11-22): who raised it (the researcher,
// or the supervisor), the records it rests on, and each decision of the researcher on it (work, park, close, same_as).
//  - each finding is a bar under the hypotheses, from the turn it was raised to the turn it was closed; one not closed runs on to the last turn
//    and ends open (a chevron). Its stretches say what it was then: open (outlined), worked on (filled), parked (hatched); a closed one ends in a
//    bar end. At its start a treasure chest, the mark of a finding wherever one is shown (2026-11-22, the operator: "What about put icon of
//    treasure chest to represent findings?"); who raised it (the researcher or the supervisor) is in its hover box and its detail, not on the bar
//    (the operator: the icon beside the chest "looks so redundant"); "!" at its end: never looked at;
//  - the bar keeps to the turns' columns (2026-11-22, the operator: "distinct representations of a finding should have the line between turns as
//    border"): it begins on the line before the turn it was raised in, each stretch ends on a line between two turns, and a closed bar ends on
//    the line after the turn that closed it. In a turn's column it stands as that turn's decisions left it (the turn that closed it: as it was
//    closed from);
//  - on the bar its id and its name only (2026-11-22, the operator: "show concise name of each bar of a finding instead of putting content on the
//    bar"): the name its author gave it (harness/loop.py, since 2026-11-22: at most 5 words), or the id alone for a finding without one; what it
//    says is in its hover box and, on a click, in the detail beside the board;
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
    const recs = M.recs || [], fs = recs.filter(r => r.type === 'finding').map(r => ({ id: r.id, by: r.by === 'supervisor' ? 'supervisor' : 'model', turn: r.turn, text: (r.body || {}).text || '', name: (r.body || {}).name || '',
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
  // a finding as it stood at the step the page is at: its status, since when, and its stretches [first turn, last turn (both drawn whole), status]:
  // in each turn's column as that turn's decisions left it; the turn that closed it keeps the status it was closed from
  fndNow(f, last) {
    const ST = { work: 'working', park: 'parked', close: 'closed', same_as: 'same_as' }, ds = f.decisions.filter(d => EV.seen(d.id)), shut = s => s === 'closed' || s === 'same_as';
    let st = 'open', from = f.turn; ds.forEach(d => { st = ST[d.action] || st; from = Math.max(from, d.turn); });
    const done = shut(st), endT = done ? from : Math.max(last, from), segs = []; let cur = 'open';
    for (let t = f.turn; t <= endT; t++) {
      ds.filter(d => d.turn === t).forEach(d => { const s = ST[d.action] || cur; if (!shut(s)) cur = s; });
      const g = segs[segs.length - 1]; if (g && g[2] === cur) g[1] = t; else segs.push([t, t, cur]);
    }
    return { status: st, since: from, segs, done, never: f.end && EV.seen(f.endId) ? !!f.end.never_looked_at : null };
  },
  // the bars, under the boxes of the board: o = { cols, colX, NW, GX, y0 (the top of the lane), last (the last turn drawn), endX (the end's column, or null) }
  fndLane(o) {
    const fs = EV.fndAll().filter(f => EV.seen(f.id)); if (!fs.length) return { h: 0, svg: '' };
    const e = EV.e, BH = 16, GAP = 5, { cols, colX, NW, GX } = o;
    // the lines between turns, where every stretch begins and ends: the one before a turn's column and the one after it (the board draws them
    // in the middle of each gap between two columns); the start's column begins at the board's left edge
    const lineL = t => t <= 0 ? 1 : (cols.includes(t) ? colX(t) : xL(t)) - GX / 2, lineR = t => t <= 0 ? 6 + NW + GX / 2 : (cols.includes(t) ? colX(t) : xL(t)) + NW + GX / 2;
    const xL = t => { if (t <= 0) return 6; const i = cols.indexOf(t); if (i >= 0) return colX(t); const after = cols.findIndex(c => c > t);
      if (after < 0) return colX(cols[cols.length - 1]) + Math.min(GX * 0.6, (t - cols[cols.length - 1]) * GX * 0.3);
      const a = after === 0 ? { t: 0, x: 6 } : { t: cols[after - 1], x: colX(cols[after - 1]) }, b = { t: cols[after], x: colX(cols[after]) }; return a.x + (t - a.t) / (b.t - a.t) * (b.x - a.x); };
    const rows = fs.map((f, i) => {
      const now = EV.fndNow(f, o.last), y = o.y0 + i * (BH + GAP), x1 = lineL(f.turn), xEnd = lineR(now.segs.length ? now.segs[now.segs.length - 1][1] : f.turn);
      const segs = now.segs.map(([a, b, s]) => { const sx = lineL(a), ex = lineR(b); return ex - sx < 1 ? '' : `<rect class="fbar fb-${s}" x="${sx.toFixed(1)}" y="${y}" width="${(ex - sx).toFixed(1)}" height="${BH}"/>`; }).join('');
      const cap = now.done ? `<path class="fb-cap" d="M${xEnd.toFixed(1)},${y - 1} V${y + BH + 1}"/>` : `<path class="fb-go" d="M${(xEnd - 2).toFixed(1)},${y + 2} L${(xEnd + 5).toFixed(1)},${y + BH / 2} L${(xEnd - 2).toFixed(1)},${y + BH - 2}"/>`;
      const room = Math.max(0, Math.floor((xEnd - x1 - 34) / 6.2)), say = `${f.id}${now.status === 'same_as' ? ' = ' + ((f.decisions.filter(d => EV.seen(d.id) && d.action === 'same_as').pop() || {}).refs || [''])[0] : ''}${f.name ? ' · ' + f.name : ''}`;
      const label = room < 3 ? f.id : say.length > room ? say.slice(0, room - 1) + '…' : say;
      const never = now.never ? `<g class="fb-never"><circle cx="${(xEnd + (now.done ? 9 : 14)).toFixed(1)}" cy="${y + BH / 2}" r="6"/><text x="${(xEnd + (now.done ? 9 : 14)).toFixed(1)}" y="${y + BH / 2 + 3.6}">!</text></g>` : '';
      return `<g class="fb" data-f="${e(f.id)}" data-step="${EV.M.recStep[f.id] ?? 0}" data-hyps="${e(f.hyps.join(' '))}" data-act="open" data-t="finding" data-id="${e(f.id)}" data-wd="f:${e(f.id)}" tabindex="0">`
        + `${segs}${cap}${EV.fndChest(x1 + 4, y + 2)}<text class="fb-t" x="${(x1 + 22).toFixed(1)}" y="${y + 11.5}">${e(label)}</text>${never}</g>`;
    }).join('');
    // the turns a bar starts or changes in that have no column of their own (a turn that stated no hypothesis): a small mark with its number under the lane
    const used = [...new Set(fs.flatMap(f => [f.turn, ...f.decisions.filter(d => EV.seen(d.id)).map(d => d.turn)]).concat([o.last]))].filter(t => t > 0 && !cols.includes(t)).sort((a, b) => a - b);
    const yT = o.y0 + fs.length * (BH + GAP) + 2, ticks = used.map(t => `<g class="fb-tick"><path d="M${xL(t).toFixed(1)},${yT} v4"/><text x="${xL(t).toFixed(1)}" y="${yT + 15}">turn ${t}</text></g>`).join('');
    return { h: 14 + fs.length * (BH + GAP) + (used.length ? 16 : 0), svg: `<g class="f-lane" id="f-lane">${rows}${ticks}</g>` };
  },
  // the detail pane: a finding's whole history
  // the box that opens when a finding's bar is pointed at (2026-11-22, the operator: "show better popup both in content and readability. Make it
  // concise also"): its chest, id and name with its status on a chip; what it says, in two lines at most; when and by whom it was raised, where it
  // stands now and for how long, the hypotheses linked to it, and (once the session has ended) whether it was ever looked at
  fndPop(id) {
    const M = EV.M, e = EV.e, f = EV.fndAll().find(q => q.id === id); if (!f || !EV.seen(f.id)) return '';
    const last = Math.max(0, ...(M.turns || []).map(t => t.n)), now = EV.fndNow(f, last), span = (f.end && EV.seen(f.endId) ? f.end.turns_open : (now.done ? now.since : last) - f.turn);
    const text = f.text.length > 160 ? f.text.slice(0, 158).replace(/\s+\S*$/, '') + ' …' : f.text, never = f.end && EV.seen(f.endId) && f.end.never_looked_at;
    return `<p class="wd-h fp-h">${EV.fndChestIcon(16, 14)}<b>${e(f.id)}${f.name ? ` · ${e(f.name)}` : ''}</b><span class="f-pill" data-s="${now.status}">${e(EV.FND_STATE[now.status])}</span></p>`
      + `<p class="wd-lead fp-t">${e(text)}</p>`
      + `<dl class="wd-kv"><dt>Raised</dt><dd>by ${f.by === 'supervisor' ? 'the supervisor' : 'the researcher'}, turn ${e(f.turn)}</dd>`
      + `<dt>${now.done ? 'Closed' : 'Now'}</dt><dd>${now.done ? `in turn ${e(now.since)}, after ${e(span)} turn${span === 1 ? '' : 's'}` : `${e(EV.FND_STATE[now.status])}${now.status === 'open' ? '' : ` since turn ${e(now.since)}`} · open ${e(span)} turn${span === 1 ? '' : 's'}`}</dd>`
      + (f.hyps.length ? `<dt>Linked</dt><dd>${f.hyps.map(e).join(', ')}</dd>` : '') + (never ? '<dt>Looked at</dt><dd><b class="warnc">never</b></dd>' : '') + '</dl>'
      + '<p class="sm fp-do">click: its course, beside the board</p>';
  },
  // the detail pane: a finding at a glance (2026-11-22, the operator: "more useful, more concise, and put more high quality design on it"): the chest,
  // its id and name, its status as a chip; one line of who raised it, when, what it rests on and how long it has stayed open; what it says, as the
  // quote it is; its course turn by turn, each step with the swatch of its stretch on the bar; the hypotheses linked to it, one line each with how
  // each ended; what a finding is, folded away
  fndCard(id) {
    const M = EV.M, e = EV.e, f = EV.fndAll().find(q => q.id === id); if (!f) return '<p class="sm">Nothing to open.</p>';
    const last = Math.max(0, ...(M.turns || []).map(t => t.n)), now = EV.fndNow(f, last), links = ids => ids.map(x => (M.byId[x] ? EV.link(x) : e(x))).join(', ');
    const who = f.by === 'supervisor' ? 'the supervisor' : 'the researcher', ST = { work: 'working', park: 'parked', close: 'closed', same_as: 'closed' };
    const sw = st => `<svg class="f-key f-sw" width="22" height="10" viewBox="0 0 22 10" aria-hidden="true"><rect class="fbar fb-${st === 'closed' ? 'working' : st}" x="1" y="1" width="${st === 'closed' ? 17 : 20}" height="8" rx="2"/>${st === 'closed' ? '<path class="fb-cap" d="M18.5,0 V10"/>' : ''}</svg>`;
    const turnsOpen = f.end && EV.seen(f.endId) ? f.end.turns_open : (now.done ? now.since : last) - f.turn;
    const steps = [`<li><span class="f-t">turn ${e(f.turn)}</span>${sw('open')}<span class="f-what"><b>raised</b> by ${who}${f.from ? ` <span class="sm">· from ${links([f.from])}</span>` : ''}</span></li>`]
      .concat(f.decisions.filter(d => EV.seen(d.id)).map(d => `<li><span class="f-t">turn ${e(d.turn)}</span>${sw(ST[d.action] || 'open')}<span class="f-what"><b>${e(d.action === 'same_as' ? 'the same as' : EV.FND_ACT[d.action] || d.action)}</b>`
        + `${d.refs.length ? ` ${d.action === 'park' ? '' : d.action === 'same_as' ? '' : 'by '}${links(d.refs)}` : ''}${d.reason ? ` <span class="f-why" data-own="model">“${e(d.reason)}”</span>` : ''}${d.auto ? ` <span class="sm" title="${e(d.auto)}">· noted by the harness</span>` : ''}</span></li>`));
    if (!now.done && !(f.end && EV.seen(f.endId)) && last > now.since) steps.push(`<li class="f-now"><span class="f-t">turn ${e(last)}</span>${sw(now.status)}<span class="f-what sm">still ${e(EV.FND_STATE[now.status])}, nothing new on it since turn ${e(now.since)}</span></li>`);
    const end = f.end && EV.seen(f.endId) ? (f.end.never_looked_at ? '<p class="f-end"><b class="warnc">Never looked at</b>: no reading, check or result reached it in the whole session.</p>' : `<p class="f-end sm">Looked at by ${links(f.end.looked_at || [])}.</p>`) : '';
    const hyps = f.hyps.map(h => { const H = M.hypById[h], st = H.state || 'open', t = EV.hshort(H);
      return `<li title="${e(t)}"><span class="f-hl">${EV.link(h)}</span><span class="f-hs" data-s="${e(st)}">${['supported', 'refuted', 'inconclusive', 'dropped'].includes(st) ? EV.gkey(st) : ''}${e(st === 'ended without a verdict' ? 'no verdict' : st)}</span><span class="f-ht">${e(t)}</span></li>`; }).join('');
    return `<div class="f-card"><div class="f-head">${EV.fndChestIcon(22, 19)}<h2>${e(f.id)}${f.name ? ` · ${e(f.name)}` : ''}</h2><span class="f-pill" data-s="${now.status}">${e(EV.FND_STATE[now.status])}${now.done ? '' : ` since turn ${e(now.since)}`}</span></div>
      <p class="f-meta">Raised by ${who} in turn ${e(f.turn)} · rests on ${links(f.about) || '–'} · ${now.done ? 'closed after' : 'open for'} ${e(turnsOpen)} turn${turnsOpen === 1 ? '' : 's'}</p>
      <p class="hq-line f-quote" data-own="${f.by === 'supervisor' ? 'supervisor' : 'model'}">${e(f.text)}</p>
      <h3 class="f-h3">Its course</h3><ol class="f-course">${steps.join('')}</ol>${end}
      ${hyps ? `<h3 class="f-h3">Hypotheses linked to it</h3><ul class="f-hyps">${hyps}</ul>` : ''}
      <details class="f-about"><summary>What is a finding?</summary><p class="sm">One thing the results did not explain. It stays on the researcher's list at the top of every turn until the researcher closes it; each turn the researcher decides on it: works on it, parks it with a reason, closes it with what explains it, or marks it the same as another. Its bar on the board runs over the turns it stayed open.</p></details></div>`;
  },
  // the mark of a finding: a treasure chest (its lid, its box, its lock), 14 by 12 at (x, y)
  // in colour (2026-11-22, the operator: "a icon with some colors for treasure chest for more instance recognition"): wood, a gold band and a gold lock
  fndChest: (x, y) => `<g class="fb-chest" transform="translate(${x},${y})"><path class="ch-lid" d="M1,5.5 V4 C1,1.9 2.8,0.7 7,0.7 C11.2,0.7 13,1.9 13,4 V5.5 Z"/><rect class="ch-box" x="1" y="5.5" width="12" height="6" rx="0.8"/>`
    + `<path class="ch-band" d="M3.6,1.2 V11.5 M10.4,1.2 V11.5"/><rect class="ch-gold" x="0.6" y="4.8" width="12.8" height="1.5" rx="0.5"/><rect class="ch-gold" x="5.6" y="4" width="2.8" height="3.6" rx="0.6"/><circle class="ch-key" cx="7" cy="5.6" r="0.55"/></g>`,
  fndChestIcon: (w = 16, h = 14) => `<svg class="fk-chest" width="${w}" height="${h}" viewBox="0 0 15 13" aria-hidden="true" style="display:inline;vertical-align:-2px">${EV.fndChest(0.5, 0.5)}</svg>`,
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
