// A session whose brief has a network ("topology": hosts, links, flows, queues; harness/network.py; TOPOLOGY.md).
// Its settings are addressed object.property and its measures are made from the network, so nothing about it can be
// read from the fixed tables of the two-host set-up. This file gives the page, for such a brief:
//   - the settings of the network by address (the same list as network.settings in the harness: keep the two alike);
//   - plain names and units for those settings and for the network's measures (put into the page's own tables, so
//     every place that looks a name up finds it);
//   - a colour for each flow (the first two are UDP's blue and TCP's orange of the two-host set-up);
//   - the picture of the network, drawn from the description;
//   - the charts over time of a simulation, from the columns its series has.
// A brief without a network is not touched by anything here.
Object.assign(EV, {
  net: b => (b && b.topology && Array.isArray(b.topology.hosts) ? b.topology : null),
  // {address: value} in the order of the description
  netSettings(t) {
    const out = {};
    for (const l of t.links || []) {
      for (const p of ['rate', 'delay', 'mtu', 'device_queue']) out[`${l.id}.${p}`] = l[p];
      const q = l.queue; if (!q) continue;
      out[`${l.id}.queue.length`] = q.length;
      for (const [f, v] of Object.entries(q.parts || {})) out[`${l.id}.queue.parts.${f}`] = v;
      for (const [f, v] of Object.entries(q.largest_rate || {})) out[`${l.id}.queue.largest_rate.${f}`] = v;
    }
    for (const f of t.flows || []) { if (f.kind === 'udp') { out[`${f.id}.rate`] = f.rate; out[`${f.id}.packet_bytes`] = f.packet_bytes; } else out[`${f.id}.type`] = f.type; }
    return out;
  },
  // the settings the network fixes (those the brief does not make knobs)
  netFixed(b) { const t = EV.net(b); if (!t) return {}; const kn = b.knobs || {}; return Object.fromEntries(Object.entries(EV.netSettings(t)).filter(([k]) => !(k in kn))); },
  // the way of a flow: [[link id, the host that sends on it]], the shortest in links; null if there is none
  netPath(t, f) {
    const adj = {}; (t.hosts || []).forEach(h => { adj[h.id] = []; });
    (t.links || []).forEach(l => { const [a, b] = l.between || []; if (adj[a] && adj[b]) { adj[a].push([b, l.id]); adj[b].push([a, l.id]); } });
    const prev = {}, seen = new Set([f.from]); let frontier = [f.from];
    while (frontier.length && !seen.has(f.to)) { const next = []; for (const h of frontier) for (const [o, l] of adj[h] || []) if (!seen.has(o)) { seen.add(o); prev[o] = [h, l]; next.push(o); } frontier = next; }
    if (!seen.has(f.to)) return null;
    const way = []; let h = f.to; while (h !== f.from) { const [p, l] = prev[h]; way.unshift([l, p]); h = p; } return way;
  },
  // a flow's colour: its place in the list of flows (1 and 2 are the two flows' colours of the two-host set-up)
  netColor(t, id) { const i = (t.flows || []).findIndex(f => f.id === id); return `var(--series-${i < 0 ? 8 : (i % 8) + 1})`; },
  netColorIndex(t, id) { const i = (t.flows || []).findIndex(f => f.id === id); return i < 0 ? 8 : (i % 8) + 1; },
  // plain names for the network's settings and measures, with units: put into the page's tables (once for each brief)
  NET_SEEN: {},
  netApply(b) {
    const t = EV.net(b); if (!t || EV.NET_SEEN[b.id + '|' + JSON.stringify(t).length]) return; EV.NET_SEEN[b.id + '|' + JSON.stringify(t).length] = 1;
    const K = {}, P = {}, U = {}, W = {};
    for (const l of t.links || []) { const [a, c] = l.between || [], q = l.queue;
      K[`${l.id}.rate`] = `rate of link ${l.id}`; K[`${l.id}.delay`] = `delay of link ${l.id}`; K[`${l.id}.mtu`] = `largest packet on ${l.id}`; U[`${l.id}.mtu`] = 'bytes';
      K[`${l.id}.device_queue`] = `device queue of ${l.id}`; U[`${l.id}.device_queue`] = 'packets';
      P[`${l.id}_util`] = `use of link ${l.id}`; W[`${l.id}_util`] = `Bits sent on link ${l.id} from ${a} to ${c}, divided by the link's rate.`;
      P[`${l.id}_util_back`] = `use of link ${l.id}, back`; W[`${l.id}_util_back`] = `Bits sent on link ${l.id} from ${c} to ${a}, divided by the link's rate.`;
      P[`${l.id}_drops`] = `drops at ${l.id}`; W[`${l.id}_drops`] = `Packets thrown away at the queue in front of link ${l.id} because it was full.`;
      P[`${l.id}_drops_back`] = `drops at ${l.id}, other side`; W[`${l.id}_drops_back`] = `Packets thrown away at the plain queue on the other side of link ${l.id}.`;
      if (q) { K[`${l.id}.queue.length`] = `queue length at ${l.id}`; U[`${l.id}.queue.length`] = 'packets';
        for (const f of Object.keys(q.parts || {})) { K[`${l.id}.queue.parts.${f}`] = `part of ${f} at ${l.id}`; K[`${l.id}.queue.largest_rate.${f}`] = `largest rate of ${f} at ${l.id}`;
          P[`${l.id}_drops_${f}`] = `drops of ${f} at ${l.id}`; W[`${l.id}_drops_${f}`] = `Packets of flow ${f} thrown away at its queue in the scheduler of link ${l.id} because the queue was full.`; } } }
    for (const f of t.flows || []) {
      P[`${f.id}_goodput_bps`] = `goodput of ${f.id}`; W[`${f.id}_goodput_bps`] = `What flow ${f.id} delivered to its receiver (${f.to}): payload bits per second over the measured time.`;
      if (f.kind === 'udp') { K[`${f.id}.rate`] = `rate of ${f.id}`; K[`${f.id}.packet_bytes`] = `packet size of ${f.id}`; U[`${f.id}.packet_bytes`] = 'bytes';
        P[`${f.id}_loss_frac`] = `loss of ${f.id}`; W[`${f.id}_loss_frac`] = `The share of the packets flow ${f.id} sent that never arrived.`; }
      else { K[`${f.id}.type`] = `TCP type of ${f.id}`; P[`${f.id}_retrans`] = `segments ${f.id} sent again`; W[`${f.id}_retrans`] = `TCP segments the sender of flow ${f.id} sent a second time.`; } }
    Object.assign(TH_DATA.KNOB, K); Object.assign(EV.LABEL, K); Object.assign(TH_DATA.PLAIN, P); Object.assign(EV.SET_UNIT, U);
    Object.entries(U).forEach(([k, u]) => { TH_DATA.UNIT[k] = ' ' + u; }); EV.NET_SAYS = Object.assign(EV.NET_SAYS || {}, W);
  },
  // what kind of number a measure is, by its name: a rate, a share, or a count (for a network's measures and the two-host ones alike)
  measureKind: k => (/_bps$/.test(k) ? 'rate' : /_loss_frac$|^link_util$|_util(_back)?$/.test(k) ? 'share' : 'count'),

  // ---- the picture: hosts as boxes from left to right along the flows, links as lines with their queue on the side that has it, each flow in its colour
  netLayout(t) {
    const hosts = (t.hosts || []).map(h => h.id), into = {}, out = {}; hosts.forEach(h => { into[h] = new Set(); out[h] = new Set(); });
    (t.flows || []).forEach(f => (EV.netPath(t, f) || []).forEach(([l, from]) => { const L = t.links.find(x => x.id === l), to = L.between[0] === from ? L.between[1] : L.between[0]; out[from].add(to); into[to].add(from); }));
    const layer = {}; let left = hosts.slice(), guard = 0;
    while (left.length && guard++ < 40) {  // a host goes one column right of the last host that sends to it; a ring of flows is cut by taking the hosts as they come
      const ready = left.filter(h => [...into[h]].every(p => p in layer || !left.includes(p)));
      const take = ready.length ? ready : [left[0]];
      take.forEach(h => { layer[h] = Math.max(-1, ...[...into[h]].filter(p => p in layer).map(p => layer[p])) + 1; });
      left = left.filter(h => !take.includes(h));
    }
    (t.links || []).forEach(l => { const [a, b] = l.between; if (!into[a].size && !out[a].size && layer[a] === 0 && (into[b].size || out[b].size)) layer[a] = Math.max(0, layer[b] - 1); });  // a host no flow touches stands beside its neighbour
    const cols = []; hosts.forEach(h => { (cols[layer[h]] = cols[layer[h]] || []).push(h); });
    return { layer, cols: cols.filter(Boolean) };
  },
  // where everything of the picture stands, in the picture's own units: each host's box, each link's two ends (on the facing edges of its hosts' boxes)
  netGeom(t) {
    const L = EV.netLayout(t), flows = t.flows || [], rowsOf = h => flows.filter(f => f.from === h || f.to === h), colGap = 190, rowGap = 44;
    // a box is as wide as its longest line needs (a flow it sends: "udp → receiver · UDP ✦ 2 Gbps"), between 178 and 290
    const lineOf = (f, h) => (f.from === h ? `${f.id} → ${f.to} · ${f.kind === 'udp' ? 'UDP ✦ ' + f.rate : 'TCP ✦ ' + String(f.type).replace(/^Tcp/, '')}` : `${f.id} ← ${f.from}`).length;
    const BW = Math.min(290, Math.max(178, 34 + 6.6 * Math.max(0, ...(t.hosts || []).flatMap(h => rowsOf(h.id).map(f => lineOf(f, h.id))))));
    const hOf = h => 34 + 17 * Math.max(1, rowsOf(h).length), colH = c => c.reduce((s, h) => s + hOf(h), 0) + rowGap * (c.length - 1), H = Math.max(120, ...L.cols.map(colH)) + 64, W = Math.max(1, L.cols.length) * BW + Math.max(0, L.cols.length - 1) * colGap + 24;
    const pos = {}; L.cols.forEach((c, i) => { let y = (H - colH(c)) / 2 + 6; c.forEach(h => { pos[h] = { x: 12 + i * (BW + colGap), y, w: BW, h: hOf(h) }; y += hOf(h) + rowGap; }); });
    const cy = h => pos[h].y + pos[h].h / 2, ends = {};
    (t.links || []).forEach(l => { const [a, c] = l.between, A = pos[a], C = pos[c]; if (!A || !C) return; const leftFirst = A.x <= C.x, same = A.x === C.x;
      ends[l.id] = same ? { a, c, x1: A.x + A.w / 2, y1: A.y < C.y ? A.y + A.h : A.y, x2: C.x + C.w / 2, y2: A.y < C.y ? C.y : C.y + C.h } : { a, c, x1: leftFirst ? A.x + A.w : A.x, y1: cy(a), x2: leftFirst ? C.x : C.x + C.w, y2: cy(c) }; });
    return { W, H, pos, ends, rowsOf };
  },
  netSvg(b, o) {
    const t = EV.net(b), e = EV.e, kn = (b && b.knobs) || {}, R = v => TASK_VIEW._rate(String(v)), o2 = o || {}; if (!t) return '';
    const G = EV.netGeom(t), flows = t.flows || [], rowsOf = G.rowsOf, pos = G.pos, W = G.W, H = G.H;
    const star = k => (k in kn ? '✦ ' : ''), cy = h => pos[h].y + pos[h].h / 2, deg = {}; (t.links || []).forEach(l => l.between.forEach(h => { deg[h] = (deg[h] || 0) + 1; }));
    // links: a line between the two boxes' facing edges; its name, rate and delay above it; the queue on the side that has one
    const links = (t.links || []).map(l => { const [a, c] = l.between, E = G.ends[l.id]; if (!E) return ''; const { x1, y1, x2, y2 } = E, q = l.queue;
      // the link's name stands nearer the host that has fewer links, where the lines are apart; its queue 30 px out from its host along the line
      const da = deg[a], dc = deg[c], at = da > dc ? 0.72 : dc > da ? 0.28 : 0.5, mx = x1 + (x2 - x1) * at, my = y1 + (y2 - y1) * at, len = Math.hypot(x2 - x1, y2 - y1) || 1, ux = (x2 - x1) / len, uy = (y2 - y1) / len;
      const through = flows.filter(f => (EV.netPath(t, f) || []).some(([id]) => id === l.id));
      const lines = through.length ? through.map((f, i) => { const d = (i - (through.length - 1) / 2) * 3.2; return `<line x1="${x1}" y1="${y1 + d}" x2="${x2}" y2="${y2 + d}" stroke="${EV.netColor(t, f.id)}" stroke-width="2.2" data-flow="${e(f.id)}"/>`; }).join('') : `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="nl-idle"/>`;
      const atA = q && q.on === a, qx = q ? (atA ? x1 + 30 * ux : x2 - 30 * ux) : 0, qy = q ? (atA ? y1 + 30 * uy : y2 - 30 * uy) : 0, away = q ? ((atA ? ux : -ux) >= 0 ? 'start' : 'end') : 'start', tx = qx + (away === 'start' ? -11 : 11);
      const parts = q && q.kind === 'scheduler' ? Object.entries(q.parts || {}).map(([f, v]) => `${star(`${l.id}.queue.parts.${f}`)}${f} ${v}`).join(' : ') : '';
      const qmark = !q ? '' : `<g class="nq" data-queue="${e(l.id)}">${q.kind === 'scheduler' ? `<circle cx="${qx}" cy="${qy}" r="11"/>` : `<rect x="${qx - 9}" y="${qy - 9}" width="18" height="18" rx="2"/>`}<text x="${tx}" y="${qy + 27}" text-anchor="${away}" class="sv">${e(q.kind === 'scheduler' ? 'scheduler' : 'queue')} · ${star(`${l.id}.queue.length`)}${e(q.length)} packets</text>${parts ? `<text x="${tx}" y="${qy + 41}" text-anchor="${away}" class="sv">${e(parts)}</text>` : ''}</g>`;
      return `<g class="nl" data-link="${e(l.id)}">${lines}<text x="${mx}" y="${my - 21}" text-anchor="middle" class="sn">${e(l.id)}</text><text x="${mx}" y="${my - 8}" text-anchor="middle" class="sv">${star(`${l.id}.rate`)}${e(R(l.rate))} · ${star(`${l.id}.delay`)}${e(R(l.delay))}</text>${qmark}</g>`; }).join('');
    // hosts: a box with its name and one line for each flow it sends or receives
    const boxes = Object.keys(pos).map(h => { const p = pos[h], rows = rowsOf(h);
      const line = (f, i) => { const sends = f.from === h, y = p.y + 38 + 17 * i, what = f.kind === 'udp' ? `UDP ${star(`${f.id}.rate`)}${R(f.rate)}` : `TCP ${star(`${f.id}.type`)}${String(f.type).replace(/^Tcp/, '')}`;
        return `<g data-flow="${e(f.id)}"><circle cx="${p.x + 13}" cy="${y - 4}" r="4.5" fill="${EV.netColor(t, f.id)}"/><text x="${p.x + 23}" y="${y}" class="sv"><tspan class="sn2">${e(f.id)}</tspan> ${sends ? `→ ${e(f.to)} · ${e(what)}` : `← ${e(f.from)}`}</text></g>`; };
      return `<g class="nh" data-host="${e(h)}"><rect x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}" rx="9"/><text x="${p.x + 10}" y="${p.y + 17}" class="sn">${e(h)}</text><text x="${p.x + p.w - 8}" y="${p.y + 17}" text-anchor="end" class="sv">${rows.length ? '' : 'forwards only'}</text>${rows.length ? rows.map(line).join('') : ''}</g>`; }).join('');
    const pol = o2.pol ? `<text x="${W / 2}" y="${H - 8}" text-anchor="middle" class="sv" id="sy-pol"${o2.op ? ' data-by="operator"' : ''}>${e(o2.pol)}</text>` : '';
    return `<svg class="sy net" id="net-pic" viewBox="0 0 ${W} ${H}" width="${Math.min(W, o2.max || 1000)}" role="img" aria-label="The network: ${e((t.hosts || []).length)} hosts, ${e((t.links || []).length)} links, ${e(flows.length)} flows">${links}${boxes}${pol}</svg>`;
  },
  // the objects of the network in words, beside the picture: its flows and its links, a ✦ before what the AI may change
  netSide(b) {
    const t = EV.net(b), e = EV.e, kn = (b && b.knobs) || {}, R = v => TASK_VIEW._rate(String(v)), s = k => (k in kn ? '<span class="nk" title="The AI may change it">✦</span> ' : '');
    const flow = f => `<tr data-flow="${e(f.id)}"><td><i class="nf" style="background:${EV.netColor(t, f.id)}"></i><b>${e(f.id)}</b></td><td>${e(f.kind.toUpperCase())}</td><td>${e(f.from)} → ${e(f.to)}</td><td>${f.kind === 'udp' ? `${s(`${f.id}.rate`)}${e(R(f.rate))} · ${s(`${f.id}.packet_bytes`)}${e(f.packet_bytes)}-byte packets` : `${s(`${f.id}.type`)}${e(String(f.type).replace(/^Tcp/, ''))}`}</td></tr>`;
    const link = l => { const q = l.queue; return `<tr data-link="${e(l.id)}"><td><b>${e(l.id)}</b></td><td>${e(l.between.join(' – '))}</td><td>${s(`${l.id}.rate`)}${e(R(l.rate))} · ${s(`${l.id}.delay`)}${e(R(l.delay))}</td><td>${q ? `${e(q.kind === 'scheduler' ? 'scheduler' : 'plain queue')} on ${e(q.on)}'s side, ${s(`${l.id}.queue.length`)}${e(q.length)} packets${q.kind === 'scheduler' ? ': ' + Object.entries(q.parts || {}).map(([f, v]) => `${s(`${l.id}.queue.parts.${f}`)}${e(f)} ${e(v)}`).join(' : ') + (Object.keys(q.largest_rate || {}).length ? '; at most ' + Object.entries(q.largest_rate).map(([f, v]) => `${e(f)} ${e(R(v))}`).join(', ') : '') : ''}` : 'a plain queue of 100 packets on each side'}</td></tr>`; };
    return `<div class="net-side" id="net-side"><table class="st-who nt" data-exact="1"><tbody><tr class="st-grp"><td colspan="4">${(t.flows || []).length} flow${(t.flows || []).length === 1 ? '' : 's'}</td></tr>${(t.flows || []).map(flow).join('')}
      <tr class="st-grp"><td colspan="4">${(t.links || []).length} link${(t.links || []).length === 1 ? '' : 's'} between ${(t.hosts || []).length} hosts</td></tr>${(t.links || []).map(link).join('')}</tbody></table>
      <p class="sm">The parts of a scheduler are divided by their sum. A host with more than one link forwards.</p></div>`;
  },

  // ---- the charts over time of a simulation of a network: one chart per kind of column of its series (a line for each flow or queue, in the flow's colour)
  netTime(series) {
    const t = EV.net(EV.M && EV.M.brief), names = Object.keys(series.cols || {}), idx = n => { const f = (t && t.flows || []).find(q => n === `${q.id}_bps` || n === `${q.id}_cwnd` || n.endsWith(`_q_${q.id}`) || n.endsWith(`_drops_${q.id}`)); return f ? EV.netColorIndex(t, f.id) : 8; };
    const pick = rx => names.filter(n => rx.test(n)), diff = a => a.map((v, i) => (i ? v - a[i - 1] : v)), lab = (n, cut) => n.replace(cut, '').replace(/_/g, ' ');
    const defs = [{ id: 'tput', title: 'Throughput per flow', unit: 'Mbps', cols: pick(/_bps$/), lines: S => pick(/_bps$/).map(n => [lab(n, /_bps$/), idx(n), S.cols[n].map(v => v / 1e6)]) },
      { id: 'cwnd', title: 'TCP congestion window', unit: 'kB', cols: pick(/_cwnd$/), lines: S => pick(/_cwnd$/).map(n => [lab(n, /_cwnd$/), idx(n), S.cols[n].map(v => v / 1e3)]) },
      { id: 'd0', title: 'Packets dropped from each queue', unit: 'packets per sample', cols: pick(/_drops(_|$)/), lines: S => pick(/_drops(_|$)/).map(n => [lab(n, /^$/), idx(n), diff(S.cols[n])]) },
      { id: 'q', title: 'Packets waiting in each queue', unit: 'packets', cols: pick(/_q(_|$)/), lines: S => pick(/_q(_|$)/).map(n => [lab(n, /^$/), idx(n), S.cols[n]]) }];
    return defs.filter(d => d.cols.length);
  },
  // the charts a simulation's series gives: the four of the two-host set-up, or those of its network
  timeDefs(series) { return series && series.cols && !series.udp ? EV.netTime(series) : EV.TIME.filter(q => !q.need || q.need(series)); },
});
Object.assign(EV, {
  // the names of the measures of the open session (its brief's outputs; the seven of the two-host set-up where none is recorded)
  outNames() { const M = EV.M, g = M && M.meta && M.meta.given; return Object.keys((g && g.outputs) || (M && M.brief && M.brief.outputs) || TH_DATA.PLAIN); },
  // which colour is which flow, in words, beside a chart
  flowsSay() { const t = EV.net(EV.M && EV.M.brief); return t ? 'each flow in its colour: ' + t.flows.map((f, i) => `<i class="sw" style="display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--series-${(i % 8) + 1})"></i> ${EV.e(f.id)}`).join(' · ') : 'UDP blue, TCP orange'; },
  // the network with some of its settings at other values (a session's knobs at their defaults; a simulation's own settings)
  netWith(t, values) {
    const c = JSON.parse(JSON.stringify(t)), have = EV.netSettings(c);
    for (const [addr, v] of Object.entries(values || {})) { if (!(addr in have)) continue; const [obj, ...rest] = addr.split('.'); let x = [...c.links, ...c.flows].find(q => q.id === obj), keys = rest;
      if (keys[0] === 'queue') { x = x.queue; keys = keys.slice(1); } if (keys.length === 2) x[keys[0]][keys[1]] = v; else x[keys[0]] = v; }
    return c;
  },
});
Object.assign(EV, {
  // the two measures a list of a network's simulations shows: what the aim's conditions are about (or the first loss), and the aim's target (or the first goodput)
  netTwo(b) { const outs = Object.keys(b.outputs || {}), g = b.goal || {}, t = g.kind === 'given' && g.target ? g.target.measure : null, cond = (g.conditions || []).map(c => outs.find(o => new RegExp('\\b' + o + '\\b').test(c))).find(Boolean);
    const first = cond || outs.find(o => /_loss_frac$/.test(o)) || outs[1], second = t || outs.find(o => /_goodput_bps$/.test(o)) || outs[0]; return first === second ? [second] : [first, second]; },
});
Object.assign(EV, {
  // a tile of a running simulation draws two lines: the samples as [t, first, second]. two-hosts writes UDP and TCP in columns 1 and 2;
  // the program that builds a network names its columns, and the first two flows' "_bps" columns are taken (one flow: the second is 0)
  tileRows(text) {
    const lines = String(text || '').trim().split('\n'), head = (lines[0] || '').split(','), bps = head.map((n, i) => (/_bps$/.test(n) ? i : -1)).filter(i => i > 0), a = bps[0] || 1, b = bps[1] || 0;
    return lines.slice(1).map(l => { const c = l.split(',').map(Number); return [c[0], c[a], b ? c[b] : 0]; }).filter(q => q.every(Number.isFinite));
  },
  tileNames() {
    const t = EV.net(EV.M && EV.M.brief); if (!t) return { a: ['UDP', 'udp_goodput_bps'], b: ['TCP', 'tcp_goodput_bps'], loss: ['UDP loss', 'udp_loss_frac'] };
    const f = t.flows || [], u = f.find(q => q.kind === 'udp');
    return { a: [f[0].id, `${f[0].id}_goodput_bps`], b: f[1] ? [f[1].id, `${f[1].id}_goodput_bps`] : null, loss: u ? [`loss of ${u.id}`, `${u.id}_loss_frac`] : null };
  },
});
Object.assign(EV, {
  // a simulation's changes to the network, in words (the harness's own short form is in its evidence line)
  editsSay(edits) { return (edits || []).map(e => (e.do === 'add_host' ? `added host ${e.id}` : e.do === 'add_link' ? `added link ${e.id} between ${e.from} and ${e.to}${e.rate ? ' (' + TASK_VIEW._rate(e.rate) + ')' : ''}` : e.do === 'add_flow' ? `added ${String(e.kind).toUpperCase()} flow ${e.id} from ${e.from} to ${e.to}`
    : e.do === 'add_queue' ? `put a ${e.kind === 'fifo' ? 'plain queue' : 'scheduler'} on ${e.on}'s side of link ${e.id}` : `removed ${e.kind === 'queue' ? 'the queue of link' : e.kind} ${e.id}`)).join('; ') || 'nothing'; },
});
