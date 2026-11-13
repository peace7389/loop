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
          return `<g data-act="open" data-t="sim" data-id="${e(q.id)}"><circle cx="${cx}" cy="${cy}" r="6" fill="transparent"/>${info.sims.has(q.id) ? `<circle cx="${cx}" cy="${cy}" r="5.6" fill="none" stroke="var(--text-primary)" stroke-width="1.6"/>` : ''}<circle cx="${cx}" cy="${cy}" r="3.6" class="${q.same_as ? '' : 'stripe'}" style="${q.same_as ? 'fill:none;stroke:var(--by-simulator);stroke-width:1.4' : ''}${q.error ? ';stroke:var(--critical);stroke-width:2' : ''}"/>
            <title>${e(`${q.id} · ${q.label || ''} · run ${q.run || 'not recorded'}${q.same_as ? ` · returned from ${q.same_as}, not run again` : ''}${q.error ? ' · no measurements: ' + q.error : ''}`)}</title></g>`; }).join('');
        out.push(`<g data-step="${s.k}">${EV.box(x, y, w, h, s.lane, ic + ' ' + e(short), `data-act="step" data-id="${s.k}"`, cls).replace('</g>', `<title>${e(text)}</title></g>`)}${dots}</g>`);
        if (prev) arrows.push(`<path class="edge" data-step="${s.k}" d="M${prev.cx},${prev.y2} C${prev.cx},${(prev.y2 + y) / 2} ${x + w / 2},${(prev.y2 + y) / 2} ${x + w / 2},${y - 2}" marker-end="url(#ev-ah)"/>`);
        prev = { cx: x + w / 2, y2: y + h }; y += h + 14;
      });
    });
    return `<svg width="${W}" height="${y + 6}" role="img" aria-label="Session flow: the steps of the session in time order, in the lane of whoever did each">${EV.arrowDefs()}${head}${lines.replace(/@H/g, y)}${arrows.join('')}${out.join('')}</svg>
      <p class="sm">A hollow dot is a simulation whose result was returned from an earlier one with the same settings and seed (not run again). Dashed orange edge: a refused step. Click a turn's band to fold it.</p>`;
  },

  // ---- View 2: one node per hypothesis, left to right by the turn it was stated in, arrows from what it follows from
  STATES: ['open', 'supported', 'refuted', 'inconclusive', 'dropped', 'ended without a verdict'],
  stCls: s => 'st-' + (s === 'ended without a verdict' ? 'ended' : s),
  mapEdges() {  // [from hypothesis id or 'brief', to hypothesis id, label, the record ids it came from]
    const M = EV.M, out = {};
    M.hyps.forEach(h => (h.follows || []).forEach(f => {
      const src = f === 'brief' ? { hyp: 'brief', label: 'brief' } : M.source(f) || { hyp: null, label: 'not recorded' };
      const from = src.hyp && src.hyp !== h.id && M.hypById[src.hyp] ? src.hyp : 'brief', key = from + '>' + h.id;
      (out[key] = out[key] || { from, to: h.id, labels: [], ids: [] }); out[key].ids.push(f);
      const lab = f === 'brief' ? 'brief' : src.label; if (!out[key].labels.includes(lab)) out[key].labels.push(lab); }));
    return Object.values(out);
  },
  viewMap() {
    const M = EV.M, S = EV.s, e = EV.e, info = EV.selInfo();
    if (!M.hyps.length) return `<p class="sm">No hypothesis ${M.ended ? 'was stated in this session.' : 'has been stated yet.'}</p>`;
    const NW = 132, NH = 50, GX = 124, GY = 16, cols = [...new Set(M.hyps.map(h => h.turn))].sort((a, b) => a - b), pos = { brief: { x: 6, y: 8 } };
    cols.forEach((t, i) => M.hyps.filter(h => h.turn === t).forEach((h, j) => { pos[h.id] = { x: 6 + (i + 1) * (NW + GX), y: 8 + j * (NH + GY) }; }));
    const edges = M.mapEdges = EV.mapEdges(), recorded = M.hyps.some(h => h.follows);
    const st = S.step == null ? null : EV_DATA.stateAt(M, S.step);
    const ringed = new Set(M.claims.flatMap(c => c.hyps)), claimH = new Set(S.claim && M.claims[S.claim - 1] ? M.claims[S.claim - 1].hyps : []);
    const onPath = new Set(), hot = new Set();
    if (S.path) { const todo = [...ringed]; while (todo.length) { const id = todo.pop(); if (onPath.has(id)) continue; onPath.add(id);
      edges.filter(x => x.to === id).forEach(x => { hot.add(x.from + '>' + x.to); todo.push(x.from); }); } }
    const W = 6 + (cols.length + 1) * (NW + GX), H = 16 + Math.max(1, ...cols.map(t => M.hyps.filter(h => h.turn === t).length)) * (NH + GY);
    const svgE = edges.map(x => { const a = pos[x.from], b = pos[x.to]; if (!a || !b) return '';
      const x1 = a.x + NW, y1 = a.y + NH / 2, x2 = b.x - 2, y2 = b.y + NH / 2, k = Math.max(M.recStep[x.to] ?? 0, x.from === 'brief' ? 0 : M.recStep[x.from] ?? 0), isHot = hot.has(x.from + '>' + x.to);
      const lab = x.labels.join(', '), short = lab.length > 24 ? lab.slice(0, 22) + '…' : lab, t = 0.6, bz = (a0, a1, a2, a3) => (1 - t) ** 3 * a0 + 3 * (1 - t) ** 2 * t * a1 + 3 * (1 - t) * t * t * a2 + t ** 3 * a3;
      const lx = bz(x1, x1 + GX / 2, x2 - GX / 2, x2), ly = bz(y1, y1, y2, y2);
      return `<g data-step="${k}"><path class="edge${isHot ? ' hot' : ''}" d="M${x1},${y1} C${x1 + GX / 2},${y1} ${x2 - GX / 2},${y2} ${x2},${y2}" marker-end="url(#${isHot ? 'ev-ahot' : 'ev-ah'})"/>
        <text x="${lx}" y="${ly - 3}" text-anchor="middle" style="font-size:var(--f-note);paint-order:stroke;stroke:var(--surface-1);stroke-width:3px">${e(short)}</text><title>${e(x.to + ' follows from ' + x.ids.join(', ') + ' (' + lab + ')')}</title></g>`; }).join('');
    const brief = EV.box(6, 8, NW, NH, 'operator', `${EV_ICON.brief} <b>${EV.term('Brief', 'brief')}</b><br><small>and the baseline the harness ran</small>`, 'data-act="open" data-t="brief" data-id="brief"', onPath.has('brief') ? 'hit' : '');
    const nodes = M.hyps.map(h => { const p = pos[h.id], s = st ? st[h.id] || 'open' : h.state, label = EV.hshort(h), short = label.length > 54 ? label.slice(0, 52) + '…' : label;
      const cls = `${EV.stCls(s)}${info.hyps.has(h.id) ? ' sel' : ''}${claimH.has(h.id) || onPath.has(h.id) ? ' hit' : ''}`, T = h.tests.filter(q => EV.seen(M.testById[q].exp)).pop();  // a node opens the test of its hypothesis
      return `<g data-step="${M.recStep[h.id] ?? 0}">${ringed.has(h.id) ? `<rect class="ring" x="${p.x - 4}" y="${p.y - 4}" width="${NW + 8}" height="${NH + 8}" rx="9"/>` : ''}
        ${EV.box(p.x, p.y, NW, NH, 'model', `${EV_ICON.hypothesis} <b>${h.id}</b> · ${e(s)}<br><small>${e(short)}</small>`, T ? `data-act="open" data-t="test" data-id="${e(T)}"` : `data-act="open" data-t="hyp" data-id="${h.id}"`, cls).replace('</g>', `<title>${e(h.id + ': ' + h.text)}</title></g>`)}</g>`; }).join('');
    const heads = cols.map((t, i) => `<text x="${6 + (i + 1) * (NW + GX)}" y="${H + 4}">${EV_ICON.turn} turn ${t}</text>`).join('');
    return `<div class="ev-scroll ev-map"><svg width="${W}" height="${H + 10}" role="img" aria-label="Hypothesis map">${EV.arrowDefs()}${svgE}${brief}${nodes}${heads}</svg></div>
      <p class="sm">${EV.STATES.map(s => `<span style="white-space:nowrap;margin-right:10px"><svg width="12" height="12" style="display:inline;vertical-align:-1px"><rect class="bx ${EV.stCls(s)}" x="1" y="1" width="10" height="10" rx="3"/></svg> ${s}</span>`).join('')}
        <span style="white-space:nowrap">◯ ring: cited by the final report's claims</span>${recorded ? '' : ` · What each hypothesis follows from: ${EV.nr} (this session was recorded before that field existed), so the map has no arrows.`}</p>`;
  },
});
