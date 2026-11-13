// View 3: one test as a flow chart, left to right: hypothesis (its id and state; its text stands above the chart) →
// decision rule (two lines; in full below) → the simulations this rule names → did the rule hold? → verdict → next →
// the hypothesis that followed. A test is one hypothesis put to one
// decision rule; EV_DATA derives it from the records. Below: the chart of the judged measure (Chart.js), one point per
// simulation, the control marked, the rule's threshold drawn; for a test or, on request, for a whole experiment.
// ======================================================================================================
Object.assign(EV, {
  // the verdict disagrees with its check: supported although a check failed, or refuted although every check held
  // (a void check says nothing a verdict could disagree with)
  contradicts(v, cs) { cs = (cs || []).filter(c => !c.void); if (!v || !cs.length) return false; const all = cs.every(c => c.result === 'held'); return (v.result === 'supported' && !all) || (v.result === 'refuted' && all); },
  // the hypotheses that followed a test: those that name its check, its verdict or its simulations in what they follow
  // from; if none does, those that name the table of the experiment it was run in
  followers(T, M = EV.M) {
    const x = M.expById[T.exp], own = new Set([...(T.check ? [T.check.id] : []), ...(T.verdict ? [T.verdict.id] : []), ...T.sims.map(s => s.id)]);
    const cites = set => M.hyps.filter(q => q.id !== T.hyp && (q.follows || []).some(f => set.has(f))).map(q => q.id), direct = cites(own);
    return direct.length ? { ids: direct, via: '' } : { ids: cites(new Set([x.id, ...(x.evidence ? [x.evidence.id] : [])])), via: x.evidence ? x.evidence.id : x.id };
  },
  measureOf(rules) { const t = rules.map(r => r.rule || '').join(' '), m = t.match(/([a-z_0-9]+)@/) || t.match(/\b(udp_\w+|tcp_\w+|link_util|drops_band\d)\b/); return m ? m[1] : 'tcp_goodput_bps'; },
  measuresOf(rule) { return [...new Set([...String(rule || '').matchAll(/\b(udp_goodput_bps|tcp_goodput_bps|udp_loss_frac|drops_band0|drops_band1|tcp_retrans|link_util)\b/g)].map(m => m[1]))]; },
  varying(sims) { return [...new Set(sims.flatMap(s => Object.keys(s.params)))].filter(k => new Set(sims.map(s => JSON.stringify(s.params[k]))).size > 1); },
  compared(T) {  // what a test compared, in a few words: the measures its rule names, at the simulations it names
    const ms = EV.measuresOf(T.rule).map(k => TH_DATA.PLAIN[k] || k).join(', ');
    return !T.rule ? 'no decision rule' : `${ms || 'a measure'} at ${T.labels.length ? T.labels.map(l => l + (l === T.control ? ' (control)' : '')).join(', ') : 'its one simulation'}`;
  },
  tlink: (T, text) => `<a data-act="open" data-t="test" data-id="${EV.e(T.id)}" title="test ${EV.e(T.id)}">${EV_ICON.test} ${text || 'test of ' + EV.e(T.hyp)}</a>`,

  // The chart is drawn to the width of the place it stands in (flowFit, once the HTML is there): its boxes share that
  // width, and where they do not fit in one row the chart continues on the next. Nothing is cut off, nothing scrolls sideways.
  viewTest(T) { return `<div class="t-flow" data-test="${EV.e(T.id)}"></div>`; },
  flowFit() {
    document.querySelectorAll('#ev .t-flow').forEach(el => { const T = EV.M.testById[el.dataset.test];
      for (let i = 0; T && i < 2 && Number(el.dataset.w) !== el.clientWidth; i++) { el.dataset.w = el.clientWidth; el.innerHTML = EV.flowSvg(T, el.clientWidth); } });  // twice: the chart's height can bring the pane a scroll bar
  },
  flowSvg(T, W) {
    const M = EV.M, e = EV.e, S = EV.s, x = M.expById[T.exp], h = M.hypById[T.hyp], BH = 84, G = 15, n = T.sims.length, simH = Math.max(BH, 50 + 15 * n + (T.missing.length ? 15 : 0)), ks = M.recStep[x.id] ?? 0;
    const simEnd = T.sims.reduce((a, s) => (s.ts > a ? s.ts : a), ''), first = T.ts && simEnd && T.ts <= simEnd, simK = Math.max(ks, ...T.sims.map(s => M.recStep[s.id] ?? 0));
    const cut = (s, m) => { s = String(s || ''); return s.length > m ? s.slice(0, Math.max(1, m - 1)) + '…' : s; };
    const atK = S.step == null ? null : EV_DATA.stateAt(M, S.step), st = h ? (atK ? atK[h.id] || 'open' : h.state) : 'not recorded';  // during the replay: the state at that step
    const cs = T.check ? [T.check] : [], v = T.verdict, bad = EV.contradicts(v, cs), kc = T.check ? M.recStep[T.check.id] ?? simK : simK, kv = v ? M.recStep[v.id] ?? kc : kc;
    const res = T.check ? T.check.result : T.rule ? 'not checked' : 'no rule', fol = EV.followers(T), fk = Math.max(kv, ...fol.ids.map(id => M.recStep[id] ?? 0));
    // the boxes in order: name, smallest width, share of the room left over, height, the step from which it can be read
    const B = [['hyp', 92, 0, BH, M.recStep[T.hyp] ?? 0], ['rule', 142, 2, BH, ks], ['sims', 128, 1, simH, simK], ['check', 96, 0, BH, kc], ['verdict', 134, 2, BH, kv], ['next', 138, 3, BH, kv], ['fol', 108, 1, BH, fk]].map(([k, w, g, hh, step]) => ({ k, w, g, h: hh, step }));
    const rows = [[]]; B.forEach(b => { const r = rows[rows.length - 1]; if (r.length && r.reduce((a, q) => a + q.w + G, 0) + b.w > W - 12) rows.push([b]); else r.push(b); });
    let y = 22; rows.forEach(r => { const spare = W - (rows.length > 1 ? 12 : 2) - r.reduce((a, q) => a + q.w, 0) - G * (r.length - 1), gs = r.reduce((a, q) => a + q.g, 0); let xx = 0;
      r.forEach(b => { b.w += gs ? Math.floor(spare * b.g / gs) : 0; b.x = xx; b.y = y; xx += b.w + G; }); r.y = y; r.h = Math.max(...r.map(b => b.h), BH + (r.some(b => (b.k === 'rule' && T.rule) || b.k === 'check') ? 62 : 0)); y += r.h + 24; });
    const fo = (xx, yy, w, html, k) => `<foreignObject data-step="${k}" x="${xx}" y="${yy}" width="${w}" height="60"><div xmlns="http://www.w3.org/1999/xhtml" class="bt sm lc3" style="padding:2px 0;height:auto">${html}</div></foreignObject>`;
    const draw = { hyp: b => EV.box(b.x, b.y, b.w, BH, 'model', `${EV_ICON.hypothesis} <b>${e(T.hyp)}</b><br>${e(st)}`, `data-act="open" data-t="hyp" data-id="${e(T.hyp)}" data-step="${b.step}"`, h ? EV.stCls(st) : ''),
      rule: b => EV.box(b.x, b.y, b.w, BH, 'model', T.rule ? `⊢ <b>${EV.term('Decision rule', 'decision rule')}</b><br><small class="lc2">${e(T.rule)}</small>` : `⊢ <b>no decision rule</b><br><small>${EV.nr}</small>`, `data-step="${ks}"`, T.rule ? '' : 'warn')
        + (T.rule ? fo(b.x, b.y + BH + 2, b.w, `written ${EV.time(T.ts)} · simulations finished ${EV.time(simEnd)} ${first ? `<span class="rs">${EV.gkey('check')}written first</span>` : EV.warn('not written first')}`, ks) : ''),
      sims: b => `<g data-step="${simK}" data-by="simulator">${EV.box(b.x, b.y, b.w, simH, 'simulator', `${EV_ICON.simulation} <b>${n}</b> ${EV.term('Simulation', n === 1 ? 'simulation' : 'simulations')} <small>this rule names</small>`)}${T.sims.map((q, i) => { const cy = b.y + 46 + i * 15;
          return `<g data-act="open" data-t="sim" data-id="${e(q.id)}" data-test="${e(T.id)}"><rect x="${b.x + 6}" y="${cy - 8}" width="${b.w - 10}" height="15" fill="transparent"/>${EV.gks(q.same_as ? 'sim-returned' : 'sim', b.x + 8, cy - 6, 12, ' style="color:var(--by-simulator)"')}
            <text x="${b.x + 23}" y="${cy + 4}" style="fill:var(--text-primary)${q.label === T.control ? ';font-weight:700' : ''}">${e(cut(q.id + ' ' + q.label, Math.floor((b.w - 28) / 6.3)))}</text><title>${e(`${q.id} · ${q.label}${q.label === T.control ? ' · the control' : ''}${q.same_as ? ' · returned from ' + q.same_as : ''}`)}</title></g>`; }).join('')}
        ${T.missing.length ? `<text x="${b.x + 10}" y="${b.y + simH - 8}" style="fill:var(--warning)">${e(cut('not found: ' + T.missing.join(', '), Math.floor((b.w - 14) / 6)))}</text>` : ''}</g>`,
      check: b => { const dx = b.x + b.w / 2, mid = b.y + BH / 2, nx = Math.max(0, b.x - 12), nw = Math.min(b.w + 58, W - nx);
        return `<g data-step="${kc}"><polygon points="${dx},${mid - 42} ${dx + 48},${mid} ${dx},${mid + 42} ${dx - 48},${mid}" class="bx"/>
          <text x="${dx}" y="${mid - 6}" text-anchor="middle">did the rule hold?</text>${T.check ? EV.gks(EV.ck(res), dx - res.length * 3.2 - 9, mid + 2, 12) : ''}<text x="${dx + (T.check ? 7 : 0)}" y="${mid + 12}" text-anchor="middle" style="fill:var(--text-primary)">${e(res)}</text><title>${e(T.check ? `${T.check.id}: ${T.check.rule} → ${T.check.numbers} → ${T.check.result}` : 'no check')}</title></g>`
          + fo(nx, b.y + BH + 2, nw, T.check ? (T.check.void ? `<span data-void="1">${EV.VOID}</span>` : `with the numbers: ${e(T.check.numbers)}`) : T.rule ? `the harness's check: ${EV.nr}` : '', kc); },
      verdict: b => EV.box(b.x, b.y, b.w, BH, 'model', v ? `${EV_ICON.verdict} <b>${v.id}</b> · ${EV.verdictRes(v.result)}${EV.rests(v)}${bad ? ' ' + EV.warn('disagrees with its check') : ''}<br><small class="${bad ? 'lc2' : 'lc3'}">${e(v.because)}</small>`
        : `${EV_ICON.verdict} <b>no verdict</b><br><small>${h && h.verdict ? 'the hypothesis was tested again first' : M.ended ? 'the session ended without one' : 'not given yet'}</small>`, v ? `data-act="open" data-t="log" data-id="${v.turn}" data-step="${kv}"` : `data-step="${kv}"`, bad ? 'warn' : ''),
      next: b => EV.box(b.x, b.y, b.w, BH, 'model', `<b>next</b><br><small class="lc4">${!v ? 'no verdict, so no next step' : v.next ? e(v.next) : EV.nr}</small>`, `data-step="${kv}"`),
      fol: b => EV.box(b.x, b.y, b.w, BH, 'model', fol.ids.length ? `followed by<br>${fol.ids.map(id => `<b>${EV_ICON.hypothesis} ${id}</b>`).join(', ')}${fol.via ? `<br><small>through the table ${e(fol.via)}</small>` : ''}` : '<small>no hypothesis followed from it</small>',
        fol.ids.length ? `data-act="open" data-t="hyp" data-id="${fol.ids[0]}" data-step="${fk}"` : `data-step="${fk}"`) };
    // the arrows: along a row; from the end of a row round to the start of the next
    const edge = (d, k) => `<path class="edge" data-step="${k}" d="${d}" marker-end="url(#ev-ah)"/>`;
    const svg = rows.map((r, i) => r.map((b, j) => { const mid = b.y + BH / 2, p = j ? r[j - 1] : i ? rows[i - 1][rows[i - 1].length - 1] : null, inset = q => (q.k === 'check' ? q.w / 2 - 48 : 0);
      return (!p ? '' : j ? edge(`M${p.x + p.w - inset(p)},${mid} H${b.x + inset(b) - 2}`, b.step) : edge(`M${p.x + p.w - inset(p)},${p.y + BH / 2} h${8 + inset(p)} V${b.y - 12} H${b.x + b.w / 2} V${b.y - 2}`, b.step)) + draw[b.k](b); }).join('')).join('');
    return `<svg width="${W}" height="${y - 16}" role="img" aria-label="Test ${e(T.id)} as a flow chart">${EV.arrowDefs()}<text x="0" y="12" class="sm">${EV_ICON.test} test of ${e(T.hyp)} · in experiment ${e(x.id)} · turn ${x.turn}${x.old ? ' · first format: no check by the harness' : ''}</text>${svg}</svg>`;
  },

  // ---- the judged measure, one point per simulation, the control marked, the decision rule's threshold as a line
  unit(k) { return /_bps$/.test(k) ? ['Mbps', v => v / 1e6] : ['udp_loss_frac', 'link_util'].includes(k) ? ['%', v => 100 * v] : ['', v => v]; },
  thresholds(x, k, rules) {  // the rules' comparisons of the judged measure with something the page can work out
    const lab = Object.fromEntries(x.sims.map(s => [s.label, s.metrics || {}])), out = [];
    rules.forEach(r => String(r.rule || '').split(/\s+(?:AND|OR)\s+|&&|\|\|/i).forEach(cl => {
      const p = cl.replace(/[()]/g, ' ').split(/(<=|>=|==|<|>)/); if (p.length !== 3) return;
      const val = s => { try { const t = s.replace(/([A-Za-z_][A-Za-z0-9_]*)@([A-Za-z0-9_]+)/g, (m0, mk, l) => { const v = (lab[l] || {})[mk]; if (typeof v !== 'number') throw 0; return String(v); });
        return TH_DATA.calc(t, {}).v; } catch (q) { return null; } };
      const isK = s => new RegExp('^' + k + '(@[A-Za-z0-9_]+)?$').test(s.trim());
      if (isK(p[0])) { const v = val(p[2]); if (v != null) out.push({ v, op: p[1], for: r.for }); } else if (isK(p[2])) { const v = val(p[0]); if (v != null) out.push({ v, op: { '<': '>', '>': '<', '<=': '>=', '>=': '<=' }[p[1]] || p[1], for: r.for }); } }));
    return out.filter((q, i) => out.findIndex(o => o.v === q.v && o.op === q.op) === i);
  },
  // o: the experiment x, the simulations to draw, the decision rules whose measure and thresholds apply, the control's label, the test (if one)
  chart(cid, o) {
    const x = o.x, k = EV.measureOf(o.rules), vary = EV.varying(o.sims), knob = vary.length === 1 ? vary[0] : null, [u, f] = EV.unit(k), T = TASK_VIEW, el = document.getElementById(cid); if (!el || !window.Chart) return;
    const pts = o.sims.filter(s => s.metrics && typeof s.metrics[k] === 'number'), num = knob && pts.every(s => typeof s.params[knob] === 'number');
    const xv = s => (knob ? (num ? s.params[knob] : String(s.params[knob])) : s.label), col = /^udp|band0/.test(k) ? css('--series-1') : /^tcp|band1/.test(k) ? css('--series-2') : css('--text-secondary');
    const data = q => q.map(s => ({ x: xv(s), y: f(s.metrics[k]), id: s.id, label: s.label })), ctl = pts.filter(s => s.label === o.control), rest = pts.filter(s => !ctl.includes(s));
    const xs = pts.map(xv), lo = num ? Math.min(...xs) : xs[0], hi = num ? Math.max(...xs) : xs[xs.length - 1];
    const lines = EV.thresholds(x, k, o.rules).map(t => ({ label: `decision rule${t.for ? ' for ' + t.for : ''}: ${t.op} ${+f(t.v).toPrecision(6)} ${u}`, guide: true, type: 'line', data: [{ x: lo, y: f(t.v) }, { x: hi, y: f(t.v) }],
      borderColor: css('--text-muted'), borderDash: [5, 4], borderWidth: 1.5, pointRadius: 0, pointHoverRadius: 0 }));
    T._last = [document.getElementById('ev')];
    const across = knob ? (TH_DATA.KNOB[knob] || knob) + ` (${knob})` : vary.length ? `simulation (they differ in ${vary.join(', ')})` : 'simulation';
    const ch = new Chart(el, { type: 'scatter', plugins: [T._bg], data: { labels: num ? undefined : [...new Set(xs)], datasets: [
      { label: 'simulations', data: data(rest), backgroundColor: col, borderColor: css('--surface-1'), borderWidth: 2, pointRadius: 6, pointHoverRadius: 8 },
      ...(ctl.length ? [{ label: `control (${o.control})`, data: data(ctl), backgroundColor: css('--surface-1'), borderColor: col, borderWidth: 2.5, pointRadius: 8, pointHoverRadius: 10, pointStyle: 'rectRot' }] : []), ...lines] },
      options: T._options(`${TH_DATA.PLAIN[k] || k}${u ? ', ' + u : ''}`, across, '', opt => {
        if (!num) { opt.scales.x.type = 'category'; opt.scales.x.offset = true; } opt.plugins.legend.display = ctl.length > 0 || lines.length > 0;
        opt.plugins.tooltip.filter = it => !it.dataset.guide;
        opt.plugins.tooltip.callbacks = { title: its => its.map(it => `${it.raw.id} · ${it.raw.label}`).join(', '), label: it => ` ${knob ? knob + ' ' + it.raw.x + ' → ' : ''}${(TH_DATA.PLAIN[k] || k)} ${(+it.raw.y.toPrecision(7)).toLocaleString('en-US')} ${u}` };
        opt.onClick = (ev, items) => { const it = items.find(q => !ch.data.datasets[q.datasetIndex].guide); if (it) { EV.s.sel = { t: 'sim', id: ch.data.datasets[it.datasetIndex].data[it.index].id, test: o.test || undefined }; EV.draw(); } };
        opt.onHover = (ev, items) => { ev.native.target.style.cursor = items.length ? 'pointer' : 'default'; }; }) });
    ch.thFile = `${o.test || x.id}-${k}`; T._charts[cid] = ch;
  },
});
// the pictures of a session's page are drawn to the width they have: when the window changes, they are drawn again (not while the reader types in a field)
// Only when the width really changed, and never while an evidence sheet is laid out for printing (a redraw would empty it).
window.addEventListener('resize', () => { clearTimeout(EV._rz); EV._rz = setTimeout(() => { const a = document.activeElement, w = window.innerWidth, same = w === EV._w; EV._w = w;
  if (!same && EV.s.view === 'session' && EV.M && !document.getElementById('ev').classList.contains('sheet') && !window.matchMedia('print').matches && !(a && ['INPUT', 'TEXTAREA'].includes(a.tagName))) EV.draw(); }, 150); });
EV._w = window.innerWidth;
