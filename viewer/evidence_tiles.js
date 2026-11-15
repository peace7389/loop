// The simulations of the experiment that is being run, one tile each, in "What it needed to find out" under the strip
// of the stage. While the simulator works the ledger does not grow, so the page reads the simulator's own files:
//   sessions/<id>/runs/<run>/series.csv   the samples the program writes as it goes (one every 0.1 s of simulated time)
//   sessions/<id>/runs/<run>/metrics.json its measures, written when the simulation has ended
//   sessions/<id>/runs/index.json         the runs the harness has collected
// A tile shows the design's label and run, the settings in which it differs from the brief's defaults, how far the
// simulated time has got, the goodput of the two flows over that time (the curve grows as the file grows), and, once
// the simulation has ended, its measures. Nothing is computed that the files do not hold; the curve is the file.
// Which run belongs to which design: the harness starts, in the order of the design, every simulation whose settings
// and seed no earlier simulation of the session had, and numbers the runs on from the last one (tools.run_many). The
// page recounts that. When the simulation has ended its params.json says which settings it ran with; if that is not the
// design the page expected, the tile says so and shows the file's settings.
// The tiles stay when the experiment's records have arrived (its simulations take seconds, the reply that follows takes minutes): until the
// next experiment starts they show the simulations of the newest experiment as they ended, read from the records (which run each simulation
// got) and from the same files. They go when the session ends: from then on its simulations are in the notebook and the tables.
// Where the reader is told: the banner, the notebook's line "ns-3 is working" (with how many have ended and a link to the tiles), and a small
// note under the banner when an experiment's simulations start (evidence_live.js).
// Nothing here is written by a model.
// ======================================================================================================
Object.assign(EV, {
  tiles: { key: null, runs: {}, more: false },
  // a rate or a number as a number, so that two designs compare as the harness compares them (2Gbps = 2000Mbps)
  tileNum(v) { const m = /^([\d.]+)\s*([kMG]?)bps$/.exec(String(v)); return m ? Number(m[1]) * ({ k: 1e3, M: 1e6, G: 1e9 }[m[2]] || 1) : typeof v === 'number' ? v : String(v); },
  tileKey: (p, keys) => JSON.stringify(keys.map(k => EV.tileNum(p[k]))),
  // the designs of the open experiment that had to be run, each with the run it got
  tilePlan(now) {
    const M = EV.M, x = now && M.recs.find(r => r.id === now.exp); if (!x) return null;
    const kn = (M.brief && M.brief.knobs) || {}, keys = Object.keys(kn), dflt = Object.fromEntries(keys.map(k => [k, kn[k].default]));
    const seen = new Set(M.sims.filter(s => !s.same_as && s.metrics).map(s => EV.tileKey({ ...dflt, ...s.params }, keys))), fresh = [], reused = [];
    for (const r of x.body.runs || []) { const p = { ...dflt, ...(r.params || {}) }, k = EV.tileKey(p, keys); if (seen.has(k)) reused.push(r.label); else { seen.add(k); fresh.push({ label: r.label, params: p }); } }
    const first = 1 + Math.max(0, ...M.sims.map(s => Number(String(s.run || '').slice(1)) || 0));
    fresh.forEach((d, i) => { d.run = 'r' + String(first + i).padStart(3, '0'); d.differs = keys.filter(k => EV.tileNum(d.params[k]) !== EV.tileNum(dflt[k])); });
    return { key: `${M.id}/${x.id}`, exp: x.id, fresh, reused, next: 'r' + String(first + fresh.length).padStart(3, '0'), keys };
  },
  // the simulations of the newest experiment whose records have arrived: the same tiles, from the records and the runs' own files
  tilePlanDone() {
    const M = EV.M, x = M.recs.filter(r => r.type === 'experiment' && M.recs.some(q => q.type === 'evidence' && q.parent === r.id)).pop(); if (!x) return null;
    const kn = (M.brief && M.brief.knobs) || {}, keys = Object.keys(kn), dflt = Object.fromEntries(keys.map(k => [k, kn[k].default])), sims = M.sims.filter(s => s.exp === x.id);
    const fresh = sims.filter(s => !s.same_as && s.run && s.metrics).map(s => { const p = { ...dflt, ...s.params }; return { label: s.label, params: p, run: s.run, sim: s, differs: keys.filter(k => EV.tileNum(p[k]) !== EV.tileNum(dflt[k])) }; });
    return { key: `${M.id}/${x.id}`, exp: x.id, fresh, reused: sims.filter(s => s.same_as).map(s => s.label), next: null, keys, done: true, baseline: x.by === 'harness' || x.id === 'X0' };
  },
  // their measures are the records'; each curve is read once more from its file, whole
  tilesDone(P, sid) {
    const T = EV.tiles, base = `../sessions/${sid}/runs/`, todo = P.fresh.filter(d => { const R = T.runs[d.run] || (T.runs[d.run] = { rows: [], there: false }); R.metrics = d.sim.metrics; R.used = d.sim.params; R.collected = R.done = true; if (R.whole) return false; R.whole = true; return true; });
    if (!todo.length) return;
    Promise.all(todo.map(async d => { const t = await EV.get(`${base}${d.run}/series.csv`), R = T.runs[d.run]; if (t != null) { R.there = true; R.rows = t.trim().split('\n').slice(1).map(l => l.split(',').slice(0, 3).map(Number)).filter(q => q.length === 3 && q.every(Number.isFinite)); } }))
      .then(() => { const el = document.getElementById('live-tiles'), now = EV.liveNow(); if (el && now && EV.M && EV.M.id === sid && el.dataset.exp === P.exp) el.innerHTML = EV.tilesHtml(now, true); });
  },
  // every two seconds while simulations run (from EV.liveTick, after the index was read): each tile's files, then the tiles that changed
  tilesTick(now, sid) {
    const P = EV.tilePlan(now), T = EV.tiles; if (!P) return; if (T.key !== P.key) { T.key = P.key; T.runs = {}; T.more = false; }
    const base = `../sessions/${sid}/runs/`, idx = Object.fromEntries((EV.files.index || []).filter(q => q && q.id).map(q => [q.id, q]));
    const jobs = P.fresh.map(async d => { const R = T.runs[d.run] || (T.runs[d.run] = { rows: [], there: false }); if (R.done) return;
      const t = await EV.get(`${base}${d.run}/series.csv`); if (t != null) { R.there = true; R.rows = t.trim().split('\n').slice(1).map(l => l.split(',').slice(0, 3).map(Number)).filter(q => q.length === 3 && q.every(Number.isFinite)); }
      const q = idx[d.run]; if (q) { R.metrics = q.metrics; R.used = q.params; R.collected = true; }
      else if (!R.metrics && R.rows.length && R.rows[R.rows.length - 1][0] >= Number(d.params.duration) + 1 - 0.15) { const m = await EV.json(`${base}${d.run}/metrics.json`), u = m && await EV.json(`${base}${d.run}/params.json`); if (m && u) { R.metrics = m; R.used = u; } }
      R.done = !!(R.metrics && R.collected); });
    // one run beyond those the page expects: if it is there, the page's recount is not the harness's, and the tiles say so
    if (!T.more) jobs.push(fetch(`${base}${P.next}/series.csv?t=${Date.now()}`, { method: 'HEAD', cache: 'no-store' }).then(r => { T.more = r.ok; }).catch(() => {}));
    Promise.all(jobs).then(() => { if (!EV.M || EV.M.id !== sid) return; const el = document.getElementById('live-tiles'); if (!el) return;
      const tmp = document.createElement('div'); tmp.innerHTML = EV.tilesHtml(now, true);
      tmp.querySelectorAll('.lt').forEach(n => { const old = el.querySelector(`.lt[data-run="${n.dataset.run}"]`); if (!old) el.querySelector('.lt-grid') ? el.querySelector('.lt-grid').appendChild(n) : (el.innerHTML = EV.tilesHtml(now, true)); else if (old.dataset.sig !== n.dataset.sig) old.replaceWith(n); });
      const note = el.querySelector('.lt-note'), nn = tmp.querySelector('.lt-note'); if (note && nn && note.textContent !== nn.textContent) note.replaceWith(nn);
      if (nn) document.querySelectorAll('#s-notebook .nb-sims-n').forEach(q => { q.textContent = ` · ${nn.dataset.ended} of ${nn.dataset.of} ended`; }); });  // the same count where the notebook says that ns-3 is working
  },
  // the curve of one tile: the goodput of the two flows over simulated time. x: from the first second of measured traffic to its last; y: from 0 to the link's rate
  tilePlot(d, R, top) {
    const W = 232, H = 62, L = 3, Rt = 6, Tp = 5, B = 3, t0 = 1, t1 = 1 + Number(d.params.duration || 0), rows = R.rows, e = EV.e;
    const x = t => L + (W - L - Rt) * Math.min(1, Math.max(0, (t - t0) / Math.max(t1 - t0, 1e-9))), y = v => H - B - (H - Tp - B) * Math.min(1, Math.max(0, v / top));
    const line = (i, c) => (rows.length < 2 ? '' : `<polyline class="lt-ln" fill="none" stroke="var(${c})" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" points="${rows.map(q => `${x(q[0]).toFixed(1)},${y(q[i]).toFixed(1)}`).join(' ')}"/>`);
    const dot = (i, c) => (rows.length ? `<circle class="lt-dot" cx="${x(rows[rows.length - 1][0]).toFixed(1)}" cy="${y(rows[rows.length - 1][i]).toFixed(1)}" r="4" fill="var(${c})" stroke="var(--surface-1)" stroke-width="2"/>` : '');
    return `<svg class="lt-plot" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" data-t0="${t0}" data-t1="${t1}" data-l="${L}" data-w="${W - L - Rt}" role="img" aria-label="${e(`Goodput of UDP and TCP over the simulated time of ${d.label}`)}">
      <line class="lt-ax" x1="${L}" x2="${W - Rt}" y1="${Tp}" y2="${Tp}"/><line class="lt-ax" x1="${L}" x2="${W - Rt}" y1="${H - B}" y2="${H - B}"/><line class="lt-x" x1="0" x2="0" y1="${Tp}" y2="${H - B}" style="display:none"/>
      ${line(1, '--series-1')}${line(2, '--series-2')}${dot(1, '--series-1')}${dot(2, '--series-2')}</svg>`;
  },
  tileHtml(d, P) {
    const M = EV.M, e = EV.e, R = EV.tiles.runs[d.run] || { rows: [] }, rows = R.rows, last = rows[rows.length - 1], dur = Number(d.params.duration || 0);
    const link = EV.tileNum(d.params.linkRate ?? ((M.brief && M.brief.system) || {}).linkRate ?? '1Gbps'), top = Math.max(typeof link === 'number' ? link : 1e9, ...rows.map(q => Math.max(q[1], q[2])));
    const state = R.metrics ? (R.collected ? 'collected' : 'ended') : last ? 'running' : R.there ? 'started' : 'waiting';
    const other = R.used && P.keys.some(k => k in R.used && EV.tileNum(R.used[k]) !== EV.tileNum(d.params[k]));  // its own params.json names other settings than the design the page expected
    const shown = other ? P.keys.filter(k => k in R.used).map(k => `${e(EV.LABEL[k] || k)} <b>${e(EV.setVal(k, R.used[k]))}</b>`).join(' · ') : d.differs.length ? d.differs.map(k => `${e(EV.LABEL[k] || k)} <b>${e(EV.setVal(k, d.params[k]))}</b>`).join(' · ') : 'every setting at the brief’s default';
    const says = { waiting: 'waiting for its first file', started: 'started · no sample yet', running: `measured second ${(last ? Math.max(0, last[0] - 1) : 0).toFixed(1)} of ${dur}`, ended: 'ended · not yet collected by the harness', collected: 'ended · collected by the harness' }[state];
    const val = (c, name, k, v) => `<span class="lt-v"><i class="lt-sw" style="background:var(${c})"></i>${name} <b>${EV.v4(k, v)}</b></span>`;
    const vals = R.metrics ? `${val('--series-1', 'UDP', 'udp_goodput_bps', R.metrics.udp_goodput_bps)}${val('--series-2', 'TCP', 'tcp_goodput_bps', R.metrics.tcp_goodput_bps)}<span class="lt-v">UDP loss <b>${EV.v4('udp_loss_frac', R.metrics.udp_loss_frac)}</b></span>`
      : last ? `${val('--series-1', 'UDP', 'udp_bps', last[1])}${val('--series-2', 'TCP', 'tcp_bps', last[2])}` : `<span class="lt-v"><i class="lt-sw" style="background:var(--series-1)"></i>UDP</span><span class="lt-v"><i class="lt-sw" style="background:var(--series-2)"></i>TCP</span>`;
    const sig = `${state}|${rows.length}|${other ? 1 : 0}|${EV.tiles.more ? 1 : 0}`;
    return `<div class="lt" data-run="${e(d.run)}" data-label="${e(other || EV.tiles.more ? '' : d.label)}" data-state="${state}" data-rows="${rows.length}" data-sig="${sig}">
      <p class="lt-h"><span class="lt-ico" data-by="simulator"><i class="sw"></i></span><b>${other || EV.tiles.more ? e(d.run) : e(d.label)}</b>${other || EV.tiles.more ? '' : ` <span class="sm" title="The run: the folder of this simulation's files">${e(d.run)}</span>`}</p>
      <p class="lt-state sm">${says}</p>
      <p class="lt-set sm">${other ? '<span title="The settings its own params.json names: not those of the design the page expected for this run">its own file says: </span>' : ''}${shown}</p>
      <div class="lt-fig"><span class="lt-top sm" title="The top line of the picture: the rate of the link">${EV.v4('link_rate_bps', top)}</span>${EV.tilePlot(d, R, top)}<p class="lt-xax sm" title="The measured time of the simulation: the picture fills from left to right as the simulator gets on"><span>0 s</span><span>measured time</span><span>${dur} s</span></p></div>
      <p class="lt-vals sm">${vals}</p><p class="lt-read sm" data-say="${e(R.metrics ? 'its measures, over the measured time' : last ? 'the newest sample' : '')}">${R.metrics ? 'its measures, over the measured time' : last ? 'the newest sample' : ''}</p></div>`;
  },
  // inner: only the tiles' own block (what a tick compares against the page)
  tilesHtml(now, inner) {
    if (!now) return ''; const live = now.phase === 'sims' || now.phase === 'baseline', P = live ? EV.tilePlan(now) : EV.tilePlanDone(); if (!P || !P.fresh.length) return '';
    if (EV.tiles.key !== P.key) { EV.tiles.key = P.key; EV.tiles.runs = {}; EV.tiles.more = false; }
    if (!live) EV.tilesDone(P, EV.M.id);
    const e = EV.e, n = P.fresh.length, ended = P.fresh.filter(d => (EV.tiles.runs[d.run] || {}).metrics).length;
    const note = `<p class="lt-note sm" data-ended="${ended}" data-of="${n}">${ended} of ${n} ended${P.reused.length ? ` · not run again, same settings and seed as an earlier simulation: ${e(P.reused.join(', '))}` : ''}${EV.tiles.more ? ' · the simulator started more runs than this page expected, so each tile is named by its run' : ''}</p>`;
    const body = `<p class="lt-t" data-live="${live ? 1 : 0}"><b>${(live ? now.phase === 'baseline' : P.baseline) ? 'The baseline simulation' : `The ${n} simulation${n === 1 ? '' : 's'} of ${e(P.exp)}`}, as ns-3 ${live ? 'runs' : 'ran'} ${n === 1 ? 'it' : 'them'}</b> <span class="sm">${live ? 'each picture is the simulation’s own series.csv, read again every 2 seconds: goodput from 0 to the link’s rate, over its measured time'
      : `the newest simulations: ${n === 1 ? 'it has' : 'they have'} ended and ${n === 1 ? 'its record is' : 'their records are'} in the notebook; the picture${n === 1 ? '' : 's'} stay${n === 1 ? 's' : ''} here until the next experiment starts · each is the simulation’s own series.csv: goodput from 0 to the link’s rate, over its measured time`}</span></p>${note}<div class="lt-grid">${P.fresh.map(d => EV.tileHtml(d, P)).join('')}</div>`;
    return inner ? body : `<div id="live-tiles" class="noprint" data-exp="${e(P.exp)}">${body}</div>`;
  },
  // pointing at a curve: the sample under the pointer, in words under the picture
  tileHover(ev) {
    const svg = ev.target.closest && ev.target.closest('svg.lt-plot'); if (!svg) return; const tile = svg.closest('.lt'), R = EV.tiles.runs[tile.dataset.run], read = tile.querySelector('.lt-read'), xl = svg.querySelector('.lt-x'); if (!R || !R.rows.length) return;
    const b = svg.getBoundingClientRect(), k = b.width / svg.viewBox.baseVal.width, px = (ev.clientX - b.left) / k, t = Number(svg.dataset.t0) + (Number(svg.dataset.t1) - Number(svg.dataset.t0)) * (px - Number(svg.dataset.l)) / Number(svg.dataset.w);
    const q = R.rows.reduce((a, c) => (Math.abs(c[0] - t) < Math.abs(a[0] - t) ? c : a)), X = Number(svg.dataset.l) + Number(svg.dataset.w) * (q[0] - Number(svg.dataset.t0)) / Math.max(Number(svg.dataset.t1) - Number(svg.dataset.t0), 1e-9);
    xl.setAttribute('x1', X); xl.setAttribute('x2', X); xl.style.display = ''; read.innerHTML = `at ${(q[0] - 1).toFixed(1)} s: UDP <b>${EV.v4('udp_bps', q[1])}</b> · TCP <b>${EV.v4('tcp_bps', q[2])}</b>`;
  },
  tileLeave(ev) { const svg = ev.target.closest && ev.target.closest('svg.lt-plot'); if (!svg || (ev.relatedTarget && svg.contains(ev.relatedTarget))) return;  // from the picture to one of its own lines is not leaving it
    const tile = svg.closest('.lt'), read = tile.querySelector('.lt-read'); svg.querySelector('.lt-x').style.display = 'none'; read.textContent = read.dataset.say; },
});
if (!EV.off) { document.addEventListener('mousemove', EV.tileHover); document.addEventListener('mouseout', EV.tileLeave); }
