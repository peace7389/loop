// Two-hosts adapter for the ADRS main viewer and the standalone page (viewer/index.html).
// TASK_VIEW.draw: one simulation run as small SVG charts (the main viewer's hover cards and gallery).
// TASK_VIEW.page: the whole page of this task (see the comment above it). TH_DATA: its content, from the raw files.
// UDP is always --series-1 and TCP always --series-2, in every chart; never two scales in one chart.
const TASK_VIEW = {
  _d: {},
  drawable: sol => !!(sol && sol.series && sol.series.t && sol.series.t.length > 1),

  _nice(max) {  // a round axis top and its step: 3 or 4 intervals
    if (!(max > 0)) return { top: 1, step: 1 };
    const raw = max / 3, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
    const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
    return { top: Math.ceil(max / step - 1e-9) * step, step };
  },
  _num(v) {
    const a = Math.abs(v);
    return a >= 1e6 ? (v / 1e6).toFixed(a >= 1e7 ? 0 : 1) + 'M' : a >= 1e4 ? (v / 1e3).toFixed(0) + 'k' : a >= 1e3 ? (v / 1e3).toFixed(1) + 'k'
      : Number.isInteger(v) ? String(v) : a >= 10 ? v.toFixed(0) : v.toFixed(1);
  },
  _tick(v) { return TASK_VIEW._num(v).replace(/\.0(?=[kM]?$)/, '');
  },

  draw(sol, { valid, size, labels, aria, simple }) {
    const S = sol.series, n = S.t.length, m = sol.metrics || {};
    const udpC = css('--series-1'), tcpC = css('--series-2'), ink = css('--text-primary'), sec = css('--text-secondary'),
      mut = css('--text-muted'), grid = css('--grid');
    const share = m.weight_udp != null && m.link_rate_bps ? m.weight_udp * m.link_rate_bps / 1e6 : null;
    const panels = [
      { title: 'Throughput per flow', unit: 'Mbps', h: simple ? 118 : 120,
        series: [{ name: 'UDP', c: udpC, v: S.udp.map(x => x / 1e6) }, { name: 'TCP', c: tcpC, v: S.tcp.map(x => x / 1e6) }],
        ref: share != null ? { v: share, name: 'UDP weight × link' } : null },
      { title: 'TCP congestion window', unit: 'kB', h: 64, series: [{ name: 'TCP window', c: tcpC, v: S.cwnd.map(x => x / 1e3) }] },
      { title: 'Drops from the UDP queue', unit: 'packets per sample', h: 64, series: [{ name: 'UDP queue drops', c: udpC, v: S.d0 }] },
      { title: 'Drops from the TCP queue', unit: 'packets per sample', h: 64, series: [{ name: 'TCP queue drops', c: tcpC, v: S.d1 }] },
    ].slice(0, simple ? 1 : 4);
    const W = simple ? 300 : 460, L = simple ? 30 : 44, R = simple ? 8 : 14, fs = simple ? 9 : 10.5;
    const head = simple ? 16 : 40, gap = simple ? 0 : 26, foot = simple ? 16 : 34;
    const t0 = S.t[0], t1 = S.t[n - 1], X = t => L + (W - L - R) * (t - t0) / (t1 - t0 || 1);
    let y = head;
    panels.forEach(p => { p.y0 = y; y += p.h + gap; });
    const H = y - gap + foot;
    const key = 'tv' + (++TASK_VIEW._seq);
    let s = `<svg viewBox="0 0 ${W} ${H}" width="${size}" style="display:block;max-width:100%;font-family:inherit" role="img" aria-label="${aria}"` +
      (simple ? '' : ` data-tv="${key}" onmousemove="TASK_VIEW.hover(event,this)" onmouseleave="TASK_VIEW.leave(this)"`) + '>';
    // legend: identity is never colour alone (name beside each swatch)
    const lg = [['UDP', udpC, ''], ['TCP', tcpC, '']].concat(share != null && !simple ? [['UDP weight × link', mut, '4 3']] : []);
    let lx = L;
    lg.forEach(([name, c, dash]) => {
      s += `<line x1="${lx}" y1="${simple ? 7 : 10}" x2="${lx + 14}" y2="${simple ? 7 : 10}" stroke="${c}" stroke-width="${dash ? 1.5 : 2.5}"${dash ? ` stroke-dasharray="${dash}"` : ''}/>` +
        `<text x="${lx + 18}" y="${simple ? 10 : 13.5}" font-size="${fs}" fill="${sec}">${name}</text>`;
      lx += 26 + name.length * fs * 0.56;
    });
    if (!simple) s += `<text class="tv-read" x="${W - R}" y="13.5" font-size="${fs}" text-anchor="end" fill="${sec}"></text>`;
    const geo = [];
    panels.forEach((p, k) => {
      const max = Math.max(...p.series.map(q => Math.max(...q.v)), p.ref ? p.ref.v : 0);
      const { top, step } = TASK_VIEW._nice(max), y0 = p.y0, yb = p.y0 + p.h;
      const Y = v => yb - p.h * v / top;
      if (!simple) s += `<text x="${L}" y="${y0 - 7}" font-size="${fs}" font-weight="600" fill="${ink}">${p.title}<tspan font-weight="400" fill="${mut}"> · ${p.unit}</tspan></text>`;
      for (let v = 0; v <= top + 1e-9; v += step) {
        s += `<line x1="${L}" y1="${Y(v).toFixed(1)}" x2="${W - R}" y2="${Y(v).toFixed(1)}" stroke="${grid}" stroke-width="1"/>` +
          `<text x="${L - 5}" y="${(Y(v) + 3.5).toFixed(1)}" font-size="${fs}" text-anchor="end" fill="${mut}">${TASK_VIEW._tick(v)}</text>`;
      }
      if (p.ref) s += `<line x1="${L}" y1="${Y(p.ref.v).toFixed(1)}" x2="${W - R}" y2="${Y(p.ref.v).toFixed(1)}" stroke="${mut}" stroke-width="1.5" stroke-dasharray="4 3"/>`;
      p.series.forEach(q => {
        s += `<polyline fill="none" stroke="${q.c}" stroke-width="${simple ? 1.5 : 2}" stroke-linejoin="round" stroke-linecap="round" points="${
          q.v.map((v, i) => X(S.t[i]).toFixed(1) + ',' + Y(v).toFixed(1)).join(' ')}"/>`;
      });
      if (!simple) {
        p.series.forEach((q, j) => { s += `<circle class="tv-dot" data-p="${k}" data-s="${j}" r="3.5" fill="${q.c}" stroke="${css('--surface-1')}" stroke-width="2" visibility="hidden"/>`; });
        s += `<text class="tv-val" data-p="${k}" x="${W - R}" y="${y0 - 7}" font-size="${fs}" text-anchor="end" fill="${sec}"></text>`;
      }
      geo.push({ y0, yb, top, h: p.h, unit: p.unit, series: p.series.map(q => ({ name: q.name, v: q.v })) });
    });
    // time axis under the last panel
    const yb = panels[panels.length - 1].y0 + panels[panels.length - 1].h, span = t1 - t0;
    const tstep = [1, 2, 5, 10].find(k => span / k <= (simple ? 4 : 8)) || 20;
    for (let t = Math.ceil(t0 / tstep) * tstep; t <= t1 + 1e-9; t += tstep)
      s += `<line x1="${X(t).toFixed(1)}" y1="${yb}" x2="${X(t).toFixed(1)}" y2="${yb + 4}" stroke="${mut}" stroke-width="1"/>` +
        `<text x="${X(t).toFixed(1)}" y="${yb + (simple ? 13 : 15)}" font-size="${fs}" text-anchor="middle" fill="${mut}">${t}${simple ? '' : ' s'}</text>`;
    if (!simple) {
      s += `<text x="${W - R}" y="${H - 3}" font-size="${fs}" text-anchor="end" fill="${mut}">run ${sol.run_id || ''} · simulated time · one sample per ${(span / (n - 1)).toFixed(1)} s · point at the chart for values</text>`;
      s += `<line class="tv-x" x1="0" x2="0" y1="${panels[0].y0}" y2="${yb}" stroke="${sec}" stroke-width="1" visibility="hidden"/>`;
      TASK_VIEW._d[key] = { W, L, R, t: S.t, geo };
      const keys = Object.keys(TASK_VIEW._d);
      if (keys.length > 80) keys.slice(0, 40).forEach(k => delete TASK_VIEW._d[k]);  // old drawings are gone from the page
    }
    return s + '</svg>';
  },
  _seq: 0,

  // Hover: one crosshair through every panel, a marker on each line, the values at that moment as text
  hover(ev, svg) {
    const d = TASK_VIEW._d[svg.dataset.tv]; if (!d) return;
    const box = svg.getBoundingClientRect(), x = (ev.clientX - box.left) * d.W / box.width;
    const n = d.t.length, f = Math.max(0, Math.min(1, (x - d.L) / (d.W - d.L - d.R)));
    const i = Math.round(f * (n - 1)), px = d.L + (d.W - d.L - d.R) * i / (n - 1);
    const line = svg.querySelector('.tv-x');
    line.setAttribute('x1', px); line.setAttribute('x2', px); line.setAttribute('visibility', 'visible');
    svg.querySelectorAll('.tv-dot').forEach(c => {
      const g = d.geo[+c.dataset.p], v = g.series[+c.dataset.s].v[i];
      c.setAttribute('cx', px); c.setAttribute('cy', g.yb - g.h * v / g.top); c.setAttribute('visibility', 'visible');
    });
    svg.querySelectorAll('.tv-val').forEach(tx => {
      const g = d.geo[+tx.dataset.p];
      tx.textContent = g.series.map(q => (g.series.length > 1 ? q.name + ' ' : '') + (q.v[i] >= 100 ? Math.round(q.v[i]).toLocaleString() : q.v[i].toFixed(1))).join(' · ');
    });
    const r = svg.querySelector('.tv-read'); if (r) r.textContent = `at ${d.t[i].toFixed(1)} s`;
  },
  leave(svg) {
    svg.querySelectorAll('.tv-x, .tv-dot').forEach(e => e.setAttribute('visibility', 'hidden'));
    svg.querySelectorAll('.tv-val').forEach(e => { e.textContent = ''; });
    const r = svg.querySelector('.tv-read'); if (r) r.textContent = '';
  },

  // ====================================================================================================
  // The page (task entry custom_page). One page for two questions: what did the numbers do over time, and
  // why did the AI choose this run?
  //   0 what this is  ->  1 every run: a table and a chart of any value against any other; a click on a row
  //   or a dot chooses a run  ->  2 the chosen run: why it was made -> its numbers over time -> what it showed.
  // A second run can be drawn on the same axes (dashed). Charts are Chart.js (from the CDN); each has PNG and
  // CSV export, and the time charts mark the same sample in all of them. Data: TH_DATA.build below.
  // The earlier six-page viewer (system objects, packet events, run control) is kept as index_full.html.
  // ====================================================================================================
  _ui: { run: null, a: null, b: '', x: 'm:weight_udp', y: 'g:goodput', only: null },
  _charts: {}, _cj: 'idle', _rows: [],
  CDN: 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
  FRACTION: ['udp_loss_frac', 'link_util'],   // measures recorded as a fraction, shown as a percentage
  _css: `
.th { max-width: 1280px; margin: 0 auto; font-size: 15px; line-height: 1.5; color: var(--text-primary); }
.th h1, .th h2, .th h3, .th p, .th figure { margin: 0; }
.th-top, .th-sec { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 20px 26px 22px; margin-bottom: 18px; }
.th-kicker { font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--text-muted); }
.th-titleline { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; justify-content: space-between; margin: 2px 0 10px; }
.th-top h1 { font-size: 24px; letter-spacing: -.02em; line-height: 1.25; } .th-top h1 small { font-size: 15px; font-weight: 500; color: var(--text-secondary); margin-left: 10px; letter-spacing: 0; }
.th-state { display: inline-flex; align-items: center; gap: 8px; font-size: 13.5px; font-weight: 600; border: 1px solid var(--border); border-radius: 999px; padding: 3px 12px; }
.th-state i { width: 9px; height: 9px; border-radius: 50%; background: var(--text-muted); } .th-state.live i { background: var(--good); }
.th-q { font-size: 16px; max-width: 940px; }
.th-facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0 18px; margin: 16px 0 0; border-top: 1px solid var(--border); }
.th-fact { padding: 12px 0 0; } .th-fact dt { font-size: 11.5px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); }
.th-fact dd { margin: 2px 0 0; font-size: 16px; font-weight: 700; overflow-wrap: anywhere; } .th-fact dd small { display: block; font-size: 12.5px; font-weight: 400; color: var(--text-secondary); }
.th-sh { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 16px; }
.th-sh > div { flex: 1; min-width: 0; }
.th-no { flex: none; width: 30px; height: 30px; border-radius: 50%; background: var(--text-primary); color: var(--surface-1); font-weight: 700; font-size: 15px; display: grid; place-items: center; margin-top: 1px; }
.th-sh h2 { font-size: 20px; letter-spacing: -.01em; line-height: 1.3; } .th-sh h2 small { font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-left: 8px; letter-spacing: 0; }
.th-sh p { font-size: 14px; color: var(--text-secondary); max-width: 860px; }
.th-ctl { flex: none; display: inline-flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; white-space: nowrap; }
.th select { font: inherit; font-size: 14px; font-weight: 400; padding: 5px 8px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-1); color: var(--text-primary); max-width: 300px; }
.th-bar select { max-width: 205px; } .th-nw { white-space: nowrap; }
.th-all { display: grid; grid-template-columns: minmax(0, 11fr) minmax(0, 9fr); gap: 28px; align-items: start; }
.th-two { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 28px; align-items: start; }
.th-wide { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 28px; align-items: start; }
@media (max-width: 900px) { .th-all, .th-two, .th-wide, .th-charts { grid-template-columns: 1fr !important; } }
.th h3 { font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); margin: 0 0 6px; }
.th h3 span { font-weight: 400; letter-spacing: 0; text-transform: none; margin-left: 6px; }
.th * + h3 { margin-top: 16px; }
.th table { border-collapse: collapse; width: 100%; font-size: 14px; font-variant-numeric: tabular-nums; }
.th th { text-align: left; font-size: 12px; font-weight: 600; color: var(--text-muted); padding: 6px 12px 6px 0; border-bottom: 1px solid var(--border); vertical-align: bottom; background: var(--surface-1); }
.th td { padding: 8px 12px 8px 0; border-bottom: 1px solid var(--grid); vertical-align: top; } .th td.num, .th th.num { text-align: right; }
.th td small { display: block; font-size: 12px; color: var(--text-muted); }
.th-list { max-height: 418px; overflow-y: auto; border: 1px solid var(--border); border-radius: 10px; }
.th-list table th { position: sticky; top: 0; z-index: 1; } .th-list tr:last-child td { border-bottom: 0; }
.th-list td:first-child, .th-list th:first-child { padding-left: 10px; width: 34px; }
.th tr.pick { cursor: pointer; } .th tr.pick:hover td { background: var(--surface-0); } .th tr.pick:focus-visible { outline: 2px solid var(--series-1); outline-offset: -2px; }
.th tr.on td { background: color-mix(in srgb, var(--series-1) 9%, transparent); } .th tr.on td:first-child { box-shadow: inset 3px 0 0 var(--series-1); }
.th tr.cmp td { background: color-mix(in srgb, var(--text-primary) 5%, transparent); }
.th-swl { vertical-align: middle; color: var(--text-primary); }
.th-muted { color: var(--text-muted); } .th-sm { font-size: 13px; color: var(--text-secondary); }
.th-ok { color: var(--good); font-weight: 700; } .th-bad { color: var(--critical); font-weight: 700; }
.th-vd { display: inline-flex; align-items: center; gap: 7px; font-size: 13.5px; font-weight: 600; border: 1px solid var(--border); border-radius: 999px; padding: 2px 11px; background: var(--surface-1); white-space: nowrap; }
.th-vd::before { content: ""; width: 9px; height: 9px; border-radius: 50%; background: var(--text-muted); box-sizing: border-box; }
.th-vd.supported::before { background: var(--good); } .th-vd.refuted::before { background: var(--critical); }
.th-vd.inconclusive::before, .th-vd.pending::before { background: none; border: 2px solid var(--text-muted); }
.th-bar { display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center; margin: 0 0 8px; font-size: 14px; }
.th-bar label { display: inline-flex; align-items: center; gap: 8px; font-weight: 600; }
.th-cv { position: relative; } .th-cv canvas { display: block; }
.th-exp { display: flex; gap: 6px; align-items: center; justify-content: flex-end; margin-top: 2px; font-size: 12px; color: var(--text-muted); }
.th-exp button { font: inherit; font-size: 12px; padding: 1px 9px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface-1); color: var(--text-secondary); cursor: pointer; }
.th-exp button:hover { border-color: var(--text-primary); color: var(--text-primary); }
.th-part { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; margin: 22px 0 14px; padding-top: 14px; border-top: 1px solid var(--border); }
.th-part:first-of-type { margin-top: 0; }
.th-part b { font-size: 16px; } .th-part b i { font-style: normal; display: inline-grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; border: 1.5px solid var(--text-primary); font-size: 12.5px; margin-right: 8px; vertical-align: 1px; }
.th-part span { font-size: 13px; color: var(--text-muted); }
.th-claim { font-size: 15.5px; } .th-claim b { font-weight: 700; }
.th-chip { display: inline-block; border: 1px solid var(--border); border-radius: 7px; padding: 2px 9px; margin: 0 6px 6px 0; font-size: 13.5px; background: var(--surface-1); }
.th-chip s { text-decoration: none; color: var(--text-muted); } .th-chip.kept { color: var(--text-secondary); background: none; }
.th details { margin-top: 10px; font-size: 14px; } .th summary { cursor: pointer; color: var(--text-secondary); }
.th details p { margin-top: 6px; color: var(--text-secondary); }
.th pre { white-space: pre-wrap; overflow-wrap: anywhere; font: 12.5px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; max-height: 320px; overflow: auto; margin: 8px 0 0; padding: 10px 12px; background: var(--surface-0); border-radius: 8px; }
.th-tag { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid var(--grid); color: var(--text-secondary); } .th-tag b { color: var(--text-primary); font-size: 15px; }
.th-diff { margin-top: 16px; padding: 9px 14px; border-left: 3px solid var(--text-primary); background: var(--surface-0); border-radius: 0 8px 8px 0; font-size: 14px; }
.th-charts { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px 28px; }
.th-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0 14px; margin-bottom: 4px; }
.th-stat span { display: block; font-size: 12.5px; color: var(--text-secondary); } .th-stat b { font-size: 22px; letter-spacing: -.01em; font-variant-numeric: tabular-nums; } .th-stat b small { font-size: 13px; font-weight: 500; color: var(--text-secondary); margin-left: 3px; }
.th-held { font-weight: 700; margin-bottom: 4px; }
.th-empty { padding: 18px 0; color: var(--text-secondary); }
.th { --by-model: #6250d6; --by-harness: #c2407a; --by-simulator: #1baf7a; --by-operator: #eda100; }
@media (prefers-color-scheme: dark) { .th { --by-model: #9085e9; --by-harness: #d55181; --by-simulator: #127a57; --by-operator: #c98500; } }
.th [data-by=model] { --c: var(--by-model); } .th [data-by=harness] { --c: var(--by-harness); } .th [data-by=simulator] { --c: var(--by-simulator); } .th [data-by=operator] { --c: var(--by-operator); }
.th-src { display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; margin: 14px 0 0; padding-top: 12px; border-top: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.th-src > b { font-size: 11.5px; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); margin-right: 4px; }
.th-src button { font: inherit; font-size: 13px; display: inline-flex; align-items: center; gap: 7px; padding: 3px 11px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface-1); color: var(--text-secondary); cursor: pointer; }
.th-src button i { width: 10px; height: 10px; border-radius: 3px; background: var(--c); } .th-src button b { color: var(--text-primary); }
.th-src button.on { border-color: var(--text-primary); box-shadow: inset 0 0 0 1px var(--text-primary); }
.th-by { border-left: 4px solid var(--c); padding-left: 12px; } .th-by + .th-by, .th * + .th-by { margin-top: 16px; } .th-by > h3:first-child { margin-top: 0; }
.th-who { font-style: normal; display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--text-secondary); margin-right: 8px; }
.th-who::before { content: ""; width: 9px; height: 9px; border-radius: 3px; background: var(--c); }
.th th[data-by] { box-shadow: inset 0 -3px 0 var(--c); }
.th[data-only] [data-by]:not(button) { transition: opacity .12s; }
.th[data-only=model] [data-by]:not([data-by=model]):not(button), .th[data-only=harness] [data-by]:not([data-by=harness]):not(button),
.th[data-only=simulator] [data-by]:not([data-by=simulator]):not(button), .th[data-only=operator] [data-by]:not([data-by=operator]):not(button) { opacity: .2; }
`,
  _e: s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])),
  _first(t) {  // the first sentence of a hypothesis, without its own "H1:" prefix
    t = String(t || '').replace(/^\s*H\d+\s*:\s*/, '');
    const i = t.search(/[.!?](\s|$)/);
    return i > 30 ? t.slice(0, i + 1) : t;
  },
  _rate(sv) { return String(sv).replace(/([0-9.]+)\s*([kMG]?)bps/g, '$1 $2bps').replace(/([0-9.]+)us\b/g, '$1 µs').replace(/([0-9.]+)ms\b/g, '$1 ms'); },
  _mb: v => (typeof v === 'number' ? (v / 1e6).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : '–'),
  _pc: v => (typeof v === 'number' ? (100 * v).toFixed(1) + '%' : '–'),
  _show(k, v) {  // a setting or a measured value as the tables show it
    const T = TASK_VIEW;
    if (v == null) return '–';
    if (typeof v !== 'number') return T._rate(String(v));
    if (/_bps$/.test(k)) return T._mb(v) + ' Mbps';
    if (T.FRACTION.includes(k)) return T._pc(v);
    return Number.isInteger(v) ? v.toLocaleString('en-US') : String(v);
  },
  _sw: dashed => `<svg class="th-swl" width="22" height="8" aria-hidden="true"><line x1="1" y1="4" x2="21" y2="4" stroke="currentColor" stroke-width="2.5"${dashed ? ' stroke-dasharray="5 3"' : ''}/></svg>`,
  _q: s => (TASK_VIEW._last ? TASK_VIEW._last[0].querySelector(s) : null),
  _name(r, cap) { const loop = TASK_VIEW._P.kind === 'loop'; return !loop ? 'run ' + r.id : r.h && r.h.baseline ? (cap ? 'Baseline' : 'the baseline') : (cap ? 'Experiment ' : 'experiment ') + r.n; },
  _Name: r => { const s = TASK_VIEW._name(r, true); return s[0].toUpperCase() + s.slice(1); },

  _loadChart() {  // Chart.js from the CDN, after the page itself: a slow or missing CDN never holds the text back
    const T = TASK_VIEW; if (T._cj !== 'idle') return;
    if (window.Chart) { T._cj = 'ready'; return; }
    T._cj = 'loading';
    const s = document.createElement('script'), done = ok => { T._cj = ok && window.Chart ? 'ready' : 'failed'; if (T._last && T._last[0].isConnected && T._q('#th-run')) { T._study(); T._run(); } };
    s.src = T.CDN; s.onload = () => done(true); s.onerror = () => done(false); document.head.appendChild(s);
  },

  page(root, data) {
    const T = TASK_VIEW, ui = T._ui, e = T._e;
    if (!document.getElementById('th-css')) { const st = document.createElement('style'); st.id = 'th-css'; st.textContent = T._css; document.head.appendChild(st); }
    const raw = data.raw || (data.page && data.page.raw);
    if (!raw) { T._last = [root, data]; T._shown = null; root.innerHTML = '<div class="th"><section class="th-sec">Loading…</section></div>'; return; }
    // content is built here from the harness's raw files (TH_DATA), the same for the standalone page and the ADRS viewer
    const key = data.run + '|' + (raw.ledger || []).length + '|' + (raw.index || []).length + '|' + Object.keys(raw.series || {}).length + '|' + !!raw.running;
    if (T._shown === key && T._last && T._last[0] === root && root.querySelector('#th-run')) return;  // nothing new: what is on the screen is not touched
    T._last = [root, data]; T._shown = key;
    if (T._built !== key) { T._built = key; T._content = TH_DATA.build(raw, data.run); }
    const P = T._P = T._content.page, loop = P.kind === 'loop', O = P.outcome; T._raw = raw;
    const hyp = Object.fromEntries((P.hyps || []).map(h => [h.n, h]));
    const index = Object.fromEntries((raw.index || []).map(r => [r.id, r])), oper = Object.fromEntries((raw.oper || []).map(r => [r.id, r]));
    T._rows = T._content.programs.map(p => { const id = p.row.Run;
      return { n: p.iteration, id, h: hyp[p.iteration] || null, params: (index[id] || {}).params || {}, metrics: p.metrics || {}, failed: !p.solution,
               series: (raw.series || {})[id] || null, policy: TH_DATA.policy(oper[id]), reasoning: p.reasoning, facts: p.facts || [] }; });
    const rows = T._rows;
    if (ui.run !== data.run) { ui.run = data.run; ui.a = null; ui.b = ''; }
    if (!rows.some(r => r.id === ui.a)) ui.a = rows.length ? rows[rows.length - 1].id : null;
    if (!rows.some(r => r.id === ui.b) || ui.b === ui.a) ui.b = '';
    T._loadChart();

    // ---- 0. what this is: the question, then the session in a few facts
    const facts = !loop ? P.facts : [P.facts[0], P.facts[2],
      ['Experiments', String(O.experiments), `in ${O.turns} turns` + (O.wasted ? `, ${O.wasted} without a usable answer` : '')],
      ['Hypotheses, by the AI’s verdict', `${O.supported} supported`, `${O.refuted} refuted · ${O.inconclusive} inconclusive · ${O.unjudged} not judged`],
      ['Decision rules, checked from the numbers', O.rules_total ? `${O.rules_met} of ${O.rules_total} held` : '–', 'each decision rule was stated by the AI before its simulations'],
      P.facts[5]];
    const SRC = { model: 'written by the AI', harness: 'found or decided by the harness', simulator: 'measured by the simulation', operator: 'set by the person: the brief, the scheduling policy' };
    const who = b => `<em class="th-who" data-by="${b}">${b}</em>`;
    T._by = (b, html) => (html ? `<div class="th-by" data-by="${b}">${html.replace('<h3>', '<h3>' + who(b))}</div>` : '');  // one block of one source: its colour on the left edge, its name before the title
    const legend = `<div class="th-src" id="th-src"><b>Who produced it</b>${TH_DATA.SOURCES.map(b => `<button data-by="${b}" class="${ui.only === b ? 'on' : ''}" aria-pressed="${ui.only === b}" title="${e(SRC[b])}. Click to dim everything else; click again to show all."><i></i><b>${b}</b>${P.by ? ` ${P.by[b]} record${P.by[b] === 1 ? '' : 's'}` : ''}</button>`).join('')}
      <span>${P.by ? 'ledger records by source' + (P.by_derived ? ' (this session was recorded before the harness wrote the source into each record: it is taken from the record’s type)' : '') + ' · ' : ''}the same colour marks every block and table column · click one to dim the rest</span></div>`;
    let h = `<div class="th"${ui.only ? ` data-only="${ui.only}"` : ''}><header class="th-top"><div class="th-kicker">${e(P.kicker)}</div>
      <div class="th-titleline"><h1>${e(P.title)}<small>${loop ? 'session' : 'run'} “${e(data.run)}”${P.brief ? ' · brief ' + e(P.brief) : ''}</small></h1>
        ${O ? `<span class="th-state${O.running ? ' live' : ''}"><i></i>${O.running ? 'Running now' : O.done ? 'Finished: the AI gave its answer' : 'Stopped before the AI gave an answer'}</span>` : ''}</div>
      <div class="th-by" data-by="operator"><p class="th-q">${loop ? who('operator') : ''}${e(P.question)}</p></div>
      ${P.many ? '<p class="th-sm" style="margin-top:10px">This session is in the multi-simulation format: an experiment can hold several simulations, and the harness checks the AI’s decision rules itself. Until this page is restructured for it, each simulation is shown as one row, with the first hypothesis its experiment tested; dropped hypotheses and the experiment designs are in the ledger but not on this page.</p>' : ''}
      <dl class="th-facts">${facts.map(([k, v, s]) => `<div class="th-fact"${k === 'Scheduling policy' ? ' data-by="operator"' : ''}><dt>${k === 'Scheduling policy' ? who('operator') : ''}${e(k)}</dt><dd>${e(v)}${s ? `<small>${e(s)}</small>` : ''}</dd></div>`).join('')}</dl>${legend}</header>`;
    if (!rows.length) { root.innerHTML = h + '<section class="th-sec"><p class="th-empty">No simulation has been run yet. This page fills in as runs finish.</p></section></div>'; return; }

    // ---- 1. every run: the table and the chart are two views of the same runs, and both choose the run shown in section 2
    // [title, class, source]: the decision-rule column is the check of the AI's decision rule against the measurement, so it has no single source
    const head = loop ? [['', ''], ['#', ''], ['What the AI changed', '', 'model'], ['UDP share', 'num', 'model'], ['UDP, Mbps', 'num', 'simulator'], ['TCP, Mbps', 'num', 'simulator'], ['Decision rule', ''], ['AI’s verdict', '', 'model']]
      : [['', ''], ['#', ''], ['Run', '', 'operator'], ['Scheduling policy', '', 'operator'], ['UDP share', 'num', 'operator'], ['UDP offered', 'num', 'operator'], ['UDP, Mbps', 'num', 'simulator'], ['TCP, Mbps', 'num', 'simulator']];
    const pill = (res, text) => `<span class="th-vd ${e(res || 'pending')}">${e(text || res || 'not judged')}</span>`;
    T._pill = pill;
    const held = x => !x || !x.total ? '<span class="th-muted">–</span>' : `<span class="th-nw"><span class="${x.met === x.total ? 'th-ok' : 'th-bad'}">${x.met === x.total ? '✓' : '✕'}</span> ${x.met} of ${x.total} held</span>`;
    const changed = r => { const x = r.h; if (!x) return ''; if (x.baseline) return 'baseline: all defaults';
      return x.changed.length ? x.changed.map(([k, a, b]) => `${e(k.replace(' of the link', ''))} <span class="th-nw">${e(T._rate(a))} → <b>${e(T._rate(b))}</b></span>`).join('<br>') : `<span class="th-muted">${r.n > 1 ? 'same settings as before' : 'all defaults'}</span>`; };
    const tr = r => { const m = r.metrics, x = r.h;
      const cells = loop ? [`<b>${r.n}</b><small>${e(r.id)}</small>`, changed(r), [e(m.weight_udp ?? '–')], [T._mb(m.udp_goodput_bps)], [T._mb(m.tcp_goodput_bps)], held(x),
                            !x ? '' : x.baseline ? pill('pending', 'baseline') : x.verdict ? pill(x.verdict.result) : pill('pending', 'not judged')]
        : [`<b>${r.n}</b>`, e(r.id), e(r.policy || '–'), [e(m.weight_udp ?? '–')], [e(T._rate(r.params.udpRate ?? '–'))], [T._mb(m.udp_goodput_bps)], [T._mb(m.tcp_goodput_bps)]];
      const src = i => (head[i + 1][2] ? ` data-by="${x && x.baseline && head[i + 1][2] === 'model' ? 'harness' : head[i + 1][2]}"` : '');  // the baseline's settings were the harness's choice
      return `<tr class="pick" data-id="${e(r.id)}" tabindex="0"><td class="th-mark"></td>${cells.map((c, i) => (Array.isArray(c) ? `<td class="num"${src(i)}>${c[0]}</td>` : `<td${src(i)}>${c}</td>`)).join('')}</tr>`; };
    h += `<section class="th-sec"><div class="th-sh"><span class="th-no">1</span><div><h2>${loop ? 'Every experiment' : 'Every run'}</h2>
        <p>One row and one dot for each simulation${loop ? ' the AI asked for' : ''}. Click a row or a dot to open that run in section 2.</p></div></div>
      <div class="th-all"><div class="th-list" id="th-list"><table><thead><tr>${head.map(([t, c, b]) => `<th${c ? ` class="${c}"` : ''}${b ? ` data-by="${b}" title="${b}: ${e(SRC[b])}"` : t === 'Decision rule' ? ' title="the AI’s decision rule (stated before the simulations), checked against the measurement"' : ''}>${t}</th>`).join('')}</tr></thead>
        <tbody>${rows.map(tr).join('')}</tbody></table></div>
      <div><div class="th-bar"><label>Across <select id="th-x" aria-label="Horizontal axis"></select></label><label>Up <select id="th-y" aria-label="Vertical axis"></select></label></div>
        <div id="th-study"></div></div></div></section>
      <section class="th-sec" id="th-run"></section></div>`;
    const y0 = window.scrollY;
    Object.values(T._charts).forEach(c => c.destroy()); T._charts = {};
    root.innerHTML = h;
    const pick = row => () => T._choose(row.dataset.id);
    root.querySelectorAll('#th-list tr.pick').forEach(row => { row.onclick = pick(row); row.onkeydown = ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); pick(row)(); } }; });
    root.querySelectorAll('#th-src button').forEach(b => { b.onclick = () => { ui.only = ui.only === b.dataset.by ? null : b.dataset.by;  // the filter: dims, removes nothing, moves nothing
      const th = root.querySelector('.th'); if (ui.only) th.dataset.only = ui.only; else delete th.dataset.only;
      root.querySelectorAll('#th-src button').forEach(o => { const on = o.dataset.by === ui.only; o.classList.toggle('on', on); o.setAttribute('aria-pressed', on); }); }; });
    root.querySelector('#th-x').onchange = ev => { ui.x = ev.target.value; T._study(); };
    root.querySelector('#th-y').onchange = ev => { ui.y = ev.target.value; T._study(); };
    T._mark(); T._study(); T._run();
    const on = root.querySelector('#th-list tr.on'), list = root.querySelector('#th-list');
    if (on && on.offsetTop + on.offsetHeight > list.clientHeight) list.scrollTop = on.offsetTop - 40;  // the chosen row is in view inside the list; the page itself does not move
    if (window.scrollY !== y0) window.scrollTo(0, y0);
  },

  // A run was chosen (a row or a dot): the mark in the table, the ring in the chart and section 2 follow. The page does not scroll.
  _choose(id) {
    const T = TASK_VIEW, ui = T._ui; if (id === ui.a || !T._rows.some(r => r.id === id)) return;
    if (id === ui.b) ui.b = '';
    ui.a = id; T._mark(); if (T._charts.study) T._charts.study.draw(); T._run();
  },
  _mark() {
    const T = TASK_VIEW, ui = T._ui;
    T._last[0].querySelectorAll('#th-list tr.pick').forEach(row => { const a = row.dataset.id === ui.a, b = row.dataset.id === ui.b;
      row.classList.toggle('on', a); row.classList.toggle('cmp', b); row.setAttribute('aria-selected', a ? 'true' : 'false');
      row.querySelector('.th-mark').innerHTML = a ? T._sw(false) : b ? T._sw(true) : ''; });
  },

  // ---- Chart.js pieces shared by all charts
  _bg: { id: 'thBg', beforeDraw(c) { const g = c.ctx; g.save(); g.fillStyle = css('--surface-1'); g.fillRect(0, 0, c.width, c.height); g.restore(); } },  // so an exported PNG is not transparent
  _options(title, xTitle, yTitle, more) {
    const ink = css('--text-primary'), sec = css('--text-secondary'), mut = css('--text-muted'), grid = css('--grid');
    const font = { family: getComputedStyle(TASK_VIEW._last[0]).fontFamily, size: 12 };
    const axis = t => ({ title: { display: !!t, text: t, color: sec, font }, ticks: { color: mut, font, maxTicksLimit: 8 }, grid: { color: grid }, border: { color: grid } });
    const o = { animation: false, responsive: true, maintainAspectRatio: false,
      plugins: { title: { display: true, text: title, align: 'start', color: ink, font: { ...font, size: 14, weight: '600' }, padding: { bottom: 4 } },
                 legend: { position: 'top', align: 'start', labels: { color: sec, font, usePointStyle: true, boxHeight: 7, padding: 12,
                           generateLabels: c => Chart.defaults.plugins.legend.labels.generateLabels(c).map(l => ({ ...l, lineDash: c.data.datasets[l.datasetIndex].borderDash || [] })) } },
                 tooltip: { backgroundColor: css('--surface-1'), titleColor: ink, bodyColor: ink, footerColor: sec, borderColor: css('--border'), borderWidth: 1,
                            titleFont: { ...font, size: 13, weight: '700' }, bodyFont: { ...font, size: 12.5 }, footerFont: { ...font, weight: '400' }, padding: 10, boxPadding: 5, usePointStyle: true } },
      scales: { x: axis(xTitle), y: axis(yTitle) } };
    more(o); return o;
  },
  _expBar: c => `<div class="th-exp" data-chart="${c}"><span>save</span><button data-x="png" title="This chart as a picture">PNG</button><button data-x="csv" title="The data drawn in this chart">CSV</button></div>`,
  _wireExp(el) { el.querySelectorAll('.th-exp button').forEach(b => { b.onclick = () => TASK_VIEW._export(b.parentNode.dataset.chart, b.dataset.x); }); },

  // ---- 1b. any setting or measure against any other, one dot per run
  _axes() {  // what an axis can show
    const T = TASK_VIEW, D = TH_DATA, rows = T._rows, out = [];
    const mk = [...new Set(rows.flatMap(r => Object.keys(r.metrics)))].filter(k => k !== 'link_rate_bps');
    const pk = [...new Set(rows.flatMap(r => Object.keys(r.params)))].filter(k => D.KNOB[k] && k !== 'weightUdp');
    const S = 'Settings', M = 'Measured';
    if (mk.includes('weight_udp')) out.push({ key: 'm:weight_udp', label: 'UDP share of the link', unit: '', group: S });
    pk.forEach(k => out.push({ key: 'p:' + k, label: D.KNOB[k], unit: { udpRate: 'Mbps', duration: 's', queuePkts: 'packets' }[k] || '', group: S }));
    if (T._P.kind !== 'loop' && rows.some(r => r.policy)) out.push({ key: 'o:policy', label: 'Scheduling policy', unit: '', group: S });
    if (mk.includes('udp_goodput_bps') && mk.includes('tcp_goodput_bps')) out.push({ key: 'g:goodput', label: 'UDP and TCP goodput', unit: 'Mbps', group: M, yOnly: true });
    mk.filter(k => k !== 'weight_udp').forEach(k => out.push({ key: 'm:' + k, label: D.PLAIN[k] || k, unit: /_bps$/.test(k) ? 'Mbps' : T.FRACTION.includes(k) ? '%' : /^drops_|retrans/.test(k) ? 'packets' : '', group: M }));
    ['udp_goodput_bps', 'tcp_goodput_bps'].filter(k => mk.includes(k)).forEach(k => out.push({ key: 'r:' + k, label: D.PLAIN[k] + ' ÷ link rate', unit: '', group: M }));
    return out;
  },
  _val(r, key) {  // a run's value on an axis: a number in the axis's unit, a name (a category), or null
    const T = TASK_VIEW, k = key.slice(2), m = r.metrics, t = key[0];
    if (t === 'o') return r.policy || null;
    if (t === 'r') return typeof m[k] === 'number' && m.link_rate_bps ? m[k] / m.link_rate_bps : null;
    if (t === 'm') { const v = m[k]; return typeof v !== 'number' ? null : /_bps$/.test(k) ? v / 1e6 : T.FRACTION.includes(k) ? 100 * v : v; }
    const v = r.params[k]; if (v == null) return null; if (typeof v === 'number') return v;
    const b = /^\s*([0-9.]+)\s*([kMG]?)bps\s*$/.exec(v); if (b) return parseFloat(b[1]) * { '': 1e-6, k: 1e-3, M: 1, G: 1e3 }[b[2]];
    return v !== '' && isFinite(v) ? Number(v) : String(v);
  },
  _fmt(v, ax) { return typeof v !== 'number' ? String(v) : (ax.unit === 'Mbps' || ax.unit === '%' ? v.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : v.toLocaleString('en-US', { maximumFractionDigits: 4 })) + (ax.unit === '%' ? '%' : ax.unit ? ' ' + ax.unit : ''); },
  _study() {
    const T = TASK_VIEW, ui = T._ui, e = T._e, rows = T._rows, box = T._q('#th-study'); if (!box) return;
    const axes = T._axes(), find = (key, y) => axes.find(a => a.key === key && (y || !a.yOnly));
    const X = find(ui.x) || find('m:weight_udp') || axes.find(a => !a.yOnly), Y = find(ui.y, true) || find('g:goodput', true) || axes[axes.length - 1];
    if (T._charts.study) { T._charts.study.destroy(); delete T._charts.study; }
    if (!X || !Y) { box.innerHTML = '<p class="th-empty">These runs have no recorded values to plot.</p>'; return; }
    ui.x = X.key; ui.y = Y.key;
    const opts = (sel, y) => ['Settings', 'Measured'].map(g => { const ks = axes.filter(a => a.group === g && (y || !a.yOnly));
      return ks.length ? `<optgroup label="${g}">${ks.map(a => `<option value="${e(a.key)}"${a.key === sel ? ' selected' : ''}>${e(a.label + (a.unit && a.unit !== '%' ? ', ' + a.unit : a.unit ? ', %' : ''))}</option>`).join('')}</optgroup>` : ''; }).join('');
    T._q('#th-x').innerHTML = opts(X.key, false); T._q('#th-y').innerHTML = opts(Y.key, true);
    if (T._cj !== 'ready') { box.innerHTML = `<p class="th-empty">${T._cj === 'failed' ? 'The chart library (Chart.js, from cdn.jsdelivr.net) could not be loaded, so this chart is missing. The table has the same runs.' : 'Loading the chart…'}</p>`; return; }
    const udp = css('--series-1'), tcp = css('--series-2'), sec = css('--text-secondary'), mut = css('--text-muted'), s1 = css('--surface-1');
    const colour = k => (/udp|band0/.test(k) ? udp : /tcp|band1|retrans/.test(k) ? tcp : sec);
    const series = Y.key === 'g:goodput' ? [['UDP goodput', 'm:udp_goodput_bps', udp], ['TCP goodput', 'm:tcp_goodput_bps', tcp]] : [[Y.label, Y.key, colour(Y.key)]];
    const sets = series.map(([label, key, c]) => ({ label, unit: Y.unit, data: rows.map(r => ({ x: T._val(r, X.key), y: T._val(r, key), id: r.id, n: r.n })).filter(p => p.x != null && p.y != null),
      backgroundColor: c, borderColor: s1, borderWidth: 2, pointRadius: 6, pointHoverRadius: 8, pointHitRadius: 12, pointStyle: 'circle' }));
    const drawn = new Set(sets.flatMap(d => d.data.map(p => p.id))).size;
    const cats = (ax, vals) => (vals.some(v => typeof v === 'string') ? [...new Set(vals.map(String))] : null);
    const xc = cats(X, sets.flatMap(d => d.data.map(p => p.x))), yc = cats(Y, sets.flatMap(d => d.data.map(p => p.y)));
    if (xc || yc) sets.forEach(d => d.data.forEach(p => { if (xc) p.x = String(p.x); if (yc) p.y = String(p.y); }));
    const diagonal = X.key === 'm:weight_udp' && Y.key[0] === 'r';
    if (diagonal) sets.push({ label: Y.key === 'r:udp_goodput_bps' ? 'UDP gets exactly its share' : 'TCP gets exactly the rest', type: 'line', guide: true,
      data: Y.key === 'r:udp_goodput_bps' ? [{ x: 0, y: 0 }, { x: 1, y: 1 }] : [{ x: 0, y: 1 }, { x: 1, y: 0 }], borderColor: mut, borderWidth: 1.5, borderDash: [6, 4], pointRadius: 0, pointHitRadius: 0, pointStyle: 'line' });
    box.innerHTML = `<div class="th-cv" style="height:340px"><canvas id="th-c-study" role="img" aria-label="${e(Y.label)} against ${e(X.label)}, one dot per run"></canvas></div>${T._expBar('study')}
      <p class="th-sm">${T._sw(false)} ring: the run open in section 2 &nbsp;·&nbsp; ${T._sw(true)} ring: the run compared with it${drawn < rows.length ? ` &nbsp;·&nbsp; ${drawn} of ${rows.length} runs drawn (the others have no value for one of the two axes)` : ''}</p>`;
    T._wireExp(box);
    // the chosen run (solid ring) and the compared run (dashed ring), with their numbers: drawn at every repaint from the current choice
    const rings = { id: 'thRings', afterDatasetsDraw(c) {
      const g = c.ctx, ink = css('--text-primary'); g.save(); g.strokeStyle = ink; g.fillStyle = ink; g.lineWidth = 2; g.font = `700 12px ${getComputedStyle(T._last[0]).fontFamily}`; g.textAlign = 'center';
      [[ui.a, []], [ui.b, [4, 3]]].forEach(([id, dash]) => { if (!id) return; let top = null, low = null;
        c.data.datasets.forEach((d, i) => { if (d.guide || !c.isDatasetVisible(i)) return; c.getDatasetMeta(i).data.forEach((pt, j) => { if (d.data[j].id !== id) return;
          g.setLineDash(dash); g.beginPath(); g.arc(pt.x, pt.y, 10.5, 0, 2 * Math.PI); g.stroke(); if (!top || pt.y < top.y) top = { x: pt.x, y: pt.y, n: d.data[j].n }; if (!low || pt.y > low.y) low = { x: pt.x, y: pt.y, n: d.data[j].n }; }); });
        // the chosen run's number above its ring, the compared run's under its ring; beside the ring where the chart's edge leaves no room
        const side = q => g.fillText('#' + q.n, q.x + (q.x - 34 > c.chartArea.left ? -24 : 24), q.y + 4);
        if (top && !dash.length) { if (top.y - 26 > c.chartArea.top) g.fillText('#' + top.n, top.x, top.y - 15); else side(top); }
        if (low && dash.length) { if (low.y + 28 < c.chartArea.bottom) g.fillText('#' + low.n, low.x, low.y + 24); else side(low); } });
      g.restore(); } };
    const title = (a) => a.label + (a.unit && a.unit !== '%' ? ', ' + a.unit : a.unit ? ', %' : '');
    T._charts.study = new Chart(T._q('#th-c-study'), { type: 'scatter', data: { datasets: sets }, plugins: [T._bg, rings],
      options: T._options(`${Y.label} against ${X.key === 'm:weight_udp' ? 'the UDP share' : /^(UDP|TCP)/.test(X.label) ? X.label : 'the ' + X.label[0].toLowerCase() + X.label.slice(1)}`, title(X), title(Y), o => {
        o.interaction = { mode: 'nearest', intersect: false }; o.layout = { padding: { top: 2, right: 12 } };
        o.plugins.legend.display = sets.length > 1;
        [['x', xc, X], ['y', yc, Y]].forEach(([a, cs, ax]) => { if (cs) { o.scales[a].type = 'category'; o.scales[a].labels = cs; o.scales[a].offset = true; }
          else { if (ax.key === 'm:weight_udp' || ax.key[0] === 'r') { o.scales[a].min = 0; o.scales[a].max = 1; } else if (a === 'y') o.scales[a].beginAtZero = true; o.scales[a].grace = '6%'; } });
        o.plugins.tooltip.filter = it => !it.dataset.guide;
        o.plugins.tooltip.callbacks = { title: items => [...new Set(items.map(it => { const r = rows.find(q => q.id === it.raw.id); return `${T._Name(r)} · ${r.id}`.replace(/^Run (\S+) · \1$/, 'Run $1'); }))].join(', '),
          label: c => ` ${c.dataset.label}: ${T._fmt(c.raw.y, Y)}`, footer: items => `${X.label}: ${T._fmt(items[0].raw.x, X)}` };
        o.onClick = (ev, els, chart) => { const hit = chart.getElementsAtEventForMode(ev.native, 'nearest', { intersect: false }, false).find(q => !chart.data.datasets[q.datasetIndex].guide);
          if (hit) T._choose(chart.data.datasets[hit.datasetIndex].data[hit.index].id); };
        o.onHover = (ev, els) => { ev.native.target.style.cursor = els.length ? 'pointer' : 'default'; };
      }) });
    T._charts.study.thFile = `${Y.label}-against-${X.label}`.replace(/[^A-Za-z0-9]+/g, '_'); T._charts.study.thX = null;
  },

  // ---- 2. the chosen run, read top to bottom: why it was made -> its numbers over time -> what it showed
  _run() {
    const T = TASK_VIEW, ui = T._ui, e = T._e, rows = T._rows, box = T._q('#th-run'); if (!box) return;
    const P = T._P, loop = P.kind === 'loop', D = TH_DATA;
    const A = rows.find(r => r.id === ui.a), B = rows.find(r => r.id === ui.b) || null; if (!A) return;
    Object.keys(T._charts).filter(k => k !== 'study').forEach(k => { T._charts[k].destroy(); delete T._charts[k]; });
    if (box.offsetHeight) box.style.minHeight = box.offsetHeight + 'px';  // the page never gets shorter under the reader
    const tag = (r, dashed) => (B ? `<div class="th-tag">${T._sw(dashed)}<b>${e(T._Name(r))}</b> run ${e(r.id)} · the ${dashed ? 'dashed' : 'solid'} line</div>` : '');
    const more = (title, body) => `<details><summary>${title}</summary>${body}</details>`;
    const by = T._by;

    // a. why: the AI's claim, and the settings it chose to test it
    const why = r => { const x = r.h;
      if (!x) return by('operator', r.facts.filter(([k]) => k !== 'Settings').map(([k, v]) => `<h3>${e(k)}</h3><p>${e(v)}</p>`).join('')) || '<p class="th-muted">Nothing was recorded about why this run was made.</p>';
      const full = String(x.text || '').replace(/^\s*H\d+\s*:\s*/, ''), first = T._first(x.text);
      return by(x.baseline ? 'harness' : x.by || 'model', `<h3>${x.baseline ? 'Baseline' : 'Hypothesis ' + e(x.id)}<span>${x.baseline ? 'run by the harness before the AI’s first turn' : 'the AI’s claim, written in turn ' + e(x.turn)}</span></h3>
        <p class="th-claim"><b>${e(first)}</b>${e(full.slice(first.length))}</p>
        ${x.observations ? more('What the AI had seen before it made this claim', `<p>${e(x.observations)}</p>`) : ''}
        ${r.reasoning ? more(`The AI’s own reasoning before this run (${r.reasoning.length.toLocaleString('en-US')} characters)`, `<pre>${e(r.reasoning)}</pre>`) : ''}`); };
    const chip = (k, v, old) => `<span class="th-chip${old === false ? ' kept' : ''}">${e(k)} ${old ? `<s>${e(T._rate(old))} →</s> ` : ''}<b>${e(T._rate(v))}</b></span>`;
    const settings = r => { const x = r.h;
      if (!x) { const ks = Object.keys(r.params).filter(k => D.KNOB[k]);
        return by('operator', `<h3>Settings<span>chosen by the operator</span></h3><p>${ks.length ? ks.map(k => chip(D.KNOB[k], D.knob(k, r.params[k]))).join('') : '<span class="th-muted">The settings of this run were not recorded.</span>'}</p>`); }
      const was = new Set(x.changed.map(c => c[0])), kept = x.settings.filter(([k]) => !was.has(k)), prev = r.n > 1 ? T._name(rows.find(q => q.n === r.n - 1) || { n: r.n - 1 }) : 'the defaults';
      return by(x.baseline ? 'harness' : 'model', `<h3>What it changed<span>from ${e(prev)}</span></h3><p>${x.changed.length ? x.changed.map(([k, a, b]) => chip(k, b, a)).join('') : `<span class="th-muted">Nothing: the same settings as ${e(prev)}.</span>`}</p>
        ${kept.length ? `<h3>Kept as before</h3><p>${kept.map(([k, v]) => chip(k, v, false)).join('')}</p>` : ''}`); };
    const pv = (r, k) => (k === 'policy' ? r.policy : r.params[k]), keys = B ? [...new Set([...Object.keys(A.params), ...Object.keys(B.params)])].filter(k => D.KNOB[k]).concat(A.policy || B.policy ? ['policy'] : []) : [];
    const diff = keys.filter(k => String(pv(A, k)) !== String(pv(B, k)));
    const differ = !B ? '' : `<p class="th-diff">${diff.length ? '<b>The two runs differ in:</b> ' + diff.map(k => `${e(D.KNOB[k] || 'Scheduling policy')} <b>${e(T._rate(D.knob(k, pv(A, k))))}</b> against <b>${e(T._rate(D.knob(k, pv(B, k))))}</b>`).join(' &nbsp;·&nbsp; ')
      : keys.length ? 'The two runs were made with the same settings.' : 'The settings of these runs were not recorded.'}</p>`;

    // c. what it showed: the averages, the AI's decision rule against them, the AI's verdict and plan
    const stats = r => { const m = r.metrics;
      if (r.failed) return by('simulator', `<p>The simulation did not return measurements.${r.h && r.h.error ? ' ' + e(r.h.error) : ''}</p>`);
      const rest = Object.keys(m).filter(k => !['udp_goodput_bps', 'tcp_goodput_bps', 'udp_loss_frac', 'link_util'].includes(k));
      return by('simulator', `<h3>Measured<span>averages over the measured time, by the simulation</span></h3>
        <div class="th-stats">${[['UDP goodput', T._mb(m.udp_goodput_bps), 'Mbps'], ['TCP goodput', T._mb(m.tcp_goodput_bps), 'Mbps'], ['UDP loss', T._pc(m.udp_loss_frac).replace('%', ''), '%'], ['Link use', T._pc(m.link_util).replace('%', ''), '%']]
          .map(([k, v, u]) => `<div class="th-stat"><span>${k}</span><b>${v}<small>${v === '–' ? '' : u}</small></b></div>`).join('')}</div>
        ${rest.length ? more('Every other value it recorded', `<table><tbody>${rest.map(k => `<tr><td>${e(D.PLAIN[k] || k)}</td><td class="num">${e(T._show(k, m[k]))}</td></tr>`).join('')}</tbody></table>`) : ''}`); };
    const check = r => { const x = r.h; if (!x || !x.criteria.length) return '';
      const all = x.total && x.met === x.total;
      // rows: in the multi-simulation format one row per decision rule (checked by the harness); before it, one row per comparison of the one decision rule
      const unit = P.many ? ['decision rule', 'decision rules'] : ['comparison of the decision rule', 'comparisons of the decision rule'];
      const mark = c => (c.ok == null ? '<span class="th-muted">not checked</span>' : c.ok ? '<span class="th-ok">✓</span> held' : '<span class="th-bad">✕</span> failed');
      const table = P.many
        ? `<table><thead><tr><th data-by="model">Decision rule (stated before the simulations)</th><th data-by="simulator">With the measured numbers</th><th title="checked by the harness">Held?</th></tr></thead><tbody>${x.criteria.map(c => `<tr>
            <td data-by="model">${e(c.what)}${c.rival ? `<small>rival explanation: ${e(c.rival)}${c.rival_predicts ? ` · under the rival this decision rule would have ${e(c.rival_predicts)}` : ''}</small>` : ''}</td>
            <td data-by="simulator">${e(c.measured)}</td><td class="th-nw">${mark(c)}</td></tr>`).join('')}</tbody></table>`
        : `<table><thead><tr><th data-by="model">Measure</th><th data-by="model">Decision rule</th><th class="num" data-by="simulator">Measured</th><th title="checked by this page">Held?</th></tr></thead><tbody>${x.criteria.map(c => `<tr><td data-by="model">${e(c.what)}</td><td data-by="model">${e(c.need)}</td><td class="num" data-by="simulator"><b>${e(c.measured)}</b></td>
          <td>${mark(c)}</td></tr>`).join('')}</tbody></table>`;
      return `<h3>Decision rule (stated before the simulations)<span>against the measurement; ${P.many ? 'checked by the harness' : 'checked here from the recorded numbers'}</span></h3>
        ${x.total ? `<p class="th-held"><span class="${all ? 'th-ok' : 'th-bad'}">${all ? '✓' : '✕'}</span> ${all ? (x.total === 1 ? `The ${unit[0]} held` : `All ${x.total} ${unit[1]} held`) : `${x.met} of ${x.total} ${unit[1]} held`}</p>` : ''}
        ${table}`; };
    const verdict = r => { const x = r.h; if (!x || x.baseline) return ''; const v = x.verdict;
      // every number in the AI's verdict that names, or equals, a value measured in this run: shown beside the measurement
      const N = (v && v.numbers) || [], off = N.filter(q => q.status === 'differs').length, word = { agrees: '<span class="th-ok">✓</span> agrees', differs: '<span class="th-bad">✕</span> differs' };
      const nums = !N.length ? '' : `<h3>The AI’s numbers against the measurement<span>each number in its verdict that names, or equals, a value measured in run ${e(r.id)}</span></h3>
        <p class="th-held"><span class="${off ? 'th-bad' : 'th-ok'}">${off ? '✕' : '✓'}</span> ${off ? `${off} of ${N.length} number${N.length === 1 ? '' : 's'} differ${off === 1 ? 's' : ''} from the measurement` : N.length === 1 ? 'The one number agrees with the measurement' : `All ${N.length} numbers agree with the measurement`}</p>
        <details${off ? ' open' : ''}><summary>The ${N.length === 1 ? 'number' : N.length + ' numbers'}, side by side</summary><table><thead><tr><th data-by="model">The AI wrote</th><th>Measure</th><th class="num" data-by="simulator">Measured</th><th title="compared by this page, to the precision the AI wrote">Same?</th></tr></thead>
          <tbody>${N.map(q => `<tr><td data-by="model">${e(q.written)}</td><td>${e(q.what)}${q.named ? '' : '<small>not named in the text; found by its value</small>'}</td><td class="num th-nw" data-by="simulator"><b>${e(q.measured)}</b></td>
            <td class="th-nw">${word[q.status] || `<span class="th-muted">= ${e(q.other)}, another experiment</span>`}</td></tr>`).join('')}</tbody></table>
          <p class="th-sm">“Agrees” means equal to the measurement when it is rounded the way the AI wrote the number (within 2% after “about”).</p></details>`;
      return by((v && v.by) || 'model', `<h3>Verdict<span>${v ? 'the AI’s own judgement, turn ' + e(v.turn) : 'the AI’s own judgement'}</span></h3>
        ${v ? `<p>${T._pill(v.result)}</p>${v.because ? `<p class="th-sm" style="margin-top:6px">${e(v.because)}</p>` : ''}` : `<p>${T._pill('pending', 'not judged')}</p><p class="th-sm" style="margin-top:6px">${P.outcome && P.outcome.running ? 'The AI has not judged this hypothesis yet.' : 'The session ended before the AI judged this hypothesis.'}</p>`}
        ${v && v.next ? `<h3>Next step<span>the AI’s plan</span></h3><p class="th-sm">${e(v.next)}</p>` : ''}`) + nums; };

    // b. over time: one chart per recorded column, all on the same time axis
    const shown = [A, B].filter(r => r && r.series && r.series.t && r.series.t.length > 1), lost = [A, B].filter(r => r && !shown.includes(r));
    const dt = shown.length ? (shown[0].series.t[shown[0].series.t.length - 1] - shown[0].series.t[0]) / (shown[0].series.t.length - 1) : null;
    const defs = !shown.length ? [] : [
      { id: 'tput', title: 'Throughput per flow', unit: 'Mbps', lines: S => [['UDP', 1, S.udp.map(v => v / 1e6)], ['TCP', 2, S.tcp.map(v => v / 1e6)]] },
      { id: 'cwnd', title: 'TCP congestion window', unit: 'kB', lines: S => [['TCP window', 2, S.cwnd.map(v => v / 1e3)]] },
      { id: 'd0', title: 'Packets dropped from the UDP queue', unit: 'packets per sample', lines: S => [['UDP queue drops', 1, S.d0]] },
      { id: 'd1', title: 'Packets dropped from the TCP queue', unit: 'packets per sample', lines: S => [['TCP queue drops', 2, S.d1]] },
      { id: 'q', title: 'Packets waiting in each queue', unit: 'packets', need: S => S.q0 && S.q1, lines: S => [['UDP queue', 1, S.q0], ['TCP queue', 2, S.q1]] },
    ].filter(d => !d.need || shown.some(r => d.need(r.series)));
    const charts = T._cj === 'ready' ? `<div class="th-charts" data-by="simulator">${defs.map(d => `<figure><div class="th-cv" style="height:${B ? 250 : 230}px"><canvas id="th-c-${d.id}" role="img" aria-label="${e(d.title)} over time"></canvas></div>${T._expBar(d.id)}</figure>`).join('')}</div>`
      : T._cj === 'failed' && shown.length ? `<p class="th-sm" style="margin-bottom:8px">The chart library (Chart.js) could not be loaded; this is the page’s built-in drawing of ${e(T._name(shown[0]))}, without comparison or export.</p>
          <div style="max-width:720px">${T.draw({ series: shown[0].series, metrics: shown[0].metrics, run_id: shown[0].id }, { valid: true, size: '100%', labels: true, aria: 'The run over time', simple: false })}</div>`
      : shown.length ? '<p class="th-empty">Loading the charts…</p>' : '';

    const part = (i, t, note, src) => `<div class="th-part"><b><i>${i}</i>${t}</b><span${src ? ` data-by="${src}"` : ''}>${src ? `<em class="th-who">${src}</em>` : ''}${note}</span></div>`;
    const opt = r => `<option value="${e(r.id)}"${r.id === ui.b ? ' selected' : ''}>${e(`${T._Name(r)} · ${r.id} · UDP share ${r.metrics.weight_udp ?? '–'}`.replace(/^Run (\S+) · \1/, 'Run $1'))}</option>`;
    box.innerHTML = `<div class="th-sh"><span class="th-no">2</span><div>
        <h2>${e(T._Name(A))}${B ? ' compared with ' + e(T._name(B)) : ''}<small>${B ? '' : loop ? `run ${e(A.id)}` + (A.h && !A.h.baseline ? ` · hypothesis ${e(A.h.id)}` : '') : 'an operator check'}</small></h2>
        <p>${loop ? 'Why the AI asked for it, what its numbers did over time, and what it showed.' : 'What it was for, what its numbers did over time, and what it showed.'}</p></div>
        <label class="th-ctl">Compare with <select id="th-b"><option value="">no second run</option>${rows.filter(r => r.id !== A.id).slice().reverse().map(opt).join('')}</select></label></div>
      ${part('a', loop ? 'Why the AI chose this run' : 'Why this run was made', loop ? 'written by the AI before the run' : 'an operator check, not an AI experiment')}
      ${B ? `<div class="th-two"><div>${tag(A, false)}${why(A)}${settings(A)}</div><div>${tag(B, true)}${why(B)}${settings(B)}</div></div>${differ}`
          : `<div class="th-wide"><div>${why(A)}</div><div>${settings(A)}</div></div>`}
      ${part('b', 'What the numbers did over time', shown.length ? `recorded by the simulation every ${dt.toFixed(1)} s of simulated time · point at any chart: the same moment is marked in all of them` : 'recorded by the simulation', 'simulator')}
      ${lost.length ? `<p class="th-sm" style="margin-bottom:10px">No samples over time were recorded for ${lost.map(r => e(T._name(r))).join(' and ')}.</p>` : ''}
      ${B && shown.length ? `<p class="th-sm" style="margin-bottom:10px">${T._sw(false)} ${e(T._name(A))} (${e(A.id)}) &nbsp;·&nbsp; ${T._sw(true)} ${e(T._name(B))} (${e(B.id)}) &nbsp;·&nbsp; the colour is the flow: UDP blue, TCP orange</p>` : ''}
      ${charts}
      ${part('c', 'What it showed', loop ? 'measured by the simulation, checked by this page, judged by the AI' : 'measured by the simulation')}
      ${B ? `<div class="th-two"><div>${tag(A, false)}${stats(A)}${check(A)}${verdict(A)}</div><div>${tag(B, true)}${stats(B)}${check(B)}${verdict(B)}</div></div>`
          : (check(A) || verdict(A) ? `<div class="th-wide"><div>${stats(A)}${check(A)}</div><div>${verdict(A)}</div></div>` : `<div class="th-wide"><div>${stats(A)}</div><div></div></div>`)}`;
    T._q('#th-b').onchange = ev => { ui.b = ev.target.value; T._mark(); if (T._charts.study) T._charts.study.draw(); T._run(); const s = T._q('#th-b'); if (s) s.focus({ preventScroll: true }); };
    T._wireExp(box);
    if (T._cj === 'ready' && defs.length) T._time(defs, shown, B);
  },

  // The time charts: run A solid, run B dashed; colour is the flow. Pointing at one chart marks the same sample in all of them.
  _time(defs, shown, B) {
    const T = TASK_VIEW, col = { 1: css('--series-1'), 2: css('--series-2') }, s1 = css('--surface-1'), mut = css('--text-muted'), two = shown.length > 1;
    const short = r => (T._P.kind === 'loop' ? '#' + r.n : r.id), ids = shown.map(r => r.id).join('-vs-');
    const near = (data, t) => { let lo = 0, hi = data.length - 1; while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (data[mid].x < t) lo = mid; else hi = mid; }
      return !data.length ? null : Math.abs(data[lo].x - t) <= Math.abs(data[hi].x - t) ? data[lo] : data[hi]; };
    const mark = { id: 'thMark', afterDatasetsDraw(c) {  // the sample under the pointer: a vertical line, and a dot on every line that has a sample there
      if (T._t == null) return; const g = c.ctx, a = c.chartArea, x = c.scales.x.getPixelForValue(T._t); if (x < a.left - 1 || x > a.right + 1) return;
      g.save(); g.strokeStyle = mut; g.lineWidth = 1; g.beginPath(); g.moveTo(x, a.top); g.lineTo(x, a.bottom); g.stroke();
      c.data.datasets.forEach((d, i) => { if (!c.isDatasetVisible(i)) return; const p = near(d.data, T._t); if (!p || Math.abs(p.x - T._t) > 0.06) return;
        g.beginPath(); g.arc(c.scales.x.getPixelForValue(p.x), c.scales.y.getPixelForValue(p.y), 4.5, 0, 2 * Math.PI); g.fillStyle = d.borderColor; g.fill(); g.lineWidth = 2; g.strokeStyle = s1; g.stroke(); });
      g.restore(); } };
    const tmax = Math.max(...shown.map(r => r.series.t[r.series.t.length - 1]));
    const made = [];
    defs.forEach(d => {
      const sets = shown.flatMap(r => (d.need && !d.need(r.series) ? [] : d.lines(r.series).map(([name, c, vals]) => ({ label: two ? `${short(r)} · ${name}` : name, name, run: r.id, unit: d.unit,
        data: r.series.t.map((t, i) => ({ x: t, y: vals[i] })), borderColor: col[c], backgroundColor: col[c], borderWidth: 2, borderDash: r === B ? [6, 4] : [], pointRadius: 0, pointHoverRadius: 0, pointStyle: 'line' }))));
      const ch = new Chart(T._q('#th-c-' + d.id), { type: 'line', data: { datasets: sets }, plugins: [T._bg, mark],
        options: T._options(`${d.title}, ${d.unit}`, 'Time since the traffic began, s', '', o => {
          o.interaction = { mode: 'index', intersect: false }; o.layout = { padding: { right: 12 } };
          o.scales.x.type = 'linear'; o.scales.x.min = 0; o.scales.x.max = Math.ceil(tmax); o.scales.y.beginAtZero = true; o.scales.y.ticks.maxTicksLimit = 6;
          o.plugins.legend.display = sets.length > 1; o.plugins.legend.labels.pointStyleWidth = 30; if (sets.length < 2) o.plugins.title.padding = { bottom: 37 };
          o.scales.x.ticks.includeBounds = false;
          o.plugins.tooltip.callbacks = {
            title: items => { const ts = [...new Set(items.map(it => it.parsed.x))]; return ts.length === 1 ? `t = ${ts[0].toFixed(1)} s` : items.map(it => `t = ${it.parsed.x.toFixed(1)} s (${it.dataset.run})`).filter((v, i, a) => a.indexOf(v) === i).join(' · '); },
            label: c => ` ${c.dataset.label}: ${c.parsed.y.toLocaleString('en-US', { minimumFractionDigits: d.unit.startsWith('packets') ? 0 : 1, maximumFractionDigits: d.unit.startsWith('packets') ? 0 : 1 })} ${c.dataset.unit.replace(' per sample', '')}` };
        }) });
      ch.thFile = `${d.id === 'tput' ? 'throughput' : d.id === 'cwnd' ? 'tcp-window' : d.id === 'd0' ? 'udp-queue-drops' : d.id === 'd1' ? 'tcp-queue-drops' : 'queue-occupancy'}-${ids}`; ch.thX = 't_s';
      T._charts[d.id] = ch; made.push(ch);
      const cv = ch.canvas, all = () => made.forEach(c => { if (c.canvas && c.canvas.isConnected) c.draw(); });
      cv.addEventListener('mousemove', ev => { const a = ch.chartArea, x = ev.offsetX; if (x < a.left || x > a.right) { if (T._t != null) { T._t = null; all(); } return; }
        const p = near(sets[0] ? sets[0].data : [], ch.scales.x.getValueForPixel(x)), t = p ? p.x : null; if (t !== T._t) { T._t = t; all(); } });
      cv.addEventListener('mouseleave', () => { if (T._t != null) { T._t = null; all(); } });
    });
    T._t = null;
  },

  // ---- export: the picture as drawn, or the data now on the chart (one column per line; hidden ones left out)
  _export(name, kind) {
    const T = TASK_VIEW, ch = T._charts[name]; if (!ch) return;
    const save = (href, file) => { const a = document.createElement('a'); a.href = href; a.download = file; document.body.appendChild(a); a.click(); a.remove(); };
    if (kind === 'png') { const t = T._t; T._t = null; ch.draw(); save(ch.toBase64Image('image/png', 1), `twohosts-${ch.thFile}.png`); T._t = t; return; }
    const q = v => (v == null ? '' : /[",\n]/.test(String(v)) ? '"' + String(v).replace(/"/g, '""') + '"' : String(v));
    const sets = ch.data.datasets.filter((d, i) => ch.isDatasetVisible(i) && !d.guide);
    let rows;
    if (ch.thX) {  // a time chart: one row per sample time, one column per line
      const xs = [...new Set(sets.flatMap(d => d.data.map(p => p.x)))].sort((a, b) => a - b), at = sets.map(d => new Map(d.data.map(p => [p.x, p.y])));
      rows = [[ch.thX, ...sets.map(d => `${d.run} ${d.name} (${d.unit})`)], ...xs.map(x => [x, ...at.map(m => m.get(x))])];
    } else {       // the chart of all runs: one row per run
      const ids = [...new Set(sets.flatMap(d => d.data.map(p => p.id)))], at = sets.map(d => new Map(d.data.map(p => [p.id, p])));
      rows = [['run', ch.options.scales.x.title.text, ...sets.map(d => d.label + (d.unit ? ` (${d.unit})` : ''))], ...ids.map(id => [id, (at.map(m => m.get(id)).find(Boolean) || {}).x, ...at.map(m => (m.get(id) || {}).y)])];
    }
    const url = URL.createObjectURL(new Blob([rows.map(r => r.map(q).join(',')).join('\n') + '\n'], { type: 'text/csv' }));
    save(url, `twohosts-${ch.thFile}.csv`); setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};

// ======================================================================================================
// TH_DATA: the page's content, built in the browser from the harness's own files, so the same code serves
// the standalone page (viewer/index.html, plain files on port 8600) and the ADRS main viewer.
// raw = { ledger: [records], index: [runs], oper: [operator rows], manifest: {...},
//         series: { run_id: {t, udp, tcp, cwnd, d0, d1} }, running: bool }
// build(raw, run) -> { page, programs } for run "loop" (the ledger) or "operator_checks" (runs no evidence points to).
// ======================================================================================================
const TH_DATA = {
  PLAIN: { udp_goodput_bps: 'UDP goodput', tcp_goodput_bps: 'TCP goodput', udp_loss_frac: 'UDP loss', drops_band0: 'Drops from the UDP queue',
           drops_band1: 'Drops from the TCP queue', tcp_retrans: 'TCP retransmissions', link_util: 'Link use', link_rate_bps: 'Link rate', weight_udp: 'UDP share' },
  KNOB: { weightUdp: 'UDP share of the link', udpRate: 'UDP offered rate', queuePkts: 'Queue length', tcpVariant: 'TCP congestion control', duration: 'Measured time', seed: 'Random seed' },
  UNIT: { queuePkts: ' packets', duration: ' s' },
  knob(k, v) { return v == null ? '–' : String(v) + (TH_DATA.UNIT[k] || ''); },
  // the scheduling policy of a run (how the scheduler divides the link), from the operator's line of it; lines written before 2026-11-11 call it "mode"
  policy(o) { return (o && (o.policy || o.mode)) || null; },

  // ---- A ledger in the multi-simulation format (hypotheses, experiments of several simulations, checks by the harness)
  // as this page reads a ledger: one experiment and one evidence record per simulation. The experiment's first tested
  // hypothesis is the simulation's hypothesis, and the harness's checks of its decision rules become the rows of its decision-rule table. Dropped
  // hypotheses and the experiment designs themselves are not shown until the page is restructured for this format.
  flat(led) {
    if (!led.some(r => r.type === 'simulation')) return led;
    const byId = Object.fromEntries(led.map(r => [r.id, r])), out = [];
    led.forEach(r => {
      if (['experiment', 'evidence', 'check', 'drop'].includes(r.type)) return;
      if (r.type !== 'simulation') { out.push(r); return; }
      if ((r.body || {}).same_as) return;  // the result of an earlier simulation, returned again: that simulation already has its row
      const x = byId[r.parent] || { id: '?', body: {} }, b = r.body || {}, run = (x.body.runs || []).find(q => q.label === b.label) || {}, hyp = (x.body.tests || [])[0] || null, xid = x.id + ':' + b.label;
      const checks = led.filter(c => c.type === 'check' && c.parent === x.id && (c.body || {}).for === hyp).map(c => ({ what: c.body.decision_rule || c.body.rule, rival: c.body.rival || null, rival_predicts: c.body.rival_predicts || null, need: 'as the AI stated it', measured: c.body.with_numbers, ok: c.body.result === 'held' ? true : c.body.result === 'failed' ? false : null }));
      out.push({ id: xid, turn: r.turn, type: 'experiment', by: x.by, parent: hyp, ts: x.ts, body: { params: run.params || {}, clamped: run.clamped || {}, pass_if: null } });
      out.push({ id: r.id, turn: r.turn, type: 'evidence', by: r.by, parent: xid, ts: r.ts,
                 body: { run_id: b.run_id, pass_if: null, ...(b.metrics || {}), ...(b.error ? { error: b.error } : {}), ...(x.id === 'X0' ? { note: x.body.question } : {}), ...(hyp ? { checks } : {}) } });
    });
    return out;
  },

  // ---- who produced a ledger record: its own "by" (the harness writes it since 2026-11-11), else what its type implies
  SOURCES: ['model', 'harness', 'simulator', 'operator'],
  by(r) { const b = r.body || {};
    return r.by || { evidence: 'simulator', malformed: 'harness', note: b.requests || b.text === 'model declared done' ? 'model' : 'harness' }[r.type] || 'model'; },

  // ---- numbers in a text the model wrote, against what was measured in the same experiment.
  // A number counts when the text names a measure just before it ("tcp_goodput=475.87 Mbps"), or, unnamed, when it has
  // three or more digits and equals a measured value. "Equal" = the measurement rounded the way the number is written
  // (within 2% after "about"). A named number that differs is looked up in the other experiments before it is marked.
  NAMES: [['udp_goodput_bps', 'udp[_ ]goodput(?:_bps)?'], ['tcp_goodput_bps', 'tcp[_ ]goodput(?:_bps)?'], ['total', 'total[_ ]goodput(?:_bps)?'], ['udp_loss_frac', 'udp[_ ]loss(?:_frac)?'],
          ['link_util', 'link[_ ]util(?:i[sz]ation)?'], ['drops_band0', 'drops_band0'], ['drops_band1', 'drops_band1'], ['tcp_retrans', 'tcp_retrans']],
  numbers(text, m, others) {
    const D = TH_DATA, out = [], used = [], seen = new Set(), T = String(text || '');
    const NUM = '(~|≈|about\\s+|around\\s+|roughly\\s+|approximately\\s+)?(-?\\d(?:[\\d,]*\\d)?(?:\\.\\d+)?(?:[eE][+-]?\\d+)?)\\s*(%|[kMG]?bps\\b)?';
    const val = (mm, k) => (k === 'total' ? (typeof mm.udp_goodput_bps === 'number' && typeof mm.tcp_goodput_bps === 'number' ? mm.udp_goodput_bps + mm.tcp_goodput_bps : null) : typeof mm[k] === 'number' ? mm[k] : null);
    const rate = k => k === 'total' || /_bps$/.test(k), frac = k => k === 'udp_loss_frac' || k === 'link_util';
    // the written number in the measure's own unit, and half a unit of its last written digit
    const read = (approx, raw, unit, k, measured) => { const t = raw.replace(/,/g, ''), n = parseFloat(t), mant = t.split(/[eE]/)[0], ex = /[eE]/.test(t) ? parseInt(t.split(/[eE]/)[1], 10) : 0;
      if (!isFinite(n) || (unit && unit !== '%' && !rate(k)) || (unit === '%' && !frac(k))) return null;
      let mult = unit ? { '%': 0.01, bps: 1, kbps: 1e3, Mbps: 1e6, Gbps: 1e9 }[unit] : 1;
      if (!unit && rate(k) && Math.abs(n) < 1e5 && measured) mult = [1e6, 1e9].sort((a, b) => Math.abs(Math.log(Math.abs(n * a / measured))) - Math.abs(Math.log(Math.abs(n * b / measured))))[0];  // "489.3" for a rate: Mbps or Gbps, whichever is nearer
      const tol = 0.5 * Math.pow(10, ex - (mant.split('.')[1] || '').length) * mult;
      return { v: n * mult, tol: approx ? Math.max(tol, 0.02 * Math.abs(measured)) : tol, digits: mant.replace(/[-.]/g, '').replace(/^0+/, '').length }; };
    const same = (w, measured) => Math.abs(w.v - measured) <= w.tol * (1 + 1e-9) + 1e-12 * Math.abs(measured);
    const exact = (k, v) => (rate(k) ? (v / 1e6).toLocaleString('en-US', { minimumFractionDigits: 3, maximumFractionDigits: 3 }) + ' Mbps' : frac(k) ? String(v) : v.toLocaleString('en-US'));
    const what = k => (k === 'total' ? 'UDP + TCP goodput' : D.PLAIN[k] || k);
    const add = (k, written, w, status, named, other) => { const id = k + '|' + w.v + '|' + status; if (seen.has(id)) return; seen.add(id);
      out.push({ key: k, what: what(k), written: written.replace(/\s+/g, ' ').trim(), measured: exact(k, val(m, k)), status, named, other: other || null }); };
    D.NAMES.forEach(([k, name]) => { const measured = val(m, k); if (measured == null) return;
      for (const x of T.matchAll(new RegExp('(?<![A-Za-z_])' + name + '\\s*(?:=|:|≈|~|\\bis\\b|\\bof\\b|\\bwas\\b)?\\s*' + NUM, 'gi'))) {
        const w = read(x[1], x[2], x[3], k, measured); if (!w) continue; used.push([x.index, x.index + x[0].length]);
        if (same(w, measured)) { add(k, x[0], w, 'agrees', true); continue; }
        const o = Object.entries(others || {}).find(([, mm]) => { const ov = val(mm, k); return ov != null && same(read(x[1], x[2], x[3], k, ov), ov); });
        add(k, x[0], w, o ? 'other' : 'differs', true, o && o[0]); } });
    for (const x of T.matchAll(new RegExp('(?<![A-Za-z_0-9.,])' + NUM + '(?![0-9])', 'g'))) {
      if (used.some(([a, b]) => x.index < b && x.index + x[0].length > a)) continue;
      for (const [k] of D.NAMES) { const measured = val(m, k); if (measured == null) continue; const w = read('', x[2], x[3], k, measured);  // unnamed: exactly as written, no allowance for "about"
        if (w && w.digits >= 3 && same(w, measured)) { add(k, x[0], w, 'agrees', false); break; } } }
    return out;
  },

  // series.csv text -> columns; drops become per-sample counts
  csv(text) {
    const lines = String(text || '').trim().split('\n'); if (lines.length < 3) return null;
    const head = lines[0].split(','), col = n => head.indexOf(n), rows = lines.slice(1).map(l => l.split(',').map(Number));
    const get = n => (col(n) < 0 ? null : rows.map(r => r[col(n)]));
    const diff = a => a.map((v, i) => (i ? v - a[i - 1] : v));
    return { t: get('t'), udp: get('udp_bps'), tcp: get('tcp_bps'), cwnd: get('cwnd'), d0: diff(get('drops_band0')), d1: diff(get('drops_band1')),
             q0: get('q_band0'), q1: get('q_band1') };  // packets waiting in each queue; null for runs made before they were recorded
  },

  // ---- the arithmetic of a decision rule of the first session (its pass_if) and nothing else: numbers, metric names, + - * /, parentheses, abs/min/max
  calc(text, m) {
    const tok = String(text).match(/\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+|[A-Za-z_][A-Za-z0-9_]*|[-+*/(),]/g) || [];
    if (tok.join('') !== String(text).replace(/\s+/g, '')) throw new Error('unknown symbol');
    let i = 0; const names = [];
    const expr = () => { let v = term(); while (tok[i] === '+' || tok[i] === '-') { const op = tok[i++], r = term(); v = op === '+' ? v + r : v - r; } return v; };
    const term = () => { let v = fac(); while (tok[i] === '*' || tok[i] === '/') { const op = tok[i++], r = fac(); v = op === '*' ? v * r : v / r; } return v; };
    const fac = () => { const t = tok[i++];
      if (t === '-') return -fac();
      if (t === '(') { const v = expr(); if (tok[i++] !== ')') throw new Error('bracket'); return v; }
      if (/^[\d.]/.test(t || '')) return parseFloat(t);
      if (/^[A-Za-z_]/.test(t || '')) {
        if (tok[i] === '(') { if (!['abs', 'min', 'max'].includes(t)) throw new Error('function'); i++; const a = [expr()]; while (tok[i] === ',') { i++; a.push(expr()); }
          if (tok[i++] !== ')') throw new Error('bracket'); return Math[t](...a); }
        if (typeof m[t] !== 'number') throw new Error('not a measured value'); names.push(t); return m[t]; }
      throw new Error('syntax'); };
    const v = expr(); if (i !== tok.length || !isFinite(v)) throw new Error('syntax');
    return { v, names };
  },
  // That decision rule as rows a person can read: what, the allowed range, the measured value, met or not.
  // Checked here from the recorded numbers (not by the model). A clause that is not plain arithmetic stays as written.
  criteria(passIf, m) {
    const rows = [], by = {};
    String(passIf || '').trim().split(/\s+AND\s+|\s*&&\s*/i).filter(Boolean).forEach(clause => {
      try {
        const parts = clause.split(/(>=|<=|==|>|<)/); if (parts.length !== 3) throw new Error('not one comparison');
        const L = TH_DATA.calc(parts[1 - 1], m), R = TH_DATA.calc(parts[2], m), op = parts[1];
        const fmt = L.names.some(n => n.endsWith('_bps')) ? v => (v / 1e6).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' Mbps'
          : L.names.length && L.names.every(n => ['udp_loss_frac', 'link_util', 'weight_udp'].includes(n)) ? v => (100 * v).toFixed(1) + '%'
          : v => (Math.abs(v) >= 100 || Number.isInteger(v) ? Math.round(v).toLocaleString('en-US') : String(+v.toPrecision(3)));
        const what = parts[0].trim().replace(/^\((.*)\)$/, '$1').replace(/\s+/g, ' ').replace(/[A-Za-z_][A-Za-z0-9_]*/g, n => TH_DATA.PLAIN[n] || n);
        let row = by[what]; if (!row) { row = by[what] = { what, measured: fmt(L.v), ok: true, v: L.v }; rows.push(row); }
        row[op[0] === '>' ? 'lo' : op[0] === '<' ? 'hi' : 'eq'] = fmt(R.v);
        row[op[0] === '>' ? 'lov' : op[0] === '<' ? 'hiv' : 'eqv'] = R.v;
        row.ok = row.ok && (op === '>=' ? L.v >= R.v : op === '>' ? L.v > R.v : op === '<=' ? L.v <= R.v : op === '<' ? L.v < R.v : L.v === R.v);
      } catch (err) { rows.push({ what: clause.trim(), need: 'as written', measured: 'not checked', ok: null }); }
    });
    rows.forEach(r => { if (!r.need) r.need = r.eq != null ? 'exactly ' + r.eq : r.lo != null && r.hi != null ? `${r.lo} to ${r.hi}` : r.lo != null ? 'at least ' + r.lo : 'at most ' + r.hi; });
    return rows;
  },

  build(raw, run) {
    const D = TH_DATA, written = raw.ledger || [], led = D.flat(written), man = raw.manifest || {}, fixed = man.fixed || {};
    const index = Object.fromEntries((raw.index || []).map(r => [r.id, r])), oper = Object.fromEntries((raw.oper || []).map(r => [r.id, r]));
    const defaults = Object.fromEntries(Object.entries(man.params || {}).map(([k, v]) => [k, v.default]));
    const used = new Set(led.filter(r => r.type === 'evidence').map(r => (r.body || {}).run_id));
    const lastRun = [...led].reverse().find(r => r.type === 'evidence');
    const system = { link_rate: fixed.linkRate || '1Gbps', link_delay: fixed.linkDelay || '50us', mtu: fixed.mtu || 1500, defaults, objects: raw.objects || null,
      policy: run === 'operator_checks' ? 'share or cap, per run' : (lastRun && D.policy(oper[(lastRun.body || {}).run_id])) || 'share' };
    const measured = Object.entries(man.outputs || {}).filter(([k]) => !['link_rate_bps', 'weight_udp'].includes(k)).map(([k, v]) => [D.PLAIN[k] || k, v]);
    const num = o => Object.fromEntries(Object.entries(o || {}).filter(([, v]) => typeof v === 'number'));
    const program = (n, rid, metrics, extra) => ({ iteration: n, metrics: metrics || {}, reasoning: null, facts: [],
      solution: metrics && metrics.udp_goodput_bps != null ? { run_id: rid, params: (index[rid] || {}).params || {}, metrics, series: (raw.series || {})[rid] || null } : null,
      row: { Run: rid, Policy: D.policy(oper[rid]) || '–', 'UDP offered': ((index[rid] || {}).params || {}).udpRate || '–' }, ...extra });

    if (run === 'operator_checks') {
      const ids = (raw.index || []).map(r => r.id).filter(id => !used.has(id));
      const policies = [...new Set(ids.map(id => D.policy(oper[id]) || '?'))].sort();
      const programs = ids.map((rid, i) => { const op = oper[rid] || {}, pr = index[rid].params || {};
        return program(i + 1, rid, index[rid].metrics, { facts: [
          ['What this is', `An operator ${op.control ? 'run started from the Control page' : 'check (' + (op.stage != null ? 'build stage ' + op.stage : 'harness test') + ')'}, not an AI experiment.`], ['Scheduling policy', D.policy(op) || '–'],
          ['Settings', Object.entries(pr).filter(([k]) => D.KNOB[k]).map(([k, v]) => `${D.KNOB[k]} ${D.knob(k, v)}`).join(', ') || 'all defaults']] }); });
      return { programs, page: { kind: 'checks', title: 'Two hosts, one link', kicker: 'Operator checks of the network simulation (ns-3), no AI',
        question: 'Simulations the operator ran while building the harness, to confirm the simulator behaves as designed before any AI used it.',
        facts: [['AI model', 'none', 'the operator chose every setting'], ['Runs', String(ids.length), 'each one ns-3 simulation'], ['Scheduling policies tried', policies.join(', '), 'the two ways the scheduler can split the link']],
        system: { ...system, no_ai: true }, knobs: [], measured, outcome: null, turns: [], hyps: [] } };
    }

    // ---- the AI session: join each evidence record with its experiment, hypothesis, verdict and thinking
    const byId = Object.fromEntries(led.map(r => [r.id, r])), verdictFor = {};
    led.forEach(r => { if (r.type === 'verdict') verdictFor[(r.body || {}).for] = r; });
    const hyps = [], programs = []; let prev = { ...defaults };
    led.filter(r => r.type === 'evidence').forEach((ev, k) => {
      const n = k + 1, eb = ev.body || {}, x = byId[ev.parent] || {}, xb = x.body || {};
      const h = (byId[x.parent] || {}).type === 'hypothesis' ? byId[x.parent] : {}, hb = h.body || {};
      const v = verdictFor[h.id], vb = (v || {}).body || {}, rid = eb.run_id;
      const params = { ...defaults, ...Object.fromEntries(Object.entries((index[rid] || {}).params || xb.params || {}).filter(([key]) => key in defaults)) };
      const changed = Object.entries(params).filter(([key, val]) => val !== prev[key]).map(([key, val]) => [D.KNOB[key] || key, D.knob(key, prev[key]), D.knob(key, val)]);
      prev = params;
      const metrics = (index[rid] || {}).metrics || num(eb);
      const crit = eb.checks || (eb.note ? [] : D.criteria(xb.pass_if || eb.pass_if, num(eb))), checked = crit.filter(c => c.ok != null);  // eb.checks: the harness's own checks (multi-simulation format)
      const others = Object.fromEntries(led.filter(r => r.type === 'evidence' && r.id !== ev.id).map(r => [r.id, num(r.body)]));
      hyps.push({ n, id: h.id || ev.id, turn: ev.turn, baseline: !!eb.note, by: h.id ? D.by(h) : null, text: hb.text || eb.note || '(no hypothesis was stated for this experiment)', prediction: hb.prediction, observations: hb.observations || null,
        run_id: rid, changed, settings: Object.entries(params).map(([key, val]) => [D.KNOB[key] || key, D.knob(key, val)]),
        criteria: crit, met: checked.filter(c => c.ok).length, total: checked.length,
        verdict: v ? { id: v.id, turn: v.turn, by: D.by(v), result: vb.result, because: vb.because, next: vb.next,
                       numbers: D.numbers([vb.because, vb.next, vb.observations].filter(Boolean).join(' \n '), num(eb), others) } : null, error: eb.error });
      const think = led.filter(s => (s.type === 'draft' || s.type === 'scratch') && s.turn === ev.turn).pop();
      programs.push(program(n, rid, eb.error ? null : metrics, { reasoning: think ? (think.body || {}).text || (think.body || {}).reasoning || null : null }));
    });
    const turns = [...new Set(led.map(r => r.turn))].sort((a, b) => a - b).map(t => {
      const recs = led.filter(r => r.turn === t), ev = recs.find(r => r.type === 'evidence'), vd = recs.find(r => r.type === 'verdict'), note = recs.find(r => r.type === 'note');
      let kind = 'other', label = 'Thinking only', exp = null;
      if (ev) { exp = (hyps.find(hh => hh.run_id === (ev.body || {}).run_id) || {}).n || null;
        if ((ev.body || {}).note) { kind = 'baseline'; label = 'Baseline run by the harness'; } else { kind = 'experiment'; label = 'Hypothesis and experiment ' + exp; } }
      else if (vd) { kind = 'verdict'; label = `Verdict on ${vd.body.for}: ${vd.body.result}`; exp = (hyps.find(hh => hh.id === vd.body.for) || {}).n || null; }
      else if (recs.some(r => r.type === 'malformed')) { kind = 'wasted'; label = 'No usable answer (the reply was cut off or invalid)'; }
      else if (note) { const b = note.body || {}, asked = (b.requests || []).map(q => q.tool).join(', ');
        if (b.text === 'model declared done') { kind = 'done'; label = 'The AI declared it was done'; } else { kind = 'info'; label = asked ? `Asked for information (${asked})` : 'Note'; } }
      return { turn: t, kind, label, exp, calls: recs.filter(r => r.type === 'draft' || r.type === 'scratch').length };
    });
    const count = k => turns.filter(t => t.kind === k).length, real = hyps.filter(h => !h.baseline), judged = hyps.filter(h => h.verdict);
    const res = r => judged.filter(h => h.verdict.result === r).length, scratch = led.filter(r => r.type === 'draft' || r.type === 'scratch');
    const mins = led.length ? Math.round((new Date(led[led.length - 1].ts) - new Date(led[0].ts)) / 60000) : null;
    const latest = real[real.length - 1];
    const bySource = Object.fromEntries(D.SOURCES.map(b => [b, written.filter(r => D.by(r) === b).length]));
    const page = { kind: 'loop', brief: man.brief || null, by: bySource, by_derived: written.some(r => !r.by), many: led !== written, title: 'Two hosts, one link', kicker: 'AI hypothesis loop over a network simulation (ns-3)', question: man.task || '',
      facts: [
        ['AI model', String((scratch.length && (scratch[scratch.length - 1].body || {}).model) || '?').split('/').pop(), 'local model on vLLM'],
        ['Thinking', scratch.length ? 'on' : 'off', scratch.length ? 'its reasoning is kept in the record' : 'no reasoning recorded'],
        ['Session', led.length ? String(led[0].ts || '').replace('T', ' ').slice(0, 16) : '–', mins != null ? mins + ' minutes' : ''],
        ['Experiments', String(real.length), 'chosen by the AI' + (hyps.length > real.length ? ', plus 1 baseline run by the harness' : '')],
        ['Turns', String(turns.filter(t => t.turn > 0).length), count('wasted') + ' without a usable answer'],
        ['Scheduling policy', hyps.length ? D.policy(oper[hyps[hyps.length - 1].run_id]) || '?' : '?', 'set by the operator, hidden from the AI']],
      system, measured,
      knobs: Object.entries(man.params || {}).map(([k, v]) => ({ name: D.KNOB[k] || k, range: v.choices ? v.choices.join(' / ') : `${v.min} to ${D.knob(k, v.max)}`, default: D.knob(k, v.default) })),
      outcome: { experiments: real.length, supported: res('supported'), refuted: res('refuted'), inconclusive: res('inconclusive'), unjudged: real.filter(h => !h.verdict).length,
        rules_met: hyps.filter(h => h.total && h.met === h.total).length, rules_total: hyps.filter(h => h.total).length,
        turns: turns.filter(t => t.turn > 0).length, wasted: count('wasted'), info: count('info'), done: written.some(r => r.type === 'report' || (r.type === 'note' && (r.body || {}).text === 'model declared done')), running: !!raw.running,
        latest: latest ? { id: latest.id, text: latest.text } : null },
      turns, hyps };
    return { page, programs };
  },
};
