// Two-hosts drawing for the ADRS main viewer: one simulation run as small charts over the same time axis.
// Four panels (one y-scale each, never two scales in one chart): throughput per flow, the TCP window, and the
// packets dropped from each queue. UDP is always --series-1 and TCP always --series-2, in every panel.
// `simple` = a small picture (hover cards, gallery): the throughput panel only. Uses the page's css().
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
  // The ordered page (task entry custom_page): one story from top to bottom, each section answering the
  // question the one before it raises. 0 what this is -> 1 the system -> 2 where it stands -> 3 what was
  // measured -> 4 how the AI got there -> 5 one experiment in detail. Data: /api/run "page" (adrs_view.py).
  // ====================================================================================================
  _ui: { sel: null, zoom: false },
  _css: `
.th { max-width: 1280px; margin: 0 auto; font-size: 15px; line-height: 1.5; color: var(--text-primary); }
.th h1, .th h2, .th h3, .th p { margin: 0; }
.th-top { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 22px 26px 20px; margin-bottom: 18px; }
.th-kicker { font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--text-muted); }
.th-top h1 { font-size: 30px; letter-spacing: -.02em; line-height: 1.2; margin: 4px 0 10px; }
.th-top h1 small { font-size: 15px; font-weight: 500; color: var(--text-secondary); margin-left: 10px; letter-spacing: 0; }
.th-q { font-size: 16px; max-width: 900px; color: var(--text-primary); }
.th-q b { display: block; font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); margin-bottom: 2px; }
.th-state { display: inline-flex; align-items: center; gap: 8px; margin-top: 12px; font-size: 13.5px; font-weight: 600; border: 1px solid var(--border); border-radius: 999px; padding: 3px 12px; }
.th-state i { width: 9px; height: 9px; border-radius: 50%; background: var(--text-muted); } .th-state.live i { background: var(--good); }
.th-facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 0; margin-top: 18px; border-top: 1px solid var(--border); }
.th-fact { padding: 12px 16px 0 0; } .th-fact dt { font-size: 11.5px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); }
.th-fact dd { margin: 2px 0 0; font-size: 16px; font-weight: 700; overflow-wrap: anywhere; } .th-fact dd small { display: block; font-size: 12.5px; font-weight: 400; color: var(--text-secondary); }
.th-sec { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 20px 26px 24px; margin-bottom: 18px; }
.th-sh { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 16px; }
.th-no { flex: none; width: 30px; height: 30px; border-radius: 50%; background: var(--text-primary); color: var(--surface-1); font-weight: 700; font-size: 15px; display: grid; place-items: center; margin-top: 1px; }
.th-sh h2 { font-size: 20px; letter-spacing: -.01em; line-height: 1.3; } .th-sh p { font-size: 14px; color: var(--text-secondary); max-width: 860px; }
.th-two { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 28px; } .th-wide { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 28px; align-items: start; }
@media (max-width: 900px) { .th-two, .th-wide { grid-template-columns: 1fr; } }
.th h3 { font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); margin: 0 0 8px; }
.th table { border-collapse: collapse; width: 100%; font-size: 14px; font-variant-numeric: tabular-nums; }
.th th { text-align: left; font-size: 12px; font-weight: 600; color: var(--text-muted); padding: 6px 12px 6px 0; border-bottom: 1px solid var(--border); vertical-align: bottom; }
.th td { padding: 8px 12px 8px 0; border-bottom: 1px solid var(--grid); vertical-align: top; } .th td.num, .th th.num { text-align: right; }
.th tr.pick { cursor: pointer; } .th tr.pick:hover td { background: var(--surface-0); } .th tr.on td { background: color-mix(in srgb, var(--series-1) 9%, transparent); }
.th tr.on td:first-child { box-shadow: inset 3px 0 0 var(--series-1); } .th td:first-child, .th th:first-child { padding-left: 10px; }
.th-muted { color: var(--text-muted); } .th-sm { font-size: 13px; color: var(--text-secondary); }
.th-tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; border: 1px solid var(--border); border-radius: 10px; }
@media (max-width: 900px) { .th-tiles { grid-template-columns: 1fr 1fr; } }
.th-tile { padding: 14px 18px 16px; border-left: 1px solid var(--border); } .th-tile:first-child { border-left: 0; }
.th-tile .big { font-size: 34px; font-weight: 700; line-height: 1.15; letter-spacing: -.02em; font-variant-numeric: tabular-nums; } .th-tile .big small { font-size: 16px; font-weight: 500; color: var(--text-secondary); letter-spacing: 0; }
.th-tile p { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.th-note { margin-top: 16px; padding: 12px 16px; border-left: 3px solid var(--text-primary); background: var(--surface-0); border-radius: 0 8px 8px 0; font-size: 14.5px; }
.th-note b.lbl { display: block; font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); }
.th-key { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 13px; color: var(--text-secondary); margin: 0 0 6px; align-items: center; }
.th-key i { display: inline-block; width: 11px; height: 11px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; } .th-key svg { vertical-align: middle; margin-right: 6px; }
.th-seg { display: inline-flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; } .th-seg button { font: inherit; font-size: 13px; padding: 4px 12px; border: 0; background: var(--surface-1); color: var(--text-secondary); cursor: pointer; }
.th-seg button.on { background: var(--text-primary); color: var(--surface-1); }
.th-strip { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 6px; margin-bottom: 18px; }
.th-turn { border: 1px solid var(--border); border-radius: 8px; padding: 7px 9px 8px; background: var(--surface-0); font: inherit; text-align: left; color: var(--text-primary); min-height: 62px; }
.th-turn small { display: block; font-size: 11px; color: var(--text-muted); } .th-turn b { display: block; font-size: 12.5px; line-height: 1.25; margin-top: 2px; }
.th-turn.k-experiment { background: var(--surface-1); border-color: var(--text-primary); cursor: pointer; } .th-turn.k-verdict { background: var(--surface-1); cursor: pointer; }
.th-turn.k-wasted { border-style: dashed; color: var(--text-muted); background: none; } .th-turn.k-wasted b { color: var(--critical); }
.th-turn.on { box-shadow: 0 0 0 2px var(--series-1); }
.th-hyp { display: grid; grid-template-columns: 52px minmax(0, 1fr) 190px 150px; gap: 14px; align-items: center; padding: 11px 12px; border: 1px solid var(--border); border-radius: 10px; margin-bottom: 8px;
  background: var(--surface-1); cursor: pointer; font: inherit; width: 100%; text-align: left; color: inherit; }
@media (max-width: 900px) { .th-hyp { grid-template-columns: 52px 1fr; } }
.th-hyp:hover { border-color: var(--text-muted); } .th-hyp.on { border-color: var(--series-1); box-shadow: 0 0 0 1px var(--series-1); }
.th-hyp .id { font-size: 18px; font-weight: 700; } .th-hyp .txt { font-size: 14.5px; } .th-hyp .chg { display: block; font-size: 13px; color: var(--text-secondary); margin-top: 3px; }
.th-rule { font-size: 13.5px; font-weight: 600; white-space: nowrap; } .th-rule small { display: block; font-weight: 400; font-size: 12px; color: var(--text-muted); }
.th-ok { color: var(--good); font-weight: 700; } .th-bad { color: var(--critical); font-weight: 700; }
.th-dl dt { font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); margin-top: 16px; } .th-dl dt:first-child { margin-top: 0; }
.th-dl dd { margin: 4px 0 0; font-size: 14.5px; overflow-wrap: anywhere; }
.th-chip { display: inline-block; border: 1px solid var(--border); border-radius: 8px; padding: 2px 9px; margin: 0 6px 6px 0; font-size: 13.5px; background: var(--surface-0); } .th-chip b { font-weight: 700; }
.th details > summary { cursor: pointer; font-size: 13.5px; color: var(--text-secondary); margin-top: 8px; } .th pre { white-space: pre-wrap; font: inherit; font-size: 13.5px; color: var(--text-secondary); max-height: 420px; overflow: auto; margin: 8px 0 0; }
.th-tabs { display: grid; grid-template-columns: repeat(var(--th-tabs, 4), minmax(0, 1fr)); gap: 10px; margin-bottom: 18px; }
.th-tabs a { display: block; text-decoration: none; color: var(--text-secondary); background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 11px 16px 12px; }
.th-tabs a:hover { border-color: var(--text-muted); }
.th-tabs a b { display: flex; align-items: center; gap: 10px; font-size: 16.5px; color: var(--text-primary); }
.th-tabs a b span { flex: none; width: 24px; height: 24px; border-radius: 50%; border: 1.5px solid var(--text-primary); display: grid; place-items: center; font-size: 13px; }
.th-tabs a small { display: block; font-size: 12.5px; margin: 3px 0 0 34px; line-height: 1.35; }
.th-tabs a.on { border-color: var(--text-primary); box-shadow: inset 0 -4px 0 var(--text-primary); } .th-tabs a.on b span { background: var(--text-primary); color: var(--surface-1); }
@media (max-width: 700px) { .th-tabs { grid-template-columns: 1fr; } }
.th-top.slim { padding: 14px 26px 16px; } .th-top.slim h1 { font-size: 22px; margin: 2px 0 0; }
.th-titleline { display: flex; align-items: center; justify-content: space-between; gap: 12px 20px; flex-wrap: wrap; } .th-titleline .th-state { margin-top: 0; }
.th-tabs a small { min-height: 4.05em; } .th-tabs.many a { padding: 11px 13px 12px; } .th-tabs.many a small { margin-left: 0; margin-top: 5px; }
.th-recs { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; }
.th-rec { text-align: left; font: inherit; color: inherit; background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 9px 12px 10px; cursor: pointer; }
.th-rec b { display: block; font-size: 14.5px; } .th-rec small { display: block; font-size: 12.5px; color: var(--text-secondary); margin-top: 2px; line-height: 1.35; }
.th-rec:hover { border-color: var(--text-muted); } .th-rec.on { border-color: var(--text-primary); box-shadow: 0 0 0 1px var(--text-primary); background: var(--surface-0); }
.th-evt tr.hd td { padding-top: 14px; border-bottom: 1px solid var(--border); } .th-evt tr.sum td { border-top: 1px solid var(--border); font-weight: 600; }
.th-evbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; } .th-evbar input[type=range] { flex: 1; min-width: 160px; accent-color: var(--text-primary); }
.th-evbtn { font: inherit; font-size: 13px; padding: 3px 10px; border: 1px solid var(--border); border-radius: 7px; background: var(--surface-1); color: var(--text-primary); cursor: pointer; } .th-evbtn:hover { border-color: var(--text-primary); }
.th-evkey { display: flex; flex-wrap: wrap; gap: 4px 18px; font-size: 12.5px; color: var(--text-secondary); margin-bottom: 8px; } .th-evkey i { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
.th-evside { display: grid; grid-template-columns: minmax(0, 1.75fr) minmax(330px, 1fr); gap: 20px; align-items: start; } @media (max-width: 1000px) { .th-evside { grid-template-columns: 1fr; } }
#th-evdia { min-height: 380px; } #th-evdet { min-height: 700px; }
.th-life { list-style: none; margin: 0; padding: 0; } .th-life li { display: grid; grid-template-columns: 24px minmax(0, 1fr); gap: 0 9px; padding: 7px 0; border-top: 1px solid var(--grid); }
.th-life .n { width: 21px; height: 21px; border-radius: 50%; border: 2px solid var(--text-primary); display: grid; place-items: center; font-size: 11px; font-weight: 700; margin-top: 1px; }
.th-life .l1 { display: flex; justify-content: space-between; gap: 10px; align-items: baseline; } .th-life .l1 b { font-size: 14px; } .th-life .l1 span { font-size: 13px; font-weight: 700; white-space: nowrap; font-variant-numeric: tabular-nums; }
.th-life .l2 { font-size: 12.5px; color: var(--text-secondary); margin-top: 2px; line-height: 1.4; } .th-life .l2 i { font-style: normal; font-weight: 700; color: var(--text-muted); text-transform: uppercase; font-size: 10.5px; letter-spacing: .05em; margin-right: 4px; }
.th-pk { font: inherit; font-size: 12.5px; color: var(--text-primary); background: var(--surface-0); border: 1px solid var(--border); border-radius: 5px; padding: 0 5px; cursor: pointer; } .th-pk:hover { border-color: var(--text-primary); }
.th-go { display: inline-block; margin-top: 14px; font-size: 14px; font-weight: 600; color: var(--text-primary); text-decoration: none; border: 1px solid var(--text-primary); border-radius: 8px; padding: 6px 14px; }
.th-go:hover { background: var(--text-primary); color: var(--surface-1); }
.th { --th-sim: color-mix(in srgb, #e9a23b 14%, var(--surface-1)); --th-simb: color-mix(in srgb, #e9a23b 55%, var(--border));
  --th-n0: color-mix(in srgb, #5f86c4 17%, var(--surface-1)); --th-n0b: color-mix(in srgb, #5f86c4 60%, var(--border));
  --th-n1: color-mix(in srgb, #d0647f 15%, var(--surface-1)); --th-n1b: color-mix(in srgb, #d0647f 55%, var(--border)); }
.th-clamp3 { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; min-height: 4.6em; }
.th-wide > div:last-child { min-height: 470px; }
.th-chain { list-style: none; margin: 0; padding: 0; }
.th-phase { font-size: 11.5px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; color: var(--text-muted); display: flex; align-items: center; gap: 10px; margin: 2px 0 12px; }
.th-phase::after { content: ""; flex: 1; height: 1px; background: var(--border); } .th-phase span { font-weight: 400; letter-spacing: 0; text-transform: none; font-size: 12.5px; }
.th-step { display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: 0 14px; position: relative; padding-bottom: 20px; }
.th-step::before { content: ""; position: absolute; left: 16px; top: 36px; bottom: 2px; width: 2px; background: var(--border); } .th-step.end::before { display: none; }
.th-step > .n { width: 34px; height: 34px; border-radius: 50%; border: 2px solid var(--text-primary); background: var(--surface-1); display: grid; place-items: center; font-weight: 700; font-size: 15px; }
.th-step.done > .n { background: var(--text-primary); color: var(--surface-1); }
.th-step .hd { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-top: 4px; } .th-step .hd b { font-size: 17px; letter-spacing: -.01em; }
.th-step .hd span { font-size: 12.5px; color: var(--text-muted); } .th-step .ask { font-size: 13.5px; color: var(--text-secondary); margin: 1px 0 9px; }
.th-step .body { border: 1px solid var(--border); border-radius: 10px; background: var(--surface-1); padding: 12px 14px; }
.th-step .lead { font-size: 16px; font-weight: 600; line-height: 1.45; } .th-step .rest { font-size: 14px; color: var(--text-secondary); margin-top: 6px; }
.th-step table { font-size: 13.5px; } .th-step td, .th-step th { padding-top: 6px; padding-bottom: 6px; }
.th-nums { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0; } .th-nums div { padding: 2px 14px 2px 0; }
.th-nums small { display: block; font-size: 12px; color: var(--text-secondary); } .th-nums b { font-size: 21px; font-variant-numeric: tabular-nums; letter-spacing: -.01em; } .th-nums b i { font-style: normal; font-size: 13px; font-weight: 500; color: var(--text-secondary); margin-left: 3px; }
.th-sum { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 600; margin-bottom: 8px; } .th-sum .mark { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; color: #fff; font-size: 15px; }
.th-sum .mark.ok { background: var(--good); } .th-sum .mark.bad { background: var(--critical); }
.th-warn { margin-top: 8px; font-size: 13.5px; border-left: 3px solid var(--critical); padding: 4px 10px; background: color-mix(in srgb, var(--critical) 8%, transparent); }
.th-md { display: grid; grid-template-columns: minmax(280px, 340px) minmax(0, 1fr); gap: 24px; align-items: start; }
.th-mdlist { position: sticky; top: 12px; max-height: calc(100vh - 24px); overflow-y: auto; padding: 2px; }
@media (max-width: 1000px) { .th-md { grid-template-columns: 1fr; } .th-mdlist { position: static; max-height: none; } }
.th-item { display: block; width: 100%; text-align: left; font: inherit; color: inherit; background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 9px 12px 10px; margin-bottom: 8px; cursor: pointer; }
.th-item:hover { border-color: var(--text-muted); } .th-item.on { border-color: var(--text-primary); box-shadow: 0 0 0 1px var(--text-primary); background: var(--surface-0); }
.th-item .top { display: flex; align-items: center; gap: 8px; justify-content: space-between; } .th-item .top b { font-size: 15.5px; } .th-item .top .vd { font-size: 12.5px; padding: 1px 9px; }
.th-item .txt { display: block; font-size: 13.5px; line-height: 1.4; margin-top: 4px; } .th-item .chg { display: block; font-size: 12.5px; color: var(--text-secondary); margin-top: 4px; }
.th-item .th-rule { font-size: 12.5px; display: block; margin-top: 4px; }
.th-mddet h3.exp { font-size: 20px; letter-spacing: -.01em; text-transform: none; color: var(--text-primary); margin: 0; } .th-mddet .expsub { font-size: 13.5px; color: var(--text-secondary); margin: 2px 0 14px; }
.th-side { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(340px, 1fr); gap: 22px; align-items: start; }
@media (max-width: 1000px) { .th-side { grid-template-columns: 1fr; } }
.th-det { border: 1px solid var(--border); border-top: 5px solid var(--dc, var(--text-muted)); border-radius: 10px; background: var(--surface-1); padding: 14px 18px 16px; min-width: 0; }
.th-det .where { font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); }
.th-det h3.name { font-size: 22px; letter-spacing: -.01em; text-transform: none; color: var(--text-primary); margin: 2px 0 0; line-height: 1.25; }
.th-det code { font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--text-muted); overflow-wrap: anywhere; }
.th-det .role { font-size: 13.5px; color: var(--text-secondary); margin: 8px 0 10px; } .th-det .role i { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
.th-det table { font-size: 14px; } .th-det td { padding: 7px 10px 7px 0 !important; border-bottom: 1px solid var(--grid); } .th-det tr:first-child td { border-top: 1px solid var(--border); }
.th-det td.k { color: var(--text-secondary); width: 44%; } .th-det td.v { font-weight: 700; } .th-det td.v small { display: block; font-size: 11.5px; font-weight: 400; color: var(--text-muted); }
.th-sim { background: var(--th-sim); border: 1px solid var(--th-simb); border-radius: 10px; padding: 0 16px 18px; }
.th-simhead { text-align: center; font-weight: 700; font-size: 15px; padding: 9px 0; border-bottom: 1px solid var(--th-simb); margin: 0 -16px 16px; }
.th-nodes { display: grid; grid-template-columns: minmax(0, 280px) minmax(96px, 190px) minmax(0, 280px); grid-template-rows: auto repeat(4, auto); justify-content: center; gap: 7px 0; }
.th-node { display: grid; grid-row: 1 / span 5; grid-template-rows: subgrid; border: 1px solid var(--nb); padding: 0 10px 10px; min-width: 0; }
.th-node.n0 { grid-column: 1; --nb: var(--th-n0b); background: var(--th-n0); } .th-node.n1 { grid-column: 3; --nb: var(--th-n1b); background: var(--th-n1); }
.th-nodehead { text-align: center; padding: 6px 0 7px; border-bottom: 1px solid var(--nb); margin: 0 -10px 2px; }
.th-nodehead b { font-size: 15px; } .th-nodehead span { display: block; font-size: 12px; color: var(--text-secondary); }
.th-lay { border: 1px solid var(--nb); background: color-mix(in srgb, var(--surface-1) 50%, transparent); padding: 5px 7px 7px; min-width: 0; }
.th-layhead { text-align: center; font-size: 12.5px; font-weight: 700; margin-bottom: 5px; }
.th-laybody { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 5px; align-content: start; }
.th-oc { font: inherit; font-size: 12.5px; font-weight: 600; line-height: 1.25; text-align: center; color: var(--text-primary); background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 6px; padding: 5px 6px 5px 10px; cursor: pointer; position: relative; overflow: hidden; min-width: 0; }
.th-oc::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--border); }
.th-oc.udp::before { background: var(--series-1); } .th-oc.tcp::before { background: var(--series-2); }
.th-oc.wide { grid-column: 1 / -1; } .th-oc.key { border: 2px solid var(--text-primary); } .th-oc.key::before { background: var(--text-primary); }
.th-oc:hover { border-color: var(--text-primary); }
.th-oc.on { background: var(--text-primary); color: var(--surface-1); border-color: var(--text-primary); }
.th-link.on b { background: var(--text-primary); color: var(--surface-1); display: inline-block; border-radius: 6px; padding: 2px 8px; } .th-link.on i { height: 6px; margin-top: 3px; } .th-link.on i::before, .th-link.on i::after { top: -4px; }
.th-link { grid-column: 2; grid-row: 5; align-self: center; margin: 0 -11px; position: relative; z-index: 1; text-align: center; background: none; border: 0; padding: 0; font: inherit; color: var(--text-primary); cursor: pointer; }
.th-link b { display: block; font-size: 13px; margin-bottom: 3px; } .th-link small { display: block; font-size: 11.5px; color: var(--text-secondary); margin-top: 4px; }
.th-link i { display: block; height: 4px; margin: 0 9px; background: var(--text-primary); position: relative; }
.th-link i::before, .th-link i::after { content: ""; position: absolute; top: -5px; border: 7px solid transparent; }
.th-link i::before { left: -16px; border-right-color: var(--text-primary); } .th-link i::after { right: -16px; border-left-color: var(--text-primary); }
.th-ai { display: inline-block; width: 8px; height: 8px; background: var(--text-primary); transform: rotate(45deg); margin-right: 7px; vertical-align: 1px; }
.th-legend { display: flex; flex-wrap: wrap; gap: 6px 22px; font-size: 13px; color: var(--text-secondary); margin: 14px 0 0; align-items: center; justify-content: center; }
.th-legend i.sw { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
.th-cfgs { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: 30px; align-items: start; }
.th-cfg { margin-bottom: 22px; } .th-cfg h3 { font-size: 15px; letter-spacing: 0; text-transform: none; color: var(--text-primary); padding: 7px 12px; margin: 0; border: 1px solid var(--nb, var(--border)); background: var(--nbg, var(--surface-0)); }
.th-cfg h3 span { font-weight: 400; font-size: 13px; color: var(--text-secondary); margin-left: 8px; }
.th-cfg.n0 { --nb: var(--th-n0b); --nbg: var(--th-n0); } .th-cfg.n1 { --nb: var(--th-n1b); --nbg: var(--th-n1); }
.th-cfg table { font-size: 13.5px; } .th-cfg td { padding: 5px 10px 5px 0; }
.th-cfg tr.lay td { font-size: 11.5px; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; color: var(--text-muted); padding: 12px 0 4px 10px; border-bottom: 1px solid var(--border); }
.th-cfg td.ob { width: 34%; border-left: 4px solid var(--border); padding-left: 10px; } .th-cfg td.ob.udp { border-left-color: var(--series-1); } .th-cfg td.ob.tcp { border-left-color: var(--series-2); }
.th-cfg td.ob b { display: block; font-size: 14px; } .th-cfg td.ob code { font: 11px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--text-muted); overflow-wrap: anywhere; }
.th-cfg td.k { width: 30%; color: var(--text-secondary); padding-left: 10px; } .th-cfg td.v { font-weight: 600; } .th-cfg td.v small { display: block; font-size: 11px; font-weight: 400; color: var(--text-muted); }
.th-cfg tr.first td { border-top: 1px solid var(--border); } .th-cfg tr td { border-bottom: 0; }
.th-cfg tr.sel td { background: color-mix(in srgb, var(--text-primary) 7%, transparent); }
.th-cfg3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; align-items: start; }
@media (max-width: 900px) { .th-nodes { grid-template-columns: 1fr; } .th-node { grid-column: 1 !important; grid-row: auto; grid-template-rows: none; row-gap: 7px; } .th-link { grid-column: 1; grid-row: auto; margin: 6px 0; }
  .th-cfgs, .th-cfg3 { grid-template-columns: 1fr; } }
.th-tip { position: fixed; z-index: 50; pointer-events: none; background: var(--surface-1); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; font-size: 13px; box-shadow: 0 6px 20px rgba(0,0,0,.14); }
.th-tip b { display: block; margin-bottom: 2px; } .th-tip i { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }
`,
  _e: s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])),
  _first(t) {  // the first sentence of a hypothesis, without its own "H1:" prefix
    t = String(t || '').replace(/^\s*H\d+\s*:\s*/, '');
    const i = t.search(/[.!?](\s|$)/);
    return i > 30 ? t.slice(0, i + 1) : t;
  },
  _rate(sv) { return String(sv).replace(/([0-9.]+)\s*([kMG]?)bps/g, '$1 $2bps').replace(/([0-9.]+)us\b/g, '$1 µs').replace(/([0-9.]+)ms\b/g, '$1 ms'); },

  // The network as a picture: who sends, where packets wait, what splits the link, who receives.
  _topology(sys) {
    const ink = css('--text-primary'), sec = css('--text-secondary'), mut = css('--text-muted'), line = css('--border'),
      s0 = css('--surface-0'), s1 = css('--surface-1'), udp = css('--series-1'), tcp = css('--series-2');
    const d = sys.defaults || {}, R = TASK_VIEW._rate;
    const w = d.weightUdp ?? 0.5, q = d.queuePkts ?? 100;
    const knob = (x, y) => `<path d="M${x} ${y - 5} l5 5 -5 5 -5 -5z" fill="${ink}"/>`;
    const txt = (x, y, t, o = {}) => `<text x="${x}" y="${y}" font-size="${o.size || 12.5}" font-weight="${o.bold ? 700 : 400}" fill="${o.fill || sec}" text-anchor="${o.anchor || 'start'}">${t}</text>`;
    const app = (y, c, name, how, val, adjustable) => `<rect x="34" y="${y}" width="190" height="78" rx="9" fill="${s1}" stroke="${line}"/><rect x="34" y="${y}" width="6" height="78" rx="3" fill="${c}"/>` +
      txt(52, y + 24, name, { bold: true, fill: ink, size: 14 }) + txt(52, y + 43, how) + (adjustable ? knob(58, y + 60) : '') + txt(adjustable ? 70 : 52, y + 64.5, val, { bold: true, fill: ink });
    const queue = (y, c, name) => {
      let g = txt(268, y - 9, name, { bold: true, fill: ink, size: 13 });
      for (let i = 0; i < 10; i++) g += `<rect x="${268 + i * 19}" y="${y}" width="16" height="30" rx="3" fill="${i >= 4 ? c : s1}" fill-opacity="${i >= 4 ? 0.85 : 1}" stroke="${i >= 4 ? c : line}"/>`;
      return g + knob(274, y + 47) + txt(286, y + 51.5, `room for ${q} packets`, { bold: true, fill: ink });
    };
    const arrow = (x1, y1, x2, y2, c = mut, sw = 2) => `<line x1="${x1}" y1="${y1}" x2="${x2 - 7}" y2="${y2}" stroke="${c}" stroke-width="${sw}"/><path d="M${x2} ${y2} l-9 -5 v10z" fill="${c}"/>`;
    return `<svg viewBox="0 0 1100 330" width="100%" style="display:block;max-width:100%;font-family:inherit" role="img" aria-label="Sender with a UDP source and a TCP source, each feeding its own queue; a scheduler splits one 1 Gbps link between the two queues; the receiver counts what arrives">
      <rect x="14" y="26" width="676" height="264" rx="16" fill="${s0}" stroke="${line}"/>${txt(34, 52, 'SENDER', { bold: true, fill: mut, size: 12 })}
      ${app(70, udp, 'UDP source', 'sends at a constant rate', `offers ${R(d.udpRate ?? '2Gbps')}`, true)}
      ${app(184, tcp, 'TCP source', 'sends as fast as TCP allows', String(d.tcpVariant ?? 'TcpCubic').replace(/^Tcp/, 'TCP '), true)}
      ${arrow(224, 109, 262, 109)}${arrow(224, 223, 262, 223)}
      ${queue(94, udp, 'UDP queue')}${queue(208, tcp, 'TCP queue')}
      ${arrow(462, 109, 502, 140)}${arrow(462, 223, 502, 192)}
      <rect x="502" y="96" width="170" height="140" rx="12" fill="${s1}" stroke="${ink}" stroke-width="2"/>
      ${txt(587, 122, 'Scheduler', { bold: true, fill: ink, size: 14, anchor: 'middle' })}${txt(587, 141, 'splits the link', { anchor: 'middle' })}
      ${txt(587, 180, `${Math.round(100 * w)} : ${Math.round(100 * (1 - w))}`, { bold: true, fill: ink, size: 26, anchor: 'middle' })}
      ${knob(530, 206)}${txt(542, 210.5, 'UDP : TCP share', { bold: true, fill: ink })}
      <line x1="672" y1="166" x2="866" y2="166" stroke="${ink}" stroke-width="7" stroke-linecap="round"/><path d="M878 166 l-14 -9 v18z" fill="${ink}"/>
      ${txt(784, 146, 'one link', { bold: true, fill: ink, size: 14, anchor: 'middle' })}
      ${txt(784, 192, `${R(sys.link_rate)} · ${R(sys.link_delay)} delay`, { anchor: 'middle' })}${txt(784, 210, `packets up to ${sys.mtu} bytes`, { anchor: 'middle' })}
      <rect x="880" y="26" width="204" height="264" rx="16" fill="${s0}" stroke="${line}"/>${txt(900, 52, 'RECEIVER', { bold: true, fill: mut, size: 12 })}
      <rect x="900" y="70" width="166" height="78" rx="9" fill="${s1}" stroke="${line}"/><rect x="900" y="70" width="6" height="78" rx="3" fill="${udp}"/>
      ${txt(918, 94, 'UDP receiver', { bold: true, fill: ink, size: 14 })}${txt(918, 113, 'counts what arrives')}${txt(918, 134, '→ UDP goodput', { bold: true, fill: ink })}
      <rect x="900" y="184" width="166" height="78" rx="9" fill="${s1}" stroke="${line}"/><rect x="900" y="184" width="6" height="78" rx="3" fill="${tcp}"/>
      ${txt(918, 208, 'TCP receiver', { bold: true, fill: ink, size: 14 })}${txt(918, 227, 'counts what arrives')}${txt(918, 248, '→ TCP goodput', { bold: true, fill: ink })}
      ${knob(20, 314)}${txt(32, 318.5, sys.no_ai ? 'an adjustable setting (values shown are the defaults)' : 'a setting the AI may change (values shown are the defaults)', { fill: sec })}${txt(1084, 318.5, 'everything else is fixed', { fill: mut, anchor: 'end' })}
    </svg>`;
  },

  // The system in two parts. _schema: the structure only, drawn the way ns-3 itself is drawn (each node a small stack
  // of layers, application on top, device at the bottom; the link a line between the two devices). _config: the
  // settings of every object, in tables. Both come from viewer/objects.json; {values} are filled from the manifest.
  _fill(sys) {
    const R = TASK_VIEW._rate, d = sys.defaults || {};
    const vals = { ...d, linkRate: sys.link_rate, linkDelay: sys.link_delay, mtu: sys.mtu, segment: (sys.mtu || 1500) - 52, mode: sys.mode || 'share',
      tcpShare: d.weightUdp != null ? +(1 - d.weightUdp).toFixed(3) : '?', tcpVariantPlain: String(d.tcpVariant || '').replace(/^Tcp/, ''), queuePktsUdp: d.queuePktsUdp != null ? d.queuePktsUdp : d.queuePkts, queuePktsTcp: d.queuePktsTcp != null ? d.queuePktsTcp : d.queuePkts };
    return t => R(String(t).replace(/\{(\w+)\}/g, (m, k) => (vals[k] != null ? vals[k] : m)));
  },
  _find(O, id) {  // an object of the schema by its id: "link", or "<host>-<layer>-<index>"
    if (id === 'link') return { o: O.channel, where: 'Link between the two devices', role: 'carries the signal from one device to the other' };
    const [hk, lk, i] = String(id || '').split('-'), H = (O.hosts || []).find(x => x.key === hk), L = (O.layers || []).find(x => x.key === lk);
    const o = H && L && (H[lk] || [])[+i];
    return o ? { o, where: `${H.node || H.title} · ${H.title} › ${L.name}`, role: (L.roles || {})[H.key] || L.role || '' } : null;
  },
  _detail(O, sys, id) {  // the settings of the chosen object, shown beside the schema
    const e = TASK_VIEW._e, fill = TASK_VIEW._fill(sys), f = TASK_VIEW._find(O, id);
    if (!f) return '<p class="th-muted">Click an object in the picture to see its settings.</p>';
    const note = { ns3: 'ns-3 default', op: sys.no_ai ? 'set by the operator' : 'set by the operator, hidden from the AI' }, o = f.o;
    const col = o.flow === 'udp' ? css('--series-1') : o.flow === 'tcp' ? css('--series-2') : css('--text-muted');
    return `<div class="where">${e(f.where)}</div><h3 class="name">${e(o.name)}</h3><code>${e(fill(o.cls))}</code>
      <p class="role"><i style="background:${col}"></i>${o.flow === 'udp' ? 'Handles UDP' : o.flow === 'tcp' ? 'Handles TCP' : id === 'link' ? 'Carries both flows' : 'Shared by both flows'}${f.role ? ' · ' + e(f.role) : ''}</p>
      <table><tbody>${o.rows.map(([k, v, fl]) => `<tr><td class="k">${e(k)}</td><td class="v">${fl === 'ai' ? '<i class="th-ai" title="adjustable"></i>' : ''}${e(fill(v))}${note[fl] ? `<small>${note[fl]}</small>` : ''}</td></tr>`).join('')}</tbody></table>
      ${o.rows.some(r => r[2] === 'ai') ? `<p class="th-sm" style="margin-top:10px"><i class="th-ai"></i>${sys.no_ai ? 'an adjustable setting' : 'a setting the AI may change'}; the value shown is the default.</p>` : ''}`;
  },
  _schema(O, sys, chosen) {
    const e = TASK_VIEW._e;
    const node = (H, cls) => `<div class="th-node ${cls}"><div class="th-nodehead"><b>${e(H.node || H.title)}</b><span>${e(H.title)}</span></div>${
      O.layers.map(L => `<div class="th-lay"><div class="th-layhead">${e(L.name)}</div><div class="th-laybody">${
        (H[L.key] || []).map((o, i) => `<button class="th-oc ${o.flow || ''}${o.wide ? ' wide' : ''}${o.key ? ' key' : ''}${chosen === `${H.key}-${L.key}-${i}` ? ' on' : ''}" data-obj="${H.key}-${L.key}-${i}" title="Show the settings of ${e(o.name)}">${e(o.name)}</button>`).join('')}</div></div>`).join('')}</div>`;
    return `<div class="th-sim"><div class="th-simhead">NS-3 Simulation</div><div class="th-nodes">${node(O.hosts[0], 'n0')}
        <button class="th-link${chosen === 'link' ? ' on' : ''}" data-obj="link" title="Show the settings of the link"><b>${e(O.channel.name)}</b><i></i><small>joins the two devices</small></button>${node(O.hosts[1], 'n1')}</div></div>
      <div class="th-legend"><span><i class="sw" style="background:${css('--series-1')}"></i>handles UDP</span><span><i class="sw" style="background:${css('--series-2')}"></i>handles TCP</span>
        <span><i class="sw" style="background:${css('--border')}"></i>shared by both</span><span>click an object to see its settings on the right</span></div>`;
  },
  _config(O, sys) {
    const e = TASK_VIEW._e, fill = TASK_VIEW._fill(sys);
    const note = { ns3: 'ns-3 default', op: sys.no_ai ? 'set by the operator' : 'set by the operator, hidden from the AI' };
    const obj = (o, id, bare) => o.rows.map(([k, v, f], i) => `<tr class="${i ? '' : 'first'}${id === sys.chosen ? ' sel' : ''}" data-cfg="${id}">${i ? '' : `<td class="ob ${o.flow || ''}" rowspan="${o.rows.length}" id="th-o-${id}">${bare ? '' : `<b>${e(o.name)}</b>`}<code>${e(fill(o.cls))}</code></td>`}
      <td class="k">${e(k)}</td><td class="v">${f === 'ai' ? '<i class="th-ai" title="adjustable"></i>' : ''}${e(fill(v))}${note[f] ? `<small>${note[f]}</small>` : ''}</td></tr>`).join('');
    const host = (H, cls) => `<div class="th-cfg ${cls}"><h3>${e(H.node || H.title)}<span>${e(H.title)} · ${e(H.sub)}</span></h3><table><tbody>${
      O.layers.map(L => `<tr class="lay"><td colspan="3">${e(L.name)}</td></tr>` + (H[L.key] || []).map((o, i) => obj(o, `${H.key}-${L.key}-${i}`)).join('')).join('')}</tbody></table></div>`;
    const single = (o, id, title, bare) => `<div class="th-cfg"><h3>${e(title)}</h3><table><tbody>${obj(o, id, bare)}</tbody></table></div>`;
    return { hosts: `<div class="th-cfgs"><div>${host(O.hosts[0], 'n0')}</div><div>${host(O.hosts[1], 'n1')}${single(O.channel, 'link', 'Link between the two devices')}</div></div>
        <p class="th-sm"><i class="th-ai"></i>${sys.no_ai ? 'an adjustable setting' : 'a setting the AI may change'}; the value shown is the default.</p>`,
      around: `<div class="th-cfg3">${(O.around || []).map((o, i) => single(o, 'around-' + i, o.name, true)).join('')}</div>` };
  },

  // One prediction as a picture: the allowed range (shaded) and where the measured value fell (dot).
  _range(c) {
    if (c.ok == null || typeof c.v !== 'number') return '';
    const lo = c.lov ?? c.eqv, hi = c.hiv ?? c.eqv, W = 190, H = 22, good = css('--good'), bad = css('--critical'), mut = css('--text-muted');
    const ref = lo != null && hi != null ? (hi - lo) || Math.abs(hi) * 0.05 || 1 : Math.max(Math.abs(c.v - (lo ?? hi)), Math.abs(lo ?? hi) * 0.05, 1e-9);
    let a = (lo ?? Math.min(hi, c.v) - ref) - ref * 0.6, b = (hi ?? Math.max(lo, c.v) + ref) + ref * 0.6;
    a = Math.min(a, c.v - ref * 0.3); b = Math.max(b, c.v + ref * 0.3);
    const X = v => 6 + (W - 12) * (v - a) / (b - a), x0 = lo != null ? X(lo) : 0, x1 = hi != null ? X(hi) : W;
    return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="allowed ${c.need}, measured ${c.measured}" style="display:block">
      <line x1="0" y1="11" x2="${W}" y2="11" stroke="${mut}" stroke-opacity=".45" stroke-width="1.5"/>
      <rect x="${x0.toFixed(1)}" y="5" width="${Math.max(3, x1 - x0).toFixed(1)}" height="12" rx="3" fill="${good}" fill-opacity=".22" stroke="${good}" stroke-opacity=".6"/>
      <circle cx="${X(c.v).toFixed(1)}" cy="11" r="5.5" fill="${c.ok ? good : bad}" stroke="${css('--surface-1')}" stroke-width="2"/></svg>`;
  },

  // UDP and TCP goodput of every experiment against its UDP share: the whole investigation in one picture.
  _map(pts, sel, zoom) {
    const ink = css('--text-primary'), sec = css('--text-secondary'), mut = css('--text-muted'), grid = css('--grid'), s1 = css('--surface-1'),
      udp = css('--series-1'), tcp = css('--series-2');
    const W = 700, H = 340, L = 56, R = 18, T = 26, B = 46;
    const link = (pts[0] && pts[0].link) || 1000;
    let x0 = 0, x1 = 1, y0 = 0, y1 = TASK_VIEW._nice(link).top, ystep = TASK_VIEW._nice(link).step;
    if (zoom) {
      const zs = pts.filter(p => zoom[0] <= p.w && p.w <= zoom[1]), vals = zs.flatMap(p => [p.udp, p.tcp]);
      x0 = zoom[0]; x1 = zoom[1];
      const lo = Math.min(...vals), hi = Math.max(...vals), pad = Math.max(2, (hi - lo) * 0.25);
      ystep = [1, 2, 5, 10, 20, 50, 100].find(k => (hi - lo + 2 * pad) / k <= 6) || 200;
      y0 = Math.floor((lo - pad) / ystep) * ystep; y1 = Math.ceil((hi + pad) / ystep) * ystep;
    }
    const X = w => L + (W - L - R) * (w - x0) / (x1 - x0), Y = v => H - B - (H - T - B) * (v - y0) / (y1 - y0);
    let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block;max-width:100%;font-family:inherit" role="img" aria-label="UDP and TCP goodput of each experiment against the UDP share of the link">`;
    for (let v = y0; v <= y1 + 1e-9; v += ystep) s += `<line x1="${L}" y1="${Y(v)}" x2="${W - R}" y2="${Y(v)}" stroke="${grid}"/><text x="${L - 8}" y="${Y(v) + 4}" font-size="12" text-anchor="end" fill="${mut}">${Math.round(v)}</text>`;
    const xstep = zoom ? [0.002, 0.005, 0.01, 0.02].find(k => (x1 - x0) / k <= 8) || 0.05 : 0.1;
    for (let k = Math.ceil(x0 / xstep - 1e-9); k * xstep <= x1 + 1e-9; k++) { const w = k * xstep;
      s += `<line x1="${X(w)}" y1="${H - B}" x2="${X(w)}" y2="${H - B + 5}" stroke="${mut}"/><text x="${X(w)}" y="${H - B + 19}" font-size="12" text-anchor="middle" fill="${mut}">${+w.toFixed(3)}</text>`; }
    s += `<text x="${(L + W - R) / 2}" y="${H - 6}" font-size="12.5" text-anchor="middle" fill="${sec}">UDP share of the link set by the AI (TCP gets the rest)</text>` +
      `<text x="${L - 44}" y="${T - 10}" font-size="12.5" fill="${sec}">Goodput, Mbps</text>`;
    // what each flow was configured to get: share x link rate
    const clipY = v => Math.max(y0, Math.min(y1, v));
    const guide = (f, c) => { const a = f(x0), b = f(x1);
      return `<line x1="${X(x0)}" y1="${Y(clipY(a))}" x2="${X(x1)}" y2="${Y(clipY(b))}" stroke="${c}" stroke-width="1.5" stroke-dasharray="5 4" stroke-opacity=".55"/>`; };
    if (!zoom) s += guide(w => w * link, udp) + guide(w => (1 - w) * link, tcp);
    const shown = pts.filter(p => p.w >= x0 - 1e-9 && p.w <= x1 + 1e-9);
    shown.forEach(p => { if (p.n === sel) s += `<line x1="${X(p.w)}" y1="${T}" x2="${X(p.w)}" y2="${H - B}" stroke="${ink}" stroke-width="1" stroke-dasharray="2 3"/>`; });
    shown.forEach(p => { const on = p.n === sel;
      s += `<circle cx="${X(p.w)}" cy="${Y(p.udp)}" r="${on ? 7 : 5.5}" fill="${udp}" stroke="${on ? ink : s1}" stroke-width="2"/>` +
        `<circle cx="${X(p.w)}" cy="${Y(p.tcp)}" r="${on ? 7 : 5.5}" fill="${tcp}" stroke="${on ? ink : s1}" stroke-width="2"/>`; });
    // one label per group of experiments that sit close together
    const groups = []; shown.slice().sort((a, b) => a.w - b.w).forEach(p => { const g = groups[groups.length - 1];
      if (g && X(p.w) - X(g[g.length - 1].w) < 30) g.push(p); else groups.push([p]); });
    groups.forEach(g => { const cx = g.reduce((a, p) => a + X(p.w), 0) / g.length, top = Math.min(...g.flatMap(p => [Y(p.udp), Y(p.tcp)]));
      s += `<text x="${Math.max(L + 14, Math.min(W - R - 14, cx))}" y="${Math.max(T - 6, top - 12)}" font-size="12.5" font-weight="700" text-anchor="middle" fill="${ink}">${g.map(p => '#' + p.n).join(' ')}</text>`; });
    shown.forEach(p => { s += `<rect class="th-hit" data-exp="${p.n}" x="${X(p.w) - 13}" y="${T}" width="26" height="${H - T - B}" fill="transparent" style="cursor:pointer"/>`; });
    return s + '</svg>';
  },

  page(root, data) {
    TASK_VIEW._last = [root, data];
    if (!document.getElementById('th-css')) { const st = document.createElement('style'); st.id = 'th-css'; st.textContent = TASK_VIEW._css; document.head.appendChild(st); }
    const ui = TASK_VIEW._ui, e = TASK_VIEW._e;
    // content is built here from the harness's raw files (TH_DATA), the same for the standalone page and the ADRS viewer
    const raw = data.raw || (data.page && data.page.raw);
    if (!raw) { root.innerHTML = '<div class="th-sec">Loading…</div>'; return; }
    const key = data.run + '|' + (raw.ledger || []).length + '|' + (raw.index || []).length + '|' + Object.keys(raw.series || {}).length + '|' + !!raw.running;
    if (TASK_VIEW._built !== key) { TASK_VIEW._built = key; TASK_VIEW._content = TH_DATA.build(raw, data.run); }
    const P = TASK_VIEW._content.page, ps = TASK_VIEW._content.programs;
    if (ui.run !== data.run) { ui.run = data.run; ui.sel = null; ui.zoom = false; }
    const byN = Object.fromEntries(ps.map(p => [p.iteration, p]));
    const hyp = Object.fromEntries((P.hyps || []).map(h => [h.n, h]));
    if (!byN[ui.sel]) ui.sel = ps.length ? ps[ps.length - 1].iteration : null;
    const sel = byN[ui.sel], H = hyp[ui.sel];
    const m = p => p.metrics || {}, mb = v => (typeof v === 'number' ? (v / 1e6).toFixed(1) : '–'), pc = v => (typeof v === 'number' ? (100 * v).toFixed(1) + '%' : '–');
    const pts = ps.filter(p => typeof m(p).udp_goodput_bps === 'number').map(p => ({ n: p.iteration, w: m(p).weight_udp, udp: m(p).udp_goodput_bps / 1e6, tcp: m(p).tcp_goodput_bps / 1e6, link: (m(p).link_rate_bps || 1e9) / 1e6 }));
    // a close-up exists when several experiments sit within 0.05 of each other
    const ws = [...new Set(pts.map(p => p.w))].sort((a, b) => a - b); let best = [];
    ws.forEach((w, i) => { const g = ws.filter(v => v >= w && v <= w + 0.05); if (g.length > best.length) best = g; });
    const zr = best.length >= 2 ? [Math.floor((best[0] - 0.004) * 500) / 500, Math.ceil((best[best.length - 1] + 0.004) * 500) / 500] : null;
    const pill = (res, text) => `<span class="vd ${e(res || 'pending')}">${e(text || res || 'not judged')}</span>`;
    const rule = h => !h || !h.total ? '<span class="th-muted">–</span>' : `<span class="th-rule"><span class="${h.met === h.total ? 'th-ok' : 'th-bad'}">${h.met === h.total ? '✓' : '✕'}</span> ${h.met} of ${h.total} met</span>`;
    const verdict = h => !h ? '' : h.baseline ? pill('pending', 'baseline') : h.verdict ? pill(h.verdict.result) : pill('pending', 'not judged');
    const sec = (no, title, sub, body, id = '') => `<section class="th-sec"${id ? ` id="${id}"` : ''}><div class="th-sh"><span class="th-no">${no}</span><div><h2>${title}</h2><p>${sub}</p></div></div>${body}</section>`;
    const loop = P.kind === 'loop', O = P.outcome;
    const TABS = [['overview', 'Overview', loop ? 'the question, where it stands, every experiment at a glance' : 'what these runs are, every run at a glance'],
                  ['system', 'System', 'every simulated object and its settings'],
                  ['experiments', 'Experiments', loop ? 'the AI’s steps, and one experiment in detail' : 'one run in detail'],
                  ['events', 'Events', 'a few milliseconds, event by event: how long each step takes and what causes what']];
    (data.pages || []).forEach(p => TABS.push([p.key, p.name, p.what]));  // further pages the host page draws itself (the standalone page: Runs, Control)
    const extra = (data.pages || []).find(p => p.key === location.hash.slice(1));
    const tab = TABS.some(t => t[0] === location.hash.slice(1)) ? location.hash.slice(1) : 'overview';
    let no = 0;
    const rate = TASK_VIEW._rate;

    // every page has the same frame, in the same place: the title line, then the three page tabs
    let h = `<div class="th"><header class="th-top slim"><div class="th-kicker">${e(P.kicker)}</div>
      <div class="th-titleline"><h1>${e(P.title)}<small>run “${e(data.run)}”</small></h1>
        ${O ? `<span class="th-state${O.running ? ' live' : ''}"><i></i>${O.running ? 'Running now' : O.done ? 'Finished: the AI declared an answer' : 'Stopped before the AI declared an answer'}</span>` : ''}</div></header>
      <nav class="th-tabs${TABS.length > 4 ? ' many' : ''}" aria-label="Pages" style="--th-tabs:${TABS.length}">${TABS.map(([k, name, what], i) => `<a href="#${k}" class="${k === tab ? 'on' : ''}"${k === tab ? ' aria-current="page"' : ''}><b><span>${i + 1}</span>${name}</b><small>${what}</small></a>`).join('')}</nav>`;

    const rows = ps.map(p => { const hh = hyp[p.iteration], r = p.row || {};
      return `<tr class="pick${p.iteration === ui.sel ? ' on' : ''}" data-exp="${p.iteration}"><td><b>#${p.iteration}</b></td>` +
        (loop ? `<td>${hh ? e(hh.id) : ''}</td><td>${hh && hh.changed.length ? hh.changed.map(c => `${e(c[0])} ${e(rate(c[1]))} → <b>${e(rate(c[2]))}</b>`).join('<br>') : '<span class="th-muted">all defaults</span>'}</td>`
              : `<td>${e(r.Run || '')}</td><td>${e(r.Mode || '')}</td><td>${e(rate(r['UDP offered'] || '–'))}</td>`) +
        `<td class="num">${m(p).weight_udp ?? '–'}</td><td class="num">${mb(m(p).udp_goodput_bps)}</td><td class="num">${mb(m(p).tcp_goodput_bps)}</td><td class="num">${pc(m(p).udp_loss_frac)}</td><td class="num">${pc(m(p).link_util)}</td>` +
        (loop ? `<td>${rule(hh)}</td><td>${verdict(hh)}</td>` : '') + '</tr>'; }).join('');
    const table = `<table><thead><tr><th>#</th>${loop ? '<th>Hypothesis</th><th>What the AI changed</th>' : '<th>Run</th><th>Scheduling policy</th><th>UDP offered</th>'}<th class="num">UDP share</th><th class="num">UDP, Mbps</th><th class="num">TCP, Mbps</th><th class="num">UDP loss</th><th class="num">Link use</th>${loop ? '<th>Decision rule (checked here)</th><th>AI’s verdict</th>' : ''}</tr></thead><tbody>${rows}</tbody></table>`;

    if (tab === 'overview') {
      // 1. what this is: the question and the session's key facts
      h += sec(++no, loop ? 'The question' : 'What these runs are', loop ? 'What the AI was asked, and the session in six facts.' : 'Why these simulations were run.',
        `<p class="th-q">${e(P.question)}</p><dl class="th-facts">${(P.facts || []).map(([k, v, note]) => `<div class="th-fact"><dt>${e(k)}</dt><dd>${e(v)}${note ? `<small>${e(note)}</small>` : ''}</dd></div>`).join('')}</dl>`);
      // 2. the system in one picture
      h += sec(++no, 'The system at a glance', 'One sender, one receiver, one link. UDP and TCP both want the whole link; a scheduler in the sender decides how it is split.' + (loop ? ' The AI cannot see inside: it only chooses settings and reads measurements.' : ''),
        TASK_VIEW._topology(P.system) + `<a class="th-go" href="#system">Every object and its settings → System</a>`);
      // 2. where it stands
      if (O) h += sec(++no, 'Where it stands', 'The session in four numbers, then the AI’s most recent claim.', `<div class="th-tiles">
          <div class="th-tile"><h3>Experiments</h3><div class="big">${O.experiments}</div><p>simulations the AI chose and the harness ran</p></div>
          <div class="th-tile"><h3>Hypotheses, by the AI’s own verdict</h3><div class="big">${O.supported}<small> supported</small></div><p>${O.refuted} refuted · ${O.inconclusive} inconclusive · <b>${O.unjudged} not judged</b>${O.unjudged ? ' (the session ended first)' : ''}</p></div>
          <div class="th-tile"><h3>Decision rules, checked by this page</h3><div class="big">${O.rules_met}<small> of ${O.rules_total} met</small></div><p>each decision rule was stated by the AI before its simulations; the check uses the recorded numbers, not the AI’s word</p></div>
          <div class="th-tile"><h3>Turns</h3><div class="big">${O.turns}</div><p>${O.experiments} experiments · ${O.supported + O.refuted + O.inconclusive} verdicts · ${O.info} information request${O.info === 1 ? '' : 's'} · <b>${O.wasted} without a usable answer</b></p></div></div>
        ${O.latest ? `<div class="th-note"><b class="lbl">The AI’s latest hypothesis (${e(O.latest.id)})</b>${e(String(O.latest.text).replace(/^\s*H\d+\s*:\s*/, ''))}</div>` : ''}`);
      // 3. what was measured
      h += sec(++no, 'What each experiment measured', 'Every experiment at a glance. Each one is a blue dot (UDP) and an orange dot (TCP) placed at the UDP share it used. Click a dot or a row to choose an experiment; its summary appears beside the chart.',
        `<div class="th-wide"><div>
            <div class="th-key"><span><i style="background:${css('--series-1')}"></i>UDP goodput</span><span><i style="background:${css('--series-2')}"></i>TCP goodput</span>
              <span style="${ui.zoom ? 'visibility:hidden' : ''}"><svg width="26" height="8"><line x1="0" y1="4" x2="26" y2="4" stroke="${css('--text-muted')}" stroke-width="1.5" stroke-dasharray="5 4"/></svg>the share each flow was set to get</span>
              ${zr ? `<span class="th-seg" style="margin-left:auto"><button data-zoom="0" class="${ui.zoom ? '' : 'on'}">Whole range</button><button data-zoom="1" class="${ui.zoom ? 'on' : ''}">Close-up ${zr[0]}–${zr[1]}</button></span>` : ''}</div>
            ${pts.length ? TASK_VIEW._map(pts, ui.sel, ui.zoom && zr ? zr : null) : '<p class="th-muted">No measurements yet.</p>'}</div>
          <div><h3>How to read it</h3><p class="th-sm">Left to right: more of the link is given to UDP. Bottom to top: more data delivered per second.
            Where the dots sit on the dashed lines, each flow received what the scheduler was told to give it.${zr ? ' Several experiments sit close together; the close-up separates them.' : ''}</p>
            ${sel ? `<h3 style="margin-top:18px">Chosen: experiment ${sel.iteration}${H ? ' · ' + e(H.id) : ''}</h3>
              ${H ? `<p class="th-sm th-clamp3" style="color:var(--text-primary)" title="${e(TASK_VIEW._first(H.text))}">${e(TASK_VIEW._first(H.text))}</p>` : ''}
              <p style="margin-top:8px"><span class="th-chip">UDP share <b>${m(sel).weight_udp ?? '–'}</b></span><span class="th-chip">UDP <b>${mb(m(sel).udp_goodput_bps)} Mbps</b></span><span class="th-chip">TCP <b>${mb(m(sel).tcp_goodput_bps)} Mbps</b></span></p>
              ${H && !H.baseline ? `<p class="th-sm" style="margin-top:4px">Decision rule: ${rule(H)} &nbsp; AI’s verdict: ${verdict(H)}</p>` : ''}
              <a class="th-go" href="#experiments" style="margin-top:10px">Open experiment ${sel.iteration} → Experiments</a>` : ''}</div></div>
         <div style="margin-top:18px">${table}</div>`);
    }

    if (tab === 'system') {
      const S = P.system, OB = S.objects;
      if (OB && !TASK_VIEW._find(OB, ui.obj)) {  // start on the object the question is about
        ui.obj = 'link'; OB.hosts.forEach(H => OB.layers.forEach(L => (H[L.key] || []).forEach((o, i) => { if (o.key) ui.obj = `${H.key}-${L.key}-${i}`; })));
      }
      const CF = OB ? TASK_VIEW._config(OB, { ...S, chosen: ui.obj }) : null;
      h += sec(++no, 'The simulated network', 'Two nodes joined by one link. Each node is a stack of layers, with the applications on top and the network device at the bottom. Every small box is one object of the simulation: click one, and its settings appear beside the picture.',
        OB ? `<div class="th-side"><div>${TASK_VIEW._schema(OB, S, ui.obj)}</div><aside class="th-det" id="th-det" aria-live="polite">${TASK_VIEW._detail(OB, S, ui.obj)}</aside></div>` : TASK_VIEW._topology(S));
      if (CF) h += sec(++no, 'All settings in one list', 'The same settings for every object at once, node by node and layer by layer, then the link. The object chosen above is shaded.', CF.hosts, 'th-config');
      if (CF && (OB.around || []).length) h += sec(++no, 'Around the network', 'Objects that are not in the path of a packet: randomness, time, and measurement.', CF.around);
      h += sec(++no, loop ? 'What the AI may change, and what is measured' : 'What is measured', loop ? 'The only settings the AI can touch, with their allowed range, and the numbers every experiment returns.' : 'The numbers every run returns.',
        `<div class="th-two">${(P.knobs || []).length ? `<div><h3>What the AI may change</h3><table><thead><tr><th>Setting</th><th>Allowed</th><th>Default</th></tr></thead><tbody>${
            P.knobs.map(k => `<tr><td><b>${e(k.name)}</b></td><td>${e(rate(k.range).replace(/Tcp/g, ''))}</td><td>${e(rate(k.default).replace(/^Tcp/, ''))}</td></tr>`).join('')}</tbody></table></div>` : ''}
          <div><h3>What every experiment measures</h3><table><tbody>${(P.measured || []).map(([k, v]) => `<tr><td style="white-space:nowrap"><b>${e(k)}</b></td><td class="th-sm">${e(v)}</td></tr>`).join('')}</tbody></table></div></div>`);
    }

    if (tab === 'events') {
      const base = data.traceBase || 'task/twohosts/trace/';
      TH_EVENTS.load(base, ui.trace || ((TH_EVENTS.index || [])[0] || {}).name, () => { if (TASK_VIEW._last && location.hash === '#events') { const y = window.scrollY; TASK_VIEW.page(...TASK_VIEW._last); window.scrollTo(0, y); } });
      h += TH_EVENTS.html(ui, sec, e);
      if (TH_EVENTS.index && TH_EVENTS.index.length && !TH_EVENTS.cache[ui.trace]) TH_EVENTS.load(base, ui.trace, () => { if (TASK_VIEW._last && location.hash === '#events') { const y = window.scrollY; TASK_VIEW.page(...TASK_VIEW._last); window.scrollTo(0, y); } });
    }

    if (tab === 'experiments') {
      // 1. the turns in order (AI session only)
      if (loop && (P.turns || []).length) h += sec(++no, 'The turns, in order', 'Each turn the AI reads the whole record and gives one answer. Click a turn that produced or judged an experiment to show it below.',
        `<div class="th-strip" style="margin-bottom:0">${P.turns.map(t => `<button class="th-turn k-${t.kind}${t.exp && t.exp === ui.sel ? ' on' : ''}" ${t.exp ? `data-exp="${t.exp}"` : 'disabled'} title="${e(t.label)}${t.calls > 1 ? ` · ${t.calls} tries` : ''}">
            <small>${t.turn === 0 ? 'Before turn 1' : 'Turn ' + t.turn}</small><b>${e({ experiment: 'Experiment ' + t.exp, verdict: 'Verdict on ' + ((hyp[t.exp] || {}).id || ''), wasted: 'No usable answer', info: 'Asked for information', baseline: 'Baseline run', done: 'Declared done' }[t.kind] || t.label)}</b></button>`).join('')}</div>`);
      // 2. the list on the left, the chosen experiment beside it
      const list = loop ? P.hyps.map(x => `<button class="th-item${x.n === ui.sel ? ' on' : ''}" data-exp="${x.n}"><span class="top"><b>${e(x.id)} · experiment ${x.n}</b>${verdict(x)}</span>
            <span class="txt">${e(TASK_VIEW._first(x.text))}</span><span class="chg">${x.changed.length ? x.changed.map(c => `${e(c[0])} ${e(rate(c[1]))} → ${e(rate(c[2]))}`).join(' · ') : 'all settings at their defaults'}</span>${x.total ? `<span class="chg">Decision rule: ${x.met === x.total ? '✓' : '✕'} ${x.met} of ${x.total} met</span>` : ''}</button>`).join('')
        : ps.map(p => `<button class="th-item${p.iteration === ui.sel ? ' on' : ''}" data-exp="${p.iteration}"><span class="top"><b>#${p.iteration} · ${e((p.row || {}).Run || '')}</b><span class="th-sm">${e((p.row || {}).Mode || '')}</span></span>
            <span class="chg">UDP share ${m(p).weight_udp ?? '–'} · offered ${e(rate((p.row || {})['UDP offered'] || '–'))}</span><span class="chg">UDP ${mb(m(p).udp_goodput_bps)} · TCP ${mb(m(p).tcp_goodput_bps)} Mbps</span></button>`).join('');
      let det = '<p class="th-muted">No experiment yet.</p>';
      if (sel) {
        // The experiment as the chain it is: claim -> prediction -> experiment -> result -> check -> verdict -> next step.
        // Each step says who did it and when; the line on the left carries the eye from one step to the next.
        const steps = []; let k = 0;
        const step = (title, who, ask, body, done = true) => steps.push(`<li class="th-step${done ? ' done' : ''}"><span class="n">${++k}</span><div><div class="hd"><b>${title}</b><span>${who}</span></div><p class="ask">${ask}</p><div class="body">${body}</div></div></li>`);
        const phase = (name, note) => steps.push(`<li class="th-phase">${name}<span>${note}</span></li>`);
        const text = String((H && H.text) || '').replace(/^\s*H\d+\s*:\s*/, ''), lead = TASK_VIEW._first(text), rest = text.slice(lead.length).trim();
        const crit = (H && H.criteria) || [], checked = crit.filter(c => c.ok != null), allMet = checked.length && checked.every(c => c.ok);
        const runId = e((sel.solution || {}).run_id || (sel.row || {}).Run || '');
        if (H && !H.baseline) {
          phase('Before the run', 'written by the AI');
          step('Hypothesis', `the AI’s claim · turn ${H.turn}`, 'What does the AI believe about the system?', `<p class="lead">${e(lead)}</p>${rest ? `<p class="rest">${e(rest)}</p>` : ''}`);
          step('Prediction', 'the AI · fixed before the run', 'If the claim is right, what must the experiment show?',
            (crit.length ? `<table><thead><tr><th>Measure</th><th>Must be</th></tr></thead><tbody>${crit.map(c => `<tr><td>${e(c.what)}</td><td><b>${e(c.need)}</b></td></tr>`).join('')}</tbody></table>` : '<p class="th-muted">No decision rule was recorded.</p>') +
            (H.prediction ? `<details><summary>The prediction in the AI’s own words</summary><p class="th-sm" style="margin-top:6px">${e(H.prediction)}</p></details>` : ''));
        }
        phase('The run', 'done by the harness');
        const changed = H ? H.changed : [], kept = H ? H.settings.filter(([name]) => !changed.some(c => c[0] === name)) : [];
        step('Experiment', `simulation run ${runId}`, H && !H.baseline ? 'Which settings did the AI choose to test it?' : 'Which settings were used?',
          H ? `${changed.length ? `<p style="margin-bottom:6px"><span class="th-sm">Changed from experiment ${sel.iteration - 1 || 'the defaults'}${sel.iteration > 1 ? '' : ''}:</span><br>${changed.map(c => `<span class="th-chip">${e(c[0])} <span class="th-muted">${e(rate(c[1]).replace(/^Tcp/, ''))} →</span> <b>${e(rate(c[2]).replace(/^Tcp/, ''))}</b></span>`).join('')}</p>` : '<p class="th-sm" style="margin-bottom:6px">Every setting at its default.</p>'}
              <p><span class="th-sm">${changed.length ? 'Kept as before:' : 'Settings:'}</span><br>${kept.map(([name, v]) => `<span class="th-chip" style="background:none">${e(name)} <b style="font-weight:600">${e(rate(v).replace(/^Tcp/, ''))}</b></span>`).join('')}</p>`
            : `<dl class="th-dl">${(sel.facts || []).map(([name, v]) => `<dt>${e(name)}</dt><dd>${e(v)}</dd>`).join('')}</dl>`);
        const num = (label, value, unit) => `<div><small>${label}</small><b>${value}<i>${unit}</i></b></div>`;
        step('Result', 'measured by the simulation', 'What actually happened?',
          `<div class="th-nums">${num('UDP goodput', mb(m(sel).udp_goodput_bps), 'Mbps')}${num('TCP goodput', mb(m(sel).tcp_goodput_bps), 'Mbps')}${num('UDP loss', typeof m(sel).udp_loss_frac === 'number' ? (100 * m(sel).udp_loss_frac).toFixed(1) : '–', '%')}${num('Link use', typeof m(sel).link_util === 'number' ? (100 * m(sel).link_util).toFixed(1) : '–', '%')}${
              typeof m(sel).tcp_retrans === 'number' ? num('TCP retransmissions', m(sel).tcp_retrans.toLocaleString(), '') : ''}</div>
           ${TASK_VIEW.drawable(sel.solution) ? `<details><summary>The run over time (throughput, TCP window, drops)</summary><div style="max-width:560px;margin-top:8px">${TASK_VIEW.draw(sel.solution, { valid: true, size: '100%', labels: true, aria: 'Experiment ' + sel.iteration + ' over time', simple: false })}</div></details>` : ''}`);
        if (H && !H.baseline) {
          phase('After the run', 'the judgement');
          step('Check', 'done by this page, from the recorded numbers', 'Did each prediction hold?',
            crit.length ? `<div class="th-sum"><span class="mark ${allMet ? 'ok' : 'bad'}">${allMet ? '✓' : '✕'}</span>${allMet ? `All ${checked.length} predictions held` : `${checked.filter(c => c.ok).length} of ${checked.length} predictions held`}${crit.length > checked.length ? ` <span class="th-sm">(${crit.length - checked.length} could not be checked)</span>` : ''}</div>
              <table><thead><tr><th>Measure</th><th>Must be</th><th class="num">Measured</th><th>Range and measured value</th><th></th></tr></thead><tbody>${
              crit.map(c => `<tr><td>${e(c.what)}</td><td>${e(c.need)}</td><td class="num"><b>${e(c.measured)}</b></td><td>${TASK_VIEW._range(c)}</td><td style="white-space:nowrap">${c.ok == null ? '<span class="th-muted">not checked</span>' : c.ok ? '<span class="th-ok">✓ held</span>' : '<span class="th-bad">✕ failed</span>'}</td></tr>`).join('')}</tbody></table>`
              : '<p class="th-muted">No decision rule to check.</p>');
          const vr = H.verdict && H.verdict.result, clash = vr && checked.length && ((vr === 'supported' && !allMet) || (vr === 'refuted' && allMet));
          step('Verdict', H.verdict ? `the AI’s own judgement · turn ${H.verdict.turn}` : 'the AI’s own judgement', 'What did the AI conclude about its hypothesis?',
            H.verdict ? `<p>${verdict(H)}</p><p style="margin-top:8px;font-size:14px">${e(H.verdict.because || '')}</p>${clash ? `<p class="th-warn">This verdict does not match the check above (${allMet ? 'all predictions held' : 'not all predictions held'}).</p>` : ''}`
              : `<p>${verdict(H)} <span class="th-sm">The session ended before the AI judged this hypothesis.${checked.length ? ` By the check above, ${allMet ? 'the prediction held' : 'the prediction did not hold'}.` : ''}</span></p>`, !!H.verdict);
          const nextH = hyp[sel.iteration + 1];
          step('Next step', H.verdict && H.verdict.next ? 'the AI’s plan' : '', 'What did the AI decide to do next?',
            (H.verdict && H.verdict.next ? `<p style="font-size:14px">${e(H.verdict.next)}</p>` : '<p class="th-sm">No plan was recorded for this hypothesis.</p>') +
            (nextH ? `<button class="th-go" data-exp="${nextH.n}" style="background:none;cursor:pointer;font:inherit;font-size:14px;font-weight:600">Continue to ${e(nextH.id)} · experiment ${nextH.n} →</button>` : ''), !!(H.verdict && H.verdict.next));
        }
        const thinking = sel.reasoning ? `<details style="margin-left:48px"><summary>Appendix: what the AI thought before proposing this experiment (${sel.reasoning.length.toLocaleString()} characters, its own words)</summary><pre>${e(sel.reasoning)}</pre></details>` : '';
        det = `<h3 class="exp">Experiment ${sel.iteration}${H ? ' · ' + e(H.id) : ''}</h3><p class="expsub">${H && !H.baseline ? 'One hypothesis, tested once. Read it from top to bottom.' : 'A run without a hypothesis.'}</p>
          <ol class="th-chain">${steps.join('').replace(/class="th-step( done)?"(?![\s\S]*class="th-step)/, m => m.replace('th-step', 'th-step end'))}</ol>${thinking}`;
      }
      h += sec(++no, loop ? 'Hypotheses and their experiments' : 'The runs, one by one', loop ? 'Choose a hypothesis on the left; its experiment is shown beside it.' : 'Choose a run on the left; it is shown beside it.',
        `<div class="th-md"><div class="th-mdlist">${list}</div><div class="th-mddet" id="th-detail">${det}</div></div>`);
    }
    if (extra) h += '<div id="th-extra"></div>';
    root.innerHTML = h + '</div>';
    if (tab === 'events') TH_EVENTS.bind(root, ui);
    if (extra) extra.mount(root.querySelector('#th-extra'), raw);

    // Moving between the three pages: the address after # says which one. Choosing something never moves the page.
    // Only when the reader opens another page from far down does the new page start at its top, as any new page does.
    if (!TASK_VIEW._hashWired) { TASK_VIEW._hashWired = true;
      window.addEventListener('hashchange', () => { if (!TASK_VIEW._last) return; const r = TASK_VIEW._last[0];
        TASK_VIEW.page(...TASK_VIEW._last);
        if (r.getBoundingClientRect().top < 0) window.scrollTo(0, window.scrollY + r.getBoundingClientRect().top); }); }
    // interactions: choose an experiment (dot, row, turn, list), zoom, hover values
    const pick = n => { ui.sel = +n; const y = window.scrollY; TASK_VIEW.page(root, data); if (window.scrollY !== y) window.scrollTo(0, y); };
    root.querySelectorAll('[data-exp]').forEach(el => el.addEventListener('click', () => pick(el.dataset.exp)));
    root.querySelectorAll('[data-obj]').forEach(el => el.addEventListener('click', () => {  // choose an object: its settings appear beside the schema
      const id = ui.obj = el.dataset.obj, OB = P.system.objects, det = root.querySelector('#th-det');
      root.querySelectorAll('[data-obj]').forEach(x => x.classList.toggle('on', x.dataset.obj === id));
      if (det) { det.innerHTML = TASK_VIEW._detail(OB, P.system, id); const f = TASK_VIEW._find(OB, id);
        det.style.setProperty('--dc', f && f.o.flow === 'udp' ? css('--series-1') : f && f.o.flow === 'tcp' ? css('--series-2') : css('--text-muted')); }
      root.querySelectorAll('[data-cfg]').forEach(r => r.classList.toggle('sel', r.dataset.cfg === id));
    }));
    { const det = root.querySelector('#th-det'), f = det && TASK_VIEW._find(P.system.objects, ui.obj);  // the panel's colour bar for the object shown at load
      if (det) det.style.setProperty('--dc', f && f.o.flow === 'udp' ? css('--series-1') : f && f.o.flow === 'tcp' ? css('--series-2') : css('--text-muted')); }
    root.querySelectorAll('[data-zoom]').forEach(el => el.addEventListener('click', () => { ui.zoom = el.dataset.zoom === '1'; TASK_VIEW.page(root, data); }));
    let tip = document.getElementById('th-tip'); if (!tip) { tip = document.createElement('div'); tip.id = 'th-tip'; tip.className = 'th-tip'; tip.hidden = true; document.querySelector('.viz-root').appendChild(tip); }
    root.querySelectorAll('.th-hit').forEach(el => {
      el.addEventListener('mousemove', ev => { const p = pts.find(q => q.n === +el.dataset.exp), hh = hyp[p.n];
        tip.innerHTML = `<b>Experiment ${p.n}${hh ? ' · ' + e(hh.id) : ''}</b>UDP share ${p.w}<br><i style="background:${css('--series-1')}"></i>UDP ${p.udp.toFixed(1)} Mbps<br><i style="background:${css('--series-2')}"></i>TCP ${p.tcp.toFixed(1)} Mbps`;
        tip.hidden = false; tip.style.left = Math.min(window.innerWidth - 220, ev.clientX + 14) + 'px'; tip.style.top = (ev.clientY + 14) + 'px'; });
      el.addEventListener('mouseleave', () => { tip.hidden = true; });
    });
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

  // series.csv text -> columns; drops become per-sample counts
  csv(text) {
    const lines = String(text || '').trim().split('\n'); if (lines.length < 3) return null;
    const head = lines[0].split(','), col = n => head.indexOf(n), rows = lines.slice(1).map(l => l.split(',').map(Number));
    const get = n => (col(n) < 0 ? null : rows.map(r => r[col(n)]));
    const diff = a => a.map((v, i) => (i ? v - a[i - 1] : v));
    return { t: get('t'), udp: get('udp_bps'), tcp: get('tcp_bps'), cwnd: get('cwnd'), d0: diff(get('drops_band0')), d1: diff(get('drops_band1')),
             q0: get('q_band0'), q1: get('q_band1') };  // packets waiting in each queue; null for runs made before they were recorded
  },

  // ---- a decision rule's arithmetic and nothing else: numbers, metric names, + - * /, parentheses, abs/min/max
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
  // The decision rule as rows a person can read: what, the allowed range, the measured value, met or not.
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
    const D = TH_DATA, led = raw.ledger || [], man = raw.manifest || {}, fixed = man.fixed || {};
    const index = Object.fromEntries((raw.index || []).map(r => [r.id, r])), oper = Object.fromEntries((raw.oper || []).map(r => [r.id, r]));
    const defaults = Object.fromEntries(Object.entries(man.params || {}).map(([k, v]) => [k, v.default]));
    const used = new Set(led.filter(r => r.type === 'evidence').map(r => (r.body || {}).run_id));
    const lastRun = [...led].reverse().find(r => r.type === 'evidence');
    const system = { link_rate: fixed.linkRate || '1Gbps', link_delay: fixed.linkDelay || '50us', mtu: fixed.mtu || 1500, defaults, objects: raw.objects || null,
      mode: run === 'operator_checks' ? 'share or cap, per run' : (lastRun && (oper[(lastRun.body || {}).run_id] || {}).mode) || 'share' };
    const measured = Object.entries(man.outputs || {}).filter(([k]) => !['link_rate_bps', 'weight_udp'].includes(k)).map(([k, v]) => [D.PLAIN[k] || k, v]);
    const num = o => Object.fromEntries(Object.entries(o || {}).filter(([, v]) => typeof v === 'number'));
    const program = (n, rid, metrics, extra) => ({ iteration: n, metrics: metrics || {}, reasoning: null, facts: [],
      solution: metrics && metrics.udp_goodput_bps != null ? { run_id: rid, params: (index[rid] || {}).params || {}, metrics, series: (raw.series || {})[rid] || null } : null,
      row: { Run: rid, Mode: (oper[rid] || {}).mode || '–', 'UDP offered': ((index[rid] || {}).params || {}).udpRate || '–' }, ...extra });

    if (run === 'operator_checks') {
      const ids = (raw.index || []).map(r => r.id).filter(id => !used.has(id));
      const modes = [...new Set(ids.map(id => (oper[id] || {}).mode || '?'))].sort();
      const programs = ids.map((rid, i) => { const op = oper[rid] || {}, pr = index[rid].params || {};
        return program(i + 1, rid, index[rid].metrics, { facts: [
          ['What this is', `An operator ${op.control ? 'run started from the Control page' : 'check (' + (op.stage != null ? 'build stage ' + op.stage : 'harness test') + ')'}, not an AI experiment.`], ['Scheduling policy', op.mode || '–'],
          ['Settings', Object.entries(pr).filter(([k]) => D.KNOB[k]).map(([k, v]) => `${D.KNOB[k]} ${D.knob(k, v)}`).join(', ') || 'all defaults']] }); });
      return { programs, page: { kind: 'checks', title: 'Two hosts, one link', kicker: 'Operator checks of the network simulation (ns-3), no AI',
        question: 'Simulations the operator ran while building the harness, to confirm the simulator behaves as designed before any AI used it.',
        facts: [['AI model', 'none', 'the operator chose every setting'], ['Runs', String(ids.length), 'each one ns-3 simulation'], ['Scheduling policies tried', modes.join(', '), 'the two ways the scheduler can split the link']],
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
      const crit = eb.note ? [] : D.criteria(xb.pass_if || eb.pass_if, num(eb)), checked = crit.filter(c => c.ok != null);
      hyps.push({ n, id: h.id || ev.id, turn: ev.turn, baseline: !!eb.note, text: hb.text || eb.note || '(no hypothesis was stated for this experiment)', prediction: hb.prediction,
        run_id: rid, changed, settings: Object.entries(params).map(([key, val]) => [D.KNOB[key] || key, D.knob(key, val)]),
        criteria: crit, met: checked.filter(c => c.ok).length, total: checked.length,
        verdict: v ? { id: v.id, turn: v.turn, result: vb.result, because: vb.because, next: vb.next } : null, error: eb.error });
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
    const page = { kind: 'loop', title: 'Two hosts, one link', kicker: 'AI hypothesis loop over a network simulation (ns-3)', question: man.task || '',
      facts: [
        ['AI model', String((scratch.length && (scratch[scratch.length - 1].body || {}).model) || '?').split('/').pop(), 'local model on vLLM'],
        ['Thinking', scratch.length ? 'on' : 'off', scratch.length ? 'its reasoning is kept in the record' : 'no reasoning recorded'],
        ['Session', led.length ? String(led[0].ts || '').replace('T', ' ').slice(0, 16) : '–', mins != null ? mins + ' minutes' : ''],
        ['Experiments', String(real.length), 'chosen by the AI' + (hyps.length > real.length ? ', plus 1 baseline run by the harness' : '')],
        ['Turns', String(turns.filter(t => t.turn > 0).length), count('wasted') + ' without a usable answer'],
        ['Scheduling policy', hyps.length ? (oper[hyps[hyps.length - 1].run_id] || {}).mode || '?' : '?', 'set by the operator, hidden from the AI']],
      system, measured,
      knobs: Object.entries(man.params || {}).map(([k, v]) => ({ name: D.KNOB[k] || k, range: v.choices ? v.choices.join(' / ') : `${v.min} to ${D.knob(k, v.max)}`, default: D.knob(k, v.default) })),
      outcome: { experiments: real.length, supported: res('supported'), refuted: res('refuted'), inconclusive: res('inconclusive'), unjudged: real.filter(h => !h.verdict).length,
        rules_met: hyps.filter(h => h.total && h.met === h.total).length, rules_total: hyps.filter(h => h.total).length,
        turns: turns.filter(t => t.turn > 0).length, wasted: count('wasted'), info: count('info'), done: count('done') > 0, running: !!raw.running,
        latest: latest ? { id: latest.id, text: latest.text } : null },
      turns, hyps };
    return { page, programs };
  },
};

// ======================================================================================================
// TH_EVENTS: the fourth page. A few milliseconds of one simulation, event by event: what happened to each
// packet, how long every step took, and what caused what. Data: <base>index.json and <base><name>/events.csv,
// recorded by harness/make_trace.py (two-hosts --events=MS). Columns: t_ns, ev (the simulator event it happened
// in), kind, obj, flow, key (one packet through its whole life), size, info.
// ======================================================================================================
const TH_EVENTS = {
  cache: {}, index: null, loading: {},
  RANK: { create: 0, tcp_send: 0, ack_send: 0, retransmit: 0, enqueue: 1, drop: 1, dequeue: 2, tx_begin: 3, tx_end: 4, rx: 5, deliver: 6, tcp_rx: 6, ack_rx: 6 },
  us(ns) { const u = ns / 1000; return Math.abs(u) >= 1000 ? (u / 1000).toFixed(Math.abs(u) >= 10000 ? 2 : 3) + ' ms' : (Math.abs(u) >= 100 ? u.toFixed(0) : u.toFixed(1)) + ' µs'; },
  kindName(p) { return p.flow === 'udp' ? 'UDP packet' : p.flow === 'tcp' ? 'TCP segment' : 'TCP acknowledgement'; },

  load(base, name, done) {  // fetch once, then call done() so the page can draw
    const E = TH_EVENTS, get = u => fetch(u + '?t=' + Date.now()).then(r => (r.ok ? r.text() : null)).catch(() => null);
    if (!E.index && !E.loading.index) { E.loading.index = true;
      get(base + 'index.json').then(t => { try { E.index = JSON.parse(t) || []; } catch (e) { E.index = []; } done(); }); }
    if (name && !E.cache[name] && !E.loading[name]) { E.loading[name] = true;
      get(base + name + '/events.csv').then(t => { E.cache[name] = E.parse(t || ''); done(); }); }
  },

  parse(text) {
    const lines = text.trim().split('\n').slice(1), ev = [], pk = {};
    if (!lines.length) return { ev, pk, t0: 0, span: 0, bad: true };
    const t0 = +lines[0].split(',')[0];
    lines.forEach((l, i) => { const c = l.split(','), r = { i, t: +c[0] - t0, ev: +c[1], kind: c[2], obj: c[3], flow: c[4], key: c[5], size: +c[6], info: +c[7] };
      ev.push(r); if (r.kind !== 'cwnd') (pk[r.key] = pk[r.key] || { key: r.key, flow: r.flow, e: [] }).e.push(r); });
    Object.values(pk).forEach(p => { p.e.sort((a, b) => a.t - b.t || TH_EVENTS.RANK[a.kind] - TH_EVENTS.RANK[b.kind]);
      const k = new Set(p.e.map(x => x.kind)); p.dropped = k.has('drop'); p.born = k.has('create') || k.has('tcp_send') || k.has('ack_send');
      p.done = k.has('deliver') || k.has('tcp_rx') || k.has('ack_rx') || p.dropped; p.whole = p.born && p.done; });
    const byEv = {}; ev.forEach(r => (byEv[r.ev] = byEv[r.ev] || []).push(r));
    const atT = {}; ev.forEach(r => { if (r.kind === 'tx_end' && r.obj === 'dev0') atT[r.t] = r; });
    return { ev, pk, byEv, txEndAt: atT, t0, span: ev[ev.length - 1].t };
  },

  // how long each step takes, over every packet whose both ends were recorded
  stats(T) {
    const med = a => { a = a.slice().sort((x, y) => x - y); return a.length ? a[Math.floor(a.length / 2)] : null; };
    const gap = (flow, from, to) => { const a = []; Object.values(T.pk).forEach(p => { if (p.flow !== flow) return;
      const x = p.e.find(r => from.includes(r.kind)), y = p.e.find(r => to.includes(r.kind) && (!x || r.t >= x.t)); if (x && y) a.push(y.t - x.t); });
      return a.length ? { n: a.length, med: med(a), min: Math.min(...a), max: Math.max(...a) } : null; };
    const flows = { udp: ['create'], tcp: ['tcp_send'] }, out = [];
    [['udp', 'UDP'], ['tcp', 'TCP']].forEach(([f, F]) => {
      const all = Object.values(T.pk).filter(p => p.flow === f && p.born), dropped = all.filter(p => p.dropped).length;
      out.push({ head: `${F} packet`, note: `${all.length} created in this recording, ${dropped} dropped on arrival at a full queue` });
      out.push({ step: 'Created → placed in its queue', why: 'handed down the stack inside the same simulator event', g: gap(f, flows[f], ['enqueue']) });
      out.push({ step: `Waiting in the ${F} queue`, why: 'until the scheduler gives this queue a turn', g: gap(f, ['enqueue'], ['dequeue']) });
      out.push({ step: 'Waiting in the device’s own queue', why: 'behind the packets the scheduler released before it', g: gap(f, ['dequeue'], ['tx_begin']) });
      out.push({ step: 'Being transmitted', why: 'its bytes × 8 ÷ the link rate', g: gap(f, ['tx_begin'], ['tx_end']) });
      out.push({ step: 'Travelling on the link', why: 'the link’s delay', g: gap(f, ['tx_end'], ['rx']) });
      out.push({ step: 'Whole life, created → delivered', why: 'the sum of the steps above', g: gap(f, flows[f], ['deliver', 'tcp_rx']), sum: true });
    });
    out.push({ head: 'TCP acknowledgement', note: 'sent by the receiver for every second segment' });
    out.push({ step: 'Sent by the receiver → back at the sender', why: 'transmission of 54 bytes + the link’s delay', g: gap('ack', ['ack_send'], ['ack_rx']) });
    return out;
  },

  // why a step happened, and what it set off, in plain words
  why(T, p, i) {
    const r = p.e[i], prev = p.e[i - 1], same = (T.byEv[r.ev] || []).filter(x => x !== r), E = TH_EVENTS;
    const link = k => `<button class="th-pk" data-pk="${k}">${k[0] === 'u' ? 'UDP packet' : k[0] === 't' ? 'TCP segment' : 'ACK'} ${k.slice(1)}</button>`;
    let what = r.kind, cause = '', effect = '';
    if (r.kind === 'create') { what = 'Created by the UDP source'; const a = T.ev.filter(x => x.kind === 'create' && x.t < r.t).pop();
      cause = a ? `the source’s own timer: one packet every ${E.us(r.t - a.t)}` : 'the source’s own timer'; }
    if (r.kind === 'tcp_send') { what = 'Sent by TCP'; const a = same.find(x => x.kind === 'ack_rx');
      cause = a ? `an acknowledgement arrived (${link(a.key)}), so TCP may send more` : 'TCP’s window had room for another segment'; }
    if (r.kind === 'retransmit') { what = 'Sent again by TCP'; cause = 'TCP concluded the first copy was lost'; }
    if (r.kind === 'ack_send') { what = 'Created by the receiver’s TCP'; const a = same.find(x => x.kind === 'tcp_rx');
      cause = a ? `${link(a.key)} arrived; the receiver acknowledges every second segment` : 'data arrived at the receiver'; }
    if (r.kind === 'enqueue') { what = `Placed in the ${r.obj === 'queue0' ? 'UDP' : 'TCP'} queue`; cause = `handed down the stack at once; ${r.info} packets now wait there`; }
    if (r.kind === 'drop') { what = `Dropped at the ${r.obj === 'queue0' ? 'UDP' : 'TCP'} queue`; cause = `the queue was full (${r.info} packets waiting), so the new packet is discarded`; }
    if (r.kind === 'dequeue') { what = 'Taken out by the scheduler'; const a = T.txEndAt[r.t];
      cause = a && a.key !== r.key ? `the device finished sending ${link(a.key)} and had room; it was this queue’s turn` : 'the device had room; it was this queue’s turn'; }
    if (r.kind === 'tx_begin') { what = r.obj === 'dev0' ? 'Transmission began' : 'Transmission began (receiver’s device)'; const a = same.find(x => x.kind === 'tx_end' && x.key !== r.key);
      cause = a ? `the device finished ${link(a.key)} at this very instant` : 'the device was free'; }
    if (r.kind === 'tx_end') { what = 'Transmission ended'; cause = `${r.size} bytes at the link rate`; const b = same.find(x => x.kind === 'tx_begin' && x.key !== r.key);
      effect = b ? `the device starts sending ${link(b.key)}` : ''; }
    if (r.kind === 'rx') { what = `Arrived at the ${r.obj === 'dev1' ? 'receiver' : 'sender'}’s device`; cause = 'the link’s delay has passed'; }
    if (r.kind === 'deliver') { what = 'Delivered to the UDP sink'; cause = 'passed up the receiver’s stack at once'; }
    if (r.kind === 'tcp_rx') { what = 'Received by the receiver’s TCP'; cause = 'passed up the receiver’s stack at once'; const b = same.find(x => x.kind === 'ack_send');
      effect = b ? `the receiver sends ${link(b.key)}` : 'no acknowledgement yet: the receiver waits for a second segment'; }
    if (r.kind === 'ack_rx') { what = 'Received by the sender’s TCP'; cause = 'passed up the sender’s stack at once'; const b = same.filter(x => x.kind === 'tcp_send');
      effect = b.length ? `TCP sends ${b.length} new segment${b.length > 1 ? 's' : ''}: ${b.slice(0, 3).map(x => link(x.key)).join(', ')}` : ''; }
    return { what, cause, effect, took: prev ? r.t - prev.t : null };
  },

  // the picture: lanes from the sender's applications (top) to the receiver (bottom), time from left to right
  draw(T, t0, tw, sel) {
    const W = 860, L = 132, R = 12, X = t => L + (W - L - R) * (t - t0) / tw, vis = r => r.t >= t0 - 60000 && r.t <= t0 + tw + 60000;
    const ink = css('--text-primary'), sec = css('--text-secondary'), mut = css('--text-muted'), grid = css('--grid'), s0 = css('--surface-0'), s1 = css('--surface-1'),
      C = { udp: css('--series-1'), tcp: css('--series-2'), ack: mut }, bad = css('--critical');
    const qmax = q => Math.max(1, ...T.ev.filter(r => r.obj === q).map(r => r.info));
    const lanes = [['udp0', 'UDP source', 'creates packets', 30], ['tcp0', 'TCP sender', 'sends · gets ACKs', 30], ['queue0', 'UDP queue', `0 to ${qmax('queue0')} waiting`, 58], ['queue1', 'TCP queue', `0 to ${qmax('queue1')} waiting`, 58],
      ['dev0', 'Sender’s device', 'one packet at a time', 34], ['link', 'Link', 'in flight', 70], ['recv', 'Receiver', 'arrivals · ACKs', 34]];
    let y = 8; const Y = {}; lanes.forEach(l => { Y[l[0]] = [y, l[3]]; y += l[3] + 6; });
    const H = y + 24, ev = T.ev.filter(vis);
    let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block;max-width:100%;font-family:inherit" role="img" aria-label="Events of the recording between ${TH_EVENTS.us(t0)} and ${TH_EVENTS.us(t0 + tw)}"><defs><clipPath id="th-evclip"><rect x="${L}" y="0" width="${W - L - R}" height="${H}"/></clipPath></defs>`;
    lanes.forEach(([k, name, sub]) => { const [ly, lh] = Y[k];
      s += `<rect x="${L}" y="${ly}" width="${W - L - R}" height="${lh}" fill="${s0}"/><text x="${L - 10}" y="${ly + lh / 2 - 1}" font-size="13" font-weight="700" text-anchor="end" fill="${ink}">${name}</text><text x="${L - 10}" y="${ly + lh / 2 + 13}" font-size="11" text-anchor="end" fill="${mut}">${sub}</text>`; });
    // time axis
    const step = [5, 10, 20, 50, 100, 200, 500, 1000, 2000].map(u => u * 1000).find(k => tw / k <= 10);
    for (let t = Math.ceil(t0 / step) * step; t <= t0 + tw; t += step) s += `<line x1="${X(t)}" y1="8" x2="${X(t)}" y2="${H - 22}" stroke="${grid}"/><text x="${X(t)}" y="${H - 8}" font-size="11" text-anchor="middle" fill="${mut}">${TH_EVENTS.us(t)}</text>`;
    s += `<g clip-path="url(#th-evclip)">`;
    // queues: how many packets wait (step line), drops as crosses along the top
    ['queue0', 'queue1'].forEach((q, b) => { const [ly, lh] = Y[q], pts = T.ev.filter(r => r.obj === q && r.kind !== 'drop'), max = qmax(q);
      const yy = n => ly + lh - 10 - (lh - 28) * n / max; let d = '', last = null;
      pts.forEach(r => { if (r.t < t0 - 60000 || r.t > t0 + tw + 60000) { last = r; return; } if (!d) d = `M${X(last ? last.t : r.t)} ${yy(last ? last.info : r.info)}`; d += ` H${X(r.t)} V${yy(r.info)}`; last = r; });
      if (d) s += `<path d="${d} H${X(t0 + tw)}" fill="none" stroke="${b ? C.tcp : C.udp}" stroke-width="1.6"/>`;
      ev.filter(r => r.obj === q && r.kind === 'drop').forEach(r => { const x = X(r.t), on = r.key === sel;
        s += `<path class="th-evh" data-pk="${r.key}" d="M${x - 3} ${ly + 3} l6 6 m0 -6 l-6 6" stroke="${on ? ink : bad}" stroke-width="${on ? 2.6 : 1.4}" style="cursor:pointer"/>`; }); });
    // sources and receiver: one tick per packet
    const tick = (r, lane, c, up) => { const [ly, lh] = Y[lane], on = r.key === sel, x = X(r.t);
      return `<line class="th-evh" data-pk="${r.key}" x1="${x}" y1="${ly + (up ? 3 : lh / 2)}" x2="${x}" y2="${ly + (up ? lh / 2 : lh - 3)}" stroke="${on ? ink : c}" stroke-width="${on ? 4 : 2}" style="cursor:pointer"/>`; };
    ev.forEach(r => {
      if (r.kind === 'create') s += tick(r, 'udp0', C.udp, true) + tick(r, 'udp0', C.udp, false);
      if (r.kind === 'tcp_send' || r.kind === 'retransmit') s += tick(r, 'tcp0', C.tcp, true);
      if (r.kind === 'ack_rx') s += tick(r, 'tcp0', C.ack, false);
      if (r.kind === 'deliver') s += tick(r, 'recv', C.udp, true);
      if (r.kind === 'tcp_rx') s += tick(r, 'recv', C.tcp, true);
      if (r.kind === 'ack_send') s += tick(r, 'recv', C.ack, false);
    });
    // device: one bar per transmission; link: a slanted line while the packet is in flight (ACKs slant back up)
    Object.values(T.pk).forEach(p => { const a = p.e.find(r => r.kind === 'tx_begin'), b = p.e.find(r => r.kind === 'tx_end'), c = p.e.find(r => r.kind === 'rx'), on = p.key === sel;
      if (!a || !b || a.t > t0 + tw + 60000 || (c || b).t < t0 - 60000) return;
      const [ly, lh] = Y.link;
      if (p.flow !== 'ack') { const [dy, dh] = Y.dev0;
        s += `<rect class="th-evh" data-pk="${p.key}" x="${X(a.t) + 0.5}" y="${dy + 3}" width="${Math.max(1.5, X(b.t) - X(a.t) - 1)}" height="${dh - 6}" rx="2" fill="${C[p.flow]}" stroke="${on ? ink : 'none'}" stroke-width="2.5" style="cursor:pointer"/>`;
        if (c) s += `<line class="th-evh" data-pk="${p.key}" x1="${X(b.t)}" y1="${ly}" x2="${X(c.t)}" y2="${ly + lh}" stroke="${on ? ink : C[p.flow]}" stroke-width="${on ? 3 : 1}" stroke-opacity="${on ? 1 : .55}" style="cursor:pointer"/>`;
      } else if (c) s += `<line class="th-evh" data-pk="${p.key}" x1="${X(b.t)}" y1="${ly + lh}" x2="${X(c.t)}" y2="${ly}" stroke="${on ? ink : C.ack}" stroke-width="${on ? 3 : 1}" stroke-dasharray="${on ? '' : '3 3'}" style="cursor:pointer"/>`; });
    // the chosen packet: its wait in the queue as a bar, and a marker at each of its events
    const P = T.pk[sel];
    if (P) { const q = P.e.find(r => r.kind === 'enqueue'), d = P.e.find(r => r.kind === 'dequeue');
      if (q) { const [ly, lh] = Y[q.obj]; s += `<rect x="${X(q.t)}" y="${ly + lh - 6}" width="${Math.max(2, X(d ? d.t : t0 + tw) - X(q.t))}" height="4" fill="${ink}"/>`; }
      const laneOf = r => (r.kind === 'create' ? 'udp0' : ['tcp_send', 'retransmit', 'ack_rx'].includes(r.kind) ? 'tcp0' : ['enqueue', 'dequeue', 'drop'].includes(r.kind) ? r.obj : ['deliver', 'tcp_rx', 'ack_send'].includes(r.kind) ? 'recv' : r.obj === 'dev0' && P.flow !== 'ack' ? 'dev0' : null);
      P.e.forEach((r, i) => { const ln = laneOf(r); if (!ln) return; const [ly, lh] = Y[ln], cy = ['enqueue', 'dequeue', 'drop'].includes(r.kind) ? ly + lh - 4 - 9 : ly + lh / 2;
        s += `<circle cx="${X(r.t)}" cy="${cy}" r="7.5" fill="${s1}" stroke="${ink}" stroke-width="2"/><text x="${X(r.t)}" y="${cy + 3.5}" font-size="9.5" font-weight="700" text-anchor="middle" fill="${ink}">${i + 1}</text>`; }); }
    return s + '</g></svg>';
  },

  // everything on the Events page
  html(ui, sec, e) {
    const E = TH_EVENTS, idx = E.index;
    if (!idx) return sec(1, 'Recorded moments', 'Loading…', '<p class="th-muted">Reading the recordings.</p>');
    if (!idx.length) return sec(1, 'Recorded moments', 'No recording yet.', '<p class="th-sm">The operator makes one with <code>harness/make_trace.py NAME "TITLE" "NOTE" [--setting=value]</code>.</p>');
    if (!idx.some(t => t.name === ui.trace)) ui.trace = idx[0].name;
    const M = idx.find(t => t.name === ui.trace), T = E.cache[ui.trace];
    let h = sec(1, 'Choose a recorded moment', 'Each recording is a few milliseconds of one simulation, with every packet-level event written down. They are made by the operator; the AI never sees them.',
      `<div class="th-recs">${idx.map(t => `<button class="th-rec${t.name === ui.trace ? ' on' : ''}" data-trace="${e(t.name)}"><b>${e(t.title)}</b><small>${e(t.note)}</small></button>`).join('')}</div>
       <p class="th-sm" style="margin-top:10px">This recording: <b>${M.ms} ms</b> starting at <b>${(M.from_ns / 1e9).toFixed(3)} s</b> of simulated time · <b>${M.events.toLocaleString()}</b> recorded events${T ? ` · <b>${Object.keys(T.pk).length.toLocaleString()}</b> packets` : ''}.
        In ns-3 an event takes no time by itself; time passes <i>between</i> events, and that is what is measured here.</p>`);
    if (!T) return h + sec(2, 'How long each step takes', 'Loading…', '<p class="th-muted">Reading the events.</p>');
    if (T.bad) return h + sec(2, 'How long each step takes', '', '<p class="th-muted">This recording is empty.</p>');
    const st = E.stats(T);
    h += sec(2, 'How long each step takes', 'The life of a packet is a chain of events. Each row is the time between two of them, over every packet in this recording whose both ends were recorded.',
      `<table class="th-evt"><thead><tr><th>Step</th><th>What decides how long it takes</th><th class="num">Typical</th><th class="num">Shortest</th><th class="num">Longest</th><th class="num">Packets</th></tr></thead><tbody>${
        st.map(r => r.head ? `<tr class="hd"><td colspan="6"><b>${e(r.head)}</b> <span class="th-sm">${e(r.note)}</span></td></tr>`
          : `<tr class="${r.sum ? 'sum' : ''}"><td>${e(r.step)}</td><td class="th-sm">${e(r.why)}</td>${r.g ? `<td class="num"><b>${E.us(r.g.med)}</b></td><td class="num">${E.us(r.g.min)}</td><td class="num">${E.us(r.g.max)}</td><td class="num">${r.g.n}</td>` : '<td class="num th-muted" colspan="4">not seen in this recording</td>'}</tr>`).join('')}</tbody></table>`);
    // window and chosen packet
    const span = T.span;
    if (!T.pk[ui.pk]) { const c = Object.values(T.pk).filter(p => p.whole && !p.dropped && p.flow !== 'ack');
      c.sort((a, b) => Math.abs(a.e.find(r => r.kind === 'tx_begin').t - span / 2) - Math.abs(b.e.find(r => r.kind === 'tx_begin').t - span / 2)); ui.pk = c.length ? c[0].key : Object.keys(T.pk)[0];
      const p = T.pk[ui.pk], a = p.e[0].t, b = p.e[p.e.length - 1].t, mg = Math.max(20000, (b - a) * 0.12); ui.tw = Math.min(span, b - a + 2 * mg); ui.t0 = a - mg; }
    if (!(ui.tw > 0) || ui.tw > span) ui.tw = Math.min(span, 600000);
    ui.t0 = Math.max(0, Math.min(span - ui.tw, ui.t0 || 0));
    const zooms = [[100000, '0.1 ms'], [300000, '0.3 ms'], [1000000, '1 ms'], [3000000, '3 ms'], [span, 'all ' + E.us(span)]];
    h += sec(3, 'The timeline: what caused what', 'Time runs left to right; the rows follow a packet from the sender’s applications (top) to the receiver (bottom). Click any mark to follow that packet: its steps are numbered in the picture and explained beside it.',
      `<div class="th-evbar"><span class="th-seg">${zooms.map(([w, t]) => `<button data-tw="${w}" class="${Math.abs(w - ui.tw) < 1 ? 'on' : ''}">${t}</button>`).join('')}</span>
          <button class="th-evbtn" data-pan="-1" aria-label="Earlier">◀</button><input type="range" id="th-evpan" min="0" max="${Math.max(0, span - ui.tw)}" step="1000" value="${ui.t0}" aria-label="Position in the recording"><button class="th-evbtn" data-pan="1" aria-label="Later">▶</button>
          <span class="th-sm" id="th-evwhere"></span></div>
       <div class="th-evkey"><span><i style="background:${css('--series-1')}"></i>UDP</span><span><i style="background:${css('--series-2')}"></i>TCP</span><span><i style="background:${css('--text-muted')}"></i>acknowledgement going back</span>
          <span><b style="color:${css('--critical')}">✕</b> dropped: queue full</span><span>① ② … the chosen packet’s steps</span></div>
       <div class="th-evside"><div id="th-evdia"></div><aside class="th-det" id="th-evdet"></aside></div>`);
    return h;
  },

  // fill the picture and the panel for the current window and packet (called after html(), and on every change)
  paint(root, ui) {
    const E = TH_EVENTS, T = E.cache[ui.trace], dia = root.querySelector('#th-evdia'), det = root.querySelector('#th-evdet'); if (!T || !dia) return;
    const e = TASK_VIEW._e;
    dia.innerHTML = E.draw(T, ui.t0, ui.tw, ui.pk);
    const w = root.querySelector('#th-evwhere'); if (w) w.textContent = `showing ${E.us(ui.t0)} – ${E.us(ui.t0 + ui.tw)} of the recording`;
    const p = T.pk[ui.pk];
    if (p) { const first = p.e[0], last = p.e[p.e.length - 1];
      det.style.setProperty('--dc', p.flow === 'udp' ? css('--series-1') : p.flow === 'tcp' ? css('--series-2') : css('--text-muted'));
      det.innerHTML = `<div class="where">The chosen packet</div><h3 class="name">${E.kindName(p)}</h3><code>${p.flow === 'tcp' ? 'sequence number ' : 'packet id '}${e(p.key.slice(1))} · ${Math.max(...p.e.map(r => r.size))} bytes on the wire</code>
        <p class="role">${p.dropped ? '<b style="color:' + css('--critical') + '">Dropped</b> on arrival at a full queue.' : p.whole ? `From creation to arrival: <b>${E.us(last.t - first.t)}</b>.` : 'Only part of its life falls inside this recording.'}
          <button class="th-evbtn" data-fit="1" style="margin-left:6px">Show its whole life</button></p>
        <ol class="th-life">${p.e.map((r, i) => { const y = E.why(T, p, i);
          return `<li><span class="n">${i + 1}</span><div><div class="l1"><b>${y.what}</b><span>${y.took == null ? 'at ' + E.us(r.t) : y.took === 0 ? 'same instant' : '+ ' + E.us(y.took)}</span></div>
            ${y.cause ? `<div class="l2"><i>because</i> ${y.cause}</div>` : ''}${y.effect ? `<div class="l2"><i>so</i> ${y.effect}</div>` : ''}</div></li>`; }).join('')}</ol>
        <p class="th-sm" style="margin-top:8px">“+” is the time since the previous step. Steps in the same instant happen inside one simulator event.</p>`; }
    const sel = k => { if (T.pk[k]) { ui.pk = k; E.paint(root, ui); } };
    root.querySelectorAll('#th-evdia [data-pk], #th-evdet [data-pk]').forEach(el => el.addEventListener('click', () => sel(el.dataset.pk)));
    const fit = det.querySelector('[data-fit]'); if (fit && p) fit.addEventListener('click', () => { const a = p.e[0].t, b = p.e[p.e.length - 1].t, m = Math.max(20000, (b - a) * 0.15);
      ui.tw = Math.min(T.span, b - a + 2 * m); ui.t0 = Math.max(0, Math.min(T.span - ui.tw, a - m)); TASK_VIEW.page(...TASK_VIEW._last); });
  },

  bind(root, ui) {  // controls that change the window; choosing never moves the page
    const E = TH_EVENTS, T = E.cache[ui.trace], redraw = () => { const y = window.scrollY; TASK_VIEW.page(...TASK_VIEW._last); if (window.scrollY !== y) window.scrollTo(0, y); };
    root.querySelectorAll('[data-trace]').forEach(el => el.addEventListener('click', () => { ui.trace = el.dataset.trace; ui.pk = null; ui.t0 = 0; ui.tw = 0; redraw(); }));
    if (!T || T.bad) return;
    root.querySelectorAll('[data-tw]').forEach(el => el.addEventListener('click', () => { const c = ui.t0 + ui.tw / 2; ui.tw = +el.dataset.tw; ui.t0 = c - ui.tw / 2; redraw(); }));
    root.querySelectorAll('[data-pan]').forEach(el => el.addEventListener('click', () => { ui.t0 = Math.max(0, Math.min(T.span - ui.tw, ui.t0 + el.dataset.pan * ui.tw * 0.5)); const r = root.querySelector('#th-evpan'); if (r) r.value = ui.t0; E.paint(root, ui); }));
    const r = root.querySelector('#th-evpan'); if (r) r.addEventListener('input', () => { ui.t0 = +r.value; E.paint(root, ui); });
    E.paint(root, ui);
  },
};
