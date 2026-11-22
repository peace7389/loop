// ======================================================================================================
// The derived metrics: the measurements the researcher made up (2026-11-22, the operator: "show measurements it comes up with in each turn on 'What it needed to
// find out' by showing appropriate minimalistic icon on matching hypothesis and show the detail in detail page when clicked"). From the records:
//  - a reading of the tool measure (an expression over recorded quantities, a statistic, a window, a level; on which run; its value) or of the
//    tool probe (a finer record of a run: its quantities and samples, and that the run came out the same);
//  - a measurement an experiment defines: its definition, and its value for each simulation of that experiment (the simulation's metrics).
// Each stands with a box of the board: the hypotheses whose guess, rethink or own record cites the reading; else the hypotheses whose test made the
// run it measured; else that run's exploration; a measurement of the baseline (made in a turn, cited by no hypothesis) under the column of the turn it
// was made in, as a mark of its own (2026-11-22, the operator: "Why all 7 flexible measurements are shown as all occured in turn 0?": until then it
// stood with the aim, at the start, as if made before the first turn). A defined measurement stands with the
// hypotheses its experiment tests (or with its exploration). A small mark on the box says how many; a click opens them in the detail pane, by turn.
// ======================================================================================================
Object.assign(EV, {
  MEAS_STAT: { mean: 'the average of', min: 'the lowest', max: 'the highest', std: 'the spread (standard deviation) of', first: 'the first value of', last: 'the last value of',
               p05: 'the 5th percentile of', p50: 'the median of', p95: 'the 95th percentile of', slope: 'the change per second of', rate: 'the rise per second of',
               time_above: 'the seconds above the level of', time_below: 'the seconds below the level of', first_time_above: 'the first time above the level of',
               first_time_below: 'the first time below the level of', crossings: 'how often it crosses the level:', corr: 'how closely it moves with', lag: 'how far behind (s) it moves with' },
  // every measurement of the open session, with the boxes it stands with (at: 'h:H5', 'x:X3'); kept with the session's model, made once
  measAll() {
    const M = EV.M; if (!M) return []; if (M._meas) return M._meas;
    const recs = (M.recs || []).filter(r => r.type !== 'draft' && r.type !== 'scratch'), by = Object.fromEntries(recs.map(r => [r.id, r])), items = [];
    const parse = s => { try { const v = JSON.parse(s); return v && typeof v === 'object' ? v : null; } catch (x) { return null; } };
    const runExp = {}; recs.forEach(r => { if (r.type === 'simulation' && r.body && r.body.run_id && !(r.body.run_id in runExp)) runExp[r.body.run_id] = r.parent; });
    recs.forEach(r => { const tool = (r.body || {}).tool; if (r.type !== 'result' || !['measure', 'probe'].includes(tool)) return;
      const a = ((by[r.parent] || {}).body || {}).args || {}, out = String(r.body.result ?? ''), v = parse(out);
      items.push({ id: r.id, turn: r.turn, kind: tool, run: a.run_id || a.run, of: a.of, stat: tool === 'measure' ? a.stat || 'mean' : null, t_from: a.t_from, t_to: a.t_to, level: a.level, with: a.with, every: a.every,
                   value: v ? v.value : null, samples: v ? v.samples : null, from_s: v ? v.from_s : null, to_s: v ? v.to_s : null, columns: v ? v.columns : null, same: v ? v.same_result : null, err: v ? null : out }); });
    recs.forEach(x => { if (x.type !== 'experiment' || !((x.body || {}).measurements || []).length) return;
      const sims = recs.filter(s => s.type === 'simulation' && s.parent === x.id);
      x.body.measurements.forEach(m => items.push({ id: x.id, turn: x.turn, kind: 'defined', name: m.name, of: m.of, stat: m.stat, t_from: m.t_from, t_to: m.t_to, level: m.level, with: m.with, exp: x.id,
        values: sims.map(s => ({ sim: s.id, label: s.body.label, run: s.body.run_id, value: (s.body.metrics || {})[m.name] })) })); });
    const hyps = recs.filter(r => r.type === 'hypothesis'), fromWhy = y => hyps.filter(h => (h.body || {}).from_why === y).map(h => 'h:' + h.id);
    const ofExp = x => (x && ((x.body || {}).tests || []).length ? x.body.tests.map(h => 'h:' + h) : x ? ['x:' + x.id] : []);
    items.forEach(it => {
      if (it.kind === 'defined') { it.at = ofExp(by[it.exp]); return; }
      const cites = recs.filter(r => (r.type === 'why' && ((r.body || {}).about || []).includes(it.id)) || (r.type === 'rethink' && ((r.body || {}).in_light_of || []).includes(it.id)));
      const at = [...new Set([...cites.flatMap(r => fromWhy(r.type === 'why' ? r.id : r.body.for)), ...hyps.filter(h => ((h.body || {}).follows_from || []).includes(it.id)).map(h => 'h:' + h.id)])];
      const x = by[runExp[it.run]];
      it.at = at.length ? at : (!x || x.id === 'X0') && it.turn > 0 ? ['t:' + it.turn] : ofExp(x);
    });
    return (M._meas = items);
  },
  // the turns with measurements of the baseline that stand under their turn's column ('t:3'): each such turn gets a column of the board
  measTurns() { return [...new Set(EV.measAll().filter(it => EV.seen(it.id)).flatMap(it => (it.at || []).filter(k => k.startsWith('t:')).map(k => Number(k.slice(2)))))].sort((a, b) => a - b); },
  // the mark of those, under the boxes of the turn's column: a ruler, how many, and of what; x, y: its top left, w: the column's width
  measTurnMark(x, y, w, t) {
    const its = EV.measOf('t:' + t); if (!its.length) return ''; const e = EV.e, n = its.length, label = w >= 160 ? `${n} of the baseline` : w >= 110 ? `${n} · baseline` : String(n);
    const says = its.slice(0, 6).map(it => '· ' + EV.measLine(it)).join('\n') + (n > 6 ? `\n… and ${n - 6} more` : '');
    return `<g class="ms-mark ms-tmark" data-act="open" data-t="meas" data-id="t:${t}" data-n="${n}" tabindex="0"><title>${e(`${n === 1 ? 'A derived metric' : n + ' derived metrics'} of the baseline the researcher defined in turn ${t}, cited by no hypothesis yet:\n${says}\nClick to open ${n === 1 ? 'it' : 'them'} beside the board.`)}</title>`
      + `<rect x="${x}" y="${y}" width="${(33 + label.length * 7.4).toFixed(1)}" height="18" rx="4"/>${EV.measBadge(x + 3, y + 3)}<text x="${x + 25}" y="${y + 13}">${e(label)}</text></g>`;
  },
  measOf(key) { return EV.measAll().filter(it => (it.at || []).includes(key) && EV.seen(it.id)); },
  // the mark of a derived metric: a formula badge, ƒx (2026-11-22, the operator: "adopt an icon for flexible measurement in similar spirit with a
  // finding", "more instantly recognizable", then "something can express its custom and on demand nature"): a formula the researcher writes itself
  // and the harness computes when it is asked; white on purple, a colour no other mark of the page has; 18 by 12 at (x, y)
  measBadge: (x, y) => `<g class="ms-fx" transform="translate(${x},${y})"><rect class="fx-b" x="0.5" y="0.5" width="17" height="11" rx="3"/><path class="fx-t" d="M7.9,2.7 C6.9,2.1 5.8,2.6 5.5,3.8 L4.2,9.6 C3.9,10.8 3.1,11 2.3,10.6 M3.6,5.4 H7.2 M9.4,5.3 L13.4,10.3 M14,5.3 L8.8,10.3"/></g>`,   // ƒx drawn as lines: the same on every computer, whatever its fonts
  // the mark of a box: a small formula badge, and how many when more than one, astride the box's lower right corner (it covers none of the box's words, also
  // on a busy board's small boxes); its hover box lists them, a click opens them. xr, yb: the box's right edge and its bottom
  measMark(xr, yb, key) {
    const its = EV.measOf(key); if (!its.length) return ''; const e = EV.e, n = its.length, w = n > 1 ? 35 : 23, x = xr - w + 3, y = yb - 11;
    const says = its.slice(0, 6).map(it => '· ' + EV.measLine(it)).join('\n') + (n > 6 ? `\n… and ${n - 6} more` : '');
    return `<g class="ms-mark" data-act="open" data-t="meas" data-id="${e(key)}" data-n="${n}" tabindex="0"><title>${e(`${n === 1 ? 'A derived metric' : n + ' derived metrics'} the researcher defined (turn ${[...new Set(its.map(it => it.turn))].join(', ')}):\n${says}\nClick to open ${n === 1 ? 'it' : 'them'} beside the board.`)}</title>`
      + `<rect x="${x}" y="${y + 3}" width="${w}" height="15" rx="4"/>${EV.measBadge(x + 2.5, y + 4.5)}${n > 1 ? `<text x="${x + 23}" y="${y + 14.5}">${n}</text>` : ''}</g>`;
  },
  measNum(v) { return v == null || v === '' ? '–' : !Number.isFinite(+v) ? String(v) : Math.abs(+v) >= 1000 ? Math.round(+v).toLocaleString('en-US') : String(+(+v).toPrecision(4)); },
  // one measurement in a line of words (hover boxes)
  measLine(it) {
    if (it.kind === 'probe') return `a finer record of ${it.run}${it.columns ? `: ${it.columns.length} quantities` : ''}${it.samples ? `, ${it.samples} samples` : ''}${it.err ? ' (refused)' : ''}`;
    const def = `${EV.MEAS_STAT[it.stat] || it.stat} ${it.of}${it.with ? ' and ' + it.with : ''}${it.level != null ? ' (level ' + it.level + ')' : ''}`;
    return it.kind === 'defined' ? `${it.name} = ${def}, in ${it.exp}` : `${def} on ${it.run}: ${it.err ? 'refused' : EV.measNum(it.value)}`;
  },
  // the detail pane: every measurement of that box, by the turn it was made in
  measCard(key) {
    const M = EV.M, e = EV.e, its = EV.measOf(key), id = String(key).slice(2), h = key.startsWith('h:') ? M.hypById[id] : null;
    const whom = h ? `${EV_ICON.hypothesis} hypothesis ${e(id)}` : key.startsWith('t:') ? `the baseline, made in turn ${e(id)} <span class="sm">(cited by no hypothesis yet)</span>` : id === 'X0' ? 'the baseline, before the first turn' : `${EV_ICON.experiment} exploration ${e(id)}`;
    const win = it => (it.t_from != null || it.t_to != null ? ` from ${it.t_from ?? 2} s to ${it.t_to ?? 'the end'}` : '');
    const card = it => {
      if (it.kind === 'probe') return `<div class="ms-c" data-kind="probe"><p><b>A finer record of ${e(it.run)}</b> <span class="sm">· ${EV.link(it.id)}, the tool probe</span></p>`
        + (it.err ? `<p class="sm">Refused: ${e(it.err.slice(0, 220))}</p>` : `<p class="sm">The same simulation run again with taps that only listen${it.every ? `, a sample every ${e(it.every)} s` : ''}: ${e(it.samples ?? '–')} samples of ${(it.columns || []).length} quantities (${e((it.columns || []).join(', '))}). The run came out the same: ${it.same ? 'yes' : 'no'}.</p>`) + '</div>';
      const def = `<b>${e(EV.MEAS_STAT[it.stat] || it.stat)}</b> <code>${e(it.of)}</code>${it.with ? ` and <code>${e(it.with)}</code>` : ''}${e(win(it))}${it.level != null ? ` <span class="sm">(level ${e(it.level)})</span>` : ''}`;
      if (it.kind === 'defined') return `<div class="ms-c" data-kind="defined"><p><b>${e(it.name)}</b> = ${def} <span class="sm">· defined by its experiment ${EV.link(it.exp)}: computed for each of its simulations</span></p>`
        + `<table class="ms-t"><tbody>${it.values.map(v => `<tr><td>${EV.link(v.sim)} ${e(v.label || '')} <span class="sm">${e(v.run || '')}</span></td><td class="ms-v">${e(EV.measNum(v.value))}</td></tr>`).join('')}</tbody></table></div>`;
      return `<div class="ms-c" data-kind="measure"><p>${def} on ${e(it.run)} <span class="sm">· ${EV.link(it.id)}, the tool measure</span></p>`
        + (it.err ? `<p class="sm">Refused: ${e(it.err.slice(0, 260))}</p>` : `<p><span class="ms-v">${e(EV.measNum(it.value))}</span> <span class="sm">from ${e(it.samples ?? '–')} samples, ${e(it.from_s ?? '–')} to ${e(it.to_s ?? '–')} s</span></p>`) + '</div>';
    };
    const turns = [...new Set(its.map(it => it.turn))].sort((a, b) => a - b);
    return `<h2>Derived metrics the researcher defined <small>for ${whom}</small></h2>${h ? `<p class="sm">${e(h.question || h.text || '')}</p>` : ''}
      <p class="sm">A derived metric is one the researcher defines itself on top of the metrics a simulation records: what it computes, on which simulation, and what came out. None costs a simulation: the harness computes it from what a simulation recorded (its series, or the finer record of a probe).</p>
      ${turns.map(t => `<h3 class="ms-turn">${EV_ICON.turn} Turn ${e(t)}</h3>${its.filter(it => it.turn === t).map(card).join('')}`).join('') || '<p class="sm">None.</p>'}`;
  },
  measIcon: () => `<svg class="ms-ic" viewBox="0 0 18 13" width="20" height="15" aria-hidden="true">${EV.measBadge(0.3, 0.5)}</svg>`,
});
