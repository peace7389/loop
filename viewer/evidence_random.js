// Best so far, against choosing at random (operator columns only; a brief with a given goal and a sweep).
// The random method: N draws, N = the simulations the session used. Each draw picks every knob evenly, and apart from
// the others, from the values of the sweep's FIRST grid (status.json "grid"; not from the rows added later around the
// best point, which would favour it); its result is the sweep row with those values. After k draws the method's result
// is the best value of the target among the draws that meet the brief's conditions; before any draw meets them it has
// no value. Repeated 2,000 times with a fixed seed (mulberry32, seed 20261113): the band is the 10th to the 90th
// percentile of those results at each k (a repetition without a value counts as the worst), the dashed line the median.
// One sentence, computed: after how many simulations the session, and the random method in the median, came within 0.5%
// of the sweep's best row. ~/research/tools/evidence_checks/ev_random.py counts the same from the sweep table, apart.
// ======================================================================================================
Object.assign(EV, {
  RND: { reps: 2000, seed: 20261113, near: 0.005 }, rnd: {}, sweepStat: {},
  mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; },
  // a sweep's table and its status file, read once; the page is drawn again when they arrive
  sweepFiles(id) {
    if (!(id in EV.sweepStat)) { EV.sweepStat[id] = undefined; EV.json(`../checks/sweeps/${id}/status.json`).then(v => { EV.sweepStat[id] = v || null; EV.draw(); }); }
    if (!(id in EV.sweeps)) { EV.sweeps[id] = null; EV.get(`../checks/sweeps/${id}/table.csv`).then(t => { EV.sweeps[id] = t ? EV.csv(t) : 'none'; EV.draw(); }); }
    const rows = EV.sweeps[id], st = EV.sweepStat[id]; return rows === null || st === undefined ? null : { rows: rows === 'none' ? null : rows, status: st };
  },
  // the random method for one sweep, one goal and N draws: { n, p10, p50, p90 (arrays, k = 1..n, null: no value), best, thr,
  // hit: { median (null: not reached), never (repetitions that never came within), reps }, grid, first (rows of the first grid), rows }
  randomBand(id, g, n) {
    const key = `${id}|${g.target}|${g.text}|${n}`; if (key in EV.rnd) return EV.rnd[key];
    const F = EV.sweepFiles(id); if (!F) return null; if (!F.rows || !F.status || !F.status.grid || n < 1) return (EV.rnd[key] = { none: !F.rows ? 'the sweep table' : 'the grid the sweep began with' });
    const grid = F.status.grid, knobs = Object.keys(grid), num = v => (v === '' || isNaN(+v) ? v : +v), same = (a, b) => String(num(a)) === String(num(b)), at = {};
    F.rows.forEach(r => { if (r.error || r[g.target] === '' || !knobs.every(k => grid[k].some(v => same(v, r[k])))) return; const m = Object.fromEntries(Object.entries(r).map(([k, v]) => [k, num(v)]));
      at[knobs.map(k => grid[k].findIndex(v => same(v, r[k]))).join(',')] = { v: m[g.target], ok: EV.meets(m, g.conds) }; });
    const ok = F.rows.filter(r => !r.error && r[g.target] !== '').map(r => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, num(v)]))).filter(m => EV.meets(m, g.conds)).map(m => m[g.target]);
    if (!ok.length) return (EV.rnd[key] = { none: 'a sweep row that meets the brief\'s conditions' });
    const best = g.max ? Math.max(...ok) : Math.min(...ok), thr = g.max ? best * (1 - EV.RND.near) : best * (1 + EV.RND.near), near = v => (g.max ? v >= thr : v <= thr), sc = v => (v == null ? -Infinity : g.max ? v : -v);
    const rand = EV.mulberry(EV.RND.seed), R = EV.RND.reps, cols = Array.from({ length: n }, () => new Array(R)), hits = new Array(R);
    for (let r = 0; r < R; r++) { let cur = null; hits[r] = Infinity;
      for (let k = 0; k < n; k++) { const d = at[knobs.map(q => Math.floor(rand() * grid[q].length)).join(',')];
        if (d && d.ok && (cur == null || (g.max ? d.v > cur : d.v < cur))) cur = d.v; cols[k][r] = cur; if (cur != null && near(cur) && hits[r] === Infinity) hits[r] = k + 1; } }
    const pick = (a, p) => a[Math.ceil(p * R) - 1], pc = p => cols.map(c => { const s = c.slice().sort((x, y) => sc(x) - sc(y)); return pick(s, p); });
    const hs = hits.slice().sort((x, y) => x - y), med = pick(hs, 0.5);
    return (EV.rnd[key] = { n, p10: pc(0.1), p50: pc(0.5), p90: pc(0.9), best, thr, hit: { median: med === Infinity ? null : med, never: hits.filter(h => h === Infinity).length, reps: R },
      grid: Object.fromEntries(knobs.map(k => [k, grid[k].length])), first: Object.keys(at).length, rows: F.rows.length });
  },
  // for a session's own chart: the band over its own simulations (those after the harness's baseline), and the sentence
  randomOf(M) {
    const d = EV.bestData(M), sc = EV.files.score; if (!EV.s.op || !d || !sc || !sc.sweep) return null;
    const own = d.pts.filter(p => p.s.exp !== 'X0'), n = own.length, B = EV.randomBand(sc.sweep, d.g, n); if (!B) return { loading: true }; if (B.none) return { none: B.none };
    const near = v => (d.g.max ? v >= B.thr : v <= B.thr), firstNear = d.pts.find(p => p.best != null && near(p.best)), k = firstNear ? d.pts.filter(p => p.n <= firstNear.n && p.s.exp !== 'X0').length : null;
    return { band: B, offset: d.pts.length - n, n, session: k, sweep: sc.sweep, at_baseline: !!firstNear && firstNear.s.exp === 'X0' };
  },
  randomSentence(r, d) {
    const B = r.band, e = EV.e, pct = (100 * B.hit.never / B.hit.reps), p = pct === 0 ? '0' : pct === 100 ? '100' : pct < 1 ? pct.toFixed(1) : String(Math.round(pct)), [u, f] = EV.unit(d.g.target), fmt = v => (+f(v).toPrecision(6)).toLocaleString('en-US') + (u ? ' ' + u : '');
    const me = r.session == null ? 'not reached' : r.at_baseline ? "at the harness's baseline, before any simulation of its own" : `after ${r.session} simulation${r.session === 1 ? '' : 's'}`;
    const rnd = B.hit.median == null ? 'not reached in the median' : `after ${B.hit.median} in the median`;
    return `<p class="sm" id="rnd-says" data-by="operator" data-session="${r.session == null ? '' : r.at_baseline ? 0 : r.session}" data-median="${B.hit.median ?? ''}" data-never="${B.hit.never}" data-n="${r.n}" data-thr="${B.thr}" data-best="${B.best}"><i class="sw"></i>Within 0.5% of the sweep's best (${e(fmt(B.best))}, so ${d.g.max ? 'at least' : 'at most'} ${e(fmt(B.thr))}): this session ${me}; random choice ${rnd} (never within ${r.n} in ${p}% of repetitions).</p>`;
  },
  randomLegend(r) {
    const B = r.band, g = Object.entries(B.grid).map(([k, n]) => `${n} value${n === 1 ? '' : 's'} of ${k}`).join(', ');
    return ` · <span id="rnd-key"><i class="rnd-band"></i>random choice (${EV.term('Operator', 'operator')} column): ${EV.RND.reps.toLocaleString('en-US')} repetitions of ${r.n} draws, each draw taking every knob evenly from the values of the sweep's first grid (${B.first} rows: ${EV.e(g)}), not from the ${(B.rows - B.first).toLocaleString('en-US')} rows added later around the best point; the band is the 10th to the 90th percentile of the best valid result so far, <span class="rnd-med">- -</span> the median</span>`;
  },
  // on Compare: one band for each scheduling policy among the ticked sessions that have a score, over as many draws as the
  // chart has simulations; names: which sessions it stands behind
  randomCompare(list, n) {
    const out = [], seen = {}; if (!EV.s.op) return out;
    list.forEach(q => { if (!q.x.score || !q.x.policy || q.x.policy_hidden) return; const sc = EV.fetchOnce(EV.scores, q.x.id, `../checks/scores/${q.x.id}.json`), d = EV.bestData(q.M); if (!sc || !sc.sweep || !d) return;
      if (!seen[sc.sweep]) { const B = EV.randomBand(sc.sweep, d.g, n); seen[sc.sweep] = { B, policy: q.x.policy, sessions: [], sweep: sc.sweep }; out.push(seen[sc.sweep]); } seen[sc.sweep].sessions.push(q.x.id); });
    return out;
  },
  // the band as SVG, for bestSvg: X(n), Y(v), offset = the simulations before the first draw (the harness's baseline)
  randomSvg(B, X, Y, offset, last) {
    const pts = k => X(Math.min(offset + k + 1, last)); let seg = [], out = '';
    const flush = () => { if (seg.length) { const up = seg.map(([k, a], i) => `${i ? 'H' : 'M'}${pts(k)}${i ? '' : ',' + Y(a)} V${Y(a)}`).join(' ') + ` H${pts(seg[seg.length - 1][0] + 1)}`, dn = seg.slice().reverse().map(([k, , b]) => `V${Y(b)} H${pts(k)}`).join(' ');
      out += `<path class="rnd-area" d="${up} ${dn} Z"/>`; seg = []; } };
    for (let k = 0; k < B.n; k++) { if (B.p10[k] == null || B.p90[k] == null) { flush(); continue; } seg.push([k, B.p90[k], B.p10[k]]); } flush();
    let d = ''; for (let k = 0; k < B.n; k++) { const v = B.p50[k]; if (v == null) continue; d += `${d ? 'H' + pts(k) + ' V' : 'M' + pts(k) + ','}${Y(v)} `; } if (d) d += `H${pts(B.n)}`;
    return `<g class="rnd" clip-path="url(#ev-bc)" data-n="${B.n}" data-p10="${B.p10.map(v => v ?? '').join(',')}" data-p50="${B.p50.map(v => v ?? '').join(',')}" data-p90="${B.p90.map(v => v ?? '').join(',')}">${out}${d ? `<path class="rnd-line" d="${d}"/>` : ''}</g>`;
  },
});
