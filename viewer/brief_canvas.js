// ======================================================================================================
// The drawing surface of the network builder (brief_net.js).
// It is built on JointJS (@joint/core 4.3.4, open source, MPL-2.0; vendor/joint.min.js with its licence beside it): the hosts can be moved about,
// a link is made by dragging a host's handle onto another host, the picture can be moved and zoomed, an object that is chosen carries a button
// that removes it. A host is drawn like a host of the two-host picture: its name, and in columns its applications, its internet stack and, where
// it has a queue, its traffic control; each flow in its own colour through them and along the links.
// The network itself stays the builder's data (BRIEF_NET.s.t); this file only draws it and reports gestures: NETC.mount draws, and calls
// BRIEF_NET.pick (an object chosen), BRIEF_NET.add.link (a link drawn), BRIEF_NET.remove (dragged out, or its button), BRIEF_NET.paint (moved).
// ======================================================================================================
const NETC = {
  paper: null, graph: null, view: null,   // view: { s, tx, ty }, the zoom and the place of the picture, kept from one drawing to the next
  // ---- a host, as SVG: { svg, w, h }
  hostSvg(t, h, knobs, passing) {
    const e = EV.e, col = id => EV.netColor(t, id), k = a => (knobs[a] ? '✦ ' : ''), plain = v => TASK_VIEW._rate(String(v)).replace(/^Tcp/, '');
    const rows = [...t.flows.filter(f => f.from === h.id).map(f => [f, 'source']), ...t.flows.filter(f => f.to === h.id).map(f => [f, 'sink'])], qs = EV.netQueues(t).filter(x => x.h === h.id);
    const mirror = rows.length > 0 && rows.every(([, role]) => role === 'sink') && !qs.length, RH = 50, top = 66, wa = 108, ws = 92, wi = 44, xi = mirror || !rows.length ? 14 : 14 + wa + 16 + ws + 12, xs = mirror ? xi + wi + 12 : 14 + wa + 16, xa = mirror ? xs + ws + 16 : 14, xt = xi + wi + 20, wt = 204;   // a host that only forwards has no applications and no sockets: its IPv4 stands first
    // the queues of a described queue's block: of a scheduler one for each part (a part holds one flow, or the flows of a class, which share its queue); of a plain queue the flows that pass
    const partsOf = x => (x.q.kind === 'scheduler' ? Object.keys(x.q.parts || {}).map(name => ({ name, who: EV.netMembers(x.q, name).filter(id => (passing[x.id] || []).includes(id)) })).filter(p => p.who.length) : (passing[x.id] || []).map(id => ({ name: id, who: [id] })));
    const nq = x => Math.max(1, partsOf(x).length), aligned = qs.length === 1 && (passing[qs[0].id] || []).length > 0 && (passing[qs[0].id] || []).every(id => rows.some(([f, role]) => f.id === id && role === 'source'));
    // the room a queue's block takes: on the rows of its flows where they start here (as in the two-host picture), else stacked under one another
    const qH = x => (aligned ? Math.max(rows.length * RH, (nq(x) - 1) * RH / 2 + 80) : (qs.length > 1 ? 16 : 0) + Math.max(nq(x) * 44 + 18, nq(x) * 22 + 82) + 4), tcH = qs.reduce((a, x) => a + qH(x), 0), bodyH = Math.max(rows.length * RH, tcH, 52);
    const W = Math.max((mirror ? xa + wa : qs.length ? xt + wt : xi + wi + (rows.length ? 0 : 104)) + 14, 190), H = top + bodyH + 10, cap = (x, text) => `<text x="${x}" y="52" font-size="12" fill="var(--text-muted)">${text}</text>`;
    const linked = t.links.filter(l => l.between.includes(h.id)).length, nth = t.hosts.findIndex(q => q.id === h.id);
    let s = `<path d="M15 12h18v12H15zM20 28h8M24 24v4" fill="none" stroke="var(--text-secondary)" stroke-width="1.5" stroke-linejoin="round"/>
      <text x="42" y="25" font-size="16" font-weight="700" fill="var(--text-primary)" class="sn">${e(h.id)}</text><text x="${W - 12}" y="24" font-size="12" text-anchor="end" fill="var(--text-muted)">ns-3 Node ${nth}</text>
      ${rows.length ? cap(xa, 'applications') + cap(mirror ? xi : xs, 'internet stack') : ''}${qs.length ? cap(xt, 'traffic control') : ''}
      <rect x="${xi}" y="${top - 6}" width="${wi}" height="${bodyH}" rx="6" fill="var(--surface-1)" stroke="var(--text-secondary)" stroke-width="1.2"/><text x="${xi + wi / 2}" y="${top - 6 + bodyH / 2 + 4}" font-size="13" font-weight="700" text-anchor="middle" fill="var(--text-primary)">IPv4</text>`;
    if (!rows.length && !qs.length) s += `<text x="${xi + wi + 10}" y="${top + 22}" font-size="13" fill="var(--text-secondary)">${linked > 1 ? 'forwards only' : 'no flow yet'}</text>`;
    rows.forEach(([f, role], i) => { const y = top + i * RH + 12, c = col(f.id), udp = f.kind === 'udp', onoff = EV.netApp(f) === 'onoff';
      const under = role === 'source' ? (onoff ? `${k(f.id + '.rate')}${e(plain(f.rate))}, constant` : 'always has data') : `from ${e(f.from)}`, sock = role === 'source' && !udp ? `${k(f.id + '.type')}${e(plain(f.type))}` : '';
      s += `<g ${role === 'source' ? `data-flow="${e(f.id)}" data-obj="flow:${e(f.id)}" class="nc-flow"` : `data-sink="${e(f.id)}" class="nc-flow"`}><title>${e(`${role === 'source' ? EV.NET_APP[EV.netApp(f)][0] + ' application' : 'PacketSink'} of flow ${f.id}, ${udp ? 'UDP' : 'TCP'} socket: ${f.from} → ${f.to}${role === 'source' ? ' · click to set it' : ''}`)}</title>
        <line x1="${mirror ? xi + wi : xa + wa}" y1="${y}" x2="${mirror ? xa : xi}" y2="${y}" stroke="${c}" stroke-width="2.5"/>
        <rect x="${xa}" y="${y - 12}" width="${wa}" height="24" rx="12" fill="${c}"/><text x="${xa + wa / 2}" y="${y + 4.5}" font-size="13" font-weight="700" text-anchor="middle" fill="#fff">${e(f.id)} ${role}</text>
        <text x="${xa + 6}" y="${y + 26}" font-size="12" fill="var(--text-secondary)">${under}</text>
        <rect x="${xs}" y="${y - 12}" width="${ws}" height="24" rx="6" fill="var(--surface-1)" stroke="var(--text-secondary)" stroke-width="1.2"/><text x="${xs + ws / 2}" y="${y + 4.5}" font-size="13" font-weight="700" text-anchor="middle" fill="var(--text-primary)">${udp ? 'UDP' : 'TCP'} socket</text>
        ${sock ? `<text x="${xs + 6}" y="${y + 26}" font-size="12" fill="var(--text-secondary)">${sock}</text>` : ''}</g>`; });
    // traffic control, as in the two-host picture: for each flow that passes, its queue (a box open on the side the packets come in, its name, its
    // length, three slots at the end they leave by); then the scheduler, a circle divided as its parts divide the link, "scheduler" above it and the
    // parts below; the flows run into it and leave it side by side. How it divides the link (the policy) is not told to the AI.
    let y0 = top - 6;
    qs.forEach(x => { const l = x.l, q = x.q, A = x.a, fl = passing[x.id] || [], ps = partsOf(x), other = l.between.find(y => y !== h.id), hq = qH(x), capH = qs.length > 1 ? 16 : 0, sched = q.kind === 'scheduler', r = 22;
      const rowOf = id => rows.findIndex(([f, role]) => f.id === id && role === 'source'), onRows = qs.length === 1 && fl.length > 0 && fl.every(id => rowOf(id) >= 0), wq = 112, mean = a => a.reduce((u, v) => u + v, 0) / a.length;
      // where the queue of part i stands: on the row of its flow (between the rows of its flows, where several share it), else under one another
      const yq = i => (onRows ? top + mean(ps[i].who.map(rowOf)) * RH - 3 : y0 + capH + 22 + i * 44 + 7), cy = ps.length ? (yq(0) + yq(ps.length - 1)) / 2 + 15 : y0 + capH + 22 + 7 + 15, cx = xt + wq + 36 + r, part = p => Number((q.parts || {})[p.name]) || 1, tot = ps.reduce((a, p) => a + part(p), 0) || 1;
      const at = d => `${(cx + r * Math.cos(d * Math.PI / 180)).toFixed(1)},${(cy + r * Math.sin(d * Math.PI / 180)).toFixed(1)}`, w = ps.length === 2 ? Math.min(0.999, Math.max(0.001, part(ps[0]) / tot)) : 0, c0 = p => col(p.who[0]);
      let a0 = -90; const pie = ps.length === 2 ? `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${c0(ps[1])}"/><path d="M${cx},${cy} L${at(-90 - 180 * w)} A${r},${r} 0 ${w > 0.5 ? 1 : 0},1 ${at(-90 + 180 * w)} Z" fill="${c0(ps[0])}"/>`
        : ps.length < 2 ? `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${ps.length ? c0(ps[0]) : 'var(--surface-1)'}"/>` : ps.map(p => { const a1 = a0 + 360 * part(p) / tot, d = `M${cx},${cy} L${at(a0)} A${r},${r} 0 ${a1 - a0 > 180 ? 1 : 0},1 ${at(a1)} Z`; a0 = a1; return `<path d="${d}" fill="${c0(p)}"/>`; }).join('');
      // a queue's box: open on the side the packets come in, its name, its length, three slots at the end they leave by (in the colours of the flows that wait in it)
      const short = text => (text.length > 17 ? text.slice(0, 16) + '…' : text);
      const qbox = (y, name, cs) => `<path d="M${xt},${y} H${xt + wq} V${y + 30} H${xt}" fill="var(--surface-1)" stroke="var(--text-secondary)" stroke-width="1.2"/>${cs.length ? [0, 1, 2].map(i => `<rect x="${xt + wq - 10 - i * 9}" y="${y + 4}" width="6" height="22" rx="1.5" fill="${cs[i % cs.length]}" opacity="${0.75 - i * 0.2}"/>`).join('') : ''}
          <text x="${xt + 5}" y="${y + 13}" font-size="12" font-weight="700" fill="var(--text-primary)">${e(short(name))}</text><text x="${xt + 5}" y="${y + 25}" font-size="12" fill="var(--text-secondary)">${k(A + '.length')}${e(q.length)} packets</text>`;
      const off = i => (i - (fl.length - 1) / 2);
      // a shared queue: one box that every flow enters and leaves, first in, first out (no part of the link for anyone, so no divided circle)
      if (!sched) { const by = cy - 15, bx = xt + 30;
        s += `<g data-queue="${e(x.id)}" data-obj="queue:${e(x.id)}" class="nc-queue"><title>${e(`shared queue on ${h.id}'s side of link ${l.id} (to ${other}): click to set it`)}</title><rect x="${xt - 8}" y="${y0}" width="${wt + 6}" height="${hq - 6}" rx="8" fill="transparent" stroke="transparent" class="nc-qbox"/>
          ${fl.map((id, i) => `<path d="M${xi + wi},${yq(i) + 15} C${xt + 14},${yq(i) + 15} ${xt + 10},${(cy + off(i) * 5).toFixed(1)} ${bx},${(cy + off(i) * 5).toFixed(1)}" fill="none" stroke="${col(id)}" stroke-width="2.2"/><line x1="${bx + wq}" y1="${(cy + off(i) * 3.2).toFixed(1)}" x2="${xt + wt - 4}" y2="${(cy + off(i) * 3.2).toFixed(1)}" stroke="${col(id)}" stroke-width="2.2"/>`).join('')}
          <path d="M${bx},${by} H${bx + wq} V${by + 30} H${bx}" fill="var(--surface-1)" stroke="var(--text-secondary)" stroke-width="1.2"/>${[0, 1, 2].map(i => `<rect x="${bx + wq - 10 - i * 9}" y="${by + 4}" width="6" height="22" rx="1.5" fill="${fl.length ? col(fl[i % fl.length]) : 'var(--text-secondary)'}" opacity="${0.75 - i * 0.2}"/>`).join('')}
          <text x="${bx + 5}" y="${by + 13}" font-size="12" font-weight="700" fill="var(--text-primary)">shared queue</text><text x="${bx + 5}" y="${by + 25}" font-size="12" fill="var(--text-secondary)">${k(A + '.length')}${e(q.length)} packets</text>
          <text x="${bx}" y="${by + 46}" font-size="12" fill="var(--text-muted)">first in, first out</text></g>`; y0 += hq; return; }
      // a scheduler: each part's queue, the flows that wait in it running in (several into one where they share it) and on to the divided circle
      let g = 0; const lanes = ps.map((p, i) => { const y = yq(i), n = p.who.length; return `${p.who.map((id, j) => { const c = col(id), dy = (j - (n - 1) / 2) * 5, yin = onRows ? top + rowOf(id) * RH + 12 : y + 15 + dy, gi = g++;
          return `<path d="M${xi + wi},${yin.toFixed(1)} C${xt - 8},${yin.toFixed(1)} ${xt - 12},${(y + 15 + dy).toFixed(1)} ${xt},${(y + 15 + dy).toFixed(1)}" fill="none" stroke="${c}" stroke-width="2.2"/>
          <path d="M${xt + wq},${(y + 15 + dy).toFixed(1)} C${xt + wq + 22},${(y + 15 + dy).toFixed(1)} ${xt + wq + 18},${(cy + off(gi) * 10).toFixed(1)} ${(cx - r + 1).toFixed(1)},${(cy + off(gi) * 8).toFixed(1)}" fill="none" stroke="${c}" stroke-width="2.2"/><line x1="${cx + r}" y1="${(cy + off(gi) * 3.2).toFixed(1)}" x2="${xt + wt - 4}" y2="${(cy + off(gi) * 3.2).toFixed(1)}" stroke="${c}" stroke-width="2.2"/>`; }).join('')}${qbox(y, n > 1 ? `${p.name}: ${p.who.join(' + ')}` : p.name + ' queue', p.who.map(col))}`; }).join('');
      s += `<g data-queue="${e(x.id)}" data-obj="queue:${e(x.id)}" class="nc-queue"><title>${e(`${q.kind} on ${h.id}'s side of link ${l.id} (to ${other}): click to set it`)}</title><rect x="${xt - 8}" y="${y0}" width="${wt + 6}" height="${hq - 6}" rx="8" fill="transparent" stroke="transparent" class="nc-qbox"/>
        ${capH ? `<text x="${xt}" y="${y0 + 12}" font-size="12" fill="var(--text-muted)">to ${e(other)} · ${e(l.id)}</text>` : ''}
        ${ps.length ? lanes : qbox(y0 + capH + 22 + 7, 'queue', [])}
        ${pie}<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--text-secondary)" stroke-width="1.2"/>
        <text x="${cx}" y="${cy - r - 8}" font-size="12" font-weight="700" text-anchor="middle" fill="var(--text-primary)">scheduler</text>
        ${ps.length ? `<text x="${cx}" y="${cy + r + 15}" font-size="12" text-anchor="middle" fill="var(--text-secondary)">${ps.some(p => knobs[`${A}.parts.${p.name}`]) ? '✦ ' : ''}${ps.map(p => e((q.parts || {})[p.name] ?? 1)).join(' : ')}</text>` : ''}
        <text x="${xt + wt - 2}" y="${cy + r + 30}" font-size="12" text-anchor="end" fill="var(--text-muted)">policy not told to the AI</text></g>`; y0 += hq; });
    // the page's own rule for text in a picture is stronger than an attribute: each text carries its size, weight and colour as its style
    s = s.replace(/<text([^>]*)>/g, (m, a) => { const g = k => (new RegExp(` ${k}="([^"]*)"`).exec(a) || [])[1], st = [['font-size', g('font-size') ? g('font-size') + 'px' : ''], ['font-weight', g('font-weight')], ['fill', g('fill')]].filter(q => q[1]).map(q => q.join(':')).join(';'); return `<text${a} style="${st}">`; });
    return { svg: s, w: W, h: H, mirror };
  },
  // a host's box at the width and the height it was given (kx, ky: times its picture's own); the picture inside keeps its proportions and fills what fits
  sized(q, kx, ky) { return { ...q, w0: q.w0 || q.w, h0: q.h0 || q.h, kx, ky, k: Math.min(kx, ky), w: (q.w0 || q.w) * kx, h: (q.h0 || q.h) * ky }; },
  // ---- the two ways a host is drawn (2026-11-17, the operator: simple objects with icons, the full structure beside the picture on a click; the reader chooses)
  mode() { let v = null; try { v = localStorage.getItem('ev-bn-mode'); } catch (x) { /* no storage */ } return v === 'full' ? 'full' : 'simple'; },
  // a host, simple: its sign, its name, and one small mark for each thing in it: an application that sends (filled, in its flow's colour), one that
  // receives (outlined), its scheduler (the divided circle). Each mark is chosen by a click like the part it stands for.
  hostSimple(t, h, knobs, passing) {
    const e = EV.e, col = id => EV.netColor(t, id), out = t.flows.filter(f => f.from === h.id), inn = t.flows.filter(f => f.to === h.id), qs = EV.netQueues(t).filter(x => x.h === h.id), linked = t.links.filter(l => l.between.includes(h.id)).length;
    const cw = id => Math.max(40, id.length * 7.4 + 18); let x = 14, chips = '';
    out.forEach(f => { const w = cw(f.id); chips += `<g data-flow="${e(f.id)}" data-obj="flow:${e(f.id)}" class="nc-flow"><title>${e(`${EV.NET_APP[EV.netApp(f)][0]} application ${f.id} on a ${f.kind.toUpperCase()} socket: sends to ${f.to} · click to set it`)}</title><rect x="${x}" y="58" width="${w}" height="20" rx="10" fill="${col(f.id)}"/><text x="${x + w / 2}" y="72" font-size="12" font-weight="700" text-anchor="middle" fill="#fff">${e(f.id)}</text></g>`; x += w + 6; });
    inn.forEach(f => { const w = cw(f.id); chips += `<g data-sink="${e(f.id)}" class="nc-flow"><title>${e(`sink of ${f.id}: receives from ${f.from} · click to set its application`)}</title><rect x="${x}" y="58" width="${w}" height="20" rx="10" fill="var(--surface-1)" stroke="${col(f.id)}" stroke-width="2"/><text x="${x + w / 2}" y="72" font-size="12" font-weight="700" text-anchor="middle" fill="${col(f.id)}">${e(f.id)}</text></g>`; x += w + 6; });
    qs.forEach(Q => { const l = Q.l, fl = passing[Q.id] || [], cx = x + 11, cy = 68; chips += `<g data-queue="${e(Q.id)}" data-obj="queue:${e(Q.id)}" class="nc-queue"><title>${e(`${EV.netDisc(Q.q.kind)[0]} (ns-3 ${EV.netDisc(Q.q.kind)[1]}) on its side of link ${l.id} · click to set it`)}</title><rect x="${x - 3}" y="55" width="28" height="26" rx="6" fill="transparent" stroke="transparent" class="nc-qbox"/>
      ${Q.q.kind === 'scheduler' ? `<circle cx="${cx}" cy="${cy}" r="10" fill="${fl.length > 1 ? col(fl[1]) : fl.length ? col(fl[0]) : 'var(--surface-1)'}"/>${fl.length > 1 ? `<path d="M${cx - 10},${cy} A10,10 0 0,1 ${cx + 10},${cy} Z" fill="${col(fl[0])}"/>` : ''}<circle cx="${cx}" cy="${cy}" r="10" fill="none" stroke="var(--text-secondary)" stroke-width="1.2"/>`
        : `<path d="M${cx - 11},${cy - 8} H${cx + 11} V${cy + 8} H${cx - 11}" fill="var(--surface-1)" stroke="var(--text-secondary)" stroke-width="1.3"/>${[0, 1, 2].map(i => `<rect x="${cx + 5 - i * 5.5}" y="${cy - 5}" width="3.5" height="10" rx="1" fill="${fl.length ? col(fl[i % fl.length]) : 'var(--text-secondary)'}" opacity="${0.8 - i * 0.2}"/>`).join('')}`}</g>`; x += 30; });
    if (!out.length && !inn.length && !qs.length) { chips = `<text x="14" y="72" font-size="12" fill="var(--text-secondary)">${linked > 1 ? 'forwards only' : 'no application yet'}</text>`; x = 130; }
    const W = Math.max(168, x + 8, 70 + h.id.length * 9.5 + 30), nth = t.hosts.findIndex(q => q.id === h.id);
    let s = `<rect x="14" y="13" width="30" height="21" rx="3" fill="var(--surface-1)" stroke="var(--text-primary)" stroke-width="1.8"/><path d="M22 41h14M29 34v7" fill="none" stroke="var(--text-primary)" stroke-width="1.8" stroke-linecap="round"/>
      <text x="54" y="27" font-size="16" font-weight="700" fill="var(--text-primary)" class="sn">${e(h.id)}</text><text x="54" y="42" font-size="12" fill="var(--text-muted)">ns-3 Node ${nth}</text>${chips}`;
    s = s.replace(/<text([^>]*)>/g, (m, a) => { const g = k => (new RegExp(` ${k}="([^"]*)"`).exec(a) || [])[1], st = [['font-size', g('font-size') ? g('font-size') + 'px' : ''], ['font-weight', g('font-weight')], ['fill', g('fill')]].filter(q => q[1]).map(q => q.join(':')).join(';'); return `<text${a} style="${st}">`; });
    return { svg: s, w: W, h: 90, mirror: false };
  },
  // the full structure of one host, as a picture of its own (beside the simple picture, in the card of what is chosen)
  detail(t, id, knobs) { const C = NETC, h = t.hosts.find(q => q.id === id); if (!h) return ''; const q = C.hostSvg(t, h, knobs, BRIEF_NET.passing(t));
    return `<div class="bn-detail" data-detail="${EV.e(id)}"><svg viewBox="0 0 ${q.w} ${q.h}" width="100%" style="max-width:${q.w}px" role="img" aria-label="${EV.e('The structure of host ' + id)}"><rect x="0.75" y="0.75" width="${q.w - 1.5}" height="${q.h - 1.5}" rx="12" fill="var(--surface-0)" stroke="var(--text-secondary)" stroke-width="1.5"/>${q.svg}</svg></div>`; },
  // where the hosts stand when nobody has placed them: in columns by their distance (in links) from the hosts that send
  layout(t, size, pos) {
    const adj = {}; t.hosts.forEach(h => { adj[h.id] = []; }); t.links.forEach(l => { const [a, b] = l.between; if (adj[a] && adj[b]) { adj[a].push(b); adj[b].push(a); } });
    const start = [...new Set(t.flows.map(f => f.from))].filter(h => adj[h]), depth = {}; let front = start.length ? start : t.hosts.slice(0, 1).map(h => h.id); front.forEach(h => { depth[h] = 0; });
    while (front.length) { const next = []; front.forEach(h => adj[h].forEach(o => { if (!(o in depth)) { depth[o] = depth[h] + 1; next.push(o); } })); front = next; }
    const far = Math.max(-1, ...Object.values(depth)) + 1; t.hosts.forEach(h => { if (!(h.id in depth)) depth[h.id] = far; });
    const cols = []; t.hosts.forEach(h => { (cols[depth[h.id]] = cols[depth[h.id]] || []).push(h.id); });
    const tall = Math.max(1, ...cols.map(c => (c || []).reduce((a, id) => a + size[id].h + 34, -34))); let x = 30; const out = {};
    cols.forEach(c => { if (!c) return; let y = 30 + (tall - c.reduce((a, id) => a + size[id].h + 34, -34)) / 2; c.forEach(id => { out[id] = pos[id] || { x, y: Math.round(y) }; y += size[id].h + 34; }); x += Math.max(...c.map(id => size[id].w)) + 240; });
    return out;
  },
  dispose() { const C = NETC; if (C.paper) { try { C.paper.remove(); } catch (x) { /* its element is gone already */ } } C.paper = C.graph = null; },
  // ---- draw the network t into el. o: { knobs, pos (the hosts' places; filled in here), sel }
  mount(el, t, o) {
    const C = NETC, N = BRIEF_NET, J = window.joint; C.dispose(); if (!J) { el.innerHTML = '<p class="sm" style="padding:14px">The drawing library (vendor/joint.min.js) could not be loaded.</p>'; return; }
    // a host's size is its picture's, times the factor it was resized to (o.pos[id].k; 1 when nobody has)
    const { dia, shapes, linkTools, elementTools } = J, passing = N.passing(t), simple = C.mode() === 'simple', parts = Object.fromEntries(t.hosts.map(h => { const q = (simple ? C.hostSimple : C.hostSvg)(t, h, o.knobs, passing), k = (o.pos[h.id] || {}).k || 1; return [h.id, C.sized(q, (o.pos[h.id] || {}).kx || k, (o.pos[h.id] || {}).ky || k)]; })), pos = C.layout(t, parts, o.pos);
    // a host that grew (an application or a queue was added to it) does not lie over the host under it: that one moves down by what is needed
    const byY = Object.keys(pos).sort((a, b) => pos[a].y - pos[b].y);
    byY.forEach((a, i) => byY.slice(i + 1).forEach(b => { const A = pos[a], B = pos[b]; if (A.x < B.x + parts[b].w && B.x < A.x + parts[a].w && B.y < A.y + parts[a].h + 10 && A.y < B.y + parts[b].h) pos[b] = { ...B, y: Math.round(A.y + parts[a].h + 16) }; }));
    Object.keys(pos).forEach(id => { o.pos[id] = { x: pos[id].x, y: pos[id].y, kx: parts[id].kx, ky: parts[id].ky }; }); C.o = o; C.parts = parts;
    const Host = dia.Element.define('net.Host', { attrs: { body: { width: 'calc(w)', height: 'calc(h)', rx: 12, ry: 12, fill: 'var(--surface-0)', stroke: 'var(--text-secondary)', strokeWidth: 1.5 } },
      // a + in the middle of each side: a link is drawn from whichever side is nearest, and a link that is there ends at the + of the side it comes from
      ports: { groups: Object.fromEntries(['top', 'right', 'bottom', 'left'].map(side => [side, { position: { name: side }, markup: [{ tagName: 'circle', selector: 'c' }, { tagName: 'path', selector: 'x' }],
        attrs: { c: { r: 9, magnet: true, fill: 'var(--surface-1)', stroke: 'var(--text-primary)', strokeWidth: 1.5, cursor: 'crosshair', title: 'Drag from here onto another host: a link between the two' }, x: { d: 'M-4 0H4M0-4V4', stroke: 'var(--text-primary)', strokeWidth: 1.6, pointerEvents: 'none' } } }])) } },
      { markup: [{ tagName: 'rect', selector: 'body' }, { tagName: 'g', selector: 'inner' }] });
    const ns = { ...shapes, net: { Host } }, graph = C.graph = new dia.Graph({}, { cellNamespace: ns }), hid = {}, cells = [];
    t.hosts.forEach(h => { const m = new Host({ id: 'h:' + h.id, position: pos[h.id], size: { width: parts[h.id].w, height: parts[h.id].h }, z: 5, ports: { items: ['right', 'left', 'top', 'bottom'].map(side => ({ id: 'p-' + side, group: side })) }, attrs: { root: { 'data-host': h.id, 'data-obj': 'host:' + h.id } } }); hid[h.id] = m.id; cells.push(m); });
    const flowsOn = {}; t.flows.forEach(f => (EV.netPath(t, f) || []).forEach(([l]) => { (flowsOn[l] = flowsOn[l] || []).push(f.id); }));
    // a label of a link; the link's own line of text (bold) stands beside the line, clear of the two devices
    const lab = (text, at, bold) => ({ position: { distance: at, offset: bold ? -17 : 0 }, markup: [{ tagName: 'rect', selector: 'b' }, { tagName: 'text', selector: 't' }],
      attrs: { t: { text, class: bold ? 'nc-lab nc-b' : 'nc-lab', textAnchor: 'middle', textVerticalAnchor: 'middle', pointerEvents: 'none' }, b: { ref: 't', x: 'calc(x-6)', y: 'calc(y-3)', width: 'calc(w+12)', height: 'calc(h+6)', rx: 6, fill: 'var(--surface-1)', stroke: bold ? 'var(--border)' : 'var(--text-secondary)', strokeWidth: 1 } } });
    t.links.forEach(l => { const [a, b] = l.between, fl = flowsOn[l.id] || []; if (!hid[a] || !hid[b]) return;
      fl.forEach((f, i) => cells.push(new shapes.standard.Link({ id: `f:${l.id}:${f}`, source: { id: hid[a] }, target: { id: hid[b] }, z: 1, off: (i - (fl.length - 1) / 2) * 6, attrs: { root: { pointerEvents: 'none', 'data-flowline': f }, line: { stroke: EV.netColor(t, f), strokeWidth: 3.5, targetMarker: null } } })));
      cells.push(new shapes.standard.Link({ id: 'l:' + l.id, source: { id: hid[a] }, target: { id: hid[b] }, z: 2, attrs: { root: { 'data-link': l.id, 'data-obj': 'link:' + l.id, cursor: 'pointer' }, line: { stroke: fl.length ? 'transparent' : 'var(--text-secondary)', strokeWidth: 2, targetMarker: null }, wrapper: { strokeWidth: 22 } },
        labels: [lab(`${l.id} · ${o.knobs[l.id + '.rate'] ? '✦ ' : ''}${TASK_VIEW._rate(String(l.rate))}${Object.entries(l.ends || {}).filter(([, x]) => x && 'rate' in x).map(([h, x]) => ` (${h}: ${o.knobs[`${l.id}.${h}.rate`] ? '✦ ' : ''}${TASK_VIEW._rate(String(x.rate))})`).join('')} · ${TASK_VIEW._rate(String(l.delay))}`, 0.5, true), ...(simple ? [] : [lab('device', 30), lab('device', -30)])] })); });
    const paper = C.paper = new dia.Paper({ el, model: graph, width: '100%', height: o.height || 440, async: false, gridSize: 1, drawGridSize: 10, drawGrid: { name: 'dot', args: { color: 'var(--border)', thickness: 1.4 } }, cellViewNamespace: ns, background: { color: 'transparent' },
      linkPinning: false, snapLinks: { radius: 60 }, markAvailable: true, clickThreshold: 6, defaultConnectionPoint: { name: 'anchor' }, defaultAnchor: { name: 'center' },
      defaultLink: () => new shapes.standard.Link({ z: 9, attrs: { line: { stroke: 'var(--live)', strokeWidth: 3, strokeDasharray: '7 5', targetMarker: null } } }),
      validateConnection: (sv, sm, tv) => sv !== tv && !!tv && tv.model.isElement() && !t.links.some(l => l.between.includes(sv.model.id.slice(2)) && l.between.includes(tv.model.id.slice(2))),
      interactive: v => (v.model.isLink() ? false : { elementMove: true, addLinkFromMagnet: true }) });
    graph.resetCells(cells);
    t.hosts.forEach(h => { const v = paper.findViewByModel(hid[h.id]), g = v && v.el.querySelector('[joint-selector=inner]'); if (g) { g.innerHTML = parts[h.id].svg; g.setAttribute('transform', `scale(${parts[h.id].k})`); } });
    C.spread(); graph.on('change:position', () => C.spread());
    // the zoom and the place of the picture: kept from the last drawing; the first time, as it fits
    if (C.view && C.view.for === N.s) { paper.scale(C.view.s); paper.translate(C.view.tx, C.view.ty); } else C.fit();
    // ---- gestures
    const idOf = m => String(m.id).slice(2), outside = ev => { const r = el.getBoundingClientRect(); return ev.clientX < r.left || ev.clientX > r.right || ev.clientY < r.top || ev.clientY > r.bottom; };
    paper.on('element:pointerclick', (v, ev) => { const f = ev.target.closest('[data-flow], [data-sink]'), q = ev.target.closest('[data-queue]'); N.pick(...(f ? ['flow', f.dataset.flow || f.dataset.sink] : q ? ['queue', q.dataset.queue] : ['host', idOf(v.model)])); });  // a part inside a host is chosen by a click on it: an application or its socket (at either end), a queue; anywhere else, the host
    paper.on('link:pointerclick', v => { if (String(v.model.id).startsWith('l:')) N.pick('link', idOf(v.model)); });
    paper.on('blank:pointerclick', () => N.pick(null));
    paper.on('element:pointermove', (v, ev) => { const id = idOf(v.model); if (outside(ev)) N.ghost(`release: remove ${N.deps('host', id).gone.map(([k, i]) => N.says(k, i)).join(', ')}`, 'rem', ev); else N.ghost(''); });
    paper.on('element:pointerup', (v, ev) => { const id = idOf(v.model); N.ghost(''); if (outside(ev)) return N.remove('host', id); o.pos[id] = { ...(o.pos[id] || {}), ...v.model.position() }; N.paint(); });
    paper.on('link:connect', v => { const a = idOf(graph.getCell(v.model.source().id)), b = v.model.target().id ? idOf(graph.getCell(v.model.target().id)) : null; v.model.remove(); if (b && a !== b) N.add.link(a, b); });
    let pan = null; paper.on('blank:pointerdown', (ev, x, y) => { pan = { x: ev.clientX, y: ev.clientY, tx: paper.translate().tx, ty: paper.translate().ty }; el.classList.add('panning'); });
    paper.on('blank:pointermove', ev => { if (!pan) return; paper.translate(pan.tx + ev.clientX - pan.x, pan.ty + ev.clientY - pan.y); C.keep(); N.paint(); });
    paper.on('blank:pointerup', () => { pan = null; el.classList.remove('panning'); });
    // the wheel of the mouse makes the picture larger and smaller, about the place the pointer is at (2026-11-17, the operator); the page does not scroll meanwhile
    el.addEventListener('wheel', ev => { if (!C.paper) return; ev.preventDefault(); C.zoom(ev.deltaY < 0 ? 1.12 : 1 / 1.12, ev); }, { passive: false });
    C.mark(o.sel);
  },
  // the lines of the flows that pass a link run side by side: each is moved off the middle line, across it
  spread() { const C = NETC; if (!C.graph) return; C.graph.getLinks().forEach(l => { if (!/^[lf]:/.test(String(l.id))) return; const off = l.get('off') || 0, a = C.graph.getCell(l.source().id), b = C.graph.getCell(l.target().id); if (!a || !b) return;
    // each end stands at the middle of the side of its host that faces the other host (where that side's + is); a flow's line is moved along that side by its offset
    const p = a.getBBox().center(), q = b.getBBox().center(), flat = Math.abs(q.x - p.x) >= Math.abs(q.y - p.y), sa = flat ? (q.x >= p.x ? 'right' : 'left') : (q.y >= p.y ? 'bottom' : 'top'), sb = flat ? (q.x >= p.x ? 'left' : 'right') : (q.y >= p.y ? 'top' : 'bottom'), args = flat ? { dy: off } : { dx: off };
    l.source({ id: a.id, anchor: { name: sa, args } }); l.target({ id: b.id, anchor: { name: sb, args } }); }); },
  keep() { const C = NETC, p = C.paper; if (p) C.view = { for: BRIEF_NET.s, s: p.scale().sx, tx: p.translate().tx, ty: p.translate().ty }; },
  // the whole network in view: every host, with its handles, inside the field (a very wide network becomes small; the wheel makes it larger again)
  fit() { const C = NETC, p = C.paper; if (!p) return; p.scale(1); p.translate(0, 0); if (C.graph.getCells().length) p.transformToFitContent({ padding: 24, maxScale: 1, minScale: 0.4, verticalAlign: 'middle', horizontalAlign: 'middle' }); C.keep(); },
  // larger or smaller by the factor f, about the pointer (ev) or, from a button, about the middle of what is in view: that place of the picture stays where it is
  zoom(f, ev) { const C = NETC, p = C.paper; if (!p) return; const s = Math.max(0.35, Math.min(2.5, p.scale().sx * f)), r = p.el.getBoundingClientRect(), px = ev ? ev.clientX - r.left : r.width / 2, py = ev ? ev.clientY - r.top : r.height / 2, c = p.paperToLocalPoint(px, py);
    p.scale(s); const c2 = p.localToPaperPoint(c); p.translate(p.translate().tx + px - c2.x, p.translate().ty + py - c2.y); C.keep(); BRIEF_NET.paint(); },
  // the chosen object: a heavier outline, and on a host or a link a button that removes it
  mark(sel) {
    const C = NETC, p = C.paper, J = window.joint; if (!p) return; p.removeTools(); p.el.querySelectorAll('.nc-sel').forEach(x => x.classList.remove('nc-sel')); if (!sel) return;
    const [kind, id] = sel, N = BRIEF_NET, act = () => N.remove(kind, id);
    if (kind === 'host' || kind === 'link') { const v = p.findViewByModel((kind === 'host' ? 'h:' : 'l:') + id); if (!v) return; v.el.classList.add('nc-sel');
      // a chosen host carries three handles: at its right edge (its width), at its lower edge (its height) and at its corner (both at once). The box
      // takes the width and the height it is given, each on its own (from half to three times); the picture inside keeps its proportions.
      const handle = (mode, d, cursor) => new (J.elementTools.Control.extend({
        children: [{ tagName: 'path', selector: 'handle', attributes: { d, fill: 'var(--text-primary)', stroke: 'var(--surface-1)', 'stroke-width': 1.5, cursor, [mode === 'xy' ? 'data-resize' : 'data-resize-' + mode]: id } }],
        getPosition(view) { const z = view.model.size(); return { x: mode === 'y' ? z.width * 0.2 : z.width, y: mode === 'x' ? z.height * 0.2 : z.height }; },  // the handle of the width stands clear of the + of the link, which is at the middle of that edge
        setPosition(view, at) { const q0 = C.parts[id], lim = v => Math.max(0.5, Math.min(3, v)), q = C.parts[id] = C.sized(q0, mode === 'y' ? q0.kx : lim(at.x / q0.w0), mode === 'x' ? q0.ky : lim(at.y / q0.h0)); view.model.resize(q.w, q.h);
          const g = view.el.querySelector('[joint-selector=inner]'); if (g) g.setAttribute('transform', `scale(${q.k})`); C.o.pos[id] = { ...view.model.position(), kx: q.kx, ky: q.ky }; C.spread(); } }))({ selector: 'body' });
      const sizers = [handle('xy', 'M-9 3 3 -9 3 3Z', 'nwse-resize'), handle('x', 'M-2 -11h4v22h-4z', 'ew-resize'), handle('y', 'M-11 -2h22v4h-22z', 'ns-resize')];
      v.addTools(new J.dia.ToolsView({ tools: kind === 'host' ? [new J.elementTools.Remove({ x: '100%', y: 0, offset: { x: 6, y: -6 }, action: act }), ...sizers] : [new J.linkTools.Remove({ distance: '50%', offset: 22, action: act })] })); }
    else { const g = p.el.querySelector(kind === 'flow' ? `[data-flow="${CSS.escape(id)}"]` : `[data-queue="${CSS.escape(id)}"]`); if (g) g.classList.add('nc-sel'); }
  },
  // While an application (or a link) waits for its second host, a line runs from the first host to the pointer: what is being drawn is seen being drawn.
  // p: { kind, from } or null. The line is in the colour the application will have (a link: dark, dashed).
  band(p) {
    const C = NETC, cv = C.paper && C.paper.el.parentNode; if (!cv) return; let g = cv.querySelector('#bn-band'); if (!p) { if (g) g.remove(); return; }
    const from = C.geom().pos[p.from]; if (!from) return; const x = from.x + from.w / 2, y = from.y + from.h / 2, n = BRIEF_NET.s.t.flows.length, col = p.kind === 'link' ? 'var(--text-primary)' : `var(--series-${(n % 8) + 1})`;
    if (!g) { g = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); g.id = 'bn-band'; cv.appendChild(g); }
    g.innerHTML = `<line x1="${x}" y1="${y}" x2="${C._bx ?? x}" y2="${C._by ?? y}" stroke="${col}" stroke-width="3" stroke-dasharray="${p.kind === 'link' ? '7 5' : '2 0'}" stroke-linecap="round" opacity=".8"/><circle cx="${x}" cy="${y}" r="5" fill="${col}"/>`; g.dataset.from = p.from; g.dataset.kind = p.kind;
  },
  bandTo(ev) { const C = NETC, cv = C.paper && C.paper.el.parentNode; if (!cv) return; const r = cv.getBoundingClientRect(); C._bx = ev.clientX - r.left; C._by = ev.clientY - r.top; const l = cv.querySelector('#bn-band line'); if (l) { l.setAttribute('x2', C._bx); l.setAttribute('y2', C._by); } },
  // where things are, in pixels of the canvas: each host's box, each link's two ends (for the places an object can be dropped at)
  geom() {
    const C = NETC, p = C.paper, out = { pos: {}, ends: {}, W: 0 }; if (!p) return out; out.W = p.el.getBoundingClientRect().width;
    C.graph.getElements().forEach(m => { const r = p.localToPaperRect(m.getBBox()); out.pos[String(m.id).slice(2)] = { x: r.x, y: r.y, w: r.width, h: r.height }; });
    C.graph.getLinks().forEach(l => { if (!String(l.id).startsWith('l:')) return; const v = p.findViewByModel(l), a = p.localToPaperPoint(v.sourcePoint), b = p.localToPaperPoint(v.targetPoint);
      out.ends[String(l.id).slice(2)] = { a: String(l.source().id).slice(2), c: String(l.target().id).slice(2), x1: a.x, y1: a.y, x2: b.x, y2: b.y }; });
    return out;
  },
  // the middle of what is in view, as a place in the picture (for a host added from the keyboard: it must come where it can be seen)
  center() { const C = NETC, p = C.paper; if (!p) return null; const r = p.el.getBoundingClientRect(), n = C.graph.getElements().length; return p.clientToLocalPoint(r.left + r.width / 2 + (n % 4) * 26, r.top + r.height / 2 + (n % 4) * 26); },
  // a point of the screen, as a place in the picture (for a host dropped there)
  at(ev) { const C = NETC; return C.paper ? C.paper.clientToLocalPoint(ev.clientX, ev.clientY) : { x: 30, y: 30 }; },
};
