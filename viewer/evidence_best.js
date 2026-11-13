// "Best so far": the brief's target measure over the simulations in the order they ran. One dot per simulation (filled:
// it meets the brief's conditions; hollow: it does not), a step line for the best value so far among those that do, a
// ring at the recommended settings, a thin mark at each turn; with the operator columns on, a line at the best row of
// the sweep, and behind the session's line a grey band: what choosing at random from the sweep's first grid gives
// (evidence_random.js). Plain SVG, drawn by this script, so it prints and works without the chart library. The Compare
// tab draws the step lines of several sessions with the same code.
// ======================================================================================================
Object.assign(EV, {
  // the brief's goal as the chart needs it (null for an open goal: the model chooses it)
  goalOf(brief) {
    const g = brief && brief.goal; if (!g || !g.target || !g.target.measure) return null;
    const conds = (g.conditions || []).map(c => String(c).match(/^\s*(\w+)\s*(<=|>=|<|>|==)\s*([-\d.eE]+)\s*$/)).filter(Boolean).map(([, k, op, v]) => ({ k, op, v: +v }));
    return { target: g.target.measure, max: g.target.direction !== 'min', conds, text: (g.conditions || []).join(' and ') };
  },
  flowCol: k => (/^udp|band0/.test(k) ? 'var(--series-1)' : /^tcp|band1/.test(k) ? 'var(--series-2)' : 'var(--text-secondary)'),  // the colour of a measure: its flow's
  meets: (m, conds) => conds.every(({ k, op, v }) => { const a = m[k]; return typeof a === 'number' && (op === '<=' ? a <= v : op === '>=' ? a >= v : op === '<' ? a < v : op === '>' ? a > v : a === v); }),
  // the simulations that ran, in order (one returned from an earlier one did not run), each with the target's value,
  // whether it meets the conditions and the best so far; rec: the one run at the recommended settings; last: the one
  // after which the best valid result no longer improved
  bestData(M) {
    if (M._best !== undefined) return M._best; const g = EV.goalOf(M.brief); if (!g) return (M._best = null);
    const pts = M.sims.filter(s => !s.same_as && s.metrics && typeof s.metrics[g.target] === 'number').map((s, i) => ({ n: i + 1, s, v: s.metrics[g.target], ok: EV.meets(s.metrics, g.conds), turn: s.turn }));
    let best = null; pts.forEach(p => { if (p.ok && (best == null || (g.max ? p.v > best : p.v < best))) { best = p.v; p.improves = true; } p.best = best; });
    const rec = M.report && M.report.recommendation, same = (a, b) => (typeof a === 'number' || typeof b === 'number' ? Number(a) === Number(b) : String(a) === String(b));
    const at = rec && typeof rec === 'object' ? pts.find(p => Object.entries(rec).every(([k, v]) => k in p.s.params && same(p.s.params[k], v))) : null;
    return (M._best = { g, pts, best, rec: at || null, last: [...pts].reverse().find(p => p.improves) || null });
  },
  spread(labels, gap) {  // labels at nearly the same height are moved apart, in order: [{ y }] -> the same, y adjusted
    labels.sort((p, q) => p.y - q.y).forEach((l, i, a) => { if (i && l.y < a[i - 1].y + gap) l.y = a[i - 1].y + gap; }); return labels;
  },
  ticks(lo, hi, n) {  // round axis values between lo and hi
    const span = hi - lo || Math.abs(hi) || 1, raw = span / n, p = Math.pow(10, Math.floor(Math.log10(raw))), step = [1, 2, 2.5, 5, 10].map(m => m * p).find(s => s >= raw), out = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9 * span; v += step) out.push(+v.toPrecision(12)); return out;
  },
  // series: [{ d: bestData, name, color }]; o.dots: draw the simulations of the (one) series; o.zoom: the scale covers
  // the best-so-far lines only; o.line: [value, label] a horizontal line (the sweep's best row); o.seen: record id -> shown at this replay step
  // the room a picture has in the left column of a session's page, worked out from the page's width (the columns are in index.html: .ev-main)
  leftW() { const R = document.getElementById('ev').clientWidth - 40; return Math.max(380, Math.floor((window.innerWidth <= 1100 ? R : Math.max(450, (R - 12) * 0.45)) - 34)); },
  bestSvg(series, o) {
    const e = EV.e, g = series[0].d.g, [u, f] = EV.unit(g.target), W = o.dots ? EV.leftW() : 760, H = 250, L = 62, R = o.dots ? 18 : 56, T = 20, B = 34, seen = o.seen || (() => true);
    const N = Math.max(...series.map(q => q.d.pts.length), 2), X = n => L + (n - 1) / (N - 1) * (W - L - R);
    const vals = series.flatMap(q => (o.dots && !o.zoom ? q.d.pts.map(p => p.v) : q.d.pts.filter(p => p.best != null).map(p => p.best))).concat(o.line && (o.zoom || !o.dots) ? [o.line[0]] : []).concat((o.bands || []).flatMap(b => (o.dots && !o.zoom ? b.B.p10.concat(b.B.p90) : o.dots ? [] : [b.B.p50[b.B.n - 1], b.B.p90[b.B.n - 1]]).filter(v => v != null))).map(f);
    if (!vals.length) return `<p class="sm">No simulation meets the brief's conditions${o.dots ? ', so there is no best-so-far line' : ''}.</p>`;
    let lo = Math.min(...vals), hi = Math.max(...vals); const pad = (hi - lo || Math.abs(hi) * 0.01 || 1) * 0.12; lo -= pad; hi += pad;
    const Y = v => T + (hi - f(v)) / (hi - lo) * (H - T - B), tk = EV.ticks(lo, hi, 5), fmt = v => (+v.toPrecision(6)).toLocaleString('en-US');
    let s = `<defs><clipPath id="ev-bc"><rect x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}"/></clipPath></defs>`;
    tk.forEach(v => { const y = T + (hi - v) / (hi - lo) * (H - T - B); s += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" stroke="var(--grid)"/><text x="${L - 6}" y="${y + 4}" text-anchor="end">${fmt(v)}</text>`; });
    for (let n = 1; n <= N; n += Math.max(1, Math.ceil(N / 10))) s += `<text x="${X(n)}" y="${H - B + 14}" text-anchor="middle">${n}</text>`;
    s += `<text x="${(L + W - R) / 2}" y="${H - 4}" text-anchor="middle">simulations, in the order they ran</text><text x="12" y="${T - 8}">${e(TH_DATA.PLAIN[g.target] || g.target)}${u ? ', ' + u : ''}</text>`;
    if (o.dots) { let turn = null; series[0].d.pts.forEach(p => { if (p.turn !== turn) { turn = p.turn; const x = X(p.n) - (p.n > 1 ? (X(2) - X(1)) / 2 : 0);
      s += `<g data-step="${EV.M.recStep[p.s.id] ?? 0}"><line x1="${x}" x2="${x}" y1="${T}" y2="${H - B}" stroke="var(--border)" stroke-dasharray="2 3"/>${turn ? `<text x="${x + 3}" y="${T + 9}" style="font-size:var(--f-note)">turn ${turn}</text>` : ''}</g>`; } }); }
    (o.bands || []).forEach(b => { s += EV.randomSvg(b.B, X, Y, b.offset || 0, N); });  // behind the lines: the random method (operator columns)
    if (o.line) s += `<line x1="${L}" x2="${W - R}" y1="${Y(o.line[0])}" y2="${Y(o.line[0])}" stroke="var(--by-operator)" stroke-width="1.5" stroke-dasharray="6 4" clip-path="url(#ev-bc)"/><text x="${W - R - 4}" y="${Y(o.line[0]) - 4}" text-anchor="end" style="fill:var(--text-primary)">${e(o.line[1])}: ${fmt(f(o.line[0]))}</text>`;
    const ends = [];
    series.forEach(q => { const ps = q.d.pts.filter(p => p.best != null && seen(p.s.id)); if (!ps.length) return;
      const d = ps.map((p, i) => (i ? `H${X(p.n)} V${Y(p.best)}` : `M${X(p.n)},${Y(p.best)}`)).join(' ') + (o.dots ? '' : ` H${X(q.d.pts.length)}`);
      s += `<path d="${d}" fill="none" stroke="${q.color}" stroke-width="2" clip-path="url(#ev-bc)"><title>${e(q.name)}: the best so far among simulations that meet the conditions</title></path>`;
      if (!o.dots) ends.push({ x: X(q.d.pts.length) + 4, y: Y(ps[ps.length - 1].best) + 4, q }); });
    EV.spread(ends, 12).forEach(l => { s += `<circle cx="${l.x + 3}" cy="${l.y - 4}" r="3.5" fill="${l.q.color}"/><text x="${l.x + 10}" y="${l.y}" style="font-weight:600;fill:var(--text-primary)">${e(l.q.name)}</text>`; });
    if (o.dots) { const q = series[0], col = EV.flowCol(g.target);
      s += q.d.pts.map(p => `<g data-act="open" data-t="sim" data-id="${e(p.s.id)}" data-step="${EV.M.recStep[p.s.id] ?? 0}" clip-path="url(#ev-bc)"><circle cx="${X(p.n)}" cy="${Y(p.v)}" r="8" fill="transparent"/>
        <circle cx="${X(p.n)}" cy="${Y(p.v)}" r="4" fill="${p.ok ? col : 'var(--surface-1)'}" stroke="${p.ok ? 'var(--surface-1)' : col}" stroke-width="${p.ok ? 1.5 : 1.8}"/><title>${e(`${p.n}: ${p.s.id} · ${p.s.label || ''} · ${fmt(f(p.v))} ${u} · ${p.ok ? 'meets' : 'does not meet'} the brief's conditions`)}</title></g>`).join('');
      if (q.d.rec) { const p = q.d.rec, k = EV.M.repRec ? EV.M.recStep[EV.M.repRec.id] ?? 0 : 0; s += `<g data-step="${k}"><circle cx="${X(p.n)}" cy="${Y(p.v)}" r="9" fill="none" stroke="var(--text-primary)" stroke-width="2"/><text x="${X(p.n) + (p.n > N * 0.8 ? -13 : 13)}" y="${Y(p.v) + 16}" text-anchor="${p.n > N * 0.8 ? 'end' : 'start'}" style="fill:var(--text-primary);font-weight:600">the recommended settings</text></g>`; } }
    return `<svg viewBox="0 0 ${W} ${H}" width="${o.dots ? W : '100%'}" style="max-width:${o.dots ? '100%' : '900px'}" role="img" aria-label="Best so far: ${e(g.target)} over the simulations in the order they ran">${s}</svg>`;
  },

  bestCard() {
    const M = EV.M, S = EV.s, e = EV.e, d = EV.bestData(M), sc = EV.files.score;
    if (!d) return `<div class="ev-card" id="s-best"><h2>Best so far</h2><p class="sm">${M.brief ? (M.brief.goal && M.brief.goal.kind === 'open' ? 'Not applicable: the goal is chosen by the model.' : `the brief's goal: ${EV.nr}`) : `the brief: ${EV.nr}`}</p></div>`;
    const [u, f] = EV.unit(d.g.target), fmt = v => (+f(v).toPrecision(7)).toLocaleString('en-US') + (u ? ' ' + u : ''), n = d.pts.length, seen = id => EV.seen(id);
    const line = S.op && sc && sc.best_row && sc.best_row[d.g.target] != null ? [Number(sc.best_row[d.g.target]), 'best row of the sweep'] : null;
    const rnd = line ? EV.randomOf(M) : null, bands = rnd && rnd.band ? [{ B: rnd.band, offset: rnd.offset }] : [];  // the random method: only with the operator columns on and a scored session
    const said = !d.pts.length ? 'No simulation has run yet.' : d.best == null ? 'No simulation meets the brief\'s conditions.' : `Best result that meets the conditions: <b>${fmt(d.best)}</b>, first reached by ${EV.link(d.last.s.id)} (simulation ${d.last.n} of ${n}).`;
    const rec = !M.report ? '' : d.rec ? ` The recommended settings were run as ${EV.link(d.rec.s.id)}: <b>${fmt(d.rec.v)}</b>${d.rec.ok ? '' : ', which does not meet the conditions'}.` : ' The recommended settings were not simulated in this session.';
    return `<div class="ev-card" id="s-best"><h2>Best so far <small>${e(d.g.max ? 'largest' : 'smallest')} ${e(d.g.target)}${d.g.text ? ' while ' + e(d.g.text) : ''} · one dot per ${EV.term('Simulation', 'simulation')}</small></h2>
      ${d.pts.length ? EV.bestSvg([{ d, name: M.id, color: 'var(--text-primary)' }], { dots: true, zoom: !!S.zoom, line, seen, bands }) : ''}
      <p class="sm">${EV.dot(1, EV.flowCol(d.g.target))}meets the brief's conditions · ${EV.dot(0, EV.flowCol(d.g.target))}does not · <b>—</b> the best so far among those that do · <i class="gk"><svg viewBox="0 0 12 12"><circle cx="6" cy="6" r="4.8" fill="none" stroke="currentColor" stroke-width="1.4"/></svg></i>the recommended settings${line ? ' · <span style="color:var(--by-operator)">- -</span> the best row of the sweep (operator column)' : ''}${bands.length ? EV.randomLegend(rnd) : ''}
        · <button data-act="zoom">${S.zoom ? 'show every simulation' : 'zoom on the best-so-far line'}</button></p>
      <p class="sm" data-step="${M.steps.length - 1}">${said}${rec}</p>${rnd && rnd.band && EV.s.step == null ? EV.randomSentence(rnd, d) : rnd && rnd.loading ? '<p class="sm">Reading the sweep table for the comparison with random choice…</p>' : rnd && rnd.none ? `<p class="sm" id="rnd-none">The comparison with random choice: ${EV.nr} (${EV.e(rnd.none)} is missing).</p>` : ''}</div>`;
  },
});
EV.act = Object.assign(EV.act || {}, { zoom() { EV.s.zoom = !EV.s.zoom; EV.draw(); } });
