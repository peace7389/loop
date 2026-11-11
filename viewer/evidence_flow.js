// View 3: one test as a flow chart, left to right: hypothesis → decision rule (with its rival) → the simulations this
// rule names → did the rule hold? → verdict → next → the hypothesis that followed. A test is one hypothesis put to one
// decision rule; EV_DATA derives it from the records. Below: the chart of the judged measure (Chart.js), one point per
// simulation, the control marked, the rule's threshold drawn; for a test or, on request, for a whole experiment.
// ======================================================================================================
Object.assign(EV, {
  // the verdict disagrees with its check: supported although a check failed, or refuted although every check held
  contradicts(v, cs) { if (!v || !cs.length) return false; const all = cs.every(c => c.result === 'held'); return (v.result === 'supported' && !all) || (v.result === 'refuted' && all); },
  // the hypotheses that followed a test: those that name its check, its verdict or its simulations in what they follow
  // from; if none does, those that name the table of the experiment it was run in
  followers(T) {
    const M = EV.M, x = M.expById[T.exp], own = new Set([...(T.check ? [T.check.id] : []), ...(T.verdict ? [T.verdict.id] : []), ...T.sims.map(s => s.id)]);
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

  viewTest(T) {
    const M = EV.M, e = EV.e, S = EV.s, x = M.expById[T.exp], h = M.hypById[T.hyp], C = [0, 152, 326, 492, 616, 770, 924], CW = [130, 152, 144, 100, 132, 132, 112];
    const BH = 84, top = 22, n = T.sims.length, simH = Math.max(BH, 50 + 15 * n + (T.missing.length ? 15 : 0)), H = top + Math.max(BH + 70, simH + 8), y = top, mid = y + BH / 2, ks = M.recStep[x.id] ?? 0;
    const simEnd = T.sims.reduce((a, s) => (s.ts > a ? s.ts : a), ''), first = T.ts && simEnd && T.ts <= simEnd, simK = Math.max(ks, ...T.sims.map(s => M.recStep[s.id] ?? 0));
    const a = (x1, y1, x2, y2, k) => `<path class="edge" data-step="${k}" d="M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2 - 2},${y2}" marker-end="url(#ev-ah)"/>`;
    const fo = (xx, yy, w, hh, html, k) => `<foreignObject data-step="${k}" x="${xx}" y="${yy}" width="${w}" height="${hh}"><div xmlns="http://www.w3.org/1999/xhtml" class="bt sm" style="padding:2px 0">${html}</div></foreignObject>`;
    const cut = (s, m) => { s = String(s || ''); return s.length > m ? s.slice(0, m - 1) + '…' : s; };
    const atK = S.step == null ? null : EV_DATA.stateAt(M, S.step), st = h ? (atK ? atK[h.id] || 'open' : h.state) : 'not recorded';  // during the replay: the state at that step
    const cs = T.check ? [T.check] : [], v = T.verdict, bad = EV.contradicts(v, cs), kc = T.check ? M.recStep[T.check.id] ?? simK : simK, kv = v ? M.recStep[v.id] ?? kc : kc;
    const res = T.check ? T.check.result : T.rule ? 'not checked' : 'no rule', fill = res === 'held' ? 'var(--good)' : res === 'failed' ? 'var(--critical)' : 'var(--warning)', dx = C[3] + CW[3] / 2;
    let svg = EV.box(C[0], y, CW[0], BH, 'model', `${EV_ICON.hypothesis} <b>${e(T.hyp)}</b> · ${e(st)}<br><small>${e(cut(h && h.text, 80))}</small>`, `data-act="open" data-t="hyp" data-id="${e(T.hyp)}" data-step="${M.recStep[T.hyp] ?? 0}"`, h ? EV.stCls(st) : '');
    svg += a(C[0] + CW[0], mid, C[1], mid, ks);
    svg += EV.box(C[1], y, CW[1], BH, 'model', T.rule ? `⊢ <b>${EV.term('Decision rule', 'decision rule')}</b><br><small>${e(cut(T.rule, 64))}</small>${T.rival ? `<br><small>${EV.term('Rival', 'rival')} would give: ${e(T.rival_predicts || 'not recorded')}</small>` : ''}`
      : `⊢ <b>no decision rule</b><br><small>${EV.nr}</small>`, `data-step="${ks}"`, T.rule ? '' : 'warn');
    if (T.rule) svg += fo(C[1], y + BH + 2, CW[1] + 20, 64, `written ${EV.time(T.ts)} · simulations finished ${EV.time(simEnd)} <span class="${first ? 'ok' : 'warnc'}">${first ? '✓ written first' : '✕ not written first'}</span>`, ks);
    svg += a(C[1] + CW[1], mid, C[2], mid, simK);
    const rows = T.sims.map((q, i) => { const cy = y + 46 + i * 15;
      return `<g data-act="open" data-t="sim" data-id="${e(q.id)}" data-test="${e(T.id)}"><rect x="${C[2] + 6}" y="${cy - 8}" width="${CW[2] - 10}" height="15" fill="transparent"/><circle cx="${C[2] + 14}" cy="${cy}" r="3.6" class="${q.same_as ? '' : 'stripe'}" style="${q.same_as ? 'fill:none;stroke:var(--by-simulator);stroke-width:1.4' : ''}"/>
        <text x="${C[2] + 23}" y="${cy + 4}" style="fill:var(--text-primary)">${e(cut(q.id + ' ' + q.label, 17))}${q.label === T.control ? ' ◇' : ''}</text><title>${e(`${q.id} · ${q.label}${q.label === T.control ? ' · the control' : ''}${q.same_as ? ' · returned from ' + q.same_as : ''}`)}</title></g>`; }).join('');
    svg += `<g data-step="${simK}" data-by="simulator">${EV.box(C[2], y, CW[2], simH, 'simulator', `${EV_ICON.simulation} <b>${n}</b> ${EV.term('Simulation', n === 1 ? 'simulation' : 'simulations')} <small>this rule names</small>`)}${rows}
      ${T.missing.length ? `<text x="${C[2] + 10}" y="${y + simH - 8}" style="fill:var(--warning)">${e(cut('not found: ' + T.missing.join(', '), 24))}</text>` : ''}</g>`;
    svg += a(C[2] + CW[2], mid, C[3] + 8, mid, kc);
    svg += `<g data-step="${kc}"><polygon points="${dx},${mid - 42} ${dx + 48},${mid} ${dx},${mid + 42} ${dx - 48},${mid}" class="bx" style="fill:color-mix(in srgb, ${fill} 18%, var(--surface-1))"/>
      <text x="${dx}" y="${mid - 6}" text-anchor="middle">did the rule hold?</text><text x="${dx}" y="${mid + 12}" text-anchor="middle" style="font-weight:700;fill:var(--text-primary)">${e(res)}</text><title>${e(T.check ? `${T.check.id}: ${T.check.rule} → ${T.check.numbers} → ${T.check.result}` : 'no check')}</title></g>`;
    svg += fo(C[3] - 20, y + BH + 2, CW[3] + 52, 64, T.check ? `with the numbers: ${e(cut(T.check.numbers, 90))}` : T.rule ? `the harness's check: ${EV.nr}` : '', kc);
    svg += a(C[3] + CW[3] - 2, mid, C[4], mid, kv);
    svg += EV.box(C[4], y, CW[4], BH, 'model', v ? `${EV_ICON.verdict} <b>${v.id}</b> · ${e(v.result)}${bad ? ' <span class="warnc">⚠ disagrees with its check</span>' : ''}<br><small>${e(cut(v.because, 70))}</small>`
      : `${EV_ICON.verdict} <b>no verdict</b><br><small>${h && h.verdict ? 'the hypothesis was tested again first' : M.ended ? 'the session ended without one' : 'not given yet'}</small>`, v ? `data-act="open" data-t="log" data-id="${v.turn}" data-step="${kv}"` : `data-step="${kv}"`, bad ? 'warn' : '');
    svg += a(C[4] + CW[4], mid, C[5], mid, kv);
    svg += EV.box(C[5], y, CW[5], BH, 'model', `<b>next</b><br><small>${!v ? 'no verdict, so no next step' : v.next ? e(cut(v.next, 96)) : EV.nr}</small>`, `data-step="${kv}"`);
    const fol = EV.followers(T), fk = Math.max(kv, ...fol.ids.map(id => M.recStep[id] ?? 0));
    svg += a(C[5] + CW[5], mid, C[6], mid, fk);
    svg += EV.box(C[6], y, CW[6], BH, 'model', fol.ids.length ? `followed by<br>${fol.ids.map(id => `<b>${EV_ICON.hypothesis} ${id}</b>`).join(', ')}${fol.via ? `<br><small>through the table ${e(fol.via)}</small>` : ''}` : '<small>no hypothesis followed from it</small>',
      fol.ids.length ? `data-act="open" data-t="hyp" data-id="${fol.ids[0]}" data-step="${fk}"` : `data-step="${fk}"`);
    return `<div class="ev-scroll"><svg width="${C[6] + CW[6] + 4}" height="${H}" role="img" aria-label="Test ${e(T.id)} as a flow chart">${EV.arrowDefs()}<text x="0" y="12" class="sm">${EV_ICON.test} test of ${e(T.hyp)} · in experiment ${e(x.id)} · turn ${x.turn}${x.old ? ' · first format: no check by the harness' : ''}</text>${svg}</svg></div>`;
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
