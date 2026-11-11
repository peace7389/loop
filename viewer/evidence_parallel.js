// The sweep as a parallel-coordinates chart (operator columns on): one axis per knob the sweep varies and one for the
// brief's target; one thin line per sweep row (grey when it fails the brief's conditions); the recommendation of each
// ticked session as a bold line in the session's colour. One chart per scheduling policy, because each policy has its
// own sweep. Read from checks/ only: the answer key, the sweep tables, the scores. Plain SVG.
// ======================================================================================================
Object.assign(EV, {
  keys: {}, scores: {},   // brief id -> its answer key; session id -> its score file (undefined: being read; null: none)
  fetchOnce(cache, id, url) { if (!(id in cache)) { cache[id] = undefined; EV.json(url).then(v => { cache[id] = v; if (EV.s.view === 'compare') EV.draw(); }); } return cache[id]; },
  sweepRows(id) { if (!(id in EV.sweeps)) { EV.sweeps[id] = null; EV.get(`../checks/sweeps/${id}/table.csv`).then(t => { EV.sweeps[id] = t ? EV.csv(t) : 'none'; if (EV.s.view === 'compare') EV.draw(); }); } return EV.sweeps[id]; },

  parallelCards(list) {
    const e = EV.e, brief = list[0].M.brief, g = EV.goalOf(brief); if (!brief) return '';
    if (!g) return `<div class="ev-card"><h2>The sweep<small>${EV.term('Operator', 'operator')} column</small></h2><p class="sm">Not applicable: the goal is chosen by the model, so there is no target to draw.</p></div>`;
    const key = EV.fetchOnce(EV.keys, brief.id, `../checks/keys/${brief.id}.json`), per = (key && key.per_scheduling_policy) || {};
    if (key === undefined) return '<div class="ev-card"><p class="sm">Reading the answer key…</p></div>';
    const pols = [...new Set(list.map(q => q.x.policy).filter(Boolean))];
    const cards = pols.map(pol => { const sid = per[pol] && per[pol].sweep, rows = sid ? EV.sweepRows(sid) : 'none', mine = list.filter(q => q.x.policy === pol);
      const recs = mine.map(q => { const sc = q.x.score ? EV.fetchOnce(EV.scores, q.x.id, `../checks/scores/${q.x.id}.json`) : null; return sc ? { name: q.x.id, color: EV.color(q.slot), values: { ...(sc.recommendation_with_defaults || sc.recommendation || {}), [g.target]: (sc.at_the_recommendation || {})[g.target] } } : null; }).filter(Boolean);
      const body = rows === 'none' ? `<p class="sm">the sweep of this scheduling policy: ${EV.nr}</p>` : !rows ? '<p class="sm">Reading the sweep table…</p>' : EV.parallelSvg(rows, brief, g, recs);
      return `<div class="ev-card cmp-par"><h2>The sweep under “${e(pol)}”, and the recommendations<small>${EV.term('Operator', 'operator')} column · sweep ${e(sid || 'not recorded')} · sessions ${e(mine.map(q => q.x.id).join(', '))}${mine.length > recs.length ? ` · ${mine.length - recs.length} not scored, so not drawn` : ''}</small></h2>${body}</div>`; }).join('');
    const hidden = list.filter(q => q.x.policy_hidden).length;
    return (cards || `<div class="ev-card"><p class="sm">the scheduling policy of the ticked sessions: ${EV.nr}</p></div>`) + (hidden ? `<div class="ev-card"><p class="sm">${hidden} ticked session${hidden === 1 ? ' has' : 's have'} a scheduling policy chosen by the harness: not drawn until scored.</p></div>` : '');
  },

  parallelSvg(rows, brief, g, recs) {
    const e = EV.e, [u, f] = EV.unit(g.target), W = 900, H = 330, L = 70, R = 90, T = 34, B = 22, ok = r => !r.error && r[g.target] !== '';
    const knobs = Object.keys(brief.knobs || {}).filter(k => k in rows[0] && new Set(rows.map(r => r[k])).size > 1), axes = [...knobs, g.target], X = i => L + i * (W - L - R) / (axes.length - 1);
    const isNum = k => rows.every(r => r[k] !== '' && !isNaN(+r[k])), cats = Object.fromEntries(knobs.map(k => [k, [...new Set(rows.map(r => r[k]))].sort((a, b) => (isNum(k) ? +a - +b : a < b ? -1 : 1))]));
    const tv = rows.filter(ok).map(r => +r[g.target]), lo = Math.min(...tv), hi = Math.max(...tv), yOf = t => T + (1 - t) * (H - T - B);
    const pos = (k, v) => {  // 0..1 along an axis: a knob by the rank of its value among the sweep's values (between two of them for a value off the grid), the target by its value
      if (k === g.target) return (Number(v) - lo) / (hi - lo || 1); const c = cats[k], i = c.indexOf(String(v)); if (i >= 0) return c.length > 1 ? i / (c.length - 1) : 0.5;
      if (!isNum(k) || v == null || isNaN(+v)) return null; const n = c.map(Number), j = n.findIndex(q => q > +v); return j <= 0 ? (j === 0 ? 0 : 1) : (j - 1 + (+v - n[j - 1]) / (n[j] - n[j - 1])) / (c.length - 1); };
    const path = get => { const p = axes.map((k, i) => { const t = pos(k, get(k)); return t == null ? null : `${X(i)},${yOf(Math.max(0, Math.min(1, t))).toFixed(1)}`; }); return p.includes(null) ? '' : 'M' + p.join(' L'); };
    const meet = rows.filter(r => ok(r) && EV.meets(Object.fromEntries(g.conds.map(c => [c.k, +r[c.k]])), g.conds)), fail = rows.filter(r => ok(r) && !meet.includes(r));
    let s = `<path d="${fail.map(r => path(k => r[k])).join(' ')}" fill="none" stroke="var(--text-muted)" stroke-width="1" opacity=".13"/><path d="${meet.map(r => path(k => r[k])).join(' ')}" fill="none" stroke="var(--series-1)" stroke-width="1" opacity=".16"/>`;
    axes.forEach((k, i) => { const x = X(i), c = k === g.target ? EV.ticks(f(lo), f(hi), 5).map(v => [v, (v - f(lo)) / (f(hi) - f(lo) || 1)]) : cats[k].map((v, j) => [v, cats[k].length > 1 ? j / (cats[k].length - 1) : 0.5]).filter((q, j, a) => a.length <= 9 || j % Math.ceil(a.length / 9) === 0 || j === a.length - 1);
      s += `<line x1="${x}" x2="${x}" y1="${T}" y2="${H - B}" stroke="var(--text-secondary)" stroke-width="1"/><text x="${x}" y="${T - 14}" text-anchor="middle" style="font-weight:600;fill:var(--text-primary)">${e(k === g.target ? (TH_DATA.PLAIN[k] || k) + (u ? ', ' + u : '') : k)}</text>`;
      c.forEach(([v, t]) => { if (t < -0.001 || t > 1.001) return; s += `<line x1="${x - 3}" x2="${x + 3}" y1="${yOf(t)}" y2="${yOf(t)}" stroke="var(--text-secondary)"/><text x="${x - 6}" y="${yOf(t) + 3.5}" text-anchor="end" style="font-size:10px;paint-order:stroke;stroke:var(--surface-1);stroke-width:3px">${e(typeof v === 'number' ? (+v.toPrecision(6)).toLocaleString('en-US') : v)}</text>`; }); });
    const ends = [];
    recs.forEach(q => { const d = path(k => q.values[k]); if (!d) return; const end = d.split(' L').pop().split(','); ends.push({ x: +end[0] + 8, y: +end[1] + 4, q });
      s += `<path d="${d}" fill="none" stroke="var(--surface-1)" stroke-width="6"/><path class="rec" d="${d}" fill="none" stroke="${q.color}" stroke-width="3"><title>${e(q.name + ': ' + axes.map(k => `${k} ${q.values[k]}`).join(' · '))}</title></path>`; });
    EV.spread(ends, 13).forEach(l => { s += `<circle cx="${l.x + 3}" cy="${l.y - 4}" r="4" fill="${l.q.color}"/><text x="${l.x + 11}" y="${l.y}" style="font-weight:700;fill:var(--text-primary)">${e(l.q.name)}</text>`; });
    return `<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:1100px" role="img" aria-label="The sweep as parallel coordinates, with the ticked sessions' recommendations">${s}</svg>
      <p class="sm">${rows.length.toLocaleString('en-US')} rows of the sweep, each one line: <span style="color:var(--series-1)">blue</span> ${meet.length.toLocaleString('en-US')} that meet ${e(g.text || 'no condition')}, grey ${fail.length.toLocaleString('en-US')} that do not. Bold: a session's recommendation, as the operator simulated it${recs.length ? '' : ' (none of the ticked sessions of this policy is scored)'}.
        A knob's axis lists the sweep's values at equal steps; a recommended value between two of them sits between them.</p>`;
  },
});
