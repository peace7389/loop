// Set up and run. On Home: the New session panel (brief, scheduling policy, settings, Start). On a running session's
// page: the banner with Stop. Everything goes through control.py's POST endpoints; the page itself writes no file.
// The operator's own simulation and sweep, on the Operator tab, are in evidence_oprun.js.
// ======================================================================================================
Object.assign(EV, {
  nw: { brief: null, policy: 'share', budget: '', draft: 'on', tokens: '', temp: '', baseline: true, edit: false, busy: false, msg: '' },
  briefs: {},  // brief id -> its file (null: it cannot be read), fetched once
  briefOf(id) { if (id && !(id in EV.briefs)) { EV.briefs[id] = undefined; EV.json(`../briefs/${id}.json`).then(b => { EV.briefs[id] = b; EV.draw(); }); } return EV.briefs[id]; },
  flags() {  // the choices of the panel as control.py takes them; a field left empty keeps the loop's default
    const n = EV.nw, o = { policy: n.policy, draft: n.draft, baseline: !!n.baseline }, num = (k, to) => { if (String(n[k]).trim()) o[to] = Number(n[k]); };
    num('budget', 'budget'); num('tokens', 'max_tokens'); num('temp', 'temperature'); return o;
  },

  newPanel() {
    const n = EV.nw, st = EV.st, e = EV.e; if (!st.briefs.includes(n.brief)) n.brief = st.briefs[0] || null;
    const b = EV.briefOf(n.brief), lim = b && b.limits ? b.limits.simulations : null, running = st.sessions.filter(x => x.running).length;
    const radio = (v, more) => `<label style="display:block;font-weight:400;margin:4px 0"><input type="radio" name="nw-policy" data-ch="nw" data-k="policy" value="${v}"${n.policy === v ? ' checked' : ''}> <b>${v}</b> <span class="sm">${more}</span></label>`;
    const field = (label, html, note) => `<div><span>${label}</span>${html}<span>${note}</span></div>`;
    return `<div class="ev-card" id="new-panel"><h2>New session<small>one complete attempt by the AI at one ${EV.term('Brief', 'brief')} · ${running} running now</small></h2>
      <div class="nw">
        <div><h3>1 · ${EV.term('Brief', 'Brief')}</h3><p><select data-ch="nw" data-k="brief">${st.briefs.map(id => `<option${id === n.brief ? ' selected' : ''}>${e(id)}</option>`).join('')}</select></p>
          <p class="sm">${b ? `${e(b.task || '')}<br><b>goal</b> ${e(b.goal && b.goal.kind === 'open' ? 'open: chosen by the model' : EV.goal(b.goal))} · <b>limit</b> ${e(lim ?? 'not recorded')} simulations` : b === null ? 'This brief cannot be read.' : 'Loading…'}</p>
          <p><button data-act="nwedit">${n.edit ? 'close the brief editor' : 'open the brief editor…'}</button> <span class="sm">change a brief and save it as a new one; an existing brief is never overwritten</span></p></div>
        <div><h3>2 · ${EV.term('Scheduling policy', 'Scheduling policy')}</h3>${radio('share', 'a flow may use what the other leaves unused')}${radio('cap', 'each flow is held to its configured part of the link')}
          ${radio('random', 'the harness chooses share or cap, records it under checks/, and this page shows it only after the session is scored')}<p class="sm">Never told to the model.</p></div>
        <div><h3>3 · Settings</h3><div class="kv">
          ${field('simulations allowed (budget)', `<input type="number" min="1" data-ch="nw" data-k="budget" value="${e(n.budget)}" placeholder="${e(lim ?? '')}">`, 'empty: the brief\'s limit')}
          ${field('draft before the answer', `<select data-ch="nw" data-k="draft"><option${n.draft === 'on' ? ' selected' : ''}>on</option><option${n.draft === 'off' ? ' selected' : ''}>off</option></select>`, 'default on')}
          ${field('most tokens of one answer', `<input type="number" min="256" data-ch="nw" data-k="tokens" value="${e(n.tokens)}" placeholder="${n.draft === 'on' ? 32000 : 3000}">`, 'empty: the default shown')}
          ${field('temperature', `<input type="number" min="0" max="2" step="0.1" data-ch="nw" data-k="temp" value="${e(n.temp)}" placeholder="0.3">`, 'default 0.3')}
          ${field('baseline', `<label style="font-weight:400"><input type="checkbox" data-ch="nw" data-k="baseline"${n.baseline ? ' checked' : ''}> run it first</label>`, 'every setting at its default, by the harness')}</div></div>
        <div><h3>4 · Start</h3><p><button class="big" data-act="nwstart"${n.busy || !n.brief ? ' disabled' : ''}>${n.busy ? 'Starting…' : 'Start the session'}</button></p>
          <p class="sm">The page then goes to the new session and follows it.</p>${n.msg ? `<p class="bad">${e(n.msg)}</p>` : ''}</div></div>
      ${n.edit ? '<div id="be-host" style="margin-top:14px;border-top:1px solid var(--border);padding-top:12px"></div>' : ''}</div>`;
  },
  // the brief editor (brief_editor.js, the one of the older control page) in its own node, kept when the page is drawn again
  async afterHome() {
    if (!document.getElementById('be-host')) return;
    if (typeof BRIEF_EDITOR === 'undefined') { if (EV.beBusy) return; EV.beBusy = true;
      await new Promise(ok => { const s = document.createElement('script'); s.src = 'brief_editor.js?t=' + Date.now(); s.onload = s.onerror = ok; document.head.appendChild(s); }); }
    const host = document.getElementById('be-host'); if (!host || typeof BRIEF_EDITOR === 'undefined') return;
    BRIEF_EDITOR.mount(host, { get st() { return EV.st; }, post: EV.post, e: EV.e, sec: (i, title, intro, body) => `<h3>${title}</h3><p class="sm" style="max-width:980px">${intro}</p>${body}`, session: EV.flags,
      after: async () => { EV.sig = ''; await EV.load(); const id = BRIEF_EDITOR.s && BRIEF_EDITOR.s.baseId; if (id && EV.st.briefs.includes(id) && EV.nw.brief !== id) { EV.nw.brief = id; EV.draw(); } } });
  },

  // ---- a running session: where it is, and Stop (for a session started from this server)
  banner() {
    const M = EV.M, row = EV.files.row || {}, e = EV.e; if (!row.running) return '';
    const t = M.turns[M.turns.length - 1];
    return `<div class="ev-card ev-bar ev-run"><span class="pill live">running</span> <b>${t && t.n ? 'turn ' + t.n : 'before the first turn'}</b> · ${t && t.left != null ? `${t.left} simulation${t.left === 1 ? '' : 's'} left` : 'simulations left: not recorded yet'}
      <span class="sm">· this page refreshes by itself as records arrive; what you have open stays open</span>
      <span class="end">${row.stoppable ? `<button data-act="stop"${EV.stopping ? ' disabled' : ''}>${EV.stopping ? 'Stopping…' : 'Stop'}</button>` : 'started from a terminal: it is stopped there'}${EV.stopMsg ? ` <span class="bad">${e(EV.stopMsg)}</span>` : ''}</span></div>`;
  },
});
EV.chg = Object.assign(EV.chg || {}, {
  nw(t) { const n = EV.nw, k = t.dataset.k; n[k] = t.type === 'checkbox' ? t.checked : t.value;  // only another brief draws the page again: a field never loses the cursor to its neighbour
    if (k === 'brief') EV.draw(); else if (k === 'draft') { const el = document.querySelector('#new-panel input[data-k=tokens]'); if (el) el.placeholder = n.draft === 'on' ? 32000 : 3000; } },
});
EV.act = Object.assign(EV.act || {}, {
  new() { EV.s.newOpen = !EV.s.newOpen; EV.draw(); },
  nwedit() { EV.nw.edit = !EV.nw.edit; EV.draw(); },
  async nwstart() {
    const n = EV.nw; if (n.busy) return; n.busy = true; n.msg = ''; EV.draw();
    try { const r = await EV.post('../api/session', { brief: n.brief, ...EV.flags() });
      for (let i = 0; i < 40; i++) { const st = await EV.json('../api/status'); if (st && st.sessions.some(x => x.id === r.id)) break; await new Promise(ok => setTimeout(ok, 500)); }  // until the loop has made its folder
      n.busy = false; EV.s.newOpen = false; return EV.go({ view: 'session', sid: r.id });
    } catch (x) { n.busy = false; n.msg = x.message; EV.draw(); }
  },
  async stop() {
    if (!window.confirm(`Stop session ${EV.s.sid}? It ends where it is, without a final report.`)) return;
    EV.stopping = true; EV.stopMsg = ''; EV.draw();
    try { await EV.post('../api/stop', { session: EV.s.sid }); } catch (x) { EV.stopMsg = x.message; }
    EV.stopping = false; EV.sig = ''; EV.load();
  },
});
