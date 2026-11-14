// Set up and run. "New session" (the address ?tab=new, reached from Home's one button, or from a session's "Start a
// new session from this setup": ?tab=new&from=<session>): the set-up page. On a running session's page: the banner with Stop. Everything goes through control.py's POST endpoints; the page itself writes no file.
// The operator's own simulation and sweep, on the Operator tab, are in evidence_oprun.js.
// ======================================================================================================
Object.assign(EV, {
  nw: { policy: 'share', budget: '', draft: 'on', tokens: '', temp: '', baseline: true },  // blocks 6 and 7 of the set-up page
  briefs: {},  // brief id -> its file (null: it cannot be read), fetched once
  briefOf(id) { if (id && !(id in EV.briefs)) { EV.briefs[id] = undefined; EV.json(`../briefs/${id}.json`).then(b => { EV.briefs[id] = b; EV.draw(); }); } return EV.briefs[id]; },
  flags() {  // the choices of the panel as control.py takes them; a field left empty keeps the loop's default
    const n = EV.nw, o = { policy: n.policy, draft: n.draft, baseline: !!n.baseline }, num = (k, to) => { if (String(n[k]).trim()) o[to] = Number(n[k]); };
    num('budget', 'budget'); num('tokens', 'max_tokens'); num('temp', 'temperature'); return o;
  },

  // ---- "New session": the set-up page. Its seven blocks, the strip above Start and the two buttons are drawn by
  // brief_editor.js in a node of its own, which is kept when the page is drawn again (nothing typed is lost).
  newTab() {
    const st = EV.st, S = EV.s, running = st.sessions.filter(x => x.running).length;
    return `<div class="ev-card" id="new-setup"><h2>New session <small>one complete attempt by the AI at one ${EV.term('Brief', 'brief')} · ${running} running now${S.from ? ` · filled from session ${EV.e(S.from)}` : ''}</small></h2>
      <p class="sec-q">What will the network be, what will the AI be asked, and what will it see?</p>${EV.legendBar()}<div id="be-host"></div></div>`;
  },
  async afterNew() {
    if (!document.getElementById('be-host')) return;
    if (typeof BRIEF_EDITOR === 'undefined') { if (EV.beBusy) return; EV.beBusy = true;
      await new Promise(ok => { const s = document.createElement('script'); s.src = 'brief_editor.js?t=' + Date.now(); s.onload = s.onerror = ok; document.head.appendChild(s); }); }
    const host = document.getElementById('be-host'); if (!host || typeof BRIEF_EDITOR === 'undefined') return;
    BRIEF_EDITOR.mount(host, { get st() { return EV.st; }, post: EV.post, e: EV.e, from: EV.s.from || null, flags: EV.flags,
      go: o => { Object.assign(EV.s, o); history.replaceState(null, '', EV.address()); },
      after: async () => { EV.sig = ''; await EV.load(); },
      started: async id => { for (let i = 0; i < 40; i++) { const st = await EV.json('../api/status'); if (st && st.sessions.some(x => x.id === id)) break; await new Promise(ok => setTimeout(ok, 500)); }  // until the loop has made its folder
        return EV.go({ view: 'session', sid: id, from: null }); } });
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
  nw(t) { const n = EV.nw, k = t.dataset.k; n[k] = t.type === 'checkbox' ? t.checked : t.value;  // a field never draws the page again: it would lose the cursor to its neighbour
    if (k === 'draft') { const el = document.querySelector('#new-setup input[data-k=tokens]'); if (el) el.placeholder = n.draft === 'on' ? 32000 : 3000; } },
});
EV.inp = Object.assign(EV.inp || {}, { nw(t) { EV.chg.nw(t); } });  // as it is typed, so that a value that cannot be used is refused at once
EV.act = Object.assign(EV.act || {}, {
  new() { EV.go({ view: 'new', from: null }); },
  async stop() {
    if (!window.confirm(`Stop session ${EV.s.sid}? It ends where it is, without a final report.`)) return;
    EV.stopping = true; EV.stopMsg = ''; EV.draw();
    try { await EV.post('../api/stop', { session: EV.s.sid }); } catch (x) { EV.stopMsg = x.message; }
    EV.stopping = false; EV.sig = ''; EV.load();
  },
});
