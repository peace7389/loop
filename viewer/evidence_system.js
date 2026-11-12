// The system a session investigates, as one picture at the top of its page: the two computers of the brief, each an
// outline that holds its ns-3 objects in the order a packet passes them (applications, internet stack, traffic control,
// net device), and the link between the two devices. The objects and their settings come from viewer/objects.json
// (hand-kept, checked against the scenario); the values come from this session: its brief's fixed settings and each
// knob's default, or the settings of the simulation the reader opened last. A click on an object shows it beside the
// picture, inside this card: its settings, what the model may change (and what this session tried), what is measured
// there. The object chosen is not the session's selection: the item open in the detail pane stays open.
// The scheduling policy is operator-only: it is shown only with the operator columns on, from control.py's session list.
// The card is not printed (the page prints four parts, and this is not one).
// ======================================================================================================
Object.assign(EV, {
  OB: undefined,  // objects.json: undefined = not asked for yet, null = on its way, false = could not be read
  sysLoad() { if (EV.OB !== undefined) return; EV.OB = null; EV.json('objects.json').then(o => { EV.OB = o && o.hosts ? o : false; EV.draw(); }); },
  sysId(host, layer, name) { const H = EV.OB.hosts.find(h => h.key === host), i = H ? (H[layer] || []).findIndex(o => o.name === name) : -1; return i < 0 ? null : `${host}-${layer}-${i}`; },
  sysFind(id) {  // an object by its id: "link", "around-<n>", or "<host>-<layer>-<n>"
    const O = EV.OB, [a, b, i] = String(id || '').split('-'); if (!O) return null;
    if (id === 'link') return { o: O.channel, where: 'between the two net devices', role: 'carries the bits of both flows from one device to the other' };
    if (a === 'around') return (O.around || [])[+b] ? { o: O.around[+b], where: 'part of every simulation, not in the path of a packet', role: '' } : null;
    const H = O.hosts.find(h => h.key === a), L = O.layers.find(l => l.key === b), o = H && L && (H[b] || [])[+i];
    return o ? { o, where: `${H.title} (ns-3 ${H.node}, ${H.sub}) › ${L.name}`, role: (L.roles || {})[H.key] || '' } : null;
  },
  // the settings the picture and the cards show, and which of them are knobs of this session's brief
  sysVals() {
    const M = EV.M, S = EV.s, b = M.brief || {}, kn = b.knobs || {}, q = S.sysSim && S.sysSim.sid === M.id ? M.simById[S.sysSim.id] : null, sim = q && EV.seen(q.id) ? q : null;
    const v = { ...(b.system || {}), ...Object.fromEntries(Object.entries(kn).map(([n, o]) => [n, o.default])), ...(sim ? sim.params : {}) };
    if (typeof v.mtu === 'number') v.segment = v.mtu - 52; if (typeof v.weightUdp === 'number') v.tcpShare = +(1 - v.weightUdp).toFixed(6); if (v.tcpVariant) v.tcpVariantPlain = String(v.tcpVariant).replace(/^Tcp/, '');
    const key = n => ({ tcpShare: 'weightUdp', tcpVariantPlain: 'tcpVariant' }[n] || n);
    return { v, sim, key, knob: n => key(n) in kn, range: n => { const o = kn[key(n)] || {}; return o.choices ? o.choices.map(c => String(c).replace(/^Tcp/, '')).join(', ') : `${o.min} to ${TASK_VIEW._rate(o.max)}`; } };
  },
  sysFill: (text, v) => TASK_VIEW._rate(String(text).replace(/\{(\w+)\}/g, (m, k) => (v[k] != null ? v[k] : 'not recorded'))),

  systemCard() {
    const M = EV.M, S = EV.s, e = EV.e; EV.sysLoad();
    if (S.sel && S.sel.t === 'sim' && M.simById[S.sel.id] && S.sel !== S.sysFrom) { S.sysSim = { sid: M.id, id: S.sel.id }; S.sysFrom = S.sel; }  // the picture follows the simulation opened last (every opening is a new selection)
    const fold = EV.store('ev-sys') === '1', V = EV.sysVals(), v = V.v, O = EV.OB, on = !O ? null : EV.sysFind(S.sysObj) ? S.sysObj : EV.sysId('sender', 'tc', 'Scheduler') || 'link';
    const shown = V.sim ? `the settings of ${EV_ICON.simulation} ${EV.term('Simulation', 'simulation')} ${e(V.sim.id)} “${e(V.sim.label || '')}”${fold ? '' : ' <button class="cl" data-act="sysdef">show the brief\'s defaults</button>'}`
      : M.brief ? `the settings shown are the ${EV.term('Brief', 'brief')}'s defaults, as in the baseline` : `the brief of this session: ${EV.nr}`;
    const head = `<h2>The system <small>two computers and one link · ${shown}${fold ? '' : ' · click an object to see its settings beside the picture'}</small> <button class="cl noprint" data-act="sysfold" style="float:right">${fold ? 'unfold' : 'fold'}</button></h2>`;
    if (fold || !O) return `<div class="ev-card noprint" id="s-system">${head}${fold ? '' : `<p class="sm">${O === false ? 'viewer/objects.json, the list of the ns-3 objects, could not be read.' : 'Loading the ns-3 objects…'}</p>`}</div>`;
    // ---- the pieces: a text, an object (a clickable group with its ns-3 class as the tooltip), a box, a queue, a computer
    const R = t => (t == null ? '' : TASK_VIEW._rate(t)), J = (...a) => a.filter(Boolean).join(' · '), T = (x, y, s, cls, anchor) => `<text x="${x}" y="${y}" class="${cls || ''}" text-anchor="${anchor || 'middle'}">${e(s)}</text>`;
    const val = (x, y, s, k, anchor) => T(x, y, s, V.knob(k) ? 'sk' : 'sv', anchor);
    const obj = (id, inner) => { const f = id && EV.sysFind(id); return f ? `<g data-act="sysobj" data-id="${id}"${on === id ? ' class="osel"' : ''}><title>${e(`${f.o.name} · ns-3 ${EV.sysFill(f.o.cls, v)}`)}</title>${inner}</g>` : ''; };
    const box = (id, x, y, w, h, l1, l2, o = {}) => obj(id, `<rect class="bx${o.cls || ''}" x="${x}" y="${y}" width="${w}" height="${h}" rx="${o.rx || 5}"/>${T(x + w / 2, y + h / 2 + (l2 ? -2 : 4), l1, o.lc || 'sn')}${l2 ? val(x + w / 2, y + h / 2 + 11, l2[0], l2[1]) : ''}`.replace(/(y=")(\d+(?:\.\d+)?)(" class="sn")/, (m, a, yy, c) => (l2 && !l2[0] ? a + (+yy + 6) + c : m)));
    const queue = (id, x, y, name, col) => obj(id, `<path class="bx" d="M${x},${y} H${x + 104} V${y + 30} H${x}"/>${[0, 1, 2].map(i => `<rect x="${x + 94 - i * 9}" y="${y + 4}" width="6" height="22" rx="1.5" fill="var(${col})" opacity="${0.75 - i * 0.2}"/>`).join('')}
      ${T(x + 5, y + 13, name, 'sn', 'start')}${val(x + 5, y + 25, v.queuePkts == null ? '' : `${v.queuePkts} packets`, 'queuePkts', 'start')}`);
    const pc = (x, w, H) => `<rect class="pc" x="${x}" y="2" width="${w}" height="166" rx="12"/><path class="pi" d="M${x + 14},11 h17 v11 h-17 z M${x + 19},26 h7 M${x + 22.5},22 v4"/>
      ${T(x + 40, 22, H.title, 'sn st', 'start')}${T(x + 40 + H.title.length * 8.2 + 8, 22, `ns-3 ${H.node} · ${H.sub}`, 'sc', 'start')}`;
    const cap = (x, s) => T(x, 50, s, 'sc'), id = EV.sysId, Y = { u: 67, t: 117 }, w = typeof v.weightUdp === 'number' ? Math.min(0.999, Math.max(0.001, v.weightUdp)) : null;
    // the scheduler: a circle divided as the ratio divides the link, the UDP part on the side the UDP queue enters
    const at = d => [432 + 22 * Math.cos(d * Math.PI / 180), 107 + 22 * Math.sin(d * Math.PI / 180)].map(n => n.toFixed(1)).join(','), cut = w == null ? '' : `<path d="M432,107 L${at(-90 - 180 * w)} A22,22 0 ${w > 0.5 ? 1 : 0},1 ${at(-90 + 180 * w)} Z" fill="var(--series-1)"/>`;
    const pol = S.op && EV.files.row && EV.files.row.policy && !EV.files.row.policy_hidden ? `<rect x="398" y="154" width="8" height="8" rx="2" fill="var(--by-operator)"/><text x="410" y="162" text-anchor="start" class="sv">policy: ${e(EV.files.row.policy)}</text>` : '';
    const sched = obj(id('sender', 'tc', 'Scheduler'), `<circle cx="432" cy="107" r="22" fill="var(${w == null ? '--surface-1' : '--series-2'})"/>${cut}<circle class="bx" cx="432" cy="107" r="22" style="fill:none"/>${T(432, 77, 'scheduler', 'sn')}
      ${val(432, 148, w == null ? '' : `${v.weightUdp} : ${v.tcpShare}`, 'weightUdp')}${pol}`);
    const X = 678, flows = `<path class="fu" d="M122,82 H388 C408,82 408,94 416,96.5 M454,105.4 H${X + 100} M${X + 138},82 H${X + 238}"/><path class="ft" d="M122,132 H388 C408,132 408,120 416,117.5 M454,108.6 H${X + 100} M${X + 138},132 H${X + 238}"/>`;
    const wire = obj('link', `<rect x="594" y="66" width="82" height="62" fill="transparent"/><path class="wa" d="M630,101.5 l9,5.5 l-9,5.5 z"/>${T(635, 80, 'link', 'sn')}${T(635, 93, J(R(v.linkRate), R(v.linkDelay)), 'sv')}`);
    const svg = `<svg class="sy" viewBox="0 0 1000 170" width="100%" style="max-width:1100px" role="img" aria-label="The system: a sender and a receiver, each one computer holding its ns-3 objects, joined by one link">
      ${pc(2, 590, O.hosts[0])}${pc(X - 2, 322, O.hosts[1])}${cap(68, 'applications')}${cap(203, 'internet stack')}${cap(366, 'traffic control')}${cap(528, 'net device')}${cap(X + 46, 'net device')}${cap(X + 154, 'internet stack')}${cap(X + 273, 'applications')}${flows}
      ${box(id('sender', 'apps', 'UDP source'), 14, Y.u, 108, 30, 'UDP source', [v.udpRate == null ? 'constant rate' : `${R(v.udpRate)}, constant`, 'udpRate'], { rx: 15 })}${box(id('sender', 'apps', 'TCP source'), 14, Y.t, 108, 30, 'TCP source', ['always has data', ''], { rx: 15 })}
      ${box(id('sender', 'stack', 'UDP socket'), 140, Y.u, 72, 30, 'UDP socket')}${box(id('sender', 'stack', 'TCP socket'), 140, Y.t, 72, 30, 'TCP socket', [v.tcpVariantPlain || '', 'tcpVariant'])}${box(id('sender', 'stack', 'IPv4'), 228, 67, 38, 80, 'IPv4')}
      ${queue(id('sender', 'tc', 'UDP queue'), 284, Y.u, 'UDP queue', '--series-1')}${queue(id('sender', 'tc', 'TCP queue'), 284, Y.t, 'TCP queue', '--series-2')}${sched}
      ${box(id('sender', 'dev', 'Point-to-point device'), 476, 85, 104, 44, 'device', [J(R(v.linkRate), 'queue 10'), 'linkRate'])}${wire}
      ${box(id('receiver', 'dev', 'Point-to-point device'), X + 10, 85, 72, 44, 'device', [R(v.linkRate), 'linkRate'])}${box(id('receiver', 'tc', 'Return queue'), X + 10, 138, 72, 22, 'return queue', null, { cls: ' dash', lc: 'sv' })}
      ${box(id('receiver', 'stack', 'IPv4'), X + 100, 67, 38, 80, 'IPv4')}${box(id('receiver', 'stack', 'UDP socket'), X + 154, Y.u, 70, 30, 'UDP socket')}${box(id('receiver', 'stack', 'TCP socket'), X + 154, Y.t, 70, 30, 'TCP socket')}
      ${box(id('receiver', 'apps', 'UDP sink'), X + 238, Y.u, 70, 30, 'UDP sink', null, { rx: 15 })}${box(id('receiver', 'apps', 'TCP sink'), X + 238, Y.t, 70, 30, 'TCP sink', null, { rx: 15 })}</svg>`;
    const around = (O.around || []).map((o, i) => `<a data-act="sysobj" data-id="around-${i}"${on === 'around-' + i ? ' style="font-weight:700"' : ''}>${e(o.name.toLowerCase())}</a>`).join(', ');
    return `<div class="ev-card noprint" id="s-system">${head}<div class="sy-row"><div><div class="ev-scroll">${svg}</div>
      <p class="sm gl-key"><span><i class="sw" style="background:var(--series-1)"></i>UDP</span><span><i class="sw" style="background:var(--series-2)"></i>TCP</span>${Object.keys((M.brief || {}).knobs || {}).length ? `<span><b style="color:var(--by-model)">violet</b>: a setting the model may change</span>` : ''}${around ? `<span>outside a packet's path: ${around}</span>` : ''}</p></div><div class="sy-det">${EV.objCard(on)}</div></div></div>`;
  },

  // ---- the chosen object, beside the picture: its settings, what the model may change and what this session tried, what is measured there
  objCard(id) {
    const M = EV.M, S = EV.s, e = EV.e, f = EV.sysFind(id); if (!f) return '';
    const V = EV.sysVals(), o = f.o, sim = V.sim, keysOf = t => [...String(t).matchAll(/\{(\w+)\}/g)].map(m => m[1]), short = x => TASK_VIEW._rate(String(x).replace(/^Tcp/, ''));
    const tried = k => { const vs = [...new Set(M.sims.filter(q => EV.seen(q.id) && q.params && q.params[k] != null).map(q => q.params[k]))], num = vs.every(x => typeof x === 'number');  // the values this session's simulations used
      return !vs.length ? '' : ` · this session tried ${vs.length === 1 ? 'one value, ' + short(vs[0]) : num ? `${vs.length} values, ${Math.min(...vs)} to ${Math.max(...vs)}` : vs.map(short).join(', ')}`; };
    const rows = o.rows.map(([k, text, flag]) => { const kn = keysOf(text).find(V.knob);
      const shown = flag === 'op' ? (S.op ? `<span data-by="operator"><i class="sw"></i>${EV.policyText(EV.files.row)}</span>` : '<span class="mut" title="Shown with the operator columns on">operator-only</span>') : e(EV.sysFill(text, V.v));
      const note = kn ? e('the model may change it: ' + V.range(kn) + tried(V.key(kn))) : flag === 'ns3' ? 'an ns-3 default' : flag === 'op' ? 'chosen by the operator, not told to the model' : '';
      return `<tr><td>${e(k)}</td><td>${kn ? `<b style="color:var(--by-model)">${shown}</b>` : shown}${note ? ` <span class="sm">· ${note}</span>` : ''}</td></tr>`; }).join('');
    const ms = o.measured || [], names = ms.map(k => TH_DATA.PLAIN[k] || k), measured = !ms.length ? '' : sim && sim.metrics ? `<p class="sm" style="margin-top:6px">Measured here in ${EV.link(sim.id)}: ${ms.map((k, i) => `${e(names[i])} <b>${e(EV.val(k, sim.metrics[k]))}</b>`).join(' · ')}</p>`
      : `<p class="sm" style="margin-top:6px">Measured here in every simulation: ${e(names.join(', '))}. Open a simulation and its values appear here.</p>`;
    return `<p><b style="font-size:var(--f-card)">${e(o.name)}</b> <span class="sm">ns-3 <code>${e(EV.sysFill(o.cls, V.v))}</code></span></p>
      <p class="sm">${e(f.where)} · ${o.flow === 'udp' ? '<i class="sw" style="background:var(--series-1)"></i>handles UDP' : o.flow === 'tcp' ? '<i class="sw" style="background:var(--series-2)"></i>handles TCP' : id === 'link' ? 'carries both flows' : id.startsWith('around') ? 'the same for both flows' : 'shared by both flows'}${f.role ? ' · ' + e(f.role) : ''}</p>
      <table><tbody>${rows}</tbody></table>${measured}`;
  },
});
EV.act = Object.assign(EV.act || {}, {
  sysdef() { EV.s.sysSim = null; EV.draw(); },
  sysobj(id) { EV.s.sysObj = id; EV.draw(); },
  sysfold() { EV.store('ev-sys', EV.store('ev-sys') === '1' ? '0' : '1'); EV.draw(); },
});
