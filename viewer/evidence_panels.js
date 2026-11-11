// The experiment panel (View 3, its chart, its simulations and checks) and the result panel of one simulation (settings
// against the control, measurements against the control, the time charts of the run page with their shared time
// marker, PNG / CSV export, a second run to compare). afterDraw draws the Chart.js charts once the HTML is in place.
// ======================================================================================================
Object.assign(EV, {
  series: {},  // "session/run" -> the columns of series.csv, or 'none'
  goal: g => (!g ? 'not recorded' : typeof g !== 'object' ? String(g) : g.target ? `${g.target.direction === 'min' ? 'smallest' : 'largest'} ${g.target.measure}${(g.conditions || []).length ? ' while ' + g.conditions.join(' and ') : ''}` : JSON.stringify(g)),
  expBtns: id => `<div class="exp">save <button data-act="export" data-id="${id}" data-x="png">PNG</button> <button data-act="export" data-id="${id}" data-x="csv">CSV</button></div>`,
  chartJs() {  // Chart.js from the CDN, once; the page is drawn again when it arrives
    if (window.Chart) return true; if (EV.cj) return false; EV.cj = 'loading';
    const s = document.createElement('script'); s.src = TASK_VIEW.CDN; s.onload = () => { EV.cj = 'ready'; EV.draw(); }; s.onerror = () => { EV.cj = 'failed'; }; document.head.appendChild(s); return false;
  },

  expPanel(id) {
    const M = EV.M, e = EV.e, x = M.expById[id]; if (!x) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const ctl = x.sims.find(s => s.label === x.control), k = EV.measureOf(x), [u, f] = EV.unit(k);
    const diff = s => (ctl && s !== ctl ? Object.keys(s.params).filter(q => JSON.stringify(s.params[q]) !== JSON.stringify(ctl.params[q])).map(q => `${q} ${s.params[q]}`).join(', ') || 'same as the control' : s === ctl ? '<b>the control</b>' : EV.nr);
    const sentence = `${x.kind === 'test' ? 'Tests ' + (x.tests.join(', ') || 'not recorded') : x.by === 'harness' ? 'The baseline: ' + (x.question || 'the defaults') : 'Explores: ' + (x.question || 'not recorded')}; ${x.sims.length} simulation${x.sims.length === 1 ? '' : 's'}, varying ${x.varied.join(' and ') || 'nothing recorded'}, against the control “${x.control || 'not recorded'}”.`;
    return `<h2>${EV_ICON.experiment} ${EV.term('Experiment', 'Experiment')} ${e(x.id)}<small>turn ${x.turn} · ${e(x.by)}</small></h2><p>${e(sentence)}</p>${EV.viewExp(x)}
      <div class="ev-top" style="margin-top:8px"><div data-step="${Math.max(0, ...x.sims.map(s => M.recStep[s.id] ?? 0))}">${window.Chart ? `<div class="cv" style="height:250px"><canvas id="ev-xc"></canvas></div>${EV.expBtns('ev-xc')}` : EV.chartJs() ? '' : '<p class="sm">Loading the chart library…</p>'}</div>
        <div><h3>${EV.term('Check', 'checks')} by the harness</h3>${x.checks.length ? `<table><tbody>${x.checks.map(c => `<tr data-step="${M.recStep[c.id] ?? 0}"><td>${EV.link(c.id)} ${e(c.for)}</td><td><code>${e(c.rule)}</code><br><span class="sm">${e(c.numbers)}</span></td><td class="${c.result === 'held' ? 'ok' : 'bad'}">${e(c.result)}</td></tr>`).join('')}</tbody></table>` : `<p class="sm">${x.old ? 'The first format had no checks by the harness: ' + EV.nr : x.rules.length ? EV.nr : 'no decision rule, so nothing to check'}.</p>`}
          <h3>${EV.term('Verdict', 'verdicts')}</h3>${x.tests.map(h => { const H = M.hypById[h], v = H && H.verdict, bad = EV.contradicts(v, x.checks.filter(c => c.for === h));
            return `<p class="sm"${v ? ` data-step="${M.recStep[v.id] ?? 0}"` : ''}>${EV.link(h)}: ${v ? `${EV.link(v.id)} <b>${e(v.result)}</b>${bad ? ' <span class="warnc">⚠ disagrees with its check</span>' : ''}` : 'no verdict'}</p>`; }).join('') || '<p class="sm">nothing tested</p>'}</div></div>
      <h3>its ${EV.term('Simulation', 'simulations')}<span class="sm" style="text-transform:none;letter-spacing:0"> · click one to open it</span></h3>
      <table><thead><tr><th>simulation</th><th>label</th><th>settings against the control</th><th class="num">${e(TH_DATA.PLAIN[k] || k)}${u ? ', ' + u : ''}</th><th>run</th></tr></thead><tbody>${x.sims.map(s => `<tr class="pick" data-act="open" data-t="sim" data-id="${e(s.id)}" data-step="${M.recStep[s.id] ?? 0}">
        <td>${s.same_as ? '○' : EV_ICON.simulation} ${e(s.id)}</td><td>${e(s.label)}</td><td>${diff(s)}</td><td class="num">${s.metrics && typeof s.metrics[k] === 'number' ? (+f(s.metrics[k]).toPrecision(7)).toLocaleString('en-US') : '–'}</td><td>${e(s.run || '')}${s.same_as ? ` <span class="sm">= ${e(s.same_as)}</span>` : ''}</td></tr>`).join('')}</tbody></table>`;
  },

  TIME: [  // the run page's time charts (adrs_view.js), drawn by its TASK_VIEW._time
    { id: 'tput', title: 'Throughput per flow', unit: 'Mbps', lines: S => [['UDP', 1, S.udp.map(v => v / 1e6)], ['TCP', 2, S.tcp.map(v => v / 1e6)]] },
    { id: 'cwnd', title: 'TCP congestion window', unit: 'kB', lines: S => [['TCP window', 2, S.cwnd.map(v => v / 1e3)]] },
    { id: 'd0', title: 'Packets dropped from the UDP queue', unit: 'packets per sample', lines: S => [['UDP queue drops', 1, S.d0]] },
    { id: 'd1', title: 'Packets dropped from the TCP queue', unit: 'packets per sample', lines: S => [['TCP queue drops', 2, S.d1]] },
    { id: 'q', title: 'Packets waiting in each queue', unit: 'packets', need: S => S.q0 && S.q1, lines: S => [['UDP queue', 1, S.q0], ['TCP queue', 2, S.q1]] }],

  simPanel(id) {
    const M = EV.M, S = EV.s, e = EV.e, s = M.simById[id]; if (!s) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const x = M.expById[s.exp], ctl = x && x.sims.find(q => q.label === x.control), m = s.metrics || {}, cm = ctl && ctl.metrics || {};
    const keys = [...new Set(Object.keys(s.params).concat(ctl ? Object.keys(ctl.params) : []))], diff = q => ctl && JSON.stringify(s.params[q]) !== JSON.stringify(ctl.params[q]);
    const meas = Object.keys(m).filter(q => !['link_rate_bps', 'weight_udp'].includes(q)), d = (q) => { if (!ctl || typeof cm[q] !== 'number' || typeof m[q] !== 'number') return '–';
      const [u, f] = EV.unit(q), v = f(m[q]) - f(cm[q]); return (v > 0 ? '+' : v < 0 ? '−' : '±') + (+Math.abs(v).toPrecision(5)).toLocaleString('en-US') + (u ? ' ' + u : ''); };
    const show = (q, v) => { const [u, f] = EV.unit(q); return typeof v !== 'number' ? '–' : (+f(v).toPrecision(7)).toLocaleString('en-US') + (u ? ' ' + u : ''); };
    const others = M.sims.filter(q => q.id !== s.id && q.run && !q.error), sr = EV.series[M.id + '/' + s.run];
    const charts = !s.run ? `<p class="sm">charts over time: ${EV.nr} (no run id)</p>` : sr === 'none' ? `<p class="sm">charts over time: ${EV.nr} (the run has no series.csv)</p>` : !sr || !window.Chart ? (EV.chartJs(), '<p class="sm">Loading the charts…</p>')
      : `<div class="charts" data-by="simulator">${EV.TIME.filter(q => !q.need || q.need(sr)).map(q => `<figure style="margin:0"><div class="cv" style="height:200px"><canvas id="th-c-${q.id}"></canvas></div>${EV.expBtns(q.id)}</figure>`).join('')}</div>`;
    return `<h2>${EV_ICON.simulation} ${EV.term('Simulation', 'Simulation')} ${e(s.id)}<small>label “${e(s.label || '')}” · run ${e(s.run || 'not recorded')} · finished ${EV.time(s.ts)}</small></h2>
      ${s.same_as ? `<p class="sm">○ The result of ${EV.link(s.same_as)} (same settings and seed), returned again: nothing was run, and it was not counted against the budget.</p>` : ''}${s.error ? `<p class="bad">No measurements: ${e(s.error)}</p>` : ''}
      <div class="ev-top"><div><h3>settings${ctl ? ` · against the control ${EV.link(ctl.id)} “${e(ctl.label)}”` : ''}</h3>${ctl ? '' : `<p class="sm">the experiment's control: ${EV.nr}</p>`}
          <table><thead><tr><th>setting</th><th>this simulation</th><th>control</th></tr></thead><tbody>${keys.map(q => `<tr class="${diff(q) ? 'diff' : ''}"><td>${e(TH_DATA.KNOB[q] || q)}</td><td>${e(s.params[q] ?? '–')}${diff(q) ? ' <span class="warnc">≠</span>' : ''}</td><td>${ctl ? e(ctl.params[q] ?? '–') : '–'}</td></tr>`).join('')}</tbody></table></div>
        <div><h3>measurements · difference from the control</h3><table><thead><tr><th>measure</th><th class="num">value</th><th class="num">− control</th></tr></thead><tbody>${meas.map(q => `<tr><td>${e(TH_DATA.PLAIN[q] || q)}</td><td class="num">${show(q, m[q])}</td><td class="num">${s === ctl ? 'the control' : d(q)}</td></tr>`).join('') || `<tr><td colspan="3">${EV.nr}</td></tr>`}</tbody></table></div></div>
      <h3>over time <span class="sm" style="text-transform:none;letter-spacing:0">· point at a chart: the same moment is marked in all of them</span></h3>
      <p class="sm"><label>Compare with <select data-ch="cmp"><option value="">no second simulation</option>${others.map(q => `<option value="${e(q.id)}"${S.cmp === q.id ? ' selected' : ''}>${e(`${q.id} · ${q.label || ''} · run ${q.run}`)}</option>`).join('')}</select></label> (drawn dashed) · UDP blue, TCP orange</p>${charts}`;
  },

  async loadSeries(sim) {
    const key = EV.M.id + '/' + sim.run; if (!sim.run || key in EV.series) return false;
    EV.series[key] = null; const t = await EV.get(`../sessions/${EV.M.id}/runs/${sim.run}/series.csv`), c = t ? TH_DATA.csv(t) : null;
    EV.series[key] = c && c.t && c.t.length > 1 ? c : 'none'; return true;
  },
  // after the HTML is in place: the charts of what is open, and the series still to be fetched
  async afterDraw() {
    const S = EV.s, M = EV.M, T = TASK_VIEW; Object.values(T._charts).forEach(c => { try { c.destroy(); } catch (q) {} }); T._charts = {};
    if (!S.sel || !window.Chart) return; T._last = [document.getElementById('ev')]; T._P = { kind: 'evidence' };
    if (S.sel.t === 'exp' && M.expById[S.sel.id]) EV.expChart(M.expById[S.sel.id], 'ev-xc');
    if (S.sel.t !== 'sim' || !M.simById[S.sel.id]) return;
    const a = M.simById[S.sel.id], b = S.cmp && M.simById[S.cmp];
    const got = (await Promise.all([a, b].filter(Boolean).map(EV.loadSeries))).some(Boolean); if (got) return EV.draw();
    const row = q => { const sr = q && EV.series[M.id + '/' + q.run]; return sr && sr !== 'none' ? { id: `${q.id} (${q.run})`, series: sr } : null; };
    const A = row(a), B = row(b); if (!A || !document.getElementById('th-c-tput')) return;
    T._time(EV.TIME.filter(q => !q.need || [A, B].some(r => r && q.need(r.series))), [A, B].filter(Boolean), B);
  },
  exportChart(id, kind) { TASK_VIEW._export(id, kind); },
});
