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
  KINDS: [['host', 'Host', 'a computer; with more than one link it forwards'], ['link', 'Link', 'a point-to-point line between two hosts'], ['udp', 'UDP flow', 'packets at a constant rate from one host to another'],
          ['tcp', 'TCP flow', 'a sender that always has data, from one host to another'], ['queue', 'Queue / scheduler', 'where packets wait on one sending side of a link']],
  TCP: ['TcpCubic', 'TcpNewReno', 'TcpLinuxReno', 'TcpBbr', 'TcpVegas', 'TcpBic'],
  RANGE: { rate: ['10Mbps', '10Gbps'], delay: ['10us', '10ms'], mtu: [576, 1500], device_queue: [1, 1000], length: [4, 1000], parts: [0.05, 4], largest_rate: ['10Mbps', '1Gbps'], packet_bytes: [64, 1400], duration: [2, 30] },
  CSS: `
.bn-pal { display: flex; flex-wrap: wrap; gap: 8px; align-items: stretch; margin: 0 0 8px; } .bn-kind { border: 1px solid var(--border); border-radius: 9px; background: var(--surface-1); padding: 6px 10px; cursor: grab; touch-action: none; user-select: none; text-align: left; font: inherit; max-width: 190px; }
.bn-kind b { display: block; font-size: var(--f-text); } .bn-kind span { font-size: var(--f-note); color: var(--text-secondary); } .bn-kind:hover, .bn-kind:focus-visible { border-color: var(--text-primary); } .bn-kind.on { outline: 2px solid var(--live); }
.bn-acts { margin-left: auto; display: flex; gap: 6px; align-items: center; } .bn-two { display: grid; grid-template-columns: minmax(0, 1000px) minmax(260px, 1fr); gap: 8px 20px; align-items: start; } @media (max-width: 1100px) { .bn-two { grid-template-columns: minmax(0, 1fr); } }
.bn-canvas { position: relative; border: 1px dashed var(--border); border-radius: 10px; background: var(--surface-0); min-height: 150px; touch-action: none; } .bn-canvas.over { border-color: var(--live); }
.bn-canvas svg { display: block; } .bn-canvas [data-obj] { cursor: grab; } .bn-canvas .sel rect, .bn-canvas .sel circle, .bn-canvas g.sel > text.sn { stroke: var(--text-primary); stroke-width: 2.2; }
.bn-zone { position: absolute; transform: translate(-50%, -50%); border: 1.5px dashed var(--text-secondary); border-radius: 999px; background: var(--surface-1); color: var(--text-secondary); min-width: 26px; height: 26px; padding: 0 7px; font: inherit; font-size: var(--f-note); line-height: 22px; white-space: nowrap; cursor: pointer; opacity: .75; z-index: 2; }
.bn-zone.near, .bn-zone:focus-visible { border: 2px solid var(--live); background: var(--live); color: #fff; opacity: 1; font-weight: 700; z-index: 3; } .bn-zone .plus { font-weight: 700; } .bn-zone .lab { display: none; } .bn-zone.near .lab, .bn-zone:focus-visible .lab, .bn-zone:hover .lab { display: inline; }
.bn-ghost { position: fixed; z-index: 50; pointer-events: none; transform: translate(12px, 12px); border-radius: 8px; padding: 4px 9px; font-size: var(--f-note); background: var(--text-primary); color: var(--surface-0); max-width: 340px; }
.bn-ghost.add { background: var(--live); color: #fff; } .bn-ghost.rem { background: var(--critical); color: #fff; } .bn-say { min-height: 20px; margin: 6px 0 0; }
.bn-card { border: 1px solid var(--border); border-radius: 10px; background: var(--surface-1); padding: 8px 12px; } .bn-card h4 { margin: 0 0 6px; font-size: var(--f-text); } .bn-row { display: grid; grid-template-columns: 128px 30px minmax(0, 1fr); gap: 4px 8px; align-items: center; margin: 3px 0; }
.bn-row input[type=text] { width: 100%; box-sizing: border-box; } .bn-row .tri { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; } .bn-row small { color: var(--text-secondary); font-size: var(--f-note); } .bn-who { border: 1px solid var(--border); border-radius: 6px; background: var(--surface-0); cursor: pointer; font: inherit; height: 24px; }
.bn-bad { color: var(--critical); } .bn-list td { padding: 2px 10px 2px 0; vertical-align: top; }`,
  DEFAULT: { hosts: [{ id: 'sender' }, { id: 'receiver' }],
             links: [{ id: 'l1', between: ['sender', 'receiver'], rate: '1Gbps', delay: '50us', mtu: 1500, device_queue: 10, queue: { on: 'sender', kind: 'scheduler', length: 100, parts: { udp: 0.5, tcp: 0.5 }, largest_rate: {} } }],
             flows: [{ id: 'udp', kind: 'udp', from: 'sender', to: 'receiver', rate: '2Gbps', packet_bytes: 1400 }, { id: 'tcp', kind: 'tcp', from: 'sender', to: 'receiver', type: 'TcpCubic' }] },

  mount(host, ctx) {
    const N = BRIEF_NET; N.ctx = ctx;
    if (!document.getElementById('bn-css')) { const st = document.createElement('style'); st.id = 'bn-css'; st.textContent = N.CSS; document.head.appendChild(st); }
    if (!N.node) {
      N.node = document.createElement('div'); N.node.className = 'be bn'; N.s = N.fresh(JSON.parse(JSON.stringify(N.DEFAULT)));
      N.node.addEventListener('pointerdown', N.down); N.node.addEventListener('click', N.click); N.node.addEventListener('input', N.input); N.node.addEventListener('change', N.input);
      document.addEventListener('keydown', N.key);  // on the document: a click on the picture chooses an object without giving the form the focus, and Delete must still reach it
      window.addEventListener('pointermove', N.move); window.addEventListener('pointerup', N.up);
    }
    if (N.node.parentNode !== host) { host.appendChild(N.node); N.draw(); } else N.paint();
  },
  fresh(t) { return { t, knobs: {}, id: '', description: '', goal: 'open', measure: '', direction: 'max', conds: '', tolerance: '', sims: '40', per: '12', duration: '10', seed: '1', sel: null, placing: null, pending: null, drag: null, msg: null, busy: '', base: '', structure: false, most: { hosts: '', links: '', flows: '' }, locked: {} }; },

  // ---- the network as data
  newId(prefix) { const N = BRIEF_NET, t = N.s.t, all = new Set([...t.hosts, ...t.links, ...t.flows].map(x => x.id)); let i = 1; while (all.has(prefix + i)) i++; return prefix + i; },
  linkOf(id) { return BRIEF_NET.s.t.links.find(l => l.id === id); },
  // which flows pass each described queue (they are sent on that link by the queue's host)
  passing(t) { const out = {}; t.links.forEach(l => { if (l.queue) out[l.id] = []; }); t.flows.forEach(f => (EV.netPath(t, f) || []).forEach(([l, from]) => { const L = t.links.find(x => x.id === l); if (L.queue && L.queue.on === from) out[l].push(f.id); })); return out; },
  // after every change: a scheduler has a part for exactly the flows that pass it; a knob whose setting is gone is dropped
  sync() {
    const N = BRIEF_NET, s = N.s, t = s.t, through = N.passing(t);
    t.links.forEach(l => { const q = l.queue; if (!q || q.kind !== 'scheduler') return; const old = q.parts || {}, vals = Object.values(old), fill = vals.length ? Math.round(1000 * vals.reduce((a, b) => a + b, 0) / vals.length) / 1000 : 0.5;
      q.parts = Object.fromEntries(through[l.id].map(f => [f, f in old ? old[f] : fill])); q.largest_rate = Object.fromEntries(Object.entries(q.largest_rate || {}).filter(([f]) => f in q.parts)); });
    const have = EV.netSettings(t); Object.keys(s.knobs).forEach(k => { if (!(k in have) && k !== 'duration') delete s.knobs[k]; });
    const outs = Object.keys(N.outputs(t)); if (!outs.includes(s.measure)) s.measure = outs.find(o => /_goodput_bps$/.test(o)) || outs[0] || '';
    if (s.sel && !N.find(s.sel)) s.sel = null;
  },
  find(sel) { const N = BRIEF_NET, t = N.s.t, [kind, id] = sel || []; return kind === 'host' ? t.hosts.find(h => h.id === id) : kind === 'link' ? t.links.find(l => l.id === id) : kind === 'flow' ? t.flows.find(f => f.id === id) : kind === 'queue' ? (N.linkOf(id) || {}).queue : null; },
  // the measures of the network, as harness/network.py names them
  outputs(t) {
    const out = {};
    t.flows.forEach(f => { out[`${f.id}_goodput_bps`] = 1; out[f.kind === 'udp' ? `${f.id}_loss_frac` : `${f.id}_retrans`] = 1; });
    t.links.forEach(l => { const q = l.queue; out[`${l.id}_util`] = 1; out[`${l.id}_util_back`] = 1; if (q && q.kind === 'scheduler') Object.keys(q.parts || {}).forEach(f => { out[`${l.id}_drops_${f}`] = 1; }); else out[`${l.id}_drops`] = 1; out[`${l.id}_drops_back`] = 1; });
    return out;
  },
  // what goes with an object when it is removed: [[kind, id], ...] (the object itself first)
  deps(kind, id) {
    const N = BRIEF_NET, t = JSON.parse(JSON.stringify(N.s.t)), gone = [[kind, id]];
    if (kind === 'host') { t.links.filter(l => l.between.includes(id)).forEach(l => gone.push(['link', l.id])); t.hosts = t.hosts.filter(h => h.id !== id); t.links = t.links.filter(l => !l.between.includes(id)); t.flows.filter(f => f.from === id || f.to === id).forEach(f => gone.push(['flow', f.id])); t.flows = t.flows.filter(f => f.from !== id && f.to !== id); }
    if (kind === 'link') t.links = t.links.filter(l => l.id !== id);
    if (kind === 'flow') t.flows = t.flows.filter(f => f.id !== id);
    if (kind === 'queue') delete t.links.find(l => l.id === id).queue;
    t.flows.filter(f => !EV.netPath(t, f)).forEach(f => { gone.push(['flow', f.id]); }); t.flows = t.flows.filter(f => EV.netPath(t, f));  // a flow that has no way any more goes too
    return { gone, t };
  },
  change(fn) { const N = BRIEF_NET, s = N.s; N.past.push(JSON.stringify({ t: s.t, knobs: s.knobs })); if (N.past.length > 50) N.past.shift(); N.ahead = []; fn(); N.sync(); s.msg = null; N.draw(); },
  step(from, to) { const N = BRIEF_NET, s = N.s; if (!from.length) return; to.push(JSON.stringify({ t: s.t, knobs: s.knobs })); const o = JSON.parse(from.pop()); s.t = o.t; s.knobs = o.knobs; s.placing = s.pending = null; N.sync(); N.draw(); },
  remove(kind, id) { const N = BRIEF_NET, d = N.deps(kind, id); N.change(() => { N.s.t = d.t; N.s.sel = null; }); },
  add: {
    host() { const N = BRIEF_NET, id = N.newId('h'); N.change(() => { N.s.t.hosts.push({ id }); N.s.sel = ['host', id]; }); },
    link(a, b) { const N = BRIEF_NET, id = N.newId('l'); N.change(() => { N.s.t.links.push({ id, between: [a, b], rate: '1Gbps', delay: '50us', mtu: 1500, device_queue: 10 }); N.s.sel = ['link', id]; }); },
    flow(kind, from, to) { const N = BRIEF_NET, id = N.newId(kind === 'udp' ? 'u' : 't'); N.change(() => { N.s.t.flows.push(kind === 'udp' ? { id, kind, from, to, rate: '100Mbps', packet_bytes: 1400 } : { id, kind, from, to, type: 'TcpCubic' }); N.s.sel = ['flow', id]; }); },
    queue(link, on) { const N = BRIEF_NET; N.change(() => { N.linkOf(link).queue = { on, kind: 'scheduler', length: 100, parts: {}, largest_rate: {} }; N.s.sel = ['queue', link]; }); },
  },
  focusZone() { const N = BRIEF_NET; if (N.viaKey) { const z = N.node.querySelector('.bn-zone'); if (z) z.focus(); } },
  says(kind, id) { return kind === 'queue' ? `the queue of link ${id}` : `${kind} ${id}`; },

  // ---- where an object of a kind can go now: [{ key, x, y (the picture's units), label, go() }]
  zones() {
    const N = BRIEF_NET, s = N.s, t = s.t, G = EV.netGeom(t), mid = h => ({ x: G.pos[h].x + G.pos[h].w / 2, y: G.pos[h].y + G.pos[h].h / 2 }), kind = s.placing, p = s.pending;
    const linked = (a, b) => t.links.some(l => l.between.includes(a) && l.between.includes(b)), hosts = t.hosts.map(h => h.id);
    if (p && p.kind === 'link') return hosts.filter(h => h !== p.from && !linked(h, p.from)).map(h => ({ key: 'to-' + h, ...mid(h), label: `link ${p.from} – ${h}`, go: () => { s.pending = s.placing = null; N.add.link(p.from, h); } }));
    if (p) return hosts.filter(h => h !== p.from && EV.netPath(t, { from: p.from, to: h })).map(h => ({ key: 'to-' + h, ...mid(h), label: `${p.kind.toUpperCase()} flow ${p.from} → ${h}`, go: () => { s.pending = s.placing = null; N.add.flow(p.kind, p.from, h); } }));
    if (kind === 'host') return [{ key: 'new-host', x: G.W / 2, y: 22, label: 'a new host', anywhere: true, go: () => { s.placing = null; N.add.host(); } }];
    if (kind === 'link') return hosts.filter(h => hosts.some(o => o !== h && !linked(h, o))).map(h => ({ key: 'from-' + h, ...mid(h), label: `a link from ${h}`, go: () => { s.pending = { kind: 'link', from: h }; N.draw(); N.focusZone(); } }));
    if (kind === 'udp' || kind === 'tcp') return hosts.filter(h => hosts.some(o => o !== h && EV.netPath(t, { from: h, to: o }))).map(h => ({ key: 'from-' + h, ...mid(h), label: `a ${kind.toUpperCase()} flow from ${h}`, go: () => { s.pending = { kind, from: h }; N.draw(); N.focusZone(); } }));
    if (kind === 'queue') return t.links.filter(l => !l.queue && G.ends[l.id]).flatMap(l => { const E = G.ends[l.id], len = Math.hypot(E.x2 - E.x1, E.y2 - E.y1) || 1, ux = (E.x2 - E.x1) / len, uy = (E.y2 - E.y1) / len;
      return [[E.a, E.x1 + 30 * ux, E.y1 + 30 * uy], [E.c, E.x2 - 30 * ux, E.y2 - 30 * uy]].map(([h, x, y]) => ({ key: `q-${l.id}-${h}`, x, y, label: `a scheduler on ${h}'s side of ${l.id}`, go: () => { s.placing = null; N.add.queue(l.id, h); } })); });
    return [];
  },

  // ---- what cannot be saved, said in words (the harness checks again when the brief is saved)
  problems() {
    const N = BRIEF_NET, s = N.s, t = s.t, bad = [];
    if (t.hosts.length < 2 || !t.links.length || !t.flows.length) bad.push('A network needs at least two hosts, one link and one flow.');
    t.hosts.filter(h => !t.links.some(l => l.between.includes(h.id))).forEach(h => bad.push(`Host ${h.id} has no link.`));
    t.flows.forEach(f => { const adj = {}; t.hosts.forEach(h => { adj[h.id] = []; }); t.links.forEach(l => { adj[l.between[0]].push(l.between[1]); adj[l.between[1]].push(l.between[0]); });
      const dist = { [f.from]: 0 }, ways = { [f.from]: 1 }; let fr = [f.from]; while (fr.length) { const nx = []; fr.forEach(h => adj[h].forEach(o => { if (!(o in dist)) { dist[o] = dist[h] + 1; ways[o] = ways[h]; nx.push(o); } else if (dist[o] === dist[h] + 1) ways[o] += ways[h]; })); fr = nx; }
      if (!(f.to in dist)) bad.push(`Flow ${f.id} has no way from ${f.from} to ${f.to}.`); else if (ways[f.to] > 1) bad.push(`Flow ${f.id} has ${ways[f.to]} equally short ways from ${f.from} to ${f.to}: remove a link so that there is one.`); });
    const through = N.passing(t); t.links.forEach(l => { if (l.queue && l.queue.kind === 'scheduler' && !through[l.id].length) bad.push(`No flow passes the scheduler of link ${l.id}: put it on the side that sends, make it a plain queue, or remove it.`); });
    if (t.hosts.length > 8 || t.links.length > 12 || t.flows.length > 8) bad.push('A network holds at most 8 hosts, 12 links and 8 flows.');
    if (!s.description.trim()) bad.push('The description is empty (block 4).');
    if (!/^[a-z0-9][a-z0-9_-]{1,59}$/.test(s.id.trim())) bad.push('The brief needs a name of 2 to 60 lower-case letters, digits, - and _ (above).');
    return bad;
  },
  num(v) { const x = String(v).trim(); return x !== '' && isFinite(Number(x)) ? Number(x) : x; },
  kindOf(addr) { const p = addr.split('.'); return addr === 'duration' ? 'duration' : p.includes('largest_rate') ? 'largest_rate' : p.includes('parts') ? 'parts' : p[p.length - 1]; },
  isText(addr) { return ['rate', 'delay', 'largest_rate', 'type'].includes(BRIEF_NET.kindOf(addr)); },
  toBrief() {
    const N = BRIEF_NET, s = N.s, t = JSON.parse(JSON.stringify(s.t)), cast = (k, v) => (N.isText(k) ? String(v).trim() : N.num(v));
    const have = EV.netSettings(t), fixed = {}; Object.keys(have).forEach(k => { fixed[k] = cast(k, have[k]); }); const net = EV.netWith(t, fixed);
    const knobs = {}; Object.entries(s.knobs).forEach(([k, q]) => { knobs[k] = q.choices ? { choices: q.choices, default: q.default, meaning: q.meaning } : { min: cast(k, q.min), max: cast(k, q.max), default: cast(k, q.default), meaning: q.meaning }; });
    const goal = s.goal === 'open' ? { kind: 'open' } : { kind: 'given', target: { measure: s.measure, direction: s.direction }, conditions: s.conds.split('\n').map(c => c.trim()).filter(Boolean), ...(String(s.tolerance).trim() ? { tolerance: N.num(s.tolerance) } : {}) };
    const b = { id: s.id.trim(), description: s.description.trim(), topology: net, system: { seed: N.num(s.seed), ...('duration' in knobs ? {} : { duration: N.num(s.duration) }) }, knobs, goal, limits: { simulations: N.num(s.sims), simulations_per_experiment: N.num(s.per) } };
    if (s.structure) b.structure = { may_change: true, most: Object.fromEntries(Object.entries(s.most).filter(([, v]) => String(v).trim()).map(([k, v]) => [k, N.num(v)])), locked: Object.keys(s.locked).filter(k => s.locked[k]) };
    return b;
  },
  fromBrief(b) {
    const N = BRIEF_NET, s = N.fresh(JSON.parse(JSON.stringify(b.topology))), g = b.goal || {}, st = b.structure || {};
    Object.assign(s, { knobs: JSON.parse(JSON.stringify(b.knobs || {})), description: b.description || '', goal: g.kind === 'given' ? 'given' : 'open', measure: (g.target || {}).measure || '', direction: (g.target || {}).direction || 'max', conds: (g.conditions || []).join('\n'), tolerance: g.tolerance == null ? '' : String(g.tolerance),
      sims: String((b.limits || {}).simulations ?? 40), per: String((b.limits || {}).simulations_per_experiment ?? 12), seed: String((b.system || {}).seed ?? 1), duration: String((b.system || {}).duration ?? ((b.knobs || {}).duration || {}).default ?? 10), base: b.id || '',
      structure: !!st.may_change, most: { hosts: String((st.most || {}).hosts ?? ''), links: String((st.most || {}).links ?? ''), flows: String((st.most || {}).flows ?? '') }, locked: Object.fromEntries((st.locked || []).map(k => [k, true])) });
    return s;
  },
  // a description written from the network, to start from: each setting by its name in braces, so that it stays true whoever decides it
  describe() {
    const N = BRIEF_NET, t = N.s.t;
    const links = t.links.map(l => { const q = l.queue; return `Link ${l.id} joins ${l.between[0]} and ${l.between[1]}: it carries {${l.id}.rate} with a one-way delay of {${l.id}.delay}.${q ? (q.kind === 'scheduler' ? ` On ${q.on}'s side a scheduler divides it between ${Object.keys(q.parts || {}).join(' and ') || 'its flows'} by the parts ${Object.keys(q.parts || {}).map(f => `{${l.id}.queue.parts.${f}}`).join(' : ')} (the parts are divided by their sum); each of them waits in a queue of {${l.id}.queue.length} packets, and a packet that arrives at a full queue is dropped. How the scheduler behaves when one of them has less to send than its part allows is not described here; finding that out is part of the work.` : ` On ${q.on}'s side packets wait in one queue of {${l.id}.queue.length} packets; a packet that arrives when it is full is dropped.`) : ''}`; });
    const flows = t.flows.map(f => (f.kind === 'udp' ? `Flow ${f.id} is UDP from ${f.from} to ${f.to}: packets of {${f.id}.packet_bytes} bytes at a constant rate ({${f.id}.rate}).` : `Flow ${f.id} is TCP from ${f.from} to ${f.to}: it always has data to send; its congestion control is {${f.id}.type}.`));
    return `A network of ${t.hosts.length} hosts: ${t.hosts.map(h => h.id).join(', ')}. ${links.join(' ')} ${flows.join(' ')} A host with more than one link forwards packets. In each simulation the flows start within the first 10 ms, traffic runs for one second that is not measured, and then for duration seconds, over which the outputs are measured.`;
  },

  // ---- the page
  field(f, v, hint) { return `<input type="text" data-f="${f}" value="${EV.e(v ?? '')}" placeholder="${EV.e(hint || '')}">`; },
  // one setting of an object, in its card: who decides it (✧ the operator: one value; ✦ the AI: lowest, highest, where it starts; a TCP type: the list it may choose from)
  row(addr, label, value) {
    const N = BRIEF_NET, e = EV.e, k = N.s.knobs[addr], kind = N.kindOf(addr);
    const who = `<button class="bn-who" data-knob="${e(addr)}" title="${k ? 'The AI may change it. Click: fixed by the operator' : 'Fixed by the operator. Click: the AI may change it'}">${k ? '✦' : '✧'}</button>`;
    const body = !k ? (kind === 'type' ? `<select data-f="v:${e(addr)}">${N.TCP.map(c => `<option${c === value ? ' selected' : ''}>${c}</option>`).join('')}</select>` : N.field('v:' + addr, value))
      : k.choices ? `<span data-choices="${e(addr)}">${N.TCP.map(c => `<label style="font-weight:400;display:inline-block;margin-right:8px"><input type="checkbox" data-choice="${e(addr)}" value="${c}"${k.choices.includes(c) ? ' checked' : ''}> ${c.replace(/^Tcp/, '')}</label>`).join('')}<small>starts at ${e(String(k.default).replace(/^Tcp/, ''))}</small></span>`
      : `<span class="tri">${N.field(`k:${addr}:min`, k.min, 'lowest')}${N.field(`k:${addr}:max`, k.max, 'highest')}${N.field(`k:${addr}:default`, k.default, 'starts at')}</span>`;
    return `<div class="bn-row" data-row="${e(addr)}"><span>${e(label)}</span>${who}${body}</div>${k && !k.choices ? '<div class="bn-row"><span></span><span></span><small>lowest · highest · starts at</small></div>' : ''}`;
  },
  card() {
    const N = BRIEF_NET, s = N.s, t = s.t, e = EV.e, sel = s.sel, o = N.find(sel);
    if (!o) return `<div class="bn-card" id="bn-card"><p class="sm mut">Click an object of the picture to see and set its values. Drag a kind from the row above onto the picture to add one; drag an object out of the picture to remove it.</p></div>`;
    const [kind, id] = sel, d = N.deps(kind, id).gone.slice(1), rm = `<p style="margin:8px 0 0"><button data-remove="${e(kind)}:${e(id)}">Remove ${e(N.says(kind, id))}</button>${d.length ? ` <span class="sm">also removes ${e(d.map(([k, i]) => N.says(k, i)).join(', '))}</span>` : ''}</p>`;
    const lock = s.structure ? `<p class="sm" style="margin:6px 0 0"><label style="font-weight:400"><input type="checkbox" data-lock="${e(kind)}:${e(id)}"${s.locked[`${kind}:${id}`] ? ' checked' : ''}> the AI may not remove or change this object</label></p>` : '';
    let rows = '';
    if (kind === 'host') rows = `<p class="sm">${t.links.filter(l => l.between.includes(id)).length} link(s), ${t.flows.filter(f => f.from === id).length} flow(s) sent, ${t.flows.filter(f => f.to === id).length} received. A host has no setting of its own.</p>`;
    if (kind === 'link') rows = N.row(`${id}.rate`, 'rate', o.rate) + N.row(`${id}.delay`, 'one-way delay', o.delay) + N.row(`${id}.mtu`, 'largest packet, bytes', o.mtu) + N.row(`${id}.device_queue`, 'device queue, packets', o.device_queue) + `<p class="sm">between ${e(o.between[0])} and ${e(o.between[1])}${o.queue ? '' : ' · a plain queue of 100 packets on each side'}</p>`;
    if (kind === 'flow') rows = (o.kind === 'udp' ? N.row(`${id}.rate`, 'rate', o.rate) + N.row(`${id}.packet_bytes`, 'packet size, bytes', o.packet_bytes) : N.row(`${id}.type`, 'TCP type', o.type)) + `<p class="sm">${e(o.kind.toUpperCase())} from ${e(o.from)} to ${e(o.to)}</p>`;
    if (kind === 'queue') rows = `<div class="bn-row"><span>kind</span><span></span><select data-qkind="${e(id)}"><option value="scheduler"${o.kind === 'scheduler' ? ' selected' : ''}>scheduler: a part of the link for each flow</option><option value="fifo"${o.kind === 'fifo' ? ' selected' : ''}>plain queue: first in, first out</option></select></div>`
      + N.row(`${id}.queue.length`, 'length, packets', o.length) + (o.kind === 'scheduler' ? Object.keys(o.parts || {}).map(f => N.row(`${id}.queue.parts.${f}`, `part of ${f}`, o.parts[f]) + `<div class="bn-row"><span>largest rate of ${e(f)}</span><span></span>${N.field(`lr:${id}:${f}`, (o.largest_rate || {})[f] || '', 'none')}</div>`).join('') : '')
      + `<p class="sm">on ${e(o.on)}'s side of link ${e(id)}${o.kind === 'scheduler' ? ' · the parts are divided by their sum' : ''}</p>`;
    return `<div class="bn-card" id="bn-card" data-sel="${e(kind)}:${e(id)}"><h4>${e(kind === 'queue' ? `Queue of link ${id}` : `${kind[0].toUpperCase()}${kind.slice(1)} ${id}`)}</h4>${rows}${lock}${rm}</div>`;
  },
  canvas() {
    const N = BRIEF_NET, s = N.s, b = { topology: s.t, knobs: s.knobs }, svg = EV.netSvg(b, { max: 1000 });
    return `<div class="bn-canvas" id="bn-canvas">${svg || '<p class="sm" style="padding:16px">An empty network: drag a host here.</p>'}<div id="bn-zones"></div></div>`;
  },
  draw() {
    const N = BRIEF_NET, s = N.s, e = EV.e, briefs = ((N.ctx.st || {}).briefs || []), nw = EV.nw, outs = Object.keys(N.outputs(s.t)), have = EV.netSettings(s.t);
    const sched = s.t.links.some(l => l.queue && l.queue.kind === 'scheduler'), name = k => (TH_DATA.KNOB[k] || k);
    EV.netApply({ id: 'setup-' + Date.now(), topology: s.t });
    const pal = `<div class="bn-pal" id="bn-pal">${N.KINDS.map(([k, title, says]) => `<button class="bn-kind${s.placing === k ? ' on' : ''}" data-kind="${k}" title="Drag it onto the picture, or press Enter and choose a place"><b>+ ${title}</b><span>${says}</span></button>`).join('')}
      <span class="bn-acts"><button id="bn-undo"${N.past.length ? '' : ' disabled'}>Undo</button><button id="bn-redo"${N.ahead.length ? '' : ' disabled'}>Redo</button></span></div>`;
    const b1 = `${pal}<div class="bn-two"><div>${N.canvas()}<p class="sm bn-say" id="bn-say"></p></div><div id="bn-side">${N.card()}</div></div>`;
    const who = k => (s.knobs[k] ? `<td>${e(s.knobs[k].choices ? 'one of ' + s.knobs[k].choices.map(c => c.replace(/^Tcp/, '')).join(', ') : `${s.knobs[k].min} to ${s.knobs[k].max}, starts at ${s.knobs[k].default}`)}</td><td>✦ the AI</td>` : `<td><b>${e(have[k])}</b></td><td>✧ the operator</td>`);
    const b2 = `<table class="bn-list" id="bn-who"><tbody>${Object.keys(have).map(k => `<tr data-k="${e(k)}"><td>${e(name(k))}</td>${who(k)}</tr>`).join('')}
        <tr data-k="duration"><td>measured time, s</td><td>${s.knobs.duration ? `${e(s.knobs.duration.min)} to ${e(s.knobs.duration.max)}, starts at ${e(s.knobs.duration.default)}` : N.field('duration', s.duration)}</td><td><button class="bn-who" data-knob="duration">${s.knobs.duration ? '✦' : '✧'}</button> ${s.knobs.duration ? 'the AI' : 'the operator'}</td></tr>
        <tr data-k="seed"><td>seed</td><td>${N.field('seed', s.seed)}</td><td>✧ the operator</td></tr></tbody></table>
      <p class="sm">A setting is changed in its object's card (block 1): click the object, then ✧ or ✦.</p>
      <p style="margin-top:8px"><label style="font-weight:400"><input type="checkbox" id="bn-structure"${s.structure ? ' checked' : ''}> <b>The AI may change the structure</b>: add and remove hosts, links, flows and queues in the simulations it asks for</label></p>
      ${s.structure ? `<div class="bn-row" style="grid-template-columns:auto 80px 80px 80px"><span>at most (empty: 8 hosts, 12 links, 8 flows)</span>${['hosts', 'links', 'flows'].map(k => N.field('most:' + k, s.most[k], k)).join('')}</div><p class="sm">An object can be kept from it: click the object, then tick “the AI may not remove or change this object”. What the aim names is kept by itself.</p>` : ''}`;
    const b3 = `<div class="be-aim" id="bn-aim"><label><input type="radio" name="bn-goal" data-goal="open"${s.goal === 'open' ? ' checked' : ''}> <b>open</b>: the AI chooses its own aim and has to justify it</label><label><input type="radio" name="bn-goal" data-goal="given"${s.goal === 'given' ? ' checked' : ''}> a target with conditions</label></div>
      ${s.goal === 'given' ? `<div class="be-two"><label>Target<small>the measure to make as large or as small as possible</small><select data-f="measure">${outs.map(k => `<option value="${e(k)}"${k === s.measure ? ' selected' : ''}>${e(TH_DATA.PLAIN[k] || k)}</option>`).join('')}</select></label>
        <label>Direction<select data-f="direction"><option value="max"${s.direction === 'max' ? ' selected' : ''}>as large as possible</option><option value="min"${s.direction === 'min' ? ' selected' : ''}>as small as possible</option></select></label>
        <label style="grid-column:1/-1">Conditions<small>one on each line: a measure, a comparison, a number, for example ${e(outs.find(o => /_loss_frac$/.test(o)) || outs[0] || 'measure')} &lt;= 0.01 · the measures: ${e(outs.join(', '))}</small><textarea data-f="conds" rows="2">${e(s.conds)}</textarea></label>
        <label>Tolerance, per cent (optional)<small>two results closer than this count as equal</small>${N.field('tolerance', s.tolerance, 'none')}</label></div>` : ''}`;
    const b4 = `<div class="be-two"><label>The task<small>written by the harness from the aim and the settings the AI may change</small><span id="bn-task" class="be-task" data-own="harness"></span></label>
        <label>The description of the system<small>plain words; a setting's address in braces is filled with its value where it is fixed and reads “the knob …” where the AI may change it <button class="cl" id="bn-describe" type="button">write it from the network</button></small><textarea data-f="description" rows="5">${e(s.description)}</textarea></label></div>`;
    const b5 = `<div class="be-two"><label>Simulations in all${N.field('sims', s.sims, 'e.g. 40')}</label><label>In one turn${N.field('per', s.per, 'e.g. 12')}</label></div>`;
    const pol = (v, says) => `<label style="font-weight:400;margin:3px 0;display:block"><input type="radio" name="nw-policy" data-ch="nw" data-k="policy" value="${v}"${nw.policy === v ? ' checked' : ''}> <b>${v}</b> <span class="sm" style="display:inline">${says}</span></label>`;
    const b6 = sched ? `<div id="bn-policy" data-by="operator">${pol('share', 'what one flow leaves unused goes to the others · the default')}${pol('cap', 'each flow is held to its part, whatever the others send')}${pol('prio', 'the first flow of a scheduler\'s list goes first; the parts are not used')}${pol('random', 'the harness chooses share or cap')}<p class="sm">How a scheduler divides its link is never told to the AI.</p></div>` : '<p class="sm" id="bn-policy">This network has no scheduler: there is no scheduling policy to choose.</p>';
    const fl = (label, html, note) => `<div><span>${label}</span>${html}<span>${note}</span></div>`;
    const b7 = `<div class="kv" id="bn-flags">${fl('simulations allowed at the start', `<input type="number" min="1" data-ch="nw" data-k="budget" value="${e(nw.budget)}" placeholder="${e(s.sims)}">`, "default: the brief's limit")}
        ${fl('draft before the answer', `<select data-ch="nw" data-k="draft"><option${nw.draft === 'on' ? ' selected' : ''}>on</option><option${nw.draft === 'off' ? ' selected' : ''}>off</option></select>`, 'default: on')}
        ${fl('baseline simulation first', `<label style="font-weight:400"><input type="checkbox" data-ch="nw" data-k="baseline"${nw.baseline ? ' checked' : ''}> run it</label>`, 'default: on')}</div>`;
    const nets = (N.ctx.st || {}).network_briefs || [];
    const top = `<div class="be-top"><div><label>Start from<small>a saved brief that has a network, or one of two examples</small><select id="bn-open"><option value="">choose…</option><option value="~default">example: two hosts, one link (UDP and TCP)</option><option value="~dumbbell">example: two senders through a third host</option>${nets.map(b => `<option value="${e(b)}"${b === s.base ? ' selected' : ''}>${e(b)}</option>`).join('')}</select></label></div>
        <label>Name of the new brief<small>lower-case letters, digits, - and _ · a saved brief is never overwritten</small>${N.field('id', s.id, 'e.g. three-hosts')}</label></div>`;
    const blk = (i, body, cls) => EV.setBlock(i, body, { says: true, cls });
    const first = blk(0, b1, 'st-wide').replace(/(<p class="st-says[^>]*>)[^<]*/, '$1Hosts, links, flows and queues. Drag a kind onto the picture to add one; drag an object out of the picture to remove it.');
    N.node.innerHTML = `${top}<div class="st" id="st-blocks">${first}${blk(1, b2)}${blk(2, b3)}${blk(3, b4, 'st-told')}<div class="st-row st-low">${blk(4, b5)}${blk(5, b6)}${blk(6, b7)}</div></div>
      <div class="be-start" id="bn-start-box"><div id="bn-state" class="sm"></div><div id="bn-msg"></div><p style="margin-top:8px"><button id="bn-save">Save as new brief</button> <button class="big primary" id="bn-start">Save and start the session</button></p></div>`;
    N.paint();
  },
  // what follows the values, in place: the drop places, the chosen object's mark, the task, what cannot be saved yet
  paint() {
    const N = BRIEF_NET, s = N.s, e = EV.e, $ = id => N.node.querySelector('#' + id), cv = $('bn-canvas'), svg = cv && cv.querySelector('svg'); if (!cv) return;
    cv.querySelectorAll('[data-host]').forEach(g => { g.dataset.obj = 'host:' + g.dataset.host; g.classList.toggle('sel', !!s.sel && s.sel[0] === 'host' && s.sel[1] === g.dataset.host); });
    cv.querySelectorAll('.nl[data-link]').forEach(g => { g.dataset.obj = 'link:' + g.dataset.link; g.classList.toggle('sel', !!s.sel && s.sel[0] === 'link' && s.sel[1] === g.dataset.link); });
    cv.querySelectorAll('.nq').forEach(g => { g.dataset.obj = 'queue:' + g.dataset.queue; g.classList.toggle('sel', !!s.sel && s.sel[0] === 'queue' && s.sel[1] === g.dataset.queue); });
    cv.querySelectorAll('.nh g[data-flow]').forEach(g => { if (s.t.flows.find(f => f.id === g.dataset.flow && f.from === g.parentNode.dataset.host)) g.dataset.obj = 'flow:' + g.dataset.flow; });
    const zs = N.zones(), box = $('bn-zones'), k = svg ? svg.getBoundingClientRect().width / svg.viewBox.baseVal.width : 1;
    box.innerHTML = zs.map((z, i) => `<button class="bn-zone" data-zone="${i}" data-key="${e(z.key)}" style="left:${z.x * k}px;top:${z.y * k}px" title="Add ${e(z.label)} here" aria-label="Add ${e(z.label)} here"><span class="plus">+</span><span class="lab"> ${e(z.label)}</span></button>`).join('');
    const say = $('bn-say'), p = s.pending;
    say.innerHTML = p ? `<b>${p.kind === 'link' ? `A link from ${e(p.from)}` : `A ${e(p.kind.toUpperCase())} flow from ${e(p.from)}`}:</b> now choose the host it goes to${zs.length ? '' : ' (no host can take it)'}. <button class="cl" id="bn-cancel">cancel</button>`
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
    const kind = t.closest('.bn-kind'), obj = t.closest('#bn-canvas [data-obj]');
    if (kind) { s.drag = { what: 'kind', kind: kind.dataset.kind, x: ev.clientX, y: ev.clientY, moved: false }; ev.preventDefault(); }
    else if (obj && !t.closest('.bn-zone')) { const [k, id] = obj.dataset.obj.split(':'); s.drag = { what: 'obj', kind: k, id, x: ev.clientX, y: ev.clientY, moved: false }; ev.preventDefault(); }
  },
  move(ev) {
    const N = BRIEF_NET, s = N.s, d = s && s.drag; if (!d || !N.node.isConnected) return;
    if (!d.moved && Math.hypot(ev.clientX - d.x, ev.clientY - d.y) < 6) return;
    if (!d.moved) { d.moved = true; if (d.what === 'kind') { s.placing = d.kind; s.pending = null; N.paint(); } }
    if (d.what === 'kind') { const n = N.near(ev); N.ghost(n.zone ? `release: add ${n.zone.label}` : `${N.KINDS.find(q => q[0] === d.kind)[1]}: move to a marked place`, n.zone ? 'add' : '', ev); }
    else { const n = N.near(ev), gone = N.deps(d.kind, d.id).gone; N.ghost(n.inside ? `drag ${N.says(d.kind, d.id)} out of the picture to remove it` : `release: remove ${gone.map(([k, i]) => N.says(k, i)).join(', ')}`, n.inside ? '' : 'rem', ev); }
  },
  up(ev) {
    const N = BRIEF_NET, s = N.s, d = s && s.drag; if (!d) return; s.drag = null; N.ghost('');
    if (d.what === 'kind') { if (!d.moved) { s.placing = s.placing === d.kind && !s.pending ? null : d.kind; s.pending = null; N.paint(); const z = N.node.querySelector('.bn-zone'); if (z && s.placing) z.focus(); return; }
      const n = N.near(ev); N.node.querySelector('#bn-canvas').classList.remove('over'); if (n.zone) n.zone.go(); else { s.placing = null; N.paint(); } return; }
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
    const rm = c('[data-remove]'); if (rm) { const [k, id] = rm.dataset.remove.split(':'); return N.remove(k, id); }
    const kn = c('[data-knob]'); if (kn) { const a = kn.dataset.knob; return N.change(() => { if (s.knobs[a]) { delete s.knobs[a]; return; }
      const kind = N.kindOf(a), v = a === 'duration' ? s.duration : EV.netSettings(s.t)[a], name = TH_DATA.KNOB[a] || (a === 'duration' ? 'seconds of measured traffic' : a);
      s.knobs[a] = kind === 'type' ? { choices: N.TCP.slice(), default: v, meaning: `${name} (TCP congestion control)` } : { min: N.RANGE[kind][0], max: N.RANGE[kind][1], default: v, meaning: name }; }); }
    if (c('#bn-describe')) { s.description = N.describe(); return N.draw(); }
    if (c('#bn-save')) return N.save(false); if (c('#bn-start')) return N.save(true);
  },
  input(ev) {
    const N = BRIEF_NET, s = N.s, t = ev.target, f = t.dataset && t.dataset.f, done = ev.type === 'change';
    if (t.id === 'bn-open' && done) return N.open(t.value);
    if (t.id === 'bn-structure') { s.structure = t.checked; return N.draw(); }
    if (t.dataset && t.dataset.goal) { s.goal = t.dataset.goal; return N.draw(); }
    if (t.dataset && t.dataset.lock) { s.locked[t.dataset.lock] = t.checked; return; }
    if (t.dataset && t.dataset.qkind && done) return N.change(() => { N.linkOf(t.dataset.qkind).queue.kind = t.value; });
    if (t.dataset && t.dataset.choice && done) { const a = t.dataset.choice, k = s.knobs[a], list = [...N.node.querySelectorAll(`[data-choice="${a}"]`)].filter(x => x.checked).map(x => x.value); if (!list.length) { t.checked = true; return; } return N.change(() => { k.choices = list; if (!list.includes(k.default)) k.default = list[0]; }); }
    if (!f) return;
    if (f.startsWith('v:')) { const a = f.slice(2), v = N.isText(a) ? t.value : N.num(t.value); s.t = EV.netWith(s.t, { [a]: v }); if (done) { N.past.push(JSON.stringify({ t: s.t, knobs: s.knobs })); N.draw(); } else N.paintTask(); return; }
    if (f.startsWith('k:')) { const [, a, part] = f.split(':'); s.knobs[a][part] = N.isText(a) ? t.value : N.num(t.value); if (done) N.draw(); return; }
    if (f.startsWith('lr:')) { const [, l, fl] = f.split(':'), q = N.linkOf(l).queue; q.largest_rate = q.largest_rate || {}; if (t.value.trim()) q.largest_rate[fl] = t.value.trim(); else delete q.largest_rate[fl]; if (done) N.draw(); return; }
    if (f.startsWith('most:')) { s.most[f.slice(5)] = t.value; return; }
    s[f] = t.value; if (done && ['measure', 'direction'].includes(f)) return N.draw(); N.paintTask();
  },
  paintTask() { const N = BRIEF_NET, $ = id => N.node.querySelector('#' + id); const task = $('bn-task'); if (task) task.textContent = EV.taskText(N.toBrief()); const bad = N.problems(); $('bn-save').disabled = !!N.s.busy || !!bad.length; $('bn-state').innerHTML = bad.length ? `<span class="bn-bad"><b>Not ready yet:</b></span><ul id="bn-bad">${bad.map(x => `<li>${EV.e(x)}</li>`).join('')}</ul>` : 'Ready.'; },
  key(ev) {
    const N = BRIEF_NET, s = N.s, t = ev.target, typing = t.matches && t.matches('input, textarea, select'); if (!N.node || !N.node.isConnected || !s) return;
    if (ev.key === 'Escape' && (s.placing || s.pending)) { s.placing = s.pending = null; N.paint(); return; }
    if (typing) return;
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
