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
  // The two ends of a link, as ns-3 has them (network.ends in the harness): {host: {rate, device_queue, queue}}: the device of that host on the
  // link (the link's values unless the end states its own, in "ends") and the queue in front of it (null: not described, a plain queue of 100 packets).
  netEnds(l) {
    const E = l.ends || {}, q = l.queue, out = {};
    (l.between || []).forEach(h => { const x = E[h] || {}; out[h] = { rate: 'rate' in x ? x.rate : l.rate, device_queue: 'device_queue' in x ? x.device_queue : l.device_queue, mtu: 'mtu' in x ? x.mtu : l.mtu, loss: 'loss' in x ? x.loss : null, queue: x.queue ? x.queue : (q && q.on === h ? q : null) }; });
    return out;
  },
  // Every described queue of the network (network.queues): [{ l, h, q, a, id }]: its link, the host whose sending side it is, the queue, the address its
  // settings stand under (<link>.queue in the older form with "on", else <link>.<host>.queue) and its name as an object (the link's id, or link.host).
  netQueues(t) {
    const out = [];
    (t.links || []).forEach(l => (l.between || []).forEach(h => { const x = (l.ends || {})[h];
      if (x && x.queue) out.push({ l, h, q: x.queue, a: `${l.id}.${h}.queue`, id: `${l.id}.${h}` });
      else if (l.queue && l.queue.on === h) out.push({ l, h, q: l.queue, a: `${l.id}.queue`, id: l.id }); }));
    return out;
  },
  // the flows that wait in the queue of a scheduler's part: a class's flows, or the one flow the part is named after
  netMembers: (q, name) => ((q.classes || {})[name] || [name]),
  // a flow is an ns-3 application and the socket it opens. kind is the socket (udp, tcp); app is the application: 'onoff' (OnOffApplication, a constant rate) or
  // 'bulk' (BulkSendApplication, as fast as TCP accepts: TCP only). Not stated, a udp flow is onoff and a tcp flow is bulk (network.app in harness/network.py)
  netApp: f => f.app || (f.kind === 'udp' ? 'onoff' : 'bulk'),
  // what a flow may state of its application's times (network.FLOW_TIMES), each with its plain name, its unit and what the program does when it is left out
  NET_TIMES: ['start', 'stop', 'on_time', 'off_time', 'max_bytes'],
  NET_TIME_SAYS: { start: ['start time', 's', '1 s'], stop: ['stop time', 's', 'the end'], on_time: ['on period', 's', 'always on'], off_time: ['off period', 's', 'always on'], max_bytes: ['byte limit', 'bytes', 'no limit'] },
  // a queue's kind is the queue disc of one net device: [plain name, the ns-3 class, what it does]. scheduler is the project's own; the others are ns-3's (network.QUEUE_DISCS)
  NET_DISC: { scheduler: ['scheduler', 'FlowQueueDisc', "this project's queue disc: its queues, and a part of the link for each"], fifo: ['shared queue', 'FifoQueueDisc', 'one queue for all the flows, first in, first out'],
    pfifofast: ['three-band queue', 'PfifoFastQueueDisc', "three queues by a packet's priority, the highest served first"], codel: ['CoDel queue', 'CoDelQueueDisc', 'one queue; a packet that waited too long is dropped'],
    fqcodel: ['FqCoDel queue', 'FqCoDelQueueDisc', "a queue for each flow, served in turn, each with CoDel; ns-3's own default"], red: ['RED queue', 'RedQueueDisc', 'one queue; packets are dropped at random before it is full'],
    pie: ['PIE queue', 'PieQueueDisc', 'one queue; packets are dropped at random to hold the waiting time'] },
  netDisc: k => EV.NET_DISC[k] || EV.NET_DISC.fifo,
  // the ns-3 attribute a setting is, by its address: shown beside the setting's plain name
  NET_ATTR: { delay: 'Channel · Delay', mtu: 'NetDevice · Mtu', device_queue: 'TxQueue · MaxSize', length: 'QueueDisc · MaxSize', parts: 'FlowQueueDisc · part', largest_rate: 'FlowQueueDisc · largest rate', packet_bytes: 'PacketSize', type: 'TcpL4Protocol · SocketType',
    start: 'StartTime', stop: 'StopTime', on_time: 'OnTime', off_time: 'OffTime', max_bytes: 'MaxBytes', loss: 'ReceiveErrorModel · ErrorRate', tcpInitCwnd: 'TcpSocket · InitialCwnd', tcpBufBytes: 'TcpSocket · SndBufSize, RcvBufSize',
    tcpSack: 'TcpSocketBase · Sack', tcpTimestamps: 'TcpSocketBase · Timestamp', tcpDelAck: 'TcpSocket · DelAckCount', duration: 'the measured seconds', seed: 'RngRun' },
  netAttr(addr, t) { const p = String(addr).split('.'), w = p.includes('parts') ? 'parts' : p.includes('largest_rate') ? 'largest_rate' : p[p.length - 1]; if (w !== 'rate') return EV.NET_ATTR[w] || '';
    return ((t && t.flows) || []).some(f => f.id === p[0]) ? 'OnOffApplication · DataRate' : 'NetDevice · DataRate'; },
  NET_APP: { onoff: ['OnOff', 'OnOffApplication', 'packets at a constant rate'], bulk: ['BulkSend', 'BulkSendApplication', 'always has data: as fast as TCP accepts'] },
  // the names of the measures of a network, as the harness makes them (network.outputs: keep the two alike)
  netOutNames(t) {
    const out = [];
    (t.flows || []).forEach(f => { out.push(`${f.id}_goodput_bps`, f.kind === 'udp' ? `${f.id}_loss_frac` : `${f.id}_retrans`); });
    (t.links || []).forEach(l => { const E = EV.netEnds(l), hs = l.between || [], given = hs.map(h => !!E[h].queue), both = given[0] && given[1], front = [], back = [];
      hs.forEach((h, side) => { const q = E[h].queue;
        if (q && q.kind === 'scheduler') Object.keys(q.parts || {}).forEach(n => front.push(`${l.id}_drops_${n}`));
        else if (q) (both && side === 1 ? back : front).push(`${l.id}_drops${both && side === 1 ? '_back' : ''}`);
        else if (given[0] || given[1] || side === 1) back.push(`${l.id}_drops_back`);
        else front.push(`${l.id}_drops`); });
      out.push(`${l.id}_util`, `${l.id}_util_back`, ...hs.filter(h => E[h].loss != null).map(h => `${l.id}_lost_${h}`), ...front, ...back); });
    return out;
  },
  // {address: value} in the order of the description
  netSettings(t) {
    const out = {}, qs = EV.netQueues(t);
    for (const l of t.links || []) {
      for (const p of ['rate', 'delay', 'mtu', 'device_queue']) out[`${l.id}.${p}`] = l[p];
      for (const [h, x] of Object.entries(l.ends || {})) for (const p of ['rate', 'device_queue', 'mtu', 'loss']) if (x && p in x) out[`${l.id}.${h}.${p}`] = x[p];
      for (const { q, a } of qs.filter(x => x.l === l)) {
        out[`${a}.length`] = q.length;
        for (const [f, v] of Object.entries(q.parts || {})) out[`${a}.parts.${f}`] = v;
        for (const [f, v] of Object.entries(q.largest_rate || {})) out[`${a}.largest_rate.${f}`] = v;
      }
    }
    for (const f of t.flows || []) { if (EV.netApp(f) === 'onoff') { out[`${f.id}.rate`] = f.rate; out[`${f.id}.packet_bytes`] = f.packet_bytes; } if (f.kind === 'tcp') out[`${f.id}.type`] = f.type; for (const p of EV.NET_TIMES) if (p in f) out[`${f.id}.${p}`] = f[p]; }
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
    for (const l of t.links || []) { const [a, c] = l.between || [], E = EV.netEnds(l), own = h => E[h] && E[h].rate !== l.rate, both = E[a] && E[c] && E[a].queue && E[c].queue;
      K[`${l.id}.rate`] = `rate of link ${l.id}`; K[`${l.id}.delay`] = `delay of link ${l.id}`; K[`${l.id}.mtu`] = `largest packet on ${l.id}`; U[`${l.id}.mtu`] = 'bytes';
      K[`${l.id}.device_queue`] = `device queue of ${l.id}`; U[`${l.id}.device_queue`] = 'packets';
      P[`${l.id}_util`] = `use of link ${l.id}`; W[`${l.id}_util`] = `Bits sent on link ${l.id} from ${a} to ${c}, divided by ${own(a) ? `the rate of ${a}'s device` : "the link's rate"}.`;
      P[`${l.id}_util_back`] = `use of link ${l.id}, back`; W[`${l.id}_util_back`] = `Bits sent on link ${l.id} from ${c} to ${a}, divided by ${own(c) ? `the rate of ${c}'s device` : "the link's rate"}.`;
      P[`${l.id}_drops`] = `drops at ${l.id}`; W[`${l.id}_drops`] = `Packets thrown away at the queue in front of link ${l.id}${both ? ` on ${a}'s side` : ''} because it was full.`;
      P[`${l.id}_drops_back`] = `drops at ${l.id}, other side`; W[`${l.id}_drops_back`] = `Packets thrown away at the plain queue on ${both ? `${c}'s side` : 'the other side'} of link ${l.id}.`;
      // what an end states of its own device (a link is a channel and two devices)
      for (const h of Object.keys(l.ends || {})) { K[`${l.id}.${h}.rate`] = `rate of ${h}'s device on ${l.id}`; K[`${l.id}.${h}.device_queue`] = `device queue of ${h} on ${l.id}`; U[`${l.id}.${h}.device_queue`] = 'packets';
        K[`${l.id}.${h}.mtu`] = `largest packet of ${h}'s device on ${l.id}`; U[`${l.id}.${h}.mtu`] = 'bytes'; K[`${l.id}.${h}.loss`] = `loss at ${h}'s device on ${l.id}`;
        P[`${l.id}_lost_${h}`] = `lost at ${h}'s device on ${l.id}`; W[`${l.id}_lost_${h}`] = `Packets the device of ${h} on link ${l.id} received in error and dropped: its loss, a part of the packets arriving there.`; }
      for (const { h, q, a, id } of EV.netQueues(t).filter(x => x.l === l)) { const at = id === l.id ? l.id : `${l.id}, ${h}'s side`;
        K[`${a}.length`] = `queue length at ${at}`; U[`${a}.length`] = 'packets';
        for (const f of Object.keys(q.parts || {})) { const who = EV.netMembers(q, f), cls = !(who.length === 1 && who[0] === f);
          K[`${a}.parts.${f}`] = `part of ${f} at ${at}`; K[`${a}.largest_rate.${f}`] = `largest rate of ${f} at ${at}`;
          P[`${l.id}_drops_${f}`] = `drops of ${f} at ${l.id}`; W[`${l.id}_drops_${f}`] = cls ? `Packets of the flows ${who.join(', ')} thrown away at the queue they share (${f}) in the scheduler of link ${l.id} on ${h}'s side because the queue was full.` : `Packets of flow ${f} thrown away at its queue in the scheduler of link ${l.id} because the queue was full.`; } } }
    for (const f of t.flows || []) {
      P[`${f.id}_goodput_bps`] = `goodput of ${f.id}`; W[`${f.id}_goodput_bps`] = `What flow ${f.id} delivered to its receiver (${f.to}): payload bits per second over the measured time.`;
      if (EV.netApp(f) === 'onoff') { K[`${f.id}.rate`] = `rate of ${f.id}`; K[`${f.id}.packet_bytes`] = `packet size of ${f.id}`; U[`${f.id}.packet_bytes`] = 'bytes'; }
      for (const p of EV.NET_TIMES) { K[`${f.id}.${p}`] = `${EV.NET_TIME_SAYS[p][0]} of ${f.id}`; U[`${f.id}.${p}`] = EV.NET_TIME_SAYS[p][1]; }
      if (f.kind === 'udp') { P[`${f.id}_loss_frac`] = `loss of ${f.id}`; W[`${f.id}_loss_frac`] = `The share of the packets flow ${f.id} sent that never arrived.`; }
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
    const lineOf = (f, h) => (f.from === h ? `${f.id} → ${f.to} · ${f.kind === 'udp' ? 'UDP ✦ ' + f.rate : 'TCP ✦ ' + String(f.type).replace(/^Tcp/, '') + (EV.netApp(f) === 'onoff' ? ' · ✦ ' + f.rate : '')}` : `${f.id} ← ${f.from}`).length;
    const BW = Math.min(290, Math.max(178, 34 + 6.6 * Math.max(0, ...(t.hosts || []).flatMap(h => rowsOf(h.id).map(f => lineOf(f, h.id))))));
    const hOf = h => 34 + 17 * Math.max(1, rowsOf(h).length), colH = c => c.reduce((s, h) => s + hOf(h), 0) + rowGap * (c.length - 1), H = Math.max(120, ...L.cols.map(colH)) + 64, W = Math.max(1, L.cols.length) * BW + Math.max(0, L.cols.length - 1) * colGap + 24;
    const pos = {}; L.cols.forEach((c, i) => { let y = (H - colH(c)) / 2 + 6; c.forEach(h => { pos[h] = { x: 12 + i * (BW + colGap), y, w: BW, h: hOf(h) }; y += hOf(h) + rowGap; }); });
    const cy = h => pos[h].y + pos[h].h / 2, ends = {};
    (t.links || []).forEach(l => { const [a, c] = l.between, A = pos[a], C = pos[c]; if (!A || !C) return; const leftFirst = A.x <= C.x, same = A.x === C.x;
      ends[l.id] = same ? { a, c, x1: A.x + A.w / 2, y1: A.y < C.y ? A.y + A.h : A.y, x2: C.x + C.w / 2, y2: A.y < C.y ? C.y : C.y + C.h } : { a, c, x1: leftFirst ? A.x + A.w : A.x, y1: cy(a), x2: leftFirst ? C.x : C.x + C.w, y2: cy(c) }; });
    return { W, H, pos, ends, rowsOf };
  },
  // ---- the schema of the network (2026-11-22, the operator: "a schema of more quality, to see what object types are in the topology"): each host drawn
  // as the builder draws it in full (NETC.hostSvg, brief_canvas.js): its ns-3 Node, its applications, its sockets, its IPv4, its traffic control; on
  // each end of a link the device (ns-3 PointToPointNetDevice), between the two devices the channel (PointToPointChannel); each flow in its colour
  // from its application to the other end. A network too wide to read that way draws each host as its sign and its marks (NETC.hostSimple).
  // Under it, EV.netKinds names each kind of ns-3 object the network has, with how many.
  NET_DW: 52, NET_DH: 24, NET_GAP: 184,
  netPassing(t) { const qs = EV.netQueues(t), out = {}; qs.forEach(x => { out[x.id] = []; }); (t.flows || []).forEach(f => (EV.netPath(t, f) || []).forEach(([l, from]) => { const x = qs.find(y => y.l.id === l && y.h === from); if (x) out[x.id].push(f.id); })); return out; },
  netSvg(b, o) {
    const t = EV.net(b); if (!t) return ''; if (typeof NETC === 'undefined' || !NETC.hostSvg) return EV.netSvgPlain(b, o);
    const e = EV.e, kn = (b && b.knobs) || {}, R = v => TASK_VIEW._rate(String(v)), o2 = o || {}, star = k => (k in kn ? '✦ ' : ''), knobs = Object.fromEntries(Object.keys(kn).map(k => [k, 1]));
    const flows = t.flows || [], links = t.links || [], passing = EV.netPassing(t), DW = EV.NET_DW, DH = EV.NET_DH, GAP = EV.NET_GAP, VG = 44;
    const L = EV.netLayout(t), colOf = {}; L.cols.forEach((c, i) => c.forEach(h => { colOf[h] = i; }));
    const draw = simple => Object.fromEntries((t.hosts || []).map(h => [h.id, (simple ? NETC.hostSimple : NETC.hostSvg)(t, h, knobs, passing)]));
    const wide = P => L.cols.reduce((a, c) => a + Math.max(...c.map(h => P[h].w)), 0) + GAP * Math.max(0, L.cols.length - 1);
    let P = draw(false), simple = false; if (wide(P) > 1700) { P = draw(true); simple = true; }
    // the side of a host a link leaves by: the side of its traffic control where it has a queue there (on the right), else the side the other host stands on
    const other = (l, h) => (l.between[0] === h ? l.between[1] : l.between[0]), exOf = (h, l) => !simple && ((P[h].geo || {}).ex || []).find(x => x.l === l.id);
    const side = (h, l) => (exOf(h, l) ? 'right' : colOf[other(l, h)] > colOf[h] ? 'right' : colOf[other(l, h)] < colOf[h] ? 'left' : P[h].mirror ? 'left' : 'right');
    const pos = {}, devY = {};   // devY[h + '|' + l]: the height of the device of host h on link l, in the host's own picture
    const place = h => { const q = P[h], g = q.geo || {}, mine = links.filter(l => l.between.includes(h));
      ['left', 'right'].forEach(sd => { const plain = mine.filter(l => side(h, l) === sd && !exOf(h, l)), y = l => (pos[other(l, h)] ? pos[other(l, h)].y + (devY[other(l, h) + '|' + l.id] || 0) : 1e9);
        plain.sort((a, c) => y(a) - y(c)).forEach((l, k) => { const lo = simple ? 0 : g.ip0, hi = simple ? q.h : g.ip1, n = plain.length;
          devY[h + '|' + l.id] = simple ? q.h * (k + 1) / (n + 1) : !g.rows && !g.qs && sd === 'right' ? hi - 12 - 26 * (n - 1 - k) : lo + (hi - lo) * (k + 1) / (n + 1); }); });
      mine.forEach(l => { const x = exOf(h, l); if (x) devY[h + '|' + l.id] = x.y; }); };
    // columns from left to right; a host is set at the height where its devices meet those of the hosts already placed it is linked to
    let x = 12 + (L.cols[0] || []).some(h => links.some(l => l.between.includes(h) && side(h, l) === 'left')) * DW;
    L.cols.forEach((c, i) => { const cw = Math.max(...c.map(h => P[h].w));
      c.forEach(h => place(h));
      const want = h => { const ls = links.filter(l => l.between.includes(h) && pos[other(l, h)]); return ls.length ? ls.reduce((a, l) => a + pos[other(l, h)].y + devY[other(l, h) + '|' + l.id] - devY[h + '|' + l.id], 0) / ls.length : null; };
      let y = 0; c.forEach(h => { const w0 = want(h), at = c.length === 1 && w0 != null ? w0 : y; pos[h] = { x: i === 0 ? x + cw - P[h].w : x, y: at, w: P[h].w, h: P[h].h }; y = at + P[h].h + VG; });
      if (c.length > 1) { const ws = c.map(want).filter(v => v != null); if (ws.length) { const top = pos[c[0]].y, bot = pos[c[c.length - 1]].y + P[c[c.length - 1]].h, mid = ws.reduce((a, v) => a + v, 0) / ws.length + P[c[0]].h / 2; c.forEach(h => { pos[h].y += mid - (top + bot) / 2; }); } }
      x += cw + GAP; });
    const y0 = Math.min(...Object.values(pos).map(p => p.y)) - 34; Object.values(pos).forEach(p => { p.y -= y0; });
    const pol = o2.pol ? 1 : 0, W = Math.max(...Object.values(pos).map(p => p.x + p.w)) + 12 + links.some(l => l.between.some(h => side(h, l) === 'right' && colOf[other(l, h)] === colOf[h])) * DW, H = Math.max(...Object.values(pos).map(p => p.y + p.h)) + 22 + pol * 22;
    // a device: a box on the outside of its host, at the height of its link; what it is and what it does in its hover box
    const dev = (h, l) => { const p = pos[h], sd = side(h, l), y = p.y + devY[h + '|' + l.id], x0 = sd === 'right' ? p.x + p.w : p.x - DW, own = (l.ends || {})[h] || {};
      const says = `device of ${h} on link ${l.id}: ns-3 PointToPointNetDevice, the network card at ${h}'s end of the link. It sends at ${R(own.rate || l.rate)}${own.device_queue ? `; its own transmit queue holds ${own.device_queue} packets` : ''}${own.loss ? `; it loses ${own.loss} of what it receives` : ''}.`;
      return { x0, x1: x0 + DW, y, sd, svg: `<g class="nd" data-nk="device" data-dev="${e(h)}" data-act="sysobj" data-id="dev:${e(h)}|${e(l.id)}"${o2.on === `dev:${h}|${l.id}` ? ' data-on="1"' : ''}><title>${e(says)}</title><rect x="${x0}" y="${y - DH / 2}" width="${DW}" height="${DH}" rx="5"/><text x="${x0 + DW / 2}" y="${y + 4}" text-anchor="middle" class="nd-t">device</text></g>` }; };
    // the flows' lines: inside the host from where they leave (its traffic control or its IPv4) to its edge, then along the channel, side by side
    const seg = (x1, y1, x2, y2, f) => `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${EV.netColor(t, f)}" stroke-width="2.2" data-flow="${e(f)}"/>`;
    const inner = (h, l, d, through) => { if (simple) return ''; const p = pos[h], g = P[h].geo, xq = exOf(h, l), sd = d.sd;
      const from = xq ? p.x + xq.x : sd === 'right' ? (!g.rows || !P[h].mirror ? p.x + g.xi + g.wi : null) : (P[h].mirror || !g.rows ? p.x + g.xi : null); if (from == null) return '';
      return through.map((f, i) => { const dy = (i - (through.length - 1) / 2) * 3.2; return seg(from, d.y + dy, sd === 'right' ? p.x + p.w : p.x, d.y + dy, f); }).join(''); };
    const linkSvg = l => { const [a, c] = l.between; if (!pos[a] || !pos[c]) return ''; const A = dev(a, l), C = dev(c, l), through = flows.filter(f => (EV.netPath(t, f) || []).some(([id]) => id === l.id)).map(f => f.id);
      const flip = colOf[c] < colOf[a], F = flip ? C : A, T = flip ? A : C;   // F: the end in the earlier column, where the link runs straight; T: where it turns
      const ax = F.sd === 'right' ? F.x1 : F.x0, cx = T.sd === 'right' ? T.x1 : T.x0, k = Math.sign(cx - ax) || 1, bend = Math.abs(F.y - T.y) > 1, turn = Math.min(44, Math.abs(cx - ax) / 2);
      const path = dy => (bend ? [[ax, F.y + dy, cx - k * turn, F.y + dy], [cx - k * turn, F.y + dy, cx - k * 8, T.y + dy], [cx - k * 8, T.y + dy, cx, T.y + dy]] : [[ax, F.y + dy, cx, T.y + dy]]);
      const lines = through.length ? through.map((f, i) => path((i - (through.length - 1) / 2) * 3.2).map(([x1, y1, x2, y2]) => seg(x1, y1, x2, y2, f)).join('')).join('') : path(0).map(([x1, y1, x2, y2]) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="nl-idle"/>`).join('');
      const mx = bend ? (ax + cx - k * turn) / 2 : (ax + cx) / 2, my = F.y, ends = Object.entries(l.ends || {}).filter(([, q]) => q && 'rate' in q).map(([h, q]) => ` (${h}: ${star(`${l.id}.${h}.rate`)}${R(q.rate)})`).join('');
      const says = `link ${l.id}: ns-3 PointToPointChannel, the wire between the devices of ${a} and ${c}: ${R(l.rate)}, a one-way delay of ${R(l.delay)}${through.length ? `; ${through.join(', ')} ${through.length === 1 ? 'passes' : 'pass'} it` : '; no flow passes it'}.`;
      return `<g class="nl" data-link="${e(l.id)}" data-act="sysobj" data-id="link:${e(l.id)}"${o2.on === 'link:' + l.id ? ' data-on="1"' : ''}><title>${e(says)}</title>${inner(a, l, A, through)}${inner(c, l, C, through)}<g data-nk="channel">${lines}</g>${A.svg}${C.svg}
        ${(() => { const line = `${l.id} · ${star(`${l.id}.rate`)}${R(l.rate)}${ends} · ${star(`${l.id}.delay`)}${R(l.delay)}`, lw = Math.max(line.length * 6.7, 120) + 16;   // the link's words in a box of their own above its line (2026-11-22, the operator: borders for clarity)
          return `<g data-nk="channel"><rect class="nl-lab" x="${(mx - lw / 2).toFixed(1)}" y="${my - 47}" width="${lw.toFixed(1)}" height="33" rx="6"/><text x="${mx}" y="${my - 33}" text-anchor="middle" class="sv"><tspan class="sn2">${e(l.id)}</tspan> · ${star(`${l.id}.rate`)}${e(R(l.rate))}${e(ends)} · ${star(`${l.id}.delay`)}${e(R(l.delay))}</text><text x="${mx}" y="${my - 19}" text-anchor="middle" class="sv nl-k">point-to-point channel</text></g>`; })()}</g>`; };
    // a host: its frame and the builder's picture of it; on this page nothing in it is clicked, so the builder's words about clicking go, and each queue says what it is
    const qSays = Object.fromEntries(EV.netQueues(t).map(({ h, q, l, id, a }) => { const name = f => { const who = EV.netMembers(q, f); return who.length === 1 && who[0] === f ? f : `${f} (${who.join(' + ')})`; };
      return [id, `${EV.netDisc(q.kind)[0]} (ns-3 ${EV.netDisc(q.kind)[1]}) on ${h}'s side of link ${l.id}: ${star(`${a}.length`)}${q.length} packets${q.kind === 'scheduler' ? '; its parts ' + Object.entries(q.parts || {}).map(([f, v]) => `${name(f)} ${v}`).join(' : ') : ''}`]; }));
    const hostSvg = h => { const p = pos[h], q = P[h], nth = (t.hosts || []).findIndex(x => x.id === h);
      let s = q.svg.replace(/( · |: )click to set (it|its application)/g, '').replace(/<text[^>]*>policy not told to the AI<\/text>/g, '').replace(/class="nc-queue"/g, 'class="nc-queue nq"')
        .replace(/(<g data-queue="([^"]+)"[^>]*>)<title>[^<]*<\/title>/g, (m, g0, id) => `${g0}<title>${e(qSays[id] || id)}</title>`)
        .replace(/ data-obj="/g, ' data-act="sysobj" data-id="').replace(/data-sink="([^"]+)" class="nc-flow"/g, 'data-sink="$1" class="nc-flow" data-act="sysobj" data-id="sink:$1"').replace(new RegExp(`data-id="${(o2.on || '#').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"`, 'g'), m => `${m} data-on="1"`);
      if (!simple && !q.geo.rows && !q.geo.qs) s = s.replace(/(<text x="[\d.]+" y=")[\d.]+("[^>]*>(forwards only|no flow yet)<\/text>)/, '$152$2');   // a host that only forwards: its words above, clear of the lines through it
      return `<g class="nh" data-host="${e(h)}" data-act="sysobj" data-id="host:${e(h)}"${o2.on === 'host:' + h ? ' data-on="1"' : ''} transform="translate(${p.x},${p.y})"><title>${e(`${h}: ns-3 Node ${nth}, a computer${q.geo && q.geo.rows ? ': its applications, its sockets, its internet stack (IPv4)' : ': its internet stack (IPv4)'}${q.geo && q.geo.qs ? ' and its traffic control' : ''}`)}</title><rect class="nh-f" data-nk="node" x="0" y="0" width="${p.w}" height="${p.h}" rx="12"/>${s}</g>`; };
    const polT = pol ? `<text x="${W / 2}" y="${H - 8}" text-anchor="middle" class="sv" id="sy-pol"${o2.op ? ' data-by="operator"' : ''}>${e(o2.pol)}</text>` : '';
    return `<svg class="sy net net-schema${simple ? ' net-simple' : ''}" id="net-pic" viewBox="0 0 ${W} ${H}" width="${W}" style="max-width:100%;height:auto" role="img" aria-label="The network: ${e((t.hosts || []).length)} hosts, ${e(links.length)} links, ${e(flows.length)} flows">${Object.keys(pos).map(hostSvg).join('')}${links.map(linkSvg).join('')}${polT}</svg>`;
  },
  // the kinds of ns-3 object the network is made of, each with its sign (as drawn in the schema), how many there are, and its ns-3 class
  netKinds(b) {
    const t = EV.net(b), e = EV.e; if (!t) return ''; const flows = t.flows || [], hosts = t.hosts || [], links = t.links || [], qs = EV.netQueues(t), uniq = a => [...new Set(a)], n = (k, one, many) => `${k} ${k === 1 ? one : many}`;
    const tcp = uniq(flows.filter(f => f.kind === 'tcp').map(f => String(f.type))), apps = uniq(flows.map(f => EV.NET_APP[EV.netApp(f)][1])), discs = uniq(qs.map(x => EV.netDisc(x.q.kind)[1]));
    const sign = d => `<svg class="nk-s" viewBox="0 0 28 18" width="28" height="18" aria-hidden="true">${d}</svg>`;
    const items = [
      ['node', sign('<path d="M8 3h12v8H8zM11 15h6M14 11v4" class="nk-o"/>'), n(hosts.length, 'node', 'nodes'), 'Node', 'A computer. Each host of the network is one ns-3 Node: it holds the applications, the sockets, the internet stack and the devices.'],
      ['app', sign('<rect x="2" y="4" width="24" height="10" rx="5" class="nk-f"/>'), n(2 * flows.length, 'application', 'applications'), `${apps.join(', ')}${flows.length ? ', PacketSink' : ''}`, 'What makes and takes the traffic: on the sender of each flow the application that sends (OnOffApplication at a set rate, BulkSendApplication as fast as TCP allows), on its receiver a PacketSink.'],
      ['socket', sign('<rect x="3" y="4" width="22" height="10" rx="2.5" class="nk-o"/>'), n(2 * flows.length, 'socket', 'sockets'), uniq(flows.map(f => (f.kind === 'tcp' ? `TCP with ${tcp.map(x => x.replace(/^Tcp/, '')).join(', ')}` : 'UDP'))).join(', '), 'The end of a connection an application writes to or reads from: a UDP socket, or a TCP socket with its congestion control (ns-3 TcpSocketBase with a TcpCongestionOps such as TcpCubic).'],
      ['ip', sign('<rect x="9" y="1" width="10" height="16" rx="2" class="nk-o"/>'), n(hosts.length, 'internet stack', 'internet stacks'), 'IPv4 with UDP and TCP', 'ns-3 InternetStackHelper on each Node: Ipv4L3Protocol, which routes a packet to the device of its link, and UdpL4Protocol, TcpL4Protocol.'],
      ...(qs.length ? [['queue', sign('<path d="M4 4h20v10H4" class="nk-o"/><rect x="18" y="6" width="3" height="6" class="nk-f"/><rect x="13.5" y="6" width="3" height="6" class="nk-f"/>'), n(qs.length, 'queue disc', 'queue discs'), discs.join(', '), "Traffic control: where packets wait before the device sends them, and which waits first. A link's side without a described one still has a plain queue of 100 packets in front of its device (ns-3 FifoQueueDisc), which the picture does not draw; its drops are measured."]] : []),
      ['device', sign('<rect x="3" y="3" width="22" height="12" rx="3" class="nk-o"/>'), n(2 * links.length, 'device', 'devices'), 'PointToPointNetDevice', 'The network card at each end of a link: it sends at the link\'s rate, from a small transmit queue of its own.'],
      ['channel', sign('<path d="M2 9h24" class="nk-l"/>'), n(links.length, 'channel', 'channels'), 'PointToPointChannel', 'The wire between two devices: its delay is the time a bit takes from one end to the other.']];
    return `<p class="sm net-kinds" id="net-kinds"><span class="nk-h">Made of</span>${items.map(([k, s, count, cls, says]) => `<span class="nk-i" data-kind="${k}" tabindex="0" title="${e(says)}">${s}<b>${e(count)}</b> <span class="nk-c">${e(cls)}</span></span>`).join('')}</p>`;
  },
  // the ids of the parts a reader can click: host:<h>, flow:<f> (its application and socket on the sender), sink:<f> (its PacketSink), queue:<id>,
  // dev:<h>|<link> (the device of a host on a link), link:<l> (the channel)
  netParts(t) { const ids = []; (t.hosts || []).forEach(h => ids.push('host:' + h.id)); (t.flows || []).forEach(f => ids.push('flow:' + f.id, 'sink:' + f.id)); EV.netQueues(t).forEach(x => ids.push('queue:' + x.id));
    (t.links || []).forEach(l => { ids.push('link:' + l.id); l.between.forEach(h => ids.push(`dev:${h}|${l.id}`)); }); return ids; },
  netCard(b, id, sim) {
    const t = EV.net(b), e = EV.e, M = EV.M, kn = (b && b.knobs) || {}, R = v => TASK_VIEW._rate(String(v)), outs = new Set([...EV.outNames(), ...Object.keys((sim && sim.metrics) || {})]); if (!t || !id) return '';
    const [kind, rest] = [id.slice(0, id.indexOf(':')), id.slice(id.indexOf(':') + 1)], set = EV.netSettings(t), unit = a => (EV.SET_UNIT || {})[a] ? ' ' + EV.SET_UNIT[a] : '';
    const tried = a => { const vs = [...new Set(M.sims.filter(q => EV.seen(q.id) && q.params && q.params[a] != null).map(q => q.params[a]))]; return vs.length ? ` · this session tried ${vs.map(v => R(String(v).replace(/^Tcp/, ''))).join(', ')}` : ''; };
    const range = q => (q.choices ? q.choices.map(v => R(String(v).replace(/^Tcp/, ''))).join(', ') : `${R(q.min)} to ${R(q.max)}`);
    // a setting: its plain name, its value, the ns-3 attribute it is, and who decides it (the AI within a range, or the operator)
    // an object that is not in the brief's network was added by a simulation's change: its rate or type is the AI's choice, the rest is what every added object gets
    const base0 = (M && M.brief && M.brief.topology) || null, newLink = (M && M.brief && M.brief.structure && M.brief.structure.new_link) || {};
    const added = a => { const o = String(a).split('.')[0]; return !!base0 && ![...(base0.links || []), ...(base0.flows || [])].some(x => x.id === o); };
    const row = (name, a, v, attr) => { const k = kn[a]; return `<tr data-k="${e(a)}"><td class="oc-k">${e(name)}</td><td class="oc-v"><span class="oc-val"${k ? ' data-knob="1"' : ''}>${k ? '✦ ' : ''}${e(R(String(v).replace(/^Tcp/, '')) + unit(a))}</span>${attr ? ` <span class="sm oc-note">· ns-3 <code>${e(attr)}</code></span>` : ''}
      <span class="sm oc-note">· ${k ? `<span data-by="model" data-set="knob"><i class="sw"></i>the AI may change it</span>: ${e(range(k) + tried(a))}` : added(a) ? `<span data-by="model" data-set="fixed"><i class="sw"></i>${/\.(rate|type)$/.test(a) ? 'chosen by the AI when it added this' + (/\.rate$/.test(a) && newLink.rate_max && (t.links || []).some(x => x.id === a.split('.')[0]) ? ` (at most ${e(R(newLink.rate_max))} in this brief)` : '') : 'the value every added object gets'}</span>` : '<span data-by="operator" data-set="fixed"><i class="sw"></i>fixed by the operator</span>'}</span></td></tr>`; };
    const words = (name, text) => `<tr><td class="oc-k">${e(name)}</td><td class="oc-v"><span class="oc-val">${text}</span></td></tr>`;
    const measured = names => { const ms = names.filter(k => outs.has(k)); if (!ms.length) return ''; const plain = k => TH_DATA.PLAIN[k] || k;
      return `<tr class="oc-meas"><td class="oc-k">Measured here</td><td class="oc-v">${sim && sim.metrics ? ms.map(k => `<span class="oc-val">${e(plain(k))} ${e(EV.val(k, sim.metrics[k]))}</span>`).join(' · ') + ` <span class="sm oc-note">· in ${EV.link(sim.id)}</span>` : `<span class="oc-val">${e(ms.map(plain).join(', '))}</span> <span class="sm oc-note">· in every simulation: open one and its value stands here</span>`}</td></tr>`; };
    const head = (name, cls, where) => `<p class="oc-h"><b>${e(name)}</b><span class="oc-cls">ns-3 <code>${e(cls)}</code></span></p><p class="sm oc-where">${where}</p>`;
    const sw = f => `<i class="sw" style="background:${EV.netColor(t, f)}"></i>`, flowOf = f => (t.flows || []).find(x => x.id === f), linkOf = l => (t.links || []).find(x => x.id === l);
    const via = f => (EV.netPath(t, f) || []).map(([l]) => l).join(', '), sides = l => { const E = EV.netEnds(l); return l.between.map((h, i) => ({ h, i, E: E[h] || {} })); };
    let body = '';
    if (kind === 'host') { const h = rest, n = (t.hosts || []).findIndex(x => x.id === h), out = t.flows.filter(f => f.from === h), inn = t.flows.filter(f => f.to === h), ls = t.links.filter(l => l.between.includes(h)), qs = EV.netQueues(t).filter(x => x.h === h);
      body = head(h, `Node ${n}`, `a computer of the network · ${ls.length} ${ls.length === 1 ? 'link' : 'links'}${ls.length > 1 ? ' · it forwards what is not for it' : ''}`) + `<table class="oc-t" data-exact="1"><tbody>`
        + words('Applications', [...out.map(f => `${sw(f.id)}${e(f.id)} source (${e(EV.NET_APP[EV.netApp(f)][1])})`), ...inn.map(f => `${sw(f.id)}${e(f.id)} sink (PacketSink)`)].join(', ') || 'none: it only forwards')
        + words('Internet stack', 'IPv4 with UDP and TCP <span class="sm oc-note">· ns-3 <code>Ipv4L3Protocol</code>, <code>UdpL4Protocol</code>, <code>TcpL4Protocol</code></span>')
        + words('Devices', ls.map(l => `on ${e(l.id)} to ${e(l.between.find(x => x !== h))}`).join(', ') + ' <span class="sm oc-note">· ns-3 <code>PointToPointNetDevice</code></span>')
        + words('Traffic control', qs.length ? qs.map(x => `${e(EV.netDisc(x.q.kind)[0])} on ${e(x.l.id)} <span class="sm oc-note">· ns-3 <code>${e(EV.netDisc(x.q.kind)[1])}</code></span>`).join(', ') : 'none described: in front of each device a plain queue of 100 packets (ns-3 FifoQueueDisc), not drawn') + '</tbody></table>'; }
    else if (kind === 'flow' || kind === 'sink') { const f = flowOf(rest); if (!f) return ''; const app = EV.netApp(f), a = f.id;
      body = (kind === 'flow' ? head(`${f.id} source`, EV.NET_APP[app][1], `${sw(f.id)}on ${e(f.from)} · sends to ${e(f.to)} through ${e(via(f))} · on a ${f.kind.toUpperCase()} socket`)
        : head(`${f.id} sink`, 'PacketSink', `${sw(f.id)}on ${e(f.to)} · receives ${e(f.id)} from ${e(f.from)} · on a ${f.kind.toUpperCase()} socket`)) + `<table class="oc-t" data-exact="1"><tbody>`
        + words('Socket', f.kind === 'udp' ? 'UDP <span class="sm oc-note">· ns-3 <code>UdpSocket</code></span>' : 'TCP <span class="sm oc-note">· ns-3 <code>TcpSocketBase</code></span>')
        + (kind === 'flow' ? (f.kind === 'tcp' ? row('Congestion control', `${a}.type`, f.type, 'TcpL4Protocol · SocketType') : '') + (app === 'onoff' ? row('Rate', `${a}.rate`, f.rate, 'OnOffApplication · DataRate') + row('Packet size', `${a}.packet_bytes`, f.packet_bytes, 'PacketSize') : words('Rate', 'as fast as TCP allows: it always has data'))
          + EV.NET_TIMES.filter(p => p in f).map(p => row(EV.NET_TIME_SAYS[p][0], `${a}.${p}`, f[p], EV.NET_ATTR[p])).join('') : '')
        + measured([`${a}_goodput_bps`, f.kind === 'udp' ? `${a}_loss_frac` : `${a}_retrans`]) + '</tbody></table>'; }
    else if (kind === 'queue') { const x = EV.netQueues(t).find(q => q.id === rest); if (!x) return ''; const { q, h, l, a } = x, [plain, cls, does] = EV.netDisc(q.kind), passing = EV.netPassing(t)[x.id] || [];
      const name = p => { const who = EV.netMembers(q, p); return who.length === 1 && who[0] === p ? p : `${p} (${who.join(' + ')})`; };
      body = head(plain, cls, `on ${e(h)}'s side of ${e(l.id)}, before its device · ${e(does)}`) + `<table class="oc-t" data-exact="1"><tbody>`
        + row('Length', `${a}.length`, q.length, 'QueueDisc · MaxSize')
        + Object.entries(q.parts || {}).map(([p, v]) => row(`Part of ${name(p)}`, `${a}.parts.${p}`, v, 'FlowQueueDisc · part')).join('')
        + Object.entries(q.largest_rate || {}).map(([p, v]) => row(`Largest rate of ${p}`, `${a}.largest_rate.${p}`, v, 'FlowQueueDisc · largest rate')).join('')
        + words('Flows that wait in it', passing.map(f => `${sw(f)}${e(f)}`).join(', ') || 'none')
        + (q.kind === 'scheduler' ? words('How it divides the link', 'by the parts, divided by their sum; its policy is not told to the AI') : '')
        + measured(sides(l).filter(s => s.h === h).flatMap(s => (q.kind === 'scheduler' ? Object.keys(q.parts || {}).map(p => `${l.id}_drops_${p}`) : [s.i === 1 && sides(l).every(x => x.E.queue) ? `${l.id}_drops_back` : `${l.id}_drops`]))) + '</tbody></table>'; }
    else if (kind === 'dev') { const [h, lid] = rest.split('|'), l = linkOf(lid); if (!l) return ''; const s = sides(l).find(x => x.h === h); if (!s) return ''; const own = (l.ends || {})[h] || {}, other = l.between.find(x => x !== h);
      const at = p => (p in own ? `${l.id}.${h}.${p}` : `${l.id}.${p}`), val = p => (p in own ? own[p] : l[p]);
      body = head(`device of ${h} on ${l.id}`, 'PointToPointNetDevice', `the network card at ${e(h)}'s end of ${e(l.id)}, to ${e(other)}`) + `<table class="oc-t" data-exact="1"><tbody>`
        + row('Rate', at('rate'), val('rate'), 'PointToPointNetDevice · DataRate') + (val('mtu') != null ? row('Largest packet', at('mtu'), val('mtu'), 'NetDevice · Mtu') : '')
        + (val('device_queue') != null ? row('Transmit queue', at('device_queue'), val('device_queue'), 'TxQueue · MaxSize') : words('Transmit queue', '100 packets, the ns-3 default <span class="sm oc-note">· ns-3 <code>DropTailQueue</code></span>'))
        + (own.loss != null ? row('Loss', `${l.id}.${h}.loss`, own.loss, 'ReceiveErrorModel · ErrorRate') : '')
        + measured([s.i === 0 ? `${l.id}_util` : `${l.id}_util_back`, `${l.id}_lost_${h}`, ...(s.E.queue ? [] : [s.i === 1 || sides(l).some(x => x.E.queue) ? `${l.id}_drops_back` : `${l.id}_drops`])]) + '</tbody></table>'; }
    else if (kind === 'link') { const l = linkOf(rest); if (!l) return ''; const fl = (t.flows || []).filter(f => (EV.netPath(t, f) || []).some(([x]) => x === l.id));
      body = head(l.id, 'PointToPointChannel', `the wire between the devices of ${e(l.between[0])} and ${e(l.between[1])}`) + `<table class="oc-t" data-exact="1"><tbody>`
        + row('Rate', `${l.id}.rate`, l.rate, 'PointToPointNetDevice · DataRate (both ends)') + row('Delay', `${l.id}.delay`, l.delay, 'PointToPointChannel · Delay')
        + words('Flows that pass it', fl.map(f => `${sw(f.id)}${e(f.id)}`).join(', ') || 'none')
        + measured([`${l.id}_util`, `${l.id}_util_back`]) + '</tbody></table>'; }
    return body;
  },
  // the flows and the links in words (EV.netSide), folded under the schema: closed on a first visit, open in Full, remembered ("ev-networds")
  netWords(b) { const S = EV.s, t = EV.net(b), open = S.full || EV.store('ev-networds') === '1'; if (!t) return '';
    return `<details class="net-words" id="net-words"${open ? ' open' : ''}><summary><b>The flows and the links in words</b> <span class="sm">${(t.flows || []).length} flows, ${(t.links || []).length} ${(t.links || []).length === 1 ? 'link' : 'links'}: each application with its rate, each link with its rate, its delay and its queues</span><span class="cl noprint fl-btn" aria-hidden="true"><span class="fl-o">open</span><span class="fl-f">fold</span></span></summary>${EV.netSide(b)}</details>`; },
  // the earlier picture (boxes, lines and words), kept for a page where the builder's drawing could not be loaded
  netSvgPlain(b, o) {
    const t = EV.net(b), e = EV.e, kn = (b && b.knobs) || {}, R = v => TASK_VIEW._rate(String(v)), o2 = o || {}; if (!t) return '';
    const G = EV.netGeom(t), flows = t.flows || [], rowsOf = G.rowsOf, pos = G.pos, W = G.W, H = G.H;
    const star = k => (k in kn ? '✦ ' : ''), cy = h => pos[h].y + pos[h].h / 2, deg = {}; (t.links || []).forEach(l => l.between.forEach(h => { deg[h] = (deg[h] || 0) + 1; }));
    // links: a line between the two boxes' facing edges; its name, rate and delay above it; the queue on the side that has one
    const links = (t.links || []).map(l => { const [a, c] = l.between, E = G.ends[l.id]; if (!E) return ''; const { x1, y1, x2, y2 } = E;
      // the link's name stands nearer the host that has fewer links, where the lines are apart; its queue 30 px out from its host along the line
      const da = deg[a], dc = deg[c], at = da > dc ? 0.72 : dc > da ? 0.28 : 0.5, mx = x1 + (x2 - x1) * at, my = y1 + (y2 - y1) * at, len = Math.hypot(x2 - x1, y2 - y1) || 1, ux = (x2 - x1) / len, uy = (y2 - y1) / len;
      const through = flows.filter(f => (EV.netPath(t, f) || []).some(([id]) => id === l.id));
      const lines = through.length ? through.map((f, i) => { const d = (i - (through.length - 1) / 2) * 3.2; return `<line x1="${x1}" y1="${y1 + d}" x2="${x2}" y2="${y2 + d}" stroke="${EV.netColor(t, f.id)}" stroke-width="2.2" data-flow="${e(f.id)}"/>`; }).join('') : `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="nl-idle"/>`;
      // a mark for each described queue, on the side of the host that sends through it; under it its length and, of a scheduler, its parts (a part that several flows share names them)
      const qmark = EV.netQueues(t).filter(x => x.l === l).map(({ h, q, a: ad, id }) => { const atA = h === a, qx = atA ? x1 + 30 * ux : x2 - 30 * ux, qy = atA ? y1 + 30 * uy : y2 - 30 * uy, away = (atA ? ux : -ux) >= 0 ? 'start' : 'end', tx = qx + (away === 'start' ? -11 : 11);
        const name = f => { const who = EV.netMembers(q, f); return who.length === 1 && who[0] === f ? f : `${f} (${who.join(' + ')})`; };
        const parts = q.kind === 'scheduler' ? Object.entries(q.parts || {}).map(([f, v]) => `${star(`${ad}.parts.${f}`)}${name(f)} ${v}`).join(' : ') : '';
        return `<g class="nq" data-queue="${e(id)}">${q.kind === 'scheduler' ? `<circle cx="${qx}" cy="${qy}" r="11"/>` : `<rect x="${qx - 9}" y="${qy - 9}" width="18" height="18" rx="2"/>`}<text x="${tx}" y="${qy + 27}" text-anchor="${away}" class="sv">${e(q.kind === 'scheduler' ? 'scheduler' : 'queue')} · ${star(`${ad}.length`)}${e(q.length)} packets</text>${parts ? `<text x="${tx}" y="${qy + 41}" text-anchor="${away}" class="sv">${e(parts)}</text>` : ''}</g>`; }).join('');
      return `<g class="nl" data-link="${e(l.id)}">${lines}<text x="${mx}" y="${my - 21}" text-anchor="middle" class="sn">${e(l.id)}</text><text x="${mx}" y="${my - 8}" text-anchor="middle" class="sv">${star(`${l.id}.rate`)}${e(R(l.rate))} · ${star(`${l.id}.delay`)}${e(R(l.delay))}</text>${qmark}</g>`; }).join('');
    // hosts: a box with its name and one line for each flow it sends or receives
    const boxes = Object.keys(pos).map(h => { const p = pos[h], rows = rowsOf(h);
      const line = (f, i) => { const sends = f.from === h, y = p.y + 38 + 17 * i, what = f.kind === 'udp' ? `UDP ${star(`${f.id}.rate`)}${R(f.rate)}` : `TCP ${star(`${f.id}.type`)}${String(f.type).replace(/^Tcp/, '')}${EV.netApp(f) === 'onoff' ? ` · ${star(`${f.id}.rate`)}${R(f.rate)}` : ''}`;
        return `<g data-flow="${e(f.id)}"><circle cx="${p.x + 13}" cy="${y - 4}" r="4.5" fill="${EV.netColor(t, f.id)}"/><text x="${p.x + 23}" y="${y}" class="sv"><tspan class="sn2">${e(f.id)}</tspan> ${sends ? `→ ${e(f.to)} · ${e(what)}` : `← ${e(f.from)}`}</text></g>`; };
      return `<g class="nh" data-host="${e(h)}"><rect x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}" rx="9"/><text x="${p.x + 10}" y="${p.y + 17}" class="sn">${e(h)}</text><text x="${p.x + p.w - 8}" y="${p.y + 17}" text-anchor="end" class="sv">${rows.length ? '' : 'forwards only'}</text>${rows.length ? rows.map(line).join('') : ''}</g>`; }).join('');
    const pol = o2.pol ? `<text x="${W / 2}" y="${H - 8}" text-anchor="middle" class="sv" id="sy-pol"${o2.op ? ' data-by="operator"' : ''}>${e(o2.pol)}</text>` : '';
    return `<svg class="sy net" id="net-pic" viewBox="0 0 ${W} ${H}" width="${Math.min(W, o2.max || 1000)}" role="img" aria-label="The network: ${e((t.hosts || []).length)} hosts, ${e((t.links || []).length)} links, ${e(flows.length)} flows">${links}${boxes}${pol}</svg>`;
  },
  // the objects of the network in words, beside the picture: its flows and its links, a ✦ before what the AI may change
  netSide(b) {
    const t = EV.net(b), e = EV.e, kn = (b && b.knobs) || {}, R = v => TASK_VIEW._rate(String(v)), s = k => (k in kn ? '<span class="nk" title="The AI may change it">✦</span> ' : '');
    const flow = f => `<tr data-flow="${e(f.id)}"><td><i class="nf" style="background:${EV.netColor(t, f.id)}"></i><b>${e(f.id)}</b></td><td title="${e(`ns-3 ${EV.NET_APP[EV.netApp(f)][1]} on a ${f.kind.toUpperCase()} socket`)}">${e(EV.NET_APP[EV.netApp(f)][0])} · ${e(f.kind.toUpperCase())}</td><td>${e(f.from)} → ${e(f.to)}</td><td>${[EV.netApp(f) === 'onoff' ? `${s(`${f.id}.rate`)}${e(R(f.rate))} · ${s(`${f.id}.packet_bytes`)}${e(f.packet_bytes)}-byte packets` : 'always has data', f.kind === 'tcp' ? `${s(`${f.id}.type`)}${e(String(f.type).replace(/^Tcp/, ''))}` : ''].filter(Boolean).join(' · ')}</td></tr>`;
    const queue = ({ h, q, a }) => { const name = f => { const who = EV.netMembers(q, f); return who.length === 1 && who[0] === f ? e(f) : `${e(f)} (${e(who.join(' + '))}, one queue)`; };
      return `${e(q.kind === 'scheduler' ? 'scheduler' : q.kind === 'fifo' ? 'plain queue' : EV.netDisc(q.kind)[0])} on ${e(h)}'s side, ${s(`${a}.length`)}${e(q.length)} packets${q.kind === 'scheduler' ? ': ' + Object.entries(q.parts || {}).map(([f, v]) => `${s(`${a}.parts.${f}`)}${name(f)} ${e(v)}`).join(' : ') + (Object.keys(q.largest_rate || {}).length ? '; at most ' + Object.entries(q.largest_rate).map(([f, v]) => `${e(f)} ${e(R(v))}`).join(', ') : '') : ''}`; };
    // an end that states its own device: its rate and its transmit queue stand after the link's
    const dev = l => Object.entries(l.ends || {}).filter(([, x]) => x && ('rate' in x || 'device_queue' in x)).map(([h, x]) => ` · ${e(h)}'s device: ${[('rate' in x) ? `${s(`${l.id}.${h}.rate`)}${e(R(x.rate))}` : '', ('device_queue' in x) ? `${s(`${l.id}.${h}.device_queue`)}a transmit queue of ${e(x.device_queue)} packets` : ''].filter(Boolean).join(', ')}`).join('');
    const link = l => { const qs = EV.netQueues(t).filter(x => x.l === l); return `<tr data-link="${e(l.id)}"><td><b>${e(l.id)}</b></td><td>${e(l.between.join(' – '))}</td><td>${s(`${l.id}.rate`)}${e(R(l.rate))} · ${s(`${l.id}.delay`)}${e(R(l.delay))}${dev(l)}</td><td>${qs.length ? qs.map(queue).join('<br>') : 'a plain queue of 100 packets on each side'}</td></tr>`; };
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
document.getElementById('ev').addEventListener('toggle', ev => { if (ev.target.id === 'net-words' && !EV.s.full) EV.store('ev-networds', ev.target.open ? '1' : '0'); }, true);
Object.assign(EV, {
  // the names of the measures of the open session (its brief's outputs; the seven of the two-host set-up where none is recorded)
  outNames() { const M = EV.M, g = M && M.meta && M.meta.given; return Object.keys((g && g.outputs) || (M && M.brief && M.brief.outputs) || TH_DATA.PLAIN); },
  // which colour is which flow, in words, beside a chart
  flowsSay() { const t = EV.net(EV.M && EV.M.brief); return t ? 'each flow in its colour: ' + t.flows.map((f, i) => `<i class="sw" style="display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--series-${(i % 8) + 1})"></i> ${EV.e(f.id)}`).join(' · ') : 'UDP blue, TCP orange'; },
  // the network with some of its settings at other values (a session's knobs at their defaults; a simulation's own settings)
  netWith(t, values) {
    const c = JSON.parse(JSON.stringify(t)), have = EV.netSettings(c);
    for (const [addr, v] of Object.entries(values || {})) { if (!(addr in have)) continue; const [obj, ...rest] = addr.split('.'); let x = [...c.links, ...c.flows].find(q => q.id === obj), keys = rest;
      // l.<host>.…: what that end of the link states of its own (its device's rate and transmit queue, its queue)
      if (keys.length > 1 && x.between && x.between.includes(keys[0]) && (x.ends || {})[keys[0]]) { x = x.ends[keys[0]]; keys = keys.slice(1); }
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
  // a recommendation's changes to the network, in words, one phrase for each (2026-11-23, the operator: a report's network changes stand before its
  // settings); a queue removed and put back on the same side of the same link reads as one replacement
  editsAdvise(edits) { const out = [], es = (edits || []).filter(x => x && typeof x === 'object'), disc = k => (k === 'fifo' ? 'plain queue' : EV.netDisc(k || 'scheduler')[0]);
    for (let i = 0; i < es.length; i++) { const x = es[i], n = es[i + 1];
      if (x.do === 'remove' && x.kind === 'queue' && n && n.do === 'add_queue' && n.id === x.id && (!x.on || x.on === n.on)) { out.push(`replace the queue on ${n.on}'s side of link ${x.id} with a ${disc(n.kind)}`); i++; continue; }
      out.push(x.do === 'add_host' ? `add host ${x.id}` : x.do === 'add_link' ? `add link ${x.id} between ${x.from} and ${x.to}${x.rate ? ' (' + TASK_VIEW._rate(x.rate) + ')' : ''}` : x.do === 'add_flow' ? `add ${String(x.kind).toUpperCase()} flow ${x.id} from ${x.from} to ${x.to}`
        : x.do === 'add_queue' ? `put a ${disc(x.kind)} on ${x.on}'s side of link ${x.id}` : `remove ${x.kind === 'queue' ? 'the queue of link' : x.kind} ${x.id}${x.kind === 'queue' && x.on ? ` on ${x.on}'s side` : ''}`); }
    return out; },
  editsSay(edits) { return (edits || []).map(e => (e.do === 'add_host' ? `added host ${e.id}` : e.do === 'add_link' ? `added link ${e.id} between ${e.from} and ${e.to}${e.rate ? ' (' + TASK_VIEW._rate(e.rate) + ')' : ''}` : e.do === 'add_flow' ? `added ${String(e.kind).toUpperCase()} flow ${e.id} from ${e.from} to ${e.to}`
    : e.do === 'add_queue' ? `put a ${e.kind === 'fifo' ? 'plain queue' : EV.netDisc(e.kind || 'scheduler')[0]} on ${e.on}'s side of link ${e.id}` : `removed ${e.kind === 'queue' ? 'the queue of link' : e.kind} ${e.id}${e.kind === 'queue' && e.on ? ` on ${e.on}'s side` : ''}`)).join('; ') || 'nothing'; },
});
// a click on a blank place of the network's part (not on a part of the schema, not in a part's card, not in the words under it, not on a button or
// link) closes the card that is open, and "Made of" stands there again (2026-11-22, the operator)
document.addEventListener('click', ev => {
  const t = ev.target; if (!t || !t.closest || !EV.s || !EV.s.sysObj || !t.closest('#s-system .sy-row.sy-net')) return;
  if (t.closest('[data-act], #net-det.on, #net-words, a, button, input, select, label')) return;
  EV.s.sysObj = ''; EV.draw();
});

// Pointing at a kind in "Made of" lights every part of that kind in the schema, and pointing at a part of the schema lights its kind in "Made of" and
// every other part of that kind (2026-11-22, the operator: "When users hover over an object, highlight matching icons and vice versa"). Kinds: node,
// app, socket, ip (the internet stack), queue (traffic control), device, channel; the schema marks each part with data-nk, "Made of" each kind with data-kind.
EV.netLight = k => { document.querySelectorAll('.ev .nk-lit').forEach(x => x.classList.remove('nk-lit')); if (!k) return;
  document.querySelectorAll(`#net-pic [data-nk="${CSS.escape(k)}"], #net-kinds .nk-i[data-kind="${CSS.escape(k)}"]`).forEach(x => x.classList.add('nk-lit')); };
EV.netLightAt = el => { const t = el && el.closest && el.closest('#net-kinds .nk-i, #net-pic [data-nk]'), k = t ? t.dataset.kind || t.dataset.nk : null; if (k !== EV._nkLit) { EV._nkLit = k; EV.netLight(k); } };
document.addEventListener('mouseover', ev => EV.netLightAt(ev.target));
document.addEventListener('focusin', ev => EV.netLightAt(ev.target));

// A setting and its part of the network light together (2026-11-22, the operator: "We should also highlight matching elements among those when users
// hover over an object and detail is shown"): pointing at a part of the schema lights the rows of the settings that set it, wherever they stand on the
// page ("Who decides what" of the setting, the brief's card in the detail); pointing at such a row lights its part. A row says its setting in data-k:
// a flow's rate, packet size and times are its application's, its TCP type its socket's; a queue's length and parts its queue's; a link's delay its
// channel's; a link's rate, transmit queue, largest packet and loss its devices' (one device's own value: that device's)
EV.netPartsOf = key => {
  const t = EV.M && EV.net(EV.M.brief); if (!t || !key) return []; const q = s => [...document.querySelectorAll(s)], c = CSS.escape;
  const f = (t.flows || []).find(f => key.startsWith(f.id + '.')); if (f) return q(`#net-pic g.nc-flow[data-flow="${c(f.id)}"] [data-nk="${key === f.id + '.type' ? 'socket' : 'app'}"]`);
  const x = EV.netQueues(t).find(x => key === x.a || key.startsWith(x.a + '.')); if (x) return q(`#net-pic [data-queue="${c(x.id)}"]`);
  const l = (t.links || []).find(l => key.startsWith(l.id + '.')); if (!l) return [];
  const rest = key.slice(l.id.length + 1); if (rest === 'delay') return q(`#net-pic g.nl[data-link="${c(l.id)}"] [data-nk="channel"]`);
  const h = (l.between || []).find(h => rest.startsWith(h + '.'));
  return q(h ? `#net-pic g.nd[data-id="${c('dev:' + h + '|' + l.id)}"]` : `#net-pic g.nd[data-id$="${c('|' + l.id)}"]`);
};
EV.netKeyLight = (keys, parts) => {
  document.querySelectorAll('#ev .nk-row, #ev .nk-key').forEach(x => x.classList.remove('nk-row', 'nk-key'));
  (keys || []).forEach(k => document.querySelectorAll(`#ev tr[data-k="${CSS.escape(k)}"]`).forEach(r => r.classList.add('nk-row'))); (parts || []).forEach(p => p.classList.add('nk-key'));
};
document.addEventListener('mouseover', ev => {
  const t = ev.target; if (!t || !t.closest) return;
  const row = t.closest('#ev tr[data-k]');
  if (row) { const k = row.dataset.k; if (EV._nkRow !== 'r:' + k) { EV._nkRow = 'r:' + k; const parts = EV.netPartsOf(k); EV.netKeyLight(parts.length ? [k] : [], parts); } return; }
  if (t.closest('#net-pic [data-nk], #net-pic [data-id]')) {
    const keys = [...new Set([...document.querySelectorAll('#ev tr[data-k]')].map(r => r.dataset.k))].filter(k => EV.netPartsOf(k).some(p => p.contains(t)));
    const sig = 'p:' + keys.join(','); if (EV._nkRow !== sig) { EV._nkRow = sig; EV.netKeyLight(keys, []); } return; }
  if (EV._nkRow) { EV._nkRow = null; EV.netKeyLight([], []); }
});
