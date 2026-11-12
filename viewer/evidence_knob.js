// The simulations of each turn, along one knob: one horizontal axis per turn, one dot per simulation at the value it
// used. Each axis spans that turn's own smallest to largest value, with both ends printed, and two lines join it to the
// part of the previous axis it covers, so the reader sees where the model looked closer. (This is the page's one
// stated exception to "never two scales in one chart": DECISION of the operator, 2026-11-12.) A turn with one value
// keeps the previous turn's axis and says what it varied instead; the first axis of all is then the brief's range.
// A knob with choices keeps the brief's order on every axis. Simulations at the same value are stacked. A dot is
// filled if the simulation meets the brief's conditions, as in "Best so far" (with an open goal there is one kind of
// dot); a simulation returned from an earlier one carries the page's sign for it, a small ring, beside its dot.
// During the replay only what is recorded by the chosen step is drawn, and the knob shown at first is chosen from that
// alone. The card is not printed.
// ======================================================================================================
Object.assign(EV, {
  knNum(v) { if (typeof v === 'number') return v; const m = String(v).match(/^\s*([0-9.]+)\s*([kMG]?)bps\s*$/); return m ? m[1] * { '': 1, k: 1e3, M: 1e6, G: 1e9 }[m[2]] : Number(v); },
  // the turns whose simulations are recorded by the replay's step
  knTurns(M) { return M.turns.filter(t => t.exp && EV.seen(t.exp.id)).map(t => ({ t, sims: t.exp.sims.filter(q => EV.seen(q.id)) })).filter(c => c.sims.length); },
  // the knobs there are (the brief's; before briefs: the settings the simulations state), and the one most experiments vary
  knKnobs(M, rows) {
    const names = M.brief && M.brief.knobs ? Object.keys(M.brief.knobs) : [...new Set(rows.flatMap(c => c.sims.flatMap(q => Object.keys(q.params || {}))))];
    const varies = k => rows.filter(c => new Set(c.sims.filter(q => q.params && q.params[k] != null).map(q => String(q.params[k]))).size > 1).length;
    return { names, varies, first: names.slice().sort((a, b) => varies(b) - varies(a))[0] || null };
  },

  knobCard() {
    const M = EV.M, S = EV.s, e = EV.e, rows = EV.knTurns(M), K = EV.knKnobs(M, rows), knob = K.names.includes(S.knob) ? S.knob : K.first, num = EV.knNum, show = v => TASK_VIEW._rate(String(v));
    const head = `<h2>The simulations of each turn, along one knob <small>one dot per ${EV.term('Simulation', 'simulation')} at the value it used · each ${EV.term('Turn', 'turn')} has its own axis, from its smallest to its largest value · click a dot to open it on the right</small></h2>`;
    if (!rows.length || !knob) return `<div class="ev-card noprint" id="s-knob">${head}<p class="sm">${rows.length ? 'the knobs of this session: ' + EV.nr : 'No simulation' + (S.step == null ? ' yet.' : ' by this step of the replay.')}</p></div>`;
    const spec = (M.brief && M.brief.knobs && M.brief.knobs[knob]) || {}, cat = spec.choices || null, g = EV.goalOf(M.brief), sc = EV.files.score, plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
    const col = !g ? 'var(--text-secondary)' : /^udp|band0/.test(g.target) ? 'var(--series-1)' : /^tcp|band1/.test(g.target) ? 'var(--series-2)' : 'var(--text-secondary)';
    const W = 760, L = 122, R = 72, at = (a, n) => (a.hi === a.lo ? (L + W - R) / 2 : L + (n - a.lo) / (a.hi - a.lo) * (W - L - R)), pos = (a, v) => (a.cat ? L + (a.cat.indexOf(String(v)) + 0.5) / a.cat.length * (W - L - R) : at(a, num(v)));
    const best = S.op && sc && sc.best_row && sc.best_row[knob] != null ? sc.best_row[knob] : null;
    let y = 4, prev = null, svg = '', anyRet = false, bestSaid = false;
    rows.forEach(c => {
      const have = c.sims.filter(q => q.params && q.params[knob] != null), vals = [...new Set(have.map(q => String(q.params[knob])))];
      const others = K.names.filter(k => k !== knob && new Set(c.sims.filter(q => q.params && q.params[k] != null).map(q => String(q.params[k]))).size > 1);
      let a = null;  // this turn's axis: its own smallest to largest value; with one value the previous axis; the first of all: the brief's range
      if (cat) a = { cat: cat.map(String), lo: 0, hi: 1 };
      else if (vals.length > 1) { const s = have.slice().sort((p, q) => num(p.params[knob]) - num(q.params[knob])); a = { lo: num(s[0].params[knob]), hi: num(s[s.length - 1].params[knob]), loT: show(s[0].params[knob]), hiT: show(s[s.length - 1].params[knob]) }; }
      else if (prev) a = prev;
      else if (vals.length) a = spec.min != null && spec.max != null ? { lo: num(spec.min), hi: num(spec.max), loT: show(spec.min), hiT: show(spec.max), brief: true } : { lo: num(vals[0]), hi: num(vals[0]), loT: show(vals[0]), hiT: '' };
      const stacks = {}; have.forEach(q => { (stacks[String(q.params[knob])] = stacks[String(q.params[knob])] || []).push(q); });
      const tall = Math.max(1, ...Object.values(stacks).map(s => s.length)) * 10 + 8, top = y + 14, ay = top + tall, name = c.t.n ? 'turn ' + c.t.n : 'start';
      const note = !have.length ? `${plural(c.sims.length, 'simulation')}: the value of ${knob} in ${c.sims.length === 1 ? 'it' : 'them'} is not recorded`
        : vals.length > 1 ? `${plural(have.length, 'simulation')} on ${vals.length} values`
        : `${plural(have.length, 'simulation')} at ${show(vals[0])}${c.t.exp.by === 'harness' ? ': the baseline, run by the harness' : others.length ? '; this turn varied ' + others.join(', ') : '; this turn varied no knob'}`;
      let row = `<text x="4" y="${ay + 4}" class="kt">${name}</text>`;
      if (a) {
        if (prev && !a.cat) { const lo = Math.max(a.lo, prev.lo), hi = Math.min(a.hi, prev.hi);  // the part of the previous axis this one covers
          if (lo <= hi) row += [lo, hi].map(v => `<line class="kj" x1="${at(prev, v).toFixed(1)}" y1="${prev.y}" x2="${at(a, v).toFixed(1)}" y2="${ay}"/>`).join(''); }
        else if (prev) row += [L, W - R].map(x => `<line class="kj" x1="${x}" y1="${prev.y}" x2="${x}" y2="${ay}"/>`).join('');
        row += `<line class="ka" x1="${L}" x2="${W - R}" y1="${ay}" y2="${ay}"/>`;
        if (a.cat) row += a.cat.map(v => `<line class="ka" x1="${pos(a, v)}" x2="${pos(a, v)}" y1="${ay}" y2="${ay + 4}"/><text x="${pos(a, v)}" y="${ay + 15}" text-anchor="middle">${e(show(v).replace(/^Tcp/, ''))}</text>`).join('');
        else row += `<text x="${L - 8}" y="${ay + 4}" text-anchor="end" class="ke">${e(a.loT)}</text><text x="${W - R + 8}" y="${ay + 4}" class="ke">${e(a.hiT)}</text>`;
        const inside = v => (a.cat ? a.cat.includes(String(v)) : num(v) >= a.lo && num(v) <= a.hi);
        if (best != null && inside(best)) { row += `<line x1="${pos(a, best)}" x2="${pos(a, best)}" y1="${top - 4}" y2="${ay}" stroke="var(--by-operator)" stroke-width="1.5" stroke-dasharray="4 3"><title>the best row of the sweep: ${e(knob)} ${e(show(best))}</title></line>${bestSaid ? '' : `<text x="${pos(a, best) + 5}" y="${top + 2}" style="fill:var(--text-primary)">best row of the sweep: ${e(show(best))}</text>`}`; bestSaid = true; }
        Object.entries(stacks).forEach(([v, qs]) => qs.forEach((q, i) => { const cx = pos(a, q.params[knob]).toFixed(1), cy = ay - 7 - i * 10, ok = !!(g && q.metrics && EV.meets(q.metrics, g.conds)), ret = !!q.same_as; anyRet = anyRet || ret;
          row += `<g data-act="open" data-t="sim" data-id="${e(q.id)}" data-v="${e(v)}" data-ok="${g ? +ok : ''}" data-ret="${+ret}"><circle cx="${cx}" cy="${cy}" r="7" fill="transparent"/><circle cx="${cx}" cy="${cy}" r="4" fill="${!g || ok ? col : 'var(--surface-1)'}" stroke="${!g || ok ? 'var(--surface-1)' : col}" stroke-width="${!g || ok ? 1.2 : 1.8}"/>
            ${ret ? `<circle cx="${+cx + 4.6}" cy="${cy - 4.2}" r="2.4" fill="var(--surface-1)" stroke="var(--text-primary)" stroke-width="1.1"/>` : ''}<title>${e(`${q.id} · ${q.label || ''} · ${knob} ${show(v)}${g ? (ok ? ' · meets' : q.metrics ? ' · does not meet' : ' · no measurements, so it does not meet') + " the brief's conditions" : ''}${ret ? ` · returned from ${q.same_as}, not run again` : ''}`)}</title></g>`; }));
      }
      svg += `<g class="kn-row" data-turn="${c.t.n}" data-n="${have.length}" data-values="${vals.length}" data-lo="${a && !a.cat ? e(a.loT) : ''}" data-hi="${a && !a.cat ? e(a.hiT) : ''}">${row}<text x="${L}" y="${ay + (a && a.cat ? 28 : 16)}" class="kn">${e(note)}</text></g>`;
      if (a) prev = { ...a, y: ay }; y = ay + (a && a.cat ? 36 : 24);
    });
    const begun = t => (t.steps[0] ? t.steps[0].k : 0) <= (S.step == null ? Infinity : S.step), none = M.turns.filter(t => t.n > 0 && begun(t) && !rows.some(c => c.t === t)).map(t => t.n);
    const key = [g ? `<span>● meets the brief's conditions${g.text ? ' (' + e(g.text) + ')' : ''}</span><span>○ does not</span>` : '<span>● a simulation · not applicable: the goal is chosen by the model, so no dot is marked as meeting it</span>',
      anyRet ? '<span><b style="font-size:9px;vertical-align:super">○</b> beside a dot: returned from an earlier one, not run again</span>' : '', rows.length > 1 ? '<span>the lines join each axis to the part of the previous axis it covers</span>' : '',
      best != null ? '<span><span style="color:var(--by-operator)">- -</span> the best row of the sweep (operator column)</span>' : '', none.length ? `<span>no simulations in turn${none.length === 1 ? '' : 's'} ${none.join(', ')}</span>` : ''].join('');
    return `<div class="ev-card noprint" id="s-knob">${head}
      <p><label>Knob <select data-ch="knob">${K.names.map(k => `<option value="${e(k)}"${k === knob ? ' selected' : ''}>${e(k)} · varied in ${plural(K.varies(k), 'experiment')}</option>`).join('')}</select></label> <span class="sm">shown at first: the knob that most ${EV.term('Experiment', 'experiments')} vary</span></p>
      <div class="ev-scroll"><svg class="kn" viewBox="0 0 ${W} ${y}" width="100%" style="max-width:900px" role="img" aria-label="The simulations of each turn along ${e(knob)}">${svg}</svg></div>
      <p class="sm gl-key">${key}</p></div>`;
  },
});
EV.chg = Object.assign(EV.chg || {}, { knob(t) { EV.s.knob = t.value; EV.draw(); } });
