// The sweep as a heat map over two chosen knobs (Operator tab): in each cell the best value of the target among the
// sweep's rows that meet the conditions. The colour scale runs over all cells or, by the switch above the map, from 99%
// of the best value to the best (one scale at a time; the darkest step is the best). Across, where the step between
// neighbouring values changes there is a small gap and the value is printed, and under the axis each stretch is named
// with its step, worked out from the values. The session's simulations are numbered circles; circles that would overlap
// are one dark mark with their count, and a click lists them under the map. The best cell's label stands above the map.
// ======================================================================================================
Object.assign(EV, {
  // the stretches of an axis: runs of columns that stand the same step from their left neighbour
  stretches(X, num) {
    if (!num || X.length < 3) return [{ a: 0, b: X.length - 1, step: null }];
    const d = X.map((v, i) => (i ? +(+v - +X[i - 1]).toPrecision(6) : null)), out = [{ a: 0, b: 1, step: d[1] }];
    for (let i = 2; i < X.length; i++) { const g = out[out.length - 1]; if (d[i] === g.step) g.b = i; else out.push({ a: i, b: i, step: d[i] }); }
    return out;
  },
  heat(rows, goal) {
    const M = EV.M, S = EV.s, e = EV.e, [kx, ky] = S.heat, tg = goal.target, max = goal.direction !== 'min', near = S.heatRange === 'near';
    const conds = (goal.conditions || []).map(c => c.match(/^\s*(\w+)\s*(<=|>=|<|>|==)\s*([-\d.eE]+)\s*$/)).filter(Boolean);
    const meets = r => conds.every(([, k, op, v]) => { const a = +r[k], b = +v; return op === '<=' ? a <= b : op === '>=' ? a >= b : op === '<' ? a < b : op === '>' ? a > b : a === b; });
    const isNum = k => rows.every(r => r[k] !== '' && !isNaN(+r[k])), sort = k => [...new Set(rows.map(r => r[k]))].sort((a, b) => (isNum(k) ? +a - +b : a < b ? -1 : 1));
    const X = sort(kx), Y = sort(ky).reverse(), cell = {};
    rows.forEach(r => { if (r.error || !meets(r) || r[tg] === '') return; const key = r[kx] + '|' + r[ky], c = cell[key];
      if (!c || (max ? +r[tg] > +c[tg] : +r[tg] < +c[tg])) cell[key] = r; });
    const vals = Object.values(cell).map(r => +r[tg]), lo = Math.min(...vals), hi = Math.max(...vals), B = max ? hi : lo, [u, f] = EV.unit(tg);
    // the scale: from a (palest) to b (darkest, the best); "within 1%": from 99% of the best value to the best
    const from = near ? (max ? 0.99 * B : 1.01 * B) : max ? lo : hi, within = vals.filter(v => (max ? v >= 0.99 * B : v <= 1.01 * B)).length;
    const ramp = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'], col = v => ramp[B === from ? 6 : Math.max(0, Math.min(6, Math.floor(7 * (v - from) / (B - from) * (1 - 1e-9))))];
    const G = EV.stretches(X, isNum(kx)), GAP = 6, cw = Math.max(7, Math.floor((820 - GAP * (G.length - 1)) / X.length)), ch = 34, L = 74, T = 24, gi = i => G.findIndex(g => i >= g.a && i <= g.b), xOf = i => L + i * cw + GAP * gi(i);
    const mapW = xOf(X.length - 1) + cw - L, base = T + ch * Y.length, W = L + mapW + 10, H = base + 86;
    const best = Object.values(cell).sort((a, b) => (max ? b[tg] - a[tg] : a[tg] - b[tg]))[0];
    const fmt = v => (+f(+v).toPrecision(6)).toLocaleString('en-US') + (u ? ' ' + u : '');
    let svg = `<defs><pattern id="ev-hatch" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="var(--surface-0)"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--grid)" stroke-width="2"/></pattern></defs>`;
    Y.forEach((yv, j) => { svg += `<text x="${L - 6}" y="${T + j * ch + ch / 2 + 4}" text-anchor="end">${e(yv)}</text>`;
      X.forEach((xv, i) => { const r = cell[xv + '|' + yv], x = xOf(i), y = T + j * ch;
        svg += `<rect class="cell" data-v="${r ? +r[tg] : ''}" x="${x}" y="${y}" width="${cw}" height="${ch}" fill="${r ? col(+r[tg]) : 'url(#ev-hatch)'}"><title>${e(`${kx} ${xv} · ${ky} ${yv}: ${r ? `best ${tg} ${fmt(r[tg])} (${Object.keys(r).filter(k => !['i', kx, ky, tg].includes(k) && M.brief && M.brief.knobs && k in M.brief.knobs).map(k => k + ' ' + r[k]).join(', ')})` : 'no simulation of the sweep meets ' + (goal.conditions || []).join(' and ')}`)}</title></rect>`;
        if (r && r === best) svg += `<rect id="heat-best" x="${x - 1}" y="${y - 1}" width="${cw + 2}" height="${ch + 2}" fill="none" stroke="var(--text-primary)" stroke-width="2.5"/><path d="M${x + cw / 2},${T - 9} V${y - 1}" stroke="var(--text-primary)" stroke-width="1.2"/><text id="heat-best-label" x="${x + cw / 2}" y="${T - 12}" text-anchor="middle" style="font-weight:700;fill:var(--text-primary)">best</text>`; }); });
    // across: the value where a stretch ends (and inside a long stretch every tenth), printed upright; under them each stretch with its step
    const tick = i => `<text class="hx" data-i="${i}" x="${xOf(i) + cw / 2 + 4}" y="${base + 6}" text-anchor="end" transform="rotate(-90 ${xOf(i) + cw / 2 + 4} ${base + 6})">${e(X[i])}</text>`;
    const say = g => (g.step == null ? '' : 'by ' + String(g.step)), steps = G.map((g, k) => `${k ? 'to' : e(X[0]) + ' to'} ${e(X[g.b])} ${say(g)}`).join(' · ');
    G.forEach((g, k) => { const x1 = xOf(g.a), x2 = xOf(g.b) + cw, wide = x2 - x1 >= say(g).length * 6.4 + 6;
      svg += (k === 0 ? tick(0) : '') + (g.b > 0 ? tick(g.b) : '') + (G.length === 1 && X.length <= 24 ? X.map((v, i) => (i && i < g.b ? tick(i) : '')).join('') : '');
      if (g.b - g.a >= 19) for (let i = g.a + 9; i < g.b - 4; i += 10) svg += tick(i);
      if (g.step != null) svg += `<path class="hs" data-a="${g.a}" data-b="${g.b}" data-s="${g.step}" d="M${x1 + 1},${base + 44} v4 H${x2 - 1} v-4" fill="none" stroke="var(--text-muted)"/>${wide ? `<text x="${(x1 + x2) / 2}" y="${base + 60}" text-anchor="middle">${e(say(g))}</text>` : ''}`; });
    svg += `<text x="${L + mapW / 2}" y="${H - 6}" text-anchor="middle" style="fill:var(--text-primary)">${e(kx)}</text><text x="10" y="${T + (ch * Y.length) / 2}" transform="rotate(-90 10 ${T + (ch * Y.length) / 2})" text-anchor="middle" style="fill:var(--text-primary)">${e(ky)}</text>`;
    // the session's simulations: where they stand on the two axes; those that would overlap are one mark with their count
    const where = (k, cats, v, at) => { if (v == null) return null; const i = cats.indexOf(String(v)); if (i >= 0) return at(i); if (!isNum(k)) return null;
      const n = cats.map(Number), j = n.findIndex(q => q > +v); if (j <= 0) return null; return at(j - 1) + (at(j) - at(j - 1)) * (+v - n[j - 1]) / (n[j] - n[j - 1]); };
    const pts = [], Yup = Y.slice().reverse();
    M.sims.filter(s => !s.same_as && s.metrics).forEach((s, n) => { const x = where(kx, X, s.params[kx], i => xOf(i) + cw / 2), y = where(ky, Yup, s.params[ky], j => base - j * ch - ch / 2);
      if (x == null || y == null) return; const p = pts.find(q => Math.hypot(q.x - x, q.y - y) < 22); if (p) p.sims.push([n + 1, s]); else pts.push({ x, y, sims: [[n + 1, s]] }); });
    const line = ([n, s]) => `${n}: ${s.id} · ${s.label} · ${kx} ${s.params[kx]} · ${ky} ${s.params[ky]} · ${tg} ${fmt(s.metrics[tg])}`, key = p => p.sims.map(q => q[1].id).join(',');
    pts.forEach(p => { const one = p.sims.length === 1, s = p.sims[0][1];
      svg += one ? `<g class="hm" data-act="open" data-t="sim" data-id="${e(s.id)}"><circle cx="${p.x}" cy="${p.y}" r="8" fill="var(--surface-1)" stroke="var(--by-simulator)" stroke-width="2"/><text x="${p.x}" y="${p.y + 4}" text-anchor="middle" style="font-weight:700;fill:var(--text-primary)">${p.sims[0][0]}</text><title>${e(line(p.sims[0]))}</title></g>`
        : `<g class="hm many${S.heatPick === key(p) ? ' on' : ''}" data-act="heatpick" data-id="${e(key(p))}" data-n="${p.sims.length}"><circle cx="${p.x}" cy="${p.y}" r="10" fill="var(--text-primary)" stroke="var(--by-simulator)" stroke-width="2"/><text x="${p.x}" y="${p.y + 4}" text-anchor="middle" style="font-weight:700;fill:var(--surface-1)">${p.sims.length}</text><title>${e(p.sims.length + ' simulations of this session here: ' + p.sims.map(q => q[0]).join(', '))}</title></g>`; });
    const picked = pts.find(p => p.sims.length > 1 && key(p) === S.heatPick), b = (id, text) => `<button data-act="heatrange" data-id="${id}" class="${(near ? 'near' : 'all') === id ? 'on' : ''}">${text}</button>`;
    return `<p class="sm" id="heat-range" style="margin-bottom:6px">colour range: ${b('all', 'all cells')} ${b('near', 'within 1% of the best')}</p>
      <svg class="heat" id="heat" width="${W}" height="${H}" role="img" aria-label="Sweep heat map" data-range="${near ? 'near' : 'all'}" data-cells="${X.length * Y.length}" data-meet="${vals.length}" data-lo="${f(lo)}" data-hi="${f(hi)}" data-within="${within}" style="max-width:100%">${svg}</svg>
      <p class="sm" id="heat-list">${picked ? `${picked.sims.length} of this session's simulations stand at this place: ${picked.sims.map(q => `<a data-act="open" data-t="sim" data-id="${e(q[1].id)}">${e(line(q))}</a>`).join(' · ')}` : ''}</p>
      <p class="sm" id="heat-steps">${isNum(kx) && G.length > 1 ? `${e(kx)}, from the sweep's own values: ${steps}. A gap stands where the step changes.` : ''}</p>
      <p class="sm" id="heat-key">colour: the best ${e(tg)} in the cell over the other knobs, among sweep rows that meet ${e((goal.conditions || []).join(' and ') || 'no condition')} · <span style="display:inline-flex;vertical-align:middle">${ramp.map(c => `<i style="display:inline-block;width:18px;height:10px;background:${c}"></i>`).join('')}</span> ${fmt(from)} → ${fmt(B)}${near ? ` (99% of the best value to the best); the palest step also holds the ${vals.length - within} cells below that` : ''}
        · hatched: no row meets the conditions · numbered circles: this session's simulations in order · a dark circle: several of them at one place, with their count · outlined: the sweep's best cell</p>`;
  },
});
EV.act = Object.assign(EV.act || {}, { heatrange(id) { EV.s.heatRange = id; EV.draw(); }, heatpick(id) { EV.s.heatPick = EV.s.heatPick === id ? null : id; EV.draw(); } });
