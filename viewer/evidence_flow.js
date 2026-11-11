// View 3: one experiment as a flow chart, left to right: hypothesis → decision rule → simulations → did the rule hold?
// → verdict → next → what followed. One row per hypothesis tested; the simulations box is shared. Below it, the chart
// of the judged measure against the varied knob (Chart.js), one point per simulation, the decision rule's threshold drawn.
// ======================================================================================================
Object.assign(EV, {
  // the verdict disagrees with its check: supported although a check failed, or refuted although every check held
  contradicts(v, cs) { if (!v || !cs.length) return false; const all = cs.every(c => c.result === 'held'); return (v.result === 'supported' && !all) || (v.result === 'refuted' && all); },
  followers(x, hid) {  // the hypotheses that name this hypothesis's verdict or checks, or this experiment's records, in what they follow from
    const M = EV.M, own = new Set([x.id, ...(x.evidence ? [x.evidence.id] : []), ...x.sims.map(s => s.id), ...x.checks.filter(c => !hid || c.for === hid).map(c => c.id)]);
    const h = hid && M.hypById[hid]; if (h && h.verdict) own.add(h.verdict.id);
    return M.hyps.filter(q => (q.follows || []).some(f => own.has(f))).map(q => q.id);
  },
  measureOf(x) { const t = x.rules.map(r => r.rule || '').join(' '), m = t.match(/([a-z_]+)@/) || t.match(/\b(udp_\w+|tcp_\w+|link_util|drops_band\d)\b/); return m ? m[1] : 'tcp_goodput_bps'; },
  knobOf(x) { if (x.varied && x.varied.length) return x.varied[0];
    const ks = [...new Set(x.sims.flatMap(s => Object.keys(s.params)))]; return ks.find(k => new Set(x.sims.map(s => JSON.stringify(s.params[k]))).size > 1) || null; },

  viewExp(x) {
    const M = EV.M, e = EV.e, S = EV.s, rows = x.tests.length ? x.tests : [null], C = [0, 152, 326, 470, 594, 748, 902], CW = [130, 152, 122, 100, 132, 132, 112];
    const BH = 84, P = 156, top = 22, H = top + rows.length * P, ks = M.recStep[x.id] ?? 0;
    const simEnd = x.sims.reduce((a, s) => (s.ts > a ? s.ts : a), ''), ruleTs = x.ts, first = !x.rules.length || (ruleTs && simEnd && ruleTs <= simEnd);
    const a = (x1, y1, x2, y2, k) => `<path class="edge" data-step="${k}" d="M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2 - 2},${y2}" marker-end="url(#ev-ah)"/>`;
    const fo = (xx, y, w, h, html, k) => `<foreignObject data-step="${k}" x="${xx}" y="${y}" width="${w}" height="${h}"><div xmlns="http://www.w3.org/1999/xhtml" class="bt sm" style="padding:2px 0">${html}</div></foreignObject>`;
    const cut = (s, n) => { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; };
    const sy = top + (rows.length * P - 24) / 2 - 50, simK = Math.max(...x.sims.map(s => M.recStep[s.id] ?? 0), 0), per = Math.floor((CW[2] - 14) / 10);
    const dots = x.sims.map((q, i) => { const cx = C[2] + 11 + (i % per) * 10, cy = sy + 62 + Math.floor(i / per) * 10;
      return `<g data-act="open" data-t="sim" data-id="${e(q.id)}"><circle cx="${cx}" cy="${cy}" r="6" fill="transparent"/><circle cx="${cx}" cy="${cy}" r="3.6" class="${q.same_as ? '' : 'stripe'}" style="${q.same_as ? 'fill:none;stroke:var(--by-simulator);stroke-width:1.4' : ''}"/><title>${e(q.id + ' · ' + (q.label || '') + (q.same_as ? ' · returned from ' + q.same_as : ''))}</title></g>`; }).join('');
    const reused = x.sims.filter(s => s.same_as).length, simH = 66 + Math.ceil(x.sims.length / per) * 10;
    let svg = `<g data-step="${simK}" data-by="simulator">${EV.box(C[2], sy, CW[2], simH, 'simulator', `${EV_ICON.simulation} <b>${x.sims.length}</b> ${EV.term('Simulation', x.sims.length === 1 ? 'simulation' : 'simulations')}${reused ? `<br><small>${reused} returned from earlier ones</small>` : ''}<br><small>finished ${EV.time(simEnd)}</small>`, `data-act="open" data-t="exp" data-id="${x.id}"`)}${dots}</g>`;
    const atK = S.step == null ? null : EV_DATA.stateAt(M, S.step), stOf = h => (atK ? atK[h.id] || 'open' : h.state);  // during the replay: the state at that step
    rows.forEach((hid, i) => {
      const y = top + i * P, h = hid && M.hypById[hid], mid = y + BH / 2, rules = x.rules.filter(r => !hid || r.for === hid), cs = x.checks.filter(c => !hid || c.for === hid);
      const v = h && h.verdict && h.verdict.turn > x.turn ? h.verdict : null, bad = EV.contradicts(v, cs), kc = Math.max(...cs.map(c => M.recStep[c.id] ?? 0), simK), kv = v ? M.recStep[v.id] ?? 0 : kc;
      const held = cs.filter(c => c.result === 'held').length, res = !cs.length ? (rules.length ? 'not checked' : 'no rule') : held === cs.length ? 'held' : held ? `${held} of ${cs.length} held` : 'failed';
      svg += EV.box(C[0], y, CW[0], BH, hid ? 'model' : x.by, hid ? `${EV_ICON.hypothesis} <b>${hid}</b> · ${e(h ? stOf(h) : 'not recorded')}<br><small>${e(cut(h && h.text, 80))}</small>` : `${EV_ICON.experiment} <b>${x.kind === 'explore' ? 'question' : 'baseline'}</b><br><small>${e(cut(x.question, 90)) || EV.nr}</small>`,
        hid ? `data-act="open" data-t="hyp" data-id="${hid}" data-step="${M.recStep[hid] ?? 0}"` : `data-step="${ks}"`, h ? EV.stCls(stOf(h)) : '');
      svg += a(C[0] + CW[0], mid, C[1], mid, ks);
      svg += EV.box(C[1], y, CW[1], BH, 'model', rules.length ? `⊢ <b>${EV.term('Decision rule', 'decision rule')}</b>${rules.length > 1 ? ` (${rules.length})` : ''}<br><small>${e(cut(rules[0].rule, 64))}</small>${rules[0].rival ? `<br><small>${EV.term('Rival', 'rival')} would give: ${e(rules[0].rival_predicts || EV.nr)}</small>` : ''}`
        : `⊢ <b>no decision rule</b><br><small>${x.kind === 'explore' ? 'an exploration' : x.by === 'harness' ? 'the baseline' : 'none was stated'}</small>`, `data-step="${ks}"`, rules.length ? '' : 'warn');
      if (rules.length) svg += fo(C[1], y + BH + 2, CW[1] + 20, 64, `written ${EV.time(ruleTs)} · simulations finished ${EV.time(simEnd)} <span class="${first ? 'ok' : 'warnc'}">${first ? '✓ written first' : '✕ not written first'}</span>`, ks);
      svg += a(C[1] + CW[1], mid, C[2], Math.min(Math.max(mid, sy + 10), sy + simH - 10), simK);
      const dx = C[3] + CW[3] / 2, fill = res === 'held' ? 'var(--good)' : res === 'failed' ? 'var(--critical)' : 'var(--warning)';
      svg += a(C[2] + CW[2], Math.min(Math.max(mid, sy + 10), sy + simH - 10), C[3] + 8, mid, kc);
      svg += `<g data-step="${kc}" data-act="open" data-t="exp" data-id="${x.id}"><polygon points="${dx},${mid - 42} ${dx + 48},${mid} ${dx},${mid + 42} ${dx - 48},${mid}" class="bx" style="fill:color-mix(in srgb, ${fill} 18%, var(--surface-1))"/>
        <text x="${dx}" y="${mid - 6}" text-anchor="middle">did the rule hold?</text><text x="${dx}" y="${mid + 12}" text-anchor="middle" style="font-weight:700;fill:var(--text-primary)">${e(res)}</text><title>${e(cs.map(c => `${c.id}: ${c.rule} → ${c.numbers} → ${c.result}`).join('\n') || 'no check')}</title></g>`;
      if (cs.length) svg += fo(C[3] - 20, y + BH + 2, CW[3] + 52, 64, `with the numbers: ${e(cut(cs.map(c => c.numbers).join(' · '), 90))}`, kc);
      svg += a(C[3] + CW[3] - 2, mid, C[4], mid, kv);
      svg += EV.box(C[4], y, CW[4], BH, 'model', v ? `${EV_ICON.verdict} <b>${v.id}</b> · ${e(v.result)}${bad ? ' <span class="warnc">⚠ disagrees with its check</span>' : ''}<br><small>${e(cut(v.because, 70))}</small>`
        : `${EV_ICON.verdict} <b>no verdict</b><br><small>${hid ? (M.ended ? 'the session ended without one' : 'not given yet') : 'nothing to judge'}</small>`, v ? `data-act="open" data-t="log" data-id="${v.turn}" data-step="${kv}"` : `data-step="${kv}"`, bad ? 'warn' : '');
      svg += a(C[4] + CW[4], mid, C[5], mid, kv);
      svg += EV.box(C[5], y, CW[5], BH, 'model', `<b>next</b><br><small>${!v ? 'no verdict, so no next step' : v.next ? e(cut(v.next, 96)) : EV.nr}</small>`, `data-step="${kv}"`);
      const fol = EV.followers(x, hid), nx = M.exps.find(q => q.turn > x.turn && q.by !== 'harness'), fk = Math.max(kv, ...fol.map(id => M.recStep[id] ?? 0));
      svg += a(C[5] + CW[5], mid, C[6], mid, fk);
      svg += EV.box(C[6], y, CW[6], BH, fol.length ? 'model' : nx ? 'model' : 'harness', fol.length ? `followed by<br>${fol.map(id => `<b>${EV_ICON.hypothesis} ${id}</b>`).join(', ')}` : nx ? `followed by<br><b>${EV_ICON.experiment} ${nx.id}</b><br><small>the next experiment</small>` : `<small>nothing followed${M.repRec ? '; then the final report' : ''}</small>`,
        fol.length ? `data-act="open" data-t="hyp" data-id="${fol[0]}" data-step="${fk}"` : nx ? `data-act="open" data-t="exp" data-id="${nx.id}" data-step="${M.recStep[nx.id] ?? fk}"` : `data-step="${fk}"`);
    });
    return `<div class="ev-scroll"><svg width="${C[6] + CW[6] + 4}" height="${H}" role="img" aria-label="Experiment ${e(x.id)} as a flow chart">${EV.arrowDefs()}<text x="0" y="12" class="sm">${EV_ICON.experiment} ${EV.term('Experiment', 'experiment')} ${e(x.id)} · ${e(x.kind || 'not recorded')} · turn ${x.turn}${x.old ? ' · first format: one simulation, no check by the harness' : ''}</text>${svg}</svg></div>`;
  },

  // ---- the judged measure against the varied knob: one point per simulation, the control marked, the threshold as a line
  unit(k) { return /_bps$/.test(k) ? ['Mbps', v => v / 1e6] : ['udp_loss_frac', 'link_util'].includes(k) ? ['%', v => 100 * v] : ['', v => v]; },
  thresholds(x, k) {  // the decision rules' comparisons of the judged measure with something the page can work out
    const lab = Object.fromEntries(x.sims.map(s => [s.label, s.metrics || {}])), out = [];
    x.rules.forEach(r => String(r.rule || '').split(/\s+(?:AND|OR)\s+|&&|\|\|/i).forEach(cl => {
      const p = cl.replace(/[()]/g, ' ').split(/(<=|>=|==|<|>)/); if (p.length !== 3) return;
      const side = s => s.trim(), val = s => { try { const t = s.replace(/([A-Za-z_][A-Za-z0-9_]*)@([A-Za-z0-9_]+)/g, (m0, mk, l) => { const v = (lab[l] || {})[mk]; if (typeof v !== 'number') throw 0; return String(v); });
        return TH_DATA.calc(t, {}).v; } catch (q) { return null; } };
      const isK = s => new RegExp('^' + k + '(@[A-Za-z0-9_]+)?$').test(side(s));
      if (isK(p[0])) { const v = val(p[2]); if (v != null) out.push({ v, op: p[1], for: r.for }); } else if (isK(p[2])) { const v = val(p[0]); if (v != null) out.push({ v, op: { '<': '>', '>': '<', '<=': '>=', '>=': '<=' }[p[1]] || p[1], for: r.for }); } }));
    return out.filter((q, i) => out.findIndex(o => o.v === q.v && o.op === q.op) === i);
  },
  expChart(x, cid) {
    const k = EV.measureOf(x), knob = EV.knobOf(x), [u, f] = EV.unit(k), T = TASK_VIEW, el = document.getElementById(cid); if (!el || !window.Chart) return;
    const pts = x.sims.filter(s => s.metrics && typeof s.metrics[k] === 'number'), num = knob && pts.every(s => typeof s.params[knob] === 'number');
    const xv = s => (knob ? (num ? s.params[knob] : String(s.params[knob])) : s.label), col = /^udp|band0/.test(k) ? css('--series-1') : /^tcp|band1/.test(k) ? css('--series-2') : css('--text-secondary');
    const data = q => q.map(s => ({ x: xv(s), y: f(s.metrics[k]), id: s.id, label: s.label })), ctl = pts.filter(s => s.label === x.control), rest = pts.filter(s => !ctl.includes(s));
    const xs = pts.map(xv), lo = num ? Math.min(...xs) : xs[0], hi = num ? Math.max(...xs) : xs[xs.length - 1];
    const lines = EV.thresholds(x, k).map(t => ({ label: `decision rule${t.for ? ' for ' + t.for : ''}: ${t.op} ${+f(t.v).toPrecision(6)} ${u}`, guide: true, type: 'line', data: [{ x: lo, y: f(t.v) }, { x: hi, y: f(t.v) }],
      borderColor: css('--text-muted'), borderDash: [5, 4], borderWidth: 1.5, pointRadius: 0, pointHoverRadius: 0 }));
    T._last = [document.getElementById('ev')];
    const ch = new Chart(el, { type: 'scatter', plugins: [T._bg], data: { labels: num ? undefined : [...new Set(xs)], datasets: [
      { label: 'simulations', data: data(rest), backgroundColor: col, borderColor: css('--surface-1'), borderWidth: 2, pointRadius: 6, pointHoverRadius: 8 },
      ...(ctl.length ? [{ label: `control (${x.control})`, data: data(ctl), backgroundColor: css('--surface-1'), borderColor: col, borderWidth: 2.5, pointRadius: 8, pointHoverRadius: 10, pointStyle: 'rectRot' }] : []), ...lines] },
      options: T._options(`${TH_DATA.PLAIN[k] || k}${u ? ', ' + u : ''}, against ${knob || 'the simulation'}`, knob ? (TH_DATA.KNOB[knob] || knob) + ` (${knob})` : 'simulation', '', o => {
        if (!num) o.scales.x.type = 'category'; o.plugins.legend.display = ctl.length > 0 || lines.length > 0;
        o.plugins.tooltip.filter = it => !it.dataset.guide;
        o.plugins.tooltip.callbacks = { title: its => its.map(it => `${it.raw.id} · ${it.raw.label}`).join(', '), label: it => ` ${knob || 'simulation'} ${it.raw.x} → ${(TH_DATA.PLAIN[k] || k)} ${(+it.raw.y.toPrecision(7)).toLocaleString('en-US')} ${u}` };
        o.onClick = (ev, items) => { const it = items.find(q => !ch.data.datasets[q.datasetIndex].guide); if (it) { EV.s.sel = { t: 'sim', id: ch.data.datasets[it.datasetIndex].data[it.index].id }; EV.draw(); } };
        o.onHover = (ev, items) => { ev.native.target.style.cursor = items.length ? 'pointer' : 'default'; }; }) });
    ch.thFile = `${x.id}-${k}-by-${knob || 'simulation'}`; T._charts[cid] = ch;
  },
});
