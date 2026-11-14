// View 1 (the session flow in three lanes) and View 2 (the hypothesis map), drawn as plain SVG. Every box carries
// data-step (the step of the session flow at which it was recorded), so the replay can grey everything later.
// ======================================================================================================
Object.assign(EV, {
  LANES: { model: [0, 232], harness: [240, 166], simulator: [414, 150] },  // x and width of each lane

  // ---- View 1: one box per step in the lane of whoever did it, joined in time order; a band marks each turn
  viewLanes() {
    const M = EV.M, S = EV.s, e = EV.e, L = EV.LANES, W = 564, out = [], arrows = [];
    const info = EV.selInfo(), selSteps = new Set([...info.recs].map(id => M.recStep[id]).filter(k => k != null));  // the boxes that hold a part of the selected item
    const hit = new Set(); if (S.claim) { const c = M.claims[S.claim - 1]; (c ? c.evidence : []).forEach(id => { if (id in M.recStep) hit.add(M.recStep[id]); }); }
    const icon = { start: EV_ICON.brief, answer: '✎', refused: EV_ICON.malformed, accepted: EV_ICON.experiment, sims: EV_ICON.simulation, checks: EV_ICON.check, report: EV_ICON.report };
    let y = 30, prev = null;
    const head = Object.entries(L).map(([b, [x, w]]) => `<g data-by="${b}"><rect class="stripe" x="${x}" y="4" width="10" height="10" rx="3"/><text x="${x + 15}" y="13" style="font-weight:600;fill:var(--text-primary)">the ${b}</text></g>`).join('');
    const lines = Object.entries(L).map(([, [x, w]]) => `<line x1="${x + w / 2}" y1="22" x2="${x + w / 2}" y2="@H" stroke="var(--grid)" stroke-dasharray="2 4"/>`).join('');
    M.turns.forEach(t => {
      if (!t.steps.length) return;
      const k0 = t.steps[0].k, shut = !!S.collapsed[t.n];
      const left = t.n === 0 ? 'before the first turn' : t.left == null ? 'simulations left: ' + 'not recorded' : `${t.left} simulation${t.left === 1 ? '' : 's'} left${t.last ? ' · last turn' : ''}`;
      out.push(`<g data-act="fold" data-id="${t.n}" data-step="${k0}"><rect class="band" x="0" y="${y}" width="${W}" height="20" rx="4"/><text x="8" y="${y + 14}" style="font-weight:600;fill:var(--text-primary)">${shut ? '▸' : '▾'} ${t.n === 0 ? 'start' : EV_ICON.turn + ' turn ' + t.n}</text>
        <text x="${W - 8}" y="${y + 14}" text-anchor="end">${e(left)}${shut ? ` · ${t.steps.length} steps folded` : ''}</text><title>${shut ? 'Show' : 'Fold'} this turn</title></g>`);
      y += 28; if (shut) { prev = null; return; }
      t.steps.forEach(s => {
        const [x, w] = L[s.lane], cpl = Math.floor((w - 16) / 6.6), ic = icon[s.kind] || '', text = s.label, short = text.length > 188 ? text.slice(0, 184) + '…' : text;
        const tl = Math.max(1, Math.ceil((short.length + 2) / cpl) + (short.match(/;/g) || []).length * 0.4), per = Math.floor((w - 14) / 10), sims = s.sims || [];
        const th = Math.round(10 + 15 * tl), h = th + (sims.length ? Math.ceil(sims.length / per) * 10 + 6 : 0);
        const cls = [s.warn ? 'warn' : '', selSteps.has(s.k) || (info.turn === s.turn && s.kind === 'answer') ? 'sel' : '', hit.has(s.k) ? 'hit' : ''].join(' ');
        const dots = sims.map((q, i) => { const cx = x + 10 + (i % per) * 10, cy = y + th + 4 + Math.floor(i / per) * 10;
          return `<g data-act="open" data-t="sim" data-id="${e(q.id)}"><circle cx="${cx}" cy="${cy}" r="6" fill="transparent"/>${info.sims.has(q.id) ? `<circle cx="${cx}" cy="${cy}" r="5.6" fill="none" stroke="var(--text-primary)" stroke-width="1.6"/>` : ''}<circle cx="${cx}" cy="${cy}" r="3.6" class="${q.same_as ? '' : 'stripe'}" style="${q.same_as ? 'fill:none;stroke:var(--text-secondary);stroke-width:1.4' : ''}${q.error ? ';stroke:var(--critical);stroke-width:2' : ''}"/>
            <title>${e(`${q.id} · ${q.label || ''} · run ${q.run || 'not recorded'}${q.same_as ? ` · returned from ${q.same_as}, not run again` : ''}${q.error ? ' · no measurements: ' + q.error : ''}`)}</title></g>`; }).join('');
        out.push(`<g data-step="${s.k}">${EV.box(x, y, w, h, s.lane, ic + ' ' + e(short), `data-act="step" data-id="${s.k}"`, cls).replace('</g>', `<title>${e(text)}</title></g>`)}${dots}</g>`);
        if (prev) arrows.push(`<path class="edge" data-step="${s.k}" d="M${prev.cx},${prev.y2} C${prev.cx},${(prev.y2 + y) / 2} ${x + w / 2},${(prev.y2 + y) / 2} ${x + w / 2},${y - 2}" marker-end="url(#ev-ah)"/>`);
        prev = { cx: x + w / 2, y2: y + h }; y += h + 14;
      });
    });
    return `<svg width="${W}" height="${y + 6}" role="img" aria-label="Session flow: the steps of the session in time order, in the lane of whoever did each">${EV.arrowDefs()}${head}${lines.replace(/@H/g, y)}${arrows.join('')}${out.join('')}</svg>
      <p class="sm">A hollow dot is a simulation whose result was returned from an earlier one with the same settings and seed (not run again). Dashed orange edge: a refused step. Click a turn's band to fold it.</p>`;
  },

  // ---- View 2, the board of "What it needed to find out": one box per hypothesis, in the column of the turn it was stated
  // in (time runs left to right; hypotheses of one turn stand one under the other), and an arrow from each hypothesis
  // a later one follows from. An arrow says by its colour and its word which result led onward: a verdict "supported"
  // or a check that held (the colour of "held"), a verdict "refuted" or a check that failed (the colour of "failed"),
  // "inconclusive" or a void check (dashed, neutral), both kinds (dark). A dotted arrow is the weak link: the later
  // hypothesis names only the result table of the experiment that tested the earlier one. A box is tinted by how its
  // hypothesis ended and opens its test. In a running session the turn being written has one empty box.
  STATES: ['open', 'supported', 'refuted', 'inconclusive', 'dropped', 'ended without a verdict'],
  stCls: s => 'st-' + (s === 'ended without a verdict' ? 'ended' : s),
  mapEdges() {  // [from hypothesis id or 'brief', to hypothesis id, labels, the record ids it came from, kind]
    const M = EV.M, out = {};
    M.hyps.forEach(h => (h.follows || []).forEach(f => {
      const src = f === 'brief' ? { hyp: 'brief', label: 'brief' } : M.source(f) || { hyp: null, label: 'not recorded' };
      const from = src.hyp && src.hyp !== h.id && M.hypById[src.hyp] ? src.hyp : 'brief', key = from + '>' + h.id;
      (out[key] = out[key] || { from, to: h.id, labels: [], ids: [] }); out[key].ids.push(f);
      const lab = f === 'brief' ? 'brief' : M.voidIds.has(f) ? 'check void' : src.label; if (!out[key].labels.includes(lab)) out[key].labels.push(lab); }));
    const good = ['supported', 'check held'], bad = ['refuted', 'check failed'];
    return Object.values(out).map(x => { const g = x.labels.some(l => good.includes(l)), b = x.labels.some(l => bad.includes(l)), strong = x.labels.filter(l => l !== 'observation' && l !== 'brief' && l !== 'not recorded');
      return { ...x, strong, kind: x.from === 'brief' ? 'brief' : g && b ? 'mixed' : g ? 'good' : b ? 'bad' : strong.length ? 'neutral' : 'weak' }; });
  },
  viewMap() {
    const M = EV.M, S = EV.s, e = EV.e, info = EV.selInfo(), now = EV.liveNow(), slotTurn = now && now.phase === 'reply' && !now.mode ? now.turn : null;
    if (!M.hyps.length && slotTurn == null) return `<p class="sm">No hypothesis ${M.ended ? 'was stated in this session.' : 'has been stated yet.'}</p>`;
    const cols = [...new Set(M.hyps.map(h => h.turn).concat(slotTurn == null ? [] : [slotTurn]))].sort((a, b) => a - b), n = cols.length + 1;
    // the boxes are as wide as the page allows (132 to 250 px); a board wider than the page is drawn smaller, as a whole
    // where even 132 px do not fit, the boxes are small and hold the hypothesis's id and the sign of how it ended (its question is on hover and in the table below)
    const avail = Math.max(600, (document.getElementById('ev').clientWidth || 1400) - 64), fit = gx => Math.floor((avail - 12 - (n - 1) * gx) / n), small = fit(56) < 132, GX = small ? 40 : n > 6 ? 56 : 84, NW = small ? Math.max(58, Math.min(96, fit(40))) : Math.min(250, fit(GX)), NH = small ? 30 : 54, GY = small ? 8 : 12, pos = { brief: { x: 6, y: 8 } };
    const chars = Math.floor((NW - 14) / 6.7) * 2 - 6, rowsOf = t => M.hyps.filter(h => h.turn === t).length + (t === slotTurn ? 1 : 0);
    cols.forEach((t, i) => M.hyps.filter(h => h.turn === t).forEach((h, j) => { pos[h.id] = { x: 6 + (i + 1) * (NW + GX), y: 8 + j * (NH + GY) }; }));
    const edges = M.mapEdges = EV.mapEdges(), recorded = !M.hyps.length || M.hyps.some(h => h.follows);  // "not recorded" is said only of hypotheses that are there and name nothing
    const st = S.step == null ? null : EV_DATA.stateAt(M, S.step);
    const ringed = new Set(EV.repNow() ? M.claims.flatMap(c => c.hyps) : []), claimH = new Set(S.claim && M.claims[S.claim - 1] ? M.claims[S.claim - 1].hyps : []);  // the ring: once the final report is there
    const onPath = new Set(), hot = new Set();
    if (S.path) { const todo = [...ringed]; while (todo.length) { const id = todo.pop(); if (onPath.has(id)) continue; onPath.add(id);
      edges.filter(x => x.to === id).forEach(x => { hot.add(x.from + '>' + x.to); todo.push(x.from); }); } }
    const W = 12 + n * NW + (n - 1) * GX, H = 16 + Math.max(1, ...cols.map(rowsOf)) * (NH + GY);
    const MK = { good: 'ev-ag', bad: 'ev-ab' }, order = { weak: 0, brief: 1, neutral: 2, mixed: 3, good: 4, bad: 4 };
    // the arrows that carry a result arrive at their box one under the other, each with its sign just before the box
    const into = {}; edges.filter(x => x.strong.length && pos[x.from] && pos[x.to]).sort((p, q) => pos[p.from].y - pos[q.from].y || pos[p.from].x - pos[q.from].x).forEach(x => { (into[x.to] = into[x.to] || []).push(x); });
    const entry = x => { const l = into[x.to] || [], i = l.indexOf(x), gap = Math.min(13, (NH - 10) / Math.max(1, l.length)); return i < 0 ? 0 : (i - (l.length - 1) / 2) * gap; }, signsOut = [];
    const svgE = edges.slice().sort((p, q) => order[p.kind] - order[q.kind]).map(x => { const a = pos[x.from], b = pos[x.to]; if (!a || !b) return '';
      const x1 = a.x + NW, y1 = a.y + NH / 2, x2 = b.x - 2, y2 = b.y + NH / 2 + entry(x), k = Math.max(M.recStep[x.to] ?? 0, x.from === 'brief' ? 0 : M.recStep[x.from] ?? 0), isHot = hot.has(x.from + '>' + x.to);
      const SIGN = { supported: 'supported', refuted: 'refuted', inconclusive: 'inconclusive', 'check held': 'held', 'check failed': 'failed', 'check void': 'void' }, signs = x.strong.map(l => SIGN[l]).filter(Boolean), t = 0.62, bz = (a0, a1, a2, a3) => (1 - t) ** 3 * a0 + 3 * (1 - t) ** 2 * t * a1 + 3 * (1 - t) * t * t * a2 + t ** 3 * a3;
      const lx = x2 - 9 - signs.length * 7, ly = y2;
      if (signs.length) signsOut.push(`<g data-step="${k}" class="esign" data-edge="${e(x.from + '>' + x.to)}"><rect class="elbg" x="${lx - signs.length * 7 - 2}" y="${ly - 8}" width="${signs.length * 14 + 4}" height="16" rx="8"/>${signs.map((q, i) => EV.gks(q, lx - signs.length * 7 + i * 14 + 1, ly - 6, 12)).join('')}</g>`);
      const says = x.kind === 'weak' ? `${x.to} names only the result table of the experiment that tested ${x.from} (${x.ids.join(', ')})` : x.kind === 'brief' ? `${x.to} follows from the brief or the baseline (${x.ids.join(', ')})` : `${x.to} follows from ${x.from}: ${x.labels.join(', ')} (${x.ids.join(', ')})`;
      return `<g data-step="${k}" data-edge="${e(x.from + '>' + x.to)}" data-kind="${x.kind}"><path class="edge ${x.kind}${isHot ? ' hot' : ''}" d="M${x1},${y1} C${x1 + GX / 2},${y1} ${x2 - GX / 2 - (signs.length ? 14 : 0)},${y2} ${x2},${y2}" marker-end="url(#${isHot ? 'ev-ahot' : MK[x.kind] || 'ev-ah'})"/>
        <title>${e(says)}</title></g>`; }).join('');
    const brief = EV.box(6, 8, NW, NH, 'operator', small ? `<b>${EV.term('Brief', 'brief')}</b>` : `${EV_ICON.brief} <b>${EV.term('Brief', 'brief')}</b><br><small>and the baseline the harness ran</small>`, 'data-act="open" data-t="brief" data-id="brief"', onPath.has('brief') ? 'hit' : '');
    const nodes = M.hyps.map(h => { const p = pos[h.id], s = st ? st[h.id] || 'open' : h.state, label = EV.hshort(h), short = label.length > chars ? label.slice(0, chars - 2) + '…' : label;
      const cls = `${EV.stCls(s)}${info.hyps.has(h.id) ? ' sel' : ''}${claimH.has(h.id) || onPath.has(h.id) ? ' hit' : ''}`, T = h.tests.filter(q => EV.seen(M.testById[q].exp)).pop();  // a node opens the test of its hypothesis
      const word = ['supported', 'refuted', 'inconclusive'].includes(s) ? EV.verdictRes(s) : e(s === 'open' ? (M.ended ? 'not judged' : 'not judged yet') : s);
      return `<g data-step="${M.recStep[h.id] ?? 0}"${EV.freshAttr(h.id)} data-node="${h.id}">${ringed.has(h.id) ? `<rect class="ring" x="${p.x - 4}" y="${p.y - 4}" width="${NW + 8}" height="${NH + 8}" rx="9"/>` : ''}
        ${EV.box(p.x, p.y, NW, NH, 'model', small ? `<b>${h.id}</b> ${['supported', 'refuted', 'inconclusive'].includes(s) ? EV.gkey(s) : s === 'dropped' ? EV.gkey('dropped') : ''}` : `<b>${h.id}</b> · ${word}<br><small data-own="model">${e(short)}</small>`, T ? `data-act="open" data-t="test" data-id="${e(T)}"` : `data-act="open" data-t="hyp" data-id="${h.id}"`, cls).replace('</g>', `<title>${e(h.id + ': ' + h.text)}</title></g>`)}</g>`; }).join('');
    // a running session: the place of the next question, in the column of the turn that is being written
    const sx = slotTurn == null ? null : { x: 6 + (cols.indexOf(slotTurn) + 1) * (NW + GX), y: 8 + M.hyps.filter(h => h.turn === slotTurn).length * (NH + GY) };
    const slot = sx ? `<g id="map-next" data-slot="question"><rect class="bx slotbox" x="${sx.x}" y="${sx.y}" width="${NW}" height="${NH}" rx="6"/><foreignObject x="${sx.x + 2}" y="${sx.y}" width="${NW - 2}" height="${NH}"><div xmlns="http://www.w3.org/1999/xhtml" class="bt">${EV.nowDot()}<span class="mut">empty</span>${small ? '' : '<br><small>the next question, if this reply asks one</small>'}</div></foreignObject></g>` : '';
    const heads = `<text x="6" y="${H + 4}">start</text>` + cols.map((t, i) => `<text x="${6 + (i + 1) * (NW + GX)}" y="${H + 4}">turn ${t}${now && now.turn === t ? ' · now' : ''}</text>`).join('');
    const defs = `${EV.arrowDefs()}<defs>${[['ev-ag', '--good'], ['ev-ab', '--critical']].map(([id, c]) => `<marker id="${id}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(${c})"/></marker>`).join('')}</defs>`;
    const kinds = new Set(edges.filter(x => EV.seen(x.to)).map(x => x.kind)), key = (k, cls, text) => (kinds.has(k) ? `<span class="mk" data-k="${k}"><svg width="30" height="10" style="display:inline;vertical-align:0"><path class="edge ${cls}" d="M1,5 H28"/></svg> ${text}</span>` : '');
    return `<div class="ev-map" data-cols="${n}"${small ? ' data-small="1"' : ''}><svg viewBox="0 0 ${W} ${H + 10}" width="${W}" height="${H + 10}" style="max-width:100%;height:auto" role="img" aria-label="The hypotheses by the turn they were stated in, and which follows from which">${defs}${svgE}${brief}${nodes}${slot}${signsOut.join('')}${heads}</svg></div>
      <p class="sm map-key">${recorded ? `<span class="mk"><b>an arrow</b>: the later hypothesis names that result as what it follows from; the sign on it is that result</span>${key('good', 'good', 'supported, or its check held')}${key('bad', 'bad', 'refuted, or its check failed')}${key('mixed', 'mixed', 'both')}${key('neutral', 'neutral', 'inconclusive, or a void check')}${key('weak', 'weak', 'it names only the result table of that experiment')}`
        : `<span class="mk">What each hypothesis follows from: ${EV.nr} (this session was recorded before that field existed), so the board has no arrows.</span>`}
        ${EV.STATES.filter(q => M.hyps.some(h => (st ? st[h.id] || 'open' : h.state) === q) && q !== 'open').map(q => `<span class="mk"><svg width="12" height="12" style="display:inline;vertical-align:-1px"><rect class="bx ${EV.stCls(q)}" x="1" y="1" width="10" height="10" rx="3"/></svg> ${q}</span>`).join('')}${ringed.size ? '<span class="mk">◯ ring: cited by the final report\'s claims</span>' : ''}${small ? '<span class="mk">many turns: a box holds its hypothesis\'s name and how it ended; its question is on hover and in the table below</span>' : ''}</p>`;
  },
});
