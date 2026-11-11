// The experiment panel (the batch: its tests, its simulations, one chart on request) and the result panel of one simulation (settings
// against the control, measurements against the control, the time charts of the run page with their shared time
// marker, PNG / CSV export, a second run to compare). afterDraw draws the Chart.js charts once the HTML is in place.
// ======================================================================================================
Object.assign(EV, {
  series: {},  // "session/run" -> the columns of series.csv, or 'none'
  goal: g => (!g ? 'not recorded' : typeof g !== 'object' ? String(g) : g.target ? `${g.target.direction === 'min' ? 'smallest' : 'largest'} ${g.target.measure}${(g.conditions || []).length ? ' while ' + g.conditions.join(' and ') : ''}` : JSON.stringify(g)),
  expBtns: id => `<div class="exp">save <button data-act="export" data-id="${id}" data-x="png">PNG</button> <button data-act="export" data-id="${id}" data-x="csv">CSV</button></div>`,
  chartJs() {  // Chart.js from the CDN, once; the page is drawn again when it arrives
    if (window.Chart) return true; if (EV.cj) return false; EV.cj = 'loading';
    const s = document.createElement('script'); s.src = window.EV_EXPORT ? EV_EXPORT.chart || 'not-in-this-export.js' : TASK_VIEW.CDN;  // an exported copy has its own copy of the library, or none
    s.onload = () => { EV.cj = 'ready'; EV.draw(); }; s.onerror = () => { EV.cj = 'failed'; EV.draw(); }; document.head.appendChild(s); return false;
  },

  canvas(kind, id, wide) {  // the place of a chart that afterDraw draws: of a test, or of a whole experiment
    const cid = `ev-c-${kind}-${id}`;
    return window.Chart ? `<div class="cv" style="height:240px"><canvas id="${cid}" data-chart="${kind}" data-id="${EV.e(id)}"${wide ? ' data-wide="1"' : ''}></canvas></div>${EV.expBtns(cid)}` : (EV.chartJs(), `<p class="sm">${EV.cj === 'failed' ? 'The chart library is not available here, so this chart is not drawn.' : 'Loading the chart library…'}</p>`);
  },
  // an experiment: the batch of simulations planned in one turn, the tests run in it, and all its simulations
  expPanel(id) {
    const M = EV.M, S = EV.s, e = EV.e, x = M.expById[id]; if (!x) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const ctl = x.sims.find(s => s.label === x.control), ts = M.tests.filter(t => t.exp === id), simK = Math.max(0, ...x.sims.map(s => M.recStep[s.id] ?? 0)), n = x.sims.length;
    const diff = s => (ctl && s !== ctl ? Object.keys(s.params).filter(q => JSON.stringify(s.params[q]) !== JSON.stringify(ctl.params[q])).map(q => `${q} ${s.params[q]}`).join(', ') || 'same as the control' : s === ctl ? '<b>the control</b>' : EV.nr);
    const what = x.by === 'harness' ? `The baseline, run by the harness before the first turn: ${e(x.question || 'every setting at its default')}.`
      : ts.length ? `The batch of ${n} simulation${n === 1 ? '' : 's'} the model planned in turn ${x.turn}, for ${ts.length} ${EV.term('Test', ts.length === 1 ? 'test' : 'tests')}. Varied: ${e(x.varied.join(', ') || 'not recorded')}; control: ${e(x.control || 'not recorded')}.`
      : `An exploration: a batch of ${n} simulation${n === 1 ? '' : 's'} with no tests. Its question: ${e(x.question || 'not recorded')} Varied: ${e(x.varied.join(', ') || 'not recorded')}.`;
    const span = (k, html) => `<span data-step="${k}">${html}</span>`, pc = v => (typeof v === 'number' ? (+(100 * v).toPrecision(4)) + ' %' : '–');
    const rows = ts.map(T => { const kc = T.check ? M.recStep[T.check.id] ?? simK : simK, v = T.verdict;
      return `<tr class="pick" data-act="open" data-t="test" data-id="${e(T.id)}"><td>${EV_ICON.test} <b>${e(T.hyp)}</b></td><td>${e(EV.compared(T))}</td><td>${span(kc, T.check ? `<span class="${T.check.result === 'held' ? 'ok' : 'bad'}">${e(T.check.result)}</span>` : T.rule ? 'not checked' : '–')}</td>
        <td>${v ? span(M.recStep[v.id] ?? kc, `${v.id} ${e(v.result)}${EV.contradicts(v, T.check ? [T.check] : []) ? ' <span class="warnc" title="the verdict disagrees with its check">⚠</span>' : ''}`) : 'no verdict'}</td></tr>`; }).join('');
    return `<h2>${EV_ICON.experiment} ${EV.term('Experiment', 'Experiment')} ${e(x.id)}<small>turn ${x.turn} · ${e(x.by)} · the container its tests were run in</small></h2><p>${what}</p>
      ${ts.length ? `<h3>the tests in it<span class="sm" style="text-transform:none;letter-spacing:0"> · click one to open it</span></h3><table><thead><tr><th>test of</th><th>what was compared</th><th>${EV.term('Check', 'check')}</th><th>${EV.term('Verdict', 'verdict')}</th></tr></thead><tbody>${rows}</tbody></table>` : ''}
      <p class="sm" style="margin-top:8px"><button data-act="xchart" data-id="${e(x.id)}">${S.xchart === x.id ? 'hide the chart' : `show one measure over all ${n} simulations`}</button></p>${S.xchart === x.id ? `<div data-step="${simK}">${EV.canvas('exp', x.id)}</div>` : ''}
      <h3>its ${EV.term('Simulation', 'simulations')}<span class="sm" style="text-transform:none;letter-spacing:0"> · click one to open it</span></h3>
      <table><thead><tr><th>simulation</th><th>label</th><th>settings against the control</th><th>named by the tests of</th><th class="num">UDP loss</th><th class="num">TCP goodput</th><th>run</th></tr></thead><tbody>${x.sims.map(s => `<tr class="pick" data-act="open" data-t="sim" data-id="${e(s.id)}" data-step="${M.recStep[s.id] ?? 0}">
        <td>${s.same_as ? '○' : EV_ICON.simulation} ${e(s.id)}</td><td>${e(s.label)}</td><td>${diff(s)}</td><td>${ts.filter(T => T.sims.includes(s)).map(T => e(T.hyp)).join(', ') || '–'}</td><td class="num">${pc((s.metrics || {}).udp_loss_frac)}</td>
        <td class="num">${s.metrics && typeof s.metrics.tcp_goodput_bps === 'number' ? EV.mb(s.metrics.tcp_goodput_bps) + ' Mbps' : '–'}</td><td>${e(s.run || '')}${s.same_as ? ` <span class="sm">= ${e(s.same_as)}</span>` : ''}</td></tr>`).join('')}</tbody></table>`;
  },

  TIME: [  // the run page's time charts (adrs_view.js), drawn by its TASK_VIEW._time
    { id: 'tput', title: 'Throughput per flow', unit: 'Mbps', lines: S => [['UDP', 1, S.udp.map(v => v / 1e6)], ['TCP', 2, S.tcp.map(v => v / 1e6)]] },
    { id: 'cwnd', title: 'TCP congestion window', unit: 'kB', lines: S => [['TCP window', 2, S.cwnd.map(v => v / 1e3)]] },
    { id: 'd0', title: 'Packets dropped from the UDP queue', unit: 'packets per sample', lines: S => [['UDP queue drops', 1, S.d0]] },
    { id: 'd1', title: 'Packets dropped from the TCP queue', unit: 'packets per sample', lines: S => [['TCP queue drops', 2, S.d1]] },
    { id: 'q', title: 'Packets waiting in each queue', unit: 'packets', need: S => S.q0 && S.q1, lines: S => [['UDP queue', 1, S.q0], ['TCP queue', 2, S.q1]] }],

  // where a simulation's samples over time are: a session's simulation in its runs folder, an operator run under checks/
  srcOf: s => s.src || (s.run ? `../sessions/${EV.M.id}/runs/${s.run}/series.csv` : null),
  // the standard result panel of one simulation: settings against a control, measurements against it, the charts over time
  // o: ctlHead (what the control is, for the heading), ctlName (the column's title), others (simulations to compare with)
  resultPanel(s, ctl, o) {
    const e = EV.e, m = s.metrics || {}, cm = (ctl && ctl.metrics) || {}, src = EV.srcOf(s), sr = src ? EV.series[src] : null;
    const keys = [...new Set(Object.keys(s.params).concat(ctl ? Object.keys(ctl.params) : []))], diff = q => ctl && q in ctl.params && JSON.stringify(s.params[q]) !== JSON.stringify(ctl.params[q]);
    const meas = Object.keys(m).filter(q => !['link_rate_bps', 'weight_udp'].includes(q)), d = (q) => { if (!ctl || typeof cm[q] !== 'number' || typeof m[q] !== 'number') return '–';
      const [u, f] = EV.unit(q), v = f(m[q]) - f(cm[q]); return (v > 0 ? '+' : v < 0 ? '−' : '±') + (+Math.abs(v).toPrecision(5)).toLocaleString('en-US') + (u ? ' ' + u : ''); };
    const show = (q, v) => { const [u, f] = EV.unit(q); return typeof v !== 'number' ? '–' : (+f(v).toPrecision(7)).toLocaleString('en-US') + (u ? ' ' + u : ''); };
    const charts = !src ? `<p class="sm">charts over time: ${EV.nr} (no run id)</p>` : sr === 'none' ? `<p class="sm">charts over time: ${EV.nr} (the run has no series.csv)</p>` : !sr || !window.Chart ? (EV.chartJs(), `<p class="sm">${EV.cj === 'failed' ? 'The chart library is not available here, so the charts over time are not drawn.' : 'Loading the charts…'}</p>`)
      : `<div class="charts" data-by="simulator">${EV.TIME.filter(q => !q.need || q.need(sr)).map(q => `<figure style="margin:0"><div class="cv" style="height:200px"><canvas id="th-c-${q.id}"></canvas></div>${EV.expBtns(q.id)}</figure>`).join('')}</div>`;
    return `<div class="ev-top"><div><h3>settings${ctl ? ' · against ' + o.ctlHead : ''}</h3>${ctl ? '' : `<p class="sm">the experiment's control: ${EV.nr}</p>`}
          <table><thead><tr><th>setting</th><th>this simulation</th><th>${e(o.ctlName || 'control')}</th></tr></thead><tbody>${keys.map(q => `<tr class="${diff(q) ? 'diff' : ''}"><td>${e(TH_DATA.KNOB[q] || q)}</td><td>${e(s.params[q] ?? '–')}${diff(q) ? ' <span class="warnc">≠</span>' : ''}</td><td>${ctl ? e(ctl.params[q] ?? '–') : '–'}</td></tr>`).join('')}</tbody></table></div>
        <div><h3>measurements${ctl && ctl.metrics ? ' · difference from the control' : ''}</h3><table><thead><tr><th>measure</th><th class="num">value</th>${ctl && ctl.metrics ? '<th class="num">− control</th>' : ''}</tr></thead><tbody>${meas.map(q => `<tr><td>${e(TH_DATA.PLAIN[q] || q)}</td><td class="num">${show(q, m[q])}</td>${ctl && ctl.metrics ? `<td class="num">${s === ctl ? 'the control' : d(q)}</td>` : ''}</tr>`).join('') || `<tr><td colspan="3">${EV.nr}</td></tr>`}</tbody></table></div></div>
      <h3>over time <span class="sm" style="text-transform:none;letter-spacing:0">· point at a chart: the same moment is marked in all of them</span></h3>
      ${o.others && o.others.length ? `<p class="sm"><label>Compare with <select data-ch="cmp"><option value="">no second simulation</option>${o.others.map(q => `<option value="${e(q.id)}"${EV.s.cmp === q.id ? ' selected' : ''}>${e(`${q.id} · ${q.label || ''} · run ${q.run}`)}</option>`).join('')}</select></label> (drawn dashed) · UDP blue, TCP orange</p>` : '<p class="sm">UDP blue, TCP orange</p>'}${charts}`;
  },
  simPanel(id) {
    const M = EV.M, e = EV.e, s = M.simById[id]; if (!s) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const x = M.expById[s.exp], ctl = x && x.sims.find(q => q.label === x.control);
    return `<h2>${EV_ICON.simulation} ${EV.term('Simulation', 'Simulation')} ${e(s.id)}<small>label “${e(s.label || '')}” · run ${e(s.run || 'not recorded')} · finished ${EV.time(s.ts)}</small></h2>
      ${s.same_as ? `<p class="sm">○ The result of ${EV.link(s.same_as)} (same settings and seed), returned again: nothing was run, and it was not counted against the budget.</p>` : ''}${s.error ? `<p class="bad">No measurements: ${e(s.error)}</p>` : ''}
      ${EV.resultPanel(s, ctl, { ctlHead: ctl ? `the control ${EV.link(ctl.id)} “${e(ctl.label)}”` : '', others: M.sims.filter(q => q.id !== s.id && q.run && !q.error) })}`;
  },

  async loadSeries(sim) {
    const src = EV.srcOf(sim); if (!src || src in EV.series) return false;
    EV.series[src] = null; const t = await EV.get(src), c = t ? TH_DATA.csv(t) : null;
    EV.series[src] = c && c.t && c.t.length > 1 ? c : 'none'; return true;
  },
  // the charts over time of one simulation (and a second, dashed), once their samples are fetched; true: fetched just now, draw the page again
  async timeCharts(a, b) {
    const T = TASK_VIEW; if (!window.Chart || !a) return false; T._last = [document.getElementById('ev')]; T._P = { kind: 'evidence' };
    if ((await Promise.all([a, b].filter(Boolean).map(EV.loadSeries))).some(Boolean)) return true;
    const row = q => { const sr = q && EV.series[EV.srcOf(q)]; return sr && sr !== 'none' ? { id: q.run && q.run !== q.id ? `${q.id} (${q.run})` : q.id, series: sr } : null; };
    const A = row(a), B = row(b); if (!A || !document.getElementById('th-c-tput')) return false;
    T._time(EV.TIME.filter(q => !q.need || [A, B].some(r => r && q.need(r.series))), [A, B].filter(Boolean), B); return false;
  },
  // after the HTML is in place: the charts of what is open, and the series still to be fetched
  async afterDraw() {
    const S = EV.s, M = EV.M, T = TASK_VIEW; Object.values(T._charts).forEach(c => { try { c.destroy(); } catch (q) {} }); T._charts = {};
    if (!S.sel || !window.Chart) return; T._last = [document.getElementById('ev')]; T._P = { kind: 'evidence' };
    document.querySelectorAll('#ev canvas[data-chart]').forEach(c => { const T = c.dataset.chart === 'test' ? M.testById[c.dataset.id] : null, x = M.expById[T ? T.exp : c.dataset.id]; if (!x) return;
      if (T) EV.chart(c.id, { x, sims: c.dataset.wide ? x.sims : T.sims, rules: [{ rule: T.rule, for: T.hyp }], control: c.dataset.wide ? x.control : T.control, test: T.id });
      else EV.chart(c.id, { x, sims: x.sims, rules: x.rules, control: x.control }); });
    if (S.sel.t === 'sim' && M.simById[S.sel.id] && await EV.timeCharts(M.simById[S.sel.id], S.cmp && M.simById[S.cmp])) EV.draw();
  },
  exportChart(id, kind) { TASK_VIEW._export(id, kind); },
});
