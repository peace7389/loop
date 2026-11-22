// The set-up page for a network the operator builds (TOPOLOGY.md, stage 4). Beside brief_editor.js, which sets up the
// two-host system; the set-up page shows one or the other (evidence_run.js).
//   - A palette of the kinds of object: host, link, UDP flow, TCP flow, queue / scheduler.
//   - Adding: press a kind and drag it over the picture. Every place where it can go is marked; the one nearest the
//     pointer shows an add sign and says what a release would add. Release there: it is added. Anywhere else: nothing.
//     A link and a flow need two hosts: the first by the drag, the second by a click (or a second drag) on a host.
//   - Removing: drag an object out of the picture; outside it a remove sign says what a release removes, with
//     everything that goes with it. Delete on the chosen object does the same.
//   - Undo and redo; and every add and remove from the keyboard (a kind's button, then Tab to a place, Enter).
// The network is the brief's "topology"; a setting is fixed (its value in the network) or left to the AI (a knob
// under its address). The harness checks the brief when it is saved (tools.check_brief): its reason is shown as it is.
const BRIEF_NET = {
  node: null, ctx: null, s: null, past: [], ahead: [],
  // the tools, in the groups of the palette (the layers of ns-3: nodes, what connects them, what sends, what makes packets wait)
  // What sends is an application, and the traffic takes its kind from it (2026-11-17, the operator: no separate "UDP flow" and "TCP flow"; the
  // connection should follow from the application). A link is the cable: it carries both kinds at once, so it has no kind of its own.
  GROUPS: [['Nodes', ['host']], ['Connections', ['link']], ['Applications', ['udp', 'tcp']], ['Traffic control', ['fifo', 'queue']]],
  ICON: { host: '<rect x="3" y="5" width="22" height="15" rx="3"/><path d="M9 24h10M14 20v4"/>', link: '<circle cx="5" cy="14" r="3.2"/><circle cx="23" cy="14" r="3.2"/><path d="M8.2 14h11.6"/>',
          udp: '<path d="M3 14h4M10 14h4M17 14h4" stroke="var(--series-1)" stroke-width="3"/><path d="M21 9l5 5-5 5" stroke="var(--series-1)"/>', tcp: '<path d="M3 14h18" stroke="var(--series-2)" stroke-width="3"/><path d="M21 9l5 5-5 5" stroke="var(--series-2)"/>',
          fifo: '<path d="M3 8h20v12H3"/><rect x="10" y="10.5" width="3" height="7" rx="1"/><rect x="14.5" y="10.5" width="3" height="7" rx="1"/><rect x="19" y="10.5" width="3" height="7" rx="1" opacity=".5"/>',
          queue: '<rect x="3" y="8" width="4" height="12" rx="1"/><rect x="9" y="8" width="4" height="12" rx="1"/><rect x="15" y="8" width="4" height="12" rx="1" opacity=".45"/><circle cx="24" cy="14" r="3.4"/>' },
  // [kind, name, a few words under the name, the sentence on hover]: the palette stays short enough to stand beside the picture
  KINDS: [['host', 'Host', 'a computer (ns-3 Node)', 'A computer; with more than one link it forwards'], ['link', 'Link', 'a cable and its two NICs', 'ns-3 PointToPointChannel with a PointToPointNetDevice, the NIC, on each of its two hosts. In ns-3 a net device is made together with its link, so it has no tool of its own: click the link to set each device'],
          ['udp', 'OnOff application', 'a constant rate', 'ns-3 OnOffApplication: sends packets at a constant rate. It opens a UDP socket; its card can make that a TCP socket. Drop it on the host that sends, then choose the host that receives'],
          ['tcp', 'BulkSend application', 'always has data', 'ns-3 BulkSendApplication: always has data to send, as fast as its TCP socket accepts (ns-3 has no such application for UDP). Drop it on the host that sends, then choose the host that receives'],
          ['fifo', 'Shared queue', 'one queue for all flows', 'ns-3 FifoQueueDisc, the queue disc of one net device: one queue for all the flows on that sending side of a link, first in, first out'], ['queue', 'Scheduler', 'its queues, a part for each', 'FlowQueueDisc, the queue disc this project adds to ns-3, on one net device: one or more queues and a part of the link for each. A flow has a queue to itself or shares one with other flows: its card says which']],
  TCP: ['TcpCubic', 'TcpNewReno', 'TcpLinuxReno', 'TcpBbr', 'TcpVegas', 'TcpBic'],
  RANGE: { rate: ['10Mbps', '10Gbps'], delay: ['10us', '10ms'], mtu: [576, 1500], device_queue: [1, 1000], length: [4, 1000], parts: [0.05, 4], largest_rate: ['10Mbps', '1Gbps'], packet_bytes: [64, 1400], duration: [2, 30], start: [0, 10], stop: [2, 12], on_time: [0.1, 5], off_time: [0, 5], max_bytes: [100000, 1000000000], loss: [0, 0.1] },
  CSS: `
.bn-seg { display: inline-flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; } .bn-seg button { border: 0; border-radius: 0; background: var(--surface-1); padding: 3px 10px; } .bn-seg button.on { background: var(--text-primary); color: var(--surface-0); font-weight: 700; }
.bn-detail { margin: 0 0 8px; } .bn-detail svg { display: block; height: auto; } .bn-detail .nc-flow, .bn-detail .nc-queue { cursor: pointer; } .bn-detail .nc-flow:hover rect, .bn-detail .nc-queue:hover .nc-qbox { stroke: var(--text-primary); stroke-width: 1.6; }
.bn-three { display: grid; grid-template-columns: 200px minmax(0, 1fr) minmax(260px, 400px); gap: 8px 14px; align-items: start; } @media (max-width: 1100px) { .bn-three { grid-template-columns: minmax(0, 1fr); } }
.bn-pal { border: 1px solid var(--border); border-radius: 12px; background: var(--surface-1); padding: 8px 8px 10px; } .bn-pal-h { margin: 0 2px 6px; font-weight: 700; font-size: var(--f-text); } .bn-pal-h .sm { font-weight: 400; display: block; }
.bn-group { margin-top: 6px; } .bn-group-h { margin: 0 2px 4px; font-size: var(--f-note); font-weight: 700; color: var(--text-muted); }
.bn-kind { display: grid; grid-template-columns: 28px minmax(0, 1fr); gap: 8px; align-items: center; width: 100%; margin: 0 0 4px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface-0); padding: 4px 8px; cursor: grab; touch-action: none; user-select: none; text-align: left; font: inherit; color: var(--text-primary); }
.bn-kind b { display: block; font-size: var(--f-sec); } .bn-kind span span { font-size: var(--f-note); color: var(--text-secondary); line-height: 1.25; display: block; } .bn-kind:hover, .bn-kind:focus-visible { border-color: var(--text-primary); background: var(--surface-1); box-shadow: 0 1px 4px rgba(0, 0, 0, .12); } .bn-kind:active { cursor: grabbing; } .bn-kind.on { outline: 2px solid var(--live); }
.bn-bar { display: flex; flex-wrap: wrap; gap: 6px 12px; align-items: center; margin: 0 0 6px; } .bn-bar .bn-hint { flex: 1 1 260px; } .bn-acts { display: flex; gap: 6px; align-items: center; } .bn-acts button { min-width: 30px; }
.bn-canvas { position: relative; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-1); min-height: 440px; overflow: hidden; touch-action: none; } .bn-canvas.over { border-color: var(--live); box-shadow: 0 0 0 2px color-mix(in srgb, var(--live) 30%, transparent); }
#bn-paper { cursor: grab; } #bn-paper.panning { cursor: grabbing; } .bn-empty { position: absolute; left: 0; right: 0; top: 46%; text-align: center; pointer-events: none; }
.bn-canvas svg text.nc-lab { font-size: 12px; fill: var(--text-primary); } .bn-canvas svg text.nc-b { font-weight: 700; } .bn-canvas .joint-element { cursor: move; } .bn-canvas .joint-element.nc-sel [joint-selector=body], .bn-canvas .joint-link.nc-sel [joint-selector=wrapper] { stroke: var(--text-primary); stroke-width: 3; } .bn-canvas .joint-link.nc-sel [joint-selector=wrapper] { stroke: color-mix(in srgb, var(--text-primary) 16%, transparent); stroke-width: 22; }
.bn-canvas .available-cell [joint-selector=body] { stroke: var(--live); stroke-width: 3; stroke-dasharray: 7 5; } .bn-canvas .nc-flow, .bn-canvas .nc-queue { cursor: pointer; } .bn-canvas .nc-flow:hover rect, .bn-canvas .nc-queue:hover .nc-qbox { stroke: var(--text-primary); stroke-width: 1.6; }
.bn-canvas .nc-flow.nc-sel rect, .bn-canvas .nc-queue.nc-sel .nc-qbox { stroke: var(--text-primary); stroke-width: 2.4; } .bn-canvas .joint-port circle:hover { fill: var(--live); }
#bn-band { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1; }
.bn-zone { position: absolute; transform: translate(-50%, -50%); border: 1.5px dashed var(--text-secondary); border-radius: 999px; background: var(--surface-1); color: var(--text-secondary); min-width: 26px; height: 26px; padding: 0 7px; font: inherit; font-size: var(--f-note); line-height: 22px; white-space: nowrap; cursor: pointer; opacity: .75; z-index: 2; }
.bn-zone.near, .bn-zone:focus-visible { border: 2px solid var(--live); background: var(--live); color: #fff; opacity: 1; font-weight: 700; z-index: 3; } .bn-zone .plus { font-weight: 700; } .bn-zone .lab { display: none; } .bn-zone.near .lab, .bn-zone:focus-visible .lab, .bn-zone:hover .lab { display: inline; }
.bn-ghost { position: fixed; z-index: 50; pointer-events: none; transform: translate(12px, 12px); border-radius: 8px; padding: 4px 9px; font-size: var(--f-note); background: var(--text-primary); color: var(--surface-0); max-width: 340px; }
.bn-ghost.add { background: var(--live); color: #fff; } .bn-ghost.rem { background: var(--critical); color: #fff; } .bn-say { min-height: 20px; margin: 6px 0 0; }
.bn-panels-h { margin: 12px 0 6px; } .bn-panels { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 8px; align-items: start; }
.bn-pc { border: 1px solid var(--border); border-radius: 10px; background: var(--surface-1); padding: 6px 10px 8px; min-width: 0; } .bn-pc-h { margin: 0 0 5px; font-size: var(--f-sec); cursor: pointer; } .bn-pc-h span { font-weight: 400; color: var(--text-secondary); font-size: var(--f-note); } .bn-pc-h:hover b { text-decoration: underline; }
.bn-pc .bn-row { grid-template-columns: 112px 22px minmax(0, 1fr); font-size: var(--f-sec); } .bn-pc .bn-row > span:first-child { color: var(--text-secondary); } .bn-fact { color: var(--text-primary); } .bn-ownrow { margin: -3px 0 2px; } .bn-ownrow button { justify-self: start; font-size: var(--f-note); padding: 0 6px; border-style: dashed; color: var(--text-secondary); white-space: nowrap; }
.bn-pc.hot { border-color: var(--live); box-shadow: 0 0 0 2px color-mix(in srgb, var(--live) 35%, transparent); background: color-mix(in srgb, var(--live) 7%, var(--surface-1)); }
.bn-canvas .joint-element.nc-hot [joint-selector=body], .bn-canvas .nc-flow.nc-hot rect, .bn-canvas .nc-queue.nc-hot .nc-qbox, .bn-detail .nc-flow.nc-hot rect, .bn-detail .nc-queue.nc-hot .nc-qbox { stroke: var(--live); stroke-width: 3; } .bn-canvas .joint-link.nc-hot [joint-selector=wrapper] { stroke: color-mix(in srgb, var(--live) 35%, transparent); }
.bn-card h5 { margin: 9px 0 3px; font-size: var(--f-note); font-weight: 700; color: var(--text-muted); } .bn-in { display: block; width: 100%; text-align: left; margin: 2px 0; font-weight: 400; } .bn-adds { margin: 4px 0 0; display: flex; flex-wrap: wrap; gap: 4px; } .bn-add { display: flex; flex-wrap: wrap; gap: 4px 6px; align-items: center; margin: 5px 0 0; padding: 5px 7px; border: 1px dashed var(--border); border-radius: 8px; font-size: var(--f-sec); } .bn-add select { flex: 1 1 90px; min-width: 0; }
.bn-card { border: 1px solid var(--border); border-radius: 10px; background: var(--surface-1); padding: 8px 12px; } .bn-card h4 { margin: 0 0 6px; font-size: var(--f-text); } .bn-row { display: grid; grid-template-columns: 128px 30px minmax(0, 1fr); gap: 4px 8px; align-items: center; margin: 3px 0; }
.bn-row input[type=text] { width: 100%; box-sizing: border-box; } .bn-row .tri { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; } .bn-row small { color: var(--text-secondary); font-size: var(--f-note); } .bn-row .bn-attr { display: block; line-height: 1.2; overflow-wrap: anywhere; } .bn-who { border: 1px solid var(--border); border-radius: 6px; background: var(--surface-0); cursor: pointer; font: inherit; height: 24px; }
.bn-row.bn-set, .bn-pc .bn-row.bn-set { grid-template-columns: minmax(0, 1fr) auto; gap: 3px 8px; padding: 4px 6px 5px; margin: 3px -6px; border-left: 3px solid transparent; border-radius: 6px; align-items: start; }
.bn-row.bn-set[data-decides=model] { border-left-color: var(--bt-model); background: color-mix(in srgb, var(--by-model) 7%, transparent); }
.bn-set .bn-val { grid-column: 1 / -1; display: block; min-width: 0; } .bn-set .bn-val select { max-width: 100%; }
.bn-seg { display: inline-flex; border: 1px solid var(--border); border-radius: 999px; overflow: hidden; background: var(--surface-0); align-self: start; }
.bn-seg .bn-who { border: 0; border-radius: 0; height: 22px; padding: 0 8px 0 6px; font-size: var(--f-note); display: inline-flex; align-items: center; background: transparent; color: var(--text-secondary); white-space: nowrap; }
.bn-seg .bn-who + .bn-who { border-left: 1px solid var(--border); } .bn-seg .bn-who:not(.on):hover { background: var(--surface-1); color: var(--text-primary); }
.bn-seg .bn-who.on { color: var(--text-primary); font-weight: 600; cursor: default; } .bn-seg .bn-who.on[data-who=operator] { background: color-mix(in srgb, var(--by-operator) 20%, var(--surface-1)); }
.bn-seg .bn-who.on[data-who=model] { background: color-mix(in srgb, var(--by-model) 20%, var(--surface-1)); } .bn-seg .bn-who:not(.on) i.sw { opacity: .55; }
.bn-conds { margin-top: 2px; } .bn-cond { display: grid; grid-template-columns: 40px minmax(150px, 280px) 104px 96px 44px 28px; gap: 4px 6px; align-items: center; margin: 5px 0; } .bn-cond select, .bn-cond input { width: 100%; box-sizing: border-box; min-width: 0; }
.bn-cond .bn-cond-says { grid-column: 2 / -1; } .bn-cond .bn-cond-says code { font-size: inherit; } .bn-cond button[data-cond-rm] { height: 26px; padding: 0; } .bn-cond .bn-cond-u { color: var(--text-secondary); }
.bn-row .tri .bn-tri { display: block; font-weight: 400; min-width: 0; } .bn-row .tri .bn-tri small { display: block; } .bn-list tr:has(td[data-decides=model]), .bn-list tr:has(.bn-seg[data-decides=model]) { background: color-mix(in srgb, var(--by-model) 7%, transparent); }
.bn-bad { color: var(--critical); } .bn-list td { padding: 2px 10px 2px 0; vertical-align: top; }`,
  DEFAULT: { hosts: [{ id: 'sender' }, { id: 'receiver' }],
             links: [{ id: 'l1', between: ['sender', 'receiver'], rate: '1Gbps', delay: '50us', mtu: 1500, device_queue: 10, queue: { on: 'sender', kind: 'scheduler', length: 100, parts: { udp: 0.5, tcp: 0.5 }, largest_rate: {} } }],
             flows: [{ id: 'udp', kind: 'udp', from: 'sender', to: 'receiver', rate: '2Gbps', packet_bytes: 1400 }, { id: 'tcp', kind: 'tcp', from: 'sender', to: 'receiver', type: 'TcpCubic' }] },

  mount(host, ctx) {
    const N = BRIEF_NET; N.ctx = ctx;
    if (!document.getElementById('bn-css')) { const st = document.createElement('style'); st.id = 'bn-css'; st.textContent = N.CSS; document.head.appendChild(st); }
    if (!N.node) {
      N.node = document.createElement('div'); N.node.className = 'be bn'; N.s = N.fresh(JSON.parse(JSON.stringify(N.DEFAULT)));
      N.node.addEventListener('pointerdown', N.down); N.node.addEventListener('mouseover', N.over); N.node.addEventListener('mouseleave', () => N.hot([])); N.node.addEventListener('click', N.click); N.node.addEventListener('input', N.input); N.node.addEventListener('change', N.input);
      document.addEventListener('keydown', N.key);  // on the document: a click on the picture chooses an object without giving the form the focus, and Delete must still reach it
      window.addEventListener('pointermove', N.move); window.addEventListener('pointerup', N.up);
    }
    if (N.node.parentNode !== host) { host.appendChild(N.node); N.draw(); } else N.paint();
  },
  fresh(t) { return { t, knobs: {}, id: '', description: '', descAuto: true, goal: 'open', measure: '', direction: 'max', conds: '', tolerance: '', sims: '40', per: '12', duration: '10', seed: '1', sel: null, pos: {}, tcpInitCwnd: '', tcpBufBytes: '', tcpSack: '', tcpTimestamps: '', tcpDelAck: '', placing: null, pending: null, drag: null, msg: null, busy: '', base: '', structure: false, most: { hosts: '', links: '', flows: '' }, locked: {} }; },

  // ---- the network as data
  newId(prefix) { const N = BRIEF_NET, t = N.s.t, all = new Set([...t.hosts, ...t.links, ...t.flows].map(x => x.id).concat(EV.netQueues(t).flatMap(x => Object.keys(x.q.classes || {})))); let i = 1; while (all.has(prefix + i)) i++; return prefix + i; },
  linkOf(id) { return BRIEF_NET.s.t.links.find(l => l.id === id); },
  // A described queue is named as the harness names it as an object: by its link (the older form: the link's one queue, with "on") or by link.host
  // (a queue of that end, in the link's "ends"). A link may have one on each of its two sending sides (2026-11-17, the operator: as in ns-3).
  queues(t) { return EV.netQueues(t || BRIEF_NET.s.t); },
  qOf(id, t) { return BRIEF_NET.queues(t).find(x => x.id === id) || null; },
  // which flows pass each described queue (they are sent on that link by the queue's host): {queue name: [flow ids]}
  passing(t) { const qs = EV.netQueues(t), out = {}; qs.forEach(x => { out[x.id] = []; }); t.flows.forEach(f => (EV.netPath(t, f) || []).forEach(([l, from]) => { const x = qs.find(y => y.l.id === l && y.h === from); if (x) out[x.id].push(f.id); })); return out; },
  // After every change (as network.sync in the harness): a scheduler has a part for exactly the flows that pass it. A flow that is new there gets a
  // queue of its own; a flow that no longer passes leaves its queue; a shared queue (a class) that holds no flow any more goes, with its part.
  // A knob whose setting is gone is dropped.
  sync() {
    const N = BRIEF_NET, s = N.s, t = s.t, through = N.passing(t);
    N.queues(t).forEach(({ q, id }) => { if (q.kind !== 'scheduler') { delete q.classes; return; } const flows = through[id], old = q.parts || {}, vals = Object.values(old), fill = vals.length ? Math.round(1000 * vals.reduce((a, b) => a + b, 0) / vals.length) / 1000 : 0.5, classes = {};
      Object.entries(q.classes || {}).forEach(([name, fl]) => { const left = fl.filter(f => flows.includes(f)); if (left.length && name in old) classes[name] = left; });
      const held = new Set(Object.values(classes).flat()), parts = {};
      Object.keys(old).forEach(k => { if (k in classes || (flows.includes(k) && !held.has(k))) parts[k] = old[k]; }); flows.forEach(f => { if (!held.has(f) && !(f in parts)) parts[f] = fill; });
      q.parts = parts; q.largest_rate = Object.fromEntries(Object.entries(q.largest_rate || {}).filter(([f]) => f in parts)); if (Object.keys(classes).length) q.classes = classes; else delete q.classes; });
    const have = EV.netSettings(t); Object.keys(s.knobs).forEach(k => { if (!(k in have) && k !== 'duration') delete s.knobs[k]; });
    const outs = Object.keys(N.outputs(t)); if (!outs.includes(s.measure)) s.measure = outs.find(o => /_goodput_bps$/.test(o)) || outs[0] || '';
    if (s.sel && !N.find(s.sel)) s.sel = null;
  },
  find(sel) { const N = BRIEF_NET, t = N.s.t, [kind, id] = sel || []; return kind === 'host' ? t.hosts.find(h => h.id === id) : kind === 'link' ? t.links.find(l => l.id === id) : kind === 'flow' ? t.flows.find(f => f.id === id) : kind === 'queue' ? (N.qOf(id) || {}).q : null; },
  // the measures of the network, as harness/network.py names them
  outputs(t) { return Object.fromEntries(EV.netOutNames(t).map(k => [k, 1])); },
  // a described queue taken out of a network (the side is then a plain queue of 100 packets again)
  dropQueue(t, id) { const [lid, h] = id.split('.'), l = t.links.find(x => x.id === lid); if (!l) return;
    if (!h) { delete l.queue; return; } const E = l.ends || {}; if (E[h]) { delete E[h].queue; if (!Object.keys(E[h]).length) delete E[h]; } if (!Object.keys(E).length) delete l.ends; },
  // what goes with an object when it is removed: [[kind, id], ...] (the object itself first)
  deps(kind, id) {
    const N = BRIEF_NET, t = JSON.parse(JSON.stringify(N.s.t)), gone = [[kind, id]];
    if (kind === 'host') { t.links.filter(l => l.between.includes(id)).forEach(l => gone.push(['link', l.id])); t.hosts = t.hosts.filter(h => h.id !== id); t.links = t.links.filter(l => !l.between.includes(id)); t.flows.filter(f => f.from === id || f.to === id).forEach(f => gone.push(['flow', f.id])); t.flows = t.flows.filter(f => f.from !== id && f.to !== id); }
    if (kind === 'link') t.links = t.links.filter(l => l.id !== id);
    if (kind === 'flow') t.flows = t.flows.filter(f => f.id !== id);
    if (kind === 'queue') N.dropQueue(t, id);
    t.flows.filter(f => !EV.netPath(t, f)).forEach(f => { gone.push(['flow', f.id]); }); t.flows = t.flows.filter(f => EV.netPath(t, f));  // a flow that has no way any more goes too
    return { gone, t };
  },
  change(fn) { const N = BRIEF_NET, s = N.s; N.past.push(JSON.stringify({ t: s.t, knobs: s.knobs })); if (N.past.length > 50) N.past.shift(); N.ahead = []; fn(); N.sync(); s.msg = null; N.draw(); },
  step(from, to) { const N = BRIEF_NET, s = N.s; if (!from.length) return; to.push(JSON.stringify({ t: s.t, knobs: s.knobs })); const o = JSON.parse(from.pop()); s.t = o.t; s.knobs = o.knobs; s.placing = s.pending = null; N.sync(); N.draw(); },
  remove(kind, id) { const N = BRIEF_NET, d = N.deps(kind, id); N.change(() => { N.s.t = d.t; N.s.sel = null; }); },
  add: {
    host(at) { const N = BRIEF_NET, id = N.newId('h'); at = at || NETC.center(); if (at) N.s.pos[id] = { x: Math.round(at.x - 110), y: Math.round(at.y - 60) }; N.change(() => { N.s.t.hosts.push({ id }); N.s.sel = ['host', id]; }); },  // at: where it was dropped, in the picture
    link(a, b) { const N = BRIEF_NET, id = N.newId('l'); N.change(() => { N.s.t.links.push({ id, between: [a, b], rate: '1Gbps', delay: '50us', mtu: 1500, device_queue: 10 }); N.s.sel = ['link', id]; }); },
    flow(kind, from, to) { const N = BRIEF_NET, id = N.newId(kind === 'udp' ? 'u' : 't'); N.change(() => { N.s.t.flows.push(kind === 'udp' ? { id, kind, from, to, rate: '100Mbps', packet_bytes: 1400 } : { id, kind, from, to, type: 'TcpCubic' }); N.s.sel = ['flow', id]; }); },
    // an application on host `from` that sends to host `to`; where no link leads there yet, a link between the two is added with it (one step, one undo)
    app(kind, from, to) { const N = BRIEF_NET, id = N.newId(kind === 'udp' ? 'u' : 't'), need = !EV.netPath(N.s.t, { from, to }), lid = need ? N.newId('l') : null;
      N.change(() => { if (need) N.s.t.links.push({ id: lid, between: [from, to], rate: '1Gbps', delay: '50us', mtu: 1500, device_queue: 10 });
        N.s.t.flows.push(kind === 'udp' ? { id, kind, from, to, rate: '100Mbps', packet_bytes: 1400 } : { id, kind, from, to, type: 'TcpCubic' }); N.s.sel = ['flow', id]; }); },
    // kind fifo: one queue shared by all the flows; else a scheduler (a queue and a part for each flow). The first queue of a link is written the
    // older way (its addresses are <link>.queue.…, as in every brief so far); one on the other side goes into the link's "ends" (<link>.<host>.queue.…)
    queue(link, on, kind) { const N = BRIEF_NET; N.change(() => { const l = N.linkOf(link), q = kind === 'fifo' ? { kind: 'fifo', length: 100 } : { kind: 'scheduler', length: 100, parts: {}, largest_rate: {} }, first = !N.queues().some(x => x.l === l);
      if (first) l.queue = { on, ...q }; else { l.ends = l.ends || {}; l.ends[on] = { ...(l.ends[on] || {}), queue: q }; } N.s.sel = ['queue', first ? link : `${link}.${on}`]; }); },
    // a device of a link given a value of its own (rate, device_queue), or back to the link's: the two devices of a link need not be alike
    own(link, host, prop) { const N = BRIEF_NET; N.change(() => { const l = N.linkOf(link), E = l.ends = l.ends || {}, x = E[host] = E[host] || {};
      if (prop in x) { delete x[prop]; if (!Object.keys(x).length) delete E[host]; } else x[prop] = prop === 'loss' ? 0.01 : l[prop]; if (!Object.keys(E).length) delete l.ends; }); },
    // a time of a flow's application (start, stop, the on and off periods together, a byte limit): stated with the value the program has (so that nothing changes by stating it), or left to the program again
    time(flow, prop) { const N = BRIEF_NET; N.change(() => { const f = N.s.t.flows.find(q => q.id === flow), end = 2 + (Number(N.s.duration) || 10); if (!f) return;
      if (prop === 'on_time') { if ('on_time' in f) { delete f.on_time; delete f.off_time; } else { f.on_time = 1; f.off_time = 1; } return; }
      if (prop in f) delete f[prop]; else f[prop] = prop === 'start' ? 1 : prop === 'stop' ? end : 1000000; }); },
    // in which queue of a scheduler a flow waits: one of its own ('~own'), a new one that others can join ('~new'), or a shared one that stands (its name)
    queueOf(qid, flow, where) { const N = BRIEF_NET; N.change(() => { const q = N.qOf(qid).q, cl = q.classes = q.classes || {}, was = Object.keys(cl).find(n => cl[n].includes(flow)), part = was ? q.parts[was] : q.parts[flow];
      if (was) cl[was] = cl[was].filter(f => f !== flow); else { delete q.parts[flow]; if (q.largest_rate) delete q.largest_rate[flow]; }
      if (where === '~new') { const n = N.newId('q'); cl[n] = [flow]; q.parts[n] = part ?? 0.5; } else if (where === '~own') q.parts[flow] = part ?? 0.5; else if (cl[where]) cl[where].push(flow); }); },
  },
  // A value that was just finished draws the form again a moment later: by then the field the reader clicked next has the focus, and draw() gives it
  // back to that same field of the new form (before, the form was drawn again under the click and the field that was clicked lost the focus).
  soon() { const N = BRIEF_NET; clearTimeout(N._soon); N._soon = setTimeout(() => N.draw(), 0); },
  // an object of the picture was chosen (or, with no kind, nothing is): its card beside the picture, its mark in it
  pick(kind, id) { const N = BRIEF_NET; if (!N.s || N.s.placing || N.s.pending) return; N.s.sel = kind ? [kind, id] : null; const side = N.node.querySelector('#bn-side'); if (side) side.innerHTML = N.card(); N.paint(); },
  focusZone() { const N = BRIEF_NET; if (N.viaKey) { const z = N.node.querySelector('.bn-zone'); if (z) z.focus(); } },
  says(kind, id) { const [l, h] = String(id).split('.'); return kind === 'queue' ? `the queue of link ${l}${h ? ` on ${h}'s side` : ''}` : `${kind} ${id}`; },

  // ---- where an object of a kind can go now: [{ key, x, y (the picture's units), label, go() }]
  zones() {
    const N = BRIEF_NET, s = N.s, t = s.t, G = NETC.geom(), mid = h => ({ x: G.pos[h].x + G.pos[h].w / 2, y: G.pos[h].y + G.pos[h].h / 2 }), kind = s.placing, p = s.pending;
    const linked = (a, b) => t.links.some(l => l.between.includes(a) && l.between.includes(b)), hosts = t.hosts.map(h => h.id);
    if (p && p.kind === 'link') return hosts.filter(h => h !== p.from && !linked(h, p.from)).map(h => ({ key: 'to-' + h, ...mid(h), label: `link ${p.from} – ${h}`, go: () => { s.pending = s.placing = null; N.add.link(p.from, h); } }));
    if (p) return hosts.filter(h => h !== p.from).map(h => ({ key: 'to-' + h, ...mid(h), label: `it sends to ${h}${EV.netPath(t, { from: p.from, to: h }) ? '' : ' (a link is added too)'}`, go: () => { s.pending = s.placing = null; N.add.app(p.kind, p.from, h); } }));
    if (kind === 'host') return [{ key: 'new-host', x: G.W / 2, y: 22, label: 'a new host', anywhere: true, go: ev => { s.placing = null; N.add.host(ev && ev.clientX != null && ev.type !== 'click' ? NETC.at(ev) : null); } }];
    if (kind === 'link') return hosts.filter(h => hosts.some(o => o !== h && !linked(h, o))).map(h => ({ key: 'from-' + h, ...mid(h), label: `a link from ${h}`, go: () => { s.pending = { kind: 'link', from: h }; N.draw(); N.focusZone(); } }));
    if (kind === 'udp' || kind === 'tcp') return hosts.filter(() => hosts.length > 1).map(h => ({ key: 'from-' + h, ...mid(h), label: `${kind === 'udp' ? 'an OnOff' : 'a BulkSend'} application on ${h}`, go: () => { s.pending = { kind, from: h }; N.draw(); N.focusZone(); } }));
    if (kind === 'queue' || kind === 'fifo') return t.links.filter(l => G.ends[l.id]).flatMap(l => { const E = G.ends[l.id], len = Math.hypot(E.x2 - E.x1, E.y2 - E.y1) || 1, ux = (E.x2 - E.x1) / len, uy = (E.y2 - E.y1) / len, has = EV.netEnds(l);
      return [[E.a, E.x1 + 30 * ux, E.y1 + 30 * uy], [E.c, E.x2 - 30 * ux, E.y2 - 30 * uy]].filter(([h]) => !has[h].queue).map(([h, x, y]) => ({ key: `q-${l.id}-${h}`, x, y, label: `a ${kind === 'fifo' ? 'shared queue' : 'scheduler'} on ${h}'s side of ${l.id}`, go: () => { s.placing = null; N.add.queue(l.id, h, kind === 'fifo' ? 'fifo' : 'scheduler'); } })); });
    return [];
  },

  // ---- what cannot be saved, said in words (the harness checks again when the brief is saved)
  // The conditions of a given aim. The brief holds each as a line the harness reads ("fb_loss_frac <= 0.1"); the form shows a line of that shape as a row:
  // a measure by its plain name, a comparison in words, a number in the unit a person uses (Mbps for bits per second, per cent for a part). A line
  // of another shape (written by hand in a saved brief) stays a text field of its own. s.conds stays the one place they are kept.
  COND_OPS: [['<=', 'at most'], ['>=', 'at least'], ['<', 'below'], ['>', 'above']],
  condUnit: m => (/_bps$/.test(m) ? ['Mbps', 1e6] : /(_loss_frac|_util|_util_back)$/.test(m) ? ['%', 0.01] : ['', 1]),
  condRows() { return String(BRIEF_NET.s.conds || '').split('\n').map(c => c.trim()).filter(Boolean).map(line => { const m = /^([A-Za-z_][A-Za-z0-9_]*)\s*(<=|>=|<|>)\s*(-?[0-9.]+(?:[eE][-+]?[0-9]+)?)$/.exec(line); return m ? { measure: m[1], op: m[2], raw: Number(m[3]) } : { text: line }; }); },
  condSet(rows) { BRIEF_NET.s.conds = rows.map(r => (r.text != null ? r.text : `${r.measure} ${r.op} ${r.raw}`)).join('\n'); },
  condShown: r => +(r.raw / BRIEF_NET.condUnit(r.measure)[1]).toPrecision(10),
  condNew(outs) { const N = BRIEF_NET, used = new Set(N.condRows().map(r => r.measure)), m = outs.find(o => /_loss_frac$/.test(o) && !used.has(o)) || outs.find(o => o !== N.s.measure && !used.has(o)) || outs[0];
    return { measure: m, op: /_bps$/.test(m) ? '>=' : '<=', raw: /_bps$/.test(m) ? 100e6 : /(_loss_frac|_util|_util_back)$/.test(m) ? 0.01 : 0 }; },
  condsHtml(outs) {
    const N = BRIEF_NET, e = EV.e, rows = N.condRows(), plain = k => TH_DATA.PLAIN[k] || k;
    const row = (r, i) => (r.text != null ? `<div class="bn-cond bn-cond-raw" data-cond="${i}"><span class="sm">${i ? 'and' : 'while'}</span><input type="text" data-cond-f="${i}:text" value="${e(r.text)}" aria-label="Condition ${i + 1}, as written" style="grid-column:2 / 6"><button type="button" data-cond-rm="${i}" title="Remove this condition" aria-label="Remove condition ${i + 1}">×</button><span class="sm bn-cond-says">written by hand: kept as it is, and read by the harness as it stands</span></div>`
      : (([unit]) => `<div class="bn-cond" data-cond="${i}"><span class="sm">${i ? 'and' : 'while'}</span><select data-cond-f="${i}:measure" aria-label="Condition ${i + 1}: the measure">${(outs.includes(r.measure) ? outs : [r.measure, ...outs]).map(k => `<option value="${e(k)}"${k === r.measure ? ' selected' : ''}>${e(plain(k))}${outs.includes(k) ? '' : ' (not measured in this network)'}</option>`).join('')}</select>
        <select data-cond-f="${i}:op" aria-label="Condition ${i + 1}: the comparison">${N.COND_OPS.map(([o, w]) => `<option value="${e(o)}"${o === r.op ? ' selected' : ''}>${w}</option>`).join('')}</select><input type="text" data-cond-f="${i}:value" value="${e(N.condShown(r))}" aria-label="Condition ${i + 1}: the number" inputmode="decimal"><span class="bn-cond-u">${e(unit)}</span>
        <button type="button" data-cond-rm="${i}" title="Remove this condition" aria-label="Remove condition ${i + 1}">×</button><span class="sm bn-cond-says" data-cond-says="${i}">${N.condSays(r)}</span></div>`)(N.condUnit(r.measure)));
    return `<div class="bn-conds" id="bn-conds" style="grid-column:1/-1"><b>Conditions</b> <small>what must hold while the target is made as ${N.s.direction === 'min' ? 'small' : 'large'} as possible. ${rows.length ? 'All of them must hold.' : 'None yet: any setting counts.'}</small>${rows.map(row).join('')}
      <div><button type="button" class="cl" id="bn-cond-add" title="One more condition: choose its measure, the comparison and the number">+ add a condition</button></div></div>`;
  },
  // a row in a sentence, and beside it the line the harness checks
  condSays(r) { const N = BRIEF_NET, [unit] = N.condUnit(r.measure), w = (N.COND_OPS.find(q => q[0] === r.op) || [])[1] || r.op;
    return `reads: ${EV.e(TH_DATA.PLAIN[r.measure] || r.measure)} ${w} ${EV.e(N.condShown(r))}${unit ? ' ' + EV.e(unit) : ''} · the harness checks: <code>${EV.e(`${r.measure} ${r.op} ${r.raw}`)}</code>`; },
  // the description follows the network while the operator has not written one of their own (descAuto): nothing has to be typed before a session can start
  syncDesc() { const N = BRIEF_NET, s = N.s; if (s.descAuto) s.description = N.describe();
    // a given aim always has a target the network measures: the one the form shows (it showed the first measure while holding none, and the brief was then refused)
    if (s.goal === 'given') { const outs = Object.keys(N.outputs(s.t)); if (!outs.includes(s.measure)) s.measure = outs.find(o => /_goodput_bps$/.test(o)) || outs[0] || ''; } },
  problems() {
    const N = BRIEF_NET, s = N.s, t = s.t, bad = []; N.syncDesc();
    if (t.hosts.length < 2 || !t.links.length || !t.flows.length) bad.push('A network needs at least two hosts, one link and one flow.');
    const bf = N.node && N.node.querySelector('#bn-flags input[data-k=budget]'), start = String(bf ? bf.value : (EV.nw || {}).budget || '').trim();
    if (start && /^\d+$/.test(String(s.sims).trim()) && Number(start) > Number(s.sims)) bad.push(`Block 7 allows ${start} simulations at the start, more than the limit of ${String(s.sims).trim()} in block 5 (“Simulations in all”). Lower it, or empty the field to start with the limit.`);
    t.hosts.filter(h => !t.links.some(l => l.between.includes(h.id))).forEach(h => bad.push(`Host ${h.id} has no link.`));
    t.flows.forEach(f => { const adj = {}; t.hosts.forEach(h => { adj[h.id] = []; }); t.links.forEach(l => { adj[l.between[0]].push(l.between[1]); adj[l.between[1]].push(l.between[0]); });
      const dist = { [f.from]: 0 }, ways = { [f.from]: 1 }; let fr = [f.from]; while (fr.length) { const nx = []; fr.forEach(h => adj[h].forEach(o => { if (!(o in dist)) { dist[o] = dist[h] + 1; ways[o] = ways[h]; nx.push(o); } else if (dist[o] === dist[h] + 1) ways[o] += ways[h]; })); fr = nx; }
      if (!(f.to in dist)) bad.push(`Flow ${f.id} has no way from ${f.from} to ${f.to}.`); else if (ways[f.to] > 1) bad.push(`Flow ${f.id} has ${ways[f.to]} equally short ways from ${f.from} to ${f.to}: remove a link so that there is one.`); });
    const through = N.passing(t); N.queues(t).forEach(x => { if (x.q.kind === 'scheduler' && !through[x.id].length) bad.push(`No flow passes the scheduler of link ${x.l.id}${x.id === x.l.id ? '' : ` on ${x.h}'s side`}: put it on the side that sends, make it a plain queue, or remove it.`); });
    if (t.hosts.length > 8 || t.links.length > 12 || t.flows.length > 8) bad.push('A network holds at most 8 hosts, 12 links and 8 flows.');
    if (!s.description.trim()) bad.push('The description is empty (block 4).');
    if (s.goal === 'given') { const outs = Object.keys(N.outputs(t)); N.condRows().forEach((r, i) => { if (r.text != null) return;
      if (!outs.includes(r.measure)) bad.push(`Condition ${i + 1} names ${r.measure}, which this network does not measure (block 3).`); else if (!isFinite(r.raw)) bad.push(`Condition ${i + 1} needs a number (block 3).`); }); }
    if (!/^[a-z0-9][a-z0-9_-]{1,59}$/.test(s.id.trim())) bad.push('The brief needs a name of 2 to 60 lower-case letters, digits, - and _ (above).');
    return bad;
  },
  num(v) { const x = String(v).trim(); return x !== '' && isFinite(Number(x)) ? Number(x) : x; },
  kindOf(addr) { const p = addr.split('.'); return addr === 'duration' ? 'duration' : p.includes('largest_rate') ? 'largest_rate' : p.includes('parts') ? 'parts' : p[p.length - 1]; },
  isText(addr) { return ['rate', 'delay', 'largest_rate', 'type'].includes(BRIEF_NET.kindOf(addr)); },
  toBrief() {
    BRIEF_NET.syncDesc();
    const N = BRIEF_NET, s = N.s, t = JSON.parse(JSON.stringify(s.t)), cast = (k, v) => (N.isText(k) ? String(v).trim() : N.num(v));
    const have = EV.netSettings(t), fixed = {}; Object.keys(have).forEach(k => { fixed[k] = cast(k, have[k]); }); const net = EV.netWith(t, fixed);
    const knobs = {}; Object.entries(s.knobs).forEach(([k, q]) => { knobs[k] = q.choices ? { choices: q.choices, default: q.default, meaning: q.meaning } : { min: cast(k, q.min), max: cast(k, q.max), default: cast(k, q.default), meaning: q.meaning }; });
    const goal = s.goal === 'open' ? { kind: 'open' } : { kind: 'given', target: { measure: s.measure, direction: s.direction }, conditions: s.conds.split('\n').map(c => c.trim()).filter(Boolean), ...(String(s.tolerance).trim() ? { tolerance: N.num(s.tolerance) } : {}) };
    const b = { id: s.id.trim(), description: s.description.trim(), topology: net, system: { seed: N.num(s.seed), ...('duration' in knobs ? {} : { duration: N.num(s.duration) }), ...(String(s.tcpInitCwnd).trim() ? { tcpInitCwnd: N.num(s.tcpInitCwnd) } : {}), ...(String(s.tcpBufBytes).trim() ? { tcpBufBytes: N.num(s.tcpBufBytes) } : {}), ...Object.fromEntries(['tcpSack', 'tcpTimestamps', 'tcpDelAck'].filter(k => String(s[k] ?? '').trim()).map(k => [k, N.num(s[k])])) }, knobs, goal, limits: { simulations: N.num(s.sims), simulations_per_experiment: N.num(s.per) } };
    if (s.structure) b.structure = { may_change: true, most: Object.fromEntries(Object.entries(s.most).filter(([, v]) => String(v).trim()).map(([k, v]) => [k, N.num(v)])), locked: Object.keys(s.locked).filter(k => s.locked[k]) };
    return b;
  },
  fromBrief(b) {
    const N = BRIEF_NET, s = N.fresh(JSON.parse(JSON.stringify(b.topology))), g = b.goal || {}, st = b.structure || {};
    Object.assign(s, { knobs: JSON.parse(JSON.stringify(b.knobs || {})), description: b.description || '', descAuto: !String(b.description || '').trim(), goal: g.kind === 'given' ? 'given' : 'open', measure: (g.target || {}).measure || '', direction: (g.target || {}).direction || 'max', conds: (g.conditions || []).join('\n'), tolerance: g.tolerance == null ? '' : String(g.tolerance),
      sims: String((b.limits || {}).simulations ?? 40), per: String((b.limits || {}).simulations_per_experiment ?? 12), seed: String((b.system || {}).seed ?? 1), tcpInitCwnd: String((b.system || {}).tcpInitCwnd ?? ''), tcpBufBytes: String((b.system || {}).tcpBufBytes ?? ''), tcpSack: String((b.system || {}).tcpSack ?? ''), tcpTimestamps: String((b.system || {}).tcpTimestamps ?? ''), tcpDelAck: String((b.system || {}).tcpDelAck ?? ''), duration: String((b.system || {}).duration ?? ((b.knobs || {}).duration || {}).default ?? 10), base: b.id || '',
      structure: !!st.may_change, most: { hosts: String((st.most || {}).hosts ?? ''), links: String((st.most || {}).links ?? ''), flows: String((st.most || {}).flows ?? '') }, locked: Object.fromEntries((st.locked || []).map(k => [k, true])) });
    return s;
  },
  // a description written from the network, to start from: each setting by its name in braces, so that it stays true whoever decides it
  // a scheduler with a single queue (every flow in one shared queue) is described as that: it has nothing to divide, so no parts are named
  describe() {
    const N = BRIEF_NET, t = N.s.t;
    const and = list => (list.length > 1 ? list.slice(0, -1).join(', ') + ' and ' + list[list.length - 1] : list[0] || '');
    const queue = ({ h, q, a }) => { const ps = Object.keys(q.parts || {}), name = f => { const who = EV.netMembers(q, f); return who.length === 1 && who[0] === f ? f : `${f} (${and(who)}, which wait in one queue)`; };
      if (q.kind === 'scheduler' && ps.length === 1) { const who = EV.netMembers(q, ps[0]); return ` On ${h}'s side a scheduler hands packets to the link from one queue${who.length > 1 ? `, ${ps[0]}, in which ${and(who)} wait together` : `, in which ${who[0] || ps[0]} waits`}. The queue holds {${a}.length} packets, and a packet that arrives when it is full is dropped. The scheduler has no second queue to divide the link with.`; }
      return q.kind === 'scheduler' ? ` On ${h}'s side a scheduler divides it between ${and(ps.map(name)) || 'its flows'} by the parts ${ps.map(f => `{${a}.parts.${f}}`).join(' : ')} (the parts are divided by their sum); each of them waits in a queue of {${a}.length} packets, and a packet that arrives at a full queue is dropped. How the scheduler behaves when one of them has less to send than its part allows is not described here; finding that out is part of the work.` : q.kind === 'fifo' ? ` On ${h}'s side packets wait in one queue of {${a}.length} packets; a packet that arrives when it is full is dropped.`
        : ` On ${h}'s side packets wait in ns-3's ${EV.netDisc(q.kind)[1]} (${EV.netDisc(q.kind)[2]}), which holds at most {${a}.length} packets.`; };
    const device = l => Object.entries(l.ends || {}).map(([h, x]) => ('rate' in x ? ` The device of ${h} on it sends at {${l.id}.${h}.rate}.` : '') + ('device_queue' in x ? ` The transmit queue of ${h}'s device holds {${l.id}.${h}.device_queue} packets.` : '') + ('mtu' in x ? ` The largest packet ${h}'s device carries is {${l.id}.${h}.mtu} bytes.` : '') + ('loss' in x ? ` The device of ${h} loses a part of the packets that arrive at it, {${l.id}.${h}.loss} of them (0.01 is one in a hundred), whatever they are.` : '')).join('');
    const links = t.links.map(l => `Link ${l.id} joins ${l.between[0]} and ${l.between[1]}: it carries {${l.id}.rate} with a one-way delay of {${l.id}.delay}.${device(l)}${N.queues(t).filter(x => x.l === l).map(queue).join('')}`);
    const times = f => ('start' in f ? ` It starts at {${f.id}.start} s of the simulation.` : '') + ('stop' in f ? ` It stops at {${f.id}.stop} s.` : '') + ('on_time' in f ? ` It sends for {${f.id}.on_time} s, is silent for {${f.id}.off_time} s, and so on.` : '') + ('max_bytes' in f ? ` It stops when it has sent {${f.id}.max_bytes} bytes.` : '');
    const flows = t.flows.map(f => (f.kind === 'udp' ? `Flow ${f.id} is UDP from ${f.from} to ${f.to}: packets of {${f.id}.packet_bytes} bytes at a constant rate ({${f.id}.rate}).` : EV.netApp(f) === 'onoff' ? `Flow ${f.id} is TCP from ${f.from} to ${f.to}: its application hands TCP {${f.id}.packet_bytes} bytes at a time at a constant rate ({${f.id}.rate}), and no more than TCP accepts; its congestion control is {${f.id}.type}.` : `Flow ${f.id} is TCP from ${f.from} to ${f.to}: it always has data to send; its congestion control is {${f.id}.type}.`) + times(f));
    return `A network of ${t.hosts.length} hosts: ${t.hosts.map(h => h.id).join(', ')}. ${links.join(' ')} ${flows.join(' ')} A host with more than one link forwards packets.${[String(N.s.tcpSack) === '0' ? ' TCP runs without selective acknowledgements (SACK).' : '', String(N.s.tcpTimestamps) === '0' ? ' TCP runs without the timestamp option.' : '', String(N.s.tcpDelAck ?? '').trim() ? ` TCP acknowledges every ${String(N.s.tcpDelAck).trim()} segment(s).` : ''].join('')} In each simulation the flows start within the first 10 ms${t.flows.some(f => 'start' in f) ? ' after one second (a flow that states its own start begins then)' : ''}, traffic runs for one second that is not measured, and then for duration seconds, over which the outputs are measured.`;
  },

  // ---- the page
  field(f, v, hint) { return `<input type="text" data-f="${f}" value="${EV.e(v ?? '')}" placeholder="${EV.e(hint || '')}">`; },
  // who decides a setting, as a switch of two halves in words: "fixed" (the operator sets one value) and "AI may change" (within a range the operator gives).
  // The half that holds is filled; a click on the other one switches (it alone carries data-knob). 2026-11-18, the operator: a small ✧ or ✦ said it too vaguely
  whoSeg(addr, k) {
    const e = EV.e, half = (on, by, word, title) => `<button type="button" class="bn-who${on ? ' on' : ''}" data-who="${by}" aria-pressed="${on}"${on ? '' : ` data-knob="${e(addr)}"`} title="${title}"><i class="sw" data-by="${by}"></i>${word}</button>`;
    return `<span class="bn-seg" role="group" aria-label="Who decides this setting" data-decides="${k ? 'model' : 'operator'}">${half(!k, 'operator', 'fixed', k ? 'Click: fix it yourself, at one value the AI cannot change' : 'Fixed: you set its value, and the AI cannot change it')}${half(!!k, 'model', 'AI may change', k ? 'The AI may change it, within the range you give: lowest, highest, and the value it starts from' : 'Click: leave it to the AI, within a range you give')}</span>`;
  },
  // one setting of an object, in its card: its name (and the ns-3 attribute it is), who decides it, and under them its value: one value when it is fixed; lowest, highest and
  // where it starts when the AI may change it (a TCP type: the list it may choose from)
  row(addr, label, value) {
    const N = BRIEF_NET, e = EV.e, k = N.s.knobs[addr], kind = N.kindOf(addr);
    const who = N.whoSeg(addr, k);
    const body = !k ? (kind === 'type' ? `<select data-f="v:${e(addr)}">${N.TCP.map(c => `<option${c === value ? ' selected' : ''}>${c}</option>`).join('')}</select>` : N.field('v:' + addr, value))
      : k.choices ? `<span data-choices="${e(addr)}">${N.TCP.map(c => `<label style="font-weight:400;display:inline-block;margin-right:8px"><input type="checkbox" data-choice="${e(addr)}" value="${c}"${k.choices.includes(c) ? ' checked' : ''}> ${c.replace(/^Tcp/, '')}</label>`).join('')}<small>starts at ${e(String(k.default).replace(/^Tcp/, ''))}</small></span>`
      : `<span class="tri">${['min', 'max', 'default'].map((q, i) => `<label class="bn-tri"><small>${['lowest', 'highest', 'starts at'][i]}</small>${N.field(`k:${addr}:${q}`, k[q], ['lowest', 'highest', 'starts at'][i])}</label>`).join('')}</span>`;
    const attr = EV.netAttr(addr, N.s.t);
    return `<div class="bn-row bn-set" data-row="${e(addr)}" data-decides="${k ? 'model' : 'operator'}"><span class="bn-name">${e(label)}${attr ? `<small class="bn-attr" title="What this setting is in ns-3">${e(attr)}</small>` : ''}</span>${who}<span class="bn-val">${body}</span></div>`;
  },
  // the same in the cards under the picture: what is stated as a setting, the rest as what the program fixes
  timeFacts(f, fact) { const N = BRIEF_NET, T = EV.NET_TIME_SAYS, cap = w => w[0].toUpperCase() + w.slice(1);
    return ('start' in f ? N.row(`${f.id}.start`, 'Starts at, s', f.start) : fact('Starts', '1 s + 0–10 ms')) + ('stop' in f ? N.row(`${f.id}.stop`, 'Stops at, s', f.stop) : '')
      + ('on_time' in f ? N.row(`${f.id}.on_time`, 'On for, s', f.on_time) + N.row(`${f.id}.off_time`, 'Then off for, s', f.off_time) : '') + ('max_bytes' in f ? N.row(`${f.id}.max_bytes`, 'Stops after, bytes', f.max_bytes) : ''); },
  // the times of a flow's application, as ns-3 has them: StartTime, StopTime, for OnOff the on and off periods (together), MaxBytes. Left out, the program's own value stands as a fact with a button to state it
  timeRows(f) {
    const N = BRIEF_NET, e = EV.e, T = EV.NET_TIME_SAYS, ap = EV.netApp(f), btn = (p, on, title) => `<div class="bn-row bn-ownrow"><span></span><span></span><button class="cl" type="button" data-time="${e(f.id)}:${p}" title="${title}">${on ? "the program's again" : 'set'}</button></div>`;
    const one = (p, label, dflt, title) => (p in f ? N.row(`${f.id}.${p}`, label, f[p]) : `<div class="bn-row bn-factrow"><span>${label}</span><span></span><span class="bn-fact">${dflt}</span></div>`) + btn(p, p in f, title);
    return one('start', 'starts at, s', '1 s (+ 0–10 ms by the seed)', 'ns-3 StartTime, in seconds of the simulation. The measured seconds begin at 2 s')
      + one('stop', 'stops at, s', 'the end of the simulation', 'ns-3 StopTime, in seconds of the simulation')
      + (ap === 'onoff' ? ('on_time' in f ? N.row(`${f.id}.on_time`, 'on for, s', f.on_time) + N.row(`${f.id}.off_time`, 'then off for, s', f.off_time) : `<div class="bn-row bn-factrow"><span>on and off periods</span><span></span><span class="bn-fact">always on</span></div>`) + btn('on_time', 'on_time' in f, 'ns-3 OnTime and OffTime of OnOffApplication: it sends at its rate for the on period, is silent for the off period, again and again')
        : `<div class="bn-row bn-factrow"><span>on and off periods</span><span></span><span class="bn-fact">none: BulkSend has no periods</span></div>`)
      + one('max_bytes', 'stops after, bytes', 'no limit', 'ns-3 MaxBytes: the application stops when it has sent that many bytes');
  },
  // the rate and the transmit queue of one device of a link: the link's value (with a button to give this device its own), or its own (and back)
  ownRows(l, h, labels) {
    const N = BRIEF_NET, e = EV.e, x = (l.ends || {})[h] || {}, L = labels || { rate: 'rate', device_queue: 'transmit queue, packets' };
    L.mtu = L.mtu || (labels ? 'Largest packet, bytes' : 'largest packet, bytes'); const lossLabel = labels ? 'Loss on arrival' : 'loss on arrival';
    const loss = ('loss' in x ? N.row(`${l.id}.${h}.loss`, lossLabel, x.loss) : `<div class="bn-row bn-factrow"><span>${lossLabel}</span><span></span><span class="bn-fact">none: no error model</span></div>`)
      + `<div class="bn-row bn-ownrow"><span></span><span></span><button class="cl" type="button" data-own="${e(l.id)}:${e(h)}:loss" title="${'loss' in x ? 'This device receives every packet again' : 'ns-3: a RateErrorModel as the ReceiveErrorModel of this device. It drops that part of the packets arriving here (0.01 = one in a hundred)'}">${'loss' in x ? 'no loss again' : 'set a loss'}</button></div>`;
    return ['rate', 'device_queue', 'mtu'].map(p => (p in x ? N.row(`${l.id}.${h}.${p}`, `${L[p]} (its own)`, x[p]) : (labels ? N.row(`${l.id}.${p}`, L[p], l[p]) : `<div class="bn-row bn-factrow"><span>${e(L[p])}</span><span></span><span class="bn-fact">the link's: ${e(p === 'rate' ? TASK_VIEW._rate(String(l[p])) : l[p])}</span></div>`))
      + `<div class="bn-row bn-ownrow"><span></span><span></span><button class="cl" type="button" data-own="${e(l.id)}:${e(h)}:${p}" title="${p in x ? 'This device takes the value of the link again, like the device at the other end' : 'The two devices of a link need not be alike: this one gets a value of its own'}">${p in x ? 'same as the link again' : 'set separately'}</button></div>`).join('') + loss;
  },
  card() {
    const N = BRIEF_NET, s = N.s, t = s.t, e = EV.e, sel = s.sel, o = N.find(sel);
    if (!o) return `<div class="bn-card" id="bn-card"><p class="sm mut">Click an object of the picture to see and set its values: a host, a link, a flow (its source), a queue.</p></div>`;
    const [kind, id] = sel, d = N.deps(kind, id).gone.slice(1), rm = `<p style="margin:8px 0 0"><button data-remove="${e(kind)}:${e(id)}">Remove ${e(N.says(kind, id))}</button>${d.length ? ` <span class="sm">also removes ${e(d.map(([k, i]) => N.says(k, i)).join(', '))}</span>` : ''}</p>`;
    const lock = s.structure ? `<p class="sm" style="margin:6px 0 0"><label style="font-weight:400"><input type="checkbox" data-lock="${e(kind)}:${e(id)}"${s.locked[`${kind}:${id}`] ? ' checked' : ''}> the AI may not remove or change this object</label></p>` : '';
    let rows = '';
    // a host: what is inside it, by the layers of its picture; each part opens its own card, and what can be added to this host is added from here
    if (kind === 'host') { const out = t.flows.filter(f => f.from === id), inn = t.flows.filter(f => f.to === id), ls = t.links.filter(l => l.between.includes(id)), pt = (k, i, text) => `<button class="bn-in" data-pick="${k}:${e(i)}">${text}</button>`, plain = v => TASK_VIEW._rate(String(v)).replace(/^Tcp/, ''), far = l => l.between.find(x => x !== id), bare = l => !EV.netEnds(l)[id].queue;
      const others = t.hosts.filter(h => h.id !== id).map(h => h.id), unlinked = others.filter(h => !ls.some(l => l.between.includes(h))), opt = (list, note) => list.map(h => `<option value="${e(h)}">${e(h)}${note && !EV.netPath(t, { from: id, to: h }) ? ' (a link to it is added too)' : ''}</option>`).join('');
      // Everything a host can hold is set up from here, with nothing that has to be done somewhere else first: an application is added with the host it
      // sends to (where no link leads there yet, the link is added with it); a link, with the host at its other end; a scheduler, on any of its links.
      rows = `<p class="sm">ns-3 Node ${t.hosts.findIndex(h => h.id === id)} · click a part to set it (here or in the picture)</p>
        <h5>Applications</h5>${out.map(f => pt('flow', f.id, `<b>${e(f.id)}</b> · ${EV.NET_APP[EV.netApp(f)][0]} application, sends to ${e(f.to)}${EV.netApp(f) === 'onoff' ? ' · ' + e(plain(f.rate)) : ''}`)).join('')}${inn.map(f => pt('flow', f.id, `<b>${e(f.id)}</b> sink · receives from ${e(f.from)}`)).join('')}
        ${others.length ? `<div class="bn-add" id="bn-add-app"><span>add one that sends to</span><select id="bn-app-to" aria-label="The host the new application sends to">${opt(others, true)}</select><button data-addapp="udp" title="ns-3 OnOffApplication: sends packets at a constant rate, on a UDP socket (its card can make that TCP)">+ OnOff</button><button data-addapp="tcp" title="ns-3 BulkSendApplication: always has data to send, on a TCP socket">+ BulkSend</button></div>` : '<p class="sm">An application sends to another host: add a second host first (drag “Host” onto the picture).</p>'}
        <h5>Internet stack</h5>${out.concat(inn).map(f => pt('flow', f.id, `${f.kind.toUpperCase()} socket of <b>${e(f.id)}</b>${f.kind === 'tcp' && f.from === id ? ' · ' + e(plain(f.type)) : ''}`)).join('')}<p class="sm">IPv4${ls.length > 1 ? ': forwards between its links' : ''} · no setting of its own</p>
        <div class="bn-row"><span>TCP first window<small class="bn-attr">TcpSocket · InitialCwnd</small></span><span></span>${N.field('tcpInitCwnd', s.tcpInitCwnd, '10 segments')}</div><div class="bn-row"><span>TCP buffers, bytes<small class="bn-attr">TcpSocket · SndBufSize, RcvBufSize</small></span><span></span>${N.field('tcpBufBytes', s.tcpBufBytes, '1048576 (1 MB)')}</div><div class="bn-row"><span>SACK<small class="bn-attr">TcpSocketBase · Sack</small></span><span></span><select data-f="tcpSack">${[['', "ns-3's own: on"], ['1', 'on'], ['0', 'off']].map(([v, w]) => `<option value="${v}"${String(s.tcpSack) === v ? ' selected' : ''}>${w}</option>`).join('')}</select></div>
        <div class="bn-row"><span>Timestamps<small class="bn-attr">TcpSocketBase · Timestamp</small></span><span></span><select data-f="tcpTimestamps">${[['', "ns-3's own: on"], ['1', 'on'], ['0', 'off']].map(([v, w]) => `<option value="${v}"${String(s.tcpTimestamps) === v ? ' selected' : ''}>${w}</option>`).join('')}</select></div>
        <div class="bn-row"><span>Segments per ACK<small class="bn-attr">TcpSocket · DelAckCount</small></span><span></span>${N.field('tcpDelAck', s.tcpDelAck, '2')}</div>
        <p class="sm">These five are attributes of every TCP socket, and ns-3 keeps one default for the whole simulation: they are the same on every host. Empty: ns-3's own value. The congestion control is the host's own (TcpL4Protocol · SocketType) and stands with each TCP socket.</p>
        <h5>Traffic control</h5>${N.queues(t).filter(x => x.h === id).map(x => pt('queue', x.id, `${e(EV.netDisc(x.q.kind)[0])} towards ${e(far(x.l))} · ${e(x.q.length)} packets${x.q.kind === 'scheduler' ? ` · ${Object.keys(x.q.parts || {}).length} queue${Object.keys(x.q.parts || {}).length === 1 ? '' : 's'}` : ''}`)).join('')}
        ${ls.filter(bare).length ? `<p class="bn-adds">${ls.filter(bare).map(l => `<button data-addq="${e(l.id)}:${e(id)}">+ scheduler towards ${e(far(l))}</button> <button data-addq="${e(l.id)}:${e(id)}" data-qk="fifo">+ shared queue towards ${e(far(l))}</button>`).join(' ')}</p>` : ''}
        <p class="sm">${ls.length ? (ls.some(bare) ? 'Where no queue is described, packets wait in a plain queue of 100 packets.' : '') : 'Packets wait where they are sent onto a link: this host has no link yet (add one below).'}</p>
        <h5>Net devices</h5>${ls.map(l => { const d = EV.netEnds(l)[id]; return pt('link', l.id, `device on link <b>${e(l.id)}</b> to ${e(far(l))} · ${e(plain(d.rate))} · queue ${e(d.device_queue)}`); }).join('')}
        ${unlinked.length ? `<div class="bn-add" id="bn-add-link"><span>add a link to</span><select id="bn-link-to" aria-label="The host at the other end of the new link">${opt(unlinked)}</select><button data-addlink="${e(id)}">+ link</button></div>` : `<p class="sm">${others.length ? 'It has a link to every other host.' : 'A link joins two hosts: add a second host first.'}</p>`}`; }
    // a link is a channel and two devices (ns-3): its line gives what the two devices have in common; a device may have a rate and a transmit queue of its own
    if (kind === 'link') rows = N.row(`${id}.rate`, 'rate', o.rate) + N.row(`${id}.delay`, 'one-way delay', o.delay) + N.row(`${id}.mtu`, 'largest packet, bytes', o.mtu) + N.row(`${id}.device_queue`, 'device queue, packets', o.device_queue)
      + o.between.map(h => `<h5>Device of ${e(h)}</h5>${N.ownRows(o, h)}`).join('') + `<p class="sm">between ${e(o.between[0])} and ${e(o.between[1])}${N.queues(t).some(x => x.l === o) ? '' : ' · a plain queue of 100 packets on each side'}</p>`;
    if (kind === 'flow') { const ap = EV.netApp(o), sel = (v, on) => `<option value="${v}"${on ? ' selected' : ''}`;
      rows = `<div class="bn-row"><span>application</span><span></span><select data-fapp="${e(id)}" title="The ns-3 application that sends: how much, and when. The socket it opens is the next choice">${sel('onoff', ap === 'onoff')}>OnOff: a constant rate</option>${sel('bulk', ap === 'bulk')}>BulkSend: always has data</option></select></div>`
        + `<div class="bn-row"><span>socket</span><span></span><select data-fkind="${e(id)}" title="The socket the application opens (ns-3: its Protocol). The sink at the other end and the measures follow from it: loss for UDP, segments sent again for TCP">${sel('udp', o.kind === 'udp')}${ap === 'bulk' ? ' disabled' : ''}>UDP${ap === 'bulk' ? ' (BulkSend needs TCP)' : ''}</option>${sel('tcp', o.kind === 'tcp')}>TCP</option></select></div>`
        + `<p class="sm" id="bn-fapp-says">ns-3 ${e(EV.NET_APP[ap][1])} on a ${e(o.kind.toUpperCase())} socket${ap === 'bulk' ? ' · ns-3 has no application that always has data for UDP: nothing would tell it how fast to send' : o.kind === 'tcp' ? ' · it hands TCP no more than TCP accepts' : ''}</p>`
        + (ap === 'onoff' ? N.row(`${id}.rate`, 'rate', o.rate) + N.row(`${id}.packet_bytes`, 'packet size, bytes', o.packet_bytes) : '') + (o.kind === 'tcp' ? N.row(`${id}.type`, 'TCP type', o.type) : '') + `<h5>Times</h5>` + N.timeRows(o) + `<p class="sm">on ${e(o.from)}; it sends to ${e(o.to)}, over ${e((EV.netPath(t, o) || []).map(([l]) => l).join(', ') || 'no link')}</p>`; }
    if (kind === 'queue') { const x = N.qOf(id), a = x.a, fl = N.passing(t)[id] || [], cl = o.classes || {}, names = Object.keys(o.parts || {}), who = n => EV.netMembers(o, n), isCl = n => n in cl;
      // in which queue each flow waits: one of its own, or one it shares with others (2026-11-17, the operator: one combined queue in front of the scheduler instead of two)
      const where = f => { const mine = Object.keys(cl).find(n => cl[n].includes(f)); return `<div class="bn-row"><span>${e(f)} waits in</span><span></span><select data-qclass="${e(id)}:${e(f)}" title="A scheduler has one queue for each of its parts. A flow has a queue to itself, or shares one with other flows: they then share its part of the link too."><option value="~own"${mine ? '' : ' selected'}>a queue of its own</option>${Object.keys(cl).map(n => `<option value="${e(n)}"${n === mine ? ' selected' : ''}>the shared queue ${e(n)}${cl[n].filter(y => y !== f).length ? ' (with ' + e(cl[n].filter(y => y !== f).join(', ')) + ')' : ''}</option>`).join('')}${mine && cl[mine].length === 1 ? '' : '<option value="~new">a new shared queue</option>'}</select></div>`; };
      rows = `<div class="bn-row"><span>kind</span><span></span><select data-qkind="${e(id)}" title="The queue disc of this net device. ns-3 puts one on every device; scheduler is this project's own, the others are ns-3's">${Object.entries(EV.NET_DISC).map(([k, d]) => `<option value="${k}"${o.kind === k ? ' selected' : ''}>${e(d[0])} · ${e(d[1])}</option>`).join('')}</select></div><p class="sm" id="bn-qdisc-says">${o.kind === 'scheduler' ? '' : 'ns-3 '}${e(EV.netDisc(o.kind)[1])}: ${e(EV.netDisc(o.kind)[2])}${['scheduler', 'fifo'].includes(o.kind) ? '' : ". Its other settings are ns-3's own"}</p>`
        + N.row(`${a}.length`, 'length, packets', o.length) + (o.kind === 'scheduler' ? (fl.length > 1 ? `<h5>Queues</h5><div id="bn-qclass">${fl.map(where).join('')}</div>` : '') + `<h5>Parts of the link</h5>` + names.map(n => N.row(`${a}.parts.${n}`, isCl(n) ? `part of ${n} (${who(n).join(' + ')})` : `part of ${n}`, o.parts[n]) + `<div class="bn-row"><span>largest rate of ${e(n)}</span><span></span>${N.field(`lr:${id}:${n}`, (o.largest_rate || {})[n] || '', 'none')}</div>`).join('') : '')
        + `<p class="sm">on ${e(x.h)}'s side of link ${e(x.l.id)}${o.kind === 'scheduler' ? ' · the parts are divided by their sum' : ''}</p>`; }
    // drawn the simple way, the picture shows a host as a sign: the full structure of the host that is chosen (or that holds what is chosen) stands here
    const owner = kind === 'host' ? id : kind === 'flow' ? o.from : kind === 'queue' ? N.qOf(id).h : null, detail = NETC.mode() === 'simple' && owner ? NETC.detail(t, owner, s.knobs) : '';
    return `<div class="bn-card" id="bn-card" data-sel="${e(kind)}:${e(id)}">${detail}<h4>${e(kind === 'queue' ? `Queue of link ${N.qOf(id).l.id}${N.qOf(id).id === N.qOf(id).l.id ? '' : ` · ${N.qOf(id).h}'s side`}` : kind === 'flow' ? `${EV.NET_APP[EV.netApp(o)][0]} application ${id} · ${o.kind.toUpperCase()} socket` : `${kind[0].toUpperCase()}${kind.slice(1)} ${id}`)}</h4>${rows}${lock}${rm}</div>`;
  },
  // ---- one card for each part of the network, with everything it has (2026-11-17, the operator: as under the two-host picture, so that every
  // configuration can be seen; a part that is added brings its cards). A setting is set in its card (✧ fixed by the operator, ✦ left to the AI: the
  // same row as in the card of the chosen object); what the program fixes is said in words (read from scratch/net: the flows start at 1 s plus up to
  // 10 ms, a full segment is the smallest largest-packet on the way less 52 bytes, the scheduler's turn is 3000 bytes times the part; the rest are
  // ns-3's own values). data-keys: the objects a card belongs to (host:, flow:, queue:, link:), for the highlight between the picture and the cards.
  panels() {
    const N = BRIEF_NET, s = N.s, t = s.t, e = EV.e, passing = N.passing(t), plain = v => TASK_VIEW._rate(String(v)).replace(/^Tcp/, ''), far = (l, h) => l.between.find(x => x !== h);
    const fact = (label, text) => `<div class="bn-row bn-factrow"><span>${label}</span><span></span><span class="bn-fact">${text}</span></div>`;
    const card = (keys, pick, title, where, rows) => `<div class="bn-pc" data-keys="${e(keys.join(' '))}" data-part="${e(title + ' @ ' + where)}"><h5 class="bn-pc-h" data-pick="${e(pick)}" title="Click: choose this part in the picture"><b>${e(title)}</b> <span>${e(where)}</span></h5>${rows}</div>`;
    const shared = (f, label, v, hint) => `<div class="bn-row"><span>${label}</span><span title="Fixed by the operator, and the same for the whole network"><i class="sw" data-by="operator"></i></span>${N.field(f, v, hint)}</div>`;
    const seg = f => { const way = (EV.netPath(t, f) || []).map(([l]) => N.linkOf(l)).filter(Boolean), m = Math.min(...way.map(l => Number(l.mtu) || 1500)); return way.length ? `${m - 52} bytes` : 'no way yet'; };
    const order = t.hosts.slice().sort((a, b) => ((s.pos[a.id] || {}).x ?? 0) - ((s.pos[b.id] || {}).x ?? 0)), seen = new Set(); let out = '';
    order.forEach(h => { const H = h.id, src = t.flows.filter(f => f.from === H), dst = t.flows.filter(f => f.to === H), ls = t.links.filter(l => l.between.includes(H));
      src.forEach(f => { out += card([`host:${H}`, `flow:${f.id}`], `flow:${f.id}`, `${f.id} source`, `${H} · applications · ${EV.NET_APP[EV.netApp(f)][1]}`, (EV.netApp(f) === 'onoff' ? N.row(`${f.id}.rate`, 'Sends, constant', f.rate) + N.row(`${f.id}.packet_bytes`, f.kind === 'udp' ? 'Packet payload, bytes' : 'Hands TCP at a time, bytes', f.packet_bytes) : fact('Sends', 'as fast as TCP accepts, no limit')) + fact('Sends to', e(f.to)) + N.timeFacts(f, fact)); });
      dst.forEach(f => { out += card([`host:${H}`, `flow:${f.id}`], `flow:${f.id}`, `${f.id} sink`, `${H} · applications · PacketSink`, fact('Receives from', e(f.from)) + fact('Counts', f.kind === 'udp' ? 'what arrives: goodput, loss' : 'what arrives: goodput')); });
      src.forEach(f => { out += card([`host:${H}`, `flow:${f.id}`], `flow:${f.id}`, `${f.kind.toUpperCase()} socket of ${f.id}`, `${H} · internet stack`, f.kind === 'udp' ? fact('Send buffer', 'none: nothing is held back') + fact('Resends lost packets', 'never')
        : N.row(`${f.id}.type`, 'Congestion control', f.type) + fact('Segment payload', seg(f)) + shared('tcpBufBytes', 'Send and receive buffer, bytes', s.tcpBufBytes, '1048576 (1 MB)') + shared('tcpInitCwnd', 'First window, segments', s.tcpInitCwnd, '10') + fact('TCP options', 'timestamps, SACK, window scaling') + fact('Shortest resend timer', '1 s')); });
      dst.forEach(f => { out += card([`host:${H}`, `flow:${f.id}`], `flow:${f.id}`, `${f.kind.toUpperCase()} socket of ${f.id}`, `${H} · internet stack`, f.kind === 'udp' ? fact('Receive buffer', '128 kB') : shared('tcpBufBytes', 'Receive buffer, bytes', s.tcpBufBytes, '1048576 (1 MB)') + fact('Sends ACK', 'every 2nd packet, or after 0.2 s')); });
      out += card([`host:${H}`], `host:${H}`, 'IPv4', `${H} · internet stack`, fact('Forwards', ls.length > 1 ? 'between its links' : 'no: it has one link or none') + fact('Largest packet', ls.length ? ls.map(l => `${e(l.mtu)} bytes on ${e(l.id)}`).join(', ') + ' (larger ones would be split)' : 'no link yet'));
      N.queues(t).filter(x => x.h === H).forEach(({ l, q, a, id }) => { const fl = passing[id] || [], names = Object.keys(q.parts || {}), who = n => EV.netMembers(q, n), shared = n => n in (q.classes || {});
        if (q.kind === 'scheduler') names.forEach(n => { out += card([`host:${H}`, `queue:${id}`, ...who(n).map(f => `flow:${f}`)], `queue:${id}`, `${n} queue`, `${H} · traffic control`, N.row(`${a}.length`, 'Room for, packets', q.length) + (shared(n) ? fact('Holds', 'the packets of ' + who(n).map(e).join(', ') + ', together') : '') + fact('When full', 'the new packet is dropped')); });
        out += card([`host:${H}`, `queue:${id}`], `queue:${id}`, q.kind === 'scheduler' ? 'Scheduler' : 'Shared queue', `${H} · traffic control · towards ${far(l, H)}`, (q.kind === 'scheduler' ? names.map(n => N.row(`${a}.parts.${n}`, shared(n) ? `Part of ${n} (${who(n).join(' + ')})` : `Part of ${n}`, q.parts[n] ?? 1)).join('') + fact('Scheduling policy', 'chosen in block 6 · not told to the AI') + fact('Turn size', '3000 bytes × part')
          : N.row(`${a}.length`, 'Room for, packets', q.length) + fact('Holds', fl.length ? 'the packets of ' + fl.map(e).join(', ') + ', together' : 'no flow passes it yet') + fact('Order', 'first in, first out') + fact('When full', 'the new packet is dropped')) + fact('Link rate (read from its device)', e(plain(EV.netEnds(l)[H].rate)))); });
      ls.forEach(l => { out += card([`host:${H}`, `link:${l.id}`], `link:${l.id}`, 'Point-to-point device', `${H} · net device · link ${l.id}`, N.ownRows(l, H, { rate: 'Rate', device_queue: 'Transmit queue, packets' }) + fact('Queue kind', 'DropTailQueue'));
        if (!seen.has(l.id)) { seen.add(l.id); out += card([`link:${l.id}`], `link:${l.id}`, `Point-to-point link ${l.id}`, `between ${l.between[0]} and ${l.between[1]}`, N.row(`${l.id}.delay`, 'Delay, one way', l.delay) + fact('Capacity', (() => { const E = EV.netEnds(l), [a, b] = l.between; return E[a].rate === E[b].rate ? `${e(plain(E[a].rate))} (set by the two devices)` : `${e(plain(E[a].rate))} from ${e(a)}, ${e(plain(E[b].rate))} from ${e(b)} (each device sends at its own rate)`; })())); } }); });
    return `<div id="bn-panels-box"><p class="sm bn-panels-h"><b>Every part, with everything it has</b> · one card for each part of the network; a part you add brings its cards · beside each setting, who decides it: <i class="sw" data-by="operator"></i>fixed (you set one value) or <i class="sw" data-by="model"></i>AI may change (within a range you give); click the other one to switch · in the picture a ✦ before a value says the AI may change it · point at a part of the picture to find its cards, and at a card to find its part</p><div class="bn-panels" id="bn-panels">${out}</div></div>`;
  },
  // the highlight between the picture and the cards: the cards of the part the pointer is on, and the part of the card it is on (no drawing again, nothing moves)
  hot(keys) {
    const N = BRIEF_NET, k = (keys || []).join(' '); if (k === N._hot) return; N._hot = k; const on = new Set(keys || []), q = id => CSS.escape(id);
    N.node.querySelectorAll('.bn-pc').forEach(c => c.classList.toggle('hot', c.dataset.keys.split(' ').some(x => on.has(x))));
    N.node.querySelectorAll('.nc-hot').forEach(x => x.classList.remove('nc-hot'));
    const specific = (keys || []).filter(x => !x.startsWith('host:')), use = specific.length ? specific : keys || [];
    use.forEach(x => { const [kind, id] = [x.slice(0, x.indexOf(':')), x.slice(x.indexOf(':') + 1)];
      const sel = kind === 'flow' ? `[data-flow="${q(id)}"], [data-sink="${q(id)}"]` : kind === 'queue' ? `[data-queue="${q(id)}"]` : kind === 'link' ? `#bn-paper [data-link="${q(id)}"]` : `#bn-paper [data-host="${q(id)}"]`;
      N.node.querySelectorAll(sel).forEach(el => el.classList.add('nc-hot')); });
  },
  over(ev) {
    const N = BRIEF_NET, t = ev.target.closest ? ev.target : null; if (!t || !N.s || N.s.drag) return;
    const pc = t.closest('.bn-pc'); if (pc) return N.hot(pc.dataset.keys.split(' '));
    if (!t.closest('#bn-paper, .bn-detail')) return N.hot([]);
    const f = t.closest('[data-flow], [data-sink]'), qd = t.closest('[data-queue]'), l = t.closest('[data-link]'), h = t.closest('[data-host], [data-detail]');
    N.hot(f ? ['flow:' + (f.dataset.flow || f.dataset.sink)] : qd ? ['queue:' + qd.dataset.queue] : l ? ['link:' + l.dataset.link] : h ? ['host:' + (h.dataset.host || h.dataset.detail)] : []);
  },
  canvas() {
    return `<div class="bn-canvas" id="bn-canvas"><div id="bn-paper"></div>${BRIEF_NET.s.t.hosts.length ? '' : '<p class="sm bn-empty">An empty network: drag a host from the palette onto this field.</p>'}<div id="bn-zones"></div></div>`;
  },
  draw() {
    const N = BRIEF_NET, s = N.s, e = EV.e, briefs = ((N.ctx.st || {}).briefs || []), nw = EV.nw, outs = Object.keys(N.outputs(s.t)), have = EV.netSettings(s.t); N.syncDesc();
    const act = document.activeElement, keep = act && N.node.contains(act) && act.dataset && act.dataset.f ? { f: act.dataset.f, part: act.closest('.bn-pc') ? act.closest('.bn-pc').dataset.part : act.closest('#bn-card') ? '#card' : '', at: act.selectionStart } : null;
    const sched = N.queues(s.t).some(x => x.q.kind === 'scheduler'), name = k => (TH_DATA.KNOB[k] || k);
    EV.netApply({ id: 'setup-' + Date.now(), topology: s.t });
    // the tool palette: the kinds of object in groups, each with its sign; a tool is dragged onto the picture (or chosen with Enter, then a place)
    const tool = k => { const [, title, says, full] = N.KINDS.find(q => q[0] === k); return `<button class="bn-kind${s.placing === k ? ' on' : ''}" data-kind="${k}" title="${e(full)}. Drag it onto the picture, or press Enter and choose a place."><svg viewBox="0 0 28 28" width="28" height="28" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${N.ICON[k]}</svg><span><b>${title}</b><span>${says}</span></span></button>`; };
    const pal = `<div class="bn-pal" id="bn-pal" aria-label="Tools"><p class="bn-pal-h">Tools <span class="sm">drag one onto the picture</span></p>${N.GROUPS.map(([name, ks]) => `<div class="bn-group" data-group="${e(name)}"><p class="bn-group-h">${e(name)}</p>${ks.map(tool).join('')}</div>`).join('')}</div>`;
    const bar = `<div class="bn-bar"><span class="bn-acts"><button id="bn-undo"${N.past.length ? '' : ' disabled'} title="Undo (key: left arrow)">← Undo</button><button id="bn-redo"${N.ahead.length ? '' : ' disabled'} title="Redo (key: right arrow)">Redo →</button></span>
      <span class="bn-seg" role="group" aria-label="How the hosts are drawn" title="Simple: a host is its sign and its marks; its full structure stands beside the picture when it is chosen. Detailed: every host shows its full structure in the picture."><button id="bn-simple" class="${NETC.mode() === 'simple' ? 'on' : ''}" aria-pressed="${NETC.mode() === 'simple'}">simple</button><button id="bn-full" class="${NETC.mode() === 'full' ? 'on' : ''}" aria-pressed="${NETC.mode() === 'full'}">detailed</button></span>
      <span class="sm bn-hint">drag a host to move it anywhere · choose it and drag a handle (right edge, lower edge, corner) to resize it · drag its <b>+</b> onto another host to link them · drag the background to move the picture · scroll to zoom</span>
      <span class="bn-acts"><button id="bn-zout" title="Smaller" aria-label="Smaller">−</button><button id="bn-zin" title="Larger" aria-label="Larger">+</button><button id="bn-fit" title="Show the whole network (key F)">fit <span class="sm">F</span></button></span></div>`;
    const b1 = `<div class="bn-three">${pal}<div>${bar}${N.canvas()}<p class="sm bn-say" id="bn-say"></p></div><div id="bn-side">${N.card()}</div></div>${N.panels()}`;
    const who = k => (s.knobs[k] ? `<td>${e(s.knobs[k].choices ? 'one of ' + s.knobs[k].choices.map(c => c.replace(/^Tcp/, '')).join(', ') : `${s.knobs[k].min} to ${s.knobs[k].max}, starts at ${s.knobs[k].default}`)}</td><td data-decides="model"><i class="sw" data-by="model"></i>the AI may change it</td>` : `<td><b>${e(have[k])}</b></td><td data-decides="operator"><i class="sw" data-by="operator"></i>fixed by the operator</td>`);
    const b2 = `<table class="bn-list" id="bn-who"><tbody>${Object.keys(have).map(k => `<tr data-k="${e(k)}"><td>${e(name(k))}</td>${who(k)}</tr>`).join('')}
        <tr data-k="duration" title="How long each simulation runs: the seconds that are measured. Before them every simulation runs 2 s of start-up that is not measured (ns-3 stops at 2 s + this many seconds)."><td>simulation time, s <span class="sm">measured seconds, after 2 s of start-up</span></td><td>${s.knobs.duration ? `${e(s.knobs.duration.min)} to ${e(s.knobs.duration.max)}, starts at ${e(s.knobs.duration.default)}` : N.field('duration', s.duration)}</td><td>${N.whoSeg('duration', s.knobs.duration)}</td></tr>
        <tr data-k="seed"><td>seed</td><td>${N.field('seed', s.seed)}</td><td data-decides="operator"><i class="sw" data-by="operator"></i>fixed by the operator</td></tr></tbody></table>
      <p class="sm">A setting is changed in its object's card (block 1): click the object; beside each setting, “fixed” or “AI may change” says who decides it, and a click on the other one switches.</p>
      <p style="margin-top:8px"><label style="font-weight:400"><input type="checkbox" id="bn-structure"${s.structure ? ' checked' : ''}> <b>The AI may change the structure</b>: add and remove hosts, links, flows and queues in the simulations it asks for</label></p>
      ${s.structure ? `<div class="bn-row" style="grid-template-columns:auto 80px 80px 80px"><span>at most (empty: 8 hosts, 12 links, 8 flows)</span>${['hosts', 'links', 'flows'].map(k => N.field('most:' + k, s.most[k], k)).join('')}</div><p class="sm">An object can be kept from it: click the object, then tick “the AI may not remove or change this object”. What the aim names is kept by itself.</p>` : ''}`;
    const b3 = `<div class="be-aim" id="bn-aim"><label><input type="radio" name="bn-goal" data-goal="open"${s.goal === 'open' ? ' checked' : ''}> <b>open</b>: the AI chooses its own aim and has to justify it</label><label><input type="radio" name="bn-goal" data-goal="given"${s.goal === 'given' ? ' checked' : ''}> a target with conditions</label></div>
      ${s.goal === 'given' ? `<div class="be-two"><label>Target<small>the measure to make as large or as small as possible</small><select data-f="measure">${outs.map(k => `<option value="${e(k)}"${k === s.measure ? ' selected' : ''}>${e(TH_DATA.PLAIN[k] || k)}</option>`).join('')}</select></label>
        <label>Direction<select data-f="direction"><option value="max"${s.direction === 'max' ? ' selected' : ''}>as large as possible</option><option value="min"${s.direction === 'min' ? ' selected' : ''}>as small as possible</option></select></label>
        ${N.condsHtml(outs)}
        <label>Tolerance, per cent (optional)<small>two results closer than this count as equal</small>${N.field('tolerance', s.tolerance, 'none')}</label></div>` : ''}`;
    const b4 = `<div class="be-two"><label>The task<small>written by the harness from the aim and the settings the AI may change</small><span id="bn-task" class="be-task" data-own="harness"></span></label>
        <label>The description of the system<small id="bn-desc-says">${s.descAuto ? 'written from the network as you build it: nothing to type. Type in it to write your own' : 'your own text: it no longer follows the network'} · a setting's address in braces is filled with its value where it is fixed and reads “the knob …” where the AI may change it <button class="cl" id="bn-describe" type="button">${s.descAuto ? 'write it from the network' : 'write it from the network again'}</button></small><textarea data-f="description" rows="5">${e(s.description)}</textarea></label></div>`;
    const b5 = `<div class="be-two"><label>Simulations in all${N.field('sims', s.sims, 'e.g. 40')}</label><label>In one turn${N.field('per', s.per, 'e.g. 12')}</label></div>`;
    const pol = (v, says) => `<label style="font-weight:400;margin:3px 0;display:block"><input type="radio" name="nw-policy" data-ch="nw" data-k="policy" value="${v}"${nw.policy === v ? ' checked' : ''}> <b>${v}</b> <span class="sm" style="display:inline">${says}</span></label>`;
    const b6 = sched ? `<div id="bn-policy" data-by="operator">${pol('share', 'what one flow leaves unused goes to the others · the default')}${pol('cap', 'each flow is held to its part, whatever the others send')}${pol('prio', 'the first flow of a scheduler\'s list goes first; the parts are not used')}${pol('random', 'the harness chooses share or cap')}<p class="sm">How a scheduler divides its link is never told to the AI.</p></div>` : '<p class="sm" id="bn-policy">This network has no scheduler: there is no scheduling policy to choose.</p>';
    const fl = (label, html, note) => `<div><span>${label}</span>${html}<span>${note}</span></div>`;
    // no "simulations allowed at the start" here any more (2026-11-22, the operator: it repeated block 5's "Simulations in all"): a session starts with the brief's limit
    const b7 = `<div class="kv" id="bn-flags">${fl('draft before the answer', `<select data-ch="nw" data-k="draft"><option${nw.draft === 'on' ? ' selected' : ''}>on</option><option${nw.draft === 'off' ? ' selected' : ''}>off</option></select>`, 'default: on')}
        ${fl('baseline simulation first', `<label style="font-weight:400"><input type="checkbox" data-ch="nw" data-k="baseline"${nw.baseline ? ' checked' : ''}> run it</label>`, 'default: on')}
        ${fl('who rules on the tests', EV.armField(), 'default: one AI')}</div>`;
    const nets = (N.ctx.st || {}).network_briefs || [];
    const top = `<div class="be-top"><div><label>Start from <span class="sm" style="font-weight:400">(optional)</span><small>the network below is ready to build on and to start. Or load another to change: a saved brief that has a network, or one of two examples</small><select id="bn-open"><option value="">the network below, as it is</option><option value="~default">example: two hosts, one link (UDP and TCP)</option><option value="~dumbbell">example: two senders through a third host</option>${nets.map(b => `<option value="${e(b)}"${b === s.base ? ' selected' : ''}>${e(b)}</option>`).join('')}</select></label></div>
        <label>Name of the new brief<small>lower-case letters, digits, - and _ · a saved brief is never overwritten</small>${N.field('id', s.id, 'e.g. three-hosts')}</label></div>`;
    const blk = (i, body, cls) => EV.setBlock(i, body, { says: true, cls });
    const first = blk(0, b1, 'st-wide').replace(/(<p class="st-says[^>]*>)[^<]*/, '$1Hosts, links, flows and queues, drawn as in the two-host picture. Drag a tool onto the picture to add one; choose an object and press its × (or Delete) to remove it.');
    NETC.dispose();
    N.node.innerHTML = `${top}<div class="st" id="st-blocks">${first}${blk(1, b2)}${blk(2, b3)}${blk(3, b4, 'st-told')}<div class="st-row st-low">${blk(4, b5)}${blk(5, b6)}${blk(6, b7)}</div></div>
      <div class="be-start" id="bn-start-box"><div id="bn-state" class="sm"></div><div id="bn-msg"></div><p style="margin-top:8px"><button id="bn-save">Save as new brief</button> <button class="big primary" id="bn-start">Save and start the session</button></p></div>`;
    NETC.mount(N.node.querySelector('#bn-paper'), s.t, { knobs: s.knobs, pos: s.pos, sel: s.sel });
    N.paint();
    if (keep) { const scope = keep.part === '#card' ? N.node.querySelector('#bn-card') : keep.part ? [...N.node.querySelectorAll('.bn-pc')].find(c => c.dataset.part === keep.part) : N.node, el = scope && scope.querySelector(`[data-f="${CSS.escape(keep.f)}"]`);
      if (el) { el.focus({ preventScroll: true }); try { el.setSelectionRange(keep.at, keep.at); } catch (x) { /* a field without a caret */ } } }
  },
  // what follows the values, in place: the drop places, the chosen object's mark, the task, what cannot be saved yet
  paint() {
    const N = BRIEF_NET, s = N.s, e = EV.e, $ = id => N.node.querySelector('#' + id), cv = $('bn-canvas'), svg = cv && cv.querySelector('svg'); if (!cv) return;
    NETC.mark(s.sel); NETC.band(s.pending);
    const zs = N.zones(), box = $('bn-zones'), k = 1;   // the places are given in pixels of the canvas (NETC.geom)
    box.innerHTML = zs.map((z, i) => `<button class="bn-zone" data-zone="${i}" data-key="${e(z.key)}" style="left:${z.x * k}px;top:${z.y * k}px" title="Add ${e(z.label)} here" aria-label="Add ${e(z.label)} here"><span class="plus">+</span><span class="lab"> ${e(z.label)}</span></button>`).join('');
    const say = $('bn-say'), p = s.pending;
    say.innerHTML = p ? `<b>${p.kind === 'link' ? `A link from ${e(p.from)}` : `The ${p.kind === 'udp' ? 'OnOff' : 'BulkSend'} application on ${e(p.from)}`}:</b> now choose the host it ${p.kind === 'link' ? 'goes to' : 'sends to'}${zs.length ? '' : ' (no host can take it)'}. <button class="cl" id="bn-cancel">cancel</button>`
      : s.placing ? `<b>${e(N.KINDS.find(q => q[0] === s.placing)[1])}:</b> ${zs.length ? `choose one of the ${zs.length} marked place${zs.length === 1 ? '' : 's'} (Tab and Enter, or a click)` : 'there is no place for one in this network'}. <button class="cl" id="bn-cancel">cancel</button>` : '';
    const task = $('bn-task'); if (task) task.textContent = EV.taskText(N.toBrief());
    const bad = N.problems(), wait = EV.mustWait ? EV.mustWait() : null;
    $('bn-save').disabled = !!s.busy || !!bad.length; $('bn-start').disabled = !!s.busy || !!bad.length || !!wait; $('bn-start').title = wait || '';
    $('bn-state').innerHTML = bad.length ? `<span class="bn-bad"><b>Not ready yet:</b></span><ul id="bn-bad">${bad.map(x => `<li>${e(x)}</li>`).join('')}</ul>` : `Ready: ${s.t.hosts.length} hosts, ${s.t.links.length} links, ${s.t.flows.length} flows; ${Object.keys(s.knobs).length} setting(s) left to the AI.${wait ? ` <b class="warnc" id="be-wait">${e(wait)}</b>` : ''}`;
    $('bn-msg').innerHTML = s.msg ? `<div class="be-msg ${s.msg.bad ? 'bad' : 'ok'}">${e(s.msg.text)}</div>` : '';
  },

  // ---- dragging: a kind from the row (add), or an object of the picture (out of it: remove)
  ghost(text, cls, ev) { let g = document.getElementById('bn-ghost'); if (!text) { if (g) g.remove(); return; } if (!g) { g = document.createElement('div'); g.id = 'bn-ghost'; document.body.appendChild(g); } g.className = 'bn-ghost ' + (cls || ''); g.textContent = text; g.style.left = ev.clientX + 'px'; g.style.top = ev.clientY + 'px'; },
  near(ev) {  // the marked place nearest the pointer, within 90 px (a new host: anywhere on the picture)
    const N = BRIEF_NET, cv = N.node.querySelector('#bn-canvas'), r = cv.getBoundingClientRect(), inside = ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom, zs = N.zones();
    let best = null, bd = 90; N.node.querySelectorAll('.bn-zone').forEach(el => { const b = el.getBoundingClientRect(), d = Math.hypot(ev.clientX - (b.left + b.width / 2), ev.clientY - (b.top + b.height / 2)), z = zs[Number(el.dataset.zone)]; if (z && z.anywhere ? inside : d < bd) { if (!(z && z.anywhere)) bd = d; best = el; } });
    N.node.querySelectorAll('.bn-zone').forEach(el => el.classList.toggle('near', el === best)); cv.classList.toggle('over', inside);
    return { el: best, zone: best ? zs[Number(best.dataset.zone)] : null, inside };
  },
  down(ev) {
    const N = BRIEF_NET, s = N.s, t = ev.target.closest ? ev.target : null; if (!t || ev.button > 0) return;
    const kind = t.closest('.bn-kind'), obj = null;   // an object of the picture is moved, chosen and removed by the drawing surface (brief_canvas.js)
    if (kind) { s.drag = { what: 'kind', kind: kind.dataset.kind, x: ev.clientX, y: ev.clientY, moved: false }; ev.preventDefault(); }
    else if (obj && !t.closest('.bn-zone')) { const [k, id] = obj.dataset.obj.split(':'); s.drag = { what: 'obj', kind: k, id, x: ev.clientX, y: ev.clientY, moved: false }; ev.preventDefault(); }
  },
  move(ev) {
    const N = BRIEF_NET, s = N.s, d = s && s.drag; if (s && s.pending && N.node.isConnected) NETC.bandTo(ev); if (!d || !N.node.isConnected) return;
    if (!d.moved && Math.hypot(ev.clientX - d.x, ev.clientY - d.y) < 6) return;
    if (!d.moved) { d.moved = true; if (d.what === 'kind') { s.placing = d.kind; s.pending = null; N.paint(); } }
    if (d.what === 'kind') { const n = N.near(ev); N.ghost(n.zone ? `release: add ${n.zone.label}` : `${N.KINDS.find(q => q[0] === d.kind)[1]}: move to a marked place`, n.zone ? 'add' : '', ev); }
    else { const n = N.near(ev), gone = N.deps(d.kind, d.id).gone; N.ghost(n.inside ? `drag ${N.says(d.kind, d.id)} out of the picture to remove it` : `release: remove ${gone.map(([k, i]) => N.says(k, i)).join(', ')}`, n.inside ? '' : 'rem', ev); }
  },
  up(ev) {
    const N = BRIEF_NET, s = N.s, d = s && s.drag; if (!d) return; s.drag = null; N.ghost('');
    if (d.what === 'kind') { if (!d.moved) { s.placing = s.placing === d.kind && !s.pending ? null : d.kind; s.pending = null; N.paint(); const z = N.node.querySelector('.bn-zone'); if (z && s.placing) z.focus(); return; }
      const n = N.near(ev); N.node.querySelector('#bn-canvas').classList.remove('over'); if (n.zone) n.zone.go(ev); else { s.placing = null; N.paint(); } return; }
    if (!d.moved) { s.sel = [d.kind, d.id]; N.node.querySelector('#bn-side').innerHTML = N.card(); N.paint(); return; }
    const n = N.near(ev); N.node.querySelector('#bn-canvas').classList.remove('over'); if (!n.inside) N.remove(d.kind, d.id); else N.paint();
  },
  click(ev) {
    const N = BRIEF_NET, s = N.s, t = ev.target, c = sel => (t.closest ? t.closest(sel) : null);
    const z = c('.bn-zone'); if (z) { const zone = N.zones()[Number(z.dataset.zone)]; N.viaKey = ev.detail === 0; if (zone) zone.go(); return; }
    // a kind chosen from the keyboard (Enter or Space on its button sends a click and no pointer event): its places are marked and the first one takes the focus
    const kd = c('.bn-kind'); if (kd && ev.detail === 0) { s.placing = s.placing === kd.dataset.kind && !s.pending ? null : kd.dataset.kind; s.pending = null; N.draw(); const first = N.node.querySelector('.bn-zone'); if (first && s.placing) first.focus(); return; }
    if (c('#bn-cancel')) { s.placing = s.pending = null; N.paint(); return; }
    if (c('#bn-undo')) return N.step(N.past, N.ahead); if (c('#bn-redo')) return N.step(N.ahead, N.past);
    if (c('#bn-simple') || c('#bn-full')) { try { localStorage.setItem('ev-bn-mode', c('#bn-full') ? 'full' : 'simple'); } catch (x) { /* no storage */ } NETC.view = null; return N.draw(); }
    // a part of the structure shown beside the picture (the simple way of drawing): chosen like the part in the picture
    const dp = c('.bn-detail [data-flow], .bn-detail [data-sink], .bn-detail [data-queue]'); if (dp) return N.pick(...(dp.dataset.queue ? ['queue', dp.dataset.queue] : ['flow', dp.dataset.flow || dp.dataset.sink]));
    if (c('#bn-zin')) return NETC.zoom(1.2); if (c('#bn-zout')) return NETC.zoom(1 / 1.2); if (c('#bn-fit')) { NETC.fit(); return N.paint(); }
    // from a host's card: a part of the host opens its own card; an application or a scheduler is added to this host
    const pk = c('[data-pick]'); if (pk) { const [k, i] = pk.dataset.pick.split(':'); return N.pick(k, i); }
    const ap = c('[data-addapp]'); if (ap && s.sel && s.sel[0] === 'host') { const to = (N.node.querySelector('#bn-app-to') || {}).value; if (to) return N.add.app(ap.dataset.addapp, s.sel[1], to); return; }
    const al = c('[data-addlink]'); if (al) { const to = (N.node.querySelector('#bn-link-to') || {}).value; if (to) return N.add.link(al.dataset.addlink, to); return; }
    const aq = c('[data-addq]'); if (aq) { const [l, h] = aq.dataset.addq.split(':'); return N.add.queue(l, h, aq.dataset.qk); }
    if (c('#bn-cond-add')) { const rows = N.condRows(); rows.push(N.condNew(Object.keys(N.outputs(s.t)))); N.condSet(rows); return N.draw(); }
    const crm = c('[data-cond-rm]'); if (crm) { const rows = N.condRows(); rows.splice(Number(crm.dataset.condRm), 1); N.condSet(rows); return N.draw(); }
    const tm = c('[data-time]'); if (tm) { const [fl, p] = tm.dataset.time.split(':'); return N.add.time(fl, p); }
    const ow = c('[data-own]'); if (ow) { const [l, h, p] = ow.dataset.own.split(':'); return N.add.own(l, h, p); }
    const rm = c('[data-remove]'); if (rm) { const [k, id] = rm.dataset.remove.split(':'); return N.remove(k, id); }
    const kn = c('[data-knob]'); if (kn) { const a = kn.dataset.knob; return N.change(() => { if (s.knobs[a]) { delete s.knobs[a]; return; }
      const kind = N.kindOf(a), v = a === 'duration' ? s.duration : EV.netSettings(s.t)[a], name = TH_DATA.KNOB[a] || (a === 'duration' ? 'seconds of measured traffic' : a);
      s.knobs[a] = kind === 'type' ? { choices: N.TCP.slice(), default: v, meaning: `${name} (TCP congestion control)` } : { min: N.RANGE[kind][0], max: N.RANGE[kind][1], default: v, meaning: name }; }); }
    if (c('#bn-describe')) { s.descAuto = true; s.description = N.describe(); return N.draw(); }
    if (c('#bn-save')) return N.save(false); if (c('#bn-start')) return N.save(true);
  },
  input(ev) {
    const N = BRIEF_NET, s = N.s, t = ev.target, f = t.dataset && t.dataset.f, done = ev.type === 'change';
    if (t.id === 'bn-open' && done) return N.open(t.value);
    if (t.id === 'bn-structure') { s.structure = t.checked; return N.draw(); }
    if (t.dataset && t.dataset.ch === 'nw') return setTimeout(N.paintTask, 0);
    if (t.dataset && t.dataset.goal) { s.goal = t.dataset.goal; return N.draw(); }
    // a condition's row: a chosen measure or comparison, or a typed number, rewrites its line (the number is shown in the measure's unit and kept as the harness reads it)
    if (t.dataset && t.dataset.condF) { const [i, part] = t.dataset.condF.split(':'), rows = N.condRows(), r = rows[Number(i)]; if (!r) return;
      if (part === 'text') r.text = t.value; else if (part === 'op') r.op = t.value; else if (part === 'measure') { const shown = N.condShown(r); r.measure = t.value; r.raw = +(shown * N.condUnit(r.measure)[1]).toPrecision(12); }
      else { const v = Number(String(t.value).trim().replace(',', '.')); r.raw = String(t.value).trim() !== '' && isFinite(v) ? +(v * N.condUnit(r.measure)[1]).toPrecision(12) : NaN; }
      N.condSet(rows); if (done && part !== 'value' && part !== 'text') return N.draw();
      const says = N.node.querySelector(`[data-cond-says="${i}"]`); if (says && r.text == null) says.innerHTML = N.condSays(r); return N.paintTask(); }
    if (t.dataset && t.dataset.lock) { s.locked[t.dataset.lock] = t.checked; return; }
    if (t.dataset && t.dataset.qkind && done) return N.change(() => { const q = N.qOf(t.dataset.qkind).q; q.kind = t.value; if (t.value === 'scheduler') { q.parts = q.parts || {}; q.largest_rate = q.largest_rate || {}; } else { delete q.parts; delete q.largest_rate; delete q.classes; } });
    if (t.dataset && t.dataset.qclass && done) { const [qid, fl] = t.dataset.qclass.split(':'); return N.add.queueOf(qid, fl, t.value); }
    // an application changed between UDP and TCP: what it sends is converted where it stands (its name, its hosts and its part of a scheduler stay; the settings of the other kind go)
    // a flow's application (OnOff, BulkSend) and its socket (UDP, TCP) are two choices; BulkSend needs TCP. What both forms have is kept (the rate while it stays OnOff, the TCP type while it stays TCP);
    // "app" is written only where it is not the socket's own (tcp with onoff), so a flow of an older brief is written as it was
    if (t.dataset && (t.dataset.fkind || t.dataset.fapp) && done) return N.change(() => { const fid = t.dataset.fkind || t.dataset.fapp, i = s.t.flows.findIndex(q => q.id === fid), o = s.t.flows[i]; if (i < 0) return;
      const ap = t.dataset.fapp ? t.value : EV.netApp(o), kind = ap === 'bulk' ? 'tcp' : (t.dataset.fkind ? t.value : o.kind), n = { id: o.id, kind }; if (ap === EV.netApp(o) && kind === o.kind) return;
      if (kind === 'tcp' && ap === 'onoff') n.app = 'onoff'; n.from = o.from; n.to = o.to;
      if (ap === 'onoff') { n.rate = o.rate || '100Mbps'; n.packet_bytes = o.packet_bytes || 1400; } if (kind === 'tcp') n.type = o.type || 'TcpCubic';
      EV.NET_TIMES.forEach(p => { if (p in o && (ap === 'onoff' || !['on_time', 'off_time'].includes(p))) n[p] = o[p]; }); s.t.flows[i] = n; });
    if (t.dataset && t.dataset.choice && done) { const a = t.dataset.choice, k = s.knobs[a], list = [...N.node.querySelectorAll(`[data-choice="${a}"]`)].filter(x => x.checked).map(x => x.value); if (!list.length) { t.checked = true; return; } return N.change(() => { k.choices = list; if (!list.includes(k.default)) k.default = list[0]; }); }
    if (!f) return;
    if (f.startsWith('v:')) { const a = f.slice(2), v = N.isText(a) ? t.value : N.num(t.value); s.t = EV.netWith(s.t, { [a]: v }); if (done) { N.past.push(JSON.stringify({ t: s.t, knobs: s.knobs })); N.soon(); } else N.paintTask(); return; }
    if (f.startsWith('k:')) { const [, a, part] = f.split(':'); s.knobs[a][part] = N.isText(a) ? t.value : N.num(t.value); if (done) N.soon(); return; }
    if (f.startsWith('lr:')) { const [, l, fl] = f.split(':'), q = N.qOf(l).q; q.largest_rate = q.largest_rate || {}; if (t.value.trim()) q.largest_rate[fl] = t.value.trim(); else delete q.largest_rate[fl]; if (done) N.soon(); return; }
    if (f.startsWith('most:')) { s.most[f.slice(5)] = t.value; return; }
    s[f] = t.value; if (f === 'description') s.descAuto = !t.value.trim();   // typed: the operator's own text from now on (emptied: written from the network again)
    if (done && ['measure', 'direction', 'tcpBufBytes', 'tcpInitCwnd', 'tcpSack', 'tcpTimestamps', 'tcpDelAck'].includes(f)) return N.soon(); N.paintTask();
  },
  // block 7's "simulations allowed at the start": empty means the brief's limit, and the grey number in the empty field is that limit as it stands now (block 5)
  budgetHint() { const N = BRIEF_NET, f = N.node.querySelector('#bn-flags input[data-k=budget]'); if (f) f.placeholder = String(N.s.sims).trim(); },
  paintTask() { const N = BRIEF_NET, $ = id => N.node.querySelector('#' + id); const task = $('bn-task'); if (task) task.textContent = EV.taskText(N.toBrief()); N.budgetHint(); const bad = N.problems(), wait = EV.mustWait ? EV.mustWait() : null; $('bn-save').disabled = !!N.s.busy || !!bad.length; $('bn-start').disabled = !!N.s.busy || !!bad.length || !!wait; $('bn-state').innerHTML = bad.length ? `<span class="bn-bad"><b>Not ready yet:</b></span><ul id="bn-bad">${bad.map(x => `<li>${EV.e(x)}</li>`).join('')}</ul>` : 'Ready.'; },
  key(ev) {
    const N = BRIEF_NET, s = N.s, t = ev.target, typing = t.matches && t.matches('input, textarea, select'); if (!N.node || !N.node.isConnected || !s) return;
    if (ev.key === 'Escape' && (s.placing || s.pending)) { s.placing = s.pending = null; N.paint(); return; }
    if (typing) return;
    if ((ev.key === 'ArrowLeft' || ev.key === 'ArrowRight') && !ev.ctrlKey && !ev.metaKey && !ev.altKey && !ev.shiftKey) { ev.preventDefault(); return ev.key === 'ArrowLeft' ? N.step(N.past, N.ahead) : N.step(N.ahead, N.past); }   // the left arrow: undo; the right arrow: redo
    if ((ev.key === 'f' || ev.key === 'F') && !ev.ctrlKey && !ev.metaKey && !ev.altKey) { ev.preventDefault(); NETC.fit(); return N.paint(); }   // F: the whole network in view
    if ((ev.key === 'Delete' || ev.key === 'Backspace') && s.sel) { ev.preventDefault(); return N.remove(s.sel[0], s.sel[1]); }
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'z') { ev.preventDefault(); return ev.shiftKey ? N.step(N.ahead, N.past) : N.step(N.past, N.ahead); }
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'y') { ev.preventDefault(); return N.step(N.ahead, N.past); }
  },
  async open(v) {
    const N = BRIEF_NET; if (!v) return;
    if (v === '~default') N.s = N.fresh(JSON.parse(JSON.stringify(N.DEFAULT)));
    else if (v === '~dumbbell') N.s = N.fresh({ hosts: [{ id: 'a' }, { id: 'b' }, { id: 'r' }, { id: 'c' }], links: [{ id: 'la', between: ['a', 'r'], rate: '1Gbps', delay: '50us', mtu: 1500, device_queue: 10 }, { id: 'lb', between: ['b', 'r'], rate: '1Gbps', delay: '50us', mtu: 1500, device_queue: 10 },
      { id: 'lc', between: ['r', 'c'], rate: '100Mbps', delay: '1ms', mtu: 1500, device_queue: 10, queue: { on: 'r', kind: 'scheduler', length: 100, parts: { fa: 0.5, fb: 0.5 }, largest_rate: {} } }], flows: [{ id: 'fa', kind: 'tcp', from: 'a', to: 'c', type: 'TcpCubic' }, { id: 'fb', kind: 'tcp', from: 'b', to: 'c', type: 'TcpCubic' }] });
    else { const b = await EV.json(`../briefs/${v}.json`); if (!b || !EV.net(b)) return; N.s = N.fromBrief(b); }
    N.past = []; N.ahead = []; N.sync(); N.draw();
  },
  async save(start) {
    const N = BRIEF_NET, s = N.s, b = N.toBrief(); s.busy = start ? 'start' : 'save'; s.msg = null; N.paint();
    try { await N.ctx.post('../api/brief', { brief: b }); s.base = b.id; if (!start) { s.busy = ''; s.msg = { text: `Saved as briefs/${b.id}.json.` }; if (N.ctx.after) await N.ctx.after(); N.draw(); return; }
      const r = await N.ctx.post('../api/session', { brief: b.id, ...N.ctx.flags() }); s.busy = ''; s.msg = { text: `Session ${r.id} started on ${b.id}.` }; N.draw(); return N.ctx.started ? N.ctx.started(r.id) : null; }
    catch (x) { s.busy = ''; s.msg = { bad: true, text: `Not saved: ${x.message}` }; N.paint(); }
  },
};
